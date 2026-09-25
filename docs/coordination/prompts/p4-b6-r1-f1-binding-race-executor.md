# P4-B6-R1-F1：外部身份并发绑定最小返修

## 角色与唯一目标

- 角色：用户侧边栏中既有的“执行智能体”任务
- 任务编号：`P4-B6-R1-F1`
- 唯一目标：关闭 `P4-B6-R1-REV-001`，使两个有效绑定码并发争用同一 active 外部身份时，败方稳定得到 409 `channel_identity_conflict`
- 交付状态：只能到 `review`；不得启动 R2、C11 或宣布 R1/P4-A complete

开始前按仓库 `AGENTS.md` 顺序读取必读文件，并额外读取：

1. `docs/coordination/control.md`
2. `docs/coordination/agents/executor.md`
3. 本任务卡
4. `docs/p4-b6-r1-coordinator-review.md`
5. `docs/phase-4-interface-freeze-002.md`
6. `docs/b6-r1-security-data-running.md`
7. `docs/coordination/snapshots/p4-b6-r1-f1-start.sha256`

开始修改前逐项重算 23 文件快照。起点有序总摘要必须为：

```text
d46c056d57f07cae567806a1ca9eb01df8627fd9cc67331e7c1fa799216ec1cd
```

若不匹配，停止并报告变化文件；不得 restore/reset 或覆盖其他工作。

## 缺陷合同

真实 PostgreSQL 已复现：两个虚拟用户的不同有效 code 同时消费，并使用同一虚拟 `(channel, external_subject)` 时，一个成功，另一个可能从 `ChannelIdentityBinding` flush 抛出 `IntegrityError`。Host HTTP 路径因此返回 500，而不是冻结的 409。

修复后必须满足：

1. 最多一个 active binding 成功；败方固定为 `channel_identity_conflict`。
2. 败方不得返回 500，不得把 SQL、约束名、digest 或原始外部身份写入响应、日志、receipt 或事件。
3. 败方 code 保持 active，attempts 不增加，允许在原 binding 撤销后用新 Idempotency-Key 重试。
4. 败方 Host receipt 与领域状态同事务保存安全错误结果；相同 key 同载荷重放同一 409，不再次执行 mutation。
5. 不得捕获并吞掉任意 `IntegrityError`。建议只在 binding insert 的局部 savepoint 中处理唯一竞争；savepoint 回滚后重新查询同一 active `(channel, external_subject_digest)`，确认竞争事实才映射业务冲突，否则重新抛出。
6. 保留 R1 的 adapter-first、code 状态机、一次性 code、事务、user scope 和隐私不变量。

## 文件边界

允许修改产品：

- `src/wife_system/host/auth/service.py`

仅在确有 HTTP 编排必要时才允许修改：

- `src/wife_system/api/host_routes.py`
- `src/wife_system/host/state.py`

允许修改执行方测试：

- `tests/host/test_auth.py`
- `tests/host/test_api.py`
- `tests/host/test_postgresql_r1.py`

允许更新交付记录：

- `docs/b6-r1-security-data-running.md`
- `docs/coordination/agents/executor.md`

其他文件全部只读。尤其禁止修改 migration、模型、冻结文档、总控审查、快照、独立测试、C10 矩阵、R2 文件、依赖、Electron、OpenClaw、微信、DeepSeek 和 Git 状态。

## 必测证据

### 本地

- 原 `test_auth.py`、`test_api.py`、`test_state.py`、`test_migrations.py` 全部通过。
- 增加顺序冲突、同键重放、撤销后新键重试及隐私扫描；原断言不得删除或放宽。
- 若 SQLite 无法证明真实唯一索引等待语义，只把它作为快速回归，不代替 PostgreSQL。

### 真实 PostgreSQL

- 只启动项目 `finance-postgres`，使用随机 schema 和虚拟数据。
- 用两个连接和同步点迫使两个事务都越过“冲突预查”后争用唯一索引。可在测试引擎的 `before_cursor_execute` 对 `channel_identity_binding` INSERT 使用线程屏障；不得在产品代码加入测试 hook。
- 断言恰好一成功、一 `channel_identity_conflict`、零 `IntegrityError`/500；败方 code active、attempts 不变；binding/audit 恰好一份；败方安全 receipt 可同键重放 409。
- 复跑原 R1 PostgreSQL 21 项，新增案例单独计数，任何 skip 不计为通过。
- 结束时普通 `docker compose down` 并确认服务列表为空；禁止 `down -v`、删除 volume、prune 或修改 Docker 全局设置。

## 交付

更新 R1 运行说明，追加 F1 章节，记录：

- 缺陷原因、修复事务语义和异常筛选方式；
- 定向失败前/通过后结果；
- 本地、原 PG 21 项和新增 PG 案例的准确统计；
- warning、skip、未验证项和 Docker 最终状态；
- 修改文件逐项 SHA-256 及新的有序总摘要。

更新执行智能体日志为 `review` / `finished`，停止修改。不得执行 Git 写操作，不得继续 R2/C11，不得要求用户操作微信或填写密钥。

如果同一问题连续两个检查点没有新进展，按协作规则停止当前任务，保存输出并报告最后错误、已尝试方案和需要总控裁定的问题。
