# P4-D14 R0 driver 恢复总控审阅

- 审阅时间：2026-09-28 16:47，Asia/Shanghai
- 审阅角色：头脑风暴总控
- 技术顾问交付状态：`review / finished`
- 总控结论：`complete`；接受 `P4-D14-F01～F21`，发布一次严格的 R0-only 恢复任务

## 1. 验收结论

P4-D14 对 `P4-E4-R1-R0-DRIVER-ARGS-001` 的定性准确：失败发生在任务 evidence driver 中，`Run-Captured` 的形参 `$Args` 与 PowerShell 自动变量冲突，导致 where、pnpm 与 Node probe 都没有收到冻结实参。package 仍为 0/1，现有证据没有否定 task-owned pnpm shim、Forge `spawnPackageManager` 恢复方案，也没有形成 Maris 产品缺陷、Forge 配置缺陷或 package wrapper 缺陷证据。

总控接受文档给出的唯一实现路线：原生程序通过 `System.Diagnostics.ProcessStartInfo` 与 `ArgumentList` 逐项传参；裸 `pnpm` 只允许四种冻结查询并通过受限 `cmd.exe /d /s /c` adapter 进入；stdout、stderr 和真实退出码分别保存；每次目标进程在放行前加入任务专属 Windows Job Object；超时或异常时按 Job 收口全部后代进程。

本次只接受技术方案，不把静态代码审查写成动态通过。Windows Job、双流捕获、超时收口、Forge probe 和六项 R0 检查仍需要执行智能体在新的任务中验证。

## 2. 独立核对证据

- P4-D14 起点快照：223/223 matched，0 mismatch，0 missing。
- 起点 manifest SHA-256：`98ac61ebe79a58e0fc4b0f5817c4530594079399dfc2ab03367d4812a1f52a2d`。
- 技术裁定文档：677 行，SHA-256 `2c067ded273b3286ec911b19316ec054e8b7f32f8a481815de879d21a962af68`。
- `P4-D14-F01～F21` 共 21 个唯一冻结 ID。
- 三个 PowerShell fenced block 分别为 0 个语法错误；最长代码块 18,312 字符。
- Markdown fence 成对，本地链接无缺失，尾随空白为零。
- 当前 Codex PowerShell 为 7.6.5 Core；`pwsh.exe` SHA-256 为 `362a356ce7f0940ec74f73a8fc2c990a2cc24a38a11c90bbd8eca947110ad139`。
- 技术顾问没有运行 R0、package、Electron、Maris 或 sidecar，没有修改产品、依赖、lock、系统 PATH 或旧 evidence。

## 3. 六项总控裁定

1. **接受参数计数勘误。** `pnpm config get hoist-pattern`、`public-hoist-pattern` 与 `node-linker` 都是 3 个实参、4 个 command tokens。禁止为满足旧任务卡中的“四参数”措辞添加空参数或改变查询。
2. **接受唯一捕获实现。** 新 driver 必须使用 P4-D14 给出的 `ProcessStartInfo + ArgumentList + 受限 cmd adapter + Job Object/worker` 边界。绑定 PowerShell 7.6.5 Core 和上述可执行文件摘要；路径只在受限外部 evidence 中记录，仓库文档不保存个人绝对路径。
3. **接受新 probe 合同。** 新 probe 的源码和摘要属于新任务 evidence；旧 E4/E4-R1 probe 与失败现场保持不可变。Q6 只接受严格 UTF-8 JSON，不能把日志或 warning 混入 JSON 后仍判通过。
4. **冻结 R0-only 运行边界。** 使用新的 evidence 目录；支持组件先完成 Unicode/空格参数、并发双流、非零退出和超时后代收口的 synthetic self-test。Q1～Q6 顺序固定、每项只运行一次；Q1 10 秒，Q2～Q5 各 15 秒，Q6 60 秒；cleanup 与 drain 各不超过 5 秒；R0 目标进程预算 24，总计预算 31。
5. **允许一次严格受限的 harness 前置修正。** 只有在尚未启动 Q1、没有运行任何冻结原生目标、没有修改环境或产品时，synthetic self-test 暴露的 driver 自身缺陷才允许保留 attempt-0 全部证据后修正一次，并在 fresh attempt-1 重跑 synthetic self-test。Q1 一旦启动，此例外立即失效；Q1～Q6 任一失败均必须停止，不能重跑该项或继续后续项。
6. **R0-ready 不授权 package。** 六项全过后只生成 `R0_READY_PACKAGE_0_OF_1` 并退出。package-only、P1、P2、P4-C12 和前端业务实现仍需总控另立任务。普通开发者直接打包的 pnpm 解析体验继续记为待验证；当前不修改 package wrapper、系统 pnpm 或永久 PATH。

## 4. 下一任务与停止条件

下一任务为 `P4-B7-R1-E4-R0-R1`，唯一负责人是执行智能体。它只能验证恢复后的 R0 driver 与六项预检，不得执行 package、Forge package、app.asar、最终 EXE、Electron、sidecar、数据库、外部登录或独立验收。

新任务固定输入为 226 项，manifest 位于 `docs/coordination/snapshots/p4-b7-r1-e4-r0-r1-start.sha256`。任务发布时的 manifest SHA-256 由总控最终复算并同步到协调状态；执行方以文件内容为准逐行校验，不能仅比较 manifest 自身摘要。

任务成功的唯一标志是 fresh evidence 中六项检查全部通过、环境和冻结输入保持不变、没有残留任务进程，并写出准确 marker `R0_READY_PACKAGE_0_OF_1`。该标志表示“可以由总控考虑下一张 package-only 任务”，不表示 package、P4-B 或产品已经通过。

若 synthetic self-test 在一次受限修正后仍失败，或 Q1～Q6 任一项失败、超时、stderr 非空、输出合同不符、进程预算超限、Job 关联失败、清理失败、冻结输入漂移，任务必须提交 `blocked / finished` 并停止。执行方不得自行创建后续任务。

## 5. 项目状态影响

P4-D14 现由总控验收为 `complete`。P4-B 仍未完成，24 项 P4-B 独立矩阵仍为 `not_run`，P4-C12 继续保持 `not_started`。本次裁定不改变产品范围，也不推进此前已暂停的公众注册、多用户、云账户、P4-C 财务驾驶舱或 P4-D 财富管理业务实现。
