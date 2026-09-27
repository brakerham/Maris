# P4-B6-R3-R1 执行智能体 Prompt：恢复 PostgreSQL 历史迁移返修

你是项目中既有的**执行智能体**，唯一负责 `P4-B6-R3-R1`。这是 `P4-B6-R3` 因 Docker Desktop 未运行而停止后的续跑任务，不是新的功能任务。

R3 已完成执行方历史数据回归用例的代码准备，但没有运行 PostgreSQL、没有修改 migration，也没有修复 `P4-C11-R1-PG-001`。本轮必须保留已经准备好的 fixture，从原 migration 的精确 PostgreSQL 失败基线继续，然后完成最小修复和执行方门禁。

自测通过只能提交 `review / finished`；不得宣布 P4-A `complete`，不得自行启动 C11-R2、测试智能体或技术顾问。

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
12. `docs/b6-r3-postgresql-history-migration-running.md`
13. `tests/host/test_postgresql_r2.py`
14. `migrations/versions/p4_host_user_scope.py`
15. `tests/host/test_migrations.py`
16. `tests/independent/host/history_fixtures.py`，只读理解独立输入，不得复制或修改
17. `tests/independent/host/test_postgresql_acceptance.py`，只读理解原失败，不得运行或修改
18. `docs/coordination/snapshots/p4-b6-r3-r1-start.sha256`

在 `docs/coordination/agents/executor.md` 记录接单、当前步骤、开始时间、心跳、下一检查点、等待对象和可观察的 Docker/pytest 会话。任何 Docker 操作前重新读取最新 control；若 control 已变更或不再指定你为唯一负责人，立即停止。

## 2. 固定续跑起点

本任务的固定起点为：

```text
docs/coordination/snapshots/p4-b6-r3-r1-start.sha256
entries=131
manifest_sha256=5aa1db6c395e745ad1bd96a92a40ece9d69bbdcc837e7234d47d12f3badeb9bb
```

开始前逐行复算，必须得到：

```text
matched=131
missing=0
mismatch=0
```

起点包含 R3 已准备的 `tests/host/test_postgresql_r2.py` 和 R3 环境阻塞报告。不得还原该测试、重复编写 fixture，或使用旧的 130 文件 R3 快照作为本轮起点。任何不匹配立即停止，不得执行 `restore`、`reset`、`checkout`、`switch` 或覆盖其他角色文件。

结束时以 131 文件起点为基准报告 changed/unchanged/missing；独立测试、报告、矩阵和冻结文件必须零漂移。

## 3. 允许修改

只允许：

```text
migrations/versions/p4_host_user_scope.py
tests/host/test_postgresql_r2.py
tests/host/test_migrations.py
docs/b6-r3-r1-postgresql-history-migration-running.md
docs/coordination/agents/executor.md
```

只有在现有 `test_postgresql_r2.py` 无法保持清晰时，才可新增：

```text
tests/host/test_postgresql_r3.py
```

R3 已经在 `test_postgresql_s1_migration_empty_history_and_round_trip` 中加入 P1 双分录、P2 run/pending 和 P3 import 历史及回滚审计。本轮优先复用和少量修正该用例，不要复制完整 PostgreSQL harness。

## 4. 禁止修改

