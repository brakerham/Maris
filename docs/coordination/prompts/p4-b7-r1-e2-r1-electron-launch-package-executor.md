# P4-B7-R1-E2-R1 执行智能体任务卡：Electron 启动分层与 package hygiene

你是执行智能体，唯一负责 `P4-B7-R1-E2-R1`。本任务延续已经停止的 E2，只处理 Playwright/app.asar/真实 EXE 启动分层和最终 package 资源清洁度；不得从头重做 P4-B7、R1、E1 或 E2 已通过的供应链、Host、sidecar 和业务实现。

用户把本文件全文发送给你，即表示授权你在本任务边界内恢复项目本地精确 Node/pnpm 依赖，运行本任务拥有的 Electron/Maris/Python sidecar 进程，修改授权桌面测试、package 配置/脚本和必要的窄范围桌面接线，并生成交付证据。不要再次要求用户确认这些已授权动作。

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
9. `docs/p4-d12-coordinator-review.md`
10. `docs/p4-b7-r1-e2-network-gate.md`
11. `docs/b7-r1-e2-windows-shell-running.md`
12. `docs/p4-b7-r1-e2-blocked-coordinator-review.md`
13. `apps/desktop/b7-r1-e2-source.sha256`
14. `docs/coordination/snapshots/p4-b7-r1-e2-r1-start.sha256`
15. 本任务卡

最新 control 与本任务冲突时，以 control 为准。依赖安装、外部下载或启动真实进程前必须再次读取最新 control。先在 `docs/coordination/agents/executor.md` 登记接单、当前步骤、开始时间、下一检查点和可观察进程/session。

## 已确认且不得重复的事实

