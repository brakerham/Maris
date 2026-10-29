# R8-R1 工具收口审阅与剩余生命周期续验裁定

2026-10-28开始审阅，2026-10-29完成发布核对；两次之间不计持续执行。Asia/Shanghai。角色：头脑风暴总控。输入为 [R1 运行说明](b7-r8-r1-lifecycle-running.md)、[原 R1 任务](coordination/prompts/p4-b7-r8-r1-lifecycle-executor.md)及 `C:/MarisSettingsR8/R8-R1-20261021-143209`。总控本轮只读核验和协调，没有运行工具候选、测试、产品、辅助程序或打包。

## 裁定

R1 保持 `blocked / finished`。时间身份检查及第三轮普通 Node 收口证据可以保留；未获准启动产品的工具候选不能直接用于 S1。剩余缺口属于验证工具，不新增产品缺陷，不要求重新实现设置恢复。

R8 的 217 项开发测试、唯一新包及静态检查保持。R1 产品启动为零，S1/S2 均未运行，因此之前授予但未消耗的两次额度仍在。本次发布 [P4-B7-R8-R2-FINALIZER](coordination/prompts/p4-b7-r8-r2-finalizer-executor.md)，仅修控制器收尾及相关输出异常路径，通过有限工具自检后，在同一任务内完成同包 S1、S2。产品、依赖、原工具和旧现场均不改。

## 亲自复算与证据边界

以下清单在总控改写协调文件之前逐文件复算，无差异：

| 输入 | 条目 | 清单 SHA-256 |
| --- | --- | --- |
| R1 仓库 source | 1371 | `9409dc9e0b3210c26af183295eb993ce27059520806ba135ae83ed7deb8f30ca` |
| R1 仓库交付 | 3 | `7189691101c19d5790b88748644fb7bd33da68f1171de0d5f1234eef74c9c3cb` |
| R1 工具候选 | 5 | `457bac8e613b0b2854f48c4bc5d2daa5e6b9e9f26d56f7265defe4f91bad6c8b` |
| R1 外部证据 | 115 | `060118aa98230fedc62a9b499a8e6344f20122e5c91f44e6684f0548cd6d25d8` |

原 1370 项起点仅 executor 状态有授权变化，无缺失。R1 `evidence/closeout.json` SHA-256 为 `6aa135ad767efa947179c6a7c4415bd0f8784269b40cad94d4dae168ad6c8644`；`end-audit.json` 为 `65bbeaf44e7a434681545e60cd17deccaaa25be21f50cdac9508df5f235bd80b`；`static-review.json` 为 `82b29d6d8b2f75a1e0a7d3dc1bacbdb64cf96217e9b0f0da1fdde85b771416bb`。旧 R8 构建、包、profile、工具与完整依赖不变采用这些绑定审计及[上轮总控核验](p4-b7-r8-settings-lifecycle-coordinator-review.md)，不声称本轮再次遍历全部历史依赖。

25 项实际身份检查包含 15 项时间断言，不相加成 40 项。普通 Node 夹具实际 5 次、4 通过、1 失败；第三轮自然退出 8177ms、故障收口 6839ms。第一轮未知退出值保留，后轮通过不回填首次失败。2026-10-26 末次资源回执中进程/监听为零，窗口为 null；这是历史观察，本轮未枚举系统，不改称窗口已验证为零。

2026-10-29恢复后再次复算待发布1375项起点、R1三项交付/五份工具/115项证据及固定EXE/asar，全部保持。随后仅刷新本次总控发布记录和新起点；没有再次运行任何测试或目标。

## 剩余缺口与修复边界

实际 `tools/controller.mjs` 第 89 行在 `finally` 的成功表达式中直接读取并解析产品 `result.json`。缺文件、非法 JSON 或 null 对象均可能抛错，使第 90 行控制器结果、终态日志及第 91～92 行释放/退出状态不再执行。第 90 行自身写入失败也存在同样路径。记录函数及 exit/stdout/stderr 回调还包含同步写文件；这些回调的异常不受外层 async try/catch 自动保护。

