# P2-C6：P2-A 财务 Agent 独立验收报告

- 任务：`P2-C6`
- 结论状态：`review`
- 控制版本：`2026-09-17T00:35:00+08:00`
- 输入快照：`P2-B4-SHA256:f0eacf340d87f7dd0ea11ae51396f5022cec99dc0f3a3009883b30aaf17362e6`
- 数据边界：全程只使用虚拟身份、虚拟消息、虚拟账户、虚拟分类、虚拟金额、隔离 SQLite 和脱敏 canary

## 结论

P2-B4 的 23 文件摘要与交接值完全一致。当前可执行的 SS 与 TestClient HTTP 范围没有发现 P2 产品缺陷：独立 P2 套件累计 45 项通过，执行方 P2 套件在最终回归中 23 项全部通过。可信上下文、六工具 Schema、五个查询、候选状态机、来源幂等、并发确认、4/8/1 限制、故障恢复、HTTP 合同、隐私和 P1 账本一致性取得本地证据。

本报告不能把 P2-A 标为 `complete`。真实 PostgreSQL、DeepSeek、桌面端和微信环境没有执行；HTTP-09 的 Agent 真实回环断线场景也没有取得完整证据。最终项目回归另有两项既有 Phase-0 回环 HTTP 用例因 uvicorn 未在 8 秒内健康而失败，因此项目全回归不是全绿。P2-C6 最高只提交 `review`，最终验收归头脑风暴总控。

## 快照与迁移门禁

按 `docs/p2-a-running.md` 的 POSIX 相对路径、Unicode 排序、路径/内容长度大端编码算法重算 23 文件摘要，结果精确匹配交接值。摘要覆盖的产品、迁移和执行方 P2 测试保持只读。

隔离 SQLite 实际迁移链为：

`base -> bfc163b9b8e9 -> 1377551283d0 -> 7f3e2d1c9a4b`

P2 head 为 `7f3e2d1c9a4b`，head 下有 19 张业务表并含 `agent_run`、`pending_action`。测试维护选择让 P1 专项固定升级到 P1 head `1377551283d0`，继续断言 P1 的 17 张表；P2 迁移测试单独断言完整 head、19 张表、升级重复、降级和重建。这样既消除了 P2 新 head 导致的陈旧预期，也没有把 P1 的表集合断言放宽。

迁移维护套件结果为 11 通过、8 跳过；8 项跳过均需要真实 PostgreSQL，未以 SQLite 或离线 DDL 冒充目标库通过。

## 独立执行结果

| 范围 | 结果 | 证据 |
| --- | --- | --- |
| P2 独立稳定套件 | 43 通过、0 失败 | `tests/independent/agent_finance/` 完整定向运行 |
| 最后补充边界 | 2 通过、0 失败 | CTX-05 模型等待期间连接释放；ACT-15 活动资源仅版本变化后 stale |
| 独立 P2 累计 | 45 通过、0 失败 | 三个测试文件及独立 fixture |
| 执行方 P2 | 23 通过、0 失败 | 最终项目回归中的 `tests/agent_finance/` |
| 迁移维护 | 11 通过、8 跳过 | P1 固定 head 与真实 PostgreSQL 条件项 |
| 最终项目回归 | 305 通过、8 跳过、2 失败，共 315 项 | P2 独立 43 + 执行方 P2 23 + 其他回归 249 |

独立案例按 C5 ID 的状态已逐行写回 `docs/testing/phase-2-agent-test-matrix.md`。71 个案例取得当前本地 SS/HTTP 预期的通过证据；混合环境案例只认定本地部分。以下 13 个案例没有完整执行：

- `DB-03`：仅真实 PostgreSQL 可证明提交成功但响应丢失后的双连接恢复。
- `WX-01`～`WX-05`：OpenClaw 安全暂停且无授权，不执行微信。
- `LIVE-01`～`LIVE-03`：未获准联网调用真实 DeepSeek。
- `DSK-01`～`DSK-03`：没有桌面测试构建或交互环境。
- `HTTP-09`：同源并发重放组件已通过，但 Agent 真实回环断线重试未执行。

## 覆盖映射

| C5 范围 | 独立证据 |
| --- | --- |
| `CTX-01`～`CTX-05` | Schema 禁止字段、参数覆盖拒绝、可信时区/不可变上下文、模型等待时连接池零占用 |
| `QRY-01`～`QRY-07` | 五查询与 P1 直接结果对照、整数分/CNY、边界参数、权限隐藏与拒绝 |
| `ACT-01`～`ACT-16` | 候选/追问/数据库选项、计划保护、相对日期、多笔拒绝、摘要、补充、取消、过期、身份、归档与版本 stale |
| `IDM-01`～`IDM-10` | 同键重放/冲突、不同键、可信提交键、顺序和并发确认、重启恢复、单交易/单收据 |
| `LOOP-01`～`LOOP-11` | 临时/永久模型故障、坏参数、未知/重复工具、4 轮/8 调用/1 写限制、空响应、权限与提交恢复 |
| `DB-01`～`DB-02`、`DB-04` | run 前不可用、确认时未知异常、无虚假 committed、同 pending 恢复成功、canary 不外泄 |
| `HTTP-01`～`HTTP-08` | run/resume/status、严格请求、身份隔离、缺失/不可用、安全错误信封、重复确认 |
| `PRV-01`～`PRV-05` | 结构化日志、响应/日志/持久化 canary 扫描、来源摘要、无原消息/密钥/SQL/路径 |
| `P1-01`～`P1-06` | 1800 分、CNY、真实 result ID、余额 98200 分、单交易/单收据、查询/快照与 stale |

## 最终回归失败与限制

最终全项目回归在修复独立测试包名收集冲突后实际收集 315 项。结果中的两项失败为：

1. `tests/independent/test_c2_b2_api.py::test_h06_client_timeout_then_retry_replays_completed_record`
2. `tests/independent/test_c2_b2_api.py::test_w04_and_restart_boundary_over_real_loopback_http`

两者都在 `_wait_for_health` 阶段失败，分别报告 `uvicorn did not become healthy: timed out` 和 `uvicorn did not become healthy: None`，未进入探针业务断言。它们属于既有 Phase-0 真实回环测试；本任务未修改对应实现或测试，也未把失败归为 P2 产品缺陷。按单次全项目回归约束没有再次执行整套回归。另有 1 个既有 Starlette/AnyIO `BlockingPortal` 弃用警告。

## 未执行范围与交接

- 不安装、启动或连接 PostgreSQL；P1 原有 8 个真实 PostgreSQL 结论继续阻塞。
- 不联网调用 DeepSeek，不使用 API key。
- 不恢复 OpenClaw、不重启网关、不扫码、不操作真实微信。
- 不测试收入、转账、退款、预算写入等 P2-A 冻结范围外的自然语言写工具。
- 不修改产品、迁移、执行方 P2 测试、依赖、接口冻结、控制文件、总览、其他角色日志或 Git 状态。

建议总控将 P2-A 记录为“本地 SS/TestClient HTTP 通过，外部环境与 HTTP-09 真实回环证据未完成”，并单独决定是否需要复现两项 Phase-0 回环失败。任何后续返修都应提供新的固定快照，再由测试智能体做定向复验。