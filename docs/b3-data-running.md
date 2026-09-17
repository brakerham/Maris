# P1-B3 财务数据底座运行说明

- 任务：`P1-B3`
- 接口依据：`P1-IF-001`
- 当前交付状态：P1-B3-R1 执行方返修已提交 `review`；等待 C4 定向复验
- 数据边界：示例和测试全部是虚拟数据，不包含真实账目、账号、消息或密钥

## 1. 已实现结构

`src/wife_system/finance/` 是不依赖 FastAPI、大模型、OpenClaw 和微信的同步 Python 数据层：

- `models.py`：17 张 SQLAlchemy 2.x 类型化 ORM 表，包含稳定命名的主键、外键、唯一约束、检查约束、索引和版本列。
- `schemas.py`：Pydantic 写命令和结果；金额字段只接受字符串，额外字段被拒绝。
- `money.py`：CNY 十进制字符串到整数分、范围校验和 `ROUND_HALF_UP` 派生舍入。
- `repositories.py`：只查询、添加和 `flush` 的持久化原语，不提交事务。
- `service.py`：一个命令一个 `Session.begin()`；实现账户/分类、期初、收入、支出、转账、退款、冲销、活动、收入安排、预算、余额、交易列表和月度快照。
- `errors.py`：稳定且不暴露 SQL、驱动参数或私人载荷的业务错误。

账本只保存交易头和平衡分录，不保存可写账户余额。收入和支出既有单分类命令，也有同一交易内的多分类拆分命令；转账和退款都由受限分录角色表达。已入账事实没有普通修改或删除入口。账户、分类、活动模板、收入安排和预算计划使用归档与乐观版本。

## 2. 安装与锁定依赖

在项目根目录使用项目虚拟环境：

```powershell
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m pip check
```

`pyproject.toml` 保存支持范围；`requirements-dev.lock` 保存本轮 Python 3.14.7 开发环境的精确版本。主要新增版本为 SQLAlchemy 2.0.54、Alembic 1.20.0、psycopg 3.3.5。

## 3. SQLite 迁移与开发重建

默认 `alembic.ini` 使用项目根目录的 `finance.db`。创建或升级：

```powershell
.venv\Scripts\alembic.exe upgrade head
.venv\Scripts\alembic.exe current
```

重复执行 `upgrade head` 是无操作。开发或测试数据库可以降到 base 再重建：

```powershell
.venv\Scripts\alembic.exe downgrade base
.venv\Scripts\alembic.exe upgrade head
```

也可以设置 `FINANCE_DATABASE_URL` 指向专用测试库。不要对未知或版本不匹配的数据文件自动删除或重建。SQLite 的外键通过每条应用连接上的 `PRAGMA foreign_keys=ON` 启用；Alembic 在需要改表时使用 batch 表重建。SQLite DDL 不具备 PostgreSQL 的同等事务语义，因此它只用于开发和快速反馈。

生产恢复不承诺向下迁移。正式数据应在升级前备份，失败时采用修复迁移或恢复备份。

## 4. PostgreSQL 可复现入口

仓库的 `compose.yaml` 提供绑定在本机 `127.0.0.1:55432` 的临时 PostgreSQL 17.6 测试实例，数据目录使用 `tmpfs`。本机安装 Docker 后可运行：

```powershell
docker compose up -d finance-postgres
$env:FINANCE_DATABASE_URL = "postgresql+psycopg://wife_test:wife_test_only@127.0.0.1:55432/wife_finance_test"
.venv\Scripts\alembic.exe upgrade head
.venv\Scripts\alembic.exe current
```

结束后：

```powershell
docker compose down
```

首个 revision 对 PostgreSQL 创建两个 `DEFERRABLE INITIALLY DEFERRED` 约束触发器。它们在事务提交时校验每笔交易至少两条分录且合计为零，防止绕过服务层直接写入不平衡交易。执行方测试还会离线编译 PostgreSQL DDL，确认触发器语句存在。

当前机器没有 Docker 命令，也没有可用 PostgreSQL 连接，因此以下行为均为**未验证**：PostgreSQL 空库实际升级/降级、约束触发器实际提交行为、两个独立连接的幂等竞争、并发退款、并发预算发布、乐观锁竞争、`READ COMMITTED` 行锁、只读 `REPEATABLE READ` 快照、`timestamptz` 往返，以及重启/多 worker 后的持久幂等。SQLite 结果不替代这些结论。

## 5. 虚拟纵向示例

以下代码只使用虚拟名称和来源编号：

