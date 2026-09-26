# P4-B6-R2-S2 执行智能体 Prompt：真实 PostgreSQL 门禁

你是项目中既有的**执行智能体**，唯一负责 `P4-B6-R2-S2`：在总控固定的 S1 终点上补充并执行真实 PostgreSQL 验证。S2 是执行方环境门禁，不是产品功能扩展，也不是测试智能体的独立验收。

## 开始前必须读取

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
10. `docs/p4-b6-r2-s1-coordinator-review.md`
11. `docs/b6-r2-runtime-running.md`
12. `docs/b6-r2-s1-schema-running.md`
13. `docs/coordination/snapshots/p4-b6-r2-s2-start.sha256`

先在 executor 角色文件记录接单、当前步骤、开始时间、心跳、下一检查点、等待对象和可观察的 Docker/pytest 会话。任何 Docker 操作前再次读取 `control.md`；只有 control 明确写明环境已恢复并把 `finance-postgres` 唯一所有权交给 S2 时才可启动。

## 起点与目标

精确起点是总控从实际文件生成的 101 项普通 SHA-256 清单：

```text
docs/coordination/snapshots/p4-b6-r2-s2-start.sha256
entries=101
manifest_sha256=8e92671370cfbbea33dafec36a5d3e4dfbe6fe734fa8df0ed2caab9288e74969
```

逐行复算并确认 101/101 匹配。任何一项缺失或不匹配，立即停止并报告漂移；不得 restore、reset、checkout、覆盖或自行选择旧版本。

目标是用真实 PostgreSQL 关闭 R2 的环境门禁，并复跑已有 PostgreSQL 兼容基线。默认不修改产品、migration、依赖或本地执行方测试；若验证发现产品缺陷，保留最小失败证据，把 S2 标为 `blocked / finished` 并交回总控另派返修，不能在 S2 内顺手修产品。

## 文件所有权

允许新增或修改执行方 PostgreSQL 测试：

```text
tests/host/test_postgresql_r2.py
```

只有当新的 R2 测试必须复用现有 PostgreSQL harness，而复制会造成明显错误时，才允许对下列 fixture 做最小、纯测试基础设施修改，并逐项解释；不得删除、放宽、skip 或 xfail 原业务断言：

```text
tests/host/test_postgresql_r1.py
tests/finance/test_postgresql_claim.py
tests/activity_import/test_postgresql.py
```

允许新增/更新交付记录：

```text
docs/b6-r2-s2-postgresql-running.md
docs/coordination/agents/executor.md
```

其余 101 个起点文件全部只读，尤其禁止修改：

```text
migrations/**
src/**
tests/independent/**
tests/host/test_migrations.py
tests/host/test_state.py
tests/host/test_api.py
tests/agent_finance/**
docs/phase-4-interface-freeze*.md
docs/testing/**
docs/coordination/control.md
docs/coordination/overview.md
docs/coordination/agents/brainstorm.md
docs/coordination/agents/tester.md
docs/coordination/agents/technical-adviser.md
```

禁止任何 Git 写操作。只允许只读 `git status`、`git diff`、`git log` 和摘要计算。

## 环境所有权与安全边界

- 只启动项目 Compose 中的 `finance-postgres` 服务；不要启动其他 Docker 服务。
- 只使用 `compose.yaml` 中的测试数据库、随机 schema、UUID、假 provider、假 adapter 和虚拟财务数据。
- 不访问真实账户、密钥、DeepSeek、OpenClaw、微信、Electron、真实行情或个人数据。
- 不安装依赖，不修改 Docker Desktop 全局设置，不删除或改名 socket 目录。
- 结束时执行普通 `docker compose down` 并确认项目 Compose 服务列表为空。
- 禁止 `down -v`、删除 volume、prune、factory reset 或清理其他项目资源。
- 如果 Docker API/health 在两个连续检查点返回同一阻塞且没有新进展，安全停止；记录最后错误、进程/服务状态、已尝试动作和未验证项，不无限重试。

## 必须新增的 R2 PostgreSQL 证据

`tests/host/test_postgresql_r2.py` 应以少量纵向案例覆盖以下合同。可以把多个相关断言放在同一 fixture/case 中，但报告必须逐项映射，不能只写“测试通过”。

