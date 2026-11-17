<template>
  <view class="xt-page xt-s13">
    <view class="body">
      <view class="page-title-row">
        <view>
          <view class="page-title">情绪树洞</view>
          <view class="page-sub">不用讲道理，说出来就好</view>
        </view>
        <view class="icon-btn" @click="goChatFromModal"><xt-icon name="i-moon" /></view>
      </view>

      <!-- 情绪选择行 -->
      <view class="mood-row">
        <view
          v-for="emotion in emotions"
          :key="emotion.value"
          class="mood"
          :class="{ on: selectedEmotion === emotion.value }"
          @click="selectEmotion(emotion.value)"
        >
          <span class="face">{{ emotion.icon }}</span>
          <span>{{ emotion.label }}</span>
        </view>
      </view>

      <!-- 输入卡 -->
      <view class="mood-card">
        <view class="q">现在，是什么让你停在这里？</view>
        <view class="hint">不用组织语言，想到什么写什么</view>

        <textarea
          v-model="noteContent"
          class="mood-input"
          placeholder="想到什么写什么…"
          :maxlength="200"
        />

        <!-- 触发标签 -->
        <view class="mood-tags">
          <text
            v-for="tag in quickTags"
            :key="tag"
            class="chip"
            :class="{ on: selectedTags.includes(tag) }"
            @click="toggleTag(tag)"
          >{{ tag }}</text>
        </view>

        <!-- AI 回应 -->
        <view class="mood-ai" v-if="aiReply">
          <image v-if="aiPhoto" :src="aiPhoto" mode="aspectFill" />
          <view v-else class="mood-ai-fb"><text>{{ aiAvatar }}</text></view>
          <span class="b">{{ aiReply }}</span>
        </view>

        <view class="speech-foot">
          <view class="mem"><xt-icon name="i-edit" /><text>{{ noteContent.length }}/200</text></view>
          <view class="reply" @click="submitEmotion">
            {{ submitting ? '记录中…' : '记录心情' }}<xt-icon name="i-arrow" />
          </view>
        </view>
      </view>

      <!-- 历史记录 -->
      <view class="n-group-t">这一周，她替你记下了</view>
      <view
        v-for="(record, idx) in recentEmotions"
        :key="record.id || idx"
        class="mem-item"
        @longpress="showDeleteMenu(record)"
      >
        <view class="mi" :class="idx % 2 ? 'tint-blue' : 'tint-green'">
          <xt-icon :name="idx % 2 ? 'i-water' : 'i-moon'" />
        </view>
        <span class="tx">
          <span class="t">{{ record.tags && record.tags.length ? '#' + record.tags.join(' #') : getEmotionIcon(record.emotion) + ' 心情记录' }}</span>
          <span class="m">{{ record.description || record.content || '没有记录内容' }}</span>
          <span class="d">{{ formatTime(record.record_date || record.date || record.created_at) }}</span>
        </span>
      </view>
      <view v-if="recentEmotions.length === 0" class="mem-item">
        <span class="tx">
          <span class="m">还没有心情记录，先记下此刻吧</span>
        </span>
      </view>
    </view>

    <!-- AI 情绪疏导弹窗 -->
    <ai-interaction-modal
      :visible="showAIModal"
      type="reminder"
      :characterId="$store.state.aiConfig.avatarType || 'linxi'"
      :message="aiModalMessage"
      :loading="aiModalLoading"
      @close="closeAIModal"
      @chat="goChatFromModal"
      @primary="closeAIModal"
    />
  </view>
</template>

<script>
import { getCharacterById } from '@/common/ai-characters'
import emotionApi from '@/api/emotion'
import AIInteractionModal from '@/components/ai-interaction-modal/ai-interaction-modal.vue'
import aiService from '@/common/ai-service.js'
import XtIcon from '@/components/xt-icon/xt-icon.vue'
import { getActivePartner, getPartnerAvatar } from '@/common/ai-partner'

