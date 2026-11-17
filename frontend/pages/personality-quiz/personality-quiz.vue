<template>
  <view class="xt-page xt-s18">
    <view class="body">
      <!-- 开始页 -->
      <view v-if="currentStep === 'start'">
        <view class="quiz-top">
          <view class="back" @click="skipQuiz"><xt-icon name="i-left" /></view>
          <view class="quiz-prog"><view class="prog-fill" style="width:0"></view></view>
          <text class="quiz-count">可跳过</text>
        </view>

        <view class="ai-rec" style="margin-top:0">
          <view class="sp"><xt-icon name="i-brain" /></view>
          <view class="tx">
            <text class="k">循途 · 自我了解</text>
            <text class="p">选更像你的那个就好，结果只用来匹配更适合你的伙伴。</text>
          </view>
        </view>

        <view class="quiz-q" style="margin-top:18px">性格测评</view>
        <view class="quiz-hint">{{ questions.length }} 道题 · 约 2 分钟 · 可跳过</view>

        <view class="mem-hero" style="margin-top:14px">
          <view class="t">先花两分钟，认识一下此刻的你</view>
          <view class="m">共 {{ questions.length }} 道题，没有标准答案，随时可以跳过。</view>
        </view>

        <view class="auth-btn" style="margin-top:16px" @click="startQuiz">开始测评</view>
        <view class="auth-alt" @click="skipQuiz">跳过测评，先去逛逛</view>
      </view>

      <!-- 答题页 -->
      <view v-else-if="currentStep === 'quiz'">
        <view class="quiz-top">
          <view class="back" @click="prevQuestion"><xt-icon name="i-left" /></view>
          <view class="quiz-prog">
            <view class="prog-fill" :style="{ width: progressPercent + '%' }"></view>
          </view>
          <text class="quiz-count">{{ currentIndex + 1 }} / {{ questions.length }}</text>
        </view>

        <view class="quiz-q">{{ currentQuestion.text || currentQuestion.question }}</view>
        <view class="quiz-hint">选更像你的那个，不用想太久</view>

        <view
          v-for="(option, idx) in currentQuestion.options"
          :key="idx"
          class="opt"
          :class="{ on: selectedAnswer === idx }"
          @click="selectOption(idx)"
        >
          <view class="os"><xt-icon :name="optionIcons[idx] || 'i-spark'" /></view>
          <text class="ot">{{ option.text }}</text>
        </view>

        <view class="focus-btns" style="margin-top:16px">
          <view class="fbtn ghost" :class="{ disabled: currentIndex === 0 }" @click="prevQuestion">上一题</view>
          <view class="fbtn main" :class="{ disabled: selectedAnswer === null }" @click="nextQuestion">
            {{ currentIndex === questions.length - 1 ? '查看结果' : '下一题' }}
          </view>
        </view>

        <view class="quiz-hint" style="margin-top:12px;text-align:center">没有标准答案 · 结果只用来匹配更适合你的伙伴</view>
        <view class="auth-alt" @click="skipQuiz">跳过测评</view>
      </view>

      <!-- 结果页 -->
      <view v-else-if="currentStep === 'result'">
        <view class="quiz-top">
          <view class="back" @click="restartQuiz"><xt-icon name="i-left" /></view>
          <view class="quiz-prog"><view class="prog-fill" style="width:100%"></view></view>
          <text class="quiz-count">已完成</text>
        </view>

        <view class="quiz-q">测评完成！</view>
        <view class="quiz-hint">这是现在的你 · 结果只保存在本地</view>

        <view class="field" v-for="(desc, key) in descriptions" :key="key">
          <view class="lab">{{ getLabel(key) }}</view>
          <view class="val" style="line-height:1.6">{{ desc }}</view>
        </view>

        <view class="role-hero" v-if="resultPartner" style="margin-top:12px">
          <view class="match-avatar" :style="resultAvatarStyle">
            <image
              v-if="resultPartnerPhoto"
              class="match-avatar-img"
              :src="resultPartnerPhoto"
              mode="aspectFill"
            />
            <text v-else>{{ resultPartner.avatar }}</text>
          </view>
          <view class="tx">
            <view class="p" style="font-weight:800;color:#8A5D33">{{ resultPartnerLabel }}</view>
            <h3>{{ resultPartner.name }}</h3>
            <view class="p">{{ resultPartner.description }}</view>
            <view class="p" style="color:var(--v7-green)">{{ resultPartner.catchphrase }}</view>
          </view>
        </view>

        <view
          v-if="selectedPartner && recommendedCharacter && recommendedCharacter.id !== selectedPartner.id"
          class="quiz-hint"
          style="margin-top:10px"
        >
          测评还为你匹配到 {{ recommendedCharacter.name }}，之后可在角色页随时切换
        </view>

        <view class="focus-btns" style="margin-top:16px">
          <view class="fbtn ghost" @click="restartQuiz">重新测评</view>
          <view class="fbtn main" @click="confirmResult">
            确认选择 {{ resultPartner ? resultPartner.name : 'AI伙伴' }}
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { QUESTIONS, calculateResult, getResultDescription, saveQuizResultAsync } from '@/common/personality-quiz'
import { getRecommendedCharacter, CHARACTERS } from '@/common/ai-characters'
import { findPartner, getPickedPartnerId, saveActivePartner, getPartnerPhoto, DEFAULT_PARTNER_ID } from '@/common/ai-partner'
import XtIcon from '@/components/xt-icon/xt-icon.vue'

