# P4-C12-R11-R1-WINDOWS：只读观察续接及剩余 Windows 验收

## 身份、当前检查点与不重复范围

你是既有 Tester，本任务唯一负责人。先按 AGENTS 读取 README、project-coordination、coordination/README、最新 control、本人 tester、本卡，再读 [R11 总控裁定](../../p4-c12-r11-origin-observer-coordinator-review.md)、[R11 报告](../../testing/phase-4-c12-r11-origin-settings-windows-report.md)、[当前观察回执](../diagnostics/p4-c12-r11-observer/readability.json)、IF-003/004/005、原矩阵及人工清单。旧 R11 已停止，不能在旧目录修后续跑。

R11 的 41 个独立节点/321 比较及四文件109兼容已通过，IPC-ORIGIN-001已限定关闭；本轮不运行它们。SETTINGS-001缺原W2真实首样，后续Windows仍未完成。本轮从**产品启动前只读观察检查**继续，不重跑H1/W1、旧退出/模块/冷入口/恢复集合或执行方S1/S2，不重新构建。

所有获准门禁通过后在同一任务继续下一场景，不逐步另派任务。最终只提交review/finished或blocked/finished，总控决定接受；Executor/顾问停止。

## 固定输入和精确文件边界

逐项复算[新固定起点](../snapshots/p4-c12-r11-r1-windows-start.sha256)：有序唯一path、真实TAB、UTF-8无BOM、LF，不含自身；全匹配且staged=0才接单。本人接单后日志单列，其他角色不得为旧任务更新日志。R11的110交付、11工具、93证据、49正式来源、90首次材料、50源码归档按各自实际基准根核对；不要把相对证据路径一律按仓库根解析。

