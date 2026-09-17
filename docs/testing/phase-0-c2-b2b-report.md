# 阶段 0 C2-B2b OpenClaw 桥接独立验收报告

- 测试角色：测试智能体 C2
- 验收对象：B2b OpenClaw TypeScript 桥接
- 冻结接口：`P0-IF-002`
- 执行时间：2026-09-15 08:32–08:48，Asia/Shanghai
- 结论：`review`；桥接功能与 OpenClaw 2026.8.2 运行时验收通过，建议总协调接受 B2b 技术交付

## 结论

B2b 桥接通过独立客户端、插件适配、元数据和真实 OpenClaw 隔离运行时验证。独立 Node 套件 `44 passed, 0 failed`，执行方 Node 套件 `27 passed, 0 failed`，TypeScript 类型检查与构建通过，Python 全量回归 `143 passed, 1 warning`。未发现需要执行智能体修复的桥接缺陷。

验证确认：TypeScript 只转发 challenge 和调用方提供的幂等键；成功请求号、随机回执、时间戳和重放标志均来自 Python；409、422、5xx、超时、拒绝连接和坏响应映射稳定；单次失败没有隐藏重试；命令每次生成新的 invocation UUID，Agent 工具原样使用 tool call ID；日志和用户错误没有泄漏测试 canary、原始幂等键、后端正文或微信身份字段。

本结论只覆盖本地 Python 探针与 OpenClaw 桥接。真实微信插件安装、扫码、入站消息、出站回复和手机实收尚未开始。

## 验收基线

环境实测为 Node.js `26.8.1`、npm `11.19.0`、OpenClaw `2026.8.2 (0965053)`。测试前后以下实现与元数据 SHA-256 保持一致：

| 文件 | SHA-256 |
| --- | --- |
| `src/client.ts` | `B4C0079C0D93E68DA4387B74552EC9F7EE13E3D32953B0437287C36274E217D3` |
| `src/config.ts` | `21401345B6DA8CBC47E1526EF9069DD05E2EE0B7725F5347350082FD82F35D38` |
| `src/errors.ts` | `F3E2EB9C47AACDB200D9D2E2BB3CE5FD8B152146479026CE98E789D5A57F579C` |
| `src/index.ts` | `EFAA861FF12F654E286D7E5BC2896810487A6ECA5C1A1A297E6FC595F1BC2FAF` |
| `openclaw.plugin.json` | `EEC4A1A38AA9EA0F05E904B15BB7F1FB50772C80068683167563A107C03297E6` |
| `package.json` | `6DE999BBE3B1BC64E8C2522E704D66FFA3D083FFBD5B8F758559E01FFC928115` |
| `package-lock.json` | `C8963E69247E3F1A17D98CF6A83A0A08DF075ABCC1504380D0C0D697A497E5B1` |

测试智能体没有修改 TypeScript 实现、package/锁文件、执行方测试、其他角色台账或用户 OpenClaw 配置。

## 独立覆盖结果

| 范围 | 结果 | 独立证据 |
| --- | --- | --- |
| 健康检查与首次成功 | 通过 | 真实随机回环 HTTP；严格检查方法、路径、body、header 和五字段原样返回 |
| 重放与调用者重试 | 通过 | 同键重放保持后端 request ID/receipt；503 后仅由调用者发起第二次请求 |
| 409、422、500、503 | 通过 | 错误码和 `retryable` 正确；每次调用仅一条请求 |
| 非 JSON、缺字段、坏类型、额外字段 | 通过 | 13 组畸形成功响应均拒绝为 `invalid_backend_response` |
| 超时、取消、拒绝连接 | 通过 | 超时主动 abort；取消和断线返回安全可重试错误；无迟到成功和隐藏重试 |
| 同键与异键并发 | 通过 | 同键保持一致，异键不串线，receipt 全部来自假后端 |
| 配置和输入边界 | 通过 | 非回环、凭据、查询、片段、坏 timeout、空白/超长参数均在网络前拒绝 |
| 命令注册 | 通过 | 仅注册 `finance-probe`，`acceptsArgs:true`、`requireAuth:true` |
| 命令幂等键 | 通过 | 相同上下文连续调用使用两个独立 invocation UUID，不使用身份/正文/challenge |
| Agent 工具 | 通过 | 仅注册 `finance_probe`；tool call ID 与 AbortSignal 原样下传；结果 details 精确 |
| 隐私 | 通过 | 成功、5xx、坏响应及身份上下文 canary 均未出现在结果或日志 |
| manifest/package/锁文件 | 通过 | 插件 ID、命令、工具、严格 Schema、ESM 入口与 OpenClaw 版本一致 |
| OpenClaw runtime inspect | 通过 | 隔离状态中状态 `loaded`；发现命令和工具；依赖完整；`diagnostics:[]` |
| 发布包清单 | 通过 | dry-run 共 18 个文件，仅含 `dist/`、manifest 和 package 元数据 |

