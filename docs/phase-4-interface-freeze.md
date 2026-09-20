# P4-IF-001：模块化 Personal AI Host 接口冻结

- 冻结编号：`P4-IF-001`
- 冻结时间：2026-09-20 18:14，Asia/Shanghai
- 总控负责人：头脑风暴智能体
- 输入：[P4-D9 技术方案](phase-4-d9-modular-agent-host-advice.md)、[P4-C10 测试矩阵](testing/phase-4-modular-agent-host-test-matrix.md)、[P2 接口冻结](phase-2-interface-freeze.md)、[P3 接口冻结](phase-3-interface-freeze.md)
- 第一实现任务：`P4-B6`，仅实现 P4-A Host、身份和通用状态地基
- 后续独立验收：`P4-C11`，绑定 B6 固定快照执行 P4-A 的 64 项及兼容回归

本文是 P4 的总架构边界和 P4-A 的唯一实现合同。D9 提供方案理由，C10 提供验收设计；与本文冲突时以本文为准。P4-B Windows Shell、P4-C 日常财务桌面闭环和 P4-D 财富管理扩展证明只冻结产品方向，依赖和详细接口在各切片开始前补充，P4-B6 不得提前实现。

## 1. 总体架构与阶段边界

1. P4 使用可信内置模块的 FastAPI/SQLAlchemy 模块化单体。模块由 Python factory、严格 manifest 和唯一显式组合根注册；不扫描目录，不加载用户提供的 import path，不安装未知插件。
2. 逻辑 Agent 由版本化 Profile 定义。Profile 决定提示词、工具授权、记忆授权、限额和评测套件；不同 Profile 不等于独立进程或独立模型。
3. Agent 负责理解、选择工具和解释；workflow 负责候选、确认、暂停恢复和重试；金额、事务、幂等、身份、权限和最终事实由确定性程序负责。
4. 现有 `AgentRunner`、`ToolRegistry`、`AgentApplication`、`pending_action` 和 `FinanceService` 通过 adapter 演进。P4-A 不移动现有包，不重写财务核心，不把内部财务工具改成 MCP。
5. P4-A 不引入 LangGraph、LangChain、向量数据库、消息队列、微服务、第三方插件运行时或 WebSocket。MCP 只保留未来外部工具 adapter 接口，不是 P4-A 交付项。
6. P4-A 提供 Host 合同、模块注册、主人账户、设备会话、渠道绑定合同、可信用户作用域、通用 run/pending 元数据、会话、结构化记忆、模块设置和 Host API。
7. P4-A 不包含 Electron/React、Tray、毛毛、主题、图表、真实微信、OpenClaw 恢复、DeepSeek 在线调用、行情、交易、证券推荐或真实个人数据迁移。
8. `wealth_management` 在 P4-A 只可作为测试 manifest/fixture 验证通用注册，不进入 builtin 生产组合根。正式只读模块在 P4-D 实现。

## 2. 模块、Profile 和工具合同

### 2.1 ID 和版本

- `module_id`：`^[a-z][a-z0-9_]{0,63}$`，首个生产值为 `daily_finance`。
- 局部名称：`^[a-z][a-z0-9_]{0,63}$`。
- canonical Profile ID：`{module_id}.{local_name}@{major}`，例如 `daily_finance.assistant@1`。
- canonical Tool ID：`{module_id}.{local_name}@{major}`，例如 `daily_finance.record_expense@1`。
- 模型可见 tool alias 继续允许现有 `finance_record_expense` 等名称，格式同局部名称；alias 必须由 manifest 显式声明。
- memory namespace：`shared.confirmed` 或 `{module_id}.confirmed` / `{module_id}.candidates`。P4-A 不允许通配 namespace。
- module `version` 使用完整 `MAJOR.MINOR.PATCH` 十进制 SemVer，P4-A 不接受 prerelease/build 后缀；`host_api_major=1`。
- 所有 ID、alias、route/API prefix、namespace 和 setting key 按原始 ASCII 精确比较；不静默小写、去空白、NFKC 或自动改名，格式不符直接拒绝。

