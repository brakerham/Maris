# P4-C12 Windows Shell 人工检查清单

- 日期：2026-10-01，Asia/Shanghai。
- 负责人：测试智能体；本轮交付 `blocked / finished`。
- 本清单所有现场步骤均为 **未执行**，不是通过记录，也不是要求用户现在操作。
- 首先解除 P1 `P4-C12-OUTBOX-001`，由总控指定新固定快照、唯一进程负责人和人工步骤后再执行。本轮产品 EXE 启动 0/8，未创建测试 profile。
- 依据：[原 24 项矩阵](phase-4-modular-agent-host-test-matrix.md)、[C12 独立报告](phase-4-c12-windows-shell-report.md)和 IF-003/004/005。没有重新定义产品规则。

## 开始条件与证据记录

后续实际执行前重新读取 control、明确获准范围，复算新快照/EXE/asar，确认虚拟身份与数据、专属新 profile、进程 ownership 与硬时限。不得复用旧 LOCALZIP profile/数据库/session，也不得操作用户真实程序。是否允许注销、启动项或显示器操作必须由后续总控任务明确；本任务没有这些操作权。

每条记录时间、案例 ID、原始设置、动作、期望、实测、脱敏截图/观察记录、owner 进程与退出证据、剩余子条件。不能用 E2E timer 到期或 PID=0 代替 Tray、设备设置、注销或普通关闭的行为证据。模拟 DPAPI、模拟 display 或源码阅读不能代替真实设备验收。

源码的 `MARIS_E2E_EXIT_MS` 只接受 1000～30000ms，任务卡 120s 是场景预算；E2E 同时抑制 OS `setLoginItemSettings`。后续 OS 启动项测试必须取得单独授权、观察实际 OS，不能从 E2E 测试推导通过。

## 原矩阵 manual 案例

| 案例 / 当前状态 | 条件与后续动作（本轮未执行） | 原验收目标 | 必须保留的通过证据 / 尚缺项 |
| --- | --- | --- | --- |
| P4B-SUP-05 / not_run | 专属 profile 的自有 Host，包含连接/子线程；分别普通退出、强关主窗口和系统注销。注销只在后续总控明确安排的测试设备操作。另设自建非 owned 进程作为对照。 | 自有后端按冻结时限退出，无僵尸/孤儿/占用端口；未拥有进程不受影响。 | 各场景独立时间线、ChildProcess/EXE/创建时间/profile ownership，退出码、树/端口/锁检查，对照进程存活；三个场景均缺，零启动不等于通过。 |
| P4B-CMP-04 / not_run | 专属测试 profile；观察首次启动默认项，后续获准后显式启用/禁用本应用开机启动。不得修改其他软件启动项。 | 默认关闭且无启动项；只有明确操作才创建；禁用清理本应用项，不改其他应用。 | 实际 OS 启动项前后对比、对应 UI 状态、仅本应用项变化、最终恢复证据；本轮未触碰任何 OS 启动项，E2E 抑制不构成证据。 |
| P4B-CMP-05 / not_run | 独立多屏/DPI 测试设备；拖动/置顶、重启、拔屏/分辨率变化、外部全屏、隐私、键盘入口。显示器配置变化须后续明确安排。 | 位置用临时文件原子替换并恢复/夹取；全屏按规则隐藏；隐私不显示金额；键盘入口可达。 | 虚拟设置文件变化、各屏坐标/DPI/bounds 对应截图、断屏后夹取、重启恢复、全屏/隐私/键盘记录；原子保存须另外逻辑证据，不能只靠截图。全部未执行。 |
| P4B-CMP-06 / not_run | 透明窗口支持/不支持的真实设备条件；mini fallback、light/dark/system/high-contrast/reduced-motion、中外行情色。 | 可安全降级且合同不变；文本对比/焦点可辨；reduced motion 生效；收入/支出色不复用涨跌色。 | 透明失败到普通迷你窗的现场证据、窗口/桥接合同仍可用，各主题焦点/对比度、减少动效和颜色语义观察；本轮未运行窗口或改变系统主题。 |

## 自动案例中仍需现场补充的子条件

这些案例当前保持 blocked；下表只列现场部分，不表示其余自动部分均已通过。完整缺口以 C12 报告为准。

