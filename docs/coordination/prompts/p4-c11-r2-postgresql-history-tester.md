# P4-C11-R2 测试智能体 Prompt：PostgreSQL 历史迁移定向独立复验

你是项目中既有的**测试智能体**，唯一负责 `P4-C11-R2`。独立复验执行方 `P4-B6-R3-R1-E1` 对 P0 缺陷 `P4-C11-R1-PG-001` 的修复，并收口矩阵 `P4A-DB-05`、`P4A-DB-06`。

这是有限复验，不重复完整 C11、64 项 P4-A、P0～P3 全量回归、认证/Agent/memory/API 全量测试或外部集成。测试通过只能提交 `review / finished` 和建议；P4-A 的最终接受、Git 提交和 `complete` 由头脑风暴总控决定。

## 1. 开始前必读

按 AGENTS.md 顺序读取公共协调文件，并重点读取：

1. `docs/coordination/control.md`
2. `docs/coordination/agents/tester.md`
3. `docs/p4-c11-r1-coordinator-review.md`
4. `docs/testing/phase-4-c11-r1-evidence-report.md`
5. `docs/testing/phase-4-c11-host-foundation-report.md`
6. `docs/testing/phase-4-modular-agent-host-test-matrix.md`
7. `docs/b6-r3-postgresql-history-migration-running.md`
8. `docs/b6-r3-r1-postgresql-history-migration-running.md`
9. `docs/b6-r3-r1-e1-postgresql-history-migration-running.md`
10. `migrations/versions/p4_host_user_scope.py`，只读
11. `tests/host/test_postgresql_r2.py`，只读执行方证据
12. `tests/independent/host/history_fixtures.py`
13. `tests/independent/host/test_postgresql_acceptance.py`
14. `tests/independent/host/test_migration_acceptance.py`
15. `docs/coordination/snapshots/p4-c11-r2-start.sha256`

在 tester 角色文件记录接单、当前步骤、开始时间、心跳、下一检查点、等待对象和 Docker/pytest 会话。任何 Docker 操作前重读最新 control；若负责人、状态或用户指令变化，安全停止。

## 2. 固定起点

```text
docs/coordination/snapshots/p4-c11-r2-start.sha256
entries=133
manifest_sha256=7ab8388edcadff5515aa5f038df13e40ae35233f2e4298c61fcd091357929fd3
```

开始前逐行复算必须为：

```text
matched=133
missing=0
mismatch=0
```

任何不匹配立即停止，不得 restore、reset、checkout、switch 或覆盖执行方文件。测试结束后再次复算固定的产品、migration 和执行方测试；它们必须零漂移。

E1 必须保持的关键摘要：

```text
migrations/versions/p4_host_user_scope.py
82bc31919bd5483650f40c0281c42764813f6f5bc0db8d1898b7ad71a3d5a800

tests/host/test_postgresql_r2.py
0da6346142304f36964370b8f48344c6ab16309058413ffa6bb45d24ae922d6f

P4-B6-R3-R1-E1-END-SHA256
a89874cfb48b5c8edc8f4260d2f6ce1f206ac02f61e31bb56f4b33ea1282eee9
```

## 3. 允许修改

只允许：

```text
tests/independent/host/test_postgresql_acceptance.py
tests/independent/host/history_fixtures.py  # 仅独立非法历史构造确有需要时
docs/testing/phase-4-c11-r2-postgresql-history-report.md
docs/testing/phase-4-c11-host-foundation-report.md
docs/testing/phase-4-modular-agent-host-test-matrix.md
docs/coordination/agents/tester.md
```

优先在现有独立 PostgreSQL 文件中增加最小参数化非法历史用例，不复制执行方测试函数、fixture 或断言。可以只读参考数据形状，但独立构造、运行和结论必须属于测试方。

## 4. 禁止修改

```text
src/**
migrations/**
tests/host/**
tests/agent_finance/**
tests/finance/**
tests/activity_import/**
docs/b6-*.md
docs/phase-4-*.md
docs/coordination/control.md
docs/coordination/overview.md
docs/coordination/snapshots/**
docs/coordination/agents/executor.md
docs/coordination/agents/technical-adviser.md
compose.yaml
alembic.ini
pyproject.toml
requirements*.txt
```

禁止任何 Git 写操作。不得通过修改产品、migration、执行测试、缩减历史 fixture、增加 skip/xfail、放宽断言、延长产品超时或重复运行挑选成功结果来关闭缺陷。

## 5. 必须取得的独立证据

### 5.1 原失败节点

唯一实际运行一次：

