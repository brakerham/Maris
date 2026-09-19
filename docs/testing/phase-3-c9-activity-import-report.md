# P3-C9 活动 Markdown 导入独立验收报告

- 任务：`P3-C9`
- 状态：`review`
- 执行时间：2026-09-19，Asia/Shanghai
- 固定输入：`P3-IF-001`、C8 89 项矩阵、B5 22 文件快照
- 总结论：**不建议总控接受 P3-B5**。本地冻结范围通过，但真实 PostgreSQL 首次迁移存在 P0 阻断缺陷 `P3-C9-PG-001`，导致必做 SPG 场景无法进入业务断言。

## 固定快照

按 B5 交接算法，在验收开始前和最终回归后分别计算 22 个文件的原始字节 SHA-256，再对有序 `path<TAB>sha256<LF>` UTF-8 字节流计算总摘要。两次均为：

```text
P3-B5-SHA256:9fb36c653d20ff14f85ad9667de454900cca0c6e3ead17c2619df11fb7f63d6e
```

22/22 个文件存在，逐文件摘要均匹配。验收期间产品、迁移和执行方测试无漂移。

## 环境

- Windows / Python 3.14.7
- SQLAlchemy 2.0.54、Alembic 1.20.0、psycopg 3.3.5、FastAPI 0.141.1、Pydantic 2.13.5
- Docker client/server 29.8.0、Compose 5.5.1
- PostgreSQL 17.6-alpine；仅回环端口 55432；随机 schema；只使用虚拟数据
- 未运行 DeepSeek、桌面端、OpenClaw、微信或真实个人数据

## 执行结果

| 证据层 | 结果 | 结论 |
|---|---:|---|
| 独立 PU/SQLite/HTTP/SQLite migration | 81 passed，0 failed，1 warning | 本地适用冻结范围通过 |
| 执行方 P3 PostgreSQL 九类 | 0 passed，9 setup errors | 同一 P3 migration 缺陷阻断 |
| 独立 PostgreSQL 最小复现 | 0 passed，1 setup error | 独立确认相同迁移缺陷；其余 SPG 场景停止扩大 |
| 执行方 P3 本地套件复跑 | 143 passed，0 failed，1 warning | 与执行方交接一致 |
| 受影响旧回归统一复跑 | 92 passed，4 skipped，1 warning | 四项仅因该进程未注入 PG URL 跳过 |
| 相邻旧 PostgreSQL 定向补证 | 4 passed，0 failed | P1 claim 首写/重放/并发/回滚仍通过 |
| 独立测试编译 | exit 0 | 独立目录可导入 |
| 最终 22 文件快照 | 匹配 | 产品无漂移 |

唯一 warning 为既有 Starlette TestClient 使用 AnyIO 弃用类型别名，不影响本次功能断言。

独立本地首轮出现 7 项测试基础设施问题：错误模型类名、旧 schema 的 UUID 绑定/列名、尾部空行位置期望、2000 行错误码期望和审计基线。它们均在获配独立目录内修正；修正后 81 项全绿，未修改产品，也未计为产品失败。

## 产品缺陷 P3-C9-PG-001

- 严重级别：**P0 / 高**
- 影响：真实 PostgreSQL 的空库和既有 P2 schema 都无法升级到 P3 head；预览同键并发、提交同键并发、同批异键、同名竞争、stale/归档、批次回滚、约束、迁移和响应丢失恢复全部被阻断。
- 最小复现：在真实 PostgreSQL 随机空 schema 执行 Alembic `upgrade head`。P1/P2 migrations 成功，进入 `c82d7a4f901e` 后失败。
- 冻结预期：P3-IF-001 第 9 节要求真实 PostgreSQL 完成空库/已有数据升级，并运行九类目标库场景。
- 实际：SQLAlchemy 抛出 `IdentifierError`。显式外键名 `fk_activity_template_revision_source_import_candidate_id_activity_import_candidate` 长于 PostgreSQL 的 63 字符标识符上限。
- 数据安全：失败发生在随机 schema；PostgreSQL transactional DDL 回滚，测试 fixture 最终删除随机 schema。没有真实数据或凭据进入报告。
- 建议返修：仅缩短 `c82d7a4f901e` 中该外键约束名，并同步 downgrade 的精确名称；形成新的 22 文件固定快照。返修后必须完整复跑执行方 9 类、独立 SPG、SQLite migration、本地独立与受影响回归。

本任务没有修改产品或迁移，因此该缺陷仍存在。

## 89 项逐案追踪

