# P4-B7-R1-E4-R0-R1-A1：使用唯一前置修正预算恢复 attempt-1

## 唯一目标

你是既有执行智能体。本任务是 `P4-B7-R1-E4-R0-R1` 的唯一 driver-only 前置修正续段。保留 attempt-0 后，在 create-new `attempt-1` 中显式控制 native 与 synthetic 子孙进程的标准流和无窗口启动，然后重新完成四类 synthetic 自测；只有 synthetic 全部通过，才能继续原定 Q1～Q6。

成功仍只生成 `R0_READY_PACKAGE_0_OF_1` 并停在 `review / finished`。任何失败停在 `blocked / finished`。不得执行 package、P1、P2、P4-C12 或创建新任务。

## 开工前必读与控制门禁

按 `AGENTS.md` 顺序读取：

1. `README.md`
2. `docs/project-coordination.md`
3. `docs/coordination/README.md`
4. 最新 `docs/coordination/control.md`
5. `docs/coordination/agents/executor.md`
6. 本任务卡
7. `docs/p4-b7-r1-e4-r0-r1-blocked-coordinator-review.md`
8. `docs/b7-r1-e4-r0-r1-running.md`
9. `docs/phase-4-d14-r0-driver-recovery-advice.md`
10. `docs/p4-d14-coordinator-review.md`
11. `docs/coordination/prompts/p4-b7-r1-e4-r0-r1-executor.md`
12. `docs/coordination/snapshots/p4-b7-r1-e4-r0-r1-a1-start.sha256`

最新 control 若不再把 A1 分配给执行智能体，立即停止。先逐文件复算新固定快照；清单应为 230 个唯一、有序路径。再更新自己的 Current execution snapshot。

## 已冻结事实

- attempt-0 的首个失败是 `process_budget_exceeded`，发生在 synthetic combined；Q1～Q6 未启动。
- Job 成员为 worker `pwsh`、synthetic `pwsh`、synthetic 派生 `conhost.exe`；三者均已退出。
- attempt-0 correction budget 使用 0/1；A1 使用这唯一一次预算。
- attempt-0 外部 evidence 26/26 匹配，清单 SHA-256 为 `aef1d227edea8b12058bd0323eecbd96cf87e3e50dc22642492c61ae1d2ddcbb`。
- source 198/198，manifest SHA-256 为 `04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1`。
- package 仍为 0/1，产品、测试、依赖、lock、PATH、out 和 staging 均未改变。

## 允许写入范围

仓库内仅允许：

- 更新 `docs/coordination/agents/executor.md`
- 新建 `docs/b7-r1-e4-r0-r1-a1-running.md`
- 新建 `apps/desktop/b7-r1-e4-r0-r1-a1-source.sha256`

外部只允许在：

`C:\MarisE4\E4-20260928-1255\r0-driver-recovery-r1\attempt-1`

以 create-new 方式写入 A1 controller、worker、synthetic、adapter、probe、evidence 和摘要。`attempt-0/**`、旧根级 closeout/classification/manifest 与所有 E4/E4-R1 evidence 全部只读。若 `attempt-1` 已存在，停止，不删除或覆盖。

## 禁止事项

- 不运行 package、Forge package、app.asar、Electron、Maris、Playwright Electron、sidecar、数据库或外部集成。
- 不安装、更新、审计或删除依赖。
- 不修改产品、测试、Forge 配置、wrapper、staging、依赖、lock、`.npmrc`、系统 pnpm、永久 PATH、注册表、代理、安全软件或 ACL。
- 不修改或运行 `tests/independent/**`。
- 不执行 Git 写操作。
- 不按进程名或 image 过滤、忽略 `conhost.exe`；它出现时仍是 Job 成员和失败证据。
- 不增加 attempt-1 的 2/4、6/24/31 live budget。
- 不允许 attempt-2 或再次修改 driver。

## attempt-1 的唯一代码修正

从 attempt-0 源码复制到新目录并核对复制前后摘要。只允许为受控标准流、无窗口启动和相应有界 pump 修改 driver/support 代码。

### worker 启动 native 目标

native `ProcessStartInfo` 必须显式设置：

- `UseShellExecute = false`
- `CreateNoWindow = true`
- `RedirectStandardInput = true`
- `RedirectStandardOutput = true`
- `RedirectStandardError = true`

