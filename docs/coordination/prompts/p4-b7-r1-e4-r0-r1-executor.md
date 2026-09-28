# P4-B7-R1-E4-R0-R1 执行智能体任务：R0 driver 单独恢复与六项预检

## 角色、唯一目标和最终状态

你是本项目既有的执行智能体。本任务唯一目标是：在不打包、不启动产品的前提下，按照 P4-D14 冻结方案动态验证新的 PowerShell R0 driver，并顺序执行 Q1～Q6 六项预检。

成功时只允许交付 `R0_READY_PACKAGE_0_OF_1`，状态为 `review / finished`；任何门禁失败时交付 `blocked / finished`。两种情况都必须停止，不得自动进入 package、P1、P2、P4-C12 或创建后续任务。

## 开工前必读

按 `AGENTS.md` 顺序重新读取：

1. `README.md`
2. `docs/project-coordination.md`
3. `docs/coordination/README.md`
4. 最新 `docs/coordination/control.md`
5. `docs/coordination/agents/executor.md`
6. 本任务卡
7. `docs/phase-4-d14-r0-driver-recovery-advice.md`
8. `docs/p4-d14-coordinator-review.md`
9. `docs/p4-b7-r1-e4-r1-blocked-coordinator-review.md`
10. `docs/b7-r1-e4-r1-pnpm-path-resume-running.md`
11. `docs/coordination/snapshots/p4-b7-r1-e4-r0-r1-start.sha256`

最新 control 若表明任务已完成、停止或转交，立即停止并报告旧任务假设已经过期。接单后先更新你自己的角色状态与 Current execution snapshot；不要修改 overview、control 或其他角色文件。

## 固定事实与规范勘误

- E4-R1 的 `$Args` 冲突属于 evidence driver 缺陷，没有形成产品、Forge、pnpm 恢复方案或 package wrapper 缺陷证据。
- E4-R1 的 package 预算为 0/1；本任务不继承或消费 package 预算。
- 三个 pnpm config 查询都是 **argumentCount=3 / commandTokenCount=4**：
  - `config`, `get`, `hoist-pattern`
  - `config`, `get`, `public-hoist-pattern`
  - `config`, `get`, `node-linker`
- 禁止为了满足旧卡中的“四参数”文字添加空参数或改变查询。
- 本任务绑定 PowerShell 7.6.5 Core。执行 `pwsh.exe` 的 SHA-256 必须为：
  `362a356ce7f0940ec74f73a8fc2c990a2cc24a38a11c90bbd8eca947110ad139`
- 仓库内不要记录包含用户名的 PowerShell 绝对路径；路径只保存到访问受限的外部 evidence。

## 允许写入范围

仓库内仅允许：

- 更新 `docs/coordination/agents/executor.md`
- 新建 `docs/b7-r1-e4-r0-r1-running.md`
- 新建 `apps/desktop/b7-r1-e4-r0-r1-source.sha256`

外部仅允许在旧 E4 任务根下创建一个全新的 sibling evidence 目录，例如：

`C:\MarisE4\E4-20260928-1255\r0-driver-recovery-r1`

不得覆盖、改写或删除 E4、E4-R1 的旧 driver、probe、result、summary、manifest 或日志。新目录必须在运行前不存在；若已存在，停止并报告，不要自行删改旧证据。

允许在新目录中创建：controller、worker、受限 pnpm adapter、Forge probe、synthetic helper、stdout/stderr、result JSON、PID/Job、摘要与最终 summary。路径名、日志和仓库交付不得保存密钥、token、财务数据或无必要的个人路径。

## 禁止事项

- 不运行任何 package 命令，不运行 Forge package。
- 不启动 app.asar、`Maris.exe`、Electron、Playwright Electron、Python sidecar、Uvicorn、Docker、PostgreSQL、OpenClaw、微信或 DeepSeek。
- 不安装、更新或删除依赖；不执行 pnpm install、audit 或 fetch。
- 不修改产品代码、测试、Forge 配置、package wrapper、staging、依赖声明、lock、`.npmrc`、系统 pnpm、用户/系统 PATH、注册表、代理、安全软件或 ACL。
- 不修改或运行 `tests/independent/**`。
- 不执行任何 Git 写操作。
- 不使用 `Invoke-Expression`、字符串拼接 shell 命令、无限 `WaitForExit`、按进程名清理或宽泛结束系统 Node/pnpm 进程。
- 不恢复旧 E4-R1 controller 的 GO/package 分支。

## 固定输入门禁

开工先复算 `docs/coordination/snapshots/p4-b7-r1-e4-r0-r1-start.sha256`。清单应有 226 个唯一、有序路径；必须逐行得到 matched、mismatch、missing。任何非授权 mismatch 或 missing 立即停止。不要只验证 manifest 文件自身摘要来代替逐文件复算。

同时只读核对旧 E4 现场的冻结事实，至少包括：

