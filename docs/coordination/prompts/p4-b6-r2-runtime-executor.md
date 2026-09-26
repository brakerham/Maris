# P4-B6-R2：Host/Agent 运行时与通用状态集成返修

## 角色与唯一目标

- 角色：用户侧边栏中既有的“执行智能体”任务
- 任务编号：`P4-B6-R2`
- 唯一目标：从总控固定的 R1/F1 精确快照开始，关闭剩余 5 个 P0 和 7 个 P1，使 Host 真正控制 Agent 的启动、恢复、工具、记忆、设置、事件、分页和生产组合根
- 交付状态：只能到 `review`；不得启动 C11、桌面端、真实微信或财富管理业务，不得宣布 P4-A `complete`

开始前必须按顺序读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. `docs/coordination/control.md`
6. `docs/coordination/agents/executor.md`
7. 本任务卡
8. `docs/phase-4-interface-freeze.md`
9. `docs/phase-4-interface-freeze-002.md`
10. `docs/p4-b6-multi-handoff-code-audit.md`
11. `docs/phase-4-d10-b6-repair-architecture.md`
12. `docs/p4-b6-r1-coordinator-review.md`
13. `docs/p4-b6-r1-f1-coordinator-review.md`
14. `docs/b6-r1-security-data-running.md`
15. `docs/testing/phase-4-modular-agent-host-test-matrix.md`
16. `docs/coordination/snapshots/p4-b6-r2-start.sha256`

开始修改前重读最新 control，确认你是 R2 的唯一实现负责人，技术顾问和测试智能体均已停止，并确认 Docker Desktop 已由用户重启后恢复正常。

## 固定输入与停止门禁

- R2 起点清单：`docs/coordination/snapshots/p4-b6-r2-start.sha256`
- 文件数：`96`
- 起点有序总摘要：

```text
7a80e083b0534c0f2547d859276f9c910b94a912b9b057ef95f8dbc9a74f3632
```

- R1/F1 22 文件安全切片摘要：

```text
e690882a291b8ec0210971d3bbed1f6da2252368cd9afff5213ff33798b87976
```

起点摘要算法：对清单中每个仓库相对 POSIX path 计算小写 SHA-256；按路径排序，拼接 `path<TAB>sha256<LF>`，再对拼接后的 UTF-8 字节计算 SHA-256。

任何修改前逐项重算 96 文件快照。若不匹配，立即停止并列出变化、缺失或新增的相关文件；不得 restore、reset、checkout、覆盖或猜测哪个版本正确。

三个 P4 migration 已由 R1 冻结。R2 若发现实现必须新增字段、索引、约束或 revision，停止冲突范围并提交“所需 schema、原因、替代方案、受影响测试”，交回总控裁定；不得自行修改 migration。

## 必须关闭的问题

```text
P0-04 cancel/confirm 竞争可形成“已取消但账本已写”
P0-05 run lease 接管只增加 attempt，不恢复执行
P0-06 模块禁用、失权或 Profile 变化后旧候选仍可提交
P0-07 普通模块设置可保存 API key/token/password 等秘密
P0-08 memory candidate 没有绑定提出它的 Profile grant 与固定 target

P1-06 ToolCatalog/BoundToolRegistry 没有进入真实 Agent 链
P1-07 Profile prompt、conversation、messages、confirmed memory 没有进入真实 Agent
P1-08 provider/tool 只在 runner 完成后续租，旧 attempt 没有完整 fence
P1-09 四类 post-commit event 与 subscriber wiring 不完整
P1-10 memory supersede/invalidate/delete 状态机与 CAS 行为缺失
P1-11 production app/factory 没有装配 Host/Agent/import
P1-12 conversations/messages/memory candidates 没有统一 Page{items,next_cursor}
```

不得把这些问题降级为后续优化。发现冻结合同互相矛盾，停止相应范围并提交最小复现和裁定问题。

## 必须实现

### 1. pending commit 所有权与恢复

