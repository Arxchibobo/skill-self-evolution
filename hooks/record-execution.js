/**
 * Self-Evolution: PostToolUse Hook - 记录 Skill 执行数据
 *
 * 在每次 Skill 执行后自动触发，收集执行数据用于后续分析
 *
 * 注意：本文件为示例实现，生产环境中应该：
 * 1. 使用 execFileNoThrow 替代 child_process.exec 避免命令注入
 * 2. 添加输入验证和清理
 * 3. 实现完整的错误处理
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execFile } = require('child_process');
const util = require('util');

const execFileAsync = util.promisify(execFile);

// 配置
const CONFIG = {
  dataDir: path.join(process.env.HOME || process.env.USERPROFILE, '.claude/skills/self-evolution/data'),
  executionsDir: 'executions',
  anonymize: true,
  verbose: false,
  enableQualityEvaluation: true  // 启用质量评估
};

/**
 * Hook 主函数
 * @param {Object} context - Claude Code 提供的上下文对象
 */
async function recordExecution(context) {
  try {
    // 只处理 Skill 工具调用
    if (context.tool !== 'Skill') {
      return { allow: true };
    }

    const executionData = collectExecutionData(context);

    // 质量评估（如果启用）
    if (CONFIG.enableQualityEvaluation) {
      try {
        const qualityScores = await evaluateQuality(executionData, context);
        executionData.quality_scores = qualityScores;
      } catch (error) {
        if (CONFIG.verbose) {
          console.log(`[Self-Evolution] 质量评估失败: ${error.message}`);
        }
        // 使用默认分数
        executionData.quality_scores = {
          overall: 0.5,
          dimensions: {},
          note: 'Quality evaluation failed'
        };
      }
    }

    await saveExecutionData(executionData);

    if (CONFIG.verbose) {
      console.log(`[Self-Evolution] 已记录执行数据: ${executionData.session_id}`);
      if (executionData.quality_scores) {
        console.log(`[Self-Evolution] 质量分数: ${executionData.quality_scores.overall}`);
      }
    }

    return { allow: true };
  } catch (error) {
    console.error('[Self-Evolution] 记录执行数据失败:', error);
    // 不阻止执行，即使记录失败
    return { allow: true };
  }
}

/**
 * 评估输出质量
 * @param {Object} executionData - 执行数据
 * @param {Object} context - 上下文
 * @returns {Promise<Object>} 质量分数
 */
async function evaluateQuality(executionData, context) {
  // 构建输入数据
  const evaluationInput = {
    output: {
      files: extractFilesFromContext(context),
      ...executionData.output
    },
    context: {
      required_elements: executionData.trigger.detected_keywords,
      skill_name: executionData.skill_name
    }
  };

  // 写入临时文件
  const tempFile = path.join(CONFIG.dataDir, '.temp_eval_input.json');
  fs.writeFileSync(tempFile, JSON.stringify(evaluationInput, null, 2), 'utf8');

  try {
    // 调用 Python 质量评估器
    const scriptPath = path.join(__dirname, '..', 'scripts', 'quality_evaluator.py');
    const { stdout } = await execFileAsync('python3', [scriptPath, tempFile]);

    const result = JSON.parse(stdout);

    // 清理临时文件
    fs.unlinkSync(tempFile);

    return result;
  } catch (error) {
    // 清理临时文件
    if (fs.existsSync(tempFile)) {
      fs.unlinkSync(tempFile);
    }
    throw error;
  }
}

/**
 * 从上下文提取生成的文件
 */
function extractFilesFromContext(context) {
  const files = {};

  // 从工具调用中提取 Write 操作
  if (context.toolCalls) {
    context.toolCalls.forEach(call => {
      if (call.tool === 'Write' && call.parameters) {
        const filename = path.basename(call.parameters.file_path || 'output.txt');
        files[filename] = call.parameters.content || '';
      }
    });
  }

  // 如果没有文件，使用结果字符串
  if (Object.keys(files).length === 0 && context.result) {
    files['output.txt'] = context.result;
  }

  return files;
}

/**
 * 收集执行数据
 */
