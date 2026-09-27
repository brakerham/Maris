# P4-C11 Host 地基独立验收报告

- 角色：测试智能体
- 任务：`P4-C11`，含 `P4-C11-R1/R2` 历史迁移补证与定向复验
- 控制版本：`2026-09-27T12:19:00+08:00`
- 最终状态：`review / finished`（R2 已独立复验 E1 修复并建议关闭 PostgreSQL 历史迁移阻断）
- 数据边界：仅虚拟用户、虚拟财务和虚拟渠道数据
- 产品结论权限：本报告只给出测试方建议，P4-A 是否 `complete` 由头脑风暴总控决定

## 1. 固定快照与资源边界

原 C11 起点和终点均逐行读取 `docs/coordination/snapshots/p4-c11-start.sha256` 并重新计算 105 个文件：`matched=105`、`missing=0`、`mismatch=0`。P4-C11-R1 开始前再次得到同一结果；R1 终点复算见 R1 独立证据报告。清单文件 SHA-256 始终为 `65ee400893171d6caf19f2bf5adf20a4432f1f3c8048d5c381b718fc10360126`。测试过程没有修改 105 个固定产品、migration、执行方测试或运行说明文件。

R2 使用 `docs/coordination/snapshots/p4-c11-r2-start.sha256` 固定 133 文件，开始前为 133 matched、0 missing、0 mismatch，manifest SHA-256 `7ab8388edcadff5515aa5f038df13e40ae35233f2e4298c61fcd091357929fd3`。终点所有产品、migration、执行方测试、依赖和配置继续逐文件零漂移；授权的独立测试、矩阵、报告和 tester 状态变化单独列在 R2 报告。

Docker Engine `29.8.0`、Compose `v5.5.1` 可达。启动前 `docker compose ps` 为空；只执行 `docker compose up -d finance-postgres`，服务达到 `running / healthy`。测试结束执行普通 `docker compose down`，最终输出 `COMPOSE_SERVICES_EMPTY`。没有使用 `-v`，没有删除 volume、prune、重置数据库或改 Docker Desktop 设置。

未执行 Electron、OpenClaw、微信、DeepSeek、真实 provider、真实账户、行情、交易或个人数据案例。

## 2. 结果总览

| 分组 | 最终结果 | 说明 |
|---|---:|---|
| P4-A 独立 contract/API/SQLite | 23 passed | 1 个 Starlette/AnyIO 第三方弃用警告 |
| P4-A 独立 PostgreSQL | 5 passed | 随机 schema；约束、并发、恢复和 readiness |
| 既有独立 P1 PostgreSQL | 8 passed | P4 head/user scope fixture 升级后全绿 |
| 既有独立 P2 PostgreSQL | 4 passed | P4 owner/Principal/时钟/lease fixture 升级后全绿 |
| 既有独立 P3 PostgreSQL | 10 passed | P4 owner/head fixture 升级后全绿 |
| 执行方 Host R1 PostgreSQL | 8 passed | 单独统计，不作为 64 项独立证据 |
| 执行方 Host R2 PostgreSQL | 9 passed | 单独统计，不作为 64 项独立证据 |
| 执行方 Finance PostgreSQL | 4 passed | 单独统计 |
| 执行方 Activity Import PostgreSQL | 10 passed | 单独统计 |
| 执行方 P1/P2/P3/P4 本地 | 28 / 35 / 145 / 79 passed | 分目录、排除 PG 后运行 |
| P0 执行方本地 | 39 passed | 无真实 DeepSeek |
| P0 独立本地 | 102 passed, 2 failed | 两项已知 Windows/uvicorn 8 秒健康等待问题，未进入业务断言 |

原 C11 曾按当时证据把 P4-A 64 项全部更新为 `passed`。R1 恢复真实历史正向升级后，`P4A-DB-05` 和 `P4A-DB-06` 暴露同一真实 PostgreSQL 产品迁移阻断，状态一度纠正为 P4-A `62 passed / 2 failed`。R2 在 E1 固定修复输入上完成独立复验后，两项均恢复为 `passed`，P4-A 当前为 `64 passed / 0 failed`；P4-B、P4-C、P4-D 共 56 项保持 `not_run`。

| R1 定向补证 | 最终结果 | 说明 |
|---|---:|---|
| P1 首版 SQLite 正向升级文件 | 8 passed | 从 `bfc163b9b8e9` 直接 SQL 写入 P1 事实后升级 P4 |
| Host SQLite 历史迁移文件 | 3 passed | 新节点从 P3 head 写入 P1/P2/P3 历史后升级 P4 |
| cancelled 后 confirm 精确节点 | 1 passed | `pending_action_cancelled`，财务写入为零 |
| Host PostgreSQL P3 历史正向升级节点 | 1 failed | 合法 P1 双分录历史触发 `ObjectInUse`，P4 migration 无法完成 |