- `claim_commit` 返回带 pending ID、version、commit attempt 和 lease 的所有权结果，不能再只返回裸布尔值。
- 只有成功取得 `committing` 所有权的请求可以首次调用 FinanceService。
- CAS 失败必须重读真实状态；`committing` 未过期时，confirm/cancel 返回 409 `commit_in_progress`；`cancelled`、`expired`、`committed` 按 IF-002 状态表返回。
- 领域幂等键固定为 `pending:{pending_action_id}:commit`。领域提交后、pending 完成前崩溃时，恢复者用同一键重放领域结果，并以新 attempt/version fence 标记 committed。
- 旧 worker 的完成写必须得到 `run_lease_lost` 或 CAS 失败，不能覆盖新 owner。
- cancelled run 保持 `cancelled`，不得伪装成 success，不产生财务事实。

### 2. run takeover、续租与 deadline

- 过期 running run 被成功 acquire 后必须重建输入并继续 provider/tool，不得 replay early-return。
- start、resume、takeover 共用一个 `ExecutionPlanCompiler` 和同一种不可变 `CompiledExecutionPlan`。
- provider 前后、每个 tool 前后、最终保存前都续租并检查 `(user_id, run_id, attempt_no, status=running)` fence。
- Profile 上限只能收紧冻结的 provider 15 秒、tool 10 秒和 60 秒 lease；tool timeout 采用 cooperative deadline，不能假装已回滚已经提交的数据库事实。
- 第三次 attempt 耗尽时，以当前 fence 保存稳定 `run_attempts_exhausted`；旧 worker 不得写 answer、message、pending link 或 terminal event。

### 3. Host 真正控制 Agent

- compiled plan 至少绑定 principal/session/device/channel/permissions、module/version/enabled revision、Profile/version/system prompt、BoundToolRegistry、memory grants、4/8/1 limits、conversation、run/attempt fence 和 action schema version。
- 每个 tool 的 schema 可见性和 invoke 都经过 BoundToolRegistry；不可见、猜名、禁用或失权统一为持久 run error `tool_not_allowed`，零 handler/领域副作用。
- resume 在读取 pending 后、claim commit 前重新编译并复查 module、Profile/version、principal permission、tool/action handler 和目标资源版本。
- provider 输入顺序固定为：Host 安全规则 → Profile prompt → 可信上下文 → 最多 8 条获准 confirmed memory → conversation history → 持久 tool facts → 当前消息。
- 当前用户消息与 run claim 同事务落库；assistant/tool/final 使用 Host 分配的 `(user_id, run_id, sequence)` 幂等写入。历史窗口最多最近 20 条且 UTF-8 总计不超过 64 KiB。
- terminal assistant message 与 run terminal state 按 attempt fence 同事务保存，commit 后才发布状态事件。

### 4. memory、setting 与 event

- memory proposal 固定 source module、target namespace、Profile ID/version；confirm DTO 不得改 target。
- propose 和 confirm 都在 service 边界复查 module enabled、Profile ownership/version、memory grant 和 principal 权限。`shared.confirmed` 也必须显式 grant 和用户确认。
- 实现 version CAS：active→superseded、active→invalidated、任意未删除状态→deleted tombstone；检索只返回 active、未过期且获 grant 的最多 8 条。
- setting 在 claim receipt/事务之前执行严格 JSON、finite number、8 KiB、递归 secret key 归一化拒绝、registry declaration 和模块 validator；失败时零 receipt、零 setting、零 event。
- 注册保留 publisher `host_core`，发布 `agent.run_status_changed@1`、`memory.changed@1`、`module.setting_changed@1`、`auth.session_revoked@1`。事件只含安全 ID/状态，不含 message、answer、value、token 或异常正文。
- composition 按内置模块注册顺序装配 subscriber。handler 失败不得回滚已提交事实或导致 mutation 重做；继续其他 handler并只记录脱敏标识。

### 5. Page API 与 production factory

