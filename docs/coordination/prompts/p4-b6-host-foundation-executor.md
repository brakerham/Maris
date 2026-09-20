# P4-B6：Host、身份和通用状态地基实现

## 角色与任务

- 角色：用户侧边栏中既有的“执行智能体”任务
- 任务编号：`P4-B6`
- 固定起点提交：以总控验收 C10/冻结 P4-IF-001 后的当前本地 HEAD 为准，开始时记录完整 commit ID
- 唯一目标：实现 [P4-IF-001](../../phase-4-interface-freeze.md) 中的 P4-A Host、身份和通用状态地基
- 交付状态：只能到 `review`；执行方自测通过不等于独立验收或项目 `complete`

开始前必须按顺序读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. `docs/coordination/control.md`
6. `docs/coordination/agents/executor.md`
7. 本任务卡
8. `docs/phase-4-interface-freeze.md`
9. `docs/phase-4-d9-modular-agent-host-advice.md`
10. `docs/testing/phase-4-modular-agent-host-test-matrix.md`
11. `docs/phase-2-interface-freeze.md`
12. `docs/phase-3-interface-freeze.md`

先确认 control 中 P4-B6 只有一个执行负责人。若冻结文件、C10 摘要或 HEAD 与总控记录不符，停止并报告，不按旧假设实现。

## 必须实现

### 1. Host 合同与模块注册

- 新建 `src/wife_system/host/`，实现严格 manifest、Profile、tool binding、memory grant、event/setting 合同、registry 和唯一 composition root。
- 实现 P4-IF-001 的 ID/版本语法、查重、Host API major、模块启停和稳定启动错误。
- 实现 `ToolCatalog -> BoundToolRegistry`：Profile、principal permission 和模块启用共同决定 Schema；执行时再次授权；现有财务 handler 继续通过薄 adapter 调用。
- 保持现有 4/8/1、provider 15 秒和一次 retryable 重试；增加冻结的工具超时/停止码，不扩大权限。
- 生产组合根只注册 `daily_finance`。第二 manifest 用测试 fixture 证明通用注册，不能提前实现财富业务或在 Host 写 `if module_id == ...`。

### 2. 主人账户、session 和渠道绑定

- 使用 `pwdlib[argon2]` 与冻结参数实现 pending bootstrap owner、初始化、登录、refresh、logout、改密、session 列表/撤销和账户停用内部能力。
- 实现 15 分钟 access、30 天绝对 refresh/device session、摘要存储、原子轮换、重放撤销和最多 10 个 active session。
- 实现 loopback + `X-Bootstrap-Token` 初始化门；测试通过依赖注入配置随机 token，不把值写入 fixture 输出或日志。
- 实现一次性渠道绑定码和假可信 adapter consume；10 分钟、5 次尝试、HMAC domain、独立高熵 adapter token、并发消费和 active 身份唯一性。
- 不启动或修改 OpenClaw/微信，不读取真实外部身份。

### 3. 可信 user scope 与 migration

- 按冻结顺序创建三个线性 Alembic revision：identity、user scope、state。
- 给冻结清单中的根表和子表增加 `user_id`，历史虚拟数据回填到 pending bootstrap owner，增加必要复合 unique/FK/non-null。
- 所有受影响 repository/service/API 从可信 principal 作用域查询和写入；body/model/tool 不得自报 user/owner。
- 保留兼容 `actor_id/owner_id` 到 P4-C，但新写必须与 user 相等；旧 P0～P3 API/测试通过显式测试 principal 兼容。
- SQLite 和 PostgreSQL 分别实现/验证迁移；发现孤儿或矛盾数据要失败并给出安全诊断，不猜测归属。

### 4. run/pending 恢复边界

- 给 run/pending 增加冻结字段、60 秒 lease、最多 3 次接管、schema version、用户/模块/Profile 绑定。
- 保留 pending 六状态和 24 小时边界；确认使用状态+版本 CAS；取消遵守 committing 线性化点。
- 保留稳定财务提交键、响应丢失 GET 恢复、重复/并发确认一次一写。
- 抽出最小 `PendingActionCoordinator`/handler registry 时，只包裹现有行为，不把任意 JSON 变成通用业务写入口。

### 5. conversation、memory、setting 与 event

- 实现 P4-IF-001 的 conversation/message、memory candidate/item、module setting 表、service 和 API。
- 实现 90/30 天边界、shared confirm、模块 namespace 授权、删除清空正文、tombstone、替代链、最多 8 条确定性检索。
- 禁止账目、余额、预算、持仓、行情、密码、token、API Key 和原始外部身份进入记忆。
- 实现四类 post-commit 进程内事件；handler 失败不回滚事实，不引入 outbox/broker。

### 6. Host API 与兼容

- 实现冻结的 auth/session/binding/modules/conversation/memory/settings/health/ready 端点。
- 扩展现有 Agent 端点，使 conversation/module/profile/user 均由服务端校验和绑定；保留 P2 URL 与响应兼容。
- 实现严格 Pydantic、统一错误、request ID、冻结的 Idempotency-Key、cursor、limit 和跨用户 404。
- `readyz` 检查数据库、migration head 和 registry。P4-A 只使用 HTTP JSON + GET；不做 SSE/WebSocket。

## 实现方式和执行子任务

执行智能体是唯一集成负责人，可以按以下边界创建临时执行子智能体，但必须先在自身角色日志登记负责人、文件范围和交接点：