- E4 source 198/198；
- Electron dist 73/73；
- 污染 marker 9/9；
- workspace lock SHA-256 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`；
- `out=false`、`.maris-staging=false`、transition artifacts=0；
- 没有 E4 自有 Electron、Maris、Node 或 Python 进程。

本任务不以普通进程名全局结束机器上的 Node/Python；只观察并管理本任务创建、记录并纳入 Job 的进程。

## 唯一 driver 实现

严格以 P4-D14 的可复制方案为实现基线：

- 原生 exe 使用 `System.Diagnostics.ProcessStartInfo`。
- `UseShellExecute=false`。
- `ArgumentList.Add()` 逐项加入一维 string 参数，不通过单字符串拼接参数。
- stdout/stderr 分别异步捕获并原样落盘。
- 真实 native exit、supervisor exit、timeout、forced cleanup、drain 与 PID 分开记录。
- 裸 `pnpm` 只通过受限 cmd adapter；adapter 只接受 `--version` 与三个冻结 config 查询，其他输入拒绝。
- worker 在放行目标前先加入无 breakaway 的任务专属 Windows Job Object；关联失败时目标不得执行。
- 超时后关闭整个 Job，等待最多 5 秒完成后代收口；双流 drain 最多 5 秒。
- 不把 controller 发送的参数计数冒充第三方 argv 自证。

所有 controller、worker、adapter、probe 和 synthetic helper 源码在首次执行前落盘并计算 SHA-256；之后不得静默覆盖。每次 dispatch 前记录安全 executable label、argumentCount 和语义标签，不在仓库文档泄漏个人绝对路径。

## synthetic self-test 与唯一一次前置修正

在 Q1 前运行支持组件 synthetic self-test，必须覆盖：

1. 含空格和 Unicode 的参数逐项保持；
2. stdout/stderr 并发大量输出可完整捕获且无死锁；
3. 非零 native exit 被准确保留；
4. 超时后父子/后代进程均被 Job 收口，没有残留。

如果 synthetic self-test 在 **Q1 尚未启动、没有运行任何冻结原生目标、没有修改固定环境** 时暴露 driver 自身缺陷，允许一次前置修正：

- 完整保留 attempt-0 的源码、摘要、原始输出与失败分类；
- 只修改 controller/worker/adapter/probe/synthetic helper，不得修改产品、环境或预期值；
- 在 fresh `attempt-1` 目录重新落盘源码与摘要并重跑 synthetic self-test；
- 这是唯一一次修正预算。attempt-1 仍失败则 `blocked / finished`。

Q1 一旦被 dispatch，该例外立即失效。Q1～Q6 任一项都不得重跑。

## Q1～Q6 固定执行合同

只有 synthetic self-test 通过后才能按顺序执行：

| 顺序 | 目标 | 冻结参数 | 参数/命令词 | 时限 | 必须满足 |
| --- | --- | --- | --- | --- | --- |
| Q1 | `where.exe` | `pnpm` | 1 / 2 | 10 s | exit 0；首个完整输出行精确为任务专属 shim 绝对路径；其他旧 shim 只可出现在后续行 |
| Q2 | 受限裸 pnpm | `--version` | 1 / 2 | 15 s | exit 0；唯一一行精确 `12.7.0` |
| Q3 | 受限裸 pnpm | `config`, `get`, `hoist-pattern` | 3 / 4 | 15 s | exit 0；唯一一行精确 `undefined` |
| Q4 | 受限裸 pnpm | `config`, `get`, `public-hoist-pattern` | 3 / 4 | 15 s | exit 0；唯一一行精确 `undefined` |
| Q5 | 受限裸 pnpm | `config`, `get`, `node-linker` | 3 / 4 | 15 s | exit 0；唯一一行精确 `hoisted` |
| Q6 | 固定 Node + Forge probe | `<probe.mjs>`, `<package-manager.js>`, `<desktop-root>` | 3 / 4 | 60 s | exit 0；严格 UTF-8 Forge JSON；内部四次调用与 Q2～Q5 参数和值一致 |

每个 Q 只 dispatch 一次并立即校验。stderr 必须为空；帮助输出即使 exit 0 也必须失败。Q1 第一行按 ASCII bytes 与可选单个 CRLF/LF 核对；Q6 使用严格 UTF-8 decoder，非法字节失败。

目标进程预算为 24；加 controller 和 synthetic harness 后的任务总预算为 31。每次启动都必须登记 PID、parent/Job 关系和用途；超预算立即停止。任何输出合同不符、超时、异常、Job 关联失败、清理失败、冻结文件漂移或无法获得真实 exit，都提交 `blocked / finished`，不得继续下一项。

## 成功收口

Q1～Q6 全部通过后：

1. 只生成准确 marker：`R0_READY_PACKAGE_0_OF_1`。
2. 不等待 GO，不包含 package 分支，不启动 package。
3. 复算新 evidence manifest、固定仓库输入、旧 E4 source/dist/marker/lock 和任务进程残留。
4. 确认 `out=false`、staging=false、transition artifacts=0，环境变量和永久 PATH 未变化。
5. 更新执行智能体状态为 `review / finished` 并停止。

该 marker 只证明 R0 环境预检通过，不证明 package、app.asar、最终 EXE、P4-B 或产品通过。

## 失败收口

失败时保存首个失败点、预期、实际、退出码、超时/清理状态和脱敏原始证据。不得用第二次运行覆盖首次失败。安全清理本任务 Job 和临时资源后，把状态写为 `blocked / finished` 并停止。

## 交付要求

`docs/b7-r1-e4-r0-r1-running.md` 至少包含：

- 起终点快照与逐文件边界；
- PowerShell 版本和可执行文件摘要；
- driver/support 文件及 SHA-256；
- synthetic self-test 四类结果；
- 若使用前置修正预算，attempt-0/attempt-1 的完整区别和证据；
- Q1～Q6 每项唯一运行结果、argumentCount/commandTokenCount、stdout/stderr、exit、deadline、PID/Job 与清理状态；
- 进程预算统计；
- 旧 E4 现场与环境不变性；
- marker 是否存在；
- package/P1/P2/P4-C12 均为 `not_run`；
- 未修改产品、测试、依赖、lock、系统环境和 Git 的声明。

`apps/desktop/b7-r1-e4-r0-r1-source.sha256` 必须是有序、唯一的固定 source 清单，并在结束时复算。不要把密钥、token、个人财务数据、原始用户名路径或非必要私有日志写入仓库交付。
