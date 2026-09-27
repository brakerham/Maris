# P4-B6-R1 安全数据边界与兼容入口返修运行说明

- 任务：`P4-B6-R1`
- 角色：执行智能体
- 交付状态：`review`
- 运行状态：`finished`
- 控制版本：`2026-09-25T20:08:00+08:00`
- 接口依据：`P4-IF-001`、`P4-IF-002`
- 固定起点：93 文件逐项匹配，`P4-B6-R1-START-SHA256:62c250c73e1c47ed13f8cd6355be9cb88ee4081f920e2ed747b82492e5168c2e`
- 验证边界：本文记录执行方开发、自测和真实 PostgreSQL 证据；没有运行或修改 `tests/independent/**`，不构成 P4-C11 独立验收或 P4-A 完成结论。

## 1. 交付结论

R1 负责的 3 个 P0 和 7 个 P1 已在授权文件范围内实现并由执行方测试覆盖。一次性绑定码只在首次 HTTP 成功响应中返回；Host receipt 只保存安全结果；initialize、create code、consume 和 revoke 的 receipt、领域事实与安全结果使用同一 SQLAlchemy Session 和事务。Host 模式活动导入从已认证 DeviceSession/Principal 派生用户、渠道和权限，静态 legacy identity 只能在没有 HostRuntime 的显式测试装配中使用。

数据库层已增加三条冻结的复合 user scope 外键、message→run 关系和 R2 预备字段。三个既有 P4 revision 保持线性单 head；SQLite 成对 rebuild 后执行 foreign key check；PostgreSQL 使用真实复合约束和延迟的 run→pending 外键。`cancelled` run 降至 P3 时转换为 `error`，仅在原 `error_code` 为空时写入 `cancelled`，清空 pause reason，并保留 run、pending 和引用。

最终执行方结果：本地组合 `265 passed, 1 warning`；真实 PostgreSQL `21 passed`；`pip check` 无破损；允许范围内源码和测试编译通过；Alembic 只有 `p4_host_state` 一个 head。项目 PostgreSQL 容器和网络已普通关闭，`docker compose ps --format json` 退出 0 且无输出。

## 2. 十个审计项映射