native 启动后立即关闭其 stdin。将 native stdout 的 `BaseStream` 异步复制到 worker 的 `Console.OpenStandardOutput()`，将 native stderr 异步复制到 `Console.OpenStandardError()`。两个 pump 必须在 native 退出后进行有界等待；不能先同步读完一条流再读另一条，也不能无限等待。native 真实退出码、pump 成功/失败和 worker 退出码仍分开记录。

outer capture 继续只捕获 worker 的 stdout/stderr，保持 1 MiB 单流上限、5 秒 drain 与现有 result schema。不得把 warning 混入标准输出或 JSON。

### synthetic 父、子、孙进程

synthetic fixture 创建下一层 `pwsh.exe` 时同样显式设置 `UseShellExecute=false`、`CreateNoWindow=true` 以及 stdin/stdout/stderr 三条重定向。立即关闭子进程 stdin；stdout/stderr 异步 drain 到 `Stream.Null`，不能让未读取管道成为超时原因。父、子、孙的 receipt、PID 和 Job membership 仍必须完整记录。

禁止改为 GUI helper、忽略 console host、使用 breakaway 或把后代移出 Job。

## 固定预算与验证顺序

attempt-1 live 预算保持：

- synthetic combined：worker + fixture，`MaxActive=2`、`MaxTotal=2`
- synthetic timeout：worker + parent + child + grandchild，`MaxActive=4`、`MaxTotal=4`
- harness 合计最多 6
- Q targets 合计最多 24
- controller 1；attempt-1 live 总计最多 31

attempt-0 已观察历史进程 4 个；最终报告必须分开统计 attempt-0 与 attempt-1，并给出跨尝试累计值。跨尝试累计上限为 35；它不是 attempt-1 的扩容。

顺序固定：

1. 复算仓库快照、attempt-0 evidence、source/dist/marker/lock/node_modules 与零残留。
2. create-new 落盘 attempt-1 源码，静态解析，计算 support manifest。
3. 运行 synthetic combined 一次，验证空格/中文、512 KiB 双流、真实 exit 37；Job total 必须恰好 2，active 最终为 0。
4. combined 通过后，运行 synthetic timeout 一次，验证 parent/child/grandchild receipt、超时、整 Job 收口；Job total 必须恰好 4，active 最终为 0。
5. 四类 synthetic 全部通过后，才创建一次进程级 PATH 配方并按原任务卡顺序执行 Q1～Q6，各一次。
6. Q1～Q6 全部通过后只写 `R0_READY_PACKAGE_0_OF_1`，复算现场并退出。

如果 combined 或 timeout 再出现 `conhost.exe`、其他额外进程、输出不完整、退出码不符、超时语义不符、Job/PID ledger 不完整、残留进程或任何新 driver 缺陷，立即停止。不得使用第二次修正。

## Q1～Q6 合同保持不变

- Q1：`where.exe pnpm`，1 argument / 2 command tokens，10 秒；第一行精确为 task-owned shim。
- Q2：`pnpm --version`，1 / 2，15 秒；唯一输出 `12.7.0`。
- Q3：`pnpm config get hoist-pattern`，3 / 4，15 秒；唯一输出 `undefined`。
- Q4：`pnpm config get public-hoist-pattern`，3 / 4，15 秒；唯一输出 `undefined`。
- Q5：`pnpm config get node-linker`，3 / 4，15 秒；唯一输出 `hoisted`。
- Q6：固定 Node + Forge probe 三参数，3 / 4，60 秒；严格 UTF-8 JSON，四个内部查询与 Q2～Q5 一致。

每项 stderr 必须为空；任何失败、超时、帮助输出、异常进程、预算超限或收口失败都停止后续项。R0-ready 不授权 package。

## 交付

运行说明必须区分：

- attempt-0 的不可变失败证据；
- attempt-1 的源码差异和摘要；
- synthetic combined/timeout 的唯一运行结果；
- Q1～Q6 的实际运行或准确 `not_run`；
- attempt-1 live 与跨尝试累计进程预算；
- 三条标准流、双流 pump、退出码、Job/PID 和清理证据；
- 固定输入和环境不变性；
- package/P1/P2/P4-C12 均为 `not_run`；
- marker 是否存在。

成功为 `review / finished`；失败为 `blocked / finished`。两种状态都停止，最终接受权属于头脑风暴总控。
