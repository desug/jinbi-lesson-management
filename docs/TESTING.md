# 测试说明

测试目标是验证角色隔离、核心写事务和前端接口契约。自动化回归执行实际业务代码，默认不使用真实学生数据、用户数据库或外部 AI 服务。

## 环境与执行命令

Python 3.12，Node 24；在仓库根目录创建独立虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
node --experimental-vm-modules --test tests/frontend/flows.test.mjs
```

Linux/macOS 使用 `.venv/bin/python` 替代 Windows 的解释器路径。也可安装 `backend/requirements-test.txt` 按兼容范围重新解析依赖；精确复现本次环境优先使用快照文件。

默认运行：后端基础回归执行，两个 MySQL 专项跳过；前端用例执行。具体数量与结果见[验证记录](VERIFICATION.md)，以当前运行输出为准。

## 隔离策略

| 层级 | 方法与范围 |
| --- | --- |
| 后端默认 | 每个用例新建 SQLite 内存库，开启外键，使用真实 ORM 模型与真实 API |
| 配置隔离 | conftest 在导入 app 前覆盖所有连接、JWT 和 AI 配置；本地 .env 不能替换它们 |
| API 数据库 | 仅覆盖 get_db，不绕过角色鉴权和业务服务；测试后清除依赖覆盖 |
| MySQL | 仅接受显式 JINBI_TEST_DATABASE_URL，协议 mysql+pymysql、主机 localhost/127.0.0.1、库名 lesson_test |
| MySQL 用例数据 | API 回归使用外层事务/保存点隔离；并发用例使用专属合成记录，结束时定向清理 |
| 外部 AI | 密钥为空，仅测试本地规则查询，不产生第三方调用或费用 |
| 前端 | Node 加载原始 ES 模块与 @/ 别名，用内存 uni 接口替换存储、网络与提示 |

FastAPI 数据库依赖覆盖参见[官方测试说明](https://fastapi.tiangolo.com/advanced/testing-dependencies/)；MySQL 保存点策略参考 [SQLAlchemy 外部事务测试模式](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)。

## 自动化覆盖

| 用例 | 核心断言 | 文件 |
| --- | --- | --- |
| 健康与接口契约 | health 正常，OpenAPI 有核心路由、不宣称学生缴费接口 | [test_api.py](../backend/tests/test_api.py) |
| 鉴权失败 | 缺失、无效、过期 token 为 401；错误管理员密码拒绝 | 同上 |
| 角色隔离 | 学生访问管理端为 403，管理员访问学生端为 403 | 同上 |
| 数据隔离 | 学生资料与流水只返回 token 对应学生 | 同上 |
| 新增与重复 | 创建学生、默认科目、缴费和初始流水；重复手机号不增加数据 | 同上 |
| 课时余额 | 加 2.25、扣 1.50，余额 10.75，流水和缴费数量正确 | 同上 |
| 业务失败 | 超额扣课 400，零/负课时 422，余额与流水不变 | 同上 |
| 数据库失败 | 注入提交异常，科目余额、缴费与流水一起回滚 | 同上 |
| 年级与删除 | 拒绝降级；软删除保留流水、禁止重新登录并从列表隐藏 | 同上 |
| AI 本地规则 | 固定查询命中且不写课时数据 | 同上 |
| 迁移版本容量 | 版本表能容纳每一个既有描述式版本号 | [test_migration_config.py](../backend/tests/test_migration_config.py) |
| MySQL 迁移 | 从空库迁移至 head，学生和流水字段与模型一致 | [test_mysql.py](../backend/tests/test_mysql.py) |
| MySQL 并发 | 余额 10，两个请求各扣 6，只有一个成功，余额 4且一条流水 | 同上 |
| Mock 登录与操作 | 真正调用前端 api/auth 与 api/admin，资料和余额正确且没有网络请求 | [flows.test.mjs](../tests/frontend/flows.test.mjs) |
| 请求契约 | Bearer 请求头、GET 编码、camelCase 响应、200 业务失败、401 清理 | 同上 |
| 日志与失败 | 嵌套凭据脱敏且不改原请求；Mock 超额扣课不改变数据 | 同上 |

测试没有 Mock 掉课时计算、ORM 事务或鉴权代码。SQLite 不支持 MySQL 行锁语义，基础回归通过不能替代 MySQL 专项通过。

## 独立 MySQL 复现

推荐在一次性容器中执行，也可使用专门的本地空测试库。测试不从 backend/.env 获取数据库地址；必须显式选择 lesson_test。以下凭据仅用于本地临时容器，端口只映射到回环地址：

```powershell
docker run --name jinbi-test-mysql --rm -d -p 127.0.0.1:3307:3306 `
  -e MYSQL_DATABASE=lesson_test -e MYSQL_USER=lesson_test_user `
  -e MYSQL_PASSWORD=ci-only-database-password -e MYSQL_ROOT_PASSWORD=ci-only-root-password mysql:8.4
