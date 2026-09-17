# C2-B2b 独立测试计划

状态：稳定 B2b 实现已完成独立验证；客户端、插件、元数据与隔离 OpenClaw 运行时共 `44` 项通过，正式结论见 `docs/testing/phase-0-c2-b2b-report.md`。依据：`docs/phase-0-b2b-bridge-brief.md`、`P0-IF-002`、C2-B2a HTTP 验收报告及总控补充的命令/工具幂等决策。

本目录只包含测试智能体拥有的独立测试。不得从这里修改桥接实现、`package.json`、锁文件、`tsconfig.json`、执行方测试或用户 OpenClaw 配置。

## 固定判定

- 客户端每次调用必须向 `/api/v1/probes` 发出一条 POST，JSON 仅为 `challenge`，header 必须含调用者给出的 `Idempotency-Key`。
- 客户端不做隐藏自动重试。一次客户端调用在 409、422、5xx、超时或传输失败时最多产生一次后端请求；是否重试由调用者根据 `retryable` 决定。
- 命令 `/finance-probe` 设置 `requireAuth: true`。OpenClaw 2026.8.2 的命令上下文没有来源事件 ID，因此每次 handler 调用生成新的 invocation UUID 作为幂等键；不得声称具备微信事件重投去重保证。
- 命令 handler 不得把 `senderId`、`from`、`to`、`accountId`、`sessionKey`、完整 `commandBody` 或 challenge 用作幂等键，也不得记录这些字段。
- Agent 工具 `finance_probe` 必须直接使用 `execute(toolCallId, ...)` 的 `toolCallId` 作为幂等键。同一工具调用的并发或显式重试必须向后端传相同键。
- TypeScript 不能生成或替换成功 `request_id`、receipt、`created_at` 或 replayed；成功文本和工具 `details` 都取自 Python 响应。
- 用户错误和日志只允许稳定错误码、简短安全说明、关联 ID、耗时及成功 receipt；不得包含原始响应、URL 查询、challenge、原始幂等键、身份字段、异常正文、堆栈或内部路径。

## 假后端脚手架

独立测试使用绑定 `127.0.0.1` 随机端口的 Node `http.createServer`，记录每次请求的方法、路径、header、JSON 和连接中止状态。每个用例启动自己的服务并在 `after`/`finally` 中关闭，不访问外部网络。

稳定成功夹具：

```json
{
  "request_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "challenge": "V001",
  "receipt": "POC-C2-B2B-BACKEND-RECEIPT",
  "created_at": "2026-09-14T21:40:00+08:00",
  "replayed": false
}
```

重放夹具只把 `replayed` 改为 `true`，其余字段保持相同。错误响应使用明显 canary，但测试报告只能记录是否泄漏，不能复制原文。

## 客户端判定矩阵

| ID | 场景 | 假后端行为 | 必须断言 |
| --- | --- | --- | --- |
| B2B-C01 | 首次成功 | 200 + 完整成功 JSON | 原样返回五个字段；POST 路径、body、header 正确；客户端不伪造值 |
| B2B-C02 | 后端重放 | 200 + `replayed:true` | 五个字段原样返回，重放状态不被桥接覆盖 |
| B2B-C03 | 409 | 409 + `duplicate_request_conflict` | 映射同名 code、`retryable:false`；一次调用只发一条请求 |
| B2B-C04 | 422 | 422 + `invalid_request` | 映射同名 code、`retryable:false`；不暴露原始后端 body |
| B2B-C05 | 500/503 | 500 与 503 + 私密正文 | 均映射 `backend_unavailable`、`retryable:true`；不暴露正文 |
| B2B-C06 | 非 JSON | 2xx + 截断 JSON/HTML | `invalid_backend_response`；不返回原文 |
| B2B-C07 | 缺字段 | 分别缺每个必填字段 | `invalid_backend_response`；不接受部分结果 |
| B2B-C08 | 字段类型/值错误 | 非 UUID request_id、空 receipt、naive/坏时间、非 bool replayed、challenge 不匹配 | 全部 `invalid_backend_response` |
| B2B-C09 | 额外字段 | 2xx + 成功字段和额外敏感字段 | 按“只接受该结构”判 `invalid_backend_response`；敏感字段不泄漏 |
| B2B-C10 | 超时 | 服务收到请求后延迟超过测试配置 | `backend_timeout`、`retryable:true`；AbortSignal 取消；无隐藏重试 |
| B2B-C11 | 拒绝连接 | 使用已关闭的随机本机端口 | `backend_unavailable`、`retryable:true`；错误不含 URL/端口/堆栈 |
| B2B-C12 | 调用者重试 | 第一次 503，调用者第二次用同一键重试并成功 | 两次各一条请求、header 键相同；第二次值来自后端 |
| B2B-C13 | 并发同键 | 两个并发调用使用同一 tool call ID，后端返回同一重放记录 | 两条请求键一致；两结果与后端一致；客户端不另造 receipt |
| B2B-C14 | 并发不同键 | 两个不同 tool call ID、同 challenge | header 不同且结果不串线 |
| B2B-C15 | 配置边界 | 默认配置、0/负数/NaN timeout、非 HTTP(S) 或含查询/凭据的 URL | 默认 `http://127.0.0.1:8000` 和 5000 ms；坏配置安全拒绝，不进入网络 |

