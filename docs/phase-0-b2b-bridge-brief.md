# B2b：OpenClaw TypeScript 桥接任务书

任务编号：`B2b`
维护者：头脑风暴智能体
输入接口：`P0-IF-002` 与已通过独立验收的 B2a FastAPI 探针

## 目标

建立一个可独立测试的 OpenClaw TypeScript 插件。插件把 OpenClaw 中的确定性命令和 Agent 工具请求转发到本机 Python `POST /api/v1/probes`，由 Python 生成请求编号、随机回执和时间。TypeScript 不生成成功回执，也不包含财务计算。

本阶段先完成本地构建、客户端契约和插件注册验证。安装微信插件、扫码登录、真实消息发送和手机实收必须等本地验收通过后由用户参与。

## 已核实环境

- Node.js：`26.8.1`
- npm：`11.19.0`
- OpenClaw：`2026.8.2`
- 当前微信插件候选：`@tencent-weixin/openclaw-weixin@2.4.8`
- Python 探针默认地址：`http://127.0.0.1:8000`
- 客户端默认超时：5 秒

OpenClaw 插件 API 属于实验性接口，因此本插件只声明并验证 OpenClaw `2026.8.2`。升级宿主前重新构建和测试。

## 实现范围

执行智能体拥有 `integrations/openclaw/`，至少交付：

- `package.json`、锁文件、`tsconfig.json`、`openclaw.plugin.json`；
- 独立的 `FinanceProbeClient`，负责 URL、JSON、必填 header、5 秒超时、响应校验和安全错误映射；
- 插件入口，注册 `/finance-probe` 确定性命令和 `finance_probe` Agent 工具；
- 执行方测试与本地运行说明。

客户端接受调用者提供的 `idempotencyKey`，不得用 challenge、完整消息文本、账号标识、会话标识或固定值代替。Agent 工具使用 OpenClaw 传给 `execute` 的 tool call ID，因此同一工具调用重试保持同一个键。

技术顾问已经核实：本机 `2026.8.2` 的命令上下文没有来源消息 ID 或事件 ID。`/finance-probe` 命令每次 handler 生成随机 invocation UUID，只用于该次 HTTP 调用关联；它不承诺微信重投去重，也不做隐藏自动重试。后续若 OpenClaw 或微信插件公开可信事件 ID，再把命令适配器切换为来源事件键。命令必须设置 `requireAuth: true`，不得持久化账号或消息正文。

## 行为契约

成功响应只接受以下结构：

```json
{
  "request_id": "UUID",
  "challenge": "V001",
  "receipt": "POC-...",
  "created_at": "带时区 ISO 8601 时间",
  "replayed": false
}
```

- 2xx 但 JSON 无效或字段错误：`invalid_backend_response`。
- Python 409：`duplicate_request_conflict`，不可重试。
- Python 422：`invalid_request`，不可重试。
- Python 500 或其他 5xx：`backend_unavailable`，可重试。
- 超时：`backend_timeout`，可重试。
- 拒绝连接或其他传输失败：`backend_unavailable`，可重试。
- 用户可见错误只显示稳定错误码和简短说明；不得包含 URL 查询、堆栈、原始响应、账号、消息正文或密钥。
- 日志可以记录请求关联 ID、错误码、耗时和回执；不得记录 challenge、原始幂等键、微信身份或异常正文。

命令成功文本必须包含 Python 返回的 `request_id`、`receipt`、`created_at` 和 `replayed`。Agent 工具必须把同一结构放在稳定的 `details` 中，并提供简短文本内容。

## 验收

1. TypeScript 类型检查、单元测试和构建通过。
2. 使用假 HTTP 服务验证健康成功、首次探针、同键重放、409、422、500、坏 JSON、字段缺失、超时和拒绝连接。
3. 并发相同调用 ID 时，后端返回的幂等结果保持一致；桥接不自行伪造结果。
4. 日志、用户错误和测试输出通过 canary 检查，不能泄漏私密输入或异常正文。
5. 用本机 OpenClaw `2026.8.2` 检查插件 manifest、运行入口和注册结果；不修改用户现有 OpenClaw 配置。
6. 测试智能体独立复验后，才进入微信插件安装与用户扫码。

## 文件边界

- 执行智能体：`integrations/openclaw/`、`docs/b2b-running.md`、自己的角色状态。
- 测试智能体：`integrations/openclaw/tests/independent/`、`docs/testing/phase-0-c2-b2b-report.md`、自己的角色状态；不修改执行方源码。
- 技术顾问：`docs/phase-0-d2-bridge-teaching.md`、自己的角色状态；先核实命令幂等来源，再结合最终代码完成教学。
- 头脑风暴：接口冻结、总览、验收和用户联调安排。

所有角色不得执行 Git 提交或推送，不得读取、记录或提交 OpenClaw/微信/模型密钥。
