# Self-Evolution Skill - 技能自我进化系统

## 🎯 核心概念

Self-Evolution 是一个**元级 (Meta-level) Skill**，能够监控、分析和优化所有其他技能的表现，实现技能系统的自我进化和持续改进。

### 核心能力

1. **质量评估** - 分析生成的提示词和输出质量
2. **反馈学习** - 从用户修改和评价中学习
3. **模式发现** - 识别高频组合和成功模式
4. **权重优化** - 自动调整元素复用性评分
5. **框架进化** - 改进 skill 配置和规则
6. **知识迁移** - 跨领域知识复用和迁移

---

## 🏗️ 架构设计

```
Self-Evolution Skill
├── 模块1: 质量评估器 (Quality Evaluator)
│   └── 分析生成内容的质量指标
├── 模块2: 反馈学习器 (Feedback Learner)
│   └── 从用户修改中提取改进点
├── 模块3: 模式发现器 (Pattern Discoverer)
│   └── 识别高频元素组合和成功模式
├── 模块4: 权重优化器 (Weight Optimizer)
│   └── 自动调整元素复用性评分
├── 模块5: 框架进化器 (Framework Evolver)
│   └── 优化 skill 配置和规则
└── 模块6: 知识迁移器 (Knowledge Transferer)
    └── 跨领域知识复用和迁移
```

---

## 📊 数据收集机制

### 自动收集数据

每次 skill 执行时自动记录：

```json
{
  "session_id": "sess_20260110_001",
  "timestamp": "2026-01-10T10:30:00Z",
  "skill_name": "ui-ux-pro-max",
  "trigger": {
    "user_request": "设计 SaaS 定价页面",
    "detected_keywords": ["saas", "pricing", "page", "design"],
    "context": {
      "tech_stack": "html-tailwind",
      "project_type": "landing-page"
    }
  },
  "execution": {
    "searches_performed": [
      {"domain": "product", "query": "saas pricing", "results": 3},
      {"domain": "style", "query": "minimalism modern", "results": 5},
      {"domain": "color", "query": "saas", "results": 2}
    ],
    "elements_used": {
      "styles": ["minimalism", "glassmorphism"],
      "colors": ["#0F172A", "#3B82F6", "#F3F4F6"],
      "fonts": ["Inter", "Space Grotesk"],
      "components": ["pricing-card", "cta-button", "feature-grid"]
    },
    "duration_ms": 1250
  },
  "output": {
    "code_lines": 450,
    "components_count": 8,
    "has_responsive": true,
    "has_dark_mode": true
  },
  "user_feedback": {
    "modified": false,
    "rating": null,
    "comments": []
  }
}
```

### 反馈收集方式

1. **隐式反馈** - 自动检测用户修改
   - 代码修改率（修改行数 / 总行数）
   - 修改类型（样式、结构、逻辑）
   - 修改时间（生成后多久修改）

2. **显式反馈** - 用户主动评价
   - 质量评分（1-5星）
   - 具体问题标注
   - 改进建议

3. **使用反馈** - 长期使用数据
   - 复用频率
   - 迭代次数
   - 最终保留率

---

## 📦 实现状态

### ✅ Phase 1: 数据收集系统（已完成）

**状态**: 生产就绪

**包含组件**:
- `hooks/record-execution.js` - PostToolUse Hook，自动记录执行数据
- `hooks/collect-feedback.js` - SessionEnd Hook，收集用户反馈
- `hooks/detect-modifications.js` - OnFileEdit Hook，实时追踪修改
- `scripts/cleanup.py` - 数据清理和归档工具
- `scripts/weekly_report.py` - 周报生成工具
- `config.yaml` - 统一配置文件
- `data/` - 数据存储目录结构

**数据流**:
```
Skill 执行 → record-execution.js → 质量评估 → 保存执行记录
用户修改 → detect-modifications.js → 追踪修改 → 保存修改记录
会话结束 → collect-feedback.js → 分析满意度 → 保存反馈记录
```

### ✅ Phase 2: 权重优化系统（已完成）

**状态**: 生产就绪

