# P4-C12-R4-R2：取消请求与有效请求分离的总控核对

核对时间：2026-10-03 03:53，Asia/Shanghai。角色：头脑风暴总控。

## 本轮接受的事实与未接受的结论

接受本轮 `blocked / finished` 交付和传播证据，不接受 LAZY-001、UI-02 或 P4-B 为通过。真实冷 main 和 act 已完成；同一个 Router 的第一次页面加载被取消后安全拒绝，第二次未取消的加载成功。当前页面没有对应错误槽，因此没有错误提示。这是本轮故障前置条件没有建立，不是已证实的新增产品缺陷。

旧 R4/R4-R1 的原因、是谁触发取消和再次加载、第二次导入实际走过哪个内部分支，仍未证实。本轮记录不能倒填旧失败。执行方 R5 的局部隔离实现、自测和包保持不变，继续等待独立验证。

总控及两个只读子任务核对摘要、原始记录、生产代码与固定工具源码，没有运行测试、诊断目标、Electron、EXE、服务或 package；子任务结果由总控汇总。原测试方日志及首次失败保持原样。

## 交付、输入与实际执行

| 对象 | 实际核对 |
| --- | --- |
| [新交付](../tests/independent/desktop/evidence/r4-r2/delivery.sha256) | 37/37 匹配、路径唯一；SHA-256 `6b2871f4275cf3eb49a7dd8850a5bb72067add69465f6e1bf804294c07b034bd` |
| [507 项起点](coordination/snapshots/p4-c12-r4-r2-start.sha256) | 503 精确不变，tester、旧主报告、人工清单、矩阵四项授权变化，0 缺失或越界差异 |
| 旧独立与顾问材料 | 110 项旧 independent、69 项旧 D15/D15-R1 逐项不变；11 项新冷入口冻结源码不变 |
| 矩阵与旧报告 | 120 唯一 ID、12 列，原前 11 列、全部状态与 B 外内容保持；两个旧报告原字节前缀保持 |
| 测试与预算 | A 一个唯一节点 0 passed/1 failed，CLI/worker/main 各一次；7623 ms，无 timeout/强杀；B、恢复、兼容、Windows 均未运行 |
| 四条原断言 | 错误提示失败；Shell、导航、Agent 三项通过，不能累计成三个独立 passed 节点 |

起点 SHA-256 为 `fac063506c7aa11be925655b7001a0493c93d172bccb9a2e749544d687faa2b0`。新报告保留原 24 项完整验收映射；P4-A64 passed、P4-B0 passed/1 failed/19 blocked/4 not_run、P4-C20 与 P4-D12 not_run 均保持。

总控保存前的完整暂存检查新增发现：首次冻结 controller `tests/independent/desktop/r4-r2-run-once.ps1:158` 的空白行有尾随空格。先前 tracked-only `git diff --check` 没有包含该新文件；完整 cached 检查实际返回2、仅此一项。原文件与其摘要、首次证据保持，不为格式清理改写独立材料；该提示作为历史格式例外随未完成 checkpoint 保存，不能把完整46文件格式检查写成通过。新总控文档的链接与行尾检查已通过。

## 同一次冷启动的因果关系

[34 条连续 journal](../tests/independent/desktop/evidence/r4-r2/cold-trace/worker.journal.jsonl)来自同一登记 worker，main/act 各自有 enter 和 terminal：

| 顺序 | 记录 | 对结论的影响 |
| --- | --- | --- |
| seq16–17 | Router1/attempt1 enter，随后 aborted=true | 第一次请求不再决定当前页面 |
| seq19–20 | attempt2 enter；页面 mock factory 一次 throw | factory 命中不等于两个请求都失败 |
| seq21 | attempt1 rejected，安全错误，aborted=true | 不能把旧请求的错误写到当前错误槽 |
| seq24–25 | attempt2 resolved，aborted=false；目标 idle/errors=0 | 当前有效页面没有导入失败的终态 |
| seq27–29 | 无错误提示、其余三个入口存在；四个原断言实际执行 | 仍不能建议关闭 LAZY-001 |

