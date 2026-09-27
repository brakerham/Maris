# P4-B6-R2-S2-T2 有限 PostgreSQL 复验运行说明

## 交付状态

- 任务：`P4-B6-R2-S2-T2`
- T2：`review / finished`
- T1：`review / finished`
- P4-B6-R2-S2：`review / finished`
- P4-B6-R2：`review / finished`
- 本轮是执行方环境门禁和自测证据，不是 P4-C11 独立验收，不表示 P4-A `complete`。
- 本轮零代码、零 migration、零测试修改，只新增本运行说明并更新执行智能体自己的角色日志。

## 104 文件起点与终点门禁

起点清单：`docs/coordination/snapshots/p4-b6-r2-s2-t2-start.sha256`

```text
entries=104
manifest_sha256=c7deef5af25f2ba6215bdd587fe13d46d027ecb37294bc9373a6aadf4c03529d
start_matched=104
start_changed=0
start_missing=0
```

三组 PostgreSQL 测试和静态检查完成后逐项重新复算：

```text
end_matched=104
end_changed=0
end_missing=0
```

因此 T2 没有修改清单内的产品、migration、测试、依赖、冻结文档、既有运行说明或快照。清单内容及其普通 SHA-256 在起点和终点保持不变。

## Docker 与 PostgreSQL 环境

外部操作前重新读取 `docs/coordination/control.md`，版本为 `2026-09-26T22:10:00+08:00`，确认 T2 是 `finance-postgres` 的唯一环境负责人；技术顾问、测试智能体和 P4-C11 均保持停止。

- Docker Desktop CLI plugin：0.4.4
- Docker Desktop：4.92.0 (240144)，状态 `running`
- context：`desktop-linux`
- Docker client/server：29.8.0 / 29.8.0
- server：Docker Desktop / linux
- Compose 起点：`docker compose ps --format json` 退出 0 且无输出，`COMPOSE_SERVICES_EMPTY`
- 唯一启动服务：`finance-postgres`
- 容器：`wife-system-finance-postgres-1`
- 镜像：`postgres:17.6-alpine`
- health：`running/healthy`
- 端口：只绑定 `127.0.0.1:55432->5432`
- 测试连接：`postgresql+psycopg://wife_test:wife_test_only@127.0.0.1:55432/wife_finance_test`

首次只读版本格式化命令引用了当前 Docker CLI 模板不支持的 `Server.OperatingSystem` 字段并退出 1；随后用标准 `docker version` 和 `docker info` 成功取得上述版本与 server 信息。Engine 全程可达，Compose 起点为空，因此该命令格式问题不属于环境或测试失败。

测试只使用虚拟身份数据和随机 schema：

- R1 fixture 每个 pytest 进程创建 `p4_b6_r1_schema_<uuid4 hex>`，结束时执行 `DROP SCHEMA IF EXISTS ... CASCADE`；round-trip 用例另创建并清理 `p4_b6_r1_roundtrip_<uuid4 hex>`。
- R2 fixture 创建 `p4_b6_r2_s2_<uuid4 hex>`，结束时执行 `DROP SCHEMA IF EXISTS ... CASCADE`。
- 三组测试是三个独立 pytest 进程，因此精确节点和 R1 其余节点分别使用独立的随机 R1 schema；没有复用真实业务 schema、账户、密钥或个人数据。

## 17 个唯一 PostgreSQL 用例

设置：

```text
FINANCE_TEST_POSTGRES_URL=postgresql+psycopg://wife_test:wife_test_only@127.0.0.1:55432/wife_finance_test
```

严格按任务卡顺序执行：

| 顺序 | 测试组 | 唯一用例数 | passed | failed | skipped | warning occurrences |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | T1 精确 Host R1 竞争绑定节点 | 1 | 1 | 0 | 0 | 2 |
| 2 | Host R1 其余节点，使用 `-k not competing_binding_codes_return_safe_replayable_conflict` | 7 | 7 | 0 | 0 | 2 |
| 3 | Host R2 完整文件 | 9 | 9 | 0 | 0 | 2 |
| 合计 | R1 8/8 + R2 9/9 | 17 | 17 | 0 | 0 | 6 |

