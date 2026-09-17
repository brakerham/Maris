# P1-B3-R1 执行智能体返修 Prompt

```text
你是本项目的执行智能体，唯一负责 P1-B3-R1：修复 P1-C4 首轮独立验收确认的三个数据层缺陷。

这是已有 P1-B3 的限定返修，不是新功能阶段。开始前按顺序读取：
1. AGENTS.md
2. README.md
3. docs/project-coordination.md
4. docs/coordination/README.md
5. docs/coordination/control.md
6. docs/coordination/agents/executor.md
7. docs/phase-1-interface-freeze.md
8. docs/b3-data-running.md
9. docs/testing/phase-1-c4-data-report.md

先核对 control.md 的指令版本和唯一负责人。如果 P1-B3-R1 已取消、暂停、完成或交给别人，立即停止并报告。OpenClaw 安全事件仍暂停：不得恢复、重装、启动网关、修改微信配置或进行真实微信操作。

输入快照：
P1-B3-SHA256:6a1127fd40dd3b1f66c0dc4fd9837cc03c9ceafc0398ca867bb595b686511580

目标：只修复 C4-DATA-001～003，补充执行方回归测试和迁移说明，提交新不可变快照。不得扩展 Agent 工具、FastAPI 财务接口、Markdown 导入、微信、前端或延期的报销/代付/分期功能。

允许修改：
- src/wife_system/finance/**
- migrations/**
- tests/finance/**
- docs/b3-data-running.md
- docs/coordination/agents/executor.md
- 仅在修复确实需要时修改 alembic.ini、pyproject.toml 或 requirements-dev.lock；默认不新增依赖

只读但允许运行：
- tests/independent/finance/**
- docs/testing/phase-1-c4-data-report.md

禁止修改独立测试、C3 矩阵、C4 报告、接口冻结、总览、控制文件、其他角色日志、OpenClaw 文件和 Git 状态。

必须修复：

1. C4-DATA-001，累计退款分类分摊。
   - 当前每次退款都从零独立按比例分配余分，连续小额退款会反复把余分给同一分类。
   - 新算法必须基于“原支出各分录 + 已累计退款 + 本次退款后的累计目标”计算本次增量，使累计全额退款后每条原支出分录恰好归零。
   - 保持 UUID 字符串升序作为稳定余分顺序；不得产生零金额分录；继续保证退款总额、累计上限、幂等和并发锁语义。
   - 增加至少覆盖两类各 1 分、连续两次各 1 分退款，以及多分类多次部分退款的执行方回归。

2. C4-DATA-002，SQLite 金额存储类型完整性。
   - 不能只在 Python/Pydantic 层拒绝；迁移后的 SQLite 数据库必须拒绝向金额列直接写入文本或非整数数值。
   - 设计适用于 SQLite 且不破坏 PostgreSQL BIGINT 的数据库约束，系统性检查所有 `_minor` 金额列，不能只为 `budget_allocation.limit_minor` 打补丁。
   - 使用新的 Alembic revision 修复，不改写已经交接的首个 revision。这样同时建立真实的“前一 revision 带虚拟数据升级到 head”路径。
   - 验证 base→head、旧 revision 带数据→新 head、重复 upgrade、downgrade/rebuild、Alembic check，以及 PostgreSQL 离线 DDL 编译。

3. C4-DATA-003，SQLite 时间时区语义。
   - 所有公开查询 DTO 中表示时间点的 datetime 必须返回 aware UTC；SQLite 驱动返回 naive 值时，在持久化边界或 DTO 映射边界按已保存的 UTC 语义恢复时区。
   - 至少覆盖 list_transactions() 的跨 Asia/Shanghai 月界样例，并检查账户、分类、预算等其他公开时间字段，避免只修一个返回点。
   - 不改变自然月按 Asia/Shanghai 计算的冻结规则。

验证要求：
- 为三个缺陷分别新增 tests/finance/** 执行方回归。
- 运行执行方财务测试、必要的只读独立失败案例、项目全量回归、pip check、compileall 和迁移检查。
- 运行独立案例只用于执行方诊断，不得据此宣布 C4 通过；最终复验仍由测试智能体负责。
- 当前没有真实 PostgreSQL 环境时如实保留未验证项，不安装 Docker/PostgreSQL，不连接未知数据库。
- 使用虚拟数据；日志和文档不得包含密钥、真实账目、账号或原始私人来源 ID。

交付要求：
- 更新 docs/b3-data-running.md，解释三项修复、迁移路径、测试结果、未验证 PostgreSQL 项和行为兼容性。
- 更新 executor.md 的当前快照、里程碑、文件范围、验证证据和交接。
- 对修复后的实现/迁移/执行方测试/依赖文件按既有算法生成新的 SHA-256 快照，列出覆盖文件数。
- 最终状态只能提交 `review`，随后停止；等待测试智能体对 C4-DATA-001～003 和受影响范围定向复验。

停滞规则：同一问题连续错过两个检查点且没有新输出时，在安全位置停止，记录最后有效输出、脱敏错误、已尝试方案、当前文件状态和需要共同决定的问题，不盲目重试。
```