- conversations、messages、memory candidates 统一返回 `Page[T]{items,next_cursor}`。
- 使用 `limit + 1` 判断下一页；稳定排序为冻结的时间降序、UUID 升序。cursor 必须绑定 endpoint、user 和 filter fingerprint，禁止跨用户、跨端点或改 filter 重放。
- 新增可供 Uvicorn/Electron supervisor 调用的 production factory，建议入口 `wife_system.api.production:create_production_app`。
- factory 显式装配 engine/session、Finance、HostRuntime、模块 registry、AgentApplication、activity import 和事件订阅；Host/legacy import identity 保持互斥。
- readiness 必须反映必要依赖状态；缺配置或依赖不可用使用稳定安全错误，不把 secret、DSN、SQL 或内部异常写入响应或日志。
- 使用假 provider、假 adapter、随机 schema 和虚拟数据完成 ready/auth/modules/Agent/import 最小冒烟；本任务不接真实模型、微信或个人数据。

## 文件所有权

允许修改产品：

```text
src/wife_system/host/contracts.py
src/wife_system/host/registry.py
src/wife_system/host/runtime.py
src/wife_system/host/factory.py
src/wife_system/host/events.py
src/wife_system/host/cursor.py
src/wife_system/host/tools/catalog.py
src/wife_system/host/state.py                 # 只接手 conversation/memory/setting 行为；不得恢复 R1 三事务
src/wife_system/agent/application.py
src/wife_system/agent/pending.py
src/wife_system/agent/loop.py
src/wife_system/agent/context.py
src/wife_system/agent/types.py
src/wife_system/agent/finance_tools.py         # 仅 Host adapter/fence/deadline 接线
src/wife_system/api/agent_routes.py
src/wife_system/api/app.py                     # production composition与Agent错误贯穿；不得放宽R1安全映射
src/wife_system/api/host_routes.py             # runtime、memory、conversation分页；不得恢复秘密重放
src/wife_system/api/host_schemas.py            # 具体Page/memory DTO；保持R1字段
src/wife_system/api/production.py              # 可新增
src/wife_system/modules/daily_finance.py
```

如果编译依赖要求修改同包 `__init__.py`，可以只增加必要导出，并在交付中单独说明；其他未列产品文件先停止报告，不自行扩大范围。

允许修改执行方测试：

```text
tests/host/test_contracts_registry.py
tests/host/test_state.py
tests/host/test_workflows.py
tests/host/test_api.py
tests/agent_finance/**
```

可以新增专门的 production composition 测试和 PostgreSQL run/pending 测试。可以只读复跑其他执行方回归；若 R1 安全回归因共享文件集成确需更新，只能增加/收紧兼容断言，不能删除或放宽原安全断言，并在交付中逐项说明。不得修改 `tests/independent/**`。

允许新增/更新交付记录：

```text
docs/b6-r2-runtime-running.md
docs/coordination/agents/executor.md
```

明确禁止修改：

- 三个 P4 migration 以及任何其他 migration；
- R1/F1 总控审查、D10、P4-IF-001、P4-IF-002、C10 矩阵、独立报告和协调快照；
- control、overview、brainstorm、technical-adviser、tester 角色文件；
- 依赖和锁文件，除非现有依赖确实无法实现冻结合同，并先停止报告；
- Electron、OpenClaw、微信、DeepSeek 在线调用、真实 provider、真实账户和真实个人数据；
- LangGraph、MCP、outbox、消息队列、向量数据库、SSE 或 WebSocket；
- Git 状态。

## 执行方测试责任

执行方自测是实现责任，不是独立验收。至少完成：

