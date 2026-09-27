# P4-C11-R1 历史迁移独立证据报告

- 角色：测试智能体
- 任务：`P4-C11-R1`
- 控制版本：`2026-09-27T00:12:00+08:00`
- 最终状态：`blocked / finished`
- 数据边界：仅随机 schema 与虚拟 P1/P2/P3 数据
- 结论权限：本报告提交独立测试结论；P4-A 的返修、接受和 `complete` 由头脑风暴总控决定

## 1. 结论

SQLite 的历史迁移证据已补齐，取消错误合同也已定向通过；真实 PostgreSQL 的 P3→P4 历史正向升级发现一个新的产品 P0 阻断 `P4-C11-R1-PG-001`。在随机 P3 schema 写入合法 P1 双分录财务事实、P2 run/pending 与 P3 import batch/candidate 后，`p4_host_user_scope` 不能完成升级。失败发生在给 `financial_transaction.user_id` 设置非空约束时，PostgreSQL 报告该表仍有待处理的触发器事件。

因此 P4-A 当前不能接受。矩阵中的 `P4A-DB-05`、`P4A-DB-06` 已从 `passed` 纠正为 `failed`；P4-A 最终为 62 passed、2 failed，P4-B/C/D 的 56 项继续 `not_run`。测试方没有修改产品 migration，也没有用缩减历史 fixture、重试覆盖或执行方结果替代首次失败。

## 2. 固定快照

### 2.1 产品快照

起点和收口时均逐项复算：

```text
docs/coordination/snapshots/p4-c11-start.sha256
entries=105
matched=105
missing=0
mismatch=0
manifest_sha256=65ee400893171d6caf19f2bf5adf20a4432f1f3c8048d5c381b718fc10360126
```

105 个产品、migration、执行方测试和运行说明文件全部保持不变。

### 2.2 测试方起点快照

修改前逐项复算：

```text
docs/coordination/snapshots/p4-c11-r1-start.sha256
entries=23
matched=23
missing=0
mismatch=0
manifest_sha256=1c59d9e08abf9acea64324b72e3c8d63cda8eff7691239cdaa5baf94e9bdac73
```

收口相对起点为 6 changed、17 unchanged、0 missing。

改变的 6 个起点文件：

```text
docs/coordination/agents/tester.md
docs/testing/phase-4-c11-host-foundation-report.md
docs/testing/phase-4-modular-agent-host-test-matrix.md
tests/independent/finance/test_migration_sqlite_contract.py
tests/independent/host/test_migration_acceptance.py
tests/independent/host/test_postgresql_acceptance.py
```

保持不变的 17 个起点文件：

```text
tests/independent/activity_import/conftest.py
tests/independent/activity_import/test_migration_contract.py
tests/independent/activity_import/test_postgresql_contract.py
tests/independent/agent_finance/conftest.py
tests/independent/agent_finance/test_http_and_migration.py
tests/independent/agent_finance/test_idempotency_and_loop.py
tests/independent/agent_finance/test_postgresql_agent_contract.py
tests/independent/agent_finance/test_tools_and_lifecycle.py
tests/independent/finance/conftest.py
tests/independent/finance/test_ledger_contract.py
tests/independent/finance/test_postgresql_contract.py
tests/independent/finance/test_refund_activity_contract.py
tests/independent/host/__init__.py
tests/independent/host/conftest.py
tests/independent/host/test_api_acceptance.py
tests/independent/host/test_contract_acceptance.py
tests/independent/host/test_state_acceptance.py
```

新增文件：

```text
tests/independent/host/history_fixtures.py
docs/testing/phase-4-c11-r1-evidence-report.md
```

## 3. 恢复的独立历史证据

### 3.1 P1 首版→P4 SQLite

`test_first_p1_revision_finance_facts_upgrade_to_p4_without_rewriting_data` 的实际起点为 `bfc163b9b8e9`。测试不导入当前 ORM 写旧 schema，而是用直接 SQL 创建：

