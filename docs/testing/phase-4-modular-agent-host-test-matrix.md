# P4 模块化 Agent Host 独立验收矩阵

- 任务：`P4-C10`
- 状态：`review`（实现前设计；未执行）
- 设计日期：2026-09-20，Asia/Shanghai
- 固定产品基座：`1d06d92c93d99fb2a3a23da6ff0958932e358814`
- 固定技术建议：`docs/phase-4-d9-modular-agent-host-advice.md`，SHA-256 `765a3547b806724183a6302f4134a28b43e987d066fe30933bde5f993073fe5a`
- 数据边界：只允许虚拟用户、虚拟财务数据、随机数据库 schema、假模型与假渠道 adapter；不得使用真实个人数据、真实微信身份、API Key 或付费模型
- 判定边界：本文件只定义未来可执行验收；所有案例初始状态均为 `not_run`，不表示任何 P4 功能已经实现或通过

## 1. 记号、证据和通用判定

| 字段 | 取值与含义 |
|---|---|
| 层级 | `contract/unit`、`API/integration`、`database`、`desktop/e2e`、`security/manual` |
| 环境 | `contract`、`API`、`SQLite`、`PostgreSQL`、`Windows/Electron`、`external/manual` |
| 自动/人工 | `auto` 表示应由稳定自动化断言；`manual` 表示必须保留人工/真机证据，不能用静态检查替代 |
| 风险 | `P0`：身份越权、数据损坏、重复财务写、密钥/敏感数据泄露或迁移不可恢复；`P1`：核心闭环、恢复或桌面安全失效；`P2`：局部功能/兼容/可用性；`P3`：低影响呈现或诊断 |
| 状态 | 本任务只能使用 `not_run`；未来执行后才可写 `passed/failed/blocked/not_applicable`，并链接固定快照证据 |

每项执行证据至少包含：固定快照摘要、虚拟前置数据、请求/事件关联 ID、结构化返回、数据库或 UI 前后状态、禁止副作用观察、脱敏日志，以及适用时的并发同步点和资源关闭记录。执行方自测不能替代独立证据；SQLite 不能替代 PostgreSQL 锁、约束或迁移证据；静态 Electron 配置不能替代目标 Windows 运行证据。

## 2. 需求追踪

### 2.1 D9 F01～F17

| 冻结输入 | 设计断言 | 主要案例 |
|---|---|---|
| F01 | 可信内置模块的 FastAPI 模块化单体；不加载未知插件 | P4A-REG-03、P4A-REG-04、P4D-EXT-01 |
| F02 | Python factory + 严格 manifest、唯一组合根、启动查重与 Host API 主版本 | P4A-REG-01～04、P4D-EXT-06 |
| F03 | Profile 是逻辑 Agent；桌面确定性路由、微信歧义追问 | P4A-REG-06～07、P4A-PRF-01 |
| F04 | ToolCatalog 绑定视图；Schema 和执行时双重授权 | P4A-PRF-04～06、P4D-EXT-03 |
| F05 | 财务工具保持进程内；MCP 只作受限外部适配 | P4A-PRF-07～09 |
| F06 | 显式 pending 六状态、24 小时、可信 user/module/profile/schema/lease | P4A-WFL-01～10 |
| F07 | 主人账户、Argon2id、可撤销设备会话、一次性渠道绑定，无公众注册 | P4A-AUT-01～10 |
| F08 | 所有事实和幂等范围使用可信 user_id；分步迁移 | P4A-ISO-01～08、P4A-DB-03～06 |
| F09 | 分层结构化记忆、共享仅 confirmed、事实不复制、最多 8 项 | P4A-MEM-01～08 |
| F10 | HTTP JSON + GET 恢复；SSE 仅条件增加；无 WebSocket | P4A-DB-01～02、P4C-FLW-07、P4C-FLT-07 |
| F11 | Electron main/preload/renderer 安全分层 | P4B-SEC-01～08 |
| F12 | OpenAPI 生成 API DTO；UI contribution 手写、版本化、编译期注册 | P4B-UI-01～04、P4D-EXT-01 |
| F13 | 只有一个毛毛；主形态/子状态分离并由 contribution 映射 | P4B-CMP-01～06、P4D-EXT-01 |
| F14 | post-commit 进程内事件只作提示，不承担事务正确性 | P4A-DB-07、P4C-FLT-05 |
| F15 | 单 Alembic 线性链、revision 标注 owner、无 multiple heads | P4A-DB-03～06、P4D-EXT-08 |
| F16 | 最小只读 wealth 模块，以八项检查证明扩展性 | P4D-EXT-01～08、P4D-CAL-01～04 |
| F17 | P0～P3 兼容；先包 adapter，不大规模搬目录 | P4A-PRF-07、P4C-FLW-01～08、最终回归集合 |

### 2.2 已采用的七个产品默认值

| 默认值 | 条件断言 | 主要案例 |
|---|---|---|
| U01 | 首次关闭主窗口隐藏到 Tray 并只提示一次；可改退出/每次询问 | P4B-CMP-02～03 |
| U02 | 简化透明毛毛 + Tray；不兼容时降级普通迷你窗口 | P4B-CMP-01、P4B-CMP-06 |
| U03 | P4-C 只用虚拟/测试数据；真实个人数据迁移另立任务 | P4C-FLW-01～08、P4C-UI-01～05 |
| U04 | 会话 90 天、候选 30 天、confirmed 到删除/失效/替代 | P4A-MEM-02～05、P4A-MEM-08 |
| U05 | 开机启动默认关闭，必须由用户显式开启 | P4B-CMP-04 |
| U06 | token streaming 不是门槛；最终状态必须 GET 恢复 | P4C-FLW-07、P4C-FLT-07 |
| U07 | wealth 首轮使用固定虚拟 fixture，不接行情/交易/证券推荐 | P4D-CAL-01～04 |

## 3. 四切片门禁与固定快照

### 3.1 P4-A Host、身份和通用状态

- 进入条件：正式 `P4-IF-A` 冻结 manifest/profile/tool/auth/workflow/memory/API/迁移合同；执行方提交可运行实现、自测、迁移顺序、虚拟 fixture 和有序文件摘要；控制文件指定唯一数据库启停负责人。
- 固定快照文件组：`src/wife_system/host/**`、P4-A 新 migration、必要的 `api/**` 与现有 agent/finance/activity_import 适配改动、执行方 P4-A 测试、依赖/锁文件和运行说明。对每个文件记录 SHA-256，再计算有序总摘要；矩阵不预造摘要。
- 退出条件：P4-A 适用案例完成；SQLite 与真实 PostgreSQL 分层通过；P0～P3 代表回归通过；无开放 P0/P1；服务和数据库资源关闭。

### 3.2 P4-B Windows Shell、设置和毛毛

- 进入条件：P4-A 已由总控接受；冻结 Electron/Node 版本、API 类型生成器、UI contribution 合同、IPC allowlist、后端 ready 协议和设备设置 schema；提供目标 Windows 设备与无真实密钥的测试 profile。
- 固定快照文件组：`apps/desktop/**`、生成的 API 类型及生成配置、桌面执行方测试、必要 Host API 只读变动、依赖锁文件和运行说明；生成物与 OpenAPI 输入分别摘要。
- 退出条件：静态安全门禁、桌面自动化和目标 Windows 人工证据均完成；后端进程无遗留；主窗口/Tray/毛毛/主题/离线恢复达到冻结行为；无开放 P0/P1。

### 3.3 P4-C 日常财务纵向闭环

- 进入条件：P4-A/B 已接受；冻结 daily contribution、通用 run API、虚拟 fixture、dashboard DTO、刷新机制和条件 SSE 合同；FinanceService/P2/P3 不变量保持只读。
- 固定快照文件组：daily module 后端/桌面 adapter 与 UI、必要公开 query DTO、执行方 P4-C 测试、OpenAPI/生成类型、运行说明；现有 finance/agent 变化必须单列摘要和理由。
- 退出条件：虚拟“午饭 18 元”端到端一次一写并可恢复；读工具、纠正、故障、权限、UI 金额/月界全部通过；P0～P3 回归和 PostgreSQL 关键门禁通过；无开放 P0/P1。