| R2 定向复验 | 最终结果 | 说明 |
|---|---:|---|
| 原失败 PostgreSQL P3 历史正向升级节点 | 1 passed | 唯一实际运行一次；事实、owner、约束、无 persistent default、重复升级与往返均通过 |
| 独立非法 P3 历史 | 2 passed | orphaned run 与 contradictory owner 均在 P4 DDL 持久化前安全拒绝并完整回滚 |
| 独立 PG round-trip/catalog | 1 passed | 真实复合 FK/unique/check 与跨 user 阻断继续生效 |
| 独立 Host SQLite migration | 3 passed | 首次 3 个 setup error 未进入断言；建立专用临时父目录后全绿 |
| 执行方 PostgreSQL / SQLite migration | 11 / 8 passed | 单独统计的兼容回归；不替代独立证据 |

## 3. P4-A 64 项逐 ID 证据

表内 node ID 均可由项目根目录直接传给 pytest；同一纵向节点覆盖多个冻结不变量时逐行列出对应断言。

| ID | 完整 pytest node ID | 环境 | 结果 | 关键断言与实际证据 |
|---|---|---|---|---|
| P4A-REG-01 | `tests/independent/host/test_contract_acceptance.py::test_c11_contracts_are_strict_frozen_and_limit_profiles` | contract | passed | DTO 严格、冻结、额外字段拒绝、全局上限不可放宽 |
| P4A-REG-02 | `tests/independent/host/test_contract_acceptance.py::test_c11_registry_is_atomic_and_builtin_composition_is_explicit` | contract | passed | 重复模块原子失败，无覆盖 |
| P4A-REG-03 | `tests/independent/host/test_contract_acceptance.py::test_c11_registry_is_atomic_and_builtin_composition_is_explicit` | contract | passed | Host API major 不兼容在启动期失败 |
| P4A-REG-04 | `tests/independent/host/test_contract_acceptance.py::test_c11_registry_is_atomic_and_builtin_composition_is_explicit` | contract | passed | builtin 显式组合；无 entry point、目录扫描或动态 import |
| P4A-REG-05 | `tests/independent/host/test_contract_acceptance.py::test_c11_bound_registry_rechecks_permission_and_module_state` | contract | passed | 执行时复核 module enabled，禁用后工具拒绝且无调用 |
| P4A-REG-06 | `tests/independent/host/test_contract_acceptance.py::test_c11_profile_ownership_and_tool_results_reject_invalid_unions` | contract | passed | Profile 必须归属 manifest module，不能串模块 |
| P4A-REG-07 | `tests/independent/host/test_contract_acceptance.py::test_c11_bound_registry_rechecks_permission_and_module_state` | contract | passed | 只有已启用且获准 Profile/工具可绑定，猜测写工具被拒 |
| P4A-REG-08 | `tests/independent/host/test_contract_acceptance.py::test_c11_contracts_are_strict_frozen_and_limit_profiles` | contract | passed | 事件/设置/manifest 版本与额外形状严格拒绝 |
| P4A-REG-09 | `tests/independent/host/test_api_acceptance.py::test_c11_health_bootstrap_login_and_safe_module_summary` | API/SQLite | passed | `/modules` 只返回安全摘要，不含 factory、prompt、路径或 secret |
| P4A-REG-10 | `tests/independent/host/test_contract_acceptance.py::test_c11_ids_are_exact_ascii_and_never_normalized` | contract | passed | 大小写、前导空白、非法 SemVer、Unicode ID 均拒绝 |
| P4A-PRF-01 | `tests/independent/host/test_contract_acceptance.py::test_c11_profile_ownership_and_tool_results_reject_invalid_unions` | contract | passed | module/Profile 不匹配稳定拒绝 |
| P4A-PRF-02 | `tests/independent/host/test_contract_acceptance.py::test_c11_contracts_are_strict_frozen_and_limit_profiles` | contract | passed | 轮次、工具、写调用和超时均不能超过 Host 上限 |
| P4A-PRF-03 | `tests/independent/agent_finance/test_idempotency_and_loop.py::test_retry_policy_distinguishes_transient_and_permanent` | SQLite | passed | 有界重试，永久错误不隐藏重试，写入不多执行一次 |
| P4A-PRF-04 | `tests/independent/host/test_contract_acceptance.py::test_c11_bound_registry_rechecks_permission_and_module_state` | contract | passed | Schema 是 Profile、permission、module enabled 三者交集 |
| P4A-PRF-05 | `tests/independent/host/test_contract_acceptance.py::test_c11_bound_registry_rechecks_permission_and_module_state` | contract | passed | 绕过 Schema 猜写工具仍为 `tool_not_allowed`，handler 零调用 |
| P4A-PRF-06 | `tests/independent/agent_finance/test_tools_and_lifecycle.py::test_schema_hides_context_and_all_tools_forbid_context_override` | SQLite | passed | 工具 DTO 不暴露或接受身份/context 覆盖 |
| P4A-PRF-07 | `tests/independent/agent_finance/test_tools_and_lifecycle.py::test_commit_replay_receipt_balance_and_result_are_single_source` | SQLite | passed | 财务候选、确认、receipt、余额和重放保持 P1 语义 |
| P4A-PRF-08 | `tests/independent/host/test_contract_acceptance.py::test_c11_no_arbitrary_execution_or_mcp_surface_is_registered` | contract | passed | 未注册 SQL/Python/shell/file/任意 MCP 入口 |
| P4A-PRF-09 | `tests/independent/host/test_contract_acceptance.py::test_c11_no_arbitrary_execution_or_mcp_surface_is_registered` | contract | passed | 当前切片无 MCP/HTTP adapter 入口，猜测名称不可连接且零副作用 |
| P4A-PRF-10 | `tests/independent/host/test_contract_acceptance.py::test_c11_profile_ownership_and_tool_results_reject_invalid_unions` | contract | passed | ToolExecutionResult 严格联合，非法 ok/error 组合拒绝 |
| P4A-AUT-01 | `tests/independent/host/test_postgresql_acceptance.py::test_c11_pg_auth_initialize_refresh_and_binding_linearize` | PostgreSQL | passed | 两并发 initialize 恰好一成功、一 `already_initialized` |
| P4A-AUT-02 | `tests/independent/host/test_api_acceptance.py::test_c11_health_bootstrap_login_and_safe_module_summary` | API/SQLite | passed | bootstrap 状态单向切换，初始化后不再建立第二 owner |
| P4A-AUT-03 | `tests/independent/host/test_api_acceptance.py::test_c11_health_bootstrap_login_and_safe_module_summary` | API/SQLite | passed | 虚拟密码只用于登录，响应与模块摘要不含密码/secret |
| P4A-AUT-04 | `tests/independent/host/test_api_acceptance.py::test_c11_untrusted_identity_fields_and_framework_errors_use_envelope` | API/SQLite | passed | 严格 body；认证/框架错误统一 request-id envelope |
| P4A-AUT-05 | `tests/independent/host/test_api_acceptance.py::test_c11_health_bootstrap_login_and_safe_module_summary` | API/SQLite | passed | access 只从登录响应取得，受保护端点使用可信 token |
| P4A-AUT-06 | `tests/independent/host/test_postgresql_acceptance.py::test_c11_pg_auth_initialize_refresh_and_binding_linearize` | PostgreSQL | passed | 同 refresh 并发最多一成功，另一为 replay 并撤销族 |
| P4A-AUT-07 | `tests/independent/host/test_state_acceptance.py::test_c11_sessions_password_boundary_and_binding_attempt_limit` | SQLite | passed | logout 后 token 立即 `session_revoked`；旧 access 在改密后撤销 |
| P4A-AUT-08 | `tests/independent/host/test_state_acceptance.py::test_c11_sessions_password_boundary_and_binding_attempt_limit` | SQLite | passed | 恰好 access 到期时改密拒绝；前一微秒成功并撤销旧 session |
| P4A-AUT-09 | `tests/independent/host/test_postgresql_acceptance.py::test_c11_pg_auth_initialize_refresh_and_binding_linearize` | PostgreSQL | passed | 同绑定码并发仅一成功，另一稳定 invalid；库仅摘要 |
| P4A-AUT-10 | `tests/independent/host/test_postgresql_acceptance.py::test_c11_pg_auth_initialize_refresh_and_binding_linearize` | PostgreSQL | passed | active 外部身份唯一，最终仅一 active binding |
| P4A-ISO-01 | `tests/independent/host/test_api_acceptance.py::test_c11_untrusted_identity_fields_and_framework_errors_use_envelope` | API/SQLite | passed | body 伪造 `user_id` 以 422 拒绝，不覆盖 principal |
| P4A-ISO-02 | `tests/independent/finance/test_ledger_contract.py::test_missing_archived_and_wrong_kind_references_have_stable_errors` | SQLite | passed | 跨范围/不存在资源统一稳定错误且无财务写入 |
| P4A-ISO-03 | `tests/independent/host/test_postgresql_acceptance.py::test_c11_pg_migration_round_trip_and_real_constraint_catalog` | PostgreSQL | passed | 三条复合 user FK 用直接 SQL 跨用户更新均触发 IntegrityError |
| P4A-ISO-04 | `tests/independent/host/test_postgresql_acceptance.py::test_c11_pg_receipt_setting_memory_cursor_and_lease_are_linearizable` | PostgreSQL | passed | user-scoped receipt 同键一成功、一可重试，随后稳定 replay |
| P4A-ISO-05 | `tests/independent/agent_finance/test_tools_and_lifecycle.py::test_expiry_identity_and_stale_resource_never_commit` | SQLite | passed | 错身份/过期/stale pending 均不提交 |
| P4A-ISO-06 | `tests/independent/host/test_state_acceptance.py::test_c11_conversation_replay_conflict_retention_and_scope` | SQLite | passed | conversation 按 user 过滤；另一 owner 得到统一 not found |
| P4A-ISO-07 | `tests/independent/host/test_api_acceptance.py::test_c11_adapter_gate_precedes_code_lookup_and_is_privacy_safe` | API/SQLite | passed | 虚拟外部身份 canary 不进入错误响应，adapter gate 在查码前 |
| P4A-ISO-08 | `tests/independent/host/test_contract_acceptance.py::test_c11_bound_registry_rechecks_permission_and_module_state` | contract | passed | 权限/module 状态在执行瞬间复核，不存在禁用窗口 |
| P4A-WFL-01 | `tests/independent/agent_finance/test_tools_and_lifecycle.py::test_supplement_cancel_and_confirm_after_cancel` | SQLite | passed | 补充、取消、取消后确认状态机终态稳定 |
| P4A-WFL-02 | `tests/independent/agent_finance/test_tools_and_lifecycle.py::test_confirmation_just_before_expiry_is_allowed` | SQLite | passed | 可控时钟验证到期前边界；过期路径零领域写 |
| P4A-WFL-03 | `tests/independent/agent_finance/test_postgresql_agent_contract.py::test_postgresql_concurrent_confirm_commits_once_and_matches_p1` | PostgreSQL | passed | 双确认只产生一财务事务/receipt，另一重放同结果 |
| P4A-WFL-04 | `tests/independent/agent_finance/test_tools_and_lifecycle.py::test_active_resource_version_change_invalidates_candidate` | SQLite | passed | 资源版本变化使候选 stale，零写入 |
| P4A-WFL-05 | `tests/independent/host/test_postgresql_acceptance.py::test_c11_pg_receipt_setting_memory_cursor_and_lease_are_linearizable` | PostgreSQL | passed | 两接管者仅一进入 attempt 2；旧 attempt renew 被拒 |
| P4A-WFL-06 | `tests/independent/host/test_postgresql_acceptance.py::test_c11_pg_pending_commit_recovery_is_exactly_once` | PostgreSQL | passed | 领域 commit 后中断，租约后恢复为 success，expense 仍恰好一条 |
| P4A-WFL-07 | `tests/independent/agent_finance/test_tools_and_lifecycle.py::test_supplement_cancel_and_confirm_after_cancel` | SQLite | passed | cancelled 后确认稳定拒绝且无写入 |
| P4A-WFL-08 | `tests/independent/agent_finance/test_idempotency_and_loop.py::test_database_failure_does_not_report_false_commit` | SQLite | passed | DB 故障不报告假 commit，恢复后同 ID 正确收敛 |
| P4A-WFL-09 | `tests/independent/agent_finance/test_postgresql_agent_contract.py::test_postgresql_commit_response_loss_recovers_same_result` | PostgreSQL | passed | 提交响应丢失、60 秒 lease 后恢复同结果，不重复事实 |
| P4A-WFL-10 | `tests/independent/agent_finance/test_tools_and_lifecycle.py::test_schema_hides_context_and_all_tools_forbid_context_override` | SQLite | passed | 模型输入不能覆盖 user/module/profile/approved/version |
| P4A-MEM-01 | `tests/independent/host/test_state_acceptance.py::test_c11_memory_requires_confirmation_rechecks_grant_and_tombstones` | SQLite | passed | 未确认候选不可检索，namespace grant 显式限制 |
| P4A-MEM-02 | `tests/independent/host/test_state_acceptance.py::test_c11_memory_expiry_limit_and_version_cas` | SQLite | passed | 恰好 30 天 candidate 过期并清空正文 |
| P4A-MEM-03 | `tests/independent/host/test_state_acceptance.py::test_c11_memory_requires_confirmation_rechecks_grant_and_tombstones` | SQLite | passed | 只有显式 `decide(confirm=True)` 创建 confirmed item |
| P4A-MEM-04 | `tests/independent/host/test_state_acceptance.py::test_c11_memory_expiry_limit_and_version_cas` | SQLite | passed | supersede 后旧 version invalidate 为 conflict；PG 双确认亦单胜者 |
| P4A-MEM-05 | `tests/independent/host/test_state_acceptance.py::test_c11_memory_requires_confirmation_rechecks_grant_and_tombstones` | SQLite | passed | delete 后正文与 tags 清空，状态为 tombstone |
| P4A-MEM-06 | `tests/independent/host/test_state_acceptance.py::test_c11_memory_requires_confirmation_rechecks_grant_and_tombstones` | SQLite | passed | `balance` 财务事实被 `memory_fact_forbidden` 拒绝 |
| P4A-MEM-07 | `tests/independent/host/test_state_acceptance.py::test_c11_memory_expiry_limit_and_version_cas` | SQLite | passed | grant/tag/active/expiry 过滤，10 条输入稳定只返回最新 8 条 |
| P4A-MEM-08 | `tests/independent/host/test_state_acceptance.py::test_c11_conversation_replay_conflict_retention_and_scope` | SQLite | passed | 恰好 90 天消息清空，90 天内消息仍可读 |
| P4A-DB-01 | `tests/independent/host/test_api_acceptance.py::test_c11_untrusted_identity_fields_and_framework_errors_use_envelope` | API/SQLite | passed | 额外身份字段、404、405 均为严格安全 envelope |
| P4A-DB-02 | `tests/independent/host/test_state_acceptance.py::test_c11_conversation_replay_conflict_retention_and_scope` | SQLite | passed | 同键同载荷 replay，同键异载荷 conflict，GET 按 owner 恢复 |
| P4A-DB-03 | `tests/independent/host/test_migration_acceptance.py::test_c11_sqlite_empty_upgrade_single_head_and_real_constraints` | SQLite/Alembic | passed | 空库到唯一 `p4_host_state`，foreign key check 为零 |
| P4A-DB-04 | `tests/independent/host/test_migration_acceptance.py::test_c11_sqlite_p3_history_forward_upgrade_preserves_p1_p2_p3_facts` | SQLite/Alembic | passed | P3 head 直接写入 P1 财务、P2 run/pending、P3 导入事实；升级 P4 后事实、整数 minor、关系、bootstrap owner、conversation 回填、零孤儿与单 head 均通过 |
| P4A-DB-05 | `tests/independent/host/test_postgresql_acceptance.py::test_c11_pg_p3_history_forward_upgrade_preserves_p1_p2_p3_facts` | PostgreSQL/Alembic | passed | R2 唯一一次原节点通过：P1/P2/P3 历史保持，唯一 P4 head、三类复合关系、真实 FK/unique/check、无 persistent default、重复 upgrade 与 head→P3→head 均通过，未再出现 ObjectInUse |
| P4A-DB-06 | `tests/independent/host/test_postgresql_acceptance.py::test_c11_pg_p3_invalid_history_is_rejected_before_user_scope_ddl` | PostgreSQL | passed | R2 两个参数场景通过：孤儿 pending run 和矛盾 pending owner 在 user-scope DDL 持久化前安全拒绝，P3 head、双分录和非法原值保持，无 app_user、无部分 user_id、无重归属/删除/自动修复 |
| P4A-DB-07 | `tests/independent/host/test_state_acceptance.py::test_c11_events_publish_after_commit_and_handler_failure_is_isolated` | SQLite | passed | commit 后发布；handler 失败不回滚 setting，日志不含异常正文 |
| P4A-DB-08 | `tests/independent/host/test_state_acceptance.py::test_c11_setting_secret_rejected_before_write_and_cas_is_idempotent` | SQLite | passed | 普通设置 CAS/replay；递归 refresh token 拒绝且零 setting/receipt |