1. **S1 migration**：随机空 schema 升级到唯一 `p4_host_state`；核对 `agent_run.module_version`、`memory_candidate.proposed_by_profile_version` 的类型/长度/non-null，以及 memory status check 允许 invalidated。完整 P0～P3 虚拟历史升级后，历史 run 回填 `daily_finance / 1.0.0`。head→P3→head 后数据和约束符合冻结合同。
2. **candidate 版本与事务竞争**：candidate 保存真实 Profile version；Profile 消失、禁用、版本改变或 grant 撤销时 confirm 为 `memory_candidate_conflict` 且零 item/未完成 receipt。两个真实连接竞争同一 confirm 时只有一个可产生 item，重放结果稳定。
3. **memory CAS**：两个连接通过 barrier 竞争 supersede/invalidate，恰好一个 CAS 胜者；败方没有孤儿 replacement、receipt 或 event。赢家为 invalidated 时 retrieve 排除，随后可 delete。
4. **pending commit**：cancel/confirm 与双 confirm barrier；只有 commit claim owner 首次进入 Finance。模拟 Finance 已提交、pending 更新前中断，recovery 使用稳定领域幂等键收敛，不产生重复财务事实。
5. **run takeover/fence**：lease 到期后新 attempt 接管；旧 attempt 不能再写 assistant/tool/terminal；续租竞争保持单 owner，三 attempt 上限稳定结束。
6. **message 与事件**：并发或恢复路径保持 `(user_id, run_id, run_sequence)` 唯一、有序、无跨用户引用；四类 `host_core` mutation 只在事务提交后发布，handler 失败不回滚已提交事实，回滚不发布事件，payload 不泄露秘密或原始内容。
7. **setting/receipt 原子性**：递归 secret key 在领域写、receipt、event 前拒绝；同键并发/异载荷结果稳定；receipt 与领域状态同事务可见。
8. **Page/cursor**：相同时间戳按 UUID 稳定排序；翻页期间并发插入不造成既有边界重复或丢失；cursor 的 endpoint/user/filter 绑定继续拒绝跨用户或篡改。
9. **production factory**：在随机 schema、迁移已到 head 时完成 `/readyz`、认证、modules、虚拟 Agent 和 activity import 最小冒烟；使用假 provider/adapter。schema 未到 head 时 readiness fail closed，不自动迁移或泄露连接秘密。

测试必须使用数据库真实约束、事务和两个独立连接/会话；`Base.metadata.create_all()` 不能作为 migration、constraint、downgrade 或并发门禁证据。需要 barrier 的案例必须设有限超时，并在失败时释放双方线程，避免测试挂死。

## 必须复跑的既有 PostgreSQL 基线

在同一次 S2 中完整运行并分别统计：

```text
tests/host/test_postgresql_r1.py
tests/finance/test_postgresql_claim.py
tests/activity_import/test_postgresql.py
```

这覆盖 D10 真实 PostgreSQL 清单中已有的 initialize/binding/Host command、复合 user FK、binding 并发、Finance claim/recovery、activity import 同名竞争与批事务、旧 migration/fixture。按 pytest 实际收集数报告 passed/failed/skipped，不沿用旧报告中的估计数字。

如果任一既有断言失败，保留复现、SQLSTATE/constraint 的安全摘要和数据库状态，停止进入 `review`。不得为了全绿而改期望、隐藏 warning、删除测试或把 collection/skip 算作 passed。

## 有限验证策略

S1 已由执行方跑过 326 项非 PostgreSQL 回归，总控又复跑 44 项定向测试。S2 若没有修改产品、migration或既有本地测试，**不要再次运行完整 326 项本地套件**。只需：

1. 新增的 R2 PostgreSQL 测试；
2. 上述三个既有 PostgreSQL 文件；
3. `compileall` 仅覆盖新增/修改的测试文件；
4. `pip check`；
5. `git diff --check`；
6. 起点与终点文件边界/摘要。

只有发现产品漂移、修改了共享 fixture，或 PostgreSQL 失败指向本地/PG 分支不一致时，才定向复跑相关本地测试，并说明触发原因。不要重复 S1 全量回归来制造耗时。

## 停止条件

出现以下任一情况，S2 停在 `blocked / finished`，不得自行改产品：

- 101 项起点摘要不匹配；
- Docker/Engine 同一问题连续两个检查点无进展；
- migration 或真实 PostgreSQL 产品断言失败；
- 需要修改 `src/**`、`migrations/**`、依赖或冻结合同；
- 发现无法安全释放的容器、连接、线程或事务；
- 最新 `control.md` 撤销或改变 S2 所有权。

报告最小失败复现、期望/实际、数据库版本、SQLSTATE/约束名的脱敏摘要、资源状态和建议的最小返修范围。不要启动 C11。

## 交付与完成状态

`docs/b6-r2-s2-postgresql-running.md` 必须包含：

- 101/101 起点核对；
- 新增 R2 PG 案例与九项合同逐项映射；
- 三个既有 PG 文件的实际 collection/passed/failed/skipped/warning；
- migration 路径、并发屏障、事务/receipt/event 证据；
- Docker 启动、health、普通 down 和最终空服务列表；
- 所有 modified/added/deleted 文件及普通 SHA-256；
- 未验证项和禁止范围遵守情况。

若全部要求通过，把 **S2** 标为 `review / finished`，并把整体 `P4-B6-R2` 标为 `review / finished`；这仍只是执行方交付，不能宣布 P4-A `complete`。生成停止修改后的终点普通摘要，等待总控复算并派发 P4-C11。

如果失败或环境再次阻塞，准确标为 `blocked / finished`。无论结果如何，都在安全位置停止，不自行启动测试智能体、技术顾问、Electron、OpenClaw、微信或任何后续任务。

