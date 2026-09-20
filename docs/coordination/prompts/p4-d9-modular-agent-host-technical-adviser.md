# P4-D9：可扩展个人 AI 应用 Host 最小技术方案评审

## 角色与任务

- 角色：用户侧边栏中既有的“技术顾问”任务
- 任务编号：`P4-D9`
- 固定输入提交：`1d06d92c93d99fb2a3a23da6ff0958932e358814`
- 唯一目标：基于当前实际代码，为 P4-A～P4-D 给出可实施、可教学、不过度抽象的最小 Agent Host 技术方案
- 交付状态：只能到 `review`；由头脑风暴总控结合后续测试矩阵冻结接口

开始前必须按顺序读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. `docs/coordination/control.md`
6. `docs/coordination/agents/technical-adviser.md`
7. 本任务卡
8. `docs/project-plan.md`
9. `docs/phase-4-desktop-cockpit-brainstorm.md`
10. `docs/phase-4-modular-agent-host-architecture.md`
11. `docs/phase-2-interface-freeze.md`
12. `docs/phase-2-d5-finance-agent-advice.md`
13. `docs/phase-2-d6-agent-teaching.md`
14. `docs/phase-3-interface-freeze.md`

然后只读检查固定提交中的实际代码和测试，至少包括：

- `src/wife_system/agent/loop.py`
- `src/wife_system/agent/application.py`
- `src/wife_system/agent/context.py`
- `src/wife_system/agent/models.py`
- `src/wife_system/agent/prompts.py`
- `src/wife_system/agent/providers.py`
- `src/wife_system/agent/finance_tools.py`
- `src/wife_system/tools.py`
- `src/wife_system/api/app.py`
- `src/wife_system/api/agent_routes.py`
- `src/wife_system/finance/models.py`
- `src/wife_system/finance/service.py`
- `src/wife_system/activity_import/**`
- `tests/agent_finance/**`
- `tests/finance/**`
- `tests/activity_import/**`

旧文档与实际代码冲突时，以固定提交代码、已冻结接口和最终验收报告为准。不得把概念草案描述成已经实现。

## 背景和必须保持的产品决定

1. 项目定位是可扩展的 Personal AI Host，财务生活和财富管理是首批内置模块。
2. Agent 负责理解、路由、规划、工具选择和解释。
3. Workflow 负责候选、确认、暂停恢复、重试与补偿。
4. 金额、余额、预算、收益、事务、幂等和领域不变量由确定性程序负责。
5. 模块可以拥有不同 Agent Profile、系统提示词、工具白名单、专属记忆和 UI。
6. 共享确认记忆、模块专属记忆、会话和事实数据库必须分层。
7. 投资是财富管理的子模块；财富管理还包括应急资金、储蓄、现金管理、风险保障、资产配置和长期目标。
8. 毛毛只有一个，主要形态为“日常管钱”和“财富管理”；它是 Host 入口，不是独立事实来源。
9. Windows 桌面端采用 Electron + React + TypeScript 候选路线；手机继续使用微信，不开发 Android 应用。
10. P4 必须用第二个模块证明扩展性，不能只写“以后可扩展”。

## 技术原则

- 优先演进现有 `AgentRunner + ToolRegistry + AgentApplicationService + FinanceService`，不得默认推倒重写。
- 先理解并保留 P0～P3 已验收的权限、确认、幂等、事务、错误和审计边界。
- 可以比较 LangGraph、MCP/FastMCP、依赖注入库或插件框架，但只有实际问题证明需要时才推荐引入。
- 首版是可信内置模块的模块化单体，不做第三方插件市场、任意代码加载或每 Agent 一个微服务。
- 系统提示词不同不自动等于独立进程或独立模型；必须区分逻辑 Agent、运行时实例、会话和模型提供方。
- 多 Agent 协作不能靠自由对话替代明确的工具、状态、权限和停止条件。
- 所有设计必须说明对用户学习 AI Agent 工程的价值，以及新增复杂度。

## 必须比较并作出推荐的技术问题

每项至少给出推荐方案、一个有意义的替代方案、采用理由、代价、何时重新评估。

### 1. 模块注册

