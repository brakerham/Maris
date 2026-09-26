# P4-B6-R1-F1 总控审查记录

- 审查时间：2026-09-26 10:41 Asia/Shanghai
- 审查对象：`P4-B6-R1-F1`
- 结论：接受为 `P4-B6-R2` 的精确开发基线；不据此宣布 P4-A `complete`
- 原缺陷：`P4-B6-R1-REV-001`

## 1. 范围与快照

总控把执行方交付与 23 文件 F1 起点清单逐项比较，结果为：

- 4 个起点文件发生变化；
- 19 个起点文件保持不变；
- 0 个起点文件缺失；
- 另有执行智能体自己的协调日志按授权更新。

发生变化的四个起点文件是：

```text
docs/b6-r1-security-data-running.md
src/wife_system/host/auth/service.py
tests/host/test_api.py
tests/host/test_postgresql_r1.py
```

执行方报告的五个最终文件摘要均可由当前工作区复算。22 个 R1 产品、migration 与执行方测试文件的有序总摘要也可复算为：

```text
P4-B6-R1-F1-SHA256:e690882a291b8ec0210971d3bbed1f6da2252368cd9afff5213ff33798b87976
```

供 R2 使用的完整 96 文件起点清单见 [P4-B6-R2 起点快照](coordination/snapshots/p4-b6-r2-start.sha256)，其有序总摘要为：

```text
7a80e083b0534c0f2547d859276f9c910b94a912b9b057ef95f8dbc9a74f3632
```

## 2. 代码审查结论

修复把唯一索引竞争限制在 binding INSERT 的局部 savepoint 中。只有 PostgreSQL SQLSTATE `23505` 且目标为冻结的 active identity 唯一索引，或 SQLite 精确命中对应两列唯一约束时，才继续按业务冲突处理；其他 `IntegrityError` 保持原样抛出。

savepoint 回滚后，服务重新查询同一 active binding 来确认竞争事实。确认后，败方绑定码恢复为 active，`attempts` 不增加，`consumed_at` 保持空；外层 Host command 事务仍能保存安全 409 receipt。相同 Idempotency-Key 重放同一 409，不再次执行 mutation；赢家撤销后，败方可用新键消费原码。

这关闭了“两个有效 code 同时绑定同一外部身份时，败方异常穿透为 HTTP 500”的窗口，同时没有恢复 R1 已删除的宽泛异常映射。

## 3. 总控验证

- 总控独立复跑 `test_auth.py`、`test_api.py`、`test_state.py`、`test_migrations.py`：`41 passed`。
- 唯一 warning 是既有 Starlette/AnyIO `BlockingPortal` 弃用提醒。
- `git diff --check` 没有格式错误；仅显示现有 Windows 行尾提示。
- 执行方提供的真实 PostgreSQL 证据为：原 R1 21 项通过，新增同步竞争案例 1 项通过，0 skip；测试后项目 Compose 服务列表为空。

总控尝试再次运行新增 PostgreSQL 案例时，测试还没有启动，Docker Desktop 已在初始化阶段失败。错误来自本机失效 socket，先后涉及 `Docker/run/sailor-ingest.sock` 和 `docker-secrets-engine/engine.sock`，不来自项目容器、migration 或测试断言。

总控已停止重复重启，没有改 ACL、没有恢复出厂设置、没有删除 volume、没有 prune。两个 `Docker/run` 现场目录保留为：

```text
%LOCALAPPDATA%\Docker\run.codex-backup-20260926-103505
%LOCALAPPDATA%\Docker\run.codex-backup-20260926-103655
```

`docker-secrets-engine` 原目录没有被改名或删除。需要在 Windows 重启释放句柄后再确认 Docker Desktop 可正常启动。

## 4. 验收边界与下一步

`P4-B6-R1-REV-001` 在开发返修层面关闭，F1 可以作为 R2 起点。这个决定依据代码审查、可复算快照、本地独立复跑以及执行方真实 PostgreSQL 证据；它不替代最终 P4-C11 独立验收。

R2 必须从 96 文件快照精确开始，保持 F1 与全部 R1 安全回归。Windows 重启并确认 Docker Desktop 正常后，才把 [P4-B6-R2 执行任务](coordination/prompts/p4-b6-r2-runtime-executor.md)发送给既有执行智能体。R2 完成并形成终点快照后，再由测试智能体执行 C11，包括真实 PostgreSQL 的 F1 竞争反例和全部 R1/R2 门禁。
