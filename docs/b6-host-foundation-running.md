# P4-B6 Host、身份和通用状态运行与交接

- 角色：执行智能体（Executor）
- 任务：`P4-B6`
- 交付状态：`review`；执行方自测完成，等待 P4-C11 独立验收和总控核对
- 控制版本：`2026-09-20T18:14:54+08:00`
- 接口依据：`docs/phase-4-interface-freeze.md`（`P4-IF-001`）
- 依赖变化：`pwdlib[argon2]>=0.2,<1`，锁文件已同步；`pip check` 通过
- 外部边界：只使用虚拟数据和临时 SQLite；没有登录真实服务、读取密钥或操作 OpenClaw/微信/DeepSeek/Electron

## 1. 本轮交接范围

本轮从既有 B6 实现检查点继续，集中完成可信 `user_id` 作用域在财务、活动导入、Agent run/pending 和工具适配中的收口。已有 Host 合同、认证、迁移、状态服务和 API 保留在同一交付快照中；没有重写 P0～P3 财务核心或改变冻结接口。

## 2. 结构和数据流

```text
可信 PrincipalContext(user_id, session/device, channel, permissions)
  -> HostRuntime（数据库、模块 Registry、认证、状态/事件、cursor）
  -> ModuleRegistry -> Profile -> ToolCatalog/BoundToolRegistry
  -> AgentApplication / workflow / PendingActionStore
  -> FinanceService 或 ActivityImportService
  -> SQLAlchemy 事务（user_id + 复合关系 + 幂等键）
  -> HTTP JSON 返回安全错误和可恢复的持久状态
```

Host 组合根只注册内置 `daily_finance`。Manifest、Profile、tool alias、权限、memory namespace、事件和 setting schema 在启动时严格校验；重复 ID、非法版本、未知权限或不匹配的 Host API major 会阻止 ready。Profile grant、当前 principal permission 和模块启用状态共同决定模型可见工具，handler 执行前再次检查。

主人账户使用 Argon2id、pending bootstrap owner、loopback + `X-Bootstrap-Token` 初始化门、15 分钟 access、30 天设备 session、摘要存储、refresh 轮换/重放撤销和本地登录限速。渠道绑定码只保存 HMAC 摘要，可信 adapter 另用独立 token；原始绑定码和外部身份不进入普通记录、日志或模型上下文。

三个线性 migration 的顺序为：

```text
c82d7a4f901e
  -> p4_host_identity
  -> p4_host_user_scope
  -> p4_host_state (head)
```

`p4_host_identity` 创建 owner、credential、device/session 和 channel binding；`p4_host_user_scope` 为 P0～P3 业务/状态表增加非空 `user_id`，把历史虚拟数据回填到 bootstrap owner，并建立复合关系；`p4_host_state` 创建 conversation/message、memory candidate/item、module setting 和 Host receipt，并补齐 run/pending 的 module/profile/schema/lease 字段。SQLite 使用受控 batch rebuild；旧历史 schema 的种子由 migration 测试用 SQL 写入，避免当前 ORM 越过旧列。

Agent run 使用 60 秒 lease、最多三次接管、用户/模块/Profile 绑定和 schema version；pending 保留六状态、24 小时边界、版本 CAS、`committing` 线性化点和稳定财务提交键。Finance 和 Activity Import 的查询、幂等、版本检查、候选提交、run/pending 恢复均从可信用户作用域取值；body、模型工具参数和普通设置不能自报 owner/user。

Host API 覆盖 bootstrap/auth、session、channel binding、modules、conversation、memory、settings、Agent run/resume/get、`healthz` 和 `readyz`。请求使用严格 Pydantic DTO、统一错误包络、认证依赖、`Idempotency-Key`、cursor 和跨用户 404；`readyz` 检查数据库、migration head 和 registry。事件只在事务提交后进程内发布，handler 失败不回滚事实。

## 3. 执行方验证

所有命令均在仓库根目录执行，未运行 `tests/independent/**`。

### 新增 P4 Host 执行方测试

```powershell
.venv\Scripts\python.exe -m pytest -o addopts="" tests/host --tb=short
```

结果：`49 passed, 1 warning in 18.14s`。

覆盖合同/manifest/registry/tool binding、Profile 和模块启停、认证 bootstrap/login/refresh/logout/密码/session、绑定码、conversation/memory/settings、workflow lease/CAS、SQLite 空库/历史升级/降级和跨用户复合外键。

### P0～P3 执行方回归

```powershell
.venv\Scripts\python.exe -m pytest -o addopts="" tests/finance tests/activity_import tests/agent_finance --tb=short
```

结果：`200 passed, 13 skipped, 1 warning in 20.25s`。13 个 skip 全部是 PostgreSQL 连接门禁（`tests/finance/test_postgresql_claim.py` 4 项、`tests/activity_import/test_postgresql.py` 9 项），不计为通过。

四组合并执行方套件：

```powershell
.venv\Scripts\python.exe -m pytest -o addopts="" tests/host tests/finance tests/activity_import tests/agent_finance --tb=short
```

