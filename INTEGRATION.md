# Self-Evolution Skill 集成指南

本文档详细说明如何将 Self-Evolution Skill 集成到现有的 Claude Code 环境中。

---

## 🚀 快速开始

### 1. 安装依赖

Self-Evolution 需要 Python 3.8+ 和一些科学计算库：

```bash
# 检查 Python 版本
python3 --version  # 应该 >= 3.8

# 安装依赖
pip3 install numpy pandas scipy scikit-learn

# 或使用 requirements.txt
cd .claude/skills/self-evolution
pip3 install -r requirements.txt
```

### 2. 验证安装

```bash
# 运行测试
python3 .claude/skills/self-evolution/scripts/analyze.py

# 应该看到类似输出:
# Self-Evolution Analyzer
# [1/5] 加载执行数据...
# 警告: 数据目录不存在...（首次运行正常）
```

### 3. 启用 Self-Evolution

Self-Evolution 在 `skill.json` 中配置为自动激活，无需手动启用。它会在后台自动运行。

---

## 📋 配置选项

### 基础配置

编辑 `.claude/skills/self-evolution/skill.json`:

```json
{
  "auto_activate": true,        // 自动激活
  "priority": 1,                // 优先级（1=最高）

  "data_collection": {
    "enabled": true,            // 启用数据收集
    "retention_days": 90,       // 数据保留天数
    "anonymize": true           // 匿名化敏感信息
  },

  "modules": [
    {
      "name": "quality-evaluator",
      "enabled": true,          // 启用质量评估
      "thresholds": {
        "completeness": 0.8,    // 完整性阈值
        "consistency": 0.7      // 一致性阈值
      }
    }
  ]
}
```

### 高级配置

创建自定义配置文件 `config.yaml`:

```yaml
# Self-Evolution 自定义配置

# 数据收集
data_collection:
  enabled: true
  storage_path: ".claude/skills/self-evolution/data"
  retention_days: 90
  anonymize: true

# 质量评估
quality_evaluator:
  enabled: true
  thresholds:
    completeness: 0.8
    consistency: 0.7
    professionalism: 0.75

# 权重优化
weight_optimizer:
  update_frequency: "daily"
  smoothing_factor: 0.3
  time_decay:
    enabled: true
    half_life_days: 60

# 报告
reporting:
  dashboard_enabled: true
  update_frequency: "weekly"
```

---

## 🔌 Hook 集成

### PostToolUse Hook

在每次 Skill 执行后自动记录数据：

```javascript
// .claude/skills/self-evolution/hooks/record-execution.js
module.exports = async function(context) {
  if (context.tool !== 'Skill') {
    return { allow: true };
  }

  // 收集执行数据
  const data = collectExecutionData(context);
  await saveExecutionData(data);

  return { allow: true };
};
```

### SessionEnd Hook

在会话结束时收集反馈：

```javascript
// .claude/skills/self-evolution/hooks/collect-feedback.js
module.exports = async function(context) {
  // 检测用户修改
  const modifications = await detectModifications(context);

  // 保存反馈数据
  await saveFeedback(context.sessionId, modifications);

  return { allow: true };
};
```

### 注册 Hooks

在 Claude Code 配置中注册 hooks（通常在 `settings.json`）：

```json
{
  "hooks": [
    {
      "type": "PostToolUse",
      "tool": "Skill",
      "script": ".claude/skills/self-evolution/hooks/record-execution.js"
    },
    {
      "type": "SessionEnd",
      "script": ".claude/skills/self-evolution/hooks/collect-feedback.js"
    }
  ]
}
```

---

## 📊 使用命令

### 查看质量报告

```bash
# 查看最近 7 天的质量报告
/self-evolution:quality-report

# 查看特定时间段
/self-evolution:quality-report --period weekly
/self-evolution:quality-report --period monthly
```

### 查看发现的模式

```bash
# 查看所有模式
/self-evolution:patterns

# 查看特定类型
/self-evolution:patterns --type combinations
/self-evolution:patterns --type sequences
/self-evolution:patterns --type success
```

### 查看权重变化

```bash
# 查看所有权重
/self-evolution:weights

# 查看特定 skill 的权重
/self-evolution:weights --skill ui-ux-pro-max
```

### 手动触发优化

```bash
# 优化所有模块
/self-evolution:optimize

# 优化特定模块
/self-evolution:optimize --module weight-optimizer
/self-evolution:optimize --module pattern-discoverer
```

### 导出数据

```bash
# 导出为 JSON
/self-evolution:export --format json

# 导出为 CSV
/self-evolution:export --format csv

# 导出特定时间段
/self-evolution:export --period 2026-01-01:2026-01-31
```

