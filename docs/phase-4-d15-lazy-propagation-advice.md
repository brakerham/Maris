# P4-D15：模块异常传播链有限诊断与后续范围建议

日期：2026-10-03，Asia/Shanghai。角色：既有技术顾问，唯一负责人。

**交付状态：`blocked / finished`。动态诊断已按预算停止，供总控审阅；没有完成独立验收。**

本轮证实两段真实链路：原页面模块的 mock factory 抛错可以令直接动态 import 拒绝；生产 `createModuleRoutes` 的默认内置 loader 也能接收该拒绝，并映射成 `desktop_module_unavailable`。两项均立即产生终态。第三项生产入口观察在进程硬限前没有回执，不能据此确定 Router 错误发布或 DOM 提交的终态，也不能据此认定产品或任何框架是根因。

旧 `P4-C12-R3-LAZY-001` 不关闭，`P4B-UI-02` 与 P4-B 不宣布通过。不存在新定级产品缺陷。技术顾问不创建后续 Prompt/接口冻结、不进行产品返修、不重跑旧测试或打包。

## 1. 权威输入与边界

最新 control 版本 `2026-10-03T00:13:00+08:00` 将 D15 分配给既有技术顾问，用户发送任务卡解除等待。测试 R4-R1 与执行方均已停止；本任务不调用其他智能体。

起点 [p4-d15-start.sha256](coordination/snapshots/p4-d15-start.sha256) 共 **429 项，429 matched，0 changed / missing / invalid**，暂存区为空。清单 SHA-256：`583d21945b0d1e307374f34f4cca04f88fb4d862cad32c2e09844f017b7e43af`。

按顺序读取 AGENTS、README、项目协调、台账规则、control、自身角色与 D15；随后核对以下实际输入：

- [总控 R4-R1 核对](p4-c12-r4-r1-propagation-coordinator-review.md)、[R4 报告](testing/phase-4-c12-r4-lazy-windows-report.md)、[R4-R1 报告](testing/phase-4-c12-r4-r1-observation-windows-report.md)。报告中的原24项要求继续有效，原矩阵与报告没有修改。
- [R4-R1 原观察节点](../tests/independent/desktop/r4-r1-observed.test.tsx)、[其配置](../tests/independent/desktop/r4-r1-vitest.config.mjs)、[首次回执](../tests/independent/desktop/evidence/r4-r1/observation-receipts.json)、首次双轮运行日志，以及 [R4 原配置](../tests/independent/desktop/r4-vitest.config.mjs)、[原 R3 故障节点](../tests/independent/desktop/r3-remaining.test.tsx)。全部只读，未执行。
- [R5 任务](coordination/prompts/p4-b7-r5-lazy-executor.md)、[R5 运行说明](b7-r5-lazy-running.md)、生产 main/module-routes/Shell/registry/contribution，以及 [开发 lazy 八项](../apps/desktop/tests/unit/lazy-isolation.test.tsx)。未复跑八项或完整132项。

允许写入只有本文、自身角色文件、`docs/coordination/diagnostics/p4-d15/**`。产品、旧测试/证据/报告/矩阵、依赖/lock/生成物、Forge/package、迁移、冻结、control/overview/snapshot、其他角色和 Git 状态只读。

## 2. 实际版本与模块解析

只读核验并复用任务卡指定普通环境 `C:/MarisLazyR5/R5-20261002-222300`；没有创建或修改该外部根。

| 项目 | 本机实际版本 | 核验方式 |
| --- | --- | --- |
| Node | 24.21.0 | 任务指定 Node executable 的 version 输出与文件摘要 |
| Vitest / @vitest/mocker | 5.0.2 / 5.0.2 | R5 普通依赖 package.json |
| Vite | 7.3.6 | 同上 |
| React / React DOM | 19.3.0 / 19.3.0 | 同上 |
| React Router | 8.4.0 | 同上，核对实际 exports 与安装实现 |
| jsdom | 30.1.1 | 同上 |
| TypeScript | 6.0.3 | 仅用于新探针语法检查，没有执行项目 typecheck/build |

