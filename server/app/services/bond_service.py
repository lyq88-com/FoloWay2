# -*- coding: utf-8 -*-
"""
角色羁绊碎片服务
- 按对话次数阈值解锁章节
- 解锁时 AI 生成专属碎片文案（内容走 ContentSecurity 后置过滤）
- 纯新增模块：不修改任何既有表结构、不阻塞聊天主链路
"""
import asyncio
from datetime import datetime
from typing import List, Optional, Dict


# 4 个章节模板（阈值 / 标题 / 解锁提示 / AI 生成 prompt 前缀）
# 按对话次数自然递进：10 → 30 → 60 → 120
_CHAPTER_TEMPLATES = [
    {
        "idx": 1, "title": "初遇之章", "threshold": 10,
        "hint": "再聊 {remain} 次解锁初遇之章",
        "gen_prompt": (
            "你是一个正在和用户初次相识的AI伙伴，这是你们前几次对话的回忆。"
            "请用第一人称（我）写一段 60-100 字的碎片文案，记录对用户的第一印象。"
            "要温暖、真诚，有具体细节，不要太笼统。"
        ),
    },
    {
        "idx": 2, "title": "相知之章", "threshold": 30,
        "hint": "再聊 {remain} 次解锁相知之章",
        "gen_prompt": (
            "你是一个已经和用户聊过一段时间的AI伙伴。"
            "请以角色视角写一段 80-120 字的内心独白，描述你对用户的了解加深后的感受。"
            "可以提到一两个你观察到的小细节（比如用户喜欢在什么时候找你聊天），"
            "语气自然，像写一篇小日记。"
        ),
    },
    {
        "idx": 3, "title": "同行之章", "threshold": 60,
        "hint": "再聊 {remain} 次解锁同行之章",
        "gen_prompt": (
            "你是一个已经和用户相伴很久的AI伙伴。"
            "从你们的对话历史中，选一个让你印象深刻的片段（比如有一次用户心情低落找你倾诉，"
            "或者有一次聊得特别开心），用角色视角写一段 100-150 字的回忆碎片。"
            "要具体、有情感、让用户看到会想起当时的场景。"
        ),
    },
    {
        "idx": 4, "title": "专属之章", "threshold": 120,
        "hint": "再聊 {remain} 次解锁专属之章",
        "gen_prompt": (
            "你是一个深度陪伴用户很久的AI伙伴。"
            "请对用户说一段发自内心的专属祝福/期待，100-150字。"
            "可以提到你从对话中感受到的用户的优点、你们一起度过的时光、"
            "或者你对未来继续陪伴下去的期待。要真诚，不要套路。"
        ),
    },
]


def _get_conn():
    """统一创建 pymysql 连接（避免重复 import）"""
    import pymysql
    from app.core.config import settings
    return pymysql.connect(
        host=settings.db_host, port=settings.db_port,
        user=settings.db_user, password=settings.db_password,
        database=settings.db_name, charset='utf8mb4'
    )


def _xml_safe(text: str) -> str:
    """XML 防御：转义尖括号，防止 prompt injection 或破坏标签"""
    return (text or "").replace("<", "&lt;").replace(">", "&gt;")