### 查看仪表板

```bash
# 打开仪表板
/self-evolution:dashboard

# 仪表板位置
# .claude/skills/self-evolution/reports/dashboard.md
```

---

## 🔄 自动化工作流

### 定时分析（推荐）

使用 cron 或任务计划程序定期运行分析：

#### Linux/Mac (cron)

```bash
# 编辑 crontab
crontab -e

# 添加每日分析（每天凌晨 2 点）
0 2 * * * cd ~/.claude/skills/self-evolution && python3 scripts/analyze.py

# 添加每周报告（每周一凌晨 3 点）
0 3 * * 1 cd ~/.claude/skills/self-evolution && python3 scripts/weekly_report.py
```

#### Windows (任务计划程序)

```powershell
# 创建定时任务
schtasks /create /tn "SelfEvolutionDaily" /tr "python E:\Bobo's Coding cache\.claude\skills\self-evolution\scripts\analyze.py" /sc daily /st 02:00

# 查看任务
schtasks /query /tn "SelfEvolutionDaily"
```

### CI/CD 集成

在 CI/CD 流程中运行质量检查：

```yaml
# .github/workflows/self-evolution.yml
name: Self-Evolution Quality Check

on:
  schedule:
    - cron: '0 2 * * *'  # 每天凌晨 2 点
  workflow_dispatch:      # 手动触发

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install numpy pandas scipy scikit-learn

      - name: Run analysis
        run: |
          cd .claude/skills/self-evolution
          python3 scripts/analyze.py

      - name: Upload dashboard
        uses: actions/upload-artifact@v3
        with:
          name: dashboard
          path: .claude/skills/self-evolution/reports/dashboard.md
```

---

## 🎯 实战场景

### 场景 1: 监控 UI/UX Skill 质量

```bash
# 1. 正常使用 ui-ux-pro-max
"设计一个 SaaS 定价页面"

# 2. Self-Evolution 自动记录数据（后台）

# 3. 查看质量报告
/self-evolution:quality-report --skill ui-ux-pro-max

# 4. 查看发现的模式
/self-evolution:patterns --type success

# 输出示例：
# 成功模式:
# - 样式组合: minimalism + glassmorphism (质量分 0.92)
# - 搜索序列: product → style → color → typography (效果最佳)
# - 技术栈: html-tailwind (最稳定)
```

### 场景 2: 优化权重和搜索策略

```bash
# 1. 运行分析
python3 .claude/skills/self-evolution/scripts/analyze.py

# 2. 查看权重变化
/self-evolution:weights

# 输出示例：
# 权重 Top 10:
# - style:minimalism: 0.923
# - color:#0F172A: 0.887
# - font:Inter: 0.856

# 3. 应用优化（自动）
# Self-Evolution 会自动更新搜索数据库权重
```

### 场景 3: 跨领域知识迁移

```bash
# 1. 在 SaaS 领域积累成功经验

# 2. 迁移到 E-commerce 领域
"设计一个电商产品页面"

# 3. Self-Evolution 自动：
# - 识别相似性（都是商业页面）
# - 迁移成功的样式组合
# - 适配行业特定元素

# 4. 查看迁移结果
/self-evolution:patterns --type transfer
```

### 场景 4: 用户反馈学习

```bash
# 1. 生成初始代码
"设计一个博客首页"

# 2. 用户修改代码（例如：改变颜色、调整布局）

# 3. SessionEnd 时 Self-Evolution 自动：
# - 检测修改
# - 分析修改原因
# - 更新规则

# 4. 下次生成时自动应用学习到的偏好
"再设计一个博客首页"
# 输出会自动包含用户偏好的颜色和布局
```

---

## 📈 性能优化

### 减少开销

如果 Self-Evolution 影响性能，可以调整配置：

```json
{
  "data_collection": {
    "enabled": true,
    "sampling_rate": 0.5  // 只收集 50% 的数据
  },

  "performance": {
    "async_processing": true,      // 异步处理
    "batch_updates": true,         // 批量更新
    "max_memory_mb": 50,           // 内存限制
    "max_cpu_percent": 5           // CPU 限制
  }
}
```

### 数据清理

定期清理旧数据：

```bash
# 清理 90 天前的数据
python3 .claude/skills/self-evolution/scripts/cleanup.py --days 90

# 压缩旧数据
python3 .claude/skills/self-evolution/scripts/compress.py --archive
```

---

## 🔍 故障排除

### 问题 1: 没有收集到数据

**症状**: 运行分析脚本时提示"没有找到执行数据"

**解决方案**:
1. 检查 hooks 是否正确配置
2. 验证 skill.json 中 `auto_activate: true`
3. 查看日志文件 `.claude/skills/self-evolution/logs/error.log`