观察门面原样返回 loader Promise、原 Router 对象并保留 this/参数；旁路监听、函数身份变化、订阅和同步日志的扰动已披露。5 秒条件观察的 13.572 ms 调度尾差如实保留，没有延长预算或重跑。清理证据支持实际 root 卸载、观察退订和 bridge 订阅归零；登记 CLI/worker 已退出。系统枚举权限拒绝、worker 自身 exit code/完整后代核对保持未核实，不能声称全系统零残留。

## 固定工具源码提供的候选解释

以下来自本机已冻结的 R5 普通安装，指向 `C:/MarisLazyR5/R5-20261002-222300/workspace/node_modules/`，仅静态审计，不代表本轮捕获了内部执行分支：

- Vitest `dist/chunks/index.hTNFpC24.js:409–420` 在 manual mock 处理中共享调用栈，并注明并发 import 的限制；`:588–590` 在当前栈已有目标 mock/URL 时，转去 `_vitest_original`。
- `@vitest/mocker/dist/chunk-registry.js:169–188` 只缓存成功 exports；factory 抛错会被包装，不形成成功缓存。
- Vite `dist/node/module-runner.js:1043–1056` 对普通模块复用已有 `mod.promise`，失败 Promise 不在 finally 中删除；`:1058–1066` 合并并发模块信息请求。
- Vite 同文件 `:1101–1105` 先把相对动态导入解析为绝对模块路径，再请求模块。因此只匹配相对 import 字面量的 alias 不足以证明注入命中。

这为“一次 factory 抛错、另一次加载成功”提供了候选解释，也为避免 manual mock 并发分支提供了依据。第二次原请求是否实际走过 `_vitest_original` 仍为假设，不写成已证实根因；无需再扩大内部探针才可改进测试前置条件。

## 下一任务裁定

发布 [P4-C12-R4-R3](coordination/prompts/p4-c12-r4-r3-persistent-import-tester.md)，唯一负责人仍为既有测试智能体。新任务只改变测试的故障实现，不改变四条业务要求或产品默认 loader：

1. 精确重定向目标页面规范模块 ID 到测试专属真实 ESM。该 fixture 没有任何 import，通过 setup 原生 recorder 记事件后在顶层抛固定虚拟错误；不使用目标页面 manual mock，不用 export getter 代替导入拒绝，不改变路由或 loader。
2. 在一个独立新 worker 先通过实际 `createModuleRoutes` 的默认 loader 做两次并发加载、随后再加载一次。三个调用必须均以安全错误拒绝，规范目标确实映射同一 fixture。这个节点只验注入，不导入 main、不当作 UI 通过，也不预热后续 worker。
3. 注入验证通过后，两个另外的新冷 worker 各运行一次 main：A 用现有同步透传观察，B 无门面。A 必须取得当前有效请求的安全拒绝和目标错误槽；A/B 都保留错误提示、Shell、导航、Agent 四条原断言。
4. 两个业务节点通过后，同任务继续已授权的独立恢复、必要兼容和原 Windows 剩余条件。初始 fixture 为持续失败，不要求它能变成恢复成功；瞬时恢复用独立可信 loader 端口，分别统计。

上述方案只有源码层面的可行性，实际注入仍待执行。精确 ID、防循环、并发/重复拒绝先取得证据，再运行冷入口；任何实际节点失败保存首次结果并停止，不加时、预热、缓存重置、重打包或要求用户现在操作窗口。

新 [固定起点](coordination/snapshots/p4-c12-r4-r3-start.sha256)绑定旧交付与新协调文档。R4-R2、顾问及执行保持停止；R4-R3 `ready / waiting_user`、接单 `unverified`。本轮仅建立描述未完成状态的本地 checkpoint，不推送。真实前端参考图与模型策略提醒门禁保持，P4-C/D 不开始。

来源：[本轮独立报告](testing/phase-4-c12-r4-r2-cold-entry-windows-report.md)、[原任务](coordination/prompts/p4-c12-r4-r2-cold-entry-tester.md)、[实际默认 loader](../apps/desktop/src/renderer/module-routes.tsx)、[观察门面](../tests/independent/desktop/r4-r2-router-facade.mjs)。