### 2.2 manifest 与启动

`ModuleManifest` 至少包含：`module_id/version/host_api_major/display_name/enabled_by_default/profiles/permissions/api_prefixes/memory_namespaces/settings_schema_version/published_events/subscribed_events/migration_owner`。运行时 `ModuleDefinition` 另持有 router、tool、service 和 UI manifest factory；callable 不得进入可序列化 manifest。

唯一组合根显式注册 builtin factory。出现重复 module/Profile/canonical tool/alias/API prefix/namespace/setting key、非法字段、未知权限或 Host API major 不匹配时，应用进入 `not ready` 并以稳定启动错误终止；不得覆盖、部分注册或因用户禁用而忽略无效 manifest。

P4-A 的 `GET /api/v1/modules` 只返回当前用户已启用且已编译模块的安全摘要，不返回提示词、factory、密钥、内部 import path 或完整权限策略。

### 2.3 Profile 和工具授权

有效系统上下文顺序固定为：Host 安全规则 → Profile 版本化提示词 → 可信身份/渠道/页面摘要 → 获准的最多 8 条记忆 → 最新工具事实。用户消息、记忆值、Markdown、搜索结果和工具内容都属于不可信数据，不能覆盖前面的规则。

Host 全局硬上限保持现有值：

| 限制 | 全局值 | Profile 规则 |
|---|---:|---|
| 模型轮次 | 4 | `1..4` |
| 总工具调用 | 8 | `1..8` |
| 写工具调用 | 1 | `0..1` |
| provider 单次超时 | 15 秒 | `1..15` 秒 |
| 进程内工具单次超时 | 10 秒 | `1..10` 秒 |
| retryable provider 重试 | 1 次 | 不可增加 |

P4-A 不冻结金额形式的模型成本上限；字段可为空，后续有真实调用统计再启用。超限沿用或增加稳定码：`max_model_turns_exceeded`、`tool_limit_exceeded`、`write_limit_exceeded`、`model_timeout`、`tool_timeout`、`cancelled`。

10 秒工具限制是 cooperative deadline：在 handler 前后、数据库语句和外部 adapter 检查，不用后台线程强行终止正在提交的同步财务事务。事务已经进入领域提交时，以真实 committed/rolled-back 结果为准，不能把客户端超时解释为安全取消。

工具授权有三层：Profile grant + 当前 principal permission + 模块启用状态决定 Schema 可见性；执行时按 canonical ID 重查同样条件；领域 adapter 再检查资源用户作用域和确认策略。猜到隐藏 canonical ID 或 alias 仍返回 `tool_not_allowed`，不得执行 handler。

## 3. 主人账户和认证

### 3.1 bootstrap owner

P4-A migration 在每个数据库创建唯一 `pending_setup` bootstrap owner，并把所有 P0～P3 历史业务数据回填给该用户。`GET /api/v1/auth/bootstrap-status` 只返回 `needs_initialization: bool`，不泄露 handle 或用户 ID。

初始化条件同时满足：bootstrap owner 仍为 `pending_setup`、没有 credential、请求来自 loopback、请求携带配置注入的 `X-Bootstrap-Token`。token 至少 32 个随机字节，只存在进程配置和调用方安全内存，不落库、不入日志、不进入 renderer。并发初始化只有一个成功，其余返回 `already_initialized`。

主人账户规则：

- handle 去首尾空白后转小写；格式 `^[a-z][a-z0-9_]{2,31}$`，数据库唯一。
- password 原文不 trim、不规范化；长度 12～128 个 Unicode code point；拒绝 NUL、C0/C1 控制字符和孤立代理项，不要求固定字符组合。
- P4-A 不提供公众注册、找回密码或管理员创建第二用户。

### 3.2 密码和登录

密码使用 `pwdlib[argon2]` 的 Argon2id，参数固定为 memory 65,536 KiB、time cost 3、parallelism 1、salt 16 bytes、hash 32 bytes。数据库只存编码后的 hash 和算法/更新时间；成功登录发现参数过旧时在同一安全流程中 rehash。

