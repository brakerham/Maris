# 总控同步指令

这是所有角色和独立 Codex 任务的当前控制面。时间较早的任务说明、聊天记录或本地假设与本文冲突时，以本文和用户最新决定为准。本文只由头脑风暴总控维护。

- 指令版本：`2026-10-17T09:03:00+08:00`
- 当前阶段：P4-A Host、身份和通用状态地基已经完成。`P4-C11-R2` 已在真实 PostgreSQL 上关闭 `P4-C11-R1-PG-001`，`P4A-DB-05` 与 `P4A-DB-06` 已通过，P4-A 矩阵为 64 passed、0 failed、0 blocked、0 not_run。
- 当前动作：P0～P3与P4-A已独立验收，QUIT-001普通关闭范围已关闭。R9-R1停于目标前脚本路径身份比较，产品/辅助新增均0，未形成产品缺陷；发布P4-C12-R9-R2，修完整参数/路径身份链后沿未耗额度续验H1及剩余Windows。旧8独立/48兼容/W1和模块/冷入口/恢复通过保持。P4-B仍1 passed、1 failed、19 blocked、3 not_run；P4-C/D未开始，执行方和顾问停止。
- 需要用户参与：将 `docs/coordination/prompts/p4-c12-r9-r2-path-windows-tester.md` 交给既有测试智能体；新任务ready/waiting_user，实际接单unverified。R9-R1已blocked/finished，不自行续旧任务。无需此刻操作产品窗口或系统。
- Git 状态：新仓库 `https://github.com/brakerham/Maris.git` 是当前正式 `origin`；远端 `main` 当前为 `251b4a2`，其后的 E5 协调与返修单元只在本地提交，尚未推送。现有远端与本地提交仍是发布前保护性检查点，不是首个正式大版本，也不启动 PR-only 流程。旧 `DM001-mm/wife-system` 只保留为 `old-origin`，后续默认不推送。
- 前端实现提醒门禁：P4-B Shell 完成独立验收后、创建首个 P4-C 财务驾驶舱技术方案或执行 Prompt 之前，总控必须主动提醒用户进入真实前端界面阶段，并先复核两张既定参考图、高保真信息架构、页面/组件切片、视觉验收方式和模型分工。不得直接沿用 Shell 占位页开始编码；必须让用户先确认当时可用模型及分工策略。当前建议重新评估“强推理/视觉模型（现为 GPT-6 Astra）负责界面方案、复杂交互和关键审阅，编码工作模型（现为 GPT-6 Sol）负责组件实现、重构和常规测试”，模型能力或额度变化时以届时讨论为准。

## DYN-R2 运行中协调变更

- 执行智能体已于 2026-09-29 02:26 在旧控制版本下完成原始 250 项起点门禁，原清单 SHA-256 为 `565f91ccca3557c2aa1f955760d31a71c866c45ce6b0604c2de6378c1a5021b8`，随后进入只读复算；不得因此重启任务或重复动态预算。
- 用户随后新增“进入真实前端开发前必须提醒并重审模型分工”的未来阶段协调规则。总控只修改 `docs/coordination/control.md`、`docs/project-coordination.md`、`docs/phase-4-b-windows-shell-brainstorm.md`、`docs/coordination/agents/brainstorm.md` 并刷新 DYN-R2 snapshot；没有修改产品、测试、依赖、lock、package、DYN-R1/PKG-R2 evidence 或外部运行现场。
- 以上五项属于总控授权的并发协调变化，执行智能体在下一检查点读取本版本后可继续当前 DYN-R2，不把它们归类为产品输入漂移、越界修改或重跑理由。执行智能体自身仍只可修改原任务卡列出的三项交付路径，P1/P2 的单次预算和停止规则不变。

## 本地单主人产品范围

- 用户于 2026-09-26 决定近期采用单机、单主人、本地数据库；其他人使用时各自在自己的设备安装实例，不登录用户的主机。
- P4-A 本来就没有公众注册或管理员创建第二用户；现有实现是一次性 bootstrap owner、登录/session 和渠道绑定的本地后端安全基础。
- 公众注册、第二用户、多租户服务器、云账户、跨主机登录、找回密码以及注册/常规登录 UI 全部暂停，不得由任何角色继续扩展。
- `user_id`、Principal、复合 user scope、singleton owner、session 安全和微信身份绑定继续保留；它们用于保护本地数据与可信入口，不代表产品提供多用户服务。
- S1、S2 和 C11 不删除或重写 auth；C11 只验证已有本地安全边界，不增加多用户产品需求。桌面 Shell 开始前再裁定自动本地 owner 会话、可选应用锁或显式登录。
- 完整决定见 [P4 本地单主人范围决定](../phase-4-local-owner-scope-decision.md)。

## OpenClaw 运行状态与安全事件记录

