# P1-IF-001：阶段 1 财务数据底座接口冻结

- 冻结编号：`P1-IF-001`
- 冻结时间：2026-09-16 12:55，Asia/Shanghai
- 总控负责人：头脑风暴智能体
- 输入：[P1-D3 技术建议](phase-1-d3-data-advice.md)、[P1-C3 独立测试矩阵](testing/phase-1-data-test-matrix.md)、[阶段 1 任务书](phase-1-data-foundation-brief.md)
- 适用任务：`P1-B3` 实现、`P1-C4` 独立验收、`P1-D4` 实际代码教学

本文冻结阶段 1 首个数据纵向切片。执行智能体可以在不改变行为契约的前提下决定私有函数和内部文件细节；表关系、金额、事务、错误、测试归属和范围不得自行改变。需要变更时先停止实现并交回总控与技术顾问。

## 1. 技术栈与运行边界

1. ORM 使用 SQLAlchemy 2.x 类型化 Declarative：`Mapped[...]`、`mapped_column()`；ORM 模型与 Pydantic 命令/结果模型分离。
2. 数据库访问使用同步 `Session`。一个业务命令使用一个短生命周期 Session 和一个 `Session.begin()` 事务。
3. Alembic 管理 schema 迁移。不能依靠 `metadata.create_all()` 代替正式迁移；测试夹具可以在明确隔离的纯单元场景使用元数据建表。
4. SQLite 用于本地开发、快速规则测试和迁移冒烟；每条应用连接显式启用外键。
5. PostgreSQL 是目标环境和 C4 的并发、锁、迁移与约束验收准绳。SQLite 通过不能替代矩阵中标记为 PostgreSQL 必测的结论。
6. B3 不增加新的 FastAPI 财务端点，不接 DeepSeek、OpenClaw、微信、桌面 UI 或真实数据。对外边界先以 Python 命令服务和 Pydantic DTO 表达。

## 2. 冻结数据模型

必须实现以下表；可以增加纯技术字段和索引，但不能改变业务含义：

| 表 | 作用与关键关系 |
| --- | --- |
| `account` | 资金位置；保存币种、版本和归档时间，余额只从账户分录计算 |
| `category` | 可编辑的收入/支出分类；历史分录可继续引用归档分类 |
| `financial_transaction` | 不可变的已入账经济事件；保存类型、发生时间、币种及退款/冲销关系 |
| `transaction_entry` | 平衡分录；账户、收入分类、支出分类或期初权益角色之一 |
| `activity_template` | 活动的稳定身份、当前修订和归档状态 |
| `activity_template_revision` | 不可变的模板名称与预测参考信息 |
| `activity_occurrence` | 某次实际活动；同一模板一天可发生多次 |
| `activity_entry_allocation` | 活动与支出分录的多对多金额分配 |
| `income_schedule` | 收入安排的稳定身份、当前版本和归档状态 |
| `income_schedule_version` | 不可变的金额、月度规则和生效区间 |
| `income_expectation` | 由安排版本生成的某日预计到账，不等于实际收入 |
| `income_expectation_match` | 预计到账与实际收入分录的匹配金额 |
| `budget_plan` | 月度预算计划的稳定身份和版本锁 |
| `budget_version` | 某预算月份的不可变已发布版本、发布时间和调整理由 |
| `budget_allocation` | 已发布预算版本对支出分类的额度 |
| `command_receipt` | 持久化来源幂等键摘要、请求指纹和首次业务结果 |
| `audit_event` | 追加式的结构化实体变化记录，不作为当前状态来源 |

聚合根和独立引用记录使用应用生成 UUID。时间点按 UTC 保存，月度边界与展示使用 `Asia/Shanghai`。已入账交易和分录直接创建为不可变事实，不实现可编辑草稿状态。

`transaction_entry` 的符号和目标约定：

- `account`：流入为正，流出为负，必须有 `account_id`。
- `expense`：消费为正，退款反向为负，必须引用 `kind=expense` 的 `category_id`。
- `income`：确认收入为负，收入冲销为正，必须引用 `kind=income` 的 `category_id`。
- `opening_equity`：与期初账户分录平衡，不引用账户或分类。
- 每条分录只能匹配一个目标形状，金额不能为零；同一交易至少两条分录且总和为零。

## 3. F01–F15 冻结参数

### F01 金额格式、表示和边界

