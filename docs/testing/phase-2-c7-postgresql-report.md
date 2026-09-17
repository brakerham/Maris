# PG-C7：真实 PostgreSQL 专项验收报告

- 任务：`PG-C7`
- 结论状态：`review`
- 新控制依据：用户明确本指令晚于 `control.md` 的 `2026-09-17T00:35:00+08:00` 版本，并授权本测试智能体独占执行 PostgreSQL 专项
- 数据边界：仅使用 compose 测试数据库、随机 schema、虚拟身份和虚拟财务数据；报告不记录连接密码

## 结论

真实 PostgreSQL 专项确认一个阻断级产品缺陷 `PG-C7-DATA-001`：全新 PostgreSQL schema 完成迁移后，首次通过 `FinanceService` 执行写命令即返回 `concurrent_modification`。因此 P1 的真实 PostgreSQL 范围不能通过，P2 的确认、重复/并发确认、提交恢复和 P1 结果一致性也不能通过。

数据库迁移、PostgreSQL 延迟平衡约束、只读可重复读快照、P2 head/Agent 表约束，以及跨两个 AgentApplication 实例的同事件单 run 幂等均通过。SQLite 与 C6 的本地结论不被本次失败推翻，但不能替代 PostgreSQL 写路径。

## 环境与生命周期

| 项目 | 实际值 |
| --- | --- |
| Docker client/server | 29.8.0 / 29.8.0 |
| Docker Compose | v5.5.1 |
| PostgreSQL | `postgres:17.6-alpine` |
| Python | 3.14.7 |
| SQLAlchemy | 2.0.54 |
| psycopg | 3.3.5 |
| 服务 | 仅 `finance-postgres` |
| 端口 | 仅绑定本机回环 55432 |
| 数据 | compose tmpfs，无持久 Docker volume |

首次检查时 Docker Engine 未运行，本任务按指令安全停止且没有重试；用户打开 Docker Desktop 后只复查一次，随后仅启动 `finance-postgres`。容器达到 `healthy` 后开始测试。每项测试创建随机 schema，结束时删除自身 schema。

测试完成后执行普通 `docker compose -f compose.yaml down`，没有使用 `-v`、prune、系统清理或数据库重置。容器和项目网络均已移除，最终 `docker compose ps` 无条目。

## 执行结果

### P1 原 8 项

结果：3 通过、5 失败。

| 测试 | 结果 | 说明 |
| --- | --- | --- |
| 空库迁移、类型、约束和重复升级 | 通过 | P1 head、表集合、`timestamptz` 与整数金额类型符合预期 |
| 延迟平衡触发器拒绝不平账提交 | 通过 | PostgreSQL 提交时约束生效 |
| 两连接同来源键 | 失败 | 前置账户创建即触发 `PG-C7-DATA-001` |
| 并发退款锁与累计上限 | 失败 | 前置账户创建即触发共同缺陷，未进入退款并发主体 |
| 并发转账无丢失更新 | 失败 | 前置账户创建即触发共同缺陷，未进入转账并发主体 |
| 并发预算发布单一胜者 | 失败 | 前置账户创建即触发共同缺陷，未进入预算并发主体 |
| 只读可重复读快照 | 通过 | 捕获到 `REPEATABLE READ READ ONLY` |
| `timestamptz` aware UTC 往返 | 失败 | 前置账户创建即触发共同缺陷，未进入时间往返主体 |

### P2 SPG 新增 4 项

结果：2 通过、2 失败。

| 测试 | 结果 | 映射 |
| --- | --- | --- |
| P2 head、20 张含 Alembic 表、Agent 唯一约束 | 通过 | P2 migration / persistence |
| 两个应用实例并发同事件 | 通过 | `IDM-01`；单 run、模型仅调用一次 |
| PostgreSQL 并发确认、单交易和 P1 余额一致性 | 失败 | `IDM-05`、`IDM-06`、`IDM-10`、`HTTP-04`、`P1-01`～`P1-05` |
| 财务提交后响应丢失并重启恢复 | 失败 | `IDM-08`、`IDM-10`、`DB-02`、`DB-03`、`LOOP-11` |

分别执行的 12 项 PostgreSQL 专项合计为 5 通过、7 失败。诊断后的两项 P2 失败再次稳定复现。一次尝试把两个目录放进同一 pytest 命令时，由两个独立目录的裸 `from conftest` 名称冲突导致收集中止，未执行产品代码，不计入上述结果；本任务没有为统计便利扩大测试结构改动。

## 缺陷 PG-C7-DATA-001

- 严重级别：P0 / 高，阻断 PostgreSQL 财务写入和 P2 写确认。
- 最小前置：随机空 schema，升级到 P1 head 或 P2 head，构造 `FinanceService` 与虚拟幂等密钥。
- 最小操作：首次调用 `FinanceService.create_account`，使用从未出现过的虚拟 `source_event_id`。
- 预期：创建账户并完成一条 command receipt；相同键后续才作为重放处理。
- 实际：抛出 `FinanceError("concurrent_modification")`。P2 confirm 返回 `paused`、`pause_reason=committing`、同一错误码和安全消息，没有 `result_id` 或 committed 结果。
- 可重复性：P1 五个写相关测试及 P2 两个确认/恢复测试均在独立随机 schema 中复现。
- 影响范围：账户/分类创建及其他全部 `FinanceService` 写命令；P1 同键、退款、转账、预算和时间往返测试；P2 确认、重复/并发确认、响应丢失恢复、重启后的 committed 重放及 P1 结果一致性。
- 未受影响证据：迁移、数据库约束、只读快照、Agent run 来源唯一性和同事件单 run。
- 代码定位：`FinanceService._claim` 使用 `result.rowcount == 1` 判断 PostgreSQL `INSERT ... ON CONFLICT DO NOTHING` 是否由当前事务插入；本环境中该判断把新插入且尚无 `result_json` 的收据走入并发中状态分支。
- 修复边界：本任务未修改产品。应由执行智能体在新返修任务中修复，并提供新固定快照；修复后需复跑本报告全部 12 项及相邻 SQLite 幂等回归。

## 矩阵结论

P2 矩阵已更新：

- `IDM-01` 增加 SPG 同事件通过证据。
- `IDM-05`、`IDM-06`、`IDM-08`、`IDM-10`、`LOOP-11`、`DB-02`、`DB-03`、`HTTP-04`、`P1-01`～`P1-05` 记录 PostgreSQL 失败或阻断。
- `IDM-09` 仅取得候选持久化和跨实例读取的部分证据，最终确认恢复仍被共同缺陷阻断。
- 其他没有实际执行的 SPG 子场景继续保持未执行，不用本次局部证据外推。

## 范围与安全

- 没有运行整个 C6 全量回归。
- 没有执行真实 DeepSeek、桌面端、OpenClaw 或微信案例。
- 没有修改产品代码、迁移、执行方测试、依赖、compose.yaml、接口冻结、控制文件、总览、其他角色状态或 Git。
- 没有输出或保存数据库连接密码。
- 仅新增 P2 PostgreSQL 独立测试，并改善其失败诊断。

PG-C7 在此提交 `review` 并停止。总控应先派发 `PG-C7-DATA-001` 产品返修；当前证据不支持把 P1 PostgreSQL 或 P2 SPG 写路径标记为通过。