### 3.4 P4-D 第二模块扩展性证明

- 进入条件：P4-A/B 公共扩展合同稳定，P4-C daily 基线已接受；冻结 wealth Profile、只读 snapshot port、固定虚拟 fixture 和计算公式；不增加行情/交易依赖。
- 固定快照文件组：wealth manifest/Profile/tool/UI/设置/毛毛 contribution、公开 snapshot port/DTO、唯一组合根的注册变化、执行方 P4-D 测试与运行说明；Host 核心和 daily 内部文件如有变化必须单列并触发架构复核。
- 退出条件：八项扩展性证明全部完成；确定性财富计算边界通过；禁用 wealth 不影响 daily；空库及 P0～P3 数据迁移与 PostgreSQL 隔离通过；无 Host 模块 ID 业务分支和开放 P0/P1。

## 4. 环境、权限与执行顺序

| 环境 | 主要用途 | 必需证据 | 不可替代项 |
|---|---|---|---|
| contract | Pydantic/TypeScript 合同、注册查重、Profile/工具/记忆授权、确定性计算 | 纯输入输出、结构/依赖规则、无副作用断言 | 不能证明 HTTP、数据库或 Windows 运行时 |
| API | FastAPI principal、严格 body、状态恢复、错误与幂等 | 本地 HTTP、依赖替身、数据库前后状态、脱敏日志 | 不能证明 PostgreSQL 并发或 Electron 隔离 |
| SQLite | 常规领域编排、迁移开发回路、回滚和保留策略 | 临时库、可控时钟、前后行/关系/内容断言 | 不能替代 PostgreSQL 复合 FK、锁和并发 |
| PostgreSQL | 目标库迁移、复合约束、并发初始化/刷新/确认、一次一写 | 随机 schema、真实约束、两连接/两实例同步 | 离线 DDL 与 SQLite 均不可替代 |
| Windows/Electron | 三进程隔离、窗口/Tray/毛毛、后端 supervisor、OS secret | 固定构建、目标 Windows 运行日志、进程/窗口观察 | 静态配置或浏览器预览不可替代 |
| external/manual | 显示器、全屏、降级窗口、可访问性等人工设备证据 | 脱敏录屏/截图、设备条件、操作步骤、结果 | 不要求真实微信、OpenClaw、DeepSeek 或付费服务 |

建议顺序：每个切片先做快照与合同门禁，再做 API/SQLite，随后 PostgreSQL，最后 Windows/Electron 与 external/manual。P4-A 的合同与独立数据库夹具可并行；P4-B 的静态安全与 UI 合同可并行，但 supervisor 和窗口人工检查须在同一固定构建上；P4-C 的后端闭环与 UI 展示可在合同冻结后并行，最终只做一次纵向合并门禁；P4-D 的八项扩展性与确定性计算可并行，迁移门禁最后收口。

## 5. 验收案例

所有案例均为设计状态，没有运行。

### 5.1 P4-A：Host、身份和通用状态（64 项）

#### 模块注册、Profile 与工具

| ID | 切片 | 需求/冻结来源 | 层级 | 环境 | 自动/人工 | 前置条件 | 输入摘要 | 步骤 | 预期结果与禁止副作用 | 风险 | 执行状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P4A-REG-01 | A | F02 | contract/unit | contract | auto | manifest/Profile/tool/event/settings DTO 已冻结 | 合法对象、缺字段、错类型、额外字段、版本往返 | 分别校验并序列化/反序列化 | 合法值稳定往返；非法值按字段拒绝；不得忽略额外字段或执行 callable | P1 | not_run |
| P4A-REG-02 | A | F02；任务卡 | contract/unit | contract | auto | 可构造两个 builtin 定义 | 重复 module/profile/tool canonical ID、别名、API 前缀、route、namespace、setting key、companion state | 参数化注册每类冲突 | 每类均在启动验证期以稳定错误失败；不得后注册覆盖先注册 | P0 | not_run |
| P4A-REG-03 | A | F01/F02 | contract/unit | contract | auto | Host API 主版本合同冻结 | compatible、低/高不兼容版本 | 注册并读取诊断 | 兼容模块可用；不兼容模块按冻结策略禁用或阻止启动并可诊断；不得部分暴露贡献 | P1 | not_run |
| P4A-REG-04 | A | F01/F02 | security/manual | contract | auto | 唯一组合根可静态导入 | builtin 列表、伪造目录插件、manifest import path | 审查注册入口并尝试注入未知路径 | 只显式调用可信 factory；无目录扫描、entry-point 自动执行或远程代码加载 | P0 | not_run |
| P4A-REG-05 | A | F02；模块启停 | API/integration | API | auto | daily 与 wealth 均已编译 | 启用→禁用→再启用模块 | 调用设置与 `/modules`，并查询导航/Profile/工具/设置摘要 | 禁用后贡献全部消失，专属 API 稳定拒绝；再启用恢复合同，不删事实数据 | P1 | not_run |
| P4A-REG-06 | A | F03 | contract/unit | contract | auto | 两模块各有 Profile | 当前桌面 route 连续切换 | 解析 Profile 多次并统计 provider 调用 | 同一路由确定性得到同一 Profile；页面切换不调用模型，不串会话/记忆 | P1 | not_run |
| P4A-REG-07 | A | F03；微信边界 | API/integration | API | auto | 假渠道 adapter、两个可匹配意图 | 歧义、唯一匹配、禁用模块匹配 | 提交虚拟消息并检查路由状态 | 唯一时只选已启用 Profile；歧义只形成追问；不得猜选写 Profile或执行工具 | P0 | not_run |
| P4A-REG-08 | A | F02/F14 | contract/unit | contract | auto | event/settings 合同冻结 | 未声明事件、版本不兼容、重复 setting key | 注册生产者/消费者/设置 | 未声明或不兼容在启动期失败；不得运行后静默丢事件或覆盖设置 | P1 | not_run |
| P4A-REG-09 | A | F01/F12 | API/integration | API | auto | registry 已启动 | 当前用户无权限、模块禁用、模块启用 | GET `/modules` 与模块摘要 | 只返回用户获准且启用的序列化贡献；不返回 factory、提示词全文、内部路径 | P1 | not_run |
| P4A-REG-10 | A | F02 | contract/unit | contract | auto | canonical 格式和 SemVer 待冻结后绑定 | 大小写、空白、Unicode 等价、非法分隔符、超长 ID | 参数化构造所有 ID/alias/version | 规范化与拒绝规则唯一；碰撞不能因后端或大小写规则绕过 | P1 | not_run |
| P4A-PRF-01 | A | F03 | contract/unit | contract | auto | Profile 合同冻结 | profile/module 不匹配、未知 Profile、禁用模块 Profile | 解析运行上下文 | 合法绑定成功；其他稳定拒绝且不退回万能 Agent | P1 | not_run |
| P4A-PRF-02 | A | F03/F04 | contract/unit | contract | auto | Host 全局硬上限固定 | Profile 等于、收紧、放宽模型轮次/工具/写调用/超时 | 绑定 Profile | 等于/收紧可用；任何放宽被拒；不得改变全局限制 | P0 | not_run |
| P4A-PRF-03 | A | P2-IF-001；F03 | contract/unit | contract | auto | 脚本化 provider 与假工具 | 恰好最大轮次、总工具、写工具、重复调用、空响应 | 执行边界场景 | 在精确上限停止并返回稳定原因；不得多执行一次写工具 | P0 | not_run |
| P4A-PRF-04 | A | F04 | contract/unit | contract | auto | 工具目录含读/写/隐藏工具 | 不同 Profile、permission、module 状态 | 生成 Schema 视图 | 仅三者交集进入模型 Schema；上下文/身份字段永不暴露 | P0 | not_run |
| P4A-PRF-05 | A | F04 | API/integration | API | auto | 隐藏工具 canonical ID 已知给测试 | 猜测隐藏名称、别名、伪造 permission/module/profile | 绕过 Schema 直接请求执行 | 执行时再次拒绝 `tool_not_allowed`；handler、数据库、审计副作用均为零 | P0 | not_run |
| P4A-PRF-06 | A | F04；P2-IF-001 | contract/unit | contract | auto | BoundToolRegistry 已绑定可信 principal | 参数中注入 user/device/module/profile/approved | 调用每个工具 Schema | 严格 DTO 拒绝身份与批准字段；实际上下文保持入口值 | P0 | not_run |
| P4A-PRF-07 | A | F05/F17；P1/P2 | API/integration | SQLite | auto | daily adapter 连接现有 FinanceService | 查询、候选、确认、坏金额、stale、同键重放 | 经 Host 调用六个财务工具 | 保持整数分、确认、事务、幂等和稳定错误；不得复制或重写领域规则 | P0 | not_run |
| P4A-PRF-08 | A | F01/F05 | security/manual | contract | auto | 工具注册完整 | `sql`、`python`、文件路径、shell、任意 MCP server 名称 | 枚举 Schema 并猜名执行 | Host 没有任意 SQL/Python/shell/文件执行入口，未允许 MCP 不可连接 | P0 | not_run |
| P4A-PRF-09 | A | F05 | contract/unit | contract | auto | 若实现 MCP/HTTP adapter 才适用 | 非 allowlist server/tool、超时、超大输出、取消、坏协议、恶意描述 | 用假传输调用 | 固定协议/allowlist/大小/超时生效，内容按不可信数据处理；不影响进程内财务事务 | P1 | not_run |
| P4A-PRF-10 | A | F03/F04 | contract/unit | contract | auto | ToolExecutionResult 合同冻结 | ok/needs_input/needs_confirmation/error 与非法组合 | 校验结果、错误与 provenance | 联合类型严格，安全错误保留 code/retryable；不得把异常正文、原参数或 audit 内部详情给模型 | P1 | not_run |

