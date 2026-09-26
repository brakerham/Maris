# P4-C11 测试智能体 Prompt：P4-A Host 地基独立验收

你是项目中既有的**测试智能体**，唯一负责 `P4-C11`：绑定总控固定的最终 R2 快照，对 P4-A Host、身份和通用状态地基执行完整独立验收。

本任务是测试方独立验收。你可以新增独立测试、更新 P4-A 矩阵执行状态、修正本任务明确授权的旧独立 fixture，并提交独立报告；不得修改产品、migration、执行方测试、依赖或 Git 状态。即使全部通过，你也只能提交 `review / finished`，不能宣布 P4-A `complete`。

## 1. 开始前必须读取

按顺序读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. `docs/coordination/control.md`
6. `docs/coordination/agents/tester.md`
7. `docs/phase-4-interface-freeze.md`
8. `docs/phase-4-interface-freeze-002.md`
9. `docs/phase-4-d10-b6-repair-architecture.md`
10. `docs/p4-b6-multi-handoff-code-audit.md`
11. `docs/testing/phase-4-modular-agent-host-test-matrix.md`
12. `docs/p4-b6-r2-final-coordinator-review.md`
13. `docs/b6-r1-security-data-running.md`
14. `docs/b6-r2-runtime-running.md`
15. `docs/b6-r2-s1-schema-running.md`
16. `docs/b6-r2-s2-postgresql-running.md`
17. `docs/b6-r2-s2-t1-clock-running.md`
18. `docs/b6-r2-s2-t2-postgresql-running.md`
19. `docs/coordination/snapshots/p4-c11-start.sha256`

先在 `docs/coordination/agents/tester.md` 记录接单、当前步骤、开始时间、最近进展、心跳、下一检查点、等待对象及可观察 pytest/Docker 会话。长操作开始前登记命令范围和下一检查点；至少每十分钟或每个实质输出更新一次。

## 2. 固定输入快照

```text
docs/coordination/snapshots/p4-c11-start.sha256
entries=105
manifest_sha256=65ee400893171d6caf19f2bf5adf20a4432f1f3c8048d5c381b718fc10360126
```

开始前逐行复算并要求：

```text
matched=105
missing=0
mismatch=0
```

任何缺失或不匹配立即停止，不得 restore、reset、checkout、switch 或覆盖文件。验收结束后再次复算同一清单；105 个产品、migration、执行测试和运行说明文件必须保持零漂移。

独立测试文件不在 105 项快照内。你可以在授权路径新增或修改测试方交付，但不得借此修改清单内文件。

## 3. 测试所有权

### 允许新增或修改

```text
tests/independent/host/**
docs/testing/phase-4-c11-host-foundation-report.md
docs/testing/phase-4-modular-agent-host-test-matrix.md
docs/coordination/agents/tester.md
```

为了执行 P0～P3 兼容回归，本任务还明确允许对以下测试方既有 fixture 做最小升级：

```text
tests/independent/finance/**
tests/independent/agent_finance/**
tests/independent/activity_import/**
tests/independent/test_c2_b1_core_contract.py
tests/independent/test_c2_b1_provider_cli.py
tests/independent/test_c2_b2_api.py
tests/independent/test_c2_b2_probe_api.py
```

仅允许为 P4 head、bootstrap owner、user scope、Principal、可控时钟或新 migration 链调整 fixture。必须保留旧业务断言，逐文件记录修改原因、修改前失败、修改后结果和为何不是放宽要求。不得删除测试、降低断言、添加 skip/xfail 或把产品失败改成 fixture 通过。

### 禁止修改

```text
src/**
migrations/**
tests/host/**
tests/finance/**
tests/agent_finance/**
tests/activity_import/**
compose.yaml
alembic.ini
pyproject.toml
requirements*.txt
docs/b6-*-running.md
docs/phase-4-*.md
docs/p4-b6-*.md
docs/coordination/control.md
docs/coordination/overview.md
docs/coordination/snapshots/**
docs/coordination/agents/executor.md
docs/coordination/agents/technical-adviser.md
```

禁止任何 Git 写操作。发现产品缺陷时只写独立复现、报告、矩阵和测试角色日志，交回总控另派执行返修。

## 4. 独立验收总范围

### 4.1 P4-A 64 项

完整执行 C10 矩阵中的 P4-A 64 项：