精确摘要见 [baseline.json](coordination/diagnostics/p4-d15/baseline.json)。专属 [配置](coordination/diagnostics/p4-d15/vitest.config.mjs) 与 R4-R1 采用相同依赖根、单一 React/React DOM/Router 别名、automatic JSX、node 环境、fork worker；只更换新 root/include/cache。三个不同测试文件由三个独立 CLI/worker 隔离，未提前导入目标页面、未 resetModules、未换版本。

官方网页只用于核对 API 语义，**不是冻结安装版本源码的替代品**；网页可能随着主线更新，不能以网页存在某个 API 宣称本机分支已经执行。实际机制结论优先使用本机上述版本实现和本轮回执。

## 3. 静态生产链与旧观察缺口

| 层 | 精确代码位置 | Promise / 状态 / 边界 | 旧 R4-R1 有何证据，尚缺什么 |
| --- | --- | --- | --- |
| 入口 | [main.tsx:7](../apps/desktop/src/renderer/main.tsx#L7) | compileRegistry 后 createRoot，以 StrictMode 渲染实际 DesktopApp | 确认使用真实入口；未记录本次入口动态 import 终态以外的路由加载链 |
| 可信模块交集 | [module-routes.tsx:104](../apps/desktop/src/renderer/module-routes.tsx#L104)、[registry.ts:51](../apps/desktop/src/modules/registry.ts#L51) | runtime/module list 异步取得；active 标记拒绝卸载后的更新；intersectModules 过滤启用、major、Profile、API prefix、settings schema | 虚拟 Host 摘要合法，runtime/list 两次符合开发 StrictMode；不证明 loader 完成 |
| Router 创建与清理 | [module-routes.tsx:113](../apps/desktop/src/renderer/module-routes.tsx#L113) | 等 hostModules 后 createHashRouter；effect cleanup 调用实际 next.dispose | 公开 hash 已到 daily；没有实际 Router 对象、initialized/navigation/matches/errors 终态 |
| index 导航 | [module-routes.tsx:89](../apps/desktop/src/renderer/module-routes.tsx#L89) | ModuleIndex 返回实际 Navigate，选择贡献首路径 | 到达 hash 只表示路径变化，不保证导航请求完成 |
| 内置动态 import | [module-routes.tsx:10](../apps/desktop/src/renderer/module-routes.tsx#L10) | 固定 daily_finance_home → await 原 DailyFinancePage 的 import → default | factory 命中1次；未记录调用该 import 的 Promise 已 resolve/reject/pending |
| 实际 route.loader | [module-routes.tsx:63](../apps/desktop/src/renderer/module-routes.tsx#L63) | attempt++；await 可信 loader；catch 原异常后重新抛固定安全 Error | 静态 catch 存在；未记录该次 loader 进入及终态，不知道错误是否被当前 Router 接收 |
| 局部错误路由 | [module-routes.tsx:75](../apps/desktop/src/renderer/module-routes.tsx#L75)、[module-routes.tsx:34](../apps/desktop/src/renderer/module-routes.tsx#L34) | 模块子 route 配置 ModuleLoadError；useRevalidator 只供明确点击重试 | 静态 errorElement 存在；未记录对应错误槽，不知道当前生效的是哪个边界 |
| 内容区域与渲染边界 | [Shell.tsx:16](../apps/desktop/src/shell/Shell.tsx#L16)、[module-routes.tsx:38](../apps/desktop/src/renderer/module-routes.tsx#L38) | Shell 的 .content 内 Outlet；成功 Page 的 render 错误由类边界捕获 | Shell/nav/Agent 存在可能来自当前页面或 hydrateFallback；不是错误已处理的证明 |
| 安全提示 DOM | [Shell.tsx:37](../apps/desktop/src/shell/Shell.tsx#L37) | RouteErrorBoundary 输出 role=alert 与固定提示，不展示原 message | 5016ms 无 alert；只证实该观察失败，不能确定是哪一上游层阻塞 |

生产根的 `onCaughtError` 只记录 `desktop_render_unavailable`。它处理 React 捕获的渲染异常；模块导入失败先走 loader/Router，不能要求每次 import 失败都必须触发该日志。

R4-R1 的 node 环境手工安装 JSDOM window/document/location 和 `IS_REACT_ACT_ENVIRONMENT`，使用真实 React act，保留生产 StrictMode。它增加了 VirtualConsole、console 与 window unhandledrejection 的安全观察，并在 finally 卸载 root、恢复 global、清理订阅；这些是旧现场的有效证据，但不是路由状态回执。

[StrictMode 官方说明](https://react.dev/reference/react/StrictMode) 中的开发 effect 再执行解释了旧 bridge 计数为何可以是2；本轮没有据此认定 StrictMode 是根因。[act 官方说明](https://react.dev/reference/react/act) 说明如何完成测试中的 React 更新，也不保证任意外部模块请求一定结算。长时间 await 一个尚未完成的外部 import，和已发布路由状态能否提交 DOM，是两个观察问题。

## 4. 安装实现的只读核对

以下都是**源码推断**，不冒充第三项运行结果：

1. `@vitest/mocker/dist/chunk-registry.js:168` 的 ManualMockedModule.resolve 调用 factory，并在同步 throw 或异步拒绝时包装错误，保留 cause。`vitest/dist/chunks/index.hTNFpC24.js:329` 的 callFunctionMock 会 await 该 resolve；请求路径继续由模块 runner 的异步调用传播。包装改变异常外形，不足以推断拒绝消失。[vi.mock 官方语义](https://vitest.dev/api/vi.html#vi-mock) 也明确其提升与异步 factory 行为。
2. `vite/dist/node/module-runner.js:1100` 附近的 dynamicRequest 解析路径后调用真实 request/cachedRequest。它不是简单把所有失败转成成功页面的后门；是否完成仍须实际回执。
3. `react-router/dist/development/lib/router/router.js:2446` 的 callLoaderOrAction await 实际 handler，捕获拒绝并形成 error result；有 abort race。错误终态必须属于仍生效的导航，不能拿另一请求的错误当当前 route 已发布。
4. `react-router/dist/development/lib/components.js:121` 的 RouterProvider 订阅真实 Router；正常更新可交 React startTransition。存在 transition 只解释提交机制，不能证明它阻止了这次错误页。
5. 本机 Router8.4.0 的 package exports 入口是 `dist/development/index.js` 等实际条件分支，不是旧版本可能使用的 index.mjs。只读猜测 index.mjs 不存在已记录，后续按 package.json 修正读取，未因此重跑目标。

上述文件位于任务指定 R5 node_modules，完全只读。可见 [Router 错误边界官方说明](https://reactrouter.com/how-to/error-boundary) 的最近边界原则，但本产品使用 data loader/errorElement，不能拿网页 Framework Mode 示例替换实际 Router 装配。

## 5. 首次探针、冻结方式与真实次数

[冻结计划](coordination/diagnostics/p4-d15/probe-plan.md) 与8个源码在目标前生成 [probe-source.sha256](coordination/diagnostics/p4-d15/probe-source.sha256)，其 SHA-256 为 `583897cd18ecc891000f036fddaa802e551f62c8c76c081ca109c66ae7e8a3fd`。新TS四文件、MJS配置及PowerShell controller语法通过；该检查不代表类型全面正确或业务行为通过。

一次 [run-once.ps1](coordination/diagnostics/p4-d15/run-once.ps1) 会话内依次运行 P1/P2/P3。实际会话 **22,663ms**，三个 CLI 各1次、0重试。每项观察上限5秒、Vitest testTimeout10秒、单CLI硬限15秒包含模块加载与退出，总会话上限60秒。没有精确总进程数量阈值。已有 results 目录会令 controller 拒绝再次启动。

| 探针 | 实际原操作与结果 | 首次过程/证据 | 诊断结论与限制 |
| --- | --- | --- | --- |
| P1 | 原 factory1次；直接 import 当毫秒 reject；Error 为 Vitest wrapper，虚拟 cause 匹配；观察结束23ms | [p1.json](coordination/diagnostics/p4-d15/results/p1.json)、[stdout](coordination/diagnostics/p4-d15/results/p1.stdout.log)、[process](coordination/diagnostics/p4-d15/results/p1.process.json)；CLI4069ms、exit0、stderr0 | 该隔离实例拒绝传播正常；没有 Router/UI，不倒推旧现场 |
| P2 | 真实 compileRegistry/贡献/default内置loader；factory1次；loader在1ms reject且安全code匹配；观察结束31ms | [p2.json](coordination/diagnostics/p4-d15/results/p2.json)、[stdout](coordination/diagnostics/p4-d15/results/p2.stdout.log)、[process](coordination/diagnostics/p4-d15/results/p2.process.json)；CLI3443ms、exit0、stderr0 | 同一产品 loader 具备拒绝映射能力；没有启动 Router，不证明导航中的活跃请求结算 |
| P3 | 已启动一次CLI；只得到RUN横幅，没有观测JSON；15秒进程硬限后停止 | [p3.stdout.log](coordination/diagnostics/p4-d15/results/p3.stdout.log)、[p3.stderr.log](coordination/diagnostics/p4-d15/results/p3.stderr.log)、[p3.process.json](coordination/diagnostics/p4-d15/results/p3.process.json)；15051ms、timedOut=true、root实际exit-1 | **unknown / blocked**；没有P3的factory、loader、Router、DOM或finally证据，不推断具体阻塞层 |

51ms是进程调度/终止核验尾差，未提高时限。P1/P2 stdout 中“1 passed”只是各自诊断脚本完成，**不计独立验收案例**。P3没有测试结果报告，不能记为一个已复现产品断言失败，也不能猜测是收集阶段还是测试body阶段。

### P3 观察包装与回执缺陷

[P3 源码](coordination/diagnostics/p4-d15/p3.test.tsx) 计划通过 async importOriginal 取得真实 react-router，然后只包装其 createHashRouter 导出。转发原参数数组中的相同 route 对象、不替换 errorElement、不改变真实返回 Router。专用 loader 包装以 Reflect.apply 转发 this/实参，原样返回原 Promise，旁路 then 记录安全终态；不 await 后造新 Promise、不吞错、不制造另一条 reject、不导航/revalidate/刷新。

这仍增加函数身份和记录微任务，可能轻微改变时序，必须作为测量局限。其设计不能直接认定已经成功运行，因为第三项没有回执。

**本轮观察实现本身还存在一个明确的取证缺口：入口/factory/loader/Router/DOM时间线先保存在worker内存，只在finally末尾统一落盘。** 一旦阻塞或硬限终止，早期事件无法保留下来。因此，P3没有JSON既不证明body没开始，也不证明main或root没启动。该观察失败不能混入原产品缺陷，更不能把“无JSON”写成已证实 mock importOriginal 死锁。

首次超时之后没有改冻结源码或重跑P3，未使用“目标前配置错误例外”增加预算。此缺口连同首次结果交总控；它是新诊断的证据完整性问题，尚不是独立测试接线根因裁定。

## 6. 按证据逐层裁定

| 因果层 | 当前事实等级 | 支持证据 | 反证/剩余unknown |
| --- | --- | --- | --- |
| 原factory是否执行 | 旧R4-R1是；P1/P2分别是；P3未知 | 旧receipt与两项新faultHits=1 | 工厂次数不能代替调用方Promise终态；三worker互不互证 |
| direct import拒绝能否传播 | P1已证实能 | P1 reject、mockWrapper/virtualCause布尔 | 排除该隔离配置中“包装后普遍吞拒绝”；不证明旧生产入口import拒绝 |
| 实际默认loader能否映射拒绝 | P2已证实能 | P2 defaultBuiltinLoader、routeTarget、安全code、1ms reject | 排除该隔离调用中catch漏接/返回成功；不证明生效导航loader终态 |
| 生产入口中loader属于哪次Router导航 | unknown | 静态main装配正确；旧hash到daily | P3无终态，无活跃Router/abort/请求关联回执 |
| Router当前错误槽是否发布 | unknown | 静态handler会产生error result，子route有errorElement | P3无errors/matches/state，不认定Router或transition故障 |
| 安全错误页是否进入Outlet并提交DOM | 旧R4-R1观察失败；D15 unknown | 旧5016ms无alert、Shell/nav/Agent存在 | 可能显示hydrateFallback或其他阶段；未证实到达错误页分支 |
| P3观察通道是否完整启动 | unknown，诊断环境阻塞 | 仅RUN、硬限退出，无worker回执 | 没有增量落盘入口证据，无法精确区分collect/mock/bootstrap/main阶段 |

有依据的候选假设如下，不把任意一项写成已确认根因：

| 假设 | 支持 | 反证/不足 | 裁定 |
| --- | --- | --- | --- |
| Vitest包装导致所有原import拒绝消失 | 本机确实包装factory异常 | P1实际reject且cause匹配，P2实际安全reject | 普遍性说法被本轮反证；特殊入口关系仍unknown |
| 生产loader的catch没有正确映射异常 | 旧无alert可能引起这种猜测 | P2实际调用该函数已正确映射 | 不支持据此返修loader |
| 旧测试只等待200ms是唯一原因 | 旧R3/R4等待较短 | R4-R1已5016ms仍失败 | 不支持继续延长等待 |
| Router/React错误发布或DOM提交有问题 | 旧有错误factory却无UI，静态存在状态提交层 | 没有当前错误槽/loader关联；P3取证失败 | 保留unknown，不定P1或修改产品 |
| 新P3观察包装或其模块bootstrap阻塞 | 新增async importOriginal和whole-module观察包装；P1/P2正常而P3只有横幅 | 没有包装开始/原导出返回/body入口增量回执 | 优先检查取证通道，不宣称具体库bug或死锁 |

## 7. 为什么开发八项通过与入口观察失败不矛盾

开发 transient/persistent/pending/render等节点把虚拟 `ModulePageLoaders` 传给真实 DesktopApp。它们运行真实 Router、Shell、边界、重试和状态保持，用可控 Promise 验证“一旦 loader 交付拒绝，局部处理及明确恢复如何工作”。这条链有价值，既不是伪Router，也不是独立验收。

开发“actual production entry”节点只覆盖内置页面导入的**成功**路径。它没有用原模块factory throw去证明真实main首次错误链。独立R4-R1则使用默认内置loader、原模块mock、真实main/StrictMode，恰好覆盖这段未被上述可控loader故障节点证明的接线。两类输入与测量不同，因此可以同时出现开发通过与独立无alert。

D15-P2把真实内置loader拒绝能力补成新证据，但没有补齐入口导航→Router错误槽→DOM。不能用开发八项、132项、正常EXE19项或P1/P2替代原四条独立断言。

## 8. 唯一下一观察问题与最窄后续范围

**选择“仍unknown，先修正观察证据完整性”分支。当前不建议产品返修，也没有足够证据裁定旧测试接线有错。**

唯一下一观察问题：**生产入口观察通道是否已越过真实 react-router 导出解析并到达 main 启动入口？**

最小缺失条件是同一隔离worker的几个前置阶段事件即时、安全落盘：worker/body入口、观察包装开始、actual导出返回、main import开始。它们只用于回答上述一个问题。只有能证明通道已就位，原loader/活跃Router错误槽/DOM阶段事件才可作为产品传播归因证据；本轮P1/P2不能补签这项前置条件。

交总控决定的窄范围仅为**诊断通道的前置回执与增量证据合同**。若以后授权观察修正，保留本轮冻结源码/首次超时和旧独立证据，用全新授权记录，不能本轮修后重跑或称D15已定位根因；不换框架、不加调试hook到产品、不延长时限、不重打包、不启动Electron或自动建立新任务。

以后得到生产链终态才能择一冻结，以下只是条件性建议，尚未授权实施：

- 若实际入口中原import未拒绝或拒绝未送入loader，修正最小模块mock/解析/观察接线，保留真实main、真实默认loader与原断言。
- 若同一次活跃loader已安全reject但Router没有对应错误槽，定位该次导航/abort/Router装配的精确位置，再由总控裁定窄产品或观察修复。
- 若错误槽已发布且目标匹配、仍无内容区alert，再定位模块errorElement/Outlet/React提交。用户无法获知失败且模块入口受影响时可建议P1，但**当前证据不够，不能现在定级**。

四条原业务断言继续保留：alert含“页面暂时无法打开”、main.shell存在、模块导航存在、统一Agent面板存在。不放宽为“Shell仍在就通过”，不skip/xfail。之后的明确重试、持续失败不循环、健康/设置导航、主题/隐私/runtime/订阅与无额外写入也不能因四条静态存在而删减。

本轮可以排除的范围仅有P1/P2各自隔离实例的导入拒绝和安全映射故障；P3入口实例、旧现场、真实Windows chunk故障、会话持久化、全部UI-02恢复要求继续未验证。

## 9. 收口、权限限制与首次失败保留

controller 使用 ProcessStartInfo/ArgumentList、双流异步捕获与真实exit，timeout时对自己启动的root调用 Kill(entireProcessTree:true)，没有按进程名杀进程，没有使用Job或总进程数阈值。P1/P2登记worker PID/parentPID与root一致，CLI和worker均已退出。P3root硬限后actual exit=-1，worker/finally回执缺失，不能声称正常卸载root/订阅/DOM/global。

只读CIM枚举曾返回“拒绝访问”，它后面的空集合是无效结果，**不得写成零残留证明**。替代的Get-Process元数据读取显示所有可见node路径可读，零个使用固定R5 Node executable，三个已知root及两个已登记worker均不存活；其他node均早于诊断会话且路径不属于R5。证据见 [resource-observation.json](coordination/diagnostics/p4-d15/resource-observation.json)。这支持固定Node进程已退出，不是完整进程 ancestry、P3正常finally或设备级收口验收。

P3源码的finally设计包括真实root unmount、bridge订阅归零、Router观察取消、显式dispose已保存的真实Router、MutationObserver断开、DOM关闭和globals/console恢复。显式观察层dispose只是额外幂等收口，不能冒称动态记录了产品effect的dispose调用；本轮甚至没有执行回执，设计不能填写成通过。

首次stdout/stderr/exit、session、P1/P2结果全部保留。P3没有伪造p3.json补齐。只读查询可选@vitest/runner和旧index.mjs路径不存在、CIM权限失败均记录为检查警告，不当成目标产品缺陷，不触发安装或重试。任务会话未运行Electron/EXE/sidecar/Windows产品、旧独立节点、开发回归、Docker/PG/OpenClaw/微信/provider；package、产品启动和外部服务操作均0。

只使用虚拟数据；异常只保存类型分类、固定安全code/虚拟cause布尔，不保存Error对象/stack、个人资料、端口、token、nonce、profile/session/db、原消息或完整DOM正文。CLI日志仅对已知D15/R5固定根做脱敏替换，首次stdout/stderr分开保留。

## 10. 交付与总控交接

- 新诊断源码、冻结预期与首次证据均在 [D15专属目录](coordination/diagnostics/p4-d15/probe-plan.md)，不进入任何测试方或开发测试目录。
- [输入不变与边界核对](coordination/diagnostics/p4-d15/end-audit.json)：固定输入429/429全部未变。权威起点未包含技术顾问角色文件，本角色授权更新另列，不能误报为429项中的一个变化；新D15文档/诊断另列。外部构建source389/389、out140/140、固定Node与8个包元数据摘要全部匹配；未复验完整依赖图。产品、旧测试/证据、控制、快照、依赖/lock/外部R5内容无写操作。
- [交付逐文件摘要](coordination/diagnostics/p4-d15/delivery.sha256) 包含新文档、新诊断源码/脱敏记录与本人角色；排除该清单自身。冻结probe清单保持首次原值，不随结果重写。
- 仅验证解析绝对边界在专属根内且无reparse后清理本轮temp缓存；保存源码及首次结果，清理证明另存专属目录。末尾机械校验/清理/摘要以最终角色日志与对应证据为准，不倒写为目标运行时完成。

总控收到的是两段已证实链路、一次P3有限诊断超时、明确的取证缺口和唯一下一观察问题。目标传播归因仍被P3通道证据阻塞，故停在`blocked / finished`；本文可审阅但不冒称任务根因定位已完成。之后由总控决定是否授权最小观察修正、旧测试接线或产品返修。技术顾问停止，不关闭LAZY-001/UI-02/P4-B，不建立D15-R1、IF或执行/测试Prompt，不执行任何Git写操作。