| 案例 ID | C9 状态 | 证据/阻断原因 |
|---|---|---|
| P3-SYN-01 | passed | 独立 `test_parser_contract.py` |
| P3-SYN-02 | passed | 独立 `test_parser_contract.py` |
| P3-SYN-03 | passed | 独立 `test_parser_contract.py` |
| P3-SYN-04 | passed | 独立 `test_parser_contract.py` |
| P3-SYN-05 | passed | 独立 `test_parser_contract.py` |
| P3-SYN-06 | passed | 独立 `test_parser_contract.py` |
| P3-SYN-07 | passed | 独立 `test_parser_contract.py` |
| P3-SYN-08 | passed | 独立 `test_parser_contract.py` |
| P3-SYN-09 | passed | 独立 `test_parser_contract.py` |
| P3-SYN-10 | passed | 独立 `test_parser_contract.py` |
| P3-SYN-11 | passed | 独立 `test_parser_contract.py` |
| P3-SYN-12 | passed | 独立 `test_parser_contract.py` |
| P3-AMT-01 | passed | 独立 parser/service 金额断言 |
| P3-AMT-02 | passed | 独立 parser/service 金额断言 |
| P3-AMT-03 | passed | 独立 parser/service 金额断言 |
| P3-AMT-04 | passed | 独立 parser/service 金额断言 |
| P3-AMT-05 | passed | 独立 parser/service 金额断言 |
| P3-AMT-06 | passed | 独立 parser/service 金额断言 |
| P3-AMT-07 | passed | 独立 parser/service 金额断言 |
| P3-AMT-08 | passed | 独立 parser/service 金额断言 |
| P3-AMT-09 | passed | 独立 parser/service 金额断言 |
| P3-AMT-10 | passed | 独立 parser/service 金额断言 |
| P3-PRV-01 | passed | 独立 `test_service_contract.py` 数据库前后快照 |
| P3-PRV-02 | passed | 独立 `test_service_contract.py` 数据库前后快照 |
| P3-PRV-03 | passed | 独立 `test_service_contract.py` 数据库前后快照 |
| P3-PRV-04 | passed | 独立 `test_service_contract.py` 数据库前后快照 |
| P3-PRV-05 | passed | 独立 `test_service_contract.py` 数据库前后快照 |
| P3-PRV-06 | passed | 独立 `test_service_contract.py` 数据库前后快照 |
| P3-PRV-07 | blocked | SQLite预览纯度已通过；P3 PostgreSQL schema不可建立 |
| P3-PRV-08 | passed | 独立 `test_service_contract.py` 数据库前后快照 |
| P3-CAN-01 | passed | 独立候选动作/来源/稳定性断言 |
| P3-CAN-02 | passed | 独立候选动作/来源/稳定性断言 |
| P3-CAN-03 | passed | 独立候选动作/来源/稳定性断言 |
| P3-CAN-04 | passed | 独立候选动作/来源/稳定性断言 |
| P3-CAN-05 | passed | 独立候选动作/来源/稳定性断言 |
| P3-CAN-06 | passed | 独立候选动作/来源/稳定性断言 |
| P3-CAN-07 | passed | 独立候选动作/来源/稳定性断言 |
| P3-CAN-08 | passed | 独立候选动作/来源/稳定性断言 |
| P3-CNF-01 | passed | 独立 SQLite 精确名、历史名、归档/stale 断言 |
| P3-CNF-02 | passed | 独立 SQLite 精确名、历史名、归档/stale 断言 |
| P3-CNF-03 | passed | 独立 SQLite 精确名、历史名、归档/stale 断言 |
| P3-CNF-04 | passed | 独立 SQLite 精确名、历史名、归档/stale 断言 |
| P3-CNF-05 | blocked | SQLite冲突/版本路径已通过；SPG并发或锁证据被迁移阻断 |
| P3-CNF-06 | passed | 独立 SQLite 精确名、历史名、归档/stale 断言 |
| P3-CNF-07 | blocked | SQLite冲突/版本路径已通过；SPG并发或锁证据被迁移阻断 |
| P3-CNF-08 | blocked | SQLite冲突/版本路径已通过；SPG并发或锁证据被迁移阻断 |
| P3-IDM-01 | passed | 独立 service/HTTP 同键、冲突与恢复断言 |
| P3-IDM-02 | passed | 独立 service/HTTP 同键、冲突与恢复断言 |
| P3-IDM-03 | blocked | SQLite/HTTP重放已通过；SPG并发/跨进程证据被迁移阻断 |
| P3-IDM-04 | blocked | SQLite/HTTP重放已通过；SPG并发/跨进程证据被迁移阻断 |
| P3-IDM-05 | blocked | SQLite/HTTP重放已通过；SPG并发/跨进程证据被迁移阻断 |
| P3-IDM-06 | blocked | SQLite/HTTP重放已通过；SPG并发/跨进程证据被迁移阻断 |
| P3-IDM-07 | blocked | SQLite/HTTP重放已通过；SPG并发/跨进程证据被迁移阻断 |
| P3-IDM-08 | blocked | SQLite/HTTP重放已通过；SPG并发/跨进程证据被迁移阻断 |
| P3-IDM-09 | blocked | SQLite/HTTP重放已通过；SPG并发/跨进程证据被迁移阻断 |
| P3-ATM-01 | blocked | SQLite原子回滚/重试已通过；SPG事务证据被迁移阻断 |
| P3-ATM-02 | blocked | SQLite原子回滚/重试已通过；SPG事务证据被迁移阻断 |
| P3-ATM-03 | blocked | SQLite原子回滚/重试已通过；SPG事务证据被迁移阻断 |
| P3-ATM-04 | blocked | SQLite原子回滚/重试已通过；SPG事务证据被迁移阻断 |
| P3-ATM-05 | blocked | SQLite原子回滚/重试已通过；SPG事务证据被迁移阻断 |
| P3-ATM-06 | blocked | SQLite原子回滚/重试已通过；SPG事务证据被迁移阻断 |
| P3-ATM-07 | blocked | SQLite原子回滚/重试已通过；SPG事务证据被迁移阻断 |
| P3-ATM-08 | blocked | SQLite原子回滚/重试已通过；SPG事务证据被迁移阻断 |
| P3-SEC-01 | passed | 独立 parser/HTTP canary 与资源边界断言 |
| P3-SEC-02 | passed | 独立 parser/HTTP canary 与资源边界断言 |
| P3-SEC-03 | passed | 独立 parser/HTTP canary 与资源边界断言 |
| P3-SEC-04 | passed | 独立 parser/HTTP canary 与资源边界断言 |
| P3-SEC-05 | passed | 独立 parser/HTTP canary 与资源边界断言 |
| P3-SEC-06 | passed | 独立 parser/HTTP canary 与资源边界断言 |
| P3-SEC-07 | passed | 独立 parser/HTTP canary 与资源边界断言 |
| P3-SEC-08 | passed | 独立 parser/HTTP canary 与资源边界断言 |
| P3-SEC-09 | passed | 独立 parser/HTTP canary 与资源边界断言 |
| P3-SEC-10 | blocked | 本地日志/数据库隐私已通过；SPG禁止列复核被迁移阻断 |
| P3-API-01 | passed | 独立 `test_http_contract.py` |
| P3-API-02 | passed | 独立 `test_http_contract.py` |
| P3-API-03 | passed | 独立 `test_http_contract.py` |
| P3-API-04 | passed | 独立 `test_http_contract.py` |
| P3-API-05 | passed | 独立 `test_http_contract.py` |
| P3-API-06 | passed | 独立 `test_http_contract.py` |
| P3-API-07 | passed | 独立 `test_http_contract.py` |
| P3-API-08 | passed | 独立 `test_http_contract.py` |
| P3-DB-01 | passed | 独立 `test_migration_contract.py` 或 SQLite 事务证据 |
| P3-DB-02 | passed | 独立 `test_migration_contract.py` 或 SQLite 事务证据 |
| P3-DB-03 | failed | `P3-C9-PG-001`；执行方9项与独立最小复现均在P3 migration失败 |
| P3-DB-04 | passed | 独立 `test_migration_contract.py` 或 SQLite 事务证据 |
| P3-DB-05 | blocked | SQLite或本地部分已通过；目标库迁移失败阻断SPG结论 |
| P3-DB-06 | blocked | SQLite或本地部分已通过；目标库迁移失败阻断SPG结论 |
| P3-DB-07 | blocked | SQLite或本地部分已通过；目标库迁移失败阻断SPG结论 |
| P3-DB-08 | blocked | SQLite或本地部分已通过；目标库迁移失败阻断SPG结论 |

