# P4-B6-R3 PostgreSQL 历史迁移返修运行说明

## 交付状态

- 任务：`P4-B6-R3`
- 状态：`blocked / finished`
- 阻塞条件：Docker Desktop/Engine 在任务卡允许的唯一一次环境检查中不可达。
- 本轮完成了执行方真实 PostgreSQL 历史回归的代码准备和静态检查，但没有运行 PostgreSQL 失败基线，也没有修改 migration；因此不能宣称 `P4-C11-R1-PG-001` 已由执行方复现、根因已最终确认或缺陷已修复。
- 本文记录执行方现场，不是 C11-R2 独立复验，不表示 P4-A `complete`。

## 130 文件起点门禁

起点清单：`docs/coordination/snapshots/p4-b6-r3-start.sha256`

```text
entries=130
manifest_sha256=ed4cec634ead2a8543066f19c7134f3d0a65d58f39ebe43133ef955129a86770
start_matched=130
start_mismatch=0
start_missing=0
```

起点完全匹配后才修改允许的执行方测试。没有 restore、reset、checkout、switch 或覆盖其他角色文件。

## 执行方失败回归准备

在 `tests/host/test_postgresql_r2.py` 的既有 `test_postgresql_s1_migration_empty_history_and_round_trip` 中扩充执行方自己的 P3 历史 fixture，没有复制独立测试文件，也没有导入独立测试的 seed 或断言。

新增的虚拟历史形状：

- P1：account、expense category、完成的 finance receipt、posted expense transaction、`-4321` account entry 和 `+4321` expense entry；
- P2：paused run、`needs_confirmation` pending、双向 run/pending 关系；
- P3：preview receipt、`previewed` import batch、`create` candidate，金额 `2500`；
- owner/actor 使用项目冻结的 bootstrap UUID；其他 ID 使用随机 UUID；没有真实账户或个人财务数据。

用例已加入修复后所需的正向断言草稿：

- P4 唯一 head 和单行 `alembic_version`；
- P1 金额、正负双分录、交易状态与关系保持；
- P2 run/pending 状态、互相引用、module/profile/version/attempt 回填和 actor/user 一致；
- P3 batch/candidate 状态、金额、关系和 owner/user 一致；
- 代表 scoped 表没有 NULL user；
- transaction、pending、import 三类复合 user FK 没有孤儿；
- 相关复合 FK、`(user_id,id)` unique、actor/owner check 存在；
- 所检查的 `user_id` 列最终没有 persistent server default；
- 再次 upgrade 幂等；head→P3→head 保持旧事实。

异常路径会在 Alembic upgrade 抛出后重新连接，并先验证：

- Alembic 仍为 P3 head；
- 双分录历史仍存在；
- `app_user` 未留下；
- financial transaction、entry、run、pending、import batch/candidate 没有部分 `user_id` 列；

随后重新抛出原始异常，使原 migration 的 `ObjectInUse` 或同类 pending-trigger ALTER 仍表现为失败测试，不会被回滚审计吞掉。

## 修改前失败回归状态

任务卡要求在原 migration 上只运行扩展后的精确 PostgreSQL 节点一次。该运行没有发生：Docker Desktop status 检查在 pytest 启动前失败，因此没有 PostgreSQL schema、Alembic事务或测试数据库连接。

```text
precise_pg_history_node=not_run
passed=0
failed=0
skipped=0
warning=0
```

独立 C11-R1 报告中已有的 `ObjectInUse` 首次失败仅作为 R3 输入，本任务没有把独立结果改写成执行方失败证据。

## 根因与 migration 修复状态

根据只读代码和独立输入，当前 `p4_host_user_scope` 的 PostgreSQL 路径为：

1. 统一更新旧 actor/owner；
2. 给每张 scoped 表添加 nullable `user_id`；
3. 对每张表执行 `UPDATE ... SET user_id=:bootstrap`；
4. 随后逐表执行 `ALTER COLUMN user_id SET NOT NULL`、unique/FK/check DDL；
5. 最后创建复合 user FK。

该顺序与独立失败现象一致：带现有外键的父子历史行被更新后，同一 PostgreSQL migration 事务中仍有约束触发器事件，立即 ALTER 相关表可能被 PostgreSQL 拒绝。任务卡要求执行方真实失败回归确认后才能开始修复；由于环境门禁未通过，本轮没有修改 `migrations/versions/p4_host_user_scope.py`。

