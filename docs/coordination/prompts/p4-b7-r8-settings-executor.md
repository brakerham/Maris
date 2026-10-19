# P4-B7-R8-SETTINGS：持久主题和隐私的启动恢复

## 唯一负责人、输入与接单

你是既有执行智能体，本任务唯一负责人。测试方R9-R3已blocked/finished，技术顾问停止。修复P1 `P4-C12-R9-R3-SETTINGS-001`；这仍是已有Windows Shell设置恢复，不是财务界面开发。

按AGENTS先读README、project-coordination、coordination/README、最新control、本人executor、本卡，再读：

- [总控裁定与SETTINGS-R8补充合同](../../p4-c12-r9-r3-settings-coordinator-review.md)、[R9-R3报告](../../testing/phase-4-c12-r9-r3-storage-windows-report.md)、其W2 result/journal及冻结driver。独立材料只读，不执行、不修改。
- [D11](../../phase-4-d11-windows-shell-technical-advice.md)的设备设置safe snapshot设计、[IF-003](../../phase-4-interface-freeze-003.md) §4/11—13、IF-004/005；[R7任务](p4-b7-r7-quit-executor.md)与[R7说明](../../b7-r7-quit-running.md)的LOCALZIP、固定工具、统一退出及产物规则。
- [新固定起点](../snapshots/p4-b7-r8-settings-start.sha256)：仓库根、原字节、唯一排序、UTF8无BOM/LF、`path<TAB>sha256<LF>`，排除自身。全部匹配且staged=0后登记接单、下一检查点。

H1本轮原生7/7已通过；W2四条失败是真实有效首样，不把它改成工具超时。QUIT-001普通关闭已接受，UI-01已passed；其余整项及LAZY-001保持。旧H1、W1、路径38项、独立退出/模块/冷B/恢复集合均不重跑。

## 精确写入边界

仅以下12个仓库路径可写，未用到的保留：

| 类别 | 路径 | 限定用途 |
| --- | --- | --- |
| 产品 | `apps/desktop/electron/main/index.ts` | 注册只读设置投影handler；不重构关闭或composition |
| 产品 | `apps/desktop/electron/main/ipc-contract.ts` | 新固定channel的零参数/既有身份校验接线 |
| 产品 | `apps/desktop/electron/preload/index.ts` | 窄getSnapshot桥接 |
| 产品 | `apps/desktop/src/shared/contracts.ts` | 三字段只读snapshot类型及必要严格运行时schema |
| 产品 | `apps/desktop/src/renderer/module-routes.tsx` | 一次启动设置水合、安全加载/错误态及失效回包保护 |
| 旧自测 | `apps/desktop/tests/unit/module-readiness.test.tsx` | 仅给两处虚拟bridge补有效snapshot；原业务断言不改 |
| 旧自测 | `apps/desktop/tests/unit/lazy-isolation.test.tsx` | 仅给虚拟bridge补有效snapshot；原业务断言不改 |
| 新自测 | `apps/desktop/tests/unit/settings-hydration.test.tsx` | 真实DesktopApp/Router/Shell恢复与故障边界 |
| 新自测 | `apps/desktop/tests/unit/settings-snapshot.test.ts` | 真实main/preload/IPC只读投影、安全及无副作用 |
| 交付 | `docs/b7-r8-settings-running.md` | 根因、开发及两次真实生命周期证据 |
| 交付 | `apps/desktop/b7-r8-settings-source.sha256` | 终点逐文件清单 |
| 角色 | `docs/coordination/agents/executor.md` | 本人状态、心跳和交接 |

禁止其他产品文件（包括device-settings存储/schema、Shell视觉、CSS、Host、outbox、registry、supervisor）、依赖/lock、Forge/package/staging、独立测试/报告/矩阵、旧首次材料、接口冻结、control/overview、其他角色文件及Git写操作。新C盘任务根可写本任务driver/evidence/cache/profile；旧根全部只读。需要超出边界，指出具体理由后停止，不擅改旧fixture断言或用产品兼容假分支绕过。

## 先留下红灯，再补读取链

在新执行方测试中运行真实DesktopApp、Router、Shell，用提供dark/true snapshot的虚拟外部bridge模拟已保存设置；先在原实现记录页面/控件仍为system/off的红灯。必须完成实际组件挂载，不能把未加载环境或TypeError当作产品复现。必要时另用真实main/preload检查证明读取接口缺失，但不启动旧EXE或独立W2。

