# P4-D14 技术顾问任务卡：E4-R1 R0 PowerShell driver 恢复裁定

你是技术顾问，唯一负责 `P4-D14`。请使用 GPT-6 Astra，reasoning effort `high`。本任务只读审计 `P4-B7-R1-E4-R1` 的 R0 evidence driver 参数转发失败，交付一份能够直接约束下一次 R0-only 执行的技术裁定。

这不是架构重做，也不是产品开发。不得运行 R0、pnpm、Forge package、Electron、Maris 或 Python Host；不得修改外部 C 盘 evidence；不得修改产品、测试、依赖、lock、系统 pnpm、PATH 或系统设置。

## 必读输入

开始前依次读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. 最新 `docs/coordination/control.md`
6. `docs/coordination/agents/technical-adviser.md`
7. `docs/p4-b7-r1-e4-blocked-coordinator-review.md`
8. `docs/coordination/prompts/p4-b7-r1-e4-r1-pnpm-path-resume-executor.md`
9. `docs/b7-r1-e4-r1-pnpm-path-resume-running.md`
10. `docs/p4-b7-r1-e4-r1-blocked-coordinator-review.md`
11. `apps/desktop/b7-r1-e4-r1-source.sha256`
12. `docs/coordination/snapshots/p4-d14-start.sha256`
13. 外部只读文件 `<task-root>/r1-pnpm-resume/r1-controller.ps1`
14. 外部只读文件 `<task-root>/r1-pnpm-resume/r0-forge-preflight.mjs`
15. 外部只读文件 `<task-root>/r1-pnpm-resume/forge-pnpm-bin/pnpm.cmd`
16. 外部只读文件 `<task-root>/r1-pnpm-resume/evidence/r0/failure-summary.json`
17. 本任务卡

`<task-root>` 是 E4 运行说明中已经固定的 C 盘任务根。项目文档不得写入用户名、用户目录、动态端口、token、nonce、真实账户或个人财务数据。

开始时逐行复算 D14 固定输入，登记接单、当前步骤、最近进展、下一检查点和等待对象。最新 control 与本任务冲突时以 control 为准。

## 固定事实

- E4 阶段 A 全过；E4 唯一 package 在 Forge system check 的裸 `pnpm` 命中失效用户 shim，尚未进入 Packager/Vite。
- 总控已经用 task-owned `pnpm.cmd` 和 E4 安装的真实 Forge `spawnPackageManager` 取得 version `12.7.0`、hoist/public-hoist `undefined`、node-linker `hoisted`、退出 0。
- E4-R1 固定输入与现场全部匹配；R0 driver 创建完成，但首次控制会话没有产生有效预检结果。
- `r1-controller.ps1` 的 `Run-Captured` 形参名为 `$Args`，函数体用 `@Args` 展开；`$Args` 是 PowerShell 自动变量，实际命令实参为空。
- `where.exe`、四个 pnpm 调用和 Node probe 的原始输出均符合“没有收到参数”；Forge log 与 `r0-result.json` 不存在。
- package 预算仍为 0/1；R2、P1、P2 均未运行；产品、依赖、lock、PATH 与系统 pnpm没有变化。
- 本轮缺陷为 `P4-E4-R1-R0-DRIVER-ARGS-001`，当前没有产品缺陷证据。
- 用户已决定：本次失败后不再立即派发普通重试，先由 GPT-6 Astra 裁定或接管解决路线。

## 必须回答的问题

### 1. 根因与 PowerShell 语义

准确解释：

- `$Args` 作为 PowerShell 自动变量的语义；
- 为什么把函数参数命名为 `$Args` 会导致当前调用链中的实参丢失；
- `@Args` 是数组 splatting 还是自动变量展开，当前脚本到底执行了什么；
- 为什么这能同时解释 `where`、pnpm 和 Node 三类症状；
- 是否还存在位置参数绑定、数组展平、字符串 quoting、`.cmd` 解析或 `$LASTEXITCODE` 的第二个潜在缺陷。

给出事实、推断和待验证项的分级，不要只写“把变量改名即可”。

### 2. 最小可靠实现

比较并裁定至少两种方案：

1. 保留 call operator，将参数名改为 `$CommandArgs`，用 `& $File @CommandArgs`；
2. 使用 `System.Diagnostics.ProcessStartInfo`/`ArgumentList` 逐项传参并捕获 stdout、stderr、exit code。

对每种方案说明：

- 对 `.exe`、无扩展命令名和 Windows `.cmd` shim 的行为；
- quoting、空格、Unicode 和路径参数风险；
- stdout/stderr 捕获是否可能死锁；
- `$LASTEXITCODE` 是否可靠；
- 如何实现硬超时与按 PID/descendant 清理；
- 是否会改变 Forge 后续实际使用的命令解析语义。

