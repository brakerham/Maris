# P2-A 自然语言财务 Agent 运行与交接

- 任务：`P2-B4`
- 接口：`P2-IF-001`
- 交付状态：`review`（执行方自测完成，等待 P2-C5 独立验收）
- P1 输入：`P1-B3-R1-SHA256:751a78aadacf6317e2dafc711569322f3843051e1fae0ee41f11e4b91cfb29bf`
- 数据边界：全部证据使用虚拟身份、虚拟账目、脚本化模型和隔离 SQLite；没有真实财务数据、账号、消息、来源 ID 或密钥

## 1. 已实现纵向路径

桌面入口提交稳定 `client_event_id`、conversation 和自然语言消息。FastAPI 从可替换依赖注入 actor 与权限，应用服务创建持久 `agent_run`，再把不受模型控制的 `RunContext` 交给原有 `AgentRunner`。模型只能看到六个严格工具 Schema；工具适配器直接调用同进程 `FinanceService`，没有新增内部财务 HTTP 服务。

“午饭 18 元”的完整路径为：

```text
POST /api/v1/agent/runs
  -> AgentRunner + finance_record_expense
  -> pending_action(needs_confirmation, 24h)
  -> POST /api/v1/agent/runs/{run_id}/resume
  -> needs_confirmation -> committing（条件更新）
  -> FinanceService.record_expense(
       source_system=<可信入口>,
       source_event_id="pending:{pending_action_id}:commit"
     )
  -> pending_action(committed) + 真实 result_id
```

等待模型和用户时没有持有 SQLAlchemy Session。模型不生成身份、权限、来源事件、批准或最终幂等键，也不负责元/分转换、余额或月度快照计算。

## 2. 六个工具

只读工具直接包装 P1，并保留整数分、稳定排序和受限结果：

- `finance_list_accounts`：最多 50 项，返回 `as_of`、`truncated`；
- `finance_list_categories`：支持 income/expense 过滤，最多 50 项；
- `finance_get_account_balance`：返回 CNY 整数分和可信时间点；
- `finance_list_transactions`：时间范围默认最多回看 31 天，limit 为 1～50；
- `finance_get_monthly_snapshot`：直接包装 P1 确定性快照；
- `finance_record_expense`：只创建或恢复候选，普通支出也默认先确认。

所有输入模型使用 `extra="forbid"`。可信 context 字段不出现在模型 JSON Schema；无权限工具从发送给模型的清单隐藏，即使模型猜中名称，服务端仍再次拒绝。

## 3. 候选、确认和恢复

`pending_action` 保存规范化候选、缺失字段、账户/分类版本、状态、版本锁、服务端批准、24 小时过期时间和最终结果。它不保存完整消息、提示词、思维过程、密钥或原始渠道来源 ID。

- 金额、账户或分类缺失时返回 `needs_input`，只给一个 `question_code`；账户/分类问题附最多 5 个真实选项。
- “大概/左右/十几”等模糊金额、计划/条件表达和模糊相对日期不能被模型给出的精确值绕过。
- “今天/昨天”按可信 `received_at` 和 Asia/Shanghai 解释；未表达日期时使用可信接收时间。
- 一条消息出现多笔金额时返回 `multiple_expenses_unsupported`，不会循环复用一个来源事件。
- 完整候选返回操作、金额、CNY、账户、分类、时间和短确认码。
- 确认码只负责用户关联；真正批准 UUID 由服务端生成。`confirmed=true` 或提示词内的授权描述会被严格 Schema 拒绝。
- 重复或并发确认复用同一个 `pending:{id}:commit`；服务重启后 `needs_input`、`needs_confirmation`、`committing` 和 `committed` 均从数据库恢复。
- 候选到期、actor/conversation 不匹配、账户/分类归档或版本变化时拒绝旧提交。

桌面 `client_event_id` 以 HMAC 摘要持久化。同事件同载荷重试复用 run；不同消息或 conversation 返回 `duplicate_request_conflict`。HMAC key 必须跨进程重启保持稳定，不能使用测试值。

## 4. HTTP 边界

已注册冻结的三条端点：

```text
POST /api/v1/agent/runs
POST /api/v1/agent/runs/{run_id}/resume
GET  /api/v1/agent/runs/{run_id}?conversation_id=<uuid>
```

请求和响应均为严格 Pydantic Schema。客户端只能提供事件 UUID、conversation、消息及 resume 动作；actor 和权限来自 `AgentIdentity` 依赖，测试可替换。响应返回结构化 run 状态、安全错误、候选 ID 和最终结果，不返回原消息、系统提示或完整内部工具载荷。

应用组装入口：

