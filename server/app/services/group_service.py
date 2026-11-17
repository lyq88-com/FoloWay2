# -*- coding: utf-8 -*-
"""
群聊核心服务：建表 / CRUD / AI 调度 / 推送分支
全部复用项目已有能力：AIService / PersonaService / dispatch_push / get_current_user
新文件，不碰任何原有业务代码。
"""
import asyncio
import json
import random
import re
import pymysql
from datetime import datetime
from typing import List, Optional, Dict

from app.core.config import settings

# ============ 自动建表（和 bond_service.py 同一模式，首次调用时执行） ============
_TABLES_READY = False

def _get_conn():
    return pymysql.connect(
        host=settings.db_host, port=settings.db_port,
        user=settings.db_user, password=settings.db_password,
        database=settings.db_name, charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
    )

def _ensure_tables():
    """幂等建表：每次服务启动后第一次调用执行，之后跳过"""
    global _TABLES_READY
    if _TABLES_READY:
        return
    conn = _get_conn()
    cur = conn.cursor()
    try:
        # 群组表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS group_chats (
              id BIGINT PRIMARY KEY AUTO_INCREMENT,
              creator_id BIGINT NOT NULL COMMENT '创建者 user.id',
              group_name VARCHAR(50) NOT NULL,
              avatar VARCHAR(100) DEFAULT '',
              status TINYINT DEFAULT 1 COMMENT '1=正常 0=解散',
              created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
              INDEX idx_creator (creator_id),
              INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='群聊表'
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS group_members (
              id BIGINT PRIMARY KEY AUTO_INCREMENT,
              group_id BIGINT NOT NULL,
              user_id BIGINT DEFAULT NULL COMMENT '人类成员 user.id（AI 时为 NULL）',
              role_type VARCHAR(30) DEFAULT NULL COMMENT 'AI 伙伴 role_type（人类时为 NULL）',
              member_type TINYINT NOT NULL COMMENT '0=人类 1=AI',
              nickname VARCHAR(30) DEFAULT '',
              joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
              UNIQUE KEY uk_group_member (group_id, user_id, role_type),
              INDEX idx_group (group_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='群成员表'
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS group_messages (
              id BIGINT PRIMARY KEY AUTO_INCREMENT,
              group_id BIGINT NOT NULL,
              sender_type TINYINT NOT NULL COMMENT '0=人类 1=AI',
              sender_user_id BIGINT DEFAULT NULL,
              sender_role_type VARCHAR(30) DEFAULT NULL,
              content TEXT NOT NULL,
              reply_to_id BIGINT DEFAULT NULL,
              created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
              INDEX idx_group_time (group_id, created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='群消息表'
        """)
        # 【修复】喊停状态列：只改本模块新建的 group_chats，幂等补列，不影响任何旧表
        cur.execute(
            "SELECT COUNT(*) AS c FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='group_chats' "
            "AND COLUMN_NAME='ai_muted'"
        )
        if cur.fetchone()['c'] == 0:
            cur.execute(
                "ALTER TABLE group_chats ADD COLUMN ai_muted TINYINT NOT NULL DEFAULT 0 "
                "COMMENT '1=群内AI已暂停发言'"
            )
        conn.commit()
        _TABLES_READY = True
        print('[GroupService] group_chats/group_members/group_messages 表就绪')
    except Exception as e:
        print(f'[GroupService] 建表失败: {e}')
    finally:
        cur.close()
        conn.close()


# ============ 同步辅助：给 FastAPI 路由用 ============

def create_group(creator_id: int, group_name: str, role_types: List[str]) -> Dict:
    """
    创建群聊：加创建者（人类）+ N 位 AI 伙伴
    role_types: AI 伙伴的 role_type 列表（来自 ai_roles.role_type）
    """
    _ensure_tables()
    conn = _get_conn()
    cur = conn.cursor()
    try:
        # 1. 建群
        cur.execute(
            "INSERT INTO group_chats (creator_id, group_name) VALUES (%s, %s)",
            (creator_id, group_name[:50])
        )
        group_id = cur.lastrowid

        # 2. 加创建者（人类成员）
        try:
            cur.execute(
                "INSERT INTO group_members (group_id, user_id, member_type, nickname) VALUES (%s, %s, 0, %s)",
                (group_id, creator_id, "")
            )
        except pymysql.err.IntegrityError:
            pass  # 已存在则跳过

        # 3. 加 AI 伙伴
        for rt in role_types:
            if not rt:
                continue
            try:
                cur.execute(
                    "INSERT INTO group_members (group_id, role_type, member_type) VALUES (%s, %s, 1)",
                    (group_id, rt)
                )
            except pymysql.err.IntegrityError:
                pass

        conn.commit()

        # 4. 回传群详情
        return get_group(cur, group_id, creator_id)
    finally:
        cur.close()
        conn.close()


def get_group(cur, group_id: int, user_id: int) -> Optional[Dict]:
    cur.execute(
        "SELECT id, creator_id, group_name, avatar, status, ai_muted, created_at "
        "FROM group_chats WHERE id=%s AND status=1",
        (group_id,)
    )
    g = cur.fetchone()
    if not g:
        return None

    cur.execute(
        "SELECT m.id, m.member_type, m.role_type, m.user_id, m.nickname, "
        "       ar.name AS ai_name, ar.avatar AS ai_avatar, ar.personality "
        "FROM group_members m "
        "LEFT JOIN ai_roles ar ON ar.role_type = m.role_type AND m.member_type=1 "
        "WHERE m.group_id=%s "
        "ORDER BY m.member_type ASC, m.joined_at ASC",
        (group_id,)
    )
    members = cur.fetchall()

    # 判断用户是否在群里（只能访问自己的群）
    user_in = any(m.get('member_type') == 0 and m.get('user_id') == user_id for m in members)
    if not user_in:
        return None

    g['members'] = members
    g['member_count'] = len(members)
    g['is_creator'] = (g['creator_id'] == user_id)
    return g


def list_my_groups(user_id: int) -> List[Dict]:
    """列出用户所在的所有群（人类成员匹配）"""
    _ensure_tables()
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT gc.id, gc.group_name, gc.avatar, gc.created_at, "
            "       (SELECT COUNT(*) FROM group_members gm2 WHERE gm2.group_id=gc.id) AS member_count, "
            "       gc.creator_id = %s AS is_creator "
            "FROM group_chats gc "
            "INNER JOIN group_members gm ON gm.group_id=gc.id "
            "WHERE gm.user_id=%s AND gm.member_type=0 AND gc.status=1 "
            "ORDER BY gc.created_at DESC",
            (user_id, user_id)
        )
        rows = cur.fetchall()
        # 补上每个群最后一条消息预览
        for r in rows:
            cur.execute(
                "SELECT content, sender_type, sender_role_type, created_at FROM group_messages "
                "WHERE group_id=%s ORDER BY id DESC LIMIT 1",
                (r['id'],)
            )
            last = cur.fetchone()
            r['last_message'] = last
        return rows
    finally:
        cur.close()
        conn.close()


def rename_group(group_id: int, user_id: int, new_name: str) -> bool:
    _ensure_tables()
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE group_chats SET group_name=%s WHERE id=%s AND creator_id=%s",
            (new_name[:50], group_id, user_id)
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        cur.close()
        conn.close()


def dissolve_group(group_id: int, user_id: int) -> bool:
    _ensure_tables()
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE group_chats SET status=0 WHERE id=%s AND creator_id=%s AND status=1",
            (group_id, user_id)
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        cur.close()
        conn.close()


def add_member(group_id: int, user_id: int, role_type: str) -> bool:
    """添加 AI 成员（仅群内人类成员可操作，防止越权往别人的群里塞角色）"""
    _ensure_tables()
    conn = _get_conn()
    cur = conn.cursor()
    try:
        # 【修复】越权拦截：先校验操作者是该群的人类成员
        cur.execute(
            "SELECT COUNT(*) AS c FROM group_members "
            "WHERE group_id=%s AND user_id=%s AND member_type=0",
            (group_id, user_id)
        )
        if cur.fetchone()['c'] == 0:
            return False
        cur.execute(
            "INSERT INTO group_members (group_id, role_type, member_type) VALUES (%s, %s, 1)",
            (group_id, role_type)
        )
        conn.commit()
        return cur.rowcount > 0
    except pymysql.err.IntegrityError:
        return False
    finally:
        cur.close()
        conn.close()


def remove_member(group_id: int, user_id: int, member_row_id: int) -> bool:
    """移除成员（只能移除 AI 成员，且只有群主能操作）"""
    _ensure_tables()
    conn = _get_conn()
    cur = conn.cursor()
    try:
        # 权限：只有群主 + 只能移除 AI 成员
        cur.execute(
            "SELECT creator_id FROM group_chats WHERE id=%s AND status=1",
            (group_id,)
        )
        g = cur.fetchone()
        if not g or g['creator_id'] != user_id:
            return False

        cur.execute(
            "DELETE FROM group_members WHERE id=%s AND group_id=%s AND member_type=1",
            (member_row_id, group_id)
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        cur.close()
        conn.close()


def leave_group(group_id: int, user_id: int) -> bool:
    """人类成员退群：群主不能退，只能解散"""
    _ensure_tables()
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT creator_id FROM group_chats WHERE id=%s AND status=1",
            (group_id,)
        )
        g = cur.fetchone()
        if not g or g['creator_id'] == user_id:
            return False
        cur.execute(
            "DELETE FROM group_members WHERE group_id=%s AND user_id=%s AND member_type=0",
            (group_id, user_id)
        )
        # 如果人类都退了，自动解散
        cur.execute(
            "SELECT COUNT(*) AS c FROM group_members WHERE group_id=%s AND member_type=0",
            (group_id,)
        )
        if cur.fetchone()['c'] == 0:
            cur.execute("UPDATE group_chats SET status=0 WHERE id=%s", (group_id,))
        conn.commit()
        return True
    finally:
        cur.close()
        conn.close()


def list_messages(group_id: int, user_id: int, page: int = 1, size: int = 50) -> Dict:
    """拉群消息历史（带权限校验 + 分页）"""
    _ensure_tables()
    conn = _get_conn()
    cur = conn.cursor()
    try:
        # 权限：确认用户在群里
        cur.execute(
            "SELECT COUNT(*) AS c FROM group_members WHERE group_id=%s AND user_id=%s AND member_type=0",
            (group_id, user_id)
        )
        if cur.fetchone()['c'] == 0:
            return {'list': [], 'total': 0}

        offset = (max(1, page) - 1) * size
        cur.execute(
            "SELECT id, sender_type, sender_user_id, sender_role_type, content, reply_to_id, created_at "
            "FROM group_messages WHERE group_id=%s "
            "ORDER BY id DESC LIMIT %s OFFSET %s",
            (group_id, size, offset)
        )
        rows = cur.fetchall()
        cur.execute("SELECT COUNT(*) AS c FROM group_messages WHERE group_id=%s", (group_id,))
        total = cur.fetchone()['c']
        return {'list': list(reversed(rows)), 'total': total}
    finally:
        cur.close()
        conn.close()


def save_message(group_id: int, sender_type: int, user_id: Optional[int],
                 role_type: Optional[str], content: str) -> int:
    """写群消息（AI/人类通用）"""
    _ensure_tables()
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO group_messages (group_id, sender_type, sender_user_id, sender_role_type, content) "
            "VALUES (%s, %s, %s, %s, %s)",
            (group_id, sender_type, user_id, role_type, content[:2000])
        )
        conn.commit()
        return cur.lastrowid
    finally:
        cur.close()
        conn.close()


# ============ 异步：AI 调度（错开时间 + 推送分支） ============

def is_member(group_id: int, user_id: int) -> bool:
    """【修复】统一的群成员校验，杜绝越权读写别人的群"""
    _ensure_tables()
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT COUNT(*) AS c FROM group_members "
            "WHERE group_id=%s AND user_id=%s AND member_type=0",
            (group_id, user_id)
        )
        return cur.fetchone()['c'] > 0
    except Exception:
        return False
    finally:
        cur.close()
        conn.close()


def _group_meta(group_id: int) -> Optional[Dict]:
    """取群名 + 喊停状态（群不存在/已解散返回 None）"""
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, group_name, ai_muted FROM group_chats WHERE id=%s AND status=1",
            (group_id,)
        )
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()


# ============ 群聊发言质量辅助（2026-11-15：全员抢答 / 角色串台 / 复读「嗨」） ============

# 模型最爱用的开场问候；群聊里连续几条都以它开头会非常机械
_GREETING_RE = re.compile(r'^\s*(嗨|哈喽|哈啰|你好呀|你好|hi|hello)[\s，,~～!！。.:：]*',
                          re.IGNORECASE)


def _strip_greeting(text: str) -> str:
    """去掉「嗨，」这类模板化开场，保留正文；去完太短则原样返回"""
    out = (text or '').strip()
    m = _GREETING_RE.match(out)
    if m:
        rest = out[m.end():].strip()
        if len(rest) >= 4:
            return rest
    return out


def _pick_reply_targets(ai_members: List[Dict], content: str):
    """
    决定这一条用户消息由谁来接：
    - 用户点名某位伙伴（如「林夕在干嘛呢」）→ 只让被点名的人回复
    - 没点名 → 沿用原来的随机 1~2 位，避免全员刷屏
    返回 (chosen, addressed)
    """
    text = content or ''
    named = [m for m in ai_members
             if (m.get('ai_name') or '').strip()
             and (m.get('ai_name') or '').strip() in text]
    if named:
        return named[:2], True
    reply_count = 1 if len(ai_members) <= 2 else (2 if random.random() < 0.6 else 1)
    return random.sample(ai_members, min(reply_count, len(ai_members))), False


async def dispatch_user_message(group_id: int, user_id: int, content: str) -> Dict:
    """
    用户发消息：存 DB → 选 AI 回复者 → 错开时间生成 → 存 AI 回复 → 推送
    返回：{message_id, ai_replies: [...]}
    """
    _ensure_tables()

    # 【修复】越权拦截：只有群内人类成员才能发言
    if not is_member(group_id, user_id):
        raise PermissionError('not_in_group')
    meta = _group_meta(group_id)
    if not meta:
        raise PermissionError('group_not_found')

    # 1. 写用户消息
    msg_id = save_message(group_id, 0, user_id, None, content)

    # 【修复】用户已喊停：正常存消息，但不再自动唤起任何 AI 发言
    if meta.get('ai_muted'):
        return {'message_id': msg_id, 'ai_replies': [], 'ai_muted': True}

    # 2. 取群成员（拿到 AI role_type 列表）
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT m.role_type, ar.name AS ai_name, ar.avatar, ar.personality "
        "FROM group_members m "
        "LEFT JOIN ai_roles ar ON ar.role_type = m.role_type "
        "WHERE m.group_id=%s AND m.member_type=1 AND m.role_type IS NOT NULL",
        (group_id,)
    )
    ai_members = cur.fetchall()
    cur.close(); conn.close()

    if not ai_members:
        return {'message_id': msg_id, 'ai_replies': []}

    # 3. 读最近 N 条群消息当上下文（排除刚写入的这条，避免重复喂给模型）
    conn = _get_conn(); cur = conn.cursor()
    cur.execute(
        "SELECT sender_type, sender_role_type, content, created_at FROM group_messages "
        "WHERE group_id=%s AND id != %s ORDER BY id DESC LIMIT 8",
        (group_id, msg_id)
    )
    recent = list(reversed(cur.fetchall()))
    cur.close(); conn.close()

    # 4. 智能调度：被点名的人回复；没点名才随机 1~2 位（不重复 + 不所有人一起回）
    name_map = {m['role_type']: (m['ai_name'] or m['role_type']) for m in ai_members}
    chosen, addressed = _pick_reply_targets(ai_members, content)

    # 【复用原有情绪识别 + 共情指令】只在识别成功且触发时注入；任何异常自动降级为普通群聊
    emotion_out, empathy_block, comfort_flag = {}, '', False
    try:
        from app.services.emotion_service import EmotionService
        from app.services.proactive_service import build_empathy_instruction
        emotion_out = EmotionService.analyze_emotion(content) or {}
        if EmotionService.is_rejecting_comfort(content):
            # 用户明确说「别安慰我」→ 停止共情，只做简短回应
            empathy_block = ("用户明确表示现在不需要安慰和建议。"
                             "请只做很短的回应（一到两句），不要讲道理、不要给方案。")
        elif EmotionService.should_trigger_comfort(emotion_out, content):
            empathy_block = build_empathy_instruction(
                emotion_out.get('emotion', ''),
                int(emotion_out.get('intensity', 0) or 0),
                EmotionService.is_crisis_level(emotion_out),
            )
            comfort_flag = (
                EmotionService.is_crisis_level(emotion_out)
                or (emotion_out.get('valence') == 'negative'
                    and (float(emotion_out.get('confidence') or 0) >= 0.5
                         or int(emotion_out.get('intensity') or 0) >= 7))
            )
    except Exception:
        # 情绪识别失败 → 完全退回普通群聊，不影响发言
        emotion_out, empathy_block, comfort_flag = {}, '', False

    # ↓↓↓ 新增（2026-11-15）：情绪场景下允许顺口推荐 App 内可做的事 ↓↓↓
    # 只在识别到负面情绪且用户没有拒绝安慰时追加；一句话带过，不列清单
    if comfort_flag:
        empathy_block += (
            "\n如果自然合适，可以在回复最后顺口邀请用户去做一件具体的事："
            "正念呼吸、写情绪树洞、或者一起专注；一句话带过，不要列清单、不要说教。"
        )
    # ↑↑↑ 新增结束 ↑↑↑

    # 5. 逐个 AI 回复（错开 800~1500ms）
    ai_replies = []
    # 用户消息也入上下文
    all_msgs_for_ctx = recent + [{'sender_type': 0, 'sender_role_type': '', 'content': content}]

    for i, member in enumerate(chosen):
        # 错开时间（模拟真实群聊节奏）
        if i > 0:
            await asyncio.sleep(random.uniform(0.8, 1.5))

        try:
            reply = await _ai_generate_group_reply(
                role_type=member['role_type'],
                ai_name=member['ai_name'] or member['role_type'],
                personality=member.get('personality') or '',
                group_name=meta.get('group_name') or '群聊',
                recent_msgs=all_msgs_for_ctx,
                user_content=content,
                user_id=user_id,
                empathy_block=empathy_block,
                name_map=name_map,
                addressed=addressed,
            )
            if reply and len(reply.strip()) > 0:
                # 写 AI 回复到 DB
                save_message(group_id, 1, None, member['role_type'], reply)
                ai_replies.append({'role_type': member['role_type'], 'content': reply})
                # 【修复】把上一位伙伴的回复也追加进上下文，后发言的人能看到，避免各说各话
                all_msgs_for_ctx.append({'sender_type': 1,
                                         'sender_role_type': member['role_type'],
                                         'content': reply})
        except Exception as e:
            # 单个 AI 失败不影响其他 AI
            print(f'[GroupService] AI {member["role_type"]} 回复失败: {e}')
            continue

    # 6. 【模块4】偶尔让另一位伙伴主动接话（AI 互相搭话，不机械轮流；情绪共情场景不插科打诨）
    #    【修复】用户点名叫人时不再让旁人插话，否则又变成全员抢答
    if ((not empathy_block) and (not addressed) and len(ai_members) >= 2
            and ai_replies and random.random() < 0.4):
        used = {r['role_type'] for r in ai_replies}
        others = [m for m in ai_members if m['role_type'] not in used]
        if others:
            nxt = random.choice(others)
            await asyncio.sleep(random.uniform(0.8, 1.4))
            try:
                follow = await _ai_generate_group_reply(
                    role_type=nxt['role_type'],
                    ai_name=nxt['ai_name'] or nxt['role_type'],
                    personality=nxt.get('personality') or '',
                    group_name=meta.get('group_name') or '群聊',
                    recent_msgs=all_msgs_for_ctx,   # 上一位的回复已在上下文里，不再重复拼接
                    user_content=content,
                    user_id=user_id,
                    follow_up=True,
                    name_map=name_map,
                )
                if follow and follow.strip():
                    save_message(group_id, 1, None, nxt['role_type'], follow)
                    ai_replies.append({'role_type': nxt['role_type'], 'content': follow})
            except Exception:
                pass

    # 7. 触发群消息推送（只推给群内人类成员）
    try:
        await _push_group_message(group_id, user_id, content)
    except Exception:
        pass

    return {'message_id': msg_id, 'ai_replies': ai_replies,
            'emotion': {
                'emotion': emotion_out.get('emotion', 'neutral'),
                'valence': emotion_out.get('valence', 'neutral'),
                'confidence': emotion_out.get('confidence', 0.0),
                'comfort': comfort_flag,
            }}


# ============ 群聊离线兜底（修复「AI 一直重复同一句话」） ============
# 根因：AIService 离线兜底是用 messages[-1]["content"] 取「用户原话」，
# 而群聊这里最后一条是整段 prompt（固定以「你正在参与一个叫…」开头），
# 兜底取前 12 字的结果恒定 → 每条回复都一样。
# 这里改为用真实用户输入做兜底，并对同一角色做相邻去重。
_GROUP_OFFLINE_LINES = [
    "我在呢，{name}听着。{snippet}——这事你更在意哪一点？",
    "嗯，{snippet}。我大概听懂你的意思了，还想多说两句吗？",
    "先别急着下结论，{snippet}这件事，你希望我怎么陪你？",
]
_LAST_OFFLINE_IDX: Dict[str, int] = {}


def _group_offline_reply(user_content: str, speaker: str, role_type: str) -> str:
    """群聊降级时的本地回复：基于用户原话，避免句句相同"""
    snippet = re.sub(r'[？?！!。,.，、\s]', '', user_content or '')[:14]
    if not snippet:
        snippet = '你说的这件事'
    idx = random.randrange(len(_GROUP_OFFLINE_LINES))
    # 同一角色不要连着两次说同一句
    if _LAST_OFFLINE_IDX.get(role_type) == idx:
        idx = (idx + 1) % len(_GROUP_OFFLINE_LINES)
    _LAST_OFFLINE_IDX[role_type] = idx
    return _GROUP_OFFLINE_LINES[idx].format(name=speaker or '我', snippet=snippet)


async def _ai_generate_group_reply(role_type: str, ai_name: str, personality: str,
                                    group_name: str, recent_msgs: List[Dict],
                                    user_content: str, user_id: int = 0,
                                    empathy_block: str = "",
                                    follow_up: bool = False,
                                    name_map: Optional[Dict[str, str]] = None,
                                    addressed: bool = False) -> str:
    """复用项目已有 AIService + PersonaService + MemoryService"""
    from app.services.ai_service import AIService
    from app.services.persona_service import PersonaService
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        role = PersonaService.get_role_by_key(db, role_type)
        persona_prompt = PersonaService.build_persona_prompt(role) if role else ""

        # 【复用原有记忆库】读取该角色已保存的记忆（失败不影响回复）
        memory_block = ""
        if user_id and role:
            try:
                from app.services.memory_service import MemoryService
                MemoryService.extract_by_rules(db, user_id, role_type,
                                               user_content, role.id)
                memory_block = MemoryService.build_prompt_block(
                    db, user_id, role_type, user_content)
            except Exception:
                memory_block = ""

        # 群聊上下文：用「显示名」而不是 role_type，模型才知道谁是谁
        speaker = ai_name or role_type
        nm = name_map or {}
        others = [n for k, n in nm.items() if n and n != speaker]
        ctx_lines = [f"你正在参与一个叫「{group_name}」的群聊。群里其他成员发言如下："]
        for m in recent_msgs[-6:]:
            if m['sender_type'] == 0:
                who = "用户"
            else:
                rt = m.get('sender_role_type') or ''
                who = nm.get(rt) or rt or '某位伙伴'
            ctx_lines.append(f"[{who}]: {m['content'][:200]}")
        ctx_text = "\n".join(ctx_lines)

        # 【修复】明确身份 + 禁止串台：之前容易出现 Kira/Yuki 替林夕回答的情况
        identity_block = (
            f"\n【群聊身份】你现在是「{speaker}」"
            + (f"，同群里还有 {'、'.join(others)}" if others else "")
            + "。你只能以你自己的身份说话，绝对不要冒充其他伙伴，"
              "也不要说自己就是别人；用户点名找别人时，不要替她回答。"
        )
        style_block = (
            "\n【群聊表达】不要用「嗨」「你好」「大家好」这类问候语开头，直接接用户这句话；"
            "不要重复上一位伙伴的开头、句式和 emoji；一两句就够，像真人在群里打字。"
        )
        if addressed:
            style_block += "\n用户这句是在叫你，用你平时的语气自然回应，不用自我介绍，也不用说自己在做什么家务式的客套话。"
        if follow_up:
            style_block += "\n你是在接上一位伙伴的话，顺着聊就行，不要复述她说过的话。"

        messages = [
            {"role": "system", "content": (
                persona_prompt +
                (("\n" + memory_block) if memory_block else "") +
                (("\n" + empathy_block) if empathy_block else "") +
                identity_block + style_block +
                f"\n你正在群聊中，群名叫「{group_name}」。"
                f"\n你的性格：{personality or '温柔体贴'}"
                f"\n规则：像真人一样自然回复，不要每次说话都长；可以简短；偶尔可以接别人的话。"
            )},
            {"role": "user", "content": (
                ctx_text +
                f"\n\n用户刚刚说了：「{user_content[:200]}」"
                + ("\n请顺着上一位伙伴的话接一句，像朋友聊天一样自然，不要重复用户原话。"
                   if follow_up else
                   "\n请以你的身份自然回复一句话。")
            )},
        ]
        reply, meta = await AIService.chat_non_stream(messages, with_meta=True)
        # 【修复】降级时不再让 AIService 用整段 prompt 生成兜底句（会句句相同）
        if meta.get('degraded'):
            prompt_len = sum(len(m.get('content') or '') for m in messages)
            print(f"[GroupService][WARN] 群聊降级 role={role_type} "
                  f"reason={meta.get('reason')} prompt_len={prompt_len}")
            reply = _group_offline_reply(user_content, speaker, role_type)
        return _strip_greeting(reply)
    finally:
        db.close()


async def _push_group_message(group_id: int, sender_user_id: int, user_content: str):
    """群消息推送分支（复用项目已有 dispatch_push，push_type='group_chat'）"""
    from app.modules.newfunc.push_service import (
        dispatch_push, get_or_create_setting, in_quiet_hours,
    )
    from app.modules.newfunc.models import PushRecord
    from app.core.database import SessionLocal
    from datetime import timedelta

    # 查群内所有人类成员（排除发送者自己）
    conn = _get_conn(); cur = conn.cursor()
    cur.execute(
        "SELECT m.user_id FROM group_members m "
        "INNER JOIN group_chats gc ON gc.id=m.group_id "
        "WHERE m.group_id=%s AND m.member_type=0 AND m.user_id != %s AND gc.status=1",
        (group_id, sender_user_id)
    )
    targets = cur.fetchall()
    cur.close(); conn.close()

    if not targets:
        return

    now = datetime.now()
    db = SessionLocal()
    try:
        preview = user_content[:30] + ('...' if len(user_content) > 30 else '')
        for t in targets:
            # 【模块4·群推送】三重复用原有开关体系：总开关 / 独立群开关 / 免打扰时段
            try:
                s = get_or_create_setting(db, t['user_id'])
                if not s.push_enabled or not s.group_push_enabled:
                    continue
                if in_quiet_hours(s, now):
                    continue
                # 冷却防轰炸：同群 3 分钟内只提醒一次（复用 push_record，不新建日志表）
                last = db.query(PushRecord).filter(
                    PushRecord.uid == t['user_id'],
                    PushRecord.push_type == 'group_chat',
                    PushRecord.ref_id == group_id,
                    PushRecord.created_at > now - timedelta(minutes=3),
                ).first()
                if last:
                    continue
            except Exception:
                # 设置读取异常时静默跳过，不影响群消息本身
                continue

            await dispatch_push(
                db, t['user_id'],
                push_type='group_chat',
                title='群里有人发消息了',
                content=preview,
                ref_id=group_id,
                jump_page=f'/pages/group-chat/group-chat?group_id={group_id}',
            )
    finally:
        db.close()


async def send_group_stop(group_id: int, user_id: int) -> Dict:
    """用户喊停：置位 ai_muted 并存一条系统消息，之后不再自动唤起 AI"""
    # 【修复】越权拦截：只有群内成员能喊停
    if not is_member(group_id, user_id):
        raise PermissionError('not_in_group')
    msg_id = save_message(group_id, 0, user_id, None, "【喊停】大家先停下来")
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE group_chats SET ai_muted=1 WHERE id=%s AND status=1",
            (group_id,)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()
    return {'message_id': msg_id, 'ai_muted': True}


def resume_group_ai(group_id: int, user_id: int) -> bool:
    """【修复】恢复群内 AI 发言（喊停后用户主动继续聊天）"""
    if not is_member(group_id, user_id):
        return False
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE group_chats SET ai_muted=0 WHERE id=%s AND status=1",
            (group_id,)
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        cur.close()
        conn.close()


# ============ 模块4 新增：SSE 流式异步生成器版 ============
# 【复用】完全复用已有 dispatch_user_message / _ai_generate_group_reply / _push_group_message 核心逻辑
# 【新增】只是把外层包成 async generator，让前端可以流式收到每个 AI 的回复
async def dispatch_user_message_sse(group_id: int, user_id: int, content: str):
    """
    SSE 版群聊调度：
    - 先 yield 一条 arrival 事件（用户消息已入群）
    - 逐个 AI 回复，每个 AI 内部用 chat_non_stream 生成完整回复后 yield 出去
    - 各个 AI 之间错开 0.8~1.5s（asyncio.sleep）
    - 每个 AI 的回复都会写 DB
    - 最后 yield done 事件 + 触发群消息推送
    """
    _ensure_tables()

    # 1. 先存用户消息（和同步版完全一样）
    msg_id = save_message(group_id, 0, user_id, None, content)
    yield {'role_type': 'arrival', 'content': '', 'message_id': msg_id}

    # 【修复】已喊停：只落库用户消息，不再唤起 AI
    meta = _group_meta(group_id)
    if meta and meta.get('ai_muted'):
        yield {'role_type': 'done', 'content': '', 'ai_muted': True}
        return

    # 2. 取 AI 成员列表
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT m.role_type, ar.name AS ai_name, ar.avatar, ar.personality "
        "FROM group_members m "
        "LEFT JOIN ai_roles ar ON ar.role_type = m.role_type "
        "WHERE m.group_id=%s AND m.member_type=1 AND m.role_type IS NOT NULL",
        (group_id,)
    )
    ai_members = cur.fetchall()
    cur.close(); conn.close()

    if not ai_members:
        yield {'role_type': 'done', 'content': ''}
        return

    # 3. 读最近消息（上下文，排除刚写入的这条）
    conn = _get_conn(); cur = conn.cursor()
    cur.execute(
        "SELECT sender_type, sender_role_type, content FROM group_messages "
        "WHERE group_id=%s AND id != %s ORDER BY id DESC LIMIT 8",
        (group_id, msg_id)
    )
    recent = list(reversed(cur.fetchall()))
    cur.close(); conn.close()
    all_msgs_for_ctx = recent + [{'sender_type': 0, 'sender_role_type': '', 'content': content}]

    # 4. 智能调度：被点名的人回复；没点名才随机 1~2 位（与同步版一致）
    name_map = {m['role_type']: (m['ai_name'] or m['role_type']) for m in ai_members}
    chosen, addressed = _pick_reply_targets(ai_members, content)

    # 4.1 【补齐与同步版一致】情绪识别 + 共情指令；任何异常自动降级为普通群聊
    empathy_block = ''
    comfort_flag = False
    try:
        from app.services.emotion_service import EmotionService
        from app.services.proactive_service import build_empathy_instruction
        emotion_out = EmotionService.analyze_emotion(content) or {}
        if EmotionService.is_rejecting_comfort(content):
            # 用户明确说「别安慰我」→ 停止共情，只做简短回应
            empathy_block = ("用户明确表示现在不需要安慰和建议。"
                             "请只做很短的回应（一到两句），不要讲道理、不要给方案。")
        elif EmotionService.should_trigger_comfort(emotion_out, content):
            empathy_block = build_empathy_instruction(
                emotion_out.get('emotion', ''),
                int(emotion_out.get('intensity', 0) or 0),
                EmotionService.is_crisis_level(emotion_out),
            )
            comfort_flag = (
                EmotionService.is_crisis_level(emotion_out)
                or (emotion_out.get('valence') == 'negative'
                    and (float(emotion_out.get('confidence') or 0) >= 0.5
                         or int(emotion_out.get('intensity') or 0) >= 7))
            )
    except Exception:
        # 情绪识别失败 → 完全退回普通群聊，不影响发言
        empathy_block, comfort_flag = '', False

    if comfort_flag:
        empathy_block += (
            "\n如果自然合适，可以在回复最后顺口邀请用户去做一件具体的事："
            "正念呼吸、写情绪树洞、或者一起专注；一句话带过，不要列清单、不要说教。"
        )

    # 5. 逐个 AI 回复（错开时间）
    for i, member in enumerate(chosen):
        if i > 0:
            await asyncio.sleep(random.uniform(0.8, 1.5))

        try:
            reply = await _ai_generate_group_reply(
                role_type=member['role_type'],
                ai_name=member['ai_name'] or member['role_type'],
                personality=member.get('personality') or '',
                group_name=(meta or {}).get('group_name') or '群聊',
                recent_msgs=all_msgs_for_ctx,
                user_content=content,
                user_id=user_id,
                empathy_block=empathy_block,
                name_map=name_map,
                addressed=addressed,
            )
            reply = (reply or '').strip()
            if reply:
                save_message(group_id, 1, None, member['role_type'], reply)
                yield {'role_type': member['role_type'], 'content': reply}
                # 后发言的伙伴能看到前面的回复，避免各说各话
                all_msgs_for_ctx.append({'sender_type': 1,
                                         'sender_role_type': member['role_type'],
                                         'content': reply})
        except Exception as e:
            print(f'[GroupService SSE] AI {member["role_type"]} failed: {e}')
            continue

    # 6. 推送（fire-and-forget，不阻塞 SSE 关闭）
    try:
        await _push_group_message(group_id, user_id, content)
    except Exception:
        pass

    yield {'role_type': 'done', 'content': ''}
# ============ 模块4 SSE 版结束 ============
