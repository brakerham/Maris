# P3-C9-R2 活动 Markdown 导入独立复验报告

- 任务：`P3-C9-R2`
- 状态：`review`
- 执行时间：2026-09-19，Asia/Shanghai
- 固定输入：P3-B5-R1 22 文件快照、原 P3-C9 报告、P3-C8 89 项矩阵
- 总结论：**建议总控接受 P3-B5-R1**。返修后的真实 PostgreSQL migration、执行方九类门禁和独立 PostgreSQL 门禁全部通过；`P3-C9-PG-001` 已关闭，89 项适用案例全部为 `passed`。最终 `complete` 仍由头脑风暴总控决定。

## 输入与快照门禁

验收开始前按 B5 交接算法独立重算 22 个文件：逐文件摘要 22/22 匹配，总摘要为：

```text
P3-B5-R1-SHA256:fb46b8fa4957c93bfd8f971b1fd987e45dd4779e8d6eac2907660fa2f1fef53c
```

原 C9 报告按原始字节重算，摘要匹配任务卡：

```text
P3-C9-REPORT-SHA256:d0b2189ec65d477a6fcefa9790898b5840d4f330f2ed713a6684346b8fada83b
```

把返修的两个文件替换为原 C9 单文件摘要后，重建总摘要精确等于原 `P3-B5-SHA256:9fb36c653d20ff14f85ad9667de454900cca0c6e3ead17c2619df11fb7f63d6e`，确认其余 20 个文件未变化。获准的两文件变化如下：

| 文件 | 原 C9 SHA-256 | R1 SHA-256 | 结论 |
|---|---|---|---|
| `migrations/versions/c82d7a4f901e_add_activity_import.py` | `8df7977aa90ffa6bf7a076886fd8eafcd2c2a43c762ecde56a6912350917abef` | `e0703c5a87f792a5e7c4414192aefd1a6ed00a328094f18dc0b4db26e9e24a0d` | 仅缩短显式外键名并保持语义 |
| `tests/activity_import/test_migration.py` | `6510dac2ff864902cd6b17dda4bb52633883d60b53e9b06eb495f1332cc68ab6` | `af4c4e025948d1dea7c5433224e48bed0e746610f961d7ce9d6ff04685f5a7a9` | 新增长度上限与双向一致回归 |

静态复核确认 upgrade 和 downgrade 均引用 `fk_activity_template_revision_import_candidate`，名称长度为 46；revision ID、表列、外键目标、`ondelete=RESTRICT` 和迁移顺序未变化。

## 执行结果

所有案例只使用虚拟活动、随机 schema 和回环 PostgreSQL，不涉及真实个人数据。

| 证据层 | 最终结果 | 判定 |
|---|---:|---|
| 独立本地 `tests/independent/activity_import`，排除 PostgreSQL 文件 | 81 passed，0 failed，1 warning | 原 C9 的 64 个本地通过结论无回退 |
| 执行方本地 `tests/activity_import`，排除 PostgreSQL 文件 | 144 passed，0 failed，1 warning | 包含新增标识符长度/对称性回归 |
| 旧 migration 定向回归 | 4 passed，0 failed | P1/P2 迁移兼容未回退 |
| 执行方真实 PostgreSQL | 9 passed，0 failed，0 skipped，0 setup error | 九类目标库门禁全部进入业务断言 |
| 独立真实 PostgreSQL最终重跑 | 10 passed，0 failed，0 skipped，1 warning | 并发、事务、约束、迁移和恢复全部通过 |
| 最终 22 文件快照 | 22/22 匹配 | 产品、迁移和执行方测试在验收中无漂移 |

warning 是既有 Starlette TestClient 使用 AnyIO 弃用类型别名的提示，不影响本次断言。

## 独立测试校正

独立 PostgreSQL 首轮为 9 passed、1 failed。失败发生在回滚案例的验证代码：测试引用了模型不存在的 `AuditEvent.resource_id`，未构成产品失败。获配的独立测试文件内做了最小校正：记录故障提交前的 `CommandReceipt` 和 `AuditEvent` 总数，并断言故障后两者均不增加；同时保留模板零写入、batch 仍为 `previewed`、candidate 决定仍为空的断言。该变化增强了整批回滚证据，没有修改或放宽产品契约。

校正后完整重跑 10/10 通过。文档收口审计又发现 `P3-SEC-10` 需要显式的 SPG 隐私证据，因此在既有同名并发冲突节点加入虚拟 canary：真实 PostgreSQL 唯一性竞争仍收敛为一个成功和一个 `concurrent_modification`，canary 未出现在异常文本或结构化日志。补强后再次完整重跑仍为 10/10 通过。

