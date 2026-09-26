# P4-B6-R2-S2-T2 执行智能体 Prompt：Docker 恢复后的有限 PostgreSQL 复验

你是项目中既有的**执行智能体**，唯一负责 `P4-B6-R2-S2-T2`。本任务只验证 T1 已完成的测试时钟修复以及现有 R1/R2 PostgreSQL 测试；不得修改产品、migration、测试代码或依赖。

这是执行方环境门禁，不是 P4-C11 独立验收。全部通过最多把 T1、S2 和整体 `P4-B6-R2` 交付为 `review / finished`，不能宣布 P4-A `complete`。

## 开始前必须读取

按顺序读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. `docs/coordination/control.md`
6. `docs/coordination/agents/executor.md`
7. `docs/phase-4-interface-freeze-002.md`
8. `docs/docker-desktop-incident-2026-09-26.md`
9. `docs/b6-r2-s2-postgresql-running.md`
10. `docs/b6-r2-s2-t1-clock-running.md`
11. `docs/coordination/snapshots/p4-b6-r2-s2-t2-start.sha256`

先在 `docs/coordination/agents/executor.md` 记录接单、当前步骤、开始时间、最近心跳、下一检查点、等待对象和可观察的 Docker/pytest 会话。任何 Docker 操作前再次读取最新 `control.md`。

## 起点门禁

```text
docs/coordination/snapshots/p4-b6-r2-s2-t2-start.sha256
entries=104
manifest_sha256=c7deef5af25f2ba6215bdd587fe13d46d027ecb37294bc9373a6aadf4c03529d
```

逐行复算并确认 `104/104 matched`、`0 missing`、`0 mismatch`。任何不匹配立即停止并报告；不得执行 restore、reset、checkout、switch 或覆盖文件。

该清单已经包含：

- T1 修复后的 `tests/host/test_postgresql_r1.py`：`f0c3144d2aeae4ceee0ac724bbcb6bb1f43607779552c34312bcbcea8a5c8bcb`；
- T1 运行说明：`426e8a92b8660f941203bed464cb24c9c8bf88b9ab552d619529ead58bc55c1f`。

## 已由总控完成的 Docker 稳定性门禁

总控在用户升级后完成了两次检查，中间通过 Docker Desktop 自身 CLI 正常停止并重新启动一次：

- Docker Desktop：`4.92.0.240144`；
- Desktop 状态：`running`；
- context：`desktop-linux`；
- `dockerDesktopLinuxEngine` 管道存在；
- client/server：`29.8.0 / 29.8.0`；
- server OS/type：`Docker Desktop / linux`；
- 项目 Compose 服务列表为空；
- 第二次启动的最近 backend 日志没有再次出现 `sailor-ingest.sock`、`docker-secrets-engine` 或 `file cannot be accessed`。

本任务不得再次停止或重启 Docker Desktop，不得处理 socket 目录。如果 Engine 在接单时不可达，只检查一次并停止为 `blocked / finished`，交回总控，不进行第二轮环境修复。

## 唯一目标

取得 17 个**唯一**真实 PostgreSQL 用例的执行证据：

1. T1 修复的精确 Host R1 用例 1 项；
2. Host R1 其余 7 项；
3. Host R2 9 项。

不要把精确节点再包含在第二组中重复执行。三组相加必须是 17 个唯一用例。

## 禁止修改范围

禁止修改：

```text
src/**
migrations/**
tests/**
alembic.ini
compose.yaml
pyproject.toml
requirements*.txt
docs/b6-r2-s2-postgresql-running.md
docs/b6-r2-s2-t1-clock-running.md
docs/testing/**
docs/phase-4-*.md
docs/coordination/control.md
docs/coordination/overview.md
docs/coordination/snapshots/**
```

也不得执行任何 Git 写操作，不得启动测试智能体、技术顾问或 P4-C11。

唯一允许新增的任务交付：

```text
docs/b6-r2-s2-t2-postgresql-running.md
```

并按协作规则只更新自己的角色文件：

```text
docs/coordination/agents/executor.md
```

## Docker 与数据边界

1. 外部操作前重新读取最新 control，确认 T2 是唯一项目环境负责人。
2. 起点先确认 `docker compose ps --format json` 为空。
3. 只执行 `docker compose up -d finance-postgres`。
4. 等待 `wife-system-finance-postgres-1` 达到 `running / healthy`。
5. 连接只使用：

   ```text
   postgresql+psycopg://wife_test:wife_test_only@127.0.0.1:55432/wife_finance_test
   ```

