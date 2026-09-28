# P4-B7-R1-E4-R0-R1：R0 driver 恢复执行与停止记录

- 负责人：既有执行智能体。
- 交付状态：`blocked / finished`。不是独立验收，不是项目 complete。
- 授权输入：最新 control `2026-09-28T16:47:00+08:00`，任务卡及已接受的 P4-D14 方案。
- 动态执行：2026-09-28 17:15，Asia/Shanghai；首次 synthetic 失败后立即停止。现场收口复算完成于 17:17；本运行说明于 20:08 整理交付。
- 首个失败：`P4-E4-R0-R1-HARNESS-PROCESS-001`，synthetic Job 累计进程超出冻结单元预算。
- Q1～Q6 均 `not_run`；package、P1、P2、P4-C12 均 `not_run`。没有 ready marker，没有 attempt-1。

## 1. 起点、边界与固定运行时

接单前完整读取规定的协调文件、任务卡、D14 技术建议、总控审阅和旧 E4-R1 报告。起点清单 [p4-b7-r1-e4-r0-r1-start.sha256](coordination/snapshots/p4-b7-r1-e4-r0-r1-start.sha256) 为 226 个唯一、有序路径：**226 matched、0 mismatch、0 missing**，清单自身 SHA-256：

`d8c4dd4c8c396d4633dcdfb4c6933ad9f5a63d96d691370ad511659e4bcea912`

control SHA-256：`3ed741cd28ae7c68ca4922c646983976a0c34af593953ef8c4d53a148e3bc3df`。动态启动前和交付时版本未变化。执行方日志更新后，controller 和收口复算都得到 taskInputs 225 matched、1 authorizedExecutorSkip、0 differences；该 skip 仅为自己的角色文件，首次 226/226 的逐文件核对发生在修改日志之前。

PowerShell 为 **7.6.5 Core / x64**，固定 executable SHA-256：

`362a356ce7f0940ec74f73a8fc2c990a2cc24a38a11c90bbd8eca947110ad139`

其个人绝对路径只在外部 `controller-owner.json` 中保留，不写入仓库交付。

仓库交付仅涉及以下三个路径：

1. [执行方角色日志](coordination/agents/executor.md)：更新。
2. 本运行说明：新建。
3. [R0-R1 source 清单](../apps/desktop/b7-r1-e4-r0-r1-source.sha256)：新建；198 个唯一、有序路径，按字节复制已冻结的 E4-R1 source 清单并逐文件复算，198/198 匹配。

新 source 清单 SHA-256：`04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1`。

最终相对 226 文件起点：225 unchanged、1 changed（仅授权的 executor.md）、0 missing；另有本说明和新 source 清单两个新增交付。只读 Git diff 检查退出 0，提示 executor.md 的 LF 将在以后由 Git 转为 CRLF；本轮没有执行任何 Git 写操作。三份交付的用户名路径和尾随空白检查无命中。

外部只创建了此前不存在的 `C:\MarisE4\E4-20260928-1255\r0-driver-recovery-r1`。支持组件在其 `attempt-0` 中以 create-new 落盘，首次执行前计算摘要；没有改写任何旧 E4/E4-R1 文件。一次过长的工具命令在创建进程前被 Windows 拒绝，未执行或写文件；随后分组 create-new 落盘成功。这不是 synthetic 重试，也没有消费前置修正预算。

只读污染 marker 的首次沙箱访问被拒绝；按任务授权对固定目录进行只读检查后通过，没有修改 ACL。没有修改产品代码、测试、Forge 配置、wrapper、staging、依赖声明、lock、系统 pnpm、永久环境或 Git 状态。既有 `.claude/`、`.pnpm-store/` 未触碰。

## 2. 支持组件及启动前摘要

实现采用 D14 的 `ProcessStartInfo`、逐项 `ArgumentList`、门闩 worker、双流异步原始字节捕获和 Windows Job。正式 `Run-Captured` 保持 `where-pnpm / pnpm / forge-probe` 三项 allowlist；synthetic 用专门入口调用同一监督组件，不冒充正式 pnpm/Forge 检查。

pnpm adapter 仅从四个固定 ASCII 查询选择 cmd 表达式，不接受其他命令；没有任意字符串 shell 拼接、Invoke-Expression 或无限 WaitForExit。worker 放行前必须成功加入无 breakaway 的 Job。退出码、timeout、强制清理、drain 和 Job accounting 分开保存。Job completion port 记录所有成员 PID；短生命周期进程的 image/parent 若无法读取，保留 null，不编造身份。

全部支持清单为外部 `attempt-0/support.sha256`，共 **9 文件**：8 份源码和 1 份按字节复制的冻结 pnpm shim。SHA-256：

`70f841cf352139fc2d78ea4cced5820def6f559339fb9650b926544d18ba4321`