**包含组件**:
- `scripts/weight_optimizer.py` - 权重优化主模块
  - 基于质量和使用频率计算权重
  - 时间衰减（半衰期 60 天）
  - 平滑因子防止过度波动
  - 支持增量更新
- `scripts/ab_testing.py` - A/B 测试统计验证
  - Welch's t-test 显著性检验
  - Cohen's d 效应量计算
  - 置信区间评估

**算法**:
```python
Weight(t) = α × Quality + (1-α) × Usage_Frequency
          × Decay_Factor(t) × (1 - Smoothing)
          + Previous_Weight × Smoothing
```

**使用方法**:
```bash
# 优化权重（分析最近 30 天数据）
python scripts/weight_optimizer.py --days 30

# A/B 测试（对比两个版本）
python scripts/ab_testing.py version_a.json version_b.json
```

### ✅ Phase 3: 核心分析模块（已完成）

**状态**: 生产就绪

**包含组件**:

#### 1. 质量评估器 (`quality_evaluator.py`)
- **5 维度评估**:
  - Completeness (完整性) - 是否包含所有必需元素
  - Consistency (一致性) - 代码风格、命名统一性
  - Professionalism (专业性) - 最佳实践遵循度
  - Performance (性能) - 代码效率和资源使用
  - Maintainability (可维护性) - 可读性、模块化程度
- **综合评分**: 加权平均，输出 0-1 范围分数
- **问题诊断**: 自动识别并列出问题清单

**使用**:
```bash
python scripts/quality_evaluator.py execution_data.json
```

#### 2. 模式发现器 (`pattern_discovery.py`)
- **Apriori 算法**: 频繁项集挖掘
- **成功模式识别**: 识别导致高质量输出的元素组合
- **失败模式识别**: 识别应避免的反模式
- **搜索序列分析**: 识别有效的搜索流程

**使用**:
```bash
python scripts/pattern_discovery.py --days 30 --min-support 0.1
```

#### 3. 知识迁移器 (`knowledge_transfer.py`)
- **跨域相似度**: 余弦相似度计算
- **模式适配性**: 评估模式在目标域的适用性
- **迁移推荐**: 为新领域提供基于相似域的推荐
- **支持 10+ 产品类型**: SaaS, 电商, 作品集, 博客, 仪表板等

**使用**:
```bash
python scripts/knowledge_transfer.py --days 90 --similarity 0.6
```

### ⏳ Phase 4: 高级功能（计划中）

- 框架进化器 (Framework Evolver) - 自动优化 Skill 配置
- 实时仪表板 (Dashboard) - 可视化分析界面
- 自动模板生成 (Template Generator) - 基于模式自动生成模板

---

## 🧠 六大核心模块

### 模块1: 质量评估器 (Quality Evaluator)

**职责**: 自动评估生成内容的质量

#### 评估维度

| 维度 | 指标 | 计算方法 |
|------|------|----------|
| **完整性** | Completeness Score | 必需元素覆盖率 × 100% |
| **一致性** | Consistency Score | 样式统一度 × 设计系统匹配度 |
| **专业性** | Professionalism | 最佳实践遵守率 × 无障碍合规率 |
| **性能** | Performance | 代码效率 × 加载速度预估 |
| **可维护性** | Maintainability | 代码结构清晰度 × 注释质量 |

#### 评分算法

```python
def calculate_quality_score(output):
    scores = {
        'completeness': check_required_elements(output),
        'consistency': check_design_consistency(output),
        'professionalism': check_best_practices(output),
        'performance': estimate_performance(output),
        'maintainability': analyze_code_structure(output)
    }

    # 加权平均
    weights = {
        'completeness': 0.25,
        'consistency': 0.20,
        'professionalism': 0.25,
        'performance': 0.15,
        'maintainability': 0.15
    }

    total_score = sum(scores[k] * weights[k] for k in scores)
    return {
        'total': total_score,
        'breakdown': scores,
        'grade': get_grade(total_score)
    }
```

#### 自动改进建议

