# 个人财务 Agent：开发与学习项目

当前阶段：阶段 0、P1 数据层、P2-A 财务 Agent 和 P3 活动 Markdown 导入纵向切片均已完成独立验收。P4-A Host、身份和通用状态地基正在返修 `P4-C11-R1-PG-001`：真实 PostgreSQL 含 P1 财务双分录、P2 run/pending 和 P3 import 历史时，user-scope migration 因待处理的外键触发器事件无法完成正向升级。执行方历史回归已经准备，但 R3 和 R3-R1 均因 Docker Desktop 尚未启动而在测试前停止；当前暂停派发，等待用户启动 Engine 后由总控先验证环境。矩阵暂为 62 passed、2 failed，P4-A 尚未 `complete`。检查点 `checkpoint/p3-foundation` 固定在提交 `6e89762`，P4 仍处于正式发布前开发阶段。

项目有三个目标：通过活动、账目和可更新计划管理大学生活开支；建立覆盖日常管钱与财富管理的个人 AI 系统；围绕真实代码学习可扩展 Agent Host、模块 Agent、工具、记忆、workflow、前后端和工程验证。财务是第一组内置应用，架构为以后新增 AI 应用模块保留受控接入面。

当前终端范围：Windows 桌面应用提供完整界面，手机通过微信消息交互。两种入口使用同一后端与数据，不开发独立 Android 应用。

角色分为头脑风暴（总协调）、技术顾问（选型、教学规划与教学子任务调度）、执行智能体（编码与执行子任务协调）、测试智能体（独立验证与代码质量改进）。用户已指定独立的“技术顾问”任务负责工程教学，按教学需要组织代码检查、测试和学习资料检索。分工与交付约定见下文。

