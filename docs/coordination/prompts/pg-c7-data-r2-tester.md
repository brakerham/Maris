# PG-C7-DATA-R2 测试智能体定向复验 Prompt

> 状态：已完成并由总控于 2026-09-18 验收为 `complete`；不得重复派发。证据见 `docs/testing/phase-2-c7-r2-postgresql-report.md`。

你是本项目既有的测试智能体，唯一负责 `PG-C7-DATA-R2`：在 DATA-R1 固定快照上独立验证 `PG-C7-DATA-001` 是否关闭。不要创建新的长期角色。

开始前依次读取：`AGENTS.md`、`README.md`、`docs/project-coordination.md`、`docs/coordination/README.md`、`docs/coordination/control.md`、`docs/coordination/agents/tester.md`、`docs/testing/phase-2-c7-postgresql-report.md`、`docs/b3-data-running.md`、`docs/coordination/agents/executor.md`、`src/wife_system/finance/service.py` 和 `tests/finance/test_postgresql_claim.py`。

## 输入门禁

预期快照：

`PG-C7-DATA-R1-SHA256:5046cb87bbb3a3ab3556f9bc72b371636fb4869f3b3eb18778f852c84d27ea8a`

摘要只覆盖 `src/wife_system/finance/service.py` 和 `tests/finance/test_postgresql_claim.py`。按相对 POSIX 路径的 Python/Unicode 升序，依次写入 4 字节大端路径长度、UTF-8 路径、8 字节大端内容长度和原始文件字节，再计算整体 SHA-256。开始容器操作前独立重算；不匹配就停止，不得修改产品或测试迁就快照。

## 唯一负责人和范围

允许修改：`docs/testing/phase-2-c7-r2-postgresql-report.md`、`docs/testing/phase-2-agent-test-matrix.md` 对应证据、必要的独立 PostgreSQL 测试诊断以及 `docs/coordination/agents/tester.md`。独立测试诊断不得削弱断言。

DATA-R1 两文件、其他产品、执行方测试、迁移、依赖、Compose、冻结接口和执行方文档只读。禁止修改产品、执行方测试、控制/总览、其他角色日志、OpenClaw、微信、DeepSeek、桌面端以及任何 Git 状态。不得执行 `git add`、提交、分支、推送或 PR。

## 环境权限

只允许启动 `compose.yaml` 的 `finance-postgres`，等待健康后使用仓库测试凭据、随机 schema 和虚拟数据。结束时普通 `docker compose down`。禁止 `down -v`、删除 volume、`prune`、数据库重置、其他服务和 Docker 系统设置。Engine 未运行时记录阻塞并停止，不要求安装或连续重试。

## 必须执行

1. 独立重算并记录快照。
2. 分开运行原 PG-C7 P1 8 项与 P2 SPG 4 项，避免两个独立目录的 `conftest` 名称冲突；分别统计。
3. 复跑相邻 SQLite 独立幂等/错误契约，至少覆盖 `tests/independent/finance/test_idempotency_error_contract.py`；不得用 SQLite 替代 PostgreSQL。
4. 可单独复跑 `tests/finance/test_postgresql_claim.py` 作为执行方测试复跑，但必须与独立证据分开统计。
5. 核对首次新写入、同载荷重放、异载荷冲突、并发同键单一结果、失败回滚、并发退款/转账/预算、timestamptz、P2 并发确认和响应丢失恢复。
6. 不重复 C6 全量回归、真实 DeepSeek、桌面、OpenClaw 或微信。
7. `tests/agent_finance` 当前 5 项固定时间夹具已确认会在 24 小时后触发 `pending_action_expired`。本任务不重复运行或修改这 23 项；报告为测试基础设施维护项，不据此判定 DATA-R1 失败。
8. 更新 R2 报告、矩阵实际证据和测试智能体状态，停止于 `review`。

## 判定与停止

12 项 PostgreSQL 独立专项和相邻 SQLite 幂等回归全部通过时，建议关闭 `PG-C7-DATA-001`；最终 `complete` 和 Git 提交只能由总控决定。任一项失败时提交最小复现、预期、实际、严重级别和影响范围，不得修产品。环境/收集失败与产品断言分开统计。

第一次系统临时目录不可写时，使用仓库 `scratch/` 下全新的隔离 basetemp，不清理不属于本任务的目录。报告记录容器启动、健康、结果、普通 down 和最终服务列表为空，不记录数据库密码。

接单、快照门禁、容器健康、P1 完成、P2 完成、SQLite 回归和环境关闭时更新自己的执行快照。超过五分钟的步骤先写下一检查点，至少每十分钟更新心跳。连续错过两个检查点或同一错误无进展时安全停止、普通关闭自己启动的容器并报告。新 `control.md` 与本 Prompt 冲突时服从新控制。

只使用虚拟数据，不读取、输出或记录密钥、令牌、二维码、账号标识或真实个人财务数据。