```python
def generate_improvement_suggestions(quality_report):
    suggestions = []

    if quality_report['completeness'] < 0.8:
        suggestions.append({
            'type': 'missing_elements',
            'severity': 'high',
            'message': '缺少必需元素',
            'missing': find_missing_elements(output)
        })

    if quality_report['consistency'] < 0.7:
        suggestions.append({
            'type': 'inconsistent_styling',
            'severity': 'medium',
            'message': '样式不一致',
            'conflicts': find_style_conflicts(output)
        })

    return suggestions
```

---

### 模块2: 反馈学习器 (Feedback Learner)

**职责**: 从用户修改中提取改进点

#### 修改检测

```python
def detect_user_modifications(original, modified):
    diff = unified_diff(original, modified)

    modifications = {
        'style_changes': [],
        'structure_changes': [],
        'logic_changes': [],
        'additions': [],
        'deletions': []
    }

    for change in diff:
        category = classify_change(change)
        modifications[category].append({
            'line': change.line_number,
            'type': change.type,
            'content': change.content,
            'reason': infer_reason(change)
        })

    return modifications
```

#### 学习模式提取

```python
def extract_learning_patterns(modifications_history):
    patterns = []

    # 频繁修改模式
    frequent_changes = find_frequent_changes(modifications_history)
    for change in frequent_changes:
        patterns.append({
            'type': 'frequent_modification',
            'pattern': change.pattern,
            'frequency': change.count,
            'suggestion': generate_default_fix(change)
        })

    # 用户偏好
    user_preferences = extract_preferences(modifications_history)
    patterns.append({
        'type': 'user_preference',
        'preferences': user_preferences
    })

    return patterns
```

#### 自动调整规则

```yaml
# 学习到的规则示例
learned_rules:
  - id: rule_001
    pattern: "用户总是将 bg-white/10 改为 bg-white/80"
    context: "明亮模式下的玻璃卡片"
    action: "默认使用 bg-white/80"
    confidence: 0.92
    occurrences: 12

  - id: rule_002
    pattern: "用户删除所有 emoji 图标，替换为 SVG"
    context: "UI 图标"
    action: "直接使用 SVG 图标库"
    confidence: 0.95
    occurrences: 18
```

---

### 模块3: 模式发现器 (Pattern Discoverer)

**职责**: 识别高频元素组合和成功模式

#### 高频组合挖掘

```python
def mine_frequent_combinations(usage_history):
    # 使用 Apriori 算法挖掘频繁项集
    combinations = []

    # 样式组合
    style_combinations = apriori(
        transactions=[h['elements_used']['styles'] for h in usage_history],
        min_support=0.3
    )

    # 颜色组合
    color_combinations = apriori(
        transactions=[h['elements_used']['colors'] for h in usage_history],
        min_support=0.4
    )

    return {
        'styles': style_combinations,
        'colors': color_combinations,
        'confidence': calculate_confidence(combinations)
    }
```

#### 成功模式识别

```python
def identify_success_patterns(execution_history):
    """识别高质量输出的共同特征"""
    high_quality = [h for h in execution_history
                    if h['quality_score'] >= 0.85
                    and h['user_feedback']['rating'] >= 4]

    patterns = {
        'common_searches': find_common_search_sequences(high_quality),
        'common_elements': find_common_elements(high_quality),
        'common_structures': find_common_structures(high_quality)
    }

    return patterns
```

#### 模板自动生成

```python
def generate_templates_from_patterns(patterns):
    """从识别的模式自动生成设计模板"""
    templates = []

    for pattern in patterns['common_structures']:
        if pattern['frequency'] > 0.7:
            template = {
                'name': generate_template_name(pattern),
                'category': pattern['category'],
                'elements': pattern['elements'],
                'structure': pattern['structure'],
                'usage_count': pattern['count'],
                'success_rate': pattern['success_rate']
            }
            templates.append(template)

    return templates
```

---

### 模块4: 权重优化器 (Weight Optimizer)

**职责**: 自动调整元素复用性评分

#### 动态权重调整

```python
def optimize_element_weights(usage_stats):
    """基于使用统计优化元素权重"""
    for element in database:
        # 计算新权重
        usage_score = calculate_usage_score(element, usage_stats)
        quality_score = calculate_quality_score(element, usage_stats)
        feedback_score = calculate_feedback_score(element, usage_stats)

        # 加权组合
        new_weight = (
            usage_score * 0.4 +
            quality_score * 0.4 +
            feedback_score * 0.2
        )

        # 平滑更新（避免剧烈变化）
        element['weight'] = (
            element['weight'] * 0.7 +
            new_weight * 0.3
        )
```

