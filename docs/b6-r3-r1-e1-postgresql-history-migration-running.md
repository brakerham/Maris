# P4-B6-R3-R1-E1 PostgreSQL 历史迁移返修运行说明

## 交付状态

- 任务：`P4-B6-R3-R1-E1`
- 执行角色：执行智能体
- 状态：`review / finished`
- 范围：只修复 `p4_host_user_scope` 在真实 PostgreSQL P3 历史升级时的 pending-trigger ALTER 阻断，并补充执行方非法历史原子回滚测试。
- 结论：修改前真实失败已按任务卡唯一复现；最小 migration 修复、真实 PostgreSQL 历史迁移、SQLite 相邻迁移、幂等、downgrade/upgrade 往返及非法图回滚门禁全部通过。
- 本文记录执行方开发与自测证据，不是 C11-R2 独立验收，不代表 P4-A `complete`。

## 控制面与固定输入

- 接单时最新 control 版本：`2026-09-27T11:51:00+08:00`。
- control 明确指定既有执行智能体为 E1 和 `finance-postgres` 唯一负责人；测试智能体、技术顾问和 C11-R2保持停止。
- 固定输入：`docs/coordination/snapshots/p4-b6-r3-r1-start.sha256`。
- 起点复算：131 matched、0 mismatch、0 missing、0 invalid。
- 起点清单 SHA-256：`5aa1db6c395e745ad1bd96a92a40ece9d69bbdcc837e7234d47d12f3badeb9bb`。
- 保留 R3 已准备的 P1 双分录、P2 run/pending、P3 import 历史 fixture 和异常回滚审计；没有 restore、重写或复制独立 fixture。
- 两份旧环境阻塞报告只读保留。

## Docker 与 PostgreSQL 环境

接管前和停止服务前均重新读取最新 control，版本和唯一负责人没有变化。

接管检查：

```text
docker context: desktop-linux
Docker Client: 29.8.0
Docker Server: 29.8.0
Server OS: linux
COMPOSE_SERVICES_EMPTY_AT_START
```

Docker Desktop CLI 状态表字段显示 `stopped`，但 Engine API、server version 和 Compose 均成功响应；任务卡的 Engine 可达门禁实际通过。

只执行 `docker compose up -d finance-postgres`。唯一容器为：

```text
name=wife-system-finance-postgres-1
container=2f159a07b0b2
port=127.0.0.1:55432
state=running
health=healthy
```

测试只使用各 fixture 创建的随机 schema 和虚拟数据。所有测试完成后执行普通 `docker compose down`，容器和项目网络均正常移除，最终检查返回：

```text
COMPOSE_SERVICES_EMPTY
```

没有执行 `down -v`、volume 删除、prune、Factory reset、Desktop 启停、context/全局设置或 socket 操作。

## 修改前真实失败基线

在 migration SHA-256 仍为 `649cf372e9bbadc6aaecf6bad4f7daac9b1be68fb663c4dc36b8376df9817e8c` 时，只运行一次：

```text
tests/host/test_postgresql_r2.py::test_postgresql_s1_migration_empty_history_and_round_trip
```

结果：`1 failed, 3 warnings`。真实异常为：

```text
psycopg.errors.ObjectInUse:
cannot ALTER TABLE "financial_transaction" because it has pending trigger events

SQL:
ALTER TABLE financial_transaction ALTER COLUMN user_id SET NOT NULL
```

失败发生在 `p4_host_user_scope`：旧实现先逐表 `UPDATE user_id`，随后对 `financial_transaction.user_id` 执行 `SET NOT NULL`。现有财务父子外键使 UPDATE 留下待处理的约束触发器事件，PostgreSQL 拒绝同事务内紧随其后的 ALTER。

测试异常路径在重新抛出原始异常前已经证明：

- Alembic 仍停在 P3 head `c82d7a4f901e`；
- P1 transaction 的两条分录仍完整；
- `app_user` 不存在；
- financial transaction、entry、run、pending、import batch/candidate 均没有部分 `user_id` 列。

