# P4-C12-R4-R1：可观察的故障复验及原R4续跑

## 角色、输入与边界

你是既有测试智能体，唯一负责人。当前不是产品返修：R4只证明原节点未观测到alert，没有证明故障命中。旧LAZY-001未关闭，UI-02/P4-B不预写通过。执行智能体与技术顾问停止。

按AGENTS重新读取README、project-coordination、coordination/README、最新control、自己的tester和本任务；再读R4任务/报告/首次log/JSON、原r3-remaining.test.tsx、R5生产main/module-routes/Shell、[总控核对](../../p4-c12-r4-observation-blocked-coordinator-review.md)。登记接单、当前步骤和检查点。

权威起点：`docs/coordination/snapshots/p4-c12-r4-r1-start.sha256`，逐项复算，staged=0。旧393起点与R4资料保留；新清单覆盖已交付材料与总控更新，不能用旧协调摘要误报产品漂移。

固定包、普通依赖/工具及EXE/asar/lock摘要沿用原R4，不安装、构建、打包或修改系统环境。R5受验根为`C:\MarisLazyR5\R5-20261002-222300`；旧源码/工具/依赖/包/profile/evidence只读。

## 新增写入范围

- 仅新增`tests/independent/desktop/r4-r1-*`测试/配置/审计/runner及`evidence/r4-r1/**`。
- 新报告`docs/testing/phase-4-c12-r4-r1-observation-windows-report.md`。
- 原C12主报告、人工清单只追加；矩阵只更新P4-B实际状态/证据备注，120ID/前11列原预期/A64 passed/C20与D12 not_run保持。
- 自己的tester日志。

全部旧public/r1/r2/r3/r4测试、配置、报告和证据不可改。生产代码、开发测试、依赖/lock/生成物、package/Forge/migration/冻结/control/overview/总控snapshot和其他角色不可改。原R4-R1故障观察通过不能称旧R4首次失败记录变成passed。

## 一次可观察的生产入口复验

先只读确认新增配置加载的是当前仓库生产main和R5普通依赖，React/Router单实例、mock规范路径、原页面端口、Host虚拟摘要与真实contribution相符。不要使用替代Router/Shell或绕过Host intersection。

在新增测试中保留原r3节点的真实入口启动、原DailyFinancePage模块mock及四条业务断言。可将mock factory增加`vi.hoisted`计数/时刻回执后抛出固定虚拟错误；不修改生产代码，也不通过另一条无关throw模拟它已触发。回执只包含虚拟阶段/计数，不记录原始私密错误。

明确记录bridge runtime/modules调用、mock factory命中、当前hash、公开DOM安全状态、错误提示出现及清理完成。VirtualConsole的安全错误/未处理拒绝需记录，不能把所有异常静默丢弃。不得记录token、原始URL/路径、真实profile或正文。

条件等待上限5秒，测试总时限上限10秒：异步轮询/DOM观察与React act正确配合，看到预期错误提示后才检查隔离；不能固定睡5秒便宣布完成，也不能把观察等待包进一个永远不结束的act。原200ms不足是待验证假设，不预设为根因。

必须保留四条原业务要求：alert包含“页面暂时无法打开”；main.shell存在；模块导航存在；统一Agent面板存在。新增前置条件为mock factory真实命中；只看到Shell存在不算错误后的隔离。记录是否超过原200ms观察窗口，实际时间只用来诊断，不作放宽验收要求。

新增节点ID为`R4-R1-UI-02-OBSERVED-FAILURE`，仅实际执行一次，首次log/JSON另存。结束时卸载真实root、清理订阅/DOM/global与自有测试会话；不能只关闭jsdom留活动异步工作。

结果分类：

1. mock未命中：给出Host摘要/公开route/路径接线/等待阶段的实际记录，判定故障前置条件未建立，产品结论unverified；不盲目延长时限或启动Windows。
2. mock命中但5秒内alert未出现，或原四条断言失败：保留实际错误分支证据，区分观察未完成与可复现产品故障；不得直接宣布通过，停止扩大并交总控。
3. mock命中且四条原业务断言通过：新增可观察复验通过，原R4失败仍保留，说明观察方式变化和证据支持的原因范围。继续下述独立边界，不能单凭它宣布整个UI-02完成。

目标前无副作用的新增配置/语法/记录映射错误可一次修正并保留首次错误。目标已运行的行为结果不可修正重跑覆盖。不要先增加一套synthetic driver或新进程计数预算。

## 原R4后续在同一任务继续

上述门禁通过后，沿用原R4全部独立恢复要求：实际DesktopApp/Router/Shell/注册器，只有bridge和可信页面loader为虚拟端口；瞬时/持续失败、显式重试、健康页面/settings切换、在途重复点击与离开、render错误、主题/隐私/runtime/订阅保持和无额外auth/recover/provider/outbox写入。新主入口故障复验与可控loader恢复证据分列，不能只用helper端口通过替代生产入口。

独立测试自己设计，不复制开发八项；必要相邻Shell/composition及新增lazy开发八项可一次兼容复跑单列。旧成功27节点、outbox42、setting/path关闭证据沿用，未受影响registry52、完整132、Python/P0～P3/Host全量不跑。

通过后接续原R4未执行公开行为与Windows，所有旧完整24项条件保持。新前缀/证据目录为r4-r1；新虚拟外部根为`C:\MarisC12\C12-R4-R1-<时间戳>`，不读取旧或个人profile。

本轮产品最多8次有计划启动、各<=120秒；辅助safeStorage虚拟fixture最多4次、各<=60秒。预算无需用满。仅Node spawn(shell:false)直接固定EXE，Playwright只CDP观察；不_electron.launch、不PID提升、不修改production fuse。owned路径/创建时间/profile精确归属、零遗留收口；不全局结束同名进程。

Windows真实chunk故障需要实际请求注入命中与恢复证据，不改EXE/asar/resources/生产代码；安全注入不可控时记录具体unverified，不以jsdom/正常smoke替代。原生过期提示、Tray、普通closePolicy及会话持久化按原R4取证。未授权的OS注销/重启、启动项/多屏/系统主题操作只准备人工清单，不要求用户现在操作。

## 停止与交付

新真实P0/P1、泄密、失控弹窗、未知所有权、无法收口、同问题两检查点无新输出时停止扩大；保留首次失败与已通过证据，不重开失败任务以洗掉结果。故障前置条件未建立不会伪装成产品通过/失败。

报告新增观察节点、原四条断言、故障命中/终态证据、独立与兼容分列、24项完整映射/未覆盖条件、启动/注入次数、资源状态和起终摘要。jsdom、正常Windows与真实故障证据分开。缺陷关闭建议不等于UI-02整项或P4-B接受。

按AGENTS记录接单、里程碑、阻塞、交付及十分钟心跳。外部操作前重读control；不Docker/PG/OpenClaw/微信/DeepSeek、provider或Git写入、不重复V002。结束为review/finished或blocked/finished后停止，不创建下个任务；最终裁定属于总控。
