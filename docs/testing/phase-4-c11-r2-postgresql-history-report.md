# P4-C11-R2 PostgreSQL 历史迁移定向独立复验报告

- 角色：测试智能体
- 任务：`P4-C11-R2`
- 控制版本：`2026-09-27T12:19:00+08:00`
- 最终状态：`review / finished`
- 数据边界：仅虚拟用户、虚拟财务数据和随机 PostgreSQL schema
- 结论权限：本报告给出独立复验结论和关闭建议；P4-A 的最终接受、`complete` 与 Git 处理属于头脑风暴总控

## 1. 结论

执行方 `P4-B6-R3-R1-E1` 对 `P4-C11-R1-PG-001` 的修复通过本轮有限独立复验。原失败 PostgreSQL P3 历史正向升级节点按任务卡只实际运行一次并通过；P1 双分录、P2 run/pending、P3 import batch/candidate 可到达唯一 `p4_host_state`，真实复合约束、非空、临时默认值清除、重复 upgrade 和 head→P3→head 均符合冻结合同，原 `ObjectInUse` 未再出现。

测试方新增的两个非法 P3 历史场景也通过：孤儿 `pending_action.run_id` 与矛盾 `pending_action.actor_id` 均在任何 P4 user-scope DDL 持久化前安全拒绝。失败后仍为 P3 head，P1 双分录和非法输入原值保持，没有 `app_user` 或部分 `user_id` 列，也没有删除、重归属或自动修复。两类安全诊断可以区分且不含凭据、连接 URL、虚拟记录 ID 或虚拟正文。

所有任务卡限定的相邻 PostgreSQL/SQLite 和执行方兼容回归通过，固定产品、migration 与执行方测试零漂移，Docker 资源已普通关闭且 Compose 为空。本轮没有发现新的 P0/P1 产品缺陷。因此测试方建议关闭 `P4-C11-R1-PG-001`，并把 `P4A-DB-05`、`P4A-DB-06` 更新为 `passed`；P4-A 当前独立矩阵为 64 passed。最终接受仍由总控决定。

## 2. 固定快照

起点清单：`docs/coordination/snapshots/p4-c11-r2-start.sha256`。

| 时点 | entries | matched | 授权变更 | missing | 非授权 mismatch | manifest SHA-256 |
|---|---:|---:|---:|---:|---:|---|
| 开始前 | 133 | 133 | 0 | 0 | 0 | `7ab8388edcadff5515aa5f038df13e40ae35233f2e4298c61fcd091357929fd3` |
| 完成后 | 133 | 129 | 4 | 0 | 0 | `7ab8388edcadff5515aa5f038df13e40ae35233f2e4298c61fcd091357929fd3` |

终点的授权变更仅为本任务允许的测试方文件；清单内所有产品、migration、执行方测试、依赖和配置均逐文件保持起点摘要。E1 两项关键文件起终点均为：

- `migrations/versions/p4_host_user_scope.py`：`82bc31919bd5483650f40c0281c42764813f6f5bc0db8d1898b7ad71a3d5a800`
- `tests/host/test_postgresql_r2.py`：`0da6346142304f36964370b8f48344c6ab16309058413ffa6bb45d24ae922d6f`

E1 的 131 文件终点摘要输入仍为 `a89874cfb48b5c8edc8f4260d2f6ce1f206ac02f61e31bb56f4b33ea1282eee9`；本任务没有修改这 131 个产品/执行测试输入中的任何文件。

## 3. 原失败节点

唯一实际运行一次：

```text
tests/independent/host/test_postgresql_acceptance.py::test_c11_pg_p3_history_forward_upgrade_preserves_p1_p2_p3_facts
```

结果：`1 passed, 0 failed, 0 skipped, 1 warning`。

独立断言证明：