- E2 状态为 `blocked / finished`；不是失败回滚点，不得重写或删除其报告。
- E2 source manifest 为 194 entries；总控复算为 194 matched、0 mismatch、0 missing；manifest SHA-256 为 `d4a6619ff0769a6d329739543013c4ab279cca515613fa6d5cef88ea32edf715`。
- 最终 lock SHA-256 为 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。
- 官方 Electron `44.4.5` Windows x64 ZIP 为 158,184,819 bytes，SHA-256 为 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d`。
- E2 的 OpenAPI drift、TypeScript、lint、22 项 Vitest、55 项 Python 回归、managed sidecar smoke 和 Forge package 已通过。除受本任务修改影响的范围外，不重复全量回归。
- 当前产品 fuses 中 `RunAsNode=false`、`EnableNodeOptionsEnvironmentVariable=false`、`EnableNodeCliInspectArguments=false` 是冻结的安全要求，不能为测试改成 true。
- E2 的 app.asar Playwright 启动失败；真实 EXE 未运行。最终 package 发现 11 个 `.pyc` 和 6 个 `.egg-info`。
- E2 最终确认 Electron、Maris、sidecar、窗口、Tray 和测试 profile 均无残留。

## 起点门禁

任何修改、安装或启动前：

1. 逐行复算 `docs/coordination/snapshots/p4-b7-r1-e2-r1-start.sha256`，必须全部匹配。
2. 独立复算 `apps/desktop/b7-r1-e2-source.sha256`，必须为 194 matched、0 mismatch、0 missing。
3. 核对 E2 report、最终 lock、Electron 官方摘要和 executor 最终状态。
4. 检查 Electron、Maris、本任务 Python sidecar、相关窗口和 Tray 均为 0 残留。
5. 重新读取最新 control，确认你仍是 R1 唯一负责人；测试智能体、技术顾问和 P4-C12 均停止。

任一 mismatch/missing 或未知活动进程占用时立即停止，不 restore、不 reset、不覆盖现场。

## 文件边界

允许修改：

- `apps/desktop/.gitignore`；
- `apps/desktop/forge.config.ts`；
- `apps/desktop/package.json`；
- `apps/desktop/scripts/**`；
- `apps/desktop/tests/e2e/**`；
- 为本任务补强的 `apps/desktop/tests/unit/**`；
- 只有在最小动态证据证明必要时，才允许对 `apps/desktop/electron/main/index.ts` 做不改变业务/安全合同的窄修复；
- `docs/b7-r1-e2-r1-windows-shell-running.md`；
- `apps/desktop/b7-r1-e2-r1-source.sha256`；
- `docs/coordination/agents/executor.md`。

可以只读核对其余 E2 source 文件和生产包。不得修改：

- 根依赖版本、`pnpm-lock.yaml`、`.node-version`、`.npmrc`、workspace 定义；
- Python 产品代码、migration、Host/Finance/Agent/activity import 业务语义；
- `tests/independent/**`、测试矩阵、独立报告；
- interface freeze、control、overview、其他角色状态；
- `.claude/**`；
- Git 状态或远程仓库。

如果正确修复必须越过边界、改变依赖版本、patch 第三方包或修改生产 fuse，立即停止并返回证据，不自行扩大任务。

## 阶段 1：最小启动兼容性探针（先证据，后改实现）

恢复精确 Node `24.21.0`、pnpm `12.7.0` 和 frozen install。安装前后 lock 必须保持已知 SHA-256。只使用官方 Electron 资产和已验证任务缓存；不得使用第三方 mirror、旧 binary、全局包或未验证缓存。

先读取本地安装的 Playwright `1.63.0` Electron launcher 源码和最终 package fuse 状态，并把以下事实写入报告：

- Playwright Electron launcher 实际注入的 main/renderer 调试参数；
- 传与不传 `executablePath` 时的启动路径差异；
- 项目 Electron 与最终 Maris.exe 的 fuse 值。

随后做一次最小、隔离、可清理的兼容性探针：

1. 用项目安装且摘要已验证的 Electron，调用 `_electron.launch()` 时不传 `executablePath`；
2. 先用任务拥有的最小 fixture 证明 Playwright 能得到 Electron application；
3. package 生成后，app.asar E2E 同样不传 `executablePath`，把 app.asar 作为 app 参数；
4. 使用隔离的绝对 userData、禁用硬件加速和脱敏 `DEBUG=pw:browser` 证据；不得把个人路径、token、nonce、端口或完整命令行写入报告。

不得用 `_electron.launch()` 启动最终 fused `Maris.exe`。真实 EXE 走阶段 4 的黑盒路线。

如果最小 fixture 或 app.asar 仍因 Electron 44/Playwright 1.63 的 inspector/remote-debugging 参数在启动前崩溃，只允许一个有新证据的相邻检查点。连续两个检查点无有效进展时立即停为 `blocked / finished`，保留精确脱敏 launch evidence；不得改 fuse、降版本、升级版本、patch Playwright、使用私有 fork或无限重试。

## 阶段 2：修正测试分层

把执行方 E2E 明确拆成：

### app.asar 受控集成模式

- Playwright `_electron.launch()` 使用项目默认 Electron，不显式传 `executablePath`；
- 覆盖窗口安全、唯一 composition、online/authenticated、`daily_finance` modules 和 recover；
- 使用隔离 profile，关闭后 Electron/sidecar/端口/profile 均清理；
- 不接触真实 AppData，不显示不受控弹窗。

### 最终 Maris.exe 黑盒模式

- 用普通子进程启动最终 `Maris.exe`，不得用 Playwright Electron launcher；
- 仅在本任务隔离 profile 和显式 E2E 环境下，使用 `--remote-debugging-address=127.0.0.1` 与动态非零 loopback port；
- 通过 Playwright Chromium `connectOverCDP()` 连接 renderer，只调用已经冻结的 `window.maris` preload API，核对 startup、online/authenticated、`daily_finance` modules 和 recover；
- 不增加产品 IPC、测试后门、常驻 debug 配置、renderer Node 能力或明文秘密；
- 用现有 `MARIS_E2E_EXIT_MS` 触发与 Tray 共用的 `requestQuit → app.quit → bounded shutdown` 代码路径，并证明 Maris、owned sidecar、端口、窗口和 profile 收口。实际点击 Tray 菜单保留给 P4-C12 的 Windows 人工门禁，不得把自动退出描述成已经点击 Tray。

`connectOverCDP()` 只用于最终 EXE 的 renderer 黑盒观察，不替代 app.asar 的 Electron application 测试。若 Electron 44 拒绝明确的非零 loopback debugging port，停止并返回证据，不改生产安全边界。

## 阶段 3：确定性 package resource allowlist

修复 `extraResource` 直接复制整个 `src`/`migrations` 的问题。首选实现是任务内确定性 staging：

1. package 前创建忽略的 staging 目录；
2. 只复制 `alembic.ini`、运行所需 migration `.py` 和 `src/wife_system/**/*.py`；
3. 明确排除 `__pycache__`、`*.pyc`、`*.pyo`、`*.pyd`、`*.egg-info`、测试、临时文件、构建元数据、任务工具/cache 和个人路径；
4. Forge `extraResource` 只指向 staging 中的三个已知入口，并保持最终 resources 中 `alembic.ini`、`migrations`、`src/wife_system` 的运行时相对布局；
5. package 完成或失败后都清理 owned staging。

必须增加执行方检查，证明即使源树在 Python smoke 后存在 `__pycache__`/`.pyc`/`.egg-info` 前置条件，最终 package 仍为零命中。不能只靠先删除副产物再打包，也不能把 Git ignore 当作 package filter。

最终 package 继续扫描：秘密/凭据样式、个人路径、更新 URL、任务 cache、旧脆弱依赖、Python bytecode 和 metadata。生产 fuses 必须保持冻结值。

## 阶段 4：有限回归、package 与真实门禁

按变更影响依次运行：

1. package staging/scan 的执行方单元测试；
2. OpenAPI generated drift、TypeScript、desktop lint 和完整 Vitest；
3. 只在桌面 main 有修改时复跑相应 Python/managed sidecar smoke；否则引用 E2 的 55 项和 sidecar 证据，不重复；
4. Forge package；
5. app.asar Playwright E2E；
6. 最终 `Maris.exe` renderer 黑盒 smoke；
7. 最终 process/port/window/Tray/profile 清理核对。

不得把历史通过计成本轮实际运行；报告必须清楚区分本轮运行、引用的 E2 证据和 `not_run`。不得 skip/xfail、删测试、放宽业务断言或用 app.asar 代替真实 EXE。

## P0 停止条件

出现以下任一项立即停为 `blocked / finished`：

- 起点快照或 E2 source mismatch/missing；
- frozen install 改写 lock，或 Electron 官方摘要/来源不匹配；
- 需要修改生产 fuse、依赖版本、lock 或第三方 Playwright/Electron 包；
- 同一 Electron launch 问题连续两个检查点没有新证据；
- app.asar 或真实 EXE 出现不受控 Windows 弹窗、访问真实 profile、读取真实秘密或残留进程；
- package staging 改变运行时资源布局，sidecar 无法启动；
- 必须修改 Python 产品、migration、独立测试或越过文件边界；
- 需要用户修改 TUN、代理、安全软件、系统设置或手动关闭任务残留进程。

停止时先终止本任务拥有的进程，清理 task profile/staging/out/trace，记录未验证项，再更新报告和角色日志。不得在相同失败上继续试。

## 交付物与完成规则

交付：

1. 授权范围内的代码、配置、脚本和执行方测试；
2. `docs/b7-r1-e2-r1-windows-shell-running.md`；
3. `apps/desktop/b7-r1-e2-r1-source.sha256`；
4. 更新 `docs/coordination/agents/executor.md`。

报告必须包含：起点复算、兼容性根因证据、两种启动模式、变更文件、lock/Electron 摘要、staging allowlist、package 扫描、app.asar、真实 EXE、测试统计、失败/警告、资源收口和逐文件 SHA-256。source manifest 排除自身、角色日志、运行说明、`node_modules`、工具/cache、staging、package/out、profile、trace、临时日志和 `.claude/**`。

只有 app.asar 与真实 EXE 门禁均通过、package hygiene 零命中、进程与临时资源收口后，才可提交 `review / finished`。完成后停止，不启动 P4-C12、测试智能体或技术顾问，不执行任何 Git 写操作，等待头脑风暴总控复算稳定快照。