| 案例 | 后续场景与需要观察的行为 | 本轮状态 / 证据限制 |
| --- | --- | --- |
| P4B-CMP-02 | 全新设置首次关闭主窗→隐藏到 Tray、提示一次；Tray 恢复再关闭→不重复提示；观察 Host/毛毛驻留和内容保留。 | blocked；未启动窗口或 Tray，未执行提示交互。 |
| P4B-CMP-03 | 分别 hide_to_tray、ask_every_time、quit；询问取消不退出；Tray 打开/隐藏状态一致；quit 清理自有 Host。 | blocked；三策略及退出都未执行，不以自动退出代替。 |
| P4B-CMP-01 | 测试方虚拟第二 contribution 与假状态流；只一个毛毛/Agent 入口，主形态与 idle/thinking/tool/confirmation/error/offline 子状态分离，无业务写入。 | blocked；未创建真实 wealth 模块或第二窗口。 |
| P4B-SEC-01/02/03/04 | 实际 renderer Node 能力、窄 bridge、CSP 注入拒绝、导航/窗口/外链、真实 IPC handler 的无副作用拒绝。 | blocked；只有部分 preferences/CSP/validateIpc 公开函数断言，无实际 Electron 运行。 |
| P4B-SEC-05/08 | 虚拟凭据的 main safeStorage、登录/刷新/重启；renderer storage/内存及脱敏 UI/console/log/crash dump；req ID 和安全错误。 | blocked；虚拟 AES-GCM adapter 与 corruption 错误通过不能代替 Windows DPAPI/秘密隔离。 |
| P4B-SEC-07 | 恶意 HTML/event handlers、RTL、长文本在导航/通知/Agent panel/错误中的安全编码和布局。 | blocked；未进行 UI 渲染或执行。 |
| P4B-SUP-01/02/03/04、SEC-06 | 真实 managed Host nonce/readiness、loopback/Bearer/origin、offline→recover、限次退避、single-flight 与 ownership；外部模式只能用自建 adapter/虚拟后端。 | blocked；没有 Host/产品进程启动，不能把执行方 LOCALZIP 门禁计为本轮 passed。 |
| P4B-SUP-06 | 在修复草稿删除后，核验离线/恢复/重启/重复点击同 ID、GET/恢复只提交一次，边界内容保留。 | failed；P1 草稿丢失已复现，先返修再安排剩余场景，不能现在重启覆盖失败。 |
| P4B-UI-01/02 | Host 与 contribution 交集实际导航/preload；两个测试 lazy route 故障、局部 retry、其他模块/Shell/会话保持。 | blocked；只有交集函数部分断言通过，未运行实际路由。 |

ZIP/staging 的附加检查、UI-03/04 冲突与漂移门禁、HostClient/session/supervisor/settings 的进一步公开行为测试也未执行；它们属于后续自动验收工作，不要求用户人工代做。

## 本轮收口与交接

没有注销/重启 Windows、修改 OS 启动项、拔屏/改显示器、强关真实程序、扫码/微信、Docker/PG、DeepSeek/provider 操作。没有新外部 profile、测试数据库或 owned Host。仅独立 Vitest runner 正常退出为失败状态，保留首次复现证据。

本清单交给总控安排后续步骤；本轮不向用户索要立即操作，也不派发返修任务。只有获得实际现场证据后，才允许逐子条件更新对应矩阵状态。

## C12-R1 状态与证据追加（2026-10-02）

以上C12首次现场缺口完整保留。本轮真实Windows人工条件仍未执行，也不要求用户现在操作；新完整结果见 [R1报告](phase-4-c12-r1-outbox-windows-report.md)。

