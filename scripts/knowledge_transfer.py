#!/usr/bin/env python3
"""
Knowledge Transfer - 知识迁移器

识别成功模式，并尝试将它们迁移到其他领域/场景。

核心功能：
1. 跨域相似度计算 - 识别相似的产品/场景
2. 模式适配性评估 - 判断模式是否适用于目标域
3. 迁移效果预测 - 预测迁移后的成功率
4. 自动建议生成 - 为新场景提供推荐

算法：
Similarity(A, B) = cosine(feature_vector_A, feature_vector_B)
Transfer_Score = α×Similarity + β×Pattern_Quality + γ×Domain_Compatibility

Author: Bobo (Self-Evolution Skill)
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Set, Optional
from collections import defaultdict
import math

# 添加父目录到路径
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


class KnowledgeTransfer:
    """知识迁移器主类"""

    def __init__(self, similarity_threshold: float = 0.6):
        """初始化知识迁移器

        Args:
            similarity_threshold: 域相似度阈值
        """
        self.similarity_threshold = similarity_threshold
        self.data_dir = PROJECT_ROOT / 'data'
        self.executions_dir = self.data_dir / 'executions'
        self.patterns_dir = self.data_dir / 'patterns'

        # 产品类型特征（用于相似度计算）
        self.domain_features = {
            'saas': {'business': 1.0, 'professional': 0.9, 'clean': 0.8, 'trust': 0.8},
            'ecommerce': {'product': 1.0, 'visual': 0.9, 'conversion': 0.9, 'trust': 0.7},
            'portfolio': {'creative': 1.0, 'visual': 0.9, 'personal': 0.8, 'showcase': 0.8},
            'blog': {'content': 1.0, 'readable': 0.9, 'personal': 0.7, 'simple': 0.8},
            'dashboard': {'data': 1.0, 'functional': 0.9, 'professional': 0.8, 'clean': 0.7},
            'landing': {'conversion': 1.0, 'visual': 0.9, 'marketing': 0.8, 'trust': 0.7},
            'healthcare': {'trust': 1.0, 'professional': 0.9, 'clean': 0.8, 'accessible': 0.9},
            'fintech': {'trust': 1.0, 'professional': 0.9, 'secure': 0.9, 'data': 0.7},
            'education': {'content': 0.9, 'accessible': 1.0, 'clean': 0.8, 'engaging': 0.8},
            'social': {'engaging': 1.0, 'visual': 0.9, 'interactive': 0.9, 'personal': 0.7}
        }

    def load_executions(self, days: int = 90) -> List[Dict]:
        """加载执行记录

        Args:
            days: 加载最近 N 天的数据

        Returns:
            执行记录列表
        """
        executions = []
        cutoff_date = datetime.now() - timedelta(days=days)

        if not self.executions_dir.exists():
            return executions

        for file_path in self.executions_dir.glob('*.json'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    timestamp = datetime.fromisoformat(data.get('timestamp', '').replace('Z', '+00:00'))
                    if timestamp >= cutoff_date:
                        executions.append(data)
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}")

        return executions

    def load_patterns(self) -> Optional[Dict]:
        """加载最新的模式发现结果"""
        latest_pattern_file = self.patterns_dir / 'latest.json'

        if not latest_pattern_file.exists():
            return None

        try:
            with open(latest_pattern_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load patterns: {e}")
            return None

    def calculate_domain_similarity(self, domain_a: str, domain_b: str) -> float:
        """计算两个域的相似度

        使用余弦相似度：sim = dot(A, B) / (||A|| × ||B||)

        Args:
            domain_a: 域 A
            domain_b: 域 B

        Returns:
            相似度分数 (0-1)
        """
        features_a = self.domain_features.get(domain_a.lower())
        features_b = self.domain_features.get(domain_b.lower())

        if not features_a or not features_b:
            # 未知域，返回低相似度
            return 0.3

        # 获取所有特征
        all_features = set(features_a.keys()) | set(features_b.keys())

        # 计算向量
        vec_a = [features_a.get(f, 0.0) for f in all_features]
        vec_b = [features_b.get(f, 0.0) for f in all_features]

        # 计算余弦相似度
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        similarity = dot_product / (norm_a * norm_b)

        return similarity

    def extract_domain_patterns(self, executions: List[Dict]) -> Dict[str, List[Dict]]:
        """提取各域的成功模式

        Args:
            executions: 执行记录列表

        Returns:
            {domain: [pattern, ...]} 字典
        """
        domain_patterns = defaultdict(list)
        quality_threshold = 0.8

        for execution in executions:
            # 提取产品类型（域）
            searches = execution.get('searches_performed', [])
            domain = None

            for search in searches:
                if search.get('domain') == 'product':
                    # 从查询中提取产品类型
                    query = search.get('query', '').lower()
                    for known_domain in self.domain_features.keys():
                        if known_domain in query:
                            domain = known_domain
                            break
                    if domain:
                        break

            if not domain:
                continue

            # 获取质量分数
            quality_scores = execution.get('quality_scores', {})
            overall_quality = quality_scores.get('overall', 0.0)

            # 只保留高质量的执行
            if overall_quality >= quality_threshold:
                pattern = {
                    'session_id': execution.get('session_id'),
                    'quality': overall_quality,
                    'elements': execution.get('elements_used', {}),
                    'searches': searches
                }
                domain_patterns[domain].append(pattern)

        return domain_patterns

    def identify_transferable_patterns(self, domain_patterns: Dict[str, List[Dict]]) -> List[Dict]:
        """识别可迁移的模式

        Args:
            domain_patterns: 各域的模式

        Returns:
            可迁移模式列表
        """
        transferable = []

        # 遍历所有源域-目标域对
        domains = list(domain_patterns.keys())

        for source_domain in domains:
            for target_domain in domains:
                if source_domain == target_domain:
                    continue

                # 计算域相似度
                similarity = self.calculate_domain_similarity(source_domain, target_domain)

                if similarity < self.similarity_threshold:
                    continue

                # 提取源域的成功模式
                source_patterns = domain_patterns[source_domain]

                if not source_patterns:
                    continue

                # 计算平均质量
                avg_quality = sum(p['quality'] for p in source_patterns) / len(source_patterns)

                # 提取常用元素
                element_counts = defaultdict(int)
                for pattern in source_patterns:
                    for category, items in pattern['elements'].items():
                        for item in items:
                            element_counts[f"{category}:{item}"] += 1

                # 保留高频元素（至少出现在 30% 的模式中）
                min_count = max(1, len(source_patterns) * 0.3)
                transferred_elements = [
                    elem for elem, count in element_counts.items()
                    if count >= min_count
                ]

                if transferred_elements:
                    transferable.append({
                        'source_domain': source_domain,
                        'target_domain': target_domain,
                        'similarity_score': round(similarity, 3),
                        'transferred_patterns': transferred_elements[:5],  # Top 5
                        'success_rate': round(avg_quality, 3),
                        'sample_size': len(source_patterns),
                        'confidence': round(similarity * avg_quality, 3)
                    })

        # 按置信度排序
        transferable.sort(key=lambda x: x['confidence'], reverse=True)

        return transferable

    def generate_recommendations(self, target_domain: str,
                                 transferable_patterns: List[Dict]) -> List[Dict]:
        """为目标域生成推荐

        Args:
            target_domain: 目标域
            transferable_patterns: 可迁移模式

        Returns:
            推荐列表
        """
        recommendations = []

        # 筛选适用于目标域的模式
        applicable = [
            p for p in transferable_patterns
            if p['target_domain'] == target_domain
        ]

        for pattern in applicable[:5]:  # Top 5
            recommendation = {
                'from_domain': pattern['source_domain'],
                'recommended_elements': pattern['transferred_patterns'],
                'confidence': pattern['confidence'],
                'rationale': f"This pattern worked well in {pattern['source_domain']} "
                            f"(success rate: {pattern['success_rate']:.1%}) and has "
                            f"{pattern['similarity_score']:.1%} similarity to {target_domain}"
            }
            recommendations.append(recommendation)

        return recommendations

    def transfer(self, days: int = 90, verbose: bool = True) -> Dict[str, Any]:
        """执行知识迁移分析

        Args:
            days: 分析最近 N 天的数据
            verbose: 是否打印详细信息

        Returns:
            迁移结果
        """
        if verbose:
            print(f"🔄 Starting knowledge transfer analysis (analyzing last {days} days)...")

        # 1. 加载数据
        executions = self.load_executions(days)

        if not executions:
            print("❌ No execution data found. Skipping knowledge transfer.")
            return {'status': 'no_data'}

        if verbose:
            print(f"   Loaded {len(executions)} executions")

        # 2. 提取域模式
        if verbose:
            print("📊 Extracting domain patterns...")

        domain_patterns = self.extract_domain_patterns(executions)

        if verbose:
            print(f"   Found patterns in {len(domain_patterns)} domains")
            for domain, patterns in domain_patterns.items():
                print(f"      {domain}: {len(patterns)} patterns")

        # 3. 识别可迁移模式
        if verbose:
            print("🎯 Identifying transferable patterns...")

        transferable = self.identify_transferable_patterns(domain_patterns)

        if verbose:
            print(f"   Found {len(transferable)} transferable patterns")

        # 4. 生成推荐（示例：为每个目标域）
        recommendations_by_domain = {}

        for domain in self.domain_features.keys():
            recs = self.generate_recommendations(domain, transferable)
            if recs:
                recommendations_by_domain[domain] = recs

        # 5. 保存结果
        result = {
            'generated_at': datetime.now().isoformat(),
            'analysis_period_days': days,
            'cross_domain_transfers': transferable[:20],  # Top 20
            'recommendations_by_domain': recommendations_by_domain,
            'statistics': {
                'total_executions': len(executions),
                'domains_analyzed': len(domain_patterns),
                'transferable_patterns': len(transferable)
            }
        }

        # 保存到 patterns 目录
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'knowledge_transfer_{timestamp}.json'
        filepath = self.patterns_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        if verbose:
            print(f"✅ Knowledge transfer analysis complete! Saved to: {filepath}")

        return {
            'status': 'success',
            'file_path': str(filepath),
            'transferable_patterns': len(transferable),
            'domains_analyzed': len(domain_patterns)
        }


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Knowledge Transfer - 跨域知识迁移分析',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分析最近 90 天数据
  python knowledge_transfer.py

  # 调整相似度阈值
  python knowledge_transfer.py --similarity 0.7
        """
    )

    parser.add_argument(
        '--days',
        type=int,
        default=90,
        help='分析最近 N 天的数据 (默认: 90)'
    )

    parser.add_argument(
        '--similarity',
        type=float,
        default=0.6,
        help='域相似度阈值 (0-1, 默认: 0.6)'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='静默模式'
    )

    args = parser.parse_args()

    try:
        transfer = KnowledgeTransfer(similarity_threshold=args.similarity)

        result = transfer.transfer(
            days=args.days,
            verbose=not args.quiet
        )

        if result['status'] == 'success':
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