## 插件注册与适配器矩阵

使用假的 `OpenClawPluginApi` 捕获 `registerCommand`、`registerTool` 和 logger 调用。只实现插件注册实际访问的 API 字段；任何额外宿主依赖都应在测试中显式暴露。

| ID | 场景 | 必须断言 |
| --- | --- | --- |
| B2B-P01 | 注册入口 | 恰好注册命令 `finance-probe` 和工具 `finance_probe`；无微信 SDK 或 Python 内部类型依赖 |
| B2B-P02 | 命令元数据 | `acceptsArgs:true`、`requireAuth:true`；handler 直接返回 OpenClaw 命令结果 |
| B2B-P03 | 命令成功 | 文本包含后端 request_id、receipt、created_at、replayed；没有桥接生成的替代值 |
| B2B-P04 | 命令调用键 | 连续两次 handler 即使上下文/参数相同也使用两个不同 UUID；不使用 sender/from/accountId/commandBody/challenge |
| B2B-P05 | 命令错误 | 用户文本只含稳定 code 与安全说明；不含异常正文、后端 URL 或身份 canary |
| B2B-P06 | 工具参数与结果 | 参数 schema 严格要求 challenge；结果 `content` 为简短文本，`details` 精确含五字段 |
| B2B-P07 | 工具幂等键 | `execute` 收到的 tool call ID 原样交给客户端；同 ID 重试仍用同键，不自行重试 |
| B2B-P08 | abort | OpenClaw 传入已取消/随后取消的 signal 时停止请求并返回安全、可重试错误，不留迟到成功 |
| B2B-P09 | 日志隐私 | 成功、409、422、500、坏响应、超时、拒绝连接均检查日志；不含 challenge、原键、senderId/from/to/accountId/session 字段、异常正文、堆栈或路径 |

## OpenClaw 2026.8.2 manifest/runtime 检查

当前只读环境事实：Node 26.8.1、npm 11.19.0、OpenClaw `2026.8.2 (0965053)`。安装包的真实类型表明：

- `OpenClawPluginApi.registerCommand(command)` 与 `registerTool(tool, opts?)` 均存在；
- 工具执行签名为 `execute(toolCallId, params, signal, onUpdate, ctx)`；
- 命令定义支持 `requireAuth`，默认虽为 true，本插件仍须显式设为 true；
- 命令上下文含 sender/account/session/commandBody，但没有来源消息事件 ID；
- `definePluginEntry` 是混合命令+工具插件的适用入口；
- 每个工具必须出现在 manifest 的 `contracts.tools`；外部插件运行入口应指向构建后的 JavaScript。

验收时执行：

1. 检查 `package.json` 为 ESM，`openclaw.extensions` 指向实际存在的构建 JS，兼容性元数据只声明已验证的 2026.8.2；
2. 检查 `openclaw.plugin.json` id/name/description、严格 `configSchema`、`contracts.tools:["finance_probe"]`、activation 与 package 入口一致；
3. 运行项目提供的 typecheck、单元测试和 build；
4. 运行 `openclaw plugins validate --root <插件根> --entry <构建入口> --json`；该命令只读项目文件；
5. 用独立临时 `OPENCLAW_STATE_DIR` 和 `OPENCLAW_CONFIG_PATH` 做 runtime inspection，禁止读取或写入用户默认 `~/.openclaw`；若 CLI 无法在不安装/配置插件时检查本地 runtime，则改用直接导入构建入口和假的 Plugin API 捕获注册，并把 CLI runtime 标记为未测，不能修改用户配置绕过；
6. 检查 `openclaw plugins inspect <id> --runtime --json`（仅在隔离临时状态中可发现插件时）列出 `finance_probe` 和 `finance-probe`，且无加载诊断错误。

## 执行顺序与交付

收到稳定实现后，先记录实现文件 SHA-256 与版本，再依据实际公开入口补充可执行 `.test.mjs`，不修改源码来迎合测试。发现问题先向总控提交最小复现，再继续其他独立案例。最终运行：执行方 typecheck/test/build、独立 Node 测试、OpenClaw manifest/runtime 只读检查，以及仓库 Python 全量回归；报告写入 `docs/testing/phase-0-c2-b2b-report.md`。

## 最终执行证据

- `npm run typecheck`、`npm run build`：退出码 0。
- 执行方测试：`27 passed, 0 failed`。
- 独立测试：`44 passed, 0 failed`，文件为 `client-contract.test.mjs`、`plugin-contract.test.mjs`、`metadata-contract.test.mjs` 与 `runtime-contract.test.mjs`。
- `npm pack --dry-run --json`：退出码 0，发布清单仅含 `dist/`、`openclaw.plugin.json` 与 `package.json`，共 18 个文件。
- OpenClaw `2026.8.2` 隔离 runtime inspect：状态 `loaded`，发现 `finance_probe` 和 `finance-probe`，依赖完整，`diagnostics` 为空。
- Python 完整回归：`143 passed, 1 warning`；警告为既有 Starlette/AnyIO 弃用提示。
- `openclaw plugins validate` 只接受 `defineToolPlugin` 纯工具元数据，当前命令加工具的 `definePluginEntry` 会被该命令拒绝；以实际成功加载的隔离 runtime inspect 作为混合插件宿主证据。
