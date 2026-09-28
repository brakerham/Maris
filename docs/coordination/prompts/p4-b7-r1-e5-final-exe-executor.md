# P4-B7-R1-E5-FINAL：最终 Maris.exe 单次黑盒动态门禁

## 唯一目标

你是既有执行智能体，唯一负责 `P4-B7-R1-E5-FINAL`。DYN-R1/DYN-R2 已将 Playwright `_electron.launch()` 进程所有权路线标记为 `automation_route_exhausted=true`；不得创建 DYN-R3，也不得再运行 packaged app.asar。

本任务不修改产品，不安装依赖，不运行测试、build 或 package。只对 PKG-R2 已冻结的最终 `Maris.exe` 做一次直接启动黑盒验证。通过后提交 `review / finished`；失败后收口并提交 `blocked / finished`。不得启动 P4-C12 或其他智能体。

## 开工前必读

按 `AGENTS.md` 顺序读取：

1. `README.md`
2. `docs/project-coordination.md`
3. `docs/coordination/README.md`
4. 最新 `docs/coordination/control.md`
5. `docs/coordination/agents/executor.md`
6. 本任务卡
7. `docs/p4-b7-r1-e4-dyn-r2-blocked-coordinator-review.md`
8. `docs/b7-r1-e4-dyn-r2-running.md`
9. `docs/p4-b7-r1-e4-pkg-r2-coordinator-review.md`
10. `docs/b7-r1-e4-pkg-r2-running.md`
11. `docs/phase-4-interface-freeze-003.md`
12. `docs/phase-4-interface-freeze-004.md`
13. `docs/phase-4-interface-freeze-005.md`
14. `docs/coordination/snapshots/p4-b7-r1-e5-final-start.sha256`

逐项复算固定快照。最新 control 若不再分配本任务，立即停止。开始时确认 Git index staged paths 为 0；既有 `.pnpm-store/`、`.claude/` 和所有旧 C 盘 evidence 不删除、不暂存、不写入。

## 固定输入

- E4 根：`C:\MarisE4\E4-20260928-1255`
- 最终 package：冻结 workspace 的 `apps\desktop\out\Maris-win32-x64`
- 最终 `Maris.exe` SHA-256：`149ccd6e2d71a8945ffef4ecba81e5121bc19c4816331ed5bcb6e72948174199`
- 最终 `resources/app.asar` SHA-256：`c38cd0c7c5b42e4576d051f936d2942cd6a180b4386c62687a1886e991ae22f6`
- PKG-R2 evidence：只读
- DYN-R1、DYN-R2 evidence：只读，只用于确认旧路线已停止和现场无残留
- 新 evidence：create-new `C:\MarisE4\E4-20260928-1255\final-exe-resume-1`

若新 evidence 已存在，或 source/dist/resources/out/EXE/app.asar/fuses 任一漂移，立即停止；不得覆盖、删除、修补或重新 package。

## 仓库写入边界

只允许：

- 更新 `docs/coordination/agents/executor.md`；
- 新建 `docs/b7-r1-e5-final-exe-running.md`；
- 新建 `apps/desktop/b7-r1-e5-final-exe-source.sha256`。

禁止修改产品、测试、独立测试、依赖、lock、Forge、staging、migration、接口冻结、control、overview、其他角色或 Git 状态。

## 单一动态 cell

最终 EXE 预算严格为 1/1，硬超时 120 秒。不得增加 app.asar 预跑、fixture、synthetic self-test、预启动 Electron、第二次产品启动或失败后重试。

runner 只能写在新 evidence 目录。启动前做静态语法检查并记录代码位置映射；静态检查不消耗动态预算。

### 1. 直接启动和进程所有权

- 使用固定 Node 的 `child_process.spawn()` 直接启动最终 `Maris.exe`；不得经 `cmd.exe`、PowerShell、shell、Playwright Electron loader 或 Forge 包装。
- `shell:false`，显式参数数组，重定向 stdout/stderr；删除继承环境中的 `NODE_OPTIONS` 和 `ELECTRON_RUN_AS_NODE`。
- `spawn()` 返回 PID 就是唯一产品根。启动后必须只读核对该 PID 仍存在、executable path 精确等于冻结 `Maris.exe`、creation time 位于本轮窗口；任一不满足立即停止，不做 PID 提升或第二次发现。
- owned set 为该根及其递归后代；允许 Electron renderer/GPU/utility、managed Python sidecar 和正常 Windows 宿主后代，不使用精确进程数量预算。

### 2. 隔离环境

必须使用：

