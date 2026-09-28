# P4-B7-R1-E4-PKG-R2：复用已通过预检，只执行一次真实 package

## 唯一目标

你是既有执行智能体。总控已经根据 PKG-R1 原始证据接受 Q1～Q6 全部通过。本任务不得重跑任何预检，只在固定 C 盘 E4 workspace 中恢复相同的进程级 PATH 配方，执行一次现有 package，然后对成功产物做只读静态核对。

成功停在 `review / finished`；真实 package 失败停在 `blocked / finished`。不得启动 app.asar、最终 `Maris.exe`、Electron、Playwright、Python sidecar、P4-C12 或其他智能体。

## 开工前必读

按 `AGENTS.md` 顺序读取：

1. `README.md`
2. `docs/project-coordination.md`
3. `docs/coordination/README.md`
4. 最新 `docs/coordination/control.md`
5. `docs/coordination/agents/executor.md`
6. 本任务卡
7. `docs/p4-b7-r1-e4-pkg-r1-blocked-coordinator-review.md`
8. `docs/b7-r1-e4-pkg-r1-running.md`
9. `docs/b7-r1-h1-r1-staging-atomicity-running.md`
10. `docs/coordination/snapshots/p4-b7-r1-e4-pkg-r2-start.sha256`

最新 control 若不再把本任务分配给执行智能体，立即停止。逐项复算新固定快照后更新自己的 Current execution snapshot。

## 已接受的事实

- Q1～Q5 的路径、版本和 config 原始结果全部通过。
- Q6 stdout 为完整预期 JSON；`inner-1`～`inner-4` 均退出 0、resolved true、stderr 为空，输出与 Q2～Q5 一致。
- PKG-R1 的错误只是核对代码读取不存在的 `inner-0-result.json` 和错误字段名。
- package 尚未启动，当前执行次数是 `0/1`。
- 不得为了补 Q6 外层 result 或结束时间重跑 Q6。

## 固定位置

- E4 根：`C:\MarisE4\E4-20260928-1255`
- workspace：`C:\MarisE4\E4-20260928-1255\workspace`
- desktop：`C:\MarisE4\E4-20260928-1255\workspace\apps\desktop`
- 固定 Node：`C:\MarisE4\E4-20260928-1255\tools\node-v24.21.0-win-x64\node.exe`
- 固定 pnpm：`C:\MarisE4\E4-20260928-1255\tools\pnpm-12.7.0\pnpm-native.exe`
- 已通过的只读预检证据：`C:\MarisE4\E4-20260928-1255\package-resume-1`
- 新 package evidence：`C:\MarisE4\E4-20260928-1255\package-resume-2`

新 evidence 目录必须 create-new。若已经存在，停止，不删除或覆盖。`package-resume-1` 和此前所有 evidence 只读。

## 允许写入范围

仓库内仅允许：

- 更新 `docs/coordination/agents/executor.md`
- 新建 `docs/b7-r1-e4-pkg-r2-running.md`
- 新建 `apps/desktop/b7-r1-e4-pkg-r2-source.sha256`

外部只允许：

- 在 `package-resume-2` 创建 package 原始日志、退出码、PID、时间、静态检查和清单；
- 现有 package wrapper 在固定 workspace 创建并清理 `.maris-staging`、backup、lock、temporary sibling 与 transition artifacts；
- Forge 在固定 workspace 创建 `out`。

## 禁止事项

- 不运行 Q1～Q6，不补写或覆盖 `package-resume-1` 的 result/receipt。
- 不创建 synthetic、Job Object、controller、worker、capture 或新的通用证据 driver。
- 不修改产品、测试、Forge 配置、package wrapper、staging、依赖、lock、`.npmrc`、系统 pnpm、永久 PATH、注册表、代理、安全软件或 ACL。
- 不安装、更新、审计或删除依赖。
- 不运行 `tests/independent/**`。
- 不执行 Git 写操作。
- 不启动 app.asar、最终 EXE、Electron、Playwright、sidecar、数据库、OpenClaw、微信或 DeepSeek。
- 不进行第二次 package。

## package 环境

在一个普通、可观察的持续 PowerShell 会话中，只为当前进程及子进程设置：

- PATH 第一项：在 `package-resume-2/forge-pnpm-bin` create-new 复制的冻结 shim，字节必须与 PKG-R1 shim一致；
- PATH 第二项：固定 Node 目录；
- 其余 PATH 原样继承；
- `ELECTRON_CACHE`：E4 既有固定 cache。

结束时恢复原始 PATH 与 `ELECTRON_CACHE`，核对用户和系统 PATH 未变化。不要使用名为 `$Args` 的变量。

## 唯一 package

在固定 desktop 目录，用固定 pnpm 直接执行现有 `run package`。这是本任务唯一 package，次数为 1/1。保留：

- 命令标签和工作目录；
- package PID、开始和结束时间；
- 原始 stdout、stderr；
- 真实退出码；
- 执行前后的 source、lock、node_modules、Electron dist、out、staging 与环境状态。

如果 package 命令非零退出、超时、崩溃或残留任务进程：记录首个真实失败，完成资源收口，提交 `blocked / finished`。不得修改后重跑。

## 成功后的只读静态核对

package 退出 0 后，不启动任何产物，只检查：

- `out` 中存在预期 Windows package、`Maris.exe`、`resources/app.asar`；
- EXE、app.asar、Electron dist 和资源清单的字节数与 SHA-256；
- production fuses 符合冻结合同；
- packaged Python resources 只包含 H1 allowlist；
- `.pyc`、`.pyo`、`.pyd`、`.egg-info`、`__pycache__`、测试、构建缓存、任务 evidence、用户路径、凭据样式和私钥均为 0 命中；
- `.maris-staging`、backup、lock、temporary sibling 与 transition artifacts 已清理；
- workspace source、`pnpm-lock.yaml`、node_modules 和 Electron dist 保持冻结摘要。

静态核对脚本若出现纯读取逻辑错误，允许在 `package-resume-2` 内修正核对代码并重新读取同一份不可变 package 产物。必须保留第一次错误和修正记录；不得重新运行 package，也不得修改产物来满足检查。

## 资源收口

- 任务派生的 pnpm、Node、Forge、Electron、Maris、Python/Pythonw 进程为 0；
- 不终止不属于本任务的系统进程，也不要求系统 `conhost.exe` 总数为 0；
- process-local 环境已恢复，用户和系统环境未变化；
- package 成功产物保留供下一任务使用，不删除 `out`；
- staging 和临时 transition 产物必须清理。

## 交付

运行说明必须列出：

- 新固定快照和 PKG-R1 证据只读复算；
- 明确写出 Q1～Q6 `accepted_from_previous_evidence / not_rerun`；
- package 实际次数、命令、时间、PID、退出码和原始日志摘要；
- 静态产物、fuse、resource、污染与 staging 结果；
- 未运行的 app.asar、最终 EXE 与 P4-C12；
- 任务进程和环境收口；
- 三个仓库交付文件及 SHA-256；
- 外部 evidence 清单与复算算法。

package 与全部静态门禁通过后提交 `review / finished`。任何真实 package 或不可解决的静态产品缺陷提交 `blocked / finished`。最终接受权属于头脑风暴总控。

