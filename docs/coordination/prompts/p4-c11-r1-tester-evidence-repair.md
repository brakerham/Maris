# P4-C11-R1 测试智能体 Prompt：历史迁移证据补强

你是项目中既有的**测试智能体**，唯一负责 `P4-C11-R1`。本任务只修复 C11 独立验收证据中的历史迁移覆盖缺口，并准确说明一处 P4 错误合同演进。不得修改产品代码、migration、执行方测试、依赖或 Git 状态；不得重新执行整套 C11、64 项矩阵或全部 P0～P4 回归。

即使全部通过，你也只能提交 `review / finished`，不能宣布 P4-A `complete`。

## 1. 开始前必须读取

按顺序读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. `docs/coordination/control.md`
6. `docs/coordination/agents/tester.md`
7. `docs/coordination/prompts/p4-c11-host-foundation-tester.md`
8. `docs/p4-c11-coordinator-review.md`
9. `docs/testing/phase-4-c11-host-foundation-report.md`
10. `docs/phase-4-interface-freeze.md`
11. `docs/phase-4-interface-freeze-002.md`
12. `docs/phase-4-d10-b6-repair-architecture.md`
13. `docs/coordination/snapshots/p4-c11-start.sha256`
14. `docs/coordination/snapshots/p4-c11-r1-start.sha256`

先在 `docs/coordination/agents/tester.md` 记录接单、当前步骤、时间、心跳、下一检查点、等待对象和可观察 pytest/Docker 会话。

## 2. 两层固定快照

产品快照继续使用：

```text
docs/coordination/snapshots/p4-c11-start.sha256
entries=105
manifest_sha256=65ee400893171d6caf19f2bf5adf20a4432f1f3c8048d5c381b718fc10360126
```

开始与结束都必须：

```text
matched=105
missing=0
mismatch=0
```

测试方 C11 起点使用：

```text
docs/coordination/snapshots/p4-c11-r1-start.sha256
entries=23
manifest_sha256=1c59d9e08abf9acea64324b72e3c8d63cda8eff7691239cdaa5baf94e9bdac73
```

开始前要求 23/23 匹配。结束时报告 23 个起点文件中哪些修改、哪些保持不变，以及新增文件；不得覆盖或恢复不匹配文件。

## 3. 允许修改

只允许：

```text
tests/independent/host/test_migration_acceptance.py
tests/independent/host/test_postgresql_acceptance.py
tests/independent/finance/test_migration_sqlite_contract.py
tests/independent/agent_finance/test_tools_and_lifecycle.py
docs/testing/phase-4-c11-host-foundation-report.md
docs/testing/phase-4-c11-r1-evidence-report.md
docs/testing/phase-4-modular-agent-host-test-matrix.md
docs/coordination/agents/tester.md
```

如果可以通过新增独立 helper 避免重复 SQL，只能在 `tests/independent/host/**` 内新增。不得修改其他旧独立测试。

禁止修改：

```text
src/**
migrations/**
tests/host/**
tests/finance/**
tests/agent_finance/**
tests/activity_import/**
compose.yaml
alembic.ini
pyproject.toml
requirements*.txt
docs/coordination/control.md
docs/coordination/overview.md
docs/coordination/snapshots/**
docs/coordination/agents/executor.md
docs/coordination/agents/technical-adviser.md
```

禁止任何 Git 写操作。

## 4. 必须修复的问题

### 4.1 恢复 P1 首版正向迁移证据

`tests/independent/finance/test_migration_sqlite_contract.py` 中原 `FIRST_REVISION` 场景不能再用 `upgrade(..., HEAD_REVISION)` 开始。必须真正从 `bfc163b9b8e9` 或与原测试目标等价的旧 revision 建库。

当前 ORM/FinanceService 依赖 P4 user scope，不适合直接操作旧 schema。使用 revision 对应的直接 SQL 或独立低层 fixture 写入代表性 P1 事实，再升级到 `p4_host_state`。至少验证：

- 金额 minor 整数值没有重写或丢失；
- 账户、分类、交易及 entry 的数量和关键值保持；
- P4 `user_id` 被安全回填为 bootstrap owner；
- 没有空 owner、孤儿或错误重归属；
- Alembic 最终是唯一 `p4_host_state` head。

测试名称必须与实际起点一致。不得从最新 head 开始后仍称作 first revision upgrade。

### 4.2 补足独立 P0～P3 历史升级

