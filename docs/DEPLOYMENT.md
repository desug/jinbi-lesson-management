# 部署说明

提供可复现的本地开发流程，以及 Linux 合成数据演示/预发布部署示例。没有操作用户现有数据库或真实服务器。实际验证范围见[验证记录](VERIFICATION.md)。

## 环境约定

| 环境 | 要求 |
| --- | --- |
| 后端 | Python 3.12，backend/requirements-lock.txt 依赖快照 |
| 数据库 | MySQL 8，CI 使用 8.4，utf8mb4；既有迁移不支持 SQLite |
| 前端 | 支持 UniApp / Vue 2 的 HBuilderX；没有 npm 构建脚本 |
| 测试 | Python 环境与 Node 24；Node 不参与 HBuilderX 发行 |
| Linux 演示部署 | Nginx、systemd、HTTPS 证书，替换示例域名与目录 |

仓库根目录创建 `.venv/`，后端工作目录为 `backend/`，HBuilderX 打开 `frontend/`。配置固定读取 `backend/.env`，系统环境变量优先。

## 本地启动

### 1. 获取代码和依赖

```powershell
git clone https://github.com/desug/jinbi-lesson-management.git
Set-Location jinbi-lesson-management
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
.\.venv\Scripts\python.exe -m pip check
Copy-Item backend/.env.example backend/.env
```

Linux/macOS 的等价命令：

```bash
git clone https://github.com/desug/jinbi-lesson-management.git
cd jinbi-lesson-management
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-lock.txt
cp backend/.env.example backend/.env
```

### 2. 创建独立开发库

以本地 MySQL 管理员身份连接，替换密码后执行：

```sql
CREATE DATABASE lesson_demo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'lesson_user'@'127.0.0.1' IDENTIFIED BY '<独立的本地数据库密码>';
GRANT ALL PRIVILEGES ON lesson_demo.* TO 'lesson_user'@'127.0.0.1';
```

示例账号只授权该开发库。部署时区分有 DDL 权限的迁移账号与只有 `SELECT, INSERT, UPDATE, DELETE` 的运行账号，应用不使用 MySQL root。已有业务库不执行建库、seed 或清理脚本。

### 3. 编辑 backend/.env

设置 `MYSQL_HOST=127.0.0.1`、`MYSQL_PORT=3306`、`MYSQL_USER=lesson_user`、对应 `MYSQL_PASSWORD`、`MYSQL_DB=lesson_demo`、`MYSQL_CHARSET=utf8mb4`。

生成独立 JWT 密钥，将输出只写入本地 `.env`：

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

| 变量 | 约定 |
| --- | --- |
| JWT_SECRET_KEY | 必填，缺失时拒绝启动；每个环境独立，不提交仓库 |
| JWT_ALGORITHM | 示例 HS256，与签发和校验配置一致 |
| JWT_ACCESS_TOKEN_EXPIRE_MINUTES | 默认 1440；演示/预发布可缩短至 60 |
| APP_ENV / DEBUG / DATABASE_ECHO | 本地 development；部署 production / false / false，不会自动关闭业务 print 或收紧 CORS |
| DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL / DEEPSEEK_MODEL | 可选；无密钥时用本地规则，默认地址 https://api.deepseek.com，模型 deepseek-chat |
| SEED_ADMIN_PASSWORD | 手动初始化演示管理员时需要，与 Mock 密码无关 |
| PROJECT_NAME / PROJECT_VERSION | 服务和 API 文档元数据 |

密钥不能放前端、截图或仓库。Linux `.env` 应只允许运行账号读取，例如 `chmod 600 backend/.env`，同时设置正确所有者。

### 4. 执行既有迁移

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m alembic current
```

成功后 current 为 `20260503_add_student_school_class_types (head)`。不要重新生成初始迁移，也不要以 `create_all` 替代迁移。

项目保留长描述式版本号，新的 `alembic_version.version_num` 使用 `VARCHAR(128)`，由 `app/core/migrations.py` 的 MySQL 实现生成，要求 Alembic 1.14+。已有版本表若仍为 32 字符，备份并确认当前版本后，使用迁移账号先执行：

```sql
ALTER TABLE alembic_version MODIFY COLUMN version_num VARCHAR(128) NOT NULL;
```

MySQL DDL 可能在迁移失败前已经生效；失败时记录 current 和实际结构，按迁移与备份修复，不直接重复迁移或随意 `stamp head`。

### 5. 可选初始化演示数据

仅在隔离的空演示库执行。在 `.env` 设置自己生成的 `SEED_ADMIN_PASSWORD`：

```powershell
..\.venv\Scripts\python.exe seed.py
```

管理员为 `admin`，密码由你设置；学生为演示学员01–03，手机号字段 `19900000001–03` 仅为虚构标识。seed 可更新已有密码、学生、科目和流水，不作为生产启动步骤；导入和补表脚本也不在正常启动流程里。

### 6. 启动 API 与前端

```powershell
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

