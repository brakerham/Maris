# P4-C12-R4-R3 总控核对：保留注入证据，裁定测试初始化与流程依赖

核对日期：2026-10-03，Asia/Shanghai。头脑风暴总控只读核对交付与首次记录，没有运行测试、产品或服务。本记录接受 `blocked / finished` 事实，不接受 LAZY-001、UI-02 或 P4-B 为完成。

## 当前证据

- [独立报告](testing/phase-4-c12-r4-r3-persistent-import-windows-report.md)与[52 项交付清单](../tests/independent/desktop/evidence/r4-r3/delivery.sha256)逐文件复算 52/52 匹配。清单普通 SHA-256：`44c36fca1341901a26594c7665cb25ffa81c86e403a322b30da5493f484148cc`。
- [冻结源码清单](../tests/independent/desktop/evidence/r4-r3/cold-source.sha256)以 `tests/independent/desktop/` 为相对路径基准，15/15 匹配；不得按仓库根目录错误解析。总控首次核对使用了错误基准，随后仅更正自己的只读核对器，未修改材料或启动目标。
- 持续故障 P：生产默认 loader 的两次并发调用及随后一次调用都安全拒绝，真实 ESM 故障模块求值一次；独立工具前置节点 1 passed。该成功证据保留，不重复验证，不补签 UI 或 Windows。
- 冷观察 A：[worker journal](../tests/independent/desktop/evidence/r4-r3/cold-trace/worker.journal.jsonl)只有 `worker_start`、`journal_ready`；[process receipt](../tests/independent/desktop/evidence/r4-r3/cold-trace/process.json)为 14,595 ms、`mainImportRequests=0`。正文、main、loader、Router 状态、DOM 与四条业务断言未执行。
- 无观察包装 B、恢复、兼容回归和 Windows 均未运行。不能把 A 的初始化停止当成产品错误提示再次失败，也不能据此认定 React Router、jsdom 或观察门面是根因。
- 已登记 CLI/worker 已退出；完整系统后代进程枚举因权限限制未核实。该限制保留，不写成全树零残留。

## 总控决定

1. 原 R4-R3 收口为 `blocked / finished`；不修改其任务、首次结果和测试源码，不要求再执行 P 或 A。
2. 总控此前把观察 A 设置为无包装业务 B 的必经门禁，反复让工具初始化问题挡住业务判断。这项流程设计由总控负责，交技术顾问审查，不归因于测试方推理强度或产品必然存在新缺陷。
3. 用户已授权准备 [P4-D16 技术顾问任务](coordination/prompts/p4-d16-harness-and-acceptance-technical-adviser.md)。既有顾问使用用户选择的 GPT-6 Astra，独立核对证据、进行有限的新初始化诊断，并提交可以冻结的验收路线。
4. 本轮只派发顾问范围。P4-D16 不运行旧 A/B，不导入产品 main，不做独立 UI 验收，不修改产品或旧测试，不打包或启动 Windows 产品；测试方与执行方继续停止。
5. 是否解除后续公开业务节点对辅助观察节点的依赖，须由 D16 给出具体方案与证据，再由总控冻结。当前不授权 B、恢复或 Windows，也不提前进入 P4-C。

## 下一交付应解决的问题

顾问应先区分 Vitest 配置、环境 setup、模块收集/转译、静态依赖求值与测试正文这些阶段；用即时记录缩小缺失阶段，避免又只有两条 worker 记录。诊断与业务验收的预算、结论和所有权必须分开。可确认根因时给出最小基础设施修正；未确认时给出最后完成阶段、最小未完成依赖和可执行的下一验收路线，不能只建议再等待或再建同类观察任务。

原四条业务要求不变：安全错误提示、Shell、模块导航和统一 Agent 入口。后续重试、持续失败不循环、健康页面切换、状态保持以及真实 Windows 条件仍须测试方独立验证。

该检查点保存未完成状态，不作发布或验收提交。P4-A 保持 64 passed；P4-B 保持 0 passed、1 failed、19 blocked、4 not_run；P4-C/D 共 32 not_run。进入真实前端阶段前的参考图、模型分工和 token 策略提醒门禁保持。
