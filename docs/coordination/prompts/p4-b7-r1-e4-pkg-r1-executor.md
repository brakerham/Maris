# P4-B7-R1-E4-PKG-R1：终止 synthetic 循环后直接执行预检与唯一 package

## 角色与目标

你是既有执行智能体。本任务替代已经停止的 R0 synthetic/Job 路线。目标是在固定的 C 盘 E4 工作副本中，以任务专属 PATH 直接验证 pnpm 与 Forge 的真实解析；预检全部通过后，只执行一次真实 package，并核对 package 产物与 H1 资源边界。

本任务不启动 app.asar、最终 `Maris.exe`、Electron、Playwright、Python sidecar、P4-C12 或独立验收。成功停在 `review / finished`；任一步失败停在 `blocked / finished`。

## 开工前必读

按 `AGENTS.md` 顺序读取：

1. `README.md`
2. `docs/project-coordination.md`
3. `docs/coordination/README.md`
4. 最新 `docs/coordination/control.md`
5. `docs/coordination/agents/executor.md`
6. 本任务卡
7. `docs/p4-b7-r1-e4-r0-r1-a1-blocked-coordinator-review.md`
8. `docs/b7-r1-e4-r0-r1-a1-running.md`
9. `docs/b7-r1-e4-package-product-gates-running.md`
10. `docs/b7-r1-h1-r1-staging-atomicity-running.md`
11. `docs/coordination/snapshots/p4-b7-r1-e4-pkg-r1-start.sha256`

最新 control 若不再把本任务分配给执行智能体，立即停止。先逐文件复算固定快照，再更新自己的 Current execution snapshot。

## 总控已经冻结的判断

- A1 再次出现 worker、fixture、`conhost.exe` 三个 Job 成员，证明 synthetic 精确进程数门禁不适合作为 package 前置条件。
- A1 的唯一 driver 修正预算已经用完，不允许 `attempt-2`，不允许继续修改或运行旧 controller、worker、capture、synthetic 与 Job driver。
- `conhost.exe` 本身不再构成失败。只要真实命令有界结束、输出和退出码正确，且任务结束后没有任务自有残留进程，即可继续。
- package 到目前仍只真实启动过一次：E4 在 Forge `Checking package manager version` 处因错误用户级 pnpm shim 失败。此任务重新授权一次新的 package 尝试。

## 固定工作区与工具

- E4 根：`C:\MarisE4\E4-20260928-1255`
- 固定源码：`C:\MarisE4\E4-20260928-1255\workspace`
- desktop：`C:\MarisE4\E4-20260928-1255\workspace\apps\desktop`
- 固定 Node：`C:\MarisE4\E4-20260928-1255\tools\node-v24.21.0-win-x64\node.exe`
- 固定 pnpm：`C:\MarisE4\E4-20260928-1255\tools\pnpm-12.7.0\pnpm-native.exe`
- 只读参考 shim：`C:\MarisE4\E4-20260928-1255\r0-driver-recovery-r1\attempt-1\forge-pnpm-bin\pnpm.cmd`
- 只读参考 Forge probe：`C:\MarisE4\E4-20260928-1255\r0-driver-recovery-r1\attempt-1\forge-probe.mjs`
- 新证据目录：`C:\MarisE4\E4-20260928-1255\package-resume-1`

新证据目录必须 create-new；如果已经存在，停止，不删除、不覆盖。旧 E4、R0、attempt-0 与 attempt-1 evidence 全部只读。

## 允许写入范围

仓库内仅允许：

- 更新 `docs/coordination/agents/executor.md`
- 新建 `docs/b7-r1-e4-pkg-r1-running.md`
- 新建 `apps/desktop/b7-r1-e4-pkg-r1-source.sha256`

外部只允许在 `package-resume-1` 中创建预检、package 与收口证据；package 自身可按现有 wrapper 写入固定 workspace 的 `.maris-staging` 和 `out`。成功或失败后必须由现有 wrapper/收口流程清理 `.maris-staging` 及 transition artifacts。

## 禁止事项