## 4. 接管审计 22 项

| 审计项 | 原风险 | 独立复现节点 | 预期与实际 | 结论 |
|---|---|---|---|---|
| P0-01 | 一次性绑定码进入 receipt | `test_c11_one_time_binding_secret_is_never_persisted_or_replayed` | 原码只返回一次；digest 与 receipt 均无原码 | 关闭 |
| P0-02 | activity import 静态身份旁路 | `test_c11_untrusted_identity_fields_and_framework_errors_use_envelope`、P3 独立 10 个 PG 节点 | body 身份拒绝；P3 以可信 owner 写入 | 关闭 |
| P0-03 | 跨 user 关系缺复合 FK | `test_c11_pg_migration_round_trip_and_real_constraint_catalog` | pending run/conversation、memory superseded 三条直接 SQL 均拒绝 | 关闭 |
| P0-04 | cancel/confirm 竞态产生假状态 | `test_supplement_cancel_and_confirm_after_cancel` | cancel 终态不可确认，零财务写 | 关闭 |
| P0-05 | run lease takeover/旧 worker 覆盖 | `test_c11_pg_receipt_setting_memory_cursor_and_lease_are_linearizable` | 单一接管，旧 attempt renew 失败 | 关闭 |
| P0-06 | candidate 后模块禁用仍确认 | `test_c11_bound_registry_rechecks_permission_and_module_state` | 执行瞬间复核 module/permission | 关闭 |
| P0-07 | settings 可存秘密 | `test_c11_setting_secret_rejected_before_write_and_cas_is_idempotent` | 递归 secret 拒绝且 setting/receipt 为零 | 关闭 |
| P0-08 | memory grant 只在 propose 检查 | `test_c11_memory_requires_confirmation_rechecks_grant_and_tombstones`、PG 双 confirm 节点 | confirm 需 allowed namespace，未确认不可检索 | 关闭 |
| P1-01 | 过期 access 可改密 | `test_c11_sessions_password_boundary_and_binding_attempt_limit` | 恰好到期拒绝，前一微秒成功 | 关闭 |
| P1-02 | command/receipt/领域事实非同事务 | `test_c11_pg_pending_commit_recovery_is_exactly_once` | 中断后恢复仍一条 expense | 关闭 |
| P1-03 | adapter 缺失或错误仍查码 | `test_c11_adapter_gate_precedes_code_lookup_and_is_privacy_safe` | 先 401，零查码副作用，identity canary 不回显 | 关闭 |
| P1-04 | 绑定五次失败边界竞态 | `test_c11_sessions_password_boundary_and_binding_attempt_limit` | 第五次错误后 code 为 locked，无 binding | 关闭 |
| P1-05 | auth 错误映射不穷尽 | `test_c11_untrusted_identity_fields_and_framework_errors_use_envelope` | 422/404/405 均含稳定 code/request id | 关闭 |
| P1-06 | BoundTool 未走真实权限链 | `test_c11_bound_registry_rechecks_permission_and_module_state` | Schema 与 invoke 均复核三重边界 | 关闭 |
| P1-07 | prompt/conversation/memory 未走真实链 | `test_c11_conversation_replay_conflict_retention_and_scope`、`test_c11_memory_requires_confirmation_rechecks_grant_and_tombstones` | owner 隔离、候选确认和删除均持久化 | 关闭 |
| P1-08 | provider/tool 前后不续租 | `test_c11_run_lease_is_owner_scoped_and_attempt_fenced`、PG lease 节点 | 60 秒边界、attempt fence 和旧 worker 拒绝 | 关闭 |
| P1-09 | 四类事件提交前发布或泄露 | `test_c11_events_publish_after_commit_and_handler_failure_is_isolated` | 事件只在 setting 可见后发布，失败 handler 被隔离且日志脱敏 | 关闭 |
| P1-10 | memory supersede/invalidate 非 CAS | `test_c11_memory_expiry_limit_and_version_cas` | supersede 后旧 version invalidate 被 CAS 拒绝；PG confirm 竞争单胜者 | 关闭 |
| P1-11 | production factory 未 fail closed | `test_c11_pg_production_factory_ready_and_stale_schema_fail_closed` | head ready=200；P3 stale ready=503 | 关闭 |
| P1-12 | cursor 跳页/跨用户复用 | `test_c11_cursor_is_endpoint_and_owner_bound` | endpoint/user 任一改变均 `invalid_cursor` | 关闭 |
| P1-13 | cancelled downgrade/upgrade 丢失 | `test_c11_sqlite_head_p3_head_keeps_old_fact_tables` 与 Host PG R1 roundtrip | 旧事实和允许状态往返保持 | 关闭 |
| P1-14 | PostgreSQL 约束名漂移 | `test_c11_pg_migration_round_trip_and_real_constraint_catalog` | 冻结 unique/FK 名从真实 catalog 取得并匹配 | 关闭 |

