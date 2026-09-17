# P2-D6：P2-A 财务 Agent 实现后教学

- 任务：P2-D6
- 角色：技术顾问
- 文档状态：review
- 实现快照：P2-B4-SHA256:f0eacf340d87f7dd0ea11ae51396f5022cec99dc0f3a3009883b30aaf17362e6
- 本地证据：独立 P2 测试 45 项通过；执行方 P2 测试 23 项通过
- 证据边界：84 个矩阵案例中 71 个已有本地证据，13 个外部环境案例未完整执行
- 数据边界：示例仅使用虚拟身份、账户、分类和金额

本文讲解固定快照中的实际代码。两项最终回归失败发生在既有 Phase-0 Uvicorn 健康等待阶段，没有进入 P2 业务断言，当前证据没有形成 P2 产品缺陷。真实 PostgreSQL、DeepSeek、桌面端与微信案例没有被写成已经通过。

## 总数据流

~~~mermaid
sequenceDiagram
    autonumber
    actor U as 用户
    participant API as FastAPI
    participant APP as AgentApplication
    participant S as agent_run / pending_action
    participant R as AgentRunner
    participant M as 模型
    participant T as ToolRegistry
    participant A as FinanceToolAdapter
    participant F as FinanceService
    participant DB as 财务数据库

    U->>API: 午饭 18 元 + client_event_id
    API->>API: Pydantic 校验；注入身份与权限
    API->>APP: start
    APP->>S: 领取或重放 agent_run
    APP->>R: 文本 + RunContext
    R->>M: 消息 + 可见工具 Schema
    M-->>R: finance_record_expense 参数
    R->>T: invoke
    T->>T: 白名单 + Pydantic 校验
    T->>A: 参数 + 可信上下文
    A->>S: 创建 pending_action
    S-->>U: needs_confirmation
    U->>API: confirm + confirmation_code
    API->>APP: resume
    APP->>S: needs_confirmation -> committing
    APP->>A: commit
    A->>F: RecordExpense + pending:{id}:commit
    F->>DB: 收据、交易、分录、审计同一事务
    DB-->>F: result_id
    F-->>APP: committed + result_id + replayed
    APP->>S: pending=committed; run=success
    APP-->>U: 结构化数据库回执
~~~

核心规则是：模型提出工具调用，程序验证和执行，数据库决定写入是否成功。确认后的提交不再依赖模型生成“成功”文案。

## 1. “午饭 18 元”的完整路径

### 代码位置

