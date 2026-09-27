# P4-B6-R2 Host/Agent 运行时返修执行记录

## 交付状态

- 任务：`P4-B6-R2`
- 角色：执行智能体；本轮唯一实现负责人
- 当前状态：`blocked`；运行状态：`finished`
- 起点门禁：96/96 文件存在，0 缺失、0 不匹配；`P4-B6-R2-START-SHA256:7a80e083b0534c0f2547d859276f9c910b94a912b9b057ef95f8dbc9a74f3632`
- R1/F1 安全切片：22/22 文件匹配；`e690882a291b8ec0210971d3bbed1f6da2252368cd9afff5213ff33798b87976`
- 停止原因一：冻结的 `memory_candidate` 没有 `proposed_by_profile_version`，无法持久保存提出候选时的 Profile 版本；冻结的 `memory_item` 状态约束只允许 `active/deleted/superseded`，无法实现 `active -> invalidated`。任务卡禁止修改三个 P4 migration，并要求发现所需字段或约束时停止冲突范围、交回总控裁定。
- 停止原因二：真实 PostgreSQL 门禁开始前已重读最新 `control.md`。连续两个检查点都找不到 `dockerDesktopLinuxEngine` 命名管道，且没有 Docker Desktop 后端进程；没有项目容器成功启动，因此任务卡要求的 R2、R1、F1 PostgreSQL 实测不能执行。
- 结论：其余授权范围已实现并通过本地执行方回归；由于上述两项门禁仍未关闭，本任务没有进入 `review`，没有启动 C11，也不宣称 P4-A 完成。

## 12 个审计项