| 条件 / 案例 | R1实际进展 | 当前现场状态与剩余条件 |
| --- | --- | --- |
| 原OUTBOX-001持久删除逻辑 / SUP-06 | 原PUB-11一次通过、新outbox26和实际main5通过，建议关闭原P1；证据在 `tests/independent/desktop/evidence/r1/` | SUP-06 blocked；真实native dialog仍unverified，需真实safeStorage隔离seed/read，以及owned UIA保留/关闭和明确删除有限集合；模拟AES-GCM不得输入真实app。 |
| 全局setting冲突 / UI-04 | 新P1 REGISTRY-001，R1-SHELL-13首次失败；两module同key被接受 | failed；先交总控返修/新快照，本轮停止扩展。 |
| 主preload、HostClient/session/supervisor | 独立部分公开行为通过；main/retention生命周期只有fake OS/FS/Host ports | 原SEC/SUP案例仍blocked，实际renderer/owned进程/端口/秘密隔离未验证。 |
| 原生提示、普通close/Tray / CMP-02/03 | 无产品启动，未进行CDP/UIA/Tray操作 | blocked；仍需普通关闭策略、首次提示/重复关闭、Tray恢复及owned退出；E2E timer不替代。 |
| OS退出/注销 / SUP-05 | 仅main mock before-quit/Hostshutdown通过，非Windows | not_run；正常退出/强关/注销与真实树/端口/锁仍缺，注销须后续明确安排。 |
| OS开机启动 / CMP-04 | 没有修改实际启动项，setLoginItemSettings只mock | not_run；真实OS默认无项、显式启/禁只影响本应用仍缺，E2E抑制无证明力。 |
| 多屏/主题/透明 / CMP-05/06 | 没有实际窗口或系统配置改变 | not_run；原多屏/DPI/拔屏/隐私/键盘/透明fallback/焦点/动效/色彩语义缺口全部保持。 |

产品启动0/8、辅助Electron0/4。任务卡允许的真实safeStorage辅助seed/read和新EXE原生提示未执行，原因是新P1严重缺陷停止门禁，不能将其记录为环境不可用/审批拒绝或设备passed。没有新C:\MarisC12 profile/database/session，也没有用户真实AppData读取。

总控确认registry返修和新快照后再安排复验及剩余现场场景。本测试智能体不派发新任务、不向用户要求立即点删除、改显示器/启动项或注销。本轮停在blocked / finished。


## C12-R2 独立追加（2026-10-02）

- [R2完整报告](phase-4-c12-r2-registry-windows-report.md)：blocked / finished。原setting REGISTRY-001不变断言一次通过、独立相邻共15 passed；新P1 P4-C12-R2-REGISTRY-PATH-001，同路径不同route ID仍accepted:2，首次失败已保留。开发26 passed单列，不抵消路径失败。
- P4-B仍0 passed、1 failed、19 blocked、4 not_run；UI-04 failed原因现为path冲突，旧setting首次失败保持历史原样；OUTBOX-001关闭及旧outbox42证据不重复。
- 产品0/8、辅助Electron0/4，因新P1停止。真实老化原生提示unverified，Windows/Tray/启动项/多屏/主题等原人工步骤继续not_run，未要求用户立即操作；未执行设置/安全/HTML/lazy/generated/ZIP/staging新门禁。
- 证据：`tests/independent/desktop/evidence/r2/original-registry/`及`remaining-independent/`首次log/JSON；原文prefix、旧R1报告/evidence不改写。没有产品或Git写操作，交总控裁定。


## C12-R3 独立追加（2026-10-02）

- [R3完整报告](phase-4-c12-r3-route-windows-report.md)：blocked / finished。原PATH-001不变断言及新路径9通过，建议关闭；新P1 P4-C12-R3-LAZY-001：lazy import故障后整个Shell/nav/Agent入口消失，首次证据在evidence/r3/remaining-independent，未重跑或修产品。
- 独立28 unique：27 passed/1 failed；开发registry52 passed单列。设置3/ZIP6/staging7通过限逻辑证据；产品0/8、辅助Electron0/4，Windows未执行。
- UI-02现failed；UI-04路径问题复验通过但完整独立复核未完成为blocked，P4-B仍0 passed/1 failed/19 blocked/4 not_run。旧OUTBOX/setting保持关闭，旧outbox42/setting节点不重复。
- 真实native dialog unverified、Tray/启动项/注销/多屏/主题人工步骤原样保留未执行，不要求用户即时动作。旧正文prefix和旧R1/R2报告/evidence保持。交总控裁定新lazy故障，测试角色停止。


## C12-R4 独立追加（2026-10-02）