6. 测试通过随机 schema 和虚拟身份数据隔离；不得读取真实账户、密钥或个人数据。
7. 成功或失败后都执行普通 `docker compose down`。
8. 最终 `docker compose ps --format json` 必须退出 0 且无输出，记录为 `COMPOSE_SERVICES_EMPTY`。
9. 禁止 `down -v`、删除 volume、prune、Factory reset、修改 Docker context/全局设置、触碰 socket 或备份目录、启动其他 Docker 服务。

## 必须按顺序执行的有限测试

在当前 PowerShell 会话中设置：

```powershell
$env:FINANCE_TEST_POSTGRES_URL = 'postgresql+psycopg://wife_test:wife_test_only@127.0.0.1:55432/wife_finance_test'
```

然后顺序执行并分别保存原始统计：

### 1. 精确修复节点：1 项

```powershell
.venv\Scripts\python.exe -m pytest -q "tests/host/test_postgresql_r1.py::test_postgresql_competing_binding_codes_return_safe_replayable_conflict"
```

要求：`1 passed`、`0 failed`、`0 skipped`。必须确认实际 HTTP 状态为 `[200, 409]`，败方 code、receipt、重放、撤销后重试和隐私原断言全部没有被修改。

如果该节点失败，保留第一次失败证据，立即停止后续测试并进入资源收口。不得重复运行覆盖首次失败，不得修改代码。

### 2. Host R1 其余节点：7 项

```powershell
.venv\Scripts\python.exe -m pytest -q tests/host/test_postgresql_r1.py -k "not competing_binding_codes_return_safe_replayable_conflict"
```

要求：实际收集并运行其余 `7` 项，`7 passed`、`0 failed`、`0 skipped`。与第一组合并后形成 Host R1 `8/8` 的唯一执行证据。

### 3. Host R2：9 项

```powershell
.venv\Scripts\python.exe -m pytest -q tests/host/test_postgresql_r2.py
```

要求：`9 passed`、`0 failed`、`0 skipped`。它在 R1 后运行，也验证 T1 的 monkeypatch 已恢复，没有跨文件时钟污染。

## 不得重复的测试

不要再运行：

- Finance PostgreSQL 4 项；
- activity import PostgreSQL 10 项；
- S1 定向 44 项；
- 326 项非 PostgreSQL 回归；
- `tests/independent/**`；
- P4-C11 矩阵。

这些范围在相同产品快照上已有证据，T2 没有修改相关实现。

## 其他有限检查

测试结束后只做：

1. `python -m pip check`；
2. `git diff --check`；
3. 重新复算 104 文件起点，要求仍为 `104/104 matched`、`0 changed`、`0 missing`；
4. 记录 T2 报告与 executor 日志的普通 SHA-256；
5. 普通关闭 Compose 并确认服务列表为空。

T2 是零代码改动任务；如果 104 文件中任何文件发生变化，任务不得进入 `review`。

## 停止条件

遇到以下任一情况立即停止修改和继续测试：

- 起点 manifest 不匹配；
- Docker Engine 不可达或容器无法达到 healthy；
- 精确节点失败；
- R1/R2 出现 failed、skipped、setup error 或线程卡死；
- 发现必须修改产品、migration 或测试才能继续；
- 104 文件快照发生漂移；
- 同一阻塞连续两个检查点没有进展。

停止时保留第一次失败证据、执行资源收口，把 T2、S2 和整体 R2 标为 `blocked / finished`，不得自行派发其他角色。

## 交付说明必须包含

`docs/b6-r2-s2-t2-postgresql-running.md` 必须记录：

- 104/104 起点与终点复算；
- Docker Desktop/Engine 版本、容器 health、回环端口和随机 schema；
- 精确节点 1 项、R1 其余 7 项、R2 9 项的 passed/failed/skipped/warning；
- 17 个唯一用例如何组成 R1 8/8 与 R2 9/9；
- monkeypatch 跨文件恢复证据；
- `pip check` 和 `git diff --check`；
- 普通 `compose down` 和最终 `COMPOSE_SERVICES_EMPTY`；
- 没有修改 104 文件、产品、migration、测试或独立验收范围；
- 报告与 executor 日志的普通 SHA-256；
- 剩余未验证项和 P4-C11 尚未启动。

全部通过时，把 `P4-B6-R2-S2-T2`、T1、S2 和整体 `P4-B6-R2` 标为 `review / finished` 并停止。最终项目接受仍由总控在 P4-C11 独立验收后决定。
