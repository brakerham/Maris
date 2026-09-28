# P4-B7-R1-E4 执行智能体任务卡：C 盘 package、app.asar 与最终 EXE 恢复门禁

你是执行智能体，唯一负责 `P4-B7-R1-E4`。本任务不是新的产品实现任务，而是对已经完成的 B7-R1/H1 产品现场执行一次有限、顺序化、不可重试的最终构建与运行门禁。你只能在新的 C 盘短 ASCII 隔离目录中复制固定源码、安装固定依赖、构建一次、验证一次 app.asar、验证一次最终 `Maris.exe`，然后停止。

用户把本文件全文发送给你，即表示授权你在本任务边界内：创建 `C:\MarisE4\<run-id>` 任务目录；从官方来源或 E3 已验证且只读的官方归档恢复固定 Node/pnpm/Electron 依赖；运行 frozen install、静态检查、执行方测试、Forge package；启动并结束本任务拥有的 Electron、Maris 和 Python sidecar；仅在隔离 profile 中绑定动态 loopback 调试端口；按记录的 PID、descendant、可执行路径、开始时间和 owner marker 清理本任务进程。不要再次要求用户确认这些已授权动作。

任何管理员提权、系统设置、TUN/代理、安全软件、Windows mitigation、显卡驱动、运行库、注册表、全局 AppData、真实账户、真实财务数据或系统级诊断工具都不在本任务授权内。

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
10. `docs/p4-b7-r1-e2-blocked-coordinator-review.md`
11. `docs/p4-b7-r1-e2-r1-blocked-coordinator-review.md`
12. `docs/p4-b7-r1-h1-r1-coordinator-review.md`
13. `docs/p4-b7-r1-e3-coordinator-review.md`
14. `docs/b7-r1-h1-package-hygiene-running.md`
15. `docs/b7-r1-e3-c-drive-electron-running.md`
16. `apps/desktop/b7-r1-e3-source.sha256`
17. `docs/coordination/snapshots/p4-b7-r1-e4-start.sha256`
18. 本任务卡

最新 control 与本任务冲突时，以 control 为准。任何 C 盘写入、依赖安装、Forge package、app.asar 启动和最终 EXE 启动前都必须重新读取最新 control。先在 `docs/coordination/agents/executor.md` 登记接单、当前阶段、开始时间、下一检查点、C 盘任务根和可观察 session；角色日志只能写脱敏路径类别和 run-id，不得写动态端口、token、nonce、完整命令行或原始私人日志。

## 已确认且不得重复的事实

- H1-R1 已关闭 `P4-H1-ATOMIC-001`。Python runtime staging 使用精确 allowlist、同卷临时 sibling、明确 commit point、验证后替换和可恢复 post-commit backup 语义。
- E3 source manifest 为 198 entries，SHA-256 为 `04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1`，总控已复算 198/198 matched。
- E3 的 C 盘 direct A1 与默认 Playwright loader A2 均通过；不得重跑 A1/A2，也不得重跑 D 盘 baseline。
- Electron dist 的 E3 有序 manifest 为 `ffb4b389d5c454ca139cb6384f5ebb3d20633cf000960a8aa1b6c1794c9ebf8f`。
- Node `24.21.0` 官方 ZIP SHA-256 为 `158f7685b44de51f6c0df1d153526cbcd3e1bc739a8dfc607721cef75de9e541`。
- Electron `44.4.5` 官方 Windows x64 ZIP 为 158,184,819 bytes，SHA-256 为 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d`。
- workspace lock SHA-256 为 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`；Playwright 为 `1.63.0`，pnpm 为 `12.7.0`。
- 最终 production fuses 中 `RunAsNode=false`、`EnableNodeOptionsEnvironmentVariable=false`、`EnableNodeCliInspectArguments=false`、`EnableCookieEncryption=true`、`EnableEmbeddedAsarIntegrityValidation=true`、`OnlyLoadAppFromAsar=true` 是冻结要求。
- E2 的 Host/sidecar、22 项 Vitest、55 项 Python 定向与 managed sidecar smoke 是历史输入；不得把它们写成本轮运行。E4 只运行受最终 package 与启动链直接影响的有限检查。
- P4-C12 尚未开始；E4 只能提交执行方 `review / finished`，不能宣布 P4-B complete 或独立验收通过。

## 起点门禁

任何外部或动态操作前：

