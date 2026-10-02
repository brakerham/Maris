# P4-C12-R4-R2：冷入口传播复验与原R4续跑

## 唯一负责人、输入与结论权限

你是既有测试智能体，唯一负责本任务。D15-R1已回答前置观察问题，由总控按有限范围接受；旧P3超时根因未知，原四业务断言未通过，LAZY-001/UI-02/P4-B均未关闭。执行与技术顾问停止。现在直接接回独立复验，不再纯bootstrap诊断、不重打包或只延长等待。

按AGENTS读README、project-coordination、coordination/README、最新control、自身tester、本任务，再读[总控裁定](../../p4-d15-r1-bootstrap-coordinator-review.md)、D15/R1报告与原始journal、旧C12-R4/R4-R1任务/测试/首次证据、R5任务/运行说明、实际main/module-routes/Shell/registry/contribution及IF-003/004与原24项矩阵。逐项复算[新起点](../snapshots/p4-c12-r4-r2-start.sha256)，staged=0后登记接单/执行快照。不要发送已完成微信V002。

本任务只有测试方能提交独立结论；通过某个节点不等于完整UI-02/P4-B验收。D15探针pass不计入独立统计。

## 写入与环境边界

- 仅新增`tests/independent/desktop/r4-r2-*`测试/同步观察门面/配置/原生setup/controller/审计及`tests/independent/desktop/evidence/r4-r2/**`。
- 新报告`docs/testing/phase-4-c12-r4-r2-cold-entry-windows-report.md`。
- 旧C12主报告、人工清单只追加；矩阵仅P4-B实际状态与证据备注，120个ID、12字段、原前11列预期、P4-A64 passed/P4-C20及P4-D12 not_run保持。
- 自己的tester日志。

所有旧public/r1/r2/r3/r4/r4-r1、D15/D15-R1测试/源码/配置/报告/证据只读，不改旧首次失败。产品/开发测试/依赖/lock/生成物/包/Forge/migration/冻结/control/overview/snapshot/其他角色禁止修改。

