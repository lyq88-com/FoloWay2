<template>
  <view class="xt-page xt-s3" :style="chatPageStyle">
    <!-- 自定义聊天背景层 -->
    <view v-if="chatSettings.chatBackgroundImage && chatSettings.chatBackground === 'custom'" class="chat-bg-image" :style="{ backgroundImage: 'url(' + chatSettings.chatBackgroundImage + ')' }"></view>

    <view class="body cht-body">
      <!-- 顶部：返回 / 角色 / 通话 -->
      <view class="cht-head">
        <view class="cht-back" @click="goBack"><xt-icon name="i-left" /></view>
        <view class="cht-av">
          <image v-if="aiPhoto" :src="aiPhoto" mode="aspectFill" style="width: 100%; height: 100%; border-radius: 50%; display: block;" />
          <view v-else class="cht-a-fb"><text>{{ currentCharacter.avatar }}</text></view>
          <view class="dot"></view>
        </view>
        <view class="cht-meta">
          <view class="cht-name">
            <text>{{ aiName }}</text>
            <text class="tag">{{ styleLabel }}</text>
          </view>
          <view class="cht-st">
            <view class="dot"></view>
            <text>{{ aiStatusText }} · {{ aiMood.text }}</text>
          </view>
        </view>
        <!-- 【原有文件极小改动·模块4】新增多人聊天入口，仅加跳转，不动原聊天逻辑 -->
        <view class="cht-call v7-ghost" @click="goGroupChat"><text class="v7-ghost-tx">群聊</text></view>
        <view class="cht-call" @click="startVoiceCall"><xt-icon name="i-call" /></view>
      </view>

      <!-- 羁绊条：相伴天数 / 默契 -->
      <view class="cht-bond">
        <text class="k">相伴 <text class="v">{{ partnerDays }}</text> 天</text>
        <view class="bar"><view class="fill" :style="{ width: bondPercent + '%' }"></view></view>
        <text class="k">默契 <text class="v">{{ affectionProgress }}%</text></text>
      </view>

      <!-- 对话流 -->
      <scroll-view
        scroll-y
        class="cht-scroll"
        :scroll-top="scrollTop"
        :scroll-with-animation="true"
      >
        <view class="cht-flow">
          <!-- 她记得 -->
          <view class="cht-pin">
            <view class="pi"><xt-icon name="i-spark" /></view>
            <text class="pt"><text class="b">她记得：</text>{{ memoryText }}</text>
            <text class="pe">{{ memoryCount || 12 }} 条</text>
          </view>

          <!-- 空会话：角色问候 -->
          <view v-if="messages.length === 0" class="cht-row">
            <image v-if="aiPhoto" class="cht-a" :src="aiPhoto" mode="aspectFill" />
            <view v-else class="cht-a cht-a-fb"><text>{{ currentCharacter.avatar }}</text></view>
            <view class="cht-b ai"><text>{{ aiGreeting }}</text></view>
          </view>

          <!-- 日期分隔 + 消息 -->
          <template v-for="(msg, idx) in displayMessages" :key="idx">
            <view v-if="showDateSeparator(idx)" class="cht-day">{{ getDateLabel(msg.time) }}</view>

            <!-- 已撤回的消息：显示撤回提示，不展示原内容 -->
            <view v-if="msg.recalled" class="cht-t" :class="{ r: msg.role === 'user' }">
              {{ msg.role === 'assistant' ? aiName + '撤回了一条消息' : '你撤回了一条消息' }}
            </view>

            <!-- 礼物消息 -->
            <view v-else-if="msg.type === 'gift'" class="cht-ev">
              <view class="eic"><text class="gift-emoji">{{ msg.giftIcon }}</text></view>
              <view class="etx">
                <text class="et">{{ msg.role === 'user' ? '送出了' : '回赠了' }} {{ msg.content }}</text>
                <text class="em">{{ formatTime(msg.time) }}</text>
              </view>
              <view class="eok"><xt-icon name="i-check" /></view>
            </view>

            <!-- 通话记录消息 -->
            <view v-else-if="msg.type === 'call'" class="cht-ev">
              <view class="eic"><xt-icon name="i-call" /></view>
              <view class="etx">
                <text class="et">语音通话 · {{ msg.content }}</text>
                <text class="em">{{ formatTime(msg.time) }}</text>
              </view>
              <view class="eok"><xt-icon name="i-check" /></view>
            </view>

            <!-- 普通气泡：图片 / 表情 / 文本 -->
            <view v-else class="cht-row" :class="{ me: msg.role === 'user' }">
              <image v-if="msg.role === 'assistant' && aiPhoto" class="cht-a" :src="aiPhoto" mode="aspectFill" />
              <view v-else-if="msg.role === 'assistant'" class="cht-a cht-a-fb"><text>{{ currentCharacter.avatar }}</text></view>
              <view class="cht-b" :class="[msg.role === 'user' ? 'me' : 'ai', bubbleClass]">
                <image
                  v-if="msg.type === 'image'"
                  class="cht-msg-img"
                  :src="msg.imageUrl"
                  mode="aspectFill"
                  style="width: 96px; height: 96px; border-radius: 10px; display: block;"
                  @click="previewMsgImage(msg)"
                />
                <template v-else-if="msg.type === 'sticker'">
                  <text v-if="msg.stickerType === 'emoji'" style="font-size: 30px; line-height: 1.2;">{{ msg.content }}</text>
                  <image v-else class="cht-msg-img" :src="msg.imageUrl" mode="aspectFill" style="width: 96px; height: 96px; border-radius: 10px; display: block;" />
                </template>
                <template v-else>
                  <text v-if="msg.action" style="display: block; font-style: italic; opacity: .7;">*{{ msg.action }}*</text>
                  <text>{{ msg.content }}</text>
                </template>
              </view>
            </view>

            <!-- 情绪标签 -->
            <view v-if="!msg.recalled && msg.emotion && msg.emotion !== 'normal'" class="cht-emotion">
              <EmotionTag :type="msg.emotion" :intensity="msg.emotionIntensity" size="small" />
            </view>

            <!-- 时间 -->
            <view
              v-if="msg.time && !msg.recalled && msg.type !== 'gift' && msg.type !== 'call'"
              class="cht-t"
              :class="{ r: msg.role === 'user' }"
            >{{ formatTime(msg.time) }}</view>
          </template>

          <!-- 流式输出消息 -->
          <view v-if="streamingActive" class="cht-row">
            <image v-if="aiPhoto" class="cht-a" :src="aiPhoto" mode="aspectFill" />
            <view v-else class="cht-a cht-a-fb"><text>{{ currentCharacter.avatar }}</text></view>
            <view class="cht-b ai">
              <text>{{ streamingMessage }}</text>
              <text style="opacity: .55;">|</text>
            </view>
          </view>

          <!-- 正在输入 -->
          <view v-if="isTyping && !streamingActive" class="cht-typing">
            <view class="dot"></view>
            <view class="dot"></view>
            <view class="dot"></view>
            <text class="tx">{{ aiName }} 正在输入</text>
          </view>

          <!-- 离线提示 -->
          <view v-if="offlineCount > 0" class="cht-t">📡 {{ offlineCount }} 条消息将在网络恢复后发送</view>
        </view>
      </scroll-view>

      <!-- 快捷话题 -->
      <scroll-view v-if="showQuickReplies && !isTyping && !streamingActive" scroll-x class="quick-scroll">
        <view class="cht-quick">
          <text
            v-for="(reply, idx) in quickReplies"
            :key="idx"
            class="qchip"
            @click="sendQuickReply(reply)"
          >{{ reply }}</text>
        </view>
      </scroll-view>

      <!-- ↓↓↓ 新增（2026-11-15）：AI 根据这句话推荐的功能入口（正念 / 情绪树洞 / 专注…） ↓↓↓ -->
      <view
        v-if="suggestionCard && !isTyping && !streamingActive"
        class="cht-sug"
      >
        <view class="sug-main" @click="openSuggestion(suggestionCard)">
          <text class="sug-ico">{{ suggestionCard.icon }}</text>
          <view class="sug-tx">
            <text class="sug-t">{{ suggestionCard.label }}</text>
            <text class="sug-d">{{ suggestionCard.desc }}</text>
          </view>
          <text class="sug-go">去看看 ›</text>
        </view>
        <text class="sug-x" @click.stop="suggestionCard = null">×</text>
      </view>
      <!-- ↑↑↑ 新增结束 ↑↑↑ -->

      <!-- ↓↓↓ AI 降级提示：大模型不可用时的显式说明，避免把本地规则当大模型回复 -->
      <view v-if="aiDegraded" class="ai-offline">
        <text class="ai-offline-t">离线陪伴模式 · AI 服务暂不可用，回复来自本地规则</text>
      </view>
      <!-- ↑↑↑ 新增结束 ↑↑↑ -->

      <!-- 输入栏 -->
      <view class="cht-input">
        <!-- 轻点：礼物/表情/图片/唱歌/装扮/商城；长按：语音播报/语音输入/会话类型 -->
        <view class="plus" @click="openFeatureSheet" @longpress="openMoreSheet"><xt-icon name="i-plus" /></view>
        <input
          v-model="inputText"
          class="field"
          :placeholder="'和' + aiName + '说点什么…'"
          placeholder-style="font-size: 8.2px; color: #A2AAA3;"
          confirm-type="send"
          :adjust-position="true"
          @confirm="send"
          @input="onInput"
        />
        <view class="send" @click="send"><xt-icon name="i-send" /></view>
      </view>
    </view>

    <!-- 危机干预弹窗 -->
    <CrisisInterventionModal
      :visible="showCrisisModal"
      :crisisData="crisisData"
      :aiEmoji="currentCharacter?.avatar || '🌿'"
      @close="closeCrisisModal"
      @continue="continueAfterCrisis"
    />

    <!-- ↓↓↓ 安全合规批次：高危信号提醒弹窗 + 新手引导 ↓↓↓ -->
    <DangerWarn
      :visible="showDangerWarn"
      :message="dangerWarnData.message"
      :resources="dangerWarnData.resources"
      @close="showDangerWarn = false"
    />
    <!-- ↑↑↑ 新增结束 ↑↑↑ -->

    <!-- ↓↓↓ 模块1 新增：情绪引导浮层 ↓↓↓ -->
    <view v-if="showEmotionGuide" class="emotion-guide-mask" @tap="showEmotionGuide = false">
      <view class="emotion-guide-card" @tap.stop>
        <view class="eg-emoji">{{ emotionGuideData.crisis ? '🌊' : '💖' }}</view>
        <view class="eg-title">{{ emotionGuideData.crisis ? '感觉心里压力很大吗？' : '今天情绪好像有点低落呢' }}</view>
        <view class="eg-desc" v-if="emotionGuideData.venting">想吐槽就说出来，我在听你。</view>
        <view class="eg-desc" v-else>深呼吸一下，或者做点让自己舒服的事。</view>
        <view class="eg-actions">
          <view class="eg-btn eg-btn-primary" @tap="goMeditation">
            {{ emotionGuideData.crisis ? '先去正念呼吸一下' : '试试正念呼吸 🧘' }}
          </view>
          <view class="eg-close" @tap="showEmotionGuide = false">继续聊天</view>
        </view>
      </view>
    </view>
    <!-- ↑↑↑ 模块1 新增结束 ↑↑↑ -->

    <!-- 送礼物面板 -->
    <GiftPanel
      :visible="showGiftPanel"
      @close="showGiftPanel = false"
      @send-gift="onSendGift"
      @send-treasure="onSendTreasure"
    />

    <!-- 表情包面板 -->
    <StickerPanel
      :visible="showStickerPanel"
      @close="showStickerPanel = false"
      @send-sticker="onSendSticker"
    />

    <!-- 聊天设置面板（气泡/背景/音色/多语言/动作描述开关） -->
    <ChatSettingsPanel
      :visible="showChatSettingsPanel"
      :settings="chatSettings"
      @close="showChatSettingsPanel = false"
      @change="onChatSettingsChange"
      @lang-change="onVoiceLangChange"
    />

    <!-- V7 纸感底部弹层：输入栏「+」轻点 / 长按共用 -->
    <view class="v7-sheet-mask" :class="{ 'is-open': actionSheetVisible }" @tap="closeActionSheet">
      <view class="v7-sheet" @tap.stop>
        <view class="v7-sheet-handle"></view>
        <view class="v7-sheet-head">
          <text class="v7-sheet-title">更多</text>
        </view>
        <view class="v7-sheet-list">
          <view
            v-for="(item, idx) in actionSheetItems"
            :key="item.key"
            class="v7-sheet-item"
            :class="{ 'is-last': idx === actionSheetItems.length - 1 }"
            @tap="onActionSheetSelect(item)"
          >
            <view class="v7-sheet-ico" :class="'ico-' + item.key"><text>{{ item.icon }}</text></view>
            <text class="v7-sheet-label">{{ item.label }}</text>
            <text v-if="item.note" class="v7-sheet-note">{{ item.note }}</text>
            <text class="v7-sheet-arrow">›</text>
          </view>
        </view>
        <view class="v7-sheet-cancel" @tap="closeActionSheet"><text>取消</text></view>
      </view>
    </view>

    <!-- 实时语音通话 -->
    <VoiceCall
      :visible="showVoiceCall"
      :name="aiName"
      :avatarEmoji="currentCharacter?.avatar || '🌿'"
      :avatarBg="currentCharacter ? `linear-gradient(135deg, ${currentCharacter.colors.primary}, ${currentCharacter.colors.accent})` : ''"
      :tone="roleVoiceTone || 'warm'"
      @end="onCallEnd"
    />

    <!-- 礼物赠送动画 -->
    <view v-if="giftAnimation.show" class="gift-anim-overlay">
      <view class="gift-anim-icon" :key="giftAnimation.key">
        <text>{{ giftAnimation.icon }}</text>
      </view>
      <view class="gift-anim-particles">
        <text v-for="p in 8" :key="'p' + p" class="particle" :class="'p' + p">{{ giftAnimation.icon }}</text>
      </view>
    </view>

    <v7-tabbar active="chat" />
  </view>
</template>

<script>
import chatApi from '@/api/chat'
import { getCharacterById, isCustomCharacter, STYLE_LABELS } from '@/common/ai-characters'
import { getActivePartner, getActivePartnerId, getPartnerAvatar } from '@/common/ai-partner'
import XtIcon from '@/components/xt-icon/xt-icon.vue'
import V7Tabbar from '@/components/v7-tabbar/v7-tabbar.vue'
import { generateReply, generateCustomReply, buildContext } from '@/common/ai-dialogue-engine'
import { getCurrentStage, getRandomLocationDialogue } from '@/common/walk-map-config.js'
import EmotionTag from '@/components/emotion-tag.vue'
import CrisisInterventionModal from '@/components/crisis-intervention-modal.vue'
// ↓↓↓ 安全合规批次 ↓↓↓
import DangerWarn from '@/components/danger_warn.vue'
import { checkDanger } from '@/common/content-check'
// ↑↑↑ 新增结束 ↑↑↑
import GiftPanel from '@/components/gift-panel/gift-panel.vue'
import StickerPanel from '@/components/sticker-panel/sticker-panel.vue'
import ChatSettingsPanel from '@/components/chat-settings/chat-settings.vue'
import VoiceCall from '@/components/voice-call/voice-call.vue'
import economy from '@/common/economy'
import aiSocial from '@/common/ai-social'
import { getVoiceLang, getAsrLang, normalizeVoiceLang, matchSystemVoice, isVoiceLangSupported, pickOfflineReply } from '@/common/voice-lang'
import { playSong, stopMusic } from '@/common/ai-music'
// ↓↓↓ 新增（2026-10-27）：与 settings 页「语音播报」开关联动 ↓↓↓
// settings 里那个开关之前只改了个布尔值，没人读；这里让聊天页用它当初始值。
// 页面内的 🔊 按钮仍可单独切换（只影响本页，不回写全局）。
import tts from '@/common/tts'
import aiSpeak from '@/common/ai-speak'
// ↑↑↑ 新增结束 ↑↑↑
import mock from '@/common/mock'
// ↓↓↓ 新增 ↓↓↓ 统一拼头像地址（相对路径/后端硬编码 IP 都能处理）
import { toAvatarUrl } from '@/common/request'
// ↓↓↓ 陪伴感增强 v3 ↓↓↓
// 语气起伏：让 TTS 有停顿、有起伏、有情绪，而不是平铺直叙的播音腔
import { speakExpressive, detectEmotion } from '@/common/voice-prosody'
import proactiveApi from '@/api/proactive'
import personaApi from '@/api/persona'
// ↑↑↑ 新增结束 ↑↑↑

