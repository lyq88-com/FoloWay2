# 循途APP · AI聊天功能 排错清单 & 完整操作手册

> 适用：`server-flask/ai_server.py`（Flask + 智谱 glm-4-flash）+ `frontend/pages/ai-chat/ai-chat.vue`
> 电脑局域网 IP 以 `ipconfig` 查询结果为准（当前：172.20.10.3）

---

## 一、排错清单（常见报错 → 原因 → 解决）

### ① 401 鉴权失败（密钥错误）

**现象**：前端收到「我这边出了点小问题…（提示：请检查 ai_server.py 里的 API_KEY 是否已替换成你的密钥）」；后端控制台打印 `[ai_server] 智谱接口 HTTP 错误 401`。

| 检查项 | 操作 |
|---|---|
| API_KEY 还是占位符 | 打开 `ai_server.py`，把 `API_KEY = "这里替换成你的智谱API-Key"` 换成真实 Key |
| Key 复制时带了空格/引号 | 粘贴后检查首尾，Key 是一串字母数字（含`.`），不带引号、不带 `Bearer` 前缀 |
| Key 已失效/被删 | 去 https://open.bigmodel.cn → 右上角头像 → API Keys，确认 Key 存在，必要时重新生成 |
| 改完没重启后端 | 改代码后必须 `Ctrl+C` 停掉再 `python ai_server.py` 重启 |

**验证密钥是否有效（电脑上直接跑）**：

```bash
python -c "import requests;r=requests.post('https://open.bigmodel.cn/api/paas/v4/chat/completions',json={'model':'glm-4-flash','messages':[{'role':'user','content':'hi'}]},headers={'Authorization':'Bearer 你的Key'},timeout=15);print(r.status_code);print(r.text[:200])"
```

- 返回 `200` + `choices` → Key 没问题，问题在 ai_server.py 的配置
- 返回 `401` → Key 本身错了，去平台重新生成

---

### ② 429 限流（免费接口频率限制）

**现象**：后端控制台打印 `HTTP 错误 429`；前端收到「调用太频繁了，稍等一会再试」。

| 检查项 | 操作 |
|---|---|
| 短时间连发多条消息 | glm-4-flash 免费档有并发/频率限制，等几秒再发 |
| 前端重复触发请求 | 本页面已做防重（sending 状态锁），若自己改过代码注意别把锁去掉 |
| 后端被别的程序循环调用 | 检查是否有其他脚本/浏览器标签页在循环请求 |
| 需要正式上限 | 智谱平台充值/升级套餐（免费开发够用，压测才需要） |

---

### ③ 手机访问不到后端（真机最大坑，按顺序排查）

**现象**：真机上聊天一直转圈/提示「连接不上后端」；H5 浏览器（电脑）却一切正常。

**排查命令（电脑上跑，确认后端活着）**：

```bash
python -c "import requests;print(requests.get('http://172.20.10.3:5001/ai/health',timeout=5).text)"
```

```text
按顺序检查这 5 项，命中 90% 的情况：
```

| 序 | 检查项 | 怎么查 | 解决 |
|---|---|---|---|
| 1 | **IP 写错** | 电脑 `ipconfig` 看「无线局域网适配器 WLAN」的 IPv4 地址 | 打开 `ai-chat.vue`，把 `AI_BASE_URL` 的 IP 换成查询结果（**不要写 127.0.0.1，真机上它指手机自己**） |
| 2 | **不在同一 WiFi** | 手机 WiFi 设置里看连接的 SSID 和电脑是否同一个 | 连同一个 WiFi。⚠️ 校园网/公共 WiFi 常开启「AP 隔离」，设备间互相不通——换成手机开热点、电脑连热点最稳 |
| 3 | **后端没启动** | 电脑任务管理器里有没有 python.exe；浏览器开 `http://127.0.0.1:5001/ai/health` | `cd liyeqing\server-flask` → `python ai_server.py` |
| 4 | **Windows 防火墙拦截**（最高频） | 后端在电脑本机通、手机就是连不上 | 控制面板 → Windows Defender 防火墙 → 高级设置 → 入站规则 → 新建规则 → 端口 → TCP 5001 → 允许连接。或首次启动 python 弹防火墙弹窗时勾选「专用+公用网络」点允许 |
| 5 | **后端没监听 0.0.0.0** | ai_server.py 启动日志是否 `Running on http://0.0.0.0:5001` | ai_server.py 默认已配好；若自己改过 host 改回 `0.0.0.0`（不能是 127.0.0.1） |

**手机侧快速验证**（不经APP直接测网络）：手机浏览器地址栏输入 `http://172.20.10.3:5001/ai/health`，能看到 `{"status":"ok",...}` 说明网络层全通，剩下的只可能是 `ai-chat.vue` 里的 IP 没改对。

---

### ④ 模型名称写错导致调用失败

**现象**：后端控制台打印 HTTP 错误（常见 400/404），返回体含 `model not found` / `模型不存在`。

| 检查项 | 操作 |
|---|---|
| 模型名拼错 | `ai_server.py` 里 `MODEL = "glm-4-flash"`——注意是**短横线 `-`**，不是下划线；`flash` 不是 `free` |
| 常见错误写法 | ~~`glm_4_flash`~~、~~`glm-4-Flash`~~、~~`glm4flash`~~、~~`chatglm-4-flash`~~ |
| 抄了别的模型名 | 免费档当前用 `glm-4-flash`；若平台调整，去智谱「模型广场」查该模型的准确英文名 |
| 改完没重启 | 同 ①，改配置必须重启后端 |