| 审计项 | 代码位置 | 执行方测试 | 结果 |
| --- | --- | --- | --- |
| P0-04 cancel/confirm 竞争 | `agent/pending.py` 的 `CommitClaim`、`claim_commit`、`mark_committed`、`cancel`；`agent/application.py` 的 `resume` | `test_cancel_is_terminal_cancelled_and_never_posts`、`test_active_commit_owner_blocks_second_confirm_and_cancel`、既有并发确认与恢复测试 | 本地通过。只有 commit lease owner 可首次调用 Finance；未过期 `committing` 对 confirm/cancel 返回 `commit_in_progress`；取消 run 保持 `cancelled` 且零财务事实。真实 PostgreSQL 竞争未验证。 |
| P0-05 run lease 接管 | `agent/application.py` 的 `start`、`_execute`、`_save_result`、`_save_exhausted`；`host/workflows.py` 的 lease CAS | `test_expired_run_takeover_executes_and_old_attempt_cannot_save`、`test_run_lease_is_user_scoped_sixty_seconds_and_three_attempts` | 本地通过。过期 run acquire 后重建计划并重新执行；旧 attempt 终态写被 `run_lease_lost` 拒绝；第三次耗尽有稳定错误路径。真实 PostgreSQL fence 未验证。 |
| P0-06 旧候选失效 | `agent/application.py` 的 `ExecutionPlanCompiler.compile` 和 `resume`；`agent/finance_tools.py` 的资源版本复查 | `test_resource_change_makes_candidate_stale`、registry 执行时 enablement/permission 测试 | module、permission、当前 Profile/version、工具与资源版本均在 resume 时复查。本地路径通过；候选无法持久保存“提出时 Profile version”，因此 Profile 版本绑定仍受冻结 schema 阻塞。 |
| P0-07 setting 秘密 | `host/contracts.py` 的递归 secret key 归一化；`host/state.py` 的 `ModuleSettingService.put` 前置校验 | `test_setting_secret_variants_fail_before_receipt_or_event` 四个参数；setting schema/CAS 测试 | 本地通过。大小写、嵌套、`_`、`-`、`.` 等变体在 receipt/事务前拒绝，零 setting、零 receipt、零 event。 |
| P0-08 candidate Profile grant/固定 target | `host/contracts.py` 的 `MemoryGrant.operations`；`host/state.py` 的 `propose`、`decide`；`api/host_schemas.py` 的空 decision DTO | memory confirm/retrieve/tombstone、API 固定 target 回归 | confirm 不接受 target，propose/confirm 复查 grant、module 与权限；本地固定 target 通过。候选 Profile version 无列可持久化，完整要求受冻结 schema 阻塞。 |
| P1-06 BoundToolRegistry 真实链 | `agent/application.py` 的 compiler 与 `_execute`；`agent/loop.py`；`host/tools/catalog.py` | `test_api_compiles_host_prompt_and_bound_tool_to_pending`、`test_write_tool_is_hidden_without_permission_and_direct_guess_is_denied` | 本地纵向链通过：认证 API → compiler → provider → BoundToolRegistry → pending。隐藏、猜名、禁用或失权统一 `tool_not_allowed`，不调用 handler。 |
| P1-07 Profile/prompt/conversation/memory | `agent/application.py` 的 `CompiledExecutionPlan`、`_history`、`compile`、`_claim_run`、`_append_message` | 真实纵向测试、conversation retention、memory 上限八条、持久 digest/privacy 测试 | 本地通过。顺序为 Host safety、Profile prompt、可信上下文、获准 confirmed memory、持久历史/工具事实、当前消息；历史最多 20 条且不超过 64 KiB；当前用户消息与 run claim 同事务。 |
| P1-08 provider/tool 续租与 attempt fence | `agent/loop.py` 的 provider/tool 前后 checkpoint 和 cooperative deadline；`agent/application.py` 的 checkpoint、message/terminal attempt fence | takeover/旧 attempt 测试、tool limit/deadline 相关回归 | 本地通过已覆盖的接管和旧终态写；provider/tool 前后及最终保存前均续租，assistant/tool/final 写入核对 attempt。真实 PostgreSQL 多 worker 未验证。 |
| P1-09 四类 post-commit event | `host/registry.py` 的 `HOST_CORE_EVENTS` 与 subscriber 装配；`agent/application.py`、`host/state.py`、`api/host_routes.py` 的发布点 | event 顺序/handler 隔离、setting/memory、认证 API 回归 | 本地通过。`host_core` 保留发布四类事件；mutation commit 后发布，handler 失败继续后续 handler，payload 只含安全 ID/状态。 |
| P1-10 memory 状态机/CAS | `host/state.py` 的 `decide`、`delete`、`supersede`、`retrieve` | memory confirmation/retrieval/tombstone、过期边界/limit 测试 | `active -> superseded`、未删除状态到 tombstone delete、检索 active/未过期/grant/最多八条已实现。本地通过；`active -> invalidated` 因冻结 check constraint 不允许该状态而停止。 |
| P1-11 production factory | `api/production.py`；`host/factory.py`；`host/runtime.py`；`api/app.py` | `test_production_config_fails_closed_without_echoing_secret`、`test_production_factory_readiness_tracks_provider`、Host/legacy import 互斥测试 | 本地通过。显式装配 engine/session、Finance、Host、Agent、activity import、registry/event；无 provider 时 fail closed 且 readiness 稳定。空 PostgreSQL schema 到 P4 head 冒烟未验证。 |
| P1-12 Page/cursor | `api/host_schemas.py` 的 `Page[T]`；`api/host_routes.py`；`host/cursor.py` | `test_page_endpoints_emit_bound_next_cursor`、authenticated conversation/cursor 测试 | 本地通过。三个端点使用 `limit + 1`，稳定排序和 `next_cursor`；cursor HMAC 绑定 endpoint、user、filter，跨端点或改 filter 被拒绝。真实 PostgreSQL 同时间排序未验证。 |

## 数据流

### start、takeover 与消息

1. 认证路由把 `user_id/session_id/device_id/channel/permissions/authenticated_at` 组成可信 Principal，用户 JSON 不能覆盖这些字段。
2. `ExecutionPlanCompiler.preflight` 核对 conversation 的 user、channel、module 与 Profile；run claim 和 sequence 0 用户消息在一个事务写入。
3. compiler 在每次 start/takeover/resume 绑定模块版本、enablement revision、Profile/version、BoundToolRegistry、memory grant、conversation、run/attempt 和 action schema。
4. provider 输入依次加入 Host safety、Profile prompt、可信上下文、最多八条 confirmed memory、受 20 条/64 KiB 限制的持久历史和当前消息。
5. provider 前后、tool 前后和 terminal 保存前调用 lease checkpoint；assistant/tool 消息只在 `(user_id, run_id, attempt_no, status=running)` fence 成立时写入。
6. terminal assistant message 和 run terminal state在同一事务提交，随后才发布 `agent.run_status_changed@1`。

### pending confirm 与恢复

1. confirm 先重新编译 Host plan，再核对 permission、Profile/module、pending 所有权、action handler 与资源版本。
2. `claim_commit` 以 status/version/commit attempt/lease CAS 返回不可变 `CommitClaim`；未持有 claim 的请求不能首次调用 Finance。
3. Finance 幂等键固定为 `pending:{pending_action_id}:commit`。领域提交后若 pending 完成前中断，lease 过期后的新 owner 使用同一键重放领域结果，再以新 claim fence 标记 committed。
4. cancel 只能从 `needs_input/needs_confirmation` 成功；活跃 `committing` 返回 `commit_in_progress`；已 committed/cancelled/expired 使用稳定状态错误或重放。

