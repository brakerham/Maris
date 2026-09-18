# P2-TIME-R1：Agent 执行方测试时钟交接

- 交付状态：`review`；执行方验证结束，等待测试智能体定向复验及总控验收。
- 控制版本：`2026-09-18T10:12:45+08:00`；任务卡：`docs/coordination/prompts/p2-time-r1-executor.md`。
- 任务输入：`9b73dbd`；实际工作区 HEAD 为 `e50e9b5`（总控任务文档提交）。两提交间 `src/**` 和 `tests/agent_finance/**` 无差异；接单前工作区干净。
- 数据与运行：现有 Python/pytest、脚本化模型、虚拟财务数据、临时 SQLite；只执行本目录测试。

## 1. 原因与选择

原夹具 `RECEIVED_AT` 是 `2026-09-16 12:00 UTC`。创建候选时它成为 `created_at`，候选默认 `expires_at = created_at + 24h`。原测试虽然给 `resume(now=RECEIVED_AT)` 传入时间，但 `resume -> _pending_for_run -> application.get -> pending.get` 还会先执行一次不带 `now` 的查询；后者读取真实 `datetime.now(UTC)`，先把旧日期候选持久化为 `expired`。

修复仅在测试目录 `conftest.py` 中加入函数级 autouse `agent_clock`：每项测试创建一个 `AgentTestClock`，默认仍为原 `RECEIVED_AT`，通过 `advance(timedelta(...))` 显式推进。`ControlledDateTime` 继承标准库 datetime，`now()` 返回该时钟的普通 datetime 值；用 monkeypatch 替换 application/pending 两个模块实际查询的名字。

| 方案 | 本轮处理 |
| --- | --- |
| 函数级 pytest fixture + 局部 monkeypatch | 采用；无新依赖，可精确推进并自动恢复 |
| 换成今天或真实 `datetime.now()` | 不采用；会重新引入日历依赖，改变固定月份和相对日期证据 |
| 在产品中注入 Clock | 留给后续架构讨论；本轮源码只读 |
| 第三方全局冻结库 | 不引入；局部两个引用已覆盖本轮路径 |

原 23 项测试的四个 test 文件和全部断言原样保留，没有删除、skip、xfail、放宽金额/月份/有效性断言、修改 TTL 或吞掉过期异常。`__init__.py` 也未改动。只读 Git 差异核对确认 `src/**`、`tests/independent/**` 和这五个既有文件无变更。

## 2. 实际改动与取时路径

| 文件 | 改动 |
| --- | --- |
| `tests/agent_finance/conftest.py` | `AgentTestClock`、线程共享 Lock、函数级 `agent_clock`、两个模块的 datetime monkeypatch |
| `tests/agent_finance/test_clock.py` | 新增五项参数化/独立回归：到期边界三项、HTTP 默认取时一项、重启后取消一项 |
| `docs/p2-time-r1-running.md` | 本交接、原节点清单、准确验证命令与快照 |
| `docs/coordination/agents/executor.md` | 接单、基线、夹具、自测与交接状态 |

实际夹具的核心片段如下（完整实现见 `conftest.py`）：

```python
@pytest.fixture(autouse=True)
def agent_clock(monkeypatch: pytest.MonkeyPatch) -> Iterator[AgentTestClock]:
    clock = AgentTestClock()

    class ControlledDateTime(datetime):
        @classmethod
        def now(cls, tz: tzinfo | None = None) -> datetime:
            current = clock.now()
            if tz is None:
                return current.astimezone().replace(tzinfo=None)
            return current.astimezone(tz)

    with monkeypatch.context() as patch:
        patch.setattr(application_module, "datetime", ControlledDateTime)
        patch.setattr(pending_module, "datetime", ControlledDateTime)
        yield clock
```

HTTP 三条路由本身不取时间；创建请求调用没有 `received_at` 的 `application.start()`，确认请求调用没有 `now` 的 `application.resume()`。因此 application 模块的默认时间也必须受控。状态 GET 和 resume 内部查询到 pending 模块后仍读同一个时钟。FastAPI 同步路由工作线程、原并发确认线程及新创建的应用实例都查询同样的模块引用。

