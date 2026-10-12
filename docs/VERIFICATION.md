# 验证记录

日期：2026-10-12。基于原 main 提交 `1320468010411ca35d3bebec7f7af4f1610e39fd` 的公开源码，并对照本地前后端源码补齐文档与回归。未修改用户原工程或操作其数据库。

## 本地验证

| 项目 | 环境 / 结果 |
| --- | --- |
| 系统 | Windows，独立工作目录与虚拟环境 |
| Python | 3.12.10 |
| Node | 24.14.0 |
| 依赖 | requirements-lock.txt 保存实际安装版本；包含 pytest 8.4.2、httpx 0.28.1 |
| 后端基础回归 | 21 项通过，2 项 MySQL 专项因未选择数据库跳过 |
| 前端接口与 Mock 回归 | 6 项通过 |
| 依赖兼容性 | pip check 通过，No broken requirements found |
| 文档与图表 | 5 个 Mermaid 图语法通过；5 份 Markdown 的 35 个相对链接目标存在；CI YAML 解析通过 |

## MySQL 持续集成

验证对象：[db189e6](https://github.com/desug/jinbi-lesson-management/commit/db189e6e7c4a0210bbb0173c22f6d9fae43c1d18)。实际运行：[CI #38259687479](https://github.com/desug/jinbi-lesson-management/actions/runs/38259687479)，结论 success。本记录在后续文档提交中保存。

| 项目 | 实际结果 |
| --- | --- |
| 后端环境 | Linux、Python 3.12、MySQL 8.4，一次性 CI 数据库 |
| 依赖兼容性 | pip check 通过 |
| 数据库迁移 | 空库依次执行四个既有版本，达到 20260503_add_student_school_class_types |
| 后端测试 | 23 项通过，0 失败、0 错误、0 跳过；包含 MySQL 并发扣课与迁移结构检查 |
| 前端测试 | 6 项通过，0 失败 |
| 报告 | backend-test-results / backend.xml，CI 保留 14 天；日志和此记录长期可查 |

并发用例初始余额 10，两次各扣 6；一个成功、一个返回余额不足，最终余额 4 且仅新增一条流水。它验证同一学生的这类竞争场景，不能替代负载测试、死锁重试或幂等性验证。

## 验证发现与修正

- Mock 登录的字段与真实 API 契约不一致：统一管理员 username/admin 与学生 user/profile，补齐科目数据结构。
- 管理员部分读接口没有 Mock handler，导致 Mock 模式仍尝试网络：为已有列表、年级、详情和流水 handler 接入前端接口。
- 既有 Alembic 版本号长于默认 VARCHAR(32)：保留原版本标识，注册 MySQL VARCHAR(128) 版本表实现；已有表的升级步骤写入部署文档。
- 数据库 URL 的编码密码可能含百分号：在 Alembic ConfigParser 中转义，保留连接 URL 的真实含义。

## 实际限制

没有操作现有业务数据库、执行其 seed、迁移或导入。没有完成 HBuilderX 编译、页面截图、浏览器页面 E2E、真机/小程序验收或真实云服务器部署；没有测试 Nginx/systemd 运行、外部模型调用、性能、渗透或真实数据合规。

Pydantic json_encoders 存在弃用警告，Node VM 模块有实验提示。当前手机号登录、开放 CORS、业务日志与错误详情、无写请求幂等键等限制仍存在；详见[部署前置条件](DEPLOYMENT.md#真实业务上线前置条件)。没有以文档完善宣称生产可用性。
