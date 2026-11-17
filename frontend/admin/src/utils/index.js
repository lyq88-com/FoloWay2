/**
 * 工具函数
 */

// 格式化日期时间
export function formatDateTime(dateStr) {
  if (!dateStr) return '-'
  return dateStr.replace('T', ' ').substring(0, 19)
}

// 格式化日期
export function formatDate(dateStr) {
  if (!dateStr) return '-'
  return dateStr.substring(0, 10)
}

// 获取状态标签类型
export function getStatusType(status) {
  return status === 1 ? 'success' : 'danger'
}

// 获取状态文本
export function getStatusText(status) {
  return status === 1 ? '正常' : '禁用'
}

// 获取审核状态标签
export function getReviewStatusTag(status) {
  const map = {
    pending: { type: 'warning', text: '待审核' },
    approved: { type: 'success', text: '已通过' },
    rejected: { type: 'danger', text: '已拒绝' }
  }
  return map[status] || { type: 'info', text: status }
}

// 情绪标签
export function getEmotionTag(emotion) {
  const map = {
    positive: { type: 'success', text: '积极' },
    negative: { type: 'danger', text: '消极' },
    neutral: { type: 'info', text: '中性' }
  }
  return map[emotion] || { type: 'info', text: emotion }
}

// 难度标签
export function getDifficultyTag(difficulty) {
  const map = {
    easy: { type: 'success', text: '简单', color: '#67C23A' },
    medium: { type: 'warning', text: '中等', color: '#E6A23C' },
    hard: { type: 'danger', text: '困难', color: '#F56C6C' }
  }
  return map[difficulty] || { type: 'info', text: difficulty }
}

// AI角色类型标签
export function getRoleTypeTag(roleType) {
  const map = {
    cute: { text: '可爱型', color: '#FF9800' },
    gentle: { text: '温柔型', color: '#FFC107' },
    serious: { text: '严肃型', color: '#607D8B' },
    energetic: { text: '活力型', color: '#E91E63' }
  }
  return map[roleType] || { text: roleType, color: '#909399' }
}