- 命令边界接受十进制字符串；禁止接受或经过 Python `float`。
- 内部和数据库使用 Python `int` / SQL `BIGINT` 最小货币单位，字段名以 `_minor` 结尾。
- CNY 允许最多两位小数。普通收入、支出、转账、退款命令金额范围为 `0.01` 至 `9,999,999,999.99` 元，即 `1..999_999_999_999` 分。
- 用户输入金额必须为正数；分录方向由命令类型产生。预算额度允许零。
- 所有聚合、余额和中间加总在落库前检查上述绝对边界，越界返回 `amount_out_of_range`。

### F02 舍入

- 已入账事实和预算输入超过两位小数时返回 `invalid_amount_precision`，不得静默舍入。
- 预测或比例分摊需要从 `Decimal` 生成整数分时使用 `ROUND_HALF_UP`。
- 多项分摊产生余分时按稳定排序分配剩余一分，确保明细总和等于原金额；排序键必须记录在实现说明中。

### F03 币种

- P1 只接受 `CNY`；省略时从应用默认配置取得 `CNY`，不能从硬编码生活费金额推导。
- 每个交易、账户、预算和收入安排显式保存币种。非 CNY、跨币种交易和汇率换算返回 `unsupported_currency`。

### F04 账本、余额与透支

- 使用交易头与受限角色平衡分录，支持 `opening_balance`、`income`、`expense`、`transfer`、`refund`、`reversal`。
- 账户期初余额通过 `opening_balance` 交易记录，不在账户表保存可写余额。
- 转账本金只有两个账户分录，不进入收入或支出。转账手续费若存在，必须是同一交易中的明确支出分录；B3 可以先不提供手续费参数。
- P1 不阻止账户余额为负。余额是账本事实；透支提醒与消费授权属于后续规划层。
- 余额、收入和支出均从分录确定性计算，不能维护第二份可漂移总额。

### F05 修订、删除、乐观锁与审计

- 已入账交易、分录、退款关系、发布预算、收入安排版本、模板修订、幂等收据和审计不得普通更新或硬删除。
- 财务纠错使用 `reversal` 完整反向交易，可再创建替代交易；原交易保持可见。
- 账户、类别、活动模板、收入安排、预算计划使用 `archived_at` 和非空整数 `version_id`。
- 修改或归档命令必须携带 `expected_version`；不匹配返回 `concurrent_modification`。
- 审计只保存命令 ID、实体类型/ID、动作、版本、原因和时间；不保存原始消息、完整描述、账号或密钥。

### F06 退款

- 退款只能引用已入账 `expense`，币种相同；累计退款不能超过原交易全部可退支出分录金额。
- 退款可进入任一未归档的 CNY 账户；支出反向必须沿用原交易的分类和分录比例，不能由调用方改分类。
- 允许部分和多次退款。并发退款必须锁定原交易或用等价约束保证单一最终余额。
- 退款按自身 `occurred_at` 进入发生月份；不改写原月份。月度快照分别显示毛支出、当月退款和净支出。

### F07 活动与账目

- 模板修订不可变；活动发生引用当时的修订。模板参考金额只用于预测，不生成账目。
- 同一模板同一天可有多个活动发生。
- 活动发生和支出分录使用 `activity_entry_allocation` 多对多关联；分配金额必须为正，同一支出分录的分配合计不得超过其正支出金额。
- 一笔支出可分配给多个活动，一次活动可关联多笔支出。
- 已有关联的活动允许标记取消但不删除历史关联；取消后禁止新增分配。归档模板不影响历史活动。

### F08 收入安排与预计到账

- P1 实现月度收入安排。版本包含金额、币种、生效起止日期和每月预计到账日 `1..31`。
- 某月不存在指定日期时取该月最后一天；周期日期按 Asia/Shanghai 计算。
- 新版本只影响其生效日期及之后尚未生成的预计项，不修改历史预计项和实际收入。
- 实现 `income_expectation` 实体。一个预计项可匹配多条实际收入分录；一条实际收入分录最多匹配一个预计项。
- 匹配金额必须为正，累计不得超过预计金额；若一笔到账覆盖多个预计项，调用方必须拆成同一交易中的多条收入分录。

### F09 预算版本

- P1 只实现自然月预算，时区为 Asia/Shanghai。预算总额等于所有支出分类额度之和，不另存一份总额。
- `budget_allocation.limit_minor >= 0`；同一版本同一分类只能出现一次。
- 同一月份允许发布多个调整版本。每个发布版本不可变，版本号递增；第二版起必须提供非空调整理由。
- 不允许为已经结束的月份回溯发布。当前月和未来月可以发布；同一计划、月份的当前版本由 `published_at <= as_of` 的最高版本号决定。
- 快照必须返回采用的 `budget_version_id`；没有预算时返回 `null` 和空额度，不伪造零预算版本。

