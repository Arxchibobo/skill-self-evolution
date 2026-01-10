/**
 * Self-Evolution Skill - OnFileEdit Hook
 *
 * 在用户编辑文件时实时检测修改
 * - 追踪用户对 Claude 生成代码的修改
 * - 识别修改类型（样式调整、逻辑更改、重构等）
 * - 为后续分析提供细粒度数据
 *
 * 注意：本文件为示例实现，生产环境需要：
 * 1. 高效的差异计算（避免性能影响）
 * 2. 节流/防抖机制（避免频繁触发）
 * 3. 内存管理（限制缓存大小）
 * 4. 隐私保护（敏感信息过滤）
 */

const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');

// 配置
const DATA_DIR = path.join(__dirname, '../data/modifications');
const CACHE_DIR = path.join(__dirname, '../cache');
const MAX_CACHE_SIZE = 100; // 最多缓存 100 个文件的历史

// 内存缓存：文件路径 -> 修改历史
const modificationCache = new Map();

/**
 * OnFileEdit Hook 主函数
 * @param {Object} context - Claude Code 提供的文件编辑上下文
 * @returns {Object} Hook 结果 { allow: true }
 */
module.exports = async function detectModifications(context) {
  try {
    // 确保数据目录存在
    await ensureDirectories();

    // 检查是否是 Claude 生成的文件
    if (!context.generatedBySkill) {
      return { allow: true }; // 只追踪 Claude 生成的文件
    }

    // 记录修改事件
    const modification = await recordModification(context);

    // 分析修改类型
    const analysis = analyzeModificationType(modification);

    // 保存到缓存和磁盘
    await saveModification(modification, analysis);

    // 清理过期缓存
    cleanupCache();

    return { allow: true };
  } catch (error) {
    console.error('[Self-Evolution] Error detecting modifications:', error);
    return { allow: true }; // 即使出错也允许继续
  }
};

/**
 * 确保必要的目录存在
 */
async function ensureDirectories() {
  await fs.mkdir(DATA_DIR, { recursive: true });
  await fs.mkdir(CACHE_DIR, { recursive: true });
}

/**
 * 记录文件修改事件
 * @param {Object} context - 文件编辑上下文
 * @returns {Object} 修改记录
 */
async function recordModification(context) {
  const now = new Date();
  const filePath = context.filePath;

  // 获取文件的修改历史
  let history = modificationCache.get(filePath);
  if (!history) {
    history = await loadModificationHistory(filePath);
    modificationCache.set(filePath, history);
  }

  // 计算与上一个版本的差异
  const previousContent = history.length > 0 ?
    history[history.length - 1].content : context.previousContent || '';
  const currentContent = context.newContent || '';

  const diff = calculateDetailedDiff(previousContent, currentContent);

  // 创建修改记录
  const modification = {
    id: generateModificationId(now),
    timestamp: now.toISOString(),
    file_path: filePath,
    skill_name: context.generatedBySkill || 'unknown',
    session_id: context.sessionId || 'unknown',
    edit_type: context.editType || 'unknown', // 'manual', 'paste', 'autocomplete', etc.
    user_action: context.userAction || 'edit',
    diff: {
      lines_added: diff.added,
      lines_removed: diff.removed,
      lines_modified: diff.modified,
      change_percentage: diff.changePercentage,
      affected_regions: diff.regions
    },
    content_snapshot: {
      before_length: previousContent.length,
      after_length: currentContent.length,
      before_lines: previousContent.split('\n').length,
      after_lines: currentContent.split('\n').length
    }
  };

  // 添加到历史
  history.push({
    timestamp: modification.timestamp,
    content: currentContent,
    diff: modification.diff
  });

  // 限制历史长度
  if (history.length > 50) {
    history = history.slice(-50);
    modificationCache.set(filePath, history);
  }

  return modification;
}

/**
 * 加载文件的修改历史
 * @param {string} filePath - 文件路径
 * @returns {Array} 修改历史
 */
async function loadModificationHistory(filePath) {
  const hash = hashFilePath(filePath);
  const historyFile = path.join(CACHE_DIR, `${hash}_history.json`);

  try {
    const content = await fs.readFile(historyFile, 'utf-8');
    return JSON.parse(content);
  } catch (error) {
    return []; // 文件不存在或解析失败，返回空历史
  }
}

/**
 * 计算详细差异
 * @param {string} before - 修改前内容
 * @param {string} after - 修改后内容
 * @returns {Object} 详细差异
 */