export default {
  components: { XtIcon },
  data() {
    return {
      currentStep: 'start',
      currentIndex: 0,
      answers: [],
      selectedAnswer: null,
      questions: QUESTIONS,
      result: null,
      descriptions: {},
      recommendedCharacter: null,
      // 用户已选中的伙伴（路由参数 / 本地记录），测评结束不能被推荐结果覆盖
      selectedPartnerId: '',
      selectedPartner: null
    }
  },
  computed: {
    currentQuestion() {
      return this.questions[this.currentIndex]
    },
    progressPercent() {
      return ((this.currentIndex + 1) / this.questions.length) * 100
    },
    // 结果页展示的伙伴：优先用户已选中的，其次才是测评推荐
    resultPartner() {
      return this.selectedPartner || this.recommendedCharacter || null
    },
    resultPartnerPhoto() {
      return this.resultPartner ? getPartnerPhoto(this.resultPartner) : ''
    },
    resultPartnerLabel() {
      return this.selectedPartner ? '你选中的伙伴' : '最适合此刻的你'
    },
    resultAvatarStyle() {
      const c = (this.resultPartner && this.resultPartner.colors) || {}
      return {
        background: `linear-gradient(135deg, ${c.primary || '#7BA08B'}, ${c.accent || '#A5D6A7'})`
      }
    },
    // 设计稿每个选项带一个线性图标（题目选项维度是 5 级量表，按序号取图标）
    optionIcons() {
      return ['i-moon', 'i-chat', 'i-spark', 'i-world', 'i-heart']
    }
  },
  onLoad(options) {
    console.log('Personality Quiz Page Loaded')
    console.log('Questions count:', this.questions.length)
    console.log('Characters count:', CHARACTERS.length)

    // 兼容多种入口参数：roleId / characterId / partnerId / roleKey
    const routeId = options && (options.roleId || options.characterId || options.partnerId || options.roleKey)
    const pickedId = getPickedPartnerId()
    this.selectedPartner = findPartner(routeId) || findPartner(pickedId)
    this.selectedPartnerId = this.selectedPartner ? this.selectedPartner.id : ''
    console.log('Selected partner:', this.selectedPartnerId || '(none)')
  },
  methods: {
    startQuiz() {
      console.log('Starting quiz...')
      this.currentStep = 'quiz'
      this.currentIndex = 0
      this.answers = new Array(this.questions.length).fill(null)
      this.selectedAnswer = null
    },
    // 跳过测评：不写完成标记，下次登录仍会提示；直接进入陪伴页
    skipQuiz() {
      uni.reLaunch({
        url: '/pages/index/index',
        fail: () => {
          uni.navigateBack({ delta: 1 })
        }
      })
    },
    selectOption(index) {
      this.selectedAnswer = index
      this.answers[this.currentIndex] = this.currentQuestion.options[index]
      console.log('Selected option:', index, this.answers[this.currentIndex])
    },
    prevQuestion() {
      if (this.currentIndex > 0) {
        this.currentIndex--
        this.selectedAnswer = this.answers[this.currentIndex] ? this.currentQuestion.options.indexOf(this.answers[this.currentIndex]) : null
      }
    },
    nextQuestion() {
      if (this.selectedAnswer === null) {
        uni.showToast({ title: '请先选择一个选项', icon: 'none' })
        return
      }
      
      if (this.currentIndex < this.questions.length - 1) {
        this.currentIndex++
        this.selectedAnswer = this.answers[this.currentIndex] ? this.currentQuestion.options.indexOf(this.answers[this.currentIndex]) : null
      } else {
        this.showResult()
      }
    },
    showResult() {
      try {
        console.log('Calculating result...')
        this.result = calculateResult(this.answers)
        console.log('Result:', this.result)
        
        this.descriptions = getResultDescription(this.result)
        console.log('Descriptions:', this.descriptions)
        
        this.recommendedCharacter = getRecommendedCharacter(this.result) || findPartner(DEFAULT_PARTNER_ID)
        console.log('Recommended character:', this.recommendedCharacter)
        
        if (!this.recommendedCharacter) {
          console.warn('No character found, using default')
          this.recommendedCharacter = CHARACTERS[0] || {
            id: 'linxi',
            name: '林夕',
            avatar: '🌿',
            description: '温柔治愈的AI伙伴',
            catchphrase: '慢慢来，一切都会好起来的~',
            colors: {
              primary: '#7BA08B',
              secondary: '#C8E6C9',
              accent: '#A5D6A7',
              light: '#F1F8E9',
              dark: '#3E5D4A'
            }
          }
        }
        
        this.currentStep = 'result'
        console.log('Current step changed to:', this.currentStep)
      } catch (e) {
        console.error('Error showing result:', e)
        uni.showToast({ title: '计算结果失败', icon: 'none' })
      }
    },
    getLabel(key) {
      const labels = {
        personality: '性格特质',
        emotionalResilience: '情绪耐受度',
        procrastination: '自律拖延',
        companionStyle: '陪伴风格'
      }
      return labels[key] || key
    },
    async confirmResult() {
      try {
        const partner = this.resultPartner
        console.log('confirmResult called, partner:', partner && partner.id)
        
        if (!partner) {
          uni.showToast({ title: '未找到合适的伙伴', icon: 'none' })
          return
        }
        
        // quiz 完成标记按登录用户名存键（旧会话回退昵称/default）
        const quizKeyUser = this.$store.state.username
          || (this.$store.state.userInfo && this.$store.state.userInfo.nickname)
          || 'default'
        // ↓↓↓ 改为 await 版：本地即时写 + 等云端落库后再跳转 ↓↓↓
        try {
          const ok = await saveQuizResultAsync(this.result, quizKeyUser)
          console.log('Quiz result saved', ok ? '(含云端)' : '(仅本地)')
        } catch (e) {
          console.warn('保存测评结果异常(继续走本地):', e && e.message)
        }
        // ↑↑↑ 改造结束 ↑↑↑
        
        this.$store.commit('setPersonalityResult', this.result)
        this.$store.commit('setQuizCompleted', true)
        // 关键修复：保存用户已选中的伙伴；只有从未选过时才采用测评推荐
        // （原来无条件写入推荐角色，导致测评结束伙伴被固定成同一个）
        const saved = saveActivePartner(partner.id, partner.name)
        if (!saved) {
          uni.showToast({ title: '伙伴数据异常，请重试', icon: 'none' })
          return
        }
        console.log('Store updated, active partner:', partner.id)
        
        uni.showToast({ 
          title: `已选好${partner.name}`, 
          icon: 'success',
          duration: 2000
        })
        
        setTimeout(() => {
          console.log('Navigating to companion...')
          uni.reLaunch({
            url: '/pages/index/index',
            success: () => {
              console.log('Navigation success')
            },
            fail: (err) => {
              console.error('Navigation failed:', err)
              uni.navigateBack({ delta: 1 })
            }
          })
        }, 2000)
      } catch (e) {
        console.error('Error in confirmResult:', e)
        uni.showToast({ title: '保存失败: ' + e.message, icon: 'none' })
      }
    },
    restartQuiz() {
      this.currentStep = 'start'
      this.currentIndex = 0
      this.answers = []
      this.selectedAnswer = null
      this.result = null
      this.descriptions = {}
      this.recommendedCharacter = null
      // 保留 selectedPartner：重测不应丢失用户已经选中的伙伴
    }
  }
}
</script>

