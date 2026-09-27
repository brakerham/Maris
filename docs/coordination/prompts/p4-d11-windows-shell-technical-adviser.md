# P4-D11 技术顾问任务卡：Windows Shell、毛毛与模块 UI 技术方案

你是技术顾问，唯一负责 `P4-D11：Windows Shell、毛毛与模块 UI 技术方案`。

## 开始前必须按顺序读取

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. `docs/coordination/control.md`
6. `docs/coordination/agents/technical-adviser.md`
7. `docs/phase-4-b-windows-shell-brainstorm.md`
8. `docs/phase-4-modular-agent-host-architecture.md`
9. `docs/phase-4-d9-modular-agent-host-advice.md`
10. `docs/phase-4-interface-freeze.md`
11. `docs/testing/phase-4-modular-agent-host-test-matrix.md`
12. `docs/p4-a-final-coordinator-review.md`

开始前再次读取最新 `docs/coordination/control.md`。若其中的任务、唯一负责人或停止指令与本任务卡冲突，以最新 control 为准，停止旧动作并报告。

## 目标

在不安装依赖、不编写产品代码、不启动 Electron/FastAPI/Docker/外部服务的前提下，为已经确定视觉基线的 P4-B Windows 桌面 Shell 给出一套可冻结、可实施、可测试、适合用户学习的技术方案。

方案必须让后续执行智能体能够实现：Electron main/preload/renderer 安全三层、React/TypeScript 模块 Shell、P4-A Host 连接、本地 owner 会话、模块注册交集、右侧模块 Agent 面板外壳、唯一毛毛窗口、Tray、主题、设备设置、BackendSupervisor 和离线恢复。

## 已经确定、不得重新讨论的产品事实

1. 应用名为 `Maris`，桌宠名为“毛毛”。
2. 用户已经通过两张效果图确定三栏视觉基线：左侧模块导航、中间模块工作区、右侧模块 Agent。
3. 日常财务效果图是财务驾驶舱目标界面；投资与学习效果图是财富管理子视图参考。
4. 投资不等于财富管理；财富管理还包括应急金、储蓄、保障、现金管理、资产配置和长期目标。
5. 右侧 Agent 随模块切换 Profile、系统规则、工具和模块记忆；页面切换本身不调用模型、不写财务数据。
6. 毛毛只有一个。模块决定主形态，运行状态决定 `idle/listening/thinking/tool/needs_confirmation/error/offline` 子状态。
7. P4-B 首版采用简化透明毛毛窗口 + Tray；不兼容时降级普通迷你窗口。
8. 主窗口首次关闭默认隐藏到 Tray 并提示一次；设置支持隐藏、每次询问、退出。
9. 开机启动默认关闭；毛毛置顶默认关闭；全屏时默认隐藏；隐私模式隐藏金额和敏感气泡。
10. 产品近期为单机、单主人、本地数据库。不做公众注册、第二用户、云账户或常规账号登录 UI；桌面恢复本地 bootstrap owner 安全会话。
11. P4-B 只交付 Shell、生命周期和模块 UI 基础。真实财务驾驶舱/账本/确认写账属于 P4-C，真实财富数据与计算属于 P4-D。
12. P4-A 已由总控验收 `complete`；不要重新审查或重新实现 P4-A。

## 输入与依赖

- P4-A 最终验收提交：`88fb178`。
- P4-B 头脑风暴提交：`6b0e485`，其后的视觉基线纠正文档以当前工作区与最新 control 为准。
- P4-B 现有独立矩阵：24 项，编号 `P4B-SEC-01～08`、`P4B-SUP-01～06`、`P4B-UI-01～04`、`P4B-CMP-01～06`，状态均为 `not_run`。
- Python/FastAPI Host、模块注册、Agent Profile、会话/记忆/设置和 production factory 已在 P4-A 实现并通过验收。
- 尚未安装或运行 Electron、React、TypeScript 桌面工具链；这不是阻塞，而是本任务要先完成选型的原因。

## 唯一负责人和文件边界

- 你是本任务唯一负责人。
- 允许修改：
  - `docs/phase-4-d11-windows-shell-technical-advice.md`
  - `docs/coordination/agents/technical-adviser.md`
