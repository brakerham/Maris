# P4-D10：B6 接管缺陷的最小返修架构裁定

## 角色与任务

- 角色：用户侧边栏中既有的“技术顾问”任务
- 任务编号：`P4-D10`
- 唯一目标：只读核对 P4-B6 审计发现，解决阻塞实现的合同冲突，并把返修拆成可执行、互不重叠的最小切片
- 交付状态：只能到 `review`；技术建议不等于接口已经冻结、代码已经修复或独立验收通过

开始前必须按顺序读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. `docs/coordination/control.md`
6. `docs/coordination/agents/technical-adviser.md`
7. 本任务卡
8. `docs/p4-b6-multi-handoff-code-audit.md`
9. `docs/phase-4-interface-freeze.md`
10. `docs/phase-4-d9-modular-agent-host-advice.md`
11. `docs/testing/phase-4-modular-agent-host-test-matrix.md`
12. `docs/b6-host-foundation-running.md`

然后只读核对审计报告引用的实际代码、migration 和执行方测试。旧文档和当前代码冲突时，分别写明“冻结要求、当前行为、建议修复”，不能把建议描述成已实现。

## 输入事实

- P4-B6 曾由多个代码 Agent 顺序续做，当前状态是 `review`、运行已停止。
- 接管审计按问题组登记 8 个 P0、14 个 P1；当前快照不得进入 C11。
- 根总控已运行当前执行方本地组合套件，结果为 249 通过、13 个 PostgreSQL skip。
- 真实 PostgreSQL 上，现有两个执行方文件为 1 通过、12 失败，主要原因是 fixture/head/user scope 没有随 P4 更新；随机 schema 的 P4 head 最小产品冒烟通过。
- Docker 已普通关闭，当前没有外部操作负责人。
- OpenClaw/微信已由用户确认恢复并可连接，但 P4-D10 不操作它们。

## 必须裁定的问题

每项必须给出：推荐方案、至少一个有意义的替代方案、拒绝替代方案的理由、数据库/HTTP/失败恢复语义、需要新增的执行方测试，以及是否需要 P4-IF-002 冻结补充。

### 1. 一次性绑定码与幂等

- 原始 code 只能在首次成功创建响应出现，普通数据库不能保存或可重建原码。
- 同一 Idempotency-Key 重放时正式返回什么 HTTP 状态、错误码和安全字段。
- 首次响应丢失后怎样作废/替换旧码，不能让客户端靠重放取回秘密。
- 是否采用 `code_id + code` 消费合同；code_id 是否非秘密、怎样防止存在性侧信道。
- 五次失败到底按 code、code_id、channel、adapter 或组合维度累计；第 1～6 次、过期、已消费和并发消费的线性化语义。

### 2. Host 命令、领域事实和 receipt 一致性

- initialize、create binding code、consume、revoke 如何消除三事务 crash window。
- 比较“共享一个数据库事务”“带 lease/status 的可恢复 receipt”“从领域事实重建结果”三种方案。
- 明确哪些结果含一次性秘密，绝不能进入 receipt；哪些结果可以安全重放。
- 进程在领域提交前、提交后、receipt 完成前退出时，下一请求的确定行为。

### 3. run/pending 并发和恢复

- cancel 与 confirm 的 CAS 所有权；`claim_commit=False` 后每个实际状态的处理。
- `committing` 的取消、GET 恢复和稳定 `commit_in_progress`。
- 过期 run 的真实 takeover、attempt fencing、旧 worker 保存结果的拒绝。
- provider/tool 前后 lease renewal，60 秒 lease 与 15/10 秒 deadline 的关系。
- cooperative tool deadline 如何覆盖同步事务而不虚假宣称取消已提交写。

### 4. Host 真正控制 Agent 的最小集成

- 唯一的 compiled execution plan 应包含哪些冻结字段：module、Profile/version、prompt、BoundToolRegistry、permissions、memory grants、limits、conversation、attempt fence。
- start/resume 在哪些点重新检查模块启用、Profile、权限和工具 grant。
- 如何把 Host 安全规则、Profile prompt、可信上下文、最多 8 条获准记忆、会话历史和工具事实按冻结顺序交给 AgentRunner。
- 用户/assistant/tool message 在何时持久化；失败和重放时怎样避免重复 message。
- `tool_not_allowed`、timeout、cancelled 等稳定码怎样贯穿 registry、runner 和 HTTP。

### 5. memory、setting 和 event