- 一个账户；
- 一项收入分类和一项支出分类；
- 一个完成的 command receipt；
- 一笔 `expense` 交易；
- `-1234` 的 account entry 和 `+1234` 的 expense entry。

正向升级到 `p4_host_state` 后验证账户、分类、交易、entry 数量与关键值完全保持，两个 minor 值仍是 SQLite `integer`，所有带 `user_id` 的表没有空 owner，代表事实都归属唯一 bootstrap owner，没有 FK 孤儿，Alembic 只有一个 `p4_host_state` head。

完整文件结果：8 passed。

### 3.2 P3→P4 SQLite

`test_c11_sqlite_p3_history_forward_upgrade_preserves_p1_p2_p3_facts` 在 `c82d7a4f901e` 直接写入：

- P1：账户、分类、receipt、expense 交易和双分录；
- P2：paused run、needs-confirmation pending 及双向关联；
- P3：previewed import batch 与 create candidate。

升级后验证 P1 金额和关系、P2 状态和 P4 module/profile/attempt 回填、P3 import 关系和金额、bootstrap owner、legacy conversation 回填、三类代表关系零孤儿、`PRAGMA foreign_key_check` 为空和单 head。

完整 Host migration 文件结果：3 passed。P0 没有持久表，因此本任务没有伪造 P0 数据表。

### 3.3 P3→P4 PostgreSQL

新增节点 `test_c11_pg_p3_history_forward_upgrade_preserves_p1_p2_p3_facts` 使用随机 schema，并复用现有连接、随机 schema 与清理机制。历史数据构造、预期值和断言来自测试方新增的低层 helper，没有引用执行方历史 seed 或执行方通过结果。

节点实际结果：1 failed。失败发生在 P4 migration 内，尚未到达事实保持、bootstrap owner、三类复合 user FK、单 head和零孤儿的最终断言。

## 4. 产品缺陷 `P4-C11-R1-PG-001`

- 严重级别：P0 / 阻断 P4-A 接受
- 环境：真实 PostgreSQL 17.6，Docker Engine 29.8.0，Compose 5.5.1，随机测试 schema
- 精确节点：`tests/independent/host/test_postgresql_acceptance.py::test_c11_pg_p3_history_forward_upgrade_preserves_p1_p2_p3_facts`
- 前置：数据库停在 P3 head；存在合法 P1 expense + 双分录、P2 run/pending、P3 import batch/candidate；所有 owner 使用同一个冻结 bootstrap UUID
- 操作：Alembic `upgrade p4_host_state`
- 预期：历史事实原值保持并统一安全回填 bootstrap owner；三个 P4 revision 成为唯一 head；无空 owner、孤儿或重归属
- 实际：`p4_host_user_scope` 在执行 `ALTER TABLE financial_transaction ALTER COLUMN user_id SET NOT NULL` 时失败；PostgreSQL 错误类别为 `ObjectInUse`，安全摘要为“表存在待处理的触发器事件”
- 影响：带合法财务交易和 entry 的 P0～P3 PostgreSQL 库不能升级到 P4；此前从空库或 P4 head 开始的迁移/约束测试不能覆盖该路径
- 数据结果：测试 schema 由独立 fixture 清理；未写入真实数据；没有修改 migration 或执行方测试
- 初步原因：从现象推断，user-scope migration 在同一 PostgreSQL migration 事务中先更新有外键关系的历史行，随后立即 ALTER 相关表，触发 PostgreSQL 对 pending FK trigger events 的限制。该原因需由执行智能体在返修任务中确认

## 5. 取消错误合同演进

精确复跑：

```text
tests/independent/agent_finance/test_tools_and_lifecycle.py::test_supplement_cancel_and_confirm_after_cancel
1 passed
```

`pending_action_cancelled` 是 D10/P4-IF-002 冻结后的 P4 合同演进，不是 fixture 适配。测试继续证明：cancel 后 pending 为终态；后续 confirm 失败；expense 数量保持零。P2 的 `confirmation_required` 仍适用于缺少或错误确认上下文等状态，不适用于已取消 pending。