1. 逐行复算 `docs/coordination/snapshots/p4-b7-r1-e4-start.sha256`，必须全部匹配，0 missing、0 mismatch。
2. 复算 `apps/desktop/b7-r1-e3-source.sha256`，必须为 198/198 matched，0 missing、0 mismatch。
3. 核对 E3 报告、总控核对、lock、Node/Electron 归档摘要与 executor 的 `review / finished` 状态。
4. 只读确认 E3 原始现场仍存在；E3 现场只读保留，不得修改、补写、清理或从中复用 package/out、fixture 结果与产品二进制。只允许复制摘要匹配的官方 Node/Electron 归档或 frozen package cache。
5. 确认旧任务拥有的 Electron、Maris、项目 sidecar、窗口和 Tray 均无残留。不得按进程名广泛结束用户其他 Electron、浏览器、Node 或 Python。
6. 创建全新的 `C:\MarisE4\<run-id>`；若目标已存在或含未知内容，换新的 run-id，不覆盖、不递归删除未知目录。
7. 重读最新 control，确认你仍是 E4 唯一负责人，技术顾问、测试智能体和 P4-C12 均停止。

任一固定输入 mismatch/missing、职责冲突、未知进程占用或无法建立全新 C 盘任务根时，立即停为 `blocked / finished`。不 restore、不 reset、不覆盖现场、不安装依赖、不启动产品。

## 仓库文件边界

本任务是验证任务。仓库内只允许：

- 新增 `docs/b7-r1-e4-package-product-gates-running.md`；
- 新增 `apps/desktop/b7-r1-e4-source.sha256`；
- 更新 `docs/coordination/agents/executor.md`。

不得修改任何产品代码、Forge 配置、staging 脚本、测试、依赖、lock、migration、Python 业务代码、独立测试、矩阵、报告、interface freeze、control、overview、其他角色文件、`.claude/**` 或 Git 状态。

如果 package、app.asar 或最终 EXE 暴露产品/测试缺陷，只记录最小复现、预期、实际、严重级别、影响范围和建议返修文件，随后停止。不得在 E4 内边验证边修改，更不得自动创建 R1、P4-C12 或技术顾问任务。

## C 盘固定源码与工具

### 1. 源码副本

以 `apps/desktop/b7-r1-e3-source.sha256` 的 198 个相对路径为唯一复制清单，从仓库逐文件复制到 C 盘任务根中的同形 workspace。复制后按相同算法重新计算：路径集合、字节数与 SHA-256 必须和仓库清单完全一致。

不要把仓库 `.git`、`.claude`、`.pnpm-store`、node_modules、out、`.vite`、`.maris-staging`、测试结果、日志、profile 或任何未列入 198 路径的文件复制到源码副本。不得在 D 盘工作树执行 Electron、Forge package 或最终 EXE。

### 2. 固定工具

- 使用 Node `24.21.0`、pnpm `12.7.0`、Electron `44.4.5` 和 lock 解析的 Playwright `1.63.0`。
- 只使用官方来源，或从 E3 只读现场复制并重新核对摘要的官方归档/cache。
- 在 C 盘源码副本执行 clean frozen install。安装前后，仓库 lock 与 C 盘 lock 必须继续等于冻结摘要。
- 复算 C 盘 Electron dist 的有序逐文件 manifest，必须等于 E3 的 `ffb4b389...f8f`。
- 不使用第三方 mirror、全局 Electron、旧 package/out、未知 cache、私有 fork或手工 DLL。

网络瞬时失败只允许按工具自身有界重试，不得切换镜像、修改 TUN/代理或要求用户操作。如果无法获得摘要匹配的固定工具，停止为 `blocked / finished`。

## 阶段 A：有限静态与执行方门禁

在 C 盘源码副本中执行一次：

1. OpenAPI generated drift 检查；
2. TypeScript `tsc --noEmit`；
3. desktop lint；
4. desktop Vitest 完整集合；
5. H1 package resource 专属与相邻 toolchain 测试；
6. 与 desktop production factory/sidecar 直接相关的 Python 定向测试；
7. `pip check` 和受影响 Python 文件编译。

不要重复 P0～P4-A 全仓回归、真实 PostgreSQL、DeepSeek、OpenClaw 或微信。历史通过不得冒充本轮结果；本轮每组必须单独报告 passed/failed/skipped/warning。

任一业务断言失败、skip/xfail、新 dependency error 或 generated drift 立即停止，不运行 package。测试基础设施错误只能记录一次；如果不改变产品、测试或参数语义即可修复任务目录/临时父目录编排，可修正任务外部编排一次并保留原始结果。产品或测试文件一律不改。

## 阶段 B：污染前置与唯一一次 Forge package

只有阶段 A 全部通过后执行。

### 1. 污染前置

只在 C 盘源码副本中，创建可识别且完全虚拟的污染样本，至少覆盖：

- `src/wife_system/**/__pycache__/*.pyc`；
- `src/**/*.pyo`；
- 一个 `.egg-info` 目录及元数据文件；
- Python tests/cache/build/dist/scratch 类目录；
- allowlist 外未知扩展文件。

