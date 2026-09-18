# PG-C7-DATA-R2：真实 PostgreSQL 定向复验报告

- 任务：`PG-C7-DATA-R2`
- 结论状态：`review`
- 控制依据：`docs/coordination/control.md` 指令版本 `2026-09-17T23:10:00+08:00`
- 数据边界：只使用 compose 测试数据库、随机 schema、虚拟身份和虚拟财务数据；未记录数据库密码

## 结论

DATA-R1 固定快照通过本轮独立复验。原 PG-C7 的 12 项 PostgreSQL 独立专项全部通过，相邻 SQLite 幂等/错误契约 9 项全部通过。执行方新增的 PostgreSQL claim 测试另行统计为 4 项全部通过。

本轮没有复现 `PG-C7-DATA-001`。首次新写入、同载荷重放、异载荷冲突、并发同键单一结果、失败回滚、并发退款/转账/预算、timestamptz、P2 并发确认、一次一写和提交后响应丢失恢复均符合预期。测试智能体建议关闭该缺陷；任务仍停在 `review`，最终 `complete` 与 Git 提交由头脑风暴总控决定。

## 固定快照门禁

预期与独立重算摘要均为：

`5046cb87bbb3a3ab3556f9bc72b371636fb4869f3b3eb18778f852c84d27ea8a`

摘要只覆盖 `src/wife_system/finance/service.py` 和 `tests/finance/test_postgresql_claim.py`。结果完全匹配，测试开始后未修改这两个文件。

## 环境与生命周期

| 项目 | 实际值 |
| --- | --- |
| Docker client/server | 29.8.0 / 29.8.0 |
| Docker Compose | v5.5.1 |
| PostgreSQL | `postgres:17.6-alpine` |
| 服务 | 仅 `finance-postgres` |
| 端口 | 仅绑定本机回环 55432 |
| 数据 | 随机 schema、全虚拟数据；容器无本地 Docker volume |

启动前再次读取控制文件，确认 DATA-R2 仍是测试智能体唯一活动任务。compose 配置只包含 `finance-postgres`，容器进入 `healthy` 后开始测试。连接凭据只注入单次测试进程，没有写入命令输出、报告或状态文件。

测试结束后执行普通 `docker compose -f compose.yaml down`，没有使用 `-v`、prune、数据库重置或系统清理。容器和项目网络均已移除，最终 compose 服务列表为空。

## 独立验收结果

### P1 原 8 项

目标：`tests/independent/finance/test_postgresql_contract.py`

结果：8 passed、0 failed。

| 覆盖 | 结果 |
| --- | --- |
| 空库迁移、数据库类型/约束、重复升级 | 通过 |
| 延迟平衡触发器拒绝不平账提交 | 通过 |
| 两连接并发同来源键得到单一结果 | 通过 |
| 并发退款锁定原账并限制累计退款 | 通过 |
| 并发转账均写入且无丢失更新 | 通过 |
| 并发预算发布只有一个版本胜者 | 通过 |
| 只读可重复读月度快照事务 | 通过 |
| `timestamptz` aware UTC 往返 | 通过 |

### P2 SPG 4 项

目标：`tests/independent/agent_finance/test_postgresql_agent_contract.py`

结果：4 passed、0 failed。

| 覆盖 | 结果 |
| --- | --- |
| P2 head、Agent 表与唯一约束 | 通过 |
| 两个应用实例并发同事件只形成一个 run | 通过 |
| 两个并发确认只提交一笔，并与 P1 余额/收据一致 | 通过 |
| 财务提交成功但响应丢失后，由新应用实例以同键恢复原结果 | 通过 |

独立 PostgreSQL 专项合计：12 passed、0 failed。

### 相邻 SQLite 幂等/错误契约

目标：`tests/independent/finance/test_idempotency_error_contract.py`

首次运行：1 passed、8 setup errors。错误来自系统 pytest 临时目录拒绝访问，8 项没有进入产品断言，属于环境/测试基础设施事件。

按任务书使用仓库 `scratch/` 下全新的隔离 basetemp 后重跑：9 passed、0 failed。新目录保留，未清理任何不属于本任务的目录。

覆盖顺序重放、冲突载荷、HMAC 隐私、不同键、SQLite 双连接并发、数据库/业务双层校验和日志脱敏，确认 DATA-R1 没有破坏相邻 SQLite 契约。

## 执行方补充证据

目标：`tests/finance/test_postgresql_claim.py`

结果：4 passed、0 failed，与独立 12 项分开统计。

覆盖首次新 claim、相同载荷重放与异载荷冲突、并发同键单一业务结果，以及业务失败回滚后同键可恢复。

## 缺陷判定

- 缺陷：`PG-C7-DATA-001`
- 原严重级别：P0 / 高
- 原最小复现：全新 PostgreSQL schema 首次 `FinanceService.create_account` 返回 `concurrent_modification`
- DATA-R2 实际：首次写入成功且 `replayed=false`；顺序和并发重放返回原结果；冲突载荷得到稳定冲突；失败事务不留下半写入
- 回归影响：P1 8 项、P2 4 项、SQLite 9 项均通过
- 测试建议：关闭 `PG-C7-DATA-001`
- 最终决定：由头脑风暴总控核对本报告、矩阵和固定摘要后作出

## 测试基础设施维护项

- 系统 pytest 临时目录不可访问；已按 Prompt 使用全新仓库 basetemp，重跑全绿，不构成产品缺陷。
- pytest 写入仓库 `.pytest_cache` 时仍出现 WinError 183 警告；不影响收集、执行或断言。
- `tests/agent_finance` 已知的 5 项固定时间夹具会在 24 小时后触发 `pending_action_expired`。本任务没有运行或修改该目录的 23 项，也没有据此判断 DATA-R1 失败。
- P1 与 P2 独立目录继续分开运行，避免裸 `conftest` 名称冲突。

## 范围与安全

- 没有重复 C6 全量回归。
- 没有执行真实 DeepSeek、桌面端、OpenClaw 或微信。
- 没有修改产品代码、DATA-R1 两文件、执行方测试、迁移、依赖、`compose.yaml`、接口冻结、控制文件、总览、其他角色状态或 Git。
- 没有读取或输出密钥、令牌、二维码、账号标识或真实个人财务数据。
- 本轮无需修改独立测试断言。

PG-C7-DATA-R2 在此提交 `review` 并停止。后续由总控决定缺陷关闭、项目验收和本地提交。