| 审计项 | 代码位置与实现 | 执行方测试 | 最终结果 |
| --- | --- | --- | --- |
| `P0-01` 原始绑定码进入 receipt 并可重放 | `host/auth/service.py` 使用随机 `code_id`、40-bit code 和冻结 v2 HMAC 域；`api/host_routes.py` 用 `CommandOutcome.public_result/receipt_result` 分离首次响应与持久结果；同键创建重放固定抛出 `one_time_secret_unavailable` | `tests/host/test_api.py` 扫描全部 SQLite 表，确认 code、access token、密码和原始外部身份零落库；`test_state.py` 检查 receipt；`test_postgresql_r1.py` 检查真实 PG receipt | 通过；首次创建 HTTP 201，同键同载荷 409，receipt 无原码 |
| `P0-02` Host 活动导入绕过认证 | `api/app.py` 拒绝 HostRuntime 与静态 identity 同时装配，生产默认无静态 identity；`api/activity_import_routes.py` 复用 Bearer、AuthenticatedSession 和 Principal，固定 `owner_id=user_id=principal.user_id` | `tests/host/test_api.py` 覆盖无 token、坏 token、撤销 token 零写和可信 principal；既有 P3 显式 legacy builder 保持通过 | 通过；Host 认证发生在 service 调用前 |
| `P0-03` 三条跨用户关系缺少复合 FK | `host/state_models.py`、`agent/models.py` 和 `p4_host_state.py` 增加 `fk_memory_item_user_superseded`、`fk_memory_candidate_user_item`、`fk_run_user_pending` 及对应 unique | `tests/host/test_migrations.py` SQLite 直接 SQL；`tests/host/test_postgresql_r1.py` PostgreSQL 直接 SQL 和 inspector | 通过；三类跨用户写均由数据库拒绝，同用户关系合法 |
| `P1-01` 过期 access 仍可改密 | `AuthService.change_password` 在任何 credential/session 写入前检查 revoked、access expiry、absolute expiry 和 active user；`now >= expiry` 失败 | `tests/host/test_auth.py` 覆盖到期前 1µs、恰好到期、到期后 1µs及失败零写 | 通过；到期边界稳定为 401 `session_expired` |
| `P1-02` Host command 三事务 crash window | `host/state.py` 的 `HostCommandService.execute` 在一个 `Session.begin()` 内完成 claim、领域命令和安全 receipt；四个路由调用 in-session 认证方法 | `tests/host/test_state.py` 覆盖提交前故障回滚、同键恢复和 secret 分离；`test_postgresql_r1.py` 参数化四个 operation 的并发、异载荷、响应丢失重试和提交前失败 | 通过；不存在永久 incomplete receipt 或事实/receipt 半提交 |
| `P1-03` adapter 缺失与错误状态不一致 | consume header 改为可选读取，`binding_command_user_id` 首先校验 adapter，再查询 code；穷举映射将 adapter 错误固定为 401 | `tests/host/test_api.py` 覆盖缺失、空和错误 adapter，并确认 attempts 仍为 0；正确 adapter 进入消费 | 通过；三种拒绝均为 401 `channel_adapter_unauthorized` |
| `P1-04` 错误 code/channel 不计真实 attempts | consume DTO 增加 `code_id`；错误尝试使用条件 UPDATE 原子递增，1～4 active，第 5 次 locked，第 6 次不增长；正确消费和第五次竞争由互斥 CAS 决定 | `tests/host/test_auth.py` 覆盖 1～6 次、错 channel、unknown/revoked/expired/consumed、并发第五次与正确消费；`test_postgresql_r1.py` 在真实 PG 重复竞争并覆盖并发新码替换 | 通过；开发中复现并修复过一次 lost-update，最终 SQLite/PG 回归均通过 |
| `P1-05` AuthError HTTP 映射不穷举 | `host/auth/errors.py` 使用 21 项闭集 `AuthErrorCode`；`api/app.py` 在导入时断言映射集合完全相等，不设默认 409 | `tests/host/test_api.py` 逐码检查状态、error envelope、request_id 和 429 `Retry-After`，并覆盖 404/405 | 通过；未知 AuthError 构造直接失败 |
| `P1-13` cancelled 阻断 P4→P3 downgrade | `p4_host_state.py` 先移除 run→pending，再把 cancelled 映射为 P3 合法 error，保留已有 error code、清空 pause reason，再回退列和 check | `tests/host/test_migrations.py` 覆盖全部 pending 状态的 SQLite head→P3→head；`test_postgresql_r1.py` 覆盖含循环引用的真实 PG 回环 | 通过；run/pending 数量和引用保留，升级回 head 后数据仍一致 |
| `P1-14` activity import 不识别 P4 unique 名 | `activity_import/service.py` 同时识别旧 `uq_activity_template_name_normalized` 和 P4 `uq_template_user_name`；不解析 PostgreSQL 完整异常文本 | `tests/activity_import/test_service.py` 约束名映射；`test_postgresql.py` 同用户同名竞争与不同用户同名成功 | 通过；竞争败方稳定映射为 `concurrent_modification` |

## 3. 数据库、HTTP 与故障恢复语义

### 一次性绑定码

- `POST /api/v1/channel-bindings/codes` 首次成功返回 201，字段为 `code_id/code/expires_at/replayed:false`。
- HMAC 输入为 `wife.channel-binding.v2\0code_id\0channel\0code`；原码不可由 receipt、日志、事件或数据库恢复。
- 同一 Idempotency-Key 和同一 payload 的创建重放返回 409 `one_time_secret_unavailable`；同键异载荷返回 409 `idempotency_conflict`。
- 新 key 在同一事务中撤销同用户/同 channel 的 active code，并创建替代 code。创建前锁定 active owner row，使并发新 key 在 PostgreSQL 中串行替换，最终只有一个 active code。
- consume 必须提供 `code_id + code + channel + provider_account + external_subject`。adapter 在 code 查询前验证；缺失、空、错误均为 401。
- unknown、expired、consumed、revoked、locked、wrong code 和 wrong channel 对外统一为 409 `binding_code_invalid`。unknown code 不创建伪 code row。
- 已知 active row 的第 1～4 次错误保持 active，第 5 次转 locked，第 6 次不再增加。错误计数、到期与正确消费都使用条件 UPDATE；竞争只允许一个终态获胜。