登录失败统一返回 `invalid_credentials`，不区分 handle 不存在、密码错误、账户停用或未初始化。单进程按 `(handle_normalized, client_fingerprint)` 记录失败：5 分钟内第 5 次失败后冻结该组合 15 分钟，返回 `login_rate_limited` 与安全 `Retry-After`；P4-A 明确只保证本地单进程限速，未来公网部署前必须替换为共享限速。

### 3.3 设备会话

- access token 与 refresh token 均为 256-bit CSPRNG 不透明值，base64url 无填充。
- access TTL 15 分钟；refresh/device session 绝对 TTL 30 天，不滑动延长。
- 数据库存 token SHA-256 digest，不存原值；原值只在 login/refresh 成功响应出现一次。
- access token 使用 `Authorization: Bearer`；refresh token 只进入 refresh body，由 Electron main/未来安全客户端持有，禁止 localStorage、日志和记忆。
- refresh 在数据库事务中轮换 access/refresh digest 和 rotation counter；同一旧 refresh 并发时只有一个成功。旧 token 再用返回 `session_refresh_replayed`，并撤销该 session family。
- logout 撤销当前 session；设备撤销立即使其 access/refresh 失效；账户停用撤销全部 session。
- 改密必须验证旧密码，更新 hash、撤销全部旧 session，并为当前设备签发一个新 session pair。
- `device.name` 1～80 字符；platform 首版仅 `windows_desktop` 或 `api_test`。每个主人最多 10 个 active device session，超过时拒绝新登录并要求用户先撤销。

认证错误不得回显 token、digest、密码、hash、SQL 或内部异常。跨用户资源无论是否存在统一返回 404。

## 4. 渠道绑定合同

P4-A 只实现假渠道 adapter 可验证的绑定服务和 API，不启动微信/OpenClaw。

- 已登录主人生成 `XXXX-XXXX` 一次性码；字符集使用去除 `0/O/1/I` 的大写 Crockford Base32，共 40 bit 随机量。
- 绑定码 TTL 10 分钟，最多 5 次失败尝试；在 `now >= expires_at` 时过期。
- 数据库只存 HMAC-SHA-256 digest；domain 固定为 `wife.channel-binding.v1`，key 从部署 secret 注入，原码只在创建响应出现一次。
- 可信 adapter 输入 `channel/provider_account/external_subject/code`；外部标识分别做带 domain 的 HMAC 后保存，原值不落普通业务表、日志、模型上下文或响应。
- HTTP consume 入口要求独立的 `X-Channel-Adapter-Token`，其值至少 32 个随机字节并由进程配置注入；只比较摘要/常量时间，不把它当主人 session 或交给模型。缺失或错误统一返回 401 `channel_adapter_unauthorized`。
- 消费码、检查过期/尝试次数和创建 active binding 在一个事务中；并发消费只有一个成功。
- 同一 `(channel, external_subject_digest)` 最多一个 active binding。冲突返回 `channel_identity_conflict`，不自动抢占。
- 解绑把 binding 置为 revoked 并写脱敏审计；新绑定码可重新绑定已撤销身份。审计保留 digest、时间、动作和内部 user，不保留原始身份。

## 5. 可信用户作用域迁移

### 5.1 覆盖表

P4-A 给所有业务和状态表增加非空 `user_id`。至少覆盖：

- 根/事实：`account`、`category`、`command_receipt`、`audit_event`、`financial_transaction`、`activity_template`、`activity_import_batch`、`activity_occurrence`、`income_schedule`、`income_expectation`、`budget_plan`、`agent_run`、`pending_action`。
- 子表：`transaction_entry`、`activity_template_revision`、`activity_import_candidate`、`activity_entry_allocation`、`income_schedule_version`、`income_expectation_match`、`budget_version`、`budget_allocation`。
- P4 新表：credential、device/session、binding、conversation/message、memory candidate/item 和 module setting。

所有 repository/query/command 必须从可信 `PrincipalContext.user_id` 取作用域；API body、模型参数、tool JSON 和普通设置不得接受 owner/user 字段。父表提供 `(user_id,id)` 唯一键，跨事实/用户敏感引用使用包含 `user_id` 的复合外键，不能只依赖应用层过滤。

