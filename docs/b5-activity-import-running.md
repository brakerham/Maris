# P3-B5 活动 Markdown 导入运行与交接

- 角色：执行智能体
- 任务：`P3-B5-R1`（`P3-C9-PG-001` 最小返修）
- 交付状态：`review`（执行方自测；未作独立验收）
- 接口依据：`P3-IF-001`
- 控制版本：`2026-09-19T14:59:01+08:00`

## 输入门禁

开始修改前按原始文件字节独立计算三份绑定输入，结果与任务卡一致：

```text
P3-IF-001-SHA256:8912359d1e4748fe1b0e537c33d6e59481dba32ac573a7bc82560c4f25e8b9cd
P3-D7-SHA256:9625009fa8b5e9e5ddd4f1fff805a437e97533a3c6e9d452cf3b84def6ca59e0
P3-C8-SHA256:5a4eec3dcba2d1d446f66cb02fa701de6b6bae5744f4083e5cbebfcc3e176da7
```

P3-B5-R1 开始修改前还独立复算旧 B5 的 22 文件快照和 C9 报告原始字节摘要，均与返修任务卡一致：

```text
P3-B5-SHA256:9fb36c653d20ff14f85ad9667de454900cca0c6e3ead17c2619df11fb7f63d6e
P3-C9-REPORT-SHA256:d0b2189ec65d477a6fcefa9790898b5840d4f330f2ed713a6684346b8fada83b
```

## 实际架构和数据流

```text
可信 FastAPI identity(owner/channel/permissions)
  + application/json(markdown, optional source_label)
  + Idempotency-Key
    -> 96 KiB HTTP 边界、重复 JSON key、UTF-8、严格 Pydantic 校验
    -> 受限离线 parser（不渲染、不读路径、不联网、不执行文本）
    -> 内容 HMAC + 独立候选块 HMAC
    -> 单事务写 command_receipt + batch + candidates
    -> GET 按 owner 恢复持久预览
    -> commit 复验完整候选集合、warning、摘要、动作和目标版本
    -> 锁批次及目标模板
    -> FinanceService Session 级 create/revise 原语
    -> 单事务写模板、追加修订、审计、候选结果、批次和回执
```

解析器实现 `activity-md-v1`：统一一个开头 BOM 与 CRLF/CR，保留正文 Unicode 语义；识别冻结的 H1/H2 和三种金额句式；金额仅用十进制文本转整数分。精确金额写三列相同值，范围保留上下界且兼容单值为空，无金额三列均空。代码、HTML、链接、路径、深层标题、组合字段和其他自由文本只形成结构化 issue，不会执行或落库存原文。

预览根据规范名及全部历史修订判定 `create/revise/unchanged/conflict/unresolved`。同批规范名重复、归档命中、历史名复用或多目标均为 `conflict`。提交只接受预览中持久字段，每个候选必须恰好有一个 `accept/skip`；warning code 集合必须完全一致。全部 skip 合法。

持久幂等复用 P1 `command_receipt`，但原始 key 只作为瞬时输入，数据库只保存带可信 owner/channel 操作域的 HMAC 摘要和规范载荷指纹。同键同载荷重放原结果，同键异载荷冲突。日志只记录 request/batch ID、解析器版本、摘要前12位、候选/动作/接受数、错误码、耗时和 replayed；不记录 Markdown、名称、source label、完整摘要、key、链接、路径或数据库诊断正文。

## 模型、迁移与兼容行为

唯一新迁移为 `c82d7a4f901e`，直接从 `7f3e2d1c9a4b` 继续。它在任何 DDL 前读取既有模板当前修订，计算 NFC、Unicode 空白折叠和 casefold 规范名；缺失当前修订、非法旧金额或规范名重复会安全失败，不自动合并。

迁移增加：

- `activity_template.name_normalized` 非空全局唯一，归档仍占名；
- `activity_template_revision.reference_min_minor/reference_max_minor/source_import_candidate_id`；
- `activity_import_batch` 和 `activity_import_candidate`，包含 owner、状态、HMAC、来源行号、结构化 issue、选择与结果；
- 金额形状、SQLite INTEGER storage、状态、目标、决定、唯一性和来源外键约束。

旧 `reference_minor` 非空行原值不变并回填上下界；历史模板、修订、发生记录 ID/版本/引用不变。现有公开 `create_activity_template` / `revise_activity_template` 仍接受精确金额，并通过与导入提交相同的 Session 级原语同时写三列。P1 旧迁移测试改用旧表结构 SQL 准备历史虚拟活动，避免当前 ORM 向旧 schema 写 P3 列；原验证意图和断言保留。P2 migration head 断言更新到新 head。