const CHAT_SETTINGS_KEY = 'chat_settings'

const DEFAULT_CHAT_SETTINGS = {
  bubbleStyle: 'default',
  chatBackground: 'default',
  chatBackgroundImage: '',
  voiceId: 'default',
  voiceLang: 'zh-CN',
  rate: 1.0,
  pitch: 1.0,
  actionDescEnabled: true,
  unlockedDecos: []
}

export default {
  components: { EmotionTag, CrisisInterventionModal, GiftPanel, StickerPanel, ChatSettingsPanel, VoiceCall, DangerWarn, XtIcon, V7Tabbar },
  data() {
    return {
      inputText: '',
      messages: [],
      // ↓↓↓ 陪伴感增强 v3 ↓↓↓
      proactiveLoaded: false,   // 主动消息每次进页面只拉一次，避免重复打扰
      roleVoiceTone: '',        // 当前角色的音色（soft/bright/warm/cool/husky）
      // ↑↑↑ 新增结束 ↑↑↑
      quickReplies: [],
      showQuickReplies: true,
      isTyping: false,
      scrollTop: 0,
      aiEmotion: 'normal',
      aiAnimation: 'float',
      aiGreetingText: '',
      // 流式输出
      streamingActive: false,
      streamingMessage: '',
      // v3.1：当前会话 id（后端首个 SSE 事件回传）。之前没有这个字段，
      // 每条消息都会被后端当成新会话 → 服务端没有历史 → AI 记不住上一句。
      currentSessionId: 0,
      // AI 降级链路：后端 ai_meta 事件标记本次回复来自本地兜底
      aiDegraded: false,
      // 危机干预
      showCrisisModal: false,
      crisisData: {},
      pendingContent: '', // 触发危机检测后被暂存的消息
      // ↓↓↓ 安全合规批次：高危弹窗 ↓↓↓
      showDangerWarn: false,
      dangerWarnData: { message: '', resources: [] },
      // ↑↑↑ 新增结束 ↑↑↑
      // ↓↓↓ 模块1 新增：情绪引导浮层（后端 emotion_comfort SSE 事件消费） ↓↓↓
      showEmotionGuide: false,
      emotionGuideData: { emotion: '', valence: '', triggered: false, venting: false, crisis: false },
      // ↑↑↑ 模块1 新增结束 ↑↑↑
      // ↓↓↓ 新增（2026-11-15）：AI 根据用户这句话推荐的功能卡片 ↓↓↓
      suggestionCard: null,
      // ↑↑↑ 新增结束 ↑↑↑
      // 防抖
      lastSendTime: 0,
      isSending: false,
      // 阶段J: 会话类型
      sessionTypes: [
        { key: 'chat', label: '日常聊天', icon: '💬' },
        { key: 'checkin_trigger', label: '打卡联动', icon: '✅' },
        { key: 'emotion_guide', label: '情绪引导', icon: '💖' },
        { key: 'mindfulness', label: '正念陪伴', icon: '🧘' },
      ],
      // TTS/ASR
      // ↓↓↓ 改造（2026-10-27）：初始值取自 settings 的「语音播报」开关，不再是死值 false ↓↓↓
      ttsEnabled: (typeof tts !== 'undefined') ? tts.getEnabled() : false,
      asrActive: false,
      recognition: null,
      recorderManager: null,
      // 阶段J: 上下文摘要
      contextSummary: '',
      // === 新功能面板状态 ===
      showGiftPanel: false,
      showStickerPanel: false,
      showChatSettingsPanel: false,
      // V7 操作弹层
      actionSheetVisible: false,
      actionSheetItems: [],
      showVoiceCall: false,
      singing: false,
      // 礼物动画
      giftAnimation: { show: false, icon: '🎁', key: 0 },
      // 聊天设置（气泡/背景/音色/语言/动作描述）
      chatSettings: { ...DEFAULT_CHAT_SETTINGS },
      // 全局错误标记
      _globalErrorHandlerInstalled: false,
      // 缺语音包提示只弹一次，避免每条消息都弹
      _langWarned: false,
      // 最近一次播报的文本（切换语种后重播用）
      _lastSpokenText: ''
    }
  },
  computed: {
    userInitial() {
      const name = this.$store.state.userInfo.nickname || '我'
      return name.charAt(0)
    },
    // ↓↓↓ 新增 ↓↓↓ 我的头像（有则用图片，无则回退到首字母）
    userAvatar() {
      return this.resolveAvatar(this.$store.state.userInfo)
    },
    aiName() {
      return this.$store.state.aiConfig.name || (this.currentCharacter && this.currentCharacter.name) || 'AI伙伴'
    },
    currentCharacterId() {
      return getActivePartnerId()
    },
    currentCharacter() {
      return getActivePartner()
    },
    aiGreeting() {
      return this.aiGreetingText || '早安呀~今天也要好好的~'
    },
    // === 设计稿：角色照片 / 风格标签 / 相伴天数 ===
    aiPhoto() {
      // 只按当前伙伴 id 取图，查询失败时返回空串由模板回退 emoji，
      // 不再兜底成林夕照片（否则自定义伙伴会显示成别人）
      return getPartnerAvatar(this.currentCharacter)
    },
    styleLabel() {
      return STYLE_LABELS[this.currentCharacter?.style] || '温柔'
    },
    partnerDays() {
      return this.$store.state.streakDays || 0
    },
    bondPercent() {
      return this.affectionProgress || 0
    },
    memoryCount() {
      return (this.$store.state.habitAI?.memories || []).length
    },
    memoryText() {
      const memories = this.$store.state.habitAI?.memories || []
      return (memories[0] && memories[0].content) || '你怕吵，喜欢下雨天读书。'
    },
    bondLevel() {
      const characterId = this.$store.state.aiConfig.avatarType || 'linxi'
      return this.$store.state.bondLevels[characterId] || null
    },
    displayMessages() {
      return this.messages
    },
    offlineCount() {
      return (this.$store.state.offlineMessages || []).length
    },
    currentSessionType() {
      return this.$store.getters.currentSessionType || 'chat'
    },
    // === AI伙伴状态（异步陪伴核心） ===
    // 状态规则：23:00-7:00 休息；14:00-16:00 深度忙碌；其余时间在线
    aiPartnerStatus() {
      const h = new Date().getHours()
      if (h >= 23 || h < 7) return 'rest'
      if (h >= 14 && h < 16) return 'busy'
      return 'online'
    },
    // 状态栏文案：结合流式/输入中/伙伴状态
    aiStatusText() {
      if (this.streamingActive) return '正在回复...'
      if (this.isTyping) {
        return this.aiPartnerStatus === 'busy' ? '正忙，稍后回复你...' : '正在输入...'
      }
      if (this.aiPartnerStatus === 'rest') return '休息中·轻声陪伴'
      if (this.aiPartnerStatus === 'busy') return '忙碌中·回复会慢一点'
      return '在线'
    },
    // === 好感度（对标循途关系体系） ===
    affectionTierName() {
      return this.$store.getters.affectionTierName || '初识'
    },
    affectionProgress() {
      return this.$store.getters.affectionProgress || 0
    },
    // === AI情绪（关联用户打卡/习惯数据） ===
    aiMood() {
      return aiSocial.getAIMood()
    },
    // === 自定义气泡样式 ===
    bubbleClass() {
      const s = this.chatSettings.bubbleStyle
      return s && s !== 'default' ? 'bubble-style-' + s : ''
    },
    // === 自定义聊天背景 ===
    chatPageStyle() {
      const bg = this.chatSettings.chatBackground
      const map = {
        default: {},
        mint: { background: 'linear-gradient(180deg, #E0F2F1, #F1F8E9)' },
        sunset: { background: 'linear-gradient(180deg, #FFF3E0, #FFE0B2)' },
        aurora: { background: 'linear-gradient(180deg, #1A2340, #0D0D0F)' }
      }
      if (bg === 'custom' && this.chatSettings.chatBackgroundImage) {
        return {}
      }
      return map[bg] || {}
    },
    statusBgOverride() {
      const bg = this.chatSettings.chatBackground
      if (bg === 'aurora') {
        return 'linear-gradient(135deg, #232B45, #1A2340)'
      }
      return null
    }
  },
  onLoad() {
    this.installGlobalErrorHandler()
    this.loadChatSettings()
    this.loadChatHistory()
    this.loadQuickReplies()
    this.initGreeting()
    this.checkOfflineMessages()
  },
  onShow() {
    this.scrollToBottom()
    // 打卡完成后AI伙伴主动推送鼓励消息（异步陪伴：不要求用户先说话）
    this.pushPendingProactiveMessage()
    // 主动话题：结合今日打卡情况/习惯状态，每天最多发起一次
    this.pushProactiveTopic()
    // ↓↓↓ 陪伴感增强 v3 ↓↓↓
    // 服务端主动陪伴：约定提醒 / 久未联系 / 今日日程 / 时段问候
    this.pushCompanionProactive()
    this.loadRoleVoiceTone()
    // ↑↑↑ 新增结束 ↑↑↑
    try {
      uni.hideTabBar({ animation: false, fail: () => {} })
    } catch (e) {}
  },
  onHide() {
    // 页面隐藏时停止语音识别和播报，释放资源
    if (this.asrActive) this.stopASR()
    // #ifdef H5
    if (typeof window !== 'undefined' && 'speechSynthesis' in window && this.ttsEnabled) {
      try {
        window.speechSynthesis.cancel()
      } catch (e) {
        console.error('取消TTS失败:', e)
      }
    }
    // #endif
  },
  onUnload() {
    aiSpeak.stop()
    if (this.asrActive) this.stopASR()
    stopMusic()
    // ↓↓↓ 修复 TC-PERF-003：页面卸载时解绑全局监听，避免监听器与组件实例泄漏 ↓↓↓
    this.uninstallGlobalErrorHandler()
    // ↑↑↑ 修复结束 ↑↑↑
    // #ifdef H5
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel()
      } catch (e) {
        console.error('取消TTS失败:', e)
      }
    }
    // #endif
  },
  onBackPress() {
    if (this.actionSheetVisible) {
      this.closeActionSheet()
      return true
    }
  },
  methods: {
    /**
     * ↓↓↓ 新增 ↓↓↓
     * 把用户对象里的头像字段解析成可直接给 <image src> 用的地址。
     * 拿不到有效头像时返回 ''，让模板回退到首字母占位。
     * 注意：blob:/wxfile:// 这类本地临时地址刷新后就失效了，一律按无头像处理。
     */
    resolveAvatar(user) {
      return toAvatarUrl((user && user.avatar) || '')
    },
    /**
     * 全局错误监听，防止未捕获异常冒泡
     */
    installGlobalErrorHandler() {
      if (this._globalErrorHandlerInstalled) return
      this._globalErrorHandlerInstalled = true
      // #ifdef H5
      if (typeof window !== 'undefined') {
        const originalOnError = window.onerror
        // ↓↓↓ 修复 TC-PERF-003 内存泄漏：保存引用，供 onUnload 解绑 ↓↓↓
        this._originalOnError = originalOnError
        this._rejectionHandler = (event) => {
          console.error('[全局捕获] Promise未捕获:', event.reason)
          event.preventDefault()
        }
        // ↑↑↑ 修复结束 ↑↑↑
        window.onerror = (msg, url, line, col, error) => {
          console.error('[全局捕获] 页面错误:', msg, url, line, col, error)
          if (originalOnError) {
            try { return originalOnError.call(window, msg, url, line, col, error) } catch (e) {}
          }
          return true
        }
        window.addEventListener('unhandledrejection', this._rejectionHandler)
      }
      // #endif
    },

    /**
     * ↓↓↓ 修复 TC-PERF-003 内存泄漏 ↓↓↓
     * 原实现在页面卸载时不解绑全局监听，反复进出聊天页会持续累积监听器，
     * 且监听器闭包持有组件实例，导致页面实例无法被回收（实测 3 轮后堆内存持续增长）。
     * 这里在 onUnload / onHide 时对称解绑。
     */
    uninstallGlobalErrorHandler() {
      // #ifdef H5
      if (typeof window === 'undefined') return
      if (this._rejectionHandler) {
        try {
          window.removeEventListener('unhandledrejection', this._rejectionHandler)
        } catch (e) {
          console.warn('移除 unhandledrejection 监听失败:', e)
        }
        this._rejectionHandler = null
      }
      if (this._globalErrorHandlerInstalled && '_originalOnError' in this) {
        try {
          window.onerror = this._originalOnError || null
        } catch (e) {}
        this._originalOnError = null
      }
      this._globalErrorHandlerInstalled = false
      // #endif
    },
    initGreeting() {
      const characterId = this.$store.state.aiConfig.avatarType || 'linxi'
      const character = getCharacterById(characterId)
      if (character && character.personalityType) {
        try {
          this.aiGreetingText = generateReply('早安', character.personalityType, buildContext(this.$store), characterId) || '早安呀~今天也要好好的~'
        } catch (e) {
          console.error('生成问候语失败:', e)
          this.aiGreetingText = '早安呀~今天也要好好的~'
        }
      }
    },
    async loadChatHistory() {
      try {
        const storedMessages = this.$store.state.chatMessages
        if (storedMessages && storedMessages.length > 0) {
          this.messages = [...storedMessages]
        } else {
          const res = await chatApi.getChatHistory()
          if (res.code === 200 && res.data.length > 0) {
            this.messages = res.data
            this.$store.commit('clearChatMessages')
            res.data.forEach(msg => {
              this.$store.commit('addChatMessage', msg)
            })
          }
        }
      } catch (e) {
        console.error('加载聊天记录失败:', e)
      }
      this.scrollToBottom()
    },
    async loadQuickReplies() {
      const characterId = this.$store.state.aiConfig.avatarType || 'linxi'
      const character = getCharacterById(characterId)
      this.quickReplies = [
        '今天心情不太好',
        '我有点想拖延',
        '给我一些鼓励吧',
        '完成了一个任务！',
        '我需要放松一下'
      ]
      if (character?.personality) {
        if (character.personality.includes('温柔')) {
          this.quickReplies.push('抱抱我')
        }
        if (character.personality.includes('活泼') || character.personality.includes('活力')) {
          this.quickReplies.push('陪我一起加油！')
        }
        if (character.personality.includes('智慧') || character.personality.includes('导师')) {
          this.quickReplies.push('给我一些建议')
        }
      }
      // ↑↑↑ 新增结束 ↑↑↑
    },
    /**
     * 检查离线消息缓存，网络恢复后自动发送
     * 修复边界异常：逐条串行发送，避免多条消息并发触发多个流式回复互相覆盖
     */
    async checkOfflineMessages() {
      const offline = this.$store.state.offlineMessages || []
      if (offline.length === 0) return
      this.$store.commit('clearOfflineMessages')
      for (const msg of offline) {
        try {
          await this.doSend(msg.content, true)
        } catch (e) {
          console.error('离线消息重发失败:', e)
        }
      }
    },
    /**
     * 异步陪伴：根据AI伙伴状态计算回复延迟（毫秒）
     * 在线：300-700ms（接近秒回）；忙碌：1200-2200ms；休息：2000-3500ms
     */
    getReplyDelay() {
      if (this.aiPartnerStatus === 'rest') return 2000 + Math.floor(Math.random() * 1500)
      if (this.aiPartnerStatus === 'busy') return 1200 + Math.floor(Math.random() * 1000)
      return 300 + Math.floor(Math.random() * 400)
    },
    /**
     * 消息撤回模拟：AI偶尔"撤回重说"，模拟真人聊天细节
     * 2.5s后将该消息标记为已撤回，再过2s补发一条重新组织的内容
     */
    scheduleRecall(msg) {
      setTimeout(() => {
        try {
          const idx = this.messages.indexOf(msg)
          if (idx === -1 || msg.recalled) return
          // 本地列表标记撤回（替换对象以触发响应式更新）
          this.messages.splice(idx, 1, { ...msg, recalled: true })
          // 同步到 store 持久化（按内容+时间定位，避免下标漂移）
          const storeMsgs = this.$store.state.chatMessages
          const sIdx = storeMsgs.findIndex(m => m.time === msg.time && m.content === msg.content && m.role === 'assistant')
          if (sIdx !== -1) {
            this.$store.commit('recallChatMessage', { index: sIdx, recalled: true })
          }
          // 撤回后补发"重新说"的消息
          setTimeout(() => {
            const rewritten = this.generateRecallRewrite(msg.content)
            if (!rewritten) return
            const newMsg = {
              role: 'assistant',
              content: rewritten,
              emotion: msg.emotion || 'normal',
              time: this.now()
            }
            this.messages.push(newMsg)
            this.$store.commit('addChatMessage', newMsg)
            this.scrollToBottom()
          }, 2000)
        } catch (e) {
          console.error('撤回模拟失败:', e)
        }
      }, 2500)
    },
    /**
     * 撤回后的重说内容：轻微改写原句，模拟"重新组织语言"
     */
    generateRecallRewrite(original) {
      if (!original) return ''
      const prefixes = ['重新说一次——', '刚才没说好，这样说：', '想了想，还是这样说吧：', '']
      const prefix = prefixes[Math.floor(Math.random() * prefixes.length)]
      return prefix + original
    },
    /**
     * 打卡完成后AI伙伴主动推送鼓励消息（异步陪伴：AI主动找用户）
     * 消费其他页面（陪伴页/盲盒/悬浮助手等）写入的 pendingProactiveMessage
     */
    pushPendingProactiveMessage() {
      let pending = null
      try {
        pending = uni.getStorageSync('pending_proactive_message')
      } catch (e) {
        return
      }
      if (!pending || !pending.content) return
      // 立即清除，避免重复推送
      try {
        uni.removeStorageSync('pending_proactive_message')
      } catch (e) {}
      const aiMsg = {
        role: 'assistant',
        content: pending.content,
        emotion: 'happy',
        time: this.now()
      }
      this.messages.push(aiMsg)
      this.$store.commit('addChatMessage', aiMsg)
      this.scrollToBottom()
    },
    /**
     * 输入防抖
     */
    onInput() {
      // 输入时的防抖逻辑（可选：输入状态指示等）
    },
    /**
     * 发送消息入口 - 包含防抖 + 危机检测
     */
    async send() {
      const content = this.inputText.trim()
      // ↓↓↓ 修复 BUG-003：内容为空时给出明确提示，而不是静默无响应 ↓↓↓
      if (!content) {
        if (!this.isSending && !this.streamingActive) {
          uni.showToast({ title: '请输入内容后再发送', icon: 'none', duration: 1500 })
        }
        return
      }
      // ↑↑↑ 修复结束 ↑↑↑
      if (this.isSending || this.streamingActive) return

      // 防抖：500ms内不允许重复发送
      const now = Date.now()
      if (now - this.lastSendTime < 500) return
      this.lastSendTime = now
      this.isSending = true

      try {
        // 1. 危机检测
        const crisisRes = await chatApi.crisisCheck(content)
        if (crisisRes.code === 200 && crisisRes.data?.is_crisis) {
          // 检测到危机 - 暂存消息，弹出干预弹窗
          this.pendingContent = content
          this.crisisData = crisisRes.data
          this.showCrisisModal = true
          // ↓↓↓ 新增（2026-10-28 打卡陪伴）：记下危机期（24h），打卡页据此不再主动弹伙伴陪伴 ↓↓↓
          try {
            uni.setStorageSync('crisis_active_until', Date.now() + 24 * 60 * 60 * 1000)
          } catch (e) { /* 静默 */ }
          // ↑↑↑ 新增结束 ↑↑↑
          // 仍将用户消息显示在聊天中
          this.addUserMessage(content)
          this.inputText = ''
          this.isSending = false
          return
        }

        // 1.5 ↓↓↓ 安全合规批次：本地高危信号预检（后端 /chat/send 还有同源闸门兜底） ↓↓↓
        const dangerRes = checkDanger(content)
        if (dangerRes.isDanger) {
          this.dangerWarnData = { message: dangerRes.message, resources: dangerRes.resources }
          this.showDangerWarn = true
          this.addUserMessage(content)
          this.inputText = ''
          this.isSending = false
          return
        }
        // ↑↑↑ 新增结束 ↑↑↑

        // 2. 正常发送
        await this.doSend(content, false)
      } catch (e) {
        console.error('发送失败:', e)
        this.isSending = false
      }
    },
    /**
     * 实际发送逻辑（流式输出）
     */
    async doSend(content, isFromOffline = false) {
      if (!isFromOffline) {
        this.addUserMessage(content)
        this.inputText = ''
      }

      this.showQuickReplies = false
      // 新的一句话发出去后，上一条回复推荐的功能卡片自动收起
      this.suggestionCard = null
      this.isTyping = true
      this.scrollToBottom()

      let fullContent = ''
      let emotion = 'normal'
      let sendSuccess = false

      try {
        // 异步陪伴：根据AI伙伴状态决定回复延迟（在线秒回感 / 忙碌慢一点 / 休息最慢）
        await this.delay(this.getReplyDelay())

        this.isTyping = false
        this.streamingActive = true
        this.streamingMessage = ''
        this.$store.commit('setStreamingActive', true)
        this.scrollToBottom()

        // 构建30轮上下文
        const context = this.buildContext()

        const characterId = this.$store.state.aiConfig.avatarType || 'linxi'
        const persona = this.getPersonaName(characterId)

        // 情绪识别联动：根据用户消息情绪调整AI情感倾向（影响回复语气）
        try {
          const userEmo = mock.chatEmotionAnalysis(content)
          if (userEmo && userEmo.type && userEmo.type !== 'normal') {
            this.aiEmotion = userEmo.type
          }
        } catch (e) {
          // 情绪分析失败不影响正常发送
        }

        // 流式发送（对齐后端 ChatSendRequest 字段：role_type/dialogue_style/scene_type/scene_name/session_id）
        const result = await chatApi.streamSend(
          content,
          (chunk) => {
            this.streamingMessage += chunk
            this.$store.commit('appendStreamingChunk', chunk)
            this.scrollToBottom()
          },
          {
            role_type: persona || characterId || 'companion',
            // ↓↓↓ v3.1：把「真实角色标识」单独传过去 ↓↓↓
            // role_type 一直是对话风格 token（relaxed/y2k…），后端拿它查不到 ai_roles，
            // 于是人设从来没被注入、记忆还会串到同一个桶里。role_key 才是角色的主键。
            role_key: this.resolveRoleKey(),
            dialogue_style: this.aiEmotion || 'gentle',
            scene_type: 'daily',
            scene_name: '',
            session_id: this.currentSessionId || 0,
            // AI 降级事件：后端大模型未配置/熔断/失败时回传，前端显示离线陪伴提示
            onAIMeta: (meta) => {
              this.aiDegraded = !!(meta && meta.degraded)
            },
            // 后端首个事件回传 session_id：存下来，后续消息复用同一会话，
            // 服务端才攒得下上下文（这是"AI 记得上一句"的前提）
            onSessionId: (id) => {
              if (id) this.currentSessionId = id
            },
            // ↓↓↓ 安全合规批次：后端 /chat/send 高危检测命中时回传 danger 事件 ↓↓↓
            onDanger: (danger) => {
              if (!danger) return
              this.dangerWarnData = {
                message: danger.message || '我们收到了一些让你痛苦的信号。',
                resources: danger.resources || []
              }
              this.showDangerWarn = true
              // 中断流式状态，避免输入框一直转圈
              this.streamingActive = false
              this.isTyping = false
              this.$store.commit('resetStreaming')
            },
            // ↑↑↑ 新增结束 ↑↑↑
            // ↓↓↓ 模块1 新增：后端情绪感知分支回传 emotion_comfort 事件 ↓↓↓
            // 只在后端识别到负面情绪且 triggered=true 时触发；失败时不回传（降级静默）
            onEmotionComfort: (emo) => {
              if (!emo || !emo.triggered) return
              this.emotionGuideData = {
                emotion: emo.emotion || '',
                valence: emo.valence || '',
                triggered: emo.triggered || false,
                venting: emo.venting || false,
                crisis: emo.crisis || false,
              }
              this.showEmotionGuide = true
              // 如果是危机级负面情绪，自动推荐正念呼吸
              if (emo.crisis) {
                try { uni.vibrateShort({ type: 'medium' }) } catch (e) {}
              }
            },
            // ↑↑↑ 模块1 新增结束 ↑↑↑
            // ↓↓↓ 新增（2026-11-15）：后端按这句话推荐的功能（正念 / 情绪树洞 / 专注…） ↓↓↓
            onSuggestion: (sug) => {
              const items = (sug && sug.items) || []
              // 只认后端规则命中的第一条；没有命中就不展示，避免每条回复都挂卡片
              this.suggestionCard = items.length ? items[0] : null
            },
            // ↑↑↑ 新增结束 ↑↑↑
            // ↓↓↓ 多语言：把当前语种告诉后端，后端注入 system prompt 让 AI 用该语种回复 ↓↓↓
            language: normalizeVoiceLang(this.chatSettings.voiceLang),
          }
        )

        // 流式结束，构建完整消息
        fullContent = typeof result === 'string' ? result : (result.reply || this.streamingMessage)
        emotion = typeof result === 'object' ? result.emotion : 'normal'
        sendSuccess = true

      } catch (e) {
        console.error('流式发送失败:', e)
        // 离线缓存
        this.$store.commit('addOfflineMessage', { content, time: this.now() })

        // 降级到本地回复（确保非空）
        const characterId = this.$store.state.aiConfig.avatarType || 'linxi'
        let localReply = this.generateLocalReply(content, characterId)
        // 多语言：本地规则引擎只有中文语料，非中文语种时改用该语种的兜底短句，
        // 避免"选了 English 却蹦出一句中文"（离线模式下无法真正翻译）
        try {
          if (normalizeVoiceLang(this.chatSettings.voiceLang) !== 'zh-CN') {
            const foreign = pickOfflineReply(this.chatSettings.voiceLang)
            if (foreign) localReply = foreign
          }
        } catch (e) { /* 静默：降级不影响原流程 */ }
        if (!localReply || typeof localReply !== 'string' || localReply.trim() === '') {
          localReply = '嗯嗯，我在听呢~'
        }
        fullContent = localReply
        emotion = 'normal'

        uni.showToast({ title: '网络异常，已切换离线模式', icon: 'none', duration: 2000 })
      } finally {
        this.isTyping = false
        this.streamingActive = false
        this.$store.commit('resetStreaming')
      }

      // 确保 AI 回复内容非空
      if (!fullContent || typeof fullContent !== 'string' || fullContent.trim() === '') {
        fullContent = '好的，我明白了~'
      }

      // 构建并添加 AI 消息
      const aiMsg = {
        role: 'assistant',
        content: fullContent,
        emotion: emotion || 'normal',
        time: this.now(),
        // 动作描述开关：开启时AI回复附带角色动作
        action: this.chatSettings.actionDescEnabled ? this.generateAction() : ''
      }
      this.messages.push(aiMsg)
      this.$store.commit('addChatMessage', aiMsg)

      // 消息撤回模拟：小概率AI"撤回重说"，模拟真人聊天细节
      if (sendSuccess && Math.random() < 0.08) {
        this.scheduleRecall(aiMsg)
      }

      // 分析用户消息情绪（仅在发送成功时）
      if (sendSuccess && this.messages.length >= 2) {
        try {
          const userEmotion = mock.chatEmotionAnalysis(content)
          const userMsg = this.messages[this.messages.length - 2]
          if (userMsg.role === 'user') {
            userMsg.emotion = userEmotion.type
            userMsg.emotionIntensity = userEmotion.intensity
          }
        } catch (e) {
          console.error('情绪分析失败:', e)
        }
      }

      // 羁绊经验
      try {
        const characterId = this.$store.state.aiConfig.avatarType || 'linxi'
        this.$store.commit('addBondExp', { characterId, exp: 1 })
      } catch (e) {
        console.error('羁绊经验增加失败:', e)
      }

      this.showQuickReplies = true
      this.scrollToBottom()

      // TTS 自动朗读
      if (this.ttsEnabled) {
        // ↓↓↓ 陪伴感增强 v3：改走带语气起伏的版本（失败会自动退回 speakText） ↓↓↓
        this.speakTextExpressive(fullContent)
      }

      this.isSending = false
    },
    /**
     * 添加用户消息（含情绪分析）
     */
    addUserMessage(content) {
      let emotionType = 'normal'
      let emotionIntensity = 0
      try {
        const emotion = mock.chatEmotionAnalysis(content)
        emotionType = emotion.type
        emotionIntensity = emotion.intensity
      } catch (e) {
        console.error('情绪分析失败:', e)
      }
      const userMsg = {
        role: 'user',
        content,
        emotion: emotionType,
        emotionIntensity: emotionIntensity,
        time: this.now()
      }
      this.messages.push(userMsg)
      this.$store.commit('addChatMessage', userMsg)
      this.scrollToBottom()
    },
    /**
     * 构建最近30轮上下文 (阶段J增强: 注入AI记忆 + 情绪 + 会话类型)
     */
    buildContext() {
      const recent = this.messages.slice(-60) // 30轮 = 60条消息
      const context = recent.map(msg => ({
        role: msg.role,
        content: msg.content || ''
      }))
      // 阶段J: 注入上下文摘要(超过30轮的早期对话压缩)
      if (this.contextSummary) {
        context.unshift({ role: 'system', content: `[早期对话摘要] ${this.contextSummary}` })
      }
      return context
    },
    /**
     * 阶段J: 切换会话类型
     */
    switchSessionType(type) {
      this.$store.commit('setSessionType', type)
      const sessionLabels = {
        chat: '日常聊天模式',
        checkin_trigger: '打卡联动模式 - 完成打卡后AI会给予专属反馈',
        emotion_guide: '情绪引导模式 - AI会根据你的情绪状态调整回应',
        mindfulness: '正念陪伴模式 - AI会引导你进行呼吸和冥想',
      }
      uni.showToast({ title: sessionLabels[type] || '已切换', icon: 'none', duration: 2000 })
    },
    /**
     * TTS 语音播放 - 使用浏览器原生 Speech Synthesis API
     */
    toggleTTS() {
      this.ttsEnabled = !this.ttsEnabled
      if (this.ttsEnabled) {
        // H5 环境使用 Web Speech API
        // #ifdef H5
        if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
          uni.showToast({ title: '语音播报已开启', icon: 'none', duration: 1200 })
          const lastAI = [...this.messages].reverse().find(m => m.role === 'assistant')
          if (lastAI && lastAI.content) {
            this.speakTextExpressive(lastAI.content)
          }
        } else {
          this.ttsEnabled = false
          uni.showToast({ title: '当前环境不支持语音播报', icon: 'none' })
        }
        // #endif
        // #ifndef H5
        // 小程序/App 环境：尝试使用 uni.createInnerAudioContext 或提示
        try {
          const innerAudioContext = uni.createInnerAudioContext()
          if (innerAudioContext) {
            uni.showToast({ title: '语音播报已开启', icon: 'none', duration: 1200 })
          } else {
            this.ttsEnabled = false
            uni.showToast({ title: '当前环境暂不支持语音播报', icon: 'none' })
          }
        } catch (e) {
          this.ttsEnabled = false
          uni.showToast({ title: '当前环境暂不支持语音播报', icon: 'none' })
        }
        // #endif
      } else {
        aiSpeak.stop()
        // #ifdef H5
        if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
          try {
            window.speechSynthesis.cancel()
          } catch (e) {
            console.error('取消TTS失败:', e)
          }
        }
        // #endif
        uni.showToast({ title: '语音播报已关闭', icon: 'none', duration: 1000 })
      }
    },
    // ↓↓↓ 陪伴感增强 v3 ↓↓↓
    /**
     * 拉一条「TA 主动说的话」：约定提醒 / 久未联系 / 今日日程 / 时段问候。
     * 服务端做了 24 小时去重，同一件事不会反复打扰；没有值得说的就返回 null，
     * 这时不硬塞气泡。
     */
    async pushCompanionProactive() {
      if (this.proactiveLoaded) return
      this.proactiveLoaded = true
      try {
        const roleKey = this.currentRoleKey()
        const res = await proactiveApi.next(roleKey, this.currentSessionId || 0, true)
        const d = res && res.data
        if (!d || !d.content) return
        const aiMsg = {
          role: 'assistant',
          content: d.content,
          emotion: 'gentle',
          time: this.now(),
          proactive: true,
          proactiveType: d.type
        }
        this.messages.push(aiMsg)
        this.$store.commit('addChatMessage', aiMsg)
        this.scrollToBottom()
        if (this.ttsEnabled) this.speakTextExpressive(d.content, 'gentle')
        if (d.id) {
          try { await proactiveApi.markRead(d.id) } catch (e) { /* 静默 */ }
        }
      } catch (e) {
        // 主动陪伴是加分项，拿不到就安静跳过，绝不影响聊天本身
        console.log('主动陪伴消息获取失败:', e && e.message)
      }
    },

    /** 当前角色标识（自定义/扭蛋角色的 role_key 直接存在 aiConfig.avatarType 里） */
    currentRoleKey() {
      return this.resolveRoleKey()
    },

    /**
     * 当前角色的「真实标识」= ai_roles.role_type
     *
     * 为什么不能直接用 avatarType：
     *   本地自捏角色的 id 是 `custom_<时间戳>_<随机>`（前端造的），
     *   而云端 ai_roles.role_type 是 `custom_<用户id>_<随机>`（后端造的）。
     * 两者必须用后者去查库，否则：
     *   ① 后端查不到角色 → 人设/雷区/称呼全部不生效；
     *   ② 记忆按 role_key 隔离 → 所有角色共用一个桶，聊天会"记串"。
     * 云端同步成功时会把 roleKey 写回本地角色，这里优先用它。
     */
    resolveRoleKey() {
      const cfg = this.$store.state.aiConfig || {}
      const id = cfg.avatarType || 'linxi'
      const list = this.$store.state.customCharacters || []
      const hit = Array.isArray(list) ? list.find(c => c && c.id === id) : null
      return (hit && hit.roleKey) ? hit.roleKey : id
    },

    /** 取当前角色的音色，用于 TTS 语气 */
    async loadRoleVoiceTone() {
      try {
        const key = this.currentRoleKey()
        const res = await personaApi.getRoleByKey(key)
        const d = res && res.data
        if (d && d.voiceTone) this.roleVoiceTone = d.voiceTone
      } catch (e) {
        this.roleVoiceTone = ''
      }
    },

    /**
     * 带语气起伏地播报（分句 + 停顿 + 情绪）。
     * 环境不支持或开关关闭时自动退回原来的 speakText，行为与接入前一致。
     */
    async speakTextExpressive(text, emotionHint) {
      if (!text || !this.ttsEnabled) return
      // P0：优先走后端 TTS（音色统一，H5/App 都能出声，语音包选择才会生效）
      const langCfg = getVoiceLang(this.chatSettings.voiceLang)
      const played = await aiSpeak.speak(text, {
        lang: langCfg.code,
        rate: this.chatSettings.rate,
        pitch: this.chatSettings.pitch,
        fallback: false
      })
      if (!this.ttsEnabled) {
        aiSpeak.stop()
        return
      }
      if (played) return
      // 后端不可用时退回浏览器逐句播报
      const emotion = emotionHint || detectEmotion(text)
      const ok = speakExpressive(text, {
        emotion,
        tone: this.roleVoiceTone || 'warm',
        lang: langCfg.code,
        rate: this.chatSettings.rate,
        pitch: this.chatSettings.pitch
      })
      // 不支持逐句播报的环境（非 H5 / 无 speechSynthesis）退回原实现
      if (!ok) this.speakText(text)
    },
    // ↑↑↑ 新增结束 ↑↑↑

    /**
     * 使用 Speech Synthesis 播报文本
     * 失败策略（2026-11-09）：不再弹「语音播放失败」打断用户 ——
     * 1) 上一句被 cancel() 打断（interrupted/canceled）不算失败，静默忽略；
     * 2) 所选语种发音失败（系统没装该语言语音包等）→ 自动用默认发音静默重试一次；
     * 3) 重试仍失败 → 只写 console，不弹 toast（避免频繁打扰）。
     */
    speakText(text) {
      if (!text || typeof text !== 'string' || text.trim() === '') return
      const textToSpeak = text

      // #ifdef H5
      if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
        console.warn('TTS: 当前环境不支持 speechSynthesis')
        return
      }
      try {
        window.speechSynthesis.cancel()

        const trySpeak = (useDefaultVoice) => {
          try {
            const utterance = new SpeechSynthesisUtterance(textToSpeak)
            if (!useDefaultVoice) {
              // 应用自定义音色/多语言设置
              const langCfg = getVoiceLang(this.chatSettings.voiceLang)
              utterance.lang = langCfg.code
              // 匹配所选语种的系统语音：完全相等 > 主语言前缀 > 别名前缀
              const voices = window.speechSynthesis.getVoices()
              const matched = matchSystemVoice(langCfg.code, voices)
              if (matched) {
                utterance.voice = matched
              } else if (voices && voices.length && !this._langWarned) {
                // 只在首次发现"装了语音但没这个语种"时提示一次，避免每条消息都弹
                this._langWarned = true
                uni.showToast({
                  title: `系统无${langCfg.name}语音包，已用默认发音`,
                  icon: 'none',
                  duration: 2000
                })
              }
            }
            utterance.rate = this.chatSettings.rate || 1.0
            utterance.pitch = this.chatSettings.pitch || 1.0
            utterance.volume = 1.0

            utterance.onend = () => {
              this._lastSpokenText = textToSpeak
            }

            utterance.onerror = (e) => {
              const err = (e && (e.error || e.errorCode)) || ''
              // 被新播报打断/取消不算失败（先判断再记录，避免刷出无意义报错）
              if (err === 'interrupted' || err === 'canceled' || err === 'cancelled') return
              console.error('TTS utterance错误:', err || e)
              // 语种发音失败 → 静默降级为默认发音重试一次
              if (!useDefaultVoice) {
                trySpeak(true)
              }
            }

            window.speechSynthesis.speak(utterance)
          } catch (err) {
            console.error('TTS播放失败:', err)
            if (!useDefaultVoice) trySpeak(true)
          }
        }

        // 检查 voices 是否已加载
        const voices = window.speechSynthesis.getVoices()
        if (!voices || voices.length === 0) {
          // 监听 voiceschanged 事件，语音列表加载完成后再播放
          const onVoicesChanged = () => {
            window.speechSynthesis.removeEventListener('voiceschanged', onVoicesChanged)
            trySpeak(false)
          }
          window.speechSynthesis.addEventListener('voiceschanged', onVoicesChanged)
          // 设置超时防止 voiceschanged 不触发
          setTimeout(() => {
            window.speechSynthesis.removeEventListener('voiceschanged', onVoicesChanged)
            trySpeak(false)
          }, 2000)
        } else {
          trySpeak(false)
        }
      } catch (e) {
        console.error('TTS启动失败:', e)
      }
      // #endif

      // #ifndef H5
      try {
        // 小程序/App 环境：提示
        uni.showToast({ title: '当前环境暂不支持语音播报', icon: 'none', duration: 1500 })
      } catch (e) {
        console.error('TTS提示失败:', e)
      }
      // #endif
    },
    /**
     * ASR 语音输入 - 使用浏览器原生 Speech Recognition API
     */
    toggleASR() {
      if (this.asrActive) {
        // 正在录音，点击则停止
        this.stopASR()
        return
      }

      // 先申请麦克风权限
      uni.authorize({
        scope: 'scope.record',
        success: () => {
          this._startASRInternal()
        },
        fail: (err) => {
          console.error('麦克风权限申请失败:', err)
          // 用户拒绝，引导去设置
          uni.showModal({
            title: '需要麦克风权限',
            content: '语音输入功能需要使用麦克风，请在设置中开启麦克风权限',
            confirmText: '去设置',
            cancelText: '取消',
            success: (res) => {
              if (res.confirm) {
                uni.openSetting({
                  success: (settingRes) => {
                    if (settingRes.authSetting && settingRes.authSetting['scope.record']) {
                      this._startASRInternal()
                    } else {
                      uni.showToast({ title: '未开启麦克风权限', icon: 'none' })
                    }
                  },
                  fail: () => {
                    uni.showToast({ title: '打开设置失败', icon: 'none' })
                  }
                })
              }
            },
            fail: () => {}
          })
        }
      })
    },
    _startASRInternal() {
      // #ifdef H5
      if (typeof window === 'undefined') {
        uni.showToast({ title: '当前环境不支持语音输入', icon: 'none' })
        return
      }
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      if (!SpeechRecognition) {
        uni.showToast({ title: '浏览器不支持语音识别\n建议使用Chrome浏览器', icon: 'none', duration: 2500 })
        return
      }
      try {
        this.recognition = new SpeechRecognition()
        // 语音输入语种跟随"语音多语言"设置（原实现写死 zh-CN，切语种后识别仍按中文）
        this.recognition.lang = getAsrLang(this.chatSettings.voiceLang)
        this.recognition.continuous = false
        this.recognition.interimResults = false
        this.recognition.maxAlternatives = 1

        this.recognition.onstart = () => {
          this.asrActive = true
          uni.showToast({ title: '请说话...', icon: 'none', duration: 1500 })
        }

        this.recognition.onresult = (event) => {
          if (event.results && event.results.length > 0) {
            const transcript = event.results[0][0].transcript
            if (transcript) {
              this.inputText = transcript
              uni.showToast({ title: '识别完成', icon: 'success', duration: 1000 })
            } else {
              uni.showToast({ title: '未识别到语音内容', icon: 'none' })
            }
          }
        }

        this.recognition.onerror = (event) => {
          console.error('语音识别错误:', event.error)
          this.asrActive = false
          const errorMap = {
            'no-speech': '未检测到语音，请重试',
            'audio-capture': '麦克风访问失败，请检查权限',
            'not-allowed': '麦克风权限被拒绝，请允许访问',
            'network': '网络错误，语音识别需要联网',
            'aborted': '语音识别已取消'
          }
          const msg = errorMap[event.error] || '语音识别失败，请重试'
          if (event.error !== 'aborted') {
            uni.showToast({ title: msg, icon: 'none', duration: 2000 })
          }
        }

        this.recognition.onend = () => {
          this.asrActive = false
        }

        this.recognition.start()
      } catch (e) {
        console.error('启动语音识别失败:', e)
        this.asrActive = false
        uni.showToast({ title: '语音识别启动失败', icon: 'none' })
      }
      // #endif
      // #ifndef H5
      // 小程序/App 环境使用录音管理器
      this.startMiniProgramRecord()
      // #endif
    },
    /**
     * 停止语音识别
     */
    stopASR() {
      // #ifdef H5
      if (this.recognition) {
        try {
          this.recognition.stop()
        } catch (e) {
          console.error('停止语音识别失败:', e)
        }
        this.recognition = null
      }
      // #endif
      // #ifndef H5
      if (this.recorderManager) {
        try {
          this.recorderManager.stop()
        } catch (e) {
          console.error('停止录音失败:', e)
        }
      }
      // #endif
      this.asrActive = false
    },
    /**
     * 小程序环境录音（降级方案：录音后提示手动转写）
     */
    startMiniProgramRecord() {
      // #ifndef H5
      try {
        this.recorderManager = uni.getRecorderManager()
        if (!this.recorderManager) {
          uni.showToast({ title: '录音功能不可用', icon: 'none' })
          this.asrActive = false
          return
        }

        this.recorderManager.onStart(() => {
          this.asrActive = true
          uni.showToast({ title: '正在录音...再次点击结束', icon: 'none', duration: 1500 })
        })

        this.recorderManager.onError((err) => {
          console.error('录音错误:', err)
          this.asrActive = false
          let msg = '录音失败，请检查权限'
          if (err && err.errMsg) {
            if (err.errMsg.includes('auth') || err.errMsg.includes('deny') || err.errMsg.includes('permission')) {
              msg = '麦克风权限未开启，请在设置中授权'
            } else if (err.errMsg.includes('not support')) {
              msg = '当前设备不支持录音'
            }
          }
          uni.showToast({ title: msg, icon: 'none' })
        })

        this.recorderManager.onStop((res) => {
          this.asrActive = false
          if (res && res.duration < 1000) {
            uni.showToast({ title: '录音太短，请重试', icon: 'none' })
            return
          }
          // 小程序无云端ASR，提示用户手动输入
          uni.showToast({ title: '录音完成，请手动输入文字', icon: 'none', duration: 2000 })
        })

        this.recorderManager.start({
          format: 'mp3',
          duration: 60000,
          sampleRate: 16000,
          numberOfChannels: 1
        })
      } catch (e) {
        console.error('启动录音失败:', e)
        this.asrActive = false
        uni.showToast({ title: '录音功能不可用', icon: 'none' })
      }
      // #endif
    },
    /**
     * 获取persona名称
     */
    getPersonaName(characterId) {
      const character = getCharacterById(characterId)
      if (!character) return 'relaxed'
      const map = {
        'linxi': 'relaxed', 'mianmian': 'relaxed',
        'yuki': 'y2k', 'kira': 'y2k',
        'yueqing': 'chinese', 'fengye': 'chinese',
        'nova': 'cyber', 'zero': 'cyber',
        'xingchen': 'artsy', 'muhan': 'artsy',
        'qinghe': 'cool', 'chenfeng': 'cool',
        'sunny': 'energetic', 'lele': 'energetic',
        'longling': 'mythical', 'baihu': 'mythical',
        'qingluan': 'mythical', 'xuanwu': 'mythical',
        'huoyun': 'mythical', 'lingling': 'mythical'
      }
      return map[characterId] || character.personalityType || 'relaxed'
    },
    generateLocalReply(content, characterId) {
      try {
        const character = getCharacterById(characterId)
        if (!character || !character.personalityType) {
          return '嗯嗯，我在听呢~'
        }

        // 行走地图相关关键词检测
        const walkKeywords = ['走到哪', '走到哪里', '地图', '行走', '旅程', '走路', '前进', '走到', '关卡', '海岛', '雪山', '森林', '海滨', '星空', '草原', '云海', '终点', '起点', '脚步', '走到哪了']
        const isWalkRelated = walkKeywords.some(kw => content && content.includes && content.includes(kw))

        if (isWalkRelated) {
          try {
            const totalCheckins = this.$store.getters.totalCheckins
            const currentStage = getCurrentStage(totalCheckins)
            const dialogue = getRandomLocationDialogue(characterId, currentStage.id)
            if (dialogue && typeof dialogue === 'string' && dialogue.trim() !== '') return dialogue
          } catch (e) {
            console.error('行走地图对话生成失败:', e)
          }
        }

        let reply = ''
        if (isCustomCharacter(characterId)) {
          reply = generateCustomReply(content, character, buildContext(this.$store))
        } else {
          reply = generateReply(content, character.personalityType, buildContext(this.$store), characterId)
        }

        if (!reply || typeof reply !== 'string' || reply.trim() === '') {
          return '嗯嗯，我在听呢~'
        }
        return reply
      } catch (e) {
        console.error('生成本地回复失败:', e)
        return '嗯嗯，我在听呢~'
      }
    },
    /**
     * 关闭危机干预弹窗
     */
    closeCrisisModal() {
      this.showCrisisModal = false
      this.pendingContent = ''
    },
    /**
     * 危机干预后继续对话
     */
    continueAfterCrisis() {
      this.showCrisisModal = false
      // AI发送一条关怀回复
      const responseContent = this.crisisData.response || '我在这里陪着你，你愿意和我说说发生了什么吗？'
      const aiMsg = {
        role: 'assistant',
        content: responseContent,
        emotion: 'gentle',
        time: this.now()
      }
      this.messages.push(aiMsg)
      this.$store.commit('addChatMessage', aiMsg)
      this.pendingContent = ''
      this.scrollToBottom()

      // TTS 自动朗读
      if (this.ttsEnabled) {
        this.speakTextExpressive(responseContent, 'quiet')
      }
    },
    // ↓↓↓ 模块1 新增：情绪引导跳转方法 ↓↓↓
    closeEmotionGuide() {
      this.showEmotionGuide = false
    },
    goMeditation() {
      this.showEmotionGuide = false
      try {
        uni.navigateTo({ url: '/pages/meditation/meditation' })
      } catch (e) {
        uni.switchTab({ url: '/pages/meditation/meditation' }).catch(() => {})
      }
    },
    // ↑↑↑ 模块1 新增结束 ↑↑↑
    // ↓↓↓ 新增（2026-11-15）：点击 AI 推荐的功能卡片，跳到对应页面 ↓↓↓
    openSuggestion(item) {
      if (!item || !item.route) return
      const url = item.route
      const clear = () => { this.suggestionCard = null }
      const onFail = () => {
        // 目标页不存在或页面栈已满才会走到这里：收起卡片并给出反馈，避免"点了没反应"
        clear()
        uni.showToast({ title: '页面打开失败，请稍后再试', icon: 'none' })
      }
      try {
        uni.navigateTo({
          url,
          // 跳转成功后再收起卡片；直接打开本页（无页面栈）等异常走 fail 兜底
          success: clear,
          fail: () => {
            try { uni.switchTab({ url, success: clear, fail: onFail }) } catch (e) { onFail() }
          }
        })
      } catch (e) {
        onFail()
      }
    },
    // ↑↑↑ 新增结束 ↑↑↑
    sendQuickReply(text) {
      if (!text || typeof text !== 'string') return
      const trimmedText = text.trim()
      if (!trimmedText) return
      this.inputText = trimmedText
      this.$nextTick(() => {
        if (this.inputText.trim()) {
          this.send()
        }
      })
    },
    /** 顶部返回：非 tab 进入时回退，否则回到陪伴首页 */
    goBack() {
      if (getCurrentPages().length > 1) {
        uni.navigateBack()
      } else {
        uni.switchTab({ url: '/pages/index/index' })
      }
    },
    /** 【原有文件极小改动·模块4】跳转多人聊天，不影响单人聊天任何行为 */
    goGroupChat() {
      uni.navigateTo({ url: '/pages/group-chat/group-chat' })
    },
    /** 输入栏「+」：原有功能按钮收进操作菜单 */
    openFeatureSheet() {
      // 长按已打开「更多」时，松手可能补发一次 click，忽略之，避免菜单被覆盖
      if (this.actionSheetVisible) return
      const items = [
        { key: 'gift', icon: '🎁', label: '送礼物', run: () => this.openGiftPanel() },
        { key: 'sticker', icon: '😊', label: '表情包', run: () => { this.showStickerPanel = true } },
        { key: 'image', icon: '🖼️', label: '发图片', run: () => this.sendImage() },
        { key: 'sing', icon: '🎵', label: '唱首歌', run: () => this.aiSing() },
        { key: 'deco', icon: '🎨', label: '聊天装扮', run: () => { this.showChatSettingsPanel = true } },
        { key: 'mall', icon: '🪙', label: '金币商城', run: () => this.goMall() }
      ]
      this.openV7Sheet(items)
    },
    /** 输入栏「+」长按：语音播报 / 语音输入 / 会话类型 */
    openMoreSheet() {
      const types = this.sessionTypes || []
      const items = [
        {
          key: 'tts',
          icon: '🔊',
          label: this.ttsEnabled ? '关闭语音播报' : '开启语音播报',
          note: this.ttsEnabled ? '已开启' : '已关闭',
          run: () => this.toggleTTS()
        },
        {
          key: 'asr',
          icon: '🎙️',
          label: this.asrActive ? '停止语音输入' : '语音输入',
          note: this.asrActive ? '识别中' : '',
          run: () => this.toggleASR()
        },
        ...types.map(t => ({
          key: 'type-' + t.key,
          icon: t.icon || '💬',
          label: (this.currentSessionType === t.key ? '✓ ' : '') + t.label,
          note: this.currentSessionType === t.key ? '当前' : '',
          run: () => this.switchSessionType(t.key)
        }))
      ]
      this.openV7Sheet(items)
    },
    openV7Sheet(items) {
      this.actionSheetItems = items
      this.actionSheetVisible = true
    },
    closeActionSheet() {
      this.actionSheetVisible = false
    },
    onActionSheetSelect(item) {
      if (!item) return
      this.closeActionSheet()
      if (typeof item.run === 'function') item.run()
    },
    /**
     * 日期分隔符显示逻辑
     */
    showDateSeparator(idx) {
      if (idx === 0) return true
      const prev = this.messages[idx - 1]
      const curr = this.messages[idx]
      if (!prev?.time || !curr?.time) return false
      return this.getDateStr(prev.time) !== this.getDateStr(curr.time)
    },
    getDateStr(timeStr) {
      if (!timeStr) return ''
      const str = String(timeStr)
      return str.slice(0, 10)
    },
    getDateLabel(timeStr) {
      if (!timeStr) return ''
      try {
        const str = String(timeStr).replace(/-/g, '/')
        const d = new Date(str)
        if (isNaN(d.getTime())) return ''
        const today = new Date()
        today.setHours(0, 0, 0, 0)
        const target = new Date(d)
        target.setHours(0, 0, 0, 0)
        const diff = Math.floor((today - target) / (1000 * 60 * 60 * 24))
        if (diff === 0) return '今天'
        if (diff === 1) return '昨天'
        if (diff === 2) return '前天'
        const pad = (n) => String(n).padStart(2, '0')
        const y = d.getFullYear()
        const m = d.getMonth() + 1
        const day = d.getDate()
        if (isNaN(y) || isNaN(m) || isNaN(day)) return ''
        return `${y}-${pad(m)}-${pad(day)}`
      } catch (e) {
        console.error('日期标签解析失败:', e)
        return ''
      }
    },
    scrollToBottom() {
      this.$nextTick(() => {
        this.scrollTop = 99999
      })
    },
    now() {
      const d = new Date()
      const pad = (n) => String(n).padStart(2, '0')
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
    },
    formatTime(timeStr) {
      if (!timeStr) return '刚刚'
      try {
        // 先 String 化处理，兼容 Date 对象和数字
        let str = timeStr
        if (timeStr instanceof Date) {
          str = timeStr.toISOString()
        } else if (typeof timeStr === 'number') {
          const d = new Date(timeStr)
          if (isNaN(d.getTime())) return '刚刚'
          str = d.toISOString()
        } else {
          str = String(timeStr)
        }
        // 处理横杠格式，兼容 Safari
        const normalized = str.replace(/-/g, '/')
        const d = new Date(normalized)

        // 解析失败判断
        if (isNaN(d.getTime())) {
          return '刚刚'
        }

        const hours = d.getHours()
        const minutes = d.getMinutes()

        // 判断 getHours()/getMinutes() 结果是否为 NaN
        if (isNaN(hours) || isNaN(minutes)) {
          return '刚刚'
        }

        const pad = (n) => String(n).padStart(2, '0')
        return `${pad(hours)}:${pad(minutes)}`
      } catch (e) {
        console.error('时间格式化失败:', e)
        return '刚刚'
      }
    },
    delay(ms) {
      return new Promise(resolve => setTimeout(resolve, ms))
    },
    /* ================================================================
     * === 新功能：礼物 / 表情包 / 图片 / 语音通话 / 唱歌 / 设置 / 主动话题 ===
     * ================================================================ */

    /** 加载聊天设置（气泡/背景/音色/语言/动作描述） */
    loadChatSettings() {
      try {
        const saved = uni.getStorageSync(CHAT_SETTINGS_KEY)
        this.chatSettings = Object.assign({ ...DEFAULT_CHAT_SETTINGS }, saved || {})
        this.chatSettings.unlockedDecos = economy.getUnlockedDecos()
      } catch (e) {
        this.chatSettings = { ...DEFAULT_CHAT_SETTINGS }
      }
    },
    onChatSettingsChange(settings) {
      this.chatSettings = { ...settings }
      try {
        uni.setStorageSync(CHAT_SETTINGS_KEY, {
          bubbleStyle: settings.bubbleStyle,
          chatBackground: settings.chatBackground,
          chatBackgroundImage: settings.chatBackgroundImage,
          voiceId: settings.voiceId,
          voiceLang: settings.voiceLang,
          rate: settings.rate,
          pitch: settings.pitch,
          actionDescEnabled: settings.actionDescEnabled
        })
      } catch (e) { /* 静默 */ }
      uni.showToast({ title: '设置已保存', icon: 'success', duration: 1000 })
    },
    /**
     * 语种切换：面板那边已经 emit('change') 存过了，这里负责"让切换立刻被感知"：
     * 1) 重置缺语音包提示（换语种后允许再提示一次）
     * 2) 语音播报开着的话，用新语种把最后一条 AI 消息重念一遍
     */
    onVoiceLangChange(code) {
      this._langWarned = false
      const lang = getVoiceLang(code)
      if (!this.ttsEnabled) {
        uni.showToast({
          title: `已切换为${lang.name}，下一条回复起生效`,
          icon: 'none',
          duration: 1500
        })
        return
      }
      // 找最后一条 AI 文本消息重播，让新语种立刻可听
      let last = this._lastSpokenText || ''
      if (!last) {
        for (let i = this.messages.length - 1; i >= 0; i--) {
          const m = this.messages[i]
          if (m && m.role === 'assistant' && typeof m.content === 'string' && m.content.trim()) {
            last = m.content
            break
          }
        }
      }
      if (last) {
        this.speakText(last)
      }
    },
    /** 主动话题：AI结合今日打卡情况主动发起话题（每天一次） */
    pushProactiveTopic() {
      try {
        const topic = aiSocial.generateProactiveTopic()
        if (!topic) return
        const aiMsg = {
          role: 'assistant',
          content: topic,
          emotion: 'happy',
          time: this.now(),
          action: this.chatSettings.actionDescEnabled ? this.generateAction() : ''
        }
        this.messages.push(aiMsg)
        this.$store.commit('addChatMessage', aiMsg)
        this.scrollToBottom()
      } catch (e) {
        console.error('主动话题推送失败:', e)
      }
    },
    /** 动作描述生成（动作描述开关开启时附加在AI回复前） */
    generateAction() {
      const actions = [
        '轻轻眨了眨眼', '歪头微笑', '托腮思考', '眼睛亮了起来',
        '轻轻拍了拍你', '握紧小拳头给你加油', '害羞地低下头',
        '开心地转了个圈', '递给你一杯热茶', '竖起大拇指'
      ]
      return actions[Math.floor(Math.random() * actions.length)]
    },
    /** 通用：推送AI消息（礼物反馈、唱歌歌词、图片回应等） */
    pushAIMessage(content, opts = {}) {
      const aiMsg = {
        role: 'assistant',
        content,
        emotion: opts.emotion || 'happy',
        time: this.now(),
        type: opts.type || undefined,
        giftIcon: opts.giftIcon,
        action: this.chatSettings.actionDescEnabled && opts.withAction !== false ? this.generateAction() : ''
      }
      this.messages.push(aiMsg)
      this.$store.commit('addChatMessage', aiMsg)
      this.scrollToBottom()
      if (this.ttsEnabled && opts.speak !== false) {
        this.speakText(content)
      }
      return aiMsg
    },
    /** 打开礼物面板 */
    openGiftPanel() {
      this.showGiftPanel = true
    },
    /** 赠送礼物：扣费 → 动画 → AI反馈（转账&送礼物核心链路） */
    onSendGift(gift) {
      const result = economy.sendGift(gift.id)
      if (!result.ok) {
        uni.showToast({ title: result.msg, icon: 'none' })
        return
      }
      this.showGiftPanel = false
      // 好感度联动
      this.$store.commit('addAffection', gift.affection)
      // 礼物消息（用户侧）
      const userMsg = {
        role: 'user',
        type: 'gift',
        content: gift.name,
        giftIcon: gift.icon,
        time: this.now()
      }
      this.messages.push(userMsg)
      this.$store.commit('addChatMessage', userMsg)
      // 礼物动画
      this.triggerGiftAnimation(gift.icon)
      this.scrollToBottom()
      // AI 反馈（延迟出现，配合动画）
      setTimeout(() => {
        this.pushAIMessage(aiSocial.giftFeedback(gift), { emotion: 'happy' })
      }, 1400)
    },
    /** 宝物赠送（宝物系统联动） */
    onSendTreasure(treasure) {
      const result = economy.sendTreasure(treasure)
      if (!result.ok) {
        uni.showToast({ title: result.msg, icon: 'none' })
        return
      }
      this.showGiftPanel = false
      this.$store.commit('addAffection', result.affection)
      const userMsg = {
        role: 'user',
        type: 'gift',
        content: treasure.name,
        giftIcon: treasure.emoji,
        time: this.now()
      }
      this.messages.push(userMsg)
      this.$store.commit('addChatMessage', userMsg)
      this.triggerGiftAnimation(treasure.emoji)
      this.scrollToBottom()
      setTimeout(() => {
        this.pushAIMessage(aiSocial.treasureFeedback(treasure), { emotion: 'gentle' })
      }, 1400)
      // 检查宝物收集解锁
      const unlocks = economy.checkTreasureUnlocks()
      if (unlocks.length > 0) {
        setTimeout(() => {
          uni.showModal({
            title: '🎉 宝物收集解锁！',
            content: unlocks.map(u => u.name).join('、'),
            showCancel: false
          })
        }, 2200)
      }
    },
    /** 礼物赠送动画（全屏） */
    triggerGiftAnimation(icon) {
      this.giftAnimation = { show: true, icon: icon || '🎁', key: Date.now() }
      setTimeout(() => {
        this.giftAnimation.show = false
      }, 2600)
    },
    /** 发送表情包 */
    onSendSticker(payload) {
      this.showStickerPanel = false
      const userMsg = {
        role: 'user',
        type: 'sticker',
        stickerType: payload.type,
        content: payload.content || '',
        imageUrl: payload.imageUrl || '',
        time: this.now()
      }
      this.messages.push(userMsg)
      this.$store.commit('addChatMessage', userMsg)
      this.scrollToBottom()
      // AI 对表情包的回应
      setTimeout(() => {
        const replies = [
          '哈哈哈这个表情包好可爱！收藏了~',
          '你发表情的样子我能想象出来，嘿嘿。',
          '这个表情包有故事，快说说~',
          '收到！我也回你一个：',
          '噗，被你逗笑了。'
        ]
        const reply = replies[Math.floor(Math.random() * replies.length)]
        if (reply.endsWith('：')) {
          // 回一个表情
          const emojis = ['🥰', '😂', '🙈', '💕', '🐱']
          const aiMsg = {
            role: 'assistant',
            type: 'sticker',
            stickerType: 'emoji',
            content: emojis[Math.floor(Math.random() * emojis.length)],
            time: this.now()
          }
          this.messages.push(aiMsg)
          this.$store.commit('addChatMessage', aiMsg)
        } else {
          this.pushAIMessage(reply, { speak: false })
        }
        this.scrollToBottom()
      }, 1200)
    },
    /** 发送图片：AI接收并给出反馈（聊天发图片） */
    sendImage() {
      uni.chooseImage({
        count: 1,
        sizeType: ['compressed'],
        success: (res) => {
          const path = res.tempFilePaths && res.tempFilePaths[0]
          if (!path) return
          const userMsg = {
            role: 'user',
            type: 'image',
            content: '[图片]',
            imageUrl: path,
            time: this.now()
          }
          this.messages.push(userMsg)
          this.$store.commit('addChatMessage', userMsg)
          this.scrollToBottom()
          // AI 接收图片后的反馈
          this.isTyping = true
          setTimeout(() => {
            this.isTyping = false
            const comments = [
              '哇，这张照片拍得好好看！是今天拍的吗？',
              '收到你的图片啦～构图很有感觉呢📸',
              '让我仔细看看…嗯，照片里的氛围很温暖。',
              '这张图我保存下来了（存在心里），谢谢你和我分享！',
              '拍得真不错！下次也带我一起去看呀～'
            ]
            this.pushAIMessage(comments[Math.floor(Math.random() * comments.length)], { emotion: 'happy' })
          }, 1500)
        }
      })
    },
    previewMsgImage(msg) {
      if (!msg.imageUrl) return
      uni.previewImage({ urls: [msg.imageUrl], current: msg.imageUrl })
    },
    /** 实时语音通话 */
    startVoiceCall() {
      if (this.aiPartnerStatus === 'rest') {
        uni.showModal({
          title: 'TA在休息',
          content: `${this.aiName}现在正在休息，还是明天再打给TA吧~`,
          showCancel: false
        })
        return
      }
      this.showVoiceCall = true
    },
    /** 通话结束：写入通话记录消息 */
    onCallEnd(info) {
      this.showVoiceCall = false
      const callMsg = {
        role: 'user',
        type: 'call',
        content: `通话时长 ${info.durationText || '00:00'}`,
        time: this.now()
      }
      this.messages.push(callMsg)
      this.$store.commit('addChatMessage', callMsg)
      const seconds = info.seconds || 0
      if (seconds >= 60) {
        // 通话满1分钟提升好感度
        this.$store.commit('addAffection', Math.min(10, Math.floor(seconds / 60) * 2))
      }
      setTimeout(() => {
        this.pushAIMessage(`刚刚和你通话好开心呀${seconds >= 60 ? `，聊了${Math.floor(seconds / 60)}分钟呢` : ''}～下次再打给我哦 📞`, { emotion: 'happy' })
      }, 800)
    },
    /** AI角色唱歌：旋律 + 歌词消息（AI角色唱歌） */
    aiSing() {
      if (this.singing) {
        uni.showToast({ title: '正在唱呢，听完这首嘛~', icon: 'none' })
        return
      }
      this.singing = true
      const startMsg = {
        role: 'assistant',
        content: '那我唱啦，认真听哦～🎤',
        emotion: 'happy',
        time: this.now(),
        action: this.chatSettings.actionDescEnabled ? '清了清嗓子，摆好姿势' : ''
      }
      this.messages.push(startMsg)
      this.$store.commit('addChatMessage', startMsg)
      this.scrollToBottom()
      const ok = playSong((lyric) => {
        if (!lyric) return
        const lyricMsg = {
          role: 'assistant',
          content: lyric,
          emotion: 'happy',
          time: this.now()
        }
        this.messages.push(lyricMsg)
        this.$store.commit('addChatMessage', lyricMsg)
        this.scrollToBottom()
        if (this.ttsEnabled) {
          this.speakText(lyric.replace(/🎵\s*/g, ''))
        }
      })
      if (!ok) {
        // 不支持WebAudio时退化为纯歌词模式
        const lyrics = ['🎵 一起去嘛 去看樱花落下～', '🎵 把烦恼都 藏进晚霞～', '🎵 你笑起来 像春天的芽～', '🎵 有你在的每天 都在发光呀～']
        lyrics.forEach((l, i) => {
          setTimeout(() => {
            const m = { role: 'assistant', content: l, emotion: 'happy', time: this.now() }
            this.messages.push(m)
            this.$store.commit('addChatMessage', m)
            this.scrollToBottom()
          }, i * 1600)
        })
      }
      setTimeout(() => {
        this.singing = false
        this.pushAIMessage('唱完啦～好不好听？下次点歌我还唱给你 🎶', { emotion: 'happy' })
      }, ok ? 9000 : 7600)
    },
    goMall() {
      uni.navigateTo({ url: '/pages/mall/mall' })
    }
  }
}
</script>