复用`C:\MarisLazyR5\R5-20261002-222300`普通固定依赖与工具，实际版本、源码389/out140/resources67、EXE/asar/lock/production fuses先只读核对。EXE `64ce71f3a7b3055f9ad27f6d611e28c4af7e9ba8b86d8b21399b7b422844a80e`，asar `5ba47909537e1419dc275fa3ca1e5e076a1aa6d5c0205229f91defb92ddd0931`，lock `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。Node24.21.0、Vitest5.0.2、React/React DOM19.3.0、React Router8.4.0、jsdom30.1.1使用现有安装。不得install/download/build/package或修改系统/用户环境、PATH、代理/TUN/时钟/安全软件。外部原R5全根只读，不用其旧profile。

## 先建立一次可观察的冷入口复验A

“冷入口”指本隔离worker内尚未导入main、module-routes、Router或页面；按原节点的虚拟bridge、jsdom/global、初始URL/空hash、真实contribution/Host交集和StrictMode直接import实际main。保留原DailyFinancePage mock抛固定虚拟错误。禁止setup/body前置import Router或产品入口、预热缓存、额外navigate/revalidate、换初始#/daily或替代loader/Router/Shell。

现有main只导出desktopRoot，无Router公共遥测。本任务明确允许**测试专属同步ESM观察门面**，只用于A：

1. Vite精确alias只匹配裸`react-router`，指向新门面；门面通过另一独立alias导入同一冻结真实包，该alias不能再回指门面。保持真实包的解析条件、React/Router单实例；其他subpath不能误匹配或形成第二包。不要用async vi.mock('react-router')/importOriginal。
2. 门面`export *`重导出真实其他导出/Context，仅同步透传createHashRouter。它在main→module-routes正常首次请求时加载，不人工提前请求；原参数、route/errorElement和实际返回Router身份保持。
3. 保存实际Router并用state/subscribe即时记录initialized、navigation、安全目标matches/errors。为取得同次默认loader终态，仅允许对目标原route.loader同步透传原this/args，原样返回原Promise，旁路then记录resolve/reject/安全code及该次request是否aborted。默认内置页面loader仍是生产实现，不提供替代page loader。
4. loader包装会改变函数身份并增加旁路监听，必须披露；不替换route对象、构造另一Promise、吞错、修改业务结果或追加导航/重试。按Router实例序号/loader尝试序号关联当前目标，区分已dispose/aborted旧实例和活跃导航，不能拿旧实例reject补签当前Router错误槽。
5. 观察异常先分类为工具问题，不制造产品失败。门面源码、精确alias、防循环和静态解析/语法先核对，运行前冻结；这套门面尚未动态验证，不预写成功结论。

原生setup在测试模块初始化前独占建立同步追加journal，仅原生文件能力、不导入React/Router/产品。每次关键事件即时落盘，记录seq、相对时间、自有PID/parent及固定安全字段；不要只在finally或stdout缓冲保存。controller活动读取采用已验证的ReadWrite共享读法，解析完整newline，保留最后完整事件；记录安全异常类型而不是raw stack。

分别记录worker/body、main import enter/resolve/reject、act enter/return、factory命中、目标loader enter/resolve/reject/aborted、Router建立/订阅状态/错误槽、DOM安全提示及Shell/nav/Agent布尔、卸载/退订/恢复。不要导出模块对象、Error/stack、请求URL、路径、完整DOM、token/nonce或个人数据。

保留原四条独立断言：alert含“页面暂时无法打开”、main.shell存在、模块导航存在、统一Agent面板存在；新增前置条件为原factory确实命中。只有当**当前活跃目标**错误和DOM状态可关联时才能建议故障隔离通过，不能只看Shell或fault计数。

条件观察最多5秒，看到安全错误提示即可检查；test最多10秒，CLI含收集/收口最多15秒。分开main与act终态，不用固定睡眠代替条件，不把5秒观察包进无限act，不延长时限。A只实际运行一次，ID `R4-R2-UI-02-COLD-TRACE`，首次stdout/stderr/journal/JSON/真实退出原样保留。

## A通过后，无观察门面的冷入口B

使用另一个新隔离worker和独立缓存/配置，Router alias直接到同一真实包；不加载门面或任何Router/mock包装，也不前置import。其余真实main/默认loader/页面故障mock/bridge/初始路径和四断言与A相同。

setup仍即时记录worker/main/act/factory/DOM/cleanup；不读取不存在的Router遥测，不凭A回填B的Router状态。B只实际运行一次，ID `R4-R2-UI-02-COLD-PUBLIC`，同5/10/15秒上限。A和B条件分列，B用于证明四断言的通过不依赖观察门面。只有两者均通过，才进入下面续跑。

前两项合计实际main启动最多2次，A/B各一次、隔离实例不可共享。A失败则B与后续not_run；B失败则后续not_run。任一实际目标已启动后的失败不得修改后重跑覆盖。目标前的纯配置/语法/记录映射问题，只有持久证据明确证明main未开始、首次材料与输入不变且自有进程已退出时可一次定向更正；最多一个额外前置worker，不第三次main，不另建synthetic driver/Job进程数量门禁。

## 失败分类必须比旧无提示报告更精确

- factory未命中或main/act未完成：报告最后持久阶段，产品结果unverified，不预热/加时再跑。
- factory命中但loader终态未知：明确对应实例/请求/abort/缺失事件，不能凭P1/P2结果补签。
- loader已安全reject：检查同实例活跃Router是否发布对应错误槽、导航是否终态；已取消或旧Router不能当产品缺陷。
- 活跃Router错误槽存在且匹配目标，但四断言失败：保留关联DOM时序、准确位置/预期/实际/影响，给证据支持的产品缺陷或原缺陷未关闭结论；不要仅猜框架原因。
- A通过、B失败：不能关闭LAZY-001，明确存在观察条件差异，不修改B变成A。

失败后停止扩大，保留已执行的结果和未执行范围。不再建议另一个仅延时或bootstrap任务；由总控根据精确阶段决定测试接线或产品返修。任何泄密、未知所有权、无法收口、新P0/P1或失控弹窗立即停止。

## 两节点通过后，在同一任务接原R4后续

沿用原R4/R4-R1独立恢复要求：实际DesktopApp/Router/Shell/注册器，只有bridge与可信页面loader是虚拟端口。独立设计瞬时/持续失败、显式有限重试、不自动循环、健康/settings切换、在途重复点击与离开、render错误、主题/隐私/runtime/订阅保持、无额外auth/recover/provider/outbox或财务写入。这些可控loader边界与A/B生产入口默认loader证据分列，不复制开发八项。

必要相邻Shell/composition与新增lazy开发八项可一次兼容复跑单列。旧成功27节点、outbox42、setting/path关闭证据沿用；不重跑未受影响registry52、完整132、Python/P0～P3/Host全量或D15任何探针。

上述通过后，接续原24项未执行公开行为与Windows。新前缀/证据目录r4-r2；新虚拟外部根`C:\MarisC12\C12-R4-R2-<时间戳>`。产品最多8次有计划启动、各<=120秒；辅助safeStorage虚拟fixture最多4次、各<=60秒，不用满预算。仅固定Node spawn(shell:false)直接固定EXE、Playwright只CDP，不_electron.launch/PID提升/修改production fuse。

Windows chunk故障必须记录实际注入命中和恢复；无法安全控制则明确unverified，不以jsdom或正常smoke替代。原生老化提示、Tray、普通closePolicy、会话持久化按原R4实际取证；OS注销/重启、启动项/多屏/系统主题等未授权设备动作只记人工清单，不要求用户现在操作。外部操作前重新读control。

## 资源与交付

卸载实际root、取消观察订阅、恢复DOM/global/console，区分正常finally与硬限。controller只定向结束自己创建的已知树，及时从journal登记worker父子身份、保留双流/真实exit/timeout/强制收口；不能全局结束Node/Electron/Maris/Python，不将权限拒绝后的空集合写零残留，父CLI退出码不复制给worker。

新报告给A/B各条件、四断言、factory→loader→活跃Router→DOM关联、首次失败/实际main及修正次数、独立与兼容分列、原24项完整预期/证据/剩余缺口、真实注入/启动预算、资源限制、起终与交付摘要。旧报告/人工清单只追加，原失败不倒写passed；矩阵按实际完整条件更新，独立关闭建议与UI-02/P4-B接受分开。

只清理经绝对边界/no-reparse核对的自有新缓存，首次源码、日志、journal和结果保留。按AGENTS记录接单/里程碑/十分钟心跳/停止，只更新tester；任务以review/finished或blocked/finished交付后停止，不创建下个Prompt或宣布总控接受。不Docker/PG/OpenClaw/微信/DeepSeek/provider，不Git写入，不进入P4-C/D。
