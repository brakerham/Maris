# P4-B6-R2 最终执行方交付总控核对

## 1. 结论

- 核对时间：`2026-09-26 22:32 Asia/Shanghai`
- 总控结论：接受 `P4-B6-R2` 的最终执行方交付作为 `P4-C11` 独立验收输入。
- 状态边界：R1、R2、S1、S2、T1、T2 均保持执行方 `review / finished`；本结论不表示 P4-A `complete`。
- 下一任务：`P4-C11`，由用户侧边栏中的既有测试智能体绑定 105 文件固定快照执行独立验收。

总控没有重复运行 T2 的 17 个 PostgreSQL 用例。执行方报告、104 文件前后快照、逐文件摘要、Docker 资源收口和实际工作区一致，没有需要定向复现的矛盾。

## 2. T2 证据核对

执行方按 T2 任务卡运行了 17 个唯一真实 PostgreSQL 用例：

| 范围 | 唯一用例 | 结果 |
| --- | ---: | --- |
| T1 修复的精确 Host R1 竞争绑定节点 | 1 | `1 passed` |
| Host R1 其余节点 | 7 | `7 passed` |
| Host R2 完整文件 | 9 | `9 passed` |
| 合计 | 17 | `17 passed, 0 failed, 0 skipped` |

精确节点只运行一次；第二组通过 `-k "not competing_binding_codes_return_safe_replayable_conflict"` 排除它。实际证据确认 `[200,409]`、败方 code 保持 active/attempts=0、同键 409 重放、撤销赢家后新键成功和隐私断言。

T1 的 pytest monkeypatch 在精确节点 teardown 后恢复；随后 R1 其余 7 项和不依赖该时钟的 R2 9 项全部通过，形成跨文件恢复证据。

## 3. 快照与文件边界

T2 起点与终点均为：

```text
entries=104
matched=104
missing=0
mismatch=0
manifest_sha256=c7deef5af25f2ba6215bdd587fe13d46d027ecb37294bc9373a6aadf4c03529d
```

总控直接从当前工作区逐项复算得到相同结果。

执行方交付摘要也匹配：

```text
docs/b6-r2-s2-t2-postgresql-running.md
59e07d0c5cd870a59d0599db032c7f2f6065a0d7d2b951e7e6c836737f54358c

docs/coordination/agents/executor.md
ea76721e2a6f53f326c292404ac1a100538340a41ecf812ae854429463e06029
```

T2 没有修改 104 文件中的产品、migration、执行方测试、依赖、Compose、冻结或既有运行说明。只新增 T2 运行说明并更新执行角色日志。

总控把 T2 运行说明加入最终 R2 输入，形成 C11 的 105 文件普通摘要清单：

```text
docs/coordination/snapshots/p4-c11-start.sha256
entries=105
manifest_sha256=65ee400893171d6caf19f2bf5adf20a4432f1f3c8048d5c381b718fc10360126
```

独立测试路径不在这 105 项产品快照中，因此测试智能体可以在授权范围内新增 P4 独立测试并升级旧独立 fixture，同时持续证明产品快照零漂移。

## 4. Docker 与 PostgreSQL 资源

- Docker Desktop：`4.92.0 (240144)`；
- Engine：client/server `29.8.0 / 29.8.0`，Linux；
- 唯一项目服务：`finance-postgres`；
- 镜像：`postgres:17.6-alpine`；
- 端口：仅 `127.0.0.1:55432`；
- 测试：UUID 随机 schema 与虚拟身份/业务数据；
- 收口：普通 `docker compose down` 退出 0，容器和项目网络正常移除；
- 最终：`docker compose ps --format json` 退出 0 且无输出。

没有执行 `down -v`、volume 删除、prune、Factory reset、Docker Desktop 重启、全局设置/context 修改或 socket 操作。

## 5. C11 进入条件核对

| 进入条件 | 结果 |
| --- | --- |
| D10 已接受并发布 P4-IF-002 | 满足 |
| R1 达到 review、真实 PostgreSQL 门禁通过 | 满足，含 F1 竞争绑定返修证据 |
| R2 从总控固定 R1 快照顺序执行并达到 review | 满足，含 S1、S2、T1、T2 交接链 |
| 8 个 P0、14 个 P1 均有实现/执行测试映射 | 满足执行方进入条件；C11 仍需独立复现 |
| 三个 P4 migration、单 head、SQLite/PG/降级证据 | 满足执行方进入条件；C11 仍需独立验证 |
| 旧 P0～P3 fixture 与 PostgreSQL 基线有明确结果 | 满足执行方进入条件；C11 执行合并兼容回归 |
| 最终 R2 文件数和摘要可复算 | 满足，105 项固定 |
| 无未说明产品/依赖/执行测试漂移 | 满足 |
| Docker 负责人和清理方式明确 | 满足；C11 期间测试智能体是唯一 `finance-postgres` 负责人 |

## 6. C11 独立验收边界

C11 必须：

1. 执行 P4-A 64 项矩阵，按 REG 10、PRF 10、AUT 10、ISO 8、WFL 10、MEM 8、DB 8 映射实际证据；
2. 独立覆盖接管审计的 8 个 P0 和 14 个 P1，可与 64 项共享测试，但必须逐项映射；
3. 运行 P0～P3 代表兼容回归和执行方 P4 回归；
4. 验证 SQLite/Alembic 空库、完整 P0～P3 虚拟历史、单 head、允许降级与实际约束；
5. 使用真实 PostgreSQL 独立验证认证、user scope、复合 FK、并发、事务恢复、memory/setting/event、分页和 production factory；
6. 保持 105 文件产品快照前后完全匹配；
7. 不操作 Electron、OpenClaw、微信、DeepSeek、真实 provider、真实密钥、账户、行情或个人数据；
8. 发现产品 P0/P1 时只提交最小复现，不修改产品；
9. 最终只提交独立报告和 `review`，由总控决定 P4-A 是否 `complete` 及 Git 提交。

## 7. Git 边界

R2 当前只有执行方 `review`，尚未完成 C11 独立验收，因此总控不提交 P4 产品实现。C11 通过且无开放 P0/P1 后，总控才按用户规则创建本地验收提交；当前不推送远程、不创建 PR。
