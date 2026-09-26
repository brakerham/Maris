# P4-B6-R3 执行智能体 Prompt：PostgreSQL 历史 user-scope migration 返修

你是项目中既有的**执行智能体**，唯一负责 `P4-B6-R3`。修复 `P4-C11-R1-PG-001`：真实 PostgreSQL P3 schema 含合法 P1 财务双分录、P2 run/pending 和 P3 import 历史时，`p4_host_user_scope` 因 pending trigger events 无法 ALTER `financial_transaction`。

本任务是窄范围 migration 返修。不得修改独立测试、测试报告、矩阵、接口冻结、业务服务或 Git 状态。自测通过只能提交 `review / finished`；不得宣布 P4-A `complete` 或自行启动 C11-R2。

## 1. 开始前必须读取

按顺序读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. `docs/coordination/control.md`
6. `docs/coordination/agents/executor.md`
7. `docs/phase-4-interface-freeze.md`
8. `docs/phase-4-interface-freeze-002.md`
9. `docs/phase-4-d10-b6-repair-architecture.md`
10. `docs/p4-c11-r1-coordinator-review.md`
11. `docs/testing/phase-4-c11-r1-evidence-report.md`
12. `tests/independent/host/history_fixtures.py`，只读理解数据形状
13. `tests/independent/host/test_postgresql_acceptance.py`，只读理解失败节点
14. `migrations/versions/p4_host_user_scope.py`
15. `tests/host/test_migrations.py`
16. `tests/host/test_postgresql_r2.py`
17. `docs/coordination/snapshots/p4-b6-r3-start.sha256`

在 `docs/coordination/agents/executor.md` 记录接单、当前步骤、开始时间、心跳、下一检查点、等待对象和可观察 pytest/Docker 会话。任何 Docker 操作前重新读取最新 control。

## 2. 固定起点

```text
docs/coordination/snapshots/p4-b6-r3-start.sha256
entries=130
manifest_sha256=ed4cec634ead2a8543066f19c7134f3d0a65d58f39ebe43133ef955129a86770
```

开始前逐行复算，要求：

```text
matched=130
missing=0
mismatch=0
```

任何不匹配立即停止，不得 restore、reset、checkout、switch 或覆盖其他角色文件。结束时以 130 文件起点为基准报告 changed/unchanged/missing；独立测试和报告必须保持零漂移。

## 3. 允许修改

只允许：

```text
migrations/versions/p4_host_user_scope.py
tests/host/test_postgresql_r2.py
tests/host/test_migrations.py
docs/b6-r3-postgresql-history-migration-running.md
docs/coordination/agents/executor.md
```

如果保持既有 R2 文件清晰需要新增执行方专用测试，可新增：

```text
tests/host/test_postgresql_r3.py
```

优先在既有 `test_postgresql_s1_migration_empty_history_and_round_trip` 的 P3 历史 fixture 中加入 transaction/entry 事实和断言；不要无必要复制完整 PostgreSQL harness。

## 4. 禁止修改

```text
src/**
migrations/versions/p4_host_identity.py
migrations/versions/p4_host_state.py
tests/independent/**
docs/testing/**
docs/coordination/control.md
docs/coordination/overview.md
docs/coordination/snapshots/**
docs/coordination/agents/tester.md
docs/coordination/agents/technical-adviser.md
compose.yaml
alembic.ini
pyproject.toml
requirements*.txt
```

禁止任何 Git 写操作。不得用执行方测试替代后续 C11-R2 独立复验。

## 5. 必须先建立执行方失败回归

在修改 migration 前，扩展或新增执行方真实 PostgreSQL 用例，独立构造等价历史：

- P1 account/category/expense transaction/正负双分录；
- P2 paused run/needs-confirmation pending；
- P3 previewed import batch/candidate；
- 从 P3 head 正向升级到 P4 head。

先保存失败前证据：失败类型、migration 阶段、表名、是否到达 P4 head、事务回滚后的 schema 状态。不得把独立测试文件复制到执行目录或导入其断言；可以参考其虚拟数据形状，自行定义执行方 fixture 和预期。

失败回归必须在原实现上稳定复现 PostgreSQL `ObjectInUse` 或同一 pending-trigger ALTER 失败，再开始修复。不要通过多次重跑挑选一次通过结果。

## 6. 修复要求

### 6.1 必须保持的语义

1. 迁移原子性：整个 revision 成功或回滚，不留下半迁移。
2. 合法 P1/P2/P3 历史事实、金额、双分录、状态和关系原值保持。
3. 所有 scoped 行统一回填唯一 bootstrap owner。
4. actor/owner 与 user check、每表 `(user_id,id)` unique、自然 unique 和复合 user FK 全部建立。
5. 非法孤儿、矛盾旧 owner、跨用户关系继续在加约束前安全拒绝，不重归属、不删除、不猜测修复。
6. migration 最终仍为三个 P4 revision、唯一 `p4_host_state` head；不得创建第四 revision。
7. PostgreSQL 和 SQLite 最终约束形状与 ORM 保持一致。
8. downgrade/head→P3→head 的既有语义不变。

