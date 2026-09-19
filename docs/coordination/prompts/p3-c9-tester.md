# P3-C9：活动 Markdown 导入独立验收

状态：`ready`。唯一负责人：用户启动的既有测试智能体。执行智能体已停止在 `review`；不得要求执行智能体并行修改产品。

## 开始前

按顺序读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. `docs/coordination/control.md`
6. `docs/coordination/agents/tester.md`
7. `docs/phase-3-interface-freeze.md`
8. `docs/testing/phase-3-activity-import-test-matrix.md`
9. `docs/b5-activity-import-running.md`
10. `docs/coordination/agents/executor.md`

绑定实现快照：

```text
P3-B5-SHA256:9fb36c653d20ff14f85ad9667de454900cca0c6e3ead17c2619df11fb7f63d6e
```

先按 B5 交接中的算法独立重算 22 个文件摘要。缺文件、额外清单项、单文件摘要或总摘要不匹配时立即停止，不得在漂移实现上形成结论。独立测试和报告不属于这 22 个执行方文件。

## 目标

在固定 B5 快照上执行 C8 的 89 项验收矩阵，独立验证：

- 受限 Markdown、Unicode、金额范围和候选动作；
- 预览允许的持久元数据与业务零写入；
- owner 隔离、严格 HTTP/Pydantic、错误和日志隐私；
- 同键/异载荷、响应丢失、跨请求恢复和全部 skip；
- stale、归档、同名竞争、批次原子回滚和数据库约束；
- SQLite 与真实 PostgreSQL 的冻结分工；
- P1/P2 兼容回归。

设计案例可以由参数化测试共同提供证据，但报告必须逐一映射 89 个 ID，并分别标记 `passed/failed/blocked/not_applicable`；不得用套件总通过数替代需求追踪。

## 文件边界

允许修改：

- `tests/independent/activity_import/**`
- `docs/testing/phase-3-activity-import-test-matrix.md` 中 P3-C9 的实际证据和状态
- `docs/testing/phase-3-c9-activity-import-report.md`
- `docs/coordination/agents/tester.md`

产品、迁移、`tests/activity_import/**`、执行角色文件、B5 运行说明、接口冻结、控制/总览、其他角色状态、依赖、Compose 配置、OpenClaw 和 Git 全部只读。

不得为了让测试通过而修改产品或执行方断言。发现缺陷时记录最小虚拟复现、冻结预期、实际结果、严重级别、影响案例和建议返修范围，然后停止扩大相关高风险场景。

## 独立测试要求

1. 在 `tests/independent/activity_import/**` 编写独立输入与断言，不复制执行方测试实现。
2. 先执行 PU/SQLite/HTTP 独立测试，覆盖 C8 A–I 的本地适用案例。
3. 检查预览后活动模板、修订、发生、分配、账目、账户、预算、收入和业务审计不变；只允许冻结的批次、候选和预览回执。
4. 检查完整 Markdown、自由文本、幂等原键、本地路径、完整摘要、SQL/驱动正文不出现在数据库禁止列、日志或错误响应中。
5. 检查同批和新批 candidate UUID 的冻结差异：同批/幂等重放稳定，新键新批次不要求 UUID 相同。
6. 独立验证迁移：空库升级、已有虚拟 P1/P2 数据升级、规范名重复安全失败、金额回填和现有引用不变。
7. 在最终回归中只复跑一次执行方 P3 套件与受影响旧回归，和独立结果分开统计。
8. 不运行真实 DeepSeek、桌面、OpenClaw、微信或真实个人数据。

## PostgreSQL 唯一负责人

C9 期间，测试智能体是 `finance-postgres` 启停和 P3 PostgreSQL 验收的唯一负责人。开始任何 Docker 操作前重新读取最新 `control.md`。

- 当前总控只读检查显示 Docker Engine `29.8.0` 可用，Compose 服务列表为空；开始时仍须自行复核。
- 只允许 `docker compose up -d finance-postgres`，等待健康后使用项目测试凭据、随机 schema 和虚拟数据。
- 必须运行执行方 `tests/activity_import/test_postgresql.py` 的九类测试，并实现/执行足以独立覆盖 C8 SPG 风险的测试；两类证据分开统计。
- 至少验证：预览同键并发、提交同键并发、同批异键并发、异批同名 create 竞争、stale/归档、整批故障回滚、约束、空库/已有数据迁移、响应丢失恢复。
- 结束时普通 `docker compose down`，确认服务列表为空。禁止 `down -v`、删除 volume、`prune`、重置其他数据库、修改 Docker Desktop 全局配置或启动其他服务。
- 若 Engine 变为不可用，只做一次复核，记录环境阻塞并停止数据库部分；不要安装、修复或连续重启 Docker。PostgreSQL 未实际通过时，P3 不能建议 `complete`。

报告不得记录数据库密码或完整连接串。

## 执行顺序

1. 接单、控制文件和 22 文件快照门禁。
2. 独立 PU/SQLite 解析、业务和隐私测试。
3. 独立 HTTP 契约与资源限制测试。
4. PostgreSQL 容器健康、执行方九类测试和独立 SPG 验收。
5. 执行方 P3 套件及受影响旧回归各统一复跑一次。
6. 重算 B5 快照，确认产品在验收期间未漂移。
7. 普通关闭自己启动的容器，形成报告、更新 89 项追踪和自己的角色日志。

## 交付与结论

交付：

- `docs/testing/phase-3-c9-activity-import-report.md`
- 更新后的 `docs/testing/phase-3-activity-import-test-matrix.md`
- `tests/independent/activity_import/**`
- `docs/coordination/agents/tester.md`

报告必须区分：独立本地、独立 PostgreSQL、执行方 P3 复跑、旧回归、失败、阻塞、未适用、warning、资源关闭状态和最终快照。

只有 89 项均有冻结后结论、所有适用 P0/P1 案例通过、PostgreSQL 必做项实际通过、快照无漂移且无 P0/P1 产品缺陷时，才可以建议总控接受 P3-B5。状态仍只能提交 `review`，最终 `complete` 和 Git 提交只属于头脑风暴总控。

接单、快照通过、每个环境层完成、Docker 健康、PostgreSQL 完成、最终回归、资源关闭和交付时更新执行快照。预计超过五分钟的步骤先记录下一检查点；连续两个检查点无进展时安全停止、关闭自己启动的容器并报告卡点。
