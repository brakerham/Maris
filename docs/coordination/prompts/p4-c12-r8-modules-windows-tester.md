# P4-C12-R8-MODULES：模块就绪独立复验与剩余 Windows 验收

## 负责人、结论边界与输入

你是既有测试智能体，本任务唯一负责人。执行方R6已停止，新模块同步实现和新包可供独立验证。先验模块同步及这次改动影响的局部行为，通过后在同一任务继续Windows剩余条件；不等待技术顾问或新派发。执行方150开发节点、22项EXE门禁不算独立通过。旧R7 W1现场原因仍unverified，不用新成功倒写旧DOM或关闭原因。

按AGENTS依次读取README、project-coordination、coordination/README、最新control、本人tester、本卡，再读：

- [总控交付核对](../../p4-b7-r6-module-ready-coordinator-review.md)、[R6执行方运行说明](../../b7-r6-module-ready-running.md)、[R6实现合同](p4-b7-r6-module-ready-executor.md)。
- [R7报告](../../testing/phase-4-c12-r7-recovery-windows-report.md)、[R7任务](p4-c12-r7-recovery-tester.md)、R7 Windows首次result/journal及windows-plan；只读复用，不启动旧目标。
- IF-003/004/005、[原120项矩阵](../../testing/phase-4-modular-agent-host-test-matrix.md)、[人工清单](../../testing/phase-4-c12-manual-checklist.md)及[R4 Windows合同](p4-c12-r4-lazy-windows-tester.md)；原验收要求保持，执行顺序、输入和预算以本卡为准。
- [R8固定起点](../snapshots/p4-c12-r8-modules-start.sha256)：仓库根、原字节、完整POSIX路径排序、UTF8无BOM、`path<TAB>sha256<LF>`，不含自身。接单前全部匹配、staged=0，登记接单及下一检查点。

旧冷入口B、R7恢复5组及注册8项的历史通过证据保留。它们对应旧输入；下述最小邻接保护用于确认新改动没有破坏相关要求，不重跑旧B、原故障节点、完整R7五组或D15/D16。旧失败与首次证据不可覆盖。

## 精确写入边界与固定环境

仓库可写仅：

1. 新`tests/independent/desktop/r8-modules-*`，例如`r8-modules-readiness.test.tsx`、`r8-modules-remaining.test.ts`及本轮配置/setup/reporter/controller/Windows helper；文件名在`modules`后必须有连字符。
2. 新`tests/independent/desktop/evidence/r8-modules/**`。
3. 新`docs/testing/phase-4-c12-r8-modules-windows-report.md`和本人`docs/coordination/agents/tester.md`。
4. 旧C12主报告和人工清单仅追加；矩阵仅更新P4-B实际状态/证据备注，120个ID、12列、原预期和A/C/D保持。

所有产品/开发测试、旧独立测试/结果、依赖/lock/构建配置、control/overview/snapshot/其他角色只读。无Git写权限。不得为测试增加业务模块、IPC、启动开关、修改asar或开启production inspect fuse。

受验新根固定为`C:/MarisModulesR6/R6-20261013-002100`，新EXE为其`workspace/apps/desktop/out/Maris-win32-x64/Maris.exe`。旧R5仅历史参考，不运行。开工及结束核对以下输入；仓库当前字节以R8新起点为准。R6交付后由总控改变的README、project-coordination、control、overview、brainstorm五项有明确来源，复算旧814清单时作为列举的协调差异，其他原项必须匹配；外部813构建副本则全部保持原字节，不回写新协调文档：

