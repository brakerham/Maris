# P4-B6 多次交接代码接管审计

- 审计编号：`P4-B6-AUDIT-1`
- 审计时间：2026-09-25，Asia/Shanghai
- 总控负责人：头脑风暴智能体
- 审计对象：当前工作区中的 P4-B6 `review` 实现
- 交接背景：同一 P4-B6 任务曾由 Claude Code、Codex、DeepSeek 依次续做；本报告评价最终代码和证据，不按模型来源归责
- 结论：`review` 不接受；先完成 P4-D10 合同裁定，再执行 P4-B6-R1/R2 返修，最后才能启动 P4-C11

## 1. 审计边界与方法

本次审计以 [P4-IF-001](phase-4-interface-freeze.md)、[P4-B6 任务卡](coordination/prompts/p4-b6-host-foundation-executor.md)和 [P4-C10 矩阵](testing/phase-4-modular-agent-host-test-matrix.md)为依据，分成三个只读代码面：

1. 认证、Session、渠道绑定、Host API、错误和隐私；
2. migration、可信 user scope、财务与活动导入兼容、SQLite/PostgreSQL；
3. Host registry、Profile、工具绑定、Agent/workflow、conversation、memory、setting、event 和生产组合根。

临时审查智能体没有修改项目文件、没有执行 Git 写操作，也没有操作 OpenClaw、微信或真实账户。根总控独占 Docker/PostgreSQL 审计环境，只使用项目测试凭据、随机 schema 和虚拟数据；结束后执行普通 Compose down，没有删除 volume，最终服务列表为空。

## 2. 证据概况

### 2.1 当前执行方证据

- 本地执行方组合套件：`249 passed, 13 skipped`。
- `compileall` 与依赖检查通过。
- Alembic 单一 head：`p4_host_state`。
- B6 运行说明声称 53 个文件，但摘要清单实际只有 52 个；52 个逐文件摘要可以复算，报告中的有序总摘要不能复算。
- 默认模块入口仍是 `app = create_app()`，未装配 HostRuntime/AgentApplication；测试通过依赖手工注入 runtime。

### 2.2 根总控真实 PostgreSQL 审计

Docker Engine 29.8.0 可用。总控只启动 `finance-postgres`，镜像 `postgres:17.6-alpine` 达到 healthy 后运行现有执行方 PostgreSQL 文件：

```text
tests/finance/test_postgresql_claim.py
tests/activity_import/test_postgresql.py

结果：12 failed, 1 passed
```

失败主要证明 P4 交接没有同步 PostgreSQL 测试基座：

- finance fixture 只迁移到 P1 head，却用当前需要 `user_id` 的 P4 service；
- activity import fixture 使用一个不存在于 `app_user` 的旧 OWNER；
- migration 断言仍把 P3 revision 当成最终 head。

为了区分“测试过期”和“产品无法运行”，总控又在随机 PostgreSQL schema 上完成最小产品冒烟：空 schema 升级到 `p4_host_state`，创建/查询账户，构造 HostRuntime，执行 `/readyz`、初始化、登录、模块查询和活动导入 preview，结果为 `P4_POSTGRES_SMOKE_PASS`。这只证明最小顺序路径可运行，不替代 P4 的并发、复合外键和恢复门禁。

### 2.3 旧独立回归的解释

旧 P1～P3 独立测试出现的大量失败主要来自历史 fixture 未升级：旧 schema 缺 `user_id`、actor/owner 与 bootstrap user 不一致、固定 pending 时间已超过 24 小时、旧 head 断言失效。这些不能整批登记为产品缺陷，也不能通过删除原断言“修绿”。C11 必须把 fixture 升到 P4 head，并保持原业务断言。

## 3. P0 阻断项

### `P4-B6-AUD-P0-01` 原始渠道绑定码进入普通回执表

[创建绑定码路由](../src/wife_system/api/host_routes.py)把原始 code 放进命令结果，[HostCommandService](../src/wife_system/host/state.py)再把完整结果写入 `host_request_receipt.result_json`。同一个 Idempotency-Key 重放还会再次返回相同原码。

只读复现结果：

```text
binding_replay: 200 / 200
same code returned: true
raw_code_persisted: true
```

这直接违反“数据库只存 HMAC digest，原码只在创建响应出现一次”。修复前必须先裁定“一次返回”和“创建请求幂等”同时成立时的正式重放语义。

### `P4-B6-AUD-P0-02` Host 模式下活动导入 API 绕过认证

[activity_import_routes.py](../src/wife_system/api/activity_import_routes.py)始终读取固定 `app.state.activity_import_identity`；存在 HostRuntime 时也不验证 Bearer token。虚拟环境中，无 Authorization 和明显错误 token 的 preview 都返回 201，并写入批次。

