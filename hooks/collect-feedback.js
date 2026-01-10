/**
 * Self-Evolution Skill - SessionEnd Hook
 *
 * 在会话结束时收集用户反馈数据
 * - 检测用户对生成代码的修改
 * - 分析修改模式（哪些被保留、哪些被删除、哪些被修改）
 * - 推断隐式反馈（修改 = 不满意，保留 = 满意）
 *
 * 注意：本文件为示例实现，生产环境需要：
 * 1. 完整的错误处理和日志记录
 * 2. 数据验证和清理
 * 3. 异步处理避免阻塞
 * 4. 隐私保护和数据匿名化
 */

const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');

// 配置
const DATA_DIR = path.join(__dirname, '../data/feedback');
const MODIFICATIONS_DIR = path.join(__dirname, '../data/modifications');

/**
 * SessionEnd Hook 主函数
 * @param {Object} context - Claude Code 提供的会话上下文
 * @returns {Object} Hook 结果 { allow: true }
 */
module.exports = async function collectFeedback(context) {
  try {
    // 确保数据目录存在
    await ensureDirectories();

    // 收集会话摘要
    const sessionSummary = await collectSessionSummary(context);

    // 检测用户修改
    const modifications = await detectUserModifications(context);

    // 分析修改模式
    const feedbackAnalysis = analyzeModifications(modifications, sessionSummary);

    // 保存反馈数据
    await saveFeedback(sessionSummary.session_id, feedbackAnalysis);

    // 如果有显式评分，记录下来
    if (context.userRating) {
      await saveUserRating(sessionSummary.session_id, context.userRating);
    }

    console.log(`[Self-Evolution] Session ${sessionSummary.session_id}: Feedback collected`);

    return { allow: true };
  } catch (error) {
    console.error('[Self-Evolution] Error collecting feedback:', error);
    // 即使出错也允许会话结束
    return { allow: true };
  }
};

/**
 * 确保必要的目录存在
 */
async function ensureDirectories() {
  await fs.mkdir(DATA_DIR, { recursive: true });
  await fs.mkdir(MODIFICATIONS_DIR, { recursive: true });
}

/**
 * 收集会话摘要信息
 * @param {Object} context - 会话上下文
 * @returns {Object} 会话摘要
 */
async function collectSessionSummary(context) {
  const now = new Date();
  const sessionId = generateSessionId(now);

  return {
    session_id: sessionId,
    timestamp: now.toISOString(),
    duration_minutes: calculateSessionDuration(context),
    skills_used: extractSkillsUsed(context),
    total_skill_invocations: countSkillInvocations(context),
    files_modified: context.filesModified?.length || 0,
    user_messages: context.messageHistory?.filter(m => m.role === 'user').length || 0
  };
}

/**
 * 检测用户对 Claude 生成内容的修改
 * @param {Object} context - 会话上下文
 * @returns {Array} 修改记录列表
 */
async function detectUserModifications(context) {
  const modifications = [];

  // 遍历所有被修改的文件
  if (context.filesModified && Array.isArray(context.filesModified)) {
    for (const file of context.filesModified) {
      const modification = await analyzeFileModification(file, context);
      if (modification) {
        modifications.push(modification);
      }
    }
  }

  return modifications;
}

/**
 * 分析单个文件的修改
 * @param {Object} file - 文件信息
 * @param {Object} context - 会话上下文
 * @returns {Object|null} 修改分析结果
 */
async function analyzeFileModification(file, context) {
  try {
    // 查找 Claude 最后一次写入该文件的内容
    const claudeVersion = findClaudeGeneratedVersion(file.path, context);
    if (!claudeVersion) {
      return null; // 不是 Claude 生成的文件
    }

    // 读取用户最终版本
    const userVersion = await fs.readFile(file.path, 'utf-8');

    // 计算差异
    const diff = calculateDiff(claudeVersion, userVersion);

    return {
      file_path: file.path,
      claude_version_length: claudeVersion.length,
      user_version_length: userVersion.length,
      modifications: {
        lines_added: diff.added,
        lines_removed: diff.removed,
        lines_modified: diff.modified,
        percentage_changed: diff.changePercentage
      },
      modification_categories: categorizeModifications(diff),
      skill_that_generated: file.generatedBySkill || 'unknown'
    };
  } catch (error) {
    console.error(`[Self-Evolution] Error analyzing file ${file.path}:`, error);
    return null;
  }
}