执行SETTINGS-R8合同：`settings.getSnapshot()` → `settings:get-snapshot@1` → main当前已加载设置的三字段新投影 → renderer严格校验/水合。不能仅将useState默认值改成dark/true，不能从renderer读磁盘、添加测试专用恢复分支、把整个DeviceSettings返回或经runtime snapshot塞入设置。

读取成功前，业务模块内容不得以默认privacy=false先展示；加载/错误态只表达用户能理解的状态，不暴露IPC、路径、token或原始异常。失败不写默认值、不自动重试/刷新整页。不能在read过程中触发update、recover、owner重建、财务/外部调用。现有设置写回行为与main损坏文件回退保持；不增加持久字段或迁移。

设置就绪和模块列表为空是两个独立状态：设置成功后，即使Host模块集合为空，也应按原合同显示Shell、Agent及设置入口；不能因空集合一直卡在设置加载态。设置水合不能削弱原模块就绪订阅或故障隔离。

新开发测试至少覆盖：

1. dark/true及非默认theme、合法system/false分别真实恢复；dataset、select、checkbox一致，首个可见业务页面前设置已经生效。reducedMotion以正确类型经过窄snapshot；不追加其视觉功能。
2. snapshot延迟时不展示未保护业务内容；拒绝、缺字段、错误类型/enum、额外字段均安全失败，旧文件不写，原始错误canary不进DOM/console，无未处理promise。
3. 普通与StrictMode、卸载/重新挂载、过期响应均安全；只统计相对加载增量，不复用历史不成立的固定绝对loader计数。runtime/modules同值通知及recover不覆盖新用户选择，不重建相同路由或隐式重试lazy失败。
4. 成功读取后正常主题/隐私交互仍用原typed update；读取等待期间不允许控件产生旧默认保存。读取与已完成用户交互不相互覆盖，不新增自动保存。
5. 导入实际main注册handler，加载虚拟DeviceSettings；getter每次只返回三字段新对象，修改上次返回对象不能改main设置；update成功后再get反映新设置，返回不含其他设备字段。测试可替换Electron/OS/存储外围，不复制生产handler当被测对象。
6. 导入实际preload验证固定channel/无参/键集合；实际validateIpc测试错误sender、subframe、origin、多参拒绝。getter不写settings、不设置系统启动项、不请求Host、不更改outbox。读取schema/权限失败保持安全错误边界，不降低既有校验。

旧动态driver中settings键集仅有update的期望必须在本任务新driver中明确变为getSnapshot/update，其他键保持；旧独立driver不改。已知独立W2后续closePolicy patch不符合当前写接口，属于留给下一Tester卡处理的工具问题，本次不开放该权限，也不借此扩展DeviceSettings。

允许正常开发调试和有理由的定向复跑，保存各次红灯/失败；不要把产品正式动态预算套在开发编辑循环。只准上述两旧fixture补getter，旧断言不降低。新两文件及现有settings-secure/ipc/module-readiness/lazy/Shell/main-quit等必要邻接、TypeScript、lint通过后，完整desktop开发回归运行一次（原17文件169项保持，加新增节点）；定向与完整重复不累计唯一数量。不要复跑Python/P0～P3或独立集合。

## 固定普通环境和一次新包

只读来源 `C:/MarisQuitR7/R7-20261014-191500`，以R9-R3已绑定的构建932、out140、资源67、dist73、完整依赖12677及157执行方证据核验；旧R7和四个R9系列现场不得回写、解密或启动。只读取其摘要/清单，不需要复制旧owner/profile作为开发输入。

新根 `C:/MarisSettingsR8/R8-<时间戳>`，验证绝对边界及无reparse后普通物化工具/依赖/源码，不用junction，不污染源目录。保持Node24.21.0、pnpm12.7.0、Electron44.4.5、Playwright1.63.0及已有已验证Python；lock SHA-256 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`；官方本地Electron ZIP SHA-256 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d`。沿用任务局部pnpm和LOCALZIP，禁止下载/安装/换版本、永久PATH或代理/安全软件修改。