唯一受验包仍为 `C:/MarisIpcR9/R9-20261101-161412/workspace/apps/desktop/out/Maris-win32-x64/Maris.exe`。固定R9 closeout及构建1432/产物140/资源67清单、EXE/asar/lock、工具版本、实际依赖入口与基准根沿用[旧R11卡“固定输入”](p4-c12-r11-origin-settings-windows-tester.md#固定输入)，逐项核对新包及实际用到的工具入口。引用已验证完整依赖审计，不再次安装/全扫每个旧阶段。不得因包字节相同换回旧R8路径。

仅允许新增 `tests/independent/desktop/r11-r1-windows-*` 工具/配置、`tests/independent/desktop/evidence/r11-r1-windows/**`、`docs/testing/phase-4-c12-r11-r1-windows-report.md`；更新本人tester。C12主报告/人工清单仅追加；矩阵仅B证据和有充分证据的状态，120 ID、12列、原预期及A/C/D保持。产品、执行方测试、旧独立源码/证据、包、依赖、control/overview/快照和其他角色均只读，无Git写权限。

新外部根仅 `C:/MarisC12/C12-R11-R1-WINDOWS-<时间戳>`；创建前检查绝对边界、未存在、无reparse，普通复制不使用junction。复用已有成功的异步观察、路径/日期身份及收尾逻辑，只做本卡必要适配，不另建进程管理框架。

## 先解决只读观察权限，再启动产品

总控18:10默认查询取得AccessDenied，18:11同一只读查询经标准工具审批成功；这是**新的当前证据**，旧R11 error仍unknown。本轮不为重现拒绝再做默认权限循环。先重读control，使用工具支持的标准审批通道申请必要只读进程、监听、窗口能力核对；若环境默认已具备所需权限，可以实际成功回执证明。不得更改WMI/服务/ACL、安全软件或永久权限，不使用RunAs、不让产品取得管理员权限。

读权限成功不等于目标所有权成功。新观察器在启动目标前一次完成下列实查；既有普通用户启动/观察结构保持。需要审批的观察调用与目标启动分开，不把一整段安装、产品或清理命令混入“只读”申请。审批被拒绝时准确记录动作与原因，停在目标前，不旁路、不将异常转为空集。

1. **进程身份**：有界取得真实库存，验证自身准确PID；后续目标身份仍绑定固定executable、创建时间、父子关系及本轮marker。按实际CIM类型处理日期，不二次字符串解析DateTime。仅排除已核实的本轮观察器/控制器准确PID，不排除一类进程名称。原脚本注释不能替代实际排除逻辑。
2. **只读错误与记录**：每个阶段立即落盘enter/result；安全记录异常类型、HResult、存在时的NativeErrorCode/StatusCode、Category和真实退出值。缺失字段为null/unknown；不输出原始全机命令行、密钥、连接URL或无关路径。查询失败不得等价于“零进程/零监听”。
3. **资源和原生能力**：进程、监听、UIA、Tray分开查询和归类，不因第一项成功全签。正常无匹配须与查询错误区分。UIA或Tray根可读取不等于已有可靠操作适配器；脚本写死false也不等于设备不支持。实际能力、未实现、unknown分开。只操作本轮身份已确认的原生对话框/Tray，其他窗口不触碰。
4. **冻结后进入W2**：核实源profile与固定旧任务没有仍运行的相关进程，保存按范围脱敏的身份结果；只有全部必需身份/资源观察成功，才允许spawn产品。只读能力不足时执行下文明确设备分支；所有权unknown一律不放行。

目标前最多30分钟实际准备、最多3版必要工具更正，审批等待不计。只对改动分支用静态/虚拟数据核对：正反斜杠/日期、精确自身PID排除且不漏外来目标、CIM拒绝、空监听与查询异常、缺失或坏result、双错首错保留、finally释放、比较ID唯一及expected/actual完整。沿用成功工具，不新开普通Node进程夹具，不重跑整个旧自检库。记录每版和第一次结果，冻结本轮实际执行的全部controller/helper/observer/配置/业务输入来源。

每次观察最多8秒且受目标剩余截止约束；进程查询内部超时应小于外层上限。无需在每条查询前重复整个能力试验；实际操作需要工具审批时按具体动作处理。正式目标开始后不再以工具修正重跑已执行场景。

## Windows 顺序和验收口径

以下原W2及剩余Windows合同保持；它们已由总控授权，可在本任务连续执行。本卡前置观察、文件范围和新起点优先于旧R11卡；旧第一阶段/109兼容不再执行。IPC-ORIGIN-001已限定关闭，不能再把它列为本轮待复验目标。SETTINGS-001关闭建议仍要求实际W2首样。

## 第二阶段：原 W2 四条首样，保持同源虚拟资料

原来源 `C:/MarisC12/C12-R9-QUIT-20261016-011200` 的 `profile-main` 和 `continuity.json`，完整库存由 `tests/independent/desktop/evidence/r9-r1/original-profile.tsv` 63项冻结（SHA-256 `575f132e0bc44a949391c9ab7c31747e4e21e58fdb8a344dc29a00e6639ce7ee`）。确认源无运行进程、边界/marker和摘要后普通复制至新根，完整路径/大小/摘要相等；原来源始终只读。不得换用执行方S1/S2 profile、失败W2后的profile或全新owner。报告准确称为“W1同内容虚拟副本续启”。

H1已独立通过，基线来自 `tests/independent/desktop/evidence/r9-r3/helper-H1/native-result.json`（SHA-256 `f6c493c244f18832b0e69e5fa7c45a09108e304bd72fb685951c92252b7a62e3`）。本次不再运行H1；后续H2比较仍必须实际执行，稳定owner摘要不等同于可轮换的refresh token相等。

W2由固定Node直接spawn(shell:false)固定新EXE，Playwright仅connectOverCDP；隔离路径/动态loopback/marker/实际PID身份绑定，禁止退出计时器。settings白名单已成为getSnapshot/update，提前修正新工具期望。**首样前不写设置、不seed、不recover、不刷新**，沿用原副本closePolicy=quit及dark/true。后台和实际daily/Shell/导航/Agent就绪分开观察，同一首次有效页面样本执行原四条比较，ID与预期保持：

| 原断言 | 预期 |
| --- | --- |
| W2-PERSISTED-UI-THEME | dark |
| W2-PERSISTED-UI-PRIVACY | on |
| W2-PERSISTED-THEME-CONTROL | dark |
| W2-PERSISTED-PRIVACY-CONTROL | true |

同时保存安全DOM/可见性/路由样本、首样设置文件摘要、driver写入数。实际UI通过不能只用getSnapshot回包替代。原 draft/request/event ID 及设置持久化要求保持，未覆盖部分交H2读回；不向真实provider提交或产生新财务写入。

## 第三阶段：同任务剩余场景与合法配置

旧脚本 `settings.update({closePolicy:...})` 与当前严格三字段写接口不符，必须在启动前从新工具去除。**只在本轮产品完全退出后**才可预置下表所列虚拟设备字段，校验原schema并记录差异；不改theme/privacy/owner/outbox以促成设置复验。预置证明的是对应配置下的行为，不是用户可通过UI设置closePolicy。

| 顺序 | 授权行为及放行条件 |
| --- | --- |
| W2内的W3 | W2首样和前置全过后，同一新profile启动第二实例一次；身份分别记录，第二实例正常结束、原主实例/Host保持。此后W2正常关窗退出，10秒上限，资源0 |
| H2 | W2/W3通过、产品全退后，同源原生读取与旧H1稳定owner/原草稿/request/event摘要比较。全部通过才seed预先冻结的少量虚拟老化draft/queued及保护对照；不改OS时钟 |
| W4 → H3 | closePolicy仍quit；真实老化原生对话框默认/取消保留，正常退出后H3实际读回数量、正文摘要和请求ID未丢失。窗口可见不等于已确认保留 |
| W5 → H4 | 同一新副本明确选择删除，正常退出后H4只读证明仅确认的过期候选被删，非候选/sending/原continuity保护对照保持；不得只比较密文hash |
| W6 | 目标前产品全退后，仅预置closePolicy=hide_to_tray、closeHintShown=true。核实本轮受管后端身份后按既有合同注入一次失效/显式恢复，观察错误分类、恢复预算和UI保持；正常关主窗应隐藏，毛毛恢复主窗；通过真实本任务Tray退出并验证资源。不得杀外来进程 |
| W7 | W6全退后，仅预置closePolicy=ask_every_time、closeHintShown=false。一次启动内验证首次提示/知道了后隐藏、毛毛恢复、以后询问的取消/隐藏、最后明确退出；原生对话框只操作身份已核实的按钮，普通退出不以强杀替代 |

每个H在spawn前从当前**新产品副本**复制完整Local State到全新helper目录，摘要相等；ready前绑定userData/sessionData，ready后仅核对加密字段与来源一致，不要求无关字段永久逐字节不变。不输出字段值/密钥，不复制helper配置回产品。H2可seed，H3/H4只读；保持R9-R3分段读取/解密/解析与真实退出记录，不加载会repair/write的产品main。旧r9-r3-storage.cjs的runH1/finish硬编码H1七条比较与COUNT=1，禁止只改场景名套用。仅复用其上下文/记录/身份公共逻辑，为H2/H3/H4写有限的比较与seed函数；在目标前工具预算内以虚拟输入检查实际同一函数的基线不符、保护条目和错误分支，再冻结。

真实chunk只可在W6这次已授权启动内、按启动前冻结的实际请求来源临时拦截一次，取得当前有效请求失败与局部安全错误/Shell/导航/Agent保持，再撤销并明确retry。不能改包、删除chunk、假页或额外冷启寻找命中；若静态能力/实际请求证据表明不支持，准确保留unverified，不增加启动。不可在首个有效失败之后靠撤销/再试把失败覆盖为通过。

分别在目标前核实老化提示、关闭对话框、Tray的只读定位/操作能力。若老化提示能力明确不可用，H2仍可只读比较续启基线，但不得seed；W4/H3/W5/H4保留unverified，不启动。H2基线和资源均通过后，仅可继续预先冻结、无依赖的W6 quit恢复分支；不把H4未运行写成通过。UIA/Tray定位只读能力在目标前核实。明确不可用时，W6可提前冻结为保留quit配置、只验证无依赖的后端故障恢复并正常退出；hide/Tray及W7原生场景保留unverified，不换工具盲试。该能力分支及理由必须在W6启动前落盘。未知所有权或操作异常不属于能力缺失，必须停止。自动操作只限本轮窗口/托盘，不要求用户此刻点击或改变系统。

## 预算、停止与交付

| 目标 | 系列已用 | 本次最多新增 | 系列总上限 |
| --- | --- | --- | --- |
| 产品EXE | 2 | 6：W2、W3、W4、W5、W6、W7各一次 | 8，不增加 |
| 原生helper | 3 | 3：H2、H3、H4各一次 | 6，不增加 |
| package/安装/H1 | — | 0 | 禁止 |

产品每场景120秒，业务最多105秒、末段至少15秒收口；W3嵌套在W2截止内，不重置W2时钟。helper60秒，末10秒收口；observer8秒且受剩余时间裁剪；页面5秒，普通关窗10秒。不要求用满额度，不新增W8或失败后续跑。实际spawn即计，审批未执行不计。

正式目标前完成计划/唯一ID/比较数据与安全输出检查后冻结。预期注入的后端离线或chunk拒绝本身不是停止条件，预期公开状态和断言未满足才是失败。正式独立产品比较失败、未知工具/身份/资源错误或非预期异常弹窗，停止后续业务，只做必要身份核实和有界定向收口；新P0/P1提交最小复现，不修改产品。预定的老化/关闭对话框属于被测操作，不按“任何弹窗”误停。安全通过且有直接证据的局部设备能力缺失可继续无依赖已冻结场景，不能把unknown改作unavailable。

首错/后续收口错误分开，真实进程exit/status/signal分别记录；文件缺失/解析错误不逃出finally，不把unknown填0。首次源码/结果不可覆盖。临时清理前核实绝对范围、非reparse和当前control，只删新根本任务临时项；profile/首次材料保留。

报告逐项列原24项完整要求、历史引用/本轮结果/剩余条件，独立与兼容分开统计。IPC-ORIGIN-001已经总控限定关闭，只引用R11的41/321独立证据与109兼容；SEC-04整项仍需逐项证据。SETTINGS-001的关闭建议必须由本轮独立水合及W2证据支持，完整CMP-06/UI-02/P4-B不能凭一个子条件签收。不改矩阵原预期，不要求OS注销/重启、启动项、主题、多屏、安全软件、Docker/OpenClaw/微信/真实provider或个人数据。

接单/实质进展/阻塞/交付更新本人快照，长操作先记检查点，有执行控制时至少10分钟心跳。终点复算固定包/受影响输入、旧profile和首次材料，精确列四共享测试文档授权变化；证据/工具/交付逐项清单避免自引用。全部获准门禁完成交review/finished，否则blocked/finished；最终接受由总控决定，不自动派发后续。真正P4-C前端开始前的参考图和模型分工提醒继续有效。
