# P4-B6-R2-S2-T1 测试时钟返修运行说明

## 交付状态

- 任务：`P4-B6-R2-S2-T1`
- 执行方状态：`blocked / finished`
- `P4-B6-R2-S2` 状态：保持 `blocked / finished`
- `P4-B6-R2` 状态：保持 `blocked / finished`
- 原因：最小测试时钟修复已经完成并通过编译与收集检查，但 Docker Desktop Engine 在两个连续检查点均不可达，任务卡要求的 1 + 8 + 9 项真实 PostgreSQL 测试未运行。执行方没有把 collect-only、历史结果或 skip 计作本轮通过。
- 本文只记录执行方实现和验证证据，不是 P4-C11 独立验收，也不表示 P4-A `complete`。

## 起点门禁

- 起点清单：`docs/coordination/snapshots/p4-b6-r2-s2-t1-start.sha256`
- 清单条目：103
- 清单普通 SHA-256：`b1c4c80d8d5a04e2571b9028e38abc7fb99f912c6b2ffba84d799f466e4d5b18`
- 开工前逐文件复算：`matched=103`、`changed=0`、`missing=0`。
- 修改后相对起点：`unchanged=102`、`changed=1`、`missing/deleted=0`；唯一变化的起点文件是 `tests/host/test_postgresql_r1.py`。

## 根因和最小修复

失败用例固定用 `2026-09-26T02:00:00Z` 创建十分钟有效的绑定码，但 HTTP consume 路由在 TestClient 工作线程中读取 `wife_system.api.host_routes.datetime.now(UTC)`。真实时钟推进后，两枚绑定码会在竞争 INSERT 前同时过期，使原期望 `[200, 409]` 变成 `[409, 409]`。

唯一产品/测试代码变更位于 `tests/host/test_postgresql_r1.py`：

1. 导入 `wife_system.api.host_routes` 模块；
2. 给 `test_postgresql_competing_binding_codes_return_safe_replayable_conflict` 增加 pytest `monkeypatch` fixture；
3. 在用例内部定义继承标准库 `datetime` 的 `ControlledDateTime`；
4. 仅在该用例期间把 `host_routes.datetime` 替换为这个测试子类。

`ControlledDateTime.now(UTC)` 返回用例已有的固定 aware 时刻，因此 TestClient 工作线程和创建绑定码的测试线程使用同一时钟。无时区参数时，它先把固定时刻转换为本地时区，再移除 `tzinfo`，返回语义正确的本地 naive 墙钟时间。替换通过 pytest `monkeypatch` fixture 注册，fixture teardown 会自动恢复 `host_routes.datetime`，没有永久修改模块对象。

原固定时间、十分钟生产 TTL、并发 INSERT barrier、`[200, 409]`、败方 `active/attempts=0`、同键 409 replay、撤销赢家后败方新键成功和隐私断言均未修改。没有修改 `src/**`、migration、路由、AuthService、生产 TTL 或错误合同。

## 编译、收集和静态检查

实际结果：

- `python -m compileall -q tests/host/test_postgresql_r1.py`：退出码 0。
- 精确节点 `--collect-only`：1 项。
- 完整 `tests/host/test_postgresql_r1.py --collect-only`：8 项。
- 完整 `tests/host/test_postgresql_r2.py --collect-only`：9 项。
- `python -m pip check`：退出码 0，`No broken requirements found.`
- `git diff --check`：退出码 0；只输出当前工作树既有的 LF→CRLF 行尾提示，没有 whitespace error。
- collect-only 的唯一 warning 是 Starlette `anyio.abc.BlockingPortal` alias 的既有第三方弃用提示。

收集成功只证明测试节点存在和导入成功，不计作实际通过。R2 的本轮真实执行没有发生，因此本轮也没有新增 monkeypatch 跨用例恢复的运行证据；自动恢复依据是 pytest `monkeypatch` fixture 的 teardown 机制，后续必须在 Docker Engine 可用时按任务卡顺序实际运行 R1 后再运行 R2。

