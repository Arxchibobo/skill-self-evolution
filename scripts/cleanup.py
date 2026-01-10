#!/usr/bin/env python3
"""
Self-Evolution Skill - 数据清理工具

定期清理旧数据，压缩归档，管理存储空间。

用法:
    python cleanup.py --days 90               # 删除 90 天前的数据
    python cleanup.py --archive               # 归档数据（压缩但保留）
    python cleanup.py --compress --days 60    # 压缩 60 天前的数据
    python cleanup.py --stats                 # 显示存储统计

功能:
    1. 删除过期数据（根据保留天数）
    2. 压缩归档旧数据（保留但压缩）
    3. 清理临时文件和缓存
    4. 生成存储统计报告
"""

import argparse
import gzip
import json
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

# 项目路径
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / 'data'
CACHE_DIR = SKILL_DIR / 'cache'
ARCHIVE_DIR = SKILL_DIR / 'archive'
LOG_FILE = SKILL_DIR / 'logs' / 'cleanup.log'


def main():
    parser = argparse.ArgumentParser(description='Self-Evolution Skill 数据清理工具')
    parser.add_argument('--days', type=int, default=90,
                        help='保留最近 N 天的数据（默认: 90）')
    parser.add_argument('--archive', action='store_true',
                        help='归档数据（压缩但保留）而不是删除')
    parser.add_argument('--compress', action='store_true',
                        help='压缩旧数据（保留原始数据）')
    parser.add_argument('--stats', action='store_true',
                        help='显示存储统计信息')
    parser.add_argument('--dry-run', action='store_true',
                        help='模拟运行（不实际删除文件）')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='显示详细信息')

    args = parser.parse_args()

    # 创建必要的目录
    ensure_directories()

    # 初始化日志
    log_message(f"[开始清理] {datetime.now()}")
    log_message(f"参数: days={args.days}, archive={args.archive}, "
                f"compress={args.compress}, dry-run={args.dry_run}")

    # 执行操作
    try:
        if args.stats:
            show_storage_stats()
        else:
            cleanup_old_data(
                days=args.days,
                archive=args.archive,
                compress=args.compress,
                dry_run=args.dry_run,
                verbose=args.verbose
            )

        log_message("[清理完成]")
        print("✓ 清理完成")

    except Exception as e:
        log_message(f"[错误] {str(e)}")
        print(f"✗ 清理失败: {e}", file=sys.stderr)
        sys.exit(1)


def ensure_directories():
    """确保必要的目录存在"""
    for directory in [ARCHIVE_DIR, LOG_FILE.parent]:
        directory.mkdir(parents=True, exist_ok=True)


