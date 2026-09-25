# P4-B6-R1 总控代码验收记录

- 任务：`P4-B6-R1`
- 角色：头脑风暴总控
- 核对时间：2026-09-26 01:47，Asia/Shanghai
- 结论：`review`，暂不接受；发现 1 个可复现 P1，并准备 `P4-B6-R1-F1` 最小返修
- R2/C11：均不得启动

## 1. 已确认的交付事实

- 执行方运行说明实际 SHA-256 为 `54edb8c9f2c5186acdb4b7e10e7be46956949c32ff6df5d8635b0c2cc9e8ff31`，与报告一致。
- 报告列出的 22 个产品、migration 和执行方测试文件逐项摘要全部匹配，有序总摘要为 `13520520ebd351797f47fb1eb143e8e01b70e7a98975b51d9aca827df1fdc0f8`。
- 与 93 文件 R1 起点相比，21 个既有文件变化、72 个不变、0 个缺失，另新增 `tests/host/test_postgresql_r1.py`；变化均在 R1 授权范围内。
- 总控定向复跑 `test_auth.py`、`test_api.py`、`test_state.py` 和 `test_migrations.py`，结果为 40 passed，只有既有 Starlette/AnyIO 弃用 warning。
- 一次性 code、Host command 单事务、Host import principal、access 到期、错误穷举映射、三条复合 FK、cancelled downgrade 和 P4 unique 名兼容的实现方向与 R1 冻结一致。

## 2. 冻结文档勘误与裁定

总控发现 P4-IF-002 曾把 binding HMAC domain 误写为 `wife.channel-binding.v1`，而已验收 D10 明确冻结的输入是：

```text
wife.channel-binding.v2\0code_id\0channel\0code
```

执行方采用 v2 是正确实现。P4-IF-002 已作文字勘误，不要求执行方回退。

D10 曾建议 run→pending 为 `DEFERRABLE INITIALLY IMMEDIATE`，P4-IF-002 当时只冻结“可延迟”。R1 采用 `INITIALLY DEFERRED`，跨用户关系仍在事务提交时由数据库拒绝，不产生其他事务可见的非法状态，并与循环关系的原子写入相容。总控将 P4-IF-002 补全为 `DEFERRABLE INITIALLY DEFERRED`，本项不构成返工。

## 3. 开放缺陷 `P4-B6-R1-REV-001`

### 现象

在真实 PostgreSQL 中建立两个虚拟用户，各自持有一个有效绑定码，让两个 Host command 同时绑定相同的虚拟 `(channel, external_subject)`：

```text
第 1 轮：[AuthError:channel_identity_conflict, success]
第 2 轮：[IntegrityError:duplicate key ... uq_binding_active_subject, success]
```

第二轮败方在 `ChannelIdentityBinding` flush 时触发唯一索引竞争。直接 `AuthService.consume_binding_code()` 会在外层捕获该异常，但 HTTP Host 路径调用的是 `consume_binding_code_in_session()`，异常越过 `HostCommandService`，最终只能得到安全但错误的 500 `internal_error`。

### 影响与分级

- 数据库唯一索引仍保证同一 active 外部身份只有一个所有者，没有身份抢占、重复绑定或跨用户数据损坏。
- 败方整个事务回滚，绑定码仍可重试；因此不是 P0 数据安全缺陷。
- 首次响应违反稳定业务错误和 Host 幂等恢复合同，属于 P1 并发稳定性缺陷。

### 预期

- 竞争胜方只允许一个成功。
- 竞争败方必须稳定返回 409 `channel_identity_conflict`，不能返回 500 或暴露 SQL/约束正文。
- 败方绑定码保持 active，现有 binding/audit 不被改写；使用相同 Idempotency-Key 重放仍返回同一 409，receipt 保存安全拒绝结果。
- 修复不能把所有 `IntegrityError` 一律伪装为身份冲突。应在局部 savepoint/条件插入失败后重新确认同一 active 外部身份确已存在；否则继续抛出真实数据库错误并整体回滚。

## 4. F1 进入与退出条件

返修固定起点为 [23 文件快照](coordination/snapshots/p4-b6-r1-f1-start.sha256)，有序总摘要：

```text
d46c056d57f07cae567806a1ca9eb01df8627fd9cc67331e7c1fa799216ec1cd
```

F1 只允许修改绑定消费实现、相应执行方测试、R1 运行说明和执行智能体日志。退出必须提供：

1. PostgreSQL 可重复同步竞争测试，断言一成功、一 409、零 500；
2. 败方 code、binding、audit、receipt 和同键重放状态断言；
3. 原 R1 本地门禁与 PostgreSQL 21 项全部保持通过；
4. 新快照及普通 `docker compose down` 后的空服务列表。

## 5. 资源与停止点

总控最小复现只使用项目 `postgres:17.6-alpine`、随机 schema 和虚拟身份。复现后已执行普通 `docker compose down`，最终 `docker compose ps --format json` 无输出；没有删除 volume、prune 或修改 Docker 全局设置。

在 F1 新快照通过总控核对前，P4-B6-R1 保持 `review`，R2 和 C11 保持未派发。