结果：`249 passed, 13 skipped, 1 warning in 33.83s`。唯一 warning 是现有 Starlette 对 AnyIO `BlockingPortal` 别名的上游弃用提示，没有屏蔽或改写第三方包。

迁移定向证据包含：P4 三 revision 单 head、空库重复升级、P0～P3 历史虚拟数据回填与 round-trip 降级、矛盾旧 owner 安全拒绝、SQLite 复合 scope FK 跨用户写入拒绝、finance/activity-import/agent migration 回归。PostgreSQL 没有在本轮进入业务断言。

### 静态和依赖检查

```powershell
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe -m compileall -q src tests
```

结果：`No broken requirements found.`；`compileall: PASS`。

## 4. PostgreSQL 与资源状态

执行前核对了最新 `control.md`。用户确认 Docker Desktop 已启动，但本次执行环境访问 `npipe:////./pipe/docker_engine` 被拒绝；`docker compose up -d finance-postgres` 未启动任何容器。一次授权提升请求未执行，自动审批服务返回模型不可用的 404，因此没有绕过权限继续尝试。PostgreSQL 测试仍为 `unverified`；没有删除 volume、prune、修改 Docker 全局配置或伪造通过证据。当前没有由执行智能体启动的服务或临时容器。若总控后续要求真实 PostgreSQL 门禁，应在具备 Docker Engine 命名管道权限的执行环境中使用随机 schema 和虚拟数据运行，并普通 `compose down` 清理。

## 5. 文件边界与限制

本交付没有修改 `tests/independent/**`、P4 冻结/D9/C10/control/overview、其他角色状态、Electron、OpenClaw、微信或真实数据。工作区原有 `.claude/settings.local.json` 未触碰，也不纳入快照。执行方自测不代表独立验收或 P4 `complete`；当前状态只能为 `review`。

## 6. 有序文件快照

快照覆盖 53 个实现、迁移、依赖和执行方测试文件；不包含本文或 `docs/coordination/agents/executor.md`，以避免自引用。每行是 UTF-8 的 `path<TAB>lowercase_sha256<LF>`，路径使用仓库相对 POSIX 路径并按 Unicode/ASCII 字典序排序；再对全部行拼接的 UTF-8 字节计算 SHA-256。