- `MARIS_E2E=1`；
- 新的绝对 `MARIS_E2E_USER_DATA`；
- `MARIS_HOST_PROJECT_ROOT` 指向最终 package resources；
- `MARIS_PYTHON_EXECUTABLE` 指向已验证的项目 Python；
- `MARIS_E2E_EXIT_MS=30000`；
- 虚拟数据库、随机虚拟 owner 数据、全新 owner marker；
- 参数 `--remote-debugging-address=127.0.0.1` 和 `--remote-debugging-port=0`。

不得读取真实 AppData、真实凭据、真实账户或个人财务数据。不得传 `--no-sandbox`、固定调试端口、Node inspect 或改变 production fuse。

### 3. CDP 附加

- 等待新 profile 中由本轮进程创建的 `DevToolsActivePort`；核对文件 creation/write time 位于本轮窗口。
- 端口必须是动态非零值，实际监听地址只能是 `127.0.0.1`；若观察到 `0.0.0.0`、`::` 或非 loopback，立即停止并收口。
- 使用同一 frozen install 的 Playwright Chromium `connectOverCDP()` 附加；它只观察 renderer，不启动或拥有 Electron。
- CDP 端点、动态端口、PID 和 websocket path 只保存到受限 evidence，不进入仓库文档。

### 4. 产品门禁

必须在自动退出前完成并保存结构化结果：

1. 恰好一个主窗口页面和一个毛毛页面；主页面暴露冻结 `window.maris`，毛毛页面暴露冻结 `window.companion`；
2. renderer 中 `process`、`require`、Node 全局和未允许桥接均不可用；bridge 键集合与冻结 preload 合同一致；
3. runtime 达到 `online`、`authenticated=true`、`errorCode=null`；
4. modules 至少包含 `daily_finance` 且 enabled；
5. 只调用一次 `window.maris.runtime.recover()`，恢复后仍为 `online/authenticated`，再次读取 modules 仍包含 `daily_finance`；
6. owner token、refresh token、nonce、bootstrap token、PID、端口和内部路径不出现在 DOM、local/session storage、console、page error、持久日志或仓库报告；
7. 毛毛 `getState()` 返回冻结状态和 appearance，`openMain()` 可调用且不产生额外窗口；
8. Electron console/page/crash event、Windows Application/Code Integrity 时间窗中没有冻结 crash/assertion；
9. EXE、app.asar、source、dist、resources、out 和 fuses 前后不变。

### 5. 正常退出和收口

`MARIS_E2E_EXIT_MS` 必须触发产品现有 `requestQuit → app.quit → bounded shutdown`。这不是 Tray 人工点击；真实 Tray 菜单留给 P4-C12。

等待根进程自然退出并取得退出码 0；随后验证：

- 根及全部记录后代为 0；
- managed Python sidecar 为 0；
- CDP 和 Host 监听端口关闭；
- 主窗口、毛毛窗口和产品 Tray 所属进程为 0；
- 隔离 profile 外没有本任务写入。

若硬超时或存在残留，只能在再次核对根 PID、精确 EXE 路径、启动时间和后代关系后，对该根执行一次定向树清理；必须报告 forced cleanup，任务结论为 blocked。禁止按进程名广泛结束 Electron、Maris、Node 或 Python。

## 停止条件

下列任一情况立即停止并收口，不得重跑：

- 固定输入、快照或产物摘要漂移；
- 直接启动 PID 不是精确 `Maris.exe`；
- CDP 不能在 loopback 动态端口观察，或必须改变产品/fuse/安全配置；
- 窗口、bridge、安全、runtime、module、recover、隐私、日志、退出或资源门禁失败；
- 出现不受控 Windows 弹窗、crash、超时、非零退出或无法安全清理；
- 需要第二次启动、修改 runner 后重试、运行 app.asar 或恢复 `_electron.launch()`。

纯静态 evidence reader 错误不得触发第二次产品运行；保留原始事实，只允许可追溯地修正运行后的只读汇总器。

## 交付

交付运行说明、198 项 source manifest、执行日志和外部 evidence manifest。报告分别列出直接启动、CDP、窗口/bridge、安全、runtime/modules/recover、隐私、退出、资源收口、事件、固定摘要、warning 和未验证项。

成功时提交 `review / finished`，等待总控生成 P4-C12；不能宣布 P4-B complete。失败时提交 `blocked / finished`，不得自行创建 E5-R1、DYN-R3、产品返修或独立验收。完成后停止，不启动技术顾问、测试智能体、Docker、OpenClaw、微信或 DeepSeek。