### Host command 与 receipt

- `CommandOutcome.public_result` 只用于首次进程内响应；`receipt_result` 是允许持久保存和重放的安全结果。
- initialize、create code、consume 和 revoke 都在 receipt claim 所在 transaction 内调用 in-session 领域方法。提交前异常会整体回滚，原 key 可再次首次执行。
- 提交后响应丢失时，initialize、consume 和 revoke 可从安全 receipt 重放；create code 的同 key 重试只能得到 `one_time_secret_unavailable`。
- 同键并发时只有一个事务执行领域 mutation；竞争事务可能直接读取已完成 receipt，或在唯一 claim 竞争期间返回 retryable `concurrent_modification`，随后同 key 重试按上述恢复语义处理。
- receipt 不保存 password、token、raw code、provider account 或 external subject；请求 payload 只以 keyed fingerprint 参与幂等比较。

### 认证、principal 和错误边界

- `AuthenticatedSession` 携带可信 DeviceSession `platform`；`windows_desktop → desktop_chat`，`api_test → api_test`。
- 改密对 access 和 absolute expiry 使用排他上界；恰好到期即失败且 credential、session、refresh 零写。
- Host 活动导入只有 Host principal 和显式 legacy test identity 两种互斥装配。Host 模式没有静态回退身份。
- 404、405、Pydantic、AuthError 和业务错误均返回带 `request_id` 的稳定 envelope；错误响应不包含内部路径、SQL、token、digest、外部身份或异常正文。

### schema 与 migration

- `memory_item(user_id,id)`：`uq_memory_item_user_id`。
- `memory_item(user_id,superseded_by_id) → memory_item(user_id,id)`：`fk_memory_item_user_superseded`。
- `memory_candidate(user_id,memory_item_id) → memory_item(user_id,id)`：`fk_memory_candidate_user_item`。
- `agent_run(user_id,pending_action_id) → pending_action(user_id,id)`：`fk_run_user_pending`，PostgreSQL 为 deferrable、initially deferred。
- `conversation_message(user_id,run_id) → agent_run(user_id,id)`：`fk_message_user_run`；`run_id/run_sequence` 同空同非空；`(user_id,run_id,run_sequence)` 唯一。
- `pending_action` 增加非负 `commit_attempt_no`（默认/回填 0）和 nullable `commit_lease_expires_at`；保留 `version_id` fence。
- downgrade 顺序先解除 run→pending，再处理 pending，之后映射 cancelled 并回退 run；memory candidate 的 item FK 在删除 memory item 前解除。SQLite 重建结束执行 `PRAGMA foreign_key_check`。

## 4. 执行方测试证据

| 组别 | 最终命令范围 | 结果 |
| --- | --- | --- |
| 本地 Host + P0～P3 组合 | `tests/host`、`tests/finance`、`tests/activity_import`、`tests/agent_finance`，明确排除三个 PostgreSQL 文件 | `265 passed, 1 warning in 40.98s`；0 failed，0 skipped |
| 最终认证/API 定向 | `tests/host/test_auth.py tests/host/test_api.py` | `24 passed, 1 warning in 17.58s` |
| SQLite migration 定向 | `tests/host/test_migrations.py` | `8 passed in 12.60s` |
| PostgreSQL finance | `tests/finance/test_postgresql_claim.py` | 4/4 passed，进入 P4 head 真实业务断言 |
| PostgreSQL activity import | `tests/activity_import/test_postgresql.py` | 10/10 passed（原 9 项加跨用户同名） |
| PostgreSQL R1 | `tests/host/test_postgresql_r1.py` | 7/7 passed，覆盖复合 FK、cancelled 回环、binding 并发和四类 Host command |
| PostgreSQL 合并 | 上述三个 PostgreSQL 文件 | `21 passed in 7.23s`；0 failed，0 skipped，0 warning |
| 静态/依赖 | `pip check`；允许范围 `compileall`；Alembic heads | `No broken requirements found`；编译退出 0；唯一 head `p4_host_state` |

