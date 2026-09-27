# 项目进度总览

更新时间：2026-09-27 14:05，Asia/Shanghai
维护者：头脑风暴智能体

## 当前阶段

P0～P3 和 P4-A 已完成验收。P4-A 的 64 项矩阵全部通过，PostgreSQL 历史迁移缺陷 `P4-C11-R1-PG-001` 已关闭，并固定 134 文件最终快照。GitHub 上的既有提交仍只是保护性检查点；产品尚未发布正式大版本。P4 从单一财务 workflow 的界面扩展为 Personal AI Host：财务生活与财富管理作为首批模块，Host 统一身份、Agent Profile、工具/MCP、分层记忆、权限、桌面 Shell、毛毛和设置扩展面。

部署范围已收紧为单机、单主人、本地数据库。其他人使用时在自己的设备安装独立实例；公众注册、多账号、云账户和注册/常规登录 UI 暂停。内部 `user_id`、Principal、session 和微信绑定继续作为本地数据安全边界，桌面端以后再决定自动本地会话或可选应用锁。

## 角色状态

| 角色 | 任务状态 | 运行状态/当前步骤 | 最近进展或心跳 | 下一检查点 | 证据 |
| --- | --- | --- | --- | --- | --- |
| 头脑风暴 | `in_progress` | P4-B 视觉基线已确认；P4-D11 技术顾问任务卡已准备 | 2026-09-27 14:05 | 用户发送 D11 Prompt；收到方案后冻结 P4-IF-003 | [D11 Prompt](prompts/p4-d11-windows-shell-technical-adviser.md)、[P4-B 讨论稿](../phase-4-b-windows-shell-brainstorm.md) |
| 技术顾问 | `ready`（P4-D11） | `waiting_user`：等待接收 Windows Shell 技术方案任务卡 | 2026-09-27 14:05 | 接单后比较工具链、IPC、supervisor、毛毛和测试方案 | [D11 Prompt](prompts/p4-d11-windows-shell-technical-adviser.md)、[角色日志](agents/technical-adviser.md) |
| 执行智能体 | `complete / finished`（P4-A） | E1 修复已由 C11-R2 独立确认，当前停止 | 2026-09-27 12:08 | 等待 P4-B 新任务卡 | [E1 运行说明](../b6-r3-r1-e1-postgresql-history-migration-running.md)、[角色日志](agents/executor.md) |
| 测试智能体 | `complete / finished`（P4-C11-R2） | 独立 7 项、执行兼容 19 项通过，P4-A 64/64 passed | 2026-09-27 12:55 | 保持停止；等待 P4-B 独立矩阵执行任务 | [C11-R2 报告](../testing/phase-4-c11-r2-postgresql-history-report.md)、[角色日志](agents/tester.md) |

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

## 当前阻塞与风险

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

1. P4-A 验收提交 `88fb178` 已按用户要求推送新仓库 Maris 的 `origin/main`。
2. 与用户确认 P4-B 的主窗口布局、模块 Agent 呈现和毛毛首版体验；财务业务闭环继续保留给 P4-C。
3. 产品范围确认后先生成技术顾问任务，比较并冻结 Electron/React/TypeScript、构建、路由、状态、OpenAPI、IPC、supervisor 和桌面测试方案；执行与测试智能体继续停止。
