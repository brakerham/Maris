# P4-B6-R1：安全数据边界与兼容入口返修

## 角色与任务

- 角色：用户侧边栏中既有的“执行智能体”任务
- 任务编号：`P4-B6-R1`
- 唯一目标：按 P4-IF-002 关闭 R1 负责的 3 个 P0、7 个 P1，形成可供 R2 精确接续的安全数据与 migration 快照
- 交付状态：只能到 `review`；不得启动 R2、C11 或宣布 P4-A complete

开始前必须按顺序读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. `docs/coordination/control.md`
6. `docs/coordination/agents/executor.md`
7. 本任务卡
8. `docs/phase-4-interface-freeze.md`
9. `docs/phase-4-interface-freeze-002.md`
10. `docs/p4-b6-multi-handoff-code-audit.md`
11. `docs/phase-4-d10-b6-repair-architecture.md`
12. `docs/b6-host-foundation-running.md`
13. `docs/testing/phase-4-modular-agent-host-test-matrix.md`

开始修改前重读最新 control，确认 P4-B6-R1 只有你一个实现负责人，技术顾问和测试智能体均已停止。

## 固定输入

- D10 SHA-256：`1e9283af99a658b024e094db5f4c31c56396322a2dee68c012c87d19b5df2399`
- R1 起点清单：[93 文件协调快照](../snapshots/p4-b6-r1-start.sha256)
- R1 起点有序总摘要：`62c250c73e1c47ed13f8cd6355be9cb88ee4081f920e2ed747b82492e5168c2e`
- 当前 Git HEAD 只作历史定位：`88376edc4358068b7db418b580b8ae58b2493de5`

起点摘要算法：对清单覆盖的 migrations、`src/wife_system/**.py`、四个执行方测试目录、依赖/迁移/Compose 配置逐文件计算小写 SHA-256；使用仓库相对 POSIX path，按路径排序，拼接 `path<TAB>sha256<LF>` 后再做 SHA-256。

在任何修改前重新计算并与协调快照逐行比较。若不匹配，停止并报告变化文件；不得 restore/reset 或覆盖其他人的工作。

## 必须关闭的问题

```text
P0-01 绑定码原文进入 receipt 并可重放
P0-02 Host 模式活动导入绕过认证
P0-03 三条跨用户复合关系缺失
P1-01 过期 access token 仍可改密
P1-02 Host command 三事务 crash window
P1-03 adapter token 缺失/错误 HTTP 不统一
P1-04 五次绑定失败对真正枚举无效
P1-05 AuthError HTTP 映射不完整
P1-13 cancelled run 阻断 P4→P3 downgrade
P1-14 activity import 未识别 P4 PostgreSQL unique 名
```

不得把其中任何项改名为后续优化。发现冻结方案无法安全实现时，停止冲突范围并把具体矛盾交回总控。

## 必须实现

### 1. `code_id + code` 一次性绑定

- 修改 create/consume DTO、AuthService、模型和 migration。
- 原始 code 只在首次 201 响应出现；数据库、receipt、日志、事件和错误中零出现。
- 相同键同载荷重放创建返回 409 `one_time_secret_unavailable`。
- 新键创建在同事务撤销同用户/同 channel 的旧 active code。
- 已知 active code_id 的错误 code/channel 第 1～4 次累计，第 5 次锁定，第 6 次不增加。
- unknown/expired/consumed/revoked/locked 对外统一 409 `binding_code_invalid`。
- adapter header 缺失、空、错误统一 401 `channel_adapter_unauthorized`，先校验 adapter 再查询 code。

### 2. Host command 与 receipt 同事务

- initialize、create code、consume、revoke 必须共享一个 SQLAlchemy Session/事务完成 receipt、领域事实和安全结果。
- 明确分离 `public_result` 与 `receipt_result`；一次性 secret/token 永不进入 receipt。
- 删除或改造当前永久 incomplete receipt 路径。
- 覆盖领域提交前故障、事务提交后响应丢失、同键并发和同键异载荷。

