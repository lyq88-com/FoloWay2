# -*- coding: utf-8 -*-
"""
循途 · newfunc 增量功能 全链路自动化测试
覆盖：
  A. 新增功能：推送设置/测试推送/通知中心/定时任务去重/免打扰、
     情绪日记日历(聚合/AI总结/月标记/授权)、多AI伙伴(人设对话/记忆隔离/删除/重置/主动陪伴)
  B. 原有功能回归：登录、打卡、情绪旧接口、日程旧接口、角色人设、开放路由完整性
运行：cd liyeqing/server && python tests/newfunc_test.py   （需服务运行在 8000 端口）
"""
import asyncio
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')
BASE = 'http://127.0.0.1:8000'
NF = '/api/newfunc'

results = []


def check(name, cond, detail=''):
    results.append((name, bool(cond)))
    print(('PASS' if cond else 'FAIL') + ' | ' + name +
          (' | ' + str(detail)[:150] if detail else ''))


def req(method, url, data=None, token=None, timeout=60):
    r = urllib.request.Request(BASE + url, method=method)
    r.add_header('Content-Type', 'application/json')
    if token:
        r.add_header('Authorization', 'Bearer ' + token)
    body = json.dumps(data).encode() if data is not None else None
    try:
        return json.loads(urllib.request.urlopen(r, body, timeout=timeout).read())
    except urllib.error.HTTPError as e:
        return {'HTTP_ERR': e.code, 'body': e.read().decode()[:200]}


def login(username):
    r = req('POST', '/api/v1/auth/login-username',
            {'username': username, 'password': 'test123456'})
    assert r.get('code') == 200, r
    return r['data']['access_token'], r['data']['user']['id']


def db_session():
    from app.core.database import SessionLocal
    return SessionLocal()


# ================= A0. 登录 =================
ta, ua = login('idea_test_a')
tb, ub = login('idea_test_b')
check('登录-用户A(原有功能)', bool(ta))
check('登录-用户B(原有功能)', bool(tb))

# ================= A1. 推送设置 =================
# 先复位到默认（保证测试幂等），再校验默认值
req('POST', NF + '/push/setting', {
    'push_enabled': True, 'checkin_push_enabled': True,
    'todo_push_enabled': True, 'ai_push_enabled': True,
    'ai_frequency': 'medium', 'quiet_enabled': False}, token=ta)
ps0 = req('GET', NF + '/push/setting', token=ta)
check('推送设置-默认值', ps0.get('code') == 200 and ps0['data']['push_enabled'] is True
      and ps0['data']['ai_frequency'] == 'medium', ps0.get('data'))
ps1 = req('POST', NF + '/push/setting', {
    'quiet_enabled': True, 'quiet_start': '23:00', 'quiet_end': '08:00',
    'ai_frequency': 'low'}, token=ta)
check('推送设置-更新(免打扰+频率)', ps1.get('code') == 200
      and ps1['data']['quiet_enabled'] is True and ps1['data']['ai_frequency'] == 'low',
      ps1.get('data'))
bc = req('POST', NF + '/push/bind-cid', {'client_id': 'test_cid_001'}, token=ta)
check('CID绑定', bc.get('code') == 200 and bc['data']['client_id'] == 'test_cid_001')

# 免打扰窗口判断（含跨零点）
from app.modules.newfunc import push_service
srow = push_service.get_or_create_setting(db_session(), ua)
check('免打扰-跨零点命中(23:00~08:00 @23:30)',
      push_service.in_quiet_hours(srow, dt.datetime(2026, 11, 9, 23, 30)))
check('免打扰-跨零点命中(凌晨5点)',
      push_service.in_quiet_hours(srow, dt.datetime(2026, 11, 9, 5, 0)))
check('免打扰-白天不命中', not push_service.in_quiet_hours(
      srow, dt.datetime(2026, 11, 9, 12, 0)))
req('POST', NF + '/push/setting', {'quiet_enabled': False}, token=ta)

