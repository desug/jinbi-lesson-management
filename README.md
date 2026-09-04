# Jinbi Lesson Management · 课时管理系统

面向培训机构的前后端分离课时管理项目，包含管理员端和学生端。使用 UniApp + Vue2 构建界面，FastAPI 提供 API，SQLAlchemy 管理 MySQL 数据，Alembic 管理数据库迁移。

> 公开展示版：种子数据和本地模拟数据已重建为虚构数据；姓名、联系方式仅供演示，不得据此联系任何人。

## 功能与边界

| 模块 | 当前源码能力 |
| --- | --- |
| 登录 | 管理员账号密码登录；学生手机号登录；JWT 身份凭据 |
| 学生管理 | 列表、搜索、新增、详情、软删除 |
| 年级与班型 | 年级列表、年级学生查询、学生升级、班型字段与校验 |
| 课时 | 加课、扣课、余额、管理员与学生课时流水 |
| AI | 管理员自然语言课时查询，需单独配置服务商 API Key |
| 展示页面 | 学生缴费、学生 AI、相册页面存在，但对应学生后端路由尚未实现，不能当作已完成的线上功能 |

本项目适合学习、代码阅读和面试展示，不应未经安全加固直接作为生产系统。没有宣称自动化集成测试、生产可用性或性能指标。

## 技术栈

- 前端：UniApp、Vue2、自定义 Vue 组件；使用 HBuilderX 工程方式，当前无 npm `package.json`，未引入 uView。
- 后端：FastAPI、Pydantic、SQLAlchemy 2、PyMySQL、Alembic、python-jose、bcrypt。
- AI：OpenAI 兼容客户端调用 DeepSeek 服务；密钥只在服务端配置。

## 目录

```text
frontend/                 # UniApp 工程，使用 HBuilderX 打开
  api/ components/ config/ mock/ pages/ static/ utils/
  App.vue main.js manifest.json pages.json
backend/
  app/
    core/ models/ routers/ schemas/ scripts/ services/ utils/
  alembic/                # 数据库迁移
  alembic.ini
  requirements.txt
  seed.py
  .env.example
README.md
.gitignore
```

## 本地启动

### 后端

以下 PowerShell 命令只用于独立开发环境。先准备 Python（建议 3.12）和本地 MySQL，手动建立一个空的开发数据库及专用用户。

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# 编辑 .env：填写本地数据库配置；用随机值替换 JWT_SECRET_KEY
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

生成 JWT 随机密钥的方法：`python -c "import secrets; print(secrets.token_urlsafe(48))"`。真实值仅存于本地 `.env` 或安全的部署配置中，不得提交。

API 文档：[Swagger UI](http://127.0.0.1:8000/docs)、[ReDoc](http://127.0.0.1:8000/redoc)；健康检查：`GET /health`。

### 前端

1. 使用 HBuilderX 打开 `frontend/`。
2. 默认 API 地址为 `http://127.0.0.1:8000`，位于 `config/index.js`。不要提交自己的生产地址。
3. 运行到浏览器进行本地开发。手机真机需自行配置可访问的开发机地址；手机上的 localhost 不是电脑。
4. 微信小程序需自行填写 AppID；工程中的应用标识已清空。前端 `useMock: true` 可启用本地模拟模式，它不提供真实身份认证。

### 可选初始化数据

**仅可用于隔离的空开发数据库。** `seed.py` 会写数据库，可能更新已有管理员密码、学生字段和课时数据；不会在启动 API 时自动执行。

在 `backend/.env` 设置自己生成的 `SEED_ADMIN_PASSWORD` 后，才可选择运行：

```powershell
.\.venv\Scripts\python.exe seed.py
```

初始化密码不会打印在控制台。`app/scripts/import_students_from_excel.py` 是导入工具，不附带 Excel 文件；导入、补表与清理脚本都可能修改数据库，不应在生产环境随意执行。

## 环境变量

模板位于 `backend/.env.example`，加载位置固定为 `backend/.env`。

| 变量 | 用途 |
| --- | --- |
| MYSQL_HOST / MYSQL_PORT / MYSQL_USER / MYSQL_PASSWORD / MYSQL_DB / MYSQL_CHARSET | 数据库连接 |
| JWT_SECRET_KEY | JWT 签名密钥，必须使用独立随机值 |
| JWT_ALGORITHM / JWT_ACCESS_TOKEN_EXPIRE_MINUTES | JWT 算法与有效期 |
| DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL / DEEPSEEK_MODEL | 可选 AI 服务配置 |
| SEED_ADMIN_PASSWORD | 手动初始化时必须设置的管理员密码 |
| APP_ENV / DEBUG / DATABASE_ECHO | 环境标识与日志选项 |

缺少 JWT_SECRET_KEY 时，整理版后端会拒绝启动，避免使用已公开的默认密钥。

## 主要 API

`POST /auth/admin-login`、`POST /auth/student-login`、`GET /student/profile`、`GET /student/records`、`GET/POST /admin/students`、`GET /admin/grades`、`POST /admin/lesson/change`、`POST /admin/ai-query`。以运行后的 `/docs` 和路由源码为准。

## 安全边界与验证范围

- 不包含原 `.env`、原 Git 历史、依赖、构建缓存或数据库备份。
- 学生登录流程目前依赖手机号，不具备短信验证码等强身份校验，真实部署前必须加固。
- CORS 当前面向开发环境开放；部署前应限制来源、关闭调试输出并评估日志中的个人信息。
- AI 功能可能向第三方发送查询上下文，使用真实学生数据前须完成隐私与授权评估。
- 已完成 Python/JavaScript 语法检查、已知当前及历史凭据残留扫描、本地 Mock 初始化/查询/余额一致性/演示登录检查。
- 后端配置运行检查因本机依赖不完整（dotenv / pydantic_core）未完成；未修改原环境，未连接数据库，未执行迁移、初始化或完整端到端测试。请按启动步骤创建独立虚拟环境。
- 新仓库使用全新历史；这不会撤回原 GitCode 仓库中可能已存在的凭据。旧凭据需另行轮换，旧历史需另行处理。

## 项目截图

TODO：仅使用虚构学生数据制作截图，不展示真实学生、手机号或缴费记录。

## 许可

原目录中的 MIT 文本仍含未填写的权利人占位符，因此本次未发布有效署名的 LICENSE。公开可见不等于授予开源许可；待作者确认权利人和许可后补充。第三方依赖遵循各自许可。
