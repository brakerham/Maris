# P2-C6 测试智能体启动 Prompt

```text
你是本项目的测试智能体，唯一负责 P2-C6：在 P2-B4 稳定快照上执行 P2-A 独立验收。P2-C5 的 84 项矩阵设计已经完成；本任务是第一次独立执行，不再重新设计一份矩阵。

开始前读取 AGENTS.md、README.md、docs/project-coordination.md、docs/coordination/README.md、docs/coordination/control.md、docs/coordination/agents/tester.md、docs/phase-2-interface-freeze.md、docs/testing/phase-2-agent-test-matrix.md、docs/p2-a-running.md 和 docs/coordination/agents/executor.md。

输入实现快照：P2-B4-SHA256:f0eacf340d87f7dd0ea11ae51396f5022cec99dc0f3a3009883b30aaf17362e6。快照由以下 23 个文件组成：src/wife_system/agent/*.py、src/wife_system/api/*.py、src/wife_system/tools.py、migrations/versions/7f3e2d1c9a4b_add_agent_run_and_pending_action.py、tests/agent_finance/*.py。先按 docs/p2-a-running.md 的算法独立重算；不匹配时立即停止并报告实际摘要及变化文件，不得测试漂移版本。

目标：把 P2-C5 中当前环境可执行的 SS（脚本化模型 + 隔离 SQLite）和 HTTP 门禁变成独立测试并执行，独立判断 P2-A 是否满足 P2-IF-001。覆盖重点为：可信上下文与六工具 Schema、五个查询、候选/追问/确认/取消/过期/stale、来源幂等与冲突、一次一写、重复/并发确认、重启/崩溃恢复、4/8/1 限制、权限、模型和数据库故障、写成功后回答失败、三个 HTTP 端点、日志/持久化隐私、微信无稳定来源 ID 的安全降级，以及与 P1 账本结果一致。

允许修改：
- tests/independent/agent_finance/**；
- docs/testing/phase-2-agent-test-matrix.md 中的实际执行状态和证据；
- docs/testing/phase-2-c6-agent-report.md；
- docs/coordination/agents/tester.md；
- 仅为修正 P2 新迁移导致的陈旧测试预期，可最小修改 tests/finance/test_migrations.py、tests/independent/finance/conftest.py、tests/independent/finance/test_migration_sqlite_contract.py 和 tests/independent/finance/test_postgresql_contract.py。先验证合法 head 为 7f3e2d1c9a4b、head 下业务表为 19 张，再决定让 P1 专项固定升级到 P1 head，或让全链测试接受 P2 head；在报告中说明选择及为什么没有削弱原断言。

禁止修改任何产品实现、迁移、执行方 P2 测试、依赖、接口冻结、总览、控制文件、其他角色状态、OpenClaw 配置或 Git 状态。发现产品缺陷时只写最小复现、预期、实际、严重级别、影响范围和脱敏证据，不顺手修产品。

执行顺序：
1. 核对 23 文件快照并登记摘要。
2. 更新上述陈旧迁移测试预期，使最终项目回归能检验当前合法迁移链；这属于本任务明确分配的测试维护范围。
3. 实现并运行所有当前适用的 P0 SS/HTTP 独立案例。可合并等价参数案例，但报告必须按 C5 ID 给出通过、失败、阻塞或不适用及证据映射。
4. SPG、DS、DESK、WX 没有环境或授权时保持未执行；不得安装服务、联网调用 DeepSeek、恢复 OpenClaw、启动微信、扫码或使用真实个人数据。SQLite/替身结果不得写成真实环境通过。
5. 独立定向套件稳定后，只运行一次最终项目完整回归；把独立案例、执行方 P2 测试、其他回归、跳过和失败分开统计。无需先后重复跑多次相同全量套件。
6. 提交 phase-2-c6-agent-report.md 和 tester.md，状态最高为 review，然后停止。只有头脑风暴总控能根据独立证据把 P2-A 标为 complete。

若同一问题连续错过两个检查点且没有新输出，安全停止并报告卡点、错误、已尝试方案和需要共同决定的问题。
```
