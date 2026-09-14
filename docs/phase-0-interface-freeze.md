# 阶段 0 接口冻结记录

冻结编号：`P0-IF-001`  
冻结时间：2026-09-14 10:55，Asia/Shanghai  
维护者：头脑风暴智能体  
适用任务：B1 独立复验、B2 探针实现、C2 独立测试

本记录汇总 D1 技术建议、B1 实际代码和 C1 测试矩阵。阶段 0 如需改变下列行为，先由技术顾问说明影响，再由头脑风暴更新冻结编号；执行者和测试者不能各自改变契约。

## 1. 技术边界与目录

- Agent 核心保持模型供应商中立：核心只依赖 `ModelProvider`、中立消息、工具调用和结果类型；DeepSeek 的 HTTP 字段只能存在于适配器中。
- 工具由 Pydantic v2 模型生成 JSON Schema，并在 Python 本地再次校验。工具不得信任模型生成的参数。
- 金额统一使用整数分，币种使用 `CNY`；阶段 0 只读取虚拟数据。
- B1 沿用已经实现的 `src/wife_system/`，不为追求目录形式把代码迁入 `backend/`。B2 的 Python API 放在 `src/wife_system/api/`；OpenClaw TypeScript 桥接放在 `integrations/openclaw/`，两者不能直接共享供应商 SDK 类型。
- FastAPI 是 B2 的薄 HTTP 边界；业务循环、工具和去重规则不能写进路由函数。

## 2. B1 Agent 核心契约

- `AgentRunner.run(user_message, request_id)` 是阶段 0 的同步核心入口。
- `max_model_turns` 表示一次 run 最多调用模型的次数，默认 `4`，最小值 `1`；达到上限后返回 `max_model_turns_exceeded`，不能再发起下一次模型调用。
- 一个模型响应可包含多个工具调用。阶段 0 按返回顺序执行；工具均为只读。未来加入写工具前，必须重新决定预校验、事务和部分成功语义。
- 相同 `tool_call_id`，或同一 run 内工具名与规范化参数完全相同，均返回 `duplicate_tool_call`，不再次执行。
- 模型未返回文本或工具调用时返回 `empty_model_response`。
- 稳定核心错误码包括：`unknown_tool`、`invalid_tool_arguments`、`duplicate_tool_call`、`max_model_turns_exceeded`、`empty_model_response`、`tool_error`、`model_timeout`、`model_invalid_request`、`model_auth_failed`、`model_balance_exhausted`、`model_rate_limited`、`model_unavailable`、`model_invalid_response` 和 `duplicate_request_conflict`。
- 用户可见错误不得带供应商原文、堆栈、密钥、完整提示词或原始私人消息。

## 3. DeepSeek 适配

- 当前 B1 使用直接 HTTP 的薄适配器，调用 OpenAI 兼容的 `/chat/completions`；这在阶段 0 可接受，因为传输可替换且供应商字段没有进入核心。
- API key 只从运行环境注入。基础地址默认 `https://api.deepseek.com`；模型名通过 `DEEPSEEK_MODEL` 配置，不把某个会变化的线上模型版本作为核心契约。
- 自动化测试默认使用确定性替身，禁止因缺少 key 而访问网络。真实 DeepSeek 测试必须显式启动，并单独记录日期、模型名和结果。
- 模型调用默认超时为 15 秒，必须可配置且大于 0；阶段 0 不做隐藏重试。

## 4. 请求去重范围

- B1 的 `request_id` 只在同一个 `AgentRunner` 进程实例内去重。相同 ID、相同输入返回首次结果并追加 `cache_hit`；相同 ID、不同输入返回 `duplicate_request_conflict`。
- 阶段 0 不承诺重启后的 Agent run 去重，也不承诺多进程共享去重状态。C2 必须把跨重启和并发多进程案例标记为 `未测/当前不支持`，不能误报通过。
- B2 探针也先采用进程内、并发安全的去重缓存。正式账目写入前必须迁移到数据库事务和持久化幂等键。
- 去重依据来自通道事件 ID 派生的幂等键，不能依据消息文本；两条内容相同但事件 ID 不同的消息是两个请求。日志只保存幂等键摘要。

## 5. FastAPI 探针契约

B2 必须实现以下两个端点：

### `GET /healthz`

- 仅证明 Python 服务可响应，不调用模型或财务工具。
- 成功：HTTP 200，`{"status":"ok","service":"wife-system"}`。

### `POST /api/v1/probes`

- 请求头：必填 `Idempotency-Key`，由桥接层根据来源事件生成；不得使用微信账号或消息文本。
- JSON 请求：`{"challenge":"非空字符串"}`；长度 1–128，禁止额外字段。
- 首次成功：HTTP 200，返回 `request_id`、原样 `challenge`、随机 `receipt`、带时区的 `created_at`、`replayed:false`。
- 同一键同一载荷重放：HTTP 200，返回首次的 `request_id/receipt/created_at`，并令 `replayed:true`。
- 同一键不同载荷：HTTP 409，错误码 `duplicate_request_conflict`，不得生成新 receipt。
- 请求校验失败：HTTP 422，错误码 `invalid_request`。未处理异常：HTTP 500，错误码 `internal_error`。响应均包含安全的 `request_id`；不得返回堆栈。

`POST /api/v1/agent/runs` 的职责保留为“把 HTTP 请求交给 B1 核心”，但不属于 B2 探针的必做范围。它的外部字段在 C2 修复 B1 问题后另行冻结，OpenClaw 探针不得依赖该端点。

## 6. 超时、版本与提醒

- B1 已冻结模型超时，尚未实现通用工具强制超时。阶段 0 的唯一财务工具是本地只读确定性函数，C1 的 A-16 对 B1 记录为“当前范围不适用”；在引入网络、文件或写入工具前，工具取消与迟到结果处理是强制设计项。
- OpenClaw 桥接调用 Python 探针的客户端超时默认 5 秒，可配置但必须大于 0；停服或超时不能返回成功回执。
- OpenClaw 与微信插件的确切版本在 B2 实际安装时读取并固定到清单或锁文件，同时写入验证证据。冻结记录不猜测尚未安装的版本。
- 正式提醒调度不在 B2 范围。阶段 0 在通道接通后进行 2 分钟、1 小时和次日的实际可达性实验，分别记录任务触发、平台接受、会话实收和手机通知；重启持久化、取消及严格至多一次发送仍记为未实现，不能宣称已有提醒服务。

## 7. 验收分界

- D1 的技术建议和 C1 的测试设计在本记录发布后可由总控验收为 `complete`。
- B1 目前是 `review`：总控复跑通过只证明可运行，仍须 C2 按冻结契约独立验证。
- B2 在 B1 核心问题完成独立复验后实施；真实 OpenClaw、微信和通知结论必须有实际账号侧证据。