汇总：64 `passed`、1 `failed`、24 `blocked`、0 `not_applicable`。混合 `SS+SPG` 或 `HTTP+SS+SPG` 案例即使本地部分已通过，只要冻结要求的 SPG 部分未执行，整项仍标为 `blocked`，没有以 SQLite 结果替代 PostgreSQL 结论。

## 独立交付物

- `tests/independent/activity_import/conftest.py`
- `tests/independent/activity_import/test_parser_contract.py`
- `tests/independent/activity_import/test_service_contract.py`
- `tests/independent/activity_import/test_http_contract.py`
- `tests/independent/activity_import/test_migration_contract.py`
- `tests/independent/activity_import/test_postgresql_contract.py`
- 更新后的 `docs/testing/phase-3-activity-import-test-matrix.md`

## 资源关闭与边界

只启动了 Compose 中的 `finance-postgres`。测试结束执行普通 `docker compose down`，没有使用 `-v`、prune、数据库重置或全局配置修改；容器与项目网络已移除，最终 `docker compose ps` 为空。

没有运行真实 DeepSeek、桌面端、OpenClaw、微信或真实个人数据，没有执行 Git 操作。P3-C9 停在 `review`；必须由执行智能体按总控新任务返修并提供新快照，再由测试智能体复验。最终 `complete` 与 Git 提交仍只属于头脑风暴总控。