- 其余文件全部只读，包括产品代码、migration、测试、矩阵、接口冻结、控制文件、总览、其他角色日志、依赖文件和 Git 状态。
- 不得安装 npm/pnpm/yarn 包，不得生成 `node_modules`、锁文件、桌面脚手架或 OpenAPI 产物。
- 不得启动 Electron、Node 开发服务器、FastAPI、Docker、PostgreSQL、DeepSeek、OpenClaw、微信或浏览器登录流程。
- 不得修改或运行 `tests/independent/**`，不得把方案核对称为独立验收。
- 不得自动继续 P4-IF-003、P4-B7 实现、P4-C12 测试或 P4-C 财务闭环。
- 不得执行任何 Git 写操作。允许只读查看 `git status`、`git diff`、`git log` 和文件摘要。

## 允许的调查

- 可以只读检查当前 Python Host API、OpenAPI、production factory、module manifest、Agent Profile、setting 和错误合同，确保方案与实际代码一致。
- 可以使用网络查阅官方文档，但技术结论优先引用 Electron、Node.js、React、TypeScript、Vite、Playwright、FastAPI/OpenAPI 等官方资料；不要把未经核实的博客当成唯一依据。
- 不需要复跑 P4-A 全量测试。若为了确认一个接口做只读或小范围本地检查，必须单独说明它不是独立验收。

## 必须完成的技术裁定

### 1. 工具链和版本策略

比较并推荐：

- Node.js LTS 版本线；
- Electron 版本线；
- React 与 TypeScript 版本线；
- 包管理器；
- monorepo/workspace 方式；
- 版本锁定、升级和安全补丁策略。

必须说明为什么适合一个 Python 为主、正在学习前后端与 Agent 工程的本科生，并列出至少一个有意义的替代方案及复评条件。

### 2. Electron 构建与未来分发

比较 Electron Forge、electron-vite、Vite + electron-builder 或其他主流组合，给出 P4-B 的推荐方案。区分：

- 当前开发和测试；
- Windows 可运行构建；
- 后续安装器、签名、自动更新和正式发布。

P4-B 不要求签名安装包和自动更新，但目录和构建方案不能阻塞以后加入。

### 3. React Shell 技术栈

裁定：

- 路由方案；
- 服务端状态、Host API 缓存和失效方案；
- 纯 UI/设备状态方案；
- 表单与运行状态处理；
- CSS/主题/token 方案；
- 是否采用组件基础库；
- P4-C/P4-D 图表库的预留方式，但 P4-B 不提前实现图表。

明确哪些状态使用 React 自身、哪些使用查询缓存、哪些才需要独立状态库，避免把全部状态放进一个全局 store。

### 4. 模块 UI 注册合同

基于 D9 的 `DesktopModuleContribution` 草案给出可冻结 TypeScript 合同，至少覆盖：

- `moduleId/version/hostUiMajor`；
- navigation 和 lazy routes；
- Agent panel 的 `profileId/title/starterPrompts`；
- settings contributions；
- companion 主形态与子状态映射；
- route/path/setting/profile/companion 冲突检查；
- 后端 `/modules` 与桌面 compiled registry 的版本兼容和交集算法；
- 未知、禁用、桌面缺失和版本不兼容模块的稳定行为。

Shell 不能包含 `if moduleId === "wealth_management"` 一类业务分支。

### 5. OpenAPI 到 TypeScript

比较并推荐 OpenAPI TypeScript 生成器和调用层方案，冻结：

- Schema 输入来自何处；
- 生成命令与产物目录；
- CI/本地如何检测生成物漂移；
- 哪些 API 类型必须生成，哪些纯 UI 合同应手写；
- 运行时不得下载 schema；
- Pydantic/FastAPI DTO 改变时怎样给出可定位的编译失败。

### 6. Electron 安全三层和 IPC allowlist

给出 main、preload、renderer 的明确职责与禁止事项，并形成最小 typed IPC allowlist。至少处理：

- `sandbox/contextIsolation/nodeIntegration`；
- CSP、导航、新窗口和外部链接；
- IPC sender/origin/参数校验；
- renderer 不得取得 `ipcRenderer`、Node require、文件系统、进程、shell 或任意 channel；
- refresh/device token、模型 API key、启动 nonce 和诊断日志分别放在哪里；
- Windows `safeStorage`/OS 凭据能力的适用边界；
- renderer 的 localStorage/sessionStorage/IndexedDB 可以保存什么、禁止保存什么；
- 错误信息与 request ID 如何安全穿过 IPC。