1. compiled plan 与真实 API→compiler→provider→BoundTool→pending 纵向链；
2. prompt 顺序、memory 上限、20 条/64 KiB 历史、message sequence 与重放；
3. 两 confirm、cancel/confirm、committing、领域提交后崩溃恢复、旧 commit fence；
4. run takeover 真正继续、旧 attempt 落盘失败、三次耗尽、provider/tool 前后续租；
5. 模块禁用、权限撤销、Profile/version变化、隐藏工具猜名全部零领域写；
6. candidate target/Profile grant/shared确认与状态竞争；memory supersede/invalidate/delete并发；
7. secret key 大小写/嵌套/分隔符变体、非法 JSON/finite/大小/schema 全部零写；
8. 四类事件的 commit 后发布、顺序、失败不回滚、重复容忍和隐私扫描；
9. 三个 Page 端点的第二页、同时间边界、末页、cursor 跨用户/端点/filter拒绝；
10. production factory 配置矩阵、readiness、Host/legacy import互斥、404/405/AuthError 表和随机 schema 冒烟；
11. R1/F1 绑定竞争、receipt、认证、活动导入、复合 user scope、migration保护测试；
12. P0～P3 执行方回归与全部 P4 执行方测试保持原不变量。

### 真实 PostgreSQL

只有 Docker Desktop 恢复后才能开始。本任务接单期间，执行智能体是项目 `finance-postgres` 的唯一环境负责人。启动前再次读取 control，并在 executor 日志记录操作、随机 schema、下一检查点。

只启动项目 `finance-postgres`，只使用项目测试凭据、随机 schema 和虚拟数据。真实进入断言：

- 两 confirm、cancel/confirm 和 committing lease/recovery；
- 领域提交后、pending 完成前故障与稳定 key 恢复；
- run takeover、新旧 attempt fence、三次耗尽和 lease renew；
- message sequence 与重复恢复；
- memory candidate、supersede、invalidate 和 user scope 并发；
- setting 失败零写、event post-commit 和 handler 失败不回滚；
- Page 同时间排序和 cursor 隔离；
- production factory 在空随机 schema 与 P4 head 的最小冒烟；
- R1 原 21 项、F1 同步外部身份竞争案例，以及 R1 migration/复合 FK 保护回归。

任何 skip、setup error 或只完成 collection 都不计为通过。结束时普通 `docker compose down` 并确认项目服务列表为空；禁止 `down -v`、删除 volume、prune、改 Docker Desktop 全局配置或触碰保留的 socket 现场目录。

## 交付与终点快照

`docs/b6-r2-runtime-running.md` 必须包含：

- 12 个审计项逐项“代码位置 → 测试 → 结果”映射；
- compiled plan、pending/run fence、prompt/message、memory/setting/event、Page 和 factory 数据流；
- R1/F1 不变量保护结果；
- 修改、新增、删除文件的准确数量和完整清单；
- 本地定向、Host、Agent、P0～P3 回归、全部 P4、PostgreSQL、静态与依赖检查分别统计；
- 所有失败、skip、warning、未验证项和 Docker 最终状态；
- 全部 R2 产品、执行方测试和运行说明的逐文件 SHA-256；
- 从 96 文件 R2 起点到终点的完整有序清单与总摘要，明确 unchanged/changed/added/deleted 数量，且报告数字必须与实际清单一致。

更新 executor 日志为 `review` / `finished` 后停止修改。不得执行任何 Git 写操作，不得派发 C11，不得要求用户扫码、发送微信消息、输入 API key 或提供真实财务资料。

## 进度与停止规则

- 接单时登记唯一负责人、96 文件起点摘要、文件边界和首个检查点。
- pending/run、compiled plan、memory/setting/event、Page/factory、PostgreSQL 每个实质里程碑更新日志；长操作至少每十分钟更新心跳。
- 预计超过五分钟的操作先记录可观察命令/测试文件和下一检查点。
- 出现跨用户写、取消后仍写事实、旧 attempt 覆盖新 owner、secret 落库/日志、事件失败回滚事实或 R1 安全回归被放宽，立即停止扩大测试并报告。
- 同一阻塞连续两个检查点没有新进展时，停止当前长操作，普通关闭由你启动的容器，保留现场并报告最后错误、已尝试方案、未验证假设和需要总控裁定的问题。
- control 更新、快照漂移或其他角色开始修改同一文件时，立即安全停止冲突范围。