生产 Host 模式必须从可信 principal 构造 `ImportIdentity`；仅历史 P3 测试构建器可显式注入虚拟身份。

### `P4-B6-AUD-P0-03` 三条跨用户关系缺少复合外键

P4 head 数据库允许以下跨用户串联：

- A 用户的 `memory_item.superseded_by_id` 指向 B 用户的 memory item；
- A 用户的 `memory_candidate.memory_item_id` 指向 B 用户的 memory item；
- A 用户的 `agent_run.pending_action_id` 指向 B 用户的 pending action。

这些关系分别缺少 `(user_id, id)` 唯一键或 `(user_id, foreign_id)` 复合外键。Alembic head、SQLite FK ON 的直接写入复现均被数据库接受。修复必须同时更新 migration 和 ORM；应用层 `if user_id` 不能替代数据库隔离。

### `P4-B6-AUD-P0-04` cancel/confirm 竞争可形成“已取消但账本已写”

[PendingActionStore.claim_commit](../src/wife_system/agent/pending.py)返回 CAS 成败，但 [AgentApplication](../src/wife_system/agent/application.py)忽略返回值并继续调用财务提交。两个进程竞争时，取消可以先成功，确认方仍写入账本，随后 `mark_committed` 失败，留下事实与 pending 状态矛盾。

只有成功取得 `committing` 所有权的请求可以首次执行领域提交；失败方必须按数据库实际状态恢复或重放。

### `P4-B6-AUD-P0-05` run lease 接管增加 attempt 却不恢复执行

过期 `running` run 被新 worker 成功 acquire 后，因为 `replayed=True` 又直接返回当前 `running` 记录，不再调用 provider 或工具。重复接管最终只会耗尽三次 attempt 并返回 `run_attempts_exhausted`。

必须实现真正的接管继续、旧 attempt fencing 和 provider/tool 前后续租。

### `P4-B6-AUD-P0-06` 模块禁用后，已有候选仍可确认写账

resume/confirm 路径没有在提交线性化点重新解析 run 绑定的模块、Profile、工具授权和 principal 权限。`daily_finance` 被禁用后，旧 confirmation code 仍可进入财务提交。

start 和 resume 都必须通过同一个已编译 Profile/BoundToolRegistry 执行计划，在实际执行点重新授权。

### `P4-B6-AUD-P0-07` 普通模块设置可以保存 API Key/token/password

严格的 `ModuleSettingValue` 只在合同单元测试中构造，生产 `ModuleSettingService.put()` 没有使用它；当前 `assistant_mode` validator 只要求字典。因此带 `api_key` 等字段的 JSON 会进入 `module_setting.value_json`。

秘密字段拒绝和模块 schema 验证必须位于实际 service 写入边界，并证明失败时数据库零写。

### `P4-B6-AUD-P0-08` 记忆确认没有绑定候选 Profile grant

memory candidate 虽保存 `proposed_by_profile_id`，提议和确认却没有按该 Profile 校验 namespace。API 把所有已启用模块的 namespace 合并，daily 候选可以确认到 wealth namespace。

候选来源、目标 namespace、模块启用和 Profile memory grant 必须在提议与确认时共同校验；shared confirmed 仍需显式确认。

## 4. P1 阻断项

| ID | 问题 | 主要影响 |
| --- | --- | --- |
| `P4-B6-AUD-P1-01` | 过期 access token 仍可改密并取得新 Session | 绕过 15 分钟 access 边界 |
| `P4-B6-AUD-P1-02` | HostCommandService 使用“claim receipt→领域提交→完成 receipt”三个事务 | 响应丢失/崩溃后留下永久 incomplete receipt；initialize/create/consume/revoke 均受影响 |
| `P4-B6-AUD-P1-03` | adapter token 缺失为 422、错误为 403 | 冻结要求两者统一 `401 channel_adapter_unauthorized` |
| `P4-B6-AUD-P1-04` | 绑定码错误 code/channel 不累计 attempts | 五次失败上限对枚举无效；当前请求也缺少安全关联具体 code 的字段 |
| `P4-B6-AUD-P1-05` | AuthError 未穷举 HTTP 映射 | `binding_code_expired`、`invalid_refresh_token` 等状态错误 |
| `P4-B6-AUD-P1-06` | ToolCatalog/BoundToolRegistry 未进入真实 Agent 链 | Profile grant 和模块启停只在孤立测试中生效 |
| `P4-B6-AUD-P1-07` | Profile prompt、会话消息和确认记忆未进入 Agent | Host 仍是旁路状态服务；真实聊天后 messages 为空 |
| `P4-B6-AUD-P1-08` | lease 只在整个 runner 返回后续租一次 | 合法长 run 可跨过 60 秒并被第二 worker 接管 |
| `P4-B6-AUD-P1-09` | 四类冻结事件只发布 memory/setting 两类 | 缺少 run status、session revoked；event bus 也未在 runtime 中装配 subscriber |
| `P4-B6-AUD-P1-10` | memory supersede/invalidate 只有字段，没有服务行为 | 无替代链 CAS、活跃链唯一和显式失效 |
| `P4-B6-AUD-P1-11` | 默认生产 app 未装配 Host/Agent | `/readyz` 和 Host API 默认 503；Electron 后续没有可监督的 Python 入口 |
| `P4-B6-AUD-P1-12` | cursor 只接受输入，不返回 `next_cursor` | 客户端无法到达第二页；memory candidate 甚至没有分页 |
| `P4-B6-AUD-P1-13` | 合法 `cancelled` run 阻断 head→P3 downgrade | 恢复旧 check 时 IntegrityError，降级可能中断 |
| `P4-B6-AUD-P1-14` | activity import 仍匹配 P3 旧 PostgreSQL unique 名 | P4 head 同名竞争败方变成 500，而非 409 |