### 6.2 禁止的绕过

不得：

- 在 revision 中手动 `COMMIT` 或拆出非原子升级；
- 设置 `session_replication_role`；
- 禁用 trigger、FK、NOT NULL 或 check；
- 删除/截断历史表或事实；
- 把合法数据当非法数据拒绝；
- 延长 Docker/测试超时来掩盖失败；
- 修改 C11 独立 fixture 使数据形状变简单；
- 依赖 `Base.metadata.create_all()` 代替 Alembic。

### 6.3 推荐方案与裁量范围

优先评估按 dialect 分流：

- SQLite 保留当前 nullable column + backfill + 受控 batch rebuild；
- PostgreSQL 添加 `user_id` 时使用仅迁移期间存在的常量 server default，并在同一 DDL 中建立非空列，使历史行无需逐表 `UPDATE user_id`；随后删除 default，再创建 unique/FK/check 和复合关系。

bootstrap user ID 来自 migration 自己查询到的唯一 pending owner，必须安全转成 UUID SQL literal，不接受外部输入。最终 schema 不保留 server default，运行期仍必须显式提供 user ID。

这只是推荐实现。可以采用其他方案，但必须保持单事务原子性，并用真实 PostgreSQL 历史回归证明不存在 `UPDATE → pending trigger → ALTER` 冲突。若安全修复必须修改其他 P4 migration、服务代码或冻结合同，立即停止为 `blocked / finished` 并交回总控，不得扩大范围。

## 7. 执行方测试

### 7.1 修改前

只运行新增/扩展的精确 PostgreSQL 历史节点一次，保存预期失败。

### 7.2 修改后定向门禁

至少运行：

1. 新增/扩展的 PostgreSQL P3 历史→P4 精确节点；
2. `tests/host/test_postgresql_r2.py` 完整文件；
3. `tests/host/test_migrations.py` 完整文件；
4. `tests/host/test_postgresql_r1.py` migration/round-trip 相关节点；
5. `tests/finance/test_migrations.py`；
6. `tests/activity_import/test_migration.py`（若实际文件存在；否则记录准确文件名并运行对应 migration 文件）；
7. migration Python 编译、`pip check`、`git diff --check`。

如果 migration diff 只涉及 PostgreSQL add/backfill 顺序且这些门禁全过，不重复 Agent、Host API、认证、memory、完整 P0～P4 或独立测试。

### 7.3 必须断言

真实 PostgreSQL 回归必须断言：

- P3 历史升级实际到达唯一 `p4_host_state`；
- P1 金额和正负双分录原值保持；
- P2 run/pending 状态、互相引用和回填字段保持；
- P3 import batch/candidate 状态、金额和关系保持；
- scoped 表无 NULL user；所有代表事实归属唯一 bootstrap owner；
- 三类复合用户 FK 和相关 unique/check 从真实 catalog 存在；
- 无孤儿、无错误重归属；
- 再次 upgrade 为幂等；允许的 head→P3→head 保持旧事实；
- 构造非法孤儿/矛盾 owner 时升级失败且事务回滚，不留下部分 `user_id` 列或错误 head；
- 最终没有 persistent server default。

## 8. Docker 边界

本任务期间执行智能体是 `finance-postgres` 的唯一负责人：

1. 先确认 Engine 可达和项目 Compose 为空；
2. 只启动 `docker compose up -d finance-postgres`；
3. 等待 `running / healthy`；
4. 使用随机 schema 和虚拟数据；
5. 完成或失败后普通 `docker compose down`；
6. 最终确认 `COMPOSE_SERVICES_EMPTY`；
7. 禁止 `down -v`、删除 volume、prune、Factory reset、Desktop 重启、context/全局设置/socket 操作。

Engine 不可达时只检查一次并停止，不自行维修 Docker Desktop。

## 9. 交付物

更新执行角色日志，并新增：

```text
docs/b6-r3-postgresql-history-migration-running.md
```

运行说明必须包含：

1. 修改前失败回归；
2. 根因确认；
3. 最终修复的数据流和为何保持原子性；
4. PostgreSQL 与 SQLite 分支差异；
5. 所有定向命令的 passed/failed/skipped/warning；
6. 历史事实、owner、约束、回滚、幂等和 downgrade 证据；
7. Docker 启动、health、普通 down 和最终空服务；
8. 130 文件起点复算和终点 changed/unchanged/missing；
9. 所有授权修改/新增文件的普通 SHA-256；
10. 明确没有运行或修改独立测试，没有 Git 写操作，没有外部集成。

停止修改后生成新的产品/执行测试有序摘要，交给总控固定 C11-R2 输入。状态只能为：

- 定向门禁全部通过：`review / finished`；
- 需要扩大产品/迁移范围、真实 PG 仍失败或 Docker 阻断：`blocked / finished`。

无论结果如何，不得自行启动测试智能体、C11-R2、技术顾问、Electron、OpenClaw、微信或 DeepSeek。