`AgentTestClock.now()` 和 `advance()` 用同一 Lock 保护读写。新增 HTTP 用例让请求自然在 TestClient 工作线程执行；原并发/恢复用例仍使用线程池，并在离开测试前等待线程退出。无需真实 sleep，也不改变系统时钟。

补丁的边界是本目录的一次函数测试：pytest 为下一项创建新的时钟；`monkeypatch.context()` 在 yield 退出时恢复原引用，测试断言失败时也会走 pytest teardown。子 context 不撤销同一测试为数据库故障等设置的其他 monkeypatch。标准库 datetime 以及财务层、其他测试目录未被冻结；这不是全进程的所有时间源替换。

## 3. 修复前原 23 项与五项失败

收集命令：

```powershell
.venv\Scripts\python.exe -m pytest -o addopts="" -p no:cacheprovider tests/agent_finance --collect-only -q
```

结果：`23 tests collected in 2.00s`。原节点清单（参数化中文 ID 保留 pytest 原始转义）：

```text
tests/agent_finance/test_failures_and_policy.py::test_write_tool_is_hidden_without_permission_and_direct_guess_is_denied
tests/agent_finance/test_failures_and_policy.py::test_second_write_and_total_tool_limits_stop_deterministically
tests/agent_finance/test_failures_and_policy.py::test_plan_or_question_can_finish_without_finance_write
tests/agent_finance/test_failures_and_policy.py::test_policy_overrides_model_guess_for_approximate_or_planned_expense[\u5348\u996d\u5927\u7ea6\u5341\u51e0\u5143-ask_amount]
tests/agent_finance/test_failures_and_policy.py::test_policy_overrides_model_guess_for_approximate_or_planned_expense[\u660e\u5929\u8ba1\u5212\u5348\u996d 18 \u5143-ask_record_intent]
tests/agent_finance/test_failures_and_policy.py::test_relative_date_uses_trusted_received_time_not_model_guess
tests/agent_finance/test_failures_and_policy.py::test_multiple_expenses_in_one_message_are_rejected_before_candidate
tests/agent_finance/test_failures_and_policy.py::test_resource_change_makes_candidate_stale
tests/agent_finance/test_failures_and_policy.py::test_database_failure_never_returns_false_success_and_can_recover
tests/agent_finance/test_failures_and_policy.py::test_retryable_model_failure_gets_one_bounded_retry
tests/agent_finance/test_migration.py::test_p2_migration_upgrade_repeat_downgrade_and_recover
tests/agent_finance/test_tools_and_http.py::test_five_read_tools_are_bounded_and_use_deterministic_finance_values
tests/agent_finance/test_tools_and_http.py::test_model_schemas_exclude_trusted_context_and_reject_confirmation_override
tests/agent_finance/test_tools_and_http.py::test_wechat_without_stable_event_can_only_create_candidate
tests/agent_finance/test_tools_and_http.py::test_expired_candidate_and_wrong_identity_do_not_commit
tests/agent_finance/test_tools_and_http.py::test_http_run_resume_status_and_strict_schema
tests/agent_finance/test_tools_and_http.py::test_persistent_rows_store_digests_not_private_input
tests/agent_finance/test_tools_and_http.py::test_execution_logs_are_structured_and_do_not_include_private_input
tests/agent_finance/test_vertical_slice.py::test_complete_candidate_confirm_and_duplicate_confirmation
tests/agent_finance/test_vertical_slice.py::test_same_desktop_event_replays_and_conflicting_payload_is_rejected
tests/agent_finance/test_vertical_slice.py::test_missing_fields_resume_to_confirmation
tests/agent_finance/test_vertical_slice.py::test_concurrent_confirmation_and_restart_recovery
tests/agent_finance/test_vertical_slice.py::test_concurrent_same_source_event_runs_model_once
```

基线命令（执行前创建 scratch 父目录，并确认该 basetemp 从未存在）：

```powershell
New-Item -ItemType Directory -Path scratch -Force | Out-Null
.venv\Scripts\python.exe -m pytest -o addopts="" -p no:cacheprovider --basetemp=scratch/p2-time-r1-baseline-20260918-1338 tests/agent_finance --tb=short -q
```

