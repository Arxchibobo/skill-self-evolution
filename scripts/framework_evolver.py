#!/usr/bin/env python3
"""
Framework Evolver - 框架进化器

基于分析结果自动优化 Skill 配置和规则。

核心功能：
1. 配置优化 - 基于性能数据调整配置参数
2. 规则进化 - 发现并更新搜索规则
3. 阈值调整 - 自动调整质量阈值
4. 搜索域优先级 - 优化搜索顺序

Author: Bobo (Self-Evolution Skill)
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import shutil

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


class FrameworkEvolver:
    """框架进化器主类"""

    def __init__(self):
        self.data_dir = PROJECT_ROOT / 'data'
        self.weights_dir = self.data_dir / 'weights'
        self.patterns_dir = self.data_dir / 'patterns'
        self.config_path = PROJECT_ROOT / 'config.yaml'

    def load_latest_weights(self) -> Optional[Dict]:
        """加载最新权重"""
        latest = self.weights_dir / 'latest.json'
        if not latest.exists():
            return None
        with open(latest, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_latest_patterns(self) -> Optional[Dict]:
        """加载最新模式"""
        latest = self.patterns_dir / 'latest.json'
        if not latest.exists():
            return None
        with open(latest, 'r', encoding='utf-8') as f:
            return json.load(f)

    def optimize_search_priority(self, weights: Dict, patterns: Dict) -> List[str]:
        """优化搜索域优先级

        基于权重和成功模式确定最佳搜索顺序
        """
        domain_scores = {}

        # 从成功模式中提取域使用频率
        success_patterns = patterns.get('success_patterns', [])
        for pattern in success_patterns:
            sequence = pattern.get('sequence', [])
            for i, domain in enumerate(sequence):
                if domain not in domain_scores:
                    domain_scores[domain] = 0
                # 早期搜索的域权重更高
                domain_scores[domain] += (len(sequence) - i) * pattern.get('success_rate', 0)

        # 按分数排序
        sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
        optimized_order = [domain for domain, _ in sorted_domains]

        # 确保基本域都包含
        essential_domains = ['product', 'style', 'color', 'typography']
        for domain in essential_domains:
            if domain not in optimized_order:
                optimized_order.append(domain)

        return optimized_order

    def generate_config_recommendations(self, weights: Dict, patterns: Dict) -> Dict[str, Any]:
        """生成配置优化建议"""
        recommendations = {
            'timestamp': datetime.now().isoformat(),
            'config_changes': [],
            'reasoning': []
        }

        # 1. 质量阈值调整
        metadata = weights.get('optimization_metadata', {})
        if metadata.get('total_executions_analyzed', 0) > 50:
            avg_quality = sum(
                weights.get('weights', {}).values()
            ) / len(weights.get('weights', {})) if weights.get('weights') else 0

            if avg_quality > 0.85:
                recommendations['config_changes'].append({
                    'section': 'quality_evaluator.thresholds',
                    'parameter': 'completeness',
                    'current': 0.8,
                    'recommended': 0.85,
                    'reason': 'Overall quality consistently high'
                })

        # 2. 平滑因子调整
        changes = weights.get('changes_since_last_update', {})
        if changes:
            max_change = max(abs(v) for v in changes.values())
            if max_change > 0.15:
                recommendations['config_changes'].append({
                    'section': 'weight_optimizer',
                    'parameter': 'smoothing_factor',
                    'current': 0.3,
                    'recommended': 0.4,
                    'reason': 'High volatility detected, increase smoothing'
                })

        # 3. 搜索域优先级
        optimized_order = self.optimize_search_priority(weights, patterns)
        recommendations['config_changes'].append({
            'section': 'search_strategy',
            'parameter': 'domain_priority',
            'recommended': optimized_order,
            'reason': 'Optimized based on success patterns'
        })

        return recommendations

    def evolve(self, verbose: bool = True, apply: bool = False) -> Dict[str, Any]:
        """执行框架进化

        Args:
            verbose: 详细输出
            apply: 是否自动应用建议

        Returns:
            进化结果
        """
        if verbose:
            print("🧬 Starting framework evolution...")

        # 加载数据
        weights = self.load_latest_weights()
        patterns = self.load_latest_patterns()

        if not weights:
            print("❌ No weights data found")
            return {'status': 'no_data'}

        # 生成建议
        recommendations = self.generate_config_recommendations(weights, patterns or {})

        if verbose:
            print(f"\n📊 Analysis complete!")
            print(f"   Generated {len(recommendations['config_changes'])} recommendations\n")

            for i, change in enumerate(recommendations['config_changes'], 1):
                print(f"{i}. {change['section']}.{change.get('parameter', 'N/A')}")
                if 'current' in change:
                    print(f"   Current: {change['current']}")
                print(f"   Recommended: {change['recommended']}")
                print(f"   Reason: {change['reason']}\n")

        # 保存建议
        output_file = self.data_dir / 'evolution_recommendations.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(recommendations, f, indent=2, ensure_ascii=False)

        if verbose:
            print(f"💾 Recommendations saved to: {output_file}")

        if apply:
            if verbose:
                print("\n⚠️  Auto-apply not implemented yet. Please review and apply manually.")

        return {
            'status': 'success',
            'recommendations': len(recommendations['config_changes']),
            'file': str(output_file)
        }


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='Framework Evolver - 框架进化器')
    parser.add_argument('--apply', action='store_true', help='自动应用建议（实验性）')
    parser.add_argument('--quiet', action='store_true', help='静默模式')

    args = parser.parse_args()

    try:
        evolver = FrameworkEvolver()
        result = evolver.evolve(verbose=not args.quiet, apply=args.apply)

        sys.exit(0 if result['status'] == 'success' else 1)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