def cleanup_old_data(days: int, archive: bool, compress: bool,
                     dry_run: bool, verbose: bool):
    """
    清理旧数据

    Args:
        days: 保留最近 N 天的数据
        archive: 是否归档（而不是删除）
        compress: 是否压缩（而不是删除）
        dry_run: 是否模拟运行
        verbose: 是否显示详细信息
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    print(f"清理日期阈值: {cutoff_date.strftime('%Y-%m-%d')}")
    print(f"模式: {'归档' if archive else '压缩' if compress else '删除'}")

    total_files = 0
    total_size = 0
    processed = 0

    # 遍历所有数据目录
    data_dirs = {
        'executions': DATA_DIR / 'executions',
        'feedback': DATA_DIR / 'feedback',
        'modifications': DATA_DIR / 'modifications',
        'patterns': DATA_DIR / 'patterns',
        'weights': DATA_DIR / 'weights'
    }

    for dir_name, dir_path in data_dirs.items():
        if not dir_path.exists():
            continue

        print(f"\n[{dir_name}]")

        for file_path in dir_path.glob('*.json'):
            total_files += 1
            file_size = file_path.stat().st_size
            total_size += file_size

            # 从文件名或内容中提取日期
            file_date = extract_file_date(file_path)

            if file_date and file_date < cutoff_date:
                processed += 1

                if verbose:
                    print(f"  处理: {file_path.name} ({file_date.strftime('%Y-%m-%d')})")

                if not dry_run:
                    if archive:
                        archive_file(file_path, dir_name)
                    elif compress:
                        compress_file(file_path)
                    else:
                        file_path.unlink()
                        if verbose:
                            print(f"    → 已删除")

    # 清理缓存
    print(f"\n[cache]")
    cache_cleaned = cleanup_cache(dry_run, verbose)
    processed += cache_cleaned

    # 清理空目录
    if not dry_run:
        cleanup_empty_dirs()

    # 显示统计
    print(f"\n{'=' * 50}")
    print(f"总文件数: {total_files}")
    print(f"总大小: {format_size(total_size)}")
    print(f"处理文件数: {processed}")
    print(f"{'模拟运行' if dry_run else '实际执行'}")

    log_message(f"清理完成: 总计 {total_files} 个文件, 处理 {processed} 个")


def extract_file_date(file_path: Path) -> datetime:
    """
    从文件名或内容中提取日期

    Args:
        file_path: 文件路径

    Returns:
        文件日期（如果无法提取则返回 None）
    """
    # 尝试从文件名提取（格式: YYYYMMDD_*.json）
    filename = file_path.stem
    if len(filename) >= 8 and filename[:8].isdigit():
        try:
            return datetime.strptime(filename[:8], '%Y%m%d')
        except ValueError:
            pass

    # 尝试从文件内容提取
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'timestamp' in data:
                return datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
    except Exception:
        pass

    # 使用文件修改时间
    return datetime.fromtimestamp(file_path.stat().st_mtime)


def archive_file(file_path: Path, category: str):
    """
    归档文件（压缩并移动到归档目录）

    Args:
        file_path: 文件路径
        category: 文件类别（executions, feedback, etc.）
    """
    # 按日期组织归档
    file_date = extract_file_date(file_path)
    year_month = file_date.strftime('%Y-%m') if file_date else 'unknown'

    archive_subdir = ARCHIVE_DIR / category / year_month
    archive_subdir.mkdir(parents=True, exist_ok=True)

    # 压缩文件
    archive_path = archive_subdir / f"{file_path.stem}.json.gz"
    with open(file_path, 'rb') as f_in:
        with gzip.open(archive_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    # 删除原文件
    file_path.unlink()


def compress_file(file_path: Path):
    """
    压缩文件（保留在原位置）

    Args:
        file_path: 文件路径
    """
    compressed_path = file_path.with_suffix('.json.gz')

    with open(file_path, 'rb') as f_in:
        with gzip.open(compressed_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    # 删除原文件
    file_path.unlink()


def cleanup_cache(dry_run: bool, verbose: bool) -> int:
    """
    清理缓存目录

    Args:
        dry_run: 是否模拟运行
        verbose: 是否显示详细信息

    Returns:
        清理的文件数
    """
    if not CACHE_DIR.exists():
        return 0

    cleaned = 0
    for file_path in CACHE_DIR.glob('*_history.json'):
        cleaned += 1
        if verbose:
            print(f"  清理缓存: {file_path.name}")
        if not dry_run:
            file_path.unlink()

    return cleaned


def cleanup_empty_dirs():
    """清理空目录"""
    for root, dirs, files in os.walk(DATA_DIR, topdown=False):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            try:
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()
            except Exception:
                pass


def show_storage_stats():
    """显示存储统计信息"""
    print("存储统计")
    print("=" * 60)

    stats = collect_storage_stats()

    # 按目录显示
    total_size = 0
    total_files = 0

    for dir_name, info in sorted(stats.items()):
        print(f"\n{dir_name}:")
        print(f"  文件数: {info['count']}")
        print(f"  大小: {format_size(info['size'])}")
        print(f"  最早: {info['oldest']}")
        print(f"  最新: {info['newest']}")

        total_files += info['count']
        total_size += info['size']

    print(f"\n{'=' * 60}")
    print(f"总计: {total_files} 个文件, {format_size(total_size)}")

    # 建议
    print(f"\n建议:")
    days_old = calculate_oldest_data_age(stats)
    if days_old > 180:
        print(f"  ⚠️  最早数据已有 {days_old} 天，建议清理")
    if total_size > 100 * 1024 * 1024:  # > 100 MB
        print(f"  ⚠️  总大小超过 100 MB，建议压缩或归档")


def collect_storage_stats() -> Dict[str, Dict]:
    """
    收集存储统计信息

    Returns:
        各目录的统计信息
    """
    stats = {}

    data_dirs = {
        'executions': DATA_DIR / 'executions',
        'feedback': DATA_DIR / 'feedback',
        'modifications': DATA_DIR / 'modifications',
        'patterns': DATA_DIR / 'patterns',
        'weights': DATA_DIR / 'weights',
        'cache': CACHE_DIR,
        'archive': ARCHIVE_DIR
    }

    for dir_name, dir_path in data_dirs.items():
        if not dir_path.exists():
            continue

        files = list(dir_path.glob('**/*.json')) + list(dir_path.glob('**/*.json.gz'))
        if not files:
            continue

        dates = [extract_file_date(f) for f in files]
        valid_dates = [d for d in dates if d]

        stats[dir_name] = {
            'count': len(files),
            'size': sum(f.stat().st_size for f in files),
            'oldest': min(valid_dates).strftime('%Y-%m-%d') if valid_dates else 'N/A',
            'newest': max(valid_dates).strftime('%Y-%m-%d') if valid_dates else 'N/A'
        }

    return stats


def calculate_oldest_data_age(stats: Dict[str, Dict]) -> int:
    """
    计算最早数据的年龄（天数）

    Args:
        stats: 存储统计信息

    Returns:
        最早数据的天数
    """
    oldest = datetime.now()

    for info in stats.values():
        if info['oldest'] != 'N/A':
            try:
                date = datetime.strptime(info['oldest'], '%Y-%m-%d')
                oldest = min(oldest, date)
            except ValueError:
                pass

    return (datetime.now() - oldest).days


def format_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 字节数

    Returns:
        格式化后的大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def log_message(message: str):
    """
    记录日志消息

    Args:
        message: 日志消息
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {message}\n"

    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry)


if __name__ == '__main__':
    main()