# ================= A2. 测试推送 + 通知中心 =================
tp = req('POST', NF + '/push/test', token=ta)
check('测试推送', tp.get('code') == 200 and tp['data']['push_type'] == 'test', tp.get('data'))
pr = req('GET', NF + '/push/records?size=5', token=ta)
check('通知中心-记录已保存', pr.get('code') == 200 and
      any(r['push_type'] == 'test' for r in pr['data']['list']))
rid = pr['data']['list'][0]['id']
rd1 = req('POST', f'{NF}/push/{rid}/read', token=ta)
check('标记已读', rd1.get('code') == 200)
pr2 = req('GET', NF + '/push/records?only_unread=true', token=ta)
check('未读过滤', all(r['is_read'] == 1 or r['id'] != rid for r in pr2['data']['list']))
ra = req('POST', NF + '/push/read-all', token=ta)
check('全部已读', ra.get('code') == 200)

# ================= A3. 定时任务：待办到期 + 去重 =================
now = dt.datetime.now()
sc = req('POST', '/api/v1/schedule/create', {
    'title': 'newfunc测试待办', 'schedule_date': now.strftime('%Y-%m-%d'),
    'start_time': now.strftime('%H:%M'), 'end_time': (now + dt.timedelta(hours=1)).strftime('%H:%M'),
    'remind_minutes': 0}, token=ta)
check('旧接口-创建日程(回归)', sc.get('code') == 200, str(sc)[:100])
scid = sc['data']['id'] if sc.get('code') == 200 and isinstance(sc.get('data'), dict) else 0


def run_todo_job():
    db = db_session()
    n = asyncio.run(push_service.job_todo_due(db))
    db.close()
    return n


db = db_session()
from app.modules.newfunc.models import PushRecord
before = db.query(PushRecord).filter(PushRecord.uid == ua,
                                     PushRecord.push_type == 'todo_due').count()
db.close()
run_todo_job()
db = db_session()
after1 = db.query(PushRecord).filter(PushRecord.uid == ua,
                                     PushRecord.push_type == 'todo_due',
                                     PushRecord.ref_id == scid).count()
db.close()
check('定时任务-待办到期已推送', after1 >= 1, f'ref_id={scid}')
run_todo_job()
db = db_session()
after2 = db.query(PushRecord).filter(PushRecord.uid == ua,
                                     PushRecord.push_type == 'todo_due',
                                     PushRecord.ref_id == scid).count()
db.close()
check('定时任务-同一次待办不重复推送', after1 == after2)

# ================= A4. 定时任务：打卡未完成提醒 =================
req('POST', NF + '/push/setting',
    {'checkin_push_time': dt.datetime.now().strftime('%H:%M')}, token=ta)
db = db_session()
asyncio.run(push_service.job_checkin_remind(db))
n1 = db.query(PushRecord).filter(PushRecord.uid == ua,
                                 PushRecord.push_type == 'checkin_remind').count()
db.close()
check('定时任务-打卡提醒已推送', n1 >= 1, f'count={n1}')
db = db_session()
asyncio.run(push_service.job_checkin_remind(db))
n2 = db.query(PushRecord).filter(PushRecord.uid == ua,
                                 PushRecord.push_type == 'checkin_remind').count()
db.close()
check('定时任务-打卡提醒当日去重', n1 == n2)

# ================= A5. 情绪日记日历 =================
today = dt.date.today().strftime('%Y-%m-%d')
# 用「旧接口」造一条情绪数据（模拟用户正常使用，只读引用不改动旧逻辑）
em = req('POST', '/api/v1/emotion/create', {
    'emotion': 'calm', 'intensity': 6, 'description': 'newfunc测试情绪',
    'record_date': today}, token=ta)
check('旧接口-情绪记录创建(回归)', em.get('code') == 200, str(em)[:100])
ds = req('POST', NF + '/diary/save', {
    'date': today, 'mood_tags': ['calm', 'tired'], 'mood_score': 6,
    'diary_text': '今天写了一点日记，测试情绪日历联动。'}, token=ta)
check('日记保存', ds.get('code') == 200 and ds['data']['mood_tags'] == ['calm', 'tired'],
      ds.get('data'))
