# P2-IF-001：自然语言财务 Agent 最小纵向切片接口冻结

- 冻结编号：`P2-IF-001`
- 冻结时间：2026-09-16 23:37，Asia/Shanghai
- 总控负责人：头脑风暴智能体
- 输入：[P2-D5 技术建议](phase-2-d5-finance-agent-advice.md)、[P1-C4-R2 报告](testing/phase-1-c4-data-report.md)、[P1 数据接口](phase-1-interface-freeze.md)
- 实现任务：`P2-B4`
- 独立测试设计：`P2-C5`

P1-B3-R1 的 SQLite 与数据库无关范围已经通过独立复验，绑定快照为：

```text
P1-B3-R1-SHA256:751a78aadacf6317e2dafc711569322f3843051e1fae0ee41f11e4b91cfb29bf
```

真实 PostgreSQL 的 8 个专项仍是环境阻塞，不能写成已通过；它们不阻止 P2-A 在隔离 SQLite 和脚本化模型上实现 Agent 适配层。

## 1. P2-A 范围

首个纵向切片完成：桌面端稳定来源事件中的自然语言 `午饭 18 元`，经过 Agent 工具循环形成结构化候选，用户确认后调用 `FinanceService.record_expense()`，返回真实交易回执，并可通过查询工具验证。

P2-A 提供六个工具：

| 工具 | 类型 | 映射 |
| --- | --- | --- |
| `finance_list_accounts` | 读 | `FinanceService.list_accounts()` |
| `finance_list_categories` | 读 | `FinanceService.list_categories()` |
| `finance_get_account_balance` | 读 | `FinanceService.account_balance()` |
| `finance_list_transactions` | 读 | `FinanceService.list_transactions()` |
| `finance_get_monthly_snapshot` | 读 | `FinanceService.monthly_snapshot()` |
| `finance_record_expense` | 候选/写 | 确认后映射 `FinanceService.record_expense()` |

收入、转账、退款、冲销、拆分、多笔批量、账户/分类管理、活动、预算发布、Markdown 导入、搜索评估和投资功能不进入 P2-A。

## 2. 架构

1. 继续使用现有 Python `AgentRunner`、`ModelProvider` 和 `ToolRegistry`，增加显式状态机；P2-A 不引入 LangGraph。
2. Agent、工具适配器和同步 `FinanceService` 保持同一模块化单体进程，工具直接调用服务，不增加内部财务 HTTP 服务。
3. 增加最薄 FastAPI Agent 边界，供未来桌面端复用；HTTP 路由调用同一 Python Agent 应用服务。
4. 模型调用、用户等待和数据库事务分离。等待模型或用户时不得持有 SQLAlchemy Session。
5. 金额、整数分、余额、预算、事务、幂等和最终成功结论都来自确定性程序。模型只负责理解、提出候选、选择工具和解释结果。

## 3. 可信上下文

`RunContext`/`ToolExecutionContext` 至少包含：`agent_run_id`、`actor_id`、`conversation_id`、`source_system`、可选稳定 `source_event_id`、`received_at`、权限集合、可选 `pending_action_id` 和服务端批准标识。

这些字段由入口构造，永不出现在模型工具 JSON Schema 中。模型不能生成或覆盖身份、权限、来源编号、接收时间或确认授权。

P2-A 使用单用户虚拟身份配置，但数据结构保留 `actor_id`。桌面入口在用户提交时生成 UUID `client_event_id`，同一次网络重试必须复用：

```text
source_system = desktop_chat
source_event_id = client_event_id
```

## 4. 写入、追问和确认

1. P2-A 默认所有支出写入都先形成 `pending_action` 并要求确认；暂不保存“以后自动记账”偏好。
2. 金额缺失或不精确、账户/分类无法唯一解析、话语可能是计划或询问时，只返回一个最能减少不确定性的问题，不写数据库。
3. 未表达日期时可使用可信 `received_at`；相对日期按 Asia/Shanghai 解析。无法唯一解析时必须追问。
4. 确认摘要显示操作、金额、币种、账户、分类、发生时间和候选短编号。
5. 确认是服务端状态转换。模型参数中的 `confirmed=true`、提示词中的授权描述或模型置信度都无效。
6. 普通支出候选默认 24 小时过期。过期、资源归档或版本变化后必须重新查询和确认。
7. 一个来源事件最多提交一个财务写命令；P2-A 一条消息多笔支出返回不支持/待后续批量处理，不循环复用同一来源键。

## 5. 持久状态

P2-A 使用 Alembic 增加 `agent_run`、`pending_action` 和必要的服务端批准/事件记录。实现可以合并批准记录，但必须满足：

