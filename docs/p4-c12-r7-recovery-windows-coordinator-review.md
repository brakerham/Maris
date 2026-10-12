# P4-C12-R7-RECOVERY 总控核对与模块就绪返修裁定

2026-10-12，Asia/Shanghai。接受R7恢复、补充独立结构及必要兼容的有限通过证据；原任务保持 blocked / finished。Windows W1-DAILY-PAGE仍为观察未通过，现场根因未核实；LAZY-001、完整UI-02及P4-B不关闭。

## 已核对的事实

- [R7报告](testing/phase-4-c12-r7-recovery-windows-report.md)与[68项交付](../tests/independent/desktop/evidence/r7-recovery/delivery.sha256)逐项匹配，清单SHA-256 `1357d6c31d7643dc661961ef695b5403da1f3c74c047c99e5378a3252bdbdd0e`。起点743项在测试方终点739保持、4项授权共享测试文档变化；总控自己的后续变化另列。
- 恢复/兼容/结构/Windows源码清单分别7/4/5/3项，首次清单分别7/5/6/2项匹配。恢复journal529条连续序号，212个enter和terminal按assertion/id/group/operation/operator/expected精确配对。
- 208个正式比较通过；2个旧对照为1对2、2对3；2个记录器自检含预期的不同数值失败。这3条assert_fail不是3个产品失败。固定初始基线2保持，明确retry后3，增量1；5组完成，真实清理记录存在。
- 独立恢复1节点、独立结构8节点均通过；开发兼容10节点单列。旧R6公开B不重复，旧R6失败不回填或改写。
- 原报告和人工清单规范化换行后保留原前缀，各新增1287字节；矩阵120唯一ID、12列及原案例行不变。总控不代替测试方调整整项状态。
- 三个Vitest CLI均exit0，登记worker实际exit1。首次报告无module/unhandled error、无controller强制终止，业务断言和清理证据可接受为有限结果；worker非零终止原因仍未核实，不宣称所有进程正常退出或工具链完全无异常。
- 两个新增文件名`r7-recovery.test.tsx`与`r7-recovery.config.mjs`不符合旧卡`r7-recovery-*`末尾连字符形式。总控接受为本次明确列举的命名例外：属于测试专属目录，首次内容/摘要已固定，不追改文件或旧任务卡，不扩大将来写入权限。

- 本次总控另行只读复算R5外部389项构建源码、140项产物、67项Python资源，均匹配；EXE/asar/lock、7份依赖元数据和固定jsdom入口保持。没有启动旧环境或重跑目标。
- r7_ready_contract_check完成源码与新任务两次只读审查，确认同值最终通知、旧getSnapshot回包及相同集合router稳定性已纳入；新包/EXE仅在开发门禁后授权。该审查不替代执行或独立验收。

## Windows首错的边界

[W1原始结果](../tests/independent/desktop/evidence/r7-recovery/windows-W1/result.json)与[journal](../tests/independent/desktop/evidence/r7-recovery/windows-W1/journal.jsonl)显示13个比较通过；runtime已online/managed/authenticated，直接模块查询具有启用的daily_finance及canonical Profile。第14个比较在等待`#daily-title`时未取得结果，actual为unknown。

runner将页面可见、导航数量及Agent数量合在一个观察函数；首个等待抛异常，后两项未采样，也没有错误时hash/存在/可见性标量。不能把unknown改写为false或0。journal的first_failure事件名被details.stage覆盖为runtime，result仍保留首错ID；旧文件保留，不补造现场。

本次产品启动1/8、辅助0/4、chunk注入0。8个登记进程和其监听在身份核验后定向清理；这是失败后的强制收口，不能验收普通退出或Tray。完整历史后代、各子进程独立退出原因仍不外推。

## 静态代码证明了缺少同步路径，尚未证明本次现场原因

| 位置 | 可直接从源码确认的行为 | 影响边界 |
| --- | --- | --- |
| [main index](../apps/desktop/electron/main/index.ts) | 先创建窗口，随后异步启动composition | 窗口与后台连接完成没有串行保证 |
| [composition root](../apps/desktop/electron/main/composition-root.ts) | 模块缓存初始为空，后台/owner连接完成后取模块并发布runtime | 后台就绪前后返回值允许变化；最终通知可能与先前runtime字段相同 |
| [DesktopApp](../apps/desktop/src/renderer/module-routes.tsx) | 挂载时仅查询一次modules；runtime订阅只setRuntime | 若初读为空，其后就绪通知没有重新同步模块列表的路径 |
| [实际日常页面](../apps/desktop/src/modules/daily-finance/DailyFinancePage.tsx) | 存在`h1#daily-title` | W1选择器与源码匹配，不能将失败直接归为拼写错误 |

以上足以派发可控时序开发回归，不需要再原样启动旧EXE碰运气；但W1未记录renderer初始模块值，不能声称这就是它的已证实根因。新复现必须用实际DesktopApp/Router/Shell及明确的空列表→就绪通知顺序证明问题，不能只测试新写辅助函数。

## 下一步

发布[P4-B7-R6-MODULE-READY](coordination/prompts/p4-b7-r6-module-ready-executor.md)，既有执行智能体唯一负责人：先保留可控时序红灯，确认后在同一任务做最小renderer修复、开发回归，再一次新包与一次真实EXE门禁。若原实现已通过目标回归或需要更改冻结接口，不猜测性修改，交回证据。

修复必须处理同值runtime的最终通知、过期异步回包、重复模块列表不重建router/自动重试及卸载退订；不增模块特殊分支、轮询、页面刷新或IPC接口。新EXE同时验证后端模块与真实页面，并在失败前保存独立安全标量，不能再仅用合并观察函数的unknown代替各项采样记录；取样失败仍准确保留unknown及安全阶段信息。

测试方、技术顾问停止；已通过B与恢复不由总控重复运行。执行方交付后再安排独立回归和剩余Windows条件。真实前端参考图、模型及token提醒仍在P4-C派发前触发，本任务只修已有Shell接线。

新任务固定输入见[812项起点](coordination/snapshots/p4-b7-r6-module-ready-start.sha256)，不包含清单自身；仅保存本轮78个明确交付与协调文件的本地未完成状态检查点，不推送。