**单独验证模型名（电脑上跑）**：把下面命令的 `你的Key` 换掉：

```bash
python -c "import requests;r=requests.post('https://open.bigmodel.cn/api/paas/v4/chat/completions',json={'model':'glm-4-flash','messages':[{'role':'user','content':'hi'}]},headers={'Authorization':'Bearer 你的Key'},timeout=15);print(r.status_code,r.text[:200])"
```

返回 200 即模型名正确。

---

### 附：错误现象速查表

| 现象 | 最可能原因 | 跳转 |
|---|---|---|
| 回复内容是「请把 API_KEY 替换成你的智谱密钥」 | 密钥没填/没重启 | ① |
| 回复内容是「调用太频繁」 | 限流 | ② |
| 电脑H5正常、手机真机转圈 | IP/防火墙/WiFi隔离 | ③ |
| 回复内容是「我没听懂刚才的回复」 | 智谱返回异常，先看后端控制台日志 | ①④ |
| 提示「请求超时」 | 网络慢或大模型拥堵，稍等重试 | ② |
| H5 页面连不上（电脑浏览器也不行） | dev server 没重启（改过代理配置） | 步骤四·3 |

---

## 二、完整操作步骤（从后端到真机）

### 步骤一：启动 Flask 后端

```bash
# 1. 装依赖（只需一次）
pip install flask requests

# 2. 填密钥：用编辑器打开 ai_server.py，改这一行
#    API_KEY = "这里替换成你的智谱API-Key"  →  API_KEY = "你的真实Key"

# 3. 启动（Windows 在项目目录开 cmd/终端）
cd C:\Users\小青\Desktop\新建文件夹\liyeqing\server-flask
python ai_server.py
```

看到 `Running on http://0.0.0.0:5001` 即启动成功。**这个窗口保持开着，关掉窗口=后端下线。**

### 步骤二：本地测试接口（电脑上）

```bash
# 健康检查（确认服务活着 + 密钥是否已配置）
curl http://127.0.0.1:5001/ai/health
# 期望: {"api_key_configured":true,"model":"glm-4-flash","status":"ok"}

# 聊天接口
curl -X POST http://127.0.0.1:5001/ai/chat -H "Content-Type: application/json" -d "{\"message\":\"今天打卡成功了！\"}"
# 期望: {"reply":"哇，太棒了！..."}
```

不想用 curl 就用 Python：

```bash
python -c "import requests;print(requests.post('http://127.0.0.1:5001/ai/chat',json={'message':'你好呀'},timeout=60).json())"
```

**测试通过的标准**：`reply` 是一句自然的中文回复（不是「还没配置好」之类的提示语）。

### 步骤三：查电脑局域网 IP（真机要用）

```bash
ipconfig
```

找「无线局域网适配器 WLAN」→「IPv4 地址」，例如 `172.20.10.3`。

### 步骤四：运行 uniapp 前端

1. **改 IP**：打开 `frontend/pages/ai-chat/ai-chat.vue`，找到 `AI_BASE_URL`，确认 App 分支写的是上一步查到的 IP：
   `const AI_BASE_URL = 'http://172.20.10.3:5001'`（换过 WiFi 就要重查重改）。
2. **HBuilderX 运行 H5**（电脑浏览器调试用，走代理不用 IP）：打开 HBuilderX → 选中 `frontend` 项目 → 运行 → 运行到浏览器。
3. ⚠️ **改过 vite.config.js / manifest.json 代理配置后，必须先停掉旧的 dev server 再重新运行**，否则新代理不生效。
4. H5 页面地址栏追加 `#/pages/ai-chat/ai-chat` 即进入聊天页。

### 步骤五：真机调试（手机）

1. **同一网络**：手机和电脑连同一个 WiFi（或手机开热点、电脑连这个热点）。
2. **手机先验网络**：手机浏览器输入 `http://172.20.10.3:5001/ai/health`，能看到 JSON 就说明通了；看不到 → 回到排错清单③（防火墙/AP隔离）。
3. **HBuilderX 真机运行**：手机开启 USB 调试（设置→开发者选项→USB调试）→ USB 连电脑 → HBuilderX → 运行 → 运行到手机或模拟器 → 运行到 Android App 基座。
4. 首次真机运行，HBuilderX 会自动给手机装基座 APP，等它装完自动打开。
5. 在 APP 里进入 AI 聊天页（地址 `pages/ai-chat/ai-chat`），发一条消息验证。

### 步骤六：日常开发流程（记住这个顺序）

```text
① python ai_server.py（后端窗口常开）
② HBuilderX 运行前端（H5 调试用浏览器；真机用数据线）
③ 测试：先 H5 后真机
④ 每次改了 ai_server.py → Ctrl+C 重启后端
   每次改了代理配置     → 重启 dev server
   每次换了 WiFi/IP     → ipconfig 重查 IP + 改 ai-chat.vue
```

---

## 三、安全红线（再强调一次）

- **智谱 API Key 只存在后端 `ai_server.py`**，前端代码、pages、打包出来的安装包里绝对不能出现 Key。
- 前端只请求自己的 Flask 后端，由后端携带 Key 转发智谱。
- 若 Key 意外泄露：立刻去智谱平台删除该 Key 重新生成。