- P3 head 中包含 P1 account/category/posted expense/正负双分录、P2 paused run 与 needs-confirmation pending 双向引用、P3 previewed import batch/create candidate；
- 升级后只有一个 `p4_host_state` 版本行，所有代表 ID、状态、金额 `-4321/+4321` 和 import 金额 `2500` 原值保持；
- owner/actor/user 统一回填唯一 bootstrap owner，代表 scoped 表无 NULL user；
- transaction、pending、import 三类复合 user 关系零孤儿；
- 真实 PostgreSQL catalog 中相关复合 FK、`(user_id,id)` unique 和 actor/owner check 存在；
- 检查的 `user_id` 列均为 NOT NULL 且 server default 为 `None`；
- 对 head 的重复 upgrade 安全；head→P3→head 后双分录、run/pending 双向引用、状态和 import 金额继续保持；
- 全程未再出现 `ObjectInUse` 或 pending trigger ALTER 失败。

## 4. 非法历史原子拒绝

节点：

```text
tests/independent/host/test_postgresql_acceptance.py::test_c11_pg_p3_invalid_history_is_rejected_before_user_scope_ddl
```

结果：`2 passed, 0 failed, 0 skipped, 1 warning`。

| 场景 | 构造 | 预期诊断 | 原子回滚证据 |
|---|---|---|---|
| orphaned pending run | 仅在隔离随机 schema 的测试准备中删除旧单 ID FK，再把 `pending_action.run_id` 指向随机不存在 UUID | `rejected orphaned legacy relationships` | P3 head、非法 run ID、原 actor、双分录与记录数量保持；无 app_user、无代表 scoped `user_id` 列 |
| contradictory pending owner | 保留 run 引用，把 `pending_action.actor_id` 改为与唯一 bootstrap owner 不同的随机 UUID | `rejected contradictory legacy owners` | P3 head、原 run ID、矛盾 actor、双分录与记录数量保持；无 app_user、无代表 scoped `user_id` 列 |

错误正文额外断言不含随机非法 UUID、`virtual` 数据正文、`password`、`postgresql://` 或 `@` 连接信息。孤儿准备对 FK 的改动只发生在随机测试 schema；产品 migration、Compose 和项目配置均未改变。

## 5. 相邻回归与静态门禁

| 分组 | 结果 | warning | 说明 |
|---|---:|---:|---|
| 独立 PostgreSQL round-trip/catalog 精确节点 | 1 passed | 1 | 真实约束目录与跨 user FK 生效 |
| 独立 Host SQLite migration 完整文件 | 3 passed | 15 | P4 空库、head→P3→head、P3 历史正向升级 |
| 执行方 `tests/host/test_postgresql_r2.py` | 11 passed | 1 | 单独统计；含 E1 历史和非法图执行方证据 |
| 执行方 `tests/host/test_migrations.py` | 8 passed | 0 | 单独统计；SQLite 相邻兼容 |
| 修改后独立测试编译 | passed | 0 | Python `compile(..., 'exec')`，无生成文件 |
| `pip check` | passed | 0 | `No broken requirements found.` |
| `git diff --check` | passed | 既有行尾提示 | 退出 0，无 whitespace error；未执行 Git 写操作 |

pytest 成功案例按唯一测试项统计为：独立 PostgreSQL 4、独立 SQLite 3、执行方 PostgreSQL 11、执行方 SQLite 8，共 26 passed、0 failed、0 skipped。执行方 19 项与独立 7 项分开解释，执行方结果不替代独立结论。

独立 SQLite 文件首次启动得到 `3 setup errors`，原因是 pytest 创建 `--basetemp` 子目录时仓库内父目录不存在；没有任何测试函数进入断言。创建专用父目录后，同一完整文件一次重跑为 3 passed。该首次结果作为测试基础设施证据保留，不归类为产品失败，也没有以重试覆盖业务断言失败。

warning 均为既有 Starlette/AnyIO alias 与 Python sqlite3 datetime adapter 弃用提示；没有产品 warning。

## 6. Docker 与资源收口

- Docker Engine client/server：`29.8.0`，server OS 为 Linux。
- Compose 配置只包含 `finance-postgres`；启动前为 `COMPOSE_SERVICES_EMPTY_AT_START`。
- 只运行 `docker compose up -d finance-postgres`；唯一服务达到 `running / healthy`。
- 凭据只从 `compose.yaml` 的解析结果注入单个 pytest 进程环境；报告、角色日志和命令输出均未记录连接密码或完整 URL。
- 所有 PostgreSQL 测试使用随机 schema 与虚拟数据，fixture 结束后删除各自随机 schema。
- 停止前重新读取同一版 control；随后执行普通 `docker compose down`，容器和项目网络均移除，最终为 `COMPOSE_SERVICES_EMPTY`。
- 未使用 `-v`，未删除 volume、prune、数据库 reset、Factory reset、Desktop 启停、context/全局设置或 socket 操作。

