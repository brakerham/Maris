# 项目进度总览

更新时间：2026-10-17 09:03，Asia/Shanghai
维护者：头脑风暴智能体

## 当前阶段

P0～P3与P4-A已独立验收，QUIT-001普通关闭范围已关闭。R9-R1停于目标前脚本路径身份比较，产品/辅助新增均0，未形成产品缺陷；发布P4-C12-R9-R2，修完整参数/路径身份链后沿未耗额度续验H1及剩余Windows。旧8独立/48兼容/W1和模块/冷入口/恢复通过保持。P4-B仍1 passed、1 failed、19 blocked、3 not_run；P4-C/D未开始，执行方和顾问停止。

部署范围已收紧为单机、单主人、本地数据库。其他人使用时在自己的设备安装独立实例；公众注册、多账号、云账户和注册/常规登录 UI 暂停。内部 `user_id`、Principal、session 和微信绑定继续作为本地数据安全边界，桌面端以后再决定自动本地会话或可选应用锁。

## 角色状态

| 角色 | 任务状态 | 运行状态/当前步骤 | 最近进展或心跳 | 下一检查点 | 证据 |
| --- | --- | --- | --- | --- | --- |
| 头脑风暴 | `ready / waiting_user` | R9-R1路径工具证据核对、R9-R2冻结 | 2026-10-17 09:03 | 既有测试方接单 | [裁定](../p4-c12-r9-r1-path-coordinator-review.md) |
| 技术顾问 | D16有限裁定`complete`；本人原`review / finished`保留 | 39交付匹配，E1/E2两次成功，旧A根因unknown | 2026-10-03 23:34（交付已核对） | 停止，不续诊断或独立验收 | [报告](../phase-4-d16-harness-and-acceptance-advice.md) |
| 执行智能体 | R7原 `review / finished` 保留；普通关闭修复已接受 | R9独立关闭QUIT-001限定范围 | 2026-10-16（总控接受） | 停止，无产品返修 | [裁定](../p4-c12-r9-quit-h1-coordinator-review.md) |
| 测试智能体 | R9-R1 `blocked / finished`；R9-R2 `ready / waiting_user` | 完整脚本身份工具修正与未耗额度续验 | 2026-10-17 00:23（本人交付），09:03（总控准备） | 复算新起点并接单 | [任务](prompts/p4-c12-r9-r2-path-windows-tester.md) |

当前唯一新任务是P4-C12-R9-R2，由既有测试方负责，实际接单unverified。原R9-R1没有产品/辅助启动；剩余产品7、辅助4沿用，累计上限8/5不增长。先一次完整修好脚本身份链，工具通过后H1及剩余Windows同任务继续，旧通过不重跑，前端提醒保持。

## 阶段 0 任务状态

