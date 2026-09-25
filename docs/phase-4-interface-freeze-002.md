# P4-IF-002：B6 安全数据与 Host 运行时返修补充冻结

- 冻结编号：`P4-IF-002`
- 冻结时间：2026-09-25，Asia/Shanghai
- 总控负责人：头脑风暴智能体
- 状态：`complete`；作为 P4-B6-R1、P4-B6-R2 和 P4-C11 的强制输入
- 输入：[P4-B6 接管审计](p4-b6-multi-handoff-code-audit.md)、[P4-D10 技术裁定](phase-4-d10-b6-repair-architecture.md)、[P4-IF-001](phase-4-interface-freeze.md)、[P4-C10 矩阵](testing/phase-4-modular-agent-host-test-matrix.md)

本文补充并收紧 P4-IF-001。两份冻结不冲突的部分继续有效；发生冲突时，以本文为准。本文不表示代码已经修复，也不表示 C11 已开始。

## 1. 顺序与完成边界

返修严格按以下顺序执行：

1. `P4-B6-R1`：认证、一次性绑定码、Host command/receipt、user scope、三个 P4 migration、错误映射、活动导入兼容入口及 PostgreSQL fixture。
2. 总控核对 R1 固定快照和执行方证据。
3. `P4-B6-R2`：Host/Agent/workflow、conversation/message、memory、setting、event、分页和生产组合根。
4. 总控核对最终 R2 固定快照。
5. `P4-C11`：测试智能体绑定 R2 快照执行独立验收。

R1 与 R2 不得并发。R1 只到 `review`，R2 只到 `review`；执行方自测不能把 P4-A 标为 `complete`。当前旧 B6 快照、D10 文档和 R1 中间快照均不能作为 C11 输入。

## 2. 一次性绑定码

### 2.1 创建

`POST /api/v1/channel-bindings/codes` 继续要求认证 principal 与 `Idempotency-Key`。首次成功返回：

```json
{
  "code_id": "uuid",
  "code": "one-time-secret",
  "expires_at": "timezone-aware ISO-8601"
}
```

- 原始 `code` 只能存在于首次成功响应的进程内对象中。
- 数据库、receipt、日志、事件、模型上下文、普通设置和错误响应均不得保存或重建原始 code。
- `channel_binding_code` 只保存带 domain 的 HMAC digest；domain 保持 `wife.channel-binding.v1`。
- `host_request_receipt.receipt_result` 只可保存 `code_id`、`expires_at` 和安全状态，不保存 code。
- 相同用户、相同 source、相同 `Idempotency-Key`、相同请求重放返回：

```text
409 one_time_secret_unavailable
```

不得再次返回原码。相同键、不同载荷仍返回幂等载荷冲突。

首次响应丢失时，客户端使用新的 Idempotency-Key 创建替代码。该创建事务必须先撤销同一用户、同一 channel 的旧 active code，再创建新 code；旧码此后不可消费。

### 2.2 消费与五次失败

消费 DTO 冻结为 `code_id + code + channel + 外部身份字段`；`code_id` 是非秘密随机 UUID，不能单独完成绑定。

消费顺序固定为：

1. 先验证可信 adapter token；缺失、空值、错误值统一 401 `channel_adapter_unauthorized`。
2. 在事务中按 `code_id` 锁定 code row。
3. 常量时间比较 code HMAC，并检查 channel、状态、过期时间和尝试次数。
4. 正确且可用时，在同一事务中消费 code、创建 active binding 和安全 receipt。

已知 active `code_id` 的错误 code 或错误 channel 计为一次失败：第 1～4 次保持 active，第 5 次原子进入 `locked`，第 6 次及以后不再增加。正确消费与第 5 次失败并发时只能有一个线性化结果。

unknown、expired、consumed、revoked、locked 以及 code/channel 不匹配，对外统一：

```text
409 binding_code_invalid
```

响应、时序、日志不得暴露 code 是否存在或具体终态。内部审计可保存安全状态、内部 user、code_id 和时间，不保存原始 code/外部身份。

## 3. Host command 与 receipt

同一数据库中的以下命令必须把 receipt claim、领域事实和安全 `receipt_result` 放进一个 SQLAlchemy Session/数据库事务：

- bootstrap initialize；
- create binding code；
- consume binding code；
- revoke binding。

冻结结果类型：

```text
CommandOutcome:
  public_result   # 只用于当前首次 HTTP 响应，可以含一次性秘密
  receipt_result  # 允许持久化和安全重放，绝不能含一次性秘密
```

事务语义：

- 领域提交前崩溃：receipt 与领域事实全部回滚，同键可重新执行。
- 事务提交后响应丢失：普通命令从 completed receipt 返回安全结果；创建绑定码返回 `one_time_secret_unavailable`。
- 不允许保留 `result_json IS NULL` 且永久返回 `concurrent_modification` 的 receipt。
- post-commit 事件在事务外发布；事件 handler 失败不回滚已提交事实，也不导致命令重做。