#### 衰减机制

```python
def apply_time_decay(elements):
    """对长期未使用的元素降低权重"""
    current_time = datetime.now()

    for element in elements:
        days_since_last_use = (current_time - element['last_used']).days

        if days_since_last_use > 30:
            decay_factor = exp(-days_since_last_use / 100)
            element['weight'] *= decay_factor
```

#### 趋势检测

```python
def detect_trending_elements(usage_history, window_days=30):
    """检测最近流行的设计元素"""
    recent = filter_recent(usage_history, window_days)

    trends = []
    for element in database:
        recent_usage = count_usage(element, recent)
        historical_usage = count_usage(element, usage_history)

        growth_rate = recent_usage / historical_usage

        if growth_rate > 1.5:  # 增长超过50%
            trends.append({
                'element': element,
                'growth_rate': growth_rate,
                'category': 'rising'
            })

    return trends
```

---

### 模块5: 框架进化器 (Framework Evolver)

**职责**: 优化 skill 配置和规则

#### 规则优化

```python
def optimize_framework_rules(performance_data):
    """基于性能数据优化框架规则"""
    rules = load_rules('prompt_framework.yaml')

    for rule in rules:
        # 分析规则效果
        effectiveness = analyze_rule_effectiveness(rule, performance_data)

        if effectiveness < 0.5:
            # 规则效果差，尝试优化
            optimized_rule = optimize_rule(rule, performance_data)
            rules.update(optimized_rule)

        elif effectiveness > 0.9:
            # 规则效果好，提升优先级
            rule['priority'] += 1

    save_rules(rules, 'prompt_framework.yaml')
```

#### 搜索策略优化

```python
def optimize_search_strategy(search_history):
    """优化搜索顺序和参数"""
    # 分析哪些搜索顺序效果最好
    sequences = extract_search_sequences(search_history)

    best_sequence = max(sequences, key=lambda s: s['success_rate'])

    # 更新默认搜索顺序
    update_default_sequence(best_sequence)

    # 优化搜索参数
    for domain in ['product', 'style', 'typography', 'color']:
        optimal_limit = find_optimal_result_limit(domain, search_history)
        update_domain_config(domain, {'limit': optimal_limit})
```

#### A/B 测试框架

```python
def ab_test_framework_changes(change_proposal):
    """对框架更改进行 A/B 测试"""
    test_config = {
        'variant_a': current_framework,  # 控制组
        'variant_b': apply_changes(current_framework, change_proposal),  # 实验组
        'traffic_split': 0.5,
        'duration_days': 14,
        'metrics': ['quality_score', 'user_satisfaction', 'execution_time']
    }

    results = run_ab_test(test_config)

    if results['variant_b']['quality_score'] > results['variant_a']['quality_score']:
        if results['p_value'] < 0.05:  # 统计显著
            apply_changes_permanently(change_proposal)
```

---

### 模块6: 知识迁移器 (Knowledge Transferer)

**职责**: 跨领域知识复用和迁移

#### 领域相似度计算

```python
def calculate_domain_similarity(domain_a, domain_b):
    """计算两个领域的相似度"""
    similarity_scores = {
        'element_overlap': jaccard_similarity(
            domain_a['elements'],
            domain_b['elements']
        ),
        'pattern_similarity': cosine_similarity(
            domain_a['patterns'],
            domain_b['patterns']
        ),
        'structure_similarity': structural_similarity(
            domain_a['structure'],
            domain_b['structure']
        )
    }

    return weighted_average(similarity_scores)
```

#### 知识迁移

```python
def transfer_knowledge(source_domain, target_domain):
    """从源领域迁移知识到目标领域"""
    transferable_patterns = []

    # 找出可迁移的模式
    for pattern in source_domain['success_patterns']:
        if is_transferable(pattern, target_domain):
            adapted_pattern = adapt_pattern(pattern, target_domain)
            transferable_patterns.append(adapted_pattern)

    # 应用迁移
    for pattern in transferable_patterns:
        target_domain['patterns'].append(pattern)
        log_transfer(source_domain, target_domain, pattern)

    return transferable_patterns
```

