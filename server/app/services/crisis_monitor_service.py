# -*- coding: utf-8 -*-
"""
危机监测服务 - 实时情绪监测 + 预警机制 + 干预措施 + 资源推荐 + 应对指南
复用 CrisisService 的关键词检测, 融合语音情绪特征与连续负面记录加权
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.crisis import CrisisContact, EmotionMonitorLog, CrisisResource, UserPrivacySetting
from app.services.crisis_service import CrisisService
from app.services.emotion_service import EmotionService
# 【习惯-伙伴融合】自我否定 → 情绪接纳优先 + 提供「暂时暂停部分习惯」选项
from app.services.habit_companion_service import HabitCompanionService as HCS


class MonitorService:
    """实时情绪监测服务"""

    # 灵敏度 → 风险分数阈值
    SENSITIVITY_THRESHOLDS = {
        "low": {"high": 65, "critical": 90},
        "medium": {"high": 50, "critical": 80},
        "high": {"high": 35, "critical": 65},
    }

    # 连续负面记录加权(条数 → 额外分数)
    CONSECUTIVE_WEIGHTS = [(5, 20), (3, 12), (2, 6)]

    @staticmethod
    def analyze_realtime(text: str = None, voice_sentiment: str = None,
                         voice_volume: float = None, voice_speed: float = None) -> Dict:
        """
        实时情绪风险分析(纯计算, 不落库)
        返回: {risk_level, score, emotion, valence, factors, message}
        """
        score = 0
        factors = []

        # 1. 文本关键词检测(复用CrisisService)
        crisis_result = {"level": "normal", "trigger": ""}
        emotion_result = {"emotion": "neutral", "valence": "neutral", "confidence": 0}
        if text:
            crisis_result = CrisisService.check_crisis(text)
            emotion_result = EmotionService.analyze_emotion(text)
            if crisis_result["level"] == "critical":
                score = 100
                factors.append({"type": "crisis_keyword", "detail": f"检测到高危词汇: {crisis_result.get('trigger', '')}"})
            elif crisis_result["level"] == "high":
                score = max(score, 55)
                factors.append({"type": "negative_keyword", "detail": f"检测到负面情绪词汇: {crisis_result.get('trigger', '')}"})
            elif emotion_result["valence"] == "negative":
                score = max(score, 35)
                factors.append({"type": "negative_text", "detail": "文本情绪偏负面"})

            # 【习惯-伙伴融合】自我否定表述（坚持不下来 / 我没用 …）：单独加权，
            # 这类话通常不是真的想伤害自己，而是被习惯压垮后的自责
            if HCS.detect_self_blame(text):
                score = max(score, 45)
                factors.append({"type": "self_blame", "detail": "出现自我否定表述，需要情绪接纳优先"})

        # 2. 语音情绪特征(声学代理: 前端上报)
        if voice_sentiment == "negative":
            add = 20
            # 低语速+负情绪 → 更高风险(声音低沉)
            if voice_speed is not None and voice_speed < 0.7:
                add += 8
                factors.append({"type": "voice_slow", "detail": "语速明显偏低"})
            score += add
            factors.append({"type": "voice_negative", "detail": "语音情绪特征偏负面"})
        elif voice_sentiment == "positive":
            score = max(0, score - 10)

        score = min(score, 100)

        return {
            "risk_level": MonitorService._level_from_score(score),
            "score": score,
            "emotion": emotion_result.get("emotion", "neutral"),
            "valence": emotion_result.get("valence", "neutral"),
            "factors": factors,
            "crisis_message": crisis_result.get("message", "") if crisis_result["level"] != "normal" else "",
        }

    @staticmethod
    def _level_from_score(score: int, sensitivity: str = "medium") -> str:
        thresholds = MonitorService.SENSITIVITY_THRESHOLDS.get(sensitivity, MonitorService.SENSITIVITY_THRESHOLDS["medium"])
        if score >= thresholds["critical"]:
            return "critical"
        if score >= thresholds["high"]:
            return "high"
        return "normal"

    @staticmethod
    def check_and_alert(db: Session, user_id: int, text: str = None,
                        voice_sentiment: str = None, voice_volume: float = None,
                        voice_speed: float = None, source: str = "text") -> Dict:
        """
        完整监测流程: 分析 → 连续负面加权 → 按隐私设置灵敏度定级 → 落库 → 生成告警
        返回: {risk_level, score, alert(弹窗数据|null), resources, log_id}
        """
        # 读取隐私设置(监测开关/灵敏度)
        privacy = db.query(UserPrivacySetting).filter(UserPrivacySetting.user_id == user_id).first()
        sensitivity = privacy.monitor_sensitivity if privacy else "medium"
        monitor_enabled = privacy.monitor_enabled if privacy is not None else True

        analysis = MonitorService.analyze_realtime(text, voice_sentiment, voice_volume, voice_speed)
        score = analysis["score"]

        # 监测关闭: 只返回分析不告警不落库
        if not monitor_enabled:
            return {**analysis, "alert": None, "resources": [], "log_id": 0, "monitor_enabled": False}

        # 3. 连续负面记录加权(最近24小时)
        since = datetime.now() - timedelta(hours=24)
        recent = db.query(EmotionMonitorLog).filter(
            EmotionMonitorLog.user_id == user_id,
            EmotionMonitorLog.created_at >= since,
            EmotionMonitorLog.risk_level != "normal",
        ).count()
        for threshold, extra in MonitorService.CONSECUTIVE_WEIGHTS:
            if recent >= threshold:
                score = min(score + extra, 100)
                analysis["factors"].append({"type": "consecutive_negative", "detail": f"24小时内已出现{recent}次异常情绪"})
                break

        risk_level = MonitorService._level_from_score(score, sensitivity)

        # 落库
        log = EmotionMonitorLog(
            user_id=user_id, source=source,
            emotion=analysis["emotion"], risk_level=risk_level, score=score,
            trigger_text=(text[:200] if text else None),
            action_taken="alert" if risk_level == "high" else ("modal" if risk_level == "critical" else "none"),
        )
        db.add(log)
        db.commit()
        db.refresh(log)

        # 生成告警(仅 high/critical)
        alert = None
        if risk_level in ("high", "critical"):
            # 推荐联系人
            contacts = db.query(CrisisContact).filter(
                CrisisContact.user_id == user_id,
                CrisisContact.notify_enabled == 1,
            ).order_by(CrisisContact.is_primary.desc()).all()
            alert = {
                "level": risk_level,
                "score": score,
                "message": analysis["crisis_message"] or CrisisService.COMFORT_TEXT,
                "contacts": [{"id": c.id, "name": c.name, "relation": c.relation, "phone": c.phone} for c in contacts],
                "hotlines": CrisisService.HOTLINES,
                "log_id": log.id,
            }

            # 【习惯-伙伴融合】自我否定：先接住情绪，再给「先停一停」的选项。
            # 明确禁止劝导咬牙硬坚持（规则写在 HCS.build_habit_relief_plan 里）
            if text and HCS.detect_self_blame(text):
                relief = HCS.build_habit_relief_plan(db, user_id)
                alert["message"] = relief["acknowledge"]
                alert["habit_relief"] = relief

        result = {
            "risk_level": risk_level, "score": score, "emotion": analysis["emotion"],
            "factors": analysis["factors"], "alert": alert,
            "resources": CrisisResourceService.recommend(db, risk_level, analysis["emotion"]),
            "log_id": log.id, "monitor_enabled": True,
        }

        # 自我否定与风险等级无关：哪怕没到告警线，也要给出「先停一停」的出口。
        # 只做情绪接纳与选项，不劝坚持、不打完成率的算盘。
        if text and HCS.detect_self_blame(text):
            result["self_blame"] = True
            result["habit_relief"] = HCS.build_habit_relief_plan(db, user_id)
        else:
            result["self_blame"] = False

        return result

    @staticmethod
    def get_history(db: Session, user_id: int, page: int = 1, page_size: int = 20) -> Dict:
        """情绪监测历史(分页+周期统计+趋势)"""
        query = db.query(EmotionMonitorLog).filter(EmotionMonitorLog.user_id == user_id)
        total = query.count()
        logs = query.order_by(EmotionMonitorLog.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        # 近30天趋势(按天聚合平均分)
        since = datetime.now() - timedelta(days=30)
        recent = db.query(EmotionMonitorLog).filter(
            EmotionMonitorLog.user_id == user_id,
            EmotionMonitorLog.created_at >= since,
        ).all()
        day_scores = {}
        for r in recent:
            ds = r.created_at.strftime("%Y-%m-%d")
            day_scores.setdefault(ds, []).append(r.score)
        trend_labels, trend_scores = [], []
        for i in range(29, -1, -1):
            ds = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            trend_labels.append(ds[5:])
            trend_scores.append(round(sum(day_scores[ds]) / len(day_scores[ds]), 1) if ds in day_scores else 0)

        # 周期统计
        stats = {
            "total": total,
            "high_count": sum(1 for r in recent if r.risk_level == "high"),
            "critical_count": sum(1 for r in recent if r.risk_level == "critical"),
            "normal_ratio": round(
                sum(1 for r in recent if r.risk_level == "normal") / max(len(recent), 1) * 100, 1
            ),
        }

        return {
            "list": [{
                "id": r.id, "source": r.source, "emotion": r.emotion,
                "risk_level": r.risk_level, "score": r.score,
                "trigger_text": (r.trigger_text[:50] + "...") if r.trigger_text and len(r.trigger_text) > 50 else (r.trigger_text or ""),
                "action_taken": r.action_taken, "resolved": r.resolved,
                "created_at": str(r.created_at),
            } for r in logs],
            "total": total, "page": page, "page_size": page_size,
            "trend": {"labels": trend_labels, "scores": trend_scores},
            "stats": stats,
        }

    @staticmethod
    def resolve_log(db: Session, user_id: int, log_id: int) -> bool:
        """标记某次异常已缓解"""
        log = db.query(EmotionMonitorLog).filter(
            EmotionMonitorLog.id == log_id, EmotionMonitorLog.user_id == user_id
        ).first()
        if not log:
            return False
        log.resolved = 1
        db.commit()
        return True


class CrisisResourceService:
    """心理资源推荐服务"""

    # 资源种子库(mock/初始化数据, DB为空时返回)
    SEED_RESOURCES = [
        {"id": 1, "type": "article", "title": "当你感到撑不下去时，可以试试这7个方法",
         "description": "心理学验证过的自我调节技巧，从呼吸练习到认知重构。", "url": "https://example.com/articles/7-ways",
         "cover_url": "", "tags": ["自我调节", "实用技巧"], "risk_level": "high", "sort": 1, "is_free": 1},
        {"id": 2, "type": "article", "title": "识别情绪信号：你的坏情绪在说什么",
         "description": "了解愤怒、焦虑、悲伤背后的真实需求，学会与情绪共处。", "url": "https://example.com/articles/emotion-signals",
         "cover_url": "", "tags": ["情绪认知"], "risk_level": "normal", "sort": 2, "is_free": 1},
        {"id": 3, "type": "video", "title": "5分钟正念呼吸引导（缓解急性焦虑）",
         "description": "跟随引导快速平复情绪，适合恐慌发作时使用。", "url": "https://example.com/videos/mindful-5min",
         "cover_url": "", "tags": ["正念", "焦虑"], "risk_level": "high", "sort": 1, "is_free": 1},
        {"id": 4, "type": "video", "title": "哈佛幸福课精选：我们为什么不快乐",
         "description": "积极心理学经典课程，理解幸福的科学。", "url": "https://example.com/videos/happiness",
         "cover_url": "", "tags": ["积极心理学"], "risk_level": "normal", "sort": 2, "is_free": 1},
        {"id": 5, "type": "book", "title": "《伯恩斯新情绪疗法》",
         "description": "认知行为疗法(CBT)自助经典，对抗抑郁与负面思维。", "url": "", "cover_url": "",
         "tags": ["CBT", "自助"], "risk_level": "high", "sort": 1, "is_free": 1},
        {"id": 6, "type": "book", "title": "《被讨厌的勇气》",
         "description": "阿德勒心理学入门，摆脱他人期待活出自我。", "url": "", "cover_url": "",
         "tags": ["阿德勒", "成长"], "risk_level": "normal", "sort": 2, "is_free": 1},
        {"id": 7, "type": "test", "title": "PHQ-9 抑郁自评量表",
         "description": "国际通用抑郁筛查量表，2分钟了解自己的情绪状态。", "url": "https://example.com/tests/phq9",
         "cover_url": "", "tags": ["抑郁", "自评"], "risk_level": "all", "sort": 1, "is_free": 1},
        {"id": 8, "type": "test", "title": "GAD-7 焦虑自评量表",
         "description": "广泛性焦虑筛查量表，评估近两周焦虑水平。", "url": "https://example.com/tests/gad7",
         "cover_url": "", "tags": ["焦虑", "自评"], "risk_level": "all", "sort": 2, "is_free": 1},
        {"id": 9, "type": "consult", "title": "在线心理咨询（壹心理）",
         "description": "专业心理咨询师在线服务，首次咨询有优惠。", "url": "https://example.com/consult",
         "cover_url": "", "tags": ["心理咨询"], "risk_level": "high", "sort": 1, "is_free": 0},
        {"id": 10, "type": "consult", "title": "简单心理 - 预约专业咨询师",
         "description": "严选心理咨询师，支持视频/语音/文字咨询。", "url": "https://example.com/consult2",
         "cover_url": "", "tags": ["心理咨询"], "risk_level": "all", "sort": 2, "is_free": 0},
    ]

    @staticmethod
    def get_resources(db: Session, res_type: str = "", risk_level: str = "") -> List[Dict]:
        """获取资源列表(优先DB, 空则种子库)"""
        query = db.query(CrisisResource).filter(CrisisResource.status == 1)
        if res_type:
            query = query.filter(CrisisResource.type == res_type)
        if risk_level and risk_level != "all":
            query = query.filter(CrisisResource.risk_level.in_([risk_level, "all"]))
        resources = query.order_by(CrisisResource.sort).all()
        if not resources:
            # DB未初始化, 返回种子数据
            result = CrisisResourceService.SEED_RESOURCES
            if res_type:
                result = [r for r in result if r["type"] == res_type]
            if risk_level and risk_level != "all":
                result = [r for r in result if r["risk_level"] in (risk_level, "all")]
            return result
        return [{
            "id": r.id, "type": r.type, "title": r.title, "description": r.description,
            "url": r.url, "cover_url": r.cover_url, "tags": r.tags or [],
            "risk_level": r.risk_level, "is_free": r.is_free,
        } for r in resources]

    @staticmethod
    def recommend(db: Session, risk_level: str, emotion: str) -> List[Dict]:
        """按风险等级推荐资源(告警时返回, 每类最多2条)"""
        resources = CrisisResourceService.get_resources(db, risk_level=risk_level)
        by_type = {}
        for r in resources:
            by_type.setdefault(r["type"], []).append(r)
        result = []
        for rtype in ("article", "video"):
            result.extend(by_type.get(rtype, [])[:1])
        if risk_level in ("high", "critical"):
            result.extend(by_type.get("consult", [])[:1])
            result.extend(by_type.get("test", [])[:1])
        return result


class CrisisGuideService:
    """危机应对指南内容库"""

    GUIDES = [
        {
            "id": 1, "level": "critical", "title": "当你有伤害自己的想法时",
            "steps": [
                "立即拨打24小时心理援助热线 400-161-9995，或联系信任的人陪伴你",
                "远离危险物品和环境，去有人、让你感到安全的地方",
                "尝试54321着陆技术：说出你看到的5样东西、听到的4种声音、触摸到的3样物品、闻到的2种气味、尝到的1种味道",
                "提醒自己：这种强烈的痛苦是暂时的，它会过去。你值得被帮助",
                "等情绪稍平稳后，联系心理咨询师进行专业评估",
            ],
        },
        {
            "id": 2, "level": "high", "title": "情绪崩溃时的急救步骤",
            "steps": [
                "停止正在做的事，找一个安静安全的地方坐下或躺下",
                "进行4-7-8呼吸：吸气4秒、屏息7秒、缓慢呼气8秒，重复4轮",
                "允许自己哭泣或发泄，不要压抑情绪",
                "给一位信任的家人或朋友发消息，哪怕只是说\"我现在很难受\"",
                "用温水洗脸或喝一杯温水，帮助身体从应激状态缓和下来",
            ],
        },
        {
            "id": 3, "level": "high", "title": "如何向家人朋友开口求助",
            "steps": [
                "不必\"铺垫完美\"，直接说\"我最近状态不太好，想和你聊聊\"就够了",
                "提前想好你需要的支持：是倾听陪伴、还是具体建议、或只是待在一起",
                "如果对方无法理解，这不是你的错，可以换一个人或寻求专业帮助",
                "求助是勇敢的表现，而不是软弱",
            ],
        },
        {
            "id": 4, "level": "normal", "title": "日常情绪保养指南",
            "steps": [
                "保持规律作息，睡眠对情绪的影响远超想象",
                "每天至少15分钟的运动或户外散步",
                "写日记或语音日记，给情绪一个出口",
                "每周留出\"无所事事\"的时间，允许自己放空",
                "与朋友保持真实连接，减少无意义刷手机",
            ],
        },
        {
            "id": 5, "level": "normal", "title": "识别身边人的求救信号",
            "steps": [
                "言语信号：说\"活着没意思\"\"我消失了大家会更好\"之类的话",
                "行为信号：突然送出珍爱物品、告别式言语、社交退缩、睡眠剧变",
                "发现信号时：认真倾听不打断、不评判，直接询问\"你是否有伤害自己的想法\"",
                "直接询问不会\"提醒\"对方自杀，反而能带来被理解的感受",
                "陪伴对方寻求专业帮助，危机时刻不离开TA",
            ],
        },
    ]

    @staticmethod
    def get_guides(level: str = "") -> List[Dict]:
        if level:
            return [g for g in CrisisGuideService.GUIDES if g["level"] == level or g["level"] == "normal"]
        return CrisisGuideService.GUIDES
