# P4-C10：模块化 Agent Host 独立验收矩阵

## 角色与任务

- 角色：用户侧边栏中既有的“测试智能体”任务
- 任务编号：`P4-C10`
- 固定产品基座：`1d06d92c93d99fb2a3a23da6ff0958932e358814`
- 固定技术建议：`docs/phase-4-d9-modular-agent-host-advice.md`，SHA-256 `765a3547b806724183a6302f4134a28b43e987d066fe30933bde5f993073fe5a`
- 唯一目标：在实现前形成 P4-A～P4-D 分层、可执行、可追踪的独立验收矩阵
- 交付状态：只能到 `review`；不得执行测试或宣布 P4 通过

开始前必须按顺序读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. `docs/coordination/control.md`
6. `docs/coordination/agents/tester.md`
7. 本任务卡
8. `docs/phase-4-modular-agent-host-architecture.md`
9. `docs/phase-4-d9-modular-agent-host-advice.md`
10. `docs/phase-2-interface-freeze.md`
11. `docs/phase-3-interface-freeze.md`
12. P0～P3 最终验收报告和现有独立测试目录

旧计划与最新 `control.md` 冲突时，以 `control.md` 为准。先核对 D9 文件摘要；不匹配时停止并报告，不依据变化中的建议设计矩阵。

## 已采用的矩阵输入

矩阵按 D9 的 `P4-D9-F01～F17` 设计，特别保持：可信内置模块的 FastAPI 模块化单体、显式组合根、Profile 绑定工具视图、进程内财务工具、显式 pending 状态机、可信 `user_id`、结构化分层记忆、HTTP JSON + GET 恢复、Electron 三进程安全边界、一个毛毛、post-commit 进程内事件、单 Alembic 链、P0～P3 兼容和最小只读财富管理模块。

总控采用以下可逆产品默认值作为矩阵前提；它们将在 P4 接口冻结中正式编号：

1. 关闭主窗口默认隐藏到 Tray，首次提示一次；设置可改为退出或每次询问。
2. 毛毛首版为简化透明窗口 + Tray；目标设备不兼容时允许降级普通迷你窗口。
3. P4-C 验收只用虚拟/测试数据；真实个人数据迁移另立任务。
4. 会话消息默认保留 90 天且可删除；记忆候选 30 天过期；已确认记忆保留到删除、失效或被替代。
5. 开机启动默认关闭，由用户显式开启。
6. token 流式显示不是首版验收门槛；状态轮询或状态流均可，最终结果必须能通过 GET 恢复。
7. P4-D 财富管理首轮使用固定虚拟 fixture；UI 自定义目标额延后，不接行情、不交易、不推荐证券。

这些决定是测试输入，不代表功能已经实现。D9 中仍标为待选的 OpenAPI 生成器、前端路由、状态管理、图表库、SSE 具体实现和 Electron 打包工具不得由测试智能体擅自冻结；对应案例写成与实现无关的合同或条件案例。

## 设计原则

1. 按 `P4-A`、`P4-B`、`P4-C`、`P4-D` 四个切片分组，每个切片都有独立进入条件、固定快照、执行顺序和停止条件。
2. 区分 `contract/unit`、`API/integration`、`SQLite`、`PostgreSQL`、`Windows/Electron`、`external/manual` 环境，不能把本地静态检查当作真实桌面或数据库证据。
3. 每项案例必须可由未来测试者直接执行，说明前置数据、操作、预期状态、禁止出现的副作用和证据来源。
4. 安全、权限、隔离、幂等、并发、恢复、迁移和隐私必须包含反例，不能只验证成功路径。
5. 执行方自测与独立验收分开；矩阵可以引用旧回归，但不得把执行方未来结果预填为通过。
6. P0～P3 已通过的范围不得无理由重复设计全部案例；选择能证明兼容边界的代表性门禁，并列出最终回归套件。
7. 所有案例初始状态必须为 `not_run`。本任务不启动服务、数据库、Docker、Electron、DeepSeek、OpenClaw 或微信。

## P4-A 必须覆盖：Host、身份和通用状态

### 模块、Profile 与工具