唯一最终 warning 是第三方 Starlette `TestClient` 对 AnyIO `BlockingPortal` 旧别名的 `DeprecationWarning`。没有屏蔽警告、修改第三方包或把 warning 写成通过项。

### 开发期间出现并已关闭的失败

1. 首轮 Host 组合为 `58 passed, 2 skipped, 1 warning, 1 failed`。失败是 SQLite inspector 的 unique 标志返回整数 `1`，测试误用 `is True`；改为布尔判断后 migration 8/8 通过。两项 skip 是当时未设置 PostgreSQL URL 的 R1 PG 文件，不计为通过。
2. 新增“第 5 次错误与正确消费竞争”后首次为 `15 passed, 1 failed`，实际复现正确消费返回成功但最终行被旧错误事务覆盖为 locked。产品实现改为数据库条件 UPDATE 后，16/16 auth 通过，真实 PostgreSQL 竞争也通过。
3. 首轮 PostgreSQL 合并为 `15 passed, 1 failed`。唯一失败是执行方新测试使用 `:schema::regnamespace`，SQLAlchemy 没有识别 bind parameter；改为 `to_regnamespace(:schema)` 后专项通过，migration 本身没有失败。
4. 扩展四类 Host command PG 并发断言后首次为 `3 passed, 4 failed`。数据库正确返回 retryable `concurrent_modification`，测试却只接受立即 replay；测试按冻结恢复合同改为允许 claim 竞争后同 key 重试，并验证领域版本只增加一次。最终 7/7 通过。
5. 首次 `docker compose up` 在受限环境中找不到 `docker_engine` 管道；提升后仍确认 Docker Desktop Linux Engine 尚未运行。启动已安装的 Docker Desktop 后，Engine 29.8.0 就绪，项目服务健康，全部 PG 测试完成。没有下载镜像替代物、修改 Docker 设置、删除 volume 或 prune。

## 5. PostgreSQL 与资源证据

- 只启动 Compose service `finance-postgres`，镜像为项目固定的 `postgres:17.6-alpine`。
- 连接使用项目测试账户和 `127.0.0.1:55432`；所有 fixture 使用随机 schema、UUID 和虚拟数据。
- 最终 PostgreSQL 合并执行 21 项，全部进入业务断言，无环境 skip。
- 约束检查确认 PostgreSQL `fk_run_user_pending` 为 `DEFERRABLE INITIALLY DEFERRED`，R1 schema 内约束名最大长度不超过 63。
- 测试后执行普通 `docker compose down`；容器和项目 network 均已移除。随后 `docker compose ps --format json` 退出 0、无输出，项目服务列表为空。
- 未执行 `down -v`、volume 删除、prune、Docker 全局设置变更或其他 service 启动。

## 6. 文件边界与准确数量

以 93 文件起点清单逐项复算：其中 21 个既有交付文件摘要变化，72 个保持原摘要；没有起点文件删除。新增执行方测试 `tests/host/test_postgresql_r1.py`。

R1 产品、migration 和执行方测试交付合计 22 个文件：21 modified、1 added、0 deleted。另新增本文并更新执行智能体日志，因此本任务工作区总计为 22 modified、2 added、0 deleted。起点中原有但不属于 R1 文件边界的 B6/R2 文件保持起点摘要，未被本任务覆盖。

## 7. 给 R2 的保护不变量和可用字段

R2 接续时必须保留以下边界：

