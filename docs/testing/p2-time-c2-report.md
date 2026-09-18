# P2-TIME-C2：Agent 测试时钟定向独立复验报告

- 任务：`P2-TIME-C2`
- 交付状态：`review`
- 控制版本：`2026-09-18T13:57:09+08:00`
- 输入快照：`P2-TIME-R1-SHA256:4f7840a0bfb27928b39e22933030fb6a600845b9ae4d19c8322b44edcb687e64`
- 数据边界：仅使用脚本化模型、虚拟财务数据、临时 SQLite 和仓库 `scratch/` 隔离目录

## 结论

P2-TIME-R1 通过定向独立复验。七文件快照完全匹配；原 23 项执行方测试保持通过；新增五个节点正确覆盖 24 小时边界、HTTP 默认取时和新实例取消；测试方同进程审计证明每项测试完整 teardown 后时钟引用恢复，线程没有泄漏。

测试智能体建议总控将 `P2-TIME-R1` 标为 `complete`。本任务只提交 `review`；最终验收和本地 Git 提交由头脑风暴总控决定。

## 快照与变化范围

七文件摘要在测试前、静态审计后和全部执行后均为：

`4f7840a0bfb27928b39e22933030fb6a600845b9ae4d19c8322b44edcb687e64`

| 文件 | SHA-256 |
| --- | --- |
| `tests/agent_finance/__init__.py` | `a94ceade41249f0bdecc5ce6addc146136fbe01588006acf82fdb078538e110c` |
| `tests/agent_finance/conftest.py` | `5579022db1a2b81ac51c55dacabd3b4d23fb7812420f6d7d73e52a737b6cf2fe` |
| `tests/agent_finance/test_clock.py` | `0993de72189561133d3614592abd6fd723ba9cf5c7b2aafdcc08bc7a2fc48b85` |
| `tests/agent_finance/test_failures_and_policy.py` | `ea80adae1f539b741726037b4f2aef43de4a5d518ac074db3f9f69bc75320b3a` |
| `tests/agent_finance/test_migration.py` | `16d776d6688bd8e23df60f5e1d5b206bd0f1f668c4fb7cbb5fd2893c02fd1d89` |
| `tests/agent_finance/test_tools_and_http.py` | `a1a4dc8c29abea24900949af634c1abd2b2205e3c63eaf1e593799545000831c` |
| `tests/agent_finance/test_vertical_slice.py` | `1f4b140416551e692a9d4d42e66cb8c78b0cfabed4b4982af6fcdbcee9f72b8f` |

只读 Git 对比确认，以下五个原文件相对 `e50e9b5` 没有变化：

- `tests/agent_finance/__init__.py`
- `tests/agent_finance/test_failures_and_policy.py`
- `tests/agent_finance/test_migration.py`
- `tests/agent_finance/test_tools_and_http.py`
- `tests/agent_finance/test_vertical_slice.py`

测试行为变化只来自 `conftest.py` 的局部测试时钟和新增 `test_clock.py`。工作区中同时存在总控与执行方的已知协调文档变化；本任务没有修改或覆盖这些文件。产品 `src/**`、TTL、依赖和迁移没有变化。

## 静态审计

| 验收点 | 结果 |
| --- | --- |
| 删除原测试、skip、xfail | 未发现 |
| 放宽原断言或修改金额、月份、固定日期 | 未发现；五个原测试文件逐字无差异 |
| 动态改日历常量 | 未发现；`RECEIVED_AT` 仍是 `2026-09-16 12:00 UTC` |
| 真实 sleep 或系统时钟操作 | 未发现 |
| 吞掉 `pending_action_expired` | 未发现；恰好及超过 24h 均显式断言该错误 |
| 把产品方法替换成恒定成功 | 未发现；新增夹具只替换两个模块的 `datetime` 名称引用 |
| 产品 TTL/到期比较 | 未改；仍为 24h，且 `expires_at <= check_time` 时过期 |
| 零副作用断言 | 到期案例检查零支出、余额不变和零 `record_expense` 回执 |

`agent_clock` 是函数级 autouse fixture。它在 `monkeypatch.context()` 内只替换 `application.datetime` 和 `pending.datetime`；子 context 退出时恢复这两个引用，不撤销测试自身的其他 monkeypatch。标准库 datetime、财务层和其他测试目录不被全局冻结。

`AgentTestClock.now()` 与 `advance()` 使用同一个 `Lock`。负增量抛出 `ValueError`，零增量不后退。测试方另用 8 个线程累计执行 8,000 次一微秒推进，最终值精确等于起点加 8,000 微秒。

`ControlledDateTime.now(tz=None)` 返回本地 naive datetime；传入时区时返回相应 aware datetime。运行时审计验证 UTC aware 值等于固定时钟，naive 值不含时区，未改变现有产品取时分支的返回形态。