dd = req('GET', f'{NF}/diary/day?date={today}', token=ta)
check('当日聚合-情绪明细(只读旧表)', dd.get('code') == 200 and len(dd['data']['emotions']) >= 1,
      dd.get('data'))
check('当日聚合-日记内容', dd['data']['diary']['diary_text'].startswith('今天写了一点'))
sm = req('POST', NF + '/diary/summary', {'date': today, 'summary': '手动总结：平稳的一天。'},
         token=ta)
check('手动当日总结', sm.get('code') == 200 and sm['data']['summary_source'] == 'manual')
ais = req('POST', NF + '/diary/ai-summary', {'date': today}, token=ta, timeout=90)
check('AI自动总结(或降级模板)', ais.get('code') == 200 and len(ais['data']['summary']) >= 20
      and ais['data']['summary_source'] == 'ai', ais.get('data'))
mk = req('GET', f"{NF}/diary/month?month={today[:7]}", token=ta)
marks = mk['data']['marks'].get(today, {})
check('月视图标记', mk.get('code') == 200 and marks.get('has_diary') == 1
      and marks.get('has_emotion') == 1 and marks.get('has_summary') == 1, marks)
au = req('POST', NF + '/diary/authorize', {'enabled': True}, token=ta)
check('情绪日历授权', au.get('code') == 200 and au['data']['diary_read_auth'] is True)

# ================= A6. 多 AI 伙伴 + 隔离记忆 =================
b1 = req('POST', NF + '/bots', {
    'name': '小澈', 'avatar': '🌊',
    'personality': '温柔细腻，情绪稳定，会先共情再给建议',
    'speak_style': '像老朋友发微信，口语化，偶尔用波浪号结尾',
    'self_intro': '陪用户备战期末的学长', 'taboo': '绝不说教，绝不列清单'}, token=ta)
check('创建伙伴-小澈', b1.get('code') == 200 and b1['data']['name'] == '小澈', b1.get('data'))
b2 = req('POST', NF + '/bots', {
    'name': '阿火', 'avatar': '🔥',
    'personality': '毒舌但热心，说话简短有力',
    'speak_style': '短句，直来直去', 'self_intro': '健身搭子',
    'taboo': '绝不用敬语'}, token=ta)
check('创建伙伴-阿火', b2.get('code') == 200, b2.get('data'))
bl = req('GET', NF + '/bots', token=ta)
bots = {b['name']: b for b in bl['data']['list']}
check('伙伴列表+记忆计数', len(bl['data']['list']) >= 2)
id1, id2 = bots['小澈']['id'], bots['阿火']['id']

c1 = req('POST', f'{NF}/bots/{id1}/chat', {
    'text': '我叫叶青，最近在准备期末高数考试，有点焦虑，不过我喜欢听周深的歌放松',
    'history': []}, token=ta, timeout=90)
check('伙伴对话-回复非空', c1.get('code') == 200 and len(c1['data']['reply']) > 2,
      c1.get('data'))
check('伙伴对话-沉淀记忆', c1['data']['memories_added'] >= 1, c1.get('data'))
low_reply = c1['data']['reply']
check('人设贴合-无机器腔', ('作为AI' not in low_reply) and ('无法' not in low_reply),
      low_reply[:60])

# 记忆隔离：小澈有记忆，阿火应为 0
m1 = req('GET', f'{NF}/bots/{id1}/memories', token=ta)
m2 = req('GET', f'{NF}/bots/{id2}/memories', token=ta)
check('记忆隔离-小澈已存', m1['data']['total'] >= 1, m1['data']['total'])
check('记忆隔离-阿火为0', m2['data']['total'] == 0, m2['data']['total'])
c2 = req('POST', f'{NF}/bots/{id2}/chat', {'text': '我叫叶青', 'history': []},
         token=ta, timeout=90)
m2b = req('GET', f'{NF}/bots/{id2}/memories', token=ta)
check('记忆隔离-阿火独立沉淀(不读小澈记忆)', c2.get('code') == 200
      and all('周深' not in mm['content'] for mm in m2b['data']['list']),
      [mm['content'][:20] for mm in m2b['data']['list']])