```python
from wife_system.agent.application import build_agent_application
from wife_system.api.app import create_app
from wife_system.finance import FinanceService, IdempotencyKeys
from wife_system.finance.db import make_engine, make_session_factory

engine = make_engine("sqlite+pysqlite:///wife-system.db")
sessions = make_session_factory(engine)
finance = FinanceService(sessions, IdempotencyKeys({1: b"replace-with-stable-secret"}))
agent = build_agent_application(
    sessions=sessions,
    finance=finance,
    provider=provider,
    digest_key=b"replace-with-separate-stable-agent-secret",
)
app = create_app(agent_application=agent)
```

启动应用前先运行迁移：

```text
.venv\Scripts\alembic.exe upgrade head
```

当前迁移链：

```text
base -> bfc163b9b8e9 -> 1377551283d0 -> 7f3e2d1c9a4b (head)
```

新 revision 只增加 `agent_run` 和 `pending_action`，没有改写 P1 表或既有 P1 revision。SQLite 已实际验证升级、重复升级、降到 P1 head 后重建和 `alembic check`。

## 5. 循环限制、故障与隐私

- 默认最多 4 个模型轮次、8 次总工具调用、1 次写工具调用。
- 临时模型超时/不可用在可信 P2 运行中最多重试 1 次；认证、无效请求和权限错误不重试。旧阶段 0 调用方式保持原有一次调用语义。
- 未知工具、坏参数、重复 call ID/相同调用、空响应、工具/写入超限均稳定停止。
- 已知 `FinanceError` 保留安全 code/retryable；SQLAlchemy 不可用归一为 `database_unavailable`；未知确认异常归一为 `tool_error`，不返回异常正文。
- 财务提交成功不依赖最终自然语言生成；确认端点直接持久化 committed 结构化结果，恢复只用同一来源键重放。
- `agent_run.events_json` 与 `wife_system.agent` 结构化日志只含 run 关联 ID、工具名、阶段、耗时、结果类型和错误码。原消息、actor、原来源 ID、完整参数、账号、密钥、SQL 和异常正文不进入日志。

## 6. 微信边界

P2-B4 没有恢复、重装或操作 OpenClaw。`wechat_openclaw` 缺少稳定来源事件 ID 时，只读工具仍可用；写工具只能形成带编号候选，不能由首条消息直接提交。候选确认可以防重复确认，但不宣称解决重复原消息：重复微信文本仍可能生成多个候选，裸“确认”也不能选择其中任何一个。

## 7. 执行方验证

执行方专属测试位于 `tests/agent_finance/**`，覆盖完整候选确认、缺字段恢复、同事件冲突、重复/并发确认、并发同事件、重启恢复、过期/stale、取消、权限、4/8/1 限制、模型/数据库故障、五个查询、严格 HTTP、迁移、日志/持久隐私、可信相对日期、模糊金额/计划和微信候选降级。

```text
.venv\Scripts\python.exe -m pytest tests/agent_finance
23 passed

.venv\Scripts\python.exe -m pytest
258 passed, 5 failed, 8 skipped
```

全量中的 5 个失败均是 P1 迁移测试仍固定断言“17 张表、head=1377551283d0”。P2-IF-001 明确要求新增两张持久表和新 revision，因此实际 head 为 `7f3e2d1c9a4b`、业务表为 19 张。这些断言分别位于执行方旧 P1 迁移测试 1 项和测试方独立 P1 迁移测试 4 项；P2-B4 没有权限修改它们。排除这 5 个已定位的陈旧期望后，产品和其余回归没有失败；8 个跳过仍是缺少真实 PostgreSQL 的 P1 项。

只排除上述 5 个精确测试节点后的最终回归为：

```text
259 passed, 8 skipped, 5 deselected
```

其他检查：

```text
alembic base -> head -> head -> 1377551283d0 -> head   通过
alembic check                                               通过
compileall -q src tests migrations                         通过
pip check                                                   通过
```

## 8. 文件索引与交接

- Agent 上下文、循环、策略和持久服务：`src/wife_system/agent/**`
- HTTP：`src/wife_system/api/agent_routes.py`、`agent_schemas.py`、`app.py`
- 通用工具上下文支持：`src/wife_system/tools.py`
- P2 migration：`migrations/versions/7f3e2d1c9a4b_add_agent_run_and_pending_action.py`
- 执行方测试：`tests/agent_finance/**`

交给 P2-C5 的实现快照：

```text
P2-B4-SHA256:f0eacf340d87f7dd0ea11ae51396f5022cec99dc0f3a3009883b30aaf17362e6
```

快照覆盖本节文件索引中的 23 个 Python、migration 和执行方测试文件，但不含本文与角色日志，避免自引用。算法按相对 POSIX 路径的 Python/Unicode 升序，依次写入 4 字节大端路径长度、UTF-8 路径、8 字节大端内容长度和原始文件字节，再计算整体 SHA-256。

尚未执行真实 PostgreSQL、真实 DeepSeek、真实桌面端或微信案例。它们分别等待对应环境、独立测试任务和总控解除 OpenClaw 安全暂停；SQLite/脚本化模型结果不替代这些证据。
