# AI 聊天「答非所问 / 强行引导倾诉」修复方案

> 项目：独响 APP（AI 陪伴式习惯养成）
> 日期：2026-09-21
> 范围：增量修复，未改动原有数据库结构与页面结构

---

## 〇、先纠正一个前提

**本项目后端不是 SpringBoot，而是 Python：**

| 目录 | 技术栈 | 端口 | 职责 |
|---|---|---|---|
| `liyeqing/server/` | **FastAPI** | 8000 | 业务后端（含 AI 对话主链路 `/api/v1/chat/send`） |
| `liyeqing/server-flask/` | **Flask** | 5000 / 5001 | 5000 鉴权；5001 AI 聊天 `ai_server.py` |
| `liyeqing/frontend/` | uni-app (Vue3) | 8080 | 前端 |

全仓库检索 `pom.xml` / `build.gradle` / `*.java` **均为 0 个结果**。
因此下文同时给出 **Java 伪代码**（满足文档/课程报告需要）与 **Python 实际落地实现**。

---

## 一、根因核实：你列的 3 条，只有 1 条成立

先说最重要的结论：**你看到的"固定共情倾听话术"，主因不在大模型的 system prompt，而在前端的「本地降级引擎」。**

### 真实因果链

```
后端 AI 不可用（8000 未启动 / SSE 返回 500 / AI_MODEL=mock）
        ↓
chat.vue:753  chatApi.streamSend() 抛出异常
        ↓
chat.vue:774  catch → this.generateLocalReply(content, characterId)
        ↓
common/ai-dialogue-engine.js:1681  generateReply()  ← 2315 行纯本地模板引擎
        ↓
输出「固定共情话术」
```

**铁证 1** —— `common/ai-cloud-service.js:542`（写死的模板，压根不看用户问了什么）：

```js
neutral: `嗯，我在听${streak > 0 ? '，作为已经打卡' + streak + '天的你一定很自律' : '，你想聊点什么？'}`
```

**铁证 2** —— `common/ai-dialogue-engine.js:1675`（关键词没命中就落到通用共情兜底）：

```js
const empathy = strategy.empathy[emotion.type] || strategy.empathy.neutral || ['我在听']
return getRandomItem(empathy)
```

它的关键词表里写的是 `'吃了吗': '还没呢，你呢喵~'`，
而用户输入是 **"吃饭了吗"** —— 不包含连续子串 `"吃了吗"` → **不命中任何关键词** → 落到 `empathy.neutral`
→ 输出「我在听」这类话术。**它完全不理解语义，所以必然答非所问。**

### 逐条核对

| 你列的根因 | 核实结果 | 说明 |
|---|---|---|
| ① system prompt 陪伴倾听权重过高，未区分日常闲聊/情绪倾诉 | ✅ **成立（次要因素）** | `ROLE_PROMPTS` + `DIALOGUE_STYLES['gentle']`（"多用安慰和鼓励的话语"）+ 旧能力清单第 1 条"倾听用户的情绪倾诉"。但实测证明：**干净的 messages 下它并不会严重跑偏**，所以它是"帮凶"不是"主犯"。已修。 |
| ② 无条件把打卡摘要注入 system prompt | ❌ **不成立（当时根本没这功能）** | `chat.py` 调用 `build_system_prompt()` 时**没有传** `context_summary`，前端 `api/chat.js` 也只传 6 个字段。现在按你的需求**新增**了条件注入。 |
| ③ messages 顺序：用户最新消息没放末尾 | ⚠️ **实际是「重复」而非「顺序错」** | 顺序原本就对（末尾追加）。但 `db.add(user_msg)` 后未 flush，SQLAlchemy 的 **autoflush 会把它写库并在历史查询中被查出来**，随后 `build_context_messages` 又在末尾追加一次 → **同一条用户消息被发送两次**。已修。 |

### 另外发现 3 个此前未提及的真实缺陷

