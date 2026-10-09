# P4-C12-R7-RECOVERY：明确恢复断言并完成剩余验收

你是既有测试智能体，本任务唯一负责人。R6公开冷入口B首次通过已获总控核对，不重复B、P、A、D15/D16、依赖实验或冷main。当前工作从恢复验收继续：补齐逐断言证据，并按明确合同判断5组恢复场景。不得修改产品、依赖或包。

## 必读、起点与授权路径

按AGENTS读取README、project-coordination、coordination/README、最新control、本人tester和本卡；再读[总控裁定](../../p4-c12-r6-env-recovery-coordinator-review.md)、[R6报告](../../testing/phase-4-c12-r6-env-windows-report.md)、R6恢复源码/首次材料、[R6任务](p4-c12-r6-env-tester.md)及其继承的R5/R4剩余范围。本文优先替换恢复断言、文件命名与取证规则，不重启旧任务。

复算[新固定起点](../snapshots/p4-c12-r7-recovery-start.sha256)，仓库根为基准、原字节、路径排序、UTF8无BOM、`path<TAB>sha256<LF>`。检查staged=0和唯一负责人，记录接单/执行快照。R6交付63项、冷/恢复源码9/5、冷/恢复首次9/7只读复算；不要把总控协调文件与旧角色摘要差异当受验产品漂移。

固定外部环境继续为 `C:\MarisLazyR5\R5-20261002-222300` 的普通依赖与Node24.21.0，版本、EXE/asar/lock及389源码/140产物/67资源清单按R6核对。沿用同一原生createRequire加载jsdom30.1.1 API，只提供真实JSDOM/VirtualConsole引用，真实React/ReactDOM/Router同一物理根。禁止改依赖、安装、下载、审计更新、build/package及系统环境。

可写仅限：新 `tests/independent/desktop/r7-recovery-*`、`tests/independent/desktop/evidence/r7-recovery/**`、新 `docs/testing/phase-4-c12-r7-recovery-windows-report.md`、本人tester；旧C12主报告/人工清单仅追加，矩阵仅P4-B实际备注/状态，120 ID/12列/原预期及A/C/D保持。产品、开发测试、旧测试与证据、旧reporter、顾问材料、control/overview/snapshot/其他角色只读，无Git写权限。

## 在运行前冻结可解释的断言证据

以R6恢复5组操作为起点。先列“原行/比较 → 新稳定ID → 期望/观测表达式 → 正式门禁或仅旧计数对照”的映射，所有比较均列入，包括公共wait/click/safety/stable、设置更新回调和finally。不删减断言；只有下一节明确的两个绝对计数改变判定用途。

- 每个断言有固定ID和组/操作序号。调用前即时写入 `assert_enter`，观测值只采一次；执行相应原比较后写 `assert_pass` 或 `assert_fail`，包含operator、安全expected/actual及elapsed。业务操作也有enter/terminal，避免操作本身异常只剩组号。
- 计数/时长是有限数字；UI存在、Shell同一性、泄漏类别等是布尔；路由/主题/runtime等是预先白名单枚举。DOM元素不序列化，使用present/same布尔；未知值明确unknown且不得当成期望值。不要写任意字符串、Error.message/stack、完整DOM、路径、token、会话或财务正文。
- reporter保留首个正式门禁失败ID、组号和安全比较信息，后续cleanup失败单列，不能覆盖首错。记录器schema必须同步允许新ID/operator/枚举，不可沿用R6仅允许Error名字的字符串白名单导致exit91。日志写失败记取证阻塞，不生成产品通过。
- 在同一worker、产品导入前对记录器做一次纯虚拟标量自检：预设不同数字应保存failed及两个值，布尔passed，禁止字段不写原文。自检不启动产品，不另起CLI/独立实验，不计业务passed。若自检失败，保留首次记录并使用下述前置工具修正规则。
- 只改取证，不装内部Router/RPC观察框架、不包装产品loader或替换Router。新测试、配置/setup/reporter/controller在运行前冻结。不要靠最终catch中的错误类型代替逐断言记录。

## 两个旧计数对照与正式产品门禁

保持R6的StrictMode、空初始hash、实际DesktopApp/compileRegistry/Router/Shell、两个虚拟模块、可信可控loader及bridge；不导入生产main，不挂新真实业务模块，不清缓存或移除StrictMode。

仅两个比较作为单列对照，名称明确为 `legacy_initial_exact_1` 和 `legacy_first_retry_total_2`：原观察点分别计算 `counts.loads === 1`、首次retry后的 `counts.loads === 2`，保存真实数值及对照passed/failed。**旧R6节点仍failed，不能宣称不变原节点通过；这两个对照不当独立测试节点累计。** 不预填实际值为2/3。

正式5组门禁如下；除上述两个计数，其他R6断言均保持：