- candidate 的 source/target namespace 怎样绑定 `proposed_by_profile_id` 和 module enablement。
- shared confirmed 的显式确认，supersede/invalidate/tombstone 的最小状态机与并发 CAS。
- setting value 的秘密字段拒绝和模块 schema validator 放在哪个确定性边界。
- 四类 post-commit 事件的 publisher、subscriber wiring、handler 失败语义；Host 自身事件怎样进入 registry 合法 publisher 集。

### 6. user scope 和 migration

- 为 memory self-reference、candidate→item、run→pending 增加复合 user FK 的准确约束形状。
- run/pending 循环引用的 SQLite batch rebuild、PostgreSQL DDL、upgrade/downgrade 顺序。
- 当前 P4 尚未验收时，是修正现有三个 revision 还是增加第四个 revision；必须与冻结的三段 migration 目标一致。
- P4 合法 `cancelled` run 在 head→P3 时的语义映射；不得删除、伪装 success 或丢失业务引用。
- ORM metadata 与 Alembic schema 是本轮同步复合约束，还是明确限制 `create_all()` 仅用于纯单元测试；说明 C11 如何验证。

### 7. 生产组合、API 与分页

- 一个可直接供 Uvicorn/Electron supervisor 启动的 Python app factory，怎样装配 config、secret、Session factory、HostRuntime、FinanceService、AgentApplication 和 activity import。
- 哪些 secret 必须来自运行配置，启动缺失时怎样 not ready/失败；不得把值放进 renderer、日志或普通设置。
- activity import 的 Host principal 和历史 P3 测试 identity 怎样兼容。
- Principal channel 怎样由 DeviceSession platform 派生。
- 404/405 与全部 AuthError 的稳定 HTTP envelope/mapping。
- conversations/messages/memory candidates 的统一分页响应形状、`items/next_cursor`、稳定排序和 endpoint/user 绑定。

### 8. 返修拆分

给出两个顺序执行、文件所有权不重叠或交接清楚的执行任务建议：

- `P4-B6-R1`：认证、user scope、migration、Host command 安全和兼容入口；
- `P4-B6-R2`：Host/Agent/workflow/conversation/memory/event/production composition 集成。

每个切片列出：准确文件范围、输入/输出合同、必须先通过的执行方测试、真实 PostgreSQL 范围、交接快照和不能顺手做的内容。若你认为必须采用其他切分，也要证明怎样避免两个任务同时编辑 `api/app.py`、`host/state.py`、`agent/application.py` 或同一 migration。

最后给出 P4-C11 的进入条件。不能把当前 B6 快照、D10 文档或执行方自测当成 C11 已开始。

## 文件边界

允许修改：

- `docs/phase-4-d10-b6-repair-architecture.md`
- `docs/coordination/agents/technical-adviser.md`

其余全部只读，尤其禁止修改：

- `src/**`
- `migrations/**`
- `tests/**`
- `docs/p4-b6-multi-handoff-code-audit.md`
- `docs/phase-4-interface-freeze.md`
- C10 矩阵和独立报告
- control、overview、brainstorm/executor/tester 角色文件
- 依赖、Compose、OpenClaw、微信、Electron、DeepSeek、Git 状态

## 验证与交付

交付文档必须：

1. 对审计中的 8 个 P0、14 个 P1 建立逐项处置表，不漏项、不合并成“后续优化”。
2. 给出上述七类合同的推荐方案、替代方案和可观察失败语义。
3. 给出至少两张 Mermaid 图：命令/receipt 恢复；Host→Profile→Agent→Tool→conversation/memory 数据流。
4. 给出 R1/R2 文件边界和顺序、C11 进入门槛、必须真实执行的 PostgreSQL 场景。
5. 引用准确代码位置；所有本地链接存在，代码围栏成对，无凭据、真实账户和个人财务数据。
6. 更新技术顾问自己的角色日志，记录接单、实质里程碑、交付和未裁定项。

可以运行只读搜索和不改状态的文档检查；无需复跑 249 项测试，不启动 Docker/FastAPI/外部服务，不安装依赖。若发现审计事实不成立，必须给出最小复现反证，不能静默删项。

完成后状态写 `review` 并停止。不要修改产品、不要启动执行智能体或测试智能体、不要自行发布 P4-IF-002，不执行任何 Git 写操作。

连续两个检查点无有效进展时，在安全位置停止并报告：最后完成的审计项、卡点、脱敏错误、已尝试方法和需要总控裁定的问题。
