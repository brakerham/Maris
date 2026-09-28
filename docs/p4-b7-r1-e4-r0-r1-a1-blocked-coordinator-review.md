# P4-B7-R1-E4-R0-R1-A1 阻塞总控核对

## 结论

`P4-B7-R1-E4-R0-R1-A1` 的停止结论成立，状态接受为 `blocked / finished`。A1 已用完唯一 driver-only 修正预算；不得创建 `attempt-2`，不得继续修改同一套 PowerShell synthetic/Job driver。

这次结果证明项目已经在 R0 验证路径上形成局部循环：attempt-0 因 worker、fixture、`conhost.exe` 三个 Job 成员超过“恰好两个进程”的自定门禁而停止；A1 明确接管 native 与 synthetic 子孙的 stdin/stdout/stderr 后，同一门禁仍以同样的三成员结构停止。两轮都没有运行 Q1～Q6，也没有启动 package。

这里的循环属于验收工具，而不是 Maris 产品、pnpm 或 Forge。A1 没有形成产品缺陷证据，也没有证明任务专属 pnpm 解析失败。继续增加 synthetic、Job、receipt、进程预算或再分析 `conhost.exe`，不会更接近“Forge 能否用正确 pnpm 完成 package”这个真实问题。

## 已核对的证据

- 仓库三份交付摘要分别匹配：
  - `docs/b7-r1-e4-r0-r1-a1-running.md`：`7618ccda255e26206ae89f883ad595578b681259b11de508eb0bf2f4c1fb3f94`
  - `docs/coordination/agents/executor.md`：`26763ee1da6c6d0ccd8c4cbb2921e61fce149abfa31a13ad99235af2c451059d`
  - `apps/desktop/b7-r1-e4-r0-r1-a1-source.sha256`：`04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1`
- 三份交付按相对路径、字节数和摘要组合后的 SHA-256 为 `44714e3fcdd0d5f00790c22b742c9614a31f6f9a88b5c4a74f0edab69eb388d2`。
- 外部 `attempt-1/delivery-evidence.sha256` 为 39 条记录，逐项复算为 39/39 匹配，清单 SHA-256 为 `ac0da66b9f5e9626bca0d491c675ee4276876ddc248859c739c9cfa89343e87a`。
- 首失败是 `process_budget_exceeded`；Job 成员为 worker、fixture 与 `conhost.exe`，累计 3、最终 active 0。
- native 真实退出码、双流压力、参数回执和 timeout 自测均没有完成，Q1～Q6、package、P1、P2、P4-C12 均为 `not_run`。
- 记录的任务进程已经退出；没有发现任务遗留进程。

## 对前一工作假设的修正

前一轮把“目标没有显式接管标准流”作为 `conhost.exe` 的待验证原因。A1 已按冻结合同完成三流重定向，但现象没有改变，因此该假设未得到支持，不能继续据此派发下一次 driver 修正。

`conhost.exe` 是否由 pwsh、Windows Console、调试环境或当前进程继承关系触发，对下一步 package 已经不是必要答案。它可以保留为 Windows 环境调查材料，但不再作为 P4-B 发布前 package 的前置门禁。

## 终止的路线

以下路线从本次核对起停止：

- synthetic combined 与 synthetic timeout；
- “Job total 必须恰好为 2/4”的门禁；
- 为 Q1～Q6 编写通用 PowerShell worker/capture/controller；
- 继续使用 D14 的 driver correction budget；
- `attempt-2` 或任何同构重跑。

保留的安全边界是：任务专属 PATH、固定 Node/pnpm、命令超时、原始 stdout/stderr、真实退出码、一次 package 预算、任务进程收口、产品和依赖不变性。它们不需要通过 synthetic 进程树才能验证。

## 新路线

下一任务为 `P4-B7-R1-E4-PKG-R1`，只完成“直接预检 → 唯一 package”两个步骤：

1. 在一个任务专属进程环境中，把已冻结的 pnpm shim 和固定 Node 放到 PATH 前部。
2. 直接、逐条运行 `where pnpm`、pnpm 版本、三个 config 查询和 Forge `spawnPackageManager` 探针，保存原始输出和退出码。
3. 任一预检失败就停止，不修 driver，不运行 package。
4. 全部预检通过后只运行一次真实 package。
5. package 成功后检查产物、fuse、资源 allowlist、污染文件和 staging 收口；不启动 app.asar 或最终 EXE。

新任务不限制 console helper 的精确数量，也不因 `conhost.exe` 本身失败。它只要求命令有界结束、结果正确、任务结束后没有任务自有残留进程。

## 项目影响

- P4-B 仍未完成，P4-C12 不启动。
- 已实现的 Windows Shell、Host 接线、H1-R1 package hygiene 与 E3 Electron 成功证据保持不变。
- 当前没有 pnpm、Forge、package 或产品缺陷结论。
- 本轮失败不需要技术顾问再次设计，也不需要测试智能体介入。

