# 循途 · 本次改动完整清单报告

> 项目：循途（AI习惯伙伴）· uni-app Vue3 + Vuex（状态管理）
> 范围：注册页改造 / 学霸模式彻底删除 / 对标循途交互优化 / 全局BUG修复 / H5编译验证
> 编译状态：`npm run build:h5` → **DONE Build complete**（零报错；仅剩3条 uni 官方插件内部 sass 弃用提示，非项目代码问题）

---

## ① 注册页配色改动（pages/login/login.vue）

严格对齐首页配色体系，**只改颜色不动布局**：

| 元素 | 原样式 | 新样式（首页同源色） |
|---|---|---|
| 页面背景 | 默认灰白 | `linear-gradient(160deg, #F8FBF9 0%, #EFF6F2 40%, #F0F7F3 100%)` |
| 应用名 | 通用黑 | `#2D4A3E`（首页标题深墨绿） |
| Slogan | 灰色 | `#8A9B8E`（首页灰绿辅助色） |
| Logo 渐变 | — | `linear-gradient(135deg, #6B8E7B, #8FBC8F)` + 主色投影 |
| 输入框 | 无描边 | 白底 + `border: 2rpx solid rgba(107,142,123,0.15)` 主色描边 |
| 输入文字 | 默认黑 | `#2D4A3E` |
| 占位符 | 系统灰 | 新增 `.input-placeholder { color: #B7C4BC }` 淡灰绿 |
| 登录按钮 | — | 主色渐变 `#6B8E7B → #8FBC8F` |
| 注册按钮 | — | `#6B8E7B` 描边空心按钮 |
| 分割线 | 灰色 | `rgba(107,142,123,0.18)` 主色分割线 |
| 协议勾选框 | 灰描边 | `#A8C9B8` 描边 / 选中 `#6B8E7B` |
| 背景装饰圆 | — | `#6B8E7B / #8FBC8F / #A8C9B8` 低透明度 |

## ② 删除的学霸模式全部代码清单

| 文件/目录 | 删除内容 |
|---|---|
| `pages.json` | `pages/study-room/study-room` 页面注册项 |
| `pages/study-room/` | 整个目录（页面文件） |
| `components/study-room-panel/` | 整个目录（学霸模式面板组件） |
| `components/quick-menu/` | 整个目录（快捷菜单独立组件） |
| `pages/habit/habit.vue` | 「自习室」菜单入口 + 红色图标样式 `.grid-icon-wrap.red`、「学霸模式」操作项、`<study-room-panel>` 标签、`import studyRoomPanel`、components 注册、data 中 `studyMode` / `showStudyRoomPanel`、methods 中 `showStudyRoom()` / `toggleStudyMode()` |
| `pages/fragment/fragment.vue` | tips 文案「在自习舱完成专注可获得随机碎片」 |
| `pages/postcard.vue` | `studyHistory` 读取与 `weekMinutes` 累加死代码 |

全局 grep 复验：`study-room / studyMode / 学霸 / 自习` 关键词在源码中零残留（ai-dialogue-engine.js 中「温柔学霸」为AI人格类型名称，与该功能无关）。

## ③ 对标循途的交互优化（只借鉴逻辑，UI/配色沿用循途）

### 3.1 AI伙伴异步陪伴（pages/chat/chat.vue）
- **AI伙伴状态机**：`aiPartnerStatus` 计算属性 → 在线 / 忙碌（14-16点）/ 休息（23-7点）；状态点颜色随状态变化（绿/橙/灰），状态栏文案同步（「忙碌中·回复会慢一点」「休息中·轻声陪伴」）
- **异步延迟回复**：`getReplyDelay()` —— 在线 300-700ms / 忙碌 1.2-2.2s / 休息 2-3.5s，不再一律"秒回"
- **打字加载动画**：已有 typing-dots 指示器保留并接入状态机（忙碌时文案变化）
- **消息撤回模拟**：AI回复后 8% 概率触发 `scheduleRecall()`——2.5s 后该消息变为「林夕撤回了一条消息」灰色提示，再 2s 后补发重新组织的内容（`recallChatMessage` mutation 持久化）
- **空会话引导**：欢迎区新增引导卡（可聊什么 / 打卡后AI会主动找你 / 消息本地保存）；快捷回复在空会话也展示作为话题起点
- **历史消息持久化**：Vuex `chatMessages`（200条上限）+ `uni.setStorageSync`，日期分隔符、滚动到底均已处理
- **情绪识别联动**：发送前用 `mock.chatEmotionAnalysis` 分析用户消息，将情绪注入流式请求 `emotion` 参数，影响AI回复语气
- **打卡后主动推送**：habit.vue 打卡成功写入 `pending_proactive_message` 本地缓存 → chat.vue `onShow` 时 `pushPendingProactiveMessage()` 消费，AI伙伴"主动"发来鼓励