function collectExecutionData(context) {
  const now = new Date();
  const sessionId = generateSessionId(now);

  const data = {
    // 基本信息
    session_id: sessionId,
    timestamp: now.toISOString(),
    date: now.toISOString().split('T')[0],

    // Skill 信息
    skill_name: context.parameters?.skill || 'unknown',
    skill_args: context.parameters?.args || '',

    // 触发上下文
    trigger: {
      user_request: extractUserRequest(context),
      detected_keywords: extractKeywords(context),
      context: extractContextInfo(context)
    },

    // 执行信息
    execution: {
      start_time: context.startTime || now.toISOString(),
      duration_ms: calculateDuration(context),
      tool_calls: context.toolCalls || [],
      searches_performed: extractSearches(context),
      elements_used: extractElementsUsed(context)
    },

    // 输出信息
    output: {
      code_lines: countCodeLines(context.result),
      components_count: countComponents(context.result),
      has_responsive: hasResponsiveDesign(context.result),
      has_dark_mode: hasDarkMode(context.result),
      file_operations: countFileOperations(context)
    },

    // 占位符：用户反馈（稍后在 SessionEnd 时更新）
    user_feedback: {
      modified: null,
      rating: null,
      comments: []
    }
  };

  // 匿名化处理
  if (CONFIG.anonymize) {
    data.trigger.user_request = anonymizeText(data.trigger.user_request);
  }

  return data;
}

/**
 * 保存执行数据
 */
async function saveExecutionData(data) {
  // 确保目录存在
  const yearMonth = data.date.substring(0, 7); // YYYY-MM
  const dir = path.join(CONFIG.dataDir, CONFIG.executionsDir, yearMonth);

  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }

  // 保存为 JSON 文件
  const filename = `${data.session_id}.json`;
  const filepath = path.join(dir, filename);

  fs.writeFileSync(filepath, JSON.stringify(data, null, 2), 'utf8');

  // 更新索引
  await updateIndex(data);
}

/**
 * 更新执行索引（用于快速查询）
 */
async function updateIndex(data) {
  const indexPath = path.join(CONFIG.dataDir, CONFIG.executionsDir, 'index.json');

  let index = { executions: [] };
  if (fs.existsSync(indexPath)) {
    const content = fs.readFileSync(indexPath, 'utf8');
    index = JSON.parse(content);
  }

  // 添加新执行记录
  index.executions.push({
    session_id: data.session_id,
    timestamp: data.timestamp,
    skill_name: data.skill_name,
    duration_ms: data.execution.duration_ms,
    date: data.date
  });

  // 只保留最近 1000 条记录的索引
  if (index.executions.length > 1000) {
    index.executions = index.executions.slice(-1000);
  }

  fs.writeFileSync(indexPath, JSON.stringify(index, null, 2), 'utf8');
}

/**
 * 辅助函数
 */

function generateSessionId(date) {
  const dateStr = date.toISOString().split('T')[0].replace(/-/g, '');
  const randomStr = crypto.randomBytes(4).toString('hex');
  return `sess_${dateStr}_${randomStr}`;
}

function extractUserRequest(context) {
  // 从对话历史中提取用户请求
  if (context.conversationHistory) {
    const userMessages = context.conversationHistory.filter(m => m.role === 'user');
    if (userMessages.length > 0) {
      return userMessages[userMessages.length - 1].content;
    }
  }
  return '';
}

function extractKeywords(context) {
  const request = extractUserRequest(context);
  // 简单的关键词提取（实际应用中可以使用更复杂的 NLP）
  const keywords = request
    .toLowerCase()
    .split(/\s+/)
    .filter(word => word.length > 3)
    .slice(0, 10);
  return keywords;
}

function extractContextInfo(context) {
  return {
    tech_stack: detectTechStack(context),
    project_type: detectProjectType(context),
    cwd: context.cwd || process.cwd()
  };
}

function calculateDuration(context) {
  if (context.startTime && context.endTime) {
    const start = new Date(context.startTime);
    const end = new Date(context.endTime);
    return end - start;
  }
  return 0;
}

function extractSearches(context) {
  // 从工具调用中提取搜索操作
  const searches = [];
  if (context.toolCalls) {
    context.toolCalls.forEach(call => {
      if (call.tool === 'Bash' && call.parameters?.command?.includes('search.py')) {
        searches.push({
          domain: extractSearchDomain(call.parameters.command),
          query: extractSearchQuery(call.parameters.command),
          results: null // 需要从结果中提取
        });
      }
    });
  }
  return searches;
}

function extractElementsUsed(context) {
  // 从输出中提取使用的设计元素
  const output = context.result || '';

  return {
    styles: extractStyles(output),
    colors: extractColors(output),
    fonts: extractFonts(output),
    components: extractComponents(output)
  };
}