1. 不得把 raw binding code、token、password 或原始外部身份写入 receipt、事件、日志、message 或模型上下文。
2. 不得把 `HostCommandService` 拆回多事务；领域 mutation 必须继续接收 claim 所在 Session，public/receipt result 必须保持分离。
3. consume 的 adapter gate 必须继续早于 code 查询；所有 code 终态继续归一为 `binding_code_invalid`。
4. `user_id` 复合外键是数据库安全边界，不得退化为应用过滤或恢复单列 FK。
5. `fk_run_user_pending` 必须保持 nullable、deferrable 和 initially deferred；R2 的 claim/lease/fence 实现可直接使用 `pending_action.commit_attempt_no`、`commit_lease_expires_at` 和 `version_id`。
6. 持久 message 可使用 `conversation_message.run_id`、`run_sequence` 和 `tool_call_id`；run_id 与 sequence 必须同空同非空，写入需遵守 `(user_id,run_id,run_sequence)` 唯一约束。
7. R2 修改共享 `agent/models.py`、Host state 或 migration 前，必须保留本报告的 22 文件快照不变量并复跑 R1 本地和 PostgreSQL 门禁。

## 8. 22 文件 SHA-256 快照

算法：仓库相对 POSIX path，按路径排序；每行 `path<TAB>lowercase_sha256<LF>`，对全部 22 行拼接后的 UTF-8 字节再计算 SHA-256。

```text
migrations/versions/p4_host_identity.py	d6de5bc19b23e2584bba5fb78cf948ca2babff746cfa7f688d58b2e0ed8349bc
migrations/versions/p4_host_state.py	8d83992fcae126005e9e82408e21104a429e0a61a1125d8cfb8c3d180c7e7a37
migrations/versions/p4_host_user_scope.py	649cf372e9bbadc6aaecf6bad4f7daac9b1be68fb663c4dc36b8376df9817e8c
src/wife_system/activity_import/service.py	bfa200b437abde8ead703d1994d3c929ad17ae79796ec924ee18a640d83dc8a3
src/wife_system/agent/models.py	394969acddaadf2d5229be1f44cc7f45983e0c313115aa6dba69e15e0c9fbbf1
src/wife_system/api/activity_import_routes.py	da607e2e06a42883108844025f12d689e28817d47bf65618e4ce2876fe0f94e2
src/wife_system/api/app.py	ec087080a9265ef6b34fd507fa1dae63f2df8f20b76427b35200b9a0244a5dd5
src/wife_system/api/host_routes.py	f30938373b96f895abb37cbadb0a0dfad84cd297a96f130cb17d412a2d82382c
src/wife_system/api/host_schemas.py	ae02e92f528e47ff2ad9fb6a2b64e2f0350acbfe3a5d8e85cf343bb08c8c381b
src/wife_system/host/auth/errors.py	4621b90ff0f058143e7e82f4f5f9569538edf96de0b21832859a58a9c30900b1
src/wife_system/host/auth/models.py	293e467c8c7aabf67b2a786d91f98e5ffaf847d0c9386692937111a456fa5fbd
src/wife_system/host/auth/service.py	e292fac8e9f93a773efd5d418925b5aea15d272445fcc359609b3ce7dc7444ae
src/wife_system/host/state_models.py	0121655c97ca6e258bb5ff3053cd0b83767cfc81637c25859e3fcc0cb20dd3b1
src/wife_system/host/state.py	d166f0de0c0653b7082e9b6c2c394ca26a92b8408ea773955e521f0ee170d798
tests/activity_import/test_postgresql.py	ac217ef3c5a192630675939f67e3994326c419abb17e1a6abdce71ca1e778a2b
tests/activity_import/test_service.py	d2908aa0288a29cf77c81019de05f6b140a462c31d5029adba23eb02ae13c1a1
tests/finance/test_postgresql_claim.py	66e0c4511b3fa696103a0dff8b3ea13a200b464d3573e87ed43925a77ee2a665
tests/host/test_api.py	353b99087ad5f806cd9af508dabffc0cb8f43411d5da2059edff33a7ad3174ca
tests/host/test_auth.py	6a408403fd1afe8a8b0e31a0b5786262ba26a0222c9e8cd31f9d8e8f3f42fe2b
tests/host/test_migrations.py	19f856c4bf05079f99b17cbf172f84f48765af4868777b1c5c88ba6d9377425f
tests/host/test_postgresql_r1.py	4fdec53c66e2d3c0e304f1be94c3ba2f02d3052dd6cb8b4f35c1eb1940e80718
tests/host/test_state.py	1c3dda17f9af516d390900291c1aa6dc42b4e4742b13ce5cd5bdbacf0ba6e5ec
```