```text
migrations/versions/p4_host_identity.py	a39ed991f63bd771c2b93ea5463344da334c0cfda233b737c96c90741858028e
migrations/versions/p4_host_state.py	927681540081fdda0ef5a3a38c43f81667933fb1267bf9735da6b7da97c4a5c9
migrations/versions/p4_host_user_scope.py	fd08f1cabf97bb662374c7bce44ac0649cea4d25742a761e0f4f7230062e5269
pyproject.toml	18e0125419259b37cc27afbd5da742e104354ac1da567af3933916c9a25e5a12
requirements-dev.lock	5106a8355453fa6e7ed96fe1879edb901a4e063a1339c4d6c32077aff4f6b564
src/wife_system/activity_import/context.py	4b055802d5c2c23047bad5490bf3a76e15ac041b5ac8423186f2a76923579d1f
src/wife_system/activity_import/repository.py	3fef4a21ee6ad645b20596de419af8d78ddb2b87f498340f7b6ffc68ed3790e3
src/wife_system/activity_import/service.py	fb92ddedfcd70cdfc942344a82d7a31e2eb6ece86657fc55ed7b95bd79f8d045
src/wife_system/agent/application.py	f3a6d52c4e0fdf75a81e6eb2a4570d04c710b5aa690005510230078caf1b9f12
src/wife_system/agent/context.py	d9945ce92a9502c0744e5b34e1becde1c846ab10c53b07aa846134299ac33d37
src/wife_system/agent/finance_tools.py	01a6f89f51a58b6d676865f206ea41d0e11079fc8a7c09b082acece11133df28
src/wife_system/agent/loop.py	06eb8097766aabd730fe76c42bbe8398400160b144434ff578d90a75d2e02ee5
src/wife_system/agent/models.py	a68519627483b1571e2b3deb9116eb0331ab4a517cccc3ec4980d33747d3de24
src/wife_system/agent/pending.py	1e24603c6418dabadecd2ba8ece58a193dc9caf2769c909777545637a1263317
src/wife_system/api/agent_routes.py	6c02a37cf07bc4439decb2d6d369ab76a168e32e0500cd5430e7d8ff105c9080
src/wife_system/api/app.py	a355f6ca6bca5e8f0bbeaf1ddc347ea1da4c040fc9dde9dc477e90dba0283725
src/wife_system/api/host_routes.py	2df721c63d0bcc11301ea0cf012a3d7fc723e9d85411b144dd7ad45709c7cfb6
src/wife_system/api/host_schemas.py	ff55090517e5957b01d23244c5433773038645d69c1500912c055e61d17873b0
src/wife_system/finance/models.py	90290d2c0f3711a5235fb3b07110e4fd9a5ca6e2cac14ad5846b8a869b90bd21
src/wife_system/finance/repositories.py	7f8cf348af949ff8d081a5483837e9f83d4112fd0068e91958aee1244e8230ac
src/wife_system/finance/service.py	76abe42b88c5c89d967113c0859bb55a722a474dc84cd9ef0aa3ebc81d565fcb
src/wife_system/host/auth/__init__.py	d5b56ebef9de1ae83206da1ce8d7278414c069b9d8bc430160e8563f8c124972
src/wife_system/host/auth/errors.py	a976f70f0da68906cc3daea2c71804517a7a814f918b13a04ceb4ab1c5bea7a6
src/wife_system/host/auth/models.py	dc02fa43408527b567124a7189b9d34df371cd7956064fd42aa317cfaab3dbff
src/wife_system/host/auth/service.py	9ff030971720fca5d5d43d732433955188f21346691df41156cc4ce641b2e543
src/wife_system/host/context.py	8c8c4b26038a2bd6f50ebc0fefca9fcebc31f6c9856c4a10c3d21ebef67c3921
src/wife_system/host/contracts.py	11c9a018d44ceff0fd51418e6073cc8ab29cd3e3695ed217e1583316c57acba1
src/wife_system/host/cursor.py	d68aac094c68265fdbd5bdd181f34f0f5d6127ed1a8c02f601da58adf1020830
src/wife_system/host/events.py	b11b2bfc7995071fb02e8a753d1aa070c16855dea53b74473ee91098a5a4e009
src/wife_system/host/factory.py	e5b0dfd3887882000e8ec4e2c0c8c74036b86aa883be20e77b758301852e332a
src/wife_system/host/registry.py	7309e0aaf33454205964c41ff39782bd67fbc321e3549826daf7256b8d70960a
src/wife_system/host/runtime.py	58c92319dfb59fdf35a3193638c932cb4730d1eb4568e12317636a852821d6b4
src/wife_system/host/state_models.py	762a5c3dfafa74c6b6fc208a63ac42f44a210b72e041f92e33b70f1a57c43bdc
src/wife_system/host/state.py	7db69f3634005c08da9e77ba7e06c8caf4ceda3d9a0fe9cc327cd13cf253afce
src/wife_system/host/tools/__init__.py	cd91c663da5e5ac20ba0e7ae2ecc8a16257f9df6bc0c046c2412a72705e34182
src/wife_system/host/tools/catalog.py	48dac785f4daaae167ca082a9806dd4ed87f87a37ab18f8b1aaccd9f7c3ef86d
src/wife_system/host/workflows.py	9ba19486d7a7b921e2d8e7939a4ceaf3b864d607e0a4431250458678d76c61c3
src/wife_system/modules/__init__.py	76b0c072512dfb6c844cc5fb01da8c5fea677d47283d55dc4dc6189d7a811bd9
src/wife_system/modules/daily_finance.py	d491f41a2f8253c88d7d9c5f2cfe30d8f03c93463c18874ff9a58de561a02012
tests/activity_import/__init__.py	f371abdeb05764ed0f4c2403c7a259c87f05f0885c663b39f3dbf501b9d1b814
tests/activity_import/test_migration.py	af173de0b65e128b053c63d2ebb2db88b1990fa29fb8a8e6b6a8db176f8d3baa
tests/activity_import/test_service.py	b5171f14d41037a34c6c06812e4d3ccb3208d6a4ef5530db7177891b09f5b550
tests/agent_finance/conftest.py	708dbb7307118b55f088c00643ac234146d79f967821a46653f89b349774cda3
tests/agent_finance/test_migration.py	c81ce242dea1fa853909363f39bd0f238591f8a74e05a2729a84dc7957bc9c32
tests/agent_finance/test_tools_and_http.py	31f3765c16f54bb3af9c6420a64266498edeb8466cfd4516a9f5027e4222c1ed
tests/finance/test_migrations.py	670f8cf45b0257018f1d895ae35def8a5823ff85a9184f9fa1995ef53869015e
tests/host/__init__.py	8f173bc3a42ca2ae4d72ffa47f36663208b88144d882901872b3db1d19e15d46
tests/host/test_api.py	6d204ba16e83bb2542e6c7e836b8e41c967b3bdf14d7c24266ed68a393e0046e
tests/host/test_auth.py	2570af9e2a9b981b9d7e8627afdb6975f00a31f235979203498d2a7965561fc3
tests/host/test_contracts_registry.py	2219e926c5f7131c4772ac4daf51255996967dc93335e271b78f3e022da55c97
tests/host/test_migrations.py	40fb865fac2919a8837c4c05c2de7282985b23095010fabcad670ed4049288bf
tests/host/test_state.py	b53b7a02862ca01c8f45d716e49f1762adfcd840e29a5d74e7db0087dff40f0
tests/host/test_workflows.py	8c8c7256b87ea5f0adcaec0e64d1e745c5c1e3ecf55e7f7e14b3facbe03897f2
```

总摘要：`B6-SHA256:009f8691e5917ca2966e7956f39ad3e08d4b4a7253803201d37d32a0a81fa4ed`。

交付后停止在 `review`，不执行 Git 写操作、不启动独立验收，也不替总控宣布 `complete`。
