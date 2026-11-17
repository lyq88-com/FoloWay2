# AI习惯伙伴 (ai-habit-partner-v2)

> AI虚拟角色习惯养成伙伴 —— 全栈项目
> UniApp 用户端 + FastAPI 后端 + Vue3 管理后台 + MySQL + Redis

---

## 项目结构

```
ai-habit-partner-v2/
├── frontend/          # uni-app 用户端 (Vue3)
│   ├── src/
│   │   ├── pages/         # 6个页面 (login/index/habit/chat/stats/profile)
│   │   ├── components/    # 公共组件 (ai-avatar/habit-card)
│   │   ├── store/         # Vuex 状态管理
│   │   ├── common/        # 请求封装/工具函数
│   │   ├── api/           # API 接口定义
│   │   └── static/        # 静态资源
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── server/            # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/        # 接口层 (Controller)
│   │   ├── core/          # 配置/数据库/Redis/安全
│   │   ├── models/        # 数据模型 (ORM)
│   │   ├── schemas/       # Pydantic 请求/响应模型
│   │   ├── services/      # 业务逻辑层 (Service)
│   │   ├── middleware/    # 中间件 (权限/日志/异常)
│   │   ├── utils/         # 工具函数
│   │   └── main.py        # 应用入口
│   ├── sql/init.sql       # 建表脚本
│   ├── tests/             # 单元测试
│   ├── requirements.txt
│   └── .env.example
├── admin/             # Vue3 + Element Plus 管理后台
│   ├── src/
│   │   ├── views/         # 页面 (用户/AI角色/模板/看板/内容)
│   │   ├── router/        # 路由
│   │   ├── store/         # Pinia
│   │   └── api/           # 接口封装
│   ├── index.html
│   └── package.json
├── docs/              # 项目文档
│   └── 数据库设计文档.md
├── docker/            # Docker 配置
└── scripts/           # 部署/启动脚本
```

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 用户端 | UniApp + Vue3 + Vuex | 跨平台 H5/小程序/App |
| 管理后台 | Vue3 + Element Plus + Pinia | 后台管理界面 |
| 后端 | FastAPI + SQLAlchemy 2.0 | Python 异步 API |
| 数据库 | MySQL 8.0 | 业务数据持久化 |
| 缓存 | Redis 6.0+ | Token/验证码/对话上下文/热点缓存 |
| AI | 大模型对话(预留) / OCR(预留) / TTS(预留) | 阶段6联调 |

---

## 开发阶段规划

| 阶段 | 内容 | 状态 |
|------|------|------|
| 1 | 项目初始化与数据库设计 | ✅ 完成 |
| 2 | 后端基础服务与通用能力(用户/权限/日志/异常) | ⏳ 待开始 |
| 3 | 核心业务后端(习惯任务/AI角色/推送/数据分析) | ⏳ 待开始 |
| 4 | uniapp 用户端全页面开发 | ✅ 完成 |
| 5 | 管理后台页面开发 | ✅ 完成 |
| 6 | AI引擎能力联调与全系统联调 | ⏳ 待开始 |
| 7 | 完整交付文档与部署脚本 | ⏳ 待开始 |

---

## 阶段1 交付物清单

| 文件 | 说明 |
|------|------|
| `server/sql/init.sql` | MySQL 建表脚本(20张表+初始数据)，可直接执行 |
| `docs/数据库设计文档.md` | 数据库设计文档(字段含义/关联/索引/Redis键设计) |
| `server/app/core/config.py` | 后端配置管理 |
| `server/app/core/database.py` | 数据库引擎与会话 |
| `server/app/core/redis_client.py` | Redis客户端+缓存键定义 |
| `server/app/main.py` | FastAPI 应用入口(健康检查可用) |
| `server/requirements.txt` | Python 依赖 |
| `server/.env.example` | 环境变量模板 |
| `frontend/` | uni-app 前端骨架(6页面路由+Store+请求封装) |
| `admin/` | 管理后台骨架(路由+请求封装+Element Plus) |

---

## 本地快速启动

### 1. 创建数据库

```bash
mysql -u root -p < server/sql/init.sql
```

### 2. 启动后端

```bash
cd server
cp .env.example .env        # 修改数据库/Redis配置
pip install -r requirements.txt
python -m app.main           # 启动 http://localhost:8000
```

访问 Swagger 文档: http://localhost:8000/docs

### 3. 启动用户端前端

```bash
cd frontend
npm install
npm run dev:h5               # 启动 http://localhost:5173
```

### 4. 启动管理后台

```bash
cd admin
npm install
npm run dev                  # 启动 http://localhost:3000
```

---

## 数据库表概览(20张)

| 模块 | 表 |
|------|-----|
| 用户体系 | users, admins |
| 习惯任务 | task_templates, habits, checkins, checkin_items, difficulty_logs |
| AI体系 | ai_roles, ai_role_assets, chat_sessions, chat_messages |
| 成就体系 | badges, user_badges |
| 推送体系 | push_tasks, push_records |
| 统计报表 | daily_reports |
| 系统支持 | sms_codes, operation_logs, app_configs, file_uploads |

详见 [数据库设计文档](docs/数据库设计文档.md)

---

## 约定

- **分层**: Controller(api) 仅做参数接收与返回，业务逻辑统一在 Service 层
- **注释**: 代码注释清晰，关键逻辑标注说明
- **软删除**: 业务表用 status 字段(1启用/0停用)
- **统一响应**: `{ code: 200, message: "ok", data: {...} }`