### 3.2 宝物 ↔ 好感度关系系统（对标循途礼物系统）
- **store/index.js**：新增 `affection: { value: 0 }`（0-500 封顶）+ `addAffection` / `setAffection` mutation + `affectionValue / affectionTier / affectionTierName / affectionProgress` getter（初识→熟悉→伙伴→挚友→知己 五阶段）；`initFromStorage` 兼容旧缓存
- **宝物使用加好感**：`pages/box/box.vue` 与 `pages/box-warehouse/box-warehouse.vue` 的 `useReward()` 统一 `addAffection(+5)` 并 toast「好感度 +5」
- **好感度影响语气**：`common/ai-dialogue-engine.js` —— `buildContext` 注入 `affection/affectionTier`；新增 `applyAffectionTone()` 在 `generateReply` 两条路径（自然语言/fallback）末尾按阶段追加亲昵语气（35%概率、避免重复修饰），低好感保持礼貌克制
- **进度条展示**：chat.vue 状态栏「好感·阶段 + 进度条」（绿色系 `#A8C9B8→#6B8E7B`，区别于羁绊暖色）；profile.vue 新增好感度卡片（阶段名 + 数值 + 进度条 + 说明文案）

### 3.3 习惯打卡优化（pages/habit/habit.vue）
- **创建表单**：新增「打卡周期」选择（每天/隔天/每周3次，`frequency` 字段随表单提交）；提醒时间 picker、打卡目标输入保留
- **连续天数计算**：`handleCheckin` 优先采用服务端返回 `res.streak`（`typeof === 'number'` 严格判断，修复原 `res.streak || 本地+1` 在 streak=0 时错误回退的BUG）；取消打卡本地回退一格
- **打卡 ↔ 好感度联动**：打卡成功 `addAffection(+2)`，取消打卡 `addAffection(-1)`（下限0）
- **打卡 → AI主动互动**：成功后写入待推送消息（含习惯名与连续天数），对话页打开即由AI伙伴主动发出

### 3.4 数据存储与隐私（common/backup.js 新增）
- 消息/打卡/好感度等全量状态由 Vuex 统一持久化本地（H5 localStorage 优先）
- 新增备份工具：`exportBackupData()`（全量JSON导出）/ `importBackupData()`（版本校验恢复）/ `uploadBackupData()`（**云端备份逻辑预留**，后端就绪后替换 TODO 即可）

## ④ 修复的BUG列表

| # | BUG | 位置 | 修复 |
|---|---|---|---|
| 1 | H5编译失败 `ENOENT: src/manifest.json`（uni CLI 默认输入目录为 src/，本项目为根目录布局） | `scripts/uni-cli.js`（新增）+ `package.json` | CLI 包装脚本显式设置 `UNI_INPUT_DIR/UNI_OUTPUT_DIR`，所有 npm scripts 改走包装脚本 |
| 2 | 根目录 vite.config.js 缺失（被移至 _cli_backup） | `vite.config.js` | 恢复并配置 `css.preprocessorOptions.scss.api='modern'`，sass 弃用警告 8→3 条 |
| 3 | 注册缺少确认密码/手机号校验 | login.vue | 新增注册模式（确认密码输入框 + 手机号 `^1[3-9]\d{9}$` 校验 + 密码强度「字母+数字」+ 两次一致校验 + 注册成功自动退出注册模式） |
| 4 | `resetState` 遗漏字段：walkMap / affection / aiConfig / settings / aiStatus 未重置，切换账号数据残留 | store/index.js | 全部补齐重置 |
| 5 | `deleteHabit` 方法重复定义两次（静默覆盖 + 死代码） | habit.vue | 删除简单版，保留含详情联动与二次确认的完整版 |
| 6 | 快捷菜单「设置」假入口，toast「开发中」 | habit.vue `showSettings()` | 改为跳转 `/pages/settings/settings` 真实页面 |
| 7 | 本地通知点击跳转无效路由 `/pages/habits/habits`（404） | settings.vue | 修正为 `/pages/habit/habit` |
| 8 | 离线消息恢复时 `forEach` 并发 `doSend`，多个流式回复互相覆盖 | chat.vue `checkOfflineMessages()` | 改为 `for...of` 串行 await |
| 9 | 打卡 streak=0 时 `res.streak \|\| habit.streak+1` 错误回退 | habit.vue | 严格 `typeof res.streak === 'number'` 判断 |
| 10 | 自定义习惯保存无防重复提交 | habit.vue `submitCustomHabit()` | 新增 `submitting` 状态锁 + finally 释放 |
| 11 | chat.vue 5个未使用 import（generateWalkStatus/getDailyQuote/analyzeEmotion/getSystemPrompt/getCharacterProfile） | chat.vue | 清理 |
| 12 | 登录/注册/微信登录/游客登录重复点击 | login.vue | 四个入口全部 `if (this.isLoading) return` + disabled |
| 13 | 旧缓存无 affection 字段导致 undefined | store/index.js `initFromStorage` | 字段兜底初始化 |