- HTTP 请求模型：[agent_schemas.py](../src/wife_system/api/agent_schemas.py#L16)。
- run 路由：[agent_routes.py](../src/wife_system/api/agent_routes.py#L42)。
- 领取 run 与启动应用：[application.py](../src/wife_system/agent/application.py#L118)、[application.py](../src/wife_system/agent/application.py#L234)。
- 工具循环：[loop.py](../src/wife_system/agent/loop.py#L48)、[loop.py](../src/wife_system/agent/loop.py#L93)。
- 支出候选：[finance_tools.py](../src/wife_system/agent/finance_tools.py#L312)。
- 确认恢复：[agent_routes.py](../src/wife_system/api/agent_routes.py#L58)、[application.py](../src/wife_system/agent/application.py#L344)。
- 最终提交：[finance_tools.py](../src/wife_system/agent/finance_tools.py#L427)、[service.py](../src/wife_system/finance/service.py#L225)、[service.py](../src/wife_system/finance/service.py#L463)。

### 输入输出示例

~~~json
{
  "client_event_id": "11111111-1111-4111-8111-111111111111",
  "conversation_id": "22222222-2222-4222-8222-222222222222",
  "message": "午饭 18 元"
}
~~~

actor_id 与 permissions 不在 JSON 中，而由服务端注入。模型提出 finance_record_expense，参数包括字符串金额、虚拟账户 UUID 和餐饮分类 UUID。第一次响应是 paused：

~~~json
{
  "status": "paused",
  "pause_reason": "needs_confirmation",
  "pending_action_id": "候选 UUID",
  "result": {
    "status": "needs_confirmation",
    "confirmation_code": "短确认码",
    "summary": {"operation": "record_expense", "amount": "18.00", "currency": "CNY"}
  }
}
~~~

确认后，FinanceService 把 18.00 解析为 1800 分，写一条 expense 交易及两条平衡分录：账户 -1800、支出分类 +1800。最终返回 committed、真实 result_id 与 replayed。执行方 [test_vertical_slice.py](../tests/agent_finance/test_vertical_slice.py#L48) 验证重复确认返回相同 result_id；独立 [test_tools_and_lifecycle.py](../tests/independent/agent_finance/test_tools_and_lifecycle.py#L306) 还验证余额由 100000 分变为 98200 分，只有一个命令收据。

### 常见误区

- 模型说“已记账”不等于成功；成功依据是 FinanceService 的 result_id。
- 第一次请求只创建候选，不写 expense。
- FastAPI 负责边界，不负责金额和账本计算。
- 确认码用于关联候选；approval_grant_id 由服务端生成。
- 确认后直接返回结构化结果，不再让模型决定成功与否。

### 小练习

画出首次请求和确认请求两段时序，分别写出 agent_run、pending_action、financial_transaction 的状态。指出哪一步之前账本中绝不能出现 expense。

## 2. AgentRunner、ToolRegistry、六个工具和确定性程序

### 代码位置

- AgentRunner：[loop.py](../src/wife_system/agent/loop.py#L26)。
- Tool 与 ToolRegistry：[tools.py](../src/wife_system/tools.py#L23)、[tools.py](../src/wife_system/tools.py#L54)。
- 六工具注册：[finance_tools.py](../src/wife_system/agent/finance_tools.py#L456)。
- 适配器：[finance_tools.py](../src/wife_system/agent/finance_tools.py#L209)。
- 确定性财务服务：[service.py](../src/wife_system/finance/service.py#L157)。

AgentRunner 管模型轮次、工具调用、暂停、错误和 4/8/1。ToolRegistry 管注册白名单、权限可见性、Pydantic 参数验证和 handler 分发。

| 工具 | 类型 | 确定性来源 |
| --- | --- | --- |
| finance_list_accounts | 读 | FinanceService.list_accounts |
| finance_list_categories | 读 | FinanceService.list_categories |
| finance_get_account_balance | 读 | FinanceService.account_balance |
| finance_list_transactions | 读 | FinanceService.list_transactions |
| finance_get_monthly_snapshot | 读 | FinanceService.monthly_snapshot |
| finance_record_expense | 候选写 | pending_action；确认后 record_expense |

模型负责理解意图、选择工具和提出候选。程序负责权限、金额精度、相对日期、模糊语义、资源版本、整数分、事务、幂等和最终结果。

### 输入输出示例

余额工具输入 account_id，返回 balance_minor=98200、currency=CNY 与可信 as_of。独立 [test_tools_and_lifecycle.py](../tests/independent/agent_finance/test_tools_and_lifecycle.py#L100) 把五个查询结果与直接调用 P1 FinanceService 的结果对照，因此余额不是模型心算。

### 常见误区

- 工具由名称、描述、输入模型、handler、权限和读写属性共同组成。
- extra="forbid" 只约束数据形状，不能替代权限和确认。
- 隐藏无权限工具还不够；模型可猜名称，所以 handler 再检查权限。
- 查询也必须限制时间、limit、truncated 和 as_of。

### 小练习

以 finance_list_transactions 为例，分别说明 Pydantic、ToolRegistry、FinanceToolAdapter、FinanceService 的职责。写出 limit=0 和无时区 start 的预期结果。

## 3. RunContext、权限和可信来源

### 代码位置

- RunContext：[context.py](../src/wife_system/agent/context.py#L12)。
- 上下文构造：[application.py](../src/wife_system/agent/application.py#L234)。
- 身份依赖：[agent_routes.py](../src/wife_system/api/agent_routes.py#L19)。
- 按权限过滤 Schema：[tools.py](../src/wife_system/tools.py#L60)。
- 独立测试：[test_tools_and_lifecycle.py](../tests/independent/agent_finance/test_tools_and_lifecycle.py#L74)、[test_tools_and_lifecycle.py](../tests/independent/agent_finance/test_tools_and_lifecycle.py#L91)。

RunContext 包含 agent_run_id、actor_id、conversation_id、source_system、source_event_id、received_at、permissions、pending_action_id 和 approval_grant_id。它 extra="forbid"、frozen=True，并要求 received_at 带时区。

这些字段决定谁在操作、来源是什么、能做什么、可信时间是什么以及批准哪个候选。模型可能误解或遭提示词注入，所以不能生成 actor_id、permissions、confirmed 或 source_event_id。它们不在工具 Schema 中。

### 输入输出示例

客户端只提交 message、client_event_id、conversation_id。服务端注入 actor_id 和权限，记录 received_at，固定 source_system=desktop_chat，并把复用的 client_event_id 作为可信来源事件。无写权限时写工具从 Schema 隐藏；模型即使猜到名称，handler 仍返回 permission_denied。

### 常见误区

- conversation_id 不是认证身份。
- 提示词写“已经确认”不构成服务端批准。
- JSON Schema 合法只能证明形状正确。
- frozen=True 不是全部安全，入口构造、权限检查和数据库约束同样必要。

### 小练习

列出模型不能控制的 RunContext 字段。设计把 actor_id 和 confirmed 塞入工具参数的攻击，说明它在哪一层被拒绝。

## 4. agent_run、pending_action、过期和恢复

### 代码位置

- 两张表：[models.py](../src/wife_system/agent/models.py#L15)、[models.py](../src/wife_system/agent/models.py#L46)。
- PendingActionStore：[pending.py](../src/wife_system/agent/pending.py#L53)。
- 创建、补充、领取、完成：[pending.py](../src/wife_system/agent/pending.py#L79)、[pending.py](../src/wife_system/agent/pending.py#L157)、[pending.py](../src/wife_system/agent/pending.py#L194)、[pending.py](../src/wife_system/agent/pending.py#L212)。
- 应用恢复：[application.py](../src/wife_system/agent/application.py#L286)、[application.py](../src/wife_system/agent/application.py#L344)。

agent_run 表示一次来源事件对应的 Agent 运行，状态为 running、paused、success、error。pending_action 表示可恢复的业务候选。

~~~mermaid
stateDiagram-v2
    [*] --> needs_input: 缺字段或意图
    [*] --> needs_confirmation: 字段完整
    needs_input --> needs_input: 仍缺字段
    needs_input --> needs_confirmation: 补齐
    needs_input --> cancelled: 取消
    needs_confirmation --> cancelled: 取消
    needs_input --> expired: 到期
    needs_confirmation --> expired: 到期
    needs_confirmation --> committing: 确认码 + 条件更新
    committing --> committed: 财务提交成功
    committing --> committing: 暂时故障后同键重试
~~~

TTL 是 24 小时。get 会在事务中把到期候选写成 expired。补充和领取提交权都要求 status 与 version_id 同时匹配，这是乐观锁。重启后的新 AgentApplication 可从数据库恢复 needs_input、needs_confirmation、committing、committed。

### 输入输出示例

缺账户时返回 needs_input、pending_action_id、missing_fields、question_code=ask_account_id 和最多五个数据库真实选项。补齐后同一个 pending_action_id 进入 needs_confirmation。确认失败时保持 paused/committing，恢复后仍用同一候选。

### 常见误区

- agent_run 记录 Agent 请求；pending_action 记录业务候选。
- paused 是等待用户，不是失败。
- 过期会持久化，而非只在内存判断。
- version_id 用来拒绝旧视图并发更新。
- committed 后应读取保存结果或同键重放，不能删除重做。

### 小练习

设计“补账户 → 补分类 → 确认”的状态轨迹并写 version_id 变化。解释两个并发补充请求为什么最多一个使用旧 version_id 成功。

## 5. 六类编号

### 代码位置

- client_event_id：[agent_schemas.py](../src/wife_system/api/agent_schemas.py#L16)。
- run_id：[application.py](../src/wife_system/agent/application.py#L118)。
- tool_call_id：[types.py](../src/wife_system/agent/types.py#L12)、[loop.py](../src/wife_system/agent/loop.py#L93)。
- pending_action_id：[models.py](../src/wife_system/agent/models.py#L46)。
- source_event_id：[context.py](../src/wife_system/agent/context.py#L12)、[schemas.py](../src/wife_system/finance/schemas.py#L18)。
- result_id：[service.py](../src/wife_system/finance/service.py#L225)。

| 编号 | 生成者 | 稳定范围 | 用途 |
| --- | --- | --- | --- |
| client_event_id | 桌面客户端 | 同一次提交及网络重试 | 入口幂等 |
| run_id | agent_run 主键 | 一条来源事件 | 关联运行、状态、日志 |
| tool_call_id | 模型协议 | 一次工具调用 | 关联调用结果、检测重复 |
| pending_action_id | 候选表 | 一个候选 | 恢复、确认、并发、派生提交键 |
| source_event_id | 可信入口/程序 | 一个来源事件 | 持久业务幂等 |
| result_id | FinanceService/数据库 | 一个已提交结果 | 指向 financial_transaction |

桌面首段 source_event_id 等于 client_event_id 字符串。财务确认段使用 pending:{pending_action_id}:commit。同一候选重复确认、重启或响应丢失时都会命中同一命令收据。P2 路径中的 AgentRunResult.request_id 等于 run_id 字符串，只是内部兼容命名。

### 输入输出示例

~~~text
client_event_id   = 1111...
run_id            = aaaa...
tool_call_id      = expense-call
pending_action_id = bbbb...
source_event_id   = 首段 1111...；提交段 pending:bbbb...:commit
result_id         = cccc...
~~~

首次 HTTP 重试复用 client_event_id，因此 run_id 不变；重复确认复用 pending_action_id，因此最终 result_id 相同。

### 常见误区

- 重试时生成新 UUID 会破坏幂等。
- tool_call_id 不能用作财务来源键。
- result_id 提交成功后才存在。
- 微信目前没有经验证的稳定消息 ID，不能用会话 ID、发送者 ID或文本哈希冒充。

### 小练习

为“首次请求超时重试”和“连续点两次确认”各画编号表，标出必须相同和可不同的编号，以及最终防重层。

## 6. 幂等、重复确认、并发确认和事务

### 代码位置

- run 唯一约束：[models.py](../src/wife_system/agent/models.py#L15)。
- 来源摘要与冲突：[application.py](../src/wife_system/agent/application.py#L118)。
- 进程内锁：[application.py](../src/wife_system/agent/application.py#L66)。
- 候选条件更新：[pending.py](../src/wife_system/agent/pending.py#L194)。
- 稳定提交键：[finance_tools.py](../src/wife_system/agent/finance_tools.py#L427)。
- 财务收据与事务：[service.py](../src/wife_system/finance/service.py#L178)、[service.py](../src/wife_system/finance/service.py#L225)。
- 独立并发证据：[test_idempotency_and_loop.py](../tests/independent/agent_finance/test_idempotency_and_loop.py#L87)、[test_idempotency_and_loop.py](../tests/independent/agent_finance/test_idempotency_and_loop.py#L120)。

四层保护：

1. 入口持久幂等：actor_id、source_system、source_event_digest 唯一；同键同载荷重放，同键不同载荷冲突。
2. 进程内合并：相同 run 正在执行时第二线程等待，模型只调用一次。
3. 候选乐观并发：needs_confirmation + version_id 条件更新为 committing。
4. 财务持久幂等：一个 Session.begin 中领取 command_receipt、写交易、平衡分录、审计和结果。

幂等表示重复逻辑请求的最终业务效果等同一次，不表示每一行代码绝不再次运行。

### 输入输出示例

~~~text
第一次确认：pending -> committing -> 写入 -> committed，replayed=false
第二次确认：读取 committed -> 同键重放，replayed=true
result_id 相同，expense 仍为 1
~~~

本地线程测试已证明单进程并发只写一笔。跨进程最终依赖数据库收据，但真实 PostgreSQL 双连接“提交成功、响应丢失”DB-03 未完整执行，不能声称目标库故障恢复已验证。独立 [test_idempotency_and_loop.py](../tests/independent/agent_finance/test_idempotency_and_loop.py#L59) 还验证模型阻塞期间连接池借出数为零。

### 常见误区

- threading.Lock 会在重启后消失，不能单独承担幂等。
- 唯一约束还需配合请求指纹，防止同键不同载荷。
- 幂等不能把失败伪装成成功；故障时保持 paused/committing。
- 等待模型或用户时不能持有数据库事务。
- 事务保证单次原子性，不替代跨请求幂等键。

### 小练习

画两个线程同时确认的时间线，标出 Python 锁、pending 条件更新、command_receipt 唯一键和 FinanceService 事务各保护什么。

## 7. 4/8/1、错误、隐私和微信安全降级

### 代码位置

- 4/8/1：[loop.py](../src/wife_system/agent/loop.py#L26)。
- 停止条件：[loop.py](../src/wife_system/agent/loop.py#L93)。
- 安全错误：[finance_tools.py](../src/wife_system/agent/finance_tools.py#L160)。
- HTTP 映射与日志：[app.py](../src/wife_system/api/app.py#L88)。
- 隐私字段：[models.py](../src/wife_system/agent/models.py#L15)。
- 微信降级测试：[test_tools_and_http.py](../tests/agent_finance/test_tools_and_http.py#L88)。
- 隐私独立测试：[test_idempotency_and_loop.py](../tests/independent/agent_finance/test_idempotency_and_loop.py#L233)、[test_http_and_migration.py](../tests/independent/agent_finance/test_http_and_migration.py#L130)。

4/8/1 是最多 4 个模型轮次、8 次总工具调用、1 次写工具调用。循环还拒绝未知工具、坏参数、重复 tool_call_id、重复相同调用和空响应。临时模型错误最多重试一次；认证等永久错误不重试。

| 层 | 示例 | 对外结果 |
| --- | --- | --- |
| HTTP/Pydantic | UUID 错、空消息、额外字段 | 422 invalid_request |
| Agent/工具 | 未知工具、坏参数、权限、超限 | 稳定 error_code |
| 财务/数据库 | FinanceError、SQLAlchemy 故障 | 安全 code；未知为 tool_error |

日志只记录关联 ID、路径、工具名、阶段、耗时、结果类型和错误码。禁止原消息、完整参数、actor、原来源 ID、账号、密钥、SQL、异常正文和思维过程。agent_run 保存 HMAC 摘要和脱敏 events_json；pending_action 保存规范化候选。

微信降级：P2-B4 未恢复 OpenClaw；没有稳定微信事件 ID 时可查询，写请求只能形成带编号候选，首条消息不得提交。同一候选可防重复确认，但重复原消息仍可能产生多个候选，裸“确认”也不能自动选择。

### 输入输出示例

未知工具返回 unknown_tool；数据库未知异常只返回 tool_error，测试 canary 不出现在响应、日志或数据库。无 source_event_id 的虚拟微信上下文调用写工具只返回 needs_confirmation，账本无 expense。

### 常见误区

- 4/8/1 是保险丝，不是正确性证明。
- retryable=true 不表示无限重试。
- 完整参数日志会泄露财务和身份信息。
- 候选去重不等于微信原消息去重。
- Uvicorn 健康等待失败没有进入 P2 路径，不能归类为 P2 缺陷。

### 小练习

构造第 9 次工具调用、第二次写工具调用、extra HTTP 字段、私密 canary 数据库异常。写出预期错误码，以及日志允许和禁止字段。

## 8. 执行方测试与独立测试

### 代码位置与证据

执行方测试位于 [tests/agent_finance](../tests/agent_finance/)，23 项通过。它随实现交付，覆盖纵向路径、重复与并发、补充、五查询、HTTP、权限、模糊语义、过期/stale、故障恢复、迁移和隐私。代表位置：

- [test_vertical_slice.py](../tests/agent_finance/test_vertical_slice.py#L48)
- [test_failures_and_policy.py](../tests/agent_finance/test_failures_and_policy.py#L189)
- [test_tools_and_http.py](../tests/agent_finance/test_tools_and_http.py#L146)

独立测试位于 [tests/independent/agent_finance](../tests/independent/agent_finance/)，45 项通过。它从冻结契约反向验证上下文、查询与 P1 对照、权限、候选生命周期、来源幂等、并发、重启、4/8/1、数据库故障、HTTP 安全信封、隐私 canary、迁移和账本一致性。代表位置：

- [test_tools_and_lifecycle.py](../tests/independent/agent_finance/test_tools_and_lifecycle.py#L74)
- [test_idempotency_and_loop.py](../tests/independent/agent_finance/test_idempotency_and_loop.py#L120)
- [test_http_and_migration.py](../tests/independent/agent_finance/test_http_and_migration.py#L30)

C6 重算 23 文件快照并精确匹配。84 个矩阵案例中 71 个有本地证据，13 个未完整执行：真实 PostgreSQL 1、微信 5、真实 DeepSeek 3、桌面 3、Agent 真实回环断线 1。最终项目回归 305 通过、8 跳过、2 失败；两项失败属于既有 Phase-0 Uvicorn 健康等待。

### 输入输出示例

执行方测试回答“实现者交付的路径能否运行”；独立测试回答“冻结契约的安全、边界、并发、恢复和隐私能否被另一套测试观察到”。

### 常见误区

- 23+45 不是 68 个完全不同需求，关键风险会交叉覆盖。
- 执行方自测不能替代独立验收。
- 71/84 是证据计数，不是产品完成度百分比。
- skipped 或未执行不能写成通过。
- 基础设施失败不能隐藏，也不能无证据归因给 P2。

### 小练习

对比执行方 [test_vertical_slice.py](../tests/agent_finance/test_vertical_slice.py#L160) 与独立 [test_idempotency_and_loop.py](../tests/independent/agent_finance/test_idempotency_and_loop.py#L120) 的并发确认测试，写出共同不变量和独立测试额外检查的恢复行为。

## 9. 为什么当前不使用 LangGraph

### 代码位置

当前编排在 [loop.py](../src/wife_system/agent/loop.py#L26)、[application.py](../src/wife_system/agent/application.py#L66)、[pending.py](../src/wife_system/agent/pending.py#L53)。它只有一次理解、受限查询、一个候选、一次暂停和一次确定性提交。

LangGraph 会增加图节点、checkpoint、thread、interrupt、resume 和序列化概念，却不能替代权限、事务、来源幂等和工具合同。当前显式小循环更容易学习底层边界。

满足以下至少两项且有可测维护成本时，再正式比较：

1. 一个流程有三个以上持久暂停点；
2. 经常跨天或跨重启继续；
3. 同时存在确认、编辑、驳回、重新取数和超时分支；
4. 多步骤需要独立重试、状态检查和可视化；
5. 当前状态机缺陷率或维护成本已有数据。

即使引入 LangGraph，finance_tools 合同、FinanceService 事务、pending 派生提交键和 command_receipt 仍保持框架无关。

### 输入输出示例

当前是 start → model/tool loop → pending pause → resume → deterministic commit。未来若出现“凭证收集 → 多次补充 → 人工审核 → 用户修改 → 隔天恢复 → 重新取数 → 批准/驳回”，才值得做框架对照实验。

### 常见误区

- 框架不会自动提供业务幂等。
- checkpoint 不等于 command_receipt。
- interrupt 恢复可能重跑节点，副作用仍须幂等。
- 代码行数不是充分理由，应看分支、暂停、恢复与缺陷成本。
- 当前不使用是延期决策，不是永久拒绝。

### 小练习

把 P2-A 画成五个状态节点，再为复杂退款审核增加节点。数暂停点和恢复分支，判断是否满足 LangGraph 对照条件。

## 术语表

| 术语 | 项目含义 |
| --- | --- |
| FastAPI 边界 | 接收 HTTP、Pydantic 校验、注入身份、调用应用服务 |
| Pydantic Schema | 验证输入输出形状、类型和额外字段 |
| AgentRunner | 有界模型工具循环 |
| ToolRegistry | 工具白名单、Schema、参数验证和分发 |
| RunContext | 可信入口构造且不可变的身份、来源、时间和权限 |
| AgentApplication | 协调持久 run、Runner、候选恢复和 HTTP 用例 |
| agent_run | 一次来源事件对应的持久运行 |
| pending_action | 等待补充、确认、提交或恢复的候选 |
| 乐观锁 | 用 status 与 version_id 条件更新，拒绝旧视图 |
| 幂等 | 重复请求的最终效果等同执行一次 |
| 请求指纹 | 判断同一幂等键下载荷是否相同的 HMAC 摘要 |
| command_receipt | FinanceService 在事务内领取和保存结果的收据 |
| result_id | 已提交业务结果 UUID，P2-A 指向 financial_transaction |
| 整数分 | 18.00 CNY 存为 1800 |
| 脚本化模型 | ScriptedModelProvider，不联网 |
| 安全降级 | 缺微信稳定事件 ID 时只查询或建候选 |
| 固定快照 | 对 23 个指定文件计算并匹配的内容摘要 |
| TestClient | 不启动真实网络服务的 FastAPI HTTP 合同客户端 |

## 学习顺序

1. 读 [agent_schemas.py](../src/wife_system/api/agent_schemas.py#L16) 和 [agent_routes.py](../src/wife_system/api/agent_routes.py#L42)，理解 HTTP 到 Python 对象。
2. 读 [context.py](../src/wife_system/agent/context.py#L12)，区分客户端、模型与服务端可信字段。
3. 读 [tools.py](../src/wife_system/tools.py#L23) 和 [finance_tools.py](../src/wife_system/agent/finance_tools.py#L456)，理解工具合同。
4. 读 [loop.py](../src/wife_system/agent/loop.py#L93)，跟踪一次调用和 4/8/1。
5. 读 [finance_tools.py](../src/wife_system/agent/finance_tools.py#L312)，理解程序策略如何修正候选。
6. 读 [models.py](../src/wife_system/agent/models.py#L15) 和 [pending.py](../src/wife_system/agent/pending.py#L53)，手画状态机。
7. 读 [application.py](../src/wife_system/agent/application.py#L118) 和 [application.py](../src/wife_system/agent/application.py#L344)，串联幂等与恢复。
8. 读 [service.py](../src/wife_system/finance/service.py#L178) 和 [service.py](../src/wife_system/finance/service.py#L225)，理解收据与事务。
9. 对照两类测试，把不变量写成证据。
10. 最后做 LangGraph 对照设计。

## 综合亲手练习

练习：给候选确认过程增加只读预览函数。先放在独立练习文件，不修改当前产品代码。

1. 输入 run_id、actor_id、conversation_id。
2. 只返回 operation、amount、currency、status、expires_at、候选短编号。
3. 错误 actor 或 conversation 统一返回 not found。
4. 不返回原消息、source_event_id、approval_grant_id、完整 action_json。
5. 为 needs_confirmation、expired、committed、错误身份各写一个测试。
6. 解释它为何不消耗一次写工具限额，也不能改变 version_id。

将来正式集成位置：src/wife_system/agent/application.py、src/wife_system/api/agent_schemas.py、src/wife_system/api/agent_routes.py、tests/agent_finance。独立验收仍由测试智能体维护 tests/independent/agent_finance。

## 五道理解检查题

1. client_event_id、tool_call_id、result_id 为什么不能互换？分别说明稳定范围。
2. 第一次返回 needs_confirmation 时，数据库已有和未有的记录是什么？
3. Python 锁、pending version_id、command_receipt 分别防什么？
4. 模型输出 confirmed=true 为什么无效？它在哪层被拒绝，真正批准在哪里产生？
5. 哪些证据支持“P2-A 本地通过”，哪些未执行项使我们不能宣称 PostgreSQL、DeepSeek、桌面和微信已通过？

## 给总控的教学结论

P2-A 已形成可教学、可测试的最小链：FastAPI 严格输入、可信身份注入、持久 run 幂等、AgentRunner 有界循环、候选确认、稳定提交键、FinanceService 单事务写入和结构化回执。核心取舍是显式小循环与业务状态机，使权限、幂等、事务和模型推理边界保持可见。

本地证据足以教学六工具、候选恢复、重复与并发确认、4/8/1、错误和隐私。真实 PostgreSQL 双连接恢复、真实 DeepSeek、桌面、微信和 Agent 真实回环断线仍需后续环境任务；OpenClaw 安全暂停继续有效。LangGraph 暂不引入，等复杂持久工作流满足触发条件后再做对照实验。
