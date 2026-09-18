# 个人财务 Agent：开发与学习项目

当前阶段：阶段 0 已完成。P1 数据层与 P2-A 财务 Agent 的本地及已冻结 PostgreSQL 范围均通过独立验收；`PG-C7-DATA-001` 已关闭。当前工程维护任务 P2-TIME-R1 已准备，消除 5 个 Agent 测试的固定时间漂移，等待执行智能体接单。OpenClaw worker 安全事件仍暂停运行时恢复。

项目有两个目标：通过活动、账目和可更新计划管理大学生活开支；围绕真实代码建立 AI Agent 应用工程能力。

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
- [P2-TIME-R1 执行智能体 Prompt](docs/coordination/prompts/p2-time-r1-executor.md)：通过测试可控时钟消除日期漂移，保留 24 小时过期边界。
- [智能体进度总览](docs/coordination/overview.md)：各角色接单、进行、阻塞、交付与验收状态。
- [任务智能体 Prompt 模板](docs/coordination/task-prompt-template.md)：用户或总控派发技术顾问、执行和测试任务时使用的可验收任务卡。

以上文档是可修改的讨论稿，不代表候选框架、微信通道或部署服务已经接入。真实账单、个人活动资料和密钥将作为运行数据管理，不提交到代码仓库。