#### 账户、设备会话、渠道绑定与用户隔离

| ID | 切片 | 需求/冻结来源 | 层级 | 环境 | 自动/人工 | 前置条件 | 输入摘要 | 步骤 | 预期结果与禁止副作用 | 风险 | 执行状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P4A-AUT-01 | A | F07 | API/integration | PostgreSQL | auto | 空 schema；本机来源判定可替换 | 两个并发 initialize、远程来源、随后重复请求 | 同步提交初始化 | 只有一个主人账户成功；其余稳定拒绝；无第二 credential/device 或半写 | P0 | not_run |
| P4A-AUT-02 | A | F07 | API/integration | SQLite | auto | 非空 P0～P3 数据库或已有用户 | initialize 请求 | 调用初始化端点 | 初始化端点稳定拒绝且零写入；既有数据的 bootstrap owner 只由受控 migration 处理，不得由 API 覆盖 owner | P0 | not_run |
| P4A-AUT-03 | A | F07 | security/manual | SQLite | auto | 已初始化虚拟用户 | 正确密码、数据库读取、响应/日志捕获 | 登录并检查 credential | 仅存 Argon2id 哈希及冻结参数；响应/日志不含密码/哈希；错误登录不改哈希 | P0 | not_run |
| P4A-AUT-04 | A | F07 | API/integration | API | auto | 存在用户 | 错 handle、错密码、停用用户、畸形输入 | 比较状态、文案、结构和可观察时序等级 | 错误不区分账户是否存在；严格 body；不签发 session，不泄露哈希或堆栈 | P0 | not_run |
| P4A-AUT-05 | A | F07 | API/integration | API | auto | 成功登录 | access/refresh 或不透明 token、恰好到期前后 | 调用受保护 API 与 refresh | 原始 token 只签发一次；库仅摘要；到期边界稳定；旧 access 按冻结策略失效 | P0 | not_run |
| P4A-AUT-06 | A | F07 | API/integration | PostgreSQL | auto | 同一 refresh/session token | 两并发刷新、顺序重放、不同设备 | 用两连接同步刷新 | 最多一个轮换成功；旧 token 重放稳定拒绝/撤销族；不产生两个 active 后继 | P0 | not_run |
| P4A-AUT-07 | A | F07 | API/integration | API | auto | 两设备 active session | logout 当前设备、撤销其他设备、已撤销 token | 连续调用 API/refresh | 目标 session 立即不可用，其他未撤销设备按规则保留；错误为 `session_revoked` | P0 | not_run |
| P4A-AUT-08 | A | F07 | API/integration | SQLite | auto | 两设备和旧密码 active | 改密成功/失败 | 改密后用旧新密码及所有 session 测试 | 旧密码失败，旧设备 session 全撤销，新凭据有效；失败事务不改变任何状态 | P0 | not_run |
| P4A-AUT-09 | A | F07；绑定默认 | API/integration | PostgreSQL | auto | 假渠道 adapter、可控时钟 | 绑定码恰好过期、超尝试、已消费、并发消费、重放 | 分别提交绑定 | 仅一个未过期码一次成功；摘要存储；失败不建立 binding、不回显原码/身份 | P0 | not_run |
| P4A-AUT-10 | A | F07 | API/integration | PostgreSQL | auto | 两虚拟用户和一个外部身份摘要 | 冲突绑定、撤销、重新绑定 | 建立/冲突/撤销/再绑定 | active 外部身份全局唯一；不自动抢占；撤销留无原始身份的审计；再绑定按冻结流程成功 | P0 | not_run |
| P4A-ISO-01 | A | F08；P2/P3 identity | API/integration | API | auto | 认证 principal A | body/query/model/tool 参数伪造 user B | 调用所有写/读入口 | 始终使用 A；自报字段被严格拒绝或忽略规则冻结；不得访问 B | P0 | not_run |
| P4A-ISO-02 | A | F08 | database | SQLite | auto | A/B 各有账户、分类、交易、活动、预算、收入、导入批次 | B 的 UUID 交给 A | 逐类 GET/命令/工具查询 | 返回统一未找到/拒绝；响应、日志、计数不泄露 B 数据存在性 | P0 | not_run |
| P4A-ISO-03 | A | F08 | database | PostgreSQL | auto | A/B 资源均存在 | 交易分录引用另一用户账户/分类；活动分配跨用户 | 直接 ORM/SQL 尝试提交 | 复合 FK/约束在数据库拒绝；整个事务回滚，无孤儿或半写 | P0 | not_run |
| P4A-ISO-04 | A | F08 | database | PostgreSQL | auto | A/B 使用同 source system 与同 raw event/key | 同载荷与异载荷组合 | 并发领取命令/run | 用户域互不冲突；每用户内部仍单一结果；HMAC/唯一键含 user 域且不存原键 | P0 | not_run |
| P4A-ISO-05 | A | F08 | API/integration | SQLite | auto | A/B 各有 run/pending/receipt/audit | 跨用户 run/pending UUID 和确认码 | GET/resume/cancel/confirm | 统一拒绝且不改变状态；不得通过 receipt/audit 反推出 B 的金额或操作 | P0 | not_run |
| P4A-ISO-06 | A | F08/F09 | database | SQLite | auto | A/B 各有 conversation/message/memory/setting | 跨用户 UUID、namespace、module key | 查询、更新、删除 | 所有记录按 user 过滤，复合关系防串联；A 的删除不影响 B | P0 | not_run |
| P4A-ISO-07 | A | F08 | security/manual | API | auto | 全链路植入虚拟 canary | 密码、token、API key、外部身份、B 的财务数据 | 触发成功、校验错、数据库错、模型错并捕获响应/日志/事件/上下文 | 所有禁止值均不存在；只允许摘要前缀和内部关联 ID | P0 | not_run |
| P4A-ISO-08 | A | F08 | database | PostgreSQL | auto | 已有跨表虚拟数据 | 停用用户、撤销 session、模块禁用同时发生 | 两连接执行查询/写入 | 新操作按可信状态拒绝；既有事实不被删除或重新归属；并发无越权窗口 | P0 | not_run |

#### Workflow、恢复与记忆

