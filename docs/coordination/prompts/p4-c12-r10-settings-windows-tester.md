# P4-C12-R10-SETTINGS：设置恢复独立复验与剩余 Windows 续验

## 负责人、输入与不重复范围

唯一负责人为既有测试智能体，Executor/顾问停止。按 AGENTS 读必读、最新 control、本人 tester、本卡及 [R8-R2 总控裁定](../../p4-b7-r8-r2-settings-coordinator-review.md)。再读 [SETTINGS-R8 补充合同](../../p4-c12-r9-r3-settings-coordinator-review.md#4-本次补充合同settings-r8)、[R9-R3 报告](../../testing/phase-4-c12-r9-r3-storage-windows-report.md)、[原生上下文卡](p4-c12-r9-r3-storage-windows-tester.md)、[剩余 Windows 原要求](p4-c12-r9-r1-h1-windows-tester.md)、IF-003/004/005、原矩阵和人工清单。本卡覆盖受验包、合法场景配置、剩余预算；旧失败/未知结果不回填。

[R10 起点](../snapshots/p4-c12-r10-settings-start.sha256)按仓库原字节逐项复算，全匹配且 staged=0 后登记接单。格式为有序唯一 `path<TAB>sha256<LF>`、UTF-8 无 BOM，不含自身。其他角色不得为已停止旧卡追加日志；新漂移不能自行忽略或改清单。

唯一受验根 `C:/MarisSettingsR8/R8-20261019-103900`，唯一 EXE 为其中 `workspace/apps/desktop/out/Maris-win32-x64/Maris.exe`。

| 固定项 | SHA-256 |
| --- | --- |
| EXE | `c80d27c8e31fa60df91065a770e669a553260cf8f883c55a0a7f83f8a430736b` |
| app.asar | `05cdad34ba60b59773eebe671156c96260e69354568b9942da59058641f9c0b2` |
| lock | `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |
| R8 构建清单，1365项 | `c880730b84d726dec41e077867e44e942855ba60790e3a0ddb38940b89efd1d4` |
| R8 产物清单，140项 | `8afdd6d3e7c928912b48acedb2d7c1931607e47f32e549a67e92d04eff142409` |
| R8 资源清单，67项 | `324845f07f050f2b90e3c1e0b89b6598c8748aca549f8f848b600d5a2a0da5d1` |

清单实际路径/基准根见固定根 `evidence/closeout.json` 的 newFixed。先核对上述清单及实际入口。工具沿用固定 Node24.21.0、Playwright1.63、Electron44.4.5、项目 Python，来源由 R8 和 R8-R2 closeout/输入审计绑定。完整历史依赖审计只引用，核对实际使用入口及 lock；不重装、升级、下载、打包或重新全扫每条命令的依赖。

R8-R2 的47/267工具和S1/S2属于执行方证据，只引用，不运行；旧H1、W1、退出8/48、模块13、冷入口B、独立恢复、注册/outbox已通过集合不重跑。原SETTINGS-001四条首次失败是本次明确复验例外；新包生命周期中的必要同类观察与独立重跑旧节点分开统计。

## 写入边界与目标前准备

允许新增 `tests/independent/desktop/r10-settings-*` 测试/配置/必要工具副本、`tests/independent/desktop/evidence/r10-settings/**`、`docs/testing/phase-4-c12-r10-settings-windows-report.md`；更新本人 tester。C12主报告、人工清单仅追加；矩阵仅按独立证据更新B的状态/备注，120ID、12列、原预期和A/C/D不变。产品、执行方测试、旧独立材料、包/依赖、控制/overview/快照和其他角色只读，无Git写权限。

新外部根仅 `C:/MarisC12/C12-R10-SETTINGS-<时间戳>`，先核实绝对边界、未存在、无reparse。所有新工具、虚拟profile/数据库、缓存和证据写新根或上述新测试路径。旧C:/MarisC12及MarisSettingsR8现场只读。可以机械复用已通过的独立身份、异步观察、路径规范化、同源加密准备和分段记录，冻结实际源码/参数差异；不新造通用进程管理框架，不用执行方业务断言替代独立判断。

目标前允许最多30分钟实际操作、3版必要工具/记录器准备，审批等待除外。仅用虚拟输入检查参数、身份时间类型/路径规范化、清单列数、safe error分类、比较ID唯一、缺失/坏结果、首错保留和finally无条件释放；复用已有通过函数只检查受影响分支。原生回执须先解析保留真实身份，再尝试保存；不因落盘失败丢失清理依据。必要的只读观察权限在目标前确认，不建新的Node试跑或完整旧工具自测集合。产品或原生helper不得作为工具自检启动。

所有正式节点在执行前冻结源/计划；计数用稳定新增行为增量，不重新引入旧初始loader绝对计数假设。正式失败保存具体安全 expected/actual、断言ID及阶段；禁止只留 AssertionError 或 operation_error。阶段即时落盘，失败不等收尾才一次输出。到达工具限额仍不能冻结则停止；正式节点有效失败/未知工具错误不得修后重跑。

## 第一阶段：新增接口与水合的独立公开行为

独立运行真实生产接口/组件，仅外部依赖用虚拟接口；不复制实现，也不以源码字符串扫描代替行为。使用已通过的原生 jsdom 环境装配方式，避免重新在测试正文内动态加载 jsdom 的旧阻塞链。新增病例按下列合同分组，独立节点/比较数分别记录：

1. `settings.getSnapshot()` 零参数、受信sender/mainFrame/origin校验，严格只返回theme/reducedMotion/privacyMode，新投影读取无写入副作用；原update合同不扩大。非主窗口、非法参数/来源拒绝，毛毛bridge不能跨窗读取。
2. 三字段合法snapshot恢复主题、隐私、控件一致；非法枚举、类型或额外字段拒绝。响应未返回时不展示默认隐私关闭的业务内容；拒绝/非法响应为有限安全错误，不写默认值、不泄露错误正文、不自动循环读取。
3. StrictMode/卸载/失效读取晚到不更新当前状态，未就绪控件不造成旧值覆盖；runtime/module/recover通知不重新水合覆盖已明确选择，不隐式重载或重试页面。模块最初为空时设置读取仍能完成，后续模块就绪继承正确设置。

为旧虚拟bridge增加新getter必须明确是测试输入适配；不修改旧文件/旧断言。失败归类依据实际来源，不能将测试装配失败写成产品P1。全部通过后只运行执行方 `settings-snapshot.test.ts` 与 `settings-hydration.test.tsx` 两文件一次（交付基线48项），单列兼容结果；不重复完整217或旧48退出兼容。输入/环境问题不得用skip、xfail或减少节点替代。

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

报告逐项列原24项完整要求、历史引用/本轮结果/剩余条件，独立与兼容分开统计。SETTINGS-001的关闭建议必须由本轮独立水合及W2证据支持，完整CMP-06/UI-02/P4-B不能凭一个子条件签收。不改矩阵原预期，不要求OS注销/重启、启动项、主题、多屏、安全软件、Docker/OpenClaw/微信/真实provider或个人数据。

接单/实质进展/阻塞/交付更新本人快照，长操作先记检查点，有执行控制时至少10分钟心跳。终点复算固定包/受影响输入、旧profile和首次材料，精确列四共享测试文档授权变化；证据/工具/交付逐项清单避免自引用。全部获准门禁完成交review/finished，否则blocked/finished；最终接受由总控决定，不自动派发后续。真正P4-C前端开始前的参考图和模型分工提醒继续有效。
