# P3-B5：活动 Markdown 导入执行任务

状态：`ready`。唯一负责人：用户启动的既有执行智能体。实现、自测和交接由执行方负责；独立结论属于后续 P3-C9。

## 开始前

按顺序读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. `docs/coordination/control.md`
6. `docs/coordination/agents/executor.md`
7. `docs/phase-3-activity-import-brief.md`
8. `docs/phase-3-interface-freeze.md`
9. `docs/phase-3-d7-activity-import-advice.md`
10. `docs/testing/phase-3-activity-import-test-matrix.md`
11. `docs/phase-1-interface-freeze.md`

绑定输入：

```text
P3-IF-001-SHA256:8912359d1e4748fe1b0e537c33d6e59481dba32ac573a7bc82560c4f25e8b9cd
P3-D7-SHA256:9625009fa8b5e9e5ddd4f1fff805a437e97533a3c6e9d452cf3b84def6ca59e0
P3-C8-SHA256:5a4eec3dcba2d1d446f66cb02fa701de6b6bae5744f4083e5cbebfcc3e176da7
```

开始修改前独立重算三份摘要。任一不匹配或控制文件改变负责人/范围时停止并报告，不在漂移契约上开发。

## 目标

实现 `P3-IF-001` 的完整最小纵向切片：

```text
Markdown JSON 文本
  → 离线受限解析
  → 持久批次与候选预览
  → GET 恢复
  → 用户逐项 accept/skip
  → 单事务创建/修订活动模板
  → 幂等结果与来源追溯
```

必须使用虚拟活动和虚拟数据库数据，不使用真实个人资料。

## 必须实现

1. `src/wife_system/activity_import/**`：纯解析器、严格 Pydantic DTO、稳定错误、仓储和预览/读取/提交服务。
2. `activity_import_batch`、`activity_import_candidate`、模板规范名、金额上下界和修订来源的 ORM 与 Alembic 迁移。
3. `P3-IF-001` 冻结的 H1/H2、三种金额语法、Unicode、warning/error、五种候选动作和资源限制。
4. 原文不落库；内容/块 HMAC、解析器版本、来源行号和稳定批次内候选 ID。
5. 三个冻结 API：preview、GET batch、commit；严格 Content-Type、schema、owner 隔离、状态码和安全错误 envelope。
6. preview/commit 持久幂等：同键同载荷重放、同键异载荷冲突、GET 恢复和已提交批次保护。
7. 一个外层事务提交整批；从 `FinanceService` 提取可复用的 session 级模板写入原语，保持现有公开命令行为兼容。
8. 精确、范围、无金额三种形状；旧 `reference_minor` 数据与直接创建/修订命令兼容。
9. 日志白名单和敏感内容禁止规则。
10. SQLite 常规证据及 P3-IF-001 第 9、11 节冻结的 PostgreSQL 并发、约束、迁移、回滚和恢复证据。

## 文件边界

允许修改：

- `src/wife_system/activity_import/**`
- `src/wife_system/api/activity_import_routes.py`
- 必要的 `src/wife_system/api/app.py`
- 必要的 `src/wife_system/finance/models.py`、`schemas.py`、`service.py`
- 一个从 `7f3e2d1c9a4b` 继续的 P3 migration
- `tests/activity_import/**`
- 为 P1/P2 兼容性必须补充的执行方测试
- `docs/b5-activity-import-running.md`
- `docs/coordination/agents/executor.md`

禁止修改：

- `tests/independent/**`
- `docs/testing/phase-3-activity-import-test-matrix.md` 及任何独立报告
- `docs/phase-3-interface-freeze.md`、控制文件、总览和其他角色状态
- OpenClaw/微信集成、真实数据、依赖清单和 Git 状态

首版不增加运行依赖。若冻结契约无法在上述边界实现，停止并把冲突、最小复现和建议交回总控，不得自行改变接口。

## 自测与环境

- 先完成纯解析和 DTO，再迁移/模型，再预览持久化，再共享写入原语和原子提交，最后接 API。
- 执行方测试放在 `tests/activity_import/**`；不得在独立测试目录写用例。
- 运行受影响的 finance、agent finance 和 API 回归，分别统计 P3 新测试与既有回归。
- PostgreSQL 专项只能使用项目测试 Compose、随机 schema 和虚拟数据。开始前重新读取 `control.md`；可普通启动/停止项目服务，不安装软件、不删除 volume、不修改 Docker Desktop 全局配置。
- 不运行 DeepSeek、外网、OpenClaw、微信、桌面端或真实文件导入。
- 发现预览写业务对象、半批提交、并发双写、历史修订被改写或内容泄露时，立即停止扩大执行并记录脱敏复现。

## 交付

更新 `docs/b5-activity-import-running.md` 和执行角色日志，至少记录：

- 实际架构和数据流；
- 迁移与兼容行为；
- 新增/修改文件；
- 各层自测命令、通过/失败/跳过计数；
- PostgreSQL 启停和清理状态；
- 未验证项、已知风险和 C9 进入说明；
- 有序文件清单及总摘要 `P3-B5-SHA256:<digest>`。

摘要算法沿用 C8：对清单中每个仓库相对路径记录 SHA-256，再对 `path<TAB>sha256<LF>` 的 UTF-8 字节流计算总 SHA-256。必须包含实现、迁移、DTO/API、执行方测试以及直接改变的 P1/P2 文件。

自测通过后状态只能是 `review`，立即停止修改，等待总控核对并派发 P3-C9。不得自行宣布独立验收、修改 Git、启动 C9 或继续扩展功能。

接单、纯解析完成、迁移完成、预览完成、提交完成、SQLite 回归、PostgreSQL 回归和交付时更新执行快照。预计超过五分钟的操作先写下一检查点；同一问题连续两个检查点无进展时安全停止，报告错误、已尝试方案和需要共同决定的问题。
