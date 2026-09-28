# P4-B7-R1-E3 执行智能体任务卡：C 盘 Electron 最小三角验证

你是执行智能体，唯一负责 `P4-B7-R1-E3`。本任务只执行 P4-D13 与 `P4-IF-005` 已冻结的 A1/A2 最小动态矩阵：先在 C 盘短 ASCII、任务专属目录中直接启动一次无业务 Electron fixture；只有 A1 完全成功，才在同一目录、同一 fixture、同一 Electron 内容下通过 Playwright 默认 loader 启动一次 A2。

用户把本文件全文发送给你，即表示授权你在本任务边界内：从官方来源恢复固定 Node/pnpm/Electron/Playwright 依赖；在 `C:\MarisE3\<run-id>` 创建任务专属工具、fixture、profile 与受限证据目录；启动本任务拥有的隐藏 Electron 进程；在硬超时或失败时按记录的 PID 与可执行路径结束任务拥有的进程树。不得再次要求用户确认这些已授权动作。任何系统级提权、Procmon、驱动、运行库、系统设置或安全策略操作都不在本任务授权内。

## 必读输入

开始前依次读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. 最新 `docs/coordination/control.md`
6. `docs/coordination/agents/executor.md`
7. `docs/phase-4-d13-electron-windows-crash-advice.md`
8. `docs/p4-d13-coordinator-review.md`
9. `docs/phase-4-interface-freeze-005.md`
10. `docs/p4-b7-r1-e2-r1-blocked-coordinator-review.md`
11. `docs/p4-b7-r1-h1-r1-coordinator-review.md`
12. `docs/b7-r1-h1-package-hygiene-running.md`
13. `apps/desktop/b7-r1-h1-source.sha256`
14. `docs/coordination/snapshots/p4-b7-r1-e3-start.sha256`
15. 本任务卡

最新 control 与本任务冲突时，以 control 为准。外部下载、首次进程启动和条件 A2 启动前都重新读取 control。先在 `docs/coordination/agents/executor.md` 登记接单、当前 cell、开始时间、下一检查点、C 盘任务根和可观察 PID/session；不得把原始私人日志写进角色文件。

## 固定事实与解释边界

- 既有 D 盘最小 fixture 已证明：GPU child 首先以 `0xC0000135 STATUS_DLL_NOT_FOUND` 退出；browser `0x80000003 STATUS_BREAKPOINT` 与 Playwright assertion 随后发生。具体 DLL 与装载失败机制未知。
- D 盘、Playwright、Windows 25H2、混合显卡、GPU sandbox、驱动、Code Integrity 和运行库都仍是待区分假设，不能提前选一个当根因。
- A1 同时改变执行位置和 launcher，只是三角验证入口。A1 成功不能单独证明 D 盘是根因；A1 失败也不能分别量化路径与 launcher。
- 只有 A1 成功后运行 A2，才能让 A2 与既有 D 盘 Playwright 证据形成同 launcher 的位置类对照。即使 A1/A2 都成功，也只能写“支持执行位置、继承 ACL、ADS 或路径元数据相关”，不能直接写“D 盘是根因”。

## 起点门禁

任何下载、C 盘写入或启动前：

1. 逐行复算 `docs/coordination/snapshots/p4-b7-r1-e3-start.sha256`，必须全部匹配。
2. 独立复算 `apps/desktop/b7-r1-h1-source.sha256`，必须为 198 matched、0 mismatch、0 missing，manifest SHA-256 为 `04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1`。
3. 核对 `pnpm-lock.yaml` SHA-256 为 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。
4. 只读确认没有旧任务拥有的 Electron、Maris 或项目 sidecar 进程；不得按名称结束用户的其他 Electron、浏览器、Python 或系统进程。
5. 确认 `C:\MarisE3\<run-id>` 是新的短 ASCII、无空格任务根；若目标已存在或包含未知文件，换一个新 run-id，不覆盖或递归删除未知目录。
6. 重读 control，确认你仍是 E3 唯一负责人；技术顾问、测试智能体、P4-C12、app.asar、package/EXE 与 F1 均停止。

任一固定输入 mismatch/missing、职责冲突、未知进程占用或无法建立全新 C 盘任务根时，立即停为 `blocked / finished`。不 restore、不 reset、不覆盖现场、不启动 Electron。

## C 盘受控环境

### 固定工具与来源

