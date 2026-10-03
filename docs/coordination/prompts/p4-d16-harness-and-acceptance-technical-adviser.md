# P4-D16：测试初始化定位与独立验收路线裁定

你是项目既有技术顾问，唯一负责人。用户已授权总控派发本任务，计划在原技术顾问聊天使用 **GPT-6 Astra**；模型由用户在界面选择，不通过 API、账号或密钥操作切换。不接管执行智能体或测试智能体，不创建其他长期角色。

本任务要交付一条可以执行的解决路线：定位冷观察测试在正文前停止的位置，并审查辅助观察 A 是否应继续阻断无包装公开验收 B。不要沿用旧诊断的结论或门禁作为未经审查的前提，也不要只提交“再试一次”或“增大时限”。

## 先恢复上下文与固定输入

依次读取仓库 `AGENTS.md`、[README](../../../README.md)、[项目分工](../../project-coordination.md)、[台账规则](../README.md)、最新 [control](../control.md)、[本人状态](../agents/technical-adviser.md)和本任务。确认 control 将 P4-D16 指定给你，其他角色已停止，再在本人角色文件登记接单及当前执行快照。任何新控制指令优先于本任务。

开始调查前复算 [D16 起点清单](../snapshots/p4-d16-start.sha256)：UTF-8 无 BOM，仓库相对路径排序，每行 `path<TAB>sha256<LF>`。全部匹配后才进入本任务的新实验；不以 CRLF 归一化掩盖实际输入变化。清单不包含自身，也不扫描 `.claude/`、`.pnpm-store/`、依赖、旧虚拟 profile 或个人目录。

必读证据按以下顺序，不要求重读整个总控聊天：

1. [R4-R3 总控核对](../../p4-c12-r4-r3-initialization-coordinator-review.md)、[R4-R3 独立报告](../../testing/phase-4-c12-r4-r3-persistent-import-windows-report.md)、[原 R4-R3 任务](p4-c12-r4-r3-persistent-import-tester.md)。
2. [P 首次 journal](../../../tests/independent/desktop/evidence/r4-r3/injection/worker.journal.jsonl)、[P process](../../../tests/independent/desktop/evidence/r4-r3/injection/process.json)、[A 首次 journal](../../../tests/independent/desktop/evidence/r4-r3/cold-trace/worker.journal.jsonl)、[A process](../../../tests/independent/desktop/evidence/r4-r3/cold-trace/process.json)、[A controller](../../../tests/independent/desktop/evidence/r4-r3/cold-trace/controller.journal.jsonl)。
3. [A 配置](../../../tests/independent/desktop/r4-r3-cold-trace.config.mjs)、[共用配置](../../../tests/independent/desktop/r4-r3-config.mjs)、[A 正文](../../../tests/independent/desktop/r4-r3-cold-trace.test.tsx)、[B 正文](../../../tests/independent/desktop/r4-r3-cold-public.test.tsx)、[setup](../../../tests/independent/desktop/r4-r3-setup.mjs)、[resolver](../../../tests/independent/desktop/r4-r3-resolver.mjs)、[观察门面](../../../tests/independent/desktop/r4-r3-router-facade.mjs)、[原 controller](../../../tests/independent/desktop/r4-r3-run-once.ps1)。
4. [D15-R1 报告](../../phase-4-d15-r1-bootstrap-advice.md)、[D15-R1 首次材料](../diagnostics/p4-d15-r1/delivery.sha256)、[R4-R2 报告](../../testing/phase-4-c12-r4-r2-cold-entry-windows-report.md)。必要时定位引用文件，不重复这些目标。
5. 真实产品 [main](../../../apps/desktop/src/renderer/main.tsx)、[module-routes](../../../apps/desktop/src/renderer/module-routes.tsx)、[Shell](../../../apps/desktop/src/shell/Shell.tsx)和原矩阵 UI-02 要求；只读理解，不执行或修改。

R4-R3 交付清单 52 项普通 SHA-256：`44c36fca1341901a26594c7665cb25ffa81c86e403a322b30da5493f484148cc`。另有 15 项 [冻结探针源码](../../../tests/independent/desktop/evidence/r4-r3/cold-source.sha256)，其相对基准是 `tests/independent/desktop/`。两种清单基准不同，先核对格式，不自行推定。

