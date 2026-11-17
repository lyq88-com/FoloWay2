/**
 * 习惯-AI 联动 API
 * 打卡触发对话 / 成就 / 记忆 / 日记 / 自定义提醒
 */
import mock from '@/common/mock'
import http from '@/common/request'

const USE_MOCK = mock.USE_MOCK

export default {
  /**
   * 打卡触发AI对话
   * @param {number} habitId - 习惯ID
   * @param {string} note - 打卡留言
   * @param {string} emotion - 当前情绪
   * @param {string} characterId - AI角色ID
   * @returns {Promise<object>} { dialogue, emotion_tag, continuous_day, achievement, diary }
   */
  checkinTrigger(habitId, note = '', emotion = '', characterId = 'linxi') {
    if (USE_MOCK) return mock.checkinTriggerAI(habitId, note, emotion, characterId)
    return http.post('/habit-ai/checkin-trigger', {
      habit_id: habitId,
      note,
      emotion,
      character_id: characterId,
    })
  },

  /**
   * 获取成就列表
   * @param {number} habitId - 习惯ID(0=全部)
   */
  getAchievements(habitId = 0) {
    if (USE_MOCK) return mock.getHabitAchievements(habitId)
    return http.get('/habit-ai/achievements', { habit_id: habitId })
  },

  /**
   * 写入AI记忆
   * @param {object} data - { memory_type, memory_content, habit_id, emotion_score, ... }
   */
  writeMemory(data) {
    if (USE_MOCK) return mock.writeHabitMemory(data)
    return http.post('/habit-ai/memory', data)
  },

  /**
   * 获取AI记忆列表
   * @param {string} memoryType - 记忆类型(空=全部)
   * @param {number} limit - 数量
   */
  getMemories(memoryType = '', limit = 20) {
    if (USE_MOCK) return mock.getHabitMemories(memoryType, limit)
    return http.get('/habit-ai/memories', { memory_type: memoryType, limit })
  },

  /**
   * 更新自定义提醒话术
   * @param {number} habitId - 习惯ID
   * @param {string} customRemindText - 自定义话术
   * @param {string} aiStyle - AI风格
   */
  updateCustomRemind(habitId, customRemindText, aiStyle = 'gentle') {
    if (USE_MOCK) return mock.updateHabitCustomRemind(habitId, customRemindText, aiStyle)
    return http.put('/habit-ai/custom-remind', {
      habit_id: habitId,
      custom_remind_text: customRemindText,
      ai_style: aiStyle,
    })
  },

  /**
   * 生成打卡日记
   * @param {number} habitId
   * @param {string} note
   * @param {string} emotion
   * @param {string} dateStr - YYYY-MM-DD
   */
  generateDiary(habitId, note = '', emotion = '', dateStr = '') {
    if (USE_MOCK) return mock.generateCheckinDiary(habitId, note, emotion, dateStr)
    return http.post('/habit-ai/diary', {
      habit_id: habitId,
      note,
      emotion,
      date: dateStr,
    })
  },

  /**
   * 获取AI提醒话术
   * @param {number} habitId
   */
  getReminder(habitId) {
    if (USE_MOCK) return mock.getHabitReminder(habitId)
    return http.get('/habit-ai/reminder', { habit_id: habitId })
  },
}
