# -*- coding: utf-8 -*-
"""小想法·共鸣匹配 全链路冒烟测试
发布 -> 共鸣匹配 -> 点亮 -> 双向点亮 -> 私聊 -> 通知/徽章
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
        return json.loads(urllib.request.urlopen(r, body, timeout=15).read())
    except urllib.error.HTTPError as e:
        return {'HTTP_ERR': e.code, 'body': e.read().decode()[:300]}


def login(username):
    r = req('POST', '/api/v1/auth/login-username',
            {'username': username, 'password': 'test123456'})
    assert r['code'] == 200, r
    return r['data']['access_token'], r['data']['user']['id']


results = []


def check(name, cond, detail=''):
    results.append((name, bool(cond), detail))
    print(('PASS' if cond else 'FAIL') + ' | ' + name + (' | ' + str(detail)[:200] if detail else ''))


ta, ua = login('idea_test_a')
tb, ub = login('idea_test_b')

# 1. A 发布匿名想法（孤独/疲惫主题）
p1 = req('POST', '/api/v1/idea/publish', {
    'content': '最近加班太累了，一个人在大城市打拼，感觉特别孤独，好想有人陪陪我',
    'is_anonymous': True}, ta)
check('A发布想法', p1.get('code') == 200, p1)
idea_a_id = (p1.get('data') or {}).get('id') or (p1.get('data') or {}).get('idea', {}).get('id')

# 2. B 发布语义相近想法（应与 A 的匹配上）
p2 = req('POST', '/api/v1/idea/publish', {
    'content': '今天下班回家只有自己一个人，加班后独自吃饭好累好孤独啊',
    'is_anonymous': True}, tb)
check('B发布想法', p2.get('code') == 200, p2)

# 3. A 查我的共鸣 —— 应看到 B 的想法（匿名，未点亮不暴露身份）
mr = req('GET', '/api/v1/idea/my-resonance', token=ta)
check('A查看共鸣列表', mr.get('code') == 200, mr)
items = (mr.get('data') or {}).get('list') or (mr.get('data') or {}).get('items') or []
check('A匹配到B的共鸣', len(items) > 0, 'matched=%d' % len(items))
if items:
    it = items[0]
    print('    共鸣条目字段:', json.dumps(it, ensure_ascii=False)[:300])
    # 隐私红线：未双向点亮时不暴露对方身份
    other_str = json.dumps(it, ensure_ascii=False)
    check('未点亮不暴露身份(无nickname/user_id)', ('idea_test_b' not in other_str))

    # 4. A 点亮 B 的共鸣记录
    rid = it.get('resonance_id')
    li = req('POST', '/api/v1/idea/light', {'resonance_id': rid}, ta)
    check('A点亮共鸣', li.get('code') == 200, li)

# 5. B 查看共鸣，A 点亮后 B 应看到（匿名内容，A 尚未点亮则 B 仍看不到身份；点亮后应可看到）
mrb = req('GET', '/api/v1/idea/my-resonance', token=tb)
check('B查看共鸣列表', mrb.get('code') == 200, mrb)
items_b = (mrb.get('data') or {}).get('list') or (mrb.get('data') or {}).get('items') or []
print('    B侧共鸣条目:', json.dumps(items_b[0], ensure_ascii=False)[:300] if items_b else 'EMPTY')

# 6. B 点亮回流 -> 双向 matched, 应产生会话
if items_b:
    li2 = req('POST', '/api/v1/idea/light', {'resonance_id': items_b[0].get('resonance_id')}, tb)
    check('B点亮共鸣(双向)', li2.get('code') == 200, li2)
    print('    双向点亮返回:', json.dumps(li2.get('data'), ensure_ascii=False)[:300])

# 7. A 再查共鸣 —— 双向点亮后应有 conversation_id 且暴露身份
mr2 = req('GET', '/api/v1/idea/my-resonance', token=ta)
items2 = (mr2.get('data') or {}).get('list') or []
conv_id = None
for it2 in items2:
    print('    A侧点亮后条目:', json.dumps(it2, ensure_ascii=False)[:300])
    if it2.get('conversation_id'):
        conv_id = it2['conversation_id']
check('双向点亮后产生会话ID', conv_id is not None)

# 8. A 的会话列表
cl = req('GET', '/api/v1/idea/conversations', token=ta)
check('A查会话列表', cl.get('code') == 200, cl)
if conv_id is None and cl.get('data'):
    lst = cl['data'].get('list') or cl['data']
    if isinstance(lst, list) and lst:
        conv_id = lst[0].get('id')

# 9. 私聊：A 发消息
sm = req('POST', '/api/v1/idea/conversation/%s' % conv_id,
         {'content': '你好呀，我也是一个人在这座城市，抱抱', 'msg_type': 'text'}, ta)
check('A发私聊消息', sm.get('code') == 200, sm)

# 10. B 读消息并回复
gm = req('GET', '/api/v1/idea/conversation/%s' % conv_id, token=tb)
check('B读会话消息', gm.get('code') == 200, gm)
print('    会话详情:', json.dumps(gm.get('data'), ensure_ascii=False)[:400])
sm2 = req('POST', '/api/v1/idea/conversation/%s' % conv_id,
          {'content': '谢谢你，看到你说话就好开心，击掌！', 'msg_type': 'text'}, tb)
check('B回复消息', sm2.get('code') == 200, sm2)

# 11. 轻互动
mr3 = req('GET', '/api/v1/idea/my-resonance', token=tb)
items3 = (mr3.get('data') or {}).get('list') or []
if items3:
    ra = req('POST', '/api/v1/idea/react', {
        'idea_id': (items3[0].get('idea') or {}).get('id'), 'action_type': 'highfive'}, tb)
    check('轻互动(击掌)', ra.get('code') == 200, ra)

# 12. 徽章 & 通知
bd = req('GET', '/api/v1/idea/badge', token=ta)
check('A查徽章', bd.get('code') == 200, bd)
nt = req('GET', '/api/v1/idea/notifications', token=ta)
check('A查通知', nt.get('code') == 200, nt)

# 13. 我的想法列表
mi = req('GET', '/api/v1/idea/my-ideas', token=ta)
check('A查我的想法', mi.get('code') == 200, mi)

print('\n===== SUMMARY =====')
fails = [r for r in results if not r[1]]
print('total=%d pass=%d fail=%d' % (len(results), len(results) - len(fails), len(fails)))
for n, _, d in fails:
    print('FAILED:', n, str(d)[:200])