### memory、setting 与 event

1. memory proposal 固定 source module、target namespace 和 Profile ID；decision DTO 无 target 字段。
2. service 边界复查 module enabled、Profile ownership、grant operation 与权限；检索只取 active、未过期且获 grant 的最多八条。
3. setting 先执行严格 Pydantic/JSON、finite number、8 KiB、递归 secret key、registry declaration 和 module validator，再申请 receipt 和写事务。
4. mutation 提交后发布脱敏事件；subscriber 依内置模块注册顺序执行，单个 handler 错误不会回滚事实或重做 mutation。

### Page 与 production factory

1. conversations、messages、memory candidates 查询 `limit + 1`，返回 `Page{items,next_cursor}`。
2. cursor 含版本、endpoint、user、filter fingerprint、时间和 ID，并使用 HMAC 验证；任一绑定不一致即拒绝。
3. production factory 从显式配置创建数据库、Finance、HostRuntime、模块、Agent、活动导入和事件订阅；没有真实 provider 时 Agent 路由不可用，readiness 返回安全稳定原因。

## R1/F1 不变量保护

- 没有修改三个 P4 migration、auth service、auth model、state model、Finance service、activity import service或 R1 PostgreSQL fixture。
- 相对 96 文件起点，R2 仅变化任务卡允许的 20 个既有产品/执行测试文件，并新增 production factory、R2 Agent 测试、production 测试和本运行说明。
- R1 auth/receipt/activity import/user scope/migration 本地回归均包含在 Host 或 P0～P3 分组中并通过；F1 PostgreSQL 同步外部身份竞争只被收集后跳过，没有被称为通过。
- 未修改、未运行 `tests/independent/**`；未修改 C11 报告、P4 矩阵、control、overview 或其他角色文件。
- 没有启动 C11、Electron、OpenClaw、微信或 DeepSeek；没有读取真实密钥、账户或个人数据；没有执行 Git 写操作。

## 验证结果

| 检查组 | 结果 | 说明 |
| --- | --- | --- |
| R2 定向 | `52 passed, 2 warnings in 43.64s` | Agent 纵向链、pending/run、Host state/API/registry/workflow、production factory。 |
| Agent 执行方 | `32 passed, 2 warnings in 48.04s` | `tests/agent_finance/**`。 |
| Host 执行方 | `72 passed, 8 skipped, 2 warnings in 82.74s` | `tests/host/**`；8 skip 全为 PostgreSQL fixture。 |
| P0～P3 执行方回归 | `212 passed, 14 skipped, 2 warnings in 42.72s` | 根测试、Finance、activity import；4 Finance PG + 10 P3 PG skip。 |
| 全部 P4 执行方 | `104 passed, 8 skipped, 2 warnings in 113.20s` | Host + Agent；8 skip 全为 R1 PostgreSQL fixture。 |
| 全部非独立执行方 | `316 passed, 22 skipped, 2 warnings in 92.06s` | `tests --ignore=tests/independent`；316 个本地案例全通过。 |
| Python 编译 | 退出码 0 | `.venv\\Scripts\\python.exe -m compileall -q src`。 |
| 依赖检查 | `No broken requirements found.` | `.venv\\Scripts\\python.exe -m pip check`。 |
| 差异格式 | 退出码 0 | `git diff --check` 没有空白错误；仅报告现有文件下次被 Git 处理时 LF→CRLF 的行尾提示。 |
| 真实 PostgreSQL | `blocked / not_run` | Docker Engine 命名管道缺失，连续两个检查点无进展；没有把 skip 或 collection 计为通过。 |

### 失败、skip、warning 与未验证项

- 最终本地测试没有失败。首次集成定向测试发现两个旧语义断言，分别改为 commit lease 到期后恢复和候选固定 target；修正后全绿。
- 22 个 skip：P3 PostgreSQL 10、Finance PostgreSQL 4、R1/F1 Host PostgreSQL 8。原因均为 `FINANCE_TEST_POSTGRES_URL` 未设置，根因是 Docker Engine 不可访问。
- 两类 warning：Starlette `TestClient` 使用已弃用的 AnyIO alias；pytest 不能更新已有 `.pytest_cache/v/cache/nodeids`。它们不改变测试结论，也没有通过删除用户缓存来掩盖。
- 未验证：全部 R2 真实 PostgreSQL 并发/fence/message/memory/setting/event/Page/factory 场景；R1 21 项与 F1 同步外部身份竞争在本轮的真实 PostgreSQL 重放；冻结 schema 所阻塞的候选 Profile version 和 `invalidated`。
- PostgreSQL 资源状态：本任务没有成功启动任何容器，因此无本任务容器可执行 `down`；Engine 不可用使项目服务列表无法查询。没有执行 `down -v`、volume 删除、prune、Docker 全局设置修改或触碰保留 socket 目录。

