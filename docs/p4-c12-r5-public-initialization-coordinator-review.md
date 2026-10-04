# P4-C12-R5-PUBLIC 初始化阻塞核对与环境恢复裁定

2026-10-04，Asia/Shanghai。总控已核对本轮交付；原任务保持 `blocked / finished`，不是产品验收失败，也不是 LAZY-001 修复通过。公开 B 已解除对 A 的执行依赖，但自身测试环境仍未初始化完成。

## 首次材料与结论边界

- [41 项交付](../tests/independent/desktop/evidence/r5-public/delivery.sha256)逐文件匹配，清单普通 SHA-256 为 `89adf287912140c8dce66264fcf57f0d7e4168d00437c71a8bc3b57afdf0c0fe`。
- [10 项冷源码](../tests/independent/desktop/evidence/r5-public/cold-source.sha256)以 desktop 测试目录为基准、[6 项首次记录](../tests/independent/desktop/evidence/r5-public/cold-first.sha256)以仓库根为基准，均匹配。delivery/cold-first 是 CRLF，cold-source/start 是 LF；按原字节核对，没有改写首次文件以统一格式。
- 原 638 项起点为 634 不变、4 授权变化、0 缺失：tester、矩阵、旧主报告和人工清单。后两项原字节前缀保持，各追加 1,027 字节。总控随后更新自己的协调材料，单列为后续协调变化。
- [worker journal](../tests/independent/desktop/evidence/r5-public/cold/worker.journal.jsonl)只到 `worker_start → journal_ready → test_module_enter → jsdom_import_enter`。一次 CLI、一个新 worker；main、故障模块求值、四条业务断言全部为 0。
- [controller journal](../tests/independent/desktop/evidence/r5-public/cold/controller.journal.jsonl)在 root 启动后 14,953 ms 开始初始化收口，总时长 15,120 ms；实际阈值 14,950 ms 为原 15 秒上限留收口余量。不能据此推断多给几十毫秒就会通过。
- [进程结果](../tests/independent/desktop/evidence/r5-public/cold/process.json)：root 被定向终止、exit -1；登记 worker 已结束，其自身退出码和完整历史后代仍未核实。双流为空不是通过证据；已核实范围不扩大成全系统零残留。

总控只读子任务 `d15_probe_audit` 复算了上述边界；`d16_acceptance_contract_audit` 核对了固定依赖加载路径。子任务及总控没有运行目标或产品。当前没有新增产品缺陷结论；LAZY-001、UI-02 和 P4-B 均未关闭。

## 与 D16 的具体比较

D16 E1 与本轮都把 `jsdom` 指向固定 `jsdom/lib/api.js`，并在测试模块顶层 `await import('jsdom')`。本轮使用 native config loader，D16 默认 bundle；本轮 config、setup 和 test_module 已经到达，因此这个差异不能直接被认定为根因。D16 的极小模块成功，不证明完整 B 必然能在相同时限内完成。

固定 R5 的 `node_modules/jsdom/package.json` 是 jsdom 30.1.1、`type: commonjs`、`main: ./lib/api.js`；实际 API 使用原生 `require` 并导出 JSDOM 和 VirtualConsole。固定 Node 24.21.0 落在该包声明的 Node 范围内。这提供了不更换依赖、直接用 Node 加载同一 API 的具体入口。

固定 Vitest `dist/chunks/index.hTNFpC24.js` 的 `fetchModule` 在 785 行先等待 `fetchWarmModules()`，随后可能请求 RPC；Vite `dist/node/module-runner.js` 的外部模块求值又是另一等待层。现有 journal 位于这些层之外，故 `jsdom_import_enter` 不等于已经进入 jsdom 内部求值。服务端 `fetchWarmModules` 遍历已有图并有 seen 集合；只读源码没有证明死锁或循环。不得把本次阻塞简单归咎于 jsdom、Vite、代理、Docker、磁盘或产品。

## 冻结新的最小恢复范围

发布 [P4-C12-R6-ENV](coordination/prompts/p4-c12-r6-env-tester.md)，仍由既有测试智能体负责测试基础设施及独立验收。执行和技术顾问保持停止，不再增加一个只做依赖导入的小实验任务。

1. 在新 setup 内用 Node 内置 `createRequire` 加载固定 jsdom 原始 API；只把原始 JSDOM/VirtualConsole 引用交给本 worker 的测试。仍在正文创建新的 DOM，不换为其他 DOM 库，不使用替身，不预热产品/Router，不改依赖。
2. React/ReactDOM/Router 和产品入口继续走原真实解析路径，不把整个测试改成原生 require，不包装 loader 或 Router。旧精确持续故障映射、四条公开断言、隐私及零写入要求全部保留。
3. 新任务初始化上限 60 秒、正文 10 秒、UI 条件观察 5 秒、清理 2 秒、总体 75 秒。初始化预算是测试工具的恢复预算，不是产品响应标准。controller 的首次结果永久保留；新成功不能倒写旧 15 秒运行通过。
4. 这同时改变了工具加载入口和初始化预算，是恢复方案，不是单变量根因实验。即使成功，也只说明新路线可用；不能宣称已经确定旧超时的充分原因。原生加载若仍无返回，或后续 React 初始化阻塞，按实际停点记录，禁止继续猜因。
5. 不先运行 E1、E2、P 或新的 synthetic 门禁。新的公开 B 实际 main 最多一次；仅对有明确证据且目标尚未启动的工具错误，允许同任务内一次修正。未知超时不自动重试，不新增内部 RPC 观察框架。
6. 新 B 通过后，按原任务的条件在同一次委派中继续独立恢复及原 Windows 范围，不再次等待 A 或单独排队。真实设备条件仍独立记录，不用 jsdom 替代。

此前流程把初始化失败转成多轮停止，确实拖延了产品行为验收；本次把可修的工具边界与业务门禁明确分开。新路线尚未执行，不承诺通过，不降低既有产品标准。

## 协调与交付

新 [固定起点](coordination/snapshots/p4-c12-r6-env-start.sha256)由总控在协调文件稳定后生成。R5-PUBLIC 的源码/证据/报告保持原字节；本轮只记录后续决定，不修改 tester 的原交付状态。新任务 `ready / waiting_user`，实际接单 `unverified`。

本地保存“初始化仍阻塞及新恢复路线”的检查点，不作为已通过的验收提交、不推送。P4-C/D 保持未启动；进入真实前端前提醒两张参考图、模型分工及 token 策略的门禁继续有效。