幂等唯一域改为 `(user_id, source_system, key_digest)`；HMAC domain 包含 user ID。所有 P0～P3 既有行回填给 bootstrap owner，并校验行数、空值、孤儿和关系一致性。

旧 `actor_id` 和活动导入 `owner_id` 保留为兼容列直到 P4-C 验收，写入时必须等于 `user_id`；新代码以 `user_id` 为语义源。测试 app 可通过显式 fixture 注入 principal，生产入口不得使用固定虚拟身份。

### 5.2 migration 顺序与降级

保持一个 Alembic linear head，采用三个连续 revision：

1. `p4_host_identity`：owner、credential、device/session、binding，创建 pending bootstrap owner。
2. `p4_host_user_scope`：先加 nullable user、回填、校验，再增加复合 unique/FK 和非空；SQLite 使用受控 batch rebuild，PostgreSQL 使用真实约束。
3. `p4_host_state`：conversation/message、memory、setting，以及 run/pending 的 module/profile/schema/lease 字段。

空库和带 P0～P3 虚拟历史数据都必须升级。允许测试数据库从 P4-A head 降到 P3 head：P0～P3 业务事实必须保持，P4-only 账户凭据、session、绑定、会话和记忆会被删除；真实个人数据尚未启用，因此 P4-A 不承诺生产数据降级。出现孤儿、矛盾 owner 或无法安全回填时 migration 失败并给出不含数据内容的诊断，不猜测修复。

## 6. Principal、run 和 pending 状态

`PrincipalContext` 至少包含：`user_id/session_id/device_id/channel/permissions/authenticated_at`。`HostRunContext` 在此基础上增加 `agent_run_id/conversation_id/module_id/profile_id/source_system/source_event_id/received_at/pending_action_id/approval_grant_id`。二者均 `extra="forbid"`、不可变、只由可信入口构造，不进入模型工具 Schema。

P4-A 给 `agent_run` 增加 `user_id/module_id/profile_id/profile_version/attempt_no/lease_expires_at/action_schema_version`；给 `pending_action` 增加 `user_id/module_id/profile_id/action_schema_version`。现有六个 pending 状态保持不变。

- run lease 固定 60 秒，在模型请求前后和工具调用前后续租；provider 15 秒、工具 10 秒必须短于 lease。
- 同一用户/来源事件的 `running` lease 过期后，可由另一个 worker 原子接管并把 `attempt_no + 1`；最多 3 次 attempt，之后为稳定错误 `run_attempts_exhausted`。
- 普通 pending TTL 24 小时；`now >= expires_at` 即过期。确认用 `status + version_id` CAS 争夺 `committing`。
- 取消只能把尚未进入 `committing` 的 run/pending 变为 cancelled；一旦 CAS 进入 committing，取消返回 `commit_in_progress`，最终由 GET 返回 committed 或真实失败。
- 领域写继续使用 `pending:{pending_action_id}:commit` 派生键。响应丢失、重启和重复确认必须查询或重放同一 run/pending/receipt，不生成新写键。
- payload 由注册的 `ActionHandler` 按 `action_schema_version=1` 验证；Host 不提供解释任意 JSON 的通用写入口。

## 7. 会话和分层记忆

### 7.1 会话

conversation 以 `(user_id, channel, module_id, profile_id)` 隔离；切换模块恢复该模块最近会话，不自动把其他模块完整历史放入上下文。message 保存 role、content、content digest、sensitivity 和时间；不保存模型思维过程、工具密钥或未脱敏异常。

- 单条 message UTF-8 最大 32 KiB；conversation 默认消息保留 90 天。
- `now >= created_at + 90 days` 的 message 不可检索；清理服务清空正文并保留最小 tombstone。
- P4-A 不做后台 scheduler；每次读取前执行到期过滤，提供可测试的 retention service，实际定时清理由后续运行维护切片加入。

### 7.2 记忆