实际结果：`5 failed, 18 passed, 1 warning in 8.42s`。五项失败节点：

1. `test_failures_and_policy.py::test_resource_change_makes_candidate_stale`：预期 stale，实际 expired。
2. `test_failures_and_policy.py::test_database_failure_never_returns_false_success_and_can_recover`：进入故障重试主体前 expired。
3. `test_vertical_slice.py::test_complete_candidate_confirm_and_duplicate_confirmation`：正常确认前 expired。
4. `test_vertical_slice.py::test_missing_fields_resume_to_confirmation`：补充信息前 expired。
5. `test_vertical_slice.py::test_concurrent_confirmation_and_restart_recovery`：恢复/并发确认前 expired。

## 4. 验证结果与准确命令

仅加入夹具、尚未增加新案例时，原 23 项运行：

```powershell
.venv\Scripts\python.exe -m pytest -o addopts="" -p no:cacheprovider --basetemp=scratch/p2-time-r1-original-green-20260918-1341 tests/agent_finance --tb=short -q
```

结果：`23 passed, 1 warning in 8.47s`，退出 0。

新增五项的业务证据：

| 模拟时间/场景 | 预期并已验证 |
| --- | --- |
| 创建后 24h−1µs，新应用实例默认 get/resume | 仍需确认并提交一次；18.00 元；余额 98,200 分，1 笔支出、1 条写回执 |
| 创建后恰好 24h，独立候选 | pending_action_expired；余额 100,000 分，0 笔支出、0 条写回执 |
| 创建后 24h+1µs，独立候选 | 同上，拒绝确认；不依赖另一个已过期候选的状态 |
| HTTP 默认时间，推进 10 分钟 | 创建/发生时间为 RECEIVED_AT；状态正常；确认更新时间等于推进后的时间；余额 98,200 分 |
| 创建后 1h，新应用实例取消 | cancelled 持久恢复；无支出，余额 100,000 分 |

每项边界用例都有新的时钟、数据库和候选，并先断言时钟从原 RECEIVED_AT 开始。到期判定仍由未修改的产品代码 `expires_at <= check_time` 执行；测试未替换候选 get、确认、财务写入或错误处理。

最终 28 项在同一 Python 进程中运行，并额外通过 pytest hook 在每项 setup 前和完整 teardown 后断言两个模块已经恢复标准库 datetime；pytest.main 返回后再次检查。下面是实际执行的检查脚本：

```powershell
@'
from datetime import UTC, datetime
from pathlib import Path
import pytest
from wife_system.agent import application, pending

baseline = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)
actual = datetime.now(UTC)
print(f"REAL_UTC={actual.isoformat()}", flush=True)
print(f"FIXED_UTC={baseline.isoformat()} AGE_HOURS={(actual-baseline).total_seconds()/3600:.3f}", flush=True)
assert application.datetime is datetime
assert pending.datetime is datetime

class IsolationAudit:
    def __init__(self):
        self.before = []
        self.after = []

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_setup(self, item):
        assert application.datetime is datetime
        assert pending.datetime is datetime
        self.before.append(item.nodeid)

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_runtest_teardown(self, item, nextitem):
        yield
        assert application.datetime is datetime
        assert pending.datetime is datetime
        self.after.append(item.nodeid)

audit = IsolationAudit()
base = Path("scratch/p2-time-r1-final-20260918-1344")
assert not base.exists(), "Use a fresh basetemp; never delete another run"
code = pytest.main([
    "-o", "addopts=", "-p", "no:cacheprovider",
    f"--basetemp={base.as_posix()}",
    "tests/agent_finance", "--tb=short", "-q",
], plugins=[audit])
assert application.datetime is datetime
assert pending.datetime is datetime
assert audit.before == audit.after
print(f"FUNCTION_ISOLATION={len(audit.after)} RESTORED_APPLICATION=True RESTORED_PENDING=True", flush=True)
raise SystemExit(code)
'@ | .venv\Scripts\python.exe -
```

复验时只需把 basetemp 换成 scratch 下新的任务目录，保留已有目录，不删除历史产物。

实际输出：

