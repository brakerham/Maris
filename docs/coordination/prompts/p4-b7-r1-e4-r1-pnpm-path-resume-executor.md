# P4-B7-R1-E4-R1 执行智能体任务卡：固定 pnpm 子进程解析并恢复最终门禁

你是执行智能体，唯一负责 `P4-B7-R1-E4-R1`。本任务只恢复 E4 在 Forge package-manager check 处停止的执行链：先用任务专属 `pnpm.cmd` 和 Forge 自己的 `spawnPackageManager` 证明子进程一定解析到已验证的 pnpm `12.7.0`，然后重新授予一次 package 预算；package 通过后继续 E4 原定的最终 resources、P1 app.asar 和 P2 `Maris.exe` 门禁。

本任务不是产品返修。不得修改产品、测试、Forge 配置、package wrapper、staging、依赖、lock、系统 pnpm 或用户环境。预检不能确定性通过时，不得消耗 package 预算。

用户把本文件全文发送给你，即表示授权你：继续使用保留的 `C:\MarisE4\E4-20260928-1255`；在其中创建新的 R1 evidence 和 task-owned shim 子目录；调用已经验证的 Node/pnpm/Electron/Playwright；执行一次新的 Forge package；按条件分别启动一次 packaged app.asar 和一次最终 `Maris.exe`；结束本任务拥有的进程。不要再次要求用户确认这些已授权动作。

任何系统级 pnpm 修复、PATH 永久修改、管理员提权、系统设置、代理/TUN、安全软件、Windows mitigation、显卡驱动、运行库、注册表、真实账户、真实财务数据或全局 AppData 修改都不在授权内。

## 必读输入

开始前依次读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. 最新 `docs/coordination/control.md`
6. `docs/coordination/agents/executor.md`
7. `docs/phase-4-interface-freeze-003.md`
8. `docs/phase-4-interface-freeze-004.md`
9. `docs/phase-4-interface-freeze-005.md`
10. `docs/p4-b7-r1-h1-r1-coordinator-review.md`
11. `docs/p4-b7-r1-e3-coordinator-review.md`
12. `docs/p4-b7-r1-e4-blocked-coordinator-review.md`
13. `docs/b7-r1-e4-package-product-gates-running.md`
14. `apps/desktop/b7-r1-e4-source.sha256`
15. `docs/coordination/snapshots/p4-b7-r1-e4-r1-start.sha256`
16. 原 E4 任务卡
17. 本任务卡

最新 control 与本任务冲突时，以 control 为准。任何 C 盘写入、预检、package、P1 和 P2 前都重新读取 control。先在 `docs/coordination/agents/executor.md` 登记接单、阶段、开始时间、下一检查点、E4 run-id 和新的 R1 evidence 子目录；不得把用户名、完整路径、动态端口、token、nonce 或原始命令行写进角色日志。

## 已冻结事实

- E4 仓库起点为 215 项；执行后只有 executor 授权变化，并新增 E4 报告与 E4 source manifest。
- E4 source 为 198/198 matched，manifest SHA-256 `04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1`。
- E4 C 盘 evidence 为 26/26 matched，manifest SHA-256 `5958703ccea01cd0b8ef3bd72b681dfbdb7b5b398c7b8c7bc5ee7cd2fb1ba2d1`。
- E4 阶段 A 已全部通过：desktop 36 passed、H1/toolchain 16 passed、Python 55 passed、OpenAPI/type/lint/compile/pip check 通过。R1 不重复阶段 A。
- Node `24.21.0`、pnpm `12.7.0`、Electron `44.4.5`、Playwright `1.63.0`、275 package install、73 文件 Electron dist 和 workspace lock 均已固定。
- 九个虚拟污染 marker 仍应为 9/9；`out` 与 `.maris-staging` 应不存在；E4 owned process 应为 0。
- E4 唯一 package 在 Forge 调用裸 `pnpm config get hoist-pattern` 时命中失效用户级 shim，尚未进入 Packager/Vite/app.asar/fuse。
- 总控已用一个短期 `pnpm.cmd` 和 E4 安装的 Forge `spawnPackageManager` 实际取得：version `12.7.0`、hoist/public-hoist `undefined`、node-linker `hoisted`、退出 0。该预检没有运行 package。
- P1、P2 和 P4-C12 都没有开始。

## 仓库文件边界

仓库内只允许：

- 新增 `docs/b7-r1-e4-r1-pnpm-path-resume-running.md`；
- 新增 `apps/desktop/b7-r1-e4-r1-source.sha256`；
- 更新 `docs/coordination/agents/executor.md`。

不得修改：

