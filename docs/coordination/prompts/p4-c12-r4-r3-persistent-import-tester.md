# P4-C12-R4-R3：持续导入失败前置验证与冷入口独立续跑

## 唯一负责人、必读与目标

你是既有测试智能体，唯一负责本任务。R4-R2 已确认：取消的 attempt1 安全拒绝，当前有效 attempt2 成功，因此四条原要求中的错误提示没有出现。LAZY-001/UI-02/P4-B 未关闭。现在修正测试的故障注入，让生产默认 loader 的有效加载稳定收到真实动态 import 拒绝；不改产品，不做新的纯 bootstrap 诊断。

按 AGENTS 先读 README、project-coordination、coordination/README、最新 control、自身 tester、本任务，再读[总控核对](../../p4-c12-r4-r2-cold-entry-coordinator-review.md)、R4-R2 报告/34 条 journal/源码/原任务、R5 任务与运行说明、IF-003/004、main/module-routes/Shell/registry/contribution、原24项矩阵。旧 R4/R4-R1/D15/D15-R1 作为只读历史。

逐项复算[新起点](../snapshots/p4-c12-r4-r3-start.sha256)，暂存为空后登记接单与当前快照。本任务测试方提供独立证据和关闭建议，总控作最后接受。不会把注入验证或开发兼容算成 UI 通过。

## 写入与工具边界

- 只新增 `tests/independent/desktop/r4-r3-*` 测试、fixture、配置/resolver、同步门面、setup/controller/reporter及审计，和 `tests/independent/desktop/evidence/r4-r3/**`。
- 新报告 `docs/testing/phase-4-c12-r4-r3-persistent-import-windows-report.md`。
- 旧 C12 主报告、人工清单只追加；矩阵仅 P4-B 的实际状态与证据备注，120 ID、12字段、原前11列与 A/C/D 保持；自己的 tester 日志。
- 全部旧测试/配置/报告/首次证据，产品、开发测试、依赖、lock、包、生成物、Forge、migration、接口冻结、control/overview/snapshot及其他角色文件只读。禁止 Git 写入、自动建下个任务或进入 P4-C/D。

复用 `C:\MarisLazyR5\R5-20261002-222300` 已有工具与普通固定依赖；根目录只读，不复用旧 profile。先核对构建源389、out140、Python资源67、EXE/asar/lock/fuses及现有 Node24.21.0/Vitest5.0.2/Vite7.3.6/React和React DOM19.3.0/Router8.4.0/jsdom30.1.1。