## 执行方测试复跑

### 收集

命令：

```powershell
.venvScriptspython.exe -m pytest -o addopts="" -p no:cacheprovider --basetemp scratch/p2-time-c2-collect-2625d1a6328348b78b733b0e76ebcad4 tests/agent_finance --collect-only -q
```

结果：28 个节点，和预期一致。

### 28 项复跑

命令：

```powershell
.venvScriptspython.exe -m pytest -o addopts="" -p no:cacheprovider --basetemp scratch/p2-time-c2-run-af8b937e08834db49ed2a6ac433f441a tests/agent_finance --tb=short -q -ra
```

结果：28 passed、0 failed、1 warning，耗时 8.78 秒。

### 原 23 项单独复跑

命令使用四个原测试模块及全新 basetemp `scratch/p2-time-c2-original23-17acde6617bc49e289af68a1629aa819`，排除新增 `test_clock.py`。

结果：23 passed、0 failed、1 warning，耗时 6.58 秒。

唯一 warning 是 Starlette TestClient 对 AnyIO `BlockingPortal` 旧别名的弃用提示。它在收集和三轮执行中稳定出现，不影响测试收集、执行或业务断言。

## 新增五节点证据

| 节点 | 实际结果 |
| --- | --- |
| 24h−1µs，新实例确认 | 可确认；提交 18.00 元，余额 98,200 分，1 笔支出、1 条写回执 |
| 恰好 24h | 返回 `pending_action_expired`；余额 100,000 分，零支出、零写回执 |
| 24h+1µs | 返回 `pending_action_expired`；余额 100,000 分，零支出、零写回执 |
| HTTP 默认取时 | 创建时间、业务发生时间和推进十分钟后的确认更新时间均来自受控时钟 |
| 新实例取消 | 一小时后恢复并取消；状态持久化，不记账，余额保持 100,000 分 |

三个边界参数各自使用新的函数级时钟、数据库和候选，避免已过期状态相互污染。

## 测试方独立还原审计

测试方以内嵌 pytest 插件在同一 Python 进程再次运行全部 28 项，使用全新 basetemp `scratch/p2-time-c2-audit-1dad16a884f04074aa4ca66fb7e6d31e`。

审计点：

1. 每项 setup 前，`application.datetime` 和 `pending.datetime` 必须是标准库 `datetime`。
2. 每项 call 开始时，两个模块必须共享受控类；标准库和财务层保持原引用。
3. 完整 teardown 后，两个模块必须恢复标准库引用。
4. pytest 返回后再次检查恢复状态。
5. 对比 pytest 前后存活的非守护线程集合，验证线程池和 TestClient 工作线程均已结束。

结果：

```text
28 passed, 1 warning
REAL_UTC=2026-09-18T06:33:17.502766+00:00
FIXED_UTC=2026-09-16T12:00:00+00:00 AGE_HOURS=42.555
RESTORE_AUDIT=28/28
RESTORED_APPLICATION=True RESTORED_PENDING=True
STDLIB_UNCHANGED=True FINANCE_UNCHANGED=True
NAIVE_AWARE_SEMANTICS=True
NON_DAEMON_THREAD_LEAKS=0
```

固定测试时间比真实运行时间早 42.555 小时，已经超过产品 24 小时 TTL。原 23 项中的正常确认、补充信息、资源 stale、数据库故障恢复、并发确认和重启恢复，以及新增取消场景仍按各自预期通过，证明回归不再依赖执行当天日期。

## 环境事件

- 所有 pytest 运行从一开始就使用本任务全新的 `scratch/p2-time-c2-*` basetemp，并关闭 pytest cacheprovider；没有删除或复用其他任务目录。
- 一次静态审计内嵌命令因 PowerShell 双引号截断而产生 SyntaxError；修正命令封装后同一审计通过。该事件发生在测试执行前，没有修改项目文件，也不构成产品或测试断言失败。
- 未遇到新的系统临时目录写入错误。

## 未验证范围

按任务卡没有执行：

- C6 全量回归、C7 或任何 PostgreSQL 测试；
- 真实 DeepSeek、桌面端、OpenClaw 或微信；
- 其他测试目录的业务回归；
- 产品时钟重构或第三方全局时间冻结方案。

这些范围不影响本次对 P2-TIME-R1 测试基础设施维护的定向结论。

## 文件边界

本任务没有新增独立测试文件；独立证据来自静态审计、单独原 23 项复跑、测试方内嵌 pytest 还原插件和线程安全实验。没有复制执行方测试充数。

没有修改 `tests/agent_finance/**`、`src/**`、执行方文档、控制/总览、其他角色日志、依赖、迁移、Compose 或任何 Git 状态，也没有启动数据库和外部服务。