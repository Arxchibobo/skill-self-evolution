#!/usr/bin/env python3
"""
Self-Evolution CLI - 统一命令行工具

提供统一的命令行接口来执行所有 Self-Evolution 操作。

用法:
    python cli.py <command> [options]

命令:
    analyze      - 运行模式分析
    optimize     - 运行权重优化
    template     - 生成代码模板
    evolve       - 执行框架进化
    schedule     - 管理调度器
    status       - 显示系统状态
    dashboard    - 打开可视化仪表板
    cleanup      - 清理旧数据

示例:
    python cli.py analyze --window 30
    python cli.py optimize --window 7
    python cli.py template --min-quality 0.75
    python cli.py schedule --daemon
    python cli.py status
    python cli.py dashboard

Author: Bobo (Self-Evolution Skill)
"""

import sys
import subprocess
import webbrowser
from pathlib import Path
from typing import List, Optional
import argparse
import json
from datetime import datetime, timedelta

SCRIPT_DIR = Path(__file__).parent / 'scripts'
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / 'data'


class CLI:
    """统一命令行工具"""

    def __init__(self):
        self.commands = {
            'analyze': self.cmd_analyze,
            'optimize': self.cmd_optimize,
            'template': self.cmd_template,
            'evolve': self.cmd_evolve,
            'schedule': self.cmd_schedule,
            'status': self.cmd_status,
            'dashboard': self.cmd_dashboard,
            'cleanup': self.cmd_cleanup
        }

    def run_script(self, script_name: str, args: List[str] = None) -> int:
        """运行 Python 脚本

        Args:
            script_name: 脚本名称
            args: 命令行参数

        Returns:
            退出代码
        """
        script_path = SCRIPT_DIR / script_name
        if not script_path.exists():
            print(f"❌ Script not found: {script_path}")
            return 1

        cmd = ['python3', str(script_path)]
        if args:
            cmd.extend(args)

        try:
            result = subprocess.run(cmd)
            return result.returncode
        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user")
            return 130
        except Exception as e:
            print(f"❌ Error running script: {e}")
            return 1

    def cmd_analyze(self, args: argparse.Namespace) -> int:
        """运行模式分析"""
        print("🔍 Running pattern discovery...\n")
        script_args = []

        if args.window:
            script_args.extend(['--window', str(args.window)])
        if args.min_support:
            script_args.extend(['--min-support', str(args.min_support)])
        if args.quiet:
            script_args.append('--quiet')

        return self.run_script('pattern_discovery.py', script_args)

    def cmd_optimize(self, args: argparse.Namespace) -> int:
        """运行权重优化"""
        print("⚙️  Running weight optimization...\n")
        script_args = []

        if args.window:
            script_args.extend(['--window', str(args.window)])
        if args.smoothing:
            script_args.extend(['--smoothing', str(args.smoothing)])
        if args.quiet:
            script_args.append('--quiet')

        return self.run_script('weight_optimizer.py', script_args)

    def cmd_template(self, args: argparse.Namespace) -> int:
        """生成代码模板"""
        print("🎨 Generating templates...\n")
        script_args = []

        if args.min_quality:
            script_args.extend(['--min-quality', str(args.min_quality)])
        if args.quiet:
            script_args.append('--quiet')

        return self.run_script('template_generator.py', script_args)

    def cmd_evolve(self, args: argparse.Namespace) -> int:
        """执行框架进化"""
        print("🧬 Running framework evolution...\n")
        script_args = []

        if args.apply:
            script_args.append('--apply')
        if args.quiet:
            script_args.append('--quiet')

        return self.run_script('framework_evolver.py', script_args)

    def cmd_schedule(self, args: argparse.Namespace) -> int:
        """管理调度器"""
        script_args = []

        if args.list:
            print("📋 Listing scheduled tasks...\n")
            script_args.append('--list')
        elif args.daemon:
            print("🚀 Starting scheduler daemon...\n")
            script_args.append('--daemon')
            if args.interval:
                script_args.extend(['--interval', str(args.interval)])
        elif args.task:
            print(f"▶️  Running task: {args.task}\n")
            script_args.extend(['--task', args.task])
        else:
            print("⏱️  Running scheduled tasks once...\n")

        return self.run_script('scheduler.py', script_args)

    def cmd_status(self, args: argparse.Namespace) -> int:
        """显示系统状态"""
        print("📊 Self-Evolution System Status\n")
        print("=" * 60 + "\n")

        # 检查数据目录
        print("📁 Data Directory:")
        print(f"   Location: {DATA_DIR}")
        print(f"   Exists: {'✅' if DATA_DIR.exists() else '❌'}\n")

        # 执行统计
        try:
            index_file = DATA_DIR / 'executions' / 'index.json'
            if index_file.exists():
                with open(index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
                    executions = index.get('executions', [])
                    print(f"📝 Total Executions: {len(executions)}")

                    if executions:
                        latest = executions[-1]
                        print(f"   Latest: {latest.get('skill_name', 'Unknown')} "
                             f"({latest.get('timestamp', 'N/A')})")
            else:
                print("📝 Executions: No data")
        except Exception as e:
            print(f"📝 Executions: Error loading ({e})")

        print()

        # 权重数据
        try:
            weights_file = DATA_DIR / 'weights' / 'latest.json'
            if weights_file.exists():
                with open(weights_file, 'r', encoding='utf-8') as f:
                    weights = json.load(f)
                    print(f"⚖️  Weights: {len(weights.get('weights', {}))} elements")
                    print(f"   Updated: {weights.get('optimization_metadata', {}).get('last_updated', 'N/A')}")
            else:
                print("⚖️  Weights: No data")
        except Exception as e:
            print(f"⚖️  Weights: Error loading ({e})")

        print()

        # 模式数据
        try:
            patterns_file = DATA_DIR / 'patterns' / 'latest.json'
            if patterns_file.exists():
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    patterns = json.load(f)
                    success = len(patterns.get('success_patterns', []))
                    failure = len(patterns.get('failure_patterns', []))
                    print(f"✨ Patterns: {success} success, {failure} failure")
                    print(f"   Analyzed: {patterns.get('analysis_metadata', {}).get('timestamp', 'N/A')}")
            else:
                print("✨ Patterns: No data")
        except Exception as e:
            print(f"✨ Patterns: Error loading ({e})")

        print()

        # 模板数据
        try:
            templates_file = DATA_DIR / 'templates' / 'latest.json'
            if templates_file.exists():
                with open(templates_file, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
                    count = len(templates.get('templates', []))
                    print(f"📚 Templates: {count} available")
                    print(f"   Generated: {templates.get('generated_at', 'N/A')}")
            else:
                print("📚 Templates: No data")
        except Exception as e:
            print(f"📚 Templates: Error loading ({e})")

        print()

        # 调度器状态
        try:
            last_run_file = DATA_DIR / 'last_run.json'
            if last_run_file.exists():
                with open(last_run_file, 'r', encoding='utf-8') as f:
                    last_run = json.load(f)
                    print(f"⏱️  Scheduler: {len(last_run)} tasks tracked")

                    # 显示最近运行的任务
                    if last_run:
                        most_recent = max(last_run.items(), key=lambda x: x[1])
                        print(f"   Last run: {most_recent[0]} ({most_recent[1]})")
            else:
                print("⏱️  Scheduler: Not initialized")
        except Exception as e:
            print(f"⏱️  Scheduler: Error loading ({e})")

        print("\n" + "=" * 60)
        return 0

    def cmd_dashboard(self, args: argparse.Namespace) -> int:
        """打开可视化仪表板"""
        dashboard_path = PROJECT_ROOT / 'dashboard.html'

        if not dashboard_path.exists():
            print("❌ Dashboard not found")
            return 1

        print("🖥️  Opening dashboard in browser...")

        try:
            # 使用绝对路径打开
            url = f'file:///{dashboard_path.absolute()}'.replace('\\', '/')
            webbrowser.open(url)
            print(f"✅ Dashboard opened: {url}")
            print("\n💡 Tip: Refresh the page to see latest data")
            return 0
        except Exception as e:
            print(f"❌ Error opening dashboard: {e}")
            print(f"\n📝 Manually open: {dashboard_path.absolute()}")
            return 1

    def cmd_cleanup(self, args: argparse.Namespace) -> int:
        """清理旧数据"""
        print("🧹 Running cleanup...\n")
        script_args = []

        if args.days:
            script_args.extend(['--days', str(args.days)])
        if args.dry_run:
            script_args.append('--dry-run')
        if args.quiet:
            script_args.append('--quiet')

        return self.run_script('cleanup.py', script_args)

    def run(self, argv: List[str]) -> int:
        """主入口

        Args:
            argv: 命令行参数

        Returns:
            退出代码
        """
        parser = argparse.ArgumentParser(
            description='Self-Evolution CLI - 统一命令行工具',
            epilog='Example: python cli.py analyze --window 30'
        )

        subparsers = parser.add_subparsers(dest='command', help='可用命令')

        # analyze 命令
        analyze_parser = subparsers.add_parser('analyze', help='运行模式分析')
        analyze_parser.add_argument('--window', type=int, default=30,
                                   help='分析窗口（天数，默认: 30）')
        analyze_parser.add_argument('--min-support', type=float, default=0.1,
                                   help='最小支持度（默认: 0.1）')
        analyze_parser.add_argument('--quiet', action='store_true', help='静默模式')

        # optimize 命令
        optimize_parser = subparsers.add_parser('optimize', help='运行权重优化')
        optimize_parser.add_argument('--window', type=int, default=7,
                                    help='优化窗口（天数，默认: 7）')
        optimize_parser.add_argument('--smoothing', type=float, default=0.3,
                                    help='平滑因子（默认: 0.3）')
        optimize_parser.add_argument('--quiet', action='store_true', help='静默模式')

        # template 命令
        template_parser = subparsers.add_parser('template', help='生成代码模板')
        template_parser.add_argument('--min-quality', type=float, default=0.75,
                                    help='最小质量分数（默认: 0.75）')
        template_parser.add_argument('--quiet', action='store_true', help='静默模式')

        # evolve 命令
        evolve_parser = subparsers.add_parser('evolve', help='执行框架进化')
        evolve_parser.add_argument('--apply', action='store_true',
                                  help='自动应用建议（实验性）')
        evolve_parser.add_argument('--quiet', action='store_true', help='静默模式')

        # schedule 命令
        schedule_parser = subparsers.add_parser('schedule', help='管理调度器')
        schedule_parser.add_argument('--daemon', action='store_true', help='Daemon 模式')
        schedule_parser.add_argument('--interval', type=int, default=60,
                                    help='检查间隔（秒，默认: 60）')
        schedule_parser.add_argument('--task', type=str, help='运行特定任务')
        schedule_parser.add_argument('--list', action='store_true', help='列出所有任务')

        # status 命令
        status_parser = subparsers.add_parser('status', help='显示系统状态')

        # dashboard 命令
        dashboard_parser = subparsers.add_parser('dashboard', help='打开可视化仪表板')

        # cleanup 命令
        cleanup_parser = subparsers.add_parser('cleanup', help='清理旧数据')
        cleanup_parser.add_argument('--days', type=int, default=90,
                                   help='保留天数（默认: 90）')
        cleanup_parser.add_argument('--dry-run', action='store_true',
                                   help='只显示将要删除的文件，不实际删除')
        cleanup_parser.add_argument('--quiet', action='store_true', help='静默模式')

        # 解析参数
        if len(argv) == 0:
            parser.print_help()
            return 0

        args = parser.parse_args(argv)

        if not args.command:
            parser.print_help()
            return 0

        # 执行命令
        if args.command in self.commands:
            try:
                return self.commands[args.command](args)
            except KeyboardInterrupt:
                print("\n⚠️  Interrupted by user")
                return 130
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
                return 1
        else:
            print(f"❌ Unknown command: {args.command}")
            parser.print_help()
            return 1


def main():
    """入口函数"""
    cli = CLI()
    sys.exit(cli.run(sys.argv[1:]))


if __name__ == '__main__':
    main()
