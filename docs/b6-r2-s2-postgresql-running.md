# P4-B6-R2-S2 真实 PostgreSQL 执行记录

## 状态与结论

- 任务：`P4-B6-R2-S2`。
- S2 状态：`blocked / finished`。
- 整体 `P4-B6-R2` 状态：保持 `blocked / finished`，没有进入 `review`。
- 阻塞原因：任务卡要求完整复跑的既有 `tests/host/test_postgresql_r1.py` 实际为 `7 passed, 1 failed, 1 warning`。失败用例的两枚绑定码都因既有测试固定时钟早于 HTTP 路由真实时钟而过期，预期 `[200, 409]`、实际 `[409, 409]`。S2 文件边界不允许修改该既有业务用例，因此保留失败证据并停止。
- 新增的 9 项 R2 真实 PostgreSQL 纵向测试最终全部通过；Finance claim 4 项和 Activity import 10 项既有 PostgreSQL 基线全部通过。这些是执行方验证，不是独立验收，也不表示 P4-A `complete`。

## 起点门禁与文件边界

- 起点清单：`docs/coordination/snapshots/p4-b6-r2-s2-start.sha256`。
- 条目：101。
- 清单自身普通 SHA-256：`8e92671370cfbbea33dafec36a5d3e4dfbe6fe734fa8df0ed2caab9288e74969`。
- 接单后逐项复算：`101/101` 匹配，`missing=0`、`mismatch=0`；通过后才新增测试。
- 停止修改前再次复算起点内 101 文件：`unchanged=101`、`changed=0`、`missing/deleted=0`。
- 新增执行方测试：`tests/host/test_postgresql_r2.py`。
- 新增本运行说明：`docs/b6-r2-s2-postgresql-running.md`。
- 按协作规则只更新本角色日志：`docs/coordination/agents/executor.md`；该文件不在 101 项产品/测试起点清单内。
- 没有修改三个既有 PostgreSQL 基线文件、任何 `src/**`、migration、依赖、冻结文档、独立测试、矩阵、control、overview 或其他角色文件；没有执行 Git 写操作。

## 新增 9 项 PostgreSQL 合同映射