- manifest/profile/tool/event/settings Schema 严格字段、版本和序列化；额外字段拒绝。
- 重复 module/profile/tool canonical ID、别名、API 前缀、桌面 route、memory namespace、setting key 和 companion state 启动失败。
- Host API 主版本兼容、模块启停、disabled module 的导航/Profile/工具/设置消失。
- 桌面按当前模块确定性选择 Profile；微信路由歧义只形成追问，不越权选择写 Profile。
- Profile 限额只能收紧 Host 上限；模型轮次、总工具、写工具、超时和取消有稳定停止结果。
- 工具在 Schema 可见性和执行时分别授权；猜测隐藏工具名、伪造 module/profile/permission 都被拒绝。
- 财务 adapter 保持现有确认、金额、事务、幂等和错误语义；Host 不提供任意 SQL/Python/MCP 执行入口。

### 账户、会话和用户隔离

- 空系统主人账户初始化只能发生一次；非空系统、远程来源、重复初始化和并发初始化稳定拒绝。
- Argon2id 凭据不回显；错误登录不区分账户存在性；密码变更撤销旧设备会话。
- access/refresh 或不透明 token 的签发、轮换、过期、注销、设备撤销、并发刷新和重放。
- API 从可信 principal 取得 `user_id`；body、模型和工具参数不能自报或覆盖身份。
- 所有财务、活动导入、Agent run、pending、receipt 和 audit 查询/命令按用户隔离；跨用户 UUID、复合外键和幂等键反例。
- 一次性微信绑定码的过期、尝试上限、消费、重放、并发使用、外部身份冲突、撤销和重新绑定；不要求真实微信运行。
- 响应、日志、事件和模型上下文不含密码、原始 token、API Key、原始外部身份或未授权财务数据。

### Workflow、记忆和迁移

- pending 的 needs_input/needs_confirmation/committing/committed/expired/cancelled；24 小时边界、版本竞争、lease 接管、响应丢失和重复/并发确认。
- run/pending 的 user/module/profile/schema/lease 不能由模型覆盖；领域写仍以稳定提交键最终幂等。
- conversation/message、candidate/item、module setting 的用户与命名空间隔离；Profile 只能取得 manifest 授权范围。
- 候选确认、拒绝、过期、晋升共享、失效、替代和删除；敏感删除清空正文，只留不含内容的 tombstone。
- 账目、余额、预算、持仓和行情不能被复制为记忆事实；运行时最多取得 8 条获准记忆。
- 会话 90 天、候选 30 天的恰好到期边界和可控时钟恢复；手动删除立即不可检索。
- 空库和 P0～P3 已有数据在 SQLite/PostgreSQL 上按 nullable→回填→复合约束→非空迁移；升级、允许的降级、孤儿、跨用户引用和单 Alembic head。

## P4-B 必须覆盖：Windows Shell、设置和毛毛

- Electron main/preload/renderer 的静态与运行时边界：sandbox、contextIsolation、CSP、导航限制、IPC sender/参数校验、renderer 无 Node/进程/密钥权限。
- 后端 supervisor 只停止自己启动的进程；随机端口、ready timeout、崩溃、重复启动、已存在手动后端、应用退出和僵尸进程。
- 登录、会话撤销、后端离线/恢复、导航、模块启停、Agent panel 和错误展示不泄露内部异常。
- compiled desktop registry 与后端 `/modules` 取交集；未知或后端禁用模块不渲染，懒加载失败可恢复。
- OpenAPI API 类型漂移门禁；UI contribution 合同版本、route/settings/profile/companion 冲突门禁。
- light/dark/system/high-contrast/reduced-motion、行情红涨绿跌设置与普通收入/支出语义色隔离。
- 主窗口关闭隐藏到 Tray 并只提示一次；退出/每次询问设置；Tray 打开/隐藏、全屏隐藏和开机启动默认关闭。
- 毛毛只有一个；daily finance/wealth management 主形态由 contribution 映射，idle/thinking/tool/confirmation/error/offline 子状态不创建第二 Agent。
- 透明窗拖动、位置原子保存、跨重启恢复、多显示器边界夹取、置顶、隐私模式、键盘入口和普通迷你窗降级。

## P4-C 必须覆盖：日常财务纵向闭环

- 使用虚拟资料完成“午饭 18 元”消息→候选→确认→FinanceService 提交→账本/图表/快照刷新。
- Agent 查询最近交易、账户余额、月度快照时只通过受控工具，带 `as_of`、限制和截断，不读取数据库账号或任意 SQL。
- 候选在确认前可纠正；已入账错误通过现有可审计领域动作处理，不由前端直接覆盖事实。
- 同一 client event、同一确认、断线重试和最终 GET 恢复不重复记账；同键异载荷冲突。
- 模型失败、工具超时、后端离线、权限撤销、资源版本变化和最终文案失败不造成半写或重复写。
- HTTP 严格 body、统一错误/request ID、取消语义、会话归属、模块/Profile 绑定和隐私模式。
- UI 图表、交易列表和详情的金额来自确定性整数分结果；空状态、负向更正、时区/月边界和大列表。
- token streaming 不作为门禁；如果实现 SSE，增加断线、Last-Event-ID/恢复、最终 GET 和资源清理条件案例。