- Node：`24.21.0`，只用官方 Node 发布资产，核对既有官方 ZIP SHA-256 `158f7685b44de51f6c0df1d153526cbcd3e1bc739a8dfc607721cef75de9e541`。
- pnpm：`12.7.0`，只用 npm 官方 registry，并核对 registry integrity。
- workspace lock：只复制根 `package.json`、`pnpm-workspace.yaml`、`pnpm-lock.yaml` 与 `apps/desktop/package.json` 到 C 盘任务根所需的同形目录；在 C 盘副本执行 frozen install。不得修改仓库 lock 或依赖版本。
- Electron：`44.4.5`，只用官方 Electron 资产。官方 ZIP 必须为 158,184,819 bytes，SHA-256 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d`。
- Playwright：只使用 frozen lock 解析出的 `1.63.0` 与其默认 Electron loader；A2 不传 `executablePath`，不打开 production inspect fuse。

安装前后分别记录仓库 lock 与 C 盘 lock 摘要；两者必须一致。记录 C 盘 Electron dist 的有序逐文件 `relative-path<TAB>bytes<TAB>sha256` manifest，并在 A1、A2 前后复算。不得从旧 package/out、第三方 mirror、全局 Electron、未知 cache 或非官方 DLL 网站复制内容。

### 固定 fixture

在 C 盘任务根创建最小 fixture，不复制 Maris 产品代码。fixture 只包含：

- `package.json`，`main` 指向一个 CommonJS main；
- 一个 CommonJS main；
- 一个静态 `index.html`；
- 任务脚本与证据写入只使用 Node/Electron 标准库。

main 必须：

- 在 ready 前 `app.disableHardwareAcceleration()`；
- 使用任务专属、空的 `userData` 目录；
- 创建 `show:false` 的单个 `BrowserWindow`；
- renderer 保持 `sandbox:true`、`contextIsolation:true`、`nodeIntegration:false`；
- 加载本地静态 HTML；
- `did-finish-load` 后由 main 写出不含个人数据的成功 marker，短暂等待后正常退出 0；
- `render-process-gone`、`child-process-gone`、`did-fail-load`、uncaught error 或 promise rejection 写安全事件并以非零码退出；
- 没有网络请求、preload、IPC、Host、Python、数据库、Maris 数据、真实用户 profile 或个人数据。

A1 与 A2 使用同一份 fixture 文件；运行前后计算摘要，任何漂移都停止。基线参数固定包含 `--disable-gpu`，并保持 GPU sandbox 与 renderer sandbox 开启。不得加入 `--no-sandbox`、`--disable-gpu-sandbox`、`--in-process-gpu`、WARP、remote debug 固定端口、额外 `--vmodule` 或其他诊断开关。

## 证据合同

在 C 盘任务根下建立任务专属 `evidence` 目录。首次启动前记录：

- run-id、UTC/本地时间窗口；
- Node/pnpm/Electron/Playwright 精确版本与来源摘要；
- Electron dist 与 fixture 有序 manifest；
- 任务根和 Electron dist 的 ACL 摘要、路径长度与 `Get-Item -Stream *` 结果；
- Windows build、CPU 架构与显示适配器名称的只读摘要；
- 启动参数的脱敏形式。

每个 cell 使用独立的 profile、marker、driver log 与 `electron.log`。Electron 参数包含 `--enable-logging=file`、任务专属 `--log-file=<evidence path>` 与最小 `--log-level`。原始日志、Windows 事件导出或截图只保留在 C 盘受限 evidence 目录，不复制进仓库。仓库报告只写脱敏事件顺序、状态码、摘要和解释边界。

任务结束时关闭所有任务拥有的进程，但在总控接受前保留整个 C 盘任务根，尤其是 Electron dist、fixture、profile、原始日志和 manifest；不得覆盖或删除，以便失败后 F1 或成功后产品 gate 复用完全相同的现场。角色文件只记录 C 盘根的固定公共前缀、run-id 和摘要，不记录用户名、token 或私人路径。

## A1：C 盘 direct，最多一次

首次启动前重读 control。使用 C 盘 Electron `electron.exe` 直接启动 fixture，不经过 Playwright/inspector/CDP。使用隐藏窗口和有界、可观察进程会话；启动命令中的 Chromium switches 位于 app path 之前。单次硬超时 60 秒。

A1 只有同时满足以下条件才算成功：

1. app ready、隐藏 BrowserWindow 创建并完成本地页面加载；
2. fixture 成功 marker 完整且与本 cell/run-id 匹配；
3. browser 正常退出 0；
4. `electron.log` 和 driver log 均成功落盘；
5. 日志与精确时间窗 Windows 事件中没有 GPU/browser/renderer 非零退出、`0xC0000135`、`0x80000003`、`STATUS_DLL_NOT_FOUND`、`STATUS_BREAKPOINT`、render-process-gone、child-process-gone 或新异常；
6. Electron dist/fixture 摘要前后不变；
7. 本任务 Electron 进程树最终为 0，没有测试窗口、Tray 或 profile 写入范围外的残留。

若出现 Windows 弹窗、任一 child/browser 非零退出、日志缺失、硬超时、摘要漂移或 owned process 无法收口，A1 失败并立即结束整个 E3。按已记录 PID 和 C 盘可执行路径关闭任务拥有的进程；不关闭 WerFault、系统服务或用户其他进程；不运行 A2、Procmon、F1、诊断开关或第二次 A1。

## A2：C 盘 Playwright，条件最多一次

只有 A1 完全成功、资源收口并重新读取最新 control 后才允许 A2。A2 必须：

- 从 C 盘 frozen install 的 Playwright 调用 `_electron.launch()`；
- 不传 `executablePath`，让 Playwright 使用同一 C 盘 workspace 的默认 Electron loader；
- 使用与 A1 同一 fixture、同一 Electron dist、同一基线参数与安全边界；
- 使用新的空 profile、独立日志和 marker；
- 不加载 app.asar、Maris.exe 或任何产品代码；
- 单次硬超时 60 秒，不重复。

A2 成功条件与 A1 相同，并额外要求 Playwright 正常连接、等待成功 marker、正常关闭且自身退出 0。任何 Windows 弹窗、assertion、Target crashed、child/browser 非零退出、超时、日志失败、摘要漂移或进程残留都立即结束整个 E3，不重试、不换参数。

## 禁止范围

本任务不得：

- 重跑 D 盘 baseline；
- 运行 Procmon、Process Explorer、ListDLLs、Sigcheck、WinDbg、GFlags、loader snaps 或管理员诊断；
- 使用 `--no-sandbox`、`--disable-gpu-sandbox`、`--in-process-gpu`、WARP 或随机 Chromium 开关；
- 试运行 Electron 43、45 alpha 或其他版本；
- 修改产品代码、Electron main/preload/renderer、Forge、fuses、依赖、lock、H1 staging、Python、migration 或测试；
- 运行 app.asar、Forge package、最终 resources scan、`Maris.exe`、Host、sidecar、数据库、Docker、OpenClaw、微信、DeepSeek 或 P4-C12；
- 修改或运行 `tests/independent/**`；
- 修改 interface freeze、control、overview、其他角色文件或 `.claude/**`；
- 执行任何 Git 写操作。

## 允许修改与交付

仓库内只允许修改：

- 新增 `docs/b7-r1-e3-c-drive-electron-running.md`
- 新增 `apps/desktop/b7-r1-e3-source.sha256`
- 更新 `docs/coordination/agents/executor.md`

E3 source manifest 复用 H1 的 198 个 source 路径并复算当前摘要；不得把 C 盘证据、任务工具、profile、cache、node_modules、日志、截图、`.claude/**` 或 manifest 自身纳入。

运行说明必须列出：起点门禁、工具/来源摘要、C 盘任务根 run-id、dist/fixture manifests、ACL/ADS 摘要、每个实际运行 cell 的唯一启动时间窗、完整参数类别、marker/日志/退出/事件/进程收口结果、未运行项、解释边界、C 盘原始证据目录摘要和保留状态。禁止粘贴未脱敏原始日志。

## 完成与停止规则

- A1 失败：状态 `blocked / finished`，A2 `not_run`。保留现场，停止并交回总控；不得自动进入 F1。
- A1 成功、A2 失败：状态 `blocked / finished`。结论只能写“支持 launcher/inspector/CDP/时序分支”，不得写成已定位根因。
- A1 与 A2 都成功：状态 `review / finished`。结论只能写“C 盘同内容 direct 与 Playwright 均稳定；结合既有 D 盘 Playwright 失败，支持执行位置类差异”，不得宣称 P4-B、app.asar 或最终 EXE 已通过。
- 任一 P0 条件或同一问题连续两个检查点无新证据：立即停止；本任务本来就不允许重复同一个 cell。

完成后停止，不创建 F1、P1、P2 或 P4-C12，不启动技术顾问或测试智能体，不清理 C 盘受限证据现场，不执行 Git 写操作，等待头脑风暴总控复算和决定下一任务。