- [项目计划](docs/project-plan.md)：需求、数据流、技术候选、约束和待决策项。
- [学习路线](docs/learning-roadmap.md)：功能、技术、练习和验收能力的对应关系。
- [技术顾问与教学交接说明](docs/teaching-handoff.md)：教学职责、子任务调度、练习检查和代码交接。
- [微信验证步骤](docs/wechat-validation.md)：开发方与用户的分工、验证动作和通过标准。
- [任务分工与进度](docs/project-coordination.md)：四类角色的边界、协作流程和当前阶段状态。
- [阶段 0 前期任务分配](docs/phase-0-assignments.md)：最小 Agent、微信探针、技术建议和独立测试的任务包。
- [阶段 0 接口冻结记录](docs/phase-0-interface-freeze.md)：B1/C2/B2 共用的边界、错误、去重与探针契约。
- [B2b OpenClaw 桥接运行说明](docs/b2b-running.md)：本机插件构建、测试、打包和隔离宿主加载证据。
- [D2 跨语言数据流教学](docs/phase-0-d2-bridge-teaching.md)：结合实际 Python/TypeScript 代码讲解 HTTP、FastAPI、幂等和微信桥接。
- [W1 真实微信验收报告](docs/testing/phase-0-w1-wechat-report.md)：手机实收、停服错误和自然语言工具的独立结论。
- [阶段 1 数据底座任务书](docs/phase-1-data-foundation-brief.md)：活动、账目、收入、预算的数据建模范围和前置任务。
- [阶段 1 接口冻结](docs/phase-1-interface-freeze.md)：P1-B3 必须遵守的数据模型、金额、事务、幂等、错误和测试边界。
- [P1-B3 执行智能体 Prompt](docs/coordination/prompts/p1-b3-executor.md)：用户粘贴到侧边栏执行智能体任务的正式开发任务卡。
- [P1-C4 测试智能体 Prompt](docs/coordination/prompts/p1-c4-tester.md)：用户粘贴到侧边栏测试智能体任务的独立验收任务卡。
- [P1-B3-R1 执行智能体返修 Prompt](docs/coordination/prompts/p1-b3-r1-executor.md)：修复 C4 确认的三个数据层缺陷并生成新快照。
- [P1-C4-R2 测试智能体复验 Prompt](docs/coordination/prompts/p1-c4-r2-tester.md)：绑定 R1 新快照，定向复验三个缺陷和迁移链。
- [P2-D5 技术顾问 Prompt](docs/coordination/prompts/p2-d5-technical-adviser.md)：并行设计自然语言记账到财务工具的数据流与接口边界。
- [P2 接口冻结](docs/phase-2-interface-freeze.md)：自然语言单笔支出、查询、候选确认、幂等和 HTTP 边界。
- [P2-B4 执行智能体 Prompt](docs/coordination/prompts/p2-b4-executor.md)：实现自然语言单笔支出最小纵向切片。
- [P2-C5 测试智能体 Prompt](docs/coordination/prompts/p2-c5-tester.md)：并行设计 P2-A 独立验收矩阵。
- [P2-C6 测试智能体 Prompt](docs/coordination/prompts/p2-c6-tester.md)：在 P2-B4 稳定快照上执行 P2-A 独立验收。
- [P2-D6 实现后教学](docs/phase-2-d6-agent-teaching.md)：结合实际代码讲解 Agent 数据流、状态、幂等、事务与测试证据。
- [PG-C7 测试智能体 Prompt（已归档）](docs/coordination/prompts/pg-c7-tester.md)：该专项已执行，不得重复派发。
- [PG-C7-DATA-R1 执行智能体 Prompt（已完成执行）](docs/coordination/prompts/pg-c7-data-r1-executor.md)：修复 PostgreSQL 首次写入被误判为并发冲突的问题。
- [PG-C7-DATA-R2 测试智能体 Prompt（已完成）](docs/coordination/prompts/pg-c7-data-r2-tester.md)：绑定 R1 两文件快照完成独立复验。
- [PG-C7-DATA-R2 验收报告](docs/testing/phase-2-c7-r2-postgresql-report.md)：P1 8/8、P2 SPG 4/4、相邻 SQLite 9/9 通过。
- [P2-TIME-R1 执行智能体 Prompt（已完成）](docs/coordination/prompts/p2-time-r1-executor.md)：通过测试可控时钟消除日期漂移，保留 24 小时过期边界。
- [P2-TIME-C2 测试智能体 Prompt（已完成）](docs/coordination/prompts/p2-time-c2-tester.md)：绑定七文件快照，独立核验 28 项、到期边界与时钟恢复。
- [P2-TIME-C2 独立验收报告](docs/testing/p2-time-c2-report.md)：28/28、原测试 23/23 与时钟还原审计 28/28 通过。
- [P3 活动 Markdown 导入任务书](docs/phase-3-activity-import-brief.md)：定义“文本输入 → 候选预览 → 用户确认 → 原子导入”的首个切片与安全边界。
- [P3-D7 技术顾问 Prompt](docs/coordination/prompts/p3-d7-technical-adviser.md)：比较并推荐解析、数据模型、API、幂等与事务方案。
- [P3-C8 测试智能体 Prompt](docs/coordination/prompts/p3-c8-tester.md)：在实现前建立独立验收矩阵，不执行测试或修改产品。
- [P3 活动导入接口冻结](docs/phase-3-interface-freeze.md)：冻结离线语法、持久候选、金额范围、API、事务、幂等和数据库证据。
- [P3-B5 执行智能体 Prompt](docs/coordination/prompts/p3-b5-executor.md)：实现活动 Markdown 导入纵向切片并完成执行方自测。
- [P3-B5 运行与交接](docs/b5-activity-import-running.md)：实际数据流、迁移、自测、R1 返修和最终 22 文件快照。
- [P3-C9 测试智能体 Prompt](docs/coordination/prompts/p3-c9-tester.md)：在固定 B5 快照上执行 89 项独立验收及真实 PostgreSQL 门禁。
- [P3-C9 独立验收报告](docs/testing/phase-3-c9-activity-import-report.md)：本地范围通过，PostgreSQL 迁移缺陷阻断 24 项并导致 1 项失败。
- [P3-B5-R1 执行智能体 Prompt](docs/coordination/prompts/p3-b5-r1-executor.md)：只缩短外键约束名、同步 downgrade，并实际复跑九项 PostgreSQL。
- [P3-C9-R2 测试智能体 Prompt](docs/coordination/prompts/p3-c9-r2-tester.md)：绑定 R1 新快照，复验独立 PostgreSQL、迁移和 89 项最终状态。
- [P3-C9-R2 独立复验报告](docs/testing/phase-3-c9-r2-activity-import-report.md)：89/89 项通过，执行方和独立 PostgreSQL 门禁通过，原 P0 缺陷关闭。
- [P0-P3 实现后教材](docs/teaching/README.md)：按 P0 → P1 → P2 → P3 学习实际代码、数据流、测试证据与练习；同目录提供四册 Markdown。
- [P0 PDF](output/pdf/p0-agent-http-wechat-teaching.pdf)、[P1 PDF](output/pdf/p1-finance-data-foundation-teaching.pdf)、[P2 PDF](output/pdf/p2-finance-agent-workflow-teaching.pdf)、[P3 PDF](output/pdf/p3-activity-import-teaching.pdf)：四册经过程序化检查和逐页视觉检查的教学版 PDF。
- [P0-P3-D8 技术顾问 Prompt](docs/coordination/prompts/p0-p3-d8-technical-adviser.md)：四册教材与 PDF 的已完成任务卡和验收边界。
- [P4 Windows 财务驾驶舱头脑风暴](docs/phase-4-desktop-cockpit-brainstorm.md)：澄清微信记账、桌面聊天、数据可视化、迷你助手、未来消费和投资模块的关系及建议切片。
- [P4 可扩展个人 AI 应用 Host 架构草案](docs/phase-4-modular-agent-host-architecture.md)：定义账户、模块注册、Agent Profile、工具/MCP、分层记忆、毛毛、主题与后续 AI 应用接入面。
- [P4-D9 Agent Host 最小技术方案](docs/phase-4-d9-modular-agent-host-advice.md)：基于现有代码给出模块化单体、身份、记忆、Electron 和第二模块证明的实施建议。
- [P4-C10 测试智能体 Prompt](docs/coordination/prompts/p4-c10-modular-agent-host-test-matrix.md)：在实现前建立 P4-A～P4-D 分层独立验收矩阵。
- [P4 模块化 Agent Host 测试矩阵](docs/testing/phase-4-modular-agent-host-test-matrix.md)：120 个尚未执行的分层验收案例，覆盖四个 P4 切片。
- [P4 接口冻结](docs/phase-4-interface-freeze.md)：冻结总架构和 P4-A Host、身份、用户隔离、记忆与 API 合同。
- [P4-B6 执行智能体 Prompt](docs/coordination/prompts/p4-b6-host-foundation-executor.md)：实现 P4-A Host、身份和通用状态地基。
- [Docker Desktop 启动故障记录与恢复计划](docs/docker-desktop-incident-2026-09-26.md)：记录 4.91.0 反复出现的 AF_UNIX socket 故障，以及升级 4.92.0 后的双启动恢复证据和后续门禁。
- [P4-B6-R2 最终执行方交付总控核对](docs/p4-b6-r2-final-coordinator-review.md)：核对 T2 的 17/17 真实 PostgreSQL 证据、105 文件最终快照和 C11 进入条件。
- [P4-C11 测试智能体 Prompt](docs/coordination/prompts/p4-c11-host-foundation-tester.md)：绑定最终 R2 快照，对 P4-A 64 项、22 个接管审计问题和 P0～P3 兼容性执行独立验收。
- [P4-C11 总控核对](docs/p4-c11-coordinator-review.md)：确认 64 项与产品快照通过，同时登记历史迁移独立证据缺口和有限补证口径。
- [P4-C11-R1 测试证据返修 Prompt](docs/coordination/prompts/p4-c11-r1-tester-evidence-repair.md)：只补强 P1/P2/P3 历史正向迁移证据并纠正报告，不修改产品或重复全部回归。
- [P4-C11-R1 总控核对](docs/p4-c11-r1-coordinator-review.md)：接受真实 PostgreSQL 历史升级的 P0 失败结论并冻结窄范围返修边界。
- [P4-B6-R3 执行智能体 Prompt](docs/coordination/prompts/p4-b6-r3-postgresql-history-migration-executor.md)：保持 migration 原子性，修复带历史外键事实时的 PostgreSQL pending-trigger ALTER 阻断。
- [P4-B6-R3-R1 续跑 Prompt](docs/coordination/prompts/p4-b6-r3-r1-postgresql-history-migration-resume-executor.md)：保留 R3 已准备的历史回归，在 Docker Engine 恢复后先复现原失败，再完成最小 migration 返修。
- [智能体进度总览](docs/coordination/overview.md)：各角色接单、进行、阻塞、交付与验收状态。
- [任务智能体 Prompt 模板](docs/coordination/task-prompt-template.md)：用户或总控派发技术顾问、执行和测试任务时使用的可验收任务卡。

P4 头脑风暴仍是可修改的讨论稿，不代表候选框架或部署服务已经接入。P0～P3 的实现、测试证据和教材按各自状态文件记录。真实账单、个人活动资料和密钥将作为运行数据管理，不提交到代码仓库。
# Maris