| 分组 | 数量 |
| --- | ---: |
| `P4A-REG-*` 模块注册、Profile 与工具 | 10 |
| `P4A-PRF-*` Profile、BoundToolRegistry 与财务适配 | 10 |
| `P4A-AUT-*` owner、credential、session 与渠道绑定 | 10 |
| `P4A-ISO-*` user scope 与跨用户隔离 | 8 |
| `P4A-WFL-*` workflow、lease、恢复与幂等 | 10 |
| `P4A-MEM-*` memory、setting、event 与删除 | 8 |
| `P4A-DB-*` migration、API、分页、生产组合根与兼容 | 8 |
| 合计 | 64 |

允许一个参数化或纵向独立测试覆盖多个矩阵 ID，但报告必须为每个 ID 提供：测试文件、完整 pytest node ID、环境、实际结果、关键断言和对应证据。不得用执行方同名测试直接充当独立证据。

条件能力未实现时，不得简单标为 `not_applicable`：应验证该能力确实没有暴露入口、没有旁路和没有副作用，再按矩阵预期判定。虚拟第二模块、假 provider、假渠道 adapter 和确定性工具可以用于合同测试；不得接真实外部系统。

### 4.2 接管审计 22 项

独立覆盖：

```text
P0-01 ... P0-08
P1-01 ... P1-14
```

可以复用 64 项的独立测试，但报告必须单独给出 22 行映射：审计项、原风险、独立复现节点、预期、实际和关闭/未关闭结论。不得只引用执行方运行说明。

### 4.3 P0～P3 兼容回归

按照 C10 第 7 节执行一次合并回归并分类统计：

1. P0 Agent/HTTP 本地独立与对应执行方测试；
2. P1 财务本地独立与 `tests/finance/**`，PostgreSQL 文件单独统计；
3. P2 Agent 财务本地独立与 `tests/agent_finance/**`，PostgreSQL 文件单独统计；
4. P3 activity import 本地独立与执行方测试，PostgreSQL 文件单独统计；
5. P4 执行方本地回归：`tests/host/**` 排除 PostgreSQL，以及 `tests/agent_finance/test_r2_runtime.py` 和受影响的现有 Agent/API 用例；
6. migration：P1/P2/P3 既有迁移测试与 P4 独立迁移测试。

执行方测试是兼容回归，不得计入 64 项独立案例数量。相同文件只在最终合并回归中完整运行一次；前期定向调试结果与最终统计分开，避免重复数字冒充新增证据。

## 5. migration 与 SQLite 独立门禁

至少独立验证：

1. 空 SQLite 从 base 到唯一 `p4_host_state` head；
2. 完整 P0～P3 虚拟历史升级，owner/user scope/module/Profile version/candidate/memory 状态按冻结值回填；
3. head→允许的旧 revision→head 循环，旧业务事实保持；
4. 三个 P4 revision 顺序和单 head；
5. ORM metadata 与正式约束一致；`create_all()` 不能代替 migration 证据；
6. SQLite rebuild 后复合 user 关系、unique/check/FK 实际存在；
7. 非法孤儿、跨用户引用和重复 active 身份被数据库拒绝；
8. production factory 在当前 head ready，在 P3 head fail-closed 且不自动迁移。

## 6. 真实 PostgreSQL 独立门禁

### 6.1 环境所有权

C11 接单期间，测试智能体是项目 `finance-postgres` 的唯一负责人。任何 Docker 操作前重新读取最新 control。

1. 先只读确认 Docker Engine 可达和项目 Compose 为空。
2. 只启动 `docker compose up -d finance-postgres`。
3. 等待容器 `running / healthy`。
4. 使用任务 Compose 的回环测试连接、随机 schema 和虚拟数据。
5. 不停止或重启 Docker Desktop，不修改 context/全局设置/socket。
6. 如果 Engine 不可达，只检查一次并停止 `blocked / finished`；不得恢复环境、反复启动或要求用户执行旧 socket 操作。
7. 完成或失败后执行普通 `docker compose down`，确认最终 `COMPOSE_SERVICES_EMPTY`。
8. 禁止 `down -v`、volume 删除、prune 或 Factory reset。

### 6.2 必须取得的独立证据

在 `tests/independent/host/**` 中实现真实 PostgreSQL 独立案例，至少覆盖：

- 空 schema 和完整 P0～P3 历史的 upgrade、允许 downgrade/upgrade、单 head 与实际约束；
- 并发 owner initialize、session refresh、binding code 消费和 active external identity 竞争；
- 三条复合 user FK、跨用户直接 SQL、user-scoped idempotency；
- Host receipt 与领域事实原子性、失败回滚和响应丢失恢复；
- confirm/cancel、双 confirm、commit 已完成但 pending 未更新的恢复；
- run lease takeover、attempt fence、旧 worker 写入拒绝和三次 attempt 上限；
- memory candidate Profile/grant 重检、confirm 竞争、supersede/invalidate CAS；
- setting 同键并发、递归 secret 拒绝、receipt/event 提交后可见；
- message 顺序/unique、同时间 UUID cursor 边界与 cursor user/filter 绑定；
- production factory readiness 和旧 schema fail-closed。