因此，失败类型、阶段、表和完整事务回滚均与任务卡预期一致。C11-R1 的独立失败只作为输入，没有被改写为本轮执行方结果。

## 最小 migration 修复

只修改 `migrations/versions/p4_host_user_scope.py` 的 PostgreSQL 历史填充顺序：

1. migration 查询并要求恰好一个 `pending_setup` bootstrap owner；
2. 在任何 P4 user-scope DDL 前验证矛盾 owner 和遗留孤儿关系；
3. bootstrap owner ID 经 Python `uuid.UUID` 解析和规范化后，才构造 PostgreSQL UUID 常量 DDL literal；该值只来自 migration 自己查询的 owner，不接受外部输入；
4. PostgreSQL 对每张 scoped 表使用单条 `ADD COLUMN user_id UUID DEFAULT '<bootstrap>'::uuid NOT NULL`，由 DDL 填充历史行并同时建立非空约束；
5. 紧接着删除该列的 server default；
6. 完成全表 owner/graph 验证后，创建 `(user_id,id)` unique、user FK、自然 unique、actor/owner check 和复合 user FK；
7. 运行时最终 schema 不保留 `user_id` default，应用仍须显式写入 user ID。

SQLite 分支保持原语义：先添加 nullable `user_id`，使用参数化 UPDATE 回填，再通过 batch rebuild 建立 NOT NULL 和约束。downgrade、三个 P4 revision 和唯一 `p4_host_state` head 均未改变。

修复没有手动 COMMIT，没有设置 `session_replication_role`，没有禁用 trigger/FK/NOT NULL/check，没有删除或截断历史表，没有更改超时，也没有使用 `Base.metadata.create_all()`。Alembic 的 PostgreSQL transactional DDL 保证整个 revision 成功提交或完整回滚。

## 历史、约束与回滚证据

修复后的精确历史节点证明：

- 到达唯一 `p4_host_state` head，`alembic_version` 只有一行；
- P1 account/category/receipt/posted expense 保留；两条分录金额分别为 `-4321` 和 `+4321`；
- P2 paused run、`needs_confirmation` pending、双向 ID、module/profile/version/attempt 回填保持；
- P3 preview receipt、`previewed` batch、`create` candidate 和金额 `2500` 保持；
- 代表 scoped 表无 NULL user，事实统一归属唯一 bootstrap owner；
- transaction、pending、import 三类复合 user FK 无孤儿，真实 catalog 中存在对应 FK、unique 和 check；
- 被检查的每张 `user_id` 列 `default is None`；
- 重复 upgrade 幂等；head→P3→head 保持历史事实和 P4 字段回填。

新增执行方参数化 PostgreSQL 测试覆盖两类非法 P3 历史：

- 孤儿 `pending_action.run_id`；
- 矛盾 `pending_action.actor_id` owner。

孤儿场景只在隔离随机 schema 的测试准备阶段删除遗留单 ID FK，以构造数据库损坏输入；产品 migration 不禁用任何约束。两种升级均按预期抛出 migration 的 `RuntimeError`，并证明仍为 P3 head、双分录和非法输入原值保留、无 `app_user`、六张代表表无部分 `user_id` 列。

## 执行方测试结果

### 修改前基线

| 组 | 结果 | warning |
| --- | --- | --- |
| 原 migration 精确 PG 历史节点，唯一一次 | 1 failed（预期 ObjectInUse） | 3 |

三条 warning 为既有 Starlette/AnyIO alias 弃用提示和两条 pytest cache 写入提示。

### 修复后必需门禁

| 组 | 结果 | failed | skipped | warning |
| --- | ---: | ---: | ---: | ---: |
| 修复后精确 PG 历史节点 | 1 passed | 0 | 0 | 2 |
| 完整 `tests/host/test_postgresql_r2.py` | 11 passed | 0 | 0 | 1 |
| 完整 `tests/host/test_migrations.py`，项目临时目录最终运行 | 8 passed | 0 | 0 | 0 |
| Host R1 migration/catalog 与 cancelled downgrade→upgrade 两节点 | 2 passed | 0 | 0 | 1 |
| `tests/finance/test_migrations.py` | 3 passed | 0 | 0 | 0 |
| `tests/activity_import/test_migration.py` | 5 passed | 0 | 0 | 0 |