```text
tests/independent/host/test_postgresql_acceptance.py::test_c11_pg_p3_history_forward_upgrade_preserves_p1_p2_p3_facts
```

必须证明：

- P3 head 含 P1 account/category/transaction/正负双分录、P2 run/pending、P3 import batch/candidate 时可升级到唯一 `p4_host_state`；
- 金额、状态、ID、双向引用和 import 金额原值保持；
- 统一回填唯一 bootstrap owner；
- scoped 表无 NULL user；
- transaction、pending、import 三类复合 user FK 无孤儿；
- 真实 catalog 中复合 FK、`(user_id,id)` unique、check 均存在；
- 所检查的 `user_id` 列没有 persistent server default；
- 重复 upgrade 和允许的 head→P3→head 保持历史；
- 原 `ObjectInUse` 不再出现。

### 5.2 `P4A-DB-06` 非法历史

由测试方独立新增或补强两个真实 PostgreSQL 场景：

1. 孤儿 `pending_action.run_id`；
2. 与唯一 bootstrap owner 矛盾的 `pending_action.actor_id`。

每个场景必须验证 migration 在任何 P4 user-scope DDL 持久化前安全拒绝，并且：

- Alembic 仍停在 P3 head；
- P1 双分录和非法输入原值保留；
- 没有 `app_user`；
- 代表表没有部分 `user_id` 列；
- 不删除、不重归属、不自动修复损坏数据；
- 错误信息足以区分 orphan 与 contradictory owner，且不泄漏连接凭据或真实数据。

若为了构造孤儿必须在随机隔离 schema 中去掉旧单 ID FK，只能发生在测试准备中；产品 migration 和真实项目配置不得改变。

### 5.3 相邻回归

在原失败和非法历史独立节点通过后，只运行：

1. `test_c11_pg_migration_round_trip_and_real_constraint_catalog`；
2. `tests/independent/host/test_migration_acceptance.py` 完整文件；
3. `tests/host/test_postgresql_r2.py` 完整文件，作为执行方兼容回归单独统计；
4. `tests/host/test_migrations.py` 完整文件，作为执行方 SQLite 兼容回归单独统计；
5. 修改的独立测试编译、`pip check`、`git diff --check`。

不运行完整 C11、其他四个 Host 独立 PG 业务节点、P0～P3 全量、认证/并发/Agent/memory/API、Electron、OpenClaw、微信或 DeepSeek。只有新增失败显示影响范围超出 migration 时才停止并交回总控，不自行扩大。

## 6. Docker 与资源

本任务开始后，测试智能体是 `finance-postgres` 的唯一负责人：

1. 检查 Engine 可达且项目 Compose 为空；
2. 只启动 `docker compose up -d finance-postgres`；
3. 等待 `running / healthy`；
4. 只使用随机 schema 和虚拟数据；
5. 完成或失败后普通 `docker compose down`；
6. 最终确认 `COMPOSE_SERVICES_EMPTY`；
7. 禁止 `down -v`、volume 删除、prune、Factory reset、Desktop 重启、context/全局设置和 socket 操作。

Engine 不可达只检查一次并停止，不自行维修 Docker。用户应保持 Docker Desktop 运行。

## 7. 缺陷和矩阵结论

只有以下条件全部满足，才可建议关闭 `P4-C11-R1-PG-001` 并把 `P4A-DB-05`、`P4A-DB-06` 改为 `passed`：

- 原独立历史正向节点通过；
- 两类独立非法历史安全拒绝与完整回滚通过；
- PG round-trip/catalog 通过；
- SQLite 独立 migration 文件通过；
- 两个执行方兼容文件通过；
- 固定产品/migration/执行测试零漂移；
- Docker 资源安全收口；
- 没有新的 P0/P1 产品缺陷。

若任一条件失败，保持相应矩阵项 `failed` 或 `blocked`，提交单次可复现证据，不继续扩大测试或修产品。

## 8. 交付

新增：

```text
docs/testing/phase-4-c11-r2-postgresql-history-report.md
```

同步更新主 C11 报告、P4 矩阵和 tester 角色日志。报告必须包含：

- 133 文件起终点快照；
- 原失败节点、两类非法历史、相邻 PG/SQLite 和执行方兼容回归的分别统计；
- `P4-C11-R1-PG-001` 是否关闭及依据；
- `P4A-DB-05/06` 最终状态；
- Docker 启动、health、普通 down 和最终空服务；
- warning/环境问题、隐私检查和未运行范围；
- 所有测试方修改/新增文件普通 SHA-256。

完成后停在 `review / finished` 或 `blocked / finished`，不得自行宣布 P4-A `complete`、修改产品或执行 Git 写操作。