登录、refresh、改密产生的 access/refresh token 不进入普通 Host receipt。原始绑定码同样禁止进入 receipt。

## 4. 认证、principal 与错误映射

### 4.1 access 生命周期

改密必须复用完整 active access 校验：user active、session 未撤销、`now < access_expires_at`、`now < absolute_expires_at`。恰好到期即过期。失败时 credential、session、refresh digest 全部零变化。

### 4.2 可信 channel

`AuthenticatedSession` 必须携带数据库 DeviceSession 的 platform。Principal channel 由可信 platform 派生：

```text
windows_desktop -> desktop_chat
api_test         -> api_test
```

客户端 body、模型和普通设置不能覆盖 principal channel。

### 4.3 统一错误

404、405、Pydantic、AuthError 和业务异常都使用：

```json
{
  "request_id": "uuid",
  "error": {
    "code": "stable_code",
    "message": "safe message",
    "retryable": false
  }
}
```

AuthError 必须使用穷举映射，测试断言错误枚举与映射键完全相等，不允许“未识别即 409”。R1 至少冻结：

- 401：`authentication_required`、`invalid_credentials`、`session_revoked`、`session_expired`、`invalid_refresh_token`、`session_refresh_replayed`、`channel_adapter_unauthorized`。
- 403：`bootstrap_unauthorized`。
- 404：`session_not_found`、`binding_not_found`、`account_not_found`。
- 409：`already_initialized`、`active_session_limit`、`channel_identity_conflict`、`binding_code_invalid`、`one_time_secret_unavailable`。
- 422：`invalid_handle`、`invalid_password`、`invalid_device`、`invalid_channel`。
- 429：`login_rate_limited`，保留安全 `Retry-After`。

内部若保留 expired/consumed/locked 等绑定细分码，HTTP 边界仍统一为 `binding_code_invalid`。

## 5. Host 与旧 P3 活动导入装配

生产 Host 模式中，活动导入必须从已认证 Bearer Principal 构造内部身份：

```text
owner_id = principal.user_id
user_id  = principal.user_id
channel  = principal.channel
permissions = principal.permissions
```

无 token、错误 token、过期/撤销 token 均为 401 且数据库零写。A 用户不能读取、提交或推断 B 用户的 batch/candidate/receipt；跨用户 UUID 统一 404。

历史 P3 执行方测试可以通过显式 test builder 注入虚拟 `ImportIdentity`，但必须满足：

- `host_runtime is None`；
- test mode 被显式选择；
- 生产 factory 不提供静态默认 identity。

同时传 HostRuntime 和静态 import identity 时，应用构造立即失败。请求 body/query/tool JSON 不接受 owner/user 字段。

PostgreSQL 同用户同名活动模板竞争必须识别 P4 constraint `uq_template_user_name`，败方稳定返回 409 `concurrent_modification`；不同用户可以拥有相同 normalized name。不得通过输出完整 SQL/参数识别错误。

## 6. user scope、ORM 与三个 P4 migration

P4 尚未验收或发布，继续修正现有三个 revision，不新增第四个 revision；head 保持 `p4_host_state`：

```text
p4_host_identity
p4_host_user_scope
p4_host_state
```

如果执行方发现已有不可重建的外部数据库把当前错误 P4 head 当作稳定历史，必须停止并交回总控，不得自行改为第四 revision。

### 6.1 三条复合关系

R1 必须同步 ORM metadata 与 Alembic schema：

```text
UNIQUE memory_item(user_id, id)                       uq_memory_item_user_id
FK memory_item(user_id, superseded_by_id)
  -> memory_item(user_id, id)                         fk_memory_item_user_superseded

FK memory_candidate(user_id, memory_item_id)
  -> memory_item(user_id, id)                         fk_memory_candidate_user_item

FK agent_run(user_id, pending_action_id)
  -> pending_action(user_id, id)                      fk_run_user_pending
```

`pending_action(user_id,id)`、`agent_run(user_id,id)` unique 和 pending→run 复合 FK 保持。被复合关系替代的单列 FK 不得继续造成 ORM/schema 双重漂移。

PostgreSQL 的 run→pending nullable FK 使用可延迟约束；downgrade 先移除 run→pending，再处理状态和列，随后才移除 pending→run。

SQLite 必须以一个受控 helper 成对 rebuild run/pending；恢复 FK 后立即执行 `PRAGMA foreign_key_check`，任何返回行都使 migration 失败。memory downgrade 先处理 candidate，再处理 item。

### 6.2 为 R2 预备的最小字段

R1 只负责 schema/ORM，不实现 R2 行为：