export default {
  components: {
    AIInteractionModal,
    XtIcon
  },
  data() {
    return {
      selectedEmotion: '',
      intensity: 5,
      selectedTags: [],
      noteContent: '',
      recordDate: '',  // 补录日期（空=今天）
      aiReply: '',
      submitting: false,
      // AI弹窗状态
      showAIModal: false,
      aiModalMessage: '',
      aiModalLoading: false,
      recentEmotions: [],
      // 6种情绪（对齐后端 EmotionService.EMOTION_LABELS）
      emotions: [
        { value: 'happy', icon: '😊', label: '开心', color: '#FFB74D', bgColor: '#FFE0B2' },
        { value: 'excited', icon: '🎉', label: '兴奋', color: '#EC407A', bgColor: '#F8BBD0' },
        { value: 'calm', icon: '😌', label: '平静', color: '#4DB6AC', bgColor: '#B2DFDB' },
        { value: 'sad', icon: '😢', label: '难过', color: '#42A5F5', bgColor: '#BBDEFB' },
        { value: 'angry', icon: '😤', label: '生气', color: '#E53935', bgColor: '#FFCDD2' },
        { value: 'tired', icon: '😴', label: '疲惫', color: '#78909C', bgColor: '#CFD8DC' }
      ]
    }
  },
  computed: {
    aiName() {
      return this.$store.state.aiConfig.name || '林夕'
    },
    aiAvatar() {
      const characterId = this.$store.state.aiConfig.avatarType || 'linxi'
      const character = getCharacterById(characterId)
      return character?.avatar || '🌿'
    },
    currentCharacter() {
      return getActivePartner()
    },
    historyTags() {
      return this.$store.state.emotionTags || []
    },
    todayStr() {
      const d = new Date()
      const pad = (n) => String(n).padStart(2, '0')
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
    },
    canSubmit() {
      return !!this.selectedEmotion
    },
    aiPhoto() {
      return getPartnerAvatar(this.currentCharacter) || ''
    },
    aiAvatar() {
      return (this.currentCharacter && this.currentCharacter.avatar) || '🌿'
    },
    quickTags() {
      const tags = (this.historyTags || []).filter(Boolean).slice(0, 4)
      return tags.length ? tags : ['累', '自责', '想被理解', '说不清']
    }
  },
  onShow() {
    this.loadHistory()
  },
  methods: {
    // AI 情绪疏导联动
    async triggerEmotionAI(payload) {
      this.aiModalLoading = true
      this.showAIModal = true
      
      try {
        const response = await aiService.onEmotionRecord(
          payload.emotion,
          payload.intensity,
          payload.tags
        )
        this.aiModalMessage = response || '谢谢你分享你的心情，我一直陪着你~'
      } catch (e) {
        console.error('AI情绪疏导失败:', e)
        this.aiModalMessage = '你的感受很重要，我在这里~'
      } finally {
        this.aiModalLoading = false
      }
    },
    closeAIModal() {
      this.showAIModal = false
      this.aiModalMessage = ''
    },
    goChatFromModal() {
      this.closeAIModal()
      uni.switchTab({ url: '/pages/chat/chat' })
    },
    selectEmotion(value) {
      if (this.selectedEmotion === value) {
        // 再次点击同一个取消选择
        this.selectedEmotion = ''
      } else {
        this.selectedEmotion = value
        // 重置强度为默认5
        this.intensity = 5
      }
      this.aiReply = ''
    },
    getEmotionIcon(value) {
      const emotion = this.emotions.find(e => e.value === value)
      return emotion?.icon || '😐'
    },
    getEmotionColor(value) {
      const emotion = this.emotions.find(e => e.value === value)
      return emotion?.bgColor || '#E8E8E8'
    },
    setToday() {
      this.recordDate = ''
    },
    onDateChange(e) {
      this.recordDate = e.detail.value
    },
    onCustomTagAdd(tag) {
      // 自定义标签添加时同步到 Vuex 记忆
      this.$store.commit('addEmotionTag', tag)
    },
    toggleTag(tag) {
      const list = [...this.selectedTags]
      const idx = list.indexOf(tag)
      if (idx >= 0) {
        list.splice(idx, 1)
      } else {
        if (list.length >= 5) {
          uni.showToast({ title: '最多选择5个标签', icon: 'none' })
          return
        }
        list.push(tag)
      }
      this.selectedTags = list
    },
    async submitEmotion() {
      if (!this.canSubmit) {
        uni.showToast({ title: '请先选择心情', icon: 'none' })
        return
      }
      if (this.submitting) return
      this.submitting = true

      try {
        const payload = {
          emotion: this.selectedEmotion,
          intensity: this.intensity,
          tags: this.selectedTags,
          description: this.noteContent.trim(),
          record_date: this.recordDate || null,
          habit_id: 0
        }

        const res = await emotionApi.createEmotion(payload)
        // Mock 和真实 API 统一返回 { code, data: {...} }
        const data = res.data || res
        this.aiReply = data.ai_reply || this.fallbackReply()

        // 同步到 Vuex 记忆标签
        if (this.selectedTags.length > 0) {
          this.$store.commit('addEmotionTag', this.selectedTags)
        }

        // 行走成长地图：情绪记录增加 0.3 步
        this.$store.commit('addWalkStep', {
          steps: 0.3,
          type: 'emotion',
          description: this.selectedEmotion,
          emotion: this.selectedEmotion
        })

        // 本地缓存（兼容旧逻辑）
        this.$store.commit('addEmotionRecord', {
          ...payload,
          id: data.id,
          ai_reply: this.aiReply,
          created_at: new Date().toISOString()
        })

        uni.showToast({ title: '记录成功！', icon: 'success' })

        // AI 情绪疏导联动
        this.triggerEmotionAI(payload)

        // 重置表单
        this.selectedEmotion = ''
        this.intensity = 5
        this.selectedTags = []
        this.noteContent = ''
        this.recordDate = ''

        // 重新加载历史
        this.loadHistory()
      } catch (err) {
        console.error('情绪记录失败:', err)
        // 失败时降级：仍然记录到本地
        const record = {
          emotion: this.selectedEmotion,
          intensity: this.intensity,
          tags: this.selectedTags,
          description: this.noteContent.trim(),
          date: new Date().toISOString(),
          ai_reply: this.fallbackReply()
        }
        this.$store.commit('addEmotionRecord', record)
        this.aiReply = record.ai_reply
        this.$store.commit('addWalkStep', {
          steps: 0.3, type: 'emotion',
          description: this.selectedEmotion, emotion: this.selectedEmotion
        })
        uni.showToast({ title: '已离线记录', icon: 'none' })

        this.selectedEmotion = ''
        this.intensity = 5
        this.selectedTags = []
        this.noteContent = ''
        this.recordDate = ''
        this.loadHistory()
      } finally {
        this.submitting = false
      }
    },
    fallbackReply() {
      // 当 API 无 ai_reply 时的降级（使用本地角色语录）
      const characterId = this.$store.state.aiConfig.avatarType || 'linxi'
      const emotion = this.selectedEmotion
      const tone = (emotion === 'sad' || emotion === 'angry' || emotion === 'tired')
        ? 'comfort'
        : (emotion === 'happy' || emotion === 'excited')
          ? 'celebrate'
          : 'morning'
      return this.getRandomLocalPhrase(tone)
    },
    getRandomLocalPhrase(tone) {
      const replies = {
        comfort: [
          '我听到你了，这种感受是真实的。先深呼吸三次，我在这里陪着你。',
          '允许自己有这样的情绪，不必急着改变。你愿意和我说说发生了什么吗？',
          '难过的时候，记得给自己一些温柔。你不是一个人在面对。'
        ],
        celebrate: [
          '太棒了！这份喜悦值得被记录下来。继续保持这份好心情~',
          '为你高兴！正向的情绪是前进的动力，记得让这份感觉多停留一会儿。',
          '看到你这么开心，我也替你高兴！继续保持哦~'
        ],
        morning: [
          '平静是很好的状态，愿你今天一整天都保持这份从容。',
          '能感受到平静，说明你和自己的内心连接得很好。继续保持~',
          '这种状态很棒，平静中蕴含着力量。愿你的一天顺遂。'
        ]
      }
      const list = replies[tone] || replies.comfort
      return list[Math.floor(Math.random() * list.length)]
    },
    async loadHistory() {
      try {
        const res = await emotionApi.getEmotionList({ page: 1, page_size: 20 })
        const data = res.data || res
        const list = data.list || []
        this.recentEmotions = list
        // 同步到 Vuex 缓存
        this.$store.commit('setEmotionRecords', list)
      } catch (err) {
        console.warn('加载历史失败，使用本地缓存:', err)
        // 降级：从 Vuex 加载
        this.recentEmotions = this.$store.state.emotionRecords.slice(0, 20)
      }
    },
    showDeleteMenu(record) {
      if (!record.id) {
        uni.showToast({ title: '该记录无法删除', icon: 'none' })
        return
      }
      uni.showActionSheet({
        itemList: ['删除此记录'],
        success: (res) => {
          if (res.tapIndex === 0) {
            this.deleteRecord(record)
          }
        }
      })
    },
    async deleteRecord(record) {
      try {
        await emotionApi.deleteEmotion(record.id)
        this.$store.commit('removeEmotionRecord', record.id)
        this.recentEmotions = this.recentEmotions.filter(r => r.id !== record.id)
        uni.showToast({ title: '已删除', icon: 'success' })
      } catch (err) {
        console.error('删除失败:', err)
        uni.showToast({ title: '删除失败', icon: 'none' })
      }
    },
    formatTime(dateStr) {
      if (!dateStr) return ''
      try {
        // 支持 ISO / YYYY-MM-DD / YYYY-MM-DD HH:mm:ss
        const d = new Date(dateStr.includes('T') ? dateStr : dateStr.replace(' ', 'T'))
        if (isNaN(d.getTime())) return dateStr
        const pad = (n) => String(n).padStart(2, '0')
        return `${d.getMonth() + 1}/${d.getDate()} ${pad(d.getHours())}:${pad(d.getMinutes())}`
      } catch (e) {
        return dateStr
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.xt-page.xt-s13 .body {
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 16px;
}

/* 设计稿 img 在 H5 渲染为 uni-image，需同步宽高与圆角 */
.xt-page.xt-s13 .mood-ai uni-image {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  border-radius: 50%;
  display: block;
  overflow: hidden;
}
/* 无立绘伙伴回退 */
.xt-page.xt-s13 .mood-ai-fb {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F1EDE3;
  font-size: 14px;
  line-height: 1;
}
</style>
