#!/usr/bin/env python3
"""
Scheduler - 自动化调度器

定期执行分析和优化任务的调度系统。

核心功能：
1. 任务调度 - 支持 daily、weekly 等周期
2. 任务依赖 - 自动处理任务间依赖关系
3. 后台运行 - Daemon 模式持续运行
4. 任务日志 - 记录所有执行历史
5. 错误处理 - 失败重试和告警

任务配置：
{
    "tasks": [
        {
            "name": "daily_optimization",
            "script": "weight_optimizer.py",
            "schedule": "daily",
            "time": "02:00",
            "enabled": true
        }
    ]
}

Schedule 语法：
- "daily" - 每天执行
- "weekly:monday" - 每周一执行
- "hourly" - 每小时执行

Author: Bobo (Self-Evolution Skill)
"""

import json
import sys
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TaskScheduler:
    """任务调度器"""

    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or PROJECT_ROOT / 'config.yaml'
        self.data_dir = PROJECT_ROOT / 'data'
        self.logs_dir = self.data_dir / 'logs'
        self.logs_dir.mkdir(exist_ok=True)

        # 配置日志
        log_file = self.logs_dir / 'scheduler.log'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # 默认任务配置
        self.default_tasks = [
            {
                'name': 'daily_optimization',
                'description': '每日权重优化',
                'script': 'weight_optimizer.py',
                'args': ['--window', '7'],
                'schedule': 'daily',
                'time': '02:00',
                'enabled': True,
                'dependencies': []
            },
            {
                'name': 'weekly_pattern_discovery',
                'description': '每周模式发现',
                'script': 'pattern_discovery.py',
                'args': ['--window', '30', '--min-support', '0.1'],
                'schedule': 'weekly:monday',
                'time': '03:00',
                'enabled': True,
                'dependencies': ['daily_optimization']
            },
            {
                'name': 'weekly_template_generation',
                'description': '每周模板生成',
                'script': 'template_generator.py',
                'args': ['--min-quality', '0.75'],
                'schedule': 'weekly:monday',
                'time': '03:30',
                'enabled': True,
                'dependencies': ['weekly_pattern_discovery']
            },
            {
                'name': 'weekly_knowledge_transfer',
                'description': '每周知识迁移',
                'script': 'knowledge_transfer.py',
                'args': ['--similarity-threshold', '0.6'],
                'schedule': 'weekly:monday',
                'time': '04:00',
                'enabled': True,
                'dependencies': ['weekly_pattern_discovery']
            },
            {
                'name': 'weekly_framework_evolution',
                'description': '每周框架进化',
                'script': 'framework_evolver.py',
                'args': [],
                'schedule': 'weekly:monday',
                'time': '04:30',
                'enabled': True,
                'dependencies': ['weekly_pattern_discovery']
            },
            {
                'name': 'weekly_report',
                'description': '每周分析报告',
                'script': 'weekly_report.py',
                'args': [],
                'schedule': 'weekly:monday',
                'time': '05:00',
                'enabled': True,
                'dependencies': [
                    'weekly_pattern_discovery',
                    'weekly_template_generation',
                    'weekly_knowledge_transfer'
                ]
            }
        ]

        self.tasks = self.default_tasks
        self.last_run = {}  # 记录上次运行时间

    def parse_schedule(self, schedule: str) -> Dict[str, Any]:
        """解析调度配置

        Args:
            schedule: 调度字符串 (如 "daily", "weekly:monday")

        Returns:
            解析后的调度信息
        """
        parts = schedule.split(':')
        schedule_type = parts[0].lower()

        result = {
            'type': schedule_type,
            'day': None
        }

        if schedule_type == 'weekly' and len(parts) > 1:
            result['day'] = parts[1].lower()
        elif schedule_type == 'monthly' and len(parts) > 1:
            result['day'] = int(parts[1])

        return result

    def should_run(self, task: Dict, now: datetime) -> bool:
        """判断任务是否应该执行

        Args:
            task: 任务配置
            now: 当前时间

        Returns:
            是否应该执行
        """
        if not task.get('enabled', True):
            return False

        task_name = task['name']
        schedule_config = self.parse_schedule(task['schedule'])
        schedule_time = task.get('time', '00:00')

        # 解析时间
        try:
            hour, minute = map(int, schedule_time.split(':'))
        except:
            hour, minute = 0, 0

        # 检查上次运行时间
        last_run = self.last_run.get(task_name)
        if last_run:
            last_run_dt = datetime.fromisoformat(last_run)

            # 如果是今天已经运行过，跳过
            if schedule_config['type'] == 'daily':
                if last_run_dt.date() == now.date():
                    return False

            # 如果是本周已经运行过，跳过
            elif schedule_config['type'] == 'weekly':
                if (now - last_run_dt).days < 7:
                    return False

        # 检查时间是否匹配
        schedule_type = schedule_config['type']

        if schedule_type == 'hourly':
            # 每小时执行
            return now.minute == minute

        elif schedule_type == 'daily':
            # 每天在指定时间执行
            return now.hour == hour and now.minute == minute

        elif schedule_type == 'weekly':
            # 每周在指定星期和时间执行
            weekday_map = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2,
                'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
            }
            target_weekday = weekday_map.get(schedule_config.get('day', 'monday'), 0)
            return (now.weekday() == target_weekday and
                   now.hour == hour and now.minute == minute)

        elif schedule_type == 'monthly':
            # 每月指定日期执行
            target_day = schedule_config.get('day', 1)
            return (now.day == target_day and
                   now.hour == hour and now.minute == minute)

        return False

    def check_dependencies(self, task: Dict) -> bool:
        """检查任务依赖是否满足

        Args:
            task: 任务配置

        Returns:
            依赖是否满足
        """
        dependencies = task.get('dependencies', [])
        if not dependencies:
            return True

        # 检查所有依赖任务是否已运行
        for dep_name in dependencies:
            if dep_name not in self.last_run:
                self.logger.warning(f"Dependency not met: {dep_name} has not run yet")
                return False

            # 检查依赖是否在最近运行过（24小时内）
            last_run = datetime.fromisoformat(self.last_run[dep_name])
            if (datetime.now() - last_run).total_seconds() > 86400:
                self.logger.warning(f"Dependency stale: {dep_name} last run was too long ago")
                return False

        return True

    def run_task(self, task: Dict) -> bool:
        """执行任务

        Args:
            task: 任务配置

        Returns:
            执行是否成功
        """
        task_name = task['name']
        script = task['script']
        args = task.get('args', [])

        self.logger.info(f"Running task: {task_name}")
        self.logger.info(f"Description: {task.get('description', 'N/A')}")

        # 构建命令
        script_path = SCRIPT_DIR / script
        if not script_path.exists():
            self.logger.error(f"Script not found: {script_path}")
            return False

        cmd = ['python3', str(script_path)] + args

        try:
            # 执行脚本
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1小时超时
            )

            if result.returncode == 0:
                self.logger.info(f"✅ Task {task_name} completed successfully")
                if result.stdout:
                    self.logger.debug(f"Output: {result.stdout[:500]}")
                return True
            else:
                self.logger.error(f"❌ Task {task_name} failed with code {result.returncode}")
                if result.stderr:
                    self.logger.error(f"Error: {result.stderr[:500]}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error(f"❌ Task {task_name} timed out after 1 hour")
            return False
        except Exception as e:
            self.logger.error(f"❌ Task {task_name} failed with exception: {e}")
            return False

    def update_last_run(self, task_name: str):
        """更新任务的最后运行时间"""
        self.last_run[task_name] = datetime.now().isoformat()

        # 保存到文件
        last_run_file = self.data_dir / 'last_run.json'
        with open(last_run_file, 'w', encoding='utf-8') as f:
            json.dump(self.last_run, f, indent=2)

    def load_last_run(self):
        """加载上次运行记录"""
        last_run_file = self.data_dir / 'last_run.json'
        if last_run_file.exists():
            with open(last_run_file, 'r', encoding='utf-8') as f:
                self.last_run = json.load(f)

    def run_once(self, task_filter: Optional[str] = None) -> Dict[str, Any]:
        """运行一次所有到期的任务

        Args:
            task_filter: 任务名称过滤器（只运行匹配的任务）

        Returns:
            执行结果
        """
        now = datetime.now()
        results = {
            'timestamp': now.isoformat(),
            'tasks_checked': 0,
            'tasks_run': 0,
            'tasks_succeeded': 0,
            'tasks_failed': 0,
            'details': []
        }

        self.load_last_run()

        # 按依赖顺序对任务排序
        sorted_tasks = self._topological_sort(self.tasks)

        for task in sorted_tasks:
            task_name = task['name']
            results['tasks_checked'] += 1

            # 任务过滤
            if task_filter and task_filter not in task_name:
                continue

            # 检查是否应该运行
            if not self.should_run(task, now):
                self.logger.debug(f"Skipping {task_name}: not scheduled")
                continue

            # 检查依赖
            if not self.check_dependencies(task):
                self.logger.warning(f"Skipping {task_name}: dependencies not met")
                results['details'].append({
                    'task': task_name,
                    'status': 'skipped',
                    'reason': 'dependencies_not_met'
                })
                continue

            # 运行任务
            results['tasks_run'] += 1
            success = self.run_task(task)

            if success:
                results['tasks_succeeded'] += 1
                self.update_last_run(task_name)
                results['details'].append({
                    'task': task_name,
                    'status': 'success'
                })
            else:
                results['tasks_failed'] += 1
                results['details'].append({
                    'task': task_name,
                    'status': 'failed'
                })

        return results

    def _topological_sort(self, tasks: List[Dict]) -> List[Dict]:
        """对任务进行拓扑排序（处理依赖关系）"""
        # 简化实现：按依赖数量排序
        return sorted(tasks, key=lambda t: len(t.get('dependencies', [])))

    def daemon(self, interval: int = 60):
        """以 Daemon 模式持续运行

        Args:
            interval: 检查间隔（秒）
        """
        self.logger.info("🚀 Scheduler daemon started")
        self.logger.info(f"⏱️  Check interval: {interval} seconds")
        self.logger.info(f"📋 Loaded {len(self.tasks)} tasks")

        try:
            while True:
                try:
                    results = self.run_once()

                    if results['tasks_run'] > 0:
                        self.logger.info(
                            f"📊 Cycle complete: "
                            f"{results['tasks_succeeded']} succeeded, "
                            f"{results['tasks_failed']} failed"
                        )
                except Exception as e:
                    self.logger.error(f"Error in scheduler cycle: {e}")

                time.sleep(interval)

        except KeyboardInterrupt:
            self.logger.info("\n👋 Scheduler daemon stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Scheduler daemon crashed: {e}")
            raise


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='Scheduler - 自动化调度器')
    parser.add_argument('--daemon', action='store_true', help='Daemon 模式')
    parser.add_argument('--interval', type=int, default=60,
                       help='Daemon 检查间隔（秒）')
    parser.add_argument('--task', type=str, help='只运行特定任务（名称包含此字符串）')
    parser.add_argument('--list', action='store_true', help='列出所有任务')

    args = parser.parse_args()

    try:
        scheduler = TaskScheduler()

        if args.list:
            print("📋 Configured Tasks:\n")
            for task in scheduler.tasks:
                status = "✅" if task.get('enabled', True) else "❌"
                print(f"{status} {task['name']}")
                print(f"   Description: {task.get('description', 'N/A')}")
                print(f"   Schedule: {task['schedule']} at {task.get('time', 'N/A')}")
                print(f"   Script: {task['script']}")
                print(f"   Dependencies: {', '.join(task.get('dependencies', [])) or 'None'}")
                print()
            sys.exit(0)

        if args.daemon:
            scheduler.daemon(interval=args.interval)
        else:
            results = scheduler.run_once(task_filter=args.task)
            print(f"\n📊 Results:")
            print(f"   Tasks checked: {results['tasks_checked']}")
            print(f"   Tasks run: {results['tasks_run']}")
            print(f"   Succeeded: {results['tasks_succeeded']}")
            print(f"   Failed: {results['tasks_failed']}")

            if results['tasks_failed'] > 0:
                sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
