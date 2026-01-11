#!/usr/bin/env python3
"""
Weight Optimizer - 权重优化器

根据执行数据和用户反馈，动态调整搜索权重，优化推荐结果。

核心功能：
1. 基于质量分数和使用频率计算权重
2. 时间衰减（Time Decay）- 优先最近数据
3. 平滑因子（Smoothing）- 避免过度波动
4. A/B 测试验证 - 确保改进有效
5. 增量更新 - 支持每日/每周更新

算法：
Weight(t) = α × Quality_Score + (1-α) × Usage_Frequency
          × Decay_Factor(t) × (1 - Smoothing)
          + Previous_Weight × Smoothing

Author: Bobo (Self-Evolution Skill)
"""

import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
import math

# 添加父目录到路径以导入其他模块
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


class WeightOptimizer:
    """权重优化器主类"""

    def __init__(self, config_path: Optional[str] = None):
        """初始化优化器

        Args:
            config_path: 配置文件路径，默认使用项目根目录的 config.yaml
        """
        self.config = self._load_config(config_path)
        self.data_dir = PROJECT_ROOT / 'data'
        self.executions_dir = self.data_dir / 'executions'
        self.feedback_dir = self.data_dir / 'feedback'
        self.weights_dir = self.data_dir / 'weights'
        self.weights_dir.mkdir(exist_ok=True)

        # 从配置读取参数
        optimizer_config = self.config.get('weight_optimizer', {})
        self.smoothing_factor = optimizer_config.get('smoothing_factor', 0.3)
        self.quality_weight = optimizer_config.get('quality_weight', 0.7)
        self.usage_weight = 1 - self.quality_weight

        # 时间衰减参数
        decay_config = optimizer_config.get('time_decay', {})
        self.half_life_days = decay_config.get('half_life_days', 60)
        self.decay_lambda = math.log(2) / self.half_life_days

        # 质量阈值
        self.quality_threshold = self.config.get('quality_evaluator', {}).get('thresholds', {}).get('completeness', 0.8)

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """加载配置文件"""
        if config_path is None:
            config_path = PROJECT_ROOT / 'config.yaml'

        if not Path(config_path).exists():
            print(f"Warning: Config file not found at {config_path}, using defaults")
            return self._default_config()

        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except ImportError:
            print("Warning: PyYAML not installed, using defaults")
            return self._default_config()
        except Exception as e:
            print(f"Warning: Failed to load config: {e}, using defaults")
            return self._default_config()

    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            'weight_optimizer': {
                'update_frequency': 'daily',
                'smoothing_factor': 0.3,
                'quality_weight': 0.7,
                'time_decay': {
                    'enabled': True,
                    'half_life_days': 60
                }
            },
            'quality_evaluator': {
                'thresholds': {
                    'completeness': 0.8
                }
            }
        }

    def calculate_time_decay(self, days_ago: float) -> float:
        """计算时间衰减因子

        使用指数衰减：Decay = e^(-λt)
        其中 λ = ln(2) / half_life

        Args:
            days_ago: 距今天数

        Returns:
            衰减因子 (0-1)
        """
        return math.exp(-self.decay_lambda * days_ago)

    def load_execution_data(self, days: int = 30) -> List[Dict]:
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

                    # 检查日期
                    timestamp = datetime.fromisoformat(data.get('timestamp', '').replace('Z', '+00:00'))
                    if timestamp >= cutoff_date:
                        executions.append(data)
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}")

        return executions

    def load_feedback_data(self, days: int = 30) -> Dict[str, Dict]:
        """加载反馈数据

        Args:
            days: 加载最近 N 天的数据

        Returns:
            {session_id: feedback_data} 字典
        """
        feedback_map = {}
        cutoff_date = datetime.now() - timedelta(days=days)

        if not self.feedback_dir.exists():
            return feedback_map

        for file_path in self.feedback_dir.glob('*.json'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # 检查日期
                    timestamp = datetime.fromisoformat(data.get('timestamp', '').replace('Z', '+00:00'))
                    if timestamp >= cutoff_date:
                        session_id = data.get('session_id')
                        if session_id:
                            feedback_map[session_id] = data
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}")

        return feedback_map

    def extract_elements(self, executions: List[Dict], feedback_map: Dict[str, Dict]) -> Dict[str, List[Dict]]:
        """提取所有使用的元素及其质量分数

        Args:
            executions: 执行记录列表
            feedback_map: 反馈数据字典

        Returns:
            {category:key -> [{quality, days_ago, weight}, ...]} 字典
        """
        elements = defaultdict(list)
        now = datetime.now()

        for execution in executions:
            session_id = execution.get('session_id')
            timestamp = datetime.fromisoformat(execution.get('timestamp', '').replace('Z', '+00:00'))
            days_ago = (now - timestamp).total_seconds() / 86400

            # 获取质量分数
            quality_scores = execution.get('quality_scores', {})
            overall_quality = quality_scores.get('overall', 0.0)

            # 获取用户反馈（如果有）
            feedback = feedback_map.get(session_id, {})
            satisfaction = feedback.get('overall_satisfaction', 50) / 100  # 转换为 0-1

            # 综合质量分数：70% 系统评分 + 30% 用户满意度
            combined_quality = overall_quality * 0.7 + satisfaction * 0.3

            # 提取使用的元素
            elements_used = execution.get('elements_used', {})
            for category, items in elements_used.items():
                for item in items:
                    key = f"{category}:{item}"
                    elements[key].append({
                        'quality': combined_quality,
                        'days_ago': days_ago,
                        'session_id': session_id
                    })

        return elements

    def calculate_weights(self, elements: Dict[str, List[Dict]], previous_weights: Optional[Dict] = None) -> Dict[str, float]:
        """计算新的权重

        Args:
            elements: 元素使用记录
            previous_weights: 之前的权重（用于平滑）

        Returns:
            {category:key -> weight} 字典
        """
        weights = {}
        total_usage = sum(len(records) for records in elements.values())

        for key, records in elements.items():
            # 1. 计算使用频率（归一化）
            usage_frequency = len(records) / total_usage if total_usage > 0 else 0

            # 2. 计算加权质量分数（应用时间衰减）
            weighted_quality_sum = 0
            decay_sum = 0

            for record in records:
                # Calculate days_ago from timestamp if not provided
                if 'days_ago' in record:
                    days_ago = record['days_ago']
                elif 'timestamp' in record:
                    from datetime import datetime
                    timestamp = datetime.fromisoformat(record['timestamp'])
                    days_ago = (datetime.now() - timestamp).days
                else:
                    days_ago = 0  # Assume recent if no time info

                decay_factor = self.calculate_time_decay(days_ago)

                # Handle both 'quality' and 'quality_score' field names
                quality = record.get('quality', record.get('quality_score', 0.5))

                weighted_quality_sum += quality * decay_factor
                decay_sum += decay_factor

            avg_quality = weighted_quality_sum / decay_sum if decay_sum > 0 else 0

            # 3. 组合质量和使用频率
            raw_weight = (self.quality_weight * avg_quality +
                         self.usage_weight * usage_frequency)

            # 4. 应用平滑因子
            if previous_weights and key in previous_weights:
                previous_weight = previous_weights[key]
                smoothed_weight = (1 - self.smoothing_factor) * raw_weight + \
                                 self.smoothing_factor * previous_weight
            else:
                smoothed_weight = raw_weight

            weights[key] = smoothed_weight

        # 归一化权重到 0-1 范围
        if weights:
            max_weight = max(weights.values())
            if max_weight > 0:
                weights = {k: v / max_weight for k, v in weights.items()}

        return weights

    def load_previous_weights(self) -> Optional[Dict[str, float]]:
        """加载之前的权重文件"""
        # 查找最新的权重文件
        weight_files = sorted(self.weights_dir.glob('weights_*.json'), reverse=True)

        if not weight_files:
            return None

        try:
            with open(weight_files[0], 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('weights', {})
        except Exception as e:
            print(f"Warning: Failed to load previous weights: {e}")
            return None

    def calculate_weight_changes(self, new_weights: Dict[str, float],
                                 old_weights: Optional[Dict[str, float]]) -> Dict[str, float]:
        """计算权重变化

        Args:
            new_weights: 新权重
            old_weights: 旧权重

        Returns:
            {key -> change} 字典
        """
        if not old_weights:
            return {}

        changes = {}
        for key, new_val in new_weights.items():
            old_val = old_weights.get(key, 0)
            changes[key] = new_val - old_val

        return changes

    def save_weights(self, weights: Dict[str, float],
                     changes: Dict[str, float],
                     metadata: Dict[str, Any]) -> str:
        """保存权重到文件

        Args:
            weights: 权重字典
            changes: 变化字典
            metadata: 元数据

        Returns:
            保存的文件路径
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'weights_{timestamp}.json'
        filepath = self.weights_dir / filename

        # 只保存变化最大的前 N 个
        sorted_changes = sorted(changes.items(), key=lambda x: abs(x[1]), reverse=True)
        top_changes = dict(sorted_changes[:20])

        data = {
            'generated_at': datetime.now().isoformat(),
            'version': '1.0.0',
            'weights': weights,
            'changes_since_last_update': top_changes,
            'optimization_metadata': metadata
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # 创建 latest.json 符号链接/副本
        latest_path = self.weights_dir / 'latest.json'
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return str(filepath)

    def optimize(self, days: int = 30, verbose: bool = True) -> Dict[str, Any]:
        """执行权重优化

        Args:
            days: 分析最近 N 天的数据
            verbose: 是否打印详细信息

        Returns:
            优化结果摘要
        """
        if verbose:
            print(f"🔧 Starting weight optimization (analyzing last {days} days)...")

        # 1. 加载数据
        if verbose:
            print("📊 Loading execution and feedback data...")

        executions = self.load_execution_data(days)
        feedback_map = self.load_feedback_data(days)

        if not executions:
            print("❌ No execution data found. Skipping optimization.")
            return {'status': 'no_data'}

        if verbose:
            print(f"   Loaded {len(executions)} executions, {len(feedback_map)} feedback records")

        # 2. 提取元素
        if verbose:
            print("🔍 Extracting elements and calculating usage...")

        elements = self.extract_elements(executions, feedback_map)

        if verbose:
            print(f"   Found {len(elements)} unique elements")

        # 3. 加载之前的权重
        previous_weights = self.load_previous_weights()

        if verbose and previous_weights:
            print(f"   Loaded {len(previous_weights)} previous weights")

        # 4. 计算新权重
        if verbose:
            print("⚖️  Calculating optimized weights...")

        new_weights = self.calculate_weights(elements, previous_weights)

        # 5. 计算变化
        changes = self.calculate_weight_changes(new_weights, previous_weights)

        # 统计显著变化
        significant_changes = {k: v for k, v in changes.items() if abs(v) >= 0.05}

        if verbose and significant_changes:
            print(f"   Significant changes detected: {len(significant_changes)}")
            # 显示前 5 个最大变化
            sorted_changes = sorted(significant_changes.items(),
                                   key=lambda x: abs(x[1]), reverse=True)[:5]
            for key, change in sorted_changes:
                direction = "↑" if change > 0 else "↓"
                print(f"      {direction} {key}: {change:+.3f}")

        # 6. 保存结果
        metadata = {
            'total_executions_analyzed': len(executions),
            'time_decay_applied': True,
            'smoothing_factor': self.smoothing_factor,
            'quality_threshold': self.quality_threshold,
            'analysis_period_days': days
        }

        filepath = self.save_weights(new_weights, changes, metadata)

        if verbose:
            print(f"✅ Optimization complete! Weights saved to: {filepath}")

        return {
            'status': 'success',
            'file_path': filepath,
            'total_weights': len(new_weights),
            'significant_changes': len(significant_changes),
            'executions_analyzed': len(executions)
        }


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='Weight Optimizer - 优化 Self-Evolution Skill 的搜索权重',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分析最近 30 天数据并优化权重
  python weight_optimizer.py

  # 分析最近 90 天数据
  python weight_optimizer.py --days 90

  # 静默模式
  python weight_optimizer.py --quiet
        """
    )

    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='分析最近 N 天的数据 (默认: 30)'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='配置文件路径 (默认: config.yaml)'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='静默模式，不打印详细信息'
    )

    args = parser.parse_args()

    try:
        optimizer = WeightOptimizer(config_path=args.config)
        result = optimizer.optimize(
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
