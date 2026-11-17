# -*- coding: utf-8 -*-
"""「专注」模块全链路冒烟测试
拆解→分步引导→番茄会话→统计→看板→计划→提醒→动态互关→陪伴聊天指令
"""
import sys, json, urllib.request, urllib.error

sys.stdout.reconfigure(encoding='utf-8')
BASE = 'http://127.0.0.1:8000'


def req(method, url, data=None, token=None):
    r = urllib.request.Request(BASE + url, method=method)
    r.add_header('Content-Type', 'application/json')
    if token:
        r.add_header('Authorization', 'Bearer ' + token)
    body = json.dumps(data).encode() if data is not None else None
    try:
        return json.loads(urllib.request.urlopen(r, body, timeout=60).read())
    except urllib.error.HTTPError as e:
        return {'HTTP_ERR': e.code, 'body': e.read().decode()[:300]}


results = []


def check(name, cond, detail=''):
    results.append((name, bool(cond), detail))
    print(('PASS' if cond else 'FAIL') + ' | ' + name + (' | ' + str(detail)[:180] if detail else ''))


def login(username):
    r = req('POST', '/api/v1/auth/login-username', {'username': username, 'password': 'test123456'})
    assert r['code'] == 200, r
    return r['data']['access_token'], r['data']['user']['id']


ta, ua = login('idea_test_a')
tb, ub = login('idea_test_b')

# 0. 角色 / 推荐 / 设置
rr = req('GET', '/api/v1/focus/roles', token=ta)
check('角色列表', rr.get('code') == 200 and len(rr['data']['list']) >= 7)
rc = req('GET', '/api/v1/focus/recommend', token=ta)
check('空态推荐', rc.get('code') == 200 and rc['data']['list'])
st0 = req('GET', '/api/v1/focus/setting', token=ta)
check('默认开关', st0.get('code') == 200 and st0['data']['allow_dynamic'])

# 1. 大任务拆解 → 引导记录
sp = req('POST', '/api/v1/focus/task/split', {'prompt': '复习高数第三章并做完课后题', 'mode': 'simple'}, ta)
check('大任务拆解', sp.get('code') == 200 and sp['data']['steps'], sp)
steps = sp['data']['steps']
rec_id = sp['data']['record_id']

# 2. 分步引导推进（完成第一步）
rd = req('GET', '/api/v1/focus/record/%d' % rec_id, token=ta)
check('引导记录详情', rd.get('code') == 200 and rd['data']['steps'])
sv = req('POST', '/api/v1/focus/record', {'record_id': rec_id, 'current_index': 2, 'duration_seconds': 300}, ta)
check('引导进度回写', sv.get('code') == 200)
rk = req('GET', '/api/v1/focus/records?keyword=' + urllib.request.quote('高数'), token=ta)
check('记录搜索', rk.get('code') == 200 and any(r['id'] == rec_id for r in rk['data']['list']))

# 3. 手动任务 + 看板 + 子步骤完成
tk = req('POST', '/api/v1/focus/task', {'title': '整理错题本', 'tag': '学习', 'est_minutes': 30}, ta)
check('手动建任务', tk.get('code') == 200, tk)
task_id = tk['data']['id']
bd = req('GET', '/api/v1/focus/tasks', token=ta)
check('今日看板', bd.get('code') == 200 and any(t['id'] == task_id for t in bd['data']['list']))

# 4. 番茄专注会话（开始→中断→结束）
ss = req('POST', '/api/v1/focus/session/start', {'task_id': task_id, 'role_id': 'mentor', 'mode': 'flow', 'tag': '学习'}, ta)
check('开启专注会话', ss.get('code') == 200 and ss['data']['session_id'], ss)
sid = ss['data']['session_id']
si = req('POST', '/api/v1/focus/session/interrupt', {'session_id': sid, 'count': 1}, ta)
check('离开检测回报', si.get('code') == 200 and si['data']['blacklist_trigger_count'] == 1)
sf = req('POST', '/api/v1/focus/session/finish', {'session_id': sid, 'duration': 1500, 'interrupted': True}, ta)
check('结束专注', sf.get('code') == 200 and sf['data']['duration_seconds'] == 1500, sf)