<style lang="scss" scoped>
/* 底部呼吸空间 */
.xt-page.xt-s18 .body {
  padding-bottom: calc(24px + env(safe-area-inset-bottom));
}

/* 设计稿进度填充为 .quiz-prog i，改用 class 承载 */
.xt-page.xt-s18 .quiz-prog .prog-fill {
  display: block;
  height: 100%;
  border-radius: 99px;
  background: linear-gradient(90deg, #9CBFAA, var(--v7-green));
  transition: width 0.4s ease;
}

/* 上一题/下一题禁用态 */
.xt-page.xt-s18 .fbtn.disabled {
  opacity: 0.45;
  pointer-events: none;
}

/* 设计稿 match 头像为 img，这里用 emoji 兜底，补等价尺寸 */
.xt-page.xt-s18 .match-avatar {
  width: 72px;
  height: 96px;
  border-radius: 18px;
  border: 3px solid #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 34px;
  flex-shrink: 0;
  overflow: hidden;
  box-shadow: 0 10px 22px -12px rgba(62, 93, 74, 0.5);
}

/* 结果页使用 3:4 完整立绘，无立绘时才回退 emoji */
.xt-page.xt-s18 .match-avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 18px;
  display: block;
}
.xt-page.xt-s18 .match-avatar :deep(uni-image > div),
.xt-page.xt-s18 .match-avatar :deep(uni-image img) {
  width: 100%;
  height: 100%;
  display: block;
  border-radius: 18px;
}
.xt-page.xt-s18 .match-avatar :deep(uni-image img) {
  object-fit: cover;
}
</style>
