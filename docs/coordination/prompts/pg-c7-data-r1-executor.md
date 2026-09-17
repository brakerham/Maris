# PG-C7-DATA-R1 执行智能体返修 Prompt

你是本项目既有的执行智能体，唯一负责 `PG-C7-DATA-R1`：修复真实 PostgreSQL 首次财务写入被误判为并发冲突的问题。不要创建或转交给新的长期角色。

开始前按顺序读取：`AGENTS.md`、`README.md`、`docs/project-coordination.md`、`docs/coordination/README.md`、`docs/coordination/control.md`、`docs/coordination/agents/executor.md`、`docs/phase-1-interface-freeze.md`、`docs/phase-2-interface-freeze.md`、`docs/testing/phase-2-c7-postgresql-report.md`、`src/wife_system/finance/service.py`。

## 目标与已知原因

对 `FinanceService._claim` 做最小修复，使 PostgreSQL 可靠区分“本事务刚插入的新 command receipt”和“既有/并发冲突的 receipt”，同时保持重放、冲突检测、事务原子性和 SQLite 行为。

最小复现是：全新随机 PostgreSQL schema 升级后，首次 `create_account` 使用从未出现过的虚拟 `source_event_id`，却抛出 `FinanceError("concurrent_modification")`。C7 已定位到 PostgreSQL `INSERT ... ON CONFLICT DO NOTHING` 后的 `result.rowcount == 1` 判定在 SQLAlchemy 2.0.54 / psycopg 3.3.5 下不可靠。P1 PostgreSQL 为 3/8 通过，P2 SPG 为 2/4 通过。

## 文件与职责边界

允许修改：

- `src/wife_system/finance/service.py`
- 为最小修复确有必要的 `src/wife_system/finance/**`，交付时逐项解释
- 执行方测试 `tests/finance/**`
- 若直接影响 Agent 确认路径，可最小修改 `tests/agent_finance/**`
- `docs/b3-data-running.md`
- `docs/coordination/agents/executor.md`

只读：`tests/independent/**`、`docs/testing/**`、两个接口冻结、`compose.yaml` 和全部既有迁移。

禁止修改：独立测试/矩阵/报告、总控文件、其他角色日志、迁移、依赖、Compose、接口冻结、OpenClaw、微信、DeepSeek、桌面端和 Git。不得顺带重构、改变公开错误码或扩展功能。

## 数据库权限

只可启动 `compose.yaml` 的 `finance-postgres`，使用仓库测试凭据、随机 schema 和虚拟数据；结束时普通 `docker compose down`。禁止 `down -v`、删除 volume、`prune`、数据库重置、其他服务和 Docker 系统设置。若 Engine 未运行，记录阻塞并停止，不要求重新安装或连续重试。

## 必须完成

1. 先用执行方测试稳定复现全新 PostgreSQL schema 的首次 `create_account`。
2. 用数据库能明确返回插入归属的机制修复 PostgreSQL 分支；优先评估 `ON CONFLICT DO NOTHING ... RETURNING`，最终方案由实际并发语义决定。
3. 保持相同键同 payload 重放同一结果、相同键不同 payload 返回 `duplicate_request_conflict`、并发同键最多一个业务结果、receipt 与业务写入同事务、SQLite 不回退。
4. 在真实 PostgreSQL 上自测首次新写入、同请求重放、冲突 payload、并发同键；运行受影响的财务/Agent 执行方测试及 SQLite 相邻幂等回归。
5. 可只读运行 C7 失败节点诊断，但不得修改独立测试或把结果称为独立验收。
6. 更新运行说明，列出修改、实际结果和未验证项。
7. 生成 `PG-C7-DATA-R1-SHA256:<digest>` 固定快照，覆盖本次产品文件和执行方测试并列出文件。
8. 更新 `executor.md`，状态只能提交为 `review`，然后停止。

## 验收和停止

全新 PostgreSQL 首写、重放、冲突和并发必须符合冻结契约；SQLite 相邻回归必须通过；交付需含新快照、执行方测试证据和普通 compose down 证据。执行智能体无权宣布 PG-C7、P1 PostgreSQL 或 P2 SPG `complete`，仍须测试智能体在新快照上独立复验。

接单、复现、修复、PostgreSQL 自测、SQLite 回归和快照形成时更新自己的执行快照。超过五分钟的操作先写下一检查点，至少每十分钟更新心跳。连续错过两个检查点或同一错误无进展时，在安全位置停止，普通关闭自己启动的容器，并报告卡点、最后脱敏错误、已尝试方案、可能原因和待决定问题。新 `control.md` 与本 Prompt 冲突时立即服从新控制并停止旧动作。

只使用虚拟数据，不读取、输出或记录密码、密钥、令牌、二维码、账号标识或真实个人财务数据。