### F10 来源幂等

- 每个业务写命令必须提供 `source_system` 和 `source_event_id`。测试使用虚拟值；原始来源 ID 不落库。
- `key_digest = HMAC-SHA-256(secret[key_version], source_system + "\\0" + source_event_id)`；唯一范围是 `(source_system, key_digest)`，P1 保留期为永久。
- 请求指纹使用同一密钥，对“命令 schema 版本 + 已校验结构化载荷的规范 JSON”计算 HMAC-SHA-256；字段顺序和无意义空白不改变指纹。
- 同键同指纹返回首次结果并标记 `replayed=true`；同键不同指纹返回 `duplicate_request_conflict`。
- 幂等占位、业务写入、审计和成功结果同事务提交。失败事务不留下成功收据；不能只靠先查后写防并发。
- `key_version` 入库；B3 不实现在线密钥轮换流程，但运行说明必须说明轮换需要维护迁移和暂停写入。

### F11 稳定错误语义

业务层至少提供以下稳定错误码，不向调用方暴露 SQL、驱动错误、堆栈或私人载荷：

| 错误码 | 含义 | 可重试 |
| --- | --- | --- |
| `validation_error` | 普通字段或状态校验失败 | 否 |
| `invalid_amount_precision` | 金额小数位超限 | 否 |
| `amount_out_of_range` | 金额或聚合越界 | 否 |
| `unsupported_currency` | 非 CNY 或跨币种 | 否 |
| `not_found` | 目标不存在 | 否 |
| `archived_resource` | 归档资源用于新写入 | 否 |
| `unbalanced_transaction` | 分录不平衡或目标形状错误 | 否 |
| `invalid_transaction_relation` | 退款/冲销关系不合法 | 否 |
| `refund_exceeds_original` | 累计退款超限 | 否 |
| `allocation_exceeds_expense` | 活动分配超过支出 | 否 |
| `expectation_match_exceeds_amount` | 实收匹配超过预计金额 | 否 |
| `budget_period_closed` | 试图回溯发布已结束月份 | 否 |
| `duplicate_request_conflict` | 幂等键相同但载荷不同 | 否 |
| `concurrent_modification` | 版本或并发竞争失败 | 是，重读后重试 |
| `database_unavailable` | 数据库暂时不可用 | 是 |

可预见约束冲突必须映射到上述语义；未知持久化错误对外统一为安全的 `persistence_error`，内部只记录脱敏关联 ID。

### F12 事务与并发

- 每个命令在一个 `Session.begin()` 中完成幂等、加载/锁定、校验、全部业务行、审计和结果收据。
- 仓储只 `add/flush/query`，不得自行 `commit`。Session 不跨线程或并发任务共享。
- PostgreSQL 默认 `READ COMMITTED`；退款、预算发布和其他竞争资源使用 `SELECT FOR UPDATE` 或等价约束。
- 可变聚合使用 SQLAlchemy `version_id_col` 或等价的带版本条件更新。禁止绕过版本检查的 bulk update/delete。
- PostgreSQL 必须验证同键幂等竞争、并发退款、预算发布和版本冲突；SQLite 锁错误要稳定映射且不得半写入。

### F13 迁移与恢复

- 使用 Alembic，迁移按主数据、账本、活动、收入、预算、幂等/审计、目标方言加固的依赖顺序组织；具体可合并为较少 revision，但提交说明必须解释依赖。
- 空 SQLite 与空 PostgreSQL 必须能从 base 升到 head，重复 upgrade 无副作用；已有虚拟数据升级必须保持主键、金额和引用。
- 开发/测试支持降到 base 或删除测试数据库后重建。P1 不承诺生产数据库向下迁移；生产恢复口径为升级前备份、修复迁移或恢复备份。
- SQLite 表重建与 PostgreSQL 事务 DDL 的差异必须写入运行说明。禁止自动删除未知或版本不匹配的数据。

### F14 月度快照

输入为 `YYYY-MM`、`as_of` 和可选账户/分类过滤；月份区间按 Asia/Shanghai 的 `[月初, 下月月初)` 计算，再转换为 UTC 查询。

快照至少返回：