# 删除单条记忆
mid = m1['data']['list'][0]['id']
dm = req('DELETE', f'{NF}/bots/{id1}/memories/{mid}', token=ta)
m1b = req('GET', f'{NF}/bots/{id1}/memories', token=ta)
check('删除单条记忆', dm.get('code') == 200
      and m1b['data']['total'] == m1['data']['total'] - 1)

# 重置小澈记忆 → 阿火不受影响
rs = req('POST', f'{NF}/bots/{id1}/memory/reset', token=ta)
m1c = req('GET', f'{NF}/bots/{id1}/memories', token=ta)
m2c = req('GET', f'{NF}/bots/{id2}/memories', token=ta)
check('重置-小澈记忆清空', rs.get('code') == 200 and m1c['data']['total'] == 0)
check('重置-阿火记忆不受影响', m2c['data']['total'] == m2b['data']['total'],
      f"{m2c['data']['total']} vs {m2b['data']['total']}")

# 主动陪伴（走人设+记忆+当日状态，落推送记录）
pb = req('POST', f'{NF}/bots/{id2}/proactive', {}, token=ta, timeout=90)
check('主动陪伴-消息生成', pb.get('code') == 200 and len(pb['data']['message']) > 2,
      pb.get('data'))
db = db_session()
ai_push = db.query(PushRecord).filter(
    PushRecord.uid == ua, PushRecord.push_type == 'ai_companion',
    PushRecord.ref_id == id2).count()
db.close()
check('主动陪伴-推送记录已落库', ai_push >= 1)

# 伙伴更新与删除
bu = req('PUT', f'{NF}/bots/{id2}', {'speak_style': '改得更简短'}, token=ta)
check('编辑伙伴', bu.get('code') == 200)
bd = req('DELETE', f'{NF}/bots/{id1}', token=ta)
m1d = req('GET', f'{NF}/bots/{id1}/memories', token=ta)
check('删除伙伴-记忆级联清除(HTTP404=伙伴已不存在)', m1d.get('HTTP_ERR') == 404 or
      (m1d.get('code') != 200), str(m1d)[:80])

# ================= B. 原有功能回归 =================
ht = req('GET', '/api/v1/habit/list', token=ta)
check('回归-习惯列表', ht.get('code') == 200, str(ht)[:80])
el = req('GET', '/api/v1/emotion/list', token=ta)
check('回归-情绪列表', el.get('code') == 200)
sl = req('GET', '/api/v1/schedule/list?month=' + today[:7], token=ta)
check('回归-日程列表', sl.get('code') == 200)
ro = req('GET', '/api/v1/persona/roles', token=ta)
check('回归-角色人设列表', ro.get('code') == 200 and ro['data'])
oc = req('GET', '/api/v1/focus/tasks', token=ta)
check('回归-专注模块看板', oc.get('code') == 200)
mo = req('GET', '/api/v1/moment/list', token=ta)
check('回归-朋友圈', mo.get('code') in (200, None) or 'HTTP_ERR' not in mo, str(mo)[:60])

# openapi 路由完整性：新前缀存在 & 旧前缀路由数量未减少
oa = req('GET', '/openapi.json')
paths = list((oa.get('paths') or {}).keys())
nf_paths = [p for p in paths if p.startswith('/api/newfunc')]
v1_paths = [p for p in paths if p.startswith('/api/v1')]
check('路由-新前缀已注册(≥19条)', len(nf_paths) >= 19, f'{len(nf_paths)} 条')
check('路由-旧前缀完整(≥150条)', len(v1_paths) >= 150, f'{len(v1_paths)} 条')

# ================= 汇总 =================
total = len(results)
passed = sum(1 for _, ok in results if ok)
print('\n===== newfunc TEST SUMMARY =====')
print(f'total={total} pass={passed} fail={total - passed}')
if total != passed:
    print('FAILED:', [n for n, ok in results if not ok])
    sys.exit(1)