开发通过后冻结构建输入，**package最多1次**。原7项静态门禁、production fuses、完整out/67资源、污染/staging零残留及新读取链确实进入asar/main/preload/renderer均须有证据。失败后保留首次并停止，不追加第二次打包。

## 两次新EXE：保存后正常退出，再原样续启

这是本轮独立执行方预算：**新包1次、EXE最多2次、helper0次**。两个EXE场景必须按S1→S2顺序，任一失败停止后续，不是每场景可重试两次。Tester R9累计产品2/8、helper3/6及其剩余额度冻结，不与本开发预算混算。

共用一个本任务新虚拟profile/owner/数据库及固定Python。每次Node spawn(shell:false)直接启动本轮新EXE，Playwright只附加本次动态loopback CDP；不使用Electron launcher、旧EXE、H1或safeStorage辅助。每次硬上限120秒，常规页面条件观察最多5秒；正常关窗最多10秒。清除继承MARIS_E2E_EXIT_MS；不能用timer、app.quit、process.exit或强杀替代正常退出。

**S1保存场景**：首次启动前仅构造本任务合法设备设置，closePolicy=quit、closeHintShown=false、毛毛可见，theme=light、privacyMode=false。保留原新包安全/后端及真实页面门禁：双窗口、bridge新增唯一getter且无额外能力、renderer隔离、online/authenticated、canonical daily，以及daily/Shell/导航/Agent分别exists/count/visible。

通过真实主题/隐私控件将其设为dark/true，顺序操作并确认实际文件已保存这两个值；不要同时发竞争保存来扩展本任务。保存前后保留安全值、大小和摘要。沿用一次recover检查，确认后台、页面及设置状态保持。随后向身份核实且唯一的主窗口发正常WM_CLOSE，要求root自然exit0、自有进程/监听/窗口0。只有S1全过，才允许S2。

**S2恢复场景**：用相同新profile、相同EXE再次启动；S1退出后到S2首次取样前不得seed、修改或重新发送theme/privacy设置，不复制回初始文件。先记录settings文件dark/true及摘要，等待真实页面ready，首次有效取样同时核验四个值：页面theme=dark、privacy=on、主题选择dark、隐私checkbox=true。精确记录首样、取样前设置写操作为0及文件是否保持，不用二次设置/刷新“修好”页面；不能把Host在线或getter返回正确代替真实DOM/控件。

若首次有效样本任一失败，立即保存并停止业务；不重新取样覆盖、不再启动。S2通过后直接普通关窗、自然exit0并确认资源0，不追加第二次recover或第三次启动。此项证明本任务虚拟设置重启恢复，不替代Tester的原W2复验、owner/session跨重启或真实设备人工项。

driver开始前冻结源码并校验语法、参数、清单列、路径身份和日志格式；已验证observer算法复用且不改独立原文件。不得自创精确进程数预算；未知查询不能记0。每个比较都有唯一ID、expected、actual、时刻；记录read/parse/observe错误的安全阶段，不仅记operation_error。目标前纯工具错误可定向修正，保留首次，每次修正重做受影响静态自检；最多2轮/30分钟，不能变成新的无限工具任务。正式EXE开始后的有效失败不得修后重跑。

## 交付与停止

输出运行说明、终点source清单及实际写入路径清单，保存两次进程真实退出/关闭回执、设置前后值/摘要与各自资源检查。终点source基于本任务起点更新授权摘要并加新增测试/报告，排除自身；外部构建/完整产物/资源、driver与证据均绑定。旧R7环境及旧R9材料保持；保留新包、新虚拟profile和原始记录，仅清理已核实边界、无reparse的本任务临时项。

不要为了数量给未运行节点填passed；不要把开发结果写成独立验收。完成只能review/finished；阻塞则blocked/finished。SETTINGS-001、CMP-06、LAZY-001/UI-02及P4-B均由后续独立复验和总控决定。

接单、红灯、修复、开发门禁、打包/启动和收口更新本人状态；超过5分钟操作前记录下一检查点，有执行控制时至少10分钟心跳。范围/接口超出本卡、新严重缺陷、秘密泄漏、不受控弹窗、所有权不清或无法安全收口立即停止；同一外部问题两检查点无新信息停止。不得改系统设置、操作Docker/OpenClaw/微信/真实provider或要求用户操作窗口；不得启动其他角色或后续独立任务。无Git写权限。