- `period`、`as_of`、`currency=CNY`、`budget_version_id`
- `income_minor`
- `gross_expense_minor`
- `refund_minor`（正数展示）
- `net_expense_minor = gross_expense_minor - refund_minor`
- `transfer_in_minor`、`transfer_out_minor`
- 按分类的毛支出、退款、净消耗、额度和剩余额度
- 每个账户的期初余额、期间流入、期间流出、期末余额
- `expected_income_minor` 与 `received_against_expectation_minor`，与实际收入字段分开

退款进入退款发生月；转账不进入收入或支出；模板和预计项不进入实际账目。结果排序必须稳定。优先使用一条确定性查询；若需要多查询，PostgreSQL 使用只读 `REPEATABLE READ` 保持同一快照。

### F15 延后范围

- 代付、报销、分期、应收款/负债正式模型均不进入 P1-B3。
- B3 不创建 `reimbursement_claim`，不增加临时类型，也不把这些场景伪装成收入、支出或退款。
- C3 的 `DEC-01..DEC-06` 保持“不适用（有冻结依据）/未执行”，后续独立阶段重新设计并冻结。

## 4. Python 命令服务

B3 至少提供可测试的应用服务入口，名称可以小幅调整，但能力和参数语义必须保持：

- 账户与分类：创建、归档、查询。
- 账本：记录期初余额、收入、支出、转账、退款和冲销。
- 活动：创建/修订模板、记录/取消实际活动、分配支出。
- 收入安排：创建/修订安排、生成预计到账、匹配实际收入。
- 预算：创建计划、发布月度版本、读取历史版本。
- 查询：账户余额、交易明细和确定性月度快照。

所有写命令使用 Pydantic DTO，并返回稳定业务 ID、`replayed` 和必要版本信息。领域对象和仓储不依赖 FastAPI。

## 5. PostgreSQL 平衡保护

B3 必须同时提供：

1. 服务层在 flush 前验证每笔交易至少两条、非零、同币种、目标形状合法且合计为零。
2. PostgreSQL 延迟到事务提交时检查的约束触发器或等价数据库机制，阻止绕过服务层写入不平衡交易。

SQLite 只要求服务层保护和可执行负向测试；差异必须在运行说明和 C4 报告中明确。

## 6. 执行方测试与独立测试

### P1-B3 执行方必须交付

- `tests/finance/` 下的单元、组件、仓储和 SQLite 迁移/冒烟测试。
- 覆盖正常收入、支出、转账、退款、活动分配、收入安排、预算版本、幂等、事务回滚和月度快照。
- 覆盖冻结错误码以及金额、浮点拒绝、归档资源、版本冲突的代表性负向路径。
- 如本机具备 PostgreSQL 环境，运行并记录执行方 PostgreSQL 冒烟；没有环境时如实标记，不能伪造通过。

执行方不得修改 `tests/independent/`、C3 矩阵或未来 C4 报告。自测通过只把 B3 提交为 `review`。

### P1-C4 独立测试

测试智能体根据 C3 矩阵建立独立用例，单独统计执行方测试复跑与独立案例。所有 P0 案例在适用数据库执行；PostgreSQL 必测项不能由 SQLite 替代。只有 C4 给出独立结论、总控核对后，B3 才能为 `complete`。

## 7. 文件所有权

P1-B3 执行智能体可以修改：

- `src/wife_system/finance/**`
- `migrations/**`、`alembic.ini`
- `tests/finance/**`
- `pyproject.toml` 及项目依赖锁定文件
- `compose.yaml`（仅用于本地 PostgreSQL 测试，若需要）
- `docs/b3-data-running.md`
- `docs/coordination/agents/executor.md`

只读：本冻结文档、D3、C3、项目规划和现有独立测试。禁止修改其他角色日志、总览、控制文件、OpenClaw/微信配置、现有 `tests/independent/**` 和 `integrations/openclaw/**`。

## 8. B3 完成门槛

执行智能体只有在以下条件全部满足时才能提交 `review`：

1. 迁移、模型、仓储、业务服务、查询和运行说明均已落盘。
2. 空 SQLite 从 base 到 head 成功，代表性开发重建成功。
3. 执行方全部测试通过；依赖检查和 Python 编译检查通过。
4. 虚拟数据完成收入、支出、转账、退款、活动、收入预计、预算和快照纵向路径。
5. 重复来源不重复入账，冲突载荷稳定失败，事务注入失败无半写入。
6. 未验证的 PostgreSQL 行为和限制逐项列出。
7. 没有真实账目、账号、密钥、原始聊天或未脱敏日志进入仓库。

完成后停止，不自动启动 C4、D4、Markdown 导入、Agent 工具或前端开发。