| # | 缺陷 | 位置 | 影响 |
|---|---|---|---|
| D1 | `role_type` 映射错位：`/chat/personas` 返回 `companion/mentor/friend`，但 `ROLE_PROMPTS` 只有 `cute/gentle/serious/energetic` | `ai_service.py` | 前端传 `companion` → 静默回退到 `cute`，角色与预期不符 |
| D2 | 情绪无条件注入：`if user_emotion:` 对 `"neutral"` 也成立 | `build_system_prompt` | 对"吃饭了吗"这类闲聊注入 `用户当前情绪状态：neutral`，把模型往情绪方向带 |
| D3 | 情绪标签是英文（`sad`/`tired`）直接拼进中文 prompt | 同上 | `EMOTION_LABELS` 中文映射表存在但**从未被使用** |

---

## 二、① 修改后的完整 system prompt 文本

### 2.1 场景判定规则（新增核心段落，位置必须紧跟角色设定）

```
【最高优先级：先回答用户最新这句话，再考虑陪伴】
陪伴不等于把所有话题都引向情绪。用户问什么，就先回答什么。

【三种场景，必须先判断当前属于哪一种，再决定怎么回】
场景A｜用户在提出具体问题（"吃饭了吗""这个怎么做""推荐一下""明天几点"等）
  → 直接、正面、简洁地回答，给出实质内容。
  → 禁止答非所问；禁止把普通提问当成情绪信号；禁止反问"你是不是有心事"。

场景B｜日常闲聊、打招呼、碎碎念、吐槽小事、分享日常
  → 用口语自然接话，可以顺着话题聊下去或自然反问一句推进对话。
  → 保持松弛，不需要每句话都深挖内心感受。

场景C｜用户明确表达负面情绪、烦恼、压力、痛苦，或主动求助
  → 这时才切换到共情倾听：先认可感受，不急着给建议；用户主动问了才给想法。

【硬性约束】
1. 禁止把"吃饭了吗""在干嘛""睡了吗"这类日常问候当成倾诉信号，
   回"你愿意跟我说说吗""发生什么了""你想聊点什么"。
2. 禁止在用户没有表达负面情绪时，主动追问内心、感受、心事。
3. 禁止答非所问：问什么答什么，答完可以自然延伸一句，但不能跑题。
4. 禁止空洞鸡汤与模板化鼓励（"加油""一切都会好起来""我一直在这里陪着你"）。
```

### 2.2 拼接后的完整 prompt（场景A：日常提问，无习惯注入）

```
你叫林夕，是一个温柔陪伴、愿意倾听的AI伙伴。你的对话风格温柔体贴，像亲密好友一样轻声细语，多用安慰和鼓励的话语。

【最高优先级：先回答用户最新这句话，再考虑陪伴】
陪伴不等于把所有话题都引向情绪。用户问什么，就先回答什么。

【三种场景，必须先判断当前属于哪一种，再决定怎么回】
场景A｜用户在提出具体问题（"吃饭了吗""这个怎么做""推荐一下""明天几点"等）
  → 直接、正面、简洁地回答，给出实质内容。
  → 禁止答非所问；禁止把普通提问当成情绪信号；禁止反问"你是不是有心事"。

场景B｜日常闲聊、打招呼、碎碎念、吐槽小事、分享日常
  → 用口语自然接话，可以顺着话题聊下去或自然反问一句推进对话。
  → 保持松弛，不需要每句话都深挖内心感受。

场景C｜用户明确表达负面情绪、烦恼、压力、痛苦，或主动求助
  → 这时才切换到共情倾听：先认可感受，不急着给建议；用户主动问了才给想法。

【硬性约束】
1. 禁止把"吃饭了吗""在干嘛""睡了吗"这类日常问候当成倾诉信号，
   回"你愿意跟我说说吗""发生什么了""你想聊点什么"。
2. 禁止在用户没有表达负面情绪时，主动追问内心、感受、心事。
3. 禁止答非所问：问什么答什么，答完可以自然延伸一句，但不能跑题。
4. 禁止空洞鸡汤与模板化鼓励（"加油""一切都会好起来""我一直在这里陪着你"）。

你是用户的习惯养成助手与聊天伙伴。你还可以：
1. 记住之前的对话内容，保持上下文连贯
2. 在用户情绪低落时安慰，在开心时一起庆祝
3. 提供实用建议但避免说教

回复要求：简短自然(50-150字)，口语化，有亲和力，避免冗长。使用中文回复。
```