/**
 * 查找 Claude 生成的文件版本
 * @param {string} filePath - 文件路径
 * @param {Object} context - 会话上下文
 * @returns {string|null} Claude 生成的内容
 */
function findClaudeGeneratedVersion(filePath, context) {
  // 从消息历史中查找最后一次 Write/Edit 该文件的内容
  if (!context.messageHistory) {
    return null;
  }

  for (let i = context.messageHistory.length - 1; i >= 0; i--) {
    const message = context.messageHistory[i];
    if (message.role === 'assistant' && message.toolUses) {
      for (const toolUse of message.toolUses) {
        if ((toolUse.name === 'Write' || toolUse.name === 'Edit') &&
            toolUse.input?.file_path === filePath) {
          return toolUse.input.content || toolUse.input.new_string || '';
        }
      }
    }
  }

  return null;
}

/**
 * 计算两个文本版本之间的差异
 * @param {string} original - 原始文本
 * @param {string} modified - 修改后文本
 * @returns {Object} 差异统计
 */
function calculateDiff(original, modified) {
  const originalLines = original.split('\n');
  const modifiedLines = modified.split('\n');

  // 简化的差异计算（生产环境应使用专业 diff 库如 diff）
  const added = modifiedLines.length - originalLines.length;
  const removed = added < 0 ? Math.abs(added) : 0;
  const modified_count = Math.min(originalLines.length, modifiedLines.length);

  let changedLines = 0;
  for (let i = 0; i < modified_count; i++) {
    if (originalLines[i] !== modifiedLines[i]) {
      changedLines++;
    }
  }

  const totalLines = Math.max(originalLines.length, modifiedLines.length);
  const changePercentage = totalLines > 0 ? (changedLines / totalLines) * 100 : 0;

  return {
    added: Math.max(0, added),
    removed,
    modified: changedLines,
    changePercentage: Math.round(changePercentage * 10) / 10
  };
}

/**
 * 将修改分类为不同类型
 * @param {Object} diff - 差异统计
 * @returns {Array} 修改类别
 */
function categorizeModifications(diff) {
  const categories = [];

  if (diff.changePercentage < 5) {
    categories.push('minor_tweaks'); // 微调（< 5% 修改）
  } else if (diff.changePercentage < 20) {
    categories.push('moderate_changes'); // 中等修改（5-20%）
  } else if (diff.changePercentage < 50) {
    categories.push('significant_rewrite'); // 重大重写（20-50%）
  } else {
    categories.push('complete_overhaul'); // 完全重写（> 50%）
  }

  if (diff.added > diff.removed) {
    categories.push('expansion'); // 扩展内容
  } else if (diff.removed > diff.added) {
    categories.push('reduction'); // 精简内容
  }

  return categories;
}

/**
 * 分析修改模式，提取反馈信号
 * @param {Array} modifications - 修改列表
 * @param {Object} sessionSummary - 会话摘要
 * @returns {Object} 反馈分析
 */