## 5. 首次失败、fixture 修正与环境问题

### 真正的测试方 fixture 适配

| 文件/范围 | 修改前失败 | 最小升级 | 修改后 |
|---|---|---|---|
| P1 独立 ORM 注入 | P4 `user_id` 非空后直接构造缺 owner | 仅补 `service.user_id` | 原业务断言保持 |
| P2 独立 fixture | 旧 ACTOR 无 AppUser/conversation；FinanceService 无 user；旧约束/head；真实时钟与冻结时钟不一致 | 插入虚拟 owner/conversation、补 user scope、绑定 P4 head/约束、统一可控时钟、lease 后恢复 | 原 C11 本地 42 + PG 4 全绿 |
| P3 独立 fixture | PG 专用 fixture 未插入 owner，FinanceService 仍用旧默认；head 仍断言 P3 | 插入虚拟 owner、FinanceService 绑定 owner、head 绑定 P4 | 原 C11 本地 81 + PG 10 全绿 |

这些项目只适配 P4 head、bootstrap owner、user scope、Principal、可控时钟和新 migration 链，没有删除旧业务断言或添加 skip/xfail。

### P4 合同演进

`tests/independent/agent_finance/test_tools_and_lifecycle.py::test_supplement_cancel_and_confirm_after_cancel` 把 cancelled pending 再 confirm 的稳定错误断言更新为 `pending_action_cancelled`。这不是 fixture 适配，而是 D10/P4-IF-002 冻结的 P4 状态合同演进。原业务不变量没有改变：cancel 后保持终态，confirm 必须失败，财务写入为零。P2 的 `confirmation_required` 继续用于缺少或错误确认上下文等适用状态，不用于已经 cancelled 的 pending。R1 精确复跑该节点为 1 passed。