| 任务 | 负责人 | 状态 | 完成条件摘要 | 证据 |
| --- | --- | --- | --- | --- |
| A：计划与总协调 | 头脑风暴 | `in_progress` | 完成派发、核对交付、关闭阶段 | [任务包](../phase-0-assignments.md) |
| D1：实现前技术建议 | 技术顾问 | `complete` | 提交方案、替代方案、目录边界和学习点 | [D1 建议](../phase-0-d1-technical-advice.md)、[冻结采用项](../phase-0-interface-freeze.md) |
| B1：最小 Agent 核心 | 执行智能体 | `complete` | 实现、自测、文档齐备并通过独立验证 | 执行方、测试方和总控全量复跑分别通过；总控为 `77 passed in 1.64s` |
| C1：阶段 0 测试设计 | 测试智能体 | `complete` | 独立验收矩阵与判定标准 | [60 项测试矩阵](../testing/phase-0-test-matrix.md) |
| C2：B1 独立测试与结构审查 | 测试智能体 | `complete` | 依赖 B1 可运行交付和冻结契约 | 初测 6 项失败；修复后六项定向、51 项独立和 77 项完整测试全部通过 |
| B2a：FastAPI 探针 | 执行/测试智能体 | `complete` | 健康检查、随机回执、进程内幂等与独立 HTTP 验收 | 25 项新增独立、104 项独立、143 项全量测试通过；真实 Uvicorn 200/200/200/409；总控复验通过 |
| B2b：OpenClaw 桥接 | 执行/测试/技术顾问 | `complete` | 客户端、命令、工具、宿主加载、跨语言冒烟和独立测试 | 执行 27 项、独立 44 项、pack 18 文件、runtime inspect loaded/无诊断；见 [C2-B2b 报告](../testing/phase-0-c2-b2b-report.md) |
| D2：实现后教学 | 技术顾问 | `complete` | 结合最终代码和验证讲解 HTTP、FastAPI、幂等和桥接 | [教学文档](../phase-0-d2-bridge-teaching.md)已定稿并通过总控核对 |
| W1：真实微信联调核心切片 | 用户/头脑风暴/测试智能体 | `complete` | 安装插件、扫码、命令实收、停服错误与工具调用 | W-02、W-03、W-04、W-12 通过；其余通道与提醒案例保留到对应功能阶段 |
| P1-D3：数据层技术建议 | 用户启动的独立技术顾问 | `complete` | 六组选型、17 张建议表、12 条不变量、迁移、风险和教学地图经总控核对 | [D3 建议](../phase-1-d3-data-advice.md) |
| P1-C3：数据层测试矩阵 | 用户启动的独立测试智能体 | `complete` | 98 个案例、98 个唯一 ID、0 非法状态；全部保持未执行 | [C3 矩阵](../testing/phase-1-data-test-matrix.md) |
| P1-IF-001：数据接口冻结 | 头脑风暴 | `complete` | F01～F15、17 张表、错误、事务、范围和测试归属已冻结 | [接口冻结](../phase-1-interface-freeze.md) |
| P1-B3：数据层实现 | 用户启动的独立执行智能体 | `review` | 首轮实现已由 C4 验出 3 个缺陷；等待 B3-R1 新快照 | [执行日志](agents/executor.md)、[B3 运行说明](../b3-data-running.md) |
| P1-C4：数据层独立验收 | 用户启动的独立测试智能体 | `review` | 首轮 65 通过、3 失败、8 个 PostgreSQL 环境阻塞；等待 R1 定向复验 | [C4 报告](../testing/phase-1-c4-data-report.md)、[C3 矩阵](../testing/phase-1-data-test-matrix.md) |
| P1-B3-R1：数据层缺陷返修 | 用户启动的独立执行智能体 | `review` | 三个缺陷已修复，28 项执行方测试通过并提交匹配的 22 文件新快照 | [执行日志](agents/executor.md)、[B3 运行说明](../b3-data-running.md) |
| P1-C4-R2：数据层定向复验 | 用户启动的独立测试智能体 | `complete` | 三个缺陷全部通过；最终回归 241 通过、0 失败、8 个 PostgreSQL 跳过 | [R2 报告](../testing/phase-1-c4-data-report.md) |
| P2-D5：财务 Agent 工具设计 | 用户启动的独立技术顾问 | `complete` | 九个工具的阶段边界、确认、幂等、状态、HTTP、风险和教学建议已验收 | [D5 建议](../phase-2-d5-finance-agent-advice.md) |
| P2-IF-001：Agent 工具接口冻结 | 头脑风暴 | `complete` | 冻结六个工具、可信上下文、候选确认、持久状态、HTTP、错误与文件所有权 | [P2 接口](../phase-2-interface-freeze.md) |
| P2-B4：Agent 财务工具实现 | 用户启动的独立执行智能体 | `complete`（本地范围） | 23 文件快照匹配；23 项执行方和 45 项独立 P2 测试通过 | [B4 运行说明](../p2-a-running.md)、[C6 报告](../testing/phase-2-c6-agent-report.md) |
| P2-C5：Agent 财务测试矩阵 | 用户启动的独立测试智能体 | `complete` | 84 个唯一案例及环境分层已完成，全部明确保持未执行 | [C5 矩阵](../testing/phase-2-agent-test-matrix.md) |
| P2-C6：Agent 财务独立执行 | 用户启动的独立测试智能体 | `complete`（本地范围） | 45 项独立和 23 项执行方 P2 测试通过；71 个矩阵案例有本地证据 | [C6 报告](../testing/phase-2-c6-agent-report.md) |
| P2-D6：Agent 实现教学 | 用户启动的独立技术顾问 | `complete` | 九节实际代码教学、两张 Mermaid 图、术语表、学习顺序、练习和检查题经总控核对 | [D6 教学](../phase-2-d6-agent-teaching.md) |
| PG-C7：PostgreSQL 专项验收 | 用户启动的独立测试智能体 | `complete`（经返修闭环） | 原基线发现 P0 缺陷，现由 DATA-R1/R2 完成修复和复验 | [C7 报告](../testing/phase-2-c7-postgresql-report.md) |
| PG-C7-DATA-R1：PostgreSQL 首次写入返修 | 用户启动的独立执行智能体 | `complete` | `RETURNING` 修复、32 项财务测试及固定快照均通过验收 | [B3 运行说明](../b3-data-running.md) |
| PG-C7-DATA-R2：PostgreSQL 定向独立复验 | 用户启动的独立测试智能体 | `complete` | P1 8/8、P2 SPG 4/4、SQLite 9/9、执行方补充 4/4 通过 | [R2 报告](../testing/phase-2-c7-r2-postgresql-report.md) |
| P2-TIME-R1：Agent 测试时钟维护 | 用户启动的独立执行智能体 | `complete` | 28 项通过、七文件摘要匹配，并通过 C2 独立复验 | [交接](../p2-time-r1-running.md) |
| P2-TIME-C2：测试时钟定向独立复验 | 用户启动的独立测试智能体 | `complete` | 28/28、原 23/23、还原审计 28/28、线程泄漏 0 | [报告](../testing/p2-time-c2-report.md) |
| P3-D7：活动 Markdown 导入方案 | 用户启动的既有技术顾问 | `complete` | 724 行方案、冻结清单及摘要经总控核对并采用 | [D7 方案](../phase-3-d7-activity-import-advice.md) |
| P3-C8：活动 Markdown 导入测试矩阵 | 用户启动的既有测试智能体 | `complete` | 89 个唯一案例、10 列完整；后由 C9-R2 执行并收口为 89/89 passed | [最终矩阵](../testing/phase-3-activity-import-test-matrix.md) |
| P3-IF-001：活动导入接口冻结 | 头脑风暴 | `complete` | 解析、持久模型、范围金额、API、幂等、事务、错误和测试边界已冻结 | [P3 接口](../phase-3-interface-freeze.md) |
| P3-B5：活动导入实现 | 用户启动的既有执行智能体 | `complete`（经 R1/R2） | 首轮 P0 迁移缺陷已最小返修并独立关闭 | [B5 交接](../b5-activity-import-running.md) |
| P3-C9：活动导入独立验收 | 用户启动的既有测试智能体 | `complete`（经 R2） | 首轮缺陷报告保留为返修依据，最终由 R2 收口 | [C9 报告](../testing/phase-3-c9-activity-import-report.md) |
| P3-B5-R1：外键名最小返修 | 用户启动的既有执行智能体 | `complete` | 22 文件摘要匹配；migration 5、P3 本地 144、PG 9、旧迁移 4 均通过 | [B5 交接](../b5-activity-import-running.md) |
| P3-C9-R2：PostgreSQL 定向复验 | 用户启动的既有测试智能体 | `complete` | 独立本地 81、执行方本地 144、旧迁移 4、PG 9/10 和矩阵 89/89 通过 | [R2 报告](../testing/phase-3-c9-r2-activity-import-report.md) |
| P0-P3-D8：阶段实现后教材 | 用户启动的既有技术顾问 | `complete` | 四册共 44 页；96 个本地链接和行号锚点、PDF 重开及 44/44 页视觉 QA 通过 | [教材索引](../teaching/README.md)、[任务卡](prompts/p0-p3-d8-technical-adviser.md) |
| P4-HOST-BRAINSTORM：可扩展 Agent Host 规划 | 头脑风暴总控 | `complete` | 定义 Host、模块、Agent、workflow、记忆、工具、桌面扩展和 P4 切片；用户已接受方向 | [Host 架构草案](../phase-4-modular-agent-host-architecture.md) |
| P4-D9：Agent Host 最小技术方案评审 | 用户启动的既有技术顾问 | `complete` | 766 行方案、F01～F17、7 个产品裁定项、14 个本地链接及摘要经总控核对 | [D9 方案](../phase-4-d9-modular-agent-host-advice.md) |
| P4-C10：模块化 Agent Host 测试矩阵 | 用户启动的既有测试智能体 | `complete` | 120 个唯一案例、12 字段完整、全部 `not_run`，F/U 与八项扩展证明已追踪 | [C10 矩阵](../testing/phase-4-modular-agent-host-test-matrix.md) |
| P4-IF-001：模块化 Agent Host 接口冻结 | 头脑风暴总控 | `complete` | 冻结总架构与 P4-A 模块、身份、user scope、workflow、记忆、API 和 migration | [P4 接口](../phase-4-interface-freeze.md) |
| P4-B6：Host、身份和通用状态地基 | 用户启动的既有执行智能体 | `complete`（经 R1、R2、R3 与 C11-R2） | 8 个 P0、14 个 P1 接管项闭环，P4-A 64/64 passed，134 文件最终快照固定 | [P4-A 最终验收](../p4-a-final-coordinator-review.md) |
| P4-D10：B6 返修架构裁定 | 用户启动的既有技术顾问 | `complete` | D10 SHA 匹配；8/14 处置、七类合同、R1/R2、12 类 PG 与 C11 门禁由总控接受 | [D10 方案](../phase-4-d10-b6-repair-architecture.md) |
| P4-IF-002：B6 返修补充冻结 | 头脑风暴总控 | `complete` | 冻结安全数据与 Host 运行时的补充合同和顺序 | [IF-002](../phase-4-interface-freeze-002.md) |
| P4-B6-R1：安全数据与兼容入口返修 | 用户启动的既有执行智能体 | `review`，已接受为 R2 输入 | R1/F1 安全切片摘要可复算，最终独立验收仍由 C11 完成 | [F1 总控审查](../p4-b6-r1-f1-coordinator-review.md) |
| P4-B6-R1-F1：外部身份并发绑定返修 | 用户启动的既有执行智能体 | `review`，开发返修接受 | 总控本地 41 项、范围和摘要通过；执行方真实 PG 原 21+新增 1 通过 | [F1 总控审查](../p4-b6-r1-f1-coordinator-review.md) |
| P4-B6-R2：Host/Agent 运行时返修 | 用户启动的既有执行智能体 | `review / finished`，总控接受为 C11 输入 | S1 结构完成；T2 已证明 R1/R2 共 17 个唯一真实 PG 用例通过；最终 105 文件快照已冻结 | [R2 最终核对](../p4-b6-r2-final-coordinator-review.md) |
| P4-B6-R2-S1：运行时结构补全 | 用户启动的既有执行智能体 | `review / finished`，总控接受为 S2 输入 | 10 个变更文件摘要匹配；总控 44 项定向通过；聚合摘要勘误已登记 | [S1 总控核对](../p4-b6-r2-s1-coordinator-review.md) |
| P4-B6-R2-S2：真实 PostgreSQL 门禁 | 用户启动的既有执行智能体 | `review / finished` | S2 原 R2 9/9、Finance 4/4、P3 10/10 通过；T2 已补齐 Host R1 8/8 与 R2 9/9 | [S2 运行说明](../b6-r2-s2-postgresql-running.md)、[T2 运行说明](../b6-r2-s2-t2-postgresql-running.md) |
| P4-B6-R2-S2-T1：R1 PG 测试时钟返修 | 用户启动的既有执行智能体 | `review / finished` | 单文件时钟修复进入最终快照；T2 精确节点及其后 16 项证明修复生效且 monkeypatch 已恢复 | [T1 运行说明](../b6-r2-s2-t1-clock-running.md)、[T2 运行说明](../b6-r2-s2-t2-postgresql-running.md) |
| P4-B6-R2-S2-T2：有限 PostgreSQL 复验 | 用户启动的既有执行智能体 | `review / finished` | 17/17 passed；104/104 前后匹配；Compose 服务最终为空 | [T2 运行说明](../b6-r2-s2-t2-postgresql-running.md)、[R2 最终核对](../p4-b6-r2-final-coordinator-review.md) |
| P4-C11：P4-A 独立验收 | 用户启动的既有测试智能体 | `complete`（经 R1、R2） | P4-A 64/64 passed；历史迁移缺陷已修复并通过真实 PostgreSQL 定向复验 | [C11 报告](../testing/phase-4-c11-host-foundation-report.md)、[P4-A 最终验收](../p4-a-final-coordinator-review.md) |
| P4-C11-R1：历史迁移证据补强 | 用户启动的既有测试智能体 | `complete`；原失败作为审计证据保留 | R1 发现的 `P4-C11-R1-PG-001` 已由 E1 修复并经 C11-R2 关闭 | [R1 报告](../testing/phase-4-c11-r1-evidence-report.md)、[R2 报告](../testing/phase-4-c11-r2-postgresql-history-report.md) |
| P4-B6-R3：PostgreSQL 历史迁移返修 | 用户启动的既有执行智能体 | `blocked / finished` | 130/130 起点通过；执行方历史 fixture 已准备；Docker Desktop 未运行，PG 未执行且 migration 未修改 | [R3 运行说明](../b6-r3-postgresql-history-migration-running.md)、[原 R3 Prompt](prompts/p4-b6-r3-postgresql-history-migration-executor.md) |
| P4-B6-R3-R1：PostgreSQL 历史迁移返修续跑 | 用户启动的既有执行智能体 | `blocked / finished` | 131/131 起终点一致；Docker Desktop 仍未运行，PG/pytest 未启动，migration 零漂移 | [R3-R1 阻塞说明](../b6-r3-r1-postgresql-history-migration-running.md)、[R3-R1 起点](snapshots/p4-b6-r3-r1-start.sha256) |
| P4-B6-R3-R1-E1：Engine 恢复后返修续段 | 用户启动的既有执行智能体 | `complete / finished` | 原缺陷按预期复现；PG 临时 default+NOT NULL 修复；30 项门禁通过；结果已独立确认 | [E1 运行说明](../b6-r3-r1-e1-postgresql-history-migration-running.md)、[固定起点](snapshots/p4-b6-r3-r1-start.sha256) |
| P4-C11-R2：PostgreSQL 历史迁移定向复验 | 用户启动的既有测试智能体 | `complete / finished` | 独立 7 passed、执行兼容 19 passed；关闭 DB-05/06 和 P0 缺陷；Compose 最终为空 | [C11-R2 报告](../testing/phase-4-c11-r2-postgresql-history-report.md)、[最终快照](snapshots/p4-a-final.sha256) |
| P4-D11：Windows Shell 技术方案 | 用户启动的既有技术顾问 | `complete / finished` | 1093 行方案、24 个 P4-B ID、19 个本地链接与两文件摘要通过总控核对；两项事实勘误由 IF-003 吸收 | [D11 方案](../phase-4-d11-windows-shell-technical-advice.md)、[总控审阅](../p4-d11-coordinator-review.md) |
| P4-IF-003：Windows Shell 接口冻结 | 头脑风暴总控 | `complete` | 精确版本、三层安全、模块 UI、OpenAPI、owner、nonce、Supervisor、outbox、Tray、毛毛、主题和测试边界已冻结 | [IF-003](../phase-4-interface-freeze-003.md) |
| P4-B7：Windows Shell 实现 | 用户启动的既有执行智能体 | `blocked / finished` | 66 文件快照匹配；执行方本地/打包/E2E 证据通过；audit 的 critical/high 与 main 未真实接 Host 阻止进入 review | [B7 运行说明](../b7-windows-shell-running.md)、[源快照](../../apps/desktop/b7-source.sha256) |
| P4-D12：B7 供应链与真实接线裁定 | 用户启动的既有技术顾问 | `complete / finished` | 16 项 advisory、五路线、三候选解析、22 条冻结、Host 组合与教学已由总控接受 | [D12 方案](../phase-4-d12-b7-supply-chain-advice.md)、[总控审阅](../p4-d12-coordinator-review.md) |
| P4-IF-004：供应链与真实 Host 补充冻结 | 头脑风暴总控 | `complete` | Forge 8 alpha 发布前候选、desktop core readiness、composition root、生命周期和门禁冻结 | [IF-004](../phase-4-interface-freeze-004.md) |
| P4-B7-R1：供应链与真实 Host 组合续段 | 用户启动的既有执行智能体 | `blocked / finished` | Forge 8 候选图、旧包消失和候选 lock 双审计有效；Electron 官方资产连续 fetch failed，Host/runtime/package 后续未执行 | [R1 运行说明](../b7-r1-windows-shell-running.md)、[总控核对](../p4-b7-r1-blocked-coordinator-review.md) |
| P4-B7-R1-E1：Electron 链路恢复续段 | 用户启动的既有执行智能体 | `blocked / finished` | 最终 lock 双审计、F04 与 clean install 通过；Node 24 正文传输 `ECONNRESET` 后按 P0 停止 | [E1 报告](../b7-r1-e1-windows-shell-running.md)、[E1 总控核对](../p4-b7-r1-e1-blocked-coordinator-review.md) |
| P4-B7 Electron 官方资产网络门禁 | 头脑风暴总控 | `complete` | 透明 TUN 路由生效；官方 Range GET 返回 HTTP 206 和准确 1 MiB，TLS 校验通过 | [E2 网络门禁](../p4-b7-r1-e2-network-gate.md) |
| P4-B7-R1-E2：Electron 下载恢复与真实 Host 组合 | 用户启动的既有执行智能体 | `blocked / finished` | 194 文件 source 匹配；官方 Electron、Host/sidecar、22 Vitest、55 Python 和 package 通过；app.asar launch 阻塞，真实 EXE 未运行，resources 含 Python 副产物 | [E2 报告](../b7-r1-e2-windows-shell-running.md)、[总控核对](../p4-b7-r1-e2-blocked-coordinator-review.md) |
| P4-B7-R1-E2-R1：启动分层与 package hygiene | 用户启动的既有执行智能体 | `blocked / finished` | 最小无业务 fixture 中 GPU child `0xC0000135`、browser `0x80000003`；产品零修改并安全收口 | [R1 报告](../b7-r1-e2-r1-windows-shell-running.md)、[总控核对](../p4-b7-r1-e2-r1-blocked-coordinator-review.md) |
| P4-D13：Windows 25H2 Electron crash 裁定 | 用户启动的既有技术顾问 | `complete / finished` | 442 行方案、26 条冻结建议、A1/A2/F1 分支、版本与 hygiene 拆分已由总控接受 | [D13 方案](../phase-4-d13-electron-windows-crash-advice.md)、[总控审阅](../p4-d13-coordinator-review.md) |
| P4-IF-005：Electron Windows 诊断与 package resource 冻结 | 头脑风暴总控 | `complete` | 冻结环境诊断顺序、安全开关、证据口径和 H1 staging 合同 | [IF-005](../phase-4-interface-freeze-005.md) |
| P4-B7-R1-H1：Python package resource 静态 staging | 用户启动的既有执行智能体 | `review / finished`，总控接受为 E3 输入 | H1-R1 已关闭原子性缺陷；198/198 source 匹配，静态结果不代表 P4-B 独立验收 | [H1 报告](../b7-r1-h1-package-hygiene-running.md)、[R1 总控核对](../p4-b7-r1-h1-r1-coordinator-review.md) |
| P4-B7-R1-H1-R1：staging 原子替换返修 | 用户启动的既有执行智能体 | `review / finished`，总控已核对 | 明确 commit point；六类故障边界与执行方 14/16 项证据通过，`P4-H1-ATOMIC-001` 已关闭 | [H1-R1 总控核对](../p4-b7-r1-h1-r1-coordinator-review.md) |
| P4-B7-R1-E3：C 盘 Electron 最小三角验证 | 用户启动的既有执行智能体 | `review / finished`，总控已接受 | A1 direct 与 A2 默认 Playwright 各一次通过；198/198 source、39/39 外部证据和零残留通过 | [E3 总控核对](../p4-b7-r1-e3-coordinator-review.md) |
| P4-B7-R1-E4：package、app.asar 与最终 EXE 恢复门禁 | 用户启动的既有执行智能体 | `blocked / finished` | 阶段 A 全过；唯一 package 在 Forge 裸 `pnpm` 命中失效用户 shim 后退出；P1/P2 未运行，资源已收口 | [E4 阻塞核对](../p4-b7-r1-e4-blocked-coordinator-review.md) |
| P4-B7-R1-E4-R1：pnpm 路径恢复与最终门禁续跑 | 用户启动的既有执行智能体 | `blocked / finished` | `$Args` 自动变量冲突导致 R0 实参为空；package/P1/P2 均未运行 | [E4-R1 报告](../b7-r1-e4-r1-pnpm-path-resume-running.md)、[总控核对](../p4-b7-r1-e4-r1-blocked-coordinator-review.md) |
| P4-D14：R0 PowerShell driver 恢复裁定 | 用户启动的 GPT-6 Astra 技术顾问 | `complete / finished` | 677 行方案、21 项冻结内容、ProcessStartInfo/Job Object 与 R0-only 合同已由总控接受 | [D14 技术裁定](../phase-4-d14-r0-driver-recovery-advice.md)、[总控审阅](../p4-d14-coordinator-review.md) |
| P4-B7-R1-E4-R0-R1：R0 driver 单独恢复与六项预检 | 用户启动的既有执行智能体 | `blocked / finished` | attempt-0 synthetic 捕获额外 `conhost.exe` 后安全停止；Q1～Q6/package 均 not_run，27 文件 evidence 匹配 | [运行说明](../b7-r1-e4-r0-r1-running.md)、[阻塞核对](../p4-b7-r1-e4-r0-r1-blocked-coordinator-review.md) |
| P4-B7-R1-E4-R0-R1-A1：标准流前置修正 | 用户启动的既有执行智能体 | `blocked / finished` | 三条标准流接管后仍由 `conhost.exe` 触发精确进程数门禁；Q1～Q6/package not_run，不允许 attempt-2 | [A1 运行说明](../b7-r1-e4-r0-r1-a1-running.md)、[总控核对](../p4-b7-r1-e4-r0-r1-a1-blocked-coordinator-review.md) |
| P4-B7-R1-E4-PKG-R1：真实预检交付 | 用户启动的既有执行智能体 | `blocked / finished` | Q1～Q6 原始证据通过；核对代码读取 `inner-0` 失败，package 0/1 | [运行说明](../b7-r1-e4-pkg-r1-running.md)、[总控核对](../p4-b7-r1-e4-pkg-r1-blocked-coordinator-review.md) |
| P4-B7-R1-E4-PKG-R2：package-only | 用户启动的既有执行智能体 | `review / finished`，总控已接受 | 唯一 package 成功；140 文件产物、fuses、67 项 Python resources、零污染和收口通过 | [运行说明](../b7-r1-e4-pkg-r2-running.md)、[总控核对](../p4-b7-r1-e4-pkg-r2-coordinator-review.md) |
| P4-B7-R1-E4-DYN-R1：最终动态门禁 | 用户启动的既有执行智能体 | `blocked / finished` | P1 1/1 被错误 root PID 假设提前停止；产品 unverified，P2 not_run，84/84 evidence 匹配 | [运行说明](../b7-r1-e4-dyn-r1-running.md)、[总控核对](../p4-b7-r1-e4-dyn-r1-blocked-coordinator-review.md) |
| P4-B7-R1-E4-DYN-R2：root promotion 恢复 | 用户启动的既有执行智能体 | `blocked / finished` | 79/79 evidence 匹配；存活 `cmd.exe` 包装进程导致 browser root 门禁停止；产品 unverified，自动启动路线耗尽 | [运行说明](../b7-r1-e4-dyn-r2-running.md)、[总控核对](../p4-b7-r1-e4-dyn-r2-blocked-coordinator-review.md) |
| P4-B7-R1-E5-FINAL：最终 EXE 黑盒门禁 | 用户启动的既有执行智能体 | `blocked / finished` | 直接启动、Host/认证、双窗口、安全和自然退出通过；模块为空，82/82 evidence 匹配 | [运行说明](../b7-r1-e5-final-exe-running.md)、[总控核对](../p4-b7-r1-e5-final-blocked-coordinator-review.md) |
| P4-B7-R1-E5-R1：module Profile 合同返修 | 用户启动的既有执行智能体 | `blocked / finished` | 四项真实 Profile 修改正确；定向回归 3 passed、3 failed，发现桌面 parser 不接受 canonical `@major`，package/EXE 均 0 次 | [E5-R1 运行说明](../b7-r1-e5-r1-module-contract-running.md)、[总控核对](../p4-b7-r1-e5-r1-blocked-coordinator-review.md) |
| P4-B7-R1-E5-R2：canonical Profile parser 返修 | 用户启动的既有执行智能体 | `blocked / finished`，代码修复接受 | canonical parser 与反例已修正；完整 package 前回归通过；package 因 Junction hoist 目录失败，EXE 未运行 | [E5-R2 运行说明](../b7-r1-e5-r2-profile-parser-running.md)、[总控核对](../p4-b7-r1-e5-r2-blocked-coordinator-review.md) |
| P4-B7-R1-E5-PKG-FINAL：隔离依赖与最终产品门禁 | 既有执行智能体 | `blocked / finished`；依赖成果已接受 | 普通依赖/离线安装/dist/22 项通过；package 1/1 fetch failed，EXE 0/1 | [交付说明](../b7-r1-e5-pkg-final-running.md)、[总控核对](../p4-b7-r1-e5-pkg-final-blocked-coordinator-review.md) |
| P4-B7-R1-E5-LOCALZIP：本地 ZIP 接线与最终门禁 | 既有执行智能体 | `review / finished`，接受为 C12 输入 | 115 evidence、274 source、140 out 匹配；package/EXE 成功 | [总控审阅](../p4-b7-r1-e5-localzip-coordinator-review.md) |
| P4-C12：Windows Shell 独立验收 | 既有测试智能体 | `blocked / finished` | P1 OUTBOX-001；24 项 1 failed/19 blocked/4 not_run；尚未 EXE | [报告](../testing/phase-4-c12-windows-shell-report.md)、[核对](../p4-c12-outbox-blocked-coordinator-review.md) |
| P4-B7-R2-OUTBOX：保留与确认返修 | 既有执行智能体 | `review / finished`，接受为复验输入 | 27/90开发测试、package/EXE成功；293source/140out匹配 | [总控核对](../p4-b7-r2-outbox-coordinator-review.md) |
| P4-C12-R1：outbox独立复验与剩余Windows验收 | 既有测试智能体 | `blocked / finished` | 原P1独立关闭；新REGISTRY-001为P1，59 passed/1 failed，尚未Windows | [核对](../p4-c12-r1-registry-blocked-coordinator-review.md) |
| P4-B7-R3-REGISTRY：设置键全局冲突返修 | 既有执行智能体 | 设置键修复已独立接受，旧执行finished | C12-R2原断言、相邻6、新8通过；setting缺陷关闭，不等于UI-04通过 | [R2核对](../p4-c12-r2-route-blocked-coordinator-review.md) |
| P4-C12-R2：设置键复验与Windows续跑 | 既有测试智能体 | `blocked / finished` | setting独立关闭；新增path P1，独立15passed/1failed，尚未Windows | [核对](../p4-c12-r2-route-blocked-coordinator-review.md) |
| P4-B7-R4-ROUTE：路径冲突返修 | 既有执行智能体 | 路径独立接受，旧执行finished | C12-R3原节点及9边界通过，PATH-001关闭；UI-04尚有缺口 | [核对](../p4-c12-r3-lazy-blocked-coordinator-review.md) |
| P4-C12-R3：路径复验与Windows续跑 | 既有测试智能体 | `blocked / finished` | path关闭，新LAZY-001；独立27passed/1failed，兼容52passed | [报告](../testing/phase-4-c12-r3-route-windows-report.md) |
| P4-B7-R5-LAZY：模块错误局部恢复 | 既有执行智能体 | `review / finished` | 稳定独立输入接受；132开发回归、新包及19项EXE门禁已核对 | [核对](../p4-b7-r5-lazy-coordinator-review.md) |
| P4-B7-R6-MODULE-READY：后台就绪后模块同步 | 既有执行智能体 | `review / finished` | 5文件、150开发及新EXE22项核对，接受为独立输入 | [核对](../p4-b7-r6-module-ready-coordinator-review.md) |
| P4-C12-R8-MODULES：模块同步及Windows续验 | 既有测试智能体 | `blocked / finished` | 9通过、1工具中断、3未执行；Windows未运行 | [报告](../testing/phase-4-c12-r8-modules-windows-report.md) |
| P4-C12-R8-R1：工具更正与剩余验收 | 既有测试智能体 | `blocked / finished` | 4独立通过，Windows正常退出P1；UI-01已接受passed | [报告](../testing/phase-4-c12-r8-r1-modules-windows-report.md) |
| P4-B7-R7-QUIT：正常关闭退出修复 | 既有执行智能体 | 普通关闭修复范围 `complete`；本人原状态保留 | R9独立证据关闭QUIT-001，不等于整项CMP-03/SUP-05通过 | [裁定](../p4-c12-r9-quit-h1-coordinator-review.md) |
| P4-C12-R9-QUIT：退出独立复验与Windows续验 | 既有测试智能体 | `blocked / finished` | 8/235、48兼容及W1的62比较通过；H1未解密即工具unknown | [报告](../testing/phase-4-c12-r9-quit-windows-report.md) |
| P4-C12-R9-R1：H1观察工具与Windows续验 | 既有测试智能体 | `blocked / finished` | 路径字面Contains错误；目标未启动，旧材料保持 | [报告](../testing/phase-4-c12-r9-r1-h1-windows-report.md) |
| P4-C12-R9-R2：脚本路径身份与Windows续验 | 既有测试智能体 | `ready / waiting_user` | 完整argv/路径/ready接线，工具开发与目标验收分层，不增动态额度 | [任务](prompts/p4-c12-r9-r2-path-windows-tester.md) |
| P4-C12-R4：lazy复验与Windows续跑 | 既有测试智能体 | `blocked / finished` | 原节点0pass/1fail；故障命中未证实，未新增产品缺陷，Windows0次 | [报告](../testing/phase-4-c12-r4-lazy-windows-report.md) |
| P4-C12-R4-R1：观察与续跑 | 既有测试智能体 | `blocked / finished` | mock1、#/daily、5016ms无alert；异常终态未定位 | [报告](../testing/phase-4-c12-r4-r1-observation-windows-report.md) |
| P4-D15：异常传播有限诊断 | 既有技术顾问 | `blocked / finished` | import/默认loader拒绝成立；P3超时无阶段回执，原证据保留 | [报告](../phase-4-d15-lazy-propagation-advice.md)、[总控核对](../p4-d15-bootstrap-coordinator-review.md) |
| P4-D15-R1：前置阶段取证 | 既有技术顾问 | `complete`（有限取证目标） | 40交付、CLI2/main1/修正1合规；真实导出/main/act完成，旧根因未知 | [总控接受](../p4-d15-r1-bootstrap-coordinator-review.md)、[报告](../phase-4-d15-r1-bootstrap-advice.md) |
| P4-C12-R4-R2：冷入口传播复验与续跑 | 既有测试智能体 | `ready / waiting_user` | 同步透传观察A及无门面冷B保留四断言，均通过后续恢复/Windows，不打包 | [Prompt](prompts/p4-c12-r4-r2-cold-entry-tester.md)、[起点](snapshots/p4-c12-r4-r2-start.sha256) |