因此修复不能只为 JSON.parse 增加 catch。最小范围是控制器统一的安全记录、一次受保护读取与结构判定、错误优先级、无条件尝试全部句柄释放及非零退出。可抽出一个小收口模块供实际控制器和分支自检共用，不重建身份观察器、进程框架或产品 runner。结果缺失不等于产品失败原因已知；须区分工具证据错误、既有 firstFailure、cleanupFailure 和最后已核实资源。

原 product runner 成功结果实际字段为 `schema=maris-settings-r8-lifecycle-v1`、`task`、`scenario`、`success`、`gates`、`comparisons`；异常结果可能没有完整 schema/gates。新校验必须对照实际生产者，失败对象始终按失败处理，不能虚构字段名或把格式缺口当作成功。成功还须满足真实退出、现有资源及墙钟限制。输出设备不可写时不承诺一定能落盘：独立尝试可用的 stderr 通道并返回非零，资源释放仍不得被输出失败阻止。

内部只读子审阅 `r8_r2_finalizer_review` 复核同一 finalizer、记录函数和事件回调路径；无文件写入或目标运行。新卡只读一致性核对已完成，无阻断项；原自然夹具默认重跑25身份的矛盾已消除，仅工具集成分支跳过旧完整自检，正式产品身份门禁不变。

## 后续权限和结论

新 R2 只更新 executor 状态并新增一份运行说明、一份终点 source 清单。新工具/自检/虚拟现场写独立 R2 外部根；旧 R8/R1 全只读。允许必要 taskRoot/任务标签机械重定位，单列差异，不借此改变已验证的时间身份或 S1/S2 业务断言。

工具开发允许有限定向迭代，全部失败保留；不把普通输出分支自检也设计成每错一次就重开完整任务。正式产品冻结后 S1 一次，全过才执行 S2 一次；任何正式失败停止后续但继续必要安全收口。系列 package 仍 1/1、EXE 仍最多 3（旧已用 1、剩余 2）、helper 0；Tester 产品 2/8、helper 3/6 不变。

SETTINGS-001、CMP-06、LAZY-001/UI-02 和 P4-B 均未关闭。P4-B 维持 1 passed、2 failed、19 blocked、2 not_run。前端高保真界面与模型分工提醒继续保留，尚未进入 P4-C。

本地 Git 仅保存明确标注未完成的证据与协调检查点，不推送，不作为验收完成提交。

## 2026-10-29 19:50 同一 R2 起点刷新

用户确认误将旧 R9-R2 Prompt 发给 Tester。Tester 按最新 control 保持停止，仅更新本人状态；Executor 随后收到正确 R2 卡，在接单前发现单项摘要差异并停止，未登记接单或消耗工具/产品额度。

总控亲自复算原1375项：1374匹配、1不匹配、0缺失；唯一变化是 `docs/coordination/agents/tester.md`，原值 `4db1a7b3912e69bdbbb10a8ad3d3d08cf08784bb5d4b71bb6620677127d33abc`，当前值 `0e83aa5599f535ab652743e32770895f1e5ddf63def70cb77cc21735165de782`。Git差异只涉及该状态文件的当前快照与19:40停止记录；从R9-R3执行记录至末尾的旧历史文本完全保持。内部 `r8_r2_snapshot_refresh_review` 独立只读核对一致，无文件修改或目标运行。

这是已核实的协调日志变化，不是新产品/工具失败。批准纳入当前起点。原清单SHA-256 `cb0a4e078923d34cc3da383e501f55d75efc8753c80f73ae2cc24dbb80b3b368`保持，新增[1376项v2清单](coordination/snapshots/p4-b7-r8-r2-finalizer-start-v2.sha256)，原R2卡改为引用v2。本次同时更新control、overview、brainstorm和本裁定；不改Tester交付原文、Executor状态、产品/测试/包/旧证据。

任务仍为P4-B7-R8-R2-FINALIZER，25分钟/3版工具开发、普通Node集成最多2次和原剩余S1/S2各一次全部不变。本次接单前只读核对不计这些额度。执行方须重新复算当前v2后首次接单，不以“角色日志可以变化”为由豁免其他未核实差异；Tester继续停止，无需重复发送旧卡。