function extractStyles(output) {
  const styles = [];
  const stylePatterns = [
    /glassmorphism/gi,
    /minimalism/gi,
    /brutalism/gi,
    /neumorphism/gi
  ];

  stylePatterns.forEach(pattern => {
    const matches = output.match(pattern);
    if (matches) {
      styles.push(matches[0].toLowerCase());
    }
  });

  return [...new Set(styles)];
}

function extractColors(output) {
  // 提取 hex 颜色代码
  const colorRegex = /#[0-9A-Fa-f]{6}/g;
  const matches = output.match(colorRegex);
  return matches ? [...new Set(matches)] : [];
}

function extractFonts(output) {
  const fonts = [];
  const fontPattern = /font-family:\s*['"]([^'"]+)['"]/gi;
  let match;

  while ((match = fontPattern.exec(output)) !== null) {
    fonts.push(match[1]);
  }

  return [...new Set(fonts)];
}

function extractComponents(output) {
  // 提取 React 组件或 HTML 元素
  const components = [];

  // React 组件
  const reactPattern = /(?:function|const)\s+([A-Z][A-Za-z0-9]*)/g;
  let match;
  while ((match = reactPattern.exec(output)) !== null) {
    components.push(match[1]);
  }

  return [...new Set(components)];
}

function countCodeLines(output) {
  if (!output) return 0;
  return output.split('\n').filter(line => line.trim().length > 0).length;
}

function countComponents(output) {
  return extractComponents(output).length;
}

function hasResponsiveDesign(output) {
  return /(?:sm:|md:|lg:|xl:|2xl:)|@media|responsive/i.test(output);
}

function hasDarkMode(output) {
  return /dark:|dark\s+mode|darkMode|theme-dark/i.test(output);
}

function countFileOperations(context) {
  if (!context.toolCalls) return 0;

  const fileOps = ['Write', 'Edit', 'Read', 'Glob', 'Grep'];
  return context.toolCalls.filter(call => fileOps.includes(call.tool)).length;
}

function detectTechStack(context) {
  const request = extractUserRequest(context);
  const stacks = {
    'react': /react|jsx|tsx/i,
    'vue': /vue|nuxt/i,
    'svelte': /svelte|sveltekit/i,
    'html-tailwind': /tailwind|html|css/i,
    'nextjs': /next\.js|next/i
  };

  for (const [stack, pattern] of Object.entries(stacks)) {
    if (pattern.test(request)) {
      return stack;
    }
  }

  return 'html-tailwind'; // 默认
}

function detectProjectType(context) {
  const request = extractUserRequest(context).toLowerCase();

  const types = {
    'landing-page': /landing|homepage|首页/,
    'dashboard': /dashboard|admin|仪表板/,
    'e-commerce': /shop|store|商城|电商/,
    'saas': /saas|pricing|定价/,
    'portfolio': /portfolio|作品集/
  };

  for (const [type, pattern] of Object.entries(types)) {
    if (pattern.test(request)) {
      return type;
    }
  }

  return 'general';
}

function extractSearchDomain(command) {
  const match = command.match(/--domain\s+(\w+)/);
  return match ? match[1] : null;
}

function extractSearchQuery(command) {
  const match = command.match(/search\.py\s+"([^"]+)"/);
  return match ? match[1] : null;
}

function anonymizeText(text) {
  // 移除可能的敏感信息
  return text
    .replace(/\b\d{3}-\d{2}-\d{4}\b/g, '[SSN]') // 社保号
    .replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, '[EMAIL]') // 邮箱
    .replace(/\b\d{13,19}\b/g, '[CARD]') // 信用卡号
    .replace(/\b(?:\d{1,3}\.){3}\d{1,3}\b/g, '[IP]'); // IP 地址
}

// 导出
module.exports = recordExecution;

// 如果直接运行（用于测试）
if (require.main === module) {
  const testContext = {
    tool: 'Skill',
    parameters: {
      skill: 'ui-ux-pro-max',
      args: 'design saas pricing page'
    },
    result: `
      function PricingPage() {
        return (
          <div className="bg-white dark:bg-gray-900">
            <h1 className="text-4xl font-bold">Pricing</h1>
          </div>
        );
      }
    `,
    toolCalls: [
      {
        tool: 'Bash',
        parameters: {
          command: 'python3 search.py "saas pricing" --domain product'
        }
      }
    ]
  };

  recordExecution(testContext).then(() => {
    console.log('测试完成');
  });
}