| # | 测试 | 真实 PostgreSQL 证据 |
| --- | --- | --- |
| 1 | `test_postgresql_s1_migration_empty_history_and_round_trip` | 随机空 schema 经 Alembic 到唯一 `p4_host_state`；inspector 核对 `agent_run.module_version` 和 `memory_candidate.proposed_by_profile_version` 均为 `VARCHAR(32) NOT NULL`，memory status check 含 `invalidated`。另建 P3 schema，写入完整虚拟 account/run/pending 历史，验证升级回填 `daily_finance / 1.0.0`，再执行 head→P3→head，数据与约束仍满足合同。没有用 `Base.metadata.create_all()` 代替 migration 证据。 |
| 2 | `test_postgresql_candidate_version_recheck_and_confirm_race` | candidate 保存真实 Profile `1.4.0`；Profile 消失、module 禁用、version 改变、grant 撤销四类 confirm 均返回 `memory_candidate_conflict`，candidate 保持 pending，零 item、零 receipt。两个独立会话在真实 UPDATE 前用 10 秒 barrier 对齐，竞争 confirm 仅一方产生 item/receipt/event，败方冲突回滚，赢家同键重放返回同一 item。 |
| 3 | `test_postgresql_memory_supersede_invalidate_cas_and_cleanup` | 两个独立会话以 barrier 竞争 supersede/invalidate，恰好一个 version/status CAS 胜者；仅一份 receipt/event，败方 replacement 随事务回滚。事件不含原始 memory。若 invalidated 胜出，retrieve 排除该 ID，并以 version 2 成功 delete；若 supersede 胜出，只有合法 replacement 存在。 |
| 4 | `test_postgresql_pending_confirm_cancel_and_commit_recovery` | 两个独立 AgentApplication 实例并发双 confirm，仅一个领域幂等事实；cancel/confirm 竞争后 pending 只有 committed/cancelled 单一终态。另在 Finance 已提交、`mark_committed` 前注入虚拟崩溃，commit lease 到期后恢复使用稳定领域幂等键收敛，expense 数量不增加。 |
| 5 | `test_postgresql_run_takeover_attempt_fence_and_exhaustion` | 两个独立会话竞争过期 run lease，只有一个取得 attempt 2；旧 attempt renew、assistant message 和 terminal result 均得到 `run_lease_lost`。到 attempt 3 后按 fence 写入稳定 `run_attempts_exhausted` 终态。 |
| 6 | `test_postgresql_messages_constraints_and_post_commit_events` | 真实 run 的 user/assistant 消息序列为 `[0,1]`；直接重复 `(user_id,run_id,run_sequence)` 被 PostgreSQL unique constraint 拒绝。run、memory、setting、session revoke 四类 `host_core` 事件均在相应事实提交后可见；故障 handler 只记录安全 `error_type`，不回滚 setting，也不泄露原始 memory、密码或异常文本。 |
| 7 | `test_postgresql_setting_receipt_atomicity_and_concurrent_keys` | 递归 `refresh_token` 在 setting、receipt、event 前被拒绝。同键同载荷两个会话竞争后至少一个完成，随后稳定重放；同键异载荷为 `idempotency_conflict`。最终 setting 与 completed receipt 同时可见。 |
| 8 | `test_postgresql_page_cursor_uuid_boundary_and_binding` | 四条同时间 conversation 按 UUID 升序稳定；第一页后插入更新记录，使用原 cursor 的后续页无既有边界重复或遗漏，新记录不混入旧边界。endpoint、user、filter 三种错误绑定均拒绝为 `invalid_cursor`。 |
| 9 | `test_postgresql_production_factory_ready_smoke_and_stale_schema` | 随机已迁移 schema 上 factory `/healthz`、`/readyz`、owner 初始化/登录、modules、conversation、假 provider Agent 和认证 activity preview 冒烟通过。另一随机 P3 schema 上 `/healthz` 存活、`/readyz` 为 503 `migration_not_current`，revision 保持 P3，不自动迁移且响应不含测试连接秘密。 |

所有并发 barrier 均设 10 秒上限；fixture 只创建随机 schema 并在 `finally` 中 `DROP SCHEMA ... CASCADE`，没有访问真实账户、密钥、个人或财务数据。

## 新增测试实际运行

| 运行 | 结果 | 说明 |
| --- | --- | --- |
| 编译与收集 | `9 collected`，退出码 0 | 首次 collection 因新增测试误导入不存在且未使用的 `Transaction` 类型失败；移除该测试 import 后正常收集。这不是产品失败。 |
| PostgreSQL 首轮 | `6 passed, 3 failed, 1 warning` | 三项均为新增测试假设错误：共享 schema 已有其他 active memory，不能断言 retrieve 全空；两个 TestClient 未声明 loopback，正确触发 bootstrap 安全门禁。 |
| PostgreSQL 第二轮 | `8 passed, 1 failed, 1 warning` | 剩余新增断言错误地期待日志包含 handler 原始异常文本；产品实际只输出安全 `error_type`。 |
| PostgreSQL 最终完整复跑 | `9 passed, 1 warning` | 九项全部通过，0 failed、0 skipped。 |

新增测试的两轮修正只改 `tests/host/test_postgresql_r2.py`，没有改变产品、migration 或既有断言。唯一 warning 为 Starlette `TestClient` 对 AnyIO `BlockingPortal` alias 的既有第三方弃用提示。

## 三个既有 PostgreSQL 基线

| 文件 | 实际 collection 与结果 | failed / skipped / warning |
| --- | --- | --- |
| `tests/host/test_postgresql_r1.py` | 8 项：`7 passed, 1 failed` | failed=1、skipped=0、warning=1；warning 为同一 Starlette/AnyIO 弃用提示。 |
| `tests/finance/test_postgresql_claim.py` | 4 项：`4 passed` | failed=0、skipped=0、warning=0。 |
| `tests/activity_import/test_postgresql.py` | 10 项：`10 passed` | failed=0、skipped=0、warning=0。 |

三组实际合计 22 项：`21 passed, 1 failed, 0 skipped, 1 warning`。没有把 collection、skip 或诊断重跑计作 passed。