## 7. 缺陷与矩阵结论

`P4-C11-R1-PG-001` 的原始 P0 复现是合法 P3 历史在 `financial_transaction.user_id SET NOT NULL` 阶段触发 PostgreSQL `ObjectInUse`。本轮固定 E1 修复输入中，原独立节点一次通过，且非法历史在 DDL 前原子拒绝、相邻回归全绿、固定产品零漂移、资源安全收口，因此测试方建议关闭该缺陷。

| 矩阵项 | R1 状态 | R2 状态 | 依据 |
|---|---|---|---|
| `P4A-DB-05` | failed | passed | 合法 P1/P2/P3 历史可完整升级，真实 catalog、重复 upgrade 与往返保持通过 |
| `P4A-DB-06` | failed | passed | 合法数据保持；孤儿和矛盾 owner 两类损坏历史均安全阻断并完整回滚 |

更新后 P4-A 为 64 passed、0 failed、0 blocked、0 not_run；P4-B/C/D 的 56 项继续 `not_run`。这只是测试方建议和矩阵证据更新，不自行宣布 P4-A `complete`。

## 8. 隐私、未运行范围与边界

- 只使用虚拟名称、虚拟金额、随机 UUID 和随机 schema；未读取、打印或保存真实个人、财务、渠道或账户数据。
- 迁移拒绝诊断按安全字符串断言，不含凭据、完整数据库 URL、随机损坏 ID 或虚拟正文。
- 未运行完整 C11、其余四个独立 Host PostgreSQL 业务节点、P0～P3 全量、认证/并发/Agent/memory/API 全量、Finance 或 Activity Import 全量。
- 未启动 Electron、OpenClaw、微信、DeepSeek、真实 provider 或外部登录；未安装依赖。
- 未修改 `src/**`、migration、执行方测试、依赖、Compose、接口冻结、control、overview、snapshot、其他角色状态或 Git 状态。

## 9. 测试方文件与 SHA-256

| 文件 | R2 终点 SHA-256 | 说明 |
|---|---|---|
| `tests/independent/host/test_postgresql_acceptance.py` | `9989bac66436c4a9af7aa17c679b396f4d87b0f62fff0a85b00295e9cc51d6f4` | 本轮补强并实际执行 |
| `tests/independent/host/history_fixtures.py` | `1cbae0fae892a23b6d7dfa0c6c36d5f2799bd8f22c38bcfcc6c6e7431779b796` | 授权可改但本轮保持不变 |
| `docs/testing/phase-4-modular-agent-host-test-matrix.md` | `ed6bc4a33f19986457c2e0d472bb223a09650a514c530946a2dac3fec33d993c` | DB-05/06 更新为 passed |
| `docs/testing/phase-4-c11-host-foundation-report.md` | `a300266627c96b9d47d5a4842a1d08434778d403c3753f729856b92ed3daae0b` | 同步 R2 结论 |
| `docs/testing/phase-4-c11-r2-postgresql-history-report.md` | 最终普通摘要记录在 tester 完成日志和交付消息 | 避免报告内自引用改变自身摘要 |
| `docs/coordination/agents/tester.md` | 最终普通摘要记录在交付消息 | 完成日志写入后再计算 |

`history_fixtures.py` 没有修改。除上表、本 R2 新报告和 tester 状态外，没有其他测试方文件变化。

## 10. 测试方结论

在固定 E1 产品输入上，合法历史正向升级、非法历史原子拒绝、真实 PostgreSQL 约束、SQLite 相邻迁移和两份执行方兼容回归全部通过。测试方建议关闭 `P4-C11-R1-PG-001`，接受 `P4A-DB-05/06` 为 passed，并由总控据此决定 P4-A 是否完成。

本任务停在 `review / finished`。测试智能体没有修改产品或 migration，没有执行 Git 写操作，也不继续扩大回归范围。