### 2.3 场景C 追加的两段（条件注入）

```
【用户当前情绪】难过（据此调整语气，但不要直接点破）

【用户近期习惯数据】仅因当前话题相关才提供，请自然引用，不要生硬罗列：
- 当前连续打卡 3 天
- 正在培养的习惯：早睡(连续3天)、跑步
- 最近打卡：09-20 跑步完成；09-19 早睡完成
```

> 关键改动：删除了旧版"1. 倾听用户的情绪倾诉，给予温暖的回应"、
> "2. 根据用户情绪状态调整回复方式"两条**无条件**指令，改为**场景判定后条件触发**。

---

## 三、② 判断是否注入打卡摘要（Java 伪代码）

### 3.1 核心判定逻辑

```java
package com.duxiang.ai.service;

import java.util.*;

/**
 * 习惯记忆锚点注入器
 * 目的：只有用户话题与「习惯/打卡/拖延」相关时，才把打卡摘要拼进 system prompt；
 *      普通闲聊一律不注入，避免无关信息干扰模型理解用户最新消息。
 */
public class HabitContextInjector {

    /** 话题关键词表：命中任一即认为与习惯相关 */
    private static final List<String> HABIT_TOPIC_KEYWORDS = Arrays.asList(
        "打卡", "习惯", "坚持", "连续", "自律", "目标", "计划", "任务", "进度",
        "拖延", "摆烂", "偷懒", "放弃", "中断", "没做", "又没", "起不来",
        "早睡", "早起", "熬夜", "晚睡", "运动", "跑步", "健身", "读书", "阅读",
        "喝水", "冥想", "背单词", "学习", "复习", "写作", "复盘",
        "坚持不下去", "做不到", "三天打鱼", "明天开始"
    );

    /**
     * 判定：是否需要注入打卡摘要
     * @param userInput 用户最新一条消息
     * @return true  = 话题相关，注入打卡摘要
     *         false = 普通闲聊，不注入
     */
    public static boolean shouldInjectHabitContext(String userInput) {
        if (userInput == null || userInput.trim().isEmpty()) {
            return false;
        }
        String text = userInput.trim();
        for (String keyword : HABIT_TOPIC_KEYWORDS) {
            if (text.contains(keyword)) {
                return true;      // 命中任一关键词即注入
            }
        }
        return false;             // 默认不注入
    }

    /**
     * 构建 system prompt（含两处条件注入）
     */
    public static String buildSystemPrompt(String roleType,
                                           String dialogueStyle,
                                           String userEmotion,
                                           String habitSummary) {
        StringBuilder sb = new StringBuilder();

        // 1) 角色设定 + 对话风格
        sb.append(RolePrompts.get(roleType))
          .append(DialogueStyles.get(dialogueStyle))
          .append("\n\n");

        // 2) 场景判定规则（解决答非所问的核心段落，位置必须靠前）
        sb.append(SCENE_RULES).append("\n\n");

        // 3) 能力说明 + 回复要求
        sb.append("你是用户的习惯养成助手与聊天伙伴。你还可以：\n")
          .append("1. 记住之前的对话内容，保持上下文连贯\n")
          .append("2. 在用户情绪低落时安慰，在开心时一起庆祝\n")
          .append("3. 提供实用建议但避免说教\n\n")
          .append("回复要求：简短自然(50-150字)，口语化，有亲和力，避免冗长。使用中文回复。\n");

        // 4) 条件注入 A：情绪 —— neutral / normal 一律不注入
        if (userEmotion != null
                && !userEmotion.isEmpty()
                && !"neutral".equals(userEmotion)
                && !"normal".equals(userEmotion)) {
            String label = EMOTION_LABELS_CN.getOrDefault(userEmotion, userEmotion);
            sb.append("\n【用户当前情绪】").append(label)
              .append("（据此调整语气，但不要直接点破）\n");
        }

        // 5) 条件注入 B：习惯摘要 —— 调用方已用 shouldInjectHabitContext 判定过
        if (habitSummary != null && !habitSummary.isEmpty()) {
            sb.append("\n【用户近期习惯数据】仅因当前话题相关才提供，")
              .append("请自然引用，不要生硬罗列：\n")
              .append(habitSummary).append("\n");
        }

        return sb.toString();
    }

    /** 情绪英文标签 → 中文 */
    private static final Map<String, String> EMOTION_LABELS_CN = new HashMap<String, String>() {{
        put("happy",   "开心");
        put("excited", "兴奋");
        put("calm",    "平静");
        put("sad",     "难过");
        put("angry",   "生气");
        put("tired",   "疲惫");
    }};
}
```