```

等待 MySQL 日志显示 ready 后，在同一终端设置临时环境变量：

```powershell
$env:MYSQL_HOST = '127.0.0.1'
$env:MYSQL_PORT = '3307'
$env:MYSQL_USER = 'lesson_test_user'
$env:MYSQL_PASSWORD = 'ci-only-database-password'
$env:MYSQL_DB = 'lesson_test'
$env:JWT_SECRET_KEY = 'ci-only-signing-key-not-for-deployment'
$env:DEEPSEEK_API_KEY = ''
$env:JINBI_TEST_DATABASE_URL = 'mysql+pymysql://lesson_test_user:ci-only-database-password@127.0.0.1:3307/lesson_test?charset=utf8mb4'
Set-Location backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m alembic current
Set-Location ..
.\.venv\Scripts\python.exe -m pytest -q --junitxml=test-results/backend.xml
```

不要指向生产库或含业务数据的库，也不要通过关闭库名校验来运行。结束后 `docker stop jinbi-test-mysql`，关闭专用终端；避免将测试环境变量带入正常 API 启动。仓库不要求本机安装 Docker，GitHub Actions 自带一次性 MySQL 服务。

## 持续集成与诊断

[CI 配置](../.github/workflows/ci.yml)在 push、pull_request 和手动触发时运行两个独立任务：

运行镜像固定为 Ubuntu 24.04，官方 GitHub Actions 固定为已核实的提交 SHA，并使用 Node 24 Action 运行时。应用的 Node 24 与 Python 3.12 分别由 setup-node 和 setup-python 配置。

1. 后端：Python 3.12 + MySQL 8.4，安装依赖快照，pip check，从空库迁移，再执行完整回归和并发测试。JUnit 报告保留 14 天。
2. 前端：Node 24，执行实际 ES 模块的接口与 Mock 回归，不要求 npm 工程。

检查[Actions](https://github.com/desug/jinbi-lesson-management/actions/workflows/ci.yml)中**对应提交**的结果，不能用旧提交的成功代表新代码通过。

常见失败：JWT 缺失检查迁移进程的临时配置；连接失败检查容器就绪和端口；版本号截断检查依赖版本与已有版本表；ModuleNotFoundError 检查当前解释器和依赖快照。Node 的 VM Modules 实验提示与 Pydantic json_encoders 弃用警告是已知提示，后者需要后续迁移到字段序列化器，不隐藏这些警告。

## 手工业务验收

使用合成数据在 HBuilderX 浏览器运行，再按实际需要验证小程序/真机：

| 步骤 | 预期结果 |
| --- | --- |
| 学生与管理员分别登录 | 进入对应首页；切换角色后缓存不串用 |
| 新增学员、搜索、筛选 | 列表与详情一致，重复手机号有明确错误 |
| 加课/扣课、刷新、重新登录 | 余额和流水一致；联调模式可从数据库恢复 |
| 扣课超过余额 | 明确提示，余额和流水不变；不可展示为成功 |
| 升级与软删除 | 不允许降级，已删除学生不能登录，历史保留 |
| AI 常见问法、未知问法 | 规则返回准确结果；未知时有提示，不执行写操作 |
| 学生缴费/AI/相册 | 明确按 Mock 占位理解，不当作真实支付或学生 AI 接口 |
| 断网、过期登录与空列表 | 提示可读，可重新登录，页面不无限等待 |
| H5 发行和设备访问 | 构建成功、刷新可加载、HTTPS 无混合内容、设备能访问 API |

本次未完成 HBuilderX 编译、页面 E2E、真实设备、线上 Nginx/systemd 部署、压力/安全/第三方模型质量测试。已有回归不等于完整质量认证，缺口与实际证据在验证记录中保留。
