# B2b OpenClaw 桥接运行说明

本文对应冻结接口 `P0-IF-002`。桥接把 OpenClaw 的 `/finance-probe` 命令和 `finance_probe` Agent 工具转发到本机 FastAPI `POST /api/v1/probes`。TypeScript 只转发并验证结果，不生成成功请求号、回执或时间。

## 已验证环境

| 组件 | 实际版本 |
| --- | --- |
| Node.js | `26.8.1` |
| npm | `11.19.0` |
| OpenClaw | `2026.8.2 (0965053)` |
| TypeBox | `1.3.17` |
| TypeScript | `5.9.3` |

插件只声明兼容 OpenClaw `2026.8.2`。宿主升级后应重新执行类型检查、测试和 runtime inspect。

## 文件入口

- [`client.ts`](../integrations/openclaw/src/client.ts)：本机 URL 限制、header/body、默认 5 秒超时、JSON 运行时校验、错误映射和脱敏日志。
- [`config.ts`](../integrations/openclaw/src/config.ts)：插件配置默认值和严格字段读取。
- [`errors.ts`](../integrations/openclaw/src/errors.ts)：稳定错误码、可重试标记和安全说明。
- [`index.ts`](../integrations/openclaw/src/index.ts)：注册确定性命令和 Agent 工具。
- [`openclaw.plugin.json`](../integrations/openclaw/openclaw.plugin.json)：工具所有权、命令激活和配置 Schema。
- [`package.json`](../integrations/openclaw/package.json)：构建入口、精确 OpenClaw peer 版本和本地检查脚本。

## 本地构建与检查

在 `integrations/openclaw` 目录执行：

```powershell
npm ci --ignore-scripts
npm run check
npm pack --dry-run --json
```

`npm run check` 依次执行严格 TypeScript 类型检查、构建和执行方 Node 测试。`npm pack --dry-run` 只检查发布包内容，不发布插件。

Python 服务运行方式见 [B2a 运行说明](b2-running.md)。默认地址是 `http://127.0.0.1:8000`。插件配置支持：

```json
{
  "backendBaseUrl": "http://127.0.0.1:8000",
  "timeoutMs": 5000
}
```

阶段 0 后端没有桥接鉴权，所以客户端只接受 `127.0.0.1`、`localhost` 或 `[::1]` 的 HTTP(S) 地址，拒绝 URL 凭据、查询、片段和 HTTP 重定向。跨机器部署前必须先设计服务认证和 TLS。

## 命令和工具的幂等范围

- `/finance-probe V001` 绕过 LLM，命令显式设置 `requireAuth: true`。OpenClaw 2026.8.2 的命令上下文没有来源事件 ID，因此每次 handler 调用生成新的随机 invocation UUID。它只标识本次 HTTP 调用，不保证微信事件重投去重。
- `finance_probe` 使用 OpenClaw 传给 `execute(toolCallId, ...)` 的原始 tool call ID。同一工具调用的显式重试会把同一个键交给 Python。
- 两条路径都不把 challenge、消息正文、账号、发送方、会话 ID 或固定值当作幂等键，也不做隐藏自动重试。

## 响应与错误

客户端只接受字段集合精确、challenge 一致、请求号为 UUID、回执合法、时间带时区且 replayed 为布尔值的 2xx JSON。成功文本包含 Python 返回的 `request_id`、`receipt`、`created_at` 和 `replayed`；工具把五个字段原样放入 `details`。

| 后端或传输结果 | 桥接错误码 | 可重试 |
| --- | --- | --- |
| HTTP 409 | `duplicate_request_conflict` | 否 |
| HTTP 422 | `invalid_request` | 否 |
| HTTP 5xx | `backend_unavailable` | 是 |
| 超时 | `backend_timeout` | 是 |
| 拒绝连接等传输失败 | `backend_unavailable` | 是 |
| 2xx 但响应不符合契约 | `invalid_backend_response` | 否 |

日志不记录 challenge、原始幂等键、微信身份、URL、后端正文、异常正文或堆栈。成功日志可记录请求号、回执、重放状态和耗时；失败日志只记录稳定错误信息与安全关联号。

## 执行方验证证据

- `npm run check`：严格类型检查、构建及 `27` 项 Node 测试通过。
- `npm audit --omit=dev --json`：生产依赖漏洞总数 `0`。
- `npm pack --dry-run --json`：退出码 0；包中只有 `dist/`、manifest 和 package 元数据，共 18 个文件。
- `openclaw plugins inspect wife-system-finance-probe --runtime --json`：在隔离的配置和状态目录中退出码 0；状态 `loaded`，发现工具 `finance_probe`、命令 `finance-probe`、严格配置 Schema，`diagnostics` 为空。未读取或修改用户现有 OpenClaw 配置。
- 真实跨语言冒烟：TypeScript 客户端访问临时 Uvicorn；健康检查 200，同一键首次与重放均为 200，Python 返回的 request ID、receipt、created_at 保持一致，第二次 `replayed:true`。临时服务随后停止，端口释放。
- Python 全量回归：`143 passed, 1 warning`；现有 Starlette/AnyIO 弃用警告与 B2a 报告一致，没有新增 Python 回归失败。

`openclaw plugins validate` 返回“entry does not expose defineToolPlugin metadata”。该命令只校验 `defineToolPlugin` 生成的纯工具元数据；本插件同时注册命令和工具，按本机文档使用 `definePluginEntry`。因此最终宿主证据采用隔离的 runtime inspect，且该检查实际成功加载了构建入口。

## 尚未验证

- C2-B2b 独立测试与总控验收；
- 腾讯微信插件的实际安装版本；
- 用户扫码、微信入站消息、OpenClaw 出站回复和手机实收；
- 微信来源事件级幂等、跨 Python 重启或多 worker 幂等；
- 正式账目写入、真实 DeepSeek 和长期提醒。

只有 C2-B2b 与总控验收通过后，才进入微信插件安装和用户扫码阶段。