### 恢复的历史迁移证据与新缺陷

原 C11 把 P1 首版迁移测试改为从 P4 head 开始再往返，削弱了 `bfc163b9b8e9`→P4 的正向证据。R1 已改为在真实首版 schema 用直接 SQL 写入 P1 账户、分类、交易和双分录，再升级到 P4；完整 P1 migration 文件 8/8 passed。新增 SQLite 节点在 P3 head 用独立低层 fixture 写入 P1/P2/P3 代表事实，升级后验证事实、关系、状态、owner、conversation、单 head 和 `PRAGMA foreign_key_check`，Host migration 文件 3/3 passed。P0 没有持久表，因此没有伪造 P0 表。

同一低层历史 fixture 在真实 PostgreSQL 随机 P3 schema 暴露 `P4-C11-R1-PG-001`：`p4_host_user_scope` 更新财务父子表的 `user_id` 后，在同一迁移事务把 `financial_transaction.user_id` 改为非空时，PostgreSQL 以 pending trigger events 拒绝 ALTER。该节点 1 failed；这是产品 migration 阻断，不能归类为 fixture 适配，也不能由测试方修改产品绕过。

R2 固定 E1 修复后，原节点唯一一次运行通过且未再出现 `ObjectInUse`。独立新增的孤儿 run 与矛盾 owner 场景分别得到可区分的安全诊断，并证明整个 P3→P4 升级事务回滚：版本仍为 P3、历史与非法输入原值保持、无 `app_user` 和部分 `user_id` 列。相邻 PG/SQLite 与两份执行方 migration 兼容回归也全绿，因此测试方建议关闭 `P4-C11-R1-PG-001`。