EXE SHA-256 `64ce71f3a7b3055f9ad27f6d611e28c4af7e9ba8b86d8b21399b7b422844a80e`；asar `5ba47909537e1419dc275fa3ca1e5e076a1aa6d5c0205229f91defb92ddd0931`；lock `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。

不得 install/download/build/package、改永久/任务 PATH、TUN/代理、时钟/安全软件、启动后端/微信/OpenClaw/Docker/真实 provider。不重复完成的微信 V002。

## 持续故障实现：真实 ESM 失败，不用页面 manual mock

新测试去掉目标页面的 `vi.mock` factory；旧测试原样保留。通过测试专属精确 alias/resolver，把生产默认动态导入所指的 DailyFinancePage 规范模块 ID 解析到新 fixture：

1. 先核对固定 runner 如何将相对动态请求变为规范绝对 ID。只匹配唯一已知目标：正常化盘符/正斜杠及已知可选 `.tsx`，记录安全布尔或 ordinal 映射回执，不输出绝对路径；若匹配相对字面量，必须限定为真实 module-routes importer。不得通配同目录所有文件、Router、未知 query，或使用 cache-bust URL。
2. fixture 是真实 ESM，可声明不可达的 default 导出以保证模块形态；**零 import**，不导入 helper/React/产品，避免环形依赖提前返回 exports。通过 setup 已建立的原生 global recorder 记录 `fixture_evaluation_enter`，随后顶层 `throw new Error('VIRTUAL_CHUNK_UNAVAILABLE')`。
3. 故障含义是模块求值失败使真实 import Promise 拒绝，仍由生产默认 loader 与原路由 loader 处理。不是网络 chunk 404，不改 `.default` getter、不替换 Page/loader/errorElement，不伪造 Router 错误槽。
4. 不使用目标 `vi.mock/doMock/importActual`、Router async mock、额外 navigate/revalidate、模块缓存 invalidate/reset、外部 monkeypatch、变更生产源码/依赖。除虚拟 bridge/环境外其他产品模块保持真实。
5. resolver/fixture 是新测试接线，静态可行尚未动态确认；记录它如何取代原 mock、影响的唯一模块、所有观察扰动。无法精确命中时停止并报测试配置问题，不扩大匹配。

所有新目标源码先语法/静态解析检查、冻结摘要，再运行。不要复制旧 controller 的控制版本/目录常量；复用已验证的原生日志/ReadWrite读取原则，并将其绑定新任务。

## P：只验证注入，单独新 worker

ID `R4-R3-INJECTION-PERSISTENT`，实际运行一次。使用无 Router 门面的真实包映射和实际 `createModuleRoutes`，通过真实合法 contribution 编译出模块路由，**不传自定义 loaders**，不导入 main。由其生产 route.loader 并发调用两次，等待二者终态后再调用一次。

三个调用均必须 reject，安全错误均为 `desktop_module_unavailable`；目标 resolver 命中同一新 fixture，至少一条 fixture 求值事件，不能从调用次数推定求值次数。保留实际调用 enter/terminal、原始错误是否在生产层变成安全 code、映射和 fixture 事件。只记录安全字段，不记录 raw stack/模块对象。

P 用新隔离 worker/config/cache；P 的模块缓存与结果不传给 A/B，P 不是 UI 独立通过。test<=10秒、CLI<=15秒；不写超复杂 synthetic driver、Job 精确进程预算或新 GO 等待分支。P 失败立即停止 A/B 和后续，不新增产品缺陷、不补跑直到绿。

## A：新的冷入口传播与四断言

P 通过后，ID `R4-R3-UI-02-COLD-TRACE`，另一个新隔离 worker/cache，实际 main 一次。保留 R4-R2 的原虚拟 bridge/jsdom/global、空 hash 初始 URL、真实 contribution/Host 交集与 StrictMode。setup/body不得提前 import Router、main、module-routes、页面、fixture 或预热产品。

使用新前缀同步 ESM Router 透传门面，由 main 正常依赖链首次加载；精确裸 `react-router` alias/独立真实包 alias 保持同一物理 React/Router和解析条件，`export *` 真实其他导出/Context，仅同步透传 createHashRouter 并返回原 Router。目标原 route.loader 包装保持 this/args、返回原 Promise，旁路记录终态/safe code/abort；不换 route/errorElement，不吞错、追加导航或 retry。

原生 setup 在测试初始化前同步建立并逐事件 append/fsync journal；controller 用 FileShare.ReadWrite 只读完整 newline。记录 seq/time/自有PID与parent、worker/body、main enter/terminal、act enter/terminal、fixture求值、目标映射、Router/loader ordinal与 abort/终态、当前目标错误槽、DOM安全布尔、卸载/退订/恢复。所有身份与时序扰动披露。

原四条断言全部实际执行：alert含“页面暂时无法打开”、main.shell存在、模块导航存在、统一Agent面板存在。软断言可以保证四项都执行，但任何失败仍使节点 failed。新增前置：fixture命中、**当前未取消的目标 loader 安全 reject、同一活跃 Router 目标错误槽为安全 code**；取消/旧请求不得补签当前错误。

条件观察最多5秒；test<=10秒、CLI含收集收口<=15秒。看到提示即检查，不加时、固定睡眠或把无限等待包进 act；main和act终态分列，保留真实调度尾差。A失败停止B及后续，首次结果不改后重跑。

## B：无观察门面的独立冷入口

A 通过后，ID `R4-R3-UI-02-COLD-PUBLIC`，第三个新隔离 worker/cache，真实 Router alias直接相同真实包，不加载门面/loader包装，不预先 import，直接实际 main 一次。使用与A完全相同的真实ESM失败fixture/resolver、bridge/初始URL和四断言。

记录 fixture/映射/main/act/DOM/cleanup，但不从A回填B的Router遥测。B只实际运行一次，同5/10/15秒限制。只有P/A/B均通过才能进入续跑；P的三调用不算三次main，也不算三个测试节点。

目标预算：P一次，main A/B各一次，独立worker三个。目标运行前纯工具配置错误如需更正，最多一次、最多一个额外前置worker，必须由持久阶段记录证明 fixture/loader/main均未开始、首次材料冻结、固定输入不变、自有进程已退出。已运行的P/A/B失败不得修后重跑；无证据证明目标未开始时不使用这项预算。普通静态格式修正与目标启动次数分列。

## 精确失败分类与原任务续跑

- P未命中或不能持续拒绝：测试接线阻塞，列明规范解析/模块终态，不猜产品根因，不加时/缓存重置。
- A有效loader未拒绝：故障前置仍未建立，保留每次abort与映射，不用fixture计数补签。
- A有效loader安全拒绝但当前错误槽/DOM不符：关联同Router/有效目标终态与四断言，给出证据支持的产品结论，不笼统说框架吞错。
- A通过B失败：存在观察条件差异，不能关闭LAZY-001，不把B改成A。

全部通过后，**同任务**接原R4-R2尚未执行的独立恢复与剩余公开/Windows范围，严格保留[原任务后续要求](p4-c12-r4-r2-cold-entry-tester.md)。持续失败fixture只用于初始隔离；瞬时恢复通过实际DesktopApp/Router/Shell与可信loader端口独立设计，分别记录，不要求缓存着失败ESM的fixture能自行成功。

必须覆盖瞬时/持续失败、显式有限重试、无自动循环、健康/设置切换、在途重复点击与离开、render错误、主题/隐私/runtime订阅保持、无额外auth/recover/provider/outbox/财务写入。必要相邻Shell/composition与lazy开发8项仅一次兼容复跑，单独统计；不复制开发案例充当独立。不重复既有27独立、outbox42、registry52、完整132、后端/P0～P3全量或D15探针。

上述通过后继续原24项剩余公开与Windows；新虚拟外部根 `C:\MarisC12\C12-R4-R3-<时间戳>`，固定EXE只读。产品最多8次各<=120秒、辅助safeStorage最多4次各<=60秒，按场景计划且不用满预算；固定Node spawn(shell:false)直接EXE、Playwright只CDP，不Electron launcher/PID提升/改fuse。真实chunk网络故障须实际命中并恢复；无法安全控制记unverified，不以ESM/jsdom或正常smoke代替。原生老化提示、Tray、closePolicy、会话持久化保留实际证据要求；未授权OS注销/重启/启动项/多屏/系统主题等只列人工缺口，不要求用户现在操作。外部操作前重读control。

## 收口、交付与停止

卸载真实root、退订观察/abort监听、恢复DOM/global/console，登记自己启动的CLI/worker父子身份、双流与真实exit；硬限只定向结束已确认的自有树。不按名字全局杀进程，不把权限失败空集合写成零，不复制父exit给worker；限制与未知部分明确列出。

新报告给P/A/B独立条件、注入是ESM求值错误而非网络404、各调用终态和四原断言、取消与活跃状态、唯一节点/actual main/修正次数、所有首次材料、独立与兼容分列、原24项完整预期/已有证据/未测缺口、Windows预算和真实注入、资源与摘要。旧主报告/人工清单只追加；矩阵只按完整实际条件更新，不把关闭建议等同UI-02/P4-B complete。

首轮材料保留，清理仅经绝对路径边界/no-reparse核对的自有新缓存；遇泄密/未知所有权/不能收口/新P0/P1/不受控弹窗或连续两检查点无进展立即停止扩大。按AGENTS记录接单、里程碑、十分钟心跳与交接，只更新tester。最终只到review/finished或blocked/finished，停止不建后续任务，不宣布总控接受。
