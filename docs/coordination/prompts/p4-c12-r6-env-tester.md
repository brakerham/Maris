# P4-C12-R6-ENV：原生加载测试环境并继续公开独立验收

你是既有测试智能体，本任务唯一负责人。R5-PUBLIC 已停止，首次记录只到 jsdom 导入等待，产品 main/故障模块/四断言均未执行。本任务授权修正自己的测试基础设施，并在同一任务继续公开 B；不修改产品，不先重做 P、A、D16 或其他极小依赖实验。

## 输入与文件边界

先按 AGENTS 读取 README、project-coordination、coordination/README、最新 control、本人 tester 状态和本卡，再读 [本轮总控裁定](../../p4-c12-r5-public-initialization-coordinator-review.md)、[R5-PUBLIC 报告](../../testing/phase-4-c12-r5-public-windows-report.md)及[原 R5-PUBLIC 合同](p4-c12-r5-public-tester.md)。本文替换其 jsdom 加载、初始化预算、文件命名及交付形式；其余明确保留的业务/安全/后续条件不降级。

开工复算 [本轮起点](../snapshots/p4-c12-r6-env-start.sha256)，基准仓库根、UTF-8 无 BOM、路径排序、`path<TAB>sha256<LF>`。检查唯一负责人、staged=0，登记接单和执行快照。复算 R5-PUBLIC 41 项交付、10 项源码及6项首次材料，基准分别为仓库根、desktop测试目录、仓库根；只读保留原字节和行尾。

工具与产品继续只读复用 `C:\MarisLazyR5\R5-20261002-222300`：Node24.21.0、Vitest5.0.2、Vite7.3.6、React/DOM19.3.0、Router8.4.0、jsdom30.1.1、TS6.0.3、普通 node_modules。核对既有源码389/out140/资源67和依赖清单，不能换工具、安装依赖或改 lock。EXE/asar/lock 摘要与原 R5 卡一致。

唯一可写集合：

- 新 `tests/independent/desktop/r6-env-*`，用于测试、setup/resolver/fixture/config/controller/reporter及必要核验；新 `tests/independent/desktop/evidence/r6-env/**`。临时缓存也只能在本轮新范围。
- 新报告 `docs/testing/phase-4-c12-r6-env-windows-report.md`。
- 本人 `docs/coordination/agents/tester.md`；原 C12 主报告及人工清单仅追加，原字节前缀保持；矩阵仅 P4-B 实际状态/备注，120 ID、12列、原预期及A/C/D保持。

产品、开发测试、所有旧独立源码/evidence、顾问材料、依赖/lock、包、migration、control/overview/snapshot和其他角色只读。无 Git 写权限。不 install/download/build/package，不改系统设置、代理/TUN/PATH/时钟/安全软件/fuses，不用真实个人 profile、账户或财务数据。

## 本次唯一环境修正

保持 node 环境、fork、maxWorkers1、isolate、新缓存及新 worker；不改为标准 jsdom environment，不换 DOM 库，不改 React 的加载渠道。

在新 setup 的原生日志建立之后、测试模块加载之前：

1. 用 Node 内置 `createRequire`，以固定 R5 `workspace/node_modules/jsdom/package.json` 的绝对文件 URL 为锚点。先只读核对 package 的版本、type、main及对应文件摘要；`require.resolve` 的真实路径必须精确指向同一个 `jsdom/lib/api.js`，不回退系统/用户安装。
2. 即时记录 `native_jsdom_enter`，通过这个原生 require 加载同一 API，成功/拒绝立即记录 terminal。捕获错误仅写安全类型/code白名单，不把 raw stack/正文写入公开日志。
3. 给本 worker 的测试提供原始 JSDOM、VirtualConsole 引用，只允许持有原引用的浅容器；不得包装构造器、伪造 DOM、替换 API 或冻结第三方对象改变其行为。测试不再执行 `await import('jsdom')`。
4. 正文之前不创建 DOM。正文继续按原方案构造全新 DOM/虚拟 bridge；React/ReactDOM/Router 的真实单根解析保持。产品 main、module-routes、contribution、页面和 Router 在正文前不得求值，不原生 require 产品或 React 来“预热”。

保留 native configLoader、固定 aliases（移除已不用的 jsdom alias可行）、真实 Router subpath、原精确 resolver 语义。新源码做静态差异表：只允许本卡环境入口、新标识/路径、预算及明确记录的工具更正；产品/路由/故障行为断言变化不在本次授权内。不要安装框架内部 RPC hook，也不要修改 node_modules 做诊断。

该改变绕开本次 jsdom 通过 Vite 测试模块导入的入口，但不是已验证修复。原生 require 可能阻塞事件循环，不能只靠 worker 内的 Promise timeout；外部 controller 必须定向管理截止与登记进程。不要把原生 require 成功外推成 React 或产品已经可用。

## 同一次运行取得公开 B

新节点 `R6-ENV-UI-02-COLD`，最多一次实际 main 启动。新 setup、fixture、resolver、日志全部使用本轮路径，不能导入会写旧目录的工具。先静态核验并冻结源码，再启动这个实际节点；不先运行仅加载依赖的练习节点或 P 验证。

以下原 R5 公开合同完整继承：