最终独立文件摘要为：

```text
tests/independent/activity_import/test_postgresql_contract.py  f2402395dd6e59c4b186e266d3038ff6c00664cf650737ec9ee82ca7273b81b3
```

## PostgreSQL 专项覆盖

执行方 9 项与独立 10 个测试节点共同实际覆盖：

- 同幂等键并发 preview 只形成一个持久 batch；
- 同幂等键并发 commit 恰好一次写入并稳定重放；
- 同一 batch 不同键只有一个提交者成功；
- 不同 batch 对同一规范名并发 create 由数据库约束收敛；
- preview 后目标被 revise 或 archive 时重新检查 stale 状态；
- 中途故障整批回滚，不留下模板、回执、审计或候选半写入；
- 规范名唯一性与金额形状由数据库约束兜底；
- 空 schema 和已有 P2 schema 均可升级到 P3 head，并保持既有数据；
- 成功响应丢失后，新服务实例可凭相同键恢复原结果，换键重复确认被拒绝。

## 缺陷关闭

`P3-C9-PG-001` 的原始最小复现是空 PostgreSQL schema 升级到 `c82d7a4f901e` 时，82 字符显式外键名超过 PostgreSQL 63 字符上限并触发 `IdentifierError`。R2 在新固定快照上验证：46 字符新名称可完成空库和已有 P2 schema 升级，执行方 9 项与独立 10 个节点均无 setup error，因此该缺陷在 P3-B5-R1 范围内关闭。本轮没有发现新的 P0/P1 产品缺陷。

## 89 项矩阵收口

[P3 独立验收矩阵](phase-3-activity-import-test-matrix.md) 已逐行更新。原 C9 的 64 个 `passed` 经本地回归和固定快照门禁保留；原 1 个 `failed` 与 24 个 `blocked` 均取得真实 PostgreSQL 证据并更新为 `passed`。

| 分组 | ID 范围 | 数量 | R2 最终状态 | 主要证据 |
|---|---|---:|---|---|
| Markdown 语法 | `P3-SYN-01..12` | 12 | 全部 passed | 独立 parser 与本地回归 |
| 金额与非记账边界 | `P3-AMT-01..10` | 10 | 全部 passed | parser/service/SQLite 与固定快照 |
| 预览纯度 | `P3-PRV-01..08` | 8 | 全部 passed | 本地数据库快照、真实 PG 回滚/迁移 |
| 候选动作与来源 | `P3-CAN-01..08` | 8 | 全部 passed | 独立候选、版本和来源断言 |
| 冲突与并发 | `P3-CNF-01..08` | 8 | 全部 passed | 本地 stale/归档与真实 PG 竞争 |
| 幂等与重放 | `P3-IDM-01..09` | 9 | 全部 passed | HTTP/SQLite、PG 同键并发和恢复 |
| 原子性与事务 | `P3-ATM-01..08` | 8 | 全部 passed | SQLite 与 PG 中途故障全回滚 |
| 安全与隐私 | `P3-SEC-01..10` | 10 | 全部 passed | 本地 canary/资源边界及 PG 冲突异常与日志 canary 断言 |
| HTTP 契约 | `P3-API-01..08` | 8 | 全部 passed | 独立 FastAPI/Pydantic 契约 |
| 数据库与迁移 | `P3-DB-01..08` | 8 | 全部 passed | SQLite、旧迁移及真实 PG 空库/已有库迁移 |
| **合计** | 89 个唯一 ID | **89** | **89 passed** | 0 failed、0 blocked、0 not_applicable |

## 资源关闭与执行边界

外部操作前控制版本为 `2026-09-19T19:18:10+08:00`，本测试智能体是 Docker Desktop 单次启动与 `finance-postgres` 启停的唯一负责人。首次检查确认 Engine 未运行后，只隐藏启动已安装的 Docker Desktop 一次；随后只操作 Compose 中的 `finance-postgres`。主验收完成后先普通 down；文档收口发现 SPG 隐私断言缺口时，又开启一个短测试窗口完整重跑独立 PostgreSQL 文件，并再次普通 down。两个窗口均只运行该服务。

测试结束执行普通 `docker compose down`，容器和项目网络已移除；`docker compose ps --format json` 退出 0 且无输出。未使用 `-v`，未删除 volume、prune、重置数据库、启动其他服务或修改 Docker 全局配置。

没有运行真实 DeepSeek、桌面端、OpenClaw、微信或真实个人数据。没有修改产品、迁移、执行方测试/文档、依赖、Compose、接口冻结、控制/总览、其他角色状态或原 C9 报告，也没有执行 Git 写操作。P3-C9-R2 停在 `review`。
