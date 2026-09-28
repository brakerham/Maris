# P4-B7-R1-E4-DYN-R1：既有 package 的 app.asar 与最终 EXE 条件式动态门禁

## 唯一目标

你是既有执行智能体，唯一负责 `P4-B7-R1-E4-DYN-R1`。总控已经接受 PKG-R2 的唯一 package 和全部静态产物门禁。本任务不安装依赖、不运行测试、不构建、不重新 package、不修改产品，只对同一份冻结 package 依次执行：

1. P1 packaged app.asar 单次动态门禁；
2. 只有 P1 全部通过，才执行 P2 最终 `Maris.exe` 单次黑盒门禁。

两级都通过时提交 `review / finished`；任一级失败时收口资源并提交 `blocked / finished`。不得启动 P4-C12 或其他智能体。

## 开工前必读

按 `AGENTS.md` 顺序读取：

1. `README.md`
2. `docs/project-coordination.md`
3. `docs/coordination/README.md`
4. 最新 `docs/coordination/control.md`
5. `docs/coordination/agents/executor.md`
6. 本任务卡
7. `docs/p4-b7-r1-e4-pkg-r2-coordinator-review.md`
8. `docs/b7-r1-e4-pkg-r2-running.md`
9. `docs/p4-b7-r1-e3-coordinator-review.md`
10. `docs/phase-4-interface-freeze-003.md`
11. `docs/phase-4-interface-freeze-004.md`
12. `docs/phase-4-interface-freeze-005.md`
13. `docs/coordination/snapshots/p4-b7-r1-e4-dyn-r1-start.sha256`

最新 control 若不再把本任务分配给执行智能体，立即停止。逐项复算固定快照后，在自己的角色日志登记接单、当前 cell、开始时间、下一检查点和脱敏 session reference。

## 冻结输入

- E4 根：`C:\MarisE4\E4-20260928-1255`
- 冻结 workspace：`C:\MarisE4\E4-20260928-1255\workspace`
- 最终 package：上述 workspace 的 `apps\desktop\out\Maris-win32-x64`
- PKG-R2 evidence：`C:\MarisE4\E4-20260928-1255\package-resume-2`
- 新动态 evidence：`C:\MarisE4\E4-20260928-1255\dynamic-resume-1`
- `Maris.exe` SHA-256：`149ccd6e2d71a8945ffef4ecba81e5121bc19c4816331ed5bcb6e72948174199`
- `resources/app.asar` SHA-256：`c38cd0c7c5b42e4576d051f936d2942cd6a180b4386c62687a1886e991ae22f6`
- Electron dist manifest：`ffb4b389d5c454ca139cb6384f5ebb3d20633cf000960a8aa1b6c1794c9ebf8f`
- source manifest：198 entries，`04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1`

新 evidence 目录必须 create-new。若已存在，停止，不覆盖、不删除。PKG-R2 evidence、package、source、Electron dist、node_modules 和 lock 只读。不得重新 package 或修补产物。

## 仓库写入边界

仓库内只允许：

- 更新 `docs/coordination/agents/executor.md`；
- 新建 `docs/b7-r1-e4-dyn-r1-running.md`；
- 新建 `apps/desktop/b7-r1-e4-dyn-r1-source.sha256`。

禁止修改产品、测试、依赖、lock、Forge、staging、migration、独立测试、矩阵、control、overview、接口冻结或其他角色状态。禁止任何 Git 写操作。

## 共同前置与证据规则

启动任何 Electron/Maris/Python 进程前：

1. 复算新固定快照，必须 0 missing、0 mismatch；
2. 复算 PKG-R2 40/40 evidence、198/198 source、73/73 Electron dist；
3. 复算最终 EXE、app.asar、67 项 Python resources、production fuses；
4. 确认没有旧任务 owned process、窗口、Tray 或监听端口残留；
5. 重读最新 control；
6. 建立全新隔离 profile、虚拟数据库、动态 loopback 端口与随机虚拟 owner 数据。

原始命令、动态端口、profile、日志、截图和 Windows 事件只保存在受限 C 盘 evidence。仓库报告只写脱敏摘要，不得记录用户名、个人绝对路径、token、refresh token、nonce、HMAC key、PID/端口明文、真实账户、真实财务数据或完整数据库正文。

清理必须使用本轮记录的 PID、descendant、可执行路径、开始时间和 owner marker 联合判定，禁止按进程名广泛结束 Electron、Maris、Node 或 Python。用户无需扫码、登录、修改代理、修改安全软件或手动结束进程。

## P1：packaged app.asar 单次门禁

P1 只允许一次，硬超时 90 秒。使用 C 盘 frozen install 的 Playwright 默认 Electron loader，不传 `executablePath`，把最终 package 的 app.asar 作为 application 参数。保持 renderer sandbox、context isolation、Node integration 禁用和既有测试用硬件加速边界。