精确节点只运行一次，没有在第二组中重复。第一组和第二组合成 Host R1 的 8 个唯一用例；第三组是 Host R2 的 9 个唯一用例。

### 精确修复节点

```text
tests/host/test_postgresql_r1.py::test_postgresql_competing_binding_codes_return_safe_replayable_conflict
1 passed
0 failed
0 skipped
```

通过未修改的原有断言确认：

- 两个并发 consume 的实际 HTTP 状态排序为 `[200, 409]`；
- 败方 code 保持 `active` 且 `attempts == 0`；
- 胜方和败方 receipt 状态、同键 409 replay 保持一致；
- 撤销赢家后，败方使用新幂等键重试成功；
- 响应、receipt 和日志的隐私断言全部通过。

### Monkeypatch 恢复证据

T1 的精确节点使用 pytest `monkeypatch` 临时替换 `wife_system.api.host_routes.datetime`。该节点完成 teardown 后，继续运行 R1 其余 7 项和 R2 9 项，全部通过；R2 文件没有接收或依赖 T1 的时钟替换。这个执行顺序证明 patch 已在 fixture teardown 后恢复，没有跨测试文件保留全局测试时钟。

### Warning

每个 pytest 进程各报告两条非阻断 warning，共 6 次、2 种唯一类型：

1. Starlette 使用已弃用的 `anyio.abc.BlockingPortal` alias；
2. pytest 无法在既存 `.pytest_cache` 路径创建 `nodeids` 的 `PytestCacheWarning`。

这些 warning 没有造成 failed、skipped、setup error 或用例未收集。没有为消除 warning 修改测试、依赖或缓存目录。

## 其他有限检查

- `.venv\Scripts\python.exe -m pip check`：退出码 0，`No broken requirements found.`
- `git diff --check`：退出码 0；只有当前起点工作树已有文件的 LF→CRLF 提示，没有 whitespace error。
- 终点 104 文件复算：`104/104 matched`、0 changed、0 missing。
- 没有运行 Finance PostgreSQL 4 项、activity import PostgreSQL 10 项、S1 44 项、326 项非 PostgreSQL 回归或 `tests/independent/**`。

## 资源关闭

测试和有限检查完成后重新读取最新 control，版本仍为 `2026-09-26T22:10:00+08:00`，然后执行普通 `docker compose down`：

- 容器正常 stopped/removed；
- 项目网络正常 removed；
- `docker compose down` 退出 0；
- 最终 `docker compose ps --format json` 退出 0 且无输出；
- 最终状态：`COMPOSE_SERVICES_EMPTY`。

没有执行 `down -v`、volume 删除、prune、Factory reset、Docker Desktop 停止/重启、context 或全局设置修改，也没有触碰 socket 或备份目录。

## 文件边界与摘要记录方式

T2 任务新增：

- `docs/b6-r2-s2-t2-postgresql-running.md`

协作规则要求更新但不属于 104 文件产品快照：

- `docs/coordination/agents/executor.md`

本运行说明和 executor 日志在停止修改后计算普通 SHA-256，并在 executor 最终日志和执行方交付消息中记录。本文件不能在自身内容中嵌入其最终普通 SHA-256 而同时保持该摘要不变；executor 文件也有相同的自引用限制。

## 剩余边界

- 本轮 17 个真实 PostgreSQL 用例全部通过，执行方已关闭 T1/S2/R2 的 PostgreSQL 自测门禁。
- P4-C11 尚未启动；P4-A 独立验收、总控接受和项目 `complete` 仍未验证。
- 没有启动测试智能体、技术顾问、Electron、OpenClaw、微信、DeepSeek 或真实 provider；没有读取真实密钥、账户、行情或个人数据。
- 没有执行任何 Git 写操作。
- 执行方在 `review / finished` 停止，等待总控核对 104 文件零漂移、报告摘要和 PostgreSQL 资源关闭证据。
