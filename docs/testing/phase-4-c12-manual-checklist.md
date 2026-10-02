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