## P4-D 必须覆盖：第二模块扩展性证明

矩阵必须把 D9 的八项证明逐项转成独立案例：

1. 注册 `wealth_management()` 后，模块 API、导航、设置和毛毛形态自动出现，Host 无模块 ID 业务分支。
2. 同一通用 Agent run API 使用 wealth Profile，不新增专用聊天 API。
3. wealth 只见声明的只读工具；猜测 `finance_record_expense` 在可见性和执行时都被拒绝。
4. wealth 只能读 `shared.confirmed` 与自身 confirmed；daily finance 专属记忆读写失败。
5. 禁用 wealth 后贡献全部消失，daily finance 数据、迁移和行为不变。
6. route/tool alias/profile/namespace/setting key 冲突稳定阻止启动。
7. wealth 页面和 adapter 不 import daily finance repository，只依赖公开 snapshot port/DTO。
8. 空库与 P0～P3 数据均可升级；PostgreSQL 复验用户隔离、唯一键和并发。

同时覆盖固定虚拟 fixture 下的应急资金/储蓄只读计算：输入、整数金额、目标、gap、月数、`data_as_of`、缺失数据和零/负边界。确认它不接行情、不写账、不推荐证券，不把“财富管理”等同于股票交易。

## 交付格式

交付 `docs/testing/phase-4-modular-agent-host-test-matrix.md`。每个案例至少包含：

- 唯一 ID；
- P4 切片；
- 需求/冻结来源；
- 层级；
- 环境；
- 自动/人工；
- 前置条件；
- 输入摘要；
- 步骤；
- 预期结果与禁止副作用；
- 风险等级；
- 执行状态。

案例 ID 建议使用 `P4A-*`、`P4B-*`、`P4C-*`、`P4D-*`。矩阵还必须包含：

1. F01～F17 和上述 7 个产品默认值的需求追踪表；
2. 四个切片各自的进入条件、固定快照文件组和退出条件；
3. 环境/权限分层和外部/manual 案例；
4. 执行顺序、可并行组、停止条件和 P0/P1 缺陷门禁；
5. 执行方测试与独立测试的路径所有权；
6. P0～P3 最终回归集合及不重复真实微信/OpenClaw/付费模型的边界；
7. 仍需在正式接口冻结中明确的问题清单，不能自行假定通过。

逐行检查 ID 唯一、必填字段完整、状态全部为 `not_run`，并给出按切片、层级、环境和风险的计数。不得伪造执行时间、通过率或固定快照摘要。

## 文件与操作边界

允许修改：

- `docs/testing/phase-4-modular-agent-host-test-matrix.md`
- `docs/coordination/agents/tester.md`

其他全部只读。特别禁止：

- 修改 `src/**`、`tests/**`、migration、依赖、产品配置、接口冻结、D9 建议、控制/总览、项目计划和其他角色日志；
- 编写独立测试实现；本任务只设计矩阵；
- 启动 FastAPI、PostgreSQL、Docker、Electron、DeepSeek、OpenClaw 或微信；
- 安装依赖、登录外部服务、调用付费 API、读取密钥或真实个人数据；
- 执行任何 Git 写操作。

可以只读检查现有代码、测试和历史报告以保证案例可执行，但不能把只读检查记成 P4 验收证据。

## 进度、交付和停止规则

- 接单后立即在测试角色文件记录固定输入、文件边界、当前步骤和下一检查点。
- 至少在“需求追踪”“P4-A”“P4-B”“P4-C/D”“质量检查与交付”五个里程碑更新执行快照。
- 预计超过五分钟的工作先写下一检查点；每十分钟或每个实质输出刷新心跳。
- 连续两个检查点或同一问题长时间无有效进展时，安全停止，保留已完成文档，并报告具体卡点、最后脱敏错误、已尝试方法和需要总控裁定的问题。
- 完成后更新 `docs/coordination/agents/tester.md`，状态写为 `review` 并停止。只有头脑风暴总控能把任务标为 `complete`、冻结接口或安排实现。