## 当前阻塞与风险

- OUTBOX/setting/PATH与QUIT-001普通关闭范围已独立关闭；LAZY-001/UI-02仍有真实Windows条件，UI-01已passed。冷B/恢复/模块/退出通过保持；R9-R1路径错误属新工具，旧H1仍unknown，R9-R2不作产品返修。
- 原C12及后续首次失败与通过材料保留；受验包为固定R7新包，真实老化提示、跨重启数据、Windows chunk故障恢复及人工设备项仍待证据。
- `P4-B6-R1-REV-001` 已由 F1 修复并由 C11 独立关闭；没有发现新的 P4-A 产品 P0/P1。
- C11-R1 发现的 PostgreSQL 历史迁移 P0 已由 E1 保持原子性完成最小修复，并经 C11-R2 的真实历史、非法历史、catalog 和相邻迁移测试关闭；原失败继续保留为审计证据。
- 历史记录：R3 首轮只完成了执行方历史 fixture 和回滚断言准备；总控复核时 Docker Desktop/backend 进程均不存在。migration 摘要仍为起点值，缺陷没有修复。续跑必须使用 131 文件 R3-R1 新快照，不得重用旧 130 文件快照或重写已准备的 fixture。
- 历史记录：R3-R1 被提前发送给执行智能体时 Docker 仍未启动，因此第二次在相同环境门禁处停止；131 个输入起终点一致。下一次不再先派任务：用户先启动 Desktop，头脑风暴总控验证 Engine 可达和 Compose 状态后才发布恢复指令。
- E1 是 R3 系列中第一次实际修改 migration 的任务：旧实现的 PostgreSQL UPDATE→ALTER 顺序被替换为临时 UUID default+NOT NULL DDL 并立即移除 default；两类非法历史原子回滚测试补齐。R3 和 R3-R1 是环境停止点，不是两次代码返修。
- 旧 P2 测试的取消后错误从 `confirmation_required` 更新为 `pending_action_cancelled`，与 D10 冻结的 P4 合同一致；R1 只要求报告准确说明这是一项合同演进并继续证明零财务写入。
- Docker Desktop 已由 4.91.0 原位升级到 `4.92.0.240144`，双启动门禁和 T2 17 个真实 PG 用例均通过；执行方普通 down 后项目 Compose 服务为空。C11 可使用该环境，但 Engine 不可达时只能检查一次并停止，不重启 Desktop 或恢复 socket。
- 历史记录：R2 的三个冻结结构缺口已由 S1 关闭，执行方真实 PostgreSQL 门禁已由 T2 收口；当前剩余门禁是 C11 对迁移、事务、约束、多连接竞争和用户隔离给出独立证据。
- S1 报告中 10 个单文件摘要全部正确，但 10 行聚合值不可复算；总控按声明算法给出勘误 `583cac21...6a10`，并直接从实际 101 个文件生成 S2 manifest `8e926713...e74969`。
- S2 的 103 项终点摘要 `b1c4c80d...d5b18` 可复算。唯一失败用例把 code 创建时间固定为 `2026-09-26T02:00Z`，HTTP 路由却读取真实 UTC；两枚 code 在竞争前均过期。这是测试时钟漂移，不是产品并发缺陷。
- R2 报告的 99 个普通文件哈希、报告普通哈希和有序清单总摘要可复算；自引用 canonical 哈希不可按声明算法复算。S1 改用总控生成的独立 100 文件普通摘要清单，避免自引用。
- P4 近期采用单机单主人范围；现有 bootstrap owner/auth 保留但停止产品扩展，不制作注册或常规登录页面。删除认证结构延后到桌面入口有真实需求时再评估，避免现在破坏 user scope、微信绑定和已完成安全修复。
- P4 前地基检查点已建立；恢复操作只能由总控在保留现有工作的前提下执行，不把检查点理解为允许其他角色自行重置工作区。
- `P3-C9-PG-001` 已由 B5-R1 修复并经 C9-R2 独立关闭；原始失败报告继续保留为审计证据。
- C2 的并发用例原有测试夹具矛盾，经测试角色独立确认后仅修正测试基础设施；六项产品缺陷仍分别修复并通过复验。
- B1/B2a 只保证进程内去重；OpenClaw 命令上下文没有来源消息 ID，适用边界已写入 `P0-IF-002`。
- OpenClaw 官方 worker 曾触发终端安全软件行为告警；用户已于 2026-09-25 确认本机 OpenClaw 恢复且微信可连接。P4-A 审计和返修仍不操作该运行时。
- P1/P2 已冻结的真实 PostgreSQL 范围已通过；结论不外推到未设计或未运行的其他 PostgreSQL 场景。
- `tests/agent_finance` 原 5 项时间漂移已关闭；局部可控时钟保留 24 小时边界，并通过独立还原、时区和线程检查。
- B2a 首次执行子任务在写出实现后错过检查点且不再活动，已按已有输出恢复；这次中断不作为失败结论。

## 下一次总控检查

1. 用户将C12-R4-R2全文发给既有测试智能体；旧任务、顾问和执行停止，测试新任务接单unverified。
2. 测试绑定新起点，冷main同实例传播观察A及无门面冷B各一次，保留原四断言；不重复D15/旧成功回归或打包。
3. A/B通过后同任务继续独立恢复与剩余Windows；失败则按实际传播阶段交总控，不只延时或继续bootstrap。缺陷关闭/完整矩阵/真实设备缺口分别裁定。
4. P4-B独立接受后触发高保真参考图/模型策略提醒，再规划P4-C。
