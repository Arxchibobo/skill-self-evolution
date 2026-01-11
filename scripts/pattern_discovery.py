#!/usr/bin/env python3
"""
Pattern Discovery - 模式发现器

使用 Apriori 算法发现元素的频繁组合模式，识别成功和失败的模式。

核心功能：
1. 频繁项集挖掘 - 发现高频元素组合
2. 成功模式识别 - 识别导致高质量输出的模式
3. 失败模式识别 - 识别应避免的反模式
4. 关联规则生成 - A => B 类型的规则
5. 跨域模式迁移 - 识别可迁移的模式

算法：
Apriori: L_k = {c ∈ C_k | support(c) ≥ min_support}
其中 C_k = apriori_gen(L_{k-1})

Author: Bobo (Self-Evolution Skill)
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict, Counter
from itertools import combinations

# 添加父目录到路径
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


class PatternDiscovery:
    """模式发现器主类"""

    def __init__(self, min_support: float = 0.1, min_confidence: float = 0.7,
                 quality_threshold: float = 0.8):
        """初始化模式发现器

        Args:
            min_support: 最小支持度（0-1）
            min_confidence: 最小置信度（0-1）
            quality_threshold: 质量分数阈值
        """
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.quality_threshold = quality_threshold

        self.data_dir = PROJECT_ROOT / 'data'
        self.executions_dir = self.data_dir / 'executions'
        self.patterns_dir = self.data_dir / 'patterns'
        self.patterns_dir.mkdir(exist_ok=True)

    def load_executions(self, days: int = 30) -> List[Dict]:
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

    def extract_transactions(self, executions: List[Dict]) -> List[Tuple[Set[str], float, Dict]]:
        """提取事务（每个执行记录作为一个事务）

        Args:
            executions: 执行记录列表

        Returns:
            [(itemset, quality_score, metadata), ...] 列表
        """
        transactions = []

        for execution in executions:
            # 提取使用的元素
            items = set()
            elements_used = execution.get('elements_used', {})

            for category, values in elements_used.items():
                for value in values:
                    # 简化形式：只保留值，不带分类前缀
                    items.add(value)

            # 获取质量分数
            quality_scores = execution.get('quality_scores', {})
            overall_quality = quality_scores.get('overall', 0.0)

            # 元数据
            metadata = {
                'session_id': execution.get('session_id'),
                'skill_name': execution.get('skill_name'),
                'timestamp': execution.get('timestamp'),
                'searches': execution.get('searches_performed', [])
            }

            transactions.append((items, overall_quality, metadata))

        return transactions

    def find_frequent_itemsets(self, transactions: List[Tuple[Set[str], float, Dict]],
                               max_length: int = 3) -> Dict[int, List[Tuple[frozenset, int]]]:
        """使用 Apriori 算法查找频繁项集

        Args:
            transactions: 事务列表
            max_length: 最大项集长度

        Returns:
            {length: [(itemset, support_count), ...]} 字典
        """
        # 提取项集（忽略质量分数）
        itemsets = [itemset for itemset, _, _ in transactions]
        n_transactions = len(itemsets)

        # 最小支持计数
        min_support_count = int(self.min_support * n_transactions)

        # L1: 单项频繁集
        item_counts = Counter()
        for itemset in itemsets:
            for item in itemset:
                item_counts[item] += 1

        L1 = [(frozenset([item]), count) for item, count in item_counts.items()
              if count >= min_support_count]

        # 存储所有频繁项集
        all_frequent = {1: L1}

        # 生成 L2, L3, ... Lk
        current_L = L1
        k = 2

        while current_L and k <= max_length:
            # 生成候选集 Ck
            candidates = self._apriori_gen(current_L, k)

            # 计数
            candidate_counts = defaultdict(int)
            for itemset in itemsets:
                for candidate in candidates:
                    if candidate.issubset(itemset):
                        candidate_counts[candidate] += 1

            # 过滤：保留频繁项集
            current_L = [(itemset, count) for itemset, count in candidate_counts.items()
                        if count >= min_support_count]

            if current_L:
                all_frequent[k] = current_L

            k += 1

        return all_frequent

    def _apriori_gen(self, L_prev: List[Tuple[frozenset, int]], k: int) -> Set[frozenset]:
        """Apriori 候选生成函数

        从 L_{k-1} 生成 C_k

        Args:
            L_prev: L_{k-1} 频繁项集
            k: 目标长度

        Returns:
            C_k 候选集
        """
        candidates = set()
        items = [itemset for itemset, _ in L_prev]

        # 连接步骤：L_{k-1} × L_{k-1}
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                # 合并两个项集
                union = items[i] | items[j]

                # 如果合并后长度为 k，添加到候选集
                if len(union) == k:
                    candidates.add(union)

        # 剪枝步骤：删除包含非频繁子集的候选
        pruned_candidates = set()
        frequent_subsets = set(items)

        for candidate in candidates:
            # 检查所有 k-1 子集是否都频繁
            subsets = [frozenset(s) for s in combinations(candidate, k - 1)]
            if all(subset in frequent_subsets for subset in subsets):
                pruned_candidates.add(candidate)

        return pruned_candidates

    def identify_success_patterns(self, transactions: List[Tuple[Set[str], float, Dict]],
                                   frequent_itemsets: Dict[int, List[Tuple[frozenset, int]]]) -> List[Dict]:
        """识别成功模式

        Args:
            transactions: 事务列表
            frequent_itemsets: 频繁项集

        Returns:
            成功模式列表
        """
        success_patterns = []
        n_transactions = len(transactions)

        # 遍历所有频繁项集
        for length, itemsets in frequent_itemsets.items():
            for itemset, count in itemsets:
                # 计算包含该项集的事务的平均质量分数
                matching_transactions = [
                    (quality, metadata)
                    for items, quality, metadata in transactions
                    if itemset.issubset(items)
                ]

                if not matching_transactions:
                    continue

                avg_quality = sum(q for q, _ in matching_transactions) / len(matching_transactions)

                # 如果平均质量高于阈值，识别为成功模式
                if avg_quality >= self.quality_threshold:
                    pattern = {
                        'items': list(itemset),
                        'support': count / n_transactions,
                        'occurrence_count': count,
                        'avg_quality_score': round(avg_quality, 3),
                        'confidence': len(matching_transactions) / count if count > 0 else 0,
                        'sample_sessions': [m['session_id'] for _, m in matching_transactions[:3]]
                    }
                    success_patterns.append(pattern)

        # 按平均质量分数排序
        success_patterns.sort(key=lambda x: x['avg_quality_score'], reverse=True)

        return success_patterns

    def identify_failure_patterns(self, transactions: List[Tuple[Set[str], float, Dict]],
                                   frequent_itemsets: Dict[int, List[Tuple[frozenset, int]]]) -> List[Dict]:
        """识别失败模式（反模式）

        Args:
            transactions: 事务列表
            frequent_itemsets: 频繁项集

        Returns:
            失败模式列表
        """
        failure_patterns = []
        n_transactions = len(transactions)
        failure_threshold = 0.6  # 低于此分数视为失败

        # 遍历所有频繁项集
        for length, itemsets in frequent_itemsets.items():
            for itemset, count in itemsets:
                # 计算包含该项集的事务
                matching_transactions = [
                    (quality, metadata)
                    for items, quality, metadata in transactions
                    if itemset.issubset(items)
                ]

                if not matching_transactions:
                    continue

                avg_quality = sum(q for q, _ in matching_transactions) / len(matching_transactions)

                # 如果平均质量低于失败阈值，识别为失败模式
                if avg_quality < failure_threshold:
                    pattern = {
                        'pattern_type': 'anti_pattern',
                        'elements': list(itemset),
                        'failure_rate': 1 - avg_quality,
                        'avg_quality_score': round(avg_quality, 3),
                        'sample_size': len(matching_transactions)
                    }
                    failure_patterns.append(pattern)

        # 按失败率排序
        failure_patterns.sort(key=lambda x: x['failure_rate'], reverse=True)

        return failure_patterns

    def identify_search_sequences(self, transactions: List[Tuple[Set[str], float, Dict]]) -> List[Dict]:
        """识别成功的搜索序列模式

        Args:
            transactions: 事务列表

        Returns:
            搜索序列模式列表
        """
        sequence_patterns = defaultdict(lambda: {'qualities': [], 'count': 0})

        for items, quality, metadata in transactions:
            searches = metadata.get('searches', [])
            if not searches:
                continue

            # 提取搜索域序列
            sequence = tuple([s.get('domain') for s in searches if s.get('domain')])

            if sequence:
                sequence_patterns[sequence]['qualities'].append(quality)
                sequence_patterns[sequence]['count'] += 1

        # 转换为列表格式
        patterns = []
        for sequence, data in sequence_patterns.items():
            if data['count'] >= 3:  # 至少出现 3 次
                avg_quality = sum(data['qualities']) / len(data['qualities'])
                success_rate = sum(1 for q in data['qualities'] if q >= self.quality_threshold) / len(data['qualities'])

                if success_rate >= 0.7:  # 70% 成功率
                    patterns.append({
                        'pattern_type': 'search_sequence',
                        'sequence': list(sequence),
                        'success_rate': round(success_rate, 3),
                        'avg_quality_score': round(avg_quality, 3),
                        'sample_size': data['count']
                    })

        # 按成功率排序
        patterns.sort(key=lambda x: x['success_rate'], reverse=True)

        return patterns

    def discover(self, days: int = 30, verbose: bool = True) -> Dict[str, Any]:
        """执行模式发现

        Args:
            days: 分析最近 N 天的数据
            verbose: 是否打印详细信息

        Returns:
            发现结果摘要
        """
        if verbose:
            print(f"🔍 Starting pattern discovery (analyzing last {days} days)...")

        # 1. 加载数据
        executions = self.load_executions(days)

        if not executions:
            print("❌ No execution data found. Skipping pattern discovery.")
            return {'status': 'no_data'}

        if verbose:
            print(f"   Loaded {len(executions)} executions")

        # 2. 提取事务
        transactions = self.extract_transactions(executions)

        if verbose:
            print(f"   Extracted {len(transactions)} transactions")

        # 3. 查找频繁项集
        if verbose:
            print("📊 Finding frequent itemsets...")

        frequent_itemsets = self.find_frequent_itemsets(transactions, max_length=3)

        total_frequent = sum(len(itemsets) for itemsets in frequent_itemsets.values())
        if verbose:
            print(f"   Found {total_frequent} frequent itemsets")

        # 4. 识别成功模式
        if verbose:
            print("✅ Identifying success patterns...")

        success_patterns = self.identify_success_patterns(transactions, frequent_itemsets)

        if verbose:
            print(f"   Found {len(success_patterns)} success patterns")

        # 5. 识别失败模式
        if verbose:
            print("⚠️  Identifying failure patterns...")

        failure_patterns = self.identify_failure_patterns(transactions, frequent_itemsets)

        if verbose:
            print(f"   Found {len(failure_patterns)} failure patterns")

        # 6. 识别搜索序列
        if verbose:
            print("🔄 Identifying search sequence patterns...")

        search_sequences = self.identify_search_sequences(transactions)

        if verbose:
            print(f"   Found {len(search_sequences)} search sequence patterns")

        # 7. 保存结果
        result = {
            'generated_at': datetime.now().isoformat(),
            'period': {
                'start_date': (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
                'end_date': datetime.now().strftime('%Y-%m-%d'),
                'days': days
            },
            'frequent_combinations': success_patterns[:10],  # Top 10
            'success_patterns': search_sequences[:5],  # Top 5
            'failure_patterns': failure_patterns[:5],  # Top 5
            'statistics': {
                'total_executions': len(executions),
                'total_frequent_itemsets': total_frequent,
                'success_patterns_count': len(success_patterns),
                'failure_patterns_count': len(failure_patterns),
                'search_sequence_patterns': len(search_sequences)
            }
        }

        # 保存到文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'patterns_{timestamp}.json'
        filepath = self.patterns_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        # 创建 latest.json
        latest_path = self.patterns_dir / 'latest.json'
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        if verbose:
            print(f"✅ Pattern discovery complete! Saved to: {filepath}")

        return {
            'status': 'success',
            'file_path': str(filepath),
            'success_patterns': len(success_patterns),
            'failure_patterns': len(failure_patterns)
        }


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Pattern Discovery - 发现 Self-Evolution Skill 的使用模式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分析最近 30 天数据
  python pattern_discovery.py

  # 分析最近 90 天数据
  python pattern_discovery.py --days 90

  # 调整支持度和置信度
  python pattern_discovery.py --min-support 0.15 --min-confidence 0.8
        """
    )

    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='分析最近 N 天的数据 (默认: 30)'
    )

    parser.add_argument(
        '--min-support',
        type=float,
        default=0.1,
        help='最小支持度 (0-1, 默认: 0.1)'
    )

    parser.add_argument(
        '--min-confidence',
        type=float,
        default=0.7,
        help='最小置信度 (0-1, 默认: 0.7)'
    )

    parser.add_argument(
        '--quality-threshold',
        type=float,
        default=0.8,
        help='质量分数阈值 (0-1, 默认: 0.8)'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='静默模式'
    )

    args = parser.parse_args()

    try:
        discovery = PatternDiscovery(
            min_support=args.min_support,
            min_confidence=args.min_confidence,
            quality_threshold=args.quality_threshold
        )

        result = discovery.discover(
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