function calculateDetailedDiff(before, after) {
  const beforeLines = before.split('\n');
  const afterLines = after.split('\n');

  const added = afterLines.length - beforeLines.length;
  const removed = added < 0 ? Math.abs(added) : 0;

  // 计算修改的行数
  let modifiedLines = 0;
  const modifiedRegions = [];
  const minLength = Math.min(beforeLines.length, afterLines.length);

  let currentRegion = null;
  for (let i = 0; i < minLength; i++) {
    if (beforeLines[i] !== afterLines[i]) {
      modifiedLines++;

      if (!currentRegion) {
        currentRegion = { start: i, end: i, type: 'modified' };
      } else {
        currentRegion.end = i;
      }
    } else if (currentRegion) {
      modifiedRegions.push(currentRegion);
      currentRegion = null;
    }
  }

  if (currentRegion) {
    modifiedRegions.push(currentRegion);
  }

  // 添加新增和删除的区域
  if (added > 0) {
    modifiedRegions.push({
      start: beforeLines.length,
      end: afterLines.length - 1,
      type: 'added'
    });
  } else if (removed > 0) {
    modifiedRegions.push({
      start: minLength,
      end: beforeLines.length - 1,
      type: 'removed'
    });
  }

  const totalLines = Math.max(beforeLines.length, afterLines.length);
  const changePercentage = totalLines > 0 ?
    ((modifiedLines + Math.abs(added)) / totalLines) * 100 : 0;

  return {
    added: Math.max(0, added),
    removed,
    modified: modifiedLines,
    changePercentage: Math.round(changePercentage * 10) / 10,
    regions: modifiedRegions
  };
}

/**
 * 分析修改类型
 * @param {Object} modification - 修改记录
 * @returns {Object} 修改类型分析
 */
function analyzeModificationType(modification) {
  const analysis = {
    modification_id: modification.id,
    categories: [],
    severity: 'minor', // minor, moderate, major
    likely_reason: []
  };

  const changePercent = modification.diff.change_percentage;
  const diff = modification.diff;

  // 1. 按修改程度分类
  if (changePercent < 2) {
    analysis.categories.push('typo_fix');
    analysis.severity = 'minor';
  } else if (changePercent < 10) {
    analysis.categories.push('minor_adjustment');
    analysis.severity = 'minor';
  } else if (changePercent < 30) {
    analysis.categories.push('moderate_change');
    analysis.severity = 'moderate';
  } else {
    analysis.categories.push('major_rewrite');
    analysis.severity = 'major';
  }

  // 2. 按操作类型分类
  if (diff.added > diff.removed * 2) {
    analysis.categories.push('content_addition');
    analysis.likely_reason.push('feature_enhancement', 'missing_functionality');
  } else if (diff.removed > diff.added * 2) {
    analysis.categories.push('content_removal');
    analysis.likely_reason.push('code_simplification', 'remove_redundancy');
  } else if (diff.modified > (diff.added + diff.removed)) {
    analysis.categories.push('content_modification');
    analysis.likely_reason.push('logic_correction', 'style_adjustment');
  }

  // 3. 按修改区域分类
  if (diff.affected_regions.length === 1) {
    analysis.categories.push('focused_change');
  } else if (diff.affected_regions.length <= 3) {
    analysis.categories.push('multi_region_change');
  } else {
    analysis.categories.push('scattered_changes');
  }

  // 4. 推断可能的原因
  if (modification.user_action === 'paste') {
    analysis.likely_reason.push('external_code_integration');
  }

  if (changePercent > 50 && modification.skill_name === 'ui-ux-pro-max') {
    analysis.likely_reason.push('style_preference_mismatch');
  }

  return analysis;
}

/**
 * 保存修改记录
 * @param {Object} modification - 修改记录
 * @param {Object} analysis - 修改分析
 */
async function saveModification(modification, analysis) {
  // 保存到磁盘
  const date = new Date(modification.timestamp).toISOString().slice(0, 10);
  const filename = `${date}_${modification.id}.json`;
  const filepath = path.join(DATA_DIR, filename);

  const data = {
    ...modification,
    analysis
  };

  await fs.writeFile(filepath, JSON.stringify(data, null, 2), 'utf-8');

  // 更新缓存历史文件
  const hash = hashFilePath(modification.file_path);
  const historyFile = path.join(CACHE_DIR, `${hash}_history.json`);
  const history = modificationCache.get(modification.file_path) || [];

  await fs.writeFile(historyFile, JSON.stringify(history, null, 2), 'utf-8');
}

/**
 * 清理过期缓存
 */
function cleanupCache() {
  if (modificationCache.size > MAX_CACHE_SIZE) {
    // 删除最旧的条目
    const entries = Array.from(modificationCache.entries());
    const toDelete = entries.slice(0, modificationCache.size - MAX_CACHE_SIZE);

    for (const [key] of toDelete) {
      modificationCache.delete(key);
    }
  }
}

// ========== 辅助函数 ==========

function generateModificationId(date) {
  const timestamp = date.getTime();
  const random = crypto.randomBytes(4).toString('hex');
  return `mod_${timestamp}_${random}`;
}

function hashFilePath(filePath) {
  return crypto.createHash('md5').update(filePath).digest('hex').slice(0, 16);
}