## 5. P2 与证据缺口

- 认证 principal 的 channel 被硬编码为 `api_test`，没有从可信 DeviceSession platform 派生。
- 框架产生的 404/405 仍是 `{"detail": ...}`，没有统一 error envelope。
- `profile_version` 在 run 中硬编码为 `1.0.0`。
- Host 自身事件未被 registry 视为合法 publisher。
- `tool_not_allowed` 在 AgentRunner 中会退化为 `unknown_tool` 或 `tool_error`。
- ORM metadata 与 Alembic 正式 schema 不一致；大量 `create_all()` 测试弱于真实数据库约束。
- migration 历史 fixture 只覆盖少量表，未满足 P0～P3 全量虚拟历史数据升级要求。
- pending store 仍保留可省略 `user_id` 的历史签名，容易被未来模块误用。
- B6 文件数/总摘要不一致；`README.md` 末尾还有无关的 `# Maris`。

## 6. 已核对的正确边界

审计没有否定全部 B6 工作。以下实现有实际代码和局部测试支持：

- 严格 manifest/Profile/ID/SemVer 基础合同和重复注册门禁；
- Argon2id 参数、密码字符规则、token 随机性与 digest 存储；
- refresh 轮换和旧 refresh 重放撤销；
- Session/binding 基本 user filter；
- 外部身份使用 domain HMAC，日志没有发现密码、token、SQL 参数或原始身份；
- 三段线性 migration 和单 Alembic head；
- P4 head 上账户、最小 Host auth/modules、活动 preview 的顺序 PostgreSQL 冒烟。

这些是可复用基础，但不能抵消开放的 P0/P1。

## 7. 返修顺序与角色边界

### 7.1 先执行 `P4-D10`

技术顾问只读裁定以下合同冲突，并给出最小 repair architecture：

1. 绑定码“原码只返回一次”与创建幂等重放的正式语义；
2. 五次绑定失败如何安全关联，不产生存在性侧信道；
3. Host 命令事实提交与 receipt 恢复的一致性协议；
4. cancel/confirm、lease takeover、attempt fencing 和 cooperative deadline；
5. Host registry/Profile/tool/conversation/memory/event 接入 Agent 的最小组合方式；
6. 三条复合 FK 与循环 run/pending migration 顺序；
7. `cancelled` downgrade 映射；
8. 分页响应 envelope；
9. 生产 app factory 与 secret/config 边界；
10. 将执行返修拆成互不重叠的安全数据切片和 Host/Agent 集成切片。

### 7.2 再执行 `P4-B6-R1/R2`

总控接受 D10 并发布冻结补充后再派执行智能体。执行方负责产品代码、migration、执行方测试和准确快照；不得修改独立测试/C10/审计报告/Git，不操作 OpenClaw、微信、Electron、DeepSeek 或真实数据。

### 7.3 最后执行 `P4-C11`

测试智能体必须绑定返修后的固定快照，执行 P4-A 64 项、针对本报告的独立复现、P0～P3 兼容回归、Alembic head SQLite 和真实 PostgreSQL 并发/复合约束门禁。当前快照不得用于启动 C11。

## 8. 当前状态

```yaml
P4-B6:
  status: review
  runtime: stopped
  acceptance: rejected_pending_design_and_repair
  open_p0_groups: 8
  open_p1_groups: 14
  postgresql:
    engine: available
    minimal_p4_head_smoke: passed
    existing_execution_pg_suite: 1_passed_12_failed_due_to_stale_p4_fixtures_and_assertions
    full_p4_gate: not_started
  c11: not_started
  git_acceptance_commit: forbidden_until_independent_acceptance
```

OpenClaw/微信已经由用户确认恢复和可连接，但它们不属于本轮 P4-A 代码返修门禁。本审计没有重复扫码、真实消息或运行时修改。