```bash
# 测试 hook
node .claude/skills/self-evolution/hooks/record-execution.js
```

### 问题 2: 分析脚本报错

**症状**: `ImportError: No module named 'numpy'`

**解决方案**:
```bash
# 安装依赖
pip3 install numpy pandas scipy scikit-learn

# 或使用虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 问题 3: 权重没有更新

**症状**: 优化权重后，生成结果没有变化

**解决方案**:
1. 检查权重文件是否正确保存
2. 确认 skill 读取了最新权重
3. 手动触发优化

```bash
# 查看权重文件
cat .claude/skills/self-evolution/data/weights/current_weights.json

# 手动优化
/self-evolution:optimize --module weight-optimizer
```

---

## 🎓 最佳实践

### 1. 渐进式启用

建议先在测试环境中验证，再在生产环境启用：

```bash
# 阶段 1: 只启用数据收集（2 周）
{
  "data_collection": {"enabled": true},
  "modules": [
    {"name": "quality-evaluator", "enabled": true},
    // 其他模块暂时禁用
  ]
}

# 阶段 2: 启用分析（1 周）
{
  "modules": [
    {"name": "pattern-discoverer", "enabled": true},
    {"name": "feedback-learner", "enabled": true}
  ]
}

# 阶段 3: 启用优化（持续）
{
  "modules": [
    {"name": "weight-optimizer", "enabled": true},
    {"name": "framework-evolver", "enabled": true}
  ]
}
```

### 2. 定期审查

定期（每周或每月）审查 Self-Evolution 的改进效果：

```bash
# 生成月度报告
python3 scripts/monthly_report.py --month 2026-01

# 对比不同时间段
python3 scripts/compare.py --period1 2025-12 --period2 2026-01
```

### 3. 保护隐私

确保敏感信息不被记录：

```json
{
  "data_collection": {
    "anonymize": true,
    "excluded_data": [
      "user_credentials",
      "api_keys",
      "personal_information",
      "proprietary_code"
    ]
  }
}
```

### 4. 备份数据

定期备份进化数据：

```bash
# 备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d)
tar -czf self-evolution-backup-$DATE.tar.gz \
  .claude/skills/self-evolution/data \
  .claude/skills/self-evolution/reports

# 移动到备份目录
mv self-evolution-backup-$DATE.tar.gz ~/backups/
```

---

## 🤝 与其他 Skills 集成

### 集成 ui-ux-pro-max

```json
{
  "integration": {
    "monitored_skills": ["ui-ux-pro-max"],
    "data_sources": ["skill_executions", "search_history"]
  }
}
```

Self-Evolution 会自动：
- 记录 ui-ux-pro-max 的每次执行
- 分析搜索模式
- 优化搜索权重
- 生成设计模板

### 集成 browser-use

```json
{
  "integration": {
    "monitored_skills": ["browser-use"],
    "data_sources": ["browser_actions", "success_rate"]
  }
}
```

Self-Evolution 会自动：
- 跟踪浏览器操作成功率
- 识别可靠的选择器模式
- 优化等待时间
- 学习错误恢复策略

### 集成 code-review

```json
{
  "integration": {
    "monitored_skills": ["code-review"],
    "data_sources": ["review_findings", "false_positives"]
  }
}
```

Self-Evolution 会自动：
- 跟踪审查发现的准确性
- 降低误报权重
- 学习项目特定模式
- 优化置信度阈值

---

## 📚 API 文档

### Python API

```python
from self_evolution import SelfEvolutionAnalyzer

# 创建分析器
analyzer = SelfEvolutionAnalyzer()

# 加载数据
executions = analyzer.load_executions(days=30)

# 计算质量分数
scored = analyzer.calculate_quality_scores(executions)

# 发现模式
patterns = analyzer.discover_patterns(executions)

# 优化权重
weights = analyzer.optimize_weights(executions)

# 生成报告
dashboard = analyzer.generate_dashboard(executions, patterns, weights)
```

### JavaScript API

```javascript
const SelfEvolution = require('.claude/skills/self-evolution');

// 记录执行
await SelfEvolution.recordExecution(context);

// 收集反馈
await SelfEvolution.collectFeedback(sessionId);

// 查询质量分数
const quality = await SelfEvolution.getQualityScore(sessionId);
```

---

## 🔗 相关资源

- [README.md](./README.md) - 核心概念和架构
- [skill.json](./skill.json) - Skill 配置
- [scripts/analyze.py](./scripts/analyze.py) - 分析脚本
- [hooks/](./hooks/) - Hook 实现

---

**最后更新**: 2026-01-10
**版本**: 1.0.0