- `pending_action` 有 UUID、actor、conversation、run、动作类型、规范化候选、缺失字段、引用资源版本、状态、版本锁、创建/过期时间、最终结果；
- 状态至少包括 `needs_input`、`needs_confirmation`、`committing`、`committed`、`expired`、`cancelled`；
- 并发确认只有一个请求能从待确认进入 `committing`；
- 最终财务来源键固定派生为 `pending:{pending_action_id}:commit`，重复确认调用同一财务命令并取得相同结果；
- 崩溃恢复不得生成新来源键；
- 不保存完整原消息、提示词、模型思维过程、密钥或原始渠道来源 ID。

## 6. 工具输入输出

工具输入使用 `extra="forbid"` 的 Pydantic 模型。查询必须限制时间范围和返回数量，输出带稳定排序、`as_of`，列表需要 `truncated`。

写工具输出是按 `status` 区分的联合类型：

- `committed`：真实 `result_id`、`replayed`、`amount_minor`、`currency`；
- `needs_input`：`pending_action_id`、缺失字段和稳定问题码；
- `needs_confirmation`：`pending_action_id`、确认码和确定性摘要；
- `error`：安全的稳定错误码、文案和 `retryable`。

模型不能计算元/分转换。展示金额由公共格式化函数从整数分生成。

## 7. Agent 循环

- 默认最多 4 个模型轮次、8 次总工具调用、1 次财务写提交；
- 保留未知工具、坏参数、重复调用、空响应和超限停止条件；
- 新增 `paused` 状态、`pending_action_id` 和稳定 `pause_reason`；
- 查询工具可多次调用，写入计数独立限制；
- 财务安全错误结构化返回；未知异常仍归一为 `tool_error`，不泄露异常正文；
- 模型临时故障最多 1 次有界重试；认证、无效请求和权限错误不重试；
- 写入成功后，即使最终自然语言生成失败，也不得再次写入，只能以同一来源键重放结果。

## 8. HTTP 边界

P2-A 增加版本化端点，具体 URL 名称冻结为：

- `POST /api/v1/agent/runs`：提交桌面 `client_event_id`、`conversation_id` 和消息；身份与权限由服务端依赖注入；
- `POST /api/v1/agent/runs/{run_id}/resume`：绑定同一 actor/conversation，对指定候选补充、确认或取消；
- `GET /api/v1/agent/runs/{run_id}`：读取结构化状态和最终结果，不返回原始提示词或内部工具载荷。

HTTP 使用 Pydantic 严格 Schema，拒绝额外字段。P2-A 不实现流式输出、登录系统或多用户资源隔离；测试通过可替换依赖注入虚拟身份。

## 9. 微信边界

当前 OpenClaw 没有经验证的稳定来源消息 ID。P2-A 不恢复 OpenClaw，也不允许微信首条消息直接写账。未来接入前：

- 微信查询可开放；
- 微信写入只能形成候选并以候选编号确认；
- 候选提交可防重复确认，但不能宣称解决重复原消息；
- 微信稳定事件 ID 单列后续渠道任务，不阻塞桌面 P2-A。

## 10. 错误、权限与隐私

新增稳定错误至少包括：`permission_denied`、`source_event_id_unavailable`、`confirmation_required`、`missing_required_context`、`ambiguous_reference`、`pending_action_not_found`、`pending_action_expired`、`pending_action_stale`、`write_limit_exceeded`。

保留并安全映射 P1 `FinanceError.code`。日志只记录关联 ID、工具名、阶段、耗时、结果类型和错误码；禁止原消息、完整参数、账号、原来源 ID、密钥、数据库异常正文和模型思维过程。

## 11. 文件所有权

P2-B4 执行智能体可修改：

- `src/wife_system/agent/**`
- 分配的 `src/wife_system/api/**`
- P2 新迁移
- `tests/agent_finance/**`
- 必要依赖和 `docs/p2-a-running.md`
- 自身角色日志

P1 `src/wife_system/finance/**` 和已有 P1 migration 默认只读；发现必须变更时停止并交回总控。测试智能体拥有 `docs/testing/phase-2-agent-test-matrix.md`、未来 `tests/independent/agent_finance/**` 和独立报告。

## 12. P2-A 验收门槛

至少覆盖：完整候选确认写入、同事件重放、冲突载荷、缺字段追问、计划/询问不入账、账户/分类歧义、权限拒绝、第二次写入阻止、重复/并发确认、过期/stale、模型和数据库故障、写成功后回答失败、五个只读查询、重启恢复、日志隐私、HTTP schema/状态以及微信无稳定来源 ID 时禁止直接写入。

执行方自测只能提交 `review`；独立验收和总控核对后才能完成 P2-A。
