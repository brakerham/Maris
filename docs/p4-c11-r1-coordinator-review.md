# P4-C11-R1 历史迁移证据总控核对

## 1. 结论

- 核对时间：`2026-09-27 00:30 Asia/Shanghai`
- `P4-C11-R1`：接受其独立失败结论，状态保持 `blocked / finished`。
- P4-A：不能接受，矩阵保持 62 passed、2 failed。
- 产品缺陷：确认登记 `P4-C11-R1-PG-001`，严重级别 P0。
- 下一任务：`P4-B6-R3`，由既有执行智能体只修复 PostgreSQL 带 P1/P2/P3 历史数据正向升级时的 user-scope migration 阻断。

## 2. 证据核对

总控直接复算：

```text
P4 产品快照
entries=105
matched=105
missing=0
mismatch=0
manifest_sha256=65ee400893171d6caf19f2bf5adf20a4432f1f3c8048d5c381b718fc10360126

C11-R1 测试方起点
entries=23
unchanged=17
changed=6
missing=0
```

交付摘要全部匹配测试方声明。矩阵为：

```text
P4A=64
passed=62
failed=2
P4A-DB-05=failed
P4A-DB-06=failed
P4-B/C/D=56 not_run
```

定向执行结果：

- P1 首版→P4 SQLite：8 passed；
- Host SQLite migration：3 passed；
- cancelled 后 confirm：1 passed；
- PostgreSQL P3 历史→P4：1 failed、0 skipped；
- 105 文件产品快照前后零漂移；
- Docker 最终 `COMPOSE_SERVICES_EMPTY`。

## 3. 缺陷边界

独立 PostgreSQL fixture 从真实 P3 head 创建合法虚拟历史：

- P1 account/category/expense transaction/正负双分录；
- P2 paused run/needs-confirmation pending；
- P3 previewed import batch/candidate。

Alembic 升级到 `p4_host_state` 时，在 `p4_host_user_scope` 为 `financial_transaction.user_id` 设置 NOT NULL 阶段失败。PostgreSQL 错误类别为 `ObjectInUse`，安全摘要为表仍存在待处理的触发器事件。迁移没有到达 P4 head。

当前实现顺序为：

1. 更新旧 actor/owner；
2. 给 21 张表添加 nullable `user_id`；
3. 对每张表执行 `UPDATE ... SET user_id=:bootstrap`；
4. 立即逐表执行 `ALTER COLUMN user_id SET NOT NULL`、unique/FK/check DDL；
5. 再创建复合 user FK。

失败位置和数据形状支持测试方的高可信原因判断：同一 PostgreSQL migration 事务内，带现有 FK 的父子历史行经过批量 UPDATE 后，相关表仍有待处理的约束触发器事件，紧接着 ALTER 该表被 PostgreSQL 拒绝。最终原因仍由执行智能体用执行方回归确认。

## 4. 返修约束

R3 必须保持：

- migration 原子性；失败时不能留下半迁移；
- 合法历史事实、金额、关系和状态不变；
- 所有历史行统一回填唯一 bootstrap owner；
- 非法孤儿或矛盾 owner 继续安全拒绝；
- PostgreSQL/SQLite 最终约束形状与 ORM 一致；
- 三个 P4 revision 和唯一 `p4_host_state` head 不变；
- 不创建第四 revision，因为 P4-A 尚未被接受，冻结允许修正当前三个 P4 migration；
- 不以中途 `COMMIT`、禁用触发器/约束、`session_replication_role`、删历史数据或放宽 NOT NULL/FK 通过。

推荐优先评估 PostgreSQL 专用 DDL 回填：添加 `user_id` 时使用临时的常量 server default 和 NOT NULL，让旧行由 DDL 安全回填，再删除 default；SQLite 继续使用当前受控 rebuild 路径。执行智能体可以采用其他同等安全方案，但必须用真实 PostgreSQL 历史回归证明不会产生 pending-trigger ALTER 冲突，且 migration 仍为一个原子升级。

## 5. 后续门禁

R3 执行方进入 `review` 后，不直接接受 P4-A。总控将固定新产品快照，再派发 `P4-C11-R2` 给测试智能体，只复跑：

1. 原失败 PostgreSQL P3 历史→P4 节点；
2. 必要的相邻 SQLite/PostgreSQL migration 节点；
3. 快照、矩阵和资源收口。

除非 R3 扩大产品影响，不重复 C11 64 项、22 项审计或完整 P0～P4 回归。

## 6. Git 边界

P4-A 仍未完成，因此产品实现、R3 返修和 C11 测试交付暂不提交。总控只提交本核对、R3 Prompt、130 文件起点快照和协调状态；不推送远程、不创建 PR。