```python
from datetime import datetime
from zoneinfo import ZoneInfo

from wife_system.finance import FinanceService, IdempotencyKeys
from wife_system.finance.db import make_engine, make_session_factory
from wife_system.finance.schemas import CreateAccount, CreateCategory, RecordIncome

engine = make_engine("sqlite:///finance.db")
service = FinanceService(
    make_session_factory(engine),
    IdempotencyKeys({1: b"replace-with-a-managed-secret"}),
)

account = service.create_account(CreateAccount(
    source_system="virtual-demo",
    source_event_id="account-001",
    name="虚拟银行卡",
))
category = service.create_category(CreateCategory(
    source_system="virtual-demo",
    source_event_id="category-001",
    kind="income",
    name="虚拟收入",
))
income = service.record_income(RecordIncome(
    source_system="virtual-demo",
    source_event_id="income-001",
    account_id=account.result_id,
    category_id=category.result_id,
    amount="1000.00",
    occurred_at=datetime(2026, 9, 5, 12, tzinfo=ZoneInfo("Asia/Shanghai")),
))
```

同一 `source_system + source_event_id` 与等价载荷再次调用会返回相同 `result_id` 和 `replayed=true`。同键不同载荷返回 `duplicate_request_conflict`。原始来源编号不会落库；数据库只保存由版本化密钥计算的 HMAC-SHA-256 摘要。

## 6. 金额、比例和时间规则

- 外部金额是十进制字符串；`float`、科学计数法、空白和超过两位小数都被拒绝。
- 已入账、预算和预计金额使用 `BIGINT` 整数分，单值和聚合绝对值不超过 `999_999_999_999` 分。
- 退款按原支出分录比例拆分。先做整数向下分配，余分按支出分录 UUID 的字符串升序逐分补齐；这就是稳定余分顺序。
- 预测舍入使用 `Decimal` 的 `ROUND_HALF_UP`；入账金额不做静默舍入。
- 时间点转为 UTC 入库；自然月、收入日期和月度边界按 `Asia/Shanghai` 计算。
- 月度快照对 PostgreSQL 显式使用只读 `REPEATABLE READ`，避免多条汇总查询混合两个提交时点。

## 7. 幂等密钥轮换

`command_receipt` 永久保存 `key_version`、来源键摘要、请求指纹和首次结果，不保存原始来源事件编号。P1-B3 不提供在线轮换：轮换时必须暂停写入，在受控维护程序中用仍可读取的旧密钥和安全来源映射统一迁移历史摘要，验证唯一约束后切换当前 `key_version`，再恢复写入。直接更换密钥并继续写入会让同一个原始事件得到新的摘要，属于禁止操作。

## 8. 自测命令

```powershell
.venv\Scripts\python.exe -m pytest -o addopts="" tests/finance --tb=short
.venv\Scripts\python.exe -m pytest -o addopts="" --tb=short
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe -m compileall -q src tests migrations
```

`tests/finance/` 覆盖 SQLite 迁移/重建、迁移后纵向冒烟、PostgreSQL DDL 离线编译、金额精度、纵向账本、余额、重放与冲突、失败回滚、数据库故障安全映射、隐私日志、归档与版本、退款、冲销、活动分配、收入安排/预计匹配、预算版本和确定性月度快照。执行方结果只表示实现已具备独立测试条件；最终结论由 P1-C4 和总控给出。

## 9. 已知限制

- PostgreSQL 实际迁移、约束和并发证据尚未取得。
- P1 没有 FastAPI 财务端点、Agent 工具、Markdown 导入、微信流程或桌面界面。
- 代付、报销、分期、应收款和负债按 F15 延后，服务不会把它们伪装成收入、支出或退款。
- P1 只接受 CNY，不处理汇率或跨币种转账。
- 快照实时从不可变账本和版本表重算，没有持久化缓存。

## 10. 本轮执行证据与交接快照

- 执行方财务测试：`24 passed in 0.53s`。
- 项目全量回归：`167 passed, 1 warning in 8.37s`；唯一警告是既有 Starlette 1.6.0 对 AnyIO 别名的第三方弃用警告。
- `pip check`：`No broken requirements found.`
- `compileall -q src tests migrations`：退出码 0。
- SQLite：空库升级、重复升级、带虚拟纵向数据的运行、降到 base 后重建均通过；`alembic check` 无待生成升级操作。
- PostgreSQL：离线 DDL 编译通过；真实数据库行为仍按第 4 节列为未验证。

交给 P1-C4 的实现快照标识：

```text
P1-B3-SHA256:6a1127fd40dd3b1f66c0dc4fd9837cc03c9ceafc0398ca867bb595b686511580
```