独立用例位于：

- [`client-contract.test.mjs`](../../integrations/openclaw/tests/independent/client-contract.test.mjs)
- [`plugin-contract.test.mjs`](../../integrations/openclaw/tests/independent/plugin-contract.test.mjs)
- [`metadata-contract.test.mjs`](../../integrations/openclaw/tests/independent/metadata-contract.test.mjs)
- [`runtime-contract.test.mjs`](../../integrations/openclaw/tests/independent/runtime-contract.test.mjs)
- [`fake-backend.mjs`](../../integrations/openclaw/tests/independent/fake-backend.mjs)

## 命令证据

| 检查 | 结果 |
| --- | --- |
| `npm run typecheck` | 退出码 0 |
| `npm run build` | 退出码 0 |
| `npm test` | `27 passed, 0 failed` |
| 独立 Node 合跑 | `44 passed, 0 failed` |
| `npm pack --dry-run --json` | 退出码 0；18 个发布文件 |
| 隔离 `openclaw plugins inspect wife-system-finance-probe --runtime --json` | 退出码 0；`loaded`；命令/工具已注册；无诊断 |
| `.venv\Scripts\python.exe -m pytest -q` | `143 passed, 1 warning`；退出码 0 |

OpenClaw 在 Windows 上即使使用隔离 `OPENCLAW_STATE_DIR`，仍会在用户 AppData 的 OpenClaw locks 目录建立临时生命周期锁。因此 sandbox 内首次检查因锁目录不可写失败；经授权在 sandbox 外重跑后成功。测试配置和状态仍位于独立临时目录，执行结束后已清理，没有读取或修改默认 OpenClaw 配置。

## `plugins validate` 分级

`openclaw plugins validate --root . --entry dist/index.js --json` 返回 `valid:false`，原因是入口没有 `defineToolPlugin` 元数据。本机 OpenClaw 2026.8.2 文档明确说明该命令用于 `defineToolPlugin` 纯工具插件；本插件同时注册命令和工具，按同版本 SDK 使用 `definePluginEntry`。实际 `plugins inspect --runtime` 已成功导入相同 `dist/index.js`、注册 `finance_probe` 与 `finance-probe`，且诊断为空。

该项记为 CLI 检查适用范围限制，不作为 B2b 功能缺陷，也不通过修改混合插件入口来迎合纯工具校验器。运行说明已记录这一点。

## 已知限制与未验证项

- Python 回归仍有既知 Starlette/AnyIO `DeprecationWarning`；与 C2-B2a 报告一致，本次没有新增 Python 告警或失败。
- `/finance-probe` 的命令上下文没有来源事件 ID，所以每次 handler 使用新 UUID，不能提供微信事件重投去重保证。
- Agent 工具只在 OpenClaw 复用同一 tool call ID 时复用幂等键；TypeScript 不自动重试。
- Python 幂等只在单进程内有效，进程重启和多 worker 不共享记录。
- 阶段 0 仅允许本机回环后端，尚无跨机器认证或 TLS 设计。
- 未验证腾讯微信插件实际版本、扫码登录、真实消息收发、手机实收、账号隔离、网关重启后的微信恢复、真实财务数据、DeepSeek 或长期提醒。

## 交接建议

建议总协调将 B2b 技术交付验收为通过。下一阶段只有在总协调接受本报告后再安装并复核微信插件版本，由用户完成扫码、发送指定测试消息并确认手机实收；测试智能体随后按冻结矩阵执行真实微信联调。
