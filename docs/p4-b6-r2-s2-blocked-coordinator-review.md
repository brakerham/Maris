# P4-B6-R2-S2 受阻总控核对

- 核对角色：头脑风暴总控
- 核对时间：2026-09-26 19:20，Asia/Shanghai
- S2 状态：`blocked / finished`
- 整体 `P4-B6-R2` 状态：`blocked / finished`
- P4-C11：未派发

## 结论

总控确认 S2 的阻塞来自既有执行方测试的固定时钟过期，不是当前产品缺陷，也不是 PostgreSQL、Docker 或 S1 migration 缺陷。

新增的 9 项 R2 真实 PostgreSQL 测试全部通过，覆盖 S1 migration、candidate Profile version、memory CAS、pending commit recovery、run takeover/fence、message/event、setting/receipt、Page/cursor 和 production factory。Finance 4 项与 activity import 10 项既有 PostgreSQL 基线也全部通过。

唯一失败是 `tests/host/test_postgresql_r1.py::test_postgresql_competing_binding_codes_return_safe_replayable_conflict`。该用例用固定的 `2026-09-26T02:00:00Z` 创建十分钟有效的绑定码，而 HTTP consume 路由读取测试运行时的真实 UTC；本轮执行时两枚 code 已经过期，所以实际 `[409,409]`，没有到达预期的 active external subject 唯一约束竞争。诊断中的两枚 code 均为 `expired / attempts=0`、active binding 为 0、receipt 为 completed rejected，与这个根因一致。

## 文件与摘要核对

总控复算执行智能体报告的三个交付文件，普通 SHA-256 均匹配：

```text
tests/host/test_postgresql_r2.py	d8ad7814dd237e62dab12d993dad591d0434b47d4615b65c02de0e93e203b002
docs/b6-r2-s2-postgresql-running.md	d141267e078c664fad5d9b742547114fd17245d7bee5573625b55ea298ca780e
docs/coordination/agents/executor.md	9df66b13b0c0525fb0c2ecf2a02f16bc44f7402fc508adb8a1d7f27366441baa
```

101 项 S2 起点仍全部匹配，新增产品/执行方测试交付只有 R2 PostgreSQL 测试和 S2 运行说明。把 101 行起点与这两个新增文件按路径排序、使用 `path<TAB>sha256<LF>` 拼接后，103 项总摘要可复算为：

```text
b1c4c80d8d5a04e2571b9028e38abc7fb99f912c6b2ffba84d799f466e4d5b18
```

总控据此生成 T1 的 103 项普通摘要起点：

```text
docs/coordination/snapshots/p4-b6-r2-s2-t1-start.sha256
entries=103
manifest_sha256=b1c4c80d8d5a04e2571b9028e38abc7fb99f912c6b2ffba84d799f466e4d5b18
```

协调角色日志不进入产品/执行方测试快照。

## 失败机制核对

失败用例在创建 runtime/app 后定义：

```python
now = datetime(2026, 9, 26, 2, 0, tzinfo=UTC)
```

并用这个固定时间创建 code。HTTP 路由 `consume_binding_code` 则执行：

```python
now = datetime.now(UTC)
```

因此用例只在真实时间不晚于固定时间十分钟时有效，运行日期一旦推进就必然在 INSERT barrier 之前进入过期分支。这和此前 P2 Agent 测试的固定日期漂移问题属于同类测试基础设施缺陷。

项目已经有 `tests/agent_finance/conftest.py` 的 `ControlledDateTime + monkeypatch` 模式，证明 pytest 对模块级 `datetime` 的测试期替换能够覆盖 TestClient 工作线程，并在 fixture 结束时恢复。T1 应复用这一模式，但只作用于 `wife_system.api.host_routes.datetime` 和这个 R1 用例，避免扩大修改面。

## 最小返修裁定

T1 只允许修改 `tests/host/test_postgresql_r1.py`：

- 给失败用例增加 pytest `monkeypatch` fixture；
- 在创建 TestClient 请求前，用 `datetime` 的测试子类或等价受控对象把 `wife_system.api.host_routes.datetime.now(UTC)` 固定为该用例的 `now`；
- 保留固定的 `2026-09-26T02:00:00Z`、十分钟生产 TTL、原 `[200,409]`、receipt/replay/revoke/retry 和隐私断言；
- monkeypatch 必须在用例结束后自动恢复，不能影响后续用例或其他线程；
- 不把固定时间简单替换成真实当前时间来掩盖问题，不修改生产路由、AuthService、TTL、migration 或错误合同。

T1 只需复跑原 R1 PostgreSQL 文件和新增 R2 PostgreSQL 文件。Finance 与 activity import 的 14 项已在相同 S2 产品快照上通过且相关文件不变；326 项非 PostgreSQL 回归、S1 44 项和 S2 其余基线不重复执行。

T1 全绿并生成稳定快照后，S2 和整体 R2 可以提交 `review / finished`；它们仍不是独立验收。总控核对 T1 后才派发 P4-C11。