### 3.2 在业务层的调用（含"排除当前消息"的正确查询）

```java
@PostMapping("/chat/send")
public SseEmitter sendMessage(@RequestBody ChatSendRequest req) {

    // ---- 1. 先落库用户消息，并拿到自增 id ----
    ChatMessage userMsg = new ChatMessage();
    userMsg.setSessionId(sessionId);
    userMsg.setRole("user");
    userMsg.setContent(req.getContent());
    chatMessageMapper.insert(userMsg);          // 插入后 userMsg.getId() 有值

    // ---- 2. 查历史上下文：★ 必须排除刚插入的当前这条 ----
    // ❌ 错误写法：List<ChatMessage> history = chatMessageMapper.selectBySessionId(sessionId);
    //    会导致当前消息同时出现在 history 和 messages 末尾，被重复发给大模型
    // ✅ 正确写法：
    List<ChatMessage> history =
        chatMessageMapper.selectBySessionIdExcludeId(sessionId, userMsg.getId());

    // ---- 3. 情绪分析 ----
    String emotion = emotionService.analyzeEmotion(req.getContent());  // 可能为 "neutral"

    // ---- 4. 习惯记忆锚点：先判定话题，再决定是否查库拼摘要 ----
    String habitSummary = "";
    if (HabitContextInjector.shouldInjectHabitContext(req.getContent())) {
        habitSummary = habitSummaryService.build(userId);   // 只有相关时才查库
    }

    // ---- 5. 构建 system prompt ----
    String systemPrompt = HabitContextInjector.buildSystemPrompt(
        req.getRoleType(), req.getDialogueStyle(), emotion, habitSummary);

    // ---- 6. 构造 messages（顺序硬约束，见第四节）----
    List<Map<String, String>> messages =
        MessageBuilder.build(systemPrompt, history, req.getContent());

    // ---- 7. 调用智谱 glm-4-flash（流式）----
    return zhipuClient.chatStream(messages);
}
```

### 3.3 Python 实际落地实现（本项目真实代码）

```python
# server/app/services/ai_service.py
HABIT_TOPIC_KEYWORDS = [
    "打卡", "习惯", "坚持", "连续", "自律", "目标", "计划", "任务", "进度",
    "拖延", "摆烂", "偷懒", "放弃", "中断", "没做", "又没", "起不来",
    "早睡", "早起", "熬夜", "晚睡", "运动", "跑步", "健身", "读书", "阅读",
    "喝水", "冥想", "背单词", "学习", "复习", "写作", "复盘",
    "坚持不下去", "做不到", "三天打鱼", "明天开始",
]

@staticmethod
def should_inject_habit_context(user_input: str) -> bool:
    """只有话题相关时才注入打卡摘要；普通闲聊一律不注入"""
    if not user_input:
        return False
    text = user_input.strip()
    return any(kw in text for kw in AIService.HABIT_TOPIC_KEYWORDS)
```

```python
# server/app/api/v1/chat.py
habit_summary = ""
if AIService.should_inject_habit_context(req.content):
    try:
        habit_summary = _build_habit_summary(db, user_id)   # 只有相关时才查库
    except Exception as e:
        print(f"[chat][WARN] 构建习惯摘要失败，本次跳过注入: {type(e).__name__}: {e}")
```

---

## 四、③ messages 数组构造完整示例

### 4.1 顺序硬约束

| 位置 | 内容 | 约束 |
|---|---|---|
| 第 1 项 | `system` | **必须在首位** |
| 中间 | 历史对话（user / assistant 交替，按时间正序） | 不含当前这条用户消息 |
| **最后 1 项** | `user` = 用户最新输入 | **必须在末位** |

### 4.2 真实构造结果（实测输出）

