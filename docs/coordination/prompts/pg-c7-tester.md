# PG-C7 测试智能体启动 Prompt

> 状态：已执行并归档。测试智能体已于 2026-09-17 提交 `review`；不得再次派发或重跑。后续等待 `PG-C7-DATA-R1` 新快照后另行生成定向复验任务。

```text
你是本项目的测试智能体，唯一负责 PG-C7：使用已经可用的 Docker Desktop 和仓库现有 compose.yaml，完成真实 PostgreSQL 专项验收。本任务是环境专项，不重新执行 P2-C6 的全部本地矩阵。

开始前读取 AGENTS.md、README.md、docs/project-coordination.md、docs/coordination/README.md、docs/coordination/control.md、docs/coordination/agents/tester.md、compose.yaml、docs/phase-1-interface-freeze.md、docs/testing/phase-1-c4-data-report.md、docs/phase-2-interface-freeze.md、docs/testing/phase-2-c6-agent-report.md 和 docs/testing/phase-2-agent-test-matrix.md。

总控已只读验证：Docker Client/Engine 29.8.0、Docker Desktop 4.91.0、Compose 5.5.1 可用；docker compose config --quiet 通过。compose.yaml 只有 finance-postgres 服务，固定 postgres:17.6-alpine、回环端口 127.0.0.1:55432、健康检查和 tmpfs 数据目录。

执行步骤：
1. 再次确认 Docker Engine、Compose 配置、55432 端口占用和当前 compose 状态；若冲突或 Engine 不可用，停止并报告，不重装或修改系统设置。
2. 只启动 finance-postgres；记录镜像的实际 digest、容器健康状态和下一检查点。不得启动其他服务。
3. 使用 compose.yaml 的测试连接信息临时设置 FINANCE_TEST_POSTGRES_URL；只用虚拟数据，不把密码、完整连接串或原始数据库日志写入报告。
4. 执行原先环境阻塞的 8 个 P1 真实 PostgreSQL 独立测试，分别记录迁移、延迟平衡约束、双连接同键、并发退款/转账/预算、锁、只读可重复读快照和 timestamptz 结果。
5. 根据 P2-C5 矩阵实现并执行当前适用的 P2 SPG 案例，重点覆盖迁移、同事件并发、重复/并发确认、跨连接持久幂等、事务、恢复、一次一写及 P1 结果一致性。只在 tests/independent/agent_finance/** 或获准的 tests/independent/finance/** 增加独立测试。
6. 只运行 PostgreSQL 专项和必要相邻回归，不重复整个 C6 全量回归；P1 与 P2 结果分开统计。
7. 不执行真实 DeepSeek、桌面端、OpenClaw、微信或 Agent 真实回环断线案例。
8. 完成或安全停止时执行 docker compose down，不使用 -v，不执行 prune、卷删除、数据库重置或其他破坏性清理；记录容器已停止。
9. 更新 docs/testing/phase-2-agent-test-matrix.md，提交 docs/testing/phase-2-c7-postgresql-report.md 和 docs/coordination/agents/tester.md，然后停止在 review。

允许修改：tests/independent/agent_finance/**、必要的 tests/independent/finance/**、docs/testing/phase-2-agent-test-matrix.md、docs/testing/phase-2-c7-postgresql-report.md、docs/coordination/agents/tester.md。

禁止修改产品代码、迁移、执行方测试、依赖、compose.yaml、接口冻结、总览、控制文件、其他角色状态、Git 状态和 OpenClaw 配置。发现产品缺陷时只提交最小复现、预期、实际、严重级别和脱敏证据，不修改产品。

长任务记录可观察检查点和心跳。同一问题连续错过两个检查点且无新输出时，安全停止测试、关闭本任务启动的容器，并报告卡点、错误、已尝试方案和需要总控决定的问题。
```