## ⑤ 修改的全部文件

**新增（4）**
- `frontend/scripts/uni-cli.js` — uni CLI 跨平台包装（修复编译）
- `frontend/vite.config.js` — 恢复根配置 + modern sass API
- `frontend/common/backup.js` — 本地/云端备份工具
- `frontend/scripts/check-routes.js` — 路由校验工具脚本

**修改（10）**
- `frontend/package.json` — npm scripts 走包装脚本
- `frontend/pages.json` — 删除 study-room 注册（前次会话）
- `frontend/pages/login/login.vue` — 注册模式 + 完整校验 + 配色
- `frontend/pages/chat/chat.vue` — AI状态机/异步延迟/撤回模拟/空会话引导/好感度条/主动推送/串行离线重发/import清理
- `frontend/pages/habit/habit.vue` — 周期表单/好感度联动/主动消息/防重复提交/删重复方法/真实设置入口
- `frontend/pages/box/box.vue` — 宝物使用 + 好感度
- `frontend/pages/box-warehouse/box-warehouse.vue` — 宝物使用 + 好感度
- `frontend/pages/profile/profile.vue` — 好感度卡片
- `frontend/pages/settings/settings.vue` — 修复无效路由
- `frontend/store/index.js` — 好感度系统/消息撤回mutation/resetState修复
- `frontend/common/ai-dialogue-engine.js` — 好感度上下文注入 + 语气调节

**删除（前次会话完成，本次复验零残留）**
- `frontend/pages/study-room/`、`frontend/components/study-room-panel/`、`frontend/components/quick-menu/`

---

## 测试验证步骤（H5 完整流程）

```bash
cd frontend
npm run build:h5        # 已验证：DONE Build complete
npm run dev:h5          # 已验证：http://localhost:8080 HTTP 200
```

1. **注册流程**：登录页点「注册新账号」→ 出现确认密码框 → 输入 11 位错误手机号格式（如 12345）失焦 → 提示「手机号格式不正确」→ 输入纯字母密码 → 提示「密码需同时包含字母和数字」→ 两次密码不一致 → 提示「两次输入的密码不一致」→ 正确填写 → 「确认注册」→ 成功后自动回到登录态（密码已清空）
2. **登录**：账号密码登录 → 1500ms 后跳转（未测评先进 personality-quiz）
3. **创建习惯**：习惯页 + → 自定义习惯 → 选周期（每天/隔天/每周3次）→ 设提醒时间与目标 → 确认保存 → 列表出现新习惯
4. **打卡**：点打卡 → AI鼓励弹窗出现（含连续天数）→ 取消打卡再打 → streak 变化正常
5. **AI对话主动推送**：完成一次打卡 → 切到「AI对话」tab → AI伙伴**主动**发出一条「刚刚看到你完成了…连续第N天啦」消息
6. **AI状态与异步回复**：14:00-16:00 之间进入对话页 → 状态显示「忙碌中·回复会慢一点」、状态点橙色 → 发消息 → 回复延迟明显（约1-2秒后才出现打字动画）；23:00 后显示「休息中」
7. **好感度联动**：首页/对话页确认好感度进度条 → 去开盲盒 → 使用宝物 → toast「好感度 +5」→ 回到对话页好感度条前进 → 多次使用后（好感≥100）AI回复开始带「~」「呀~」等亲昵语气
8. **消息撤回模拟**：连续与AI对话多轮 → 偶见「林夕撤回了一条消息」灰字 → 2秒后AI补发重新组织的内容（8%概率，可多试几轮）
9. **空会话引导**：清除聊天记录后进入对话页 → 显示欢迎语 + 三条引导说明 + 快捷话题chips
10. **本地持久化**：刷新页面/重开浏览器 → 聊天记录、打卡状态、好感度全部保留（localStorage）
11. **个人中心**：我的页显示「与 林夕 的好感度」卡片（阶段/数值/进度条）
12. **控制台**：F12 无 Vue 警告、无未捕获异常（全局错误兜底已装）

---

*报告生成时间：2026-09-06 · 循途前端改造完成*