任务卡六组修复后命令合计 `30 passed, 0 failed, 0 skipped`。warning 是同一条既有 Starlette/AnyIO alias 弃用提示，以及两次精确运行期间的 pytest cache 提示；没有产品 warning。

在完整 R2 前，新增非法图节点还单独运行一次：`2 passed, 2 warnings`；这两项随后也包含在完整 R2 的 11 项中，不重复计入上述 30 项。

完整 Host SQLite migration 首次运行受本机系统 Temp 权限影响，得到 `1 passed, 7 setup errors`；七项错误均为 pytest 在 `C:\Users\xuhaolin\AppData\Local\Temp\pytest-of-xuhaolin` 执行 `os.scandir` 时的 `PermissionError [WinError 5]`，没有产品断言失败。改用仓库内专用 basetemp 后原文件 `8 passed`；测试结束后该临时目录已删除。

静态门禁：

- migration 与变更测试 `compileall`：退出 0；
- `pip check`：退出 0，`No broken requirements found.`；
- `git diff --check`：退出 0，只有工作区既有 LF→CRLF 提示，没有 whitespace error。

没有运行或修改 `tests/independent/**`，没有运行 C11-R2。

## 文件边界、SHA-256 与终点摘要

相对固定 131 文件起点：

- unchanged：129；
- changed：2；
- missing/deleted：0；
- added product/executor-test files：0。

两项 changed：

| 文件 | 起点 SHA-256 | 终点 SHA-256 |
| --- | --- | --- |
| `migrations/versions/p4_host_user_scope.py` | `649cf372e9bbadc6aaecf6bad4f7daac9b1be68fb663c4dc36b8376df9817e8c` | `82bc31919bd5483650f40c0281c42764813f6f5bc0db8d1898b7ad71a3d5a800` |
| `tests/host/test_postgresql_r2.py` | `671269d182fa37d7c66b3fe056d1bf4dc6d8091bd14d6eb9668d20f0cdf87e43` | `0da6346142304f36964370b8f48344c6ab16309058413ffa6bb45d24ae922d6f` |

授权但未修改：

- `tests/host/test_migrations.py`：`9e6d77a83887d8c80a7cdd27210d04500d1bd35ae6d8662d9bfbce9ecdaf62d5`；
- 未新增 `tests/host/test_postgresql_r3.py`。

旧报告只读保持：

- `docs/b6-r3-postgresql-history-migration-running.md`：`e6ab61d865dea61b3b64efc2aa58d533c7e6d0291ab51bac09f1d2e79cfb463f`；
- `docs/b6-r3-r1-postgresql-history-migration-running.md`：`221acc51de0105854b65ff43bb144d8047f3903ad41d5a0a6ca93443d1e07dd1`。

终点有序摘要算法：读取起点清单原始 UTF-8 内容，保持路径顺序、制表符、换行和末尾换行不变，只把每行摘要替换为当前文件 SHA-256，再对 UTF-8 无 BOM 字节计算 SHA-256。结果：

```text
P4-B6-R3-R1-E1-END-SHA256:a89874cfb48b5c8edc8f4260d2f6ce1f206ac02f61e31bb56f4b33ea1282eee9
```

本报告和执行智能体角色日志位于 131 文件产品/执行测试输入之外；它们停止修改后的普通 SHA-256 记录在角色日志之外的最终交付消息中，避免自引用改变摘要。

## 边界与交接

- 未修改 `src/**`、其他 migration、Compose、配置、依赖、冻结合同、control、overview、snapshot、其他角色文件、独立测试、独立报告或矩阵。
- 未读取真实密钥、真实账户或个人数据；数据库内容均为虚拟测试数据。
- 未执行任何 Git 写操作。
- 未启动测试智能体、技术顾问、C11-R2、Electron、OpenClaw、微信或 DeepSeek。
- 执行智能体提交 `review / finished` 并停止；最终独立验收和 P4-A 状态由测试智能体与头脑风暴总控决定。