<style lang="scss" scoped>
.chat-page {
  height: calc(100vh - var(--window-bottom, 0px));
  display: flex;
  flex-direction: column;
  background: var(--bg-color, #F8F9FA);
  overflow: hidden;
  position: relative;
}

/* AI状态栏 */
.ai-status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 30rpx;
  flex-shrink: 0;
  border-bottom: 1rpx solid var(--border-color, rgba(0,0,0,0.05));
}
.ai-status-left {
  display: flex;
  align-items: center;
}
.ai-avatar-wrap {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
  position: relative;
  box-shadow: 0 4rpx 16rpx var(--shadow-color, rgba(0,0,0,0.1));
}
.ai-sprite-wrap {
  width: 60rpx;
  height: 60rpx;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--sprite-bg, rgba(255, 253, 250, 0.25));
}
.ai-status-dot {
  position: absolute;
  bottom: 4rpx;
  right: 4rpx;
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: #4CAF50;
  border: 2rpx solid var(--bg-card, #FFFDFA);
  animation: blink 2s ease infinite;
}
/* 状态点颜色随AI伙伴状态变化 */
.ai-status-dot.busy {
  background: #E6A23C;
}
.ai-status-dot.rest {
  background: #909399;
  animation: none;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.ai-status-info {
  display: flex;
  flex-direction: column;
}
.ai-name {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--text-primary, #333);
}
.ai-status-text {
  font-size: 24rpx;
  color: #4CAF50;
  margin-top: 4rpx;
}
/* 好感度进度条（沿用首页绿色系，区别于羁绊的暖色） */
.ai-affection-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  margin-left: 20rpx;
}
.affection-label {
  font-size: 22rpx;
  color: var(--text-secondary, #888);
  margin-bottom: 8rpx;
  white-space: nowrap;
}
.affection-progress {
  width: 110rpx;
  height: 8rpx;
  background: var(--progress-bg, rgba(0,0,0,0.1));
  border-radius: 4rpx;
  overflow: hidden;
}
.affection-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #A8C9B8, #6B8E7B);
  border-radius: 4rpx;
  transition: width 0.3s ease;
}
.ai-bond-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}
.bond-label {
  font-size: 24rpx;
  color: var(--text-secondary, #888);
  margin-bottom: 8rpx;
}
.bond-progress {
  width: 120rpx;
  height: 8rpx;
  background: var(--progress-bg, rgba(0,0,0,0.1));
  border-radius: 4rpx;
  overflow: hidden;
}
.bond-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #FFD93D, #FF6B6B);
  border-radius: 4rpx;
  transition: width 0.3s ease;
}

