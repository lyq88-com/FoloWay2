import http from '@/common/request'

/**
 * 【四大新增模块·模块3】互动扭蛋机接口封装
 * 路径前缀: /gacha
 * 分类: companion=陪伴打卡向 / emotion=情绪倾诉向 / chat=趣味闲聊向
 * tab: recommend=推荐 / hot=最热 / favorite=收藏 / mine=我创建的
 */
export default {
  // 我的扭蛋币钱包(首次自动创建并送欢迎币)
  getWallet() {
    return http.get('/gacha/wallet')
  },

  // 剧本列表
  getList(tab = 'recommend', category = '') {
    return http.get('/gacha/list', { tab, category })
  },

  // 收藏/取消收藏
  toggleFavorite(templateId) {
    return http.post(`/gacha/favorite/${templateId}`)
  },

  // 创建自定义剧本 { title, description, category, opening_text, questions:[{question,options,hint}] }
  create(data) {
    return http.post('/gacha/create', data)
  },

  // 执行抽取(消耗10扭蛋币) { category } 空=全分类随机
  draw(category = '') {
    return http.post('/gacha/draw', { category })
  },

  // 剧本问答 { record_id, question_index, answer }
  answer(recordId, questionIndex, answer) {
    return http.post('/gacha/answer', {
      record_id: recordId,
      question_index: questionIndex,
      answer
    })
  },

  // 我的抽取记录
  getRecords() {
    return http.get('/gacha/records')
  }
}
