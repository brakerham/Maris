# P3-IF-001：活动 Markdown 导入接口冻结

- 冻结编号：`P3-IF-001`
- 冻结时间：2026-09-18 16:10，Asia/Shanghai
- 总控负责人：头脑风暴智能体
- 输入：[P3 任务书](phase-3-activity-import-brief.md)、[P3-D7 技术方案](phase-3-d7-activity-import-advice.md)、[P3-C8 测试矩阵](testing/phase-3-activity-import-test-matrix.md)
- 实现任务：`P3-B5`
- 后续独立验收：`P3-C9`

P3-B5 建立“Markdown 文本 → 持久候选预览 → 用户逐项确认 → 活动模板原子导入”的最小纵向切片。本文是唯一实现契约；D7 是方案依据，C8 是验收设计。三者冲突时以本文为准。

## 1. 范围与技术选择

1. 首版完全离线、确定性解析，不调用 DeepSeek 或其他模型，不联网，不增加 Markdown/HTML 解析依赖。
2. 使用 Python 标准库、Pydantic、FastAPI、SQLAlchemy 和 Alembic；不引入 LangChain、LangGraph、RAG 或向量数据库。
3. 预览持久化最小导入批次和候选；完整 Markdown、自由文本原文、HTML、链接目标和本地路径不落库。
4. 活动参考金额扩展为上下界；精确金额以 `min=max` 表示。不能把范围压成平均值、端点或单一事实。
5. 活动组合延后。组合或成员字段必须形成不可提交的 `unresolved`，不得伪装成普通活动模板。
6. P3 不创建活动发生记录、账目、账户变化、预算消耗、收入、提醒或 Agent 记忆。
7. React、Electron、真实文件选择器、DeepSeek、OpenClaw、微信及真实个人资料不在 P3-B5。

## 2. 受限 Markdown 语法

### 2.1 文档结构

- 请求体中的 `markdown` 是 UTF-8 JSON 字符串。先移除一个开头 BOM，把 CRLF 和单独 CR 统一为 LF；正文不作 NFKC。
- 文档可以有零个或一个 H1 显示标题；多个 H1、H1 出现在首个 H2 之后或没有 H2，返回整体 `invalid_markdown_structure`。
- 每个行首 `## ` H2 开始一个活动候选。H3 及更深标题不承载业务字段；候选内出现时产生阻塞问题 `unsupported_markdown_structure`，候选为 `unresolved`。
- 活动名称作 NFC、首尾去空白、连续 Unicode 空白折叠后保存显示值；最大 120 个 Unicode 字符。
- 同一批次中 `name_normalized` 相同的 H2 全部标为 `conflict`。
- 首版只把以 `- ` 开头的普通无序列表和下面三种白名单自然句式解释为业务输入。`*`、`+`、有序列表、嵌套列表和表格不解释为字段，并产生可确认的 `unsupported_free_text` warning；它们不能静默写库。

### 2.2 金额语法

只识别下面三种完整行；全角冒号和末尾句号按示例固定：

```markdown
- 参考金额：18.00 元
- 参考金额范围：15.00–20.00 元
- 通常每次 15.00–20.00 元，只用于预测。
```

- 范围分隔符接受 `-`、`–` 或 `至`；分隔符两侧可有普通空格。
- 数字只接受十进制非负字符串，最多两位小数；不接受逗号、指数、`float`、符号或静默舍入。
- 零可作为参考预测值。上限沿用 P1：`999_999_999_999` 分，即 `9,999,999,999.99` 元。
- 只接受 `元`，规范币种固定为 `CNY`。其他显式币种产生阻塞问题 `unsupported_currency`。
- 精确值保存为 `reference_minor=min=max`；范围保存为 `reference_minor=NULL` 和完整上下界；无金额时三个字段都为空。
- 下界大于上界、只有一个端点、非法精度、越界或同候选出现多个金额字段，候选均为 `unresolved`。

### 2.3 未支持文本与不可信结构

- 普通频率、日期、交通、备注和其他自由文本产生 `unsupported_free_text` warning。用户逐项确认该 warning 后，可以只导入已结构化字段。
- 未知 `键：值` 产生 `unknown_import_field` warning，不映射到任何业务列。看起来意图填写已支持字段但解析失败时，产生阻塞 error，不能通过 warning 确认绕过。
- 围栏/缩进代码、HTML、图片、链接、路径文本和伪系统/工具指令不执行、不渲染、不请求、不读取；它们产生带行号的问题。
- NUL、孤立代理项、双向文本控制字符和除换行、制表外的 C0 控制字符使整体请求失败。
- warning 可以显式确认；error 不能确认绕过。API 不回显完整自由文本。

## 3. 名称匹配和候选动作

`name_normalized` 由 NFC、空白折叠、首尾去空白和 `casefold()` 产生。不删标点，不作拼音或简繁转换，不作模糊匹配。

