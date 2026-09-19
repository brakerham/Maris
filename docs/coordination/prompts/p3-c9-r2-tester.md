# P3-C9-R2：PostgreSQL 迁移缺陷独立复验

状态：`ready`。唯一负责人：用户启动的既有测试智能体。执行智能体已停止在 P3-B5-R1 `review`；本任务复验 `P3-C9-PG-001` 并完成 P3 最终门禁。

## 开始前

按顺序读取 `AGENTS.md`、`README.md`、`docs/project-coordination.md`、`docs/coordination/README.md`、`docs/coordination/control.md`、`docs/coordination/agents/tester.md`、`docs/phase-3-interface-freeze.md`、`docs/b5-activity-import-running.md`、`docs/testing/phase-3-c9-activity-import-report.md`、`docs/testing/phase-3-activity-import-test-matrix.md` 和 `docs/coordination/agents/executor.md`。

绑定输入：

```text
P3-B5-R1-SHA256:fb46b8fa4957c93bfd8f971b1fd987e45dd4779e8d6eac2907660fa2f1fef53c
P3-C9-REPORT-SHA256:d0b2189ec65d477a6fcefa9790898b5840d4f330f2ed713a6684346b8fada83b
```

先按 B5 交接算法独立重算 22 个文件和总摘要，再核对原 C9 报告原始字节摘要。任一不匹配就停止，不在漂移输入上形成结论。

总控已核对新旧 22 文件清单：只有以下两个执行方文件摘要发生变化，其他 20 个文件必须与 C9 原快照一致：

- `migrations/versions/c82d7a4f901e_add_activity_import.py`
- `tests/activity_import/test_migration.py`

## 返修预期

- upgrade 与 downgrade 使用同一名称 `fk_activity_template_revision_import_candidate`；
- 名称长度 46，不超过 PostgreSQL 63 字符；
- revision ID、表列、外键目标、`ondelete=RESTRICT`、迁移顺序和其他产品行为不变；
- 执行方新增可维护的 identifier 长度/双向一致回归。

若实际差异超出上述范围，停止并报告，不得替执行智能体修正。

## 文件边界

允许修改：

- 必要时补强 `tests/independent/activity_import/test_postgresql_contract.py` 或该独立目录的 PostgreSQL fixture；
- `docs/testing/phase-3-activity-import-test-matrix.md` 的 R2 证据和最终状态；
- 新报告 `docs/testing/phase-3-c9-r2-activity-import-report.md`；
- `docs/coordination/agents/tester.md`。

原 C9 报告、全部产品/迁移、执行方测试/文档、接口冻结、控制/总览、其他角色状态、依赖、Compose、OpenClaw 和 Git 只读。独立测试调整只能修复测试自身问题或补充冻结断言，不能削弱预期。

## 精简但完整的复验

1. 定向检查返修差异、显式标识符上限及 upgrade/downgrade 一致性。
2. 复跑独立本地 `tests/independent/activity_import`，排除 PostgreSQL 文件；预期原 81 项继续通过。
3. 复跑执行方本地 `tests/activity_import`，排除 PostgreSQL 文件；记录新增回归后的准确总数。
4. 复跑受迁移影响的旧测试：`tests/agent_finance/test_migration.py` 和 `tests/finance/test_migrations.py`。无需重复完整 92 项旧业务回归，除非快照超出两文件、定向测试失败或出现矛盾。
5. 在真实 PostgreSQL 上完整运行执行方 `tests/activity_import/test_postgresql.py` 九项。
6. 在真实 PostgreSQL 上完整运行独立 `tests/independent/activity_import/test_postgresql_contract.py` 的所有节点，覆盖并发、stale/归档、回滚、约束、空库/已有 P2 schema 迁移和响应丢失恢复。
7. R2 结束前再次重算 22 文件快照，确认产品未漂移。
8. 把原矩阵的 1 failed、24 blocked 更新为真实 R2 结论；原 64 passed 只有在对应本地复跑仍通过且快照满足门禁时才能保留。最终逐项汇总仍须等于 89。

## Docker 唯一负责人

R2 期间测试智能体是 Docker Desktop 启动尝试和 `finance-postgres` 启停的唯一负责人。任何操作前重新读取最新 `control.md`。

总控在派发前只读检查发现 Docker Engine 当前未运行。允许执行：

1. 检查 Docker API 一次；
2. 若未运行，最多启动一次本机已经安装的 Docker Desktop，不安装、不升级、不修改全局配置；启动窗口保持隐藏，等待 Engine 就绪；
3. Engine 可用后，只执行 `docker compose up -d finance-postgres`，等待 healthy；
4. 使用项目测试凭据、随机 schema 和虚拟数据；
5. 结束时普通 `docker compose down`，确认服务列表为空。

禁止 `down -v`、删除 volume、`prune`、数据库重置、其他 Compose 服务、Docker 全局配置和连续重启。一次启动后 Engine 仍无法就绪时，安全停止并报告环境阻塞；PostgreSQL 未实际通过时不得建议 P3 完成。报告不得记录密码或完整连接串。

## 交付与判定

交付：

- `docs/testing/phase-3-c9-r2-activity-import-report.md`
- 更新后的 89 项矩阵
- 必要的独立 PostgreSQL 测试补充
- 测试智能体状态日志

报告分列：新快照、两文件差异、独立本地、执行方本地、旧迁移回归、执行方 PostgreSQL、独立 PostgreSQL、矩阵 89 项、warning 和资源关闭状态。

只有以下条件全部满足时才建议总控接受 P3-B5-R1：

- 新快照执行前后匹配；
- `P3-C9-PG-001` 已关闭；
- 执行方与独立 PostgreSQL 全部实际通过，无 skip/setup error；
- 本地与旧迁移定向回归通过；
- 89 项全部有最终结论，所有适用案例通过；
- 没有新的 P0/P1 产品缺陷。

任务状态只能提交 `review`。最终 `complete`、Git 提交和下一阶段只属于头脑风暴总控。接单、快照门禁、本地层、Docker 就绪、两组 PostgreSQL、矩阵收口、最终快照和资源关闭时更新检查点；连续两个检查点无进展时安全停止并报告。
