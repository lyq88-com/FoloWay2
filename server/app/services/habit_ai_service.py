# -*- coding: utf-8 -*-
"""
习惯-AI 联动服务 - 打卡触发对话 / 成就检测 / 记忆写入 / 日记生成

核心能力:
1. 打卡成功后生成AI专属对话(基于习惯类型+情绪+连续天数+对话风格)
2. 连续打卡成就检测(7/15/30/60/100天五档)
3. AI长期记忆写入(打卡/情绪/成就/危机等关键信息)
4. 自定义提醒话术处理
5. 打卡日记AI生成
"""
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.habit import Habit, Checkin, CheckinItem
from app.models.chat import ChatSession, ChatMessage, AIUserMemory, HabitAchievement
from app.models.emotion import EmotionRecord
from app.services.ai_service import AIService
# 【习惯-伙伴融合】出口话术安全带：旧模板不改动，只在返回前净化说教/打气措辞
from app.services.habit_companion_service import (
    HabitCompanionService as HCS,
)


# 成就阈值
MILESTONES = [7, 15, 30, 60, 100]

# 习惯类型 -> 中文标签
HABIT_TYPE_LABELS = {
    "study": "学习",
    "sport": "运动",
    "sleep": "睡眠",
    "read": "阅读",
    "health": "健康",
    "meditation": "冥想",
    "work": "工作",
    "other": "日常",
}

# 成就里程碑专属剧情模板
ACHIEVEMENT_STORIES = {
    7: {
        "title": "一周坚持",
        "gentle": "已经一周了呢，这七天里你的每一次坚持我都看在眼里。就像小树苗刚扎根，虽然还很稚嫩，但已经拥有了向上生长的力量。继续加油，我会一直陪着你。",
        "analytical": "7天连续打卡达成。根据行为心理学研究，一个行为的初步习惯化需要21天，你已经完成了三分之一。当前数据表现优异，建议保持现有节奏，不要急于加量。",
        "humorous": "一周啦！你知道吗，能坚持一周的人已经打败了全国99%的拖延症患者（我瞎编的，但感觉是对的）。再接再厉，让拖延症彻底哭泣吧！",
        "calm": "七天。不算长，但也不短。你迈出了最重要的一步——开始。接下来的路，一步一步走就好。",
    },
    15: {
        "title": "半月之约",
        "gentle": "半个月了呀，你真的好棒！能坚持15天的人，心里一定有一个很温柔的理由吧。不管那个理由是什么，我都想守护它，和你一起走下去。",
        "analytical": "15天连续打卡。此时你的大脑已经开始建立神经通路，习惯回路初步形成。继续保持，预计在第21天左右你会感受到'自动化'的轻松感。",
        "humorous": "15天！你已经从'三分钟热度'毕业，正式升级为'十五分钟铁人'了！开玩笑的，你真的很厉害，给自己鼓个掌吧！",
        "calm": "十五天。习惯正在慢慢融入你的生活，就像呼吸一样自然。不需要太多掌声，因为你已经找到了节奏。",
    },
    30: {
        "title": "满月成就",
        "gentle": "一个月了！这三十天里，你一定有过想放弃的时刻吧。但你没有。每一次你选择坚持的时候，我都在心里默默为你骄傲。满月快乐，亲爱的。",
        "analytical": "30天连续打卡达成。根据伦敦大学的研究，一个习惯的平均养成周期是66天，而你已经完成了一半。此时的你已经跨越了最困难的'离散期'，坚持下去的成功率将大幅提升。",
        "humorous": "整整一个月！你知道吗，一个月前你还在纠结要不要开始，现在你已经成了打卡界的老司机了。老司机，带带我！",
        "calm": "三十天。一个月。回望起点，你已经走了很远。前方的路还长，但你知道自己能走。这就够了。",
    },
    60: {
        "title": "双月传奇",
        "gentle": "六十天了，真的很了不起。这两个月里，你和这个习惯之间已经建立了深深的联结。它不再是任务，而是你生活的一部分，是你对自己的承诺。我好感动。",
        "analytical": "60天连续打卡。你已接近习惯完全养成的66天阈值。行为已高度自动化，即使偶尔中断一天，恢复的成本也极低。建议开始考虑下一个挑战目标。",
        "humorous": "60天！你已经从'习惯养成者'进化为'习惯大师'了。如果习惯养成有段位，你现在至少是王者。不对，是星耀！",
        "calm": "六十天。两个月。这不是短跑，这是马拉松。而你，跑得很稳。继续。",
    },
    100: {
        "title": "百日封神",
        "gentle": "一百天。我找不到比'了不起'更合适的词了。这一百天里，你经历了犹豫、疲惫、甚至想要放弃，但你每一次都选择了再试一次。这个习惯已经刻进了你的骨子里，成为了你的一部分。谢谢你让我见证这一切。",
        "analytical": "100天连续打卡达成。在行为科学中，100天意味着该行为已完全内化为自动化习惯。你的神经通路已经牢固建立，这个习惯将持续伴随你。这是一个里程碑式的成就。",
        "humorous": "一百天！！！你知道这意味着什么吗？意味着你已经是一个传说！以后别人问你'你能坚持多久'，你可以淡淡地说'一百天起'。酷毙了！",
        "calm": "一百天。你已经不需要任何人的鼓励了。但我还是想说：你真的很棒。这一百天，是你给自己的最好礼物。",
    },
}