- Python 显式注册、声明式配置、Python + 配置混合三种方案；
- `ModuleDefinition`/manifest 的最小字段；
- 模块发现、启停、版本兼容和重复 ID；
- 为什么 P4 不需要运行时安装未知插件。

### 2. Agent Profile 与路由

- 基础安全提示词、模块提示词和动态上下文如何组合；
- `AgentProfile` 的类型、版本、工具权限、记忆范围、成本和停止条件；
- 桌面模块确定性路由与微信意图路由的区别；
- 跨模块问题怎样处理，何时由 Host 编排，何时询问用户；
- 会话是否按 Agent/模块隔离，切换模块后怎样恢复。

### 3. Tool Registry 与 MCP 边界

- 怎样从当前单一 `finance_registry()` 演进为按 Profile 组合的工具集合；
- 权限在 schema 可见性和执行时各检查一次的边界；
- 本地领域工具、外部 HTTP 工具、MCP Server 的统一结果与错误契约；
- 哪些现有工具继续进程内，哪些未来适合 MCP；
- 工具名称冲突、版本、超时、取消、审计和脱敏。

### 4. Workflow 和运行状态

- 当前 `pending_action`、24 小时到期、确认和恢复怎样抽成可复用能力；
- 通用 workflow 状态与财务领域状态怎样分离；
- 是否真的需要 LangGraph，若暂不需要，明确什么信号出现后再引入；
- 进程重启、重复消息、响应丢失和并发确认的处理边界。

### 5. 登录、用户和渠道身份

- 主人账户、密码哈希、设备会话、退出和撤销的最小模型；
- 微信一次性绑定码、外部身份冲突、解绑和重新绑定；
- 怎样向现有财务表、Agent run、幂等键加入可信 `user_id`，避免破坏历史规则；
- 本地单用户阶段与未来服务端多端使用的迁移路径；
- API Key/模型凭据保存位置和禁止进入的上下文。

### 6. 分层记忆与会话

- 共享确认记忆、模块记忆候选、会话、消息和事实数据的最小关系模型；
- 建议字段、索引、生命周期、来源、确认、敏感级别、失效和删除语义；
- 专属记忆晋升共享记忆的确认流程；
- 运行时如何检索少量相关记忆，不把全部账本/对话塞给模型；
- P4 是否需要向量数据库，以及暂缓的判断依据。

### 7. FastAPI 与桌面会话 API

- P4 所需最小 API：登录、会话、模块清单、Agent 对话、确认、记忆、设置和健康状态；
- HTTP、SSE、WebSocket 的选择，首版是否需要 token 流式输出；
- 统一错误、请求 ID、取消、重试、后端离线和幂等；
- Electron 开发期如何启动/停止本地 FastAPI，正式部署如何解耦。

### 8. Electron、React 与模块 UI

- Electron main/preload/renderer 的职责和安全设置；
- React 模块注册、路由、导航、设置页和 Agent 面板的最小 TypeScript 契约；
- Shell 如何接入第二模块而不增加核心业务分支；
- API 类型生成或共享 DTO 的选择；
- 主窗口、托盘和更新机制的范围边界。

### 9. 毛毛与主题

- 毛毛透明独立窗口、托盘、置顶、拖动、位置持久化和主窗口关闭后的生命周期；
- 当前模块、Agent、毛毛主形态和子状态怎样分离；
- “日常管钱/财富管理”两种形态怎样通过注册映射，而不是写死到 Host；
- 主题 token、浅色/深色/跟随系统、减少动画和行情涨跌颜色习惯；
- 后台资源、全屏隐藏、隐私模式和无障碍边界。

### 10. 事件、设置、迁移和第二模块证明

- 进程内事件总线是否足够，事件 envelope 的版本、用户、幂等和隐私字段；
- 账户同步、设备本地和运行时设置怎样分层；
- 模块 migration 与主 Alembic 链怎样管理；
- `daily_finance` 和最小 `wealth_management` 如何作为两个内置模块接入；
- 哪些检查能证明第二模块无需修改 Host 核心路由、工具授权和记忆隔离逻辑。

## 必须提交的具体设计

交付文档不得只给概念描述，必须包含：

