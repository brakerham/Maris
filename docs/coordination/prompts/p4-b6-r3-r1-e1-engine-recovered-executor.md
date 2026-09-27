# P4-B6-R3-R1-E1 执行智能体 Prompt：Engine 恢复后继续历史迁移返修

你是项目中既有的**执行智能体**，唯一负责 `P4-B6-R3-R1-E1`。这是同一项 PostgreSQL 历史 migration 返修在 Docker Engine 恢复后的执行续段，不是新功能，也不重新设计或重写 R3 已准备的历史 fixture。

头脑风暴总控已于 `2026-09-27 11:49～11:50 Asia/Shanghai` 完成只读环境门禁：

```text
docker desktop status: running, exit 0
Docker Desktop/backend processes: present
docker context: desktop-linux
Docker Client: 29.8.0
Docker Server: 29.8.0
Server OS: linux
Platform: Docker Desktop 4.92.0 (240144)
docker compose ps --format json: exit 0, no services
```

该证据只说明恢复任务可以开始，不替代你接管后的任务内检查、PostgreSQL 测试或资源收口。

## 1. 开始与控制面

按 AGENTS.md 要求读取全部必读文件，特别是：

1. `docs/coordination/control.md`
2. `docs/coordination/agents/executor.md`
3. `docs/coordination/prompts/p4-b6-r3-r1-postgresql-history-migration-resume-executor.md`
4. `docs/b6-r3-postgresql-history-migration-running.md`
5. `docs/b6-r3-r1-postgresql-history-migration-running.md`
6. `docs/coordination/snapshots/p4-b6-r3-r1-start.sha256`

完整 R3-R1 Prompt 的技术合同、允许/禁止文件、测试顺序、原子性、安全边界和 Docker 边界继续全部有效。本文只更新环境状态、任务 ID 和本次交付文件；冲突时以最新 control 和本文为准。

在执行智能体角色文件中记录接单、当前步骤、开始时间、心跳、下一检查点、等待对象和 Docker/pytest 会话。确认最新 control 明确指定本任务后才能操作 Docker。

## 2. 固定输入

继续使用原 131 文件固定输入：

```text
docs/coordination/snapshots/p4-b6-r3-r1-start.sha256
entries=131
manifest_sha256=5aa1db6c395e745ad1bd96a92a40ece9d69bbdcc837e7234d47d12f3badeb9bb
```

开始前必须复算为 `131 matched / 0 mismatch / 0 missing`。两份环境阻塞报告和角色日志不属于这 131 个产品/执行测试输入，不得因此误报漂移。

保留 [tests/host/test_postgresql_r2.py](../../../tests/host/test_postgresql_r2.py) 中已经准备好的 P1 双分录、P2 run/pending、P3 import 历史和回滚审计。不要还原、重写或复制 fixture。

## 3. 本次执行顺序

1. 接管后只检查一次 Engine 可达和项目 Compose 为空。
2. 只启动 `docker compose up -d finance-postgres`，等待 `running / healthy`。
3. 在原 migration 未修改的前提下，只运行精确历史节点一次：

   ```text
   tests/host/test_postgresql_r2.py::test_postgresql_s1_migration_empty_history_and_round_trip
   ```

4. 必须取得真实 `ObjectInUse` 或等价 pending-trigger ALTER 失败，以及完整事务回滚证据；若原 migration 意外通过、错误位置不同或回滚审计失败，立即停止为 `blocked / finished`，不要修改 migration。
5. 失败基线符合预期后，按完整 R3-R1 Prompt 的合同最小修改 `p4_host_user_scope.py`，优先采用 PostgreSQL 临时 constant server default + NOT NULL、随后删除 default 的单事务方案；SQLite 路径保持原语义。
6. 完整执行 R3-R1 Prompt 第 7 节的修复后门禁，证明历史事实、owner、复合 FK、unique/check、无 persistent default、幂等、downgrade 和非法图完整回滚。
7. 无论成功或失败，都普通执行 `docker compose down` 并确认 `COMPOSE_SERVICES_EMPTY`；禁止 `down -v`、删除 volume、prune、Factory reset、Desktop 重启、context/全局设置或 socket 操作。

若接管时 Engine 再次不可达，只检查一次后停止，不自行维修。若需要扩大到其他 migration、`src/**` 或冻结合同，立即停止交回总控。

## 4. 文件边界

允许范围保持为：

```text
migrations/versions/p4_host_user_scope.py
tests/host/test_postgresql_r2.py
tests/host/test_migrations.py
docs/b6-r3-r1-e1-postgresql-history-migration-running.md
docs/coordination/agents/executor.md
```

只有现有 R2 测试文件确实无法保持清晰时，才可新增：

```text
tests/host/test_postgresql_r3.py
```

原 R3 和 R3-R1 环境阻塞报告只读保留。完整 R3-R1 Prompt 中的所有禁止范围继续有效，包括 `src/**`、其他 migration、`tests/independent/**`、独立报告/矩阵、control、overview、snapshot、其他角色文件、Compose、依赖和 Git 状态。

## 5. 交付

新增：

```text
docs/b6-r3-r1-e1-postgresql-history-migration-running.md
```

报告必须覆盖完整 R3-R1 Prompt 要求，并明确区分：

- E1 修改前真实失败基线；
- migration 修复后的执行方测试；
- 未运行的独立验收；
- Docker 起点、health、普通 down 和最终空服务；
- 131 文件起点复算与终点 changed/unchanged/missing；
- 所有授权文件普通 SHA-256 和新的有序终点摘要。

全部执行方门禁通过时停在 `review / finished`；任何环境复发、失败差异、扩大范围需求或测试失败停在 `blocked / finished`。不得自行启动 C11-R2、测试智能体、技术顾问、Electron、OpenClaw、微信或 DeepSeek，不得执行任何 Git 写操作，不得宣布 P4-A `complete`。
