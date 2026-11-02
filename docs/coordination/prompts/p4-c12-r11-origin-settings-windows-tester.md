# P4-C12-R11-ORIGIN-SETTINGS：来源独立复验、设置与 Windows 续验

## 唯一负责人和本轮目标

你是既有测试智能体。本任务唯一负责人为 Tester；Executor/技术顾问停止。按 AGENTS 读 README、project-coordination、coordination/README、最新 control、本人 tester、本卡，再读 [R9 总控裁定](../../p4-b7-r9-ipc-origin-coordinator-review.md)、[R9 交付](../../b7-r9-ipc-origin-running.md)、[R10 首次报告](../../testing/phase-4-c12-r10-settings-windows-report.md)、[SETTINGS-R8 合同](../../p4-c12-r9-r3-settings-coordinator-review.md#4-本次补充合同settings-r8)、IF-003/004/005、原矩阵/人工清单及下述 Windows 原要求。旧 R10 已停止，不能在其目录修后续跑。

本任务先检验开发来源修复，再完成 R10 未运行的设置节点；前置通过后，同任务直接推进剩余 Windows 条件，不逐场景等待新派发。正式失败保留，不把测试装配或工具未知错误报成产品缺陷。

## 固定输入

按仓库原字节复算[本轮起点](../snapshots/p4-c12-r11-origin-settings-start.sha256)，有序唯一 `path<TAB>sha256<LF>`、UTF-8 无 BOM、不含自身；全部匹配且 staged=0 后登记接单。本人接单后的日志变动单列，其他角色不得为旧卡追加日志。旧失败/未知材料不可改写。

唯一受验包根为 `C:/MarisIpcR9/R9-20261101-161412`，EXE 为其中 `workspace/apps/desktop/out/Maris-win32-x64/Maris.exe`。不得按相同摘要自行换回旧 R8 路径。

| 固定项 | SHA-256 |
| --- | --- |
| R9 closeout.json | `a0dacd4ff8969e4b0045d1238f7635b47221400df00896d3599a2f70c1d2eef4` |
| R9 七文件交付 | `7fe3eb3c3f03f38fa78af110507b27e0d0b032fe95d52d3a1df8a315c6aec9b3` |
| R9 实际构建清单，1432 项 | `492e1a1e9d3c9885a7e7f486c8d6a9c4dc57d83981ef5c053548072d599a3a1a` |
| R9 140 项产物清单 | `8afdd6d3e7c928912b48acedb2d7c1931607e47f32e549a67e92d04eff142409` |
| R9 67 项 Python 资源清单 | `324845f07f050f2b90e3c1e0b89b6598c8748aca549f8f848b600d5a2a0da5d1` |
| EXE | `c80d27c8e31fa60df91065a770e669a553260cf8f883c55a0a7f83f8a430736b` |
| app.asar | `05cdad34ba60b59773eebe671156c96260e69354568b9942da59058641f9c0b2` |
| pnpm-lock.yaml | `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |

实际清单路径/base/列数见固定根 `evidence/closeout.json`。先核对 R9 75 证据、工具/入口、构建/产物/资源；R10 50 交付、8 来源、29 首次按各自基准根核对。R9 七交付中的 executor 保持原交付字节，当前协调变更以本起点为准，不要求 R9 全 source 在总控更新后仍全匹配。

Node24.21.0、pnpm12.7.0、Electron44.4.5、Playwright1.63.0、已有 Python 和同份 jsdom 保持。工具沿用 R9/R8/R8-R2 closeout 绑定的实际入口；完整历史依赖审计引用，核对实际使用入口和 lock，不每条命令全扫/重装。源码级测试须解析到新起点的 security.ts；包测试使用上表新根。配置、工作目录、模块解析来源和缓存根必须在目标前写明。

生产编译裁剪 dev 来源分支，新旧包字节相同已有静态来源证据。不得通过运行生产包声称开发来源已复验，不启动 Vite/开发服务器验证此缺陷，也不追加 package。R8-R2 S1/S2、旧 H1/W1/退出/模块/冷入口/恢复等已通过集合仅引用。

## 文件边界和准备

仅允许新增 `tests/independent/desktop/r11-origin-settings-*` 测试、配置、必要工具副本，`tests/independent/desktop/evidence/r11-origin-settings/**`、`docs/testing/phase-4-c12-r11-origin-settings-windows-report.md`；更新本人 tester。C12 主报告、人工清单仅追加；矩阵仅 B 证据/状态，120 ID、12 列、原预期和 A/C/D 保持。产品、执行方测试、旧独立测试/证据、包/依赖、control/overview/快照和其他角色只读，无 Git 写权限。

新外部根仅 `C:/MarisC12/C12-R11-ORIGIN-SETTINGS-<时间戳>`，先验证绝对边界、未存在、无 reparse；普通复制，不用 junction，缓存不得写旧证据或固定依赖根。机械复用已有成功的独立路径/身份时间/原生上下文/异步收口逻辑，不新建通用进程管理框架，也不直接采用执行方业务判断。

目标前最多 30 分钟实际工具准备、3 版必要更正，审批等待除外；只用虚拟数据和静态检查覆盖改动分支：路径/日期、参数、清单列数、比较 ID 唯一、完整 expected/actual、缺失/损坏结果、首错保留和 finally 无条件释放。无需新 Node 进程夹具或重跑完整旧自检集合。必要只读观察权限先核实，目标不得用作工具自检。阶段即时落盘，不能只留下 AssertionError/operation_error。正式源清单必须包含所有实际测试/fixture/record/setup/config/controller 以及实际产品输入映射，避免沿用 R9 局部阶段清单的缺项。

## 第一阶段：原反例、必要来源边界与未执行设置节点

冻结以下顺序和各节点输入后一次运行；任一有效失败或未知工具错误停止其后节点，不重复旧 I01～I05 整组。

1. **原 R10-I06 一次**：在新只读适配副本中保持原业务正文、同源正对照、同一 sender/mainFrame、断言 ID 和 `ipc_origin_rejected` 预期。保留原 `R10-I06.DIFFERENT_PORT_REJECTED`，失败与通过分别在旧/新证据目录。不得把正对照改成仅测纯谓词，或改 frame 对象让身份拒绝冒充来源拒绝；NO_SAVE 也必须完成。
2. **八个新独立来源节点**，使用 R11-O01～O08，每节点内部的比较 ID 唯一。矩阵输入在运行前冻结，不在失败后追加探索：

| 节点 | 独立要求 |
| --- | --- |
| O01 | 配置有/无尾斜杠、同 origin 不同 path/query/hash 通过；HTTP/HTTPS 主机大小写及显式/默认端口正对照 |
| O02 | 不同端口和 5173/51730 双向拒绝；不同协议、不同主机/后缀、localhost 与 IP 不擅自视为等价 |
| O03 | 配置或请求非法、相对、空、带用户名密码安全拒绝；不泄露原始解析异常 |
| O04 | data/javascript/ftp/blob 与 opaque/null 不因 origin 相等放行；生产原 file/maris 正反对照保持，覆盖合法与非法开发配置 |
| O05 | 真实 validateIpc 的 sender/subframe 优先拒绝，origin 在参数解析之前，可信来源仍严格校验参数，不扩大 getter/update |
| O06 | 真实 main 注册 getter 与至少一个写 handler：同源正对照、错来源拒绝且无设置/Host/outbox/窗口新增副作用；以启动后增量比较 |
| O07 | 真实 companion 两个 handler：只接受自身配置，错误 main 来源拒绝、无打开主窗副作用；可信 openMain 正向及身份/参数保持 |
| O08 | main/companion 相邻端口双向隔离，不能合并两个窗口来源；通过同身份仅改 URL 的正反对照证明拒绝来自来源判断 |

不得复制执行方测试/生产比较函数作为 oracle，不 mock 掉被验的 predicate/validateIpc/handler。可在 R10 fixture 的新副本增加 companion 来源和副作用观测输入，不改变默认原 I06 语义；所有改动列差异。上述八组足以覆盖本次变化，不运行网络探测或生产漏洞扫描。

3. **旧未运行 32 个节点**：R10-I07 及 R10-U01～U31，各首次运行一次，原业务要求/比较保持；只在新文件作记录器/路径/fixture 的机械适配并保留 old→new 映射。I07 验证真实 preload；U01～16 合法组合、U17～24 非法响应、U25～31 等待/拒绝/StrictMode/卸载/通知/空模块/故障页面保护均不得遗漏。真实 DesktopApp/Router/Shell，虚拟外部 bridge，沿用已成功的 native jsdom 装配，不回到正文动态 import jsdom 的旧路线。

本轮独立计划 **41 个唯一节点**：1 原失败复验＋8 新来源＋32 未执行。前五项历史通过不计本轮；名称筛选未选中不是 skip/xfail，不删旧测试来凑计数。可以复用只读原文件并选择节点，或建立保持业务正文的新副本，禁止在导入过程中意外执行旧五节点或写旧 evidence。目标前计划/collector 检查不得运行产品正文；清楚标记未选中和未运行。

第一阶段全通过后，兼容仅一次运行四文件：`security.test.ts`、`ipc.test.ts`、`settings-snapshot.test.ts`、`settings-hydration.test.tsx`，冻结基线 **45＋12＋25＋27＝109**，单列不计独立。旧两文件48已经过时，不再另跑；不跑完整217/退出48或其他旧集合。无 skip/xfail、降断言或改产品。

## 后续 Windows 续验合同

以下原 W2 及剩余场景合同整体沿用；旧 R10 卡仅作历史依据，本卡的新包、新根、源码范围、第一阶段和兼容109优先。每一步全部满足放行条件时在同一任务继续下一步，不自动另立诊断或返修任务。

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

报告逐项列原24项完整要求、历史引用/本轮结果/剩余条件，独立与兼容分开统计。IPC-ORIGIN-001只在原I06和新来源边界独立通过后建议限定关闭，SEC-04整项仍需逐项证据。SETTINGS-001的关闭建议必须由本轮独立水合及W2证据支持，完整CMP-06/UI-02/P4-B不能凭一个子条件签收。不改矩阵原预期，不要求OS注销/重启、启动项、主题、多屏、安全软件、Docker/OpenClaw/微信/真实provider或个人数据。

接单/实质进展/阻塞/交付更新本人快照，长操作先记检查点，有执行控制时至少10分钟心跳。终点复算固定包/受影响输入、旧profile和首次材料，精确列四共享测试文档授权变化；证据/工具/交付逐项清单避免自引用。全部获准门禁完成交review/finished，否则blocked/finished；最终接受由总控决定，不自动派发后续。真正P4-C前端开始前的参考图和模型分工提醒继续有效。
