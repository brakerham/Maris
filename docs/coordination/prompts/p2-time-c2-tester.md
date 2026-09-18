# P2-TIME-C2：Agent 测试时钟定向独立复验

状态：已完成并由总控于 2026-09-18 验收为 `complete`；不得重复派发。证据见 `docs/testing/p2-time-c2-report.md`。

你只负责核验 `P2-TIME-R1` 的测试时钟维护。绑定下列七文件快照，完成后提交 `review` 并停止；不要重复 C6、C7、PostgreSQL、真实模型、桌面或微信测试。

```text
P2-TIME-R1-SHA256:4f7840a0bfb27928b39e22933030fb6a600845b9ae4d19c8322b44edcb687e64
```

## 必读输入

按顺序读取 `AGENTS.md`、`README.md`、`docs/project-coordination.md`、`docs/coordination/README.md`、`docs/coordination/control.md`、`docs/coordination/agents/tester.md` 和本文件。然后读取：

- `docs/coordination/prompts/p2-time-r1-executor.md`
- `docs/p2-time-r1-running.md`
- `docs/coordination/agents/executor.md`
- `tests/agent_finance/conftest.py`
- `tests/agent_finance/test_clock.py`
- `src/wife_system/agent/application.py`
- `src/wife_system/agent/pending.py`

接单前只读检查 Git 状态和最新控制版本。若快照不匹配，或执行方允许范围中的文件仍在变化，停止测试并报告；不要修改文件迁就快照。

## 快照算法与范围

摘要覆盖 `tests/agent_finance/` 下全部七个 `.py` 文件。相对 POSIX 路径按 Unicode 升序，依次写入 4 字节大端路径长度、UTF-8 路径、8 字节大端内容长度和原始文件字节，再计算整体 SHA-256。

先独立重算并记录摘要。另行确认相对于输入提交 `e50e9b5`，以下五个原测试文件没有变化：

- `tests/agent_finance/__init__.py`
- `tests/agent_finance/test_failures_and_policy.py`
- `tests/agent_finance/test_migration.py`
- `tests/agent_finance/test_tools_and_http.py`
- `tests/agent_finance/test_vertical_slice.py`

## 文件和职责边界

允许修改：

- `docs/testing/p2-time-c2-report.md`
- 如确有必要，可在 `tests/independent/time_fixture/**` 新增测试方专属检查；不得复制执行方测试充数
- `docs/coordination/agents/tester.md`

只读：`tests/agent_finance/**`、全部 `src/**`、其他 `tests/independent/**`、既有测试报告、接口冻结、执行日志和运行说明。

禁止修改产品代码、执行方测试及夹具、执行方文档、总控文件、其他角色日志、依赖、迁移、Compose、OpenClaw、微信、DeepSeek、桌面端和任何 Git 状态。不得安装依赖、启动数据库容器、调用真实 API 或修改系统时间。

## 必须验证

1. 独立重算七文件快照，并检查变更范围：只有 `conftest.py` 的局部时钟夹具和新增 `test_clock.py` 改变测试行为；产品代码、TTL 与原五个测试文件没有改动。
2. 静态核对没有删除测试，没有 `skip`、`xfail`、断言放宽、动态改日历常量、真实 sleep、系统时钟操作、吞掉 `pending_action_expired`，也没有把产品方法替换成恒定成功。
3. 使用仓库现有虚拟环境和全新的 `scratch/p2-time-c2-*` basetemp，独立收集并运行 `tests/agent_finance`。预期收集 28 项、28 项通过；warning 单列，不把环境错误算作产品失败。
4. 独立核对原 23 项仍通过，新增五个参数化节点覆盖：24h−1µs 可确认；恰好 24h 和 24h+1µs 拒绝且零支出/零写回执；HTTP 默认取时；新实例取消不记账。
5. 独立执行同进程还原审计：每项测试 setup 前、完整 teardown 后，以及 pytest 返回后，`application.datetime` 与 `pending.datetime` 都恢复为标准库 `datetime`。审计覆盖全部 28 项，并验证线程执行结束后没有泄漏。
6. 在真实运行时间已经晚于固定 `RECEIVED_AT` 超过 24 小时的条件下，确认正常确认、补充信息、取消、故障恢复和并发/重启场景仍通过；固定时间常量不得改成测试当天。
7. 检查时钟只影响 `application` 与 `pending` 模块在本测试目录生命周期内的名称引用；标准库、财务层和其他测试目录不被全局冻结。说明 `monkeypatch.context()` 与函数级 autouse fixture 的恢复边界。
8. 检查 `AgentTestClock` 只允许时间前进，线程共享读写有锁；timezone-aware 与无时区分支的返回语义不改变现有产品契约。
9. 把执行方 28 项复跑与测试方独立审计分别统计。报告实际命令、节点数、通过/失败、warning、环境事件、未验证项和结论。

系统临时目录不可写时，只能使用 `scratch/` 下本任务全新的 basetemp，不删除其他目录。默认沙箱初始化失败可按已有受控方式继续工作区命令，但要把环境事件与测试断言分开记录。

## 判定与交付

全部验收点通过时，建议总控把 `P2-TIME-R1` 标为 `complete`。若发现失败，提交最小复现、预期、实际、严重级别和影响范围；不要修执行方文件。

交付：

- `docs/testing/p2-time-c2-report.md`
- 必要时新增的测试方专属检查及其说明
- 更新 `docs/coordination/agents/tester.md`

状态只能提交为 `review`。最终 `complete`、本地 Git 提交以及是否进入下一产品里程碑由头脑风暴总控决定。

## 进度与停止

接单、快照门禁、静态审计、28 项复跑、还原审计和交付时更新自己的当前执行快照。预计超过五分钟的步骤先记录下一检查点，至少每十分钟更新心跳。

连续错过两个检查点或同一错误无进展时，在安全位置停止，保留已有证据并报告卡点、最后脱敏错误、已尝试办法、可能原因和待决定问题，不无限重试。新 `control.md` 与本任务冲突时服从新控制并停止旧动作。

只使用虚拟数据，不读取、输出或记录密钥、令牌、二维码、账号标识或真实个人财务数据。