污染文件不得包含用户数据、凭据样式、真实路径正文或可执行恶意内容；不得写回仓库。先记录污染清单和摘要，证明 package 前它们确实存在。不得通过先删除污染再打包来获得零命中。

### 2. package

重新读取 control 后，只运行一次正式 desktop package wrapper。wrapper 必须按冻结顺序执行 `stagePythonResources → Forge package → finally cleanupPythonResources`。不得直接绕过 wrapper 调 Forge，不得重跑 package 来覆盖首次失败。

package 成功后必须证明：

- `.maris-staging`、临时 sibling、backup 和 lock 全部收口；
- 最终 package 只有预期的 app.asar、Electron runtime 和 extra resources；
- app.asar 能被完整列出，main/preload/renderer 入口齐全；
- production fuses 精确等于冻结值；
- `resources/alembic.ini`、`resources/migrations`、`resources/src/wife_system` 存在；
- packaged Python 路径集合、字节数和摘要精确等于 H1 staging manifest；
- migration、desktop sidecar 与 production factory 必需文件齐全；
- 最终 resources 对 `__pycache__`、`*.py[cod]`、`*.egg-info`、tests、pytest/tool caches、build、dist、scratch 和任务污染 marker 均为零命中；
- 最终 package 对个人绝对路径、用户名、凭据/token/private-key 样式、更新器 URL、旧脆弱依赖名和任务 cache 路径均为零命中。

记录 `Maris.exe`、`app.asar`、packaged resources manifest 与 fuses 的摘要。任何缺失、污染命中、fuse 漂移、staging 残留或 package 非零退出都立即停为 `blocked / finished`，不启动 app.asar。

## 阶段 C：P1 packaged app.asar 单次门禁

只有阶段 B 完全通过后执行。启动前重读 control，并再次确认没有 E4 owned process。

app.asar 必须：

- 在 C 盘任务根内运行；
- 使用 C 盘 frozen install 的 Playwright 默认 Electron loader，不传 `executablePath`；
- 把最终 package 的 app.asar 作为 application 参数；
- 保持 renderer sandbox、context isolation、Node integration 禁用和硬件加速禁用测试边界；
- 使用全新的绝对隔离 profile；
- 通过 `MARIS_HOST_PROJECT_ROOT` 指向最终 package 的 resources，而不是 D 盘仓库；
- 通过 `MARIS_PYTHON_EXECUTABLE` 指向已验证版本和依赖的项目 Python 解释器；报告只写解释器版本/摘要类别，不写个人绝对路径；
- 使用虚拟数据、随机本地数据库和动态 loopback 端口，不读取真实 AppData、真实凭据或个人财务数据。

P1 只允许一次启动，硬超时 90 秒。通过现有 `window.maris` preload API 核对：

1. 只出现预期主窗口与毛毛窗口，没有空白/额外业务窗口；
2. renderer sandbox、context isolation 和 Node isolation 生效；
3. desktop runtime 达到 online/authenticated；
4. owner 会话由隔离 profile 建立，不暴露 token；
5. modules 至少包含 `daily_finance`，且返回来自真实本地 Host；
6. `runtime.recover()` 可完成一次受控恢复并回到 online/authenticated；
7. 关闭后 Electron、owned sidecar、端口、窗口、Tray 和 profile 外写入均为 0 残留；
8. 日志与 Windows 事件没有 `0xC0000135`、`0x80000003`、child-process-gone、render-process-gone、Target crashed、assertion、秘密或私人路径正文。

任何 Windows 弹窗、超时、非零 child/browser、断言失败、真实 profile 访问、日志失败、进程/端口残留或安全边界漂移都立即停止；不得重跑 P1，不运行 P2。

## 阶段 D：P2 最终 Maris.exe 单次黑盒门禁

只有 P1 完全通过后执行。启动前重读 control，确认 P1 全部资源已收口。

### 启动模式

- 使用普通子进程直接启动最终 C 盘 package 中的 `Maris.exe`，不得使用 Playwright `_electron.launch()`。
- production fuses 保持冻结值，不开启 Node CLI inspect、NODE_OPTIONS、RunAsNode 或 renderer Node 能力。
- 只在本任务隔离 profile 和显式 E2E 环境中使用 `--remote-debugging-address=127.0.0.1` 与动态非零 loopback port；不得使用固定端口、外网地址或常驻调试配置。
- Playwright 只通过 Chromium `connectOverCDP()` 附加 renderer，且只调用已经冻结的 `window.maris` preload API；不得注入产品 main、访问 Node/Electron 内部对象或新增测试后门。
- 使用最终 package resources、已验证 Python、虚拟数据库和全新隔离 profile。
- 使用现有 `MARIS_E2E_EXIT_MS` 触发与 Tray 共用的 `requestQuit → app.quit → bounded shutdown` 路径。它不是“真实点击 Tray”；报告必须把真实 Tray 菜单点击保留给 P4-C12 人工门禁。