- 2026-09-16，终端安全软件以 `PDM:Trojan.Win32.Generic` 行为规则删除 OpenClaw 2026.8.2 的 `openclaw-database-verify.worker.js`；本机安装目录中的目标文件已不存在。
- 总控从 npm registry 重新取得官方 2026.8.2 发布包并核对完整性：压缩包 SHA-1 与 registry 公布值一致，包内同名文件 MD5 与告警对象完全一致；registry 同时列出发布签名与 SLSA provenance。
- 代码只执行只读 SQLite 完整性检查、子进程 IPC 和清理；当前证据更符合行为启发式误报，但在安全软件厂商确认或完成处置前仍按安全事件管理。
- 2026-09-25 用户确认本机 OpenClaw 已恢复，微信当前可以连接；该用户确认 supersede 早期“运行时暂停”状态。本轮 P4-B6 审计不启动、停止、重装或修改 OpenClaw，也不重复扫码或真实消息测试。
- 任何角色仍不得自行下载替换被安全软件删除的文件、关闭安全软件或添加排除项。后续若修改 OpenClaw 安装、安全配置或微信登录状态，仍需新的明确任务与唯一外部操作负责人。

## Git 权限与发布控制

- Git 写权限只属于头脑风暴总控。执行智能体、测试智能体、技术顾问及所有子智能体不得执行暂存、提交、还原、重置、切换/创建分支、合并、变基、标签、推送或 PR 操作。
- 其他角色只交付工作区修改、验证证据和文件摘要；可以只读查看 Git 状态、差异和历史。
- 每个任务或里程碑通过所需独立验证并由总控验收为 `complete` 时，总控创建对应的本地提交。
- 用户明确宣布首个大版本发布前，验收单元默认只在本地提交；只有用户明确要求保护性远端检查点时才推送。
- 保护性远端检查点不等于大版本发布，不触发 PR-only 流程。当前 P0～P3 基座推送与文档 PR #1 都按保护性检查点处理。
- 用户明确宣布正式大版本时，由总控发布已验收的本地历史；只有该版本以后所有变更才必须经独立分支和 GitHub PR，由总控负责 Git 写操作与验收后合并。
- 未完成的 `review` 工作不得伪装为验收提交；历史积压或缺陷现场只能建立描述准确的本地检查点。
- `checkpoint/p3-foundation` 固定指向已验收提交 `6e89762`。它只用于比较、复现和在保留后续工作的前提下建立恢复分支；任何角色不得据此自行执行 `reset`、`restore`、切换分支或删除当前工作。

## 开发与测试边界（所有后续任务强制适用）

- 执行智能体负责业务代码、调试、执行方单元/组件测试和最小冒烟测试。自测是开发交付的一部分，不属于越权。
- 执行智能体不得修改测试方专属目录、独立验收矩阵或独立报告；自测通过只能把任务提交为 `review`，不能宣布独立验收或项目 `complete`。
- 测试智能体负责实现前的独立矩阵，以及实现后的边界、并发、故障、回归和契约验收。可以复跑执行方测试，但必须与独立案例分开统计。
- 测试智能体未经总控明确划定返修范围不得修改产品代码；发现缺陷先提交最小复现、预期、实际、严重级别和影响范围。
- 技术顾问可以只读代码、复跑测试并用于教学，但不得替执行方实现、替测试方下独立结论或修改双方专属交付物。
- 头脑风暴总控冻结接口和验收标准、派发返修、核对双方证据并作最终项目验收，不替代执行或独立测试。
- 每份新任务 Prompt 必须明确：允许写哪些测试、禁止修改哪些测试、交付状态只能到哪一步、谁有权作最终结论。
- 执行方自测、测试方独立验收、总控证据核对采用单向流水线。快照未变化且报告一致时，总控不再重复全量测试或完整代码审查；仅对摘要冲突、严重失败或结论矛盾做定向复现。

## 当前唯一负责人