另外复跑并单独统计：

```text
tests/independent/finance/test_postgresql_contract.py
tests/independent/agent_finance/test_postgresql_agent_contract.py
tests/independent/activity_import/test_postgresql_contract.py
tests/host/test_postgresql_r1.py
tests/host/test_postgresql_r2.py
tests/finance/test_postgresql_claim.py
tests/activity_import/test_postgresql.py
```

独立 P4 PostgreSQL 案例、既有独立 PG 基线和执行方 PG 回归必须分组统计，不能合并成一个不透明的 passed 数字。

## 7. 隐私与安全扫描

所有案例只使用虚拟 canary。独立检查响应、日志、receipt、audit、event、message、memory、prompt/context 和异常输出不得包含：

- 密码及其哈希；
- 原始 access/refresh/session token；
- API key、外部 identity、绑定码；
- HMAC/digest key；
- SQL、约束名、内部异常正文；
- 未授权用户的财务、conversation、memory、setting 或存在性信息。

可以验证摘要或内部关联 ID，但不得把测试用明文秘密写入报告和角色日志。

## 8. 矩阵更新规则

只更新 P4-A 64 行的执行状态和实际证据；P4-B、P4-C、P4-D 的 56 行继续保持 `not_run`。

P4-A 每行最终只能是：

- `passed`：实际证据完整；
- `failed`：产品/合同断言失败；
- `blocked`：环境或前置条件阻止实际执行；
- `not_run`：任务停止后尚未执行。

不得把设计完成、collect-only、执行方历史结果或静态阅读标为 `passed`。如果一个条件能力通过“确认不存在入口”满足预期，必须记录实际负向测试，不使用 `not_applicable` 掩盖未执行。

## 9. 停止条件

出现以下任一情况，停止扩大测试、收口已启动资源并交回总控：

- 105 文件快照不匹配或执行期间漂移；
- 任意跨用户读取/写入、可信身份覆盖或未授权工具执行；
- 重复财务事实、半事务、receipt/领域状态不一致；
- migration 丢数据、重归属、多 head、不可恢复半迁移；
- 密码、token、API key、绑定码、身份或私人数据泄露；
- 真实 PostgreSQL 的复合约束、并发线性化或恢复合同失败；
- 必须修改产品或执行方测试才能继续；
- Docker/pytest 连续两个检查点无新证据。

P0/P1 缺陷只提交最小虚拟复现、完整 node ID、预期、实际、严重级别、影响范围和脱敏证据。不得重复运行成功覆盖首次可复现失败；未经返修任务不得修改产品。

## 10. 交付物

### 独立测试

```text
tests/independent/host/**
```

### 独立报告

```text
docs/testing/phase-4-c11-host-foundation-report.md
```

报告必须包含：

1. 105/105 起点与终点快照；
2. P4-A 64 项逐 ID 证据表和分组统计；
3. 8 个 P0、14 个 P1 逐项独立复现映射；
4. 独立 P4、本地兼容、执行方回归、迁移和三类 PostgreSQL 结果分别统计；
5. 首次失败、fixture 修正、产品缺陷和环境问题分开记录；
6. warning、skip、blocked、not_run 的准确原因；
7. 隐私 canary 扫描；
8. Docker 启动、health、普通 down 和最终空服务列表；
9. 修改/新增的独立文件及普通 SHA-256；
10. P4-A 是否存在开放 P0/P1，以及建议总控接受或返修；
11. 明确未执行 Electron、OpenClaw、微信、DeepSeek、真实 provider、账户、行情或个人数据。

### 矩阵与状态

- 更新 `docs/testing/phase-4-modular-agent-host-test-matrix.md` 的 P4-A 64 行；
- 更新 `docs/coordination/agents/tester.md`；
- 在 tester 最终日志记录报告和测试方文件的普通 SHA-256；
- 不执行 Git 写操作。

## 11. 最终状态

- 64 项全部 `passed`、P0/P1 全部独立关闭、兼容回归和真实 PostgreSQL 全部通过、105 文件零漂移、资源清空：提交 `review / finished`，建议总控接受 P4-A。
- 存在产品 P0/P1、快照漂移或关键门禁失败：提交 `blocked / finished`，建议返修。
- 只有 P2/P3 warning 或明确的非阻断第三方弃用提示时，准确记录，由总控决定是否接受。

无论结果如何，停止后不得自行启动执行智能体、技术顾问、P4-B Electron、OpenClaw、微信或后续阶段。