P3-B5-R1 只把 `activity_template_revision.source_import_candidate_id` 的显式外键名在 upgrade 和 downgrade 中同步冻结为 `fk_activity_template_revision_import_candidate`。新名称为 46 字符，低于 PostgreSQL 的 63 字符上限；revision ID、表列、删除规则、约束语义和迁移顺序均未改变。执行方回归会枚举 migration 中未经过命名约定包装的显式标识符，验证长度上限，并确认 upgrade/downgrade 都引用同一个模块常量。

## HTTP 接口

- `POST /api/v1/activity-imports/preview`：首次 `201`，同键重放 `200`。
- `GET /api/v1/activity-imports/{batch_id}`：只按可信 owner 查询；不存在和 owner 不符统一 `404 batch_not_found`。
- `POST /api/v1/activity-imports/{batch_id}/commit`：首次和同键重放均 `200`；成功批次换新 key 再提交通知 `import_already_committed`。

两个 POST 只接受 UTF-8 `application/json`、单个可打印 ASCII `Idempotency-Key`（去首尾空白后1..256）和严格 `extra=forbid` DTO。HTTP body 最大96 KiB，规范 Markdown 最大64 KiB；超限在解析和数据库写入前拒绝。错误统一为 `{request_id,error:{code,message,retryable}}`。

## 执行方自测

只使用虚拟活动和临时数据库。没有运行 `tests/independent/**`，没有启动 P3-C9。

P3-B5-R1 最终文件版本的定向结果：

```text
tests/activity_import/test_migration.py
5 passed in 2.00s

tests/activity_import
144 passed, 9 skipped, 1 warning in 8.72s

tests/activity_import/test_postgresql.py（设置项目测试 PostgreSQL URL）
9 passed in 1.57s

tests/agent_finance/test_migration.py tests/finance/test_migrations.py
4 passed in 1.58s
```

本地整套中的 9 个 skip 只代表未给该次本地命令设置 PostgreSQL 地址；同一最终文件版本随后在健康的 PostgreSQL 17.6 临时服务上单独运行该文件，九项全部进入业务断言并通过，无 skip 或 setup error。既有本地 143 项加新增标识符回归后总数为 144。

1. 初始受影响基线：

   ```text
   .venv\Scripts\python.exe -m pytest -o addopts='' -p no:cacheprovider --basetemp=scratch/p3-b5-baseline tests/finance tests/agent_finance tests/test_probe_api.py tests/test_agent_loop.py tests/test_c2_regressions.py --tb=short -q
   92 passed, 4 skipped, 1 warning in 15.23s
   ```

2. 纯解析与 DTO 首个阶段门禁：`120 passed in 0.21s`。后续增加两项路径标题边界，纳入最终 P3 结果。

3. SQLite P3 最终测试：

   ```text
   .venv\Scripts\python.exe -m pytest -o addopts='' -p no:cacheprovider --basetemp=scratch/p3-final-local tests/activity_import --ignore=tests/activity_import/test_postgresql.py --tb=short -q
   143 passed, 1 warning in 9.40s
   ```

4. 受影响 finance、agent finance 与现有 API 最终回归：

   ```text
   .venv\Scripts\python.exe -m pytest -o addopts='' -p no:cacheprovider --basetemp=scratch/p3-final-regression tests/finance tests/agent_finance tests/test_probe_api.py tests/test_agent_loop.py tests/test_c2_regressions.py --tb=short -q
   92 passed, 4 skipped, 1 warning in 13.85s
   ```

5. 静态与依赖：`compileall -q` 退出0；`pip check` 返回 `No broken requirements found.`。唯一 warning 是既有 Starlette/AnyIO 类型别名弃用提示。

## PostgreSQL 专项与清理状态

执行方文件 `tests/activity_import/test_postgresql.py` 已实现冻结的九类 PostgreSQL 场景：预览同键并发、提交同键并发、同批异键并发、异批同名 create 竞争、stale/归档、整批故障回滚、数据库约束、空库/已有数据升级、响应丢失恢复。

P3-B5-R1 在每次 Docker 操作前重新读取 `control.md`，版本仍为 `2026-09-19T14:59:01+08:00`，执行方仍是唯一启停负责人。只启动 `finance-postgres`，健康状态为 `healthy`；测试使用项目测试凭据、随机 schema 和虚拟数据。最终文件版本实际结果为 `9 passed in 1.57s`，没有收集替代、skip 或 setup error，原空 schema migration 已通过。

结束后执行普通 `docker compose down`，容器与项目网络均正常移除；随后 `docker compose ps --format json` 退出 0 且无输出，服务列表为空。未使用 `down -v`，未删除 volume、prune、重置数据库、启动其他服务或修改 Docker 全局配置。