| ID | 切片 | 需求/冻结来源 | 层级 | 环境 | 自动/人工 | 前置条件 | 输入摘要 | 步骤 | 预期结果与禁止副作用 | 风险 | 执行状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P4A-WFL-01 | A | F06；P2-IF-001 | contract/unit | contract | auto | 通用 coordinator 与假 handler | needs_input→needs_confirmation→committing→committed；expired/cancelled | 枚举合法/非法转换 | 只允许冻结转换，终态不可回退；非法转换无版本/审计副作用 | P0 | not_run |
| P4A-WFL-02 | A | F06；U04 | database | SQLite | auto | 可控时钟和普通候选 | 24h−1µs、恰好24h、24h+1µs | 确认并检查事实/回执 | 前者可提交；后两者 expired 且零领域写；时钟 teardown 恢复 | P0 | not_run |
| P4A-WFL-03 | A | F06 | database | PostgreSQL | auto | 一个 needs_confirmation 候选 | 同确认 ID 两并发请求 | 两连接同步确认 | 只有一个获得提交权；另一重放同结果；领域回执与事实恰好一份 | P0 | not_run |
| P4A-WFL-04 | A | F06 | database | SQLite | auto | 候选引用资源版本 v1 | 确认前归档/修订为 v2 | 确认并恢复状态 | 返回 stale/重新确认要求；不写事实、不伪造 committed | P0 | not_run |
| P4A-WFL-05 | A | F06 | database | PostgreSQL | auto | running run 持有 lease | lease 未到期、恰好到期、过期；两个接管者 | 同步尝试接管 | 未到期拒绝；到期边界按冻结规则；过期只有一个新 attempt，旧 worker 不能覆盖结果 | P0 | not_run |
| P4A-WFL-06 | A | F06/F10 | API/integration | API | auto | commit 已完成但响应被丢弃 | 同 event/confirmation ID 和新 ID | 新应用实例 GET/重放 | 同 ID 恢复原 committed 结果；新 ID 不重复写；关联 ID 可追踪 | P0 | not_run |
| P4A-WFL-07 | A | F06 | API/integration | API | auto | 分别处于 needs_input/confirmation/committing/committed | cancel 请求 | 各状态取消并 GET | 事务前可进入 cancelled；committing 后只报告确定结果中并最终恢复；不得虚假称已取消写入 | P0 | not_run |
| P4A-WFL-08 | A | F06 | API/integration | SQLite | auto | 可注入模型、工具、数据库故障 | 超时、永久错误、事务前/中故障 | 执行后重试同 ID | 稳定分类；失败无半写；允许重试路径复用原 ID；永久错误不隐藏重试 | P1 | not_run |
| P4A-WFL-09 | A | F06；P2 | API/integration | SQLite | auto | 领域提交成功 | 最终自然语言生成失败/进程退出 | GET 并重试 run | committed 事实保持一份，可从结构化结果恢复；不得再次调用写工具 | P0 | not_run |
| P4A-WFL-10 | A | F06/F08 | contract/unit | contract | auto | 模型可返回任意 JSON | 覆盖 user/module/profile/schema/lease/version/approved | 让模型补充或确认 | 所有可信字段保持服务端值；伪造内容只作为不可信输入并被拒 | P0 | not_run |
| P4A-MEM-01 | A | F09 | database | SQLite | auto | shared/daily/wealth 命名空间有虚拟条目 | 各 Profile 读/提议/确认越权组合 | 检索与写候选 | 只允许 manifest grant；无 wildcard；越权不泄露条目数量/内容 | P0 | not_run |
| P4A-MEM-02 | A | F09；U04 | database | SQLite | auto | pending candidate、可控时钟 | confirm/reject；30d−1µs/恰好30d/+1µs | 执行状态转换 | 确认生成获准 item；拒绝/过期不保留敏感正文；边界稳定且不可复活 | P1 | not_run |
| P4A-MEM-03 | A | F09 | API/integration | SQLite | auto | daily candidate 请求晋升 shared | 来源摘要、敏感级别、有效期、影响模块 | GET 详情后确认 | 只有显式确认可创建 `shared.confirmed`，候选关系可追溯；不得静默晋升 | P0 | not_run |
| P4A-MEM-04 | A | F09 | database | SQLite | auto | confirmed v1 | 失效、由 v2 替代、重复确认、并发替代 | 执行并回查 | 活跃链唯一、旧版本可审计但不可检索；并发只有一个胜者 | P1 | not_run |
| P4A-MEM-05 | A | F09；U04 | database | SQLite | auto | 敏感 message/item | 手动删除 | 删除并直接检索数据库与 API | 立即不可检索，正文/value_json 被清空，只留无内容 tombstone；缓存/上下文也失效 | P0 | not_run |
| P4A-MEM-06 | A | F09 | security/manual | SQLite | auto | 账目、余额、预算、持仓、行情虚拟事实 | 建议记忆与对话总结 | 检查 candidate/item/message/prompt | 事实不被复制为长期记忆；只能由授权工具按需取最新值 | P0 | not_run |
| P4A-MEM-07 | A | F09 | contract/unit | contract | auto | 12 条跨 namespace/状态/时间记忆 | Profile grant、tag、到期和相同时间 | 多次检索 | 只返回获准 active 未过期项，最多 8 条，稳定排序；不塞入全账本/全对话 | P1 | not_run |
| P4A-MEM-08 | A | F09；U04 | database | SQLite | auto | 会话消息可控时钟 | 90d−1µs/恰好90d/+1µs、手动删除、保留 confirmed | 执行清理并 GET | 会话按冻结边界清理；手删立即生效；confirmed 不因会话清理消失 | P1 | not_run |

#### API、迁移、事件与设置

| ID | 切片 | 需求/冻结来源 | 层级 | 环境 | 自动/人工 | 前置条件 | 输入摘要 | 步骤 | 预期结果与禁止副作用 | 风险 | 执行状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P4A-DB-01 | A | F10；D9 API | API/integration | API | auto | Host API 已组装 | auth/modules/conversation/run/memory/settings 的额外字段、错类型、缺 token、未知 ID | 参数化请求 | 严格 body、统一 request ID/error envelope/状态码；无处理器和数据库副作用 | P1 | not_run |
| P4A-DB-02 | A | F10 | API/integration | API | auto | run/pending/conversation 已创建 | 断线、重复 GET、相同状态变更键、同键异载荷 | 重连并查询/重放 | GET 可恢复最终结构化结果；同键同载荷稳定，同键异载荷冲突；不依赖 token streaming | P0 | not_run |
| P4A-DB-03 | A | F08/F15 | database | SQLite | auto | 空库与 migration chain | base→head、重复 upgrade、允许 downgrade/rebuild | 执行并检查 schema/head | 单一 head、owner 标注和约束符合冻结模型；重复操作安全；无 multiple heads | P0 | not_run |
| P4A-DB-04 | A | F08/F15/F17 | database | SQLite | auto | P0～P3 全量虚拟历史数据 | nullable→回填→复合约束→非空升级 | 每阶段核对数量、ID、金额、版本、引用、摘要 | 历史逐字/数值保持，统一 bootstrap user；孤儿/重复安全失败，不自动合并或删数据 | P0 | not_run |
| P4A-DB-05 | A | F08/F15 | database | PostgreSQL | auto | 空 schema 与已有 P0～P3 schema | 完整升级、重复升级、允许降级 | 在随机 schema 执行 | 类型、非空、复合 FK/unique/index 真实生效；单 head；失败事务不留半迁移 | P0 | not_run |
| P4A-DB-06 | A | F08/F15 | database | PostgreSQL | auto | 含孤儿、跨用户引用、同用户/跨用户同幂等键的构造数据 | 回填与约束阶段 | 分别迁移 | 合法数据保持；非法数据在加约束前安全阻断并可诊断；不得重归属、截断或删除 | P0 | not_run |
| P4A-DB-07 | A | F14 | API/integration | SQLite | auto | 领域事务和两个事件 handler | 事务成功/失败、handler 抛错、重复消费提示 | 提交并检查事实/UI提示 | 只在 commit 后发布；失败事务零事件；handler 失败不回滚事实；事件载荷最小且无原始键/敏感详情 | P0 | not_run |
| P4A-DB-08 | A | F02/F09/F13 | API/integration | SQLite | auto | 账户同步、设备本地、运行时三类设置 | 合法/未知 key、错 schema version、并发更新、API key 伪装设置 | 分别通过 Host/Electron 假接口写入 | 服务端只存账户同步设置并做版本冲突；设备设置不上传；运行时可丢弃；API Key 不进入普通 JSON | P1 | not_run |