## 已知事实与尚未解决的问题

| 证据 | 已确认 | 不能据此断言 |
| --- | --- | --- |
| R4-R3 P | 默认内置 loader 两并发加随后一次均安全拒绝，真实 ESM fixture 求值一次；1 节点 passed | 四条界面断言或 Windows 已通过；旧 manual mock 的内部根因已定位 |
| R4-R3 A | 仅 `worker_start`、`journal_ready`；CLI 14,595 ms 到硬限，正文和 main 请求为 0 | 产品吞错、Router 死锁、jsdom 或门面已发生故障 |
| R4-R3 B | 尚未执行，被 A 的先行门禁阻断 | B 也会超时，或 B 一定可以通过 |
| D15-R1 | 显式前置解析真实 Router 后，同一 worker main/act 返回 | 没有前置解析的冷入口已经通过；旧超时根因已经解决 |
| R4-R2 | 取消的第一次加载安全拒绝，第二次有效加载成功，当前路由错误槽为空 | 当前有效请求收到故障；增加等待就能显示错误 |

LAZY-001、UI-02、P4-B 尚未独立关闭。P4-A 64 passed；B 0 passed、1 failed、19 blocked、4 not_run；C/D 32 not_run。执行方 R5 的 132 项开发回归、新包与 19 项 EXE 冒烟是既有自测证据，不能替代独立结论。

## 调查任务与结论要求

**一、解释正文前阶段。** 画出本次 CLI/config/plugin、worker/setup、测试模块收集/转译与依赖求值、正文之间的实际顺序。结合固定版本源代码和原回执，指出已发生、未发生及缺少记录的边界。特别检查是否存在解析/别名循环、同一 React/Router 物理根不一致、观察模块初始化依赖、Vitest 收集与导入等待、原控制器预算分配等候选；用支持证据和反证收窄，不能先指定一个根因再为其找解释。

**二、实际取得最小缺失阶段证据。** 先静态审计，再选择新初始化探针，每次只回答一个具体问题。可用精确的 config/plugin 生命周期记录或新最小测试模块记录依赖加载；不得复制完整旧 A 后再运行，不得请求产品 main、页面 loader 或故障 fixture，不得重做已经通过的 P。如果静态源代码已足以确认问题，明确因果并避免无必要实验；需要实验时，交付真实结果而非未运行建议代码。

**三、审查 A→B 依赖。** 逐条说明四条公开行为断言、故障注入有效性、是否冷入口、辅助 Router 观察分别需要什么证据。比较“保留 A 必经”“公开 B 独立运行、A 只解释失败”和必要的其他最小路线，选定一条，列清风险。不能通过取消四条断言、使用已取消请求、预热 Router、改产品或复用 P 的通过结果降低验收标准。选定路线必须附未来独立节点的最小源码/配置差异、进入条件、事件与退出要求；本任务只形成建议，不启动 B。

**四、给总控可冻结的结论。** 将产品问题、测试基础设施问题、缺失观察和流程设计分别判定。根因已确认时给出精确位置、最小修正与相邻验证；仍未知时给出最后已完成阶段、最小未完成调用/依赖及最多两个仍有证据支持的假设，并交付一条可执行的验收路线。不得把未知自动升级为产品 P1，也不能只建议再建一份同类观察任务。

## 新实验权限与预算

唯一可写范围：

- `docs/phase-4-d16-harness-and-acceptance-advice.md`：正式裁定。
- `docs/coordination/diagnostics/p4-d16/**`：新计划、探针/config/controller、隔离虚拟文件、首次记录与逐文件摘要。
- `docs/coordination/agents/technical-adviser.md`：本人接单、快照、心跳、交接。

新实验仅验证**测试基础设施初始化**，不作产品验收。先写 `probe-plan.md`，列每次实验问题、最少依赖、预期阶段、预算和文件所有权；静态自检后冻结源码。最多 **3 次诊断 CLI 调用**，每次总体硬限 **120 秒**，累计动态运行不超过 **6 分钟**，包含启动与收口。静态语法/摘要检查不计 CLI，但不得执行旧目标。各次必须因新增证据而回答新的问题，不允许三个相同探针盲试。