### 环境与测试基础设施

1. 一次误用系统 Python，输出 `No module named pytest`；未收集测试。
2. 一次 pytest 尝试访问用户 Temp 被 Windows 拒绝；改为项目内专用 `--basetemp` 后正常。
3. P0 独立回归两项失败：
   - `tests/independent/test_c2_b2_api.py::test_h06_client_timeout_then_retry_replays_completed_record`
   - `tests/independent/test_c2_b2_api.py::test_w04_and_restart_boundary_over_real_loopback_http`

两项均只在 `_wait_for_health` 的 8 秒期限失败，未进入断线重放或重启业务断言。同一虚拟 uvicorn 目标随后可正常完成 startup；该现象与 P2-C6 已记录问题一致。没有修改 P0 测试超时，也没有用重跑覆盖首次失败。它不构成 P4 Host 产品缺陷，但意味着“P0 兼容回归全绿”这一字面条件仍有两个环境失败。

## 6. 隐私与安全证据

- 绑定码只在首次响应出现；数据库保存 HMAC digest，receipt 不保存原码。
- adapter token 在 code lookup 前验证；错误响应不含虚拟 provider/subject。
- setting 递归包含 API key/refresh token 时在 receipt/event 前拒绝。
- memory 拒绝余额等财务事实；删除后清空 `value_json` 和 tags。
- PG receipt、event、日志和恢复结果未包含虚拟 secret、密码、token、绑定码或外部身份明文。
- 404/405、认证、数据库并发和业务错误只暴露稳定 code、retryable 与 request ID，不暴露 SQL、约束名或内部异常正文。

