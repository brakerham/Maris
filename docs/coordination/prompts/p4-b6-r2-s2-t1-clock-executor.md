# P4-B6-R2-S2-T1 执行智能体 Prompt：R1 PostgreSQL 测试时钟返修

你是项目中既有的**执行智能体**，唯一负责 `P4-B6-R2-S2-T1`：修复一个既有 R1 PostgreSQL 测试的固定时钟过期问题，并重新关闭 S2 执行方门禁。它是单文件测试基础设施返修，不是产品修复。

## 开始前必须读取

按顺序读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. `docs/coordination/control.md`
6. `docs/coordination/agents/executor.md`
7. `docs/phase-4-interface-freeze-002.md`
8. `docs/p4-b6-r2-s2-blocked-coordinator-review.md`
9. `docs/b6-r2-s2-postgresql-running.md`
10. `docs/coordination/snapshots/p4-b6-r2-s2-t1-start.sha256`

先在 executor 角色文件记录接单、当前步骤、开始时间、心跳、下一检查点、等待对象和可观察 Docker/pytest 会话。任何 Docker 操作前再次读取最新 `control.md`；只在 control 明确把 `finance-postgres` 唯一所有权交给 T1 时启动。

## 起点

```text
docs/coordination/snapshots/p4-b6-r2-s2-t1-start.sha256
entries=103
manifest_sha256=b1c4c80d8d5a04e2571b9028e38abc7fb99f912c6b2ffba84d799f466e4d5b18
```

逐行复算并确认 103/103 匹配。任何缺失或不匹配立即停止并报告；不得 restore、reset、checkout 或覆盖文件。

## 唯一问题

失败用例：

```text
tests/host/test_postgresql_r1.py::test_postgresql_competing_binding_codes_return_safe_replayable_conflict
```

当前用例固定用 `2026-09-26T02:00:00Z` 创建十分钟有效 code，但 HTTP consume 路由读取真实 `datetime.now(UTC)`。真实时间推进后，两枚 code 在竞争 INSERT 前都过期，导致预期 `[200,409]`、实际 `[409,409]`。

## 冻结修复方式

只修改：

```text
tests/host/test_postgresql_r1.py
```

要求：

1. 给该用例增加 pytest `monkeypatch` fixture。
2. 导入 `wife_system.api.host_routes` 模块，并仅在该用例期间替换它的模块级 `datetime`。
3. 使用继承标准 `datetime` 的测试子类或等价可控对象，使 `datetime.now(UTC)` 在 TestClient 工作线程中返回用例已有的固定 `now`；naive 调用也必须返回语义正确的 naive 值，虽然本用例不依赖它。
4. pytest fixture 结束时必须自动恢复原对象，不留下全局时钟污染。
5. 保留固定时间、原十分钟 TTL、并发 INSERT barrier、`[200,409]`、败方 active/attempts=0、同键 409 replay、撤销赢家后败方新键成功和全部隐私断言。

禁止：

- 把固定时间直接改成真实 `datetime.now(UTC)`；
- 修改 `src/**`、migration、依赖、生产 TTL、路由、AuthService 或错误合同；
- 删除、放宽、skip、xfail 或重写原业务断言；
- 修改 `tests/host/test_postgresql_r2.py`、Finance/P3 PostgreSQL 测试或 `tests/independent/**`；
- 修改 S2 原始失败报告、冻结文档、矩阵、control、overview 或其他角色状态；
- 任何 Git 写操作。

允许新增交付说明：

```text
docs/b6-r2-s2-t1-clock-running.md
```

并按协作规则更新：

```text
docs/coordination/agents/executor.md
```

## 有限验证

外部操作前重读 control，只启动 Compose 服务 `finance-postgres`。至少顺序执行并分别报告：

1. 精确失败节点一次；
2. 完整 `tests/host/test_postgresql_r1.py`，要求原 8 个实际 collection 全部通过、0 skip；
3. 完整 `tests/host/test_postgresql_r2.py`，要求原 9 项全部通过、0 skip；它在 R1 后运行，也作为 monkeypatch 已恢复、无跨用例污染的执行证据；
4. `compileall` 仅覆盖修改的 R1 测试；
5. `pip check`；
6. `git diff --check`；
7. 终点文件边界和普通 SHA-256。

不要重复 Finance 4 项、activity import 10 项、S1 44 项或 326 项非 PostgreSQL 回归。它们在相同产品快照上已经通过，T1 不修改相关文件。

如果精确节点仍失败，或者必须修改产品才能通过，保留一次失败证据并停在 `blocked / finished`，不得反复运行覆盖首次结果。相同环境问题连续两个检查点无进展时停止并报告。

## Docker 边界

- 只使用 `finance-postgres`、随机 schema 和虚拟数据；
- 完成或失败后执行普通 `docker compose down` 并确认服务列表为空；
- 禁止 `down -v`、volume 删除、prune、factory reset、全局 Docker 配置或 socket 目录操作；
- 不访问 Electron、OpenClaw、微信、DeepSeek、真实 provider、账户、密钥、行情或个人数据。

## 交付与状态

`docs/b6-r2-s2-t1-clock-running.md` 必须包含：

- 103/103 起点核对；
- 根因、精确修改位置和可控时钟如何覆盖 TestClient 线程；
- monkeypatch 自动恢复证据；
- 精确节点、R1 8 项、R2 9 项的 passed/failed/skipped/warning；
- Docker 启动、health、普通 down 和最终空服务列表；
- 修改/新增/删除文件与普通 SHA-256；
- 未验证项和禁止范围遵守情况。

若全部通过，把 T1、S2 和整体 `P4-B6-R2` 标为 `review / finished`，然后停止。该状态仍只是执行方交付，不表示 P4-A `complete`，不得自行启动 P4-C11 或测试智能体。

若失败，把 T1、S2 和整体 R2 保持 `blocked / finished`，准确交回总控。无论结果如何，不继续扩展任务。