1. 初始局部错误可见，当前hash、Shell、导航、Agent和安全条件正确。加载数须 `Number.isSafeInteger(value) && value > 0`；记录一次当时数值N0，固定为initialBaseline，在原pause的60ms无操作窗口中继续处理事件，结束N1必须等于N0。不要等待增长停止后重新选更大的基线；发生增长就是本门禁失败。只证明本观察窗口无增长，不外推无限期。所有实际门禁通过后，初始对照即使failed也不阻止进入下一组。
2. 按原顺序设置dark/privacy并发布offline观察，记录状态/订阅基线。**这些操作后、点击retry前，loads仍必须等于组1固定的initialBaseline**；不能重取更大基线掩盖未经许可的加载。点击一次，恢复后loads须严格等于initialBaseline+1，并单列pre/post增量1及真实恢复页面。保留原总数2的对照，但不能用它代替增量门禁。主题/隐私/runtime、Shell身份、订阅和恰好两次设置写入等原检查保持。
3. 持续失败、健康/settings切换、一次明确失败retry及无自动增长，按每个动作前的计数比较原增量；保留原稳定观察。
4. 在途多次点击只增加一次请求，pending按钮状态正确；离开后旧请求完成不能覆盖健康页面或hash，状态/订阅保持。
5. render异常仍局部、安全，明确retry重新loader一次并成功恢复；状态、额外调用和真实清理继续核对。

仅这两个旧绝对计数对照可非阻断。不得看到其他失败后将其改为对照、skip、xfail或调整期望。产品公开/恢复/安全门禁任何失败，停止后续点击/导航/状态改变；对同一已到达状态可收齐剩余只读断言再清理，记录后续组not_run。不要因第一条计数比较抛出而再次丢掉当前UI/安全结果。

这不是假定R6原失败来自计数，也不是允许任意重复调用。新结果只能定位新运行，不能用来补造旧expected/actual。若仅旧计数对照不同且全部正式要求通过，报告为“新恢复合同通过，旧计数对照差异”，原R6失败永久保留；实际缺陷按证据定级。

## 运行预算与后续

恢复目标只有一次挂载的完整生命周期，默认1个CLI/1个fork；不拆成重复挂载来规避场景间状态保持。一个节点分5组，实际到达多少就报告多少，不把组数冒充独立节点数。原生初始化60秒、正文10秒（每次UI条件观察最多5秒）、清理2秒、CLI总体75秒、Vitest函数外层12秒保持；controller独立计时及共享读取、真实owned收口沿用已验证方法。

有明确原因且证据证明DesktopApp/产品模块尚未开始的工具错误，可保留首次文件并在本任务更正一次，最多一个额外CLI；未知超时或目标已经开始的失败不得修后重跑。源码/语法/摘要静态小错正常修正记账，不另造任务。所有收口/日志补读只读，不重启目标。

恢复正式门禁及清理通过后，在本任务继续R6授权的lazy开发8项和必要Shell/composition兼容，各文件一次、单列；随后原24项未完成公开与Windows。旧B/P/A/D16和无关已过集合不重复，不再等待其他角色派发。

Windows使用固定EXE、新虚拟根 `C:\MarisC12\C12-R7-RECOVERY-<时间戳>`，创建/清理前检查绝对边界与无reparse；Node直接spawn(shell:false)，Playwright只CDP附加。产品最多8次各120秒、辅助safeStorage最多4次各60秒，不为用满预算重复smoke；每次外部操作前重读control。其他真实chunk/session/原生老化提示/Tray/关闭/单实例/人工设备条件和禁止事项，完整继承R6/R5/R4未替换的合同。

无OS注销重启、实际启动项/系统主题/多屏设置变更或要求用户点击授权；无真实个人profile/provider/Docker/OpenClaw/微信/V002操作。缺设备条件准确未验证，不拿jsdom或自然退出代替设备验收。

## 交付

交付一份增量报告，列R6已通过部分的只读复用、逐断言映射、两个对照和正式门禁的分列结果、首错ID/expected/actual、各组实际执行/未执行、兼容/设备条件、首次失败/修正及资源限制、起终与交付摘要。原24项完整要求链接旧报告，仅列本次增量与剩余缺口，不重复全文历史。

本轮所有实际首次结果保留。已登记root/worker分别核对，worker退出码拿不到如实unknown，历史完整后代不冒充已核实；不按进程名批量结束程序。P0/P1、泄密、不受控弹窗、unknown ownership或无法收口立即停止扩大；同一问题两检查点无新输出不进入等待循环。

最终交 `review / finished` 或 `blocked / finished`，总控接受后才调整完整UI-02/P4-B结论。不自动创建新任务、启动其他角色或进入P4-C/D；正式前端前参考图/模型/token提醒保持。