| 任务 | 唯一执行负责人 | 其他角色允许动作 | 禁止重复动作 |
| --- | --- | --- | --- |
| W1 微信账号接入与真实消息操作 | 头脑风暴总控 | 测试智能体只读核验证据并写测试报告；用户按总控给出的单一步骤操作 | 执行智能体不得安装插件、生成二维码、扫码登录、重启网关或要求用户重复测试 |
| W1 Python 服务故障测试 | 头脑风暴总控 | 测试智能体记录结果 | 其他角色不得自行启动或停止 Python 服务 |
| W1 自然语言工具调用 | 已完成；头脑风暴总控 | 测试智能体已完成只读验收 | 不重复发送或重新扫码；后续案例另行分配 |
| P1-D3 数据层技术建议 | 已完成；总控验收 | 各角色只读使用 | 任何角色不得把建议文件改成实现状态 |
| P1-C3 数据层测试矩阵 | 已完成；总控验收 | 测试智能体在 C4 实现独立案例，不回写假通过 | 执行角色不得修改 C3 或独立测试路径 |
| P1-IF-001 接口冻结 | 已完成；头脑风暴总控 | 各角色只读执行 | 架构或范围变更必须退回总控与技术顾问 |
| P1-B3-R1 数据层返修 | 用户启动的侧边栏独立“执行智能体”任务；已于 2026-09-16 21:22 提交 `review` | 测试智能体按新快照复验；技术顾问可只读分析 | 执行智能体停止；没有新的总控返修任务不得继续修改实现 |
| P1-C4-R2 数据层定向复验 | 已完成；三个返修缺陷由测试智能体独立复验通过 | 后续 8 个 PostgreSQL 项已由 DATA-R2 通过 | 不重复 R2 或已完成的 PostgreSQL 专项 |
| P2-D5 财务 Agent 工具技术设计 | 已完成；总控已验收并形成 P2-IF-001 | 各角色只读使用 | 不回写为实现状态；接口变化交回总控与技术顾问 |
| P2-IF-001 接口冻结 | 已完成；头脑风暴总控 | 各角色只读执行 | 范围变更交回总控与技术顾问 |
| P2-B4 Agent 财务工具实现 | 本地范围已完成；C6 未发现 P2 产品缺陷 | PostgreSQL 专项只读验证现有实现；技术顾问已完成 D6 | B4 产品实现停止；当前仅按 P2-TIME-R1 维护执行方测试 |
| P2-C5 Agent 财务测试矩阵 | 已完成；测试智能体交付 84 项设计并停止 | C6 直接复用矩阵，不重新设计 | 不把“设计完成/未执行”误报为验收通过 |
| P2-C6 Agent 财务独立执行 | 本地范围已完成；45 项独立和 23 项执行方 P2 测试通过 | 13 个外部环境案例后续分项验证 | 不重复 C6 本地全量回归；两项 Phase-0 回环等待失败单独作为测试基础设施问题 |
| P2-D6 Agent 实现教学 | 已完成；总控于 2026-09-17 验收 | 各角色只读使用教学文档 | 不回写为产品实现或独立测试结论 |
| PG-C7 PostgreSQL 专项 | `complete`；原失败已由 DATA-R1/R2 修复和复验 | 报告只读保留原始失败基线 | 不重复原 C7 |
| PG-C7-DATA-R1 产品返修 | `complete`；`RETURNING` 修复及两文件快照已验收 | 各角色只读使用 | 后续变化必须另立任务 |
| PG-C7-DATA-R2 定向独立复验 | `complete`；P1 8/8、P2 SPG 4/4、SQLite 9/9 通过 | 测试容器和网络已普通 down | 不重复 R2；`PG-C7-DATA-001` 已关闭 |
| P2-TIME-R1 测试时钟维护 | `complete`；执行方 28/28 通过并停止 | 七文件摘要由执行、测试和总控三方匹配 | 不重复任务；后续测试时钟变化另立任务 |
| P2-TIME-C2 测试时钟独立复验 | `complete`；28/28、原 23/23、还原审计 28/28 通过 | 报告只读保留测试角色原始 `review` 结论 | 不重复 C2、C6/C7 或外部联调 |
| P3-D7 活动 Markdown 导入方案 | `complete`；总控已接受 | 各角色只读使用 | 不回写为实现或测试结论 |
| P3-C8 活动 Markdown 导入测试矩阵 | `complete`；89 项设计已用于 C9/R2 | 最终矩阵由 C9-R2 收口为 89/89 passed | 不把最初设计状态与最终执行证据混淆 |
| P3-IF-001 接口冻结 | `complete`；头脑风暴总控 | 各角色按冻结契约执行 | 变更必须退回总控与技术顾问 |
| P3-B5 活动 Markdown 导入实现 | `complete`（经 B5-R1/C9-R2 闭环） | 各角色只读使用最终实现与交接 | 后续变化另立任务，不继续扩展原 B5 |
| P3-C9 活动 Markdown 导入独立验收 | `complete`（经 R2） | 原 C9 报告保留首次缺陷证据 | 不重复原失败验收 |
| P3-B5-R1 PostgreSQL 外键名返修 | `complete` | 46 字符外键名和 22 文件快照已验收 | 执行智能体停止；后续变化另立任务 |
| P3-C9-R2 PostgreSQL 定向复验 | `complete`；89/89 passed | R2 报告、矩阵和独立测试只读保留 | 不重复 R2 或修改最终验收证据 |
| P3-C9-R2 PostgreSQL 环境 | `complete`；容器与项目网络已普通关闭 | 无当前外部操作负责人 | 禁止无新任务启动服务、删除 volume、prune 或改全局配置 |
| P0-P3-D8 阶段实现后教材 | `complete`；总控已接受四册交付 | 四册 Markdown、四份 PDF、统一生成/验证脚本；44 页视觉 QA 与 96 个本地链接通过 | 教材只读保留；后续授课不回写为产品或测试结论 |
| P4-HOST-BRAINSTORM 可扩展 Agent Host 规划 | `complete`；用户已接受方向 | 产品定位、模块契约、Agent Profile、工具/MCP、分层记忆、账户、毛毛与主题 | 规划已进入保护性远端检查点；后续以 D9 技术评审继续 |
| P4-D9 Agent Host 最小技术方案评审 | `complete`；总控已接受 | D9 的 F01～F17 作为 C10 和正式冻结输入；7 个产品项采用可逆默认值 | 技术顾问停止；不得把建议文档改写成已实现能力 |
| P4-C10 模块化 Agent Host 测试矩阵 | `complete`；总控已接受 | 120 个唯一案例、12 字段完整、全部 `not_run`；作为 P4 验收口径 | 测试智能体停止；不得提前执行未形成快照的案例 |
| P4-IF-001 模块化 Agent Host 接口冻结 | `complete`；头脑风暴总控 | 冻结总架构和 P4-A 的身份、user scope、workflow、记忆、API 与迁移合同 | 变更必须交回总控与技术顾问，不得由执行方自行修改 |
| P4-B6 Host/身份地基实现 | `complete`（经 R1、R2、R3 与 C11-R2 闭环） | P4-A 64/64 独立矩阵通过；134 文件最终快照由总控固定 | 原 B6 及全部返修任务停止；后续变化另立任务 |
| P4-B6 多交接接管审计 | 头脑风暴总控；`complete` | [审计报告](../p4-b6-multi-handoff-code-audit.md)登记 8 个 P0、14 个 P1、PG 证据和任务顺序 | 不重复本轮三路审查；新代码快照形成后才重新审查相应差异 |
| P4-A PostgreSQL 复验环境 | `complete`；当前无活动环境负责人 | C11-R2 只启动 `finance-postgres`，普通 down 后最终 Compose 为空 | 当前不再操作 Docker/PostgreSQL；下一任务另行指定唯一负责人 |
| P4-D10 B6 返修架构裁定 | `complete`；总控已接受 | 762 行、8 P0/14 P1 逐项处置、R1/R2 边界、12 类 PG 场景与 C11 门禁已核对 | 技术顾问停止；不得修改产品或自行派发后续任务 |
| P4-D11 Windows Shell、毛毛与模块 UI 技术方案 | `complete`；总控已接受 | 1093 行方案、24 项矩阵映射、19 个本地链接和两文件摘要匹配；总控登记 TS 版本与 pnpm/Forge 两项勘误 | 技术顾问停止；不创建 D11-R1，不把设计证据写成桌面功能已实现 |
| P4-IF-003 Windows Shell 接口冻结 | `complete`；头脑风暴总控 | 冻结精确工具链、三层边界、模块 UI、OpenAPI、owner 会话、nonce/readiness、Supervisor、outbox、Tray、毛毛、主题和测试口径 | 变更必须退回总控与技术顾问；执行方不得自行替换 Electron、工具链或扩大到 P4-C/P4-D |
| P4-B7 Windows Shell 实现 | 执行智能体；`blocked / finished` | 66 文件 source manifest 匹配；类型、测试、package、asar E2E 与 EXE smoke 有执行方证据；audit 发现 1 critical、11 high，main 真实 Host 组合未完成 | 执行智能体停止；不得忽略 advisory、自行改变冻结依赖图、继续接线或启动 P4-C12 |
| P4-D12 B7 供应链与真实接线裁定 | `complete`；总控已接受 | 728 行方案、16 项 advisory、三候选隔离解析、F01～F22、Host 组合与教学地图已核对 | 技术顾问停止；不得继续改方案、依赖或产品 |
| P4-IF-004 供应链与真实 Host 补充冻结 | `complete`；头脑风暴总控 | Forge 8 alpha 仅发布前验证；desktop core readiness、composition root、Supervisor、owner/token 和完整门禁已冻结 | 变更必须退回总控；执行方不得自由试版本、改通用 `/readyz` 或扩大业务 |
| P4-B7-R1 供应链与真实 Host 组合续段 | 执行智能体；`blocked / finished` | Forge 8 精确候选图与旧包消失通过；候选 lock full/prod audit 均为 0；Electron 官方资产连续两个检查点 fetch failed，Host 组合未开始 | 原任务停止；不得把 8/9 Vitest files 冒充全绿、引用候选审计代表最终 lock 或启动 C12 |
| P4-B7-R1-E1 Electron 链路恢复续段 | 执行智能体；`blocked / finished` | 最终 lock 双审计、F04 和 clean frozen install 通过；Node 24 正文/redirect 以 `ECONNRESET` 阻塞，后续未执行 | 原任务停止；不得再次发送 E1、换镜像、复用旧 binary、修改安全软件或启动 C12 |
| P4-B7 Electron 官方资产网络门禁 | 头脑风暴总控；`complete` | TUN 的 `Meta Tunnel` 默认路由 metric 0；沙箱外官方 Range GET 返回 HTTP 206、1,048,576 字节、TLS 校验 0 | 门禁已经解除；保持当前 TUN 设置，证据见 E2 网络门禁文档 |
| P4-B7-R1-E2 Electron 下载恢复与真实 Host 组合 | 执行智能体；`blocked / finished` | 194 文件 source manifest 总控复算匹配；官方 Electron、Host/sidecar、22 Vitest、55 Python 和 package 已通过；app.asar launch 阻塞、真实 EXE 未运行，resources 含 11 `.pyc` 与 6 `.egg-info` | 原任务停止；不得继续用 Playwright Electron launcher 启动 fused EXE或重复盲试 |
| P4-B7-R1-E2-R1 启动分层与 package hygiene | 执行智能体；`blocked / finished` | 200/200 起点和 194/194 source 匹配；最小无业务 fixture 的 debugger/CDP 已连接，GPU child 随后以 `0xC0000135` 退出，browser 弹出 `0x80000003`；产品零变化且资源已收口 | 原任务停止；不得再次运行相同 D 盘 fixture、app.asar 或 EXE |
| P4-D13 Windows 25H2 Electron crash 裁定 | `complete`；总控已接受 | 442 行方案、26 条冻结建议、A1/A2/F1 分支、诊断开关与 hygiene 拆分已核对 | 技术顾问停止；不得继续运行动态诊断或自行创建后续任务 |
| P4-IF-005 Electron Windows 诊断与 package resource 冻结 | `complete`；头脑风暴总控 | 冻结首故障措辞、C 盘三角验证、安全开关、版本边界、H1 staging 与后续顺序 | 变更必须返回总控与技术顾问；执行方不得自由遍历开关或版本 |
| P4-B7-R1-H1 Python package resource 静态 staging | `review / finished`；总控接受为 E3 输入 | H1-R1 已关闭 `P4-H1-ATOMIC-001`；198/198 source 匹配，执行方专属 14 项、相邻合计 16 项通过 | H1/H1-R1 停止；不得继续改 allowlist/Forge 合同或把静态结果写成 P4-B complete |
| P4-B7-R1-H1-R1 staging 原子替换返修 | `review / finished`；总控已核对 | 209 项起点只有 6 个授权变化；明确 commit point 与六类故障边界全部匹配报告 | 不重复 H1-R1；结果只作为 E3 输入，独立结论仍等待 P4-C12 |
| P4-B7-R1-E3 C 盘 Electron 最小三角验证 | 执行智能体；`review / finished`，总控已接受 | A1 direct 与 A2 默认 Playwright 各一次通过；198/198 source 与 39/39 外部证据匹配；只支持执行位置类差异 | E3 停止；不得重跑 A1/A2、D 基线、Procmon、诊断开关或版本遍历 |
| P4-B7-R1-E4 package、app.asar 与最终 EXE 恢复门禁 | 执行智能体；`blocked / finished` | 阶段 A 全过；唯一 package 在 Forge 裸 `pnpm` 命中失效用户 shim 后退出；P1/P2 未运行，资源已收口 | E4 停止；不得直接重跑 package、修改系统 pnpm或把未运行门禁写成通过 |
| P4-B7-R1-E4-R1 pnpm 路径恢复与最终门禁续跑 | 执行智能体；`blocked / finished` | R0 driver 的 `$Args` 自动变量冲突吞掉全部实参；package 0/1、P1/P2 not_run，现场与环境不变 | 原执行停止；不得修 driver 后重跑或自动创建 package 续段 |
| P4-D14 R0 driver 恢复技术裁定 | `complete`；总控已接受 | 677 行方案、21 项冻结内容；接受 ProcessStartInfo/ArgumentList、受限 cmd adapter、Job Object、fresh evidence 与参数计数勘误 | 技术顾问停止；不得运行 R0/package 或自行创建执行任务 |
| P4-B7-R1-E4-R0-R1 R0 driver 单独恢复与六项预检 | 执行智能体；`blocked / finished` | attempt-0 combined 捕获额外 `conhost.exe` 后以 `process_budget_exceeded` 停止；清理完成，Q1～Q6 全部 not_run | attempt-0 与 27 文件 evidence 只读保留；不得改预算、忽略 console host 或直接进入 Q/package |
| P4-B7-R1-E4-R0-R1-A1 标准流前置修正 | 执行智能体；`blocked / finished` | 三条标准流显式接管后仍记录 `conhost.exe` 并触发精确进程数门禁；Q1～Q6/package 均 not_run | 唯一修正预算已用完；禁止 attempt-2、synthetic 重跑或继续修改同一 driver |
| P4-B7-R1-E4-PKG-R1 直接预检结果 | 执行智能体；`blocked / finished` | Q1～Q6 原始真实结果均通过；核对代码错误读取 `inner-0` 后停止，package 0/1 | 禁止重跑预检或修改旧 evidence；总控以原始 inner 证据接受 Q6 |
| P4-B7-R1-E4-PKG-R2 package-only | 执行智能体；`review / finished`，总控已接受 | 唯一 package 退出 0；140 文件产物、fuses、67 项 Python resources、零污染与进程收口通过 | PKG-R2 停止；禁止重跑 Q1～Q6、package 或修改不可变产物 |
| P4-B7-R1-E4-DYN-R1 最终动态门禁 | 执行智能体；`blocked / finished` | P1 1/1 在产品 API 前由错误 root PID 假设停止；产品 unverified，P2 0/1 not_run；84/84 evidence 与最终资源收口通过 | DYN-R1 停止；旧 evidence/profile/PID 只读，不得补跑或复用 |
| P4-B7-R1-E4-DYN-R2 root promotion 恢复 | 执行智能体；`blocked / finished` | 79/79 evidence 匹配；存活 `cmd.exe` 包装进程导致 browser root 门禁按规则停止；产品 `unverified`，无 crash 证据 | DYN-R2 停止；不创建 DYN-R3，不再使用 Playwright Electron launcher 或重跑旧动态 cell |
| P4-B7-R1-E5-FINAL 最终 EXE 黑盒门禁 | 执行智能体；`blocked / finished` | EXE/Host/认证/双窗口/安全/自然退出通过；`modules.list()` 为空，首失败 `daily_finance_missing`；82/82 evidence 匹配 | 原任务停止；旧 package、profile、数据库、PID、端口与 evidence 只读，不得重跑 |
| P4-B7-R1-E5-R1 module Profile 合同返修 | 执行智能体；`blocked / finished` | 真实 Profile 与 fixture 已修正；旧 desktop parser 拒绝 canonical `@major`，package/EXE 0 次 | 保留交付和失败证据，不得重跑或扩大范围 |
| P4-B7-R1-E5-R2 canonical parser 返修 | 执行智能体；`blocked / finished`，parser 修复已接受 | canonical parser 与反例已修正；完整 package 前回归通过；package 1/1 因 Junction hoist 目录在构建前失败，最终 EXE 0/1 | 原任务停止；旧 E4/E5 依赖目录全部只读，不得恢复、链接、复制或执行 |
| P4-B7-R1-E5-PKG-FINAL 隔离依赖、package 与最终 EXE | 执行智能体；`blocked / finished`；依赖成果已接受 | 普通 node_modules、离线安装、dist、TypeScript/22 项通过；package 1/1 在 Vite build 后 fetch failed；EXE 0/1 | 原 evidence 只读；不得自行重跑，清洁依赖可作为 LOCALZIP 输入 |
| P4-B7-R1-E5-LOCALZIP 本地 ZIP 构建接线与最终门禁 | 执行智能体；`review / finished`，总控接受为 C12 输入 | package 1/1、EXE 1/1 成功；115 evidence、274 source、140 out 精确匹配 | 停止；不重复打包/启动；等待 C12 独立结论 |
| P4-C12 Windows Shell 独立验收 | 测试智能体；`blocked / finished` | 独立 10 passed、1 failed；P1 OUTBOX-001，P4-B 1 failed/19 blocked/4 not_run | 停止；首次 evidence 只读，待修复和新快照后派发复验 |
| P4-B7-R2-OUTBOX 消息保留与确认返修 | 旧执行结束；缺陷逻辑独立关闭 | C12-R1原PUB-11、其余10、outbox26/main5通过；旧失败证据保留 | 不重复修复outbox；SUP-06整体及设备提示仍待独立覆盖，不宣布P4-B complete |
| P4-C12-R1 outbox独立复验与剩余Windows验收 | 既有测试智能体；`blocked / finished` | 59 passed/1 failed；REGISTRY-001 P1，Windows/辅助Electron 0次；28交付匹配 | 保持停止；原节点/首次失败/报告只读，待新registry修复和新快照 |
| P4-B7-R3-REGISTRY 设置键全局冲突返修 | 设置键修复独立接受；旧执行finished | C12-R2原断言及14相邻/新增节点通过，REGISTRY-001关闭；UI-04整体仍failed | 不重复setting返修/旧打包；新path问题只由R4处理 |
| P4-C12-R2 注册缺陷复验与未执行Windows | 既有测试智能体；`blocked / finished` | 设置键缺陷独立关闭，新路径冲突P1；16唯一节点15passed/1failed，产品/辅助0次 | 原R2首次失败/通过只读，停止；UI-04仍failed，等新修复快照 |
| P4-B7-R4-ROUTE 路径冲突与UI-04开发核对 | 路径修复独立接受；旧执行finished | C12-R3原路径1/新边界9通过，PATH-001关闭；UI-04完整缺口仍blocked | 不重复path返修或旧package；新lazy问题由R5处理 |
| P4-C12-R3 路径复验与剩余Windows | 既有测试智能体；`blocked / finished` | 独立27 passed/1 failed，兼容52 passed；LAZY-001新P1，产品/辅助0次 | 原首次失败和已通过材料只读；停止，等修复快照 |
| P4-B7-R5-LAZY 模块故障局部隔离与恢复 | 既有执行智能体；`review / finished` | 390源码/7交付/60证据/140产物匹配；132开发回归、新包及19项EXE门禁记录通过；独立输入接受 | 停止产品修改；LAZY-001未关闭，不自行启动后续 |
| P4-C12-R4 lazy复验与Windows续跑 | 既有测试智能体；`blocked / finished` | 原节点一次0pass/1fail，未观测alert，故障命中未证实；首次记录保留，无新增产品缺陷 | 原任务停止；不重跑覆盖或宣布关闭 |
| P4-C12-R4-R1 故障观察与原R4续跑 | 既有测试智能体；`blocked / finished` | mock1命中、5秒无alert，异常终态未定位，未新定级缺陷；首次结果保留 | 停止；不得再延时重试/自行恢复Windows |
| P4-D15 异常传播有限诊断 | 既有技术顾问；`blocked / finished` | P1/P2各自拒绝/安全映射已证实，P3硬限且无持久阶段回执；31交付/429输入核对通过 | 原源码/首次结果保留，不重跑P1/P2/P3，不把无回执认定框架或产品根因 |
| P4-D15-R1 前置阶段取证 | `complete`；总控已按有限取证范围接受，顾问finished停止 | 同worker真实Router导出/main/act各自完成；40交付/CLI2/main1/修正1合规；旧超时根因未知 | 原首次材料/角色review保留，预热成功不算业务通过，不重复诊断或关闭LAZY-001 |
| P4-C12-R4-R2 冷入口传播复验与续跑 | 既有测试智能体；`blocked / finished`，总控已核对 | A一次main/34事件：取消加载拒绝、有效加载成功，当前errors=0；四断言1失败3通过，节点0passed/1failed；B及后续未运行 | 原材料只读；不重跑A/B、不新增产品缺陷或关闭LAZY；完整进程枚举未核实保持 |
| P4-C12-R4-R3 持续导入故障与冷入口续跑 | 既有测试智能体；`blocked / finished` | 52/52 交付、15/15 源码匹配；P 实际三次默认 loader 安全拒绝，A 初始化硬限且正文/main 为 0；B 及后续未运行 | 不重复 P 或旧 A/B，不把正文前超时称为产品缺陷；旧首次材料只读，完整系统后代枚举未核实保留 |
| P4-D16 测试初始化定位与独立验收路线裁定 | 有限技术裁定 `complete`；既有顾问原 `review / finished` 保留 | 39/39 交付、E1 10/10 与 E2 11/11 源码匹配；两次初始化实验exit0，产品请求0；旧A根因unknown，四登记PID退出/全系统枚举未核实 | 顾问停止；不重做E1/E2或使用第三次盲试，不创建D16-R1，不把技术接受写成LAZY/UI-02/P4-B通过 |
| P4-C12-R5-PUBLIC 无包装公开冷入口与剩余独立验收 | 既有测试智能体；`blocked / finished`，总控已核对 | 41/41交付、10/10源码、6/6首次记录匹配；B一次停在jsdom导入等待，main/fixture/四断言0，登记root/worker已结束、worker自身exit及完整历史后代未核实 | 旧源码/首次结果只读，不重跑覆盖、不认定产品失败；后续以R6-ENV为准 |
| P4-C12-R6-ENV 原生测试环境加载与公开验收续跑 | 既有测试智能体；`blocked / finished`，总控已核对 | 63交付匹配；B首次1 passed、四条公开要求/来源/安全/清理通过，恢复1 failed但具体assert/比较值缺失；后续not_run | B子条件接受，不重复；旧恢复原失败永久保留，不猜产品归因；全历史后代/worker exit限制保持，后续以R7为准 |
| P4-C12-R7-RECOVERY 恢复断言取证与剩余验收 | 既有测试智能体；`blocked / finished`，总控已核对 | 68交付匹配；恢复5组/208正式比较通过，结构8与兼容10分列；W1页面采样unknown，8登记进程/监听已强制收口 | 原源码/首次结果保留，测试方停止；worker exit1原因未核实；LAZY-001/UI-02/P4-B不关闭 |
| P4-B7-R6-MODULE-READY 模块就绪同步复现与最小修复 | 既有执行智能体；`review / finished`，接受为独立输入 | 5交付精确匹配，原同值通知时序已红绿验证；开发150、新包7静态、新EXE22门禁分列 | 已停止，不改后续产品；执行方通过不代替独立验收，旧W1现场原因不回填 |
| P4-C12-R8-MODULES 模块同步独立验收 | 既有测试智能体；`blocked / finished`，首次材料冻结 | 九节点通过，十节点工具重复ID中断，三节点未运行 | 旧源码/结果只读，不重跑旧整组，不作为产品失败 |
| P4-C12-R8-R1 工具更正及剩余验收 | 既有测试智能体；`blocked / finished` | 四节点/28兼容/6公开通过，Windows1/8正常退出P1；UI-01通过已接受 | 停止后续目标；不改产品/旧证据，不自行复验新包 |
| P4-B7-R7-QUIT 主窗口正常退出修复 | 总控接受普通关闭修复范围；执行方原review/finished保留 | R9独立8节点/235比较、48兼容及W1正常关闭约480ms通过，QUIT-001限定关闭 | 执行停止；不重打包或重跑EXE；其余原生条件仍待验 |
| P4-C12-R9-QUIT 退出独立复验与Windows续验 | 既有测试智能体；`blocked / finished` | W1 62/62通过；H1未release/解密即观察失败，底层unknown | 保留原首次材料，不重跑8/48/W1；由R9-R1续验 |
| P4-C12-R9-R1 H1观察工具与剩余Windows | 既有测试智能体；`blocked / finished` | 两次Node现场observer均exit3，第二次仅script谓词false，产品/辅助0次 | 原首次保留，不修旧工具或回填旧H1原因；新R9-R2续验 |
| P4-C12-R9-R2 脚本路径身份与Windows续验 | 既有测试智能体；`ready / waiting_user`，接单unverified | 真实argv边界、完整绝对路径及H1统一接线，纯工具开发有界后现场门禁 | 产品剩7/累计8，辅助剩4/累计5，不增额、不重跑旧通过；新路径内改工具，禁止产品及Git写 |
| P4-IF-002 返修补充冻结 | `complete`；头脑风暴总控 | 冻结一次性绑定、同事务 receipt、认证/错误、活动导入 principal、复合 FK、三 migration、R1/R2 顺序 | 变更必须退回总控与技术顾问；执行方不得自行选择替代语义 |
| P4-B6-R1 安全数据与兼容入口返修 | 既有执行智能体；`review`，已接受为 R2 输入 | R1/F1 22 文件安全切片摘要 `e690882a...7976` 可复算；最终独立结论仍由 C11 给出 | 原 R1/F1 执行已停止；不得继续修改 migration、独立测试或启动 C11 |
| P4-B6-R1-F1 外部身份并发绑定返修 | 既有执行智能体；`review`，开发返修接受 | 总控核对 4 changed/19 unchanged/0 missing、五文件摘要、本地 41 passed；执行方 PG 原 21+新增 1 通过 | 作为 R2 精确基线保留；F1 真实并发反例在 C11 再独立执行，不重复改实现 |
| P4-B6-R2 Host/Agent 运行时返修 | 既有执行智能体；`review / finished`，总控接受为 C11 输入 | S1 结构完成；T2 已证明 R1/R2 共 17 个唯一真实 PG 用例全部通过；最终 105 文件快照已冻结 | 执行智能体继续停止；最终独立结论由 C11 给出 |
| P4-B6-R2-S1 运行时结构补全 | 既有执行智能体；`review / finished`，总控接受为 S2 输入 | 10 个单文件摘要匹配；报告聚合摘要勘误为 `583cac21...6a10`；总控定向 44 passed | S1 不再修改；独立结论仍由 C11 给出 |
| P4-B6-R2-S2 真实 PostgreSQL 门禁 | 既有执行智能体；`review / finished` | S2 原 R2 9/9、Finance 4/4、activity import 10/10 通过；T2 已补齐 Host R1 8/8 与 R2 9/9 | S2/T1/T2 均停止；不得重复执行，独立数据库门禁由 C11 负责 |
| P4-B6-R2-S2-T1 R1 测试时钟返修 | 既有执行智能体；`review / finished` | 单文件 monkeypatch 已完成；104 项终点摘要为 `c7deef5a...529d`；T2 精确节点及后续 16 项证明时钟恢复 | T1 不再修改或运行；其修复随最终 105 文件快照进入 C11 |
| P4-B6-R2-S2-T2 有限 PostgreSQL 复验 | 既有执行智能体；`review / finished` | 17 个唯一 PG 用例全部通过；104/104 前后匹配；报告摘要 `59e07d0c...f54358c` | 执行智能体停止；不得重复 T2 或自行启动 C11 |
| P4-C11 P4-A 独立验收 | `complete`（经 R1、R2 收口） | P4-A 64/64 passed；8 P0/14 P1 接管项和真实 PostgreSQL 历史迁移均取得关闭证据 | 不重复完整 C11；后续变化另立独立验收 |
| P4-C11-R1 历史迁移证据补强 | `complete`；其发现的缺陷已关闭 | 原失败证据保留；`P4-C11-R1-PG-001` 已由 E1 修复并经 C11-R2 独立验证 | 不重复原失败任务 |
| P4-B6-R3 PostgreSQL 历史迁移返修 | 执行智能体；`blocked / finished` | 130/130 起点通过；执行方历史 fixture 已准备，migration 未修改；Docker Desktop 首次检查不可达后按规则停止 | 不重复旧 R3；保留 fixture 和环境阻塞报告，由 R3-R1 续跑 |
| P4-B6-R3-R1 PostgreSQL 历史迁移返修续跑 | 执行智能体；`blocked / finished` | 固定 131 文件摘要 `5aa1db6c...b9bb` 起终点一致；Docker Desktop 仍未运行，pytest 未启动，migration 零漂移 | 不再重复发送 Prompt；等待用户启动 Docker、总控验证并发布新的恢复指令 |
| P4-B6-R3-R1-E1 Engine 恢复后返修续段 | `complete`；执行智能体已停止 | 原 PG 失败唯一复现；migration 与执行 PG 测试两文件变化；30 passed、0 failed/skip；其结果已获 C11-R2 独立确认 | 不重复 E1 |
| P4-C11-R2 PostgreSQL 历史迁移定向复验 | `complete`；测试智能体已停止 | 独立 7 passed、执行兼容 19 passed；关闭 `P4-C11-R1-PG-001`，P4-A 最终 64/64 passed | 不重复 C11-R2；报告和矩阵只读保留 |

