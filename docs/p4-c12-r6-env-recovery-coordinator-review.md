# P4-C12-R6-ENV 总控核对与恢复断言裁定

2026-10-05，Asia/Shanghai。总控接受公开冷入口 B 的独立通过证据；R6 整个任务仍为 `blocked / finished`。初始故障隔离这一子条件已有证据，不再重复 B。恢复、真实 Windows 和完整 UI-02 尚未完成，LAZY-001 和 P4-B 不关闭。

2026-10-09恢复核对并发布：R6交付及四份源码/首次清单重新复算一致；中断期间不补造执行或心跳。新卡经 `r7_final_readonly` 对实际恢复源码再次只读审阅，未发现阻断发布矛盾；这不是执行结果。

## 首次证据

- [R6 增量报告](testing/phase-4-c12-r6-env-windows-report.md)、[63 项交付清单](../tests/independent/desktop/evidence/r6-env/delivery.sha256)逐项匹配，清单 SHA-256 为 `efb4f2af1539b9133d7701303b485a6fd685262db0ab489e290e1ad7eeb25bfa`。
- 冷源码9、恢复源码5、冷首次9、恢复首次7均匹配。679起点在交付时为675不变、4项授权文档变化、0缺失；总控自己的后续协调变化单列，不算测试方越界。
- delivery使用Python `sorted(Path)` 的目录分段顺序，不是完整POSIX路径字符串的Ordinal顺序；普通文件摘要及逐项字节均正确，不改首次清单。原主报告/人工清单字节前缀保持，各追加1,034字节；矩阵120 ID/12列及原案例行保持。
- [B 结果](../tests/independent/desktop/evidence/r6-env/cold/result.json)是首次1 passed。实际main一次，持续故障模块求值一次；同样本的安全错误提示、Shell、导航和Agent面板四条断言通过，来源与公开结果分别计算。安全、退订、DOM/global恢复通过。jsdom实际加载约18.178秒，初始化约22.479秒，整次约25.881秒，未触及新预算。
- 这个时长说明本次环境准备确实超过旧15秒上限，但加载入口也改变了，不能因此声称旧超时根因已经查明。
- [恢复结果](../tests/independent/desktop/evidence/r6-env/recovery/result.json)为1 failed、1条AssertionError、timeout=false；[恢复journal](../tests/independent/desktop/evidence/r6-env/recovery/worker.journal.jsonl)只有第1组进入和失败，没有具体失败比较。第2～5组、兼容、Windows未运行。
- 四个登记CLI/worker已在执行后的定向检查确认退出；worker自身exit code及完整历史后代仍未核实。不得从root exit0/1推定worker同值，也不将局部核实写全系统零残留。

只读子审查 `r6_evidence_audit` 核对交付、首次记录和资源边界；`r6_recovery_audit` 核对断言顺序、产品入口及合同。总控与子任务均未运行测试或产品。

## 已确认的问题在记录方式，产品归因仍待补证

[恢复 reporter](../tests/independent/desktop/r6-env-recovery-reporter.mjs)仅保留错误类型、数量和timeout；[恢复测试](../tests/independent/desktop/r6-env-recovery.test.tsx)的catch只写组号。该组合丢失了能安全保存的断言ID、运算符、期望与实际值。清理数据和极短失败耗时不能恢复具体比较值，不能猜成“实际加载两次”或新的产品P1。

下一任务必须在每个断言执行前后即时记录安全比较值，而非再次依赖结束时读取raw Error。DOM/对象只保存存在、同一性和泄漏类别等布尔，计数存有限数字，路由/主题/状态存固定枚举；禁止raw stack、完整DOM、token或私人路径。可解释的失败证据与隐私保护可以同时满足。

## 初始绝对次数的合同裁定

R6恢复第1组包含 `counts.loads === 1`，第2组包含首次重试后的总数 `=== 2`。原 [UI-02](testing/phase-4-modular-agent-host-test-matrix.md) 与 [R4合同](coordination/prompts/p4-c12-r4-lazy-windows-tester.md)要求局部隔离、明确重试、无自动循环和状态保持，没有规定StrictMode初始加载绝对次数必须为1。

实际开发测试直接render DesktopApp，独立恢复则显式包裹StrictMode；产品ModuleIndex经Navigate跳转。React官方说明StrictMode开发检查包含额外的Effect设置/清理周期，不能把不同生命周期环境下的初始次数直接等同。[React StrictMode 文档](https://react.dev/reference/react/StrictMode)

本裁定不是说“两次必然正确”，更不是确认R6失败就来自计数。冻结如下有限调整：

1. 旧R6源码、失败与断言永久保留。新运行仍计算这两个原比较条件，记录真实actual及passed/failed，标为旧绝对计数对照；不冒充原节点复跑通过，不计入独立passed总数。
2. 新产品门禁要求实际初始调用为安全正整数、局部失败可见、固定60ms观察期无额外加载；初始基线只取一次。主题/隐私/runtime操作后且retry前仍须等于这个基线，不能重取更大值掩盖额外加载；用户一次明确retry的调用增量必须严格为1，并实际出现恢复页面。持续失败、重复点击、在途离开、状态/订阅与零额外写入仍严格核对。
3. 只有这两条绝对总数对照允许非阻断。其余原公开/安全/恢复断言均为正式门禁，不允许看到结果后再降级其他断言或调整期望。
4. 仅对照失败且所有实际合同门禁通过时，可同任务继续；实际门禁失败立即停止新的状态改变操作，同一已到达状态的只读断言可收齐后清理。记录不完整属于未验证，不补签通过。

这样保留原首次失败，同时按已冻结的产品要求判断下一次真实行为。明确重试的次数限制没有放宽，也不删除StrictMode、改变初始hash或替换产品Router来获得通过。

## 下一任务与停止点

发布 [P4-C12-R7-RECOVERY](coordination/prompts/p4-c12-r7-recovery-tester.md)，既有测试智能体唯一负责人。只新增恢复取证与必要记录工具，沿用已验证原生环境；不重复B/P/A/D16，不修改产品、依赖或打包。新的恢复生命周期一次，按预先列出的5组场景逐项执行；通过后同任务接必要兼容及原Windows未完成范围。

新 [固定起点](coordination/snapshots/p4-c12-r7-recovery-start.sha256)按当前字节生成。新任务ready/waiting_user，实际接单unverified，原测试交付状态不改；长期执行和技术顾问继续停止。本地仅保存公开子条件通过与恢复仍阻塞的检查点，不推送或宣布P4-B complete。正式前端阶段之前的参考图、模型与token提醒门禁保持。