选择一个最小推荐方案，并给出可以由执行智能体直接复制的完整 `Run-Captured` 实现。代码必须使用非自动变量名、明确参数类型、明确返回结构，并保留真实退出码。不要提供多个模糊候选让执行智能体现场自由选择。

### 3. 参数传递的自证证据

为下一次 R0-only 设计一个不依赖人工观察的证据合同。至少包括：

- 每个进程启动前记录安全的 executable label、argument count 和参数语义标签；
- 不在项目报告中保存个人绝对路径或秘密；
- `where pnpm` 必须精确收到一个 pattern；
- pnpm version 必须精确收到一个参数；
- 三个 config 查询必须分别收到四个参数；
- Node probe 必须精确收到 probe、package-manager module、desktop root 三个参数；
- 每个命令必须保存独立 stdout、stderr、exit code、是否超时和摘要；
- Forge JSON 只能在 exit 0 且 schema 严格匹配时解析；
- 任一参数计数或结果不符时，不产生 ready marker。

说明如何避免把无参数帮助输出误判为有效结果。

### 4. R0-only 恢复任务边界

下一任务必须只执行 R0，不得同任务进入 package。请冻结：

- 使用新的 evidence 子目录，不覆盖 E4 或 E4-R1 失败现场；
- 复算 D14 后的新起点、E4/R1 source、旧 evidence、工具、lock、node_modules、Electron dist、污染 marker；
- 在新的单一持续会话构造一次进程级 PATH；
- 重建或复制 shim 前如何核对其内容、摘要和目标 pnpm native；
- 六项预检、Forge 同构结果和不变性核对的精确顺序；
- 每项的硬超时、最大进程启动数、失败停止和 owned process 收口；
- 通过时只交付 `R0_READY_PACKAGE_0_OF_1` evidence，不运行 package；
- 失败时如何区分 driver、环境、pnpm 和 Forge 缺陷。

明确回答：R0-only 通过以后，是否可以由总控另立 package-only 任务；哪些证据缺一不可。

### 5. 是否需要持久修改 wrapper

审查 `apps/desktop/scripts/package-desktop.mjs` 的边界，但保持只读。回答：

- 当前已知证据是否足以要求 wrapper 永久构造 pnpm PATH；
- task-owned PATH 只作为验收环境是否会掩盖真实开发者体验；
- 应在什么后续触发条件下，把 pnpm 解析固定逻辑变成仓库工具链实现；
- 在当前 R0 恢复前是否应修改产品或 wrapper。

### 6. 工程流程复盘

简短说明为什么连续的“一次运行即停止”虽然保留了首失败证据，却也让简单的 driver 缺陷产生过多任务轮次。给出以后区分以下两类错误的建议：

- 被测产品/环境 cell 的真实失败；
- 在进入 cell 前由任务 runner/evidence driver 自己造成的 harness setup failure。

建议必须保持证据诚实，但避免每次无副作用的 harness setup error 都升级为完整项目返修。

## 资料要求

以 Microsoft PowerShell 官方文档为主要依据，至少核对：

- about Automatic Variables 中 `$Args`；
- about Splatting；
- about Operators 中 call operator；
- `System.Diagnostics.ProcessStartInfo.ArgumentList` 和重定向/异步读取要求。

每个关键 PowerShell 结论附近提供官方链接。不得以博客片段替代语言语义依据。

## 文件边界

只允许修改：

- `docs/phase-4-d14-r0-driver-recovery-advice.md`；
- `docs/coordination/agents/technical-adviser.md`。

禁止修改或运行：

- 外部 C 盘 E4/E4-R1 evidence、driver、shim 或 probe；
- 任何产品、测试、Forge、wrapper、staging、依赖、lock、manifest、snapshot；
- control、overview、矩阵、运行报告和其他角色文件；
- pnpm、Node probe、Forge package、Electron、Maris、Python sidecar、Docker、OpenClaw、微信或 DeepSeek；
- 用户/系统 PATH、系统 pnpm、注册表、安全软件或系统设置；
- Git 写操作。

允许对项目文件和外部 evidence 做只读检查与摘要复算。不得创建 D14-R1、执行 Prompt、接口冻结或 P4-C12。

## 交付要求

在 `docs/phase-4-d14-r0-driver-recovery-advice.md` 交付：

1. 一页结论；
2. 根因与症状映射；
3. 两种实现比较和唯一推荐；
4. 完整、可复制的 `Run-Captured` 实现；
5. 六项参数与结果 evidence 合同；
6. R0-only 执行顺序、超时、进程和停止条件；
7. wrapper 是否持久修改的裁定；
8. harness setup failure 与真实 cell failure 的流程改进；
9. `P4-D14-F01...` 推荐冻结项；
10. 仍需总控决定的问题。

完成后提交 `review / finished` 并停止。不得运行修复、package 或后续阶段；最终执行授权由头脑风暴总控作出。