这里的时限是新基础设施实验的安全上限，不是修改旧 A 的 15 秒结果或 UI 等待条件。启动、收集/依赖求值和正文分别计时；业务测试等待时限由后续总控另行冻结，不由本任务自动延长。不要用任意精确进程数量替代进程所有权与退出核对。

在原生 controller 启动、配置加载与各关键依赖进入/返回处即时追加阶段记录并刷新文件；不能只在 finally 批量写日志。没有回执时保持 unknown。日志只保留安全阶段、ordinal、时长、退出/强制终止和任务 PID 等必要信息，不保存完整模块对象、DOM、raw Error/stack、连接 URL、密钥或个人内容。阶段名必须真实对应实际完成调用，不能在启动前预写成功。

普通的语法、路径基准、字段读取等**新工具自身错误**允许在本任务内更正；保留首次材料，在新 attempt 下冻结修正，不覆盖旧结果。这不是产品重跑授权，且涉及实际 CLI 的调用仍计入 3 次总预算。不要把无副作用工具自误再次升级成完整新返修任务；不得通过改参数或预算绕过已执行目标的实际失败。证据若不能证明产品 main/loader 未开始，立即停止并报告范围越界。

新实验若经任何间接依赖意外触达产品 main、页面 loader 或故障 fixture，立即停止，该次调用仍计入预算，不将间接导入解释为授权。总体硬限包含收口；收口未能确认时保留限制，不能补写正常完成或增大时限。

同一阻塞连续两个检查点没有新证据、达到总预算、输入变化、所有权不明、泄密、无法收口或必须修改禁止范围时，停止动态诊断。仍应完成已有证据分析和可执行路线交付；不要进入等待循环或自动创建 D16-R1。

使用已有工具和依赖只读：`C:\MarisLazyR5\R5-20261002-222300\tools\node\node.exe`、该任务 `workspace\node_modules`。核对 Node 24.21.0、Vitest 5.0.2、Vite 7.3.6、React/DOM 19.3.0、Router 8.4.0、jsdom 30.1.1、TypeScript 6.0.3。新缓存、虚拟 profile 和输出只能进入本任务新目录，不向旧工具/工作区安装、写入或清理；当前命令通道或依赖不可读时记录具体阻塞，不自行下载或修复系统。

controller 记录自己创建的 root 与 worker、启动时间、必要路径身份和父子关系，双流分别捕获，记录真实退出与 deadline。清理仅限已证明属于本任务的进程/目录，不按 Node/Electron 名称批量结束；权限失败后的空列表不是零残留，完整枚举不可得时披露核实范围。停止前重读 control，按授权边界核对固定输入，安全收口后完成报告。

## 必须交付与停止边界

正式报告包含：一段可供用户理解的卡点说明；真实初始化顺序；候选/反证/已确认原因表；每个实验的首次结果与阶段；A/B 依赖裁定；选定的最小验收路线及源码/配置建议；保留的四条断言；建议冻结项和必要待决策项；实际 CLI 数、时限、工具修正、资源与未核实范围。

新探针、原始即时记录、stdout/stderr、安全结果、逐文件摘要和输入不变审计全部交付。摘要说明相对路径基准及 LF 算法；自己的角色日志与新增文件单列。诊断成功或失败都不得记入 P4-B 矩阵 passed。

能交付有证据支持且可冻结的路线，提交 **`review / finished`**；连最小路线仍无法形成则 **`blocked / finished`**，写清唯一缺失条件。根因尚未确认必须在报告中保持 unknown，不能为取得 review 填写推断为事实。技术裁定 review 不表示产品验收通过。

禁止修改 `apps/**`、`src/**`、migrations、执行方测试、`tests/independent/**`、旧首次材料/报告、矩阵、control、overview、snapshot、依赖/lock、系统代理/TUN/PATH/时钟/安全配置、外部 R5 根及个人 profile。禁止启动 Electron/Maris/EXE、Python Host/sidecar、Docker/PostgreSQL、OpenClaw/微信、真实 provider；禁止 build/package、旧 A/B/P/恢复/Windows测试、Git 写操作或要求用户点击窗口。

完成后停止。不要创建接口冻结、后续 Prompt 或调度其他长期角色；总控审阅后负责冻结基础设施方案或另派独立验收。本任务不进入真实前端界面开发；进入 P4-C 前的参考图、模型分工和 token 策略提醒仍由总控触发。