有序总摘要：`P4-B6-R1-SHA256:13520520ebd351797f47fb1eb143e8e01b70e7a98975b51d9aca827df1fdc0f8`。

本文自身不能把自身最终文件摘要写入自身而保持摘要不变；因此上面的可复算总摘要只覆盖 22 个产品、migration 和执行方测试文件。本文最终 SHA-256 单独记录在执行智能体日志中，由总控复算时与本文件一起核对。

## 9. 未验证与停止点

- `tests/independent/**` 未运行、未读取为执行依据、未修改；P4-C11 仍未开始。
- P4-B6-R2、Agent runtime 接管、Electron、OpenClaw、微信和 DeepSeek 未启动或修改。
- 没有读取真实密钥、真实账户或真实个人数据；全部数据库数据为虚拟值。
- 没有执行 Git 写操作，也没有修改 control、冻结、D10、接管审计、C10 矩阵或其他角色状态。

执行方现停在 `review` / `finished`。下一步只能由头脑风暴总控核对快照并决定是否派发 R2；本任务不自行启动后续阶段。

## 10. P4-B6-R1-F1 外部身份并发绑定返修

### 缺陷原因与修复语义

R1 原实现先查询 active `(channel, external_subject_digest)`，没有冲突时再 INSERT binding。两个不同用户的有效 code 可以同时越过预查，随后在 PostgreSQL partial unique index 上竞争。直接调用 `AuthService.consume_binding_code()` 的外层曾把任意 `IntegrityError` 映射为业务冲突，但 Host HTTP 使用同事务的 `consume_binding_code_in_session()`，败方异常会穿过 Host command transaction 并返回 500；败方 receipt 也会随事务回滚。

F1 移除了 direct wrapper 对任意 `IntegrityError` 的兜底。binding INSERT 现在单独位于 SQLAlchemy savepoint 中，且 binding 只在进入 savepoint 后加入 Session，避免 `begin_nested()` 的预 flush 把错误抛到局部边界之外。败方只在以下条件同时成立时映射为 `channel_identity_conflict`：

1. PostgreSQL SQLSTATE 为 `23505`，并且诊断约束名精确为 migration 的 `uq_binding_active_subject` 或 ORM 建表路径的 `uq_channel_identity_active`；SQLite 则必须为 `SQLITE_CONSTRAINT_UNIQUE`，且错误列精确包含 `channel_identity_binding.channel` 和 `channel_identity_binding.external_subject_digest`。
2. savepoint 回滚后重新查询，确实存在相同 channel、相同 external subject digest、状态为 active 的竞争 binding。

满足竞争事实后，外层 Host command transaction 仍然有效：败方 code 从临时 consumed 恢复为 active，`consumed_at` 清空，attempts 保持 0；命令保存只含安全 code_id/status/error code 的 receipt，并对首次请求及同键同载荷重放都返回 409 `channel_identity_conflict`。赢家 binding 撤销后，败方可以用新 Idempotency-Key 消费原 code 并成功绑定。任何其他约束错误、无法确认竞争记录的目标唯一错误或 audit/receipt 错误均继续抛出，不被伪装成业务冲突。

### 失败前与通过后证据

