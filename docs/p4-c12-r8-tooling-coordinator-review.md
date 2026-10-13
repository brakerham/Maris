# P4-C12-R8-MODULES 总控核对与工具续验裁定

2026-10-14，Asia/Shanghai。R8原交付保持 `blocked / finished`；接受9个已完成节点的有限独立证据，不据此关闭LAZY-001、UI-02或P4-B。不派发产品返修或重新打包。

## 已复算的证据

[R8报告](testing/phase-4-c12-r8-modules-windows-report.md)、实际源码、首次journal与process/result已核对。总控只读复算：

| 清单 | 结果 | SHA-256 |
| --- | --- | --- |
| [R8交付](../tests/independent/desktop/evidence/r8-modules/delivery.sha256) | 29/29匹配 | `3b91fa7a276ab04c671eb1926adf7ca5c20dd8846cc66aa6615cce3427f34f73` |
| [运行前源码](../tests/independent/desktop/evidence/r8-modules/modules-source.sha256) | 7/7匹配；基准independent/desktop | `2e877d54df1e6012ea8509c873b6e3a4042a9a6c773cdb1e317c9ad61973fecc` |
| [首次运行](../tests/independent/desktop/evidence/r8-modules/modules-first.sha256) | 6/6匹配；基准仓库根 | `24aae3eadf70d792213f29488dbee1f5436fb339ffdd0d32e9a876e3dc365760` |

818项原起点在测试方收口时814不变、4项授权文档变化；本轮总控接单后另有本人日志变化。后续总控README、project-coordination、control、overview变化单独列出，不冒充原起点匹配。旧主报告和人工清单相对HEAD均为仅追加，原120个12列案例行和预期保持。

本轮另复算外部R6实际构建源码813/813、EXE、asar与lock，均匹配原冻结值。140产物、67资源、73dist及12443依赖的原逐文件验证由R8 start/end审计保留；总控不再次启动产品或复跑测试。新任务仍按原R8合同核对全部固定输入。

## 首次结果与分类

- R8-01至09实际通过；R8-10 runner失败，11至13未执行。965条journal含395对比较（393个正式比较全部通过，2个标量自检含预期失败）；9个body_pass、10个cleanup。比较数不替代完整节点通过。
- R8-10源码先 `ui('REMOVED.NAV', 'nav a[href="#/alpha"]', false)`，再 `chrome('REMOVED')`；后者展开导航区域的同名 `R8-10.REMOVED.NAV.EXISTS`。唯一性保护在第二次assert_enter之前抛错。旧模块链接不存在已有证据，整个导航区域此时未取样，不能用前一个false冒充后一个结果。
- 原始异常message未保存；上述原因来自冻结源码与journal次序的只读重建，不宣称恢复了丢失日志。reporter仅挑assert_fail/operation_fail，使firstFailure为null；cleanup标记不能替代runner结论。这些都是取证限制，不是产品P1。
- 已登记root30140、worker22216均退出1，无超时或强制终止，CLI5909ms；清理证据范围为登记进程、组件卸载、退订与环境恢复，不外推全系统历史后代。
- 必要兼容28与Windows产品0/8、辅助0/4均未执行。

## 最小更正和后续范围

发布[P4-C12-R8-R1](coordination/prompts/p4-c12-r8-r1-tooling-resume-tester.md)，既有测试智能体唯一负责。在新副本中只把移除模块链接的ID前缀改为 `REMOVED.ALPHA_LINK`，保留导航区域、selector、expected、操作和原业务断言。补安全工具异常记录及node/cleanup分离，不改产品。

R8-10至13各有自己的scenario、DOM、root、bridge、计数与订阅集合，可精确选择这4个节点；不重跑已通过的01至09。R8-13末尾已覆写chrome为FINAL空root检查，原卸载后DOM/读取/订阅要求保留，不增加不必要生命周期改造。

新任务明确授权一次后续纯取证工具更正：仅限稳定诊断已证明是测试记录器/ID/汇总错误、无实际产品或安全断言失败、资源已收口；首次证据和源码冻结，换新attempt，仅重新进入中断节点和其后未执行节点。实际产品失败、未知异常、超时、安全或所有权问题不适用。此授权只作用于新四节点模块suite，不追溯改变旧R8结果。

四节点完成后，同任务继续原28项开发兼容、尚缺公开条件和Windows最多8次/辅助4次计划；旧B、完整R7恢复和旧EXE不重复，不再等待一次纯派单。原人工/设备限制及24项要求保持。真正产品失败仍提交最小证据并停止，不通过分类掩盖。

新任务固定起点见[续验清单](coordination/snapshots/p4-c12-r8-r1-start.sha256)。执行方、顾问停止；新测试ready/waiting_user，实际接单unverified。只保存准确描述未完成状态的本地检查点，不推送。真实前端开始前的参考图和模型策略提醒保持。