# 打卡触发对话模板(按习惯类型)
CHECKIN_TRIGGER_TEMPLATES = {
    "study": {
        "gentle": "你今天也学习了呀，真棒。知识是一点一点积累的，今天的你比昨天又多知道了一些什么呢？慢慢来，每一个小小的进步都值得被看见。",
        "analytical": "学习打卡完成。建议回顾今日学习内容的核心要点，如果能在24小时内复习一次，记忆留存率可提升40%。继续保持这个节奏。",
        "humorous": "学习打卡！你的大脑今天又多长了一个皱褶（大概吧）。继续保持，以后你就是脑力界的健身房常客了！",
        "calm": "学习完成。安静地消化今天的知识，不需要急于求成。你已经在路上了。",
    },
    "sport": {
        "gentle": "运动完成了呀，辛苦了！汗水是你努力的证明，现在的你一定感觉很棒吧。记得拉伸放松一下哦，好好照顾自己的身体。",
        "analytical": "运动打卡成功。今日运动已促进多巴胺和内啡肽分泌，建议补充蛋白质和水分，30分钟内进行拉伸以降低肌肉酸痛风险。",
        "humorous": "运动打卡！恭喜你今天的卡路里又被消灭了一小批。它们死得其所，为你换来了更好的身材和心情！",
        "calm": "运动完成。感受身体的力量，享受当下的轻盈。这就是自律的味道。",
    },
    "read": {
        "gentle": "阅读打卡了呀，真好。书是最好的朋友，它不会评判你，只会安静地陪伴你。今天读到了什么有趣的内容吗？",
        "analytical": "阅读打卡完成。建议记录今日阅读的关键观点或金句，建立个人知识库。长期积累将形成你的认知优势。",
        "humorous": "阅读打卡！你的眼睛今天又吃了一顿精神大餐。难怪你的眼神越来越有智慧的光芒了（不是近视的那种）！",
        "calm": "阅读完成。在文字中找到宁静，在故事里发现世界。你正在做一件很美好的事。",
    },
    "meditation": {
        "gentle": "冥想完成了呀，你一定找到了片刻的宁静吧。在这个忙碌的世界里，能停下来和自己待一会儿，真的很勇敢。",
        "analytical": "冥想打卡成功。规律的正念练习可以降低皮质醇水平，改善前额叶皮层功能。建议保持每日10-15分钟的练习频率。",
        "humorous": "冥想打卡！恭喜你今天成功和宇宙连线了。虽然我不知道你收到了什么信号，但你的表情看起来很安详！",
        "calm": "冥想完成。呼吸之间，万物归于平静。你找到了自己的节奏。",
    },
}