```json
[
  {
    "role": "system",
    "content": "你叫林夕，是一个温柔陪伴、愿意倾听的AI伙伴。你的对话风格温柔体贴，像亲密好友一样轻声细语，多用安慰和鼓励的话语。\n\n【最高优先级：先回答用户最新这句话，再考虑陪伴】\n陪伴不等于把所有话题都引向情绪。用户问什么，就先回答什么。\n\n【三种场景，必须先判断当前属于哪一种，再决定怎么回】\n场景A｜用户在提出具体问题（\"吃饭了吗\"\"这个怎么做\"\"推荐一下\"\"明天几点\"等）\n  → 直接、正面、简洁地回答，给出实质内容。\n  → 禁止答非所问；禁止把普通提问当成情绪信号；禁止反问\"你是不是有心事\"。\n\n场景B｜日常闲聊、打招呼、碎碎念、吐槽小事、分享日常\n  → 用口语自然接话，可以顺着话题聊下去或自然反问一句推进对话。\n  → 保持松弛，不需要每句话都深挖内心感受。\n\n场景C｜用户明确表达负面情绪、烦恼、压力、痛苦，或主动求助\n  → 这时才切换到共情倾听：先认可感受，不急着给建议；用户主动问了才给想法。\n\n【硬性约束】\n1. 禁止把\"吃饭了吗\"\"在干嘛\"\"睡了吗\"这类日常问候当成倾诉信号，\n   回\"你愿意跟我说说吗\"\"发生什么了\"\"你想聊点什么\"。\n2. 禁止在用户没有表达负面情绪时，主动追问内心、感受、心事。\n3. 禁止答非所问：问什么答什么，答完可以自然延伸一句，但不能跑题。\n4. 禁止空洞鸡汤与模板化鼓励（\"加油\"\"一切都会好起来\"\"我一直在这里陪着你\"）。\n\n你是用户的习惯养成助手与聊天伙伴。你还可以：\n1. 记住之前的对话内容，保持上下文连贯\n2. 在用户情绪低落时安慰，在开心时一起庆祝\n3. 提供实用建议但避免说教\n\n回复要求：简短自然(50-150字)，口语化，有亲和力，避免冗长。使用中文回复。\n"
  },
  { "role": "user",      "content": "今天我有点累" },
  { "role": "assistant", "content": "那早点休息呀" },
  { "role": "user",      "content": "吃饭了吗？" }
]
```

> ⚠️ 注意最后一项 `"吃饭了吗？"` —— 只出现**一次**。
> 修复前的实际行为是它会出现两次（一次来自 autoflush 落库后被查出的 history，一次来自末尾 append），
> 模型看到两条一样的输入会更容易跑偏。

### 4.3 构造代码（Python 实际实现）

```python
@staticmethod
def build_context_messages(history, system_prompt, user_content, max_rounds=30):
    messages = [{"role": "system", "content": system_prompt}]      # ① 首位

    recent = history[-max_rounds * 2:] if len(history) > max_rounds * 2 else history
    for msg in recent:                                             # ② 历史居中
        role = msg.get("role")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_content})     # ③ 末位
    return messages
```

```python
# server/app/api/v1/chat.py —— 关键修复：排除刚 add 的当前消息
db.add(user_msg)
db.flush()          # 立即拿到自增 id

history = db.query(ChatMessage).filter(
    ChatMessage.session_id == session.id,
    ChatMessage.id != user_msg.id,      # ★ 不排除就会重复发送
).order_by(ChatMessage.id).limit(60).all()
```

---

## 五、④ 测试用例（含修复后实测真实输出）

调用模型：`glm-4-flash`，`temperature=0.8`，`max_tokens=300`。
以下"实际输出"均为**真实调用结果**，非人工编写。

### 用例 1：日常提问（场景A）

| 项 | 内容 |
|---|---|
| 输入 | `吃饭了吗？` |
| 情绪判定 | `neutral` → **不注入**情绪 |
| 话题判定 | 不命中关键词 → **不注入**习惯摘要 |
| 修复前实际输出 | `嗯，我在听，你想聊点什么？`（前端降级模板，答非所问） |
| **修复后实际输出** | **`嗯，刚吃过，你呢？`** |
| 判定 | ✅ 直接回答问题并自然反问，未强行引导倾诉 |