该值覆盖 20 个文件：`alembic.ini`、`compose.yaml`、`pyproject.toml`、`requirements-dev.lock`，以及 `src/wife_system/finance/`、`migrations/`、`tests/finance/` 下除 `__pycache__`/`.pyc` 外的全部文件。算法按相对路径升序，依次写入 4 字节大端路径长度、UTF-8 路径、8 字节大端内容长度和原始文件字节，再计算整体 SHA-256。运行说明和角色日志不参与摘要，避免记录摘要产生自引用。

## 11. P1-B3-R1 限定返修

R1 只处理 C4-DATA-001～003，没有改变冻结接口或扩展产品范围。

### 11.1 累计退款分摊

退款不再把每次金额单独从零分摊。服务先读取原支出的正支出分录和所有既有退款，使用“既有累计退款 + 本次退款”计算新的累计比例目标，再减去各分类已经退款的金额，生成本次非零增量。余分顺序继续使用原支出分录 UUID 字符串升序。

这一变化保留退款总额、累计上限、幂等事务和 PostgreSQL 原交易行锁语义。两类各 1 分连续退款两次后各归零；三分类多次部分退款最终也与原分类金额逐项相等。若累计目标在极端比例下出现配额回摆，本次只分配正增量并按稳定顺序消耗本次金额，不产生负退款或零金额分录。

### 11.2 SQLite 金额存储类型

迁移链现在为：

```text
base -> bfc163b9b8e9 -> 1377551283d0 (head)
```

新 revision 没有改写首个 revision。SQLite 通过 batch 表重建，为以下 7 个 `_minor` 列增加存储类别检查：

- `transaction_entry.amount_minor`
- `activity_template_revision.reference_minor`（允许 `NULL`）
- `activity_entry_allocation.allocated_minor`
- `income_schedule_version.amount_minor`
- `income_expectation.expected_minor`
- `income_expectation_match.matched_minor`
- `budget_allocation.limit_minor`

约束要求 `typeof(column)='integer'`，因此会拒绝无法按 INTEGER affinity 保存的文本和 REAL。PostgreSQL 分支不生成 `typeof` 语句，继续依靠原有 `BIGINT` 类型；离线 PostgreSQL DDL 编译确认没有 SQLite 表达式。

已实际验证首个 revision 中带有账户、分类、收支、活动关联、收入安排/预计/匹配和预算的虚拟数据升级到新 head，主键、金额和引用保持；7 个金额列均直接拒绝文本 canary 和 `1.5`。空库 base→head、重复 upgrade、downgrade base→head 和 `alembic check` 也通过。

### 11.3 SQLite 时间点

应用写入 SQLite 前已经转为 UTC，但 SQLite 驱动读取 `DateTime(timezone=True)` 时会丢失 `tzinfo`。公开 DTO 映射现在把 naive 数据库时间按已保存的 UTC 语义恢复为 aware UTC；已有 aware 值则统一转换到 UTC。覆盖位置包括：

- `list_transactions().occurred_at`
- `list_accounts()` 的 `created_at`、`archived_at`
- `list_categories()` 的 `created_at`、`archived_at`
- `list_budget_versions().published_at`

`2026-09-01 00:30+08:00` 的交易会公开返回 `2026-08-31 16:30+00:00`，自然月边界仍按 Asia/Shanghai 计算。

### 11.4 R1 验证与交接

- 执行方财务测试：`28 passed in 1.00s`。
- C4-DATA-001～003 原失败节点只读定向诊断：`3 passed in 0.48s`。
- 独立 finance 扩大诊断：`67 passed, 1 failed, 8 skipped`；唯一失败是测试方把旧 Alembic head `bfc163b9b8e9` 写死，实际新 head 按 R1 要求为 `1377551283d0`。执行方未修改独立测试。
- 项目全量回归：`238 passed, 1 failed, 8 skipped, 1 warning in 22.23s`；唯一失败同上。排除这个待测试智能体更新的旧 head 断言后，结果为 `238 passed, 8 skipped, 1 deselected, 1 warning in 17.55s`。
- `pip check`：无破损；`compileall -q src tests migrations`：退出码 0；`git diff --check`：退出码 0。
- 真实 PostgreSQL 环境仍不可用；8 个 PostgreSQL 独立案例继续跳过，R1 没有安装 Docker/PostgreSQL 或连接未知数据库。

R1 交给测试智能体的实现快照为：

```text
P1-B3-R1-SHA256:751a78aadacf6317e2dafc711569322f3843051e1fae0ee41f11e4b91cfb29bf
```

摘要算法与第 10 节相同，覆盖文件增至 22 个；新增文件是第二个 migration 和 `tests/finance/test_r1_regressions.py`。