| 条件 | `proposed_action` |
| --- | --- |
| 当前和归档模板均无精确规范名 | `create` |
| 一个未归档精确同名模板，显示名或金额结构不同 | `revise` |
| 一个未归档精确同名模板，显示名和金额结构相同 | `unchanged` |
| 精确命中归档模板、同批重名、历史重复或目标不唯一 | `conflict` |
| 结构/金额阻塞错误或活动组合 | `unresolved` |

- `activity_template.name_normalized` 全局唯一，归档后继续占用；P3 不自动恢复、改名或复用身份。
- 相似但规范名不同的活动按 `create`，不自动合并；首版不要求相似度提示。
- 两个候选不得同时接受并写入同一逻辑名称或同一目标模板。
- 提交决定只有 `accept` 和 `skip`。只有 `create`、`revise` 可 `accept`；`unchanged`、`conflict`、`unresolved` 必须 `skip`。

## 4. 持久模型

新增 `activity_import_batch`，至少包含：UUID、可信 `owner_id`、`previewed/committed` 状态、`activity-md-v1` 解析器版本、可空 `source_label`、内容 HMAC 的密钥版本与摘要、预览/提交回执引用、选择指纹、整数版本、UTC 创建/提交时间。

新增 `activity_import_candidate`，至少包含：UUID、批次与唯一 ordinal、清理后的 H2、1 基闭区间来源行号、候选块 HMAC、`name_normalized`、`CNY`、可空金额上下界、动作、目标模板与预期版本、受约束的问题 JSON、提交决定和结果模板/版本。

- 候选 UUID 在同一个批次、GET 和同预览幂等键重放中稳定。
- 使用新的预览幂等键，即使 Markdown 相同，也会生成新批次和新候选 UUID；跨批次只要求顺序、规范字段和块摘要确定，不要求 UUID 相同。
- `issues_json` 只保存 code、severity、field、line 等结构化值，不保存原文。
- `source_label` 可选，最大 120 字符，只保存去路径后的基本名；空值合法。
- 完整 Markdown 永不落库。内容摘要为带域分隔和密钥版本的 HMAC-SHA-256；候选块使用独立域。
- 已提交和未提交批次在 P3 均保留，不增加后台清理或过期状态。删除、导出和保留期另立隐私任务。

`activity_template` 增加非空唯一 `name_normalized`。`activity_template_revision` 增加可空 `reference_min_minor`、`reference_max_minor`、`source_import_candidate_id`，保留兼容 `reference_minor`，并冻结：

1. 无金额：三列全空。
2. 精确金额：三列相同。
3. 范围金额：兼容单值为空，上下界均非空且 `0 <= min <= max <= MAX_MINOR`。
4. 旧非空单值迁移时回填上下界。
5. 现有直接创建/修订命令继续接受精确金额并同时写三列。

## 5. API

### 5.1 公共边界

- 前缀：`/api/v1/activity-imports`。
- 身份、owner、来源系统和权限由 FastAPI 依赖注入；body 不得自报。
- 两个 POST 必须带 `Idempotency-Key`：去首尾空白后 1–256 个可打印 ASCII 字符；原值不落库。
- Content-Type 必须是 `application/json`，JSON 按 UTF-8 处理；所有 Pydantic 模型 `extra="forbid"`。
- 错误沿用 `{request_id,error:{code,message,retryable}}`，不得泄露输入、SQL、驱动错误、堆栈或路径。

### 5.2 预览

`POST /api/v1/activity-imports/preview`

请求只含 `markdown` 和可空 `source_label`。限制：

- HTTP body 最大 96 KiB；
- 规范行尾后的 Markdown UTF-8 最大 64 KiB；
- 最多 2,000 行、50 个 H2 候选；
- 每个候选最多 20 个非空内容行；
- H1/H2 和 source label 最大 120 字符。

首次成功返回 `201`；同操作域、同键同载荷重放返回 `200` 且 `replayed=true`。预览事务可以写批次、候选和预览幂等回执，但不得写任何活动模板、修订、发生记录或财务业务对象，也不得写业务审计事件。

### 5.3 批次读取

`GET /api/v1/activity-imports/{batch_id}`

只读取当前可信 owner 的批次，返回当前候选、决定和结果。不存在或不属于当前 owner 统一返回 `404 batch_not_found`。

### 5.4 原子提交

`POST /api/v1/activity-imports/{batch_id}/commit`

请求包含字面量 `confirmed=true`、`batch_version`、`content_digest` 和 `decisions`。每个持久候选必须恰好出现一次：

- 客户端只能回传 candidate ID、`accept/skip`、预期动作、可空预期模板版本和 warning code 列表；不能回传名称、金额或目标 ID 作为写入依据。
- warning 确认集合必须与该候选当前 warning codes 精确匹配；未知、缺失或重复 code 均拒绝。
- 批次版本、内容摘要、动作和模板版本必须匹配预览。
- 全部候选 `skip` 是合法提交：批次进入 committed，不创建模板。空 decisions 因缺失候选而非法。
- 首次和同键同载荷重放均返回 `200`；重放设置 `replayed=true`。

## 6. 幂等、并发和事务

