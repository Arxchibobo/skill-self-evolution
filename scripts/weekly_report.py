#!/usr/bin/env python3
"""
Self-Evolution Skill - 周报生成工具

生成每周进化报告，展示质量趋势、发现的模式、权重变化等。

用法:
    python weekly_report.py                    # 生成上周报告
    python weekly_report.py --weeks 4          # 生成最近 4 周报告
    python weekly_report.py --output weekly.md # 指定输出文件

输出:
    - 周报 Markdown 文件
    - 可选：发送到 Slack/Email
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
import pandas as pd

# 项目路径
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / 'data'
REPORTS_DIR = SKILL_DIR / 'reports'


def main():
    parser = argparse.ArgumentParser(description='Self-Evolution Skill 周报生成工具')
    parser.add_argument('--weeks', type=int, default=1,
                        help='生成最近 N 周的报告（默认: 1）')
    parser.add_argument('--output', type=str,
                        help='输出文件路径（默认: reports/weekly_YYYYMMDD.md）')
    parser.add_argument('--format', choices=['markdown', 'html', 'json'],
                        default='markdown', help='输出格式')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='显示详细信息')

    args = parser.parse_args()

    # 确保报告目录存在
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # 生成报告
        report = generate_weekly_report(weeks=args.weeks, verbose=args.verbose)

        # 确定输出文件
        if args.output:
            output_file = Path(args.output)
        else:
            date_str = datetime.now().strftime('%Y%m%d')
            output_file = REPORTS_DIR / f"weekly_{date_str}.md"

        # 保存报告
        if args.format == 'markdown':
            save_markdown_report(report, output_file)
        elif args.format == 'html':
            save_html_report(report, output_file.with_suffix('.html'))
        elif args.format == 'json':
            save_json_report(report, output_file.with_suffix('.json'))

        print(f"✓ 周报已生成: {output_file}")

    except Exception as e:
        print(f"✗ 生成报告失败: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def generate_weekly_report(weeks: int, verbose: bool) -> Dict[str, Any]:
    """
    生成周报数据

    Args:
        weeks: 报告周数
        verbose: 是否显示详细信息

    Returns:
        报告数据字典
    """
    if verbose:
        print(f"[1/5] 加载执行数据...")
    executions = load_weekly_executions(weeks)

    if verbose:
        print(f"[2/5] 计算质量指标...")
    quality_metrics = calculate_quality_metrics(executions)

    if verbose:
        print(f"[3/5] 分析模式...")
    patterns = analyze_patterns(executions)

    if verbose:
        print(f"[4/5] 检查权重变化...")
    weights = analyze_weight_changes(weeks)

    if verbose:
        print(f"[5/5] 生成摘要...")
    summary = generate_summary(executions, quality_metrics, patterns, weights)

    return {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'period': {
                'weeks': weeks,
                'start_date': (datetime.now() - timedelta(weeks=weeks)).strftime('%Y-%m-%d'),
                'end_date': datetime.now().strftime('%Y-%m-%d')
            }
        },
        'summary': summary,
        'quality_metrics': quality_metrics,
        'patterns': patterns,
        'weights': weights,
        'executions_count': len(executions)
    }


def load_weekly_executions(weeks: int) -> List[Dict[str, Any]]:
    """
    加载最近 N 周的执行数据

    Args:
        weeks: 周数

    Returns:
        执行记录列表
    """
    cutoff_date = datetime.now() - timedelta(weeks=weeks)
    executions = []

    exec_dir = DATA_DIR / 'executions'
    if not exec_dir.exists():
        return []

    for file_path in exec_dir.glob('*.json'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                exec_date = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))

                if exec_date >= cutoff_date:
                    executions.append(data)
        except Exception:
            continue

    return executions


def calculate_quality_metrics(executions: List[Dict]) -> Dict[str, Any]:
    """
    计算质量指标

    Args:
        executions: 执行记录列表

    Returns:
        质量指标字典
    """
    if not executions:
        return {
            'overall_score': 0,
            'completeness': 0,
            'consistency': 0,
            'professionalism': 0,
            'trend': 'stable'
        }

    # 按时间排序
    sorted_execs = sorted(executions, key=lambda x: x['timestamp'])

    # 计算各维度平均分
    scores = {
        'completeness': [],
        'consistency': [],
        'professionalism': []
    }

    for exec_data in sorted_execs:
        if 'quality_score' in exec_data:
            for dimension in scores.keys():
                if dimension in exec_data['quality_score']:
                    scores[dimension].append(exec_data['quality_score'][dimension])

    # 计算平均值
    avg_scores = {}
    for dimension, values in scores.items():
        avg_scores[dimension] = np.mean(values) if values else 0

    # 计算整体分数
    overall_score = np.mean(list(avg_scores.values()))

    # 计算趋势（比较前半周期和后半周期）
    trend = calculate_trend(sorted_execs)

    return {
        'overall_score': round(overall_score, 2),
        'completeness': round(avg_scores['completeness'], 2),
        'consistency': round(avg_scores['consistency'], 2),
        'professionalism': round(avg_scores['professionalism'], 2),
        'trend': trend,
        'sample_size': len(sorted_execs)
    }


def calculate_trend(executions: List[Dict]) -> str:
    """
    计算质量趋势

    Args:
        executions: 执行记录列表（已排序）

    Returns:
        趋势描述：'improving', 'declining', 'stable'
    """
    if len(executions) < 10:
        return 'stable'  # 数据太少，无法判断趋势

    mid_point = len(executions) // 2
    first_half = executions[:mid_point]
    second_half = executions[mid_point:]

    # 计算两半的平均质量分数
    def avg_quality(execs):
        scores = []
        for e in execs:
            if 'quality_score' in e and 'overall' in e['quality_score']:
                scores.append(e['quality_score']['overall'])
        return np.mean(scores) if scores else 0

    first_avg = avg_quality(first_half)
    second_avg = avg_quality(second_half)

    diff = second_avg - first_avg

    if diff > 0.05:  # 提升超过 5%
        return 'improving'
    elif diff < -0.05:  # 下降超过 5%
        return 'declining'
    else:
        return 'stable'


def analyze_patterns(executions: List[Dict]) -> Dict[str, Any]:
    """
    分析发现的模式

    Args:
        executions: 执行记录列表

    Returns:
        模式分析结果
    """
    # 加载最新的模式文件
    patterns_dir = DATA_DIR / 'patterns'
    if not patterns_dir.exists():
        return {'frequent_combinations': [], 'success_patterns': []}

    latest_pattern_file = get_latest_file(patterns_dir, '*.json')
    if not latest_pattern_file:
        return {'frequent_combinations': [], 'success_patterns': []}

    try:
        with open(latest_pattern_file, 'r', encoding='utf-8') as f:
            patterns = json.load(f)
            return {
                'frequent_combinations': patterns.get('frequent_combinations', [])[:5],
                'success_patterns': patterns.get('success_patterns', [])[:5],
                'new_discoveries': count_new_patterns(patterns, weeks=1)
            }
    except Exception:
        return {'frequent_combinations': [], 'success_patterns': []}


def count_new_patterns(patterns: Dict, weeks: int) -> int:
    """
    统计新发现的模式数量

    Args:
        patterns: 模式数据
        weeks: 周数

    Returns:
        新模式数量
    """
    cutoff_date = datetime.now() - timedelta(weeks=weeks)
    new_count = 0

    for pattern in patterns.get('frequent_combinations', []):
        if 'first_seen' in pattern:
            try:
                first_seen = datetime.fromisoformat(pattern['first_seen'].replace('Z', '+00:00'))
                if first_seen >= cutoff_date:
                    new_count += 1
            except Exception:
                pass

    return new_count


def analyze_weight_changes(weeks: int) -> Dict[str, Any]:
    """
    分析权重变化

    Args:
        weeks: 周数

    Returns:
        权重变化分析
    """
    weights_dir = DATA_DIR / 'weights'
    if not weights_dir.exists():
        return {'top_improved': [], 'top_declined': [], 'total_changes': 0}

    # 获取本周和上周的权重文件
    weight_files = sorted(weights_dir.glob('*.json'), reverse=True)
    if len(weight_files) < 2:
        return {'top_improved': [], 'top_declined': [], 'total_changes': 0}

    try:
        with open(weight_files[0], 'r', encoding='utf-8') as f:
            current_weights = json.load(f)
        with open(weight_files[1], 'r', encoding='utf-8') as f:
            previous_weights = json.load(f)

        # 计算变化
        changes = {}
        for key, current_value in current_weights.items():
            if key in previous_weights:
                change = current_value - previous_weights[key]
                if abs(change) > 0.01:  # 只关注变化超过 1% 的
                    changes[key] = change

        # 排序
        sorted_changes = sorted(changes.items(), key=lambda x: abs(x[1]), reverse=True)
        top_improved = [(k, v) for k, v in sorted_changes if v > 0][:5]
        top_declined = [(k, v) for k, v in sorted_changes if v < 0][:5]

        return {
            'top_improved': top_improved,
            'top_declined': top_declined,
            'total_changes': len(changes)
        }
    except Exception:
        return {'top_improved': [], 'top_declined': [], 'total_changes': 0}


def generate_summary(executions: List[Dict], quality_metrics: Dict,
                     patterns: Dict, weights: Dict) -> str:
    """
    生成摘要文本

    Args:
        executions: 执行记录
        quality_metrics: 质量指标
        patterns: 模式分析
        weights: 权重变化

    Returns:
        摘要文本
    """
    summary_parts = []

    # 执行统计
    summary_parts.append(f"本周共执行 {len(executions)} 次 skill 调用")

    # 质量趋势
    trend_desc = {
        'improving': '质量持续提升 📈',
        'declining': '质量有所下降 📉',
        'stable': '质量保持稳定 ➡️'
    }
    summary_parts.append(trend_desc[quality_metrics['trend']])

    # 新模式
    new_patterns = patterns.get('new_discoveries', 0)
    if new_patterns > 0:
        summary_parts.append(f"发现 {new_patterns} 个新的成功模式")

    # 权重变化
    if weights['total_changes'] > 0:
        summary_parts.append(f"{weights['total_changes']} 个权重发生显著变化")

    return '；'.join(summary_parts) + '。'


def save_markdown_report(report: Dict, output_file: Path):
    """
    保存为 Markdown 格式

    Args:
        report: 报告数据
        output_file: 输出文件路径
    """
    md_content = generate_markdown(report)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md_content)


def generate_markdown(report: Dict) -> str:
    """
    生成 Markdown 内容

    Args:
        report: 报告数据

    Returns:
        Markdown 文本
    """
    period = report['metadata']['period']
    summary = report['summary']
    quality = report['quality_metrics']
    patterns = report['patterns']
    weights = report['weights']

    md = f"""# Self-Evolution 周报

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**报告周期**: {period['start_date']} ~ {period['end_date']}