把建议逐项映射到 `P4B-SEC-01～08`。

### 7. 本地 owner 会话

基于 P4-A 已实现的 bootstrap owner/auth/session，说明没有登录页面时桌面如何：

- 首次启动建立或恢复本地安全会话；
- refresh/access token 只在获准边界流转；
- session 撤销、后端重启和应用重启后的恢复；
- 区分“自动本地 owner 会话”和未来可选应用锁；
- 不重新引入公众注册、多用户或云账户。

### 8. BackendSupervisor

给出可冻结状态机、进程所有权和 ready 协议。至少包含：

- 桌面托管后端与连接开发者手工后端两种模式；
- 随机 loopback port、启动 nonce、PID/进程句柄和实例所有权；
- `starting/online/offline/recovering/failed/stopping`；
- health 与 readiness 的区别；
- ready 超时、坏 nonce、端口冲突、启动前/启动后崩溃；
- 有界重启和退避；
- 只停止自己启动的后端；
- Windows 正常退出、强关主窗口、系统注销和崩溃后的资源收口；
- 开发源码运行与未来打包 Python sidecar 的路径差异；
- 日志位置、轮转、脱敏和用户可见诊断摘要。

把建议逐项映射到 `P4B-SUP-01～06`。

### 9. 未发送消息和离线恢复

冻结 renderer、main 和 Host 对未发送文本及 `client_event_id` 的所有权：

- 后端离线、恢复、应用重启和重复点击时使用同一 ID；
- 何时可以丢弃草稿；
- 怎样避免重复 Agent run、重复候选或重复财务写；
- P4-B 只实现 Shell 状态和恢复基础，不能宣称 P4-C 写账闭环已完成。

### 10. 主窗口、Tray 和关闭策略

给出：

- 主窗口创建、显示、隐藏、聚焦和单实例行为；
- 第一次关闭提示只出现一次；
- “隐藏到 Tray / 每次询问 / 退出”的精确状态；
- Tray 打开/隐藏、退出和后端所有权收口；
- 开机启动默认关闭、显式启用和清理本应用启动项；
- 两个桌面实例或重复启动请求的行为。

### 11. 毛毛窗口与设备设置

给出毛毛 `BrowserWindow` 的推荐配置与降级策略：

- 透明、无边框、拖动、可选置顶；
- 点击/焦点/键盘入口与是否需要 click-through；
- 主形态和子状态的状态源；
- 模块切换不创建第二窗口或第二 Agent；
- 多显示器、DPI、缩放、分辨率变化和拔屏后的边界夹取；
- 全屏隐藏、隐私模式和 reduced motion；
- 透明/GPU/无障碍不兼容时降级普通迷你窗口；
- 设备设置 JSON 的 schema version、默认值、迁移、节流和临时文件原子替换；
- 账户同步设置与设备本地设置的边界。

把建议逐项映射到 `P4B-CMP-01～06`。

### 12. 主题与视觉实现

以已确认的两张效果图为视觉基线，给出语义 token、布局断点和无障碍策略。至少包括：

- system/light/dark/high-contrast/reduced-motion；
- surface/text/accent/success/warning/danger/income/expense/market-up/market-down；
- 中国市场与国际市场涨跌色作为财富模块设置；
- 收入/支出颜色不得复用行情涨跌含义；
- Agent 面板折叠、窄屏与最小窗口尺寸；
- 恶意/超长/RTL 文本的安全布局；
- 图标、插画和毛毛资源未来如何进入项目，不在 P4-B 技术方案中生成最终美术。

### 13. 测试策略

比较并推荐：

- TypeScript 单元测试；
- React 组件测试；
- Electron main/preload/IPC 合同测试；
- Electron Windows E2E；
- Playwright Electron 或其他方案；
- 安全静态检查；
- Windows 手工验收；
- 多显示器、全屏、开机启动和系统注销等无法稳定自动化的项目如何记录证据。

明确 Spectron 等已过时方案是否排除以及原因。把执行方自测与测试智能体独立验收分开；不得把执行方 E2E 称为独立验收。

### 14. 目录、命令和开发数据流

给出建议目录，至少覆盖：

```text
apps/desktop/
  electron/main/
  electron/preload/
  src/shell/
  src/modules/
  src/generated/
  tests/
```

给出未来开发者需要的命令形态，但本任务不得实际安装或执行，例如：安装、类型生成、开发运行、单元测试、E2E、构建和差异检查。