| 输入 | 绑定路径或SHA-256 |
| --- | --- |
| R6交付source 814项 | `apps/desktop/b7-r6-module-ready-source.sha256`，`74c6df4829b2f9ce8b0de2b84b748f14cc3dec520ceab234b91113d3a269a68e` |
| 813项实际构建源码 | 新根`evidence/static/workspace-source.sha256`，`05677054bf73b1a40c60a844f7cad99cc2654bf638ea3798a2081d04212851b4`；基准新根`workspace` |
| 140项产物 | `evidence/static/out-manifest-v4.tsv`，`ebb3521d71bb45d03b692dc0eacda52db540bd722e1aee414c9c025211a28694`；基准包根 |
| 67项Python资源 | `evidence/static/python-resources-v4.tsv`，`324845f07f050f2b90e3c1e0b89b6598c8748aca549f8f848b600d5a2a0da5d1`；基准包内resources |
| EXE / asar | `4ef5bce604fc61fc2b815300edee8a29ab593083d308e849445c6c97235c5f1e` / `5eb153002f4c48ce704f1d0f90b3bf441d5edf3799ea5fe4428f706aee7c69db` |
| 12443项冻结依赖 | 新根`evidence/inputs/node-modules-final.sha256`，`15f5613ce7744083a81c05c68ab06e06b6aa0b6e30f0c9c98ed933d87899e04c`；基准`workspace/node_modules` |
| 73项dist | 新根`evidence/inputs/electron-dist-final.sha256`，`ffb4b389d5c454ca139cb6384f5ebb3d20633cf000960a8aa1b6c1794c9ebf8f`；基准`workspace/node_modules/electron/dist` |
| lock | `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |

只读使用固定Node24.21.0、pnpm12.7.0、Electron44.4.5、Playwright1.63.0及已有Python。jsdom30.1.1沿用R6/R7已验证原生createRequire入口；真实React/ReactDOM/Router来自同一固定物理依赖根。不安装/下载/重新audit/改永久PATH，不运行build/package或创建新包。

新虚拟工作根`C:/MarisC12/C12-R8-MODULES-<时间戳>`。测试工具、cache、profile和虚拟DB均只写本轮自有根；不得把新测试/缓存写入固定R6环境。若需普通副本，先验证解析绝对边界与无reparse，再只物化所需工具，不用junction、不改旧来源。仓库外原始秘密/端点/加密profile留在受限自有根，仓库只保存脱敏证据。

## 第一阶段：独立模块同步与最小邻接保护

根据公开行为独立设计，不复制18个执行方节点或只检查新内部计数器。使用真实DesktopApp、compileRegistry、React Router和Shell；外围bridge和可信虚拟页面loader可控。测试前核对实际main仍装配该DesktopApp。保留StrictMode，至少对关键启动/通知场景另覆盖普通挂载；不导入生产main重做旧冷B。

必须取得以下行为证据，可合并同一生命周期中的相关条件，不把比较数冒充唯一测试节点：

- 明确先返回空列表，再模拟后台认证就绪、模块完成读取；字段相同的前后runtime通知也能使真实页面和导航出现。已就绪再挂载也正确；不得手动刷新/重新挂载/recover来促成首次成功。
- 初始快照晚到、模块请求内同步通知、突发通知和在途旧回包：新值不被旧值覆盖，读取有界，最后有效列表实际显示。事件结束后不自动轮询；卸载/StrictMode旧effect完成不写状态，订阅清理可观察。
- 初始或后续读取拒绝安全处理，raw错误不进DOM/console，无unhandled rejection；已有可用页面不因离线观察被清空。
- 内容等价的新Host数组、无关Host条目及同值runtime通知不重建路由或隐式加载。固定观察点记录加载基线，通知/设置/runtime操作后仍相等，不等它增长后重取基线。
- 同集合失败页面保持局部安全错误、Shell/导航/Agent，通知不自动retry；明确点击一次retry新增恰好一次loader并实际恢复。沿用状态/订阅、无额外auth/recover/provider/outbox/财务写入的真实计数断言。初始Strict加载数不预填为1，以固定正整数基线与明确增量判断。
- 真正模块交集变化可用：缺失/禁用/不兼容/未知不导航或预载，合法新模块出现；当前显示模块被移除后旧内容消失，Shell、导航、Agent仍在。健康/设置路由在同集合刷新后、主题/隐私保持。
- 邻接保护覆盖旧在途页面结果在路由集合变化后不能重新显示已移除内容；局部render错误仍有安全边界。仅检查受本次router实例/Provider改动影响的交互，不重跑完整R7五组。

在同一worker中直接记录稳定断言ID、操作、operator、安全expected/actual、耗时及enter/terminal。UI存在/count/visible分别采样；未知写unknown，不把读取异常写成0/false。失败后停止新的改变状态动作，但可对已到达状态收齐只读安全断言，然后嵌套finally卸载/退订/恢复console与DOM。

独立模块suite一次正式运行；必要剩余公开缺口可另编本轮suite一次运行。明确列节点ID/原合同/已有证据/新增断言，不用试跑替代首次。准备阶段的语法/配置静态检查和同worker记录器虚拟标量自检不计业务通过，不另外搭观察框架或Job进程数实验。

沿用60秒原生初始化上限、每个测试正文最多15秒（单次UI观察仍最多5秒）、finally清理最多5秒；每个suite整CLI最多300秒。多节点不是旧单节点的10秒总预算，不继承不相容的旧总时限。控制器记录阶段，日志即时落盘，不在最后统一写；进程数不设固定2/3上限。

第一阶段通过后，仅一次必要开发兼容：module-readiness18、lazy8、Shell1、composition1，共28项分列；不重复完整150、registry或Python/P0～P3/Host。若节点数变化，先核对固定输入，不静默忽略。任何实际门禁失败保留首次、停止扩展；不能改产品或降低断言。

## 第二阶段：固定新包的剩余 Windows 条件

第一阶段及相关兼容通过后，同任务继续。先按[R7的24项缺口](../../testing/phase-4-c12-r7-recovery-windows-report.md#24项增量映射)和`windows-plan.json`建立本轮覆盖/启动表，替换为新包与新根。旧静态/独立证据输入无关部分只读复用；UI-03/04等尚缺公开条件可补独立静态/虚拟输入测试，禁止改受验产品/生成物或重新编译受验包来证明漂移。

本轮产品最多8次有计划启动，每次120秒；辅助safeStorage最多4次，各60秒。单实例第二次启动计入8次，辅助不得借此启动产品main。预算是上限，不为用满而重复冒烟；先列每次新增覆盖、共享虚拟profile关系和退出入口。每次目标/外部操作前重读control。

1. 新W1从真实managed/认证/canonical daily模块与**真实页面**开始，分别记录`#daily-title`、Shell、导航、Agent的exists/count/visible、白名单hash和readyState。后端通过不是页面通过；每次就绪观察5秒，终点保留安全取样或具体读取阶段错误。继续窄bridge/隔离、CSP/导航/IPC、副作用与隐私、虚拟草稿同ID、主题/隐私、一次recover及正常退出等未完成门禁。
2. 使用本轮同一虚拟owner/profile的后续启动，验证实际会话/设置/同ID持久化；并安排单实例第二次启动、关闭hide/ask/cancel/quit和Tray。自然exit或PID归零不能代替真实Tray、默认关闭提示或会话不丢失；固定E2E抑制的行为必须保留未验证。
3. 条件具备时继续原生老化提示：辅助只对本轮虚拟fixture加密seed/read/count/digest；不读旧profile或改变系统时钟。仅通过限定owned PID/标题/按钮的UI Automation操作，验证默认保留/取消/关闭及明确删除后的有限持久化；不得全局坐标点击其他程序。
4. 其他原监督/安全条件按已批准的虚拟owned后端/adapter与固定接口覆盖，不接管用户手工服务，不向真实provider写入。未知安全输入/nonce/token只用本轮虚拟值，保留安全比较，不入库正文。

