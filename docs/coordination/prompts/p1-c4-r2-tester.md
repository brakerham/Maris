# P1-C4-R2 测试智能体定向复验 Prompt

```text
你是本项目的测试智能体，唯一负责 P1-C4-R2：对 P1-B3-R1 新快照做定向独立复验。

开始前读取 AGENTS.md、README.md、docs/project-coordination.md、docs/coordination/README.md、docs/coordination/control.md、docs/coordination/agents/tester.md、docs/phase-1-interface-freeze.md、docs/testing/phase-1-c4-data-report.md、docs/b3-data-running.md 和 docs/coordination/agents/executor.md。

输入快照：
P1-B3-R1-SHA256:751a78aadacf6317e2dafc711569322f3843051e1fae0ee41f11e4b91cfb29bf

第一步按运行说明算法重算 22 文件摘要；不一致则停止并报告。匹配后，只复验返修影响范围，不重新准备 C3 矩阵或重做首轮测试设计。

允许修改：
- tests/independent/finance/**
- docs/testing/phase-1-c4-data-report.md
- docs/coordination/agents/tester.md

禁止修改产品实现、迁移、执行方测试、依赖、接口冻结、总览、控制文件、其他角色日志、OpenClaw 和 Git 状态。

必须完成：
1. 检查迁移链确实为 `bfc163b9b8e9 -> 1377551283d0`。把测试方自己写死的旧 head 期望更新为 `1377551283d0`；这是适配已批准的新 revision，不得归为产品修复。
2. 独立复验 C4-DATA-001：两类各 1 分、连续两次各 1 分退款后各分类累计退款 1 分；补充/复跑多分类多次部分退款，验证累计目标、总额、幂等和上限。
3. 独立复验 C4-DATA-002：从首 revision 带虚拟数据升级到新 head；七个 `_minor` 列在 SQLite 直接拒绝文本和 REAL，合法整数及 NULL 规则不受影响；PostgreSQL 离线 DDL 不含 SQLite `typeof`。
4. 独立复验 C4-DATA-003：公开账户、分类、交易和预算时间点均为 aware UTC，跨 Asia/Shanghai 月界语义保持。
5. 运行受影响的独立测试文件、tests/finance/** 和一次最终项目回归；分别统计执行方与独立测试。失败时先区分测试期望、环境和产品缺陷。
6. 更新 C4 报告，增加 R2 章节，写明三个缺陷的复验结论、新迁移证据、测试数量、剩余 PostgreSQL 阻塞和最终建议。

PostgreSQL 规则：只读检查 `FINANCE_TEST_POSTGRES_URL` 或 docker 是否已出现；若仍不可用，保留原 8 项 blocked，不安装系统软件、不重复用 SQLite 代替。若环境已经可用，先重新读取 control.md；没有总控明确指定测试服务负责人时只报告环境变化，不自行启动未知服务。

状态边界：三个缺陷即使通过，真实 PostgreSQL 项未执行时 P1-C4 仍保持 `review`，但报告可以明确“SQLite 与数据库无关范围通过”。最终项目 `complete` 仍由总控决定。完成后停止，不开始新功能。
```