报告和角色日志未记录连接密码、原始 token、密码、HMAC key、外部身份或个人财务数据。

## 7. Warning、skip、blocked 与未执行范围

- Warning：Starlette `TestClient` 仍使用 AnyIO `BlockingPortal` 已弃用别名；不影响本轮断言。
- 本地运行中的 PostgreSQL skip 均由无 `FINANCE_TEST_POSTGRES_URL` 的预门禁运行产生；容器 healthy 后对应 P1 8、P2 4、P3 10 均实际通过。
- P4-A 最终为 64 passed、0 failed、0 blocked、0 not_run；P4-B/C/D 56 项保持 `not_run`。
- R1 发现的 P4-A 产品 P0 迁移阻断 `P4-C11-R1-PG-001` 已由 R2 独立复验通过，测试方建议关闭；`P4A-DB-05` 和 `P4A-DB-06` 均为 passed。
- P0 两个 loopback 环境失败仍需总控决定是否作为既有基础设施例外接受；它们不是本轮产品失败。

## 8. 测试方文件与 SHA-256

下表保留 C11/R1 终点摘要；R2 变化与最终普通摘要见 `docs/testing/phase-4-c11-r2-postgresql-history-report.md` 和 tester 完成日志。

| 文件 | SHA-256 |
|---|---|
| `docs/testing/phase-4-modular-agent-host-test-matrix.md` | `5be45adcf198b5336a81a97e6ece10a58a8bf41b292cc4ea35cdc1e4d8cb1abd` |
| `tests/independent/host/__init__.py` | `fa1082762364b3fa1acaf96084b983a20c7e74b13be0bbf1a2514869437810ed` |
| `tests/independent/host/conftest.py` | `3953fe277acf591f3e62e64fffeb28d4c9e5062c1eefce98f3df235222e13282` |
| `tests/independent/host/test_api_acceptance.py` | `4a98cb976f04b27e28919a018d7e2ba1735c7a4806cd010fa74ed7a2b9e6ce04` |
| `tests/independent/host/test_contract_acceptance.py` | `61807b4f51ff2105431fe1c6a31d01608038863298b17974680b547f391efcbd` |
| `tests/independent/host/test_migration_acceptance.py` | `0e2dfdf2dd9e9bf626550c6c83a79003c011731df11aa2327310472836e1ff69` |
| `tests/independent/host/test_state_acceptance.py` | `2ae4305a9ef5e24dc845c6f73cda846e68373d3c9480622e844e2af8a2f7d52c` |
| `tests/independent/host/test_postgresql_acceptance.py` | `12b1ecea9974ebdd3431d1fdc458cdad3476f2a7a95c8291d7a87c8c2775b920` |
| `tests/independent/host/history_fixtures.py` | `1cbae0fae892a23b6d7dfa0c6c36d5f2799bd8f22c38bcfcc6c6e7431779b796` |
| `tests/independent/finance/conftest.py` | `0e6b50b9b98b0e93033eb77ccb7799ec61ae6314ad7c243ea9713a2dd00359cd` |
| `tests/independent/finance/test_ledger_contract.py` | `37965689948e07c9e42c63502aa5e7909d13f2f4445df10a89035b3c8be61aa1` |
| `tests/independent/finance/test_migration_sqlite_contract.py` | `139a7e0d70f9aa3649dceb06a28b270b2fd72e9e06ae137d75c5fab5e33c2a07` |
| `tests/independent/finance/test_postgresql_contract.py` | `934cde125a2d6121d09dc262ef332c410e72453c8a089ec531f62fff86515fa3` |
| `tests/independent/finance/test_refund_activity_contract.py` | `41bd5cf557fa7d94b07dd02e7780781a6a2caaf53b4c5e178d8f54332f79ee4f` |
| `tests/independent/agent_finance/conftest.py` | `2192011fd852e09101c5bc8b8a33217965bc5513109bfd48175d02b6abeab68f` |
| `tests/independent/agent_finance/test_http_and_migration.py` | `da84dad278be97eac82d4036818c0f45c4e0594d20a1bb235bc7beeee6f77791` |
| `tests/independent/agent_finance/test_idempotency_and_loop.py` | `5336c4968ca6eebfa3e8ba4ca6e8dfc4432c23ab25e83a652c07ba9f443917f9` |
| `tests/independent/agent_finance/test_postgresql_agent_contract.py` | `d329027bcb2b204f0e511fa2b54395726295f96b87953fc9d31110dc9c8a05f8` |
| `tests/independent/agent_finance/test_tools_and_lifecycle.py` | `39f419641de09ac9842d64ccc7f651d41398af5075217063522afccd50150b9b` |
| `tests/independent/activity_import/conftest.py` | `f4b004fca8557782d7b68378d63ecbdd2baef70d7cda605ea8d26d4cbaf09f47` |
| `tests/independent/activity_import/test_migration_contract.py` | `6ade21ff3983062a743b99c433c155b3d9261ac75aa68834b2e99c1f7efee801` |
| `tests/independent/activity_import/test_postgresql_contract.py` | `3a146b26cf2f9cce0a6a1d3d3dbe43be991c99bebaeb832c5dc65c4051b70121` |

报告自身摘要在写入测试角色最终日志后单独记录，避免报告自引用。

## 9. 测试方结论

R1 保留了原 C11 的 62 项不受影响 P4-A 通过证据，并发现真实 PostgreSQL 历史迁移阻断。R2 在新的 133 文件固定输入上独立证明：合法 P1/P2/P3 历史可完整升级并往返，非法孤儿和矛盾 owner 会在 DDL 持久化前原子拒绝，所有限定相邻回归通过，产品与执行方输入零漂移，Docker 资源安全收口。

因此测试方建议关闭 `P4-C11-R1-PG-001`，将 `P4A-DB-05`、`P4A-DB-06` 接受为 passed，并由总控决定 P4-A 是否 `complete`。原 P0 两个 Windows/uvicorn 8 秒基础设施失败仍按既有记录保留，与本次 PostgreSQL migration 缺陷闭环分开。