复用 P1 `command_receipt`、HMAC 键摘要和规范 JSON 指纹，操作域分别为可信 owner/channel 下的 `activity_import.preview` 与 `activity_import.commit`。

- 同域、同键、同指纹重放首次结果；同键异载荷返回 `duplicate_request_conflict`。
- 成功提交后换新键再次提交同一批次返回 `import_already_committed`；客户端用 GET 恢复原结果。
- 提交在一个外层 `Session.begin()` 中依次完成：抢占回执、锁批次、验证全集、稳定顺序锁目标、复验版本/归档/名称、写全部模板修订与审计、保存候选结果、更新批次、保存回执。
- 现有单模板公开方法与批量提交共享接收当前 Session 的模板写入原语；禁止循环调用各自开启事务的公开方法。
- 任一步失败，模板、修订、审计、候选决定、批次状态和成功回执全部回滚，批次保持 `previewed`。
- PostgreSQL 使用批次行锁、模板乐观锁和规范名唯一约束；两个并发提交最多一个改变状态。名称竞争者返回可重试 `concurrent_modification` 并要求重新预览。
- 首版只持久化 `previewed` 和 `committed`，不增加 `processing` 或 `failed`。

## 7. 稳定错误

| HTTP | code | retryable |
| --- | --- | --- |
| 404 | `batch_not_found` | false |
| 409 | `duplicate_request_conflict` | false |
| 409 | `import_content_mismatch` | false |
| 409 | `concurrent_modification` | true |
| 409 | `candidate_not_actionable` | false |
| 409 | `unacknowledged_warning` | false |
| 409 | `import_already_committed` | false |
| 413 | `import_text_too_large` | false |
| 415 | `invalid_content_type` | false |
| 422 | `invalid_request` | false |
| 422 | `invalid_markdown_structure` | false |
| 422 | `import_candidate_limit_exceeded` | false |
| 422 | `invalid_candidate_selection` | false |
| 422 | `invalid_amount_precision` | false |
| 422 | `amount_out_of_range` | false |
| 422 | `unsupported_currency` | false |
| 503 | `database_unavailable` | true |
| 500 | `persistence_error` | true |

候选级 warning/error 正常放在成功预览的 issues 中；只有整体无法安全形成预览时返回 HTTP 错误。

## 8. 日志、权限与安全

允许日志字段：request/batch ID、parser version、内容摘要前 12 位、候选数、动作计数、接受数、稳定错误码、耗时和 replayed。

禁止日志字段：Markdown、活动名、source label、完整摘要、幂等键、候选字段、链接、路径、Pydantic 原始 input、SQL/驱动正文和账号标识。

Markdown 永远只是数据。解析器不得执行代码、读取路径、发出网络请求、调用工具或改变 Agent 权限。后续若增加模型，模型输出仍是不可信候选，必须经过同一确定性校验、版本复验和用户确认。

## 9. 迁移和数据库证据

- 新 Alembic revision 从 `7f3e2d1c9a4b` 继续，不改写既有迁移。
- 回填规范名时若发现重复，迁移安全失败并报告，不自动合并。
- SQLite 用于解析、DTO、常规服务、API 和回归。
- PostgreSQL 必须独立覆盖：预览同键并发、提交同键并发、同批异键并发、同名 create 竞争、stale/归档、整批故障回滚、数据库约束、空库/已有数据升级和响应丢失恢复。
- SQLite 通过不能代替上述 PostgreSQL 结论。

## 10. 文件所有权

P3-B5 执行智能体可修改：

- `src/wife_system/activity_import/**`；
- `src/wife_system/api/activity_import_routes.py` 与必要的 `api/app.py` 组装；
- 为范围金额、规范名和共享 session 原语所必需的 `src/wife_system/finance/models.py`、`schemas.py`、`service.py`；
- 一个从当前 head 继续的 P3 Alembic migration；
- `tests/activity_import/**` 及为 P1/P2 兼容性所必需的执行方测试；
- `docs/b5-activity-import-running.md` 和自身角色状态。

`tests/independent/**`、C8/C9 文档、本文、控制/总览、其他角色状态、OpenClaw 和 Git 全部只读。发现必须改变本文契约时停止并报告，不得自行扩大范围。

## 11. P3-B5 自测和交付

执行方至少提供：

1. 纯解析与 DTO 的正常、Unicode、金额、未知结构和资源边界测试；
2. SQLite 的预览纯度、五种动作、重放/冲突、warning 确认、全部 skip、整批故障回滚；
3. 三个 API 的状态码、严格 schema、owner 隔离、安全错误和日志白名单；
4. 空库与既有虚拟数据迁移，及 finance、agent finance、API 回归；
5. PostgreSQL 的九类并发、约束、回滚、迁移和恢复证据；
6. 运行说明、未验证项和有序文件摘要快照 `P3-B5-SHA256`。

执行方自测只能提交 `review`。测试智能体必须先核对固定快照，再按 C8 形成 P3-C9 独立结论；总控验收前不得标记产品 `complete`。
