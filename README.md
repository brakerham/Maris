# 个人财务 Agent：开发与学习项目

当前阶段：阶段 0、P1 数据层、P2-A 财务 Agent、P3 活动 Markdown 导入和 P4-A Host/身份/通用状态地基均已完成独立验收。H1-R1 已关闭 Python package resource staging 的 `P4-H1-ATOMIC-001`；E3 的 C 盘 direct 与默认 Playwright loader 各一次通过，198 文件 source 与 39 文件外部证据均已由总控复算。当前只进行 E4 的 C 盘最终构建门禁：唯一一次 Forge package，通过后再各执行一次 app.asar 和最终 `Maris.exe`。24 项 P4-B 独立矩阵和 P4-C12 尚未启动。P4-C 财务驾驶舱和 P4-D 财富管理尚未开始。检查点 `checkpoint/p3-foundation` 固定在提交 `6e89762`，P4 仍处于正式发布前开发阶段。

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
- [P4-B6-R3-R1-E1 恢复 Prompt](docs/coordination/prompts/p4-b6-r3-r1-e1-engine-recovered-executor.md)：记录总控已通过的 Engine/Compose 门禁，恢复同一返修并沿用 131 文件固定输入。
- [P4-C11-R2 测试智能体 Prompt](docs/coordination/prompts/p4-c11-r2-postgresql-history-tester.md)：只复验原 PostgreSQL 历史失败、非法历史原子拒绝和相邻 migration，不重复完整 C11。
- [P4-A 最终总控验收](docs/p4-a-final-coordinator-review.md)：接受 64/64 独立矩阵、关闭历史迁移 P0，并固定 134 文件最终快照。
- [P4-B Windows Shell、毛毛与模块交互头脑风暴](docs/phase-4-b-windows-shell-brainstorm.md)：讨论主窗口、模块导航、Agent 面板、毛毛、Tray、主题、本地后端生命周期及 P4-C/P4-D 边界。
- [P4-D11 技术顾问 Prompt](docs/coordination/prompts/p4-d11-windows-shell-technical-adviser.md)：比较并推荐 P4-B 的 Electron/React/TypeScript、OpenAPI、IPC、BackendSupervisor、毛毛、主题和桌面测试方案。
- [P4-D11 Windows Shell 技术方案](docs/phase-4-d11-windows-shell-technical-advice.md)：给出工具链、三层安全边界、模块 UI、Supervisor、outbox、毛毛、测试与七个实施里程碑。
- [P4-D11 总控审阅](docs/p4-d11-coordinator-review.md)：接受技术方案并登记 TypeScript 版本与 pnpm/Forge 的两项勘误。
- [P4-IF-003 Windows Shell 接口冻结](docs/phase-4-interface-freeze-003.md)：冻结 P4-B 的精确版本、IPC、owner 会话、nonce/readiness、窗口、主题、毛毛、测试与变更控制。
- [P4-B7 执行智能体 Prompt](docs/coordination/prompts/p4-b7-windows-shell-executor.md)：按七个内部里程碑实现桌面 Shell 并提交执行方自测和固定交付。
- [P4-B7 固定输入快照](docs/coordination/snapshots/p4-b7-start.sha256)：绑定 P4-A 产品代码、执行方测试及 P4-B 冻结文档；开始前必须逐行复算。
- [P4-B7 受阻运行说明](docs/b7-windows-shell-running.md)：记录已保留实现、执行方测试/打包证据、供应链 P0 和 main 真实 Host 组合缺口。
- [P4-D12 技术顾问 Prompt](docs/coordination/prompts/p4-d12-b7-supply-chain-technical-adviser.md)：完整核对 16 项 advisory，裁定精确依赖图与 B7-R1 真实接线边界。
- [P4-D12 技术裁定](docs/phase-4-d12-b7-supply-chain-advice.md)：16 项公告、五路线、三候选解析、22 条冻结建议、真实 Host 组合和教学地图。
- [P4-D12 总控审阅](docs/p4-d12-coordinator-review.md)：批准发布前 Forge 8 alpha 候选和 desktop core readiness，明确退出条件。
- [P4-IF-004](docs/phase-4-interface-freeze-004.md)：冻结供应链候选、desktop sidecar/readiness、composition root、Supervisor、owner/token 和完整门禁。
- [P4-B7-R1 执行智能体 Prompt](docs/coordination/prompts/p4-b7-r1-windows-shell-supply-chain-runtime-executor.md)：先修复供应链，再完成 main 到真实 Host 的有限续段。
- [P4-B7-R1 固定输入快照](docs/coordination/snapshots/p4-b7-r1-start.sha256)：绑定 182 个 P4-A/B7/D12/冻结/任务输入文件。
- [P4-B7-R1 阻塞总控核对](docs/p4-b7-r1-blocked-coordinator-review.md)：接受官方 Electron 下载临时失败的停止结论，保留供应链成果并冻结恢复顺序。
- [P4-B7-R1-E1 恢复 Prompt](docs/coordination/prompts/p4-b7-r1-e1-electron-download-resume-executor.md)：在官方资产重新可达后，对最终 lock 重做审计并从 Electron/Vitest 门禁继续真实 Host 组合。
- [P4-B7-R1-E1 固定输入快照](docs/coordination/snapshots/p4-b7-r1-e1-start.sha256)：绑定 187 个 R1 产品、证据、状态和恢复任务输入文件。
- [P4-B7-R1-E1 重复网络阻塞总控核对](docs/p4-b7-r1-e1-blocked-coordinator-review.md)：确认正文 GET 在 Node 与 curl 中均被重置，停止重复执行任务并冻结网络切换后的官方缓存恢复路线。
- [P4-B7-R1-E2 网络门禁](docs/p4-b7-r1-e2-network-gate.md)：确认透明 TUN 路由生效，并从官方资产成功取得限量 1 MiB 正文。
- [P4-B7-R1-E2 执行智能体 Prompt](docs/coordination/prompts/p4-b7-r1-e2-electron-runtime-resume-executor.md)：不重复供应链审计，从官方 Electron 安装继续真实 Host、sidecar、package、E2E 和 EXE 门禁。
- [P4-B7-R1-E2 固定输入快照](docs/coordination/snapshots/p4-b7-r1-e2-start.sha256)：绑定 192 个 E1 产品、证据、网络门禁、角色状态和 E2 任务输入文件。
- [P4-B7-R1-E2 阻塞总控核对](docs/p4-b7-r1-e2-blocked-coordinator-review.md)：接受 194 文件稳定现场，拆分 Playwright 启动合同与 package hygiene 两个问题，并冻结恢复路线。
- [P4-B7-R1-E2-R1 执行智能体 Prompt](docs/coordination/prompts/p4-b7-r1-e2-r1-electron-launch-package-executor.md)：先做最小启动兼容性探针，再分离 app.asar 与真实 EXE 测试并建立确定性 Python 资源 allowlist。
- [P4-B7-R1-E2-R1 固定输入快照](docs/coordination/snapshots/p4-b7-r1-e2-r1-start.sha256)：绑定 200 个 E2 产品、证据、执行状态、总控核对和 R1 任务输入文件。
- [P4-B7-R1-E2-R1 阻塞总控核对](docs/p4-b7-r1-e2-r1-blocked-coordinator-review.md)：接受最小 fixture 的 GPU child `0xC0000135` 与 browser `0x80000003` 失败链，停止重复动态尝试。
- [P4-B7 Electron Windows 环境证据](docs/p4-b7-electron-windows-environment-evidence.md)：记录 Windows 25H2 build 26200、混合显卡、运行时、事件日志和上游相似问题。
- [P4-D13 技术顾问 Prompt](docs/coordination/prompts/p4-d13-electron-windows-crash-technical-adviser.md)：只读裁定 C/D 盘 A/B、sandbox、诊断工具、版本策略和 package hygiene 拆分顺序。
- [P4-D13 固定输入快照](docs/coordination/snapshots/p4-d13-start.sha256)：绑定 205 个产品、失败现场、环境证据、角色状态和 D13 任务输入文件。
- [P4-D13 技术裁定](docs/phase-4-d13-electron-windows-crash-advice.md)：冻结首个故障、证据等级、有限动态矩阵、诊断开关与 package hygiene 拆分建议。
- [P4-D13 总控审阅](docs/p4-d13-coordinator-review.md)：接受 D13 并裁定八个未决问题，决定先执行无 Electron 的 H1。
- [P4-IF-005](docs/phase-4-interface-freeze-005.md)：冻结 Electron Windows 诊断顺序与 Python package resource staging 合同。
- [P4-B7-R1-H1 执行智能体 Prompt](docs/coordination/prompts/p4-b7-r1-h1-package-hygiene-executor.md)：只实现 allowlist、原子 staging、manifest 与静态测试，不启动 Electron 或 Forge package。
- [P4-B7-R1-H1 固定输入快照](docs/coordination/snapshots/p4-b7-r1-h1-start.sha256)：绑定 H1 的产品、证据、冻结、角色状态和任务输入文件。
- [P4-B7-R1-H1 运行说明](docs/b7-r1-h1-package-hygiene-running.md)：记录 allowlist、staging、执行方测试、未运行门禁与资源收口。
- [P4-B7-R1-H1 总控核对](docs/p4-b7-r1-h1-coordinator-review.md)：接受 H1 有效证据并登记 `P4-H1-ATOMIC-001`。
- [P4-B7-R1-H1-R1 执行智能体 Prompt](docs/coordination/prompts/p4-b7-r1-h1-r1-staging-atomicity-executor.md)：只修 replacement commit point 与确定性故障注入测试。
- [P4-B7-R1-H1-R1 固定输入快照](docs/coordination/snapshots/p4-b7-r1-h1-r1-start.sha256)：绑定 H1 终点、总控缺陷核对和 R1 任务输入。
- [P4-B7-R1-H1-R1 总控核对](docs/p4-b7-r1-h1-r1-coordinator-review.md)：关闭原子替换缺陷并接受 H1 为 E3 输入。
- [P4-B7-R1-E3 执行智能体 Prompt](docs/coordination/prompts/p4-b7-r1-e3-c-drive-electron-triangle-executor.md)：只运行一次 C 盘 direct，成功后条件运行一次同目录 Playwright。
- [P4-B7-R1-E3 总控核对](docs/p4-b7-r1-e3-coordinator-review.md)：接受两次单次动态门禁，登记 A1 driver 过严判定和有限执行位置结论。
- [P4-B7-R1-E4 执行智能体 Prompt](docs/coordination/prompts/p4-b7-r1-e4-package-product-gates-executor.md)：从新的 C 盘固定源码副本依次执行 package、app.asar 与最终 EXE 门禁，验证中不修改产品。
- [P4-B7-R1-E3 固定输入快照](docs/coordination/snapshots/p4-b7-r1-e3-start.sha256)：绑定 H1-R1 终点、D13/IF-005、总控核对与 E3 任务卡。
- [智能体进度总览](docs/coordination/overview.md)：各角色接单、进行、阻塞、交付与验收状态。
- [任务智能体 Prompt 模板](docs/coordination/task-prompt-template.md)：用户或总控派发技术顾问、执行和测试任务时使用的可验收任务卡。

P4 头脑风暴仍是可修改的讨论稿，不代表候选框架或部署服务已经接入。P0～P3 的实现、测试证据和教材按各自状态文件记录。真实账单、个人活动资料和密钥将作为运行数据管理，不提交到代码仓库。
# Maris