#### 跨栈适配

```python
def adapt_across_stacks(knowledge, source_stack, target_stack):
    """在不同技术栈之间适配知识"""
    adaptations = {
        'html-tailwind': {
            'to_react': convert_tailwind_to_react_classes,
            'to_vue': convert_tailwind_to_vue_classes,
            'to_swiftui': convert_web_to_swiftui
        },
        'react': {
            'to_vue': convert_react_to_vue,
            'to_svelte': convert_react_to_svelte
        }
    }

    adapter = adaptations[source_stack][f'to_{target_stack}']
    return adapter(knowledge)
```

---

## 🚀 使用方式

### 自动模式（推荐）

Self-Evolution 在后台自动运行，无需显式调用：

```bash
# 正常使用任何 skill
"设计一个 SaaS 定价页面"

# Self-Evolution 自动：
# 1. 记录执行数据
# 2. 评估输出质量
# 3. 收集用户反馈
# 4. 优化权重和规则
```

### 手动分析

查看和管理进化数据：

```bash
# 查看质量报告
/self-evolution:quality-report

# 查看学习到的模式
/self-evolution:patterns

# 查看权重变化
/self-evolution:weights

# 触发手动优化
/self-evolution:optimize

# 导出进化数据
/self-evolution:export
```

---

## 📈 进化效果追踪

### 关键指标 (KPI)

| 指标 | 目标 | 计算方式 |
|------|------|----------|
| **质量提升率** | 每月 +5% | 平均质量分增长率 |
| **用户满意度** | ≥ 4.5/5 | 用户评分平均值 |
| **修改率下降** | 每月 -10% | 用户修改比例 |
| **复用率提升** | 每月 +8% | 元素复用次数增长 |
| **执行效率** | < 2秒 | 平均执行时间 |

### 进化仪表板

```markdown
## Self-Evolution Dashboard

### 整体健康度: 87/100 ⬆️ (+5)

#### 本周进化数据
- 总执行次数: 245
- 平均质量分: 0.87 (+0.03)
- 用户满意度: 4.6/5 (+0.2)
- 修改率: 12% (-3%)

#### 学习成果
- 新发现模式: 3
- 规则优化: 5
- 权重调整: 18
- 知识迁移: 2

#### Top 改进
1. 明亮模式对比度问题解决 ✅
2. SVG 图标使用提升 50%
3. 响应式断点优化
4. 颜色调色板更新

#### 待优化项
1. 复杂布局生成耗时较长
2. 某些字体组合覆盖不足
3. 动画性能优化空间
```

---

## 🔧 配置文件

### self-evolution-config.yaml

```yaml
# Self-Evolution Skill 配置

# 数据收集
data_collection:
  enabled: true
  storage_path: ".claude/skills/self-evolution/data"
  retention_days: 90
  anonymize: true

# 质量评估
quality_evaluator:
  enabled: true
  evaluation_mode: "automatic"  # automatic | on_demand
  thresholds:
    completeness: 0.8
    consistency: 0.7
    professionalism: 0.75
    performance: 0.6
    maintainability: 0.7

# 反馈学习
feedback_learner:
  enabled: true
  modification_tracking: true
  learning_rate: 0.3
  min_confidence: 0.7

# 模式发现
pattern_discoverer:
  enabled: true
  min_support: 0.3
  min_confidence: 0.6
  pattern_types:
    - "element_combinations"
    - "search_sequences"
    - "success_patterns"

# 权重优化
weight_optimizer:
  enabled: true
  update_frequency: "daily"  # hourly | daily | weekly
  smoothing_factor: 0.3
  time_decay_enabled: true
  decay_half_life_days: 60

# 框架进化
framework_evolver:
  enabled: true
  ab_testing: true
  auto_apply_threshold: 0.95
  manual_review_threshold: 0.7

# 知识迁移
knowledge_transferer:
  enabled: true
  cross_domain: true
  cross_stack: true
  similarity_threshold: 0.6

# 报告
reporting:
  dashboard_enabled: true
  dashboard_path: ".claude/skills/self-evolution/dashboard.md"
  update_frequency: "weekly"
  export_format: "json"  # json | csv | markdown
```

