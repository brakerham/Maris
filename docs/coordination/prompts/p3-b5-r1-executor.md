# P3-B5-R1：PostgreSQL 外键名最小返修

状态：`ready`。唯一负责人：用户启动的既有执行智能体。测试智能体已停止在 P3-C9 `review`；本任务只修复 `P3-C9-PG-001`。

## 开始前

按顺序读取 `AGENTS.md`、`README.md`、`docs/project-coordination.md`、`docs/coordination/README.md`、`docs/coordination/control.md`、`docs/coordination/agents/executor.md`、`docs/phase-3-interface-freeze.md`、`docs/b5-activity-import-running.md`、`docs/testing/phase-3-c9-activity-import-report.md` 和 `docs/coordination/agents/tester.md`。

绑定输入：

```text
P3-B5-SHA256:9fb36c653d20ff14f85ad9667de454900cca0c6e3ead17c2619df11fb7f63d6e
P3-C9-REPORT-SHA256:d0b2189ec65d477a6fcefa9790898b5840d4f330f2ed713a6684346b8fada83b
```

开始修改前独立重算 B5 的 22 文件快照和 C9 报告摘要。任一不匹配或控制文件改变负责人时停止并报告。

## 已确认缺陷

`migrations/versions/c82d7a4f901e_add_activity_import.py` 为 `activity_template_revision.source_import_candidate_id` 创建了 82 字符显式外键名：

```text
fk_activity_template_revision_source_import_candidate_id_activity_import_candidate
```

PostgreSQL 标识符上限为 63 字符，因此空 schema 在 P3 migration 处失败，阻断全部九类 PostgreSQL 场景。SQLite 和本地业务测试通过不能关闭此缺陷。

## 唯一修复

把 upgrade 和 downgrade 中该显式名称同时改为：

```text
fk_activity_template_revision_import_candidate
```

该名称长度为 46。不得改 revision ID、表/列、on-delete、约束语义、迁移顺序或其他产品行为。

在 `tests/activity_import/test_migration.py` 增加一个执行方回归，至少保证：

- P3 migration 中所有显式 PostgreSQL identifier 名称不超过 63 字符；
- upgrade 和 downgrade 使用同一个冻结外键名；
- 测试不依赖脆弱的单纯源码整段复制，可通过 migration 模块常量或等价的可维护方式锁定该契约。

如果为可维护测试需要把外键名提取为 migration 文件内常量，允许这样做；不得移动到产品运行模块或新增依赖。

## 文件边界

允许修改：

- `migrations/versions/c82d7a4f901e_add_activity_import.py`
- `tests/activity_import/test_migration.py`
- `docs/b5-activity-import-running.md`
- `docs/coordination/agents/executor.md`

其余 20 个 B5 快照文件、全部独立测试/报告/矩阵、接口冻结、控制/总览、其他角色状态、依赖、Compose、OpenClaw 和 Git 全部只读。

## 自测和 PostgreSQL 责任

本返修期间执行智能体是 `finance-postgres` 的唯一启停负责人。开始 Docker 操作前重新读取最新 `control.md`。

1. 运行新的标识符回归和 SQLite migration 相关测试。
2. 运行 `tests/activity_import` 本地套件一次，确认 143 项既有行为没有回退，并单列新增测试后的总数。
3. 只启动 `docker compose up -d finance-postgres`，等待健康后使用项目测试凭据、随机 schema 和虚拟数据。
4. 实际运行 `tests/activity_import/test_postgresql.py` 九类执行方测试；九项必须进入业务断言并通过，不能以收集、跳过或 setup error 代替。
5. 定向复跑受迁移影响的旧 migration 测试；无需重复完整 92 项旧本地回归，C9-R2 会统一复跑。
6. 结束时普通 `docker compose down` 并确认服务列表为空。禁止 `down -v`、删除 volume、prune、数据库重置、其他服务或 Docker 全局配置。

不得运行或修改 `tests/independent/**`，不得把执行方 PostgreSQL 通过写成独立验收。

## 新快照与交付

沿用 B5 的同一 22 文件清单和 `path<TAB>sha256<LF>` 算法，更新变更文件摘要并生成：

```text
P3-B5-R1-SHA256:<new digest>
```

更新 B5 运行说明和执行日志，记录：

- 精确修改及约束名长度；
- 本地 migration/P3 测试结果；
- PostgreSQL 九项实际结果；
- 容器普通关闭和服务列表；
- 新的 22 文件清单及总摘要；
- 未验证项。

自测通过后只能提交 `review` 并停止。不得修改 Git、启动 C9-R2、顺手重构迁移或扩展产品功能。若九项 PostgreSQL 仍在迁移/设置阶段失败，保留脱敏错误、普通关闭容器并停止；连续两个检查点无进展时按协调规则报告。