## 文件边界与终点快照

相对固定的 96 文件起点：`unchanged=76`、`changed=20`、`added=4`、`deleted=0`，终点共 100 个文件。20 个 changed 和 3 个新增代码/测试文件均在任务卡授权范围；第 4 个 added 是本运行说明。执行智能体角色日志不属于 96 文件产品/测试快照，单独按协作规则更新。

运行说明不能在自身内容中保存其最终普通 SHA-256 而仍保持该摘要有效。下面的 100 文件终点摘要采用可复算的自引用规范：先把清单中 `docs/b6-r2-runtime-running.md` 的摘要字段替换为 64 个 `0`，对最终文件内容计算该文件的 canonical SHA-256，再把该 canonical 值用于有序清单和总摘要。文件写定后的普通 SHA-256 记录在 `docs/coordination/agents/executor.md`，不纳入本文件自身。其他 99 个文件均使用普通小写 SHA-256。

<!-- R2_SNAPSHOT_BEGIN -->
### R2 产品、执行方测试和运行说明逐文件摘要

格式为 `status<TAB>path<TAB>sha256`。运行说明一项使用下述 canonical 自引用摘要，其余均为普通文件 SHA-256。

```text
added	docs/b6-r2-runtime-running.md	a5c4f63500712048bd35a691fe135fb73b20bee3c94f63be6f5781c7f18f53d9
changed	src/wife_system/agent/application.py	5c6d2cc4a3bce3cc96a3c016b440a03b9201aba0f4cdceaa7432c6501237eedd
changed	src/wife_system/agent/context.py	7d4a31cacc23e8ca6f4ac9dc6833bd283c5cc31392ff2ed8f71c9b8f70b9a2ea
changed	src/wife_system/agent/finance_tools.py	51ff6804c2441c4d67ecb9e6ef6ed52020ec62421944b03c142f7e59f23d3d6d
changed	src/wife_system/agent/loop.py	80f1620c6ec8c6acc9f10f2e7052c6d67c09ed0286eac75db1501e4c3d3e353b
changed	src/wife_system/agent/pending.py	42dd85572c5f38b3a511d8c5c5dd18817d77e7279dc45d192dd814fb4a701001
changed	src/wife_system/api/agent_routes.py	755f2bdf85ec1a83b9482757b8dd5cf1627bfe8956102042db9936146a0e3f23
changed	src/wife_system/api/app.py	8ec05220b3483c6a6ea73ce231064204847635a6a6c1b9f9d70ecc9c8ccfa7e3
changed	src/wife_system/api/host_routes.py	7afcb0ed20618a7e8e66f14b94aa6dbd881505c8835afee4ae5aa291627c94e8
changed	src/wife_system/api/host_schemas.py	7492a327b2feca1c74f6e2024c1abd76218ebd87afa86d5a35359eee00d361be
added	src/wife_system/api/production.py	6abcf39bb7ba882f1ab938fb043dfd02242c858a33d1197102536dd20910cb6f
changed	src/wife_system/host/contracts.py	9b4e4c1c1bc0e4670e4843ce07a820db2d1dfe8060d7cc0ec842c68669cbd7cc
changed	src/wife_system/host/cursor.py	3c7697a3efa61eaeb36eca2538812650b6ca11eb31b45e7e1927955ccb15e604
changed	src/wife_system/host/factory.py	3cc7d272ff79534e1b90e19931d594f0bba893616442983682925bd3156522e6
changed	src/wife_system/host/registry.py	d20a346118425015cee3783c7f0193c283f29dfa3a7cf09c4abfeb1896e476ed
changed	src/wife_system/host/runtime.py	1475dbe83c12fe2cbdde50c50b409477ba5716c10c3c4ae755d890214af2af65
changed	src/wife_system/host/state.py	cc32dd15395a260f050c1f9d1f1afbbf1efd63e7a7a6fe18296a79a5b3fd6bfb
changed	src/wife_system/host/tools/catalog.py	c3dd38f4fff84e8174dd742c59d21676a30b035ec64380047424961162a0dbd1
changed	src/wife_system/modules/daily_finance.py	0c40fb956fcfa0cd9fc0549dc34a63385c7ebecc82cfac942ca2d236c5b8ffbe
changed	tests/agent_finance/test_failures_and_policy.py	d711445d0ffa768658c8f3d7f60abe90bc533a1790c3274af377a6b89a1ec24b
added	tests/agent_finance/test_r2_runtime.py	e3b89ec5dc68eb2b1fe9ac55fc1942c60a0bc2a8690b8303591930ef01ee4f75
changed	tests/host/test_api.py	a8a75bd8489e0ab92e8a391ce143dd40abf1739c36baa3c1d6433ed80e817687
added	tests/host/test_production.py	519e007fc173758f807ecaaa9b16853f06c0527bca259e94e07c8a79e6ac0a13
changed	tests/host/test_state.py	0d15331487ecf526c911219b29e9128204494ac47e8092dd04a83e2430a7dc55
```

