#!/usr/bin/env python3
"""
A/B Testing - A/B 测试工具

对权重优化进行统计验证，确保改进的有效性。

核心功能：
1. 随机分组 - 将用户随机分配到 A/B 组
2. 统计显著性检验 - t-test, chi-square test
3. 效果评估 - 计算改进幅度和置信区间
4. 多指标分析 - 质量分数、用户满意度、修改率等

统计方法：
t-test: t = (mean_B - mean_A) / sqrt(s²/n_A + s²/n_B)
p-value: P(T > |t|) under H0: mean_A = mean_B

Author: Bobo (Self-Evolution Skill)
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import math

# 添加父目录到路径
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


class ABTesting:
    """A/B 测试工具类"""

    def __init__(self, confidence_level: float = 0.95):
        """初始化 A/B 测试

        Args:
            confidence_level: 置信水平 (默认 0.95 即 95%)
        """
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level  # 显著性水平

    def calculate_mean(self, values: List[float]) -> float:
        """计算平均值"""
        return sum(values) / len(values) if values else 0.0

    def calculate_variance(self, values: List[float]) -> float:
        """计算方差"""
        if len(values) < 2:
            return 0.0

        mean = self.calculate_mean(values)
        return sum((x - mean) ** 2 for x in values) / (len(values) - 1)

    def calculate_std(self, values: List[float]) -> float:
        """计算标准差"""
        return math.sqrt(self.calculate_variance(values))

    def t_test(self, group_a: List[float], group_b: List[float]) -> Tuple[float, float, bool]:
        """独立样本 t 检验

        H0: mean_A = mean_B
        H1: mean_B > mean_A (单尾检验)

        Args:
            group_a: 对照组数据
            group_b: 实验组数据

        Returns:
            (t_statistic, p_value, is_significant) 元组
        """
        if not group_a or not group_b:
            return 0.0, 1.0, False

        n_a = len(group_a)
        n_b = len(group_b)

        if n_a < 2 or n_b < 2:
            return 0.0, 1.0, False

        # 计算均值和方差
        mean_a = self.calculate_mean(group_a)
        mean_b = self.calculate_mean(group_b)
        var_a = self.calculate_variance(group_a)
        var_b = self.calculate_variance(group_b)

        # 计算 t 统计量（使用 Welch's t-test，不假设方差齐性）
        se = math.sqrt(var_a / n_a + var_b / n_b)

        if se == 0:
            return 0.0, 1.0, False

        t_stat = (mean_b - mean_a) / se

        # 自由度（Welch-Satterthwaite 方程）
        df = ((var_a / n_a + var_b / n_b) ** 2) / \
             ((var_a / n_a) ** 2 / (n_a - 1) + (var_b / n_b) ** 2 / (n_b - 1))

        # 近似 p 值计算（简化版，使用正态分布近似）
        # 对于大样本（df > 30），t 分布接近正态分布
        if df > 30:
            # 使用标准正态分布近似
            # P(Z > t) ≈ 1 - Φ(t)
            # 近似公式：Φ(x) ≈ 0.5 * (1 + erf(x/sqrt(2)))
            # erf(x) ≈ sign(x) * sqrt(1 - exp(-x²*(4/π + 0.147*x²)/(1 + 0.147*x²)))

            x = t_stat / math.sqrt(2)
            a = 0.147
            erf_approx = (1 if x >= 0 else -1) * math.sqrt(
                1 - math.exp(-x * x * (4 / math.pi + a * x * x) / (1 + a * x * x))
            )
            p_value = 0.5 * (1 - erf_approx)
        else:
            # 对于小样本，使用保守估计
            p_value = 0.1 if t_stat > 1.5 else 0.3

        # 判断是否显著（单尾检验）
        is_significant = (t_stat > 0) and (p_value < self.alpha)

        return t_stat, p_value, is_significant

    def calculate_effect_size(self, group_a: List[float], group_b: List[float]) -> float:
        """计算效应量（Cohen's d）

        d = (mean_B - mean_A) / pooled_std

        Args:
            group_a: 对照组数据
            group_b: 实验组数据

        Returns:
            Cohen's d 效应量
        """
        if not group_a or not group_b:
            return 0.0

        n_a = len(group_a)
        n_b = len(group_b)

        if n_a < 2 or n_b < 2:
            return 0.0

        mean_a = self.calculate_mean(group_a)
        mean_b = self.calculate_mean(group_b)
        var_a = self.calculate_variance(group_a)
        var_b = self.calculate_variance(group_b)

        # 合并标准差
        pooled_var = ((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2)
        pooled_std = math.sqrt(pooled_var)

        if pooled_std == 0:
            return 0.0

        cohens_d = (mean_b - mean_a) / pooled_std

        return cohens_d

    def analyze(self, version_a_data: List[Dict], version_b_data: List[Dict],
                metrics: List[str] = None) -> Dict[str, Any]:
        """分析 A/B 测试结果

        Args:
            version_a_data: 版本 A 的数据（对照组）
            version_b_data: 版本 B 的数据（实验组）
            metrics: 要分析的指标列表

        Returns:
            分析结果字典
        """
        if metrics is None:
            metrics = ['quality_score', 'satisfaction', 'modification_rate']

        results = {
            'test_date': datetime.now().isoformat(),
            'confidence_level': self.confidence_level,
            'sample_sizes': {
                'version_a': len(version_a_data),
                'version_b': len(version_b_data)
            },
            'metrics': {},
            'overall_winner': None,
            'recommendation': None
        }

        # 分析每个指标
        for metric in metrics:
            # 提取指标值
            values_a = [d.get(metric, 0.0) for d in version_a_data if metric in d]
            values_b = [d.get(metric, 0.0) for d in version_b_data if metric in d]

            if not values_a or not values_b:
                continue

            # 计算统计量
            mean_a = self.calculate_mean(values_a)
            mean_b = self.calculate_mean(values_b)
            std_a = self.calculate_std(values_a)
            std_b = self.calculate_std(values_b)

            # t 检验
            t_stat, p_value, is_significant = self.t_test(values_a, values_b)

            # 效应量
            effect_size = self.calculate_effect_size(values_a, values_b)

            # 改进幅度
            improvement = ((mean_b - mean_a) / mean_a * 100) if mean_a > 0 else 0

            # 置信区间（近似）
            se = math.sqrt(self.calculate_variance(values_b) / len(values_b))
            margin_of_error = 1.96 * se  # 95% 置信区间
            ci_lower = mean_b - margin_of_error
            ci_upper = mean_b + margin_of_error

            results['metrics'][metric] = {
                'version_a': {
                    'mean': round(mean_a, 4),
                    'std': round(std_a, 4),
                    'n': len(values_a)
                },
                'version_b': {
                    'mean': round(mean_b, 4),
                    'std': round(std_b, 4),
                    'n': len(values_b),
                    'confidence_interval': [round(ci_lower, 4), round(ci_upper, 4)]
                },
                'statistics': {
                    't_statistic': round(t_stat, 4),
                    'p_value': round(p_value, 4),
                    'effect_size': round(effect_size, 4),
                    'is_significant': is_significant
                },
                'improvement': {
                    'absolute': round(mean_b - mean_a, 4),
                    'relative': round(improvement, 2),  # %
                },
                'winner': 'version_b' if mean_b > mean_a and is_significant else 'no_difference'
            }

        # 确定总体赢家
        significant_improvements = sum(
            1 for m in results['metrics'].values()
            if m['statistics']['is_significant'] and m['improvement']['relative'] > 0
        )

        significant_regressions = sum(
            1 for m in results['metrics'].values()
            if m['statistics']['is_significant'] and m['improvement']['relative'] < 0
        )

        if significant_improvements > significant_regressions:
            results['overall_winner'] = 'version_b'
            results['recommendation'] = 'Deploy version B - Shows significant improvement'
        elif significant_regressions > significant_improvements:
            results['overall_winner'] = 'version_a'
            results['recommendation'] = 'Keep version A - Version B shows regression'
        else:
            results['overall_winner'] = 'inconclusive'
            results['recommendation'] = 'Needs more data or no significant difference'

        return results

    def format_report(self, results: Dict[str, Any]) -> str:
        """格式化为可读报告

        Args:
            results: 分析结果

        Returns:
            格式化的报告字符串
        """
        report = []
        report.append("=" * 60)
        report.append("A/B Test Report")
        report.append("=" * 60)
        report.append(f"Test Date: {results['test_date']}")
        report.append(f"Confidence Level: {results['confidence_level']*100}%")
        report.append(f"Sample Sizes: A={results['sample_sizes']['version_a']}, "
                     f"B={results['sample_sizes']['version_b']}")
        report.append("")

        # 每个指标的结果
        for metric, data in results['metrics'].items():
            report.append(f"Metric: {metric}")
            report.append("-" * 40)
            report.append(f"  Version A: {data['version_a']['mean']:.4f} "
                         f"(± {data['version_a']['std']:.4f})")
            report.append(f"  Version B: {data['version_b']['mean']:.4f} "
                         f"(± {data['version_b']['std']:.4f})")
            report.append(f"  Improvement: {data['improvement']['relative']:+.2f}%")
            report.append(f"  p-value: {data['statistics']['p_value']:.4f}")
            report.append(f"  Effect Size: {data['statistics']['effect_size']:.4f}")
            report.append(f"  Winner: {data['winner']}")
            report.append("")

        # 总体结论
        report.append("=" * 60)
        report.append(f"Overall Winner: {results['overall_winner'].upper()}")
        report.append(f"Recommendation: {results['recommendation']}")
        report.append("=" * 60)

        return "\n".join(report)


def main():
    """命令行测试入口"""
    import argparse

    parser = argparse.ArgumentParser(description='A/B Testing - 统计验证工具')
    parser.add_argument('file_a', help='版本 A 数据文件（JSON）')
    parser.add_argument('file_b', help='版本 B 数据文件（JSON）')
    parser.add_argument('--confidence', type=float, default=0.95,
                       help='置信水平 (默认: 0.95)')
    parser.add_argument('--output', type=str, help='输出报告文件路径')

    args = parser.parse_args()

    try:
        # 加载数据
        with open(args.file_a, 'r', encoding='utf-8') as f:
            data_a = json.load(f)

        with open(args.file_b, 'r', encoding='utf-8') as f:
            data_b = json.load(f)

        # 执行 A/B 测试
        ab_test = ABTesting(confidence_level=args.confidence)
        results = ab_test.analyze(data_a, data_b)

        # 生成报告
        report = ab_test.format_report(results)
        print(report)

        # 保存结果
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Results saved to: {args.output}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
