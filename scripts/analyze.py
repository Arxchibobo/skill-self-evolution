#!/usr/bin/env python3
"""
Self-Evolution: 数据分析和优化脚本

分析 skill 执行数据，生成质量报告，发现模式，优化权重
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import List, Dict, Any, Tuple
import re

# 尝试导入科学计算库
try:
    import numpy as np
    from scipy.stats import pearsonr
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("警告: 未安装 scipy，部分统计功能将不可用")


class SelfEvolutionAnalyzer:
    """Self-Evolution 分析器"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            home = os.path.expanduser("~")
            data_dir = os.path.join(home, ".claude/skills/self-evolution/data")

        self.data_dir = Path(data_dir)
        self.executions_dir = self.data_dir / "executions"
        self.patterns_dir = self.data_dir / "patterns"
        self.weights_dir = self.data_dir / "weights"
        self.reports_dir = self.data_dir / ".." / "reports"

        # 确保目录存在
        for dir_path in [self.patterns_dir, self.weights_dir, self.reports_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def load_executions(self, days: int = 30) -> List[Dict[str, Any]]:
        """加载最近 N 天的执行数据"""
        executions = []
        cutoff_date = datetime.now() - timedelta(days=days)

        # 遍历所有月份目录
        if not self.executions_dir.exists():
            print(f"警告: 数据目录不存在: {self.executions_dir}")
            return executions

        for month_dir in sorted(self.executions_dir.iterdir()):
            if not month_dir.is_dir() or month_dir.name == '.':
                continue

            # 加载该月的所有执行记录
            for exec_file in month_dir.glob("sess_*.json"):
                try:
                    with open(exec_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # 检查日期
                    exec_date = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                    if exec_date >= cutoff_date:
                        executions.append(data)
                except Exception as e:
                    print(f"警告: 无法加载 {exec_file}: {e}")

        print(f"已加载 {len(executions)} 条执行记录")
        return executions

    def calculate_quality_scores(self, executions: List[Dict]) -> List[Dict]:
        """计算质量分数"""
        scored = []

        for exec_data in executions:
            scores = {
                'completeness': self._score_completeness(exec_data),
                'consistency': self._score_consistency(exec_data),
                'professionalism': self._score_professionalism(exec_data),
                'performance': self._score_performance(exec_data),
                'maintainability': self._score_maintainability(exec_data)
            }

            # 加权平均
            weights = {
                'completeness': 0.25,
                'consistency': 0.20,
                'professionalism': 0.25,
                'performance': 0.15,
                'maintainability': 0.15
            }

            total_score = sum(scores[k] * weights[k] for k in scores)

            exec_data['quality_score'] = total_score
            exec_data['quality_breakdown'] = scores
            exec_data['quality_grade'] = self._get_grade(total_score)

            scored.append(exec_data)

        return scored

    def _score_completeness(self, exec_data: Dict) -> float:
        """评分：完整性"""
        output = exec_data.get('output', {})
        score = 0.0

        # 有代码行
        if output.get('code_lines', 0) > 0:
            score += 0.3

        # 有组件
        if output.get('components_count', 0) > 0:
            score += 0.2

        # 有响应式设计
        if output.get('has_responsive', False):
            score += 0.25

        # 有暗色模式
        if output.get('has_dark_mode', False):
            score += 0.25

        return score

    def _score_consistency(self, exec_data: Dict) -> float:
        """评分：一致性"""
        elements = exec_data.get('execution', {}).get('elements_used', {})
        score = 1.0

        # 检查样式一致性
        styles = elements.get('styles', [])
        if len(styles) > 3:
            score -= 0.2  # 样式太多可能不一致

        # 检查颜色使用
        colors = elements.get('colors', [])
        if len(colors) > 8:
            score -= 0.2  # 颜色太多

        # 检查字体使用
        fonts = elements.get('fonts', [])
        if len(fonts) > 3:
            score -= 0.2  # 字体太多

        return max(0.0, score)

    def _score_professionalism(self, exec_data: Dict) -> float:
        """评分：专业性"""
        output = exec_data.get('output', {})
        score = 0.5  # 基础分

        # 有响应式设计
        if output.get('has_responsive', False):
            score += 0.25

        # 有暗色模式
        if output.get('has_dark_mode', False):
            score += 0.25

        return score

    def _score_performance(self, exec_data: Dict) -> float:
        """评分：性能"""
        duration = exec_data.get('execution', {}).get('duration_ms', 0)

        # 执行时间越短越好
        if duration < 1000:
            return 1.0
        elif duration < 2000:
            return 0.8
        elif duration < 3000:
            return 0.6
        elif duration < 5000:
            return 0.4
        else:
            return 0.2

    def _score_maintainability(self, exec_data: Dict) -> float:
        """评分：可维护性"""
        output = exec_data.get('output', {})
        components = output.get('components_count', 0)
        lines = output.get('code_lines', 0)

        if lines == 0:
            return 0.0

        # 组件化程度
        if components > 0:
            ratio = components / (lines / 100)  # 每 100 行代码的组件数
            if ratio >= 1.0:
                return 1.0
            else:
                return 0.5 + (ratio * 0.5)

        return 0.3  # 没有组件化

    def _get_grade(self, score: float) -> str:
        """获取等级"""
        if score >= 0.9:
            return 'A'
        elif score >= 0.8:
            return 'B'
        elif score >= 0.7:
            return 'C'
        elif score >= 0.6:
            return 'D'
        else:
            return 'F'

    def discover_patterns(self, executions: List[Dict]) -> Dict[str, Any]:
        """发现模式"""
        patterns = {
            'frequent_combinations': self._find_frequent_combinations(executions),
            'search_sequences': self._analyze_search_sequences(executions),
            'success_patterns': self._identify_success_patterns(executions)
        }

        # 保存模式
        output_file = self.patterns_dir / f"patterns_{datetime.now().strftime('%Y%m%d')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, indent=2, ensure_ascii=False)

        print(f"模式已保存到: {output_file}")
        return patterns

    def _find_frequent_combinations(self, executions: List[Dict]) -> List[Dict]:
        """找出频繁组合"""
        # 样式组合
        style_combinations = Counter()
        color_combinations = Counter()

        for exec_data in executions:
            elements = exec_data.get('execution', {}).get('elements_used', {})

            # 样式组合
            styles = tuple(sorted(elements.get('styles', [])))
            if styles:
                style_combinations[styles] += 1

            # 颜色组合
            colors = tuple(sorted(elements.get('colors', []))[:5])  # 只取前5个颜色
            if colors:
                color_combinations[colors] += 1

        # 取 Top 10
        return {
            'styles': [
                {'combination': list(combo), 'count': count, 'frequency': count / len(executions)}
                for combo, count in style_combinations.most_common(10)
            ],
            'colors': [
                {'combination': list(combo), 'count': count, 'frequency': count / len(executions)}
                for combo, count in color_combinations.most_common(10)
            ]
        }

    def _analyze_search_sequences(self, executions: List[Dict]) -> List[Dict]:
        """分析搜索序列"""
        sequences = Counter()

        for exec_data in executions:
            searches = exec_data.get('execution', {}).get('searches_performed', [])
            if searches:
                # 提取搜索域序列
                domains = tuple(s.get('domain') for s in searches if s.get('domain'))
                if domains:
                    sequences[domains] += 1

        return [
            {'sequence': list(seq), 'count': count, 'frequency': count / len(executions)}
            for seq, count in sequences.most_common(10)
        ]

    def _identify_success_patterns(self, executions: List[Dict]) -> Dict[str, Any]:
        """识别成功模式"""
        # 筛选高质量执行
        high_quality = [e for e in executions if e.get('quality_score', 0) >= 0.85]

        if not high_quality:
            return {'message': '没有足够的高质量执行数据'}

        # 分析共同特征
        common_styles = Counter()
        common_searches = Counter()
        common_stacks = Counter()

        for exec_data in high_quality:
            # 样式
            styles = exec_data.get('execution', {}).get('elements_used', {}).get('styles', [])
            for style in styles:
                common_styles[style] += 1

            # 搜索序列
            searches = exec_data.get('execution', {}).get('searches_performed', [])
            for search in searches:
                domain = search.get('domain')
                if domain:
                    common_searches[domain] += 1

            # 技术栈
            stack = exec_data.get('trigger', {}).get('context', {}).get('tech_stack')
            if stack:
                common_stacks[stack] += 1

        return {
            'high_quality_count': len(high_quality),
            'common_styles': common_styles.most_common(5),
            'common_searches': common_searches.most_common(5),
            'common_stacks': common_stacks.most_common(3),
            'avg_quality_score': np.mean([e['quality_score'] for e in high_quality]) if HAS_SCIPY else sum(e['quality_score'] for e in high_quality) / len(high_quality)
        }

    def optimize_weights(self, executions: List[Dict]) -> Dict[str, float]:
        """优化元素权重"""
        # 计算每个元素的使用频率和质量相关性
        element_stats = defaultdict(lambda: {'usage': 0, 'quality_sum': 0, 'count': 0})

        for exec_data in executions:
            quality = exec_data.get('quality_score', 0)
            elements = exec_data.get('execution', {}).get('elements_used', {})

            # 样式
            for style in elements.get('styles', []):
                element_stats[f'style:{style}']['usage'] += 1
                element_stats[f'style:{style}']['quality_sum'] += quality
                element_stats[f'style:{style}']['count'] += 1

            # 颜色
            for color in elements.get('colors', []):
                element_stats[f'color:{color}']['usage'] += 1
                element_stats[f'color:{color}']['quality_sum'] += quality
                element_stats[f'color:{color}']['count'] += 1

        # 计算权重
        weights = {}
        for element, stats in element_stats.items():
            if stats['count'] > 0:
                avg_quality = stats['quality_sum'] / stats['count']
                usage_score = min(1.0, stats['usage'] / len(executions))

                # 综合权重
                weights[element] = avg_quality * 0.6 + usage_score * 0.4

        # 保存权重
        output_file = self.weights_dir / f"weights_{datetime.now().strftime('%Y%m%d')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(weights, f, indent=2, ensure_ascii=False)

        print(f"权重已保存到: {output_file}")
        return weights

    def generate_dashboard(self, executions: List[Dict], patterns: Dict, weights: Dict) -> str:
        """生成仪表板"""
        # 统计数据
        total_executions = len(executions)
        avg_quality = np.mean([e.get('quality_score', 0) for e in executions]) if HAS_SCIPY else sum(e.get('quality_score', 0) for e in executions) / len(executions) if executions else 0
        avg_duration = np.mean([e.get('execution', {}).get('duration_ms', 0) for e in executions]) if HAS_SCIPY else sum(e.get('execution', {}).get('duration_ms', 0) for e in executions) / len(executions) if executions else 0

        # 按 skill 分组
        skill_stats = defaultdict(lambda: {'count': 0, 'quality_sum': 0})
        for exec_data in executions:
            skill = exec_data.get('skill_name', 'unknown')
            skill_stats[skill]['count'] += 1
            skill_stats[skill]['quality_sum'] += exec_data.get('quality_score', 0)

        # 生成 Markdown
        dashboard = f"""# Self-Evolution Dashboard

**最后更新**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 整体概览

### 核心指标
- **总执行次数**: {total_executions}
- **平均质量分**: {avg_quality:.3f}
- **平均执行时间**: {avg_duration:.0f}ms
- **时间范围**: 最近 30 天

### 质量分布
"""

        # 质量分布
        grade_dist = Counter(e.get('quality_grade', 'F') for e in executions)
        for grade in ['A', 'B', 'C', 'D', 'F']:
            count = grade_dist.get(grade, 0)
            pct = (count / total_executions * 100) if total_executions > 0 else 0
            dashboard += f"- **{grade}级**: {count} ({pct:.1f}%)\n"

        dashboard += "\n---\n\n## 🎯 Skill 表现\n\n"

        # Skill 统计
        for skill, stats in sorted(skill_stats.items(), key=lambda x: x[1]['count'], reverse=True):
            avg_quality_skill = stats['quality_sum'] / stats['count'] if stats['count'] > 0 else 0
            dashboard += f"### {skill}\n"
            dashboard += f"- 执行次数: {stats['count']}\n"
            dashboard += f"- 平均质量: {avg_quality_skill:.3f}\n\n"

        dashboard += "---\n\n## 🔍 发现的模式\n\n"

        # 频繁组合
        if 'frequent_combinations' in patterns:
            dashboard += "### 频繁组合\n\n"
            dashboard += "**样式组合 Top 5**:\n"
            for combo in patterns['frequent_combinations'].get('styles', [])[:5]:
                dashboard += f"- {', '.join(combo['combination'])} (使用 {combo['count']} 次)\n"

        # 搜索序列
        if 'search_sequences' in patterns:
            dashboard += "\n**常用搜索序列**:\n"
            for seq in patterns['search_sequences'][:5]:
                dashboard += f"- {' → '.join(seq['sequence'])} (使用 {seq['count']} 次)\n"

        dashboard += "\n---\n\n## 📈 优化权重 Top 10\n\n"

        # Top 权重
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:10]
        for element, weight in sorted_weights:
            dashboard += f"- `{element}`: {weight:.3f}\n"

        dashboard += "\n---\n\n## 💡 改进建议\n\n"

        # 生成改进建议
        suggestions = []
        if avg_quality < 0.8:
            suggestions.append("- 整体质量分低于 0.8，建议重点提升完整性和专业性")
        if avg_duration > 2000:
            suggestions.append("- 平均执行时间超过 2秒，建议优化搜索策略")

        if suggestions:
            dashboard += "\n".join(suggestions)
        else:
            dashboard += "- 当前表现良好，继续保持！"

        # 保存仪表板
        output_file = self.reports_dir / "dashboard.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(dashboard)

        print(f"仪表板已保存到: {output_file}")
        return dashboard


def main():
    """主函数"""
    print("=" * 60)
    print("Self-Evolution Analyzer")
    print("=" * 60)

    analyzer = SelfEvolutionAnalyzer()

    # 1. 加载执行数据
    print("\n[1/5] 加载执行数据...")
    executions = analyzer.load_executions(days=30)

    if not executions:
        print("错误: 没有找到执行数据")
        sys.exit(1)

    # 2. 计算质量分数
    print("\n[2/5] 计算质量分数...")
    executions = analyzer.calculate_quality_scores(executions)

    # 3. 发现模式
    print("\n[3/5] 发现模式...")
    patterns = analyzer.discover_patterns(executions)

    # 4. 优化权重
    print("\n[4/5] 优化权重...")
    weights = analyzer.optimize_weights(executions)

    # 5. 生成仪表板
    print("\n[5/5] 生成仪表板...")
    dashboard = analyzer.generate_dashboard(executions, patterns, weights)

    print("\n" + "=" * 60)
    print("分析完成！")
    print("=" * 60)
    print(f"\n请查看仪表板: {analyzer.reports_dir / 'dashboard.md'}")


if __name__ == "__main__":
    main()