---

## 📁 数据文件结构

```
.claude/skills/self-evolution/
├── README.md                       # 本文档
├── config.yaml                     # 配置文件
├── data/                           # 数据存储
│   ├── executions/                 # 执行记录
│   │   ├── 2026-01/
│   │   │   ├── sess_20260110_001.json
│   │   │   └── sess_20260110_002.json
│   │   └── index.db
│   ├── feedback/                   # 反馈数据
│   │   ├── modifications.json
│   │   ├── ratings.json
│   │   └── comments.json
│   ├── patterns/                   # 发现的模式
│   │   ├── frequent_combinations.json
│   │   ├── success_patterns.json
│   │   └── templates.json
│   ├── weights/                    # 权重历史
│   │   ├── current_weights.json
│   │   ├── weight_history.json
│   │   └── trends.json
│   └── rules/                      # 学习到的规则
│       ├── learned_rules.yaml
│       └── rule_history.json
├── reports/                        # 报告输出
│   ├── dashboard.md
│   ├── weekly_reports/
│   └── exports/
└── scripts/                        # 辅助脚本
    ├── analyze.py
    ├── optimize.py
    └── export.py
```

---

## 🔄 集成方式

### 与现有 Skills 集成

Self-Evolution 通过钩子系统集成：

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

### 数据流

```
Skill 执行
    ↓
[PostToolUse Hook] 记录执行数据
    ↓
[质量评估器] 评估输出质量
    ↓
[反馈学习器] 检测用户修改
    ↓
[模式发现器] 挖掘成功模式
    ↓
[权重优化器] 调整元素权重
    ↓
[框架进化器] 优化规则配置
    ↓
[知识迁移器] 跨域知识迁移
    ↓
[报告生成] 更新仪表板
```

---

## 🎯 进化目标

### 短期目标 (1个月)

- ✅ 质量分从 0.75 提升到 0.85
- ✅ 修改率从 20% 降低到 12%
- ✅ 用户满意度从 4.0 提升到 4.5
- ✅ 发现并创建 10 个高质量模板

### 中期目标 (3个月)

- ✅ 质量分提升到 0.90+
- ✅ 修改率降低到 8%
- ✅ 用户满意度达到 4.7+
- ✅ 知识迁移覆盖 5 个领域
- ✅ 执行效率提升 30%

### 长期目标 (6个月)

- ✅ 质量分稳定在 0.92+
- ✅ 修改率降低到 5%
- ✅ 用户满意度稳定在 4.8+
- ✅ 自动生成 50+ 设计模板
- ✅ 实现跨栈知识迁移
- ✅ 框架规则完全优化

---

## 🚨 注意事项

### 隐私保护

- ✅ 所有数据本地存储
- ✅ 支持数据匿名化
- ✅ 可配置数据保留期
- ✅ 用户可随时清除数据

### 性能影响

- ✅ 数据收集异步进行，不影响主流程
- ✅ 优化和分析在后台定期执行
- ✅ 可配置更新频率
- ✅ 支持按需禁用模块

### 安全性

- ✅ 不收集敏感代码内容
- ✅ 不上传到外部服务
- ✅ 权限限制在 skill 范围内
- ✅ 完全透明和可审计

---

## 📚 相关文档

- [ARCHITECTURE.md](./ARCHITECTURE.md) - 详细架构设计
- [ALGORITHMS.md](./ALGORITHMS.md) - 算法实现细节
- [API.md](./API.md) - 编程接口文档
- [CHANGELOG.md](./CHANGELOG.md) - 更新日志

---

## 🤝 贡献

欢迎贡献改进建议和代码！

### 改进方向

- 新的质量评估指标
- 更智能的模式识别算法
- 跨栈适配规则
- 领域特定优化
- 可视化仪表板增强

---

**最后更新**: 2026-01-11
**版本**: 1.0.3
**状态**: Phase 1-3 已完成，可投入使用