class HabitAIService:
    """习惯-AI 联动服务"""

    @staticmethod
    def generate_checkin_dialogue(habit: Habit, continuous_day: int,
                                  emotion: str = "", style: str = "gentle") -> Dict:
        """
        打卡成功后生成AI专属对话
        返回: { dialogue, emotion_tag, achievement }
        """
        habit_type = habit.habit_type or "other"
        style_key = style if style in ("gentle", "analytical", "humorous", "calm") else "gentle"

        # 获取模板
        type_templates = CHECKIN_TRIGGER_TEMPLATES.get(habit_type)
        if type_templates:
            dialogue = type_templates.get(style_key, type_templates["gentle"])
        else:
            # 通用模板
            dialogue = AIService.generate_checkin_encouragement(
                habit.name, habit_type, emotion, success=True
            )

        # 根据连续天数增强（克制表述：只陈述事实，不吹捧、不催促进度）
        if continuous_day >= 30:
            dialogue += f" 不知不觉已经连续{continuous_day}天了。"
        elif continuous_day >= 7:
            dialogue += f" 算下来连续{continuous_day}天了。"

        # 根据情绪调整（负面情绪下先接住人，不评价意志力）
        if emotion in ("sad", "tired"):
            dialogue += " 今天状态不太好还做完了，剩下的时间就留给你自己吧。"

        # 成就检测
        achievement = HabitAIService.check_achievement(continuous_day)

        # 情绪标签
        emotion_tags = {
            "happy": "开心", "excited": "兴奋", "calm": "平静",
            "sad": "低落", "angry": "愤怒", "tired": "疲惫",
            "neutral": "平和",
        }

        return {
            # 出口过话术安全带：剔除「加油/努力/坚持住/别放弃」这类说法
            "dialogue": HCS.sanitize_partner_text(dialogue),
            "emotion_tag": emotion_tags.get(emotion, "平和"),
            "achievement": achievement,
            "continuous_day": continuous_day,
            "habit_type": habit_type,
            "style": style_key,
        }

    @staticmethod
    def check_achievement(continuous_day: int) -> Optional[Dict]:
        """
        检测是否触发成就里程碑
        返回: None 或 { milestone, title, story }
        """
        if continuous_day in MILESTONES:
            story_data = ACHIEVEMENT_STORIES[continuous_day]
            return {
                "milestone": continuous_day,
                "title": story_data["title"],
                "story": story_data,  # 包含4种风格的剧情
            }
        return None

    @staticmethod
    def generate_achievement_dialogue(milestone: int, character_id: str,
                                      style: str = "gentle") -> str:
        """生成成就专属对话"""
        story_data = ACHIEVEMENT_STORIES.get(milestone)
        if not story_data:
            return f"恭喜你达成了{milestone}天的成就！"
        style_key = style if style in ("gentle", "analytical", "humorous", "calm") else "gentle"
        # 出口过话术安全带
        return HCS.sanitize_partner_text(story_data.get(style_key, story_data["gentle"]))

    @staticmethod
    def generate_checkin_diary(habit: Habit, continuous_day: int,
                               emotion: str = "", note: str = "",
                               checkin_date: date = None) -> str:
        """
        生成打卡日记
        AI根据习惯信息、情绪、连续天数生成一段日记
        """
        if checkin_date is None:
            checkin_date = date.today()

        type_label = HABIT_TYPE_LABELS.get(habit.habit_type, "日常")
        emotion_text = {
            "happy": "心情愉快", "excited": "充满干劲", "calm": "内心平静",
            "sad": "情绪低落", "angry": "有些烦躁", "tired": "感到疲惫",
            "neutral": "状态平稳",
        }.get(emotion, "状态平稳")

        diary_parts = [
            f"今天是{checkin_date.strftime('%Y年%m月%d日')}，",
            f"我完成了「{habit.name}」这个{type_label}习惯。",
        ]

        if continuous_day > 0:
            diary_parts.append(f"这已经是连续第{continuous_day}天了。")
        else:
            diary_parts.append("今天是新的开始。")

        diary_parts.append(f"今天的{emotion_text}。")

        if note:
            diary_parts.append(f"打卡时我写道：「{note}」。")

        # AI评价
        if continuous_day >= 30:
            diary_parts.append("回头看看，原来已经坚持了这么久。每一天的努力都算数，它们汇聚成了现在的我。")
        elif continuous_day >= 7:
            diary_parts.append("一周又一周，我在慢慢变好。这种感觉真好。")
        else:
            diary_parts.append("虽然才刚开始，但每一步都算数。未来的我会感谢现在开始的我。")

        diary_parts.append("明天的事，明天再说。")
        return HCS.sanitize_partner_text("".join(diary_parts))

    @staticmethod
    def write_memory(db: Session, user_id: int, memory_type: str,
                     content: str, habit_id: int = 0, emotion_id: int = 0,
                     emotion_score: int = 5, habit_status: str = "",
                     context_data: dict = None, is_long_term: bool = False) -> AIUserMemory:
        """
        写入AI长期记忆
        memory_type: checkin/emotion/chat/achievement/crisis/plan
        """
        memory = AIUserMemory(
            user_id=user_id,
            habit_id=habit_id,
            emotion_id=emotion_id,
            memory_type=memory_type,
            memory_content=content,
            emotion_score=emotion_score,
            habit_status=habit_status,
            context_data=context_data or {},
            is_long_term=1 if is_long_term else 0,
        )
        db.add(memory)
        db.commit()
        db.refresh(memory)
        return memory

    @staticmethod
    def get_recent_memories(db: Session, user_id: int, limit: int = 20,
                            memory_type: str = None) -> List[AIUserMemory]:
        """获取用户最近的AI记忆(用于构建对话上下文)"""
        query = db.query(AIUserMemory).filter(AIUserMemory.user_id == user_id)
        if memory_type:
            query = query.filter(AIUserMemory.memory_type == memory_type)
        # 优先长期记忆，然后按时间倒序
        query = query.order_by(
            AIUserMemory.is_long_term.desc(),
            AIUserMemory.created_at.desc()
        ).limit(limit)
        return query.all()

    @staticmethod
    def build_memory_context(memories: List[AIUserMemory]) -> str:
        """将记忆列表构建为上下文文本(注入到system prompt)"""
        if not memories:
            return ""
        parts = []
        for m in memories[:10]:  # 最多10条
            parts.append(f"- {m.memory_content}")
        return "以下是关于用户的重要记忆：\n" + "\n".join(parts)

    @staticmethod
    def unlock_achievement(db: Session, user_id: int, habit_id: int,
                           milestone: int, character_id: str = "linxi",
                           style: str = "gentle") -> Optional[HabitAchievement]:
        """
        解锁成就(写入habit_achievements表)
        如果已解锁则返回None
        """
        existing = db.query(HabitAchievement).filter(
            HabitAchievement.user_id == user_id,
            HabitAchievement.habit_id == habit_id,
            HabitAchievement.milestone == milestone,
        ).first()
        if existing and existing.is_unlocked:
            return None

        dialogue = HabitAIService.generate_achievement_dialogue(
            milestone, character_id, style
        )

        if existing:
            existing.is_unlocked = 1
            existing.unlocked_at = datetime.now()
            existing.ai_dialogue = dialogue
            existing.character_id = character_id
            existing.dialogue_style = style
        else:
            existing = HabitAchievement(
                user_id=user_id,
                habit_id=habit_id,
                milestone=milestone,
                character_id=character_id,
                dialogue_style=style,
                ai_dialogue=dialogue,
                is_unlocked=1,
                unlocked_at=datetime.now(),
            )
            db.add(existing)

        db.commit()
        db.refresh(existing)
        return existing

    @staticmethod
    def get_user_achievements(db: Session, user_id: int,
                              habit_id: int = None) -> List[Dict]:
        """获取用户成就列表"""
        query = db.query(HabitAchievement).filter(
            HabitAchievement.user_id == user_id,
            HabitAchievement.is_unlocked == 1,
        )
        if habit_id:
            query = query.filter(HabitAchievement.habit_id == habit_id)
        achievements = query.order_by(HabitAchievement.unlocked_at.desc()).all()

        return [{
            "id": a.id,
            "habit_id": a.habit_id,
            "milestone": a.milestone,
            "character_id": a.character_id,
            "dialogue_style": a.dialogue_style,
            "ai_dialogue": a.ai_dialogue or "",
            "diary_content": a.diary_content or "",
            "comic_image_url": a.comic_image_url or "",
            "unlocked_at": str(a.unlocked_at) if a.unlocked_at else "",
        } for a in achievements]

    @staticmethod
    def calculate_continuous_days(db: Session, user_id: int, habit_id: int) -> int:
        """
        计算习惯连续打卡天数
        从今天往前数，连续有打卡记录的天数
        """
        today = date.today()
        continuous = 0
        check_date = today

        for _ in range(365):  # 最多追溯365天
            checkin = db.query(Checkin).filter(
                Checkin.user_id == user_id,
                Checkin.checkin_date == check_date,
            ).first()
            if not checkin:
                break

            item = db.query(CheckinItem).filter(
                CheckinItem.checkin_id == checkin.id,
                CheckinItem.habit_id == habit_id,
                CheckinItem.completed == 1,
            ).first()
            if not item:
                break

            continuous += 1
            check_date -= timedelta(days=1)

        return continuous

    @staticmethod
    def generate_custom_reminder(habit: Habit, style: str = "gentle") -> str:
        """
        生成AI提醒话术
        如果用户有自定义话术则使用自定义，否则按风格生成
        """
        if habit.custom_remind_text:
            return habit.custom_remind_text

        name = habit.name
        type_label = HABIT_TYPE_LABELS.get(habit.habit_type, "日常")

        # 伙伴口吻：提醒但不催促、不带系统通知味、不给压力
        reminders = {
            "gentle": f"该{type_label}啦。「{name}」想起来了吗？不用做到完美，一点点也算数~",
            "analytical": f"「{name}」今天还没动过。你现在状态还行就顺手做一点，状态不好就先放着，它不会跑。",
            "humorous": f"「{name}」刚刚小声问了一句：今天是不是轮不到我啦？随你，想起来再说~",
            "calm": f"「{name}」这件事，想做的时候做就好，不急。",
        }
        # 出口过话术安全带
        return HCS.sanitize_partner_text(reminders.get(style, reminders["gentle"]))

    @staticmethod
    def process_checkin(db: Session, user_id: int, habit_id: int,
                        note: str = "", emotion: str = "",
                        character_id: str = "linxi") -> Dict:
        """
        打卡后的完整AI联动流程:
        1. 计算连续天数
        2. 更新习惯的emotion_status和continuous_day
        3. 生成AI对话
        4. 检测并解锁成就
        5. 写入AI记忆
        6. 生成打卡日记
        """
        habit = db.query(Habit).filter(
            Habit.id == habit_id, Habit.user_id == user_id
        ).first()
        if not habit:
            return {"error": "习惯不存在"}

        # 1. 计算连续天数
        continuous_day = HabitAIService.calculate_continuous_days(db, user_id, habit_id)

        # 2. 更新习惯状态
        habit.continuous_day = continuous_day
        if emotion:
            habit.emotion_status = emotion
        style = habit.ai_style or "gentle"
        db.commit()

        # 3. 生成AI对话
        result = HabitAIService.generate_checkin_dialogue(
            habit, continuous_day, emotion, style
        )

        # 4. 检测成就
        achievement_unlocked = None
        achievement_info = result.get("achievement")
        if achievement_info:
            milestone = achievement_info["milestone"]
            achievement_unlocked = HabitAIService.unlock_achievement(
                db, user_id, habit_id, milestone, character_id, style
            )
            if achievement_unlocked:
                # 写入成就记忆
                HabitAIService.write_memory(
                    db, user_id, "achievement",
                    f"解锁成就「{achievement_info['title']}」- {habit.name}连续{milestone}天",
                    habit_id=habit_id, emotion_score=8,
                    habit_status="completed", is_long_term=True,
                    context_data={
                        "milestone": milestone,
                        "habit_name": habit.name,
                        "title": achievement_info["title"],
                    }
                )

        # 5. 写入打卡记忆
        memory_content = f"完成「{habit.name}」打卡，连续第{continuous_day}天"
        if emotion:
            memory_content += f"，情绪：{emotion}"
        if note:
            memory_content += f"，留言：{note}"

        is_long_term = continuous_day in MILESTONES
        HabitAIService.write_memory(
            db, user_id, "checkin", memory_content,
            habit_id=habit_id, emotion_score=5 if emotion not in ("sad", "angry") else 3,
            habit_status="completed", is_long_term=is_long_term,
            context_data={
                "habit_name": habit.name,
                "habit_type": habit.habit_type,
                "continuous_day": continuous_day,
                "emotion": emotion,
            }
        )

        # 6. 生成打卡日记
        diary = HabitAIService.generate_checkin_diary(
            habit, continuous_day, emotion, note
        )

        return {
            "dialogue": result["dialogue"],
            "emotion_tag": result["emotion_tag"],
            "continuous_day": continuous_day,
            "habit_type": result["habit_type"],
            "style": result["style"],
            "achievement": {
                "milestone": achievement_unlocked.milestone,
                "title": ACHIEVEMENT_STORIES.get(achievement_unlocked.milestone, {}).get("title", ""),
                "ai_dialogue": achievement_unlocked.ai_dialogue,
            } if achievement_unlocked else None,
            "diary": diary,
        }