P2 只允许一次最终 EXE 启动，硬超时 120 秒。必须核对：

1. `Maris.exe` 正常进入主窗口与毛毛窗口，CDP 只绑定 loopback；
2. runtime 达到 online/authenticated；
3. `daily_finance` module 可见；
4. `runtime.recover()` 一次完成后仍回到 online/authenticated；
5. owner/token/nonce/PID/端口/文件路径不进入 renderer DOM、console、报告或持久日志；
6. 退出路径在预算内完成；最终 Maris、Electron child、owned Python、端口、窗口和 Tray 均为 0；
7. 最终 profile 外无写入，Application/Code Integrity 时间窗中无本任务异常；
8. production fuses、EXE/app.asar/resources 摘要在运行前后不变。

若动态非零 loopback CDP 被 Electron 拒绝，或需要改变 fuse、产品代码、依赖、测试、系统策略才能观察，立即停止并返回证据。不得改用 Playwright Electron launcher、固定远程端口、无 sandbox、明文 token 或第二次 EXE 启动。

## 进程、证据与隐私

- 每个阶段开始前记录 run-id、开始时间、owned PID/session、预期下一检查点和硬超时。
- 进程清理只按 PID、descendant、可执行路径、开始时间和 owner marker 共同确认；禁止按进程名广泛终止。
- 原始命令、动态端口、profile、日志、截图和 Windows 事件保存在 C 盘任务受限 evidence 目录；先计算 SHA-256，再写脱敏项目报告。
- 项目报告不得包含用户名、个人绝对路径、token、refresh token、nonce、HMAC key、绑定码、真实账户、个人财务数据、完整数据库正文或未脱敏命令行。
- 成功或失败后都保留 C 盘 evidence、package 与 manifests，等待总控复算；不要修改 E3 现场，不要自动清理 E4 受限现场。
- 仓库内 source manifest 排除自身、角色日志、运行说明、C 盘任务文件、node_modules、cache、staging、out、profile、trace、日志、二进制和 `.claude/**`。

## P0 停止条件

出现以下任一项，立即结束后续阶段，安全收口 owned process，并提交 `blocked / finished`：

- 起点或 198 文件 source mismatch/missing；
- 固定 Node/pnpm/Electron/lock/dist 摘要不匹配；
- frozen install 改写 lock，或需要第三方 mirror/未知 cache；
- 阶段 A 出现产品/测试失败、skip/xfail 或依赖破损；
- 唯一一次 package 失败、资源污染命中、fuse 漂移或 staging 无法收口；
- P1 或 P2 出现 Windows 弹窗、超时、非零退出、crash/assertion、真实 profile/secret 访问或 owned process 残留；
- 必须修改仓库产品、测试、依赖、lock、fuse、Python 业务、migration 或独立测试；
- 需要用户修改 TUN、代理、安全软件、系统设置或手动结束本任务进程；
- 同一问题需要第二次 package、第二次 P1 或第二次 P2 才能继续。

停止时不得把历史通过写成本轮通过，不得自动开始返修、技术评审或 P4-C12。报告应明确已经完成的最后一个阶段、未运行项和下一张最小任务建议。

## 交付与完成规则

交付：

1. `docs/b7-r1-e4-package-product-gates-running.md`；
2. `apps/desktop/b7-r1-e4-source.sha256`；
3. 更新 `docs/coordination/agents/executor.md`；
4. C 盘受限 evidence 目录及其自校验 manifest，保留到总控核对。

运行说明必须分别列出：起点、C 盘源码复算、工具来源与摘要、阶段 A 每组实际结果、污染前置、唯一 package、staging/最终 resources/fuses 扫描、P1、P2、Windows 事件、进程/端口/窗口/Tray/profile 收口、warning、未运行项、解释边界、交付文件摘要和 C 盘 evidence manifest 摘要。

只有以下全部满足时，任务才可提交 `review / finished`：

- 阶段 A 全部通过；
- 唯一 package 通过且最终资源零污染、fuses 正确；
- P1 app.asar 单次通过；
- P2 最终 `Maris.exe` 单次通过；
- 所有 owned process、端口、窗口、Tray 和 staging 收口；
- 仓库只有三个授权交付文件变化，产品/测试/lock 零变化。

完成后停止。不要启动 P4-C12、测试智能体、技术顾问、OpenClaw、微信、DeepSeek、Docker 或真实 PostgreSQL，不执行任何 Git 写操作，等待头脑风暴总控复算和决定是否进入独立验收。
