/**
 * custom-character-init.js
 * 自定义AI伙伴初始化模块（独立封装，不改动原有业务逻辑）
 *
 * 职责：
 * 1. 应用启动时从 store 恢复自定义角色到运行时注册表
 * 2. 注册到 character-sprites（视觉参数表）和 ai-characters（角色数据表）
 * 3. 提供统一的保存/删除/同步接口
 *
 * 使用方式：
 *   import { initCustomCharacters, syncCustomCharacter, removeCustomCharacterSync } from '@/common/custom-character-init.js'
 *   // App.vue onLaunch 中调用 initCustomCharacters(store)
 *   // 工坊保存角色后调用 syncCustomCharacter(character)
 */

import { registerCustomSprite, unregisterCustomSprite, buildSpriteFromConfig } from '@/common/character-sprites.js'
import { registerCustomCharacterData, unregisterCustomCharacterData } from '@/common/ai-characters'

/**
 * 从 store 恢复所有自定义角色到运行时注册表
 * 应在 App.vue onLaunch 中 store 初始化后调用
 * @param {Object} store - Vuex store 实例
 */
export function initCustomCharacters(store) {
  try {
    if (!store || !store.state) return
    const list = store.state.customCharacters || []
    if (!Array.isArray(list) || list.length === 0) return

    list.forEach(character => {
      if (!character || !character.id) return
      _registerOne(character)
    })
    console.log(`[custom-character-init] 已恢复 ${list.length} 个自定义角色`)
  } catch (e) {
    console.error('[custom-character-init] 恢复自定义角色失败', e)
  }
}

/**
 * 同步单个自定义角色到运行时注册表（保存/更新时调用）
 * @param {Object} character - 自定义角色完整数据
 */
export function syncCustomCharacter(character) {
  try {
    if (!character || !character.id) return
    _registerOne(character)
  } catch (e) {
    console.error('[custom-character-init] 同步自定义角色失败', e)
  }
}

/**
 * 从运行时注册表移除自定义角色（删除时调用）
 * @param {String} characterId
 */
export function removeCustomCharacterSync(characterId) {
  try {
    if (!characterId) return
    unregisterCustomSprite(characterId)
    unregisterCustomCharacterData(characterId)
  } catch (e) {
    console.error('[custom-character-init] 移除自定义角色失败', e)
  }
}

/**
 * 内部：注册单个角色到两个注册表
 */
function _registerOne(character) {
  // 注册视觉参数（sprite）
  if (character.sprite) {
    registerCustomSprite(character.id, character.sprite)
  } else if (character.diy) {
    // 兼容：若没有 sprite 但有 diy 配置，动态构建
    try {
      const sprite = buildSpriteFromConfig(character.diy)
      registerCustomSprite(character.id, sprite)
    } catch (e) {
      console.warn('[custom-character-init] 构建sprite失败', character.id, e)
    }
  }

  // 注册角色数据（ai-characters）
  // 确保必要字段存在，避免对话引擎崩溃
  const safeCharacter = {
    ...character,
    phrases: character.phrases || {
      morning: [character.catchphrase || '早安~'],
      comfort: ['我在呢~'],
      celebrate: ['太棒了！'],
      catchphrase: character.catchphrase || ''
    },
    colors: character.colors || {
      primary: '#7BA08B',
      secondary: '#C8E6C9',
      accent: '#A5D6A7',
      light: '#F1F8E9',
      dark: '#3E5D4A'
    },
    avatar: character.avatar || '🌟',
    catchphrase: character.catchphrase || '',
    traits: Array.isArray(character.traits) ? character.traits : ['自定义'],
    personalityType: character.personalityType || 'gentle_healer',
    voiceWords: Array.isArray(character.voiceWords) ? character.voiceWords : []
  }
  registerCustomCharacterData(character.id, safeCharacter)
}

export default {
  initCustomCharacters,
  syncCustomCharacter,
  removeCustomCharacterSync
}