### 3. access、principal 与错误

- 改密使用完整 active access 校验；恰好 access expiry 即 401 `session_expired`，失败零写。
- `AuthenticatedSession` 从可信 DeviceSession 携带 platform；principal channel 按 IF-002 映射。
- AuthError 建立穷举映射并提供枚举覆盖测试。
- 404/405 使用统一 envelope；不得回显内部路径、SQL、token、digest、原始外部身份或异常正文。

### 4. 活动导入 Host principal

- Host 模式从 `get_principal` 构造 ImportIdentity，无/坏/过期/撤销 token 401 且零写。
- HostRuntime 与静态 legacy import identity 互斥；生产入口不再有静态默认身份。
- A/B batch、candidate、receipt、提交与 UUID 查询保持用户隔离。
- PostgreSQL 同用户同名模板竞争识别 `uq_template_user_name`，返回 409 `concurrent_modification`；保留旧 P3 约束名兼容但不解析完整异常文本。

### 5. ORM 与三个 migration

- 按 IF-002 增加三条复合 FK、对应 unique、message→run 复合关系和 R2 预备字段。
- ORM metadata 与正式 Alembic schema 一致；被复合约束替代的单列 FK 不继续漂移。
- 保持三个 P4 revision和单 head `p4_host_state`，不新增第四 revision。
- SQLite 成对 rebuild run/pending，恢复 FK 后执行 `PRAGMA foreign_key_check`。
- PostgreSQL 建立真实复合约束和正确的 downgrade 顺序。
- head→P3 把 cancelled run 映射为 `error` + `error_code=cancelled`，保留引用；再升级 head 后数据一致。
- 修复现有 PostgreSQL fixture：迁移到 P4 head，使用真实存在的 app_user，最终 head 断言更新；不得删除原业务断言。

## 文件所有权

允许修改产品：

- `src/wife_system/host/auth/errors.py`
- `src/wife_system/host/auth/models.py`
- `src/wife_system/host/auth/service.py`
- `src/wife_system/host/state_models.py`
- `src/wife_system/host/state.py`，仅 idempotency/Host command 部分
- `src/wife_system/agent/models.py`，仅 schema/constraint/R2 预备字段
- `src/wife_system/api/app.py`
- `src/wife_system/api/host_routes.py`
- `src/wife_system/api/host_schemas.py`
- `src/wife_system/api/activity_import_routes.py`
- `src/wife_system/activity_import/service.py`
- `migrations/versions/p4_host_identity.py`
- `migrations/versions/p4_host_user_scope.py`
- `migrations/versions/p4_host_state.py`

允许修改执行方测试：

- `tests/host/test_auth.py`
- `tests/host/test_api.py`
- `tests/host/test_state.py`
- `tests/host/test_migrations.py`
- 可新增 `tests/host/test_postgresql_r1.py`
- `tests/finance/test_postgresql_claim.py`
- `tests/finance/test_migrations.py`
- `tests/activity_import/test_postgresql.py`
- `tests/activity_import/test_migration.py`
- `tests/activity_import/test_service.py`
- `tests/agent_finance/test_migration.py`

允许修改交付文档：

- 新建 `docs/b6-r1-security-data-running.md`
- 更新 `docs/coordination/agents/executor.md`

其他全部只读。尤其禁止修改：

- `tests/independent/**`
- C10 矩阵、所有独立报告、接管审计、D10、P4-IF-001、P4-IF-002
- control、overview、brainstorm、technical-adviser、tester 角色文件
- `agent/application.py`、`agent/pending.py`、`agent/loop.py` 和 R2 运行时文件
- 依赖声明和锁文件，除非发现现有冻结完全无法实现并先停止报告
- Electron、OpenClaw、微信、DeepSeek、真实账户、真实个人数据
- Git 状态

如果需要修改未授权文件，先停止并说明具体编译/合同依赖，不要自行扩大范围。

## 执行方测试责任