---

## 📊 执行摘要

{summary}

- **总执行次数**: {report['executions_count']}
- **整体质量分数**: {quality['overall_score']:.2f} / 1.00
- **质量趋势**: {quality['trend']}

---

## 📈 质量指标

| 维度 | 分数 | 说明 |
|------|------|------|
| 完整性 (Completeness) | {quality['completeness']:.2f} | 生成代码的完整程度 |
| 一致性 (Consistency) | {quality['consistency']:.2f} | 与现有代码风格的一致性 |
| 专业性 (Professionalism) | {quality['professionalism']:.2f} | 代码质量和最佳实践 |

**样本数**: {quality['sample_size']} 次执行

---

## 🔍 发现的模式

### 高频组合

"""

    for i, pattern in enumerate(patterns.get('frequent_combinations', [])[:5], 1):
        items = ' + '.join(pattern.get('items', []))
        support = pattern.get('support', 0)
        md += f"{i}. **{items}** (出现 {support} 次)\n"

    md += "\n### 成功模式\n\n"

    for i, pattern in enumerate(patterns.get('success_patterns', [])[:5], 1):
        items = ' + '.join(pattern.get('items', []))
        quality_score = pattern.get('avg_quality', 0)
        md += f"{i}. **{items}** (质量分数: {quality_score:.2f})\n"

    md += f"\n**新发现模式**: {patterns.get('new_discoveries', 0)} 个\n"

    md += "\n---\n\n## ⚖️ 权重变化\n\n### Top 5 提升\n\n"

    for i, (key, value) in enumerate(weights.get('top_improved', [])[:5], 1):
        md += f"{i}. **{key}**: +{value:.3f}\n"

    md += "\n### Top 5 下降\n\n"

    for i, (key, value) in enumerate(weights.get('top_declined', [])[:5], 1):
        md += f"{i}. **{key}**: {value:.3f}\n"

    md += f"\n**总变化数**: {weights.get('total_changes', 0)} 个权重\n"

    md += "\n---\n\n## 📌 建议\n\n"

    # 根据数据生成建议
    if quality['trend'] == 'declining':
        md += "- ⚠️ 质量下降，建议审查最近的模式发现和权重调整\n"
    elif quality['trend'] == 'improving':
        md += "- ✓ 质量提升良好，继续保持当前优化策略\n"

    if quality['completeness'] < 0.8:
        md += "- ⚠️ 完整性偏低，建议增强代码生成的完整度\n"

    if patterns.get('new_discoveries', 0) == 0:
        md += "- ⚠️ 未发现新模式，建议增加执行样本或调整发现阈值\n"

    md += "\n---\n\n*本报告由 Self-Evolution Skill 自动生成*\n"

    return md


def save_html_report(report: Dict, output_file: Path):
    """保存为 HTML 格式"""
    # 简化实现：将 Markdown 转为基础 HTML
    md_content = generate_markdown(report)
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Self-Evolution 周报</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
    </style>
</head>
<body>
    <pre>{md_content}</pre>
</body>
</html>"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)


def save_json_report(report: Dict, output_file: Path):
    """保存为 JSON 格式"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


def get_latest_file(directory: Path, pattern: str) -> Path:
    """
    获取目录中最新的文件

    Args:
        directory: 目录路径
        pattern: 文件模式

    Returns:
        最新文件路径（如果没有则返回 None）
    """
    files = sorted(directory.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
    return files[0] if files else None


if __name__ == '__main__':
    main()
