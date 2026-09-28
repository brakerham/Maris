# P4-B7-R1-E4-DYN-R2：修正 browser root 提升后恢复最终动态门禁

## 唯一目标

你是既有执行智能体，唯一负责 `P4-B7-R1-E4-DYN-R2`。DYN-R1 已证明唯一 package 能启动到创建隔离 owner session 和虚拟数据库，但任务外 runner 错把 Playwright 返回的短生命周期 PID 当成必须持续存活的 Electron browser root，导致窗口和 preload API 验证尚未开始就停止。

本任务只修正新 evidence runner 的进程所有权识别，给予新的 P1 1/1 动态预算。P1 全部通过后，才执行 P2 最终 `Maris.exe` 1/1 黑盒门禁。不得修改产品、测试、依赖、lock、package 或系统设置。

## 开工前必读

按 `AGENTS.md` 顺序读取：

1. `README.md`
2. `docs/project-coordination.md`
3. `docs/coordination/README.md`
4. 最新 `docs/coordination/control.md`
5. `docs/coordination/agents/executor.md`
6. 本任务卡
7. `docs/p4-b7-r1-e4-dyn-r1-blocked-coordinator-review.md`
8. `docs/b7-r1-e4-dyn-r1-running.md`
9. `docs/p4-b7-r1-e4-pkg-r2-coordinator-review.md`
10. `docs/coordination/prompts/p4-b7-r1-e4-dyn-r1-executor.md`
11. `docs/coordination/snapshots/p4-b7-r1-e4-dyn-r2-start.sha256`

逐项复算固定快照。最新 control 若不再分配本任务，立即停止。接单后更新自己的状态、当前 cell、开始时间、下一检查点和脱敏 session reference。

开始时使用只读 Git 检查确认 index 中没有 staged paths。工作区既有 `.pnpm-store/` 和 `.claude/` 不属于任务文件，不得暂存、删除、清理或纳入摘要。任务结束时再次证明 index 无 staged paths；不得用 `git add -N`、`git add` 或其他 index 写入来生成差异证据。

## 固定现场

- E4/package/source/tool 继续使用 DYN-R1 登记的同一冻结位置与摘要。
- DYN-R1 evidence 只读：`C:\MarisE4\E4-20260928-1255\dynamic-resume-1`。
- 新 evidence 必须 create-new：`C:\MarisE4\E4-20260928-1255\dynamic-resume-2`。
- 新 P1 必须使用新的隔离 profile、虚拟数据库、动态 loopback、owner marker 和日志。
- 不复制或复用旧 profile、owner session、数据库、PID、端口或运行结果。

若新 evidence 目录已经存在，或固定 EXE/app.asar/source/dist/resources/out/fuses 与 DYN-R1 终点摘要不一致，立即停止，不覆盖、不删除、不修补产物。

## 仓库写入边界

只允许：

- 更新 `docs/coordination/agents/executor.md`；
- 新建 `docs/b7-r1-e4-dyn-r2-running.md`；
- 新建 `apps/desktop/b7-r1-e4-dyn-r2-source.sha256`。

禁止修改产品、执行方测试、独立测试、依赖、lock、Forge、staging、migration、interface freeze、control、overview、其他角色状态或 Git 状态。

## 启动前 runner 修正

runner 只存在于新的受限 evidence 目录，不进入产品或仓库。启动产品前必须通过静态语法检查，并在运行说明中给出以下规则的代码位置映射：

1. `ElectronApplication.process()` 返回值只记作 `launchPid`；
2. 若 `launchPid` 查询时仍存活且 executable path 精确匹配冻结 Electron executable，直接作为 `browserRootPid`；
3. 若 `launchPid` 已退出，从启动后已经记录的父子快照中查找它的直接后代；候选必须同时满足：
   - executable path 精确匹配；
   - creation time 位于本轮启动窗口；
   - ancestry 回到 `launchPid`；
   - 本轮 owner marker receipt 匹配；