```text
src/**
migrations/versions/p4_host_identity.py
migrations/versions/p4_host_state.py
tests/independent/**
docs/testing/**
docs/b6-r3-postgresql-history-migration-running.md
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

禁止任何 Git 写操作。不得把执行方测试称为独立验收，也不得把 C11-R1 的独立失败改写成执行方运行结果。

## 5. 第一门禁：取得修改前失败基线

在修改 migration 前：

1. 确认 Docker Desktop Engine 可达、项目 Compose 服务为空；
2. 只启动 `docker compose up -d finance-postgres`；
3. 等待 PostgreSQL `running / healthy`；
4. 只运行已经扩展的精确 PostgreSQL 历史 migration 节点一次；
5. 保存失败类型、migration 阶段、表名、P4 head 是否到达，以及事务回滚后是否仍停在 P3、历史双分录是否保留、是否不存在部分 `user_id` 列。

期望在原 migration 上稳定复现 PostgreSQL `ObjectInUse` 或等价的 pending-trigger ALTER 失败。若原 migration 意外通过、失败位置与独立证据不同、回滚审计失败，立即停止为 `blocked / finished`，不要先改 migration。

Docker Engine 不可达时只检查一次并停止，不启动、重启或维修 Docker Desktop。不要用历史结果、collect-only 或 skip 冒充本轮运行。

## 6. 最小修复合同

在取得执行方失败基线后，只修复 `p4_host_user_scope.py` 的 PostgreSQL 历史回填/ALTER 顺序。

优先方案：

- SQLite 保留现有 nullable column、backfill 和受控 batch rebuild；
- PostgreSQL 添加 `user_id` 时，使用只在迁移期间存在的 bootstrap UUID 常量 server default，并在同一 DDL 中建立非空列，让历史行由 DDL 填充；
- 随即删除 server default，再创建 unique、FK、check 和复合 user 关系；
- bootstrap ID 必须来自 migration 自己确认的唯一 pending owner，并安全构造为 UUID SQL literal；不得接受外部输入；
- 最终 schema 不得保留 `user_id` default，运行时仍显式提供 user ID。

允许采用其他窄范围方案，但必须同时满足：

1. 整个 revision 单事务原子成功或回滚；
2. 合法 P1/P2/P3 历史事实、金额、双分录、状态和关系原值保持；
3. 所有 scoped 行统一回填唯一 bootstrap owner；
4. actor/owner check、每表 `(user_id,id)` unique、自然 unique 和复合 user FK 全部建立；
5. 非法孤儿、矛盾 owner 和跨用户关系继续安全拒绝，不删除、不重归属、不猜测修复；
6. 保持三个 P4 revision 和唯一 `p4_host_state` head，不创建第四 revision；
7. PostgreSQL 与 SQLite 的最终约束形状继续与 ORM 一致；
8. downgrade 和 head→P3→head 语义不变。

严禁在 migration 中手动 `COMMIT`、设置 `session_replication_role`、禁用 trigger/FK/NOT NULL/check、删除或截断历史表、延长超时掩盖失败、简化独立 fixture，或使用 `Base.metadata.create_all()` 代替 Alembic。

如果安全修复必须修改其他 migration、服务代码或冻结合同，立即停止为 `blocked / finished` 并交回总控。

## 7. 修复后执行方门禁

至少运行并分开统计：

1. 修复后的精确 PostgreSQL P3 历史→P4 节点；
2. `tests/host/test_postgresql_r2.py` 完整文件；
3. `tests/host/test_migrations.py` 完整文件；
4. `tests/host/test_postgresql_r1.py` 中 migration/round-trip 相邻节点；
5. `tests/finance/test_migrations.py`；
6. `tests/activity_import/test_migration.py`；实际文件名不同则记录实际路径并运行对应 migration 文件；
7. migration 与变更测试的 Python 编译；
8. `pip check`；
9. `git diff --check`。

真实 PostgreSQL 回归必须证明：

- 到达唯一 `p4_host_state` head；
- P1 金额和正负双分录保持；
- P2 run/pending 状态、双向关系和回填字段保持；
- P3 import batch/candidate 状态、金额和关系保持；
- scoped 表无 NULL user，代表事实全部归属唯一 bootstrap owner；
- 三类复合 user FK、相关 unique/check 在真实 catalog 中存在；
- 无孤儿、无错误重归属，最终无 persistent server default；
- 重复 upgrade 幂等，head→P3→head 保持历史；
- 非法孤儿/矛盾 owner 的升级失败并完整回滚，不留下部分列或错误 head。

若差异只涉及 PostgreSQL add/backfill 顺序且上述门禁全过，不重复 Agent、Host API、认证、memory、完整 P0～P4 或独立测试。

## 8. Docker 边界

本轮执行智能体是 `finance-postgres` 的唯一负责人：

1. 起点确认 Engine 可达且项目 Compose 为空；
2. 只启动 `finance-postgres`；
3. 只用随机 schema 和虚拟数据；
4. 完成或失败后执行普通 `docker compose down`；
5. 最终确认 `COMPOSE_SERVICES_EMPTY`；
6. 禁止 `down -v`、volume 删除、prune、Factory reset、Desktop 重启、context/全局设置和 socket 操作。

## 9. 交付物

新增并完成：

```text
docs/b6-r3-r1-postgresql-history-migration-running.md
```

同时更新执行智能体自己的角色日志。运行说明必须包含：

1. 修改前真实失败基线；
2. 根因确认；
3. 最终修复数据流及其原子性；
4. PostgreSQL 与 SQLite 分支差异；
5. 所有定向测试的 passed/failed/skipped/warning；
6. 历史事实、owner、约束、回滚、幂等和 downgrade 证据；
7. Docker 启动、health、普通 down 和最终空服务；
8. 131 文件起点复算和终点 changed/unchanged/missing；
9. 所有授权修改或新增文件的普通 SHA-256；
10. 明确没有运行或修改独立测试，没有 Git 写操作，没有外部集成。

停止修改后生成新的产品/执行测试有序摘要，交给总控固定 C11-R2 输入。状态只能为：

- 全部门禁通过：`review / finished`；
- 需要扩大范围、真实 PostgreSQL 仍失败或 Docker 再次阻断：`blocked / finished`。

无论结果如何，不得自行启动 C11-R2、测试智能体、技术顾问、Electron、OpenClaw、微信或 DeepSeek。