### 5.2 P4-B：Windows Shell、设置和毛毛（24 项）

#### Electron 安全与后端监督

| ID | 切片 | 需求/冻结来源 | 层级 | 环境 | 自动/人工 | 前置条件 | 输入摘要 | 步骤 | 预期结果与禁止副作用 | 风险 | 执行状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P4B-SEC-01 | B | F11 | security/manual | Windows/Electron | auto | 固定 Electron 构建 | BrowserWindow 配置与运行时 renderer | 静态检查并在 renderer 探测 | sandbox/contextIsolation 开启、nodeIntegration 关闭；无 `require/process/fs/child_process` 或任意 preload 对象 | P0 | not_run |
| P4B-SEC-02 | B | F11 | security/manual | Windows/Electron | auto | CSP/导航 allowlist 冻结 | inline script、data/javascript URL、未知 origin、新窗口、外链 | 从不可信内容触发导航/打开 | CSP 阻止执行；未知导航/窗口拒绝；获准外链只由 main 安全打开，不加载进应用权限域 | P0 | not_run |
| P4B-SEC-03 | B | F11 | contract/unit | contract | auto | preload 类型合同可导入 | 枚举 contextBridge 暴露对象 | 与 allowlist 对比并尝试直接 ipcRenderer/send/invoke | 只暴露窄 typed 方法；无通用 channel、Node require、密钥或进程控制 | P0 | not_run |
| P4B-SEC-04 | B | F11 | security/manual | Windows/Electron | auto | IPC handlers 已注册 | 伪造 sender、错 origin、额外/错型参数、未知 channel、重复调用 | 逐项 invoke/send | sender 与参数双校验；稳定拒绝；不得启动进程、改设置、打开窗口或泄露异常 | P0 | not_run |
| P4B-SEC-05 | B | F07/F11 | security/manual | Windows/Electron | auto | 假 token 与假 API key | localStorage/sessionStorage/IndexedDB/renderer 内存转储、main safeStorage | 登录/刷新/重启并检查各层 | refresh/device token 与 API key 只在 main/OS 保护边界；renderer 无持久原文；日志与 crash dump 无值 | P0 | not_run |
| P4B-SEC-06 | B | F11 | API/integration | Windows/Electron | auto | 后端绑定随机 loopback port | 只知道端口、错 nonce、错 origin、过期 access、远程地址 | 绕过 main 直连 Host | 端口不是认证；nonce/origin/token 均校验；只绑定 loopback，远程连接拒绝 | P0 | not_run |
| P4B-SEC-07 | B | F11/F12 | security/manual | Windows/Electron | auto | 模块标签、错误、消息均含虚拟恶意 HTML | script/img/event handler/RTL/超长文本 | 渲染导航、通知、Agent panel、错误 | 文本安全编码、布局有界且不执行；不得改变 IPC、模块注册或权限 | P0 | not_run |
| P4B-SEC-08 | B | F11 | desktop/e2e | Windows/Electron | auto | 可注入 preload/backend/lazy-load 故障 | 内部路径、SQL、堆栈、token canary | 触发并查看 UI、console、日志 | 用户只见稳定安全错误和 request ID；renderer console/日志无秘密或未授权数据 | P0 | not_run |
| P4B-SUP-01 | B | D9 BackendSupervisor | desktop/e2e | Windows/Electron | auto | supervisor 可记录 PID+nonce | 自己启动、手工启动、伪造同 PID | 请求停止/应用退出 | 只停止 PID+nonce 匹配且由本实例启动的子进程；手工/他实例进程保持 | P0 | not_run |
| P4B-SUP-02 | B | D9 lifecycle | desktop/e2e | Windows/Electron | auto | 端口分配与 ready 协议冻结 | 端口冲突、无 ready、坏 nonce、ready 超时 | 启动后端 | 使用随机可用 loopback 端口；超时进入离线/诊断并清理自有子进程，不把 health 当 ready | P1 | not_run |
| P4B-SUP-03 | B | D9 lifecycle | desktop/e2e | Windows/Electron | auto | 假后端可崩溃 | 启动前崩溃、ready 后崩溃、连续崩溃 | 观察重启策略 | 状态转 offline；重启次数/退避有界，不形成重启风暴或重复 run；用户可恢复 | P1 | not_run |
| P4B-SUP-04 | B | D9 lifecycle | desktop/e2e | Windows/Electron | auto | 已有手动后端或两个 app 启动请求 | 重复启动、开发连接模式 | 启动/关闭两个客户端 | 不产生重复 owned 后端；连接手动后端时不取得停止权；状态可区分 | P1 | not_run |
| P4B-SUP-05 | B | D9 lifecycle | security/manual | Windows/Electron | manual | 目标 Windows，后端含子线程/连接 | 正常退出、强关主窗口、系统注销 | 检查进程树/端口/文件锁 | 自有后端按冻结时限退出，无僵尸/孤儿/占用端口；未拥有进程不受影响 | P1 | not_run |
| P4B-SUP-06 | B | D9 offline recovery | desktop/e2e | Windows/Electron | auto | renderer 有未发送虚拟消息 | 后端离线→恢复、应用重启、重复点击 | 发送并观察 client_event_id/GET | 未发送内容和同一 ID 保留；恢复后只提交一次；UI 不凭新 ID 制造重复账候选 | P0 | not_run |

#### 模块 UI、主题、Tray 与毛毛

| ID | 切片 | 需求/冻结来源 | 层级 | 环境 | 自动/人工 | 前置条件 | 输入摘要 | 步骤 | 预期结果与禁止副作用 | 风险 | 执行状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P4B-UI-01 | B | F12 | contract/unit | contract | auto | compiled registry 与 `/modules` fixture | 后端启用/禁用、桌面缺失、版本不兼容、未知模块 | 计算交集 | 只渲染两侧均存在且兼容的模块；未知/禁用不导航、不预加载 | P1 | not_run |
| P4B-UI-02 | B | F12 | desktop/e2e | Windows/Electron | auto | 两个 lazy route | chunk 加载失败、重试成功、切换模块 | 导航并恢复 | 局部错误边界可重试，Shell/登录/其他模块可用；不循环加载或丢当前会话 | P1 | not_run |
| P4B-UI-03 | B | F12 | contract/unit | contract | auto | 冻结 OpenAPI 与生成命令 | 后端 DTO 字段/枚举/required 改变；生成物陈旧 | CI 比较生成差异并编译 | 漂移门禁失败并定位；不得靠手写 API 类型掩盖差异或运行时下载 schema | P1 | not_run |
| P4B-UI-04 | B | F12 | contract/unit | contract | auto | UI contribution 合同冻结 | hostUiMajor、route/path/setting/profile/companion 冲突 | 编译期注册和启动验证 | 不兼容或冲突稳定失败；Shell 无 `if moduleId` 业务分支 | P1 | not_run |
| P4B-CMP-01 | B | F13；U02 | desktop/e2e | Windows/Electron | auto | daily/wealth contributions 与假状态流 | 切换模块及 idle/thinking/tool/confirmation/error/offline | 观察窗口、Profile 和状态 | 始终只有一个毛毛窗口/Agent 入口；主形态随 contribution，子状态不创建第二 Agent或触发写入 | P1 | not_run |
| P4B-CMP-02 | B | U01/F13 | desktop/e2e | Windows/Electron | auto | 新设备设置 | 首次和第二次关闭主窗口 | 关闭、从 Tray 恢复、再次关闭 | 首次隐藏并只提示一次；第二次不重复提示；Host/毛毛按设置驻留且无数据丢失 | P1 | not_run |
| P4B-CMP-03 | B | U01 | desktop/e2e | Windows/Electron | auto | 关闭策略可切换 | 退出/每次询问/隐藏，Tray 打开/隐藏 | 每种设置执行关闭与取消 | 行为精确对应设置；“退出”清理自有后端；询问取消不退出；Tray 状态一致 | P1 | not_run |
| P4B-CMP-04 | B | U05 | security/manual | Windows/Electron | manual | 新安装测试 profile | 首次运行、显式启用/禁用开机启动 | 检查 OS 启动项和 UI | 默认关闭且无启动项；只有明确操作才创建；禁用清理本应用项，不改其他应用 | P1 | not_run |
| P4B-CMP-05 | B | F13 | desktop/e2e | external/manual | manual | 多显示器/缩放/全屏测试设备 | 拖动、置顶、重启、拔屏、分辨率变化、全屏、隐私、键盘 | 逐项操作并重启 | 位置用临时文件原子替换并恢复/夹取；全屏按规则隐藏；隐私不显示金额；键盘入口可达 | P1 | not_run |
| P4B-CMP-06 | B | U02；主题要求 | desktop/e2e | external/manual | manual | 支持/不支持透明窗口设备 | 透明失败、普通迷你窗降级；light/dark/system/high-contrast/reduced-motion；中外行情色 | 切换设备条件和主题 | 可安全降级且合同不变；文本对比/焦点可辨；reduced motion 生效；收入/支出色不复用涨跌色 | P2 | not_run |