在 C11 独立 migration 测试中增加明确的旧历史正向升级证据：

1. SQLite：至少在 P3 head 创建代表性 P1 财务、P2 agent run/pending 和 P3 activity import 事实，再升级到 P4；验证事实、关系、状态、owner 回填和 `PRAGMA foreign_key_check`。
2. PostgreSQL：随机 schema 在 P3 head 写入代表性 P1/P2/P3 事实，再升级到 P4；验证事实保持、bootstrap owner 回填、三类复合用户关系、单 head 和零孤儿。

这里的“P0～P3 历史”表示升级前数据库包含此前各阶段已经存在的代表性持久事实；P0 无持久表时需在报告中明确说明，而不是伪造 P0 数据表。

可以复用数据库连接、随机 schema 和清理 fixture 机械结构；历史数据构造、预期值和验收断言必须由独立测试自己定义。不得把执行方 `test_postgresql_s1_migration_empty_history_and_round_trip` 的通过结果当作本任务独立证据。

### 4.3 准确记录取消错误码合同演进

保留 `pending_action_cancelled` 断言，因为 D10 已冻结：cancelled pending 再 confirm 返回 409 `pending_action_cancelled`。

在 C11 主报告和 R1 报告明确说明：

- 这是一项 P4 合同演进，不是 fixture 适配；
- 原业务不变量仍保留：cancel 后为终态、confirm 失败、财务写入为零；
- P2 的 `confirmation_required` 仍用于缺少/错误确认上下文等适用状态，不用于已取消 pending。

定向复跑该节点，证明新稳定错误和零写入。

## 5. 有限验证范围

先运行修改节点；修正测试自身错误后，最终只运行：

1. `tests/independent/finance/test_migration_sqlite_contract.py`；
2. `tests/independent/host/test_migration_acceptance.py`；
3. `tests/independent/agent_finance/test_tools_and_lifecycle.py::test_supplement_cancel_and_confirm_after_cancel`；
4. 新增或修改的 PostgreSQL 历史升级节点；
5. 如果 PostgreSQL 共用 fixture 被修改，只复跑 `tests/independent/host/test_postgresql_acceptance.py` 的 5 个既有节点加新增节点。

不要重复：

- C11 64 项全量；
- P0 102+2 回环套件；
- P1/P2/P3 全量本地回归；
- 执行方 P0～P4 全量；
- 已通过且未受影响的 PostgreSQL 基线。

报告必须把历史 C11 结果与本轮定向结果分开，不把历史 passed 重新计成本轮执行。

## 6. Docker 边界

只有 PostgreSQL 定向节点需要时才使用 Docker。操作前重新读取最新 control：

1. 确认项目 Compose 为空；
2. 只启动 `finance-postgres`；
3. 等待 healthy，使用随机 schema 和虚拟数据；
4. 完成或失败后普通 `docker compose down`；
5. 确认 `COMPOSE_SERVICES_EMPTY`；
6. 禁止 `down -v`、volume 删除、prune、Factory reset、Desktop 重启、context/全局设置/socket 操作。

Engine 不可达时只检查一次并停止，不恢复 Docker Desktop。

## 7. 报告与矩阵

新增：

```text
docs/testing/phase-4-c11-r1-evidence-report.md
```

同时修正 C11 主报告中“所有旧独立修改都只是 fixture”的不准确表述，列出：

- 真正的 fixture 适配；
- `pending_action_cancelled` 合同演进；
- 被恢复的 P1 首版迁移场景；
- 新增 SQLite/PostgreSQL P0～P3 历史升级节点；
- 本轮命令、passed/failed/skipped/warning；
- 105 产品快照前后结果；
- 23 文件测试方快照变化；
- Docker 资源收口；
- 是否仍有开放产品 P0/P1 或独立证据缺口。

矩阵只在证据节点变化时更新相应 P4-A 行；P4-B/C/D 56 行保持 `not_run`。

## 8. 停止条件和最终状态

以下情况立即停止、收口资源并报告：

- 105 产品快照漂移；
- 必须修改产品/migration/执行方测试才能通过；
- 旧历史升级丢数据、错误归属、产生孤儿或多 head；
- PostgreSQL 实际约束/回填不符合冻结；
- Docker/pytest 连续两个检查点没有新证据。

全部定向证据通过、105 产品文件零漂移、报告纠正且资源清空时，提交 `review / finished` 并建议总控接受 P4-A。最终 `complete` 和 Git 提交仍由头脑风暴总控决定。
