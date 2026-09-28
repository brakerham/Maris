# P4-B7-R1-E4-R0-R1 synthetic 进程预算阻塞总控核对

- 核对时间：2026-09-28 20:18，Asia/Shanghai
- 执行方状态：`blocked / finished`
- 总控结论：接受停止状态与不可变证据；未形成 pnpm、Forge、package 或 Maris 产品缺陷
- 后续决定：使用尚未消耗的 driver-only 前置修正预算，发布 `P4-B7-R1-E4-R0-R1-A1`

## 1. 交付与快照核对

总控复算结果：

- 226 文件起点：226/226 matched，0 mismatch，0 missing。
- 停止后：225 unchanged，仅授权的执行智能体角色日志变化，0 missing。
- source：198/198 matched；清单 SHA-256 `04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1`。
- 外部 `delivery-evidence.sha256`：26/26 matched，0 mismatch，0 missing；清单 SHA-256 `aef1d227edea8b12058bd0323eecbd96cf87e3e50dc22642492c61ae1d2ddcbb`。
- 仓库三份交付的路径/字节/SHA 有序总摘要：`5e72dcf8be1522d4413c55685a9ffb436fb4472accf35535ea3228006564cace`。
- out、staging、transition artifacts 与任务自有目标进程均为零；三个 Job PID 已全部退出。
- Q1～Q6、package、P1、P2、P4-C12 均为 `not_run`；`R0_READY_PACKAGE_0_OF_1` 不存在。

执行方在第三个 Job 成员出现后立即终止整个 Job，cleanup 4 ms、双流 drain 5 ms、active process 归零。该证据证明本次异常路径收口有效，但不能代替尚未运行的四类 synthetic 自测。

## 2. 首个失败的准确解释

首次 synthetic 的 Job 事件为：

1. worker `pwsh.exe`；
2. synthetic fixture `pwsh.exe`；
3. fixture 派生的 `conhost.exe`。

执行方把 combined cell 的 `MaxActive/MaxTotal` 设为 2，随后 Job accounting 得到 total 3，触发 `process_budget_exceeded`。这不是 Q1 或任何 pnpm/Forge 目标的失败。

Microsoft 将 `conhost.exe` 定义为命令行应用的 Windows Console API 服务端与传统 UI 宿主；console 应用需要标准句柄。Job Object 默认会把已关联进程创建的子进程纳入同一 Job；其 `TotalProcesses` 还会包含因 active process limit 关联失败而被终止的进程。参考：[Windows Console definitions](https://learn.microsoft.com/en-us/windows/console/definitions)、[Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)、[JOBOBJECT_BASIC_ACCOUNTING_INFORMATION](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_accounting_information)、[Process creation flags](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags)。

结合本轮 `MaxActive=2`、Job total 3、第三个 PID 为 `conhost.exe`、fixture 输出为零以及随后整体被强制收口，总控推断：native synthetic `pwsh.exe` 没有显式接入受控三条标准流，Windows 尝试为 console 客户端提供 console host；该关联又碰到 active limit。该推断需要 A1 动态验证，不能写成已证明的 Windows 根因。

## 3. 为什么不是直接增加预算

D14 冻结的是 harness 前置最多 6 个任务进程、R0 目标最多 24、单次成功路线总上限 31；D14 没有冻结 combined cell 必须永久容纳一个额外 console host。简单把 2 改为 3 会让未受控 console 基础设施进入正式 Q 路线，而且无法保证 timeout 父/子/孙链不会生成更多 console host。

因此 A1 不过滤、不忽略 `conhost.exe`，也不把 live budget 调高。它先修正标准流和无控制台启动边界：native 目标与 synthetic 子孙进程均显式使用受控 stdin/stdout/stderr；combined 仍限 2，timeout 仍限 4。如果同一额外进程再次出现，A1 立即停止。

## 4. A1 恢复边界

原任务明确授权 Q1 前最多一次保留现场的 driver-only 修正；本轮 Q1 尚未启动、产品与环境未改变、修正预算为 0/1。因此总控允许把后续续段作为同一恢复链的 `attempt-1`，而不是重新设计产品或再次执行 package。

A1 必须：

- 完整保留 `attempt-0` 和旧 27 文件 evidence；
- 在 create-new `attempt-1` 中落盘修正源码与摘要；
- native `ProcessStartInfo` 显式重定向 stdin/stdout/stderr，stdout/stderr 通过异步有界 pump 转发到外层 capture；
- synthetic 父/子/孙创建时同样显式使用无窗口与受控标准流；
- combined Job 仍为 2，timeout Job 仍为 4；不按进程名或 image 排除 console host；
- synthetic 任一项失败即停止，不再允许第二次修正；
- synthetic 全部通过后，Q1～Q6 才各运行一次；成功仍只生成 `R0_READY_PACKAGE_0_OF_1`。

attempt-0 已观察到 controller 1 加 Job 成员 3，共 4 个历史进程。A1 的实时预算继续保持 controller 1、harness 6、targets 24、合计 31；为准确披露已发生的修正，attempt-0 与 attempt-1 的跨尝试累计审计上限为 35。这个 35 只用于历史累计报告，不允许增加 attempt-1 的并发或单次预算。

## 5. 项目状态

`P4-B7-R1-E4-R0-R1` 保持 `blocked / finished`，其失败现场作为不可变输入保留。`P4-B7-R1-E4-R0-R1-A1` 为 `ready / waiting_user`。package 仍为 0/1；P4-B、P4-C12 和财务驾驶舱前端均未完成。技术顾问与测试智能体继续停止。

A1 固定输入为 230 项，manifest 位于 `docs/coordination/snapshots/p4-b7-r1-e4-r0-r1-a1-start.sha256`。执行方必须逐文件复算，不能只核对 manifest 自身摘要。