# 5. 统计
gs = req('GET', '/api/v1/focus/stat?period=day', token=ta)
check('统计-当日', gs.get('code') == 200 and gs['data']['total_minutes'] >= 25, gs['data'] if gs.get('code') == 200 else gs)
check('统计-角色排行', any(r['role_id'] == 'mentor' for r in gs['data']['role_rank']))
gw = req('GET', '/api/v1/focus/stat?period=week', token=ta)
check('统计-本周', gw.get('code') == 200)

# 6. 备考计划（AI 可能走 fallback，不强制）
gp = req('POST', '/api/v1/focus/plan/generate', {
    'exam_type': '期末数学', 'exam_date': '2026-12-20', 'weakness': '大题', 'daily_minutes': 45, 'remind_time': '19:30'}, ta)
check('备考计划生成', gp.get('code') == 200 and gp['data']['task_count'] > 0, gp)
check('计划提醒已挂', gp.get('code') == 200)
rm = req('GET', '/api/v1/focus/reminds', token=ta)
check('提醒列表', rm.get('code') == 200 and len(rm['data']['list']) > 0, rm['data'])

# 7. 陪伴聊天指令解析（AI 不可用时 cmd 为 None，接口必须不报错）
cc = req('POST', '/api/v1/focus/companion-chat', {'text': '提醒我九点四十五收拾房间', 'history': []}, ta)
check('陪伴聊天', cc.get('code') == 200 and cc['data'].get('reply'), cc)

# 8. 专注动态：A 发 follow 动态，B 互关后可见
fu = req('POST', '/api/v1/focus/follow/%d' % ub, token=ta)
check('A关注B', fu.get('code') == 200)
fu2 = req('POST', '/api/v1/focus/follow/%d' % ua, token=tb)
check('B关注A(互关成立)', fu2.get('code') == 200 and fu2['data']['mutual'])
dy = req('POST', '/api/v1/focus/dynamic', {'content': '今天专注了 25 分钟，感觉不错', 'visible_type': 'follow'}, ta)
check('A发动态(互关可见)', dy.get('code') == 200 and dy['data']['comments'], dy)
dy_self = req('POST', '/api/v1/focus/dynamic', {'content': '仅自己可见的小记', 'visible_type': 'self'}, ta)
check('A发动态(仅自己)', dy_self.get('code') == 200)
db_b = req('GET', '/api/v1/focus/dynamics', token=tb)
check('B能看到A的follow动态', any(d['id'] == dy['data']['id'] for d in db_b['data']['list']))
check('B看不到A的self动态', all(d['id'] != dy_self['data']['id'] for d in db_b['data']['list']))
lk = req('POST', '/api/v1/focus/dynamic/%d/react' % dy['data']['id'], token=tb)
check('B点赞', lk.get('code') == 200 and lk['data']['liked'])
lk2 = req('POST', '/api/v1/focus/dynamic/%d/react' % dy['data']['id'], token=tb)
check('点赞幂等取消', lk2.get('code') == 200 and not lk2['data']['liked'])

# 9. 开关关闭动态
st = req('POST', '/api/v1/focus/setting', {'allow_dynamic': False}, tb)
check('B关闭动态开关', st.get('code') == 200 and not st['data']['allow_dynamic'])
dy_b = req('POST', '/api/v1/focus/dynamic', {'content': 'x', 'visible_type': 'self'}, tb)
check('关闭后发布被拦截', dy_b.get('code') == 400)
req('POST', '/api/v1/focus/setting', {'allow_dynamic': True}, tb)

# 10. 删除级联
dl = req('DELETE', '/api/v1/focus/task/%d' % task_id, token=ta)
check('删除任务', dl.get('code') == 200)
bd2 = req('GET', '/api/v1/focus/tasks', token=ta)
check('删除后看板无该任务', all(t['id'] != task_id for t in bd2['data']['list']))

print('\n===== SUMMARY =====')
fails = [r for r in results if not r[1]]
print('total=%d pass=%d fail=%d' % (len(results), len(results) - len(fails), len(fails)))
for n, _, d in fails:
    print('FAILED:', n, str(d)[:200])