### 5.3 P4-C：日常财务纵向闭环（20 项）

#### 主闭环、查询与恢复

| ID | 切片 | 需求/冻结来源 | 层级 | 环境 | 自动/人工 | 前置条件 | 输入摘要 | 步骤 | 预期结果与禁止副作用 | 风险 | 执行状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P4C-FLW-01 | C | P4-C；F17；U03 | desktop/e2e | Windows/Electron | auto | 虚拟用户、现金账户1000.00元、餐饮分类、daily Profile | `午饭 18 元` + stable client_event_id | 桌面发送→候选→确认→GET→账本/图表/快照刷新 | 只记一笔18.00元支出，整数分1800、账户98200分；候选/回执/audit 可追踪；确认前零事实写 | P0 | not_run |
| P4C-FLW-02 | C | P2查询工具 | API/integration | SQLite | auto | 有跨月/多分类虚拟交易 | 最近交易 limit/time range/as_of | Agent 调受控查询并比较 FinanceService | 稳定排序、限制、`truncated`、`as_of` 正确；不得返回全库、数据库凭据或任意 SQL 能力 | P1 | not_run |
| P4C-FLW-03 | C | P2查询工具 | API/integration | SQLite | auto | 多账户、转账、退款、预算虚拟数据 | 余额和月度快照问题 | 经 Profile 工具调用并与确定性快照核对 | 余额/收入/支出/转账/退款口径与 P1 一致；模型不自行算金额或改 `as_of` | P0 | not_run |
| P4C-FLW-04 | C | P4-C 候选纠正 | API/integration | SQLite | auto | 已有 needs_confirmation 候选 | 确认前改金额/账户/分类/时间 | 使用补充/纠正 API 后确认 | 产生版本化新摘要并要求重新确认；旧确认码 stale；只提交修正后的单一事实 | P0 | not_run |
| P4C-FLW-05 | C | P1审计边界 | API/integration | SQLite | auto | 已 committed 错误支出 | 前端直接 PUT 事实、合法 reversal/refund/correction 动作 | 分别尝试 | 直接覆盖拒绝；合法领域动作追加可审计事实并保留原账；不得改写 ledger 历史 | P0 | not_run |
| P4C-FLW-06 | C | F06/F08；P2幂等 | database | PostgreSQL | auto | 两个应用实例、同一虚拟用户 | 同 client event、同确认、断线重试、同键异载荷 | 用同步屏障并发运行/确认 | 同载荷恰好一次记账并重放；异载荷冲突；run/pending/receipt/audit 与 P1 结果一致 | P0 | not_run |
| P4C-FLW-07 | C | F10；U06 | API/integration | API | auto | run 最终可持久恢复 | 无 streaming；若实现则断开状态流 | 创建、断线、GET 恢复 | 轮询路径足以取得最终结果；token 流不是通过条件；任何流都不能成为唯一结果来源 | P1 | not_run |
| P4C-FLW-08 | C | F03/F08 | API/integration | API | auto | A/B 用户、daily/wealth Profile、两个 conversation | 伪造会话/module/profile/user，跨模块 resume | run/resume/GET | 绑定必须与可信 principal 和会话一致；daily 写仅在 daily Profile；响应不含另一会话/模块内容 | P0 | not_run |

#### 故障、取消、权限和 UI 数据

| ID | 切片 | 需求/冻结来源 | 层级 | 环境 | 自动/人工 | 前置条件 | 输入摘要 | 步骤 | 预期结果与禁止副作用 | 风险 | 执行状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P4C-FLT-01 | C | P2模型失败 | API/integration | SQLite | auto | 假 provider | timeout/auth/rate limit/invalid response 在候选前发生 | 提交消息并重试 | 稳定分类和有界重试；无 pending/财务事实；恢复后同 ID 不重复执行已完成阶段 | P1 | not_run |
| P4C-FLT-02 | C | P4-C故障 | desktop/e2e | Windows/Electron | auto | 假慢工具与可停后端 | 工具超时、后端离线、恢复 | 发送/离线/恢复重试 | UI 显示安全可恢复状态；复用 client_event_id；无半写、重复候选或内部异常泄露 | P0 | not_run |
| P4C-FLT-03 | C | F04/F07 | API/integration | PostgreSQL | auto | 候选创建时有写权限 | 确认前撤销 permission/session/module | 并发撤销与确认 | 执行时授权门生效；失权确认零财务写；若事务已取得提交权则按冻结线性化点返回真实结果 | P0 | not_run |
| P4C-FLT-04 | C | F06；P2 stale | database | PostgreSQL | auto | 候选引用账户/分类版本 | 确认前归档/改版本 | 确认并 GET | 返回 stale/重新查询，不提交；原候选保留可审计状态，不自动换目标 | P0 | not_run |
| P4C-FLT-05 | C | F14；P1事务 | database | PostgreSQL | auto | 可在 receipt/header/entry/audit/event 点故障 | 每个点注入异常 | 确认并查询全部表 | 领域事务内任一点失败全回滚且可同键恢复；post-commit event 失败不回滚已提交账 | P0 | not_run |
| P4C-FLT-06 | C | P2最终文案失败 | API/integration | SQLite | auto | FinanceService 已 committed | 最终模型/渲染失败、响应丢失 | 重试 run/GET | 结构化 committed 结果可恢复且只写一次；不得把文案失败显示成记账失败或再次写 | P0 | not_run |
| P4C-FLT-07 | C | F10；条件 SSE | API/integration | API | auto | 仅在实现 SSE 时适用 | 断线、Last-Event-ID、token/event 重放、慢客户端、取消 | 重连并最终 GET，检查连接资源 | 事件 ID/恢复规则稳定，最终 GET 权威；无重复工具/写入、连接/任务泄漏；未实现 SSE 时标 `not_applicable` 而非失败 | P1 | not_run |
| P4C-UI-01 | C | P4-C金额显示 | desktop/e2e | Windows/Electron | auto | snapshot DTO 全为整数分 | 0.01、18.00、超大合法值、负向更正 | 渲染卡片/图表/列表/详情并交叉核对 | 全部从确定性 minor 格式化，无 float 误差；各视图同一金额与币种 | P0 | not_run |
| P4C-UI-02 | C | P4-C UI边界 | desktop/e2e | Windows/Electron | auto | 空库、仅退款/冲销、负净流虚拟月 | 空状态和负向数据 | 打开 dashboard 与详情 | 空状态不伪造0趋势；负向更正语义明确；不把退款计收入或转账计消费 | P1 | not_run |
| P4C-UI-03 | C | P1月度口径 | API/integration | SQLite | auto | Asia/Shanghai 月界前后虚拟交易 | UTC/月末、跨月退款、DST无关输入 | 请求 snapshot 并渲染 | 按 Asia/Shanghai 归月且与 P1 快照一致；前后端不各自重算成不同月份 | P0 | not_run |
| P4C-UI-04 | C | P4-C大列表 | desktop/e2e | Windows/Electron | auto | 超过页面限制的虚拟交易 | 分页/滚动、稳定同时间戳、筛选、刷新 | 连续加载并去重 | 稳定排序、无遗漏/重复，明确截断/分页；不一次把全库或未授权数据载入 renderer | P1 | not_run |
| P4C-UI-05 | C | F13/F14；隐私 | desktop/e2e | Windows/Electron | auto | committed 事件、隐私模式、离线切换 | 写成功、事件丢失、手动刷新 | 观察 dashboard/毛毛/通知 | 事件只提示刷新，GET snapshot 最终收敛；毛毛切确认→idle；隐私模式不显示金额；事件丢失不改变事实正确性 | P1 | not_run |