首版 kind 只允许 `preference`、`constraint`、`goal`、`communication_style`；`value_json` 必须是严格对象，规范 JSON 最大 4 KiB。sensitivity 只允许 `private`、`restricted`。财务事实、余额、预算、持仓、行情、密码、token、API Key 和原始外部身份不得进入记忆。

- candidate 默认 30 天；`now >= expires_at` 为 expired。状态为 pending/confirmed/rejected/expired。
- confirmed memory 保留到用户删除、显式失效或被新 item supersede；共享 namespace 只能由显式确认产生。
- 模块 candidate 晋升共享时必须返回来源摘要、目标 namespace、敏感等级和到期信息，并在一个事务中更新 candidate、创建 item 和审计。
- 删除敏感记忆时把 `value_json` 设为空，保留 id/user/namespace/kind/source digest/status/version/created/deleted/superseded_by 和审计 ID；tombstone 不含正文。
- 检索先按 user、Profile grant、namespace、active、未过期和 kind/tag 过滤；排序为匹配 tag 数降序、confirmed_at 降序、id 升序；最终数量为 Profile limit 与 8 的较小值。
- P4-A 使用关系数据库确定性检索，不生成 embedding，不使用向量数据库。

## 8. 模块设置和事件

module setting 的唯一键为 `(user_id,module_id,key)`；key 使用局部名称格式。值为模块 schema 验证后的 JSON，规范形式最大 8 KiB，带 `schema_version` 和 `version_id` 乐观锁。API Key 和设备窗口设置不属于 module setting。

P4-A 进程内事件只允许：`agent.run_status_changed@1`、`memory.changed@1`、`module.setting_changed@1`、`auth.session_revoked@1`。`EventEnvelope` 包含 event ID/type/version/time/user/producer module/correlation/idempotency digest/sensitivity/最小 payload。

事件只在事务提交后按注册顺序同步发布，用于刷新提示；handler 失败写脱敏诊断但不回滚业务事务，不自动重试。消费者必须容忍重复提示并重新 GET 权威事实。P4-A 不提供可靠投递、outbox 或 broker。

## 9. P4-A HTTP API

### 9.1 端点

冻结以下 `/api/v1` 端点：

| 范围 | 端点 |
|---|---|
| bootstrap/auth | `GET /auth/bootstrap-status`；`POST /auth/initialize`；`POST /auth/login`；`POST /auth/refresh`；`POST /auth/logout`；`POST /auth/password/change` |
| session | `GET /auth/sessions`；`DELETE /auth/sessions/{session_id}` |
| binding | `POST /channel-bindings/codes`；`POST /channel-bindings/consume`（可信 adapter）；`GET /channel-bindings`；`DELETE /channel-bindings/{binding_id}` |
| modules | `GET /modules`；`GET /modules/{module_id}` |
| conversation | `POST /conversations`；`GET /conversations`；`GET /conversations/{id}`；`GET /conversations/{id}/messages` |
| Agent | 保留 `POST /agent/runs`、`POST /agent/runs/{id}/resume`、`GET /agent/runs/{id}`，增加服务端绑定的 conversation/module/profile |
| memory | `GET /memories`；`DELETE /memories/{id}`；`GET /memory-candidates`；`POST /memory-candidates/{id}/confirm`；`POST /memory-candidates/{id}/reject` |
| settings | `GET /settings/{module_id}`；`PUT /settings/{module_id}` |
| health | `GET /healthz`；`GET /readyz` |

`healthz` 只说明进程存活；`readyz` 必须检查数据库连接、Alembic head 和 module registry，有一项失败返回 503 `backend_not_ready`。

### 9.2 通用 HTTP 规则