- [R4报告](phase-4-c12-r4-lazy-windows-report.md)：blocked / finished。原R3-UI-02-LAZY精确节点一次失败，actual alert不存在、Shell/nav/Agent存在；无法确认故障命中/完成，不建议关闭LAZY-001，也不把结果新增定级为产品P1。
- 独立0 passed/1 failed；新增恢复/兼容均not_run。按原失败门禁停止，产品0/8、辅助Electron0/4、Windows chunk注入0；真实Windows/native/人工条件仍未执行。
- 旧OUTBOX/setting/PATH保持关闭，旧27成功与outbox42不重跑；B仍0 passed/1 failed/19 blocked/4 not_run。原首次代码/报告/evidence保持，当前主报告和清单仅追加。
- 首次JSON/log在evidence/r4/original-lazy，静态来源/观察限制在readonly-source-observation.json；交总控裁定有限测试观察契约，未改产品或Git。


## C12-R4-R1 可观察复验追加（2026-10-02）

- [R4-R1报告](phase-4-c12-r4-r1-observation-windows-report.md)：blocked / finished。新OBS节点一次0 passed/1 failed，确认mock factory1、#/daily，但5016ms仍无alert；Shell/nav/Agent在，原四条要求不降级，旧R4首次失败不改写。
- 原因不再能直接归于200ms，当前预期错误终态/错误传播原因仍unverified，不新增未经定位产品P1、不建议关闭LAZY-001。真实root卸载/订阅2→0/DOM/global清理有首次回执。
- 后续独立恢复/兼容/Windows未执行，产品0/8、辅助0/4、chunk注入0；旧已通过outbox/setting/path不重跑。B仍0 passed/1 failed/19 blocked/4 not_run，人工条件保持。
- 新首次log/JSON与observation-receipts在evidence/r4-r1，原所有资料不变；交总控裁定有限观察/核对范围，不改产品或Git、不自行续跑。


## C12-R4-R2 冷入口复验追加（2026-10-03）

- [R2独立报告](phase-4-c12-r4-r2-cold-entry-windows-report.md)：blocked / finished；A唯一一次0 passed/1 failed，B及后续not_run，LAZY-001未关闭。
- main/act完成，同一Router1的attempt1被取消后安全拒绝、attempt2未取消成功resolve，活跃目标idle/errors0，无alert；Shell/nav/Agent三断言通过，不能把取消错误补签为当前有效请求故障。
- 本次未建立活跃请求错误前置，不新增已定级产品P0/P1；第二次import解析原因仍unverified，交总控裁定测试接线。不继续延时/预热/重打包，不重跑首次结果。
- 产品0/8、辅助0/4、chunk注入0；系统枚举CimException明确未核实全树，已登记CLI/worker结束、真实root及订阅清理有记录。旧证据和24项原要求保持，人工条件不要求现在操作。


## C12-R4-R3 持续导入复验追加（2026-10-03）

- [R3报告](phase-4-c12-r4-r3-persistent-import-windows-report.md)：blocked / finished；P工具前置1 passed，真实默认loader两并发及随后3/3safe reject，零import ESM求值1/精确映射1；不是网络chunk404或UI通过。
- 全新A首次停在worker_start/journal_ready，正文/main/fixture/loader均0，CLI14595ms硬限定向收口；无runner JSON，四原断言not_run，不编造failed产品节点。B、恢复、兼容和Windows未执行，产品0/8、辅助0/4。
- 没有明确纯工具配置错误，不消耗额外前置worker盲重试；原P/A首次材料完整保留，LAZY-001/UI-02/P4-B未关闭，无新增产品缺陷。已登记CLI/worker结束，完整系统后代枚举CimException保持unverified。
- 原24项完整预期/历史保持，普通静态映射修正1与目标更正0分列；用户继续后的长可见性空档如实记录。交总控review后停止，不自动续跑。


## C12-R5-PUBLIC 公开冷入口追加（2026-10-04）

