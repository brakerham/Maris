# 项目进度总览

更新时间：2026-09-29 02:14，Asia/Shanghai
维护者：头脑风暴智能体

## 当前阶段

P0～P3 和 P4-A 已完成验收。H1-R1、E3 和 PKG-R2 已通过总控核对。DYN-R1 的 app.asar 已实际启动，但 runner 在窗口和 preload API 验证前错误地要求 Playwright 返回的短生命周期 PID 仍是存活 browser root。总控接受该编排失败和 84/84 evidence，产品保持未验证。下一步只修正任务外 root promotion，以新 P1 单次预算恢复；P1 通过后才运行最终 EXE。24 项 P4-B 独立矩阵和 P4-C12 仍未启动。GitHub 上的既有提交仍只是保护性检查点；产品尚未发布正式大版本。

部署范围已收紧为单机、单主人、本地数据库。其他人使用时在自己的设备安装独立实例；公众注册、多账号、云账户和注册/常规登录 UI 暂停。内部 `user_id`、Principal、session 和微信绑定继续作为本地数据安全边界，桌面端以后再决定自动本地会话或可选应用锁。

## 角色状态

| 角色 | 任务状态 | 运行状态/当前步骤 | 最近进展或心跳 | 下一检查点 | 证据 |
| --- | --- | --- | --- | --- | --- |
| 头脑风暴 | `ready / waiting_user` | 已接受 DYN-R1 runner 编排失败，冻结唯一 browser child 提升规则与新 P1 预算 | 2026-09-29 02:14 | 用户把 DYN-R2 Prompt 发给既有执行智能体 | [DYN-R1 阻塞核对](../p4-b7-r1-e4-dyn-r1-blocked-coordinator-review.md) |
| 技术顾问 | `complete / finished`（P4-D14） | 677 行技术裁定、21 项冻结内容与六项待决策已由总控接受 | 2026-09-28 16:47 | 保持停止；不运行 R0 或创建后续任务 | [D14 技术裁定](../phase-4-d14-r0-driver-recovery-advice.md) |
| 执行智能体 | `ready / waiting_user`（P4-B7-R1-E4-DYN-R2） | DYN-R1 已 blocked/finished；产品 unverified，进程和资源已收口 | 2026-09-29 02:14 | 用户发送 DYN-R2 Prompt；修 runner 后新 P1 1/1 | [DYN-R2 Prompt](prompts/p4-b7-r1-e4-dyn-r2-executor.md)、[固定快照](snapshots/p4-b7-r1-e4-dyn-r2-start.sha256) |
| 测试智能体 | `complete / finished`（P4-C11-R2） | 当前停止；P4-B 的 24 项仍全部 `not_run` | 2026-09-27 12:55 | 等 B7 稳定终点快照和总控 C12 任务卡 | [P4-B 矩阵](../testing/phase-4-modular-agent-host-test-matrix.md)、[角色日志](agents/tester.md) |

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
| P4-B7-R1-E4-DYN-R2：root promotion 恢复 | 用户启动的既有执行智能体 | `ready / waiting_user` | 只修任务外 runner；新 P1 通过后才执行 P2，不重跑 package | [DYN-R2 Prompt](prompts/p4-b7-r1-e4-dyn-r2-executor.md)、[固定快照](snapshots/p4-b7-r1-e4-dyn-r2-start.sha256) |
| P4-C12：Windows Shell 独立验收 | 用户启动的既有测试智能体 | `not_started` | 等 B7 稳定快照后生成任务卡；执行 24 个 P4-B 案例和 Windows 人工门禁 | [P4-B 矩阵](../testing/phase-4-modular-agent-host-test-matrix.md) |

## 当前阻塞与风险

- H1 replacement 原子性缺陷已关闭，E3 C 盘路线稳定。R0-R1 首次 synthetic 已证明 Job 关联和异常收口工作，但 native console host 超出执行方自定单元预算；四类 synthetic 仍为 0/4。A1 使用唯一前置修正预算显式接管标准流，不提高 live 预算；再次失败就停止。该任务仍不授权 package，也不得把 harness 失败写成 pnpm 或产品失败。
- P4-C12 不能提前启动：24 项矩阵已经存在，不需要测试智能体再次设计；只有 B7 形成稳定产品快照后，测试智能体才能绑定快照执行独立验收。
- `P4-B6-R1-REV-001` 已由 F1 修复并由 C11 独立关闭；没有发现新的 P4-A 产品 P0/P1。
- C11-R1 发现的 PostgreSQL 历史迁移 P0 已由 E1 保持原子性完成最小修复，并经 C11-R2 的真实历史、非法历史、catalog 和相邻迁移测试关闭；原失败继续保留为审计证据。
- R3 首轮只完成了执行方历史 fixture 和回滚断言准备；总控复核时 Docker Desktop/backend 进程均不存在。migration 摘要仍为起点值，缺陷没有修复。续跑必须使用 131 文件 R3-R1 新快照，不得重用旧 130 文件快照或重写已准备的 fixture。
- R3-R1 被提前发送给执行智能体时 Docker 仍未启动，因此第二次在相同环境门禁处停止；131 个输入起终点一致。下一次不再先派任务：用户先启动 Desktop，头脑风暴总控验证 Engine 可达和 Compose 状态后才发布恢复指令。
- E1 是 R3 系列中第一次实际修改 migration 的任务：旧实现的 PostgreSQL UPDATE→ALTER 顺序被替换为临时 UUID default+NOT NULL DDL 并立即移除 default；两类非法历史原子回滚测试补齐。R3 和 R3-R1 是环境停止点，不是两次代码返修。
- 旧 P2 测试的取消后错误从 `confirmation_required` 更新为 `pending_action_cancelled`，与 D10 冻结的 P4 合同一致；R1 只要求报告准确说明这是一项合同演进并继续证明零财务写入。
- Docker Desktop 已由 4.91.0 原位升级到 `4.92.0.240144`，双启动门禁和 T2 17 个真实 PG 用例均通过；执行方普通 down 后项目 Compose 服务为空。C11 可使用该环境，但 Engine 不可达时只能检查一次并停止，不重启 Desktop 或恢复 socket。
- R2 的三个冻结结构缺口已由 S1 关闭，执行方真实 PostgreSQL 门禁已由 T2 收口；当前剩余门禁是 C11 对迁移、事务、约束、多连接竞争和用户隔离给出独立证据。
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

1. 用户把 `docs/coordination/prompts/p4-b7-r1-h1-r1-staging-atomicity-executor.md` 全文发送给既有执行智能体。
2. 执行智能体只修 replacement commit point 与六类确定性故障注入；不重做 allowlist，不启动 Electron/Forge package/sidecar/数据库。
3. 技术顾问和测试智能体保持停止；不得重复 H1/D13/E2 系列，E3 与 P4-C12 继续 `not_started`。