4. 候选必须恰好一个，才可提升为 `browserRootPid`；零个或多个立即停止且不得调用产品 API；
5. `browserRootPid` 的后代闭包构成 owned set，允许 Chromium GPU/utility/renderer 和 `conhost.exe` 等正常后代；
6. 不设精确进程数量预算，不要求 `launchPid` 在 P1 结束时仍存活；
7. cleanup 从 `browserRootPid` 开始，并在执行前再次核对 path、creation time、ancestry 和 marker；
8. runner 的初始 known-owned 集合必须在生成“残留为零”结论前建立，禁止再次出现空集合假绿。

不得为这个 runner 增加 synthetic self-test、Job Object、controller/worker、固定 PID、进程名广杀、第二次发现尝试或新的动态预检 cell。静态语法检查不消耗 P1 预算。

## P1：新的唯一 app.asar 动态预算

P1 为 1/1，硬超时 90 秒。除了上述 root promotion，完整沿用 DYN-R1 的 launcher、安全、隔离、虚拟数据和验证合同：

- Playwright 默认 Electron loader，不传 `executablePath`；
- 最终 app.asar 为 application 参数；
- renderer sandbox、context isolation、Node integration 禁用；
- `MARIS_E2E=1`、新的绝对隔离 profile、最终 resources、已验证 Python、虚拟数据库和动态 loopback；
- 只调用冻结的 `window.maris` preload API。

必须验证主窗口与毛毛窗口、sandbox/Node isolation、runtime `online/authenticated`、owner token 隔离、`daily_finance` 模块、一次 `runtime.recover()` 及恢复后的状态、日志/Windows 事件、摘要不变和 bounded shutdown。

任一产品 gate、所有权唯一性、日志、退出或清理失败，立即提交 `blocked / finished`。不得修改后重跑 P1；不得进入 P2。

若再次发生 root identity/ownership 识别阻塞，明确写入 `automation_route_exhausted=true`。不得建议或创建 DYN-R3；总控将重新裁定验收方式。

## P2：条件式最终 EXE 单次黑盒门禁

只有 P1 所有 gate 通过且资源完全收口，才允许 P2。启动前重读 control。P2 为 1/1，硬超时 120 秒。

- 普通子进程直接启动最终 `Maris.exe`，不得使用 Playwright `_electron.launch()`；
- production fuses 保持冻结；禁止 Node CLI inspect、NODE_OPTIONS、RunAsNode、renderer Node、固定调试端口或 `--no-sandbox`；
- CDP 只绑定 `127.0.0.1` 动态端口；Playwright 只用 `connectOverCDP()` 附加 renderer，并只调用 `window.maris`；
- 使用另一份新的隔离 profile、虚拟数据库和 owner marker；
- 使用 `MARIS_E2E_EXIT_MS` 触发共享 bounded shutdown，不把它写成真实 Tray 点击。

验证主窗口与毛毛、runtime、`daily_finance`、一次 recover、renderer 隐私、Windows 事件、profile 外零写入、产物摘要不变，以及最终 Maris/Electron/Python/端口/窗口/Tray 全部收口。

P2 失败不得重跑或改产品。P2 通过也只能提交执行方 `review / finished`，不能宣布 P4-B complete；独立结论留给 P4-C12。

## 交付与停止

交付文件：

1. `docs/b7-r1-e4-dyn-r2-running.md`；
2. `apps/desktop/b7-r1-e4-dyn-r2-source.sha256`；
3. 更新 `docs/coordination/agents/executor.md`；
4. C 盘 `dynamic-resume-2` 原始 evidence 与自校验 manifest。

报告必须分开写 runner root promotion、P1、P2、进程/端口/窗口/Tray 收口、日志/事件、未运行项和仓库边界。不得包含个人绝对路径、token、nonce、动态端口、PID、真实账户或个人财务数据正文。

完成后停止。不要启动 P4-C12、测试智能体、技术顾问、Docker、OpenClaw、微信或 DeepSeek，不执行 Git 写操作。