用 Mermaid 描述至少四条数据流：

1. 启动与本地 owner 会话；
2. 模块切换 → Agent Profile → 毛毛形态；
3. renderer → preload → main → Host API；
4. 后端崩溃 → offline → 有界恢复 → 同 ID 重试。

### 15. 实施顺序与文件所有权

给出 P4-B 实施顺序、每一步的文件范围、进入条件、自测和停止条件。优先建议一个执行任务配合内部里程碑；只有确有共享文件冲突或 Windows 环境门禁时才拆成顺序子任务，避免无必要的微任务和重复全量测试。

提出后续任务命名建议：

- 总控冻结：`P4-IF-003`；
- 执行实现：`P4-B7`；
- 独立验收：`P4-C12`。

技术顾问只提出方案，不自行创建这些任务、不修改 control、不派发其他智能体。

### 16. 教学地图

用户会 Python 和 Git，但没有系统学过 JavaScript/TypeScript、前端、后端或 Electron。请给出与实际项目代码对应的学习顺序，每节说明：

- 要解决的项目问题；
- 需要理解的概念；
- 将来对应的代码目录；
- 一个可亲手完成的小练习；
- 可验证结果。

至少覆盖 TypeScript 类型、ES Modules、React 组件与状态、HTTP/OpenAPI、Electron 进程模型、IPC、安全边界、子进程生命周期和桌面 E2E。不要把教学写成与项目无关的通用课程目录。

## 必须提供的方案比较格式

每个关键选型至少包含：

| 项目 | 推荐方案 | 备选方案 | 推荐理由 | 代价 | 何时复评 |
| --- | --- | --- | --- | --- | --- |

必须区分：

- 官方文档能够保证的事实；
- 结合本项目得出的工程判断；
- 尚未在当前 Windows 设备实际验证的假设。

## 交付物

1. `docs/phase-4-d11-windows-shell-technical-advice.md`
2. 更新 `docs/coordination/agents/technical-adviser.md`
3. 最终回复向总控报告：推荐栈、关键合同、与 24 项矩阵的映射、开放问题、未验证项、文件摘要和当前状态

## 验收标准

- 文档完整覆盖上述 16 个主题，没有把已经确定的视觉布局重新列为待用户决定。
- 至少有一张总架构图和上述四条数据流，Mermaid 围栏成对。
- 所有关键技术选择均有推荐、替代、代价和复评条件。
- `P4B-SEC-01～08`、`P4B-SUP-01～06`、`P4B-UI-01～04`、`P4B-CMP-01～06` 共 24 项均能在文档中找到明确设计证据映射。
- 方案与当前 P4-A API、module/profile/memory/settings 和单机单主人范围一致。
- 不新增产品代码、依赖、锁文件、脚手架、生成物、测试或外部状态。
- 本地 Markdown 链接有效；代码围栏与 Mermaid 围栏成对；无尾随空白；交付文件提供 SHA-256。
- 未验证的 Electron/Windows 行为明确标为 `unverified`，不得写成已通过。

## 进度与停止规则

- 接单后立即更新技术顾问角色文件，记录当前步骤、开始时间、最近进展、心跳、下一检查点和等待对象。
- 在完成选型比较、核心合同、测试映射和最终校验时分别记录里程碑；预计超过五分钟的工作先写检查点。
- 至少每十分钟或出现实质输出时更新心跳。
- 若连续两个检查点没有新进展，安全停止并报告卡点、最后脱敏错误、已尝试办法、可能原因和需要总控裁定的问题。
- 若命令执行器或网络阻止读取资料，不要凭旧印象写结论；记录受阻项，能继续的部分先继续，重复无进展后停止。
- 发现新 control 与本任务冲突时，立即停止旧任务。

## 完成状态

交付完成后停在 `review / finished`。技术顾问无权把 `P4-D11`、`P4-B` 或项目标记为 `complete`，无权开始 P4-IF-003、P4-B7、P4-C12 或任何实现、测试、安装和外部集成。

## 安全要求

- 不读取、输出或记录 API key、GitHub token、微信身份、二维码、个人账号标识和真实个人财务数据。
- 文档示例只使用虚拟数据和虚拟路径。
- 不执行 Git 写操作，不操作 GitHub 远端，不修改任何账号、凭据或全局配置。