- [R5-PUBLIC报告](phase-4-c12-r5-public-windows-report.md)：blocked / finished；公开B独立启动，不依赖A。唯一新CLI/worker停在jsdom_import_enter缺少terminal，initialization_blocked；正文/main/fixture0，四断言not_run，没有runner JSON或产品failed节点。
- 主进程启动→初始化收口14953ms，process15113ms、controller_finished15120ms；正文/观察/UI cleanup未开始，自有CLI/登记worker已结束。worker exit code unknown，完整系统后代未核实；缓存未生成/未删除，首次六文件及10源码保留。
- 来源与公开结果都未计算，P旧成功只读不补签；恢复/兼容/剩余公开/Windows停止，产品0/8、辅助0/4、网络chunk注入0。普通静态谓词更正1、额外worker/目标重试0；根因unknown不作为工具重试授权。
- 原24项要求与状态保持，LAZY-001/UI-02/P4-B未关闭。只交总控review，不改产品/依赖/Git、不自动启动A或新任务。


## P4-C12-R6-ENV 增量（2026-10-04）

- [R6独立报告](phase-4-c12-r6-env-windows-report.md)：原生固定jsdom已返回；公开B首次1/1 passed，main1/fixture1、四原断言4/4、同次来源/安全/清理通过。旧R5初始化阻塞证据不倒写。
- 同任务已继续独立恢复，首场景出现AssertionError，runner1 failed；具体比较值未留存，产品归因unverified，第2～5场景及相邻兼容/Windows未执行。目标已进入，不自动重跑。
- root/worker均已退出，界面卸载/退订/global/console/DOM实际清理；全系统历史后代及worker自身exit code未核实。缓存仅清理本轮专属路径，首次材料保留。
- B整项0 passed/1 failed/19 blocked/4 not_run保持；Windows0/8、辅助0/4、真实chunk0。实际Tray、老化原生提示、session/系统注销/启动项/多屏/OS主题等原缺口保持，不要求用户现在操作。
- blocked / finished，供总控review；LAZY-001/UI-02/P4-B未关闭，未修改产品/依赖或Git，不进入P4-C/D。


## P4-C12-R7-RECOVERY 增量（2026-10-12）

- [R7增量报告](phase-4-c12-r7-recovery-windows-report.md)：新恢复合同1节点5/5组通过、208正式比较通过；两个旧计数对照为expected1/actual2、expected2/actual3，旧R6失败保留。独立结构8 passed，必要开发兼容10 passed单列；R6公开冷B不重跑。
- 真实固定EXE首次W1运行，13比较passed/1观察failed；首ID W1-DAILY-PAGE expected=true actual=unknown，5000ms等待没有页面就绪样本。真实后端online/认证/canonical模块、安全窄bridge/CSP部分通过；未取得页面初读模块/终态DOM，根因和产品定级unverified。
- 产品1/8、辅助0/4、chunk注入0。首错后停止动态扩大，root3448按已验证身份定向收口，8登记进程与监听均无；这是强制清理，不是正常关闭/Tray通过。虚拟加密profile/db仅在本轮C:/MarisC12专属根保留，仓库无原文。
- 原24项整项状态保持：B0 passed/1 failed/19 blocked/4 not_run；真实session重启、原生老化提示、关闭策略/单实例、OS注销/启动项/多屏/主题等缺口未通过，不要求用户立即操作。R7首次材料和新命名/取证限制详见报告，交付blocked / finished供总控review；不自动复跑或进入后续场景。


## P4-C12-R8-MODULES 增量（2026-10-13）

- [R8报告](phase-4-c12-r8-modules-windows-report.md)：提交总控review，blocked / finished。新818起点与R6源码/包/依赖已绑定；独立首次runner9 passed/1 failed/3 not_run，393正式比较passed。R8-10为测试辅助重复断言ID中断（R8-TOOL-ID-001），非新增产品缺陷；部分模块移除观察不代表节点通过。
- 已取得普通/Strict空列表→同值就绪通知、已就绪启动、晚快照、同步通知、突发合并/旧列表、拒绝保页及同集合retry+1/状态保持证据。旧冷B/完整R7不重跑，旧W1原因仍unverified；jsdom样式可见性与真实Windows分别统计。
- 目标已进入后不能修后重跑，保留首次源码/日志。后3节点、开发兼容28和Windows均not_run；产品0/8、辅助0/4、chunk0。root30140/worker22216实际exit1、无强杀/超时，真实卸载/退订/global恢复通过。
- 原24项仍0 passed/1 failed/19 blocked/4 not_run；所有Tray、真实session/同ID重启、老化原生提示、设备条件继续未验证。无新外部profile或OS/用户操作，不请求即时点击；原预期及历史材料保持。