function analyzeModifications(modifications, sessionSummary) {
  const analysis = {
    session_id: sessionSummary.session_id,
    timestamp: sessionSummary.timestamp,
    overall_satisfaction: calculateSatisfactionScore(modifications),
    modification_patterns: {},
    skill_feedback: {}
  };

  // 按 skill 分组统计
  const bySkill = {};
  for (const mod of modifications) {
    const skill = mod.skill_that_generated;
    if (!bySkill[skill]) {
      bySkill[skill] = {
        total_files: 0,
        total_changes: 0,
        avg_change_percentage: 0,
        categories: {}
      };
    }
    bySkill[skill].total_files++;
    bySkill[skill].total_changes += mod.modifications.lines_modified;
    bySkill[skill].avg_change_percentage += mod.modifications.percentage_changed;

    // 统计修改类别
    for (const category of mod.modification_categories) {
      bySkill[skill].categories[category] = (bySkill[skill].categories[category] || 0) + 1;
    }
  }

  // 计算平均值
  for (const skill in bySkill) {
    if (bySkill[skill].total_files > 0) {
      bySkill[skill].avg_change_percentage =
        Math.round((bySkill[skill].avg_change_percentage / bySkill[skill].total_files) * 10) / 10;
    }
  }

  analysis.skill_feedback = bySkill;

  // 提取常见修改模式
  const allCategories = modifications.flatMap(m => m.modification_categories);
  const categoryCount = {};
  for (const cat of allCategories) {
    categoryCount[cat] = (categoryCount[cat] || 0) + 1;
  }
  analysis.modification_patterns = categoryCount;

  return analysis;
}

/**
 * 计算整体满意度分数（基于修改程度）
 * @param {Array} modifications - 修改列表
 * @returns {number} 满意度分数 (0-100)
 */
function calculateSatisfactionScore(modifications) {
  if (modifications.length === 0) {
    return 100; // 没有修改 = 完全满意
  }

  // 计算平均修改百分比
  const avgChange = modifications.reduce((sum, m) =>
    sum + m.modifications.percentage_changed, 0) / modifications.length;

  // 转换为满意度分数（修改越少 = 满意度越高）
  // 0% 修改 = 100 分，100% 修改 = 0 分
  return Math.max(0, Math.min(100, Math.round(100 - avgChange)));
}

/**
 * 保存反馈数据到文件
 * @param {string} sessionId - 会话 ID
 * @param {Object} feedbackAnalysis - 反馈分析结果
 */
async function saveFeedback(sessionId, feedbackAnalysis) {
  const filename = `${sessionId}_feedback.json`;
  const filepath = path.join(DATA_DIR, filename);

  await fs.writeFile(filepath, JSON.stringify(feedbackAnalysis, null, 2), 'utf-8');
}

/**
 * 保存用户显式评分
 * @param {string} sessionId - 会话 ID
 * @param {Object} rating - 用户评分
 */
async function saveUserRating(sessionId, rating) {
  const filename = `${sessionId}_rating.json`;
  const filepath = path.join(DATA_DIR, filename);

  const ratingData = {
    session_id: sessionId,
    timestamp: new Date().toISOString(),
    rating: rating.score,
    comment: rating.comment || '',
    aspects: rating.aspects || {}
  };

  await fs.writeFile(filepath, JSON.stringify(ratingData, null, 2), 'utf-8');
}

// ========== 辅助函数 ==========

function generateSessionId(date) {
  const dateStr = date.toISOString().slice(0, 10).replace(/-/g, '');
  const random = crypto.randomBytes(4).toString('hex');
  return `${dateStr}_${random}`;
}

function calculateSessionDuration(context) {
  if (!context.startTime || !context.endTime) {
    return 0;
  }
  const duration = (context.endTime - context.startTime) / 1000 / 60;
  return Math.round(duration * 10) / 10;
}

function extractSkillsUsed(context) {
  const skills = new Set();
  if (context.messageHistory) {
    for (const message of context.messageHistory) {
      if (message.role === 'assistant' && message.toolUses) {
        for (const toolUse of message.toolUses) {
          if (toolUse.name === 'Skill' && toolUse.input?.skill) {
            skills.add(toolUse.input.skill);
          }
        }
      }
    }
  }
  return Array.from(skills);
}

function countSkillInvocations(context) {
  let count = 0;
  if (context.messageHistory) {
    for (const message of context.messageHistory) {
      if (message.role === 'assistant' && message.toolUses) {
        for (const toolUse of message.toolUses) {
          if (toolUse.name === 'Skill') {
            count++;
          }
        }
      }
    }
  }
  return count;
}