- Pydantic request/response 均 `extra="forbid"`；JSON UTF-8；不接受 body 自报 user、owner、permission、session、module/profile ownership。
- 状态改变的 initialize、绑定码创建/消费、conversation 创建、memory confirm/reject/delete 和 setting PUT 要求 `Idempotency-Key`。去空白后为 1～128 个可打印 ASCII 字符；原值不落库，同键异载荷返回 `idempotency_conflict`。
- Agent create 继续使用稳定 `client_event_id`；resume 使用 pending/run 身份和动作版本，不另造随机写键。
- 列表 limit 默认 50，范围 1～100；稳定排序使用时间降序、UUID 升序。cursor 是不透明、带 HMAC 的 base64url 排序元组，最长 512 字符；无效或跨 endpoint/user 使用返回 `invalid_cursor`。
- 所有成功对象包含稳定 ID 和相关时间；时间为带时区 ISO 8601 UTC，展示层再转 Asia/Shanghai。
- 错误包络保持 `{request_id,error:{code,message,retryable}}`。验证 422；未认证 401；无权限 403；跨用户/不存在 404；幂等/版本/状态冲突 409；过期 410；限速 429；依赖不可用 503。
- 响应和日志不得包含密码/token/hash/digest、原始绑定码/外部身份、完整 message/memory 内容、SQL、堆栈、本地路径或模型私密输出。

### 9.3 P2/P3 兼容

现有 Agent 和活动导入 URL、成功字段、错误包络和 P0～P3 测试保持。生产调用改为认证 principal；测试构建器可显式注入 owner principal。兼容 `actor_id/owner_id` 只在内部 adapter 存续到 P4-C 验收，不能重新暴露为客户端可写字段。

P4-A 使用普通 HTTP JSON 和最终 GET 恢复，不实现 SSE/WebSocket。任何 provider 在线调用都用假 provider；DeepSeek 配置不进入 P4-A 验收。

## 10. P4-B～P4-D 已冻结方向与延后项

### P4-B Windows Shell

冻结 Electron main/preload/renderer 三层、renderer sandbox/contextIsolation/CSP、一个毛毛、Tray、隐私模式、主题、主窗口默认隐藏并提示一次、开机启动默认关闭。Electron/Node/React/TypeScript 版本、OpenAPI 生成器、router/state/chart、IPC allowlist、BackendSupervisor 和设备设置 schema 在 P4-A 验收后另行冻结；B6 不增加 `apps/desktop`。

### P4-C 日常财务闭环

冻结只用虚拟数据验收、“午饭 18 元”候选→确认→一次写入→GET/账本/图表刷新、已入账错误只能追加可审计领域动作、token streaming 不作门槛。dashboard DTO、刷新机制、候选纠正和可选 SSE 合同留到 P4-C。

### P4-D 财富管理扩展证明

冻结最小只读应急资金/储蓄模块、C10 的八项扩展性证明、固定虚拟 fixture、不接行情/交易/证券推荐。精确 fixture、公式、舍入和陈旧阈值留到 P4-D；财富管理不等于股票投资。

## 11. 文件所有权、验证和完成条件

P4-B6 执行方拥有 `src/wife_system/host/**`、必要 `modules/**`、明确交接的现有 agent/api/finance/activity-import 适配、P4 migration、执行方 `tests/host/**` 及运行说明。不得修改 `tests/independent/**`、C10 矩阵、D9、本文、测试报告、其他角色日志或 Git。

P4-C11 测试方以后拥有 `tests/independent/host/**`、P4-A 独立报告和 C10 矩阵执行状态；没有返修任务不得修改产品。

P4-A 只有满足以下条件才可由总控接受：

1. 执行方提交有序文件 SHA-256 快照、自测和迁移证据并停在 `review`。
2. 测试方在同一快照执行 P4-A 64 项适用案例、P0～P3 代表回归、SQLite 和真实 PostgreSQL 门禁。
3. 空库与 P0～P3 历史虚拟库升级通过，允许的测试降级保留旧业务事实，单 Alembic head。
4. 无开放 P0/P1；无跨用户访问、重复财务写、半事务、secret 泄露或未授权工具执行。
5. PostgreSQL、服务和临时资源正常关闭；不删除用户既有 volume，不操作 OpenClaw/微信/DeepSeek/Electron。

接口冻结不代表功能已实现。执行方自测只能到 `review`，测试方独立结果只能建议接受，最终 `complete` 和 Git 本地提交由头脑风暴总控决定。