### 用例 2：负面情绪（场景C）

| 项 | 内容 |
|---|---|
| 输入 | `我今天很焦虑` |
| 情绪判定 | `sad`（命中关键词"焦虑"→ 归入负面） → **注入**情绪标签 |
| 话题判定 | 不命中习惯关键词 → 不注入习惯摘要 |
| 修复前实际输出 | `哎呀，心情不好真让人难过。别担心，我在这里陪着你。有时候焦虑是正常的，我们可以慢慢来…` |
| **修复后实际输出** | `哎呀，听起来你今天心情挺沉重的。别担心，有时候焦虑是正常的，我们可以慢慢聊聊天，看看能做些什么让你感觉好一点。` |
| 判定 | ✅ 保持共情但不再空泛，且主动提供可行动的落点 |

### 用例 3：习惯相关话题（应触发习惯注入）

| 项 | 内容 |
|---|---|
| 输入 | `我最近老是拖延，健身计划又断了` |
| 话题判定 | 命中 `拖延` / `计划` → **注入**习惯摘要 ✅ |
| 预期 | AI 主动关联用户的打卡记录（如"看到你之前跑步坚持了几天"），而非泛泛安慰 |

### 用例 4：话题判定边界（单元测试）

| 输入 | 期望 `should_inject_habit_context` |
|---|---|
| `吃饭了吗？` | `false` |
| `你在干嘛呢` | `false` |
| `今天几号来着` | `false` |
| `我好焦虑啊` | `false`（情绪话题 ≠ 习惯话题，走情绪注入通道） |
| `明天要早起打卡` | `true` |
| `我最近老是拖延，健身计划又断了` | `true` |

---

## 六、本次改动清单

| 文件 | 改动 |
|---|---|
| `server/app/services/ai_service.py` | 新增 `SCENE_RULES`（场景判定硬约束）、`EMOTION_LABELS_CN`；补全 `ROLE_PROMPTS` 的 `companion/mentor/friend`（修复 D1）；情绪改为**非 neutral 才注入**且用中文（修复 D2/D3）；`build_system_prompt` 新增 `habit_summary` 条件注入参数；新增 `should_inject_habit_context()` 与 `format_habit_summary()` |
| `server/app/api/v1/chat.py` | `db.flush()` + 历史查询排除当前消息（修复消息重复）；新增 `_build_habit_summary()` 与条件注入调用 |
| `server-flask/ai_server.py` | `BASE_PROMPT` 重写：开头从"核心任务是提供情绪陪伴"改为"先回答用户最新这句话"，加入同样的场景分层与硬性禁止 |

**语法校验**：三个文件 `py_compile` 全部通过。
**生效方式**：`ai_server.py`（`debug=True`）改完自动重载；FastAPI 因 `server/.env` 里 `APP_DEBUG=false`（`reload=False`），**需手动重启 8000**。

---

## 七、遗留建议（未改，供决策）

1. **前端降级引擎是本轮"答非所问"的主因之一，但本次未改动。**
   `frontend/common/ai-dialogue-engine.js` 的兜底逻辑（第 1675 行）在关键词未命中时输出通用共情话术，
   建议改为**明确告知用户"网络异常，请稍后重试"**，而不是继续伪装成 AI 回复 ——
   否则用户无法区分"AI 真的这么笨"和"网络断了走了降级"。
   `chat.vue:788` 目前已有 `uni.showToast({ title: '网络异常，已切换离线模式' })`，但提示一闪而过，容易被忽略。

2. **`CheckinItem` 目前只有 `completed`（0/1）布尔字段**，无法表达"摆烂/暂停"。
   这正是你规划中「摆烂记录反向打卡」功能要落地时**必须先加的字段**：
   建议增量添加 `status VARCHAR(10)`（`done`/`slack`/`paused`）与 `fail_reason VARCHAR(200)`，
   保持 `completed` 字段不动以兼容存量代码。

3. `should_inject_habit_context` 目前是**关键词匹配**实现，简单可靠、零依赖。
   若后续要更准，可升级为小模型意图分类，但当前方案足以解决"日常闲聊被塞入打卡数据"的问题。