1. Host contracts/registry/tool binding：优先写 `host/contracts.py`、`registry.py`、`tools/**` 和对应执行方测试。
2. Auth/session/channel binding：优先写 `host/auth/**`、相关 API 和测试。
3. Migration/user scope：优先写 migration、models/repositories 和数据库测试。
4. Workflow/memory/API integration：在前三项合同稳定后集成，不与其他子任务同时编辑相同文件。

子智能体不得执行 Git 写操作，不得修改独立测试、C10、冻结文档或其他角色日志。执行智能体必须检查每个交付后再整合，不能让两个子任务同时修改 `finance/models.py`、`api/app.py` 或同一 migration。

## 允许修改

- `src/wife_system/host/**`
- `src/wife_system/modules/**` 中 P4-A daily adapter 和测试 fixture 所需代码
- P4-A 所需的 `src/wife_system/agent/**`、`api/**`、`finance/**` 及现有 activity import adapter；只做冻结范围内修改
- `migrations/versions/` 的三个 P4-A 线性 revision
- `pyproject.toml`，只增加冻结的 Argon2 password 依赖；如仓库出现锁文件则同步
- 执行方 `tests/host/**`，以及因 user scope/兼容确需更新的现有执行方测试
- `docs/b6-host-foundation-running.md`
- `docs/coordination/agents/executor.md`

禁止修改：

- `tests/independent/**`
- `docs/testing/phase-4-modular-agent-host-test-matrix.md` 和所有独立报告
- `docs/phase-4-interface-freeze.md`、D9、控制/总览、其他角色日志
- `apps/desktop/**`、OpenClaw、微信配置、真实个人数据或密钥
- Git 状态；不得 add/commit/switch/push/PR

不要大规模搬目录、重命名现有公共类型、放宽旧断言或为减少改动绕开数据库 user scope。若冻结合同确实无法实现，先停止并把冲突交回总控，不自行改口径。

## 依赖和外部操作

允许在 `pyproject.toml` 增加 `pwdlib[argon2]>=0.2,<1`。安装前按 AGENTS.md 重读 control；只安装项目声明依赖，不添加其他认证框架。网络或安装被环境阻止时记录错误并继续完成不依赖安装的部分，连续两个检查点无进展则停止报告。

P4-B6 可以在自测阶段使用已安装 Docker/Compose 启动项目 PostgreSQL，并使用随机测试 schema。启动前重读 control，记录 session/下一检查点；完成后普通 `compose down`，确认服务列表为空，不删除 volume、不 prune、不修改全局 Docker 设置。Docker Engine 不可用时不得反复要求用户操作，先记录 PostgreSQL 为 `unverified` 并完成本地证据。

禁止启动 Electron、DeepSeek、OpenClaw 或微信，禁止登录服务、调用付费 API、读取真实密钥或导入真实数据。

## 执行方测试

至少提供并运行：

1. manifest/Profile/tool/memory/event/setting 严格合同、ID/版本和全部冲突启动门禁。
2. Profile 工具可见性与执行授权、禁用模块、4/8/1、超时和重试。
3. bootstrap 并发、密码 hash/rehash、登录限速、session 轮换/重放/撤销/改密。
4. binding 过期、次数、HMAC、并发消费、冲突、解绑重绑和脱敏。
5. SQLite user scope、跨用户反例、复合关系、幂等 domain、run/pending lease/CAS/取消/响应丢失。
6. conversation/memory 生命周期、namespace、shared confirm、删除/tombstone、8 条排序和事实禁止项。
7. API 严格 body、auth、404 隔离、Idempotency-Key、cursor、错误 envelope、health/ready。
8. 三段 migration 的空库、P0～P3 历史虚拟库升级、允许降级和单 head；能运行时补真实 PostgreSQL 约束与并发。
9. P0～P3 代表回归，至少覆盖现有 finance、agent_finance、activity_import 和 API/migration 套件；不得修改独立路径。

自测结果按“新增执行方”“旧执行方回归”“PostgreSQL”“静态/依赖”分开统计。失败、skip 和 warning 均列明；不能把环境阻塞写成通过。

## 快照与交付

交付：

- P4-A 产品代码、migration 和执行方测试
- `docs/b6-host-foundation-running.md`：架构、数据流、迁移、运行、自测、限制、文件列表和逐文件 SHA-256
- `docs/coordination/agents/executor.md` 更新
- 有序总摘要，算法为 UTF-8 `path<TAB>lowercase_sha256<LF>` 按仓库相对 POSIX path 排序后再做 SHA-256

最终回复必须明确：修改文件数、各组自测计数、PostgreSQL 是否真实执行、P0～P3 回归、依赖变化、未验证项、资源状态和总摘要。状态写为 `review` 后停止，不自动派发测试智能体，不运行独立测试，不执行 Git。

## 进度和停止规则

- 接单、每个执行子任务分配、合同/身份/迁移/workflow-memory/API 集成、长测试开始、阻塞和完成时更新执行快照。
- 预计超过五分钟的操作先记录下一检查点；每十分钟或每个实质输出刷新心跳。
- 连续两个检查点或同一错误没有有效进展时，停止当前长操作和未完成子任务，保留现场，报告具体步骤、最后脱敏错误、已尝试方法、可复现条件和需要共同解决的问题。
- 任意跨用户访问、重复财务写、半事务、migration 数据丢失、secret 泄露或权限绕过视为 P0，立即停止扩大测试并报告。
- control 更新、文件所有权冲突或其他智能体同时修改实现时，以最新 control 为准，安全停止冲突范围。
