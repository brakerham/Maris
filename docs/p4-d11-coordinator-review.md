# P4-D11 Windows Shell 技术方案总控审阅

- 审阅任务：`P4-D11`
- 审阅角色：头脑风暴总控
- 审阅时间：2026-09-27，Asia/Shanghai
- 结论：`accepted / complete`
- 后续冻结：[P4-IF-003](phase-4-interface-freeze-003.md)

## 1. 结论

技术顾问交付的 [Windows Shell、毛毛与模块 UI 技术方案](phase-4-d11-windows-shell-technical-advice.md)可以作为 P4-B 的实现依据。它把桌面程序分为 Electron main、preload 和 React renderer 三层，保留 P4-A FastAPI Host 为权威后端，并明确了本地 owner 会话、模块 UI 注册、OpenAPI 类型生成、BackendSupervisor、离线 outbox、Tray、毛毛、主题和测试边界。

本次接受的是**实现前技术设计**。Electron、Node、pnpm 和前端依赖尚未安装，桌面程序尚未实现，P4-B 的 24 项矩阵仍全部为 `not_run`。D11 不能被描述为桌面产品已经完成。

总控接受 D11，但在 P4-IF-003 中加入两项勘误：

1. TypeScript 7.0 已于 2026-07-08 发布。D11 把 TypeScript 6.0 写成“当前稳定”已过期。由于 TypeScript 7.0 尚未提供稳定 compiler API，部分工具仍依赖 6.0 API，本项目有意固定 `6.0.3` 作为首版兼容基线，并在 7.1 或工具链明确兼容后重新评估。
2. Electron Forge 官方要求 pnpm 项目在 `.npmrc` 中使用 `node-linker=hoisted`，P4-B7 必须把这一项纳入可复现安装和打包门禁。

这两处不改变 D11 的核心架构，也不需要建立 `P4-D11-R1`。

## 2. 交付核对

| 项目 | 实际结果 | 结论 |
| --- | --- | --- |
| 技术方案 | 1093 行、67 个标题、22 个代码块、6 张 Mermaid 图 | 完整 |
| 矩阵映射 | `P4B-SEC-01～08`、`SUP-01～06`、`UI-01～04`、`CMP-01～06`，共 24 个唯一 ID | 完整 |
| 本地链接 | 19 个本地链接及行号有效 | 通过 |
| 文件格式 | 无尾随空白、UTF-8 无 BOM、末尾换行存在 | 通过 |
| 技术方案 SHA-256 | `ad3dc4b899d7462d46c8b344eba0c8cd044622059d274ccfbdca7a9aba532405` | 与交接一致 |
| 技术顾问状态 SHA-256 | `c052b37e7d532dd4f4f39759118ee450b11a809f1bd4a04ef2818caa89bee02d` | 与交接一致 |

## 3. 与现有代码的相容性

总控对照当前 P4-A 代码确认：

- bootstrap status、owner initialize、login 和 refresh API 已存在，可供 Electron main 建立自动本地 owner 会话；
- `/api/v1/modules` 已提供后端启用模块的安全摘要，桌面 compiled registry 可以与其求交集；
- `/healthz` 与 `/readyz` 已存在，但当前 `/readyz` 没有 desktop startup nonce；D11 正确把 nonce 标为 P4-B 的窄扩展；
- production factory 已显式装配数据库、Finance、Host、Agent 和 activity import，桌面受管后端必须使用这一组合根；
- 当前仓库没有 Electron、React、设备设置、加密 outbox、Tray 或毛毛窗口，D11 没有把这些未来能力写成当前事实。

## 4. 接受的关键决定

- 使用 Electron 模块化单体桌面壳；不改成 Tauri、微服务或浏览器直接访问数据库。
- Electron main 独占 token、文件、进程、窗口、Tray、safeStorage 和 Host HTTP；renderer 不持有这些能力。
- preload 只暴露固定的 typed API，不暴露原始 `ipcRenderer` 或通用执行入口。
- 生产 renderer 的网络策略为 `connect-src 'none'`；所有 Host 请求经 main 代理。
- UI 模块采用 `DesktopModuleContribution` 和 compiled registry；Shell 不按 `moduleId` 写业务分支。
- OpenAPI Schema 在仓库内离线导出并生成 TypeScript 类型；运行时不下载 Schema。
- 使用现有 P4-A owner/session 结构，不增加公众注册、第二用户、云账户或常规登录页。
- `BackendSupervisor` 只管理自己启动且 nonce/句柄匹配的 Python 后端。
- 离线 outbox 由 main 加密持久化，并固定 `client_event_id` 处理重试和响应丢失。
- 全局只有一个毛毛窗口；模块切换改变同一毛毛的主形态，运行状态改变其子状态。
- P4-B 只实现 Shell、生命周期、模块占位与连接能力；真实财务驾驶舱和聊天写账属于 P4-C，财富管理属于 P4-D。

## 5. 未通过本次审阅证明的事项

- 依赖组合是否能在本机完成安装、开发启动、打包和 E2E；
- Windows safeStorage、Tray、开机启动、系统注销、多显示器、DPI、透明窗口和 GPU 降级的真实行为；
- Python sidecar 的正式捆绑、安装器、代码签名和自动更新；
- 24 项 P4-B 独立验收；
- 财务驾驶舱、桌面对话、真实建议、写账确认和投资数据。

## 6. 后续顺序

1. 总控发布 P4-IF-003 和 `P4-B7` 执行任务卡。
2. 用户把 `P4-B7` 任务卡发送给既有执行智能体。
3. 执行智能体完成七个内部里程碑、自测和固定快照，只能停在 `review / finished`。
4. 总控核对交付并生成 C12 固定输入快照。
5. 用户再把 `P4-C12` 任务卡发送给测试智能体；不得在 B7 快照稳定前提前执行 C12。
6. 只有 C12 独立验证通过并由总控接受，P4-B 才能标为 `complete` 和创建本地验收提交。