### 5.4 P4-D：第二模块扩展性证明（12 项）

| ID | 切片 | 需求/冻结来源 | 层级 | 环境 | 自动/人工 | 前置条件 | 输入摘要 | 步骤 | 预期结果与禁止副作用 | 风险 | 执行状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P4D-EXT-01 | D | F16证明1 | API/integration | API | auto | 仅在 builtin 列表加入 `wealth_management()` | `/modules`、桌面 registry、设置、毛毛 contribution | 注册并读取各贡献 | API/导航/设置/毛毛主形态自动出现；Host/Shell 无 wealth ID 业务分支或远程代码加载 | P1 | not_run |
| P4D-EXT-02 | D | F16证明2 | API/integration | API | auto | wealth Profile 可用 | 通用 run API 指定 wealth conversation | 创建/恢复 run 并枚举路由 | 使用同一通用端点和状态模型；不得新增 `/wealth-agent-chat` 或专用身份旁路 | P1 | not_run |
| P4D-EXT-03 | D | F16证明3/F04 | contract/unit | contract | auto | wealth 只授予 snapshot/计算只读工具 | Schema 检视并猜 `finance_record_expense` canonical/alias | 分别可见性与直接执行 | 写工具不可见且执行拒绝；无 pending、receipt、ledger 或 audit 写入 | P0 | not_run |
| P4D-EXT-04 | D | F16证明4/F09 | database | SQLite | auto | shared、wealth、daily 各有记忆 | wealth 读 shared/wealth，读写 daily，提议 shared | 检索/候选/确认 | 仅 shared.confirmed 与 wealth.confirmed 可读；daily 专属读写失败；共享仍需用户确认 | P0 | not_run |
| P4D-EXT-05 | D | F16证明5 | API/integration | SQLite | auto | daily 与 wealth 均有设置/会话/数据 | 禁用 wealth | 查询模块贡献并运行 daily 回归 | wealth 导航/Profile/工具/设置/毛毛映射全部消失；daily 数据、迁移、行为与会话不变 | P0 | not_run |
| P4D-EXT-06 | D | F16证明6/F02 | contract/unit | contract | auto | 可构造冲突 contribution | route、tool alias、profile、namespace、setting key 冲突 | 逐类启动注册 | 每类稳定阻止启动且定位双方；不得覆盖、自动改名或部分启用 | P1 | not_run |
| P4D-EXT-07 | D | F16证明7 | security/manual | contract | auto | 依赖规则工具可扫描 import graph | wealth 页面/adapter 直接 import daily repository/internal model/session | 静态依赖门禁与假公开 port 测试 | 非法 import 使门禁失败；wealth 只依赖公开 snapshot port/DTO，不取得万能 Session | P0 | not_run |
| P4D-EXT-08 | D | F16证明8/F15 | database | PostgreSQL | auto | 空 schema 与 P0～P3 历史库 | 升级/允许降级、跨用户 snapshot、同键并发 | 随机 schema 执行并核对 | 单 Alembic head；数据保持；user 隔离/unique/并发真实生效；wealth 不创建不必要事实表 | P0 | not_run |
| P4D-CAL-01 | D | F16；U07 | contract/unit | contract | auto | 冻结固定虚拟 fixture 与公式 | current/target/monthly expense 正常值 | 调用确定性只读计算 | 精确输出 `current_minor/target_minor/gap_minor/months_of_expense/data_as_of`，整数金额且可复算 | P1 | not_run |
| P4D-CAL-02 | D | F16；U07 | API/integration | SQLite | auto | snapshot port 可返回缺项 | 缺余额、目标、月支出、陈旧 as_of | 调用工具/页面 | 明确缺失/数据日期，不猜值、不除零、不让模型补金额；无写入 | P1 | not_run |
| P4D-CAL-03 | D | F16；U07 | contract/unit | contract | auto | 公式与舍入待冻结后绑定 | 0、负值、target=current、current>target、极大值、零月支出 | 参数化计算 | 边界按唯一规则返回/拒绝，无 float/溢出/负月数；gap 不被静默截错 | P1 | not_run |
| P4D-CAL-04 | D | F16；U07 | security/manual | API | auto | 监控所有工具/表/网络 adapter | 正常与缺失 fixture、诱导买股/交易/改目标 | 运行 wealth Agent 和页面动作 | 不接行情、不写账/目标、不推荐证券、不调用网络；只解释确定性虚拟结果和限制 | P0 | not_run |

## 6. 执行方与独立测试所有权

路径在正式接口冻结时最终确认；以下划分用于防止双方修改同一测试或把执行方自测当成独立证据：

| 所有者 | 建议路径 | 职责 |
|---|---|---|
| 执行智能体 | `tests/host/**`、`tests/modules/daily_finance/**`、`tests/modules/wealth_management/**`、`apps/desktop/**` 内的单元/组件/E2E 测试，以及必要的既有执行方回归 | 随实现提交合同、单元、API、迁移、桌面组件和最小冒烟；自测只能到 `review` |
| 测试智能体 | `tests/independent/host/**`、`tests/independent/desktop/**`、`tests/independent/modules/**`、未来 P4 独立报告和本矩阵 | 在固定快照上实现权限反例、并发、故障、迁移、恢复、Windows 人工检查和最终回归；独立给出通过/失败/阻塞 |
| 共享只读基线 | 现有 `tests/independent/**`、`tests/finance/**`、`tests/agent_finance/**`、`tests/activity_import/**` | P4 执行期只作为兼容证据；任何改动必须在任务卡中单列所有者、理由和新快照，不能为通过 P4 而放宽旧断言 |

测试智能体发现产品缺陷时只提交最小虚拟复现、预期、实际、严重级别、影响范围和脱敏证据；没有返修授权不得改产品。执行智能体不得修改独立路径或本矩阵。

## 7. P0～P3 最终回归集合

P4 的 user scope、Host adapter 和 migration 会横切旧功能，因此最终验收需要一次合并回归，但不重新设计已经通过的全部业务案例。

| 门禁 | 建议执行集合 | 目的 |
|---|---|---|
| P0 Agent/HTTP 本地 | `tests/independent/test_c2_b1_core_contract.py`、`test_c2_b1_provider_cli.py`、`test_c2_b2_api.py`、`test_c2_b2_probe_api.py`，以及对应执行方 P0 测试 | 保留工具循环、错误、日志、探针健康与 HTTP 幂等；全部使用假 provider/本地 HTTP |
| P1 财务本地 | `tests/independent/finance/**` 排除 PostgreSQL 文件，及 `tests/finance/**` | 保留金额、ledger、转账、退款、收入、预算、快照、SQLite 迁移和隐私 |
| P2 Agent 财务本地 | `tests/independent/agent_finance/**` 排除 PostgreSQL 文件，及 `tests/agent_finance/**` | 保留候选/确认、24 小时、上下文、工具、HTTP、恢复和可控时钟 |
| P3 活动导入本地 | `tests/independent/activity_import/**` 排除 PostgreSQL 文件，及 `tests/activity_import/**` 排除 PostgreSQL 文件 | 保留离线解析、持久预览、原子导入、严格 API 和 SQLite migration |
| PostgreSQL 合并门禁 | 三个既有独立 PostgreSQL 文件，加上 P4 user scope/migration/并发独立文件及必要执行方 PostgreSQL 文件 | 真实验证迁移链、复合 FK、跨用户隔离、同键并发、确认一次一写与 P3 导入；按目录分进程运行以避免 fixture 冲突 |
| 迁移链 | P1/P2/P3 现有迁移测试 + P4 空库/已有 P0～P3 数据升级与允许降级 | 单 Alembic head、数据保持、回填和恢复 |