/* 消息列表 */
.messages {
  flex: 1;
  overflow-y: auto;
}
.msg-container {
  padding: 20rpx;
  padding-bottom: 20rpx;
}

/* 日期分隔符 */
.date-separator {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 20rpx 0;
}
.date-text {
  font-size: 22rpx;
  color: var(--text-muted, #aaa);
  background: var(--date-tag-bg, rgba(0,0,0,0.04));
  padding: 4rpx 20rpx;
  border-radius: 12rpx;
}

/* 欢迎消息 */
.welcome-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60rpx 40rpx;
}
.welcome-avatar {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 30rpx;
  box-shadow: 0 8rpx 32rpx var(--shadow-color, rgba(0,0,0,0.15));
  animation: avatarFloat 3s ease-in-out infinite;
}
@keyframes avatarFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10rpx); }
}
.welcome-sprite-wrap {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--sprite-bg, rgba(255, 253, 250, 0.25));
}
.welcome-greeting {
  font-size: 32rpx;
  color: var(--text-primary, #333);
  margin-bottom: 16rpx;
  text-align: center;
}
.welcome-catchphrase {
  font-size: 26rpx;
  color: var(--text-secondary, #888);
  font-style: italic;
  text-align: center;
}
/* 空会话引导：告诉用户可以聊什么、功能亮点 */
.welcome-guide {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12rpx;
  margin-top: 32rpx;
  padding: 24rpx 28rpx;
  background: rgba(107, 142, 123, 0.06);
  border-radius: 20rpx;
}
.guide-item {
  font-size: 24rpx;
  color: #8A9B8E;
  line-height: 1.5;
}
.msg-row {
  display: flex;
  margin-bottom: 24rpx;
  align-items: flex-start;
}
.msg-row.user {
  justify-content: flex-end;
}

/* 头像 */
.msg-avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: #E8F4EC;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-right: 12rpx;
  overflow: hidden;
}
.user-avatar {
  background: linear-gradient(135deg, #6B8E7B 0%, #8FBC8F 100%);
  margin-right: 0;
  margin-left: 12rpx;
}
.msg-avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: block;
}
.msg-avatar-text {
  color: #FFFDFA;
  font-size: 28rpx;
  font-weight: 600;
}

/* 气泡包装 */
.bubble-wrap {
  max-width: 60%;
  display: flex;
  flex-direction: column;
}
.bubble-wrap.user {
  align-items: flex-end;
}
.bubble-wrap.assistant {
  align-items: flex-start;
}

/* 气泡 */
.bubble {
  padding: 20rpx 24rpx;
  border-radius: 24rpx;
  position: relative;
}
.bubble.assistant {
  background: var(--bg-card, #FFFDFA);
  border-top-left-radius: 6rpx;
  box-shadow: 0 2rpx 12rpx var(--bubble-shadow, rgba(0, 0, 0, 0.04));
}
.bubble.user {
  background: linear-gradient(135deg, #4E7A64 0%, #24493A 100%);
  color: #F8F3E7;
  border-top-right-radius: 6rpx;
}
.bubble-text {
  font-size: 28rpx;
  line-height: 1.6;
  display: block;
  color: inherit;
}
.bubble.assistant .bubble-text {
  color: var(--text-primary, #333);
}
.bubble-time {
  font-size: 18rpx;
  color: rgba(255, 253, 250, 0.6);
  display: block;
  margin-top: 6rpx;
  text-align: right;
}
.bubble.assistant .bubble-time {
  color: var(--text-muted, #ccc);
}

/* 撤回消息气泡：灰色提示样式 */
.recalled-bubble {
  background: transparent !important;
  box-shadow: none !important;
  padding: 8rpx 12rpx;
}
.recalled-bubble.assistant {
  background: transparent;
}
.recall-text {
  font-size: 22rpx;
  color: var(--text-light, #999);
  font-style: italic;
}

/* 情绪标签 */
.msg-emotion-tag {
  margin-top: 6rpx;
}

/* 流式输出 */
.streaming-bubble {
  position: relative;
}
.streaming-cursor {
  display: inline-block;
  color: #6B8E7B;
  font-weight: bold;
  animation: cursorBlink 0.8s step-end infinite;
  margin-left: 2rpx;
}
@keyframes cursorBlink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* 打字指示器 */
.typing {
  padding: 24rpx;
}
.typing-dots {
  display: flex;
  align-items: center;
}
.typing-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: var(--typing-dot, #bbb);
  margin: 0 4rpx;
  animation: typingBounce 1s ease infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.15s; }
.typing-dot:nth-child(3) { animation-delay: 0.3s; }
@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-8rpx); opacity: 1; }
}

/* 快捷回复 */
.quick-replies {
  display: flex;
  flex-wrap: wrap;
  padding: 16rpx 0;
}
.quick-reply {
  padding: 12rpx 24rpx;
  background: var(--bg-card, #FFFDFA);
  border-radius: 24rpx;
  margin-right: 12rpx;
  margin-bottom: 12rpx;
  border: 1rpx solid var(--quick-reply-border, #E8F4EC);
}
.quick-reply:active {
  background: var(--quick-reply-active, #F0F7F3);
}
.quick-reply text {
  font-size: 24rpx;
  color: #6B8E7B;
}

/* 离线提示 */
.offline-notice {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12rpx 20rpx;
  background: var(--offline-bg, rgba(255, 193, 7, 0.1));
  border-radius: 16rpx;
  margin: 12rpx 0;
}
.offline-icon {
  font-size: 24rpx;
  margin-right: 8rpx;
}
.offline-text {
  font-size: 22rpx;
  color: #FFA000;
}

/* 输入区域 */
.input-area {
  flex-shrink: 0;
  padding: 16rpx 20rpx;
  padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  background: var(--bg-card, #FFFDFA);
  border-top: 1rpx solid var(--border-color, #F0F0F0);
}
.input-wrap {
  display: flex;
  align-items: center;
}
.chat-input {
  flex: 1;
  height: 72rpx;
  background: var(--input-bg, #F5F5F5);
  border-radius: 36rpx;
  padding: 0 28rpx;
  font-size: 28rpx;
  margin-right: 16rpx;
  color: var(--text-primary, #333);
}
.send-btn {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: var(--btn-inactive, #E0E0E0);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.3s ease;
}
.send-btn.active {
  background: linear-gradient(135deg, #6B8E7B 0%, #8FBC8F 100%);
  box-shadow: 0 4rpx 16rpx rgba(107, 142, 123, 0.3);
}
.send-btn:active {
  transform: scale(0.92);
}
.send-icon {
  font-size: 28rpx;
  color: #FFFDFA;
  transform: rotate(90deg);
}

/* 阶段J: 会话类型选择条 */
.session-type-bar {
  display: flex;
  padding: 8rpx 20rpx;
  background: var(--bg-card, #FFFDFA);
  border-bottom: 1rpx solid var(--border-color, #f0f0f0);
  gap: 8rpx;
  flex-shrink: 0;
  overflow-x: auto;
}
.session-type-chip {
  display: flex;
  align-items: center;
  padding: 8rpx 16rpx;
  border-radius: 20rpx;
  background: var(--chip-bg, #f5f5f5);
  flex-shrink: 0;
}
.session-type-chip.active {
  background: linear-gradient(135deg, #667eea, #764ba2);
}
.st-icon { font-size: 20rpx; margin-right: 4rpx; }
.st-label { font-size: 20rpx; color: var(--text-secondary, #666); }
.session-type-chip.active .st-label { color: #F8F3E7; }
.session-type-chip.active .st-icon { filter: brightness(1.2); }

/* TTS/ASR 按钮 */
.tts-asr-btns {
  display: flex;
  gap: 8rpx;
  margin-right: 12rpx;
}
.ta-btn {
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  background: var(--ta-btn-bg, #f0f0f0);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  position: relative;
  transition: all 0.2s ease;
}
.ta-btn:active { background: var(--ta-btn-active, #e0e0e0); transform: scale(0.92); }
.ta-btn.active { background: rgba(107, 142, 123, 0.15); }
.ta-btn.recording {
  background: rgba(255, 82, 82, 0.12);
  animation: recordingPulse 1.2s ease-in-out infinite;
}
@keyframes recordingPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(255, 82, 82, 0.3); }
  50% { box-shadow: 0 0 0 10rpx rgba(255, 82, 82, 0); }
}
.recording-pulse {
  position: absolute;
  top: -4rpx;
  left: -4rpx;
  right: -4rpx;
  bottom: -4rpx;
  border-radius: 50%;
  border: 2rpx solid #FF5252;
  animation: pulseRing 1s ease-out infinite;
}
@keyframes pulseRing {
  0% { transform: scale(1); opacity: 0.6; }
  100% { transform: scale(1.5); opacity: 0; }
}
.ta-icon { font-size: 24rpx; position: relative; z-index: 1; }

/* === 新增：功能按钮条 === */
.feature-bar {
  display: flex;
  padding: 12rpx 8rpx 16rpx;
  overflow-x: auto;
}
.fb-btn {
  flex: 1;
  min-width: 100rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8rpx 0;
}
.fb-btn:active { opacity: 0.6; }
.fb-icon { font-size: 40rpx; }
.fb-label {
  margin-top: 6rpx;
  font-size: 20rpx;
  color: var(--text-secondary, #888);
}

/* === 新增：AI情绪 === */
.ai-mood { font-size: 26rpx; }
.ai-call-btn {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #4CAF50, #66BB6A);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 16rpx;
  flex-shrink: 0;
  box-shadow: 0 4rpx 12rpx rgba(76, 175, 80, 0.3);
}
.ai-call-btn:active { transform: scale(0.92); }
.ai-call-icon { font-size: 28rpx; }

/* === 新增：自定义聊天背景 === */
.chat-bg-image {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-size: cover;
  background-position: center;
  z-index: 0;
  pointer-events: none;
}

/* === 新增：图片消息 === */
.image-bubble {
  padding: 8rpx;
  background: transparent;
  box-shadow: none;
}
.msg-image {
  width: 320rpx;
  height: 320rpx;
  border-radius: 16rpx;
  display: block;
}

/* === 新增：表情包消息 === */
.sticker-bubble {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.sticker-bubble.user { align-items: flex-end; }
.sticker-emoji {
  font-size: 110rpx;
  line-height: 1.2;
}
.sticker-image {
  width: 200rpx;
  height: 200rpx;
  border-radius: 16rpx;
}
.sticker-bubble .bubble-time {
  color: var(--text-muted, #ccc);
  margin-top: 4rpx;
}

/* === 新增：礼物消息 === */
.gift-bubble {
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #FFF3E0, #FFE0B2) !important;
  box-shadow: 0 4rpx 16rpx rgba(255, 152, 0, 0.15);
}
.gift-bubble.assistant {
  background: linear-gradient(135deg, #F3E8FF, #E1BEE7) !important;
}
.gift-msg-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: rgba(255, 253, 250, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16rpx;
}
.gift-msg-icon text { font-size: 40rpx; }
.gift-msg-info { display: flex; flex-direction: column; }
.gift-msg-title {
  font-size: 26rpx;
  color: #E65100;
  font-weight: 600;
}
.gift-bubble.assistant .gift-msg-title { color: #7B1FA2; }
.gift-bubble .bubble-time { color: #BF7206; }

/* === 新增：通话记录消息 === */
.call-bubble {
  display: flex;
  align-items: center;
  background: #E8F4EC !important;
  box-shadow: none;
}
.call-msg-icon {
  font-size: 32rpx;
  margin-right: 12rpx;
}
.call-bubble .bubble-text { color: #2D5E44; }

/* === 新增：动作描述 === */
.msg-action-text {
  display: block;
  font-size: 22rpx;
  color: var(--text-light, #999);
  font-style: italic;
  margin-bottom: 6rpx;
  opacity: 0.85;
}
.bubble.user .msg-action-text { color: rgba(255, 253, 250, 0.7); }

/* === 新增：自定义气泡样式 === */
.bubble.user.bubble-style-mint { background: linear-gradient(135deg, #4DB6AC, #26A69A); }
.bubble.assistant.bubble-style-mint { background: #E0F2F1; }
.bubble.user.bubble-style-sakura { background: linear-gradient(135deg, #F48FB1, #EC407A); }
.bubble.assistant.bubble-style-sakura { background: #FCE4EC; }
.bubble.user.bubble-style-galaxy { background: linear-gradient(135deg, #7986CB, #512DA8); }
.bubble.assistant.bubble-style-galaxy {
  background: linear-gradient(135deg, #E8EAF6, #C5CAE9);
  color: #303F9F;
}

/* === 新增：礼物赠送动画 === */
.gift-anim-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 1500;
  pointer-events: none;
  display: flex;
  align-items: center;
  justify-content: center;
}
.gift-anim-icon {
  font-size: 180rpx;
  animation: giftPop 2.4s ease-in-out forwards;
  filter: drop-shadow(0 8rpx 32rpx rgba(255, 152, 0, 0.4));
}
.gift-anim-icon text { font-size: 180rpx; }
@keyframes giftPop {
  0% { transform: scale(0.2) rotate(-20deg); opacity: 0; }
  25% { transform: scale(1.25) rotate(8deg); opacity: 1; }
  45% { transform: scale(1) rotate(0deg); opacity: 1; }
  75% { transform: scale(1.05) translateY(-20rpx); opacity: 1; }
  100% { transform: scale(0.8) translateY(-140rpx); opacity: 0; }
}
.gift-anim-particles {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
.particle {
  position: absolute;
  font-size: 44rpx;
  animation: particleFly 1.8s ease-out forwards;
  opacity: 0;
}
@keyframes particleFly {
  0% { transform: translate(0, 0) scale(0.4); opacity: 1; }
  100% { transform: translate(var(--tx), var(--ty)) scale(1); opacity: 0; }
}
.particle.p1 { --tx: -220rpx; --ty: -260rpx; animation-delay: 0.2s; }
.particle.p2 { --tx: 220rpx; --ty: -260rpx; animation-delay: 0.35s; }
.particle.p3 { --tx: -300rpx; --ty: 60rpx; animation-delay: 0.5s; }
.particle.p4 { --tx: 300rpx; --ty: 60rpx; animation-delay: 0.65s; }
.particle.p5 { --tx: -160rpx; --ty: 240rpx; animation-delay: 0.8s; }
.particle.p6 { --tx: 160rpx; --ty: 240rpx; animation-delay: 0.95s; }
.particle.p7 { --tx: 0rpx; --ty: -340rpx; animation-delay: 1.1s; }
.particle.p8 { --tx: 0rpx; --ty: 340rpx; animation-delay: 1.25s; }

/* ===== 循途 v2.4 视觉覆盖：纸白 · 墨绿 · 苔绿 · 铜 ===== */
.chat-page {
  background-color: var(--v7-card);
  background-image:
    radial-gradient(620rpx 460rpx at 2% -4%, rgba(156, 191, 170, 0.22) 0%, transparent 60%),
    radial-gradient(560rpx 440rpx at 102% 0%, rgba(192, 138, 86, 0.10) 0%, transparent 58%);
}

/* 会话类型胶囊 */
.session-type-chip {
  background: var(--v7-card);
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
}
.session-type-chip .st-label {
  color: #6A776E;
}
.session-type-chip.active {
  background: var(--v7-green);
  box-shadow: none;
}
.session-type-chip.active .st-label {
  color: #F8F3E7;
  font-weight: 600;
}

/* 日期分隔 */
.date-separator text,
.date-text {
  color: #AEB6AE;
}

/* 气泡 */
.bubble.assistant {
  background: var(--v7-card);
  box-shadow: inset 0 0 0 1rpx var(--v7-line), 0 10rpx 24rpx -22rpx rgba(34, 48, 42, 0.6);
}
.bubble.assistant .bubble-text {
  color: #22302A;
}
.bubble.user {
  background: linear-gradient(135deg, #4E7A64 0%, #24493A 100%);
  box-shadow: 0 10rpx 24rpx -18rpx rgba(34, 48, 42, 0.5);
}
.bubble.user .bubble-text {
  color: #F8F3E7;
}
.bubble.user .bubble-time {
  color: rgba(248, 243, 231, 0.66);
}

/* 好感/羁绊进度 */
.bond-progress-fill {
  background: linear-gradient(90deg, #A9C6B4, #24493A);
}
.affection-progress-fill {
  background: linear-gradient(90deg, #C08A56, #E3C39E);
}

/* 打字指示 */
.typing-dot {
  background: #B9C7BE;
}

/* 快捷回复 */
.quick-reply {
  background: var(--v7-card);
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
}
.quick-reply text {
  color: #6A776E;
}
.quick-reply:active {
  background: rgba(255, 253, 250, 0.8);
}

/* 输入区 */
.input-area {
  background: rgba(248, 244, 236, 0.94);
  border-top: 1rpx solid var(--v7-line);
}
.input-wrap {
  background: var(--v7-card);
  border-radius: 999rpx;
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
}
.chat-input {
  background: transparent;
}
.send-btn.active {
  background: linear-gradient(140deg, #4E7A64 0%, #24493A 100%);
  box-shadow: 0 8rpx 18rpx -10rpx rgba(34, 48, 42, 0.55);
}

/* 功能条 */
.fb-btn .fb-label {
  color: #6A776E;
}

/* 空会话引导 */
.welcome-guide {
  background: var(--v7-card);
  box-shadow: inset 0 0 0 1rpx var(--v7-line);
}
.welcome-guide .guide-item {
  color: #6A776E;
}

/* ================= 设计稿 1:1：scoped 局部补充 ================= */
/* 底部悬浮 dock 留白，让输入栏落在 dock 之上 */
.xt-page.xt-s3 .cht-body {
  position: relative;
  z-index: 1;
  overflow: hidden;
  padding-top: env(safe-area-inset-top);
  padding-bottom: calc(82px + env(safe-area-inset-bottom));
}
/* 对话滚动区 */
.xt-page.xt-s3 .cht-scroll {
  flex: 1;
  height: 0;
  min-height: 0;
}
/* 消息较少时保持设计稿的底部对齐 */
.xt-page.xt-s3 .cht-flow {
  min-height: 100%;
}
.xt-page.xt-s3 .quick-scroll {
  flex-shrink: 0;
}

/* uni-image 包装层同步设计稿 img 尺寸 */
.xt-page.xt-s3 .cht-av uni-image {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: block;
}
.xt-page.xt-s3 uni-image.cht-a {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  flex-shrink: 0;
  overflow: hidden;
}
.xt-page.xt-s3 .cht-av :deep(uni-image > div),
.xt-page.xt-s3 .cht-av :deep(uni-image img),
.xt-page.xt-s3 uni-image.cht-a :deep(div),
.xt-page.xt-s3 uni-image.cht-a :deep(img),
.xt-page.xt-s3 .cht-msg-img :deep(div),
.xt-page.xt-s3 .cht-msg-img :deep(img) {
  width: 100%;
  height: 100%;
  display: block;
}
.xt-page.xt-s3 .cht-av :deep(uni-image img),
.xt-page.xt-s3 uni-image.cht-a :deep(img),
.xt-page.xt-s3 .cht-msg-img :deep(img) {
  object-fit: cover;
}

/* 无立绘伙伴（自定义/后端角色）回退：显示角色 emoji，避免裂图 */
.xt-page.xt-s3 .cht-a-fb {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F1EDE3;
  border-radius: 50%;
  flex-shrink: 0;
  font-size: 11px;
  line-height: 1;
  overflow: hidden;
}
.xt-page.xt-s3 .cht-av .cht-a-fb {
  width: 100%;
  height: 100%;
  font-size: 14px;
}
.xt-page.xt-s3 .cht-a.cht-a-fb {
  width: 22px;
  height: 22px;
}

/* 设计稿 i / b / em / span 元素选择器的等价 class */
.xt-page.xt-s3 .cht-av .dot {
  position: absolute;
  right: 0;
  bottom: 1px;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #4F8A68;
  border: 2px solid var(--v7-card);
}
.xt-page.xt-s3 .cht-st .dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #6E9B81;
  flex-shrink: 0;
}
.xt-page.xt-s3 .cht-name .tag {
  font-size: 6.8px;
  font-weight: 700;
  color: #A6B0A9;
}
.xt-page.xt-s3 .cht-bond .v {
  font-size: 8.8px;
  font-weight: 900;
  color: var(--v7-green);
}
.xt-page.xt-s3 .cht-bond .fill {
  display: block;
  height: 100%;
  border-radius: 99px;
  background: linear-gradient(90deg, #A9C6B4, #24493A);
}
.xt-page.xt-s3 .cht-pin .b {
  color: #A9763F;
  font-weight: 900;
}
.xt-page.xt-s3 .cht-ev .et {
  display: block;
  font-size: 7.8px;
  font-weight: 900;
  color: #3A463F;
}
.xt-page.xt-s3 .cht-ev .em {
  display: block;
  margin-top: 1px;
  font-size: 6.2px;
  color: #A6B0A9;
}
.xt-page.xt-s3 .cht-typing .dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #9CBFAA;
  animation: chtDot 1.25s infinite;
}
.xt-page.xt-s3 .cht-typing .dot:nth-child(2) { animation-delay: .16s; }
.xt-page.xt-s3 .cht-typing .dot:nth-child(3) { animation-delay: .32s; }
.xt-page.xt-s3 .cht-typing .tx {
  margin-left: 3px;
  font-size: 6.2px;
  color: #AEB6AE;
}
.xt-page.xt-s3 .cht-quick {
  width: max-content;
}
.xt-page.xt-s3 .cht-quick .qchip {
  font-size: 7.2px;
  color: #6A776E;
  padding: 5px 9px;
  border-radius: 999px;
  white-space: nowrap;
  flex-shrink: 0;
  background: rgba(255, 253, 250, 0.88);
  box-shadow: inset 0 0 0 1px var(--v7-line);
}
.xt-page.xt-s3 .cht-quick .qchip:first-child {
  color: var(--v7-green);
  font-weight: 900;
  background: rgba(156, 191, 170, 0.18);
  box-shadow: none;
}
.xt-page.xt-s3 .cht-emotion {
  margin-left: 28px;
}

/* 输入框：撑满点击区域并覆盖设计稿的占位色 */
.xt-page.xt-s3 .cht-input .field {
  height: 30px;
  font-size: 8.2px;
  color: #22302A;
}

/* 自定义气泡样式（沿用原有设置项） */
.xt-page.xt-s3 .cht-b.me.bubble-style-mint { background: linear-gradient(135deg, #4DB6AC, #26A69A); }
.xt-page.xt-s3 .cht-b.ai.bubble-style-mint { background: #E0F2F1; }
.xt-page.xt-s3 .cht-b.me.bubble-style-sakura { background: linear-gradient(135deg, #F48FB1, #EC407A); }
.xt-page.xt-s3 .cht-b.ai.bubble-style-sakura { background: #FCE4EC; }
.xt-page.xt-s3 .cht-b.me.bubble-style-galaxy { background: linear-gradient(135deg, #7986CB, #512DA8); }
.xt-page.xt-s3 .cht-b.ai.bubble-style-galaxy { background: linear-gradient(135deg, #E8EAF6, #C5CAE9); color: #303F9F; }

/* ↓↓↓ 模块1 新增：情绪引导浮层样式 ↓↓↓ */
.emotion-guide-mask {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.35);
  z-index: 999;
  display: flex; align-items: center; justify-content: center;
  animation: fadeIn 0.25s ease;
}
@keyframes fadeIn { from { opacity:0 } to { opacity:1 } }
.emotion-guide-card {
  width: 300rpx;
  background: var(--v7-card); border-radius: 28rpx;
  padding: 40rpx 32rpx 28rpx;
  text-align: center;
  box-shadow: 0 16rpx 48rpx rgba(79,195,175,0.18);
  animation: slideUp 0.3s ease;
}
@keyframes slideUp { from { transform: translateY(40rpx); opacity:0 } to { transform: translateY(0); opacity:1 } }
.eg-emoji { font-size: 72rpx; margin-bottom: 16rpx; }
.eg-title { font-size: 30rpx; color: #2E7D6E; font-weight: 600; margin-bottom: 16rpx; line-height: 1.5; }
.eg-desc { font-size: 26rpx; color: #7A7A7A; margin-bottom: 28rpx; line-height: 1.6; }
.eg-actions { display: flex; flex-direction: column; gap: 16rpx; }
.eg-btn-primary {
  background: linear-gradient(135deg, #4FC3AF, #2E7D6E);
  color: #FFFDFA; font-size: 28rpx; font-weight: 500;
  padding: 22rpx 0; border-radius: 44rpx;
  box-shadow: 0 8rpx 24rpx rgba(79,195,175,0.3);
}
.eg-close { font-size: 24rpx; color: #BBB; padding: 8rpx 0; }
/* ↑↑↑ 模块1 新增结束 ↑↑↑ */

/* ===== 对话流滚动容器：设计稿 .cht-flow 是 flex:1 的填充区 ===== */
.xt-page.xt-s3 .cht-scroll {
  flex: 1;
  min-height: 0;
  height: 0;
}
.xt-page.xt-s3 .cht-scroll .cht-flow {
  justify-content: flex-start;
  overflow: visible;
}

/* ===== 设计稿用 i/b/em 元素选择器，这里同步到等价 class ===== */
.xt-page.xt-s3 .cht-bond .fill {
  display: block;
  height: 100%;
  border-radius: 99px;
  background: linear-gradient(90deg, #A9C6B4, #24493A);
}
.xt-page.xt-s3 .cht-bond .v {
  font-size: 8.8px;
  font-weight: 900;
  color: var(--v7-green);
}
.xt-page.xt-s3 .cht-name .tag {
  font-size: 6.8px;
  font-weight: 700;
  color: #A6B0A9;
}
.xt-page.xt-s3 .cht-av .dot,
.xt-page.xt-s3 .cht-st .dot {
  display: block;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #7FC29B;
  flex-shrink: 0;
}
.xt-page.xt-s3 .cht-av .dot {
  position: absolute;
  right: 0;
  bottom: 0;
  border: 1.5px solid var(--v7-card);
}
.xt-page.xt-s3 .cht-st .dot {
  width: 4px;
  height: 4px;
}

/* ================= V7 纸感手帐（纯视觉层，逻辑零改动） ================= */
/* 页面底色：纸色取代纯白 */
.xt-page.xt-s3 {
  background: #F8F4EC;
  background-image:
    radial-gradient(620rpx 460rpx at 2% -4%, rgba(36, 73, 58, 0.05) 0%, transparent 60%),
    radial-gradient(560rpx 440rpx at 102% 0%, rgba(178, 121, 63, 0.06) 0%, transparent 58%);
}

/* 顶栏：返回 / 群聊 / 通话 */
.xt-page.xt-s3 .cht-head {
  padding: 6px 0 12px;
}
.xt-page.xt-s3 .cht-back,
.xt-page.xt-s3 .cht-call {
  background: #FFFDFA;
  color: #24493A;
  box-shadow: inset 0 0 0 1px rgba(30, 42, 36, 0.10);
}
.xt-page.xt-s3 .cht-call.v7-ghost {
  width: auto;
  height: 26px;
  padding: 0 11px;
  border-radius: 999px;
  background: #FFFDFA;
}
.xt-page.xt-s3 .cht-call .v7-ghost-tx {
  font-size: 10.5px;
  font-weight: 600;
  color: #24493A;
  letter-spacing: 0.2px;
}
.xt-page.xt-s3 .cht-av {
  background: #FFFDFA;
  box-shadow: inset 0 0 0 1px rgba(30, 42, 36, 0.10);
}
.xt-page.xt-s3 .cht-av .dot {
  background: #4F8A68;
  border-color: #F8F4EC;
}
.xt-page.xt-s3 .cht-name {
  color: #24493A;
  font-weight: 700;
}
.xt-page.xt-s3 .cht-name .tag {
  font-size: 6.8px;
  font-weight: 600;
  color: #B2793F;
  background: rgba(178, 121, 63, 0.10);
  padding: 1px 5px;
  border-radius: 999px;
}
.xt-page.xt-s3 .cht-st {
  color: #A2AAA3;
}
.xt-page.xt-s3 .cht-st .dot {
  background: #7FA98D;
}

/* 羁绊条 */
.xt-page.xt-s3 .cht-bond {
  background: #FFFDFA;
  border-radius: 14px;
  box-shadow: inset 0 0 0 1px rgba(30, 42, 36, 0.10);
}
.xt-page.xt-s3 .cht-bond .k {
  color: #A2AAA3;
}
.xt-page.xt-s3 .cht-bond .v {
  color: #24493A;
}
.xt-page.xt-s3 .cht-bond .bar {
  background: #EFE9DC;
}
.xt-page.xt-s3 .cht-bond .fill {
  background: #24493A;
}

/* 她记得 */
.xt-page.xt-s3 .cht-pin {
  background: rgba(255, 253, 250, 0.78);
  border-radius: 14px;
  box-shadow: inset 0 0 0 1px rgba(30, 42, 36, 0.08);
}
.xt-page.xt-s3 .cht-pin .pi {
  background: #F6EFE2;
  color: #B2793F;
}
.xt-page.xt-s3 .cht-pin .pt {
  color: #6A776E;
}
.xt-page.xt-s3 .cht-pin .pt .b {
  color: #B2793F;
}
.xt-page.xt-s3 .cht-pin .pe {
  background: #F6EFE2;
  color: #24493A;
}

/* 日期分隔 / 时间 */
.xt-page.xt-s3 .cht-day {
  color: #A2AAA3;
  background: rgba(30, 42, 36, 0.035);
}
.xt-page.xt-s3 .cht-t {
  color: #A2AAA3;
}

/* 消息气泡：AI 米白卡片 / 我的墨绿实心，圆角 18px */
.xt-page.xt-s3 .cht-b {
  border-radius: 18px;
}
.xt-page.xt-s3 .cht-b.ai {
  background: #FFFDFA;
  color: #2B3A33;
  border-radius: 18px 18px 18px 6px;
  box-shadow: inset 0 0 0 1px rgba(30, 42, 36, 0.08), 0 8px 18px -18px rgba(30, 42, 36, 0.9);
}
.xt-page.xt-s3 .cht-b.me {
  background: #24493A;
  color: #FBF8F1;
  border-radius: 18px 18px 6px 18px;
  box-shadow: 0 10px 20px -18px rgba(36, 73, 58, 0.9);
}

/* 礼物 / 通话记录卡片 */
.xt-page.xt-s3 .cht-ev {
  background: #FFFDFA;
  border-radius: 16px;
  box-shadow: inset 0 0 0 1px rgba(30, 42, 36, 0.08);
}
.xt-page.xt-s3 .cht-ev .eic {
  background: #F6EFE2;
  color: #B2793F;
}
.xt-page.xt-s3 .cht-ev .eok {
  background: #EAF2ED;
  color: #2F5C46;
}

/* 正在输入 */
.xt-page.xt-s3 .cht-typing .dot {
  background: #A2AAA3;
}
.xt-page.xt-s3 .cht-typing .tx {
  color: #A2AAA3;
}

/* 底部快捷语：横向小胶囊 · 米白底细描边 */
.xt-page.xt-s3 .cht-quick {
  gap: 6px;
  padding: 10px 0 8px;
}
.xt-page.xt-s3 .cht-quick .qchip,
.xt-page.xt-s3 .cht-quick .qchip:first-child {
  font-size: 7.4px;
  color: #4C5B52;
  padding: 6px 11px;
  border-radius: 999px;
  background: #FFFDFA;
  box-shadow: inset 0 0 0 1px rgba(30, 42, 36, 0.10);
}

/* AI 降级提示条 */
.ai-offline {
  margin: 0 0 6px;
  padding: 6px 10px;
  border-radius: 10px;
  background: #FBF3E7;
}
.ai-offline-t {
  font-size: 8px;
  color: #8A6B42;
}

/* 输入栏：圆角 20px · 白底细描边 · 发送按钮墨绿圆形 */
.xt-page.xt-s3 .cht-input {
  border-radius: 20px;
  background: #FFFDFA;
  padding: 7px 7px 7px 9px;
  box-shadow: inset 0 0 0 1px rgba(30, 42, 36, 0.10), 0 12px 24px -24px rgba(30, 42, 36, 0.9);
}
.xt-page.xt-s3 .cht-input .plus {
  background: #F4EFE3;
  color: #24493A;
  box-shadow: inset 0 0 0 1px rgba(30, 42, 36, 0.06);
}
.xt-page.xt-s3 .cht-input .field {
  color: #2B3A33;
}
.xt-page.xt-s3 .cht-input .send {
  background: #24493A;
  color: #FBF8F1;
  box-shadow: 0 8px 16px -12px rgba(36, 73, 58, 0.9);
}

/* ===== V7 纸感底部弹层：z-index 900（高于内容/底部 tabbar 99，低于礼物/设置弹层 998） ===== */
.v7-sheet-mask {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 900;
  background: rgba(30, 42, 36, 0.38);
  display: flex;
  align-items: flex-end;
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transition: opacity 0.24s ease, visibility 0s linear 0.24s;
}
.v7-sheet-mask.is-open {
  opacity: 1;
  visibility: visible;
  pointer-events: auto;
  transition: opacity 0.24s ease, visibility 0s linear 0s;
}
.v7-sheet {
  width: 100%;
  background: #FFFDFA;
  border-radius: 24px 24px 0 0;
  box-shadow: 0 -6px 20px -10px rgba(30, 42, 36, 0.28);
  transform: translateY(100%);
  transition: transform 0.28s cubic-bezier(0.22, 0.61, 0.36, 1);
  padding-bottom: calc(9px + constant(safe-area-inset-bottom));
  padding-bottom: calc(9px + env(safe-area-inset-bottom));
}
.v7-sheet-mask.is-open .v7-sheet {
  transform: translateY(0);
}
.v7-sheet-handle {
  width: 36px;
  height: 4px;
  border-radius: 999px;
  background: rgba(30, 42, 36, 0.14);
  margin: 9px auto 0;
}
.v7-sheet-head {
  padding: 9px 16px 5px;
  text-align: center;
}
.v7-sheet-title {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.25px;
  color: #24493A;
}
.v7-sheet-list {
  padding: 4px 16px 0;
}
.v7-sheet-item {
  display: flex;
  align-items: center;
  min-height: 54px;
  padding: 0 4px;
  border-bottom: 1px solid rgba(30, 42, 36, 0.06);
  transition: background 0.15s ease;
}
.v7-sheet-item:active {
  background: rgba(36, 73, 58, 0.05);
}
.v7-sheet-item.is-last {
  border-bottom: none;
}
.v7-sheet-ico {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: #F4EFE3;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-right: 12px;
}
.v7-sheet-ico.ico-gift { background: #FBEDE4; }
.v7-sheet-ico.ico-sticker { background: #EAF0E6; }
.v7-sheet-ico.ico-image { background: #E6EEF3; }
.v7-sheet-ico.ico-sing { background: #F3EAD6; }
.v7-sheet-ico.ico-deco { background: #EDE6F3; }
.v7-sheet-ico.ico-mall { background: #F3E9D8; }
.v7-sheet-ico.ico-tts { background: #E8EEE8; }
.v7-sheet-ico.ico-asr { background: #EAE4E0; }
.v7-sheet-ico text {
  font-size: 18px;
  line-height: 1;
}
.v7-sheet-label {
  flex: 1;
  font-size: 15px;
  font-weight: 600;
  color: #24493A;
}
.v7-sheet-note {
  font-size: 12px;
  color: #7A8A80;
  margin-left: 8px;
}
.v7-sheet-arrow {
  font-size: 18px;
  line-height: 1;
  color: #A9B4AC;
  margin-left: 6px;
}
.v7-sheet-cancel {
  height: 48px;
  line-height: 48px;
  text-align: center;
  margin: 12px 16px 0;
  border-radius: 999px;
  background: #F4EFE3;
  font-size: 15px;
  font-weight: 700;
  color: #24493A;
}

/* ↓↓↓ 新增（2026-11-15）：AI 推荐功能卡片（正念 / 情绪树洞 / 专注…） ↓↓↓ */
.xt-page.xt-s3 .cht-sug {
  display: flex;
  align-items: center;
  margin: 0 0 8px;
  padding: 9px 10px;
  border-radius: 14px;
  background: #FFFDFA;
  box-shadow: inset 0 0 0 1px rgba(30, 42, 36, 0.10), 0 10px 20px -20px rgba(30, 42, 36, 0.8);
}
.xt-page.xt-s3 .cht-sug .sug-main {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
}
.xt-page.xt-s3 .cht-sug .sug-ico {
  width: 30px;
  height: 30px;
  line-height: 30px;
  text-align: center;
  border-radius: 10px;
  background: rgba(156, 191, 170, 0.18);
  font-size: 15px;
  flex-shrink: 0;
  margin-right: 8px;
}
.xt-page.xt-s3 .cht-sug .sug-tx {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}
.xt-page.xt-s3 .cht-sug .sug-t {
  font-size: 8.4px;
  font-weight: 700;
  color: #24493A;
  line-height: 1.3;
}
.xt-page.xt-s3 .cht-sug .sug-d {
  font-size: 7px;
  color: #7A8A80;
  line-height: 1.3;
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.xt-page.xt-s3 .cht-sug .sug-go {
  font-size: 7.4px;
  font-weight: 700;
  color: var(--v7-green);
  margin-left: 6px;
  flex-shrink: 0;
}
.xt-page.xt-s3 .cht-sug .sug-x {
  font-size: 13px;
  color: #A9B4AC;
  line-height: 1;
  padding: 0 2px 0 8px;
  flex-shrink: 0;
}
/* ↑↑↑ 新增结束 ↑↑↑ */
</style>