- 精确目标 ID/importer 映射；零 import/零 JSX 的真实 ESM 持续 throw；无 vi.mock/doMock、二次成功替身、cache reset/bust、getter替身或网络造成功。旧 P 只作背景，本次必须取得自己的来源。
- 实际 main/StrictMode/默认 loader/真实 Router、初始空 hash 与原 URL，真实 contribution/Host intersection。只导入 main 一次，main import 与 React act 各自记录 enter/terminal；不额外 navigate、revalidate 或 recover。
- 同次 `#/daily` 的 `main.shell .content [role="alert"]` 安全错误提示、Shell、Shell内模块导航、Shell内统一Agent面板四条原断言都执行并保留结果；任何一条失败仍使节点失败，不因 soft 断言方式补签通过。
- `faultSourceValid` 由本次精确映射、真实 throw、root/worker身份、固定持续模块和冷入口合同计算；当前 hash、alert及四断言是另列的 `publicTargetResult`，不能把缺alert循环归类为来源无效。
- DOM/console隐私、原始错误/路径不泄露、额外auth/recover/provider/outbox/财务写入为零，必须有真实观测与断言；禁止用未监测推定零。
- 嵌套 finally 清理真实 root/订阅/console/global/DOM，即便一项失败仍尝试其他项。不得预写清理成功，不采集或伪造内部 Router/abort 字段，不包装生产 loader。

## 预算与有限更正

| 阶段 | 新上限 | 记录要求 |
| --- | --- | --- |
| controller启动root至body_enter | 60秒 | config、worker/setup、native_jsdom enter/terminal、test_module、React enter/terminal；不等于产品时限 |
| 正文 | 10秒 | main/act、故障来源、公开与安全断言；UI条件观察仍最多5秒 |
| 自有收口 | 2秒 | 实际进入finally时记录cleanup_enter，逐项完成/未核实 |
| CLI总计 | 75秒 | 含阶段/报告/强制收口；不得按阶段重置总截止 |

Vitest函数外层仍12秒覆盖正文10秒与finally2秒，不能由其替代初始化控制。controller独立单调时钟，收到完整body/cleanup记录才切换阶段；不拼接不同进程相对时间、不借用清理额度延长业务观察。阶段停止给总限预留有界收口；可能持续超过一分钟的CLI用可观察会话，期间报告最新具体阶段，禁止阻塞工具等待超过60秒而无更新。

新 CLI 默认一次，实际 main 总预算1。若发生有明确因果和修复的纯工具错误，且首次持久记录及静态边界证明main/loader/fixture未开始、输入不变、自有进程退出，可在**本任务内**更正一次并用新attempt目录再启动；总CLI最多2、main仍最多1。修正前冻结首次源码和结果，不覆盖。未知初始化超时不满足更正条件；不得纯粹延时/重复来碰运气，也不因收口字段读取小错重启目标。静态语法/路径/摘要核验允许就地修正并保留说明，不另建任务。

本轮同时改变加载入口与初始化预算，属于恢复验证；通过也不能宣称旧超时充分根因已定位。若无返回，记录究竟停在native_jsdom、React、body或main，并按初始化/注入/产品/清理层级分开结论。不能把未来成功倒写进旧15秒首次结果。

## B通过后在本任务继续

B全部业务、安全和收口要求通过后，直接接原 [R5卡“通过后接独立恢复及剩余原24项”](p4-c12-r5-public-tester.md)与 [R4剩余要求](p4-c12-r4-lazy-windows-tester.md)，不等待A、不再单独请求派发。新恢复节点使用同一已验证环境加载方式，真实DesktopApp/Router/Shell与可控可信loader；覆盖原卡的瞬时/持续失败、显式retry、无自动循环、重复点击/在途离开、健康/settings切换、render异常、状态订阅保持与零额外写入。

开发lazy八项及必要Shell/composition各文件一次、兼容单列；已过集合不重复。Windows固定EXE仅在前置通过后使用新虚拟根 `C:\MarisC12\C12-R6-ENV-<时间戳>`，创建/清理前核对绝对边界和无reparse。Node spawn(shell:false)直接启动，Playwright只CDP附加；产品最多8次各120秒、辅助safeStorage最多4次各60秒，按未覆盖场景使用且不为耗尽预算重复smoke。每次外部操作前重读control。

原Windows chunk/session/老化原生提示/Tray等要求、禁止系统注销重启或擅改启动项/主题/多屏及用户操作边界全部继承。实际不支持的故障注入据实未验证，不拿jsdom替代实机，不重复微信V002、Docker、OpenClaw或真实provider。

## 交付与停止

新报告写本次增量及可核查证据，链接原24项完整映射，逐项说明本次状态/剩余缺口，**不必再复制24项的全部历史叙述**。启动次数、main次数、阶段耗时、原生依赖真实身份、四断言/安全断言、环境修正、首次结果、资源核实范围和输入/交付摘要必须齐全。精简辅助脚本和重复清单，禁止为报告完整重启目标。

进程所有权依创建句柄、固定exe、时间窗、父子关系建立，登记root/worker的实际退出；不设任意精确进程数、不按名批量kill、不把权限拒绝后的空集写零、不复制父退出码给worker。历史全系统不可枚举可保留限制，但已登记自有进程收口失败须停止扩大。

正文前阻塞、来源不完整、真实业务失败或清理不足分别记录；新P0/P1、泄密、不受控弹窗、未知ownership、无法收口或同问题连续两个检查点无新证据时停止扩大。不得自动追加A/D16/R7或调高预算；首次材料保持。最终仅 `review / finished` 或 `blocked / finished`，由总控审阅，不自行关闭LAZY-001/UI-02/P4-B，不开始P4-C/D。进入真实前端前提醒参考图/模型/token策略的门禁保持。