该测试文件在 R1 起点已经包含正确断言，本轮只定向执行，文件保持原 SHA-256 `39f419641de09ac9842d64ccc7f651d41398af5075217063522afccd50150b9b`。

## 6. 本轮实际命令结果

| 范围 | 结果 | warning / skip | 判定 |
|---|---:|---|---|
| `tests/independent/finance/test_migration_sqlite_contract.py` | 8 passed | 0 skip | 通过 |
| `tests/independent/host/test_migration_acceptance.py` | 3 passed | 15 warnings；1 个既有 Starlette/AnyIO、14 个 Python sqlite3 datetime adapter 弃用提示 | 通过，warning 不影响断言 |
| cancelled 精确节点 | 1 passed | 0 skip | 通过 |
| PostgreSQL 历史正向升级精确节点 | 1 failed | 1 个既有 Starlette/AnyIO warning，0 skip | 产品迁移阻断 |

首次 PostgreSQL 命令包装曾因 PowerShell 正则引号解析失败，pytest 未收集、数据库测试未开始；改用 `docker compose config --format json` 在内存读取测试配置后，唯一一次实际 pytest 运行得到上述产品失败。没有通过重跑覆盖产品结果。

按任务卡没有执行 C11 64 项全量、P0 102+2、P1/P2/P3 全量、执行方 P0～P4、既有五个 Host PG 节点或其他已通过 PG 基线。公共 PostgreSQL fixture 未修改，因此无需扩展运行范围。

## 7. Docker 与隐私收口

- 操作前重新读取 control，版本仍为 `2026-09-27T00:12:00+08:00`；本测试智能体是唯一负责人。
- 启动前 Engine 可达，Compose 只定义 `finance-postgres`，项目服务为空。
- 只启动 `finance-postgres`，达到 `running / healthy` 后运行一个新增 PG 节点。
- 失败后立即执行普通 `docker compose down`；最终为 `COMPOSE_SERVICES_EMPTY`。
- 未使用 `-v`，未删除 volume、prune、重置数据库、重启 Docker Desktop 或修改全局设置。
- Compose 测试密码只在进程环境中构造，没有写入报告、日志或角色状态。
- 所有历史事实为虚拟 canary；报告没有连接密码、token、个人财务数据、原始外部身份或未脱敏 SQL 参数。

## 8. 测试方文件摘要

| 文件 | SHA-256 |
|---|---|
| `tests/independent/finance/test_migration_sqlite_contract.py` | `139a7e0d70f9aa3649dceb06a28b270b2fd72e9e06ae137d75c5fab5e33c2a07` |
| `tests/independent/host/test_migration_acceptance.py` | `0e2dfdf2dd9e9bf626550c6c83a79003c011731df11aa2327310472836e1ff69` |
| `tests/independent/host/test_postgresql_acceptance.py` | `12b1ecea9974ebdd3431d1fdc458cdad3476f2a7a95c8291d7a87c8c2775b920` |
| `tests/independent/host/history_fixtures.py` | `1cbae0fae892a23b6d7dfa0c6c36d5f2799bd8f22c38bcfcc6c6e7431779b796` |

文档及状态文件的最终摘要记录在测试智能体完成日志，避免报告自引用。

## 9. 建议与复验边界

总控应派发一个窄范围执行返修，修复真实 PostgreSQL 历史行存在时的 `p4_host_user_scope` 升级顺序或事务边界，并生成新的固定产品快照。执行方需要证明合法双分录历史能够升级，同时失败事务不留下半迁移。

返修后测试方只需绑定新快照，复跑本次失败的 PostgreSQL 历史节点，并按 migration 改动范围补一组相邻 SQLite/PG migration 回归。除非新改动扩大影响，不应重复完整 C11、全部 64 项或已通过的外部/执行方基线。