必须设置并核对：

- 全新的绝对隔离 profile；
- `MARIS_E2E=1`；
- `MARIS_HOST_PROJECT_ROOT` 指向最终 package 的 resources；
- `MARIS_PYTHON_EXECUTABLE` 指向已验证的项目 Python；
- 虚拟数据库和动态 loopback；
- 不读取真实 AppData、真实凭据或个人财务数据。

只通过现有 `window.maris` preload API 验证：

1. 只有预期主窗口和毛毛窗口；
2. renderer sandbox、context isolation、Node isolation 生效；
3. runtime 达到 `online` 且 `authenticated=true`；
4. 隔离 profile 建立本地 owner 会话，renderer 中无 token；
5. modules 至少包含真实 Host 返回的 `daily_finance`；
6. `runtime.recover()` 一次后回到 `online/authenticated`；
7. bounded shutdown 后 Electron、owned sidecar、端口、窗口和 Tray 均为 0；
8. 日志与 Windows 事件没有 `0xC0000135`、`0x80000003`、`child-process-gone`、`render-process-gone`、`Target crashed`、assertion 或秘密正文；
9. EXE、app.asar、resources 与 fuse 摘要前后不变。

任何弹窗、超时、非零 child/browser、断言失败、真实 profile 访问、日志失败、秘密泄露或资源残留，立即停止；不得重跑 P1，不得进入 P2。

## P2：最终 Maris.exe 单次黑盒门禁

只有 P1 完全通过并完成资源收口，才允许 P2。启动前重读 control，复算最终产物摘要。P2 只允许一次，硬超时 120 秒。

- 使用普通子进程直接启动最终 `Maris.exe`，不得使用 Playwright `_electron.launch()`；
- production fuses 保持不变；禁止 Node CLI inspect、NODE_OPTIONS、RunAsNode、renderer Node 和 `--no-sandbox`；
- 只允许 `--remote-debugging-address=127.0.0.1` 与动态非零 loopback port；
- Playwright 只通过 Chromium `connectOverCDP()` 附加 renderer，只调用冻结的 `window.maris` preload API；
- 使用新的隔离 profile、虚拟数据库、最终 package resources 和已验证 Python；
- 使用现有 `MARIS_E2E_EXIT_MS` 触发与 Tray 共用的 `requestQuit → app.quit → bounded shutdown`。这不代表真实点击 Tray；真实 Tray 菜单点击留给 P4-C12 人工门禁。

必须核对：

1. 主窗口与毛毛窗口正常出现，CDP 只绑定 loopback；
2. runtime 为 `online/authenticated`；
3. `daily_finance` 可见；
4. 一次 `runtime.recover()` 后仍为 `online/authenticated`；
5. owner/token/nonce/PID/端口/文件路径不进入 renderer DOM、console、仓库报告或持久日志；
6. bounded shutdown 后 Maris、Electron child、owned Python、端口、窗口和 Tray 均为 0；
7. 隔离 profile 外无本任务写入，Application/Code Integrity 时间窗无本任务异常；
8. production fuses、EXE、app.asar、resources 摘要前后不变。

若 loopback CDP 被 production Electron 拒绝，或必须改变 fuse、产品、测试、依赖、系统策略才能观察，立即停止并记录真实边界。不得改用固定端口、Playwright Electron launcher 或第二次 EXE 启动。

## 停止条件

任一项立即收口并提交 `blocked / finished`：

- 固定输入或产物摘要不匹配；
- P1 或 P2 出现弹窗、crash、超时、非零退出或安全边界漂移；
- 同一 cell 需要第二次运行；
- 需要修改产品、测试、依赖、lock、fuse、系统设置或真实用户数据；
- 不能按所有权安全清理本任务进程或端口；
- control 发生更新或职责冲突。

不要因为 evidence reader 的纯读取问题重启动态 cell。保留不可变原始动态证据；只允许对已完成运行的静态读取器做可追溯纠正，并且不得改变动态事实或产物。

## 交付

运行说明必须分别列出：

- 固定快照、PKG-R2 evidence 与 package 摘要复算；
- P1 的唯一启动次数、时间、退出、窗口、preload API、runtime、owner、modules、recover、事件与收口；
- P2 若获准执行，同样列出唯一启动与黑盒结果；否则准确写 `not_run`；
- 两级前后的 EXE/app.asar/resources/fuse 摘要；
- 进程、端口、窗口、Tray、profile、环境和 Windows 事件收口；
- warnings、未验证项、三份仓库交付摘要及外部 evidence manifest。

P1/P2 全部通过后提交 `review / finished`。这仍是执行方动态验证，不是 P4-B 独立验收，也不表示财务驾驶舱业务 UI 已实现。完成后停止，等待总控决定是否派发 P4-C12。