产品只用Node child_process.spawn(shell:false)启动固定EXE，Playwright仅loopback动态CDP附加；禁止Electron launcher/app.asar路线、PID提升猜测、改fuses或使用test-only产品注入。owned树以固定路径、创建句柄/时间、父子关系和本轮profile核实；无按进程名批量结束。退出采用该场景真实业务入口，runner硬限及失败定向清理保留；普通退出与强制清理单列。

真实chunk故障只允许本轮owned页面/会话上，限定实际chunk请求的临时CDP故障注入；须取得请求命中、真实失败、Shell/会话保持、撤销注入后明确retry成功。不得改asar/resources、删除chunk、导入另一假页面冒充产物。若file/asar/CDP/缓存使正确注入不可能，先记录具体限制，保留该条件unverified，不盲目加启动。

**不具备工具或设备条件不等于已观测到产品失败。** 已明确不支持的chunk或人工设备条件只阻塞对应条件；资源安全收口后，可继续无依赖的其他计划场景，不要求再开一个“只观察”任务。业务断言真的失败、来源完整仍行为不符或安全/所有权/清理问题，则按停止条款停止扩大，不通过分类调整绕过失败。

真实注销/重启、修改启动项、OS主题、多屏/拔屏/分辨率变化、请求用户立即点击均未授权。只更新单步人工清单和前置条件，不操作用户设备。没有这些条件时保留blocked/not_run，不删预期，不把自动化代理结果写成实机通过。

## 首次证据、有限更正与交付

目标开始前且有明确证据的无副作用工具错误可在本任务定向更正一次，保留首次源码/输出并换新attempt；未知初始化超时或产品已开始后的失败不得修后重跑。源码、配置和记录器在对应正式运行前冻结，误读文件名/汇总错误可只读补证，不重启目标。event和details.stage分别保存，不能覆盖首错ID。安全错误类型之外必须保留具体比较值类别，避免只剩AssertionError。

新P0/P1、秘密泄漏、不受控弹窗、unknown ownership、无法收口或同一环境问题连续两检查点无新证据时停止扩大。逐项登记已执行/失败/blocked/not_run及预算，已登记root/worker分别核对退出，拿不到子退出码写unknown，不用父退出码替代；全系统枚举限制不冒充全树零残留。

交增量报告，列模块同步新独立结果、窄邻接保护、28项开发兼容、实际Windows/辅助启动数及逐场景首错/样本/退出，旧证据复用关系、原24项本次状态与剩余缺口。原预期链接旧报告，不复制全部历史或所有旧清单。首次红灯、warning、工具修正和权限限制准确保留。

缺陷逻辑、完整UI-02与P4-B分层提出建议，不预设必须维持0passed，也不能为了出结果将未执行条件判passed。只有整项全部原要求有独立证据才更新passed；未完成的Windows chunk/session等不能用执行方22门禁代签。总控作最终关闭和complete决定。

接单/里程碑/长操作检查点/阻塞/交付更新本人日志；有控制时至少10分钟心跳，中断不伪造持续工作。最终复算新起点与所有旧材料，仅列授权差异；新R6输入只读不变，保留虚拟profile和产物，仅清理验证过绝对边界/无reparse的本轮临时项。交付review/finished或blocked/finished后停止，不自行启动执行方/顾问/P4-C/D。前端参考图、模型及token提醒由总控在真实界面阶段触发。