| 相对 attempt-0 的文件 | SHA-256 |
| --- | --- |
| capture.ps1 | 27e38b09ac24326b7b8c7eb45d887501484daa3d57c75524fbd80cc09e5483b9 |
| controller.ps1 | 62767e79a8e6ae39419026f467c0b0b789c9d523b26f00ded2f73a5491e81868 |
| forge-pnpm-bin/pnpm.cmd | 57785cc51fff3a94b68815e46f48a400f1cb016f9edc82d2cb9606cbdb088bdf |
| forge-probe.mjs | 2809939cded9888f6516dbfeaed332d3acdf0654bb0d89a5ecbc3200168bd9ad |
| job.cs | 33319cde7e68d9bb1b373fd2bada86b48a67d657b3cb12d595229fe9f1dab8bf |
| pnpm-adapter.ps1 | f9b3a04b78549f2b924e6959dabce6bfb556171144523a8cab8b16d741d1879f |
| synthetic.ps1 | 6ec0aae01f7480bf640dcb4f23ed777ad4d90ca83bb39a9eeae9ded53eeb9aa7 |
| verify.ps1 | 4b7b2671d0acf5783322bb898bc681be9e1d07c9f0841b3e2d525ddfa39d91e9 |
| worker.ps1 | a302ac55c1c9d9ac7a0653d02dad36efabb5548744628b405fd570d67676b1e0 |

六份 PowerShell 文件启动前静态解析均为 0 个语法错误；收口时再次解析并保存到 `static-parse.json`，仍为 0。C# Job 类型实际编译、关联及 completion accounting 成功；这些局部证据不等于整体 synthetic 通过。

## 3. 首个 synthetic 失败与实际资源收口

计划在两次调用中覆盖四类自测：第一次同时核对空格/中文参数、512 KiB stdout 与 512 KiB stderr 并发输出、native exit 37；第二次验证超时后父、子、孙进程全部退出。预算分别为 2 和 4 个 Job 成员，合计 harness 6；加 controller 1 与 Q 目标 24，总上限 31。

首次调用已经进入真实 synthetic dispatch，随后 Job 记录第三个进程，立即触发 `process_budget_exceeded`。观察到的进程树为：

| PID | 类型/用途 | parent PID | 所属 |
| --- | --- | --- | --- |
| 31908 | PowerShell R0-only controller | 未在本证据中推断 | controller，已退出 |
| 11968 | 门闩 worker / pwsh.exe | 31908 | 本次 synthetic Job |
| 33316 | synthetic fixture / pwsh.exe | 11968 | 同一 Job |
| 32176 | 额外 conhost.exe | 33316 | 同一 Job |

Job ID：`75b64023c75d401f9973f7b50c9e2880`。第一项要求 Job total ≤2，实际为 **3**；Job 成员记录为 3 个唯一 PID，与 accounting 一致。extra conhost 的派生机制尚未验证，不把它归因为 pnpm、Forge、Electron 或 Maris 产品缺陷。

| 首次调用字段 | 真实结果 |
| --- | --- |
| argumentCount / commandTokenCount | 13 / 14，synthetic helper 参数；不是任何 Q 的计数 |
| deadline | 15 秒；在约 556 ms 已因预算停止 |
| 首个 failureCode | process_budget_exceeded |
| native exitCode | null；目标没有正常完成，不用 supervisor 值替代 |
| workerExitCode | 124，Job 强制终止后的 supervisor 值 |
| timedOut | false |
| forcedCleanup | true |
| cleanupComplete / captureComplete | true / true |
| cleanup / drain | 4 ms / 5 ms，均小于 5 秒 |
| totalOwnedProcesses / activeOwnedProcesses | 3 / 0 |
| stdout / stderr | 0 bytes / 0 bytes；原始 bin 已保留 |
| transportOk | false |

四类自测的准确状态：

| 自测类别 | 结果 |
| --- | --- |
| 空格与中文参数逐项保持 | 未得到 fixture receipt，未通过 |
| 并发大量 stdout/stderr 完整捕获 | fixture 未产出预期字节，未通过 |
| 非零 native exit 37 保真 | native exit 为 null，未通过 |
| timeout 父/子/后代 Job 收口 | 专用 timeout 调用 not_run；不得用本次预算异常清理替代该测试 |

本次预算失败仍有独立可复算的资源清理证据：同一 Job 的三个 PID 全部退出，Job active=0，stdout/stderr drain 完成。但四类 synthetic 的通过数为 **0/4**。

`attempt-0/summary.json` 的外层 failureCode 是 `controller_runtime_failure`：强制收口后 fixture receipt 不存在，controller 的后续读取产生次生错误。首个真实失败在 `synthetic-combined/result.json` 中明确为 `process_budget_exceeded`。另建 `failure-classification.json` 解释两者，没有覆盖旧 summary 或原始证据。

前置修正预算使用 **0/1**，不存在 attempt-1。本轮选择在进程预算门禁失败处停止：任务卡要求“进程预算超限”交付 blocked，D14 7.3 要求意外新增进程时停止、不得增加预算容纳它。没有通过提高单元预算、忽略 conhost 或排除已启动进程来继续执行。Q1 尚未开始；后续是否允许新的受限修正，以及如何保持总预算，由总控根据此固定证据裁定。本报告不自行创建后续任务。

## 4. Q1～Q6 与预算

