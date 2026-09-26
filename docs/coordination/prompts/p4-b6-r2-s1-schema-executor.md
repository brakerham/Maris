# P4-B6-R2-S1 执行智能体 Prompt：运行时结构补全

你是项目中既有的**执行智能体**，唯一负责 `P4-B6-R2-S1`：补全 R2 已冻结但当前 schema 无法表达的三个结构，并完成本地执行方验证。

## 开始前必须读取

按顺序读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. `docs/coordination/control.md`
6. `docs/coordination/agents/executor.md`
7. `docs/phase-4-interface-freeze.md`
8. `docs/phase-4-interface-freeze-002.md`
9. `docs/phase-4-d10-b6-repair-architecture.md`
10. `docs/p4-b6-r2-blocked-coordinator-review.md`
11. `docs/b6-r2-runtime-running.md`
12. `docs/coordination/snapshots/p4-b6-r2-s1-start.sha256`

先在 executor 角色文件记录接单、当前步骤、开始时间、心跳、下一检查点和等待对象，再修改代码。

## 起点与目标

起点是 R2 受阻停止后的 100 文件普通 SHA-256 清单：

```text
docs/coordination/snapshots/p4-b6-r2-s1-start.sha256
manifest_sha256=d6357a6e2612e5cc56217759780eaa3ab205930455e459eb4326f318965b194b
entries=100
```

逐行复算并确认 100/100 匹配。任何一项不匹配，立即停止修改并报告漂移；不得自行 restore、reset、checkout 或覆盖文件。

目标只包含三项：

1. `agent_run` 持久保存并正确比较独立的 module version。
2. `memory_candidate` 持久保存 proposal 时的 Profile version，confirm 重新解析并核对同一 ID/version/grant。
3. `memory_item` 完整实现 `active -> invalidated -> deleted` 的 version CAS 状态机。

这三项是已冻结合同的结构补全，不重新设计 P4，不扩展到 C11、Electron、OpenClaw、微信、DeepSeek 或桌面界面。

## 总控已冻结的实现语义

### A. agent run module version

- 在 `AgentRunRecord` 和 `p4_host_state` migration 增加非空 `module_version VARCHAR(32)`。
- migration 对既有 P0～P3 run 使用与同段 `module_id='daily_finance'` 一致的 `module_version='1.0.0'` 回填，再改为 non-null；downgrade 与该批 P4 列一起删除。
- start/preflight 必须取得并保存 `definition.manifest.version` 与 `profile.version` 两个独立值。
- start、resume、takeover 共用的 compiler 分别比较：
  - `definition.manifest.version == row.module_version`
  - `profile.version == row.profile_version`
- 禁止再把 module version 与 `row.profile_version` 比较。
- 模块或 Profile 的持久版本与当前 registry 不一致时，沿用 409 `profile_changed`，零 provider、零 tool、零领域写；本任务不新增外部错误码。
- 测试必须构造 module version 与 Profile version 不相等的合法 manifest，证明二者不会互相比较；再分别改变其中一个，证明恢复路径 fail closed。

### B. memory candidate Profile version

- 在 `MemoryCandidateRecord` 和 `p4_host_state` 新建表定义加入非空 `proposed_by_profile_version VARCHAR(32)`。
- `propose` 必须解析实际 Profile，验证 source module、module enabled、target grant/kind/operation，并把当时的 Profile ID/version 一起保存。调用者不能伪造一个与 registry 不一致的版本。
- `confirm` 不接受 target namespace；重新解析 candidate 保存的 Profile ID，要求当前 Profile version 与保存值一致，再复查 module enablement、固定 target、kind 和 propose grant。
- Profile 消失、模块禁用、版本变化或 grant 被撤销时，confirm 以 409 `memory_candidate_conflict` 拒绝，零 memory item；事务失败不得留下未完成 receipt。
- reject 仍是用户减少数据动作，不因模块后来禁用而失效。
- `memory_candidate` 是 P4 新表，本任务不伪造旧候选的历史版本，也不破坏性重建任何用户数据库。

### C. memory invalidation

- migration 与 ORM check 允许 `active/deleted/superseded/invalidated`。
- 增加 service 级 invalidate 操作：只允许 `active` 且 version 匹配者 CAS 成功；清空 `value_json` 与 `tags_json`，保留安全审计字段，递增 version，写同事务 receipt，commit 后发布脱敏 `memory.changed@1`。
- 同一 idempotency key 安全重放；同 key 不同 payload 冲突；旧 expected version 返回 `memory_version_conflict`。
- supersede 与 invalidate 并发时恰好一个 CAS 胜者；败方不得留下 replacement、半写 receipt 或事件。
- retrieve 继续只返回 active、未过期、获 grant 的最多八条。
- delete 接受 active、superseded 或 invalidated，清空内容后成为 deleted tombstone；重复 delete 安全重放。
- 不新增 HTTP invalidate 路由；P4 当前只冻结 service 状态机。若实现被现有 API 编译依赖阻塞，先停止报告，不自行扩展 API。