- 不创建或运行新的通用 PowerShell driver、Job Object、synthetic fixture、worker、capture 或进程预算控制器。
- 不限制 `conhost.exe` 或其他 Windows console helper 的精确数量；不按 image 过滤后伪造统计。
- 不执行第二次 package；第一次真实 package 结束后，无论成功或失败都停止 package 动作。
- 不启动 Electron、Playwright、app.asar、最终 EXE、sidecar、数据库、OpenClaw、微信或 DeepSeek。
- 不修改产品、测试、Forge 配置、package wrapper、staging、依赖、lock、`.npmrc`、系统 pnpm、永久 PATH、注册表、代理、安全软件或 ACL。
- 不安装、更新、审计或删除依赖。
- 不执行任何 Git 写操作。
- 不修改或运行 `tests/independent/**`。

## 执行方式

使用一个可观察、持续的普通 PowerShell 会话。环境变量只在该进程及其子进程中生效，结束时还原：

- PATH 第一项为任务专属 shim 目录；shim 内容必须与冻结参考 shim 字节一致，指向固定 pnpm。
- PATH 第二项为固定 Node 目录。
- 其余 PATH 原样继承。
- `ELECTRON_CACHE` 使用已有 E4 固定 cache。

不要把命令参数保存在名为 `$Args` 的变量中。不要再抽象 `Run-Captured`；六项预检应写成六条明确命令，分别保存 stdout、stderr、退出码、开始/结束时间和命令标签。可使用 shell 会话本身的超时/中断能力；若一项超过时限，只结束该任务派生的命令树并停止后续步骤。

## R0 直接预检

顺序固定，每项只运行一次：

1. `where.exe pnpm`：10 秒；第一条必须是任务专属 shim。
2. `pnpm --version`：15 秒；唯一有效内容为 `12.7.0`。
3. `pnpm config get hoist-pattern`：15 秒；唯一有效内容为 `undefined`。
4. `pnpm config get public-hoist-pattern`：15 秒；唯一有效内容为 `undefined`。
5. `pnpm config get node-linker`：15 秒；唯一有效内容为 `hoisted`。
6. 固定 Node 调用 Forge probe：60 秒；必须证明 Forge `spawnPackageManager` 的四个查询得到与第 2～5 项相同结果。

每项 stderr 必须为空、退出码必须为 0。保存原始输出，不用 synthetic 证明参数、双流或精确进程数。任一项失败、超时或输出不符，记录失败并停止；不得在本任务内修复后重跑。

## 唯一 package

六项直接预检全部通过后，在同一进程环境、同一 PATH 配方和固定 desktop 目录执行现有 `pnpm run package`，次数严格为 1/1。保留完整原始日志、真实退出码、开始/结束时间和任务派生 PID 证据。

package 失败时：

- 不修改代码或环境后重试；
- 分类首个真实失败；
- 收口任务自有进程；
- 核对 lock、源码、依赖、out 与 staging 状态；
- 提交 `blocked / finished`。

package 成功时，只做静态核对：

- `out` 中存在预期 Windows package、`Maris.exe` 与 `resources/app.asar`；
- production fuses 符合冻结合同；
- packaged resources 只包含 H1 allowlist，不能包含 `.pyc`、`.pyo`、`.egg-info`、`__pycache__`、测试、用户路径、任务 evidence 或凭据样式；
- `.maris-staging`、backup、lock、temporary sibling 与 transition artifacts 全部清理；
- `pnpm-lock.yaml`、固定 source、Electron dist 与 `node_modules` 摘要不变；
- 只记录 EXE/app.asar/资源清单摘要，不启动它们。

不要把 package 成功写成 app.asar、最终 EXE 或 P4-B 已通过。后两项将由总控另行派发一次性动态任务。

## 资源收口

结束时确认：

- 本任务派生的 pnpm、Node、Forge、Electron、Maris、Python/Pythonw 进程为 0；
- 不要求系统中 `conhost.exe` 总数为 0，也不终止不属于本任务的进程；
- process-local PATH 与 `ELECTRON_CACHE` 已还原；
- 没有改变用户或系统环境；
- 未删除 node_modules、E4 workspace、旧 evidence 或 package 成功产物。

## 交付

运行说明必须清楚列出：

- 起点快照与固定 C 盘输入复算；
- 六项直接预检的逐项实际结果；
- package 是否执行、唯一执行次数、真实退出码与首失败或成功产物；
- 静态 package/fuse/resource/staging 核对；
- 未运行的 app.asar、EXE、P4-C12；
- 任务进程和环境收口；
- 三个仓库交付文件及 SHA-256；
- 新外部证据清单及复算算法。

成功状态为 `review / finished`；失败状态为 `blocked / finished`。两种状态都停止，等待头脑风暴总控。