| 项目 | 冻结参数语义 | argumentCount / commandTokenCount | deadline | 实际 |
| --- | --- | --- | --- | --- |
| Q1 | where.exe pnpm | 1 / 2 | 10 s | not_run |
| Q2 | pnpm --version | 1 / 2 | 15 s | not_run |
| Q3 | pnpm config get hoist-pattern | 3 / 4 | 15 s | not_run |
| Q4 | pnpm config get public-hoist-pattern | 3 / 4 | 15 s | not_run |
| Q5 | pnpm config get node-linker | 3 / 4 | 15 s | not_run |
| Q6 | Node probe / installed package-manager / desktop-root | 3 / 4 | 60 s | not_run |

表中 Q 参数和时限是冻结预期；没有实际 stdout、stderr、exit、PID、Job 或 Forge 内部回执，不能把这些预期值写成实测通过。Q dispatch 共 **0 次**。正式 target 进程 **0/24**；实际 synthetic Job 成员 **3**，超过首单元上限 2；controller **1**；监督任务进程累计 **4/31**。完整任务总上限未被耗尽，但首单元预算已经失败。

四项 Forge 内部查询均未执行。仓库和工具命令只用于文档、摘要与资源只读核对，不冒充驱动目标运行。没有重跑首次 synthetic，没有执行任何冻结原生 where、pnpm、Node/Forge 目标。

## 5. 现场与环境不变性

启动前及停止后完整复算结果一致：

| 固定项目 | 结果 |
| --- | --- |
| E4 C 盘 source copy | 198/198 matched |
| 仓库冻结 source | 198/198 matched |
| Electron dist | 73/73 matched |
| 虚拟污染 marker | 9/9 matched |
| E4 旧 evidence | 26/26 matched |
| E4-R1 旧 evidence | 14/14 matched |
| node_modules | 12,451 files，570,581,590 bytes |
| out / .maris-staging | false / false |
| transition artifacts | 0 |
| E4 自有 Electron / Maris / Node / Python | 0 |
| 记录的 Job 三 PID 仍存活 | 0 |

node_modules 按相对路径排序、逐行 `path<TAB>bytes<TAB>sha<LF>` 的 UTF-8 无 BOM 聚合 SHA-256：

`f06ce306456134f7f78176e64d3f9a7e54133607d3e9202ff6bb1a9fcbf800c7`

lock：`5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。

`.modules.yaml`：`68dd21a69c44908e3436b47c0ee40be328cfab4b9e7d0f89728fd809e7b317e1`。

Node：`ba4e6d110e8c1592a1ecd390f6b05f3da124b13871a5be62b341a07a853c6c32`。

pnpm native：`3e1a5bb3aba371d4c1bb5bb87f8ef1bd8dea41e0cd39d4bddf7c3dfbaae665ce`。

Electron executable：`bd14928e0728366fd3f41499cb398ff3f4304dab259a3e605077899a6f8c748e`。

synthetic 在临时 PATH 配方创建之前失败，因此 PATH 与 ELECTRON_CACHE 的赋值分支没有执行。controller 的完整环境摘要前后相同，`environmentRestored=true`。没有修改用户/系统 PATH、注册表、代理、安全软件、ACL 或 Docker 配置。没有外部登录、安装、服务重启、真实个人数据读取或消息发送。

## 6. 不可变证据与复算办法

外部交付根含 **27 文件**：`delivery-evidence.sha256` 的 26 条唯一、有序记录，加清单自身。此清单覆盖全部 attempt-0 文件、原始失败清单、收口状态、收口 PID、故障分类及静态解析结果，排除自身。旧 attempt-0 清单 21/21 逐文件复算通过；最终根清单也需按相同三列算法复算。

| 证据 | 文件/记录数 | SHA-256 |
| --- | --- | --- |
| attempt-0/support.sha256 | 9 支持文件 | 70f841cf352139fc2d78ea4cced5820def6f559339fb9650b926544d18ba4321 |
| attempt-0/final-evidence.sha256 | 21 条记录 | 7199563a42a0a4f705080b17b40f139b8160cd32814edae66f53954ed0aa9b89 |
| failure-classification.json | 1 文件 | adf084694eb06ff929d85a41ff746c0b87172e82bfceffc7d0e3cee527a988d3 |
| delivery-evidence.sha256 | 26 条记录；根共 27 文件 | aef1d227edea8b12058bd0323eecbd96cf87e3e50dc22642492c61ae1d2ddcbb |

清单算法：相对路径使用 `/`，按路径排序；每行为 `path<TAB>bytes<TAB>lowercase-sha256<LF>`；UTF-8 无 BOM，末尾保留一个 LF；清单自身不递归纳入清单。逐文件读取 bytes 与 SHA，再对清单原始 bytes 计算 SHA，即可同时核对每个文件和总摘要。source 清单使用两列 `path<TAB>sha`，同样有序、唯一；不存在将 CRLF 诊断摘要代替冻结 LF 聚合摘要的做法。

准确停止状态：`blocked / finished`，等待头脑风暴总控核对首个进程预算失败。`R0_READY_PACKAGE_0_OF_1` 不存在；package 0 次、P1 0 次、P2 0 次、P4-C12 0 次。本轮没有形成 R0-ready、打包通过或产品验收结论。