## 阻塞失败的脱敏复现

- 用例：`test_postgresql_competing_binding_codes_return_safe_replayable_conflict`。
- PostgreSQL：项目 Compose image `postgres:17.6-alpine`，容器本轮达到 `healthy`；随机 schema、虚拟 user/provider/subject/code。
- 期望：两个有效 code 竞争相同 active external subject，HTTP 状态为 `[200,409]`，赢家创建 binding，败方为 `channel_identity_conflict`。
- 首次基线实际：HTTP `[409,409]`，因此断言在选择赢家前失败。
- 一次 PDB 诊断复现实际：两端安全错误码均为 `binding_code_invalid`；两枚 code 均为 `expired / attempts=0`；active binding 数为 0；两个 `binding.code.consume` receipt 均为 completed rejected，且不含原始 code/provider/subject。
- 时间根因：用例用固定 `2026-09-26T02:00:00Z` 创建 code，十分钟后过期；HTTP consume 路由使用本轮真实系统时间（Asia/Shanghai 约 19:xx，即 UTC 约 11:xx），所以在并发 binding INSERT 屏障前已走过期分支。SQLSTATE/约束名不适用，因为没有执行到唯一约束竞争。
- 最小建议返修范围：另立任务只修 `tests/host/test_postgresql_r1.py` 的测试时钟，使 code 创建和 HTTP consume 使用同一个可控时钟或以当前 UTC 动态创建，再重跑原 8 项与 S2 基线。S2 没有获得修改该既有业务用例的权限，因此没有改断言、延长生产 TTL、skip、xfail 或反复重跑掩盖失败。

## 静态检查

- `.venv\Scripts\python.exe -m compileall -q tests\host\test_postgresql_r2.py`：退出码 0。
- `.venv\Scripts\python.exe -m pip check`：`No broken requirements found.`。
- `git diff --check`：退出码 0；仅输出起点工作树已有文件的 LF→CRLF 提示，没有 whitespace error。
- 按 S2 有限验证策略，没有重复运行 S1 已完成的 326 项非 PostgreSQL 回归。

## Docker 与资源关闭

- 外部操作前重读 control `2026-09-26T18:55:00+08:00`，确认本执行智能体为 S2 和 `finance-postgres` 唯一环境负责人，起点 Compose 服务列表为空。
- 只执行 `docker compose up -d finance-postgres`；容器 `wife-system-finance-postgres-1` 达到 `running / healthy`，端口仅绑定 `127.0.0.1:55432`。
- 测试只使用 Compose 中的测试账户、随机 schema 和虚拟数据。
- 测试结束执行普通 `docker compose down`；容器和项目网络正常停止并移除。
- 最终 `docker compose ps --format json` 无输出，记录为 `COMPOSE_SERVICES_EMPTY`。
- 未执行 `down -v`、volume 删除、prune、factory reset、Docker 全局设置变更或 socket 目录操作。

## 文件摘要

停止修改时，101 项起点清单仍全部匹配。新增执行方测试的普通 SHA-256：

```text
tests/host/test_postgresql_r2.py\td8ad7814dd237e62dab12d993dad591d0434b47d4615b65c02de0e93e203b002
```

本运行说明不在自身内容中保存其最终普通 SHA-256，以免制造自引用；文件写定后的普通 SHA-256 与执行智能体角色日志的最终普通 SHA-256 记录在执行智能体最终日志和交付消息。没有 deleted 文件。

## 未验证与停止点

- 因既有 Host R1 基线失败，S2 和整体 R2 均不能进入 `review`；P4-C11 不得启动。
- 未形成“全部既有 PostgreSQL 基线通过”证据；绑定 active external subject 唯一竞争本轮被过期测试时钟挡在 INSERT 前，没有重新验证其 `[200,409]` 业务分支。
- 新增 9 项通过、Finance 4 项通过、Activity import 10 项通过只作为已执行证据保留，不能抵消 Host R1 的失败。
- 没有启动测试智能体、技术顾问、Electron、OpenClaw、微信、DeepSeek 或真实 provider；没有读取真实密钥或数据；没有执行 Git 写操作。
