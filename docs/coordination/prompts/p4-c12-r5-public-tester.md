# P4-C12-R5-PUBLIC：无包装公开冷入口与剩余独立验收

你是既有测试智能体，唯一负责人。D16 有限技术裁定已由总控接受，后续 **B 不再依赖 A 先通过**。旧 A 根因 unknown，旧首次材料全部保留；P 的持续故障验证已通过，不重复 P、旧 A/B、D15 或 D16 实验。本任务先取得公开界面本身的判断，通过后在同一任务继续原恢复和剩余 Windows 验收。

## 必读、接单与固定环境

按 AGENTS 读取 README、project-coordination、coordination/README、最新 control、本人 tester 状态、本任务；再读 [D16 总控冻结](../../p4-d16-harness-and-acceptance-coordinator-review.md)、[D16 正式报告](../../phase-4-d16-harness-and-acceptance-advice.md)第 6～9 节、[R4-R3 独立报告](../../testing/phase-4-c12-r4-r3-persistent-import-windows-report.md)、原 24 项矩阵/人工清单及 [R4 原后续要求](p4-c12-r4-lazy-windows-tester.md)。旧各任务只作历史与未替换范围参考；本文和最新 control 优先，不再执行旧 A→B 门禁。

开工逐项复算 [本轮起点](../snapshots/p4-c12-r5-public-start.sha256)、staged=0，并核对 control 唯一负责人，再登记接单、当前步骤/起始时刻、最近进展/心跳和下一检查点。起点清单基准为仓库根，UTF-8 无 BOM、路径排序、`path<TAB>sha256<LF>`；原字节核对，不归一化掩盖漂移。

只读复用 R5 外部根 `C:\MarisLazyR5\R5-20261002-222300`：Node24.21.0、Vitest5.0.2、Vite7.3.6、React/DOM19.3.0、Router8.4.0、jsdom30.1.1、TypeScript6.0.3，原普通 node_modules。产品源码389/out140/Python资源67、依赖/产物清单分别核对；旧虚拟 profile 不使用。