1. 当前代码结构与可复用能力清单，引用准确文件和关键代码位置。
2. 推荐架构图与至少三条实际数据流：桌面记账、微信路由、财富管理只读分析。
3. 最小 Python 类型草案：`ModuleDefinition`、`AgentProfile`、工具绑定、记忆权限、事件 envelope；可以是说明性伪代码，不写入产品。
4. 最小 TypeScript 类型草案：模块导航、页面注册、Agent 面板、设置贡献和毛毛状态映射。
5. 最小数据模型：账户/设备/渠道绑定、会话/消息、记忆、模块设置；标明哪些进入 P4-A，哪些延后。
6. P4-A、P4-B、P4-C、P4-D 的实施顺序、依赖、文件边界和每阶段可验收结果。
7. 从当前代码演进的逐步迁移方案，避免大爆炸重构；列出保持不变的 P0～P3 接口和测试。
8. 测试建议：单元、契约、权限、记忆隔离、API、Electron、并发、迁移和第二模块扩展性。
9. 风险表：安全、隐私、复杂度、模型成本、供应商、桌面后台、微信身份和未来部署。
10. 用户学习地图：每个 P4 切片对应要理解的 Agent/Host、HTTP、认证、React/Electron、MCP 和测试知识。
11. 提供一份供总控冻结的编号决策清单，明确推荐默认值和仍需用户决定的产品问题。

## 允许的外部资料

可以只读查询官方或一手资料，用于核对当前版本的：

- FastAPI 安全、依赖注入和流式响应；
- Electron 安全、BrowserWindow、Tray 和进程模型；
- React/TypeScript 模块与路由相关官方文档；
- MCP 官方协议/SDK；
- SQLAlchemy/Alembic/PostgreSQL；
- DeepSeek 工具调用。

外部资料必须提供链接并区分“官方保证”“方案推断”和“项目决定”。不得登录外部账户、安装依赖、启动服务或调用付费 API。网络不可用时先完成代码分析，把未核实版本项列为 `unverified`，不要无限重试。

## 文件与权限边界

允许修改：

- `docs/phase-4-d9-modular-agent-host-advice.md`
- `docs/coordination/agents/technical-adviser.md`

其他全部只读。特别禁止：

- 修改任何 `src/**`、migration、依赖、配置和测试；
- 修改接口冻结、项目计划、P4 头脑风暴、控制文件、总览和其他角色日志；
- 启动 FastAPI、Docker、DeepSeek、OpenClaw、微信或 Electron；
- 读取或记录密钥、Token、二维码、账号标识或真实财务数据；
- 执行 Git 写操作；只能只读查看状态、差异、历史和摘要；
- 自动继续 P4 实现、测试矩阵或接口冻结。

所有示例使用虚拟数据。可以只读运行现有本地测试用于理解，但不得把技术顾问复跑写成独立验收。

## 交付与验收

交付：

- `docs/phase-4-d9-modular-agent-host-advice.md`
- 更新 `docs/coordination/agents/technical-adviser.md`
- 最终回复给总控一份：推荐方案、关键替代方案、冻结清单、未验证项和准确文件链接

验收标准：

1. 十组技术问题全部有明确推荐、替代方案和重新评估条件。
2. 每项核心结论能追溯到实际代码、已冻结接口或引用的一手资料。
3. 方案解释 Agent、workflow、领域程序、模块、MCP 和 Host 的清晰边界。
4. 账户、记忆、工具和模块隔离包含具体类型/数据模型和权限流程。
5. P4-D 给出可执行的第二模块扩展性证明，不只写目录建议。
6. 迁移方案不要求重写 P0～P3，不把未实现能力写成完成。
7. 未修改禁止范围，不存在凭据或个人数据。
8. 最终状态为 `review`，等待总控结合测试建议冻结接口。

## 进度和停止规则

- 接单后立即在技术顾问角色文件记录固定提交、当前步骤、下一检查点和文件边界。
- 至少在“代码现实盘点”“后端 Host 决策”“身份/记忆设计”“Electron/UI 设计”“完整交付”五个里程碑更新进度。
- 预计超过五分钟的检查先记录下一检查点；每十分钟或每个实质输出刷新心跳。
- 连续两个检查点没有有效进展时安全停止，报告具体卡点、最后脱敏错误、已尝试方法、可能原因和需要共同决定的问题。
- 发现 `docs/coordination/control.md` 更新或与本任务冲突时，以控制文件为准，停止旧动作并报告。