- `apps/desktop/scripts/package-desktop.mjs`；
- `apps/desktop/scripts/stage-python-resources.mjs`；
- Forge 配置、package.json、依赖、lock、`.npmrc`；
- Electron main/preload/renderer、Python 产品、migration；
- 任何执行方或独立测试、矩阵、报告、interface freeze；
- control、overview、其他角色文件、`.claude/**`；
- Git 状态或远程仓库。

如果必须修改这些文件才能继续，立即停止为 `blocked / finished`，给出建议修改位置，不在 R1 中实现。

## 起点与保留现场门禁

任何写入或进程启动前：

1. 逐行复算 `docs/coordination/snapshots/p4-b7-r1-e4-r1-start.sha256`，必须 0 missing、0 mismatch。
2. 复算仓库 `apps/desktop/b7-r1-e4-source.sha256`，必须 198/198 matched。
3. 复算 E4 原始 `final-evidence.sha256`，必须 26/26 matched；不得覆盖、删除或重写 E4 evidence。
4. 复算 C 盘 source copy、workspace lock、Node/pnpm/Electron、node_modules 和 73 文件 Electron dist。
5. 确认九个污染 marker 仍为 9/9，内容和摘要与 E4 相同。
6. 确认 `out=false`、`.maris-staging=false`、transition artifacts 0、E4 owned process 0。
7. 在 E4 任务根下创建新的 `r1-pnpm-resume` 子目录，只保存 R1 shim、预检、package/P1/P2 和最终 evidence；不得覆盖 E4 文件。
8. 重读 control，确认你仍是 R1 唯一负责人，技术顾问、测试智能体和 P4-C12 停止。

任一门禁不满足，立即停止，不 restore、不 reset、不补文件、不启动 package。

## 阶段 R0：确定性 pnpm 子进程预检

### 1. 任务专属 shim

在 R1 子目录下创建 `forge-pnpm-bin/pnpm.cmd`。它只能调用 E4 已验证、SHA-256 已记录的 `tools/pnpm-12.7.0/pnpm-native.exe`，原样传递 `%*`，并原样返回 `%ERRORLEVEL%`。

要求：

- shim 内容、字节数和 SHA-256 进入 R1 evidence；
- shim 不进入仓库、source manifest、package 或最终 resources；
- 不执行 `pnpm setup`、global install、Corepack 全局 enable 或用户级 shim 修复；
- 不修改用户/系统 PATH；
- 只为 R1 driver、wrapper 和 Forge child 构造进程级环境，PATH 第一项必须是 `forge-pnpm-bin`，第二项必须是 E4 固定 Node 目录；其余原 PATH 保持相对顺序；
- 同一环境必须由后面的正式 package 直接继承，预检通过后不得重新构造另一套 PATH。

### 2. package 前硬门禁

使用后续 package 将继承的完全相同环境，依次执行并保存原始输出：

1. `where.exe pnpm`：第一项必须是任务专属 `pnpm.cmd`；
2. 裸 `pnpm --version`：必须精确为 `12.7.0`；
3. 裸 `pnpm config get hoist-pattern`：必须成功；
4. 裸 `pnpm config get public-hoist-pattern`：必须成功；
5. 裸 `pnpm config get node-linker`：必须为 `hoisted`；
6. 用 E4 固定 Node 导入实际安装的 `@electron-forge/core-utils/dist/package-manager.js`，调用其中的 `spawnPackageManager(PACKAGE_MANAGERS.pnpm, args, {cwd: desktopRoot})`，再次取得：
   - version `12.7.0`；
   - hoist-pattern `undefined`；
   - public-hoist-pattern `undefined`；
   - node-linker `hoisted`。

再确认：

- 预检没有创建 `out` 或 `.maris-staging`；
- lock/source/node_modules/Electron dist/污染 marker 摘要未变；
- 用户级失效 shim、用户环境变量和系统环境变量未修改。

以上任一项失败时，R1 立即停为 `blocked / finished`，package attempt 保持 `0/1`。不得为了让预检通过而修改系统 pnpm、wrapper、Forge、依赖或 PATH 永久值。

## 阶段 R1：唯一一次恢复 package

只有 R0 全部通过并重新读取 control 后执行。

直接用 E4 固定 Node 启动 C 盘源码副本中的正式 `apps/desktop/scripts/package-desktop.mjs`。不得通过用户级 pnpm 启动，不得绕过 wrapper 直接调 Forge。wrapper/Forge 必须继承 R0 已验证的同一个 PATH、Electron cache 和其他冻结环境。

本任务重新授予 package attempt `1/1`。不重复 clean install、阶段 A 或源码复制。package 前九个污染 marker 必须仍存在。

如果 Forge 再次解析到任务 shim以外的 pnpm、package 非零、staging 无法收口、lock 漂移或出现新失败，立即停止，不修改代码，不运行第二次 package，不进入 P1。