任何角色在开始工作前必须确认任务表中只有一个执行负责人。没有被列为执行负责人的角色不得“顺手继续”外部操作；发现空缺、冲突或旧指令时，只向总控报告并等待重新分配。

## 已完成且禁止重复

- 本地财务桥接 0.1.0 已安装并加载。
- 腾讯微信插件 2.4.8 已安装并加载。
- 微信扫码登录已完成，频道已配置并运行。
- `/finance-probe V001` 已从手机微信真实发送，Python 返回 200，手机实收字段与脱敏服务事件一致。
- Python 停服时 `/finance-probe V002` 已返回稳定的 `backend_unavailable`，没有生成请求编号或回执；故障路径通过。
- DeepSeek 新认证已完成最小在线验证，认证选择限定为用户新填的 manual 档案；自然语言工具调用与手机实收通过。
- 禁止再次启动扫码、刷新二维码、覆盖微信登录配置或重复安装上述插件，除非总控发布更新版本的明确指令。

## 对旧执行任务的停止指令

任何仍在要求用户扫码、安装微信插件或重复启动 W1 正常链路的执行任务，必须在安全检查点立即停止当前操作，不再重试。请保留已有产物并向总控报告：所依据的旧指令时间、当前步骤、最后输出、是否改动外部配置，以及等待的新任务。不要自行修改本文件。

## 同步通道

- 总控树内的子智能体：总控使用 Codex 协作消息实时同步，并以本文作为恢复依据。
- 侧边栏中的独立任务：协作接口无法保证互相可见，必须在每次开始工作以及任何外部操作前重新读取本文。
- 用户已明确：四个长期角色由用户在侧边栏独立启动。总控为阶段工作生成 Prompt 与控制指令，不替用户创建这些长期角色；总控只有在用户明确要求某个临时子任务时才创建子智能体。
- 角色进度仍写入各自状态文件；总控同步指令不替代完成证据与测试报告。

本文不记录密钥、二维码、微信账号标识、个人财务数据或原始私密日志。
