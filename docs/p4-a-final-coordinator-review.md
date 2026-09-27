# P4-A Host 地基最终总控验收

## 结论

- 验收时间：2026-09-27 12:55 Asia/Shanghai
- 验收角色：头脑风暴总控
- 阶段：P4-A Host、身份和通用状态地基
- 最终状态：`complete`
- P4-A 独立矩阵：64 passed、0 failed、0 blocked、0 not_run
- P4-B、P4-C、P4-D：56 not_run，未因 P4-A 完成而提前宣称实现
- P0 缺陷 `P4-C11-R1-PG-001`：关闭
- PostgreSQL 矩阵 `P4A-DB-05`、`P4A-DB-06`：接受为 `passed`

P4-A 已完成实现、自测、独立验收、真实 PostgreSQL 历史迁移返修和定向独立复验。现有证据满足接口冻结、D10 返修裁定和 C10 矩阵中 P4-A 的全部 64 项。总控接受该切片并按项目 Git 规则创建本地提交；不推送远程，不启动正式发布或 PR-only 流程。

## 最终固定快照

```text
docs/coordination/snapshots/p4-a-final.sha256
entries=134
matched=134
mismatch=0
missing=0
manifest_sha256=1e9b3037d2a963522a0250f4f4573b112053b6d8c20f7495bbe7bd4a238c6f0a
```

快照固定 P4-A 产品代码、三个 P4 migration、执行方测试、独立测试、迁移历史 fixture、执行/测试报告和测试角色最终状态。协调控制文件、总控角色日志和本验收说明不纳入产品快照，避免协调更新造成伪漂移。

关键 E1 文件：

| 文件 | SHA-256 |
| --- | --- |
| `migrations/versions/p4_host_user_scope.py` | `82bc31919bd5483650f40c0281c42764813f6f5bc0db8d1898b7ad71a3d5a800` |
| `tests/host/test_postgresql_r2.py` | `0da6346142304f36964370b8f48344c6ab16309058413ffa6bb45d24ae922d6f` |
| `docs/testing/phase-4-c11-r2-postgresql-history-report.md` | `dc9eb8f8ac9c89880e97636f1f6bb60c7049e607abdb2b02c1b786baf9339fcf` |
| `docs/testing/phase-4-c11-host-foundation-report.md` | `a300266627c96b9d47d5a4842a1d08434778d403c3753f729856b92ed3daae0b` |
| `docs/testing/phase-4-modular-agent-host-test-matrix.md` | `ed6bc4a33f19986457c2e0d472bb223a09650a514c530946a2dac3fec33d993c` |
| `tests/independent/host/test_postgresql_acceptance.py` | `9989bac66436c4a9af7aa17c679b396f4d87b0f62fff0a85b00295e9cc51d6f4` |

## 最后缺陷闭环

`P4-C11-R1-PG-001` 的原始失败路径是：真实 PostgreSQL P3 schema 含 P1 transaction/双分录、P2 run/pending 和 P3 import 历史；旧 `p4_host_user_scope` 在同一事务先 UPDATE 外键相关历史行，随后执行 `ALTER financial_transaction.user_id SET NOT NULL`，PostgreSQL 因 pending trigger events 返回 `ObjectInUse`。

E1 在原 migration 上唯一复现该失败并证明整个 Alembic revision 完整回滚。修复只改变 PostgreSQL 历史填充路径：使用经 `uuid.UUID` 验证的唯一 bootstrap owner 作为迁移期常量 server default，在一条 ADD COLUMN DDL 中建立 UUID、历史值和 NOT NULL，随后立即移除 default，再建立 unique、FK、check 和复合 user 关系。SQLite 的 nullable + 参数化 UPDATE + batch rebuild 路径保持不变。

执行方修复后门禁：30 passed、0 failed、0 skipped。C11-R2 独立复验：

- 原失败 PostgreSQL 历史节点：1 passed；
- 独立非法历史两参数场景：2 passed；
- 相邻 PostgreSQL round-trip/catalog：1 passed；
- 独立 Host SQLite migration：3 passed；
- 执行方 PostgreSQL 兼容：11 passed；
- 执行方 SQLite 兼容：8 passed；
- 合计：独立 7 passed，执行兼容 19 passed，26 passed、0 failed、0 skipped。

独立证据证明合法 P1/P2/P3 历史可到达唯一 `p4_host_state`，金额、双分录、状态、引用和 import 金额保持；所有代表事实归属唯一 bootstrap owner；复合 user FK、unique、check 和 NOT NULL 在真实 catalog 中生效；最终没有 persistent server default；重复 upgrade 和 head→P3→head 保持历史。

孤儿 `pending_action.run_id` 和矛盾 `pending_action.actor_id` 均在 P4 user-scope DDL 持久化前被安全拒绝。失败后仍为 P3 head，双分录与非法原值保持，没有 `app_user` 或部分 `user_id` 列，也没有删除、重归属或自动修复。

## 其他验收证据

原 C11 已覆盖 P4-A 合同、API、SQLite、真实 PostgreSQL、身份、session、绑定、receipt、setting、memory、run/pending、lease、恢复、分页 cursor、production factory 和 P0～P3 兼容。C11-R1 修复了历史迁移证据缺口，C11-R2 只复验由该缺口发现的产品迁移缺陷和相邻范围，没有重复完整 C11。

矩阵程序化检查：120 行、120 个唯一 ID；P4-A 64 passed，P4-B/C/D 56 not_run。没有把未实现的桌面 Shell、驾驶舱、聊天 UI、毛毛、wealth 模块或 Electron 能力记为完成。

C11-R2 执行期间只启动 `finance-postgres`，使用随机 schema 和虚拟数据；普通 `docker compose down` 后最终项目 Compose 为空。没有删除 volume、prune、数据库 reset、Factory reset 或修改 Desktop 设置。没有访问 Electron、OpenClaw、微信、DeepSeek、真实 provider、密钥、账户或个人财务数据。

## 已知非阻塞事项

- 原 P0 独立回归中两个 Windows 真实回环测试曾在固定 8 秒内等待 uvicorn 健康失败；该现象在 P2-C6 和 C11 均记录为既有测试基础设施问题，同一虚拟目标可启动，没有形成 P4-A 产品缺陷。后续改动回环基础设施时另立任务，不为关闭 P4-A 重复全量测试。
- Starlette/AnyIO alias 与 Python sqlite3 datetime adapter 的弃用 warning 保留；没有屏蔽 warning，也没有产品断言失败。
- Docker Desktop 4.91 的 AF_UNIX socket 启动问题已通过升级 4.92.0 恢复；R3/R3-R1 两次环境停止没有修改产品。E1 与 C11-R2 均在 Engine 29.8.0 上完成并安全收口。
- 当前产品范围仍为单机、单主人、本地数据库。公众注册、第二用户、云账户、跨主机登录和常规登录 UI 保持暂停。

## 下一阶段边界

P4-A 只完成 Host 地基。P4-B、P4-C、P4-D 仍未执行：桌面 Shell、可视化驾驶舱、聊天与毛毛、第二模块和财富管理扩展必须分别冻结接口、实现和独立验收，不能因本次地基完成而跳过。

下一步由头脑风暴总控先整理 P4-B 的最小纵向切片、技术选项、用户可见效果和文件所有权；在新 Prompt 发布前，执行智能体、测试智能体和技术顾问均停止。