## 未验证项和已知限制

- 本交付是执行方自测，只能进入 `review`；P3-C9-R2 独立复验尚未运行，也未据执行方九项通过宣称独立验收。
- P3 不含真实文件选择器、UI、DeepSeek、OpenClaw、微信、活动发生自动创建、财务记账、预算、收入、提醒、组合活动或保留期清理。
- 已提交和未提交批次按冻结要求持续保留；导出、删除及保留期应另立隐私任务。

## 文件快照

摘要清单只覆盖实现、迁移、DTO/API、执行方测试及直接改变的 P1/P2 文件。运行说明和角色日志包含摘要本身，故不纳入以避免自引用。算法为：按仓库相对路径排序，记录每个文件 SHA-256；再对每行 `path<TAB>sha256<LF>` 拼接后的 UTF-8 字节计算总 SHA-256。

```text
migrations/versions/c82d7a4f901e_add_activity_import.py	e0703c5a87f792a5e7c4414192aefd1a6ed00a328094f18dc0b4db26e9e24a0d
src/wife_system/activity_import/__init__.py	c07e7c4533114149d1ecc0e7c4d7d50ccbcbc159f331d1e6c4dd1d4c91403b0c
src/wife_system/activity_import/context.py	ee68eb9bd2159b059d38e3ca6b1c704863c7e1d10a27bb2c4efe9a2bb849dd81
src/wife_system/activity_import/errors.py	3b48cbb882017754c0e52327e2d856d78cdb32adf3662f957b8a641dac7779b1
src/wife_system/activity_import/parser.py	12b003b5b47469c1fc3badd9a8396406801651786b984674d3566b9b0c275a05
src/wife_system/activity_import/repository.py	9ff5894f540e93bccfcd6b12a36e1adefde7f140d44686b517369d66bdb2a44e
src/wife_system/activity_import/schemas.py	ecfc8ccd748557090e8bdf3fde3ae7d0af6c6147457d86f3f52c62d1c5739ff7
src/wife_system/activity_import/service.py	c916d533980818f45f1ff66e3cc9af497657e45d4fe50a5da1524a2ec3b3909f
src/wife_system/api/activity_import_routes.py	d93aae22d689308a8b98b3f8c8982eacd5c62c086d83dc72b7d7054c2ea8463b
src/wife_system/api/app.py	9973fdcd18d3f8fbe6edc2183d2d6502c4201ab4c79a1283de08a2a41162a927
src/wife_system/finance/models.py	1e07d205955635afb9bc5b2ca4ab1b79eda44fee7aaa8e73854b604ff21156de
src/wife_system/finance/service.py	3a83d236106e26093ee5af0730bf7595b1280505beb9e977cf7d6ea28b163890
tests/activity_import/__init__.py	f371abdeb05764ed0f4c2403c7a259c87f05f0885c663b39f3dbf501b9d1b814
tests/activity_import/test_api.py	a9d59c3401328148d87bca8eba607ea1c193155b17cf28298e7f1dfe49f04b22
tests/activity_import/test_migration.py	af4c4e025948d1dea7c5433224e48bed0e746610f961d7ce9d6ff04685f5a7a9
tests/activity_import/test_parser.py	d4d8266fb7838a7b0cef9b6ad0e1e2bfc4d84bc32d97d8590120a6a74193da4b
tests/activity_import/test_postgresql.py	b8f4c2fb0a5fbc69ae46d76908c395417e4fe0784d5ffa967ca220a00515e699
tests/activity_import/test_schemas.py	417e99ab913f747cf4b42be8d25a91997023930e6c4b7fad3506639c3697c592
tests/activity_import/test_service.py	b317fd1759086a767b28678fd5efebda677ee2dbd6139ff3c32b9a8495d3822e
tests/agent_finance/test_migration.py	5754089dea4f74a12d39e46829deaa7cf6cc7491ae6fff31698d08358b8f8fef
tests/finance/test_migrations.py	ffe6d9d3bc9699702e33e0d1b73a8c9fbb4d21f4a2eb6d082f1d179259afbb8c
tests/finance/test_service.py	7efa88741d73ec89ad96edb55d6da650388433d568e581cff90e38f45dee6753
P3-B5-R1-SHA256:fb46b8fa4957c93bfd8f971b1fd987e45dd4779e8d6eac2907660fa2f1fef53c
```

## C9-R2 进入说明

总控核对有序文件清单及总摘要无漂移后，才能派发 P3-C9-R2。测试智能体应先独立重算快照，再按返修范围执行独立复验；执行方在 `review` 停止，不自行启动验收或修改 Git。