## 文件所有权

允许修改产品：

```text
migrations/versions/p4_host_state.py
src/wife_system/agent/models.py
src/wife_system/agent/application.py
src/wife_system/host/state_models.py
src/wife_system/host/state.py
src/wife_system/host/factory.py
```

允许修改执行方测试：

```text
tests/host/test_migrations.py
tests/host/test_state.py
tests/host/test_api.py
tests/agent_finance/test_r2_runtime.py
```

只有某个现有构造器因新增必填字段必须同步时，才允许最小修改下列执行方 fixture，并在交付中逐项解释：

```text
tests/host/test_workflows.py
tests/host/test_postgresql_r1.py
tests/agent_finance/test_tools_and_http.py
```

允许新增/更新交付记录：

```text
docs/b6-r2-s1-schema-running.md
docs/coordination/agents/executor.md
```

只读参考但禁止修改：

```text
docs/coordination/snapshots/p4-b6-r2-s1-start.sha256
docs/b6-r2-runtime-running.md
docs/p4-b6-r2-blocked-coordinator-review.md
docs/phase-4-interface-freeze*.md
docs/phase-4-d10-b6-repair-architecture.md
tests/independent/**
```

明确禁止：

- 新增第四个 P4 migration 或改变 revision/head 拓扑；
- 修改其他 product、独立测试、C10 矩阵、独立报告、control、overview、brainstorm、technical-adviser 或 tester 文件；
- 删除、放宽或 xfail/skip 既有安全和业务断言；
- 启动 Docker Desktop、容器或 PostgreSQL；S1 是纯本地结构/逻辑任务；
- 访问 Electron、OpenClaw、微信、DeepSeek、真实 provider、真实账户、密钥或真实财务数据；
- 任何 Git 写操作。只允许只读 `git status`、`git diff`、`git log` 和对象摘要。

## 执行方验证

至少完成并分别统计：

1. migration：SQLite 空库升级到唯一 P4 head、P0～P3 虚拟历史升级、downgrade/upgrade；字段 non-null、长度、status check 和单一 head 都有断言。
2. module/profile 版本：两个版本不同仍可 start/compile；任一持久版本与当前 registry 漂移均 fail closed，零 provider/tool/领域写。
3. memory candidate：保存 ID/version；confirm 使用固定 target 和精确版本；模块禁用、版本变化、grant 撤销均零 item/receipt；reject 仍可用。
4. memory invalidation：正常、同键重放、异 payload 冲突、旧 version、与 supersede 竞争、delete invalidated、检索排除、事件隐私。
5. 原 R2 定向测试、Agent、Host 相关本地测试和一次非 PostgreSQL 执行方回归。不要为了得到全绿而把 PostgreSQL 用例计入通过，也不要删除 skip。
6. `compileall`、`pip check`、`git diff --check`。

如果新增字段使只读的 PostgreSQL fixture 需要同步，可以修改上面列出的最小 fixture 文本，但本轮不运行 PostgreSQL，不声称真实数据库通过。所有 PostgreSQL 行为继续标为 `unverified`，留给 S2。

## 交付与停止

`docs/b6-r2-s1-schema-running.md` 必须包含：

- 三个结构缺口的代码位置、迁移语义、数据流和测试映射；
- 起点 100/100 摘要核对结果；
- 实际修改/新增/删除文件清单；
- 每组测试的 passed/failed/skipped/warning；
- 未验证的 PostgreSQL 项；
- 普通 SHA-256 逐文件摘要。

不要在运行说明内设计自引用 canonical hash。报告自身的普通 SHA-256 只写入 executor 角色日志；总控在停止修改后生成下一份稳定清单。

完成本地实现和验证后，把 **S1** 标为 `review / finished` 并停止，但整体 `P4-B6-R2` 仍保持 `blocked`，原因是 PostgreSQL S2 尚未执行。不得自行启动 S2、Docker 或 P4-C11。

同一问题连续两个检查点没有新进展时，在安全位置停止并记录：最后错误、已尝试方案、当前文件状态、未验证项和需要总控裁定的问题。control.md 更新或文件漂移时立即停止旧动作。