## 阶段 R2：package 后静态门禁

package 成功后，按原 E4 合同完整核对：

- `.maris-staging`、临时 sibling、backup 和 lock 全部收口；
- app.asar、Maris.exe 和 packaged resources 的字节数及 SHA-256；
- app.asar 中 main/preload/renderer 入口；
- production fuses 精确为冻结值；
- resources 中 `alembic.ini`、migrations、`src/wife_system`、desktop sidecar 和 production factory 完整；
- packaged Python 路径、字节、摘要精确等于 H1 manifest；
- 对九个污染 marker、`__pycache__`、`*.py[cod]`、`.egg-info`、tests、cache、build、dist、scratch 零命中；
- 对个人路径、用户名、凭据/token/private-key、更新 URL、旧脆弱依赖和任务 cache 零命中；
- package 前后 source、lock、node_modules 和 Electron dist 不变。

任一门禁失败立即停止，不进入 P1。

## 阶段 R3：P1 packaged app.asar 单次门禁

只有 R2 全部通过并重新读取 control 后执行。沿用原 E4 P1 合同：

- Playwright 默认 Electron loader，不传 `executablePath`；
- 最终 app.asar 作为 application 参数；
- `MARIS_HOST_PROJECT_ROOT` 指向 package resources；
- 使用已验证 Python、虚拟数据库、全新隔离 profile 和动态 loopback 端口；
- 验证窗口安全、online/authenticated、owner、`daily_finance`、一次 recover 和 bounded cleanup；
- sandbox/context isolation/Node isolation 保持冻结；
- 最终 Electron、owned sidecar、端口、窗口、Tray 与 profile 外写入为 0。

P1 最多一次，硬超时 90 秒。失败立即停止，不重跑、不进入 P2。

## 阶段 R4：P2 最终 Maris.exe 单次黑盒门禁

只有 P1 通过并重新读取 control 后执行：

- 普通子进程直接启动最终 `Maris.exe`，不得用 Playwright `_electron.launch()`；
- production fuses 保持冻结；
- 仅使用 `127.0.0.1` 动态非零 CDP 端口；
- Playwright Chromium `connectOverCDP()` 只调用既有 `window.maris` preload API；
- 核对 online/authenticated、`daily_finance`、一次 recover、隐私和摘要不变；
- 使用现有 `MARIS_E2E_EXIT_MS` 进入与 Tray 共用的 bounded shutdown；报告不得写成真实点击 Tray；
- 最终 Maris、Electron child、owned Python、端口、窗口和 Tray 为 0。

P2 最多一次，硬超时 120 秒。失败立即停止，不重跑。

## 证据、隐私和停止条件

- R1 原始证据只写入新的 R1 子目录，先算 SHA-256，再生成脱敏项目报告。
- 项目文档不得包含用户名、个人绝对路径、动态端口、token、nonce、HMAC key、绑定码、真实账户、个人财务数据、完整数据库或未脱敏命令行。
- 进程清理只按 PID、descendant、可执行路径、开始时间和 owner marker；禁止按名称广泛终止。
- 成功或失败都保留 E4 与 R1 evidence，等待总控复算；不自动删除 C 盘现场。

任一阶段出现以下情况立即停为 `blocked / finished`：

- 固定输入或 evidence mismatch/missing；
- R0 预检不能精确证明 Forge 使用 task-owned pnpm 12.7.0；
- package/P1/P2 的唯一预算失败；
- Windows 弹窗、crash/assertion、超时、真实 profile/secret 访问或 owned process 残留；
- 需要修改产品、测试、依赖、lock、wrapper、fuse、系统 pnpm 或永久 PATH；
- 需要用户修改代理、安全软件或系统设置；
- 同一 cell 需要第二次执行。

停止后不得自动创建后续任务、技术评审或 P4-C12。

## 交付与完成规则

交付：

1. `docs/b7-r1-e4-r1-pnpm-path-resume-running.md`；
2. `apps/desktop/b7-r1-e4-r1-source.sha256`；
3. 更新 `docs/coordination/agents/executor.md`；
4. 新 R1 evidence 子目录和自校验 manifest。

运行说明分别记录 R0、package、R2、P1、P2 的实际状态、唯一运行次数、摘要、warning、未运行项和进程/端口/窗口/Tray/staging 收口。不得把 E4 历史通过计作 R1 实际运行；阶段 A 应明确写成绑定的固定输入而非本轮重跑。

只有 R0、唯一 package、package 后静态门禁、单次 P1、单次 P2 和全部资源收口都通过时，才提交 `review / finished`。完成后停止，不启动 P4-C12、测试智能体、技术顾问、OpenClaw、微信、DeepSeek、Docker 或 PostgreSQL，不执行任何 Git 写操作，等待头脑风暴总控复算。