### 100 文件完整有序终点清单

- `unchanged=76`
- `changed=20`
- `added=4`
- `deleted=0`
- `running_note_canonical_sha256:a5c4f63500712048bd35a691fe135fb73b20bee3c94f63be6f5781c7f18f53d9`
- `P4-B6-R2-END-SHA256:d8ff817da54875bcf2ca899a9b739e11438cd7f710f6e6ebeddbf6f8d2d588d5`

总摘要算法：按下面路径顺序拼接 `path<TAB>sha256<LF>`，对 UTF-8 字节计算 SHA-256；运行说明使用 canonical SHA-256。

```text
alembic.ini	de081bf4df3368de8a113700ded32074df005ae43dd9c56e1eb16363e58eeb1e	unchanged
compose.yaml	c3d6355b9fc594684fde078a29cca2e3377ff97797d440af30c30b68fa7d11d2	unchanged
docs/b6-host-foundation-running.md	49536bf5858c705d748f42d0b53c0df201eccd880039ed9e8663b4be353461c5	unchanged
docs/b6-r1-security-data-running.md	e5c67b7851ca3aa92a27626db089bd99afbad1de536ceee9dd4542335ec1dde9	unchanged
docs/b6-r2-runtime-running.md	a5c4f63500712048bd35a691fe135fb73b20bee3c94f63be6f5781c7f18f53d9	added
migrations/versions/1377551283d0_enforce_sqlite_integer_minor_storage.py	8b41a7b24a47ebb670d7a9405d6f4b410aeefae6cf5753b5b554b4bbb9a02f7b	unchanged
migrations/versions/7f3e2d1c9a4b_add_agent_run_and_pending_action.py	051c4fa47a2676d2848532b5cce00c0d39e0848b9307b9ceef4adc7db1554a64	unchanged
migrations/versions/bfc163b9b8e9_create_finance_foundation.py	c704d2e3187181dc1e1f5acb2a5b0b940459765756dffe4ae3574f1ca038c073	unchanged
migrations/versions/c82d7a4f901e_add_activity_import.py	e0703c5a87f792a5e7c4414192aefd1a6ed00a328094f18dc0b4db26e9e24a0d	unchanged
migrations/versions/p4_host_identity.py	d6de5bc19b23e2584bba5fb78cf948ca2babff746cfa7f688d58b2e0ed8349bc	unchanged
migrations/versions/p4_host_state.py	8d83992fcae126005e9e82408e21104a429e0a61a1125d8cfb8c3d180c7e7a37	unchanged
migrations/versions/p4_host_user_scope.py	649cf372e9bbadc6aaecf6bad4f7daac9b1be68fb663c4dc36b8376df9817e8c	unchanged
pyproject.toml	18e0125419259b37cc27afbd5da742e104354ac1da567af3933916c9a25e5a12	unchanged
requirements-dev.lock	5106a8355453fa6e7ed96fe1879edb901a4e063a1339c4d6c32077aff4f6b564	unchanged
src/wife_system/__init__.py	ce17c401b99449f7eeb629b592061a506d051613f0b91d61bd3f288462396e7f	unchanged
src/wife_system/activity_import/__init__.py	c07e7c4533114149d1ecc0e7c4d7d50ccbcbc159f331d1e6c4dd1d4c91403b0c	unchanged
src/wife_system/activity_import/context.py	4b055802d5c2c23047bad5490bf3a76e15ac041b5ac8423186f2a76923579d1f	unchanged
src/wife_system/activity_import/errors.py	3b48cbb882017754c0e52327e2d856d78cdb32adf3662f957b8a641dac7779b1	unchanged
src/wife_system/activity_import/parser.py	12b003b5b47469c1fc3badd9a8396406801651786b984674d3566b9b0c275a05	unchanged
src/wife_system/activity_import/repository.py	3fef4a21ee6ad645b20596de419af8d78ddb2b87f498340f7b6ffc68ed3790e3	unchanged
src/wife_system/activity_import/schemas.py	ecfc8ccd748557090e8bdf3fde3ae7d0af6c6147457d86f3f52c62d1c5739ff7	unchanged
src/wife_system/activity_import/service.py	bfa200b437abde8ead703d1994d3c929ad17ae79796ec924ee18a640d83dc8a3	unchanged
src/wife_system/agent/__init__.py	188ecc30cf52de7cc9209adefe32bfd56188b78924d7a1884bcc08c5d5ac915b	unchanged
src/wife_system/agent/application.py	5c6d2cc4a3bce3cc96a3c016b440a03b9201aba0f4cdceaa7432c6501237eedd	changed
src/wife_system/agent/context.py	7d4a31cacc23e8ca6f4ac9dc6833bd283c5cc31392ff2ed8f71c9b8f70b9a2ea	changed
src/wife_system/agent/finance_tools.py	51ff6804c2441c4d67ecb9e6ef6ed52020ec62421944b03c142f7e59f23d3d6d	changed
src/wife_system/agent/loop.py	80f1620c6ec8c6acc9f10f2e7052c6d67c09ed0286eac75db1501e4c3d3e353b	changed
src/wife_system/agent/models.py	394969acddaadf2d5229be1f44cc7f45983e0c313115aa6dba69e15e0c9fbbf1	unchanged
src/wife_system/agent/pending.py	42dd85572c5f38b3a511d8c5c5dd18817d77e7279dc45d192dd814fb4a701001	changed
src/wife_system/agent/prompts.py	81e40e83c0edeb6eba7da89abb5c9983bdc45ce650c3714bf65f8f54d609c885	unchanged
src/wife_system/agent/providers.py	245602fdc80cbc99558d43430378301369da1f1ef30920bc3671217440a586ce	unchanged
src/wife_system/agent/types.py	a80c4e6e80c789d8041032de633719742aaa63bbbf4c3107b02652bf600fffdb	unchanged
src/wife_system/api/__init__.py	f2b19dab818028174923dfd94fa5aa7c0133f44c7266fca0fb1ea18d49131634	unchanged
src/wife_system/api/activity_import_routes.py	da607e2e06a42883108844025f12d689e28817d47bf65618e4ce2876fe0f94e2	unchanged
src/wife_system/api/agent_routes.py	755f2bdf85ec1a83b9482757b8dd5cf1627bfe8956102042db9936146a0e3f23	changed
src/wife_system/api/agent_schemas.py	794319176ce4624700a03ba5b6c39c6b8de6f9ac257998338792a3d832de96a8	unchanged
src/wife_system/api/app.py	8ec05220b3483c6a6ea73ce231064204847635a6a6c1b9f9d70ecc9c8ccfa7e3	changed
src/wife_system/api/host_routes.py	7afcb0ed20618a7e8e66f14b94aa6dbd881505c8835afee4ae5aa291627c94e8	changed
src/wife_system/api/host_schemas.py	7492a327b2feca1c74f6e2024c1abd76218ebd87afa86d5a35359eee00d361be	changed
src/wife_system/api/production.py	6abcf39bb7ba882f1ab938fb043dfd02242c858a33d1197102536dd20910cb6f	added
src/wife_system/api/schemas.py	970c668d0045b27a04eac13a4571e28cc24fa8ad7ace6f67288b8a6b9bdce647	unchanged
src/wife_system/cli.py	658b0fc9902fef0f34dc1e12fd22e143bba74f8b37a7383944f5f8709aea6fc0	unchanged
src/wife_system/finance/__init__.py	84f4b9d9b02ca9b60bf241799dba1947644741ce4d688f94bbbd15d151498219	unchanged
src/wife_system/finance/db.py	f112f754274638a0b6327c2172d0d6a73d87fd3f61203c9ddda3a745d169f7cd	unchanged
src/wife_system/finance/errors.py	930bebc1c7f7798c3b0f34aa9eb3bfd519dad0cf0995d172cb9048456c1131fc	unchanged
src/wife_system/finance/models.py	90290d2c0f3711a5235fb3b07110e4fd9a5ca6e2cac14ad5846b8a869b90bd21	unchanged
src/wife_system/finance/money.py	65f646e1c3ea9dae13c121b5ab06c0fb9bc45ff54743899337b1227cd1999e19	unchanged
src/wife_system/finance/repositories.py	7f8cf348af949ff8d081a5483837e9f83d4112fd0068e91958aee1244e8230ac	unchanged
src/wife_system/finance/schemas.py	cf5a00dd5afd9e3267112632093b8d7a33bfe351ce8177db4070f8029651f015	unchanged
src/wife_system/finance/service.py	76abe42b88c5c89d967113c0859bb55a722a474dc84cd9ef0aa3ebc81d565fcb	unchanged
src/wife_system/host/auth/__init__.py	d5b56ebef9de1ae83206da1ce8d7278414c069b9d8bc430160e8563f8c124972	unchanged
src/wife_system/host/auth/errors.py	4621b90ff0f058143e7e82f4f5f9569538edf96de0b21832859a58a9c30900b1	unchanged
src/wife_system/host/auth/models.py	293e467c8c7aabf67b2a786d91f98e5ffaf847d0c9386692937111a456fa5fbd	unchanged
src/wife_system/host/auth/service.py	745f22e4f1702fc76e38be9f793981bbefa055e6d4ec24a0b8ef3a8139563084	unchanged
src/wife_system/host/context.py	8c8c4b26038a2bd6f50ebc0fefca9fcebc31f6c9856c4a10c3d21ebef67c3921	unchanged
src/wife_system/host/contracts.py	9b4e4c1c1bc0e4670e4843ce07a820db2d1dfe8060d7cc0ec842c68669cbd7cc	changed
src/wife_system/host/cursor.py	3c7697a3efa61eaeb36eca2538812650b6ca11eb31b45e7e1927955ccb15e604	changed
src/wife_system/host/events.py	b11b2bfc7995071fb02e8a753d1aa070c16855dea53b74473ee91098a5a4e009	unchanged
src/wife_system/host/factory.py	3cc7d272ff79534e1b90e19931d594f0bba893616442983682925bd3156522e6	changed
src/wife_system/host/registry.py	d20a346118425015cee3783c7f0193c283f29dfa3a7cf09c4abfeb1896e476ed	changed
src/wife_system/host/runtime.py	1475dbe83c12fe2cbdde50c50b409477ba5716c10c3c4ae755d890214af2af65	changed
src/wife_system/host/state.py	cc32dd15395a260f050c1f9d1f1afbbf1efd63e7a7a6fe18296a79a5b3fd6bfb	changed
src/wife_system/host/state_models.py	0121655c97ca6e258bb5ff3053cd0b83767cfc81637c25859e3fcc0cb20dd3b1	unchanged
src/wife_system/host/tools/__init__.py	cd91c663da5e5ac20ba0e7ae2ecc8a16257f9df6bc0c046c2412a72705e34182	unchanged
src/wife_system/host/tools/catalog.py	c3dd38f4fff84e8174dd742c59d21676a30b035ec64380047424961162a0dbd1	changed
src/wife_system/host/workflows.py	9ba19486d7a7b921e2d8e7939a4ceaf3b864d607e0a4431250458678d76c61c3	unchanged
src/wife_system/modules/__init__.py	76b0c072512dfb6c844cc5fb01da8c5fea677d47283d55dc4dc6189d7a811bd9	unchanged
src/wife_system/modules/daily_finance.py	0c40fb956fcfa0cd9fc0549dc34a63385c7ebecc82cfac942ca2d236c5b8ffbe	changed
src/wife_system/probes.py	a9f2f9fd0fc555733aed8f5b7b8f87599ac7c9ecd5e214b2488833b5d247b8f0	unchanged
src/wife_system/tools.py	5ac23117241f5091b0561cc9075c00fa7d59f2f366bbad167927621b46e7a4a3	unchanged
tests/activity_import/__init__.py	f371abdeb05764ed0f4c2403c7a259c87f05f0885c663b39f3dbf501b9d1b814	unchanged
tests/activity_import/test_api.py	a9d59c3401328148d87bca8eba607ea1c193155b17cf28298e7f1dfe49f04b22	unchanged
tests/activity_import/test_migration.py	af173de0b65e128b053c63d2ebb2db88b1990fa29fb8a8e6b6a8db176f8d3baa	unchanged
tests/activity_import/test_parser.py	d4d8266fb7838a7b0cef9b6ad0e1e2bfc4d84bc32d97d8590120a6a74193da4b	unchanged
tests/activity_import/test_postgresql.py	ac217ef3c5a192630675939f67e3994326c419abb17e1a6abdce71ca1e778a2b	unchanged
tests/activity_import/test_schemas.py	417e99ab913f747cf4b42be8d25a91997023930e6c4b7fad3506639c3697c592	unchanged
tests/activity_import/test_service.py	d2908aa0288a29cf77c81019de05f6b140a462c31d5029adba23eb02ae13c1a1	unchanged
tests/agent_finance/__init__.py	a94ceade41249f0bdecc5ce6addc146136fbe01588006acf82fdb078538e110c	unchanged
tests/agent_finance/conftest.py	708dbb7307118b55f088c00643ac234146d79f967821a46653f89b349774cda3	unchanged
tests/agent_finance/test_clock.py	0993de72189561133d3614592abd6fd723ba9cf5c7b2aafdcc08bc7a2fc48b85	unchanged
tests/agent_finance/test_failures_and_policy.py	d711445d0ffa768658c8f3d7f60abe90bc533a1790c3274af377a6b89a1ec24b	changed
tests/agent_finance/test_migration.py	c81ce242dea1fa853909363f39bd0f238591f8a74e05a2729a84dc7957bc9c32	unchanged
tests/agent_finance/test_r2_runtime.py	e3b89ec5dc68eb2b1fe9ac55fc1942c60a0bc2a8690b8303591930ef01ee4f75	added
tests/agent_finance/test_tools_and_http.py	31f3765c16f54bb3af9c6420a64266498edeb8466cfd4516a9f5027e4222c1ed	unchanged
tests/agent_finance/test_vertical_slice.py	1f4b140416551e692a9d4d42e66cb8c78b0cfabed4b4982af6fcdbcee9f72b8f	unchanged
tests/finance/conftest.py	4b81763da9c521f25d1e68fb48fd4dfbb52d4ed3a0792d40d5c66118e9d90313	unchanged
tests/finance/test_migrations.py	670f8cf45b0257018f1d895ae35def8a5823ff85a9184f9fa1995ef53869015e	unchanged
tests/finance/test_money.py	11009ee0a10c4e44dad3f3b1894b748029d01f9e28fcb2fb4a3847eb1530e930	unchanged
tests/finance/test_postgresql_claim.py	66e0c4511b3fa696103a0dff8b3ea13a200b464d3573e87ed43925a77ee2a665	unchanged
tests/finance/test_r1_regressions.py	d584ab67cd6b0a9ea52ccd684c4fc23f855aa44a17186e7e1e9b42b7935af8c6	unchanged
tests/finance/test_service.py	7efa88741d73ec89ad96edb55d6da650388433d568e581cff90e38f45dee6753	unchanged
tests/host/__init__.py	8f173bc3a42ca2ae4d72ffa47f36663208b88144d882901872b3db1d19e15d46	unchanged
tests/host/test_api.py	a8a75bd8489e0ab92e8a391ce143dd40abf1739c36baa3c1d6433ed80e817687	changed
tests/host/test_auth.py	6a408403fd1afe8a8b0e31a0b5786262ba26a0222c9e8cd31f9d8e8f3f42fe2b	unchanged
tests/host/test_contracts_registry.py	2219e926c5f7131c4772ac4daf51255996967dc93335e271b78f3e022da55c97	unchanged
tests/host/test_migrations.py	19f856c4bf05079f99b17cbf172f84f48765af4868777b1c5c88ba6d9377425f	unchanged
tests/host/test_postgresql_r1.py	1a4dffabf133f2d6bb97d0e683b405c8785ca059f82ce5aab04fc082f117e618	unchanged
tests/host/test_production.py	519e007fc173758f807ecaaa9b16853f06c0527bca259e94e07c8a79e6ac0a13	added
tests/host/test_state.py	0d15331487ecf526c911219b29e9128204494ac47e8092dd04a83e2430a7dc55	changed
tests/host/test_workflows.py	8c8c7256b87ea5f0adcaec0e64d1e745c5c1e3ecf55e7f7e14b3facbe03897f2	unchanged
```
<!-- R2_SNAPSHOT_END -->

## 需要总控裁定

1. 为 `memory_candidate` 增加可持久化的 `proposed_by_profile_version`，并决定现有候选的迁移默认/回填规则；替代方案只能是放弃版本绑定，不能满足 R2 冻结要求。
2. 扩展 `memory_item.status` 约束以允许 `invalidated`，并明确 downgrade 映射；替代方案是把 invalidation 映射为 superseded/delete，但会丢失冻结合同要求的独立状态语义。
3. Docker Desktop Engine 恢复后，重新派发真实 PostgreSQL 门禁；必须运行任务卡列出的 R2 场景以及 R1/F1 回归，普通 `docker compose down` 并确认项目服务列表为空。