## PostgreSQL 环境证据

在启动前重新读取 `docs/coordination/control.md`，版本仍为 `2026-09-26T19:41:00+08:00`，确认本执行智能体是 T1 和 `finance-postgres` 的唯一负责人，其他角色与 P4-C11 保持停止。

检查点 1：

- `docker compose up -d finance-postgres` 在创建容器前失败；
- 错误为 `dockerDesktopLinuxEngine` 命名管道不存在，Docker API 不可达；
- 当前 context 为 `desktop-linux`，Docker client 为 29.8.0；
- 没有 `Docker Desktop` 或 `com.docker.backend` 进程。

检查点 2：

- 再次读取最新 control 后执行 `docker compose ps --services` 和 `docker compose up -d finance-postgres`；
- 两个命令均因相同的命名管道缺失而失败；
- 相同环境条件连续两个检查点无进展，按任务卡停止，不启动桌面应用或修改外部环境。

资源收口：

- 本任务没有成功创建或启动任何项目容器；health 状态不可获取。
- 普通 `docker compose down` 已尝试，因同一 Docker API 不可达而退出 1。
- 最终 `docker compose ps --format json` 也因 Engine 不可达而退出 1，无法从 Compose API 取得空列表；操作系统进程检查仍未发现 Docker Desktop 后端。
- 因容器从未启动，没有本任务遗留的已知运行资源；最终 Compose 服务空列表属于 `unverified`，不得写成已确认。
- 未执行 `down -v`、volume 删除、prune、factory reset、context/global setting 修改或 socket 目录操作。

## 有限测试结果

| 验证组 | 实际执行 | passed | failed | skipped | warning | 结论 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 精确失败节点 | 否 | 0 | 0 | 0 | 0 | `not_run`，Docker Engine 不可达 |
| 完整 PostgreSQL R1（8 项） | 否 | 0 | 0 | 0 | 0 | `not_run`，Docker Engine 不可达 |
| 完整 PostgreSQL R2（9 项） | 否 | 0 | 0 | 0 | 0 | `not_run`，Docker Engine 不可达 |

按任务卡没有重复 Finance 4 项、activity import 10 项、S1 44 项或 326 项本地回归。它们的历史通过结果没有被重新记为本轮证据。

## 文件边界和摘要

相对 103 文件起点：

- changed：`tests/host/test_postgresql_r1.py`
- added：`docs/b6-r2-s2-t1-clock-running.md`
- deleted：无
- 角色进度文件：`docs/coordination/agents/executor.md` 按协作规则更新，位于产品/测试/运行说明摘要之外。

普通 SHA-256：

- `tests/host/test_postgresql_r1.py`：`f0c3144d2aeae4ceee0ac724bbcb6bb1f43607779552c34312bcbcea8a5c8bcb`
- 本运行说明和 executor 角色文件的最终普通 SHA-256 在文件停止修改后记录于 executor 日志和交付消息；文件不能在自身内容中嵌入其最终普通摘要而仍保持该摘要不变。

终点产品/测试/运行说明快照由起点 103 行中替换上述 R1 测试摘要，再加入本运行说明的最终普通 SHA-256，按路径升序拼接 `path<TAB>sha256<LF>` 后复算。最终条目数应为 104；摘要在本文件停止修改后记录于 executor 日志和交付消息。

## 未验证项和停止边界

- 未验证：精确节点的 `[200,409]` 实际结果、R1 8/8、R2 9/9、R1 后 R2 的同进程/顺序恢复证据、PostgreSQL health、最终 Compose 空服务列表。
- 未读取或修改真实密钥、账户、行情、个人数据；未访问 Electron、OpenClaw、微信、DeepSeek 或真实 provider。
- 未修改或运行 `tests/independent/**`，未启动测试智能体、技术顾问或 P4-C11。
- 未执行任何 Git 写操作。
- 后续只有总控重新派发并确认 Docker Engine 可用后，才能按 T1 的有限顺序补跑真实 PostgreSQL 测试；当前执行智能体停止扩展任务。