- EXE `workspace/apps/desktop/out/Maris-win32-x64/Maris.exe` SHA：`64ce71f3a7b3055f9ad27f6d611e28c4af7e9ba8b86d8b21399b7b422844a80e`。
- `resources/app.asar` SHA：`5ba47909537e1419dc275fa3ca1e5e076a1aa6d5c0205229f91defb92ddd0931`。
- workspace lock SHA：`5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。

P 的 [52 项材料](../../../tests/independent/desktop/evidence/r4-r3/delivery.sha256)和 [15 项冻结源码](../../../tests/independent/desktop/evidence/r4-r3/cold-source.sha256)只读复核，基准分别为仓库根与 `tests/independent/desktop/`。不运行 P。D16 两次依赖实验不计入本轮独立 passed。

## 精确写入范围

- 新增 `tests/independent/desktop/r5-public-*`：独立测试、精确 resolver/fixture、新配置/setup/controller/reporter及审计；新增 `tests/independent/desktop/evidence/r5-public/**`，所有首次材料保留。
- 新报告 `docs/testing/phase-4-c12-r5-public-windows-report.md`。
- 原 C12 主报告、人工清单只追加本轮事实，原字节前缀保持。
- 矩阵只更新 P4-B 实际状态与证据备注；120 ID、12 字段、原验收预期及 A64 passed/C20、D12 not_run 不变。
- 仅本人 `docs/coordination/agents/tester.md`。

产品/开发测试/旧独立测试与 evidence/顾问材料/依赖/lock/包/生成物/migration/冻结/control/overview/snapshot/其他角色均禁止修改；不 install/download/audit/build/package，不改用户或系统环境、代理/TUN/PATH/时钟/安全配置/fuses。新缓存及 Vite 配置临时目录须在本轮新范围内，不向只读 R5 或上级目录写入。

## 一个公开冷入口 B

新 ID `R5-PUBLIC-UI-02-COLD`，最多一次实际 main 启动。只参考 [旧未执行 B 源码](../../../tests/independent/desktop/r4-r3-cold-public.test.tsx)设计新节点，不运行它，不导入会写旧目录的 resolver/setup/controller。新目录、fork worker、独立缓存；环境 node、isolate、maxWorkers1，不复用旧 worker/module cache。

真实 Router 裸包及 subpath直接解析同一 R5 物理包，React/ReactDOM 单根；**不安装观察门面、不包装 loader、不采集或伪造内部 Router/abort 字段**。用 E1 式顶层分段 await 加载 jsdom/React，逐项 enter/resolved/rejected；它们都在正文前，不前置求值 Router/main/module-routes/contribution/页面。不清 OS 缓存，不把冷 worker 声称为磁盘冷启动。

新精确 resolver 保持旧谓词语义，只替换新 fixture/journal 标识和路径：只映射实际 DailyFinancePage 唯一规范 ID 或精确相对请求与实际 importer；单层已知 Vite 包装和盘符/斜杠规则保持，未知 query/hash 拒绝。新 fixture仍零 import、零 JSX、顶层同步记录并 throw 固定虚拟错误，不能因二次 import 返回成功替身。静态核对差异后冻结新源码；不使用 vi.mock/doMock、getter 替身、替代 Page/loader、cache reset/bust 或网络请求来造成功。

正文建立同原虚拟 bridge、初始空 hash/URL、真实 contribution 与 Host intersection，实际 main/StrictMode/default loader 一次。main import Promise 与 React act 的进入/返回分别记录；不额外 navigate/revalidate/recover，不先设 `#/daily`，不调用模型或写财务事实。

条件观察仍最多 5 秒，看到安全提示与自身来源命中后立即采样，不能固定睡满或无限 act。**同一采样时点**在当前 `#/daily` 的 `main.shell .content [role="alert"]` 核对“页面暂时无法打开”，并保留 Shell、Shell 内模块导航、Shell 内统一 Agent 面板四条原断言。前置未满足时也实际执行四条可执行断言并保留失败/未执行原因，不让一个 fixture hard assertion 阻止后续四项记录；soft 断言只保证完整取证，任何失败仍使节点失败。

分开计算**故障来源**与**公开结果**。`faultSourceValid`只由本次精确 resolver 命中及 importer/唯一目标/root 身份、本 worker 真实顶层 throw 求值及父子身份、固定持续失败模块 ID、无缓存操纵/第二成功替身、真实默认 loader 与冷入口合同计算；不只判断 fixtureHits>0，也不直接赋 true。当前自然 hash 是否为 `#/daily`、局部安全 alert 和四断言属于 `publicTargetResult`，同次记录但**不参与来源是否有效的定义**。否则“没有错误提示”会被循环归类为“注入无效”。来源已完整而 alert 缺失仍是公开断言失败，具体原因不足可保持 unknown。P 的通过不是本次命中的替代。B 不记录逐请求 abort/内部错误槽，这些字段写未采集；不得声称某个已取消请求代表当前有效目标。

安全 DOM/console、零额外 auth/recover/provider/outbox/财务写入、root/unsubscribe/global/console 恢复等原条件保持；编写实际独立断言和边界调用观测，不能只记录 settingsWrites 或 warning.virtualFailure 布尔而不判定。检查虚拟原始错误/路径未进入公开 DOM/日志；不能从缺少监测推定零调用，也不触发真实网络或 provider。finally 使用嵌套 try/finally：即便 unmount 失败仍尝试退订及恢复，记录真实完成/未完成，不能预写全部清理成功。

## 阶段预算、工具修正与结果分流

| 阶段 | 本轮冻结上限 | 必须留证 |
| --- | --- | --- |
| controller启动root→body_enter | 15秒 | config加载、setup、测试模块及jsdom/React enter/terminal；正文未开始时不记产品断言失败 |
| 正文 | 10秒 | main/act各自终态、条件观察最多5秒、四断言及来源证据 |
| 自有资源收口 | 2秒 | 卸载/退订/恢复、root和登记worker退出，权限/超时限制单列 |
| 整个CLI | 30秒硬限 | 上述阶段及报告开销均计入，不以阶段切换重置总体截止 |

controller 用自己的单调计时器执行总体和阶段门禁；收到完整 `body_enter` 时记录本地切换时刻，worker 自己记录正文/观察耗时，不能直接拼接两进程相对时间。实际进入 finally/afterEach 时立即记录 `cleanup_enter`，无论正文断言正常完成还是异常提前结束；收到该记录才切换收口阶段，无记录时不能假定 finally 正常开始。Vitest 的外层 `testTimeout=12000` 覆盖正文和 finally，正文仍由独立阶段门禁严格限制 10 秒、UI 仍 5 秒；这不是把业务等待改成 12 秒。不要用同一个 10 秒函数 timeout 抢占单独的 2 秒 finally 收口。阶段超限立即进入有界定向收口，不能保证 finally 完成时写未核实，预算不累积借用；达到总体硬限定向结束已证明自有的树，不续时。初始化预算增加可观测性，不能宣称旧 A 根因是“时间不够”。

原生 setup/logger 在测试初始化前建立，即时 append/刷新 journal；控制器共享读取完整 newline，stdout/stderr 分开。真实完成调用才记 terminal，关键阶段不能只存在内存/finally。安全字段使用 seq/ordinal/布尔/时长/任务PID，禁止 raw Error/stack、完整 DOM/模块、token/nonce、连接 URL 或个人内容。

新 B 默认只执行一次 CLI。纯前置工具代码错误最多一次定向更正、最多一个额外前置 worker：首次源码/结果已冻结，错误已明确，固定输入不变、自有进程已退出，持久阶段加静态调用边界能证明 main/loader/fixture均未开始。缺回执或 unknown 初始化超时不是更正理由；目标已开始的实际失败不得修后重跑。静态语法/摘要小错可就地更正并记录，收口后的字段读取错误只读补证，不重启目标，不为小错再造整轮返修。

- 正文前停止：`initialization_blocked`，保留最后具体阶段，不启动 A 或接后续。
- 故障来源/冷入口不完整：接线未验证，四条结果如实记录，产品归因 unverified，不用 P 补签。
- 来源完整、公开断言失败：保存同次来源与 DOM 证据，给证据支持的产品行为结论；因果不足时保持未知，交总控裁定，不自动启动 A。
- 所有公开条件和收口通过：仅取得初始冷入口隔离证据，**同任务**进入下面续跑，不因 A 未执行再次停止；不直接宣布 LAZY-001/UI-02/P4-B complete。

## 通过后接独立恢复及剩余原24项

独立设计真实 DesktopApp/Router/Shell/compileRegistry 的恢复节点，外围 bridge 和可信页面 loader 可控；与 B 的默认生产 loader证据分列。至少两条虚拟 route，不添加生产第二业务模块。必须覆盖瞬时/持续失败、明确有限 retry 成功、无自动循环、重复点击与在途离开、健康/settings切换、render异常局部处理、主题/隐私/runtime订阅及会话保持、无额外 auth/recover/provider/outbox/财务写入。持续 throw ESM 只用于初始隔离，不要求它凭空恢复。各新增唯一节点首次运行一次，失败保留，不复制开发八项充当独立证据。

新 lazy 开发八项及必要 Shell/composition 相邻兼容各文件一次、单列，不重跑完整132、未改 registry52、已过27独立/outbox42/setting/PATH、后端或P0～P3全量。恢复通过后接 [原 R4 剩余范围](p4-c12-r4-lazy-windows-tester.md)的公开缺口及 Windows；原要求完整保留，缺条件不预写通过。

新外部虚拟根 `C:\MarisC12\C12-R5-PUBLIC-<时间戳>`，创建/清理前核对解析绝对边界和无 reparse。固定 EXE 只读，Node spawn(shell:false)直接启动；Playwright 仅 CDP附加，不 Electron launcher/app.asar loader/PID提升/生产inspect fuse。产品最多8次、各<=120秒；辅助safeStorage最多4次、各<=60秒；每次计划对应实际未覆盖场景，不用满预算、不重复正常smoke。每次外部操作前重读 control。

真实 Windows chunk 故障仅对本轮 owned 页面/会话的实际目标请求临时注入，保留命中、失败与撤销后重试恢复；不能改 EXE/asar/resources或删除chunk。若 file/asar/CDP阶段不支持、缓存使故障不可控，记录具体未核实条件，不追加盲启动，不用 jsdom 顶层 throw替代网络404。真实session只用新虚拟owner/profile，文件存在不替代会话故障保持证据。

真实原生老化提示使用本轮虚拟safeStorage seed/read和限定owned PID/标题/按钮的自动化，默认保留/取消/关闭与明确删除分别取证；普通双窗口不替代提示。真实Tray、closePolicy、单实例与持久设置按原清单验收；未授权注销/重启/启动项/多屏/改OS主题或要求用户点击只记人工缺口，不自行操作。不访问个人AppData、OpenClaw/微信/真实provider、Docker或PostgreSQL。

## 交付、资源与停止

root/worker所有权按创建句柄、固定exe、时间窗、父子关系与新虚拟根建立，不要求任意精确进程数或全系统枚举才能启动。只定向结束自有进程，不按名称批量kill，不把权限拒绝后的空集写零；父exit不复制给worker。无法证明收口则停止扩大并保留核实范围，未知全系统状态不伪造。

报告给出 B 的来源/冷入口/四断言、安全条件和实际阶段，独立恢复与兼容分列、原24项完整预期/已有证据/本轮与具体缺口、真实Windows启动/注入数、工具修正/首次失败/warning、起终输入和交付摘要。旧材料不倒写，矩阵整项只有满足所有原条件才passed；缺陷关闭建议与完整UI-02/P4-B分开，最终接受属于总控。

新P0/P1、泄密、不受控弹窗、未知ownership、无法收口或同一问题连续两个检查点无新输出，立即停止扩大并安全交接；不用等待循环或自动新建后续任务。按AGENTS记录接单、里程碑、长操作检查点与十分钟心跳，只更新tester。最终只能 `review / finished` 或 `blocked / finished`，停止由总控接手；没有 Git 写权限，不进入 P4-C/D。进入真实前端前的设计/模型/token提醒门禁保持。