因此以下方案仍只是待验证的任务卡推荐方案，不是本轮已实现结果：PostgreSQL 添加 `user_id` 时使用仅迁移期间存在的 bootstrap UUID 常量 server default 和同一 DDL 的 NOT NULL，让历史行由 DDL 回填，再删除 default；SQLite 保留现有 nullable/backfill/batch rebuild 路径。单事务原子性、三个 P4 revision、唯一 `p4_host_state` head、非法历史拒绝和 downgrade 语义均尚待恢复任务验证。

## Docker 检查与资源状态

Docker 操作前重新读取 `docs/coordination/control.md`，版本仍为 `2026-09-27T00:30:00+08:00`，确认 R3 是唯一实现和 `finance-postgres` 环境负责人。

唯一一次环境检查：

```text
docker desktop status
exit=1
Could not retrieve status. Is Docker Desktop running?
```

命令按顺序在 Desktop status 失败后立即退出，没有继续执行 Engine version、Compose 起点检查、`docker compose up` 或 pytest。R3 任务卡明确规定 Engine 不可达时只检查一次并停止、不得自行维修 Docker Desktop，因此：

- 没有执行第二次 Engine 检查；
- 没有执行 `docker desktop start`、停止或重启 Desktop；
- 没有启动 `finance-postgres`；
- 没有创建项目容器、网络或随机 schema；
- 没有容器可供普通 down；
- Compose 最终空列表因 Engine 未检查成功而记为 `unverified`，没有伪写 `COMPOSE_SERVICES_EMPTY`；
- 没有删除 volume、prune、Factory reset、修改 context/全局设置或触碰 socket/备份目录。

## 静态检查

- `python -m compileall -q tests/host/test_postgresql_r2.py`：退出码 0。
- `python -m pip check`：退出码 0，`No broken requirements found.`
- `git diff --check`：退出码 0；只输出起点工作树已有文件的 LF→CRLF 提示，没有 whitespace error。
- 没有运行任何 pytest；因此没有测试 passed/failed/skipped/warning 可报告。

## 未运行的任务卡门禁

以下均因 Docker 环境停止条件而没有运行：

1. 原 migration 的精确 PostgreSQL 历史失败节点；
2. 修复后的精确节点；
3. 完整 `tests/host/test_postgresql_r2.py`；
4. 完整 `tests/host/test_migrations.py`；
5. Host R1 migration/round-trip 节点；
6. `tests/finance/test_migrations.py`；
7. `tests/activity_import/test_migration.py`；
8. PostgreSQL 非法孤儿/矛盾 owner 回滚验证；
9. migration 编译和最终 migration diff 验证。

没有重复 Agent、Host API、认证、memory、完整 P0～P4 或独立测试。

## 文件边界

相对 130 文件起点的收口状态：

- unchanged：129；
- changed：1；
- missing/deleted：0；
- 唯一 changed：`tests/host/test_postgresql_r2.py`；
- added：本运行说明；
- 角色日志：`docs/coordination/agents/executor.md` 按协作规则更新，位于产品/执行测试快照之外。

普通 SHA-256：

- `tests/host/test_postgresql_r2.py`：`671269d182fa37d7c66b3fe056d1bf4dc6d8091bd14d6eb9668d20f0cdf87e43`
- `migrations/versions/p4_host_user_scope.py` 保持起点摘要：`649cf372e9bbadc6aaecf6bad4f7daac9b1be68fb663c4dc36b8376df9817e8c`
- `tests/host/test_migrations.py` 保持起点摘要：`9e6d77a83887d8c80a7cdd27210d04500d1bd35ae6d8662d9bfbce9ecdaf62d5`
- 独立 fixture 保持 `1cbae0fae892a23b6d7dfa0c6c36d5f2799bd8f22c38bcfcc6c6e7431779b796`
- 独立 PostgreSQL 文件保持 `12b1ecea9974ebdd3431d1fdc458cdad3476f2a7a95c8291d7a87c8c2775b920`

本运行说明与 executor 日志的最终普通 SHA-256，以及把起点 130 行替换执行测试摘要并加入本运行说明后的有序总摘要，在文件停止修改后记录于 executor 日志和交付消息，避免自引用改变摘要。

## 停止与交接

- 没有修改或运行 `tests/independent/**`，没有修改独立报告、矩阵、冻结、control、overview 或其他角色状态。
- 没有修改任何 product service、其他 P4 migration、Compose/依赖配置或 Git 状态。
- 没有启动 C11-R2、测试智能体、技术顾问、Electron、OpenClaw、微信或 DeepSeek。
- 当前执行方停止修改和测试，等待总控确认 Docker Desktop Engine 恢复后重新派发 R3。
- 恢复时必须保留当前执行方 fixture，从原 migration 的精确节点唯一一次实际失败开始；不得直接跳到 migration 修复或把独立失败当作执行方失败基线。