执行智能体必须编写和运行实现所需的单元、组件、API、migration 和最小集成测试。这是开发责任，不属于独立验收。禁止运行或修改 `tests/independent/**`。

### 本地必测

至少覆盖：

1. receipt、日志、事件和全部相关表不含原始 code/token/外部身份；
2. 创建首次、同键重放、新键替换和异载荷冲突；
3. code_id + code 的第 1～6 次、错 channel、过期、消费、撤销、并发第五次；
4. initialize/create/consume/revoke 在事务提交前故障和提交后响应丢失的恢复；
5. access 到期前 1µs、恰好到期、到期后 1µs改密；
6. adapter header 缺失/空/错误/正确；全部 AuthError 映射；404/405 envelope；
7. Host/legacy import 装配互斥，无/坏/撤销 token 零写，A/B 隔离；
8. 三条复合 FK 的合法同用户和非法跨用户直接写；
9. 空库、完整 P0～P3 虚拟历史、已有虚拟 P4 head、重复 upgrade、head→P3→head；
10. cancelled run 和全部 pending 状态 downgrade；迁移失败不留半状态；
11. ORM metadata 与实际 migration constraint 名、列和目标一致；
12. P0～P3 执行方回归保持原断言。

### 真实 PostgreSQL

本任务接单后，执行智能体是 `finance-postgres` 的唯一环境负责人。启动前再次读取 control 并在执行日志记录操作和下一检查点。

只启动项目 `finance-postgres`，使用项目测试凭据、随机 schema 和虚拟数据。必须实际进入业务断言：

- 更新后的 finance 4 项和 activity import 9 项原 PostgreSQL 测试；
- 并发 binding 第五次/正确消费/新码替换；
- 四个 Host command 同键并发、异载荷和响应丢失；
- 三条复合 user FK 的直接 SQL；
- 空 schema、完整历史、含 cancelled 的 P4 head upgrade/downgrade/upgrade；
- activity import 同用户同名竞争与不同用户同名成功；
- 约束名不超过 63 字符、单 head、失败无半迁移。

失败或 skip 必须逐项列出，不能把收集成功、环境跳过或最小冒烟写成通过。结束时普通 `docker compose down` 并确认服务列表为空；禁止 `down -v`、删除 volume、prune 或修改 Docker 全局设置。

## 交付与快照

`docs/b6-r1-security-data-running.md` 必须包含：

- 10 个审计项逐项“代码位置 → 测试 → 结果”映射；
- 数据库/HTTP/故障恢复语义；
- 修改、新增、删除文件的准确数量；
- 本地定向、Host、P0～P3 回归、PostgreSQL、静态/依赖分别统计；
- 所有失败、skip、warning 和未验证项；
- Docker 最终资源状态；
- 给 R2 的共享文件保护不变量和可用 schema 字段；
- 全部 R1 产品、migration、执行方测试和运行说明的逐文件 SHA-256；
- 按 `path<TAB>lowercase_sha256<LF>`、POSIX path、排序拼接生成的新总摘要。

快照清单文件数必须与报告数字一致。完成后更新 executor 日志，状态写 `review`，运行状态写 `finished`，停止修改。

不要执行任何 Git 写操作，不要派发 R2/C11，不要要求用户扫码、填写密钥或发送微信消息。

## 进度与停止规则

- 接单时立即登记唯一负责人、起点摘要、文件所有权和首个检查点。
- migration/receipt/auth/import/PostgreSQL 每个实质里程碑更新一次日志；长操作至少每十分钟刷新心跳。
- 一个 operation 预计超过五分钟时，先记录命令范围、可观察会话和下一检查点。
- 任意原始 secret 落库/日志、跨用户写、事实与 receipt 半提交、cancelled 数据丢失、迁移半状态都视为 P0，立即停止扩大测试并报告。
- 同一阻塞连续两个检查点无有效进展时，停止当前长操作，普通关闭由你启动的容器，报告最后错误、已尝试方法、可能原因和需要总控决定的问题。
- control 出现更新或其他角色开始修改同一文件时，立即安全停止冲突范围。