```text
REAL_UTC=2026-09-18T05:44:16.430166+00:00
FIXED_UTC=2026-09-16T12:00:00+00:00 AGE_HOURS=41.738
28 passed, 1 warning in 8.33s
FUNCTION_ISOLATION=28 RESTORED_APPLICATION=True RESTORED_PENDING=True
```

固定时间比真实运行日期早 41.738 小时，仍完成正常确认、取消、补充信息及故障重试；日历常量没有更新。真实时间仅作为执行证据打印，不成为新测试依赖，未来日期不会让回归重新漂移。

附加检查：

```powershell
.venv\Scripts\python.exe -m compileall -q tests/agent_finance
git diff --check
```

两项均退出 0。环境：正常沙箱命令启动报 `helper_unknown_error: setup refresh had errors`，后续采用已获准的沙箱外工作区命令继续；未改系统设置。鉴于既有系统 tmp 与 `.pytest_cache` 权限问题，本轮一开始使用全新 scratch basetemp 和 `-p no:cacheprovider`，未出现新的 pytest 环境错误。唯一 warning 仍为 Starlette 的 AnyIO `BlockingPortal` 弃用提示，未屏蔽。

## 5. 快照与交接

```text
P2-TIME-R1-SHA256:4f7840a0bfb27928b39e22933030fb6a600845b9ae4d19c8322b44edcb687e64
```

覆盖本目录全部七个 `.py` 文件（含未修改的原文件）：

| 相对 POSIX 路径 | 文件 SHA-256 |
| --- | --- |
| `tests/agent_finance/__init__.py` | `a94ceade41249f0bdecc5ce6addc146136fbe01588006acf82fdb078538e110c` |
| `tests/agent_finance/conftest.py` | `5579022db1a2b81ac51c55dacabd3b4d23fb7812420f6d7d73e52a737b6cf2fe` |
| `tests/agent_finance/test_clock.py` | `0993de72189561133d3614592abd6fd723ba9cf5c7b2aafdcc08bc7a2fc48b85` |
| `tests/agent_finance/test_failures_and_policy.py` | `ea80adae1f539b741726037b4f2aef43de4a5d518ac074db3f9f69bc75320b3a` |
| `tests/agent_finance/test_migration.py` | `16d776d6688bd8e23df60f5e1d5b206bd0f1f668c4fb7cbb5fd2893c02fd1d89` |
| `tests/agent_finance/test_tools_and_http.py` | `a1a4dc8c29abea24900949af634c1abd2b2205e3c63eaf1e593799545000831c` |
| `tests/agent_finance/test_vertical_slice.py` | `1f4b140416551e692a9d4d42e66cb8c78b0cfabed4b4982af6fcdbcee9f72b8f` |

整体摘要严格按相对 POSIX 路径的 Unicode 升序，依次写入 4 字节大端路径字节长度、UTF-8 路径、8 字节大端内容长度和原始文件字节，再做整体 SHA-256；不是对单文件 hash 字符串拼接。运行说明、角色日志、scratch 与 pycache 不参与快照。

临时执行方只读辅助 `time_fixture_review` 核对了双模块补丁、间接 get、HTTP、线程、TTL 三边界和恢复策略，未发现阻止交付的缺口；它未写文件、未运行测试或服务，已停止。这属于执行方自查，不是独立验收。

待测试智能体绑定本快照独立核对原断言保留、日期隔离、到期三边界及还原机制，进行一次任务范围内定向复验；最终 complete 和 Git 写操作由总控负责。无执行阻塞。独立测试目录也有固定 NOW 的相同风险，本次只提示，未修改或运行该目录。

未验证：测试智能体尚未验收本次快照；未执行 C6 全量、C7/PostgreSQL、真实模型、桌面、微信或外部联调。旧报告和既有运行说明保留历史原样。测试 scratch 目录保留，未清理其他任务的数据。

## 6. 教学小练习

在独立练习副本中，为 `needs_input` 候选补一个场景：先推进至创建后 23h，补充账户/分类，再推进到创建后恰好 24h 尝试确认。预测补充字段是否延长原 TTL，随后用候选 `expires_at`、错误码、余额和支出条数验证。不要改产品 TTL，也不要用真实 sleep。正式仓库的练习改动须另获分配。
