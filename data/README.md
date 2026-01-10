# Self-Evolution Data 目录

此目录存储 Self-Evolution Skill 收集的所有数据。

## 目录结构

```
data/
├── executions/      # Skill 执行记录
├── feedback/        # 用户反馈数据
├── modifications/   # 文件修改记录
├── patterns/        # 发现的模式
├── weights/         # 搜索权重数据
└── README.md        # 本文件
```

## 各目录说明

### executions/
存储每次 skill 执行的详细记录，包括：
- 触发原因
- 执行参数
- 搜索历史
- 生成结果
- 质量评分

**文件命名**: `YYYYMMDD_<session_id>_execution.json`

### feedback/
存储用户反馈数据，包括：
- 显式评分（如果用户提供）
- 隐式反馈（基于用户修改行为）
- 满意度分数
- 修改模式分析

**文件命名**: `<session_id>_feedback.json`

### modifications/
存储用户对生成代码的修改记录，包括：
- 修改前后对比
- 修改类型分类
- 修改原因推断
- 受影响区域

**文件命名**: `YYYYMMDD_<modification_id>.json`

### patterns/
存储发现的模式，包括：
- 高频组合模式
- 成功序列模式
- 失败模式（反模式）
- 跨领域迁移模式

**文件命名**: `YYYYMMDD_patterns.json`

### weights/
存储搜索权重数据，包括：
- 当前权重配置
- 权重历史变化
- A/B 测试结果
- 优化建议

**文件命名**: `YYYYMMDD_weights.json`

## 数据保留策略

- **默认保留**: 90 天
- **归档策略**: 超过 90 天的数据可以归档（压缩但保留）
- **清理工具**: 使用 `scripts/cleanup.py` 进行数据清理

## 隐私保护

所有敏感信息都会被自动匿名化：
- API keys
- User credentials
- Personal information
- Proprietary code snippets

## 数据使用

这些数据用于：
1. **质量评估**: 计算各维度的质量分数
2. **模式发现**: 挖掘成功和失败的模式
3. **权重优化**: 调整搜索权重以提高相关性
4. **框架进化**: A/B 测试和自动化改进
5. **知识迁移**: 跨领域和跨技术栈的知识复用
6. **报告生成**: 生成周报、月报和仪表板

## 数据格式

所有数据文件均为 JSON 格式，便于分析和处理。

示例查看：请参考 `data/examples/` 目录中的样例文件。