访问 `/health`、`/docs`、`/redoc`。HBuilderX 导入 `frontend/`，设置 `baseURL: 'http://127.0.0.1:8000'`、`useMock: false`，运行到浏览器。Swagger 的 HTTPBearer 授权框输入 token，不重复添加 Bearer 前缀。

真机调试时 API 监听 `0.0.0.0`，前端填写电脑局域网 IP，手机与电脑同网，开发端口只对受信局域网开放。手机 localhost 是手机自身。小程序需填写 AppID，正式发布恢复域名校验并配置 HTTPS request 合法域名。发行入口参见 [DCloud HBuilderX 工程说明](https://en.uniapp.dcloud.io/quickstart-hx.html)。

## Linux 演示/预发布部署

示例采用 H5 与 API 同域，域名 `demo.example.com`、API 前缀 `/api`。先完成数据库、依赖和迁移，再按服务器环境调整配置；以下不是已经执行的上线记录。

### 后端服务

1. 创建非特权账号 `jinbi`，将已测试的 Git 提交部署到 `/srv/jinbi/current`，建立根目录 `.venv` 并安装依赖。
2. 配置 `.env`，运行账号使用受限数据库权限；迁移由独立账号在发布窗口执行。运行账号能读代码、依赖和 `.env`，不需要写源码。
3. 修改 [jinbi.service.example](../deploy/jinbi.service.example) 的账号与目录，安装到 `/etc/systemd/system/jinbi.service`。

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now jinbi
sudo systemctl status jinbi --no-pager
curl --fail http://127.0.0.1:8000/health
```

示例使用 2 个 Uvicorn worker，不使用 reload，只信任本机代理头；`--root-path /api` 保证代理后的 Swagger 正确访问 OpenAPI。worker 数是示例值，需结合 CPU、连接数与压力测试调整。[Uvicorn 官方配置说明](https://uvicorn.dev/settings/)。

### H5 与 Nginx

1. 前端设 `useMock: false`、`baseURL: 'https://demo.example.com/api'`。HBuilderX 发行菜单选择网站 H5，将编译生成的发行目录（通常 `unpackage/dist/build/h5/`）部署至 `/srv/jinbi/www`，不发布源码或开发预览产物。
2. 准备域名和有效 HTTPS 证书，替换 [nginx.conf.example](../deploy/nginx.conf.example) 中的域名、证书路径和静态目录，安装为站点配置。
3. `/api/` 转发到 `127.0.0.1:8000/` 并去掉前缀，其余请求由 H5 静态目录处理。

```bash
sudo nginx -t
sudo systemctl reload nginx
curl --fail https://demo.example.com/api/health
```

对外仅开放 HTTPS，API 和 MySQL 不开放公网端口。证书路径必须存在。代码 CORS 当前仍开放，同域部署不等同于身份安全措施。

## 验收与回退

| 验收 | 预期 |
| --- | --- |
| /api/health | 200 且 ok=true，仅证明进程响应，不检查数据库 |
| /api/docs 和 /api/openapi.json | 正常加载，请求前缀正确 |
| 管理员登录后查学生 | 数据库查询成功；无 token 为 401，学生 token 为 403 |
| 加 2.25、扣 1.50 | 余额净增 0.75，流水可追溯，余额等于总课时减已扣课时 |
| 超额扣课 | 400 / INSUFFICIENT_HOURS，余额与流水不变 |
| 学生资料与流水 | 仅本人数据 |
| H5 刷新和真机 | 页面可加载，无混合内容，API 地址可访问 |

验收使用专门的合成数据，不能只检查 health。查看服务与错误使用 `systemctl status jinbi`、`journalctl -u jinbi`；当前日志可能含业务信息，需要限制读取和保留周期。

发布前记录 Git 提交、依赖快照、alembic current、H5 产物版本，并备份数据库、演练恢复。小型演示库可使用 `mysqldump --single-transaction --no-tablespaces -u <备份账号> -p lesson_demo > <备份文件>`，交互输入密码，文件放受限目录且不提交仓库；它不是生产完整备份策略。

回退先停止写入，恢复匹配的代码与 H5 产物；不兼容的数据库变更按演练过的备份恢复。downgrade 可能删除数据，不在真实库直接试错。

## 真实业务上线前置条件

| 当前缺口 | 所需工作 |
| --- | --- |
| 学生手机号登录 | 可靠验证码/账号认证、登录限流、防手机号枚举 |
| 身份生命周期 | 账号禁用校验、令牌撤销/轮换、管理员密码管理 |
| 日志与异常 | 隐藏内部详情，结构化日志与脱敏；DEBUG=false 不会自动完成这些改动 |
| 接口与数据 | 收紧 CORS、精度校验、写请求幂等、列表分页与规模验证 |
| 数据保护 | 独立密钥、最小权限、备份恢复、AI 输入授权与脱敏 |
| 运维验证 | 数据库就绪检查、监控告警、负载测试、平台编译与完整业务验收 |

这些是待完成工作，不是已实现能力；部署文档不能代替生产评审。