真实 DeepSeek、OpenClaw、微信扫码/消息和 W1 手机实收不重复执行。它们保留既有报告作为历史证据；P4 只用假 provider、假渠道 adapter 和虚拟外部身份验证 Host 合同。不得访问付费 API、真实凭据或真实个人资料。OpenClaw 安全事件恢复仍以未来控制文件为准。

## 8. 停止条件与缺陷门禁

出现以下任一项立即停止扩大执行，关闭本任务启动的资源并提交最小脱敏复现：

- 固定快照不匹配、控制文件更换负责人或实现差异超出该切片交接范围；
- 任意跨用户财务、会话、记忆、设置、run/pending/receipt/audit 可读写，或客户端/模型能够覆盖可信身份；
- 一个 client event/确认产生两笔财务事实、事务失败留下半写、旧事实被覆盖或余额/快照不再可由 ledger 推导；
- migration 丢失/重归属 P0～P3 数据、产生多 head、留下不可恢复半迁移或无法在干净随机 schema 重现；
- 密码、原始 token/API Key、外部身份、个人内容、SQL 参数或未授权财务数据进入响应、日志、事件、prompt、renderer storage 或 crash 输出；
- Electron renderer 获得 Node/进程/密钥能力，IPC sender/参数校验可绕过，或 supervisor 停止非自有进程；
- disabled/wealth 模块仍能调用 daily 写工具或读取 daily 专属记忆，事实数据被复制为记忆，或事件成为事务正确性的唯一依赖；
- 目标 Windows 出现无法清理的自有后端/僵尸进程，或连续两个检查点没有新证据。

上述数据损坏、越权、重复写和秘密泄露默认为 P0；核心闭环/恢复/桌面安全失效默认为 P1。P0/P1 未关闭时不得进入下一切片或建议总控接受。普通断言失败可继续同层收集，但不得用重试成功掩盖首次可复现失败。

## 9. 正式接口冻结仍需明确

以下内容不能由测试矩阵自行决定；冻结后应把唯一值绑定到相应条件案例：

1. manifest/profile/tool/event/setting/UI contribution 的完整字段、canonical ID/alias/route/namespace 语法、长度、SemVer 和 Host API/UI major 不兼容时是禁用还是阻止启动。
2. Host 全局与 Profile 的模型轮次、总工具、写工具、provider/tool 超时、取消检查点、成本上限及稳定停止/错误码。
3. 主人账户初始化窗口的“本机”判定、handle/password 规则、Argon2id 库/参数/升级策略、登录速率限制与账户停用行为。
4. access/refresh 或不透明 token 的形式、TTL、轮换族、并发刷新线性化点、重放响应、logout/改密/设备撤销范围，以及 Electron main 与 renderer 的持有边界。
5. 渠道绑定码 TTL、最大尝试、摘要/HMAC 域、消费线性化点、外部身份冲突和解绑后的重新绑定/审计策略；不恢复真实微信运行。
6. `PrincipalContext`、user scope 根/子表清单、复合 FK/unique 方案、bootstrap owner 规则、旧 `actor_id/owner_id` 兼容期限和幂等 domain。
7. 通用 run/pending schema、六状态转换、lease 时长/接管条件、取消的事务线性化点、响应丢失查询合同和稳定错误/HTTP 映射。
8. conversation/message/memory candidate/item 的值 schema、敏感等级、替代链、tombstone 保留内容、90/30 天恰好到期算法、检索排序/tag 和最多 8 条的计数方式。
9. Host API 的精确 URL/DTO/Idempotency-Key 适用面、分页/limit/as_of、统一错误 envelope、新旧 P2/P3 compatibility facade 的存续期限。
10. P4 migration revision 顺序、owner 标识、分批回填策略、非法孤儿/重复的诊断、SQLite 与 PostgreSQL 允许的 downgrade/rebuild 边界。
11. OpenAPI TypeScript 生成器与版本、前端 router/state/chart 选择、Node/Electron/React/TypeScript 版本、构建锁文件、CSP/origin/nonce/外链 allowlist 和 IPC channel 清单。
12. BackendSupervisor 启动命令白名单、ready 信号、随机端口交接、超时、重启次数/退避、PID+nonce ownership 和正式/开发 connection profile。
13. 设备设置 JSON 版本与原子保存路径、关闭/Tray/全屏/多屏夹取细节、开机启动实现、透明窗口失败判定、目标 Windows/显示器/缩放测试组合。
14. 主题语义 token、high-contrast/reduced-motion 门槛、行情色配置与收入/支出色的可访问性验收值。
15. post-commit EventEnvelope 的允许类型/版本/payload 白名单、同步/异步 handler 顺序、失败记录和重复提示处理；明确首版不作可靠投递。
16. P4-C 固定虚拟账户/分类/交易数据、dashboard DTO/刷新条件、候选纠正 API、已入账错误允许的领域动作，以及条件 SSE 的事件 ID、Last-Event-ID、背压和清理合同。
17. wealth 固定 fixture 的精确数值、应急金目标/月份公式、舍入/零负边界、`data_as_of` 陈旧阈值和缺失字段错误；确认没有目标写 API、行情或证券推荐。
18. 每个切片的执行方/独立测试最终路径、快照算法、真实 PostgreSQL 与 Windows 资源负责人、支持的依赖版本和最终回归命令。

## 10. 计数与质量检查

### 10.1 按切片

| 切片 | 案例数 |
|---|---:|
| P4-A | 64 |
| P4-B | 24 |
| P4-C | 20 |
| P4-D | 12 |
| **合计** | **120** |

### 10.2 按层级

| 层级 | 案例数 |
|---|---:|
| contract/unit | 24 |
| API/integration | 41 |
| database | 23 |
| desktop/e2e | 18 |
| security/manual | 14 |
| **合计** | **120** |

### 10.3 按环境

| 环境 | 案例数 |
|---|---:|
| contract | 27 |
| API | 19 |
| SQLite | 32 |
| PostgreSQL | 16 |
| Windows/Electron | 24 |
| external/manual | 2 |
| **合计** | **120** |

### 10.4 按风险与执行方式

| 维度 | 值 | 案例数 |
|---|---|---:|
| 风险 | P0 | 76 |
| 风险 | P1 | 43 |
| 风险 | P2 | 1 |
| 风险 | P3 | 0 |
| 方式 | auto | 116 |
| 方式 | manual | 4 |

结构质量要求：120 个 ID 必须唯一；每行恰好包含任务卡要求的 12 个字段；执行状态必须全部为 `not_run`；F01～F17、U01～U07、P4-D 八项证明和任务卡所有强制范围都必须至少映射一个案例。当前文档没有执行时间、通过率或未来实现快照摘要。

## 11. 本任务未测试范围

- 未运行任何现有或新测试，未启动 FastAPI、SQLite/PostgreSQL 服务、Docker、Electron、DeepSeek、OpenClaw 或微信。
- 未安装依赖、登录外部服务、访问网络、读取密钥或使用真实个人/财务/渠道数据。
- 未选择 OpenAPI 生成器、前端 router/state/chart、SSE 实现、Electron 打包工具或 MCP SDK；案例只约束与实现无关的合同。
- 未实现 P4 产品、migration、桌面应用、独立测试、财富规划、行情、交易、证券推荐、公众注册、远程多端、第三方插件市场、自动更新或发布签名。
- 未执行 Git 写操作；本矩阵只能提交 `review`，正式冻结、实现派发、最终 `complete` 和 Git 处理均属于头脑风暴总控。