| 检查 | 结果 |
| --- | --- |
| 修复前真实 PostgreSQL 定向竞争 | `1 failed, 1 warning in 2.29s`；两个事务经 INSERT 屏障同时越过预查，实际状态为 `[200, 500]`，期望 `[200, 409]` |
| 修复后同一定向竞争 | `1 passed, 1 warning in 1.97s`；恰好一项 200、一项 409，零 500 |
| 修复后最终新增 PG 案例单独复跑 | `1 passed, 1 warning in 2.27s`；0 failed、0 skipped |
| 本地 SQLite 顺序冲突定向及 auth 回归 | `17 passed, 1 warning in 14.73s` |
| 任务卡指定四份本地文件 | `41 passed, 1 warning in 32.99s`；`test_auth.py`、`test_api.py`、`test_state.py`、`test_migrations.py` 全部通过，0 failed、0 skipped |
| 原 R1 PostgreSQL 21 项 | `21 passed, 1 deselected, 1 warning in 9.27s`；deselect 仅为本轮新增案例以便分开计数，原 21 项 0 failed、0 skipped |
| 静态与依赖 | `pip check` 无破损；F1 三个实现/测试文件 `compileall` 退出 0；Alembic 仍只有 `p4_host_state` 一个 head |

唯一 warning 仍是第三方 Starlette `TestClient` 使用 AnyIO `BlockingPortal` 旧别名的 `DeprecationWarning`。没有屏蔽 warning，也没有把 warning 或 deselect 计入通过数。

新增 PostgreSQL 案例使用两个虚拟用户、两个不同有效 code、两个数据库连接和 `before_cursor_execute` INSERT 屏障，强制两边都越过冲突预查。断言覆盖：恰好一胜一冲突；败方 code active/attempts 0；初次竞争只有一个 active binding 和一条 bound audit；败方安全 receipt 同事务保存并可同键重放；赢家撤销后败方新键成功；响应、receipt 和日志不含原始 provider、subject、code、digest、SQL、目标约束名或 `IntegrityError`。

### PostgreSQL 资源状态

- 外部操作前分别重读 control，版本始终为 `2026-09-26T01:47:00+08:00`，F1 仍由既有执行智能体唯一负责。
- 只启动项目 Compose service `finance-postgres`；所有测试使用随机 schema、UUID 和虚拟 provider/subject，没有读取真实密钥、账户或个人数据。
- 最终执行普通 `docker compose down`，容器和项目 network 均移除；随后 `docker compose ps --format json` 退出 0、无输出，服务列表为空。
- 未执行 `down -v`、volume 删除、prune、Docker 全局设置修改或其他 service 启动。

### 文件边界、数量与快照

F1 共修改 5 个授权文件：3 个产品/执行方测试文件和 2 个交付记录文件；0 added、0 deleted。没有修改 `host_routes.py`、`state.py`、migration、模型、冻结/审查/起点快照、独立测试、R2 或其他角色文件，也没有执行 Git 写操作。

本轮发生内容变化的 3 个产品/执行方测试文件 SHA-256：

```text
src/wife_system/host/auth/service.py	745f22e4f1702fc76e38be9f793981bbefa055e6d4ec24a0b8ef3a8139563084
tests/host/test_api.py	779f3a32890e9a5dfed0fccc1c0979fde6118bdfb4a3027e0210161f0a8be540
tests/host/test_postgresql_r1.py	1a4dffabf133f2d6bb97d0e683b405c8785ca059f82ce5aab04fc082f117e618
```

继续使用第 8 节的 22 文件算法和行顺序；其中上述 3 行替换为新摘要，其余 19 行保持不变。新的可复算总摘要为：

```text
P4-B6-R1-F1-SHA256:e690882a291b8ec0210971d3bbed1f6da2252368cd9afff5213ff33798b87976
```

本文最终 SHA-256 在内容固定后单独记录到执行智能体日志；执行日志自身属于可变协调记录，不纳入 22 文件产品/测试总摘要。

### F1 停止点

- `tests/independent/**` 未运行、未修改；上述结果全部是执行方开发自测，不构成独立验收。
- P4-B6-R2、P4-C11、Electron、OpenClaw、微信和 DeepSeek 均未启动或修改。
- F1 交付状态为 `review`，运行状态为 `finished`；执行方在此停止，等待头脑风暴总控复算快照和决定后续派发。