- `pending_action.commit_attempt_no`：非负，默认 0；
- `pending_action.commit_lease_expires_at`：nullable；
- 现有 `version_id` 作为 commit claim fence；
- `conversation_message.run_id/run_sequence/tool_call_id`：历史消息允许为空；
- `UNIQUE(user_id, run_id, run_sequence)`；
- message→run 复合 user FK；
- `run_id` 与 `run_sequence` 同时为空或同时非空的 check。

R2 如需冻结之外的新数据库字段，必须停止并交回总控，不得自行修改 migration。

### 6.3 P4→P3 cancelled 映射

恢复 P3 run status check 前，把合法 `cancelled` 映射为：

```text
status = error
error_code = cancelled   # 仅原值为空时写入
pause_reason = null
```

不得删除 run/pending/业务引用，不得映射为 success，不得生成财务事实。SQLite/PostgreSQL 都必须覆盖含 cancelled run 的 head→P3→head round trip。

### 6.4 `create_all()` 边界

ORM metadata 必须表达正式复合约束。`Base.metadata.create_all()` 仅可用于纯单元测试；不能作为 migration、SQLite rebuild、PostgreSQL constraint、downgrade 或 C11 证据。

## 7. R1 必须关闭的审计项

R1 必须关闭并提供执行方证据：

```text
P0-01 绑定码原文落 receipt
P0-02 活动导入绕过认证
P0-03 三条跨用户关系缺少复合 FK
P1-01 过期 access 仍可改密
P1-02 Host command 三事务 crash window
P1-03 adapter 缺失/错误状态不统一
P1-04 五次失败对枚举无效
P1-05 AuthError HTTP 映射不完整
P1-13 cancelled run 阻断 downgrade
P1-14 P4 PostgreSQL constraint 名未同步
```

任何一项没有代码、测试和可复算快照证据，R1 不得提交 `review`。

## 8. R2 已冻结但本轮不得提前实现的合同

R1 只准备必要 schema。R2 将实现：

- `claim_commit` 返回带 version/attempt/lease 的所有权；CAS 失败方绝不调用 FinanceService；
- `committing` 的第二确认/取消返回 409 `commit_in_progress`；稳定领域键保持 `pending:{id}:commit`；
- run takeover 真正继续执行，所有保存使用 `attempt_no` fence；provider/tool 前后续租；
- start/resume/takeover 使用同一种 `CompiledExecutionPlan`；
- plan 绑定 principal、module/version、Profile/version/prompt、BoundToolRegistry、permissions、memory grants、limits、conversation 和 attempt fence；
- prompt 顺序为 Host 安全规则 → Profile prompt → 可信上下文 → 最多 8 条获准记忆 → 会话历史 → 工具事实 → 当前消息；
- candidate target/Profile/version 在 proposal 时固定，confirm 不可改投 namespace；
- memory active→superseded/invalidated/deleted tombstone 使用 version CAS；
- setting service 在 receipt 前拒绝秘密、超限和错误 schema；
- `host_core` 发布四类 post-commit 事件；
- conversations/messages/memory candidates 返回 `Page{items,next_cursor}`；
- 提供可供 Uvicorn/Electron supervisor 调用的 production app factory。

R1 不得顺手实现这些运行时行为。

## 9. PostgreSQL 与 C11 门禁

R1 使用真实 PostgreSQL 验证认证、binding、receipt、三条复合 FK、migration/downgrade、activity import constraint 和已更新的 P1/P3 fixture。R2 再验证 cancel-confirm、commit recovery、run takeover、event、分页和 production factory。

C11 只有同时满足以下条件才可派发：

1. R1、R2 均提交 `review` 并停止；
2. R2 从总控核对的精确 R1 快照开始；
3. 8 个 P0、14 个 P1 都有实现与执行方证据；
4. 三个 P4 migration 仍为单一 head；
5. SQLite 与真实 PostgreSQL 的空库、P0～P3 全量虚拟历史、复合 FK、并发和 downgrade 有证据；
6. 旧 fixture 升级到 P4 head，但原业务断言没有删除或放宽；
7. 最终 R2 文件数、逐文件摘要和总摘要可复算；
8. 无未说明的产品、依赖或测试漂移。

OpenClaw、微信、Electron、DeepSeek 在线调用、真实个人数据和真实行情不属于 P4-A 返修或 C11。

## 10. 所有权与 Git

- R1/R2 的唯一负责人均为用户侧边栏中的既有执行智能体，但必须顺序接单；未收到对应 Prompt 时保持停止。
- 测试智能体保持停止，不能提前修改独立测试或运行 C11。
- 技术顾问完成 D10 后保持停止。
- 只有头脑风暴总控拥有 Git 写权限。R1/R2 不得 add、commit、restore、reset、switch、merge、rebase、tag、push 或创建 PR。
- 当前产品仍处于发布前阶段；本冻结不触发 PR-only 流程。