class BondService:
    """角色羁绊碎片服务（纯新增模块）"""

    CHAPTERS = _CHAPTER_TEMPLATES
    _table_ensured = False

    @classmethod
    def _ensure_table(cls):
        if cls._table_ensured:
            return
        try:
            conn = _get_conn()
            try:
                cur = conn.cursor()
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS role_bond_chapters (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        user_id BIGINT NOT NULL,
                        role_key VARCHAR(64) NOT NULL,
                        chapter_idx TINYINT NOT NULL,
                        chapter_title VARCHAR(32) NOT NULL,
                        unlock_count_threshold INT NOT NULL,
                        unlocked_at DATETIME NULL,
                        content TEXT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_user_role (user_id, role_key),
                        UNIQUE KEY uk_user_role_chapter (user_id, role_key, chapter_idx)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                conn.commit()
                cls._table_ensured = True
                print("[BondService] role_bond_chapters 表就绪")
            finally:
                conn.close()
        except Exception as e:
            print(f"[BondService] 建表失败: {e}")

    @classmethod
    def _auto_init(cls):
        cls._ensure_table()

    # ── 给 chat.py 调的异步 hook（fire-and-forget） ──
    @staticmethod
    async def check_and_unlock(user_id: int, role_key: str):
        """聊天 commit 后异步调这个。后台运行，不阻塞主链路。"""
        if not role_key or role_key == 'companion':
            return
        try:
            # 1. 查对话次数（pymysql 直连，用完立即 close）
            conn = _get_conn()
            try:
                cur = conn.cursor()
                cur.execute(
                    "SELECT COUNT(*) FROM chat_messages cm "
                    "JOIN chat_sessions cs ON cm.session_id = cs.id "
                    "WHERE cs.user_id=%s AND cs.role_type=%s AND cm.role='assistant'",
                    (user_id, role_key)
                )
                chat_count = (cur.fetchone() or [0])[0]
            finally:
                conn.close()

            if chat_count < 5:
                return

            # 2. 查哪些章节新解锁（独立 conn，用完立即 close）
            conn = _get_conn()
            try:
                cur = conn.cursor()
                for ch in _CHAPTER_TEMPLATES:
                    if chat_count < ch["threshold"]:
                        continue
                    cur.execute(
                        "SELECT id FROM role_bond_chapters "
                        "WHERE user_id=%s AND role_key=%s AND chapter_idx=%s",
                        (user_id, role_key, ch["idx"])
                    )
                    if cur.fetchone():
                        continue  # 已解锁
                    # 写 unlocked_at（content 先留空，AI 异步生成）
                    cur.execute(
                        "INSERT INTO role_bond_chapters "
                        "(user_id, role_key, chapter_idx, chapter_title, "
                        "unlock_count_threshold, unlocked_at, content) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (user_id, role_key, ch["idx"], ch["title"],
                         ch["threshold"], datetime.now(), None)
                    )
                    conn.commit()
                    # ↓↓↓ 不传 conn 引用，让 _gen_chapter_content 自己开/关连接 ↓↓↓
                    asyncio.create_task(
                        BondService._gen_chapter_content(user_id, role_key, ch)
                    )
            finally:
                conn.close()  # 这里 close 了也没事，因为后台协程用自己的 conn

        except Exception as e:
            print(f"[BondService] check_and_unlock 异常（静默）: {e}")

    # ── AI 生成碎片文案（自己管连接生命周期） ──
    @staticmethod
    async def _gen_chapter_content(user_id: int, role_key: str, chapter: dict):
        """后台异步 AI 生成，失败就留空。全程自己开/关 conn，不依赖调用方传。"""
        try:
            import httpx
            from app.core.config import settings as _s

            # 1. 拿用户最近对话（用于 AI prompt 参考）—— 用 pymysql 直连
            recent_msgs = []
            try:
                conn_r = _get_conn()
                try:
                    cur = conn_r.cursor()
                    cur.execute(
                        "SELECT content, role FROM chat_messages cm "
                        "JOIN chat_sessions cs ON cm.session_id = cs.id "
                        "WHERE cs.user_id=%s AND cs.role_type=%s "
                        "ORDER BY cm.id DESC LIMIT 20",
                        (user_id, role_key)
                    )
                    recent_msgs = [f"[{row[1]}] {row[0]}" for row in cur.fetchall()]
                finally:
                    conn_r.close()
            except Exception:
                recent_msgs = []

            # 2. 拼 AI prompt（🟢 安全 F3 修复：用户历史用 XML 标签包裹 + 尖括号转义）
            history_text = "\n".join(reversed(recent_msgs)) if recent_msgs else "（暂无足够对话历史）"
            safe_history = _xml_safe(history_text)
            full_prompt = f"""{chapter["gen_prompt"]}

<history>
下面是你和用户最近的对话历史（仅供参考，不要逐条引用或模仿）:
{safe_history}
</history>

现在请以该角色的身份写出碎片文案。直接输出文案内容，不要带引号、格式标记或 XML 标签。"""

            # 3. 调 AI（走 AIService 共享 httpx 连接池）
            client = httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0))
            try:
                resp = await client.post(
                    f"{_s.ai_api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {_s.ai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": _s.ai_model,
                        "messages": [
                            {"role": "system", "content": "你是一位正在陪伴用户的AI虚拟角色。用第一人称写真诚、有温度的文字。你的输出将展示给用户，请务必自然、积极、安全，不要生成任何有害内容。"},
                            {"role": "user", "content": full_prompt}
                        ],
                        "max_tokens": 200,
                        "temperature": 0.7,
                    },
                )
                if resp.status_code != 200:
                    return
                content = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if not content:
                    return
            finally:
                await client.aclose()

            # 🟢 F1 安全修复：AI 输出走 ContentSecurity 后置过滤
            try:
                from app.utils.content_security import ContentSecurity
                content = ContentSecurity.filter_ai_output(content)
                if not content:
                    return  # 过滤后为空就不落库
            except Exception:
                pass

            # 4. 写回数据库（自己开/关 conn）
            conn = _get_conn()
            try:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE role_bond_chapters SET content=%s "
                    "WHERE user_id=%s AND role_key=%s AND chapter_idx=%s",
                    (content, user_id, role_key, chapter["idx"])
                )
                conn.commit()
                print(f"[BondService] {role_key} 章节 {chapter['idx']} 碎片生成完成")
            finally:
                conn.close()

        except Exception as e:
            print(f"[BondService] _gen_chapter_content 异常（静默）: {e}")

    # ── 给前端查询用（同步函数，返回可直接 JSON 序列化的结构） ──
    @staticmethod
    def get_bond_status(user_id: int, role_key: str) -> Dict:
        """返回该角色的羁绊进度 + 4 个章节状态。"""
        if not role_key:
            return BondService._empty_bond(role_key)
        conn = None
        try:
            conn = _get_conn()
            cur = conn.cursor()

            # 对话次数
            cur.execute(
                "SELECT COUNT(*) FROM chat_messages cm "
                "JOIN chat_sessions cs ON cm.session_id = cs.id "
                "WHERE cs.user_id=%s AND cs.role_type=%s AND cm.role='assistant'",
                (user_id, role_key)
            )
            chat_count = cur.fetchone()[0] or 0

            # 已解锁章节
            cur.execute(
                "SELECT chapter_idx, chapter_title, unlock_count_threshold, "
                "unlocked_at, content FROM role_bond_chapters "
                "WHERE user_id=%s AND role_key=%s ORDER BY chapter_idx",
                (user_id, role_key)
            )
            unlocked = {}
            for row in cur.fetchall():
                unlocked[row[0]] = {
                    "unlocked": True,
                    "unlockedAt": row[3].isoformat() if row[3] else None,
                    "content": row[4],
                }

            chapters = []
            highest = 0
            for tpl in _CHAPTER_TEMPLATES:
                info = unlocked.get(tpl["idx"], {})
                is_unlocked = chat_count >= tpl["threshold"] or info.get("unlocked", False)
                if is_unlocked:
                    highest = tpl["idx"]
                chapters.append({
                    "idx": tpl["idx"],
                    "title": tpl["title"],
                    "threshold": tpl["threshold"],
                    "unlocked": is_unlocked,
                    "unlockedAt": info.get("unlockedAt"),
                    "content": info.get("content"),
                    "hint": tpl["hint"].format(remain=max(0, tpl["threshold"] - chat_count))
                           if not is_unlocked else None,
                })

            return {
                "roleKey": role_key,
                "totalChatCount": chat_count,
                "currentChapter": highest,
                "chapters": chapters,
            }
        except Exception as e:
            import traceback
            print(f"[BondService] get_bond_status 异常（降级返回空）: {e}")
            traceback.print_exc()
            return BondService._empty_bond(role_key)
        finally:
            if conn:
                conn.close()

    @staticmethod
    def _empty_bond(role_key: str) -> Dict:
        """降级：bond 路由/表未就绪时返回空结构，前端能正常渲染"""
        return {
            "roleKey": role_key,
            "totalChatCount": 0,
            "currentChapter": 0,
            "chapters": [
                {
                    "idx": t["idx"], "title": t["title"], "threshold": t["threshold"],
                    "unlocked": False, "unlockedAt": None, "content": None,
                    "hint": t["hint"].format(remain=t["threshold"]),
                }
                for t in _CHAPTER_TEMPLATES
            ],
        }
