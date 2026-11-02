# R11 独立结果接受与 Windows 观察续接裁定

2026-11-03，Asia/Shanghai，头脑风暴总控；只读核对始于11月2日。依据 [R11 报告](testing/phase-4-c12-r11-origin-settings-windows-report.md)、[具体比较](../tests/independent/desktop/evidence/r11-origin-settings/assertions.md)及首次证据，只读复核；本总控没有启动测试、产品、helper、构建或安装。

## 接受与未完成范围

**限定关闭 `P4-C12-R10-IPC-ORIGIN-001`。** 原 R10-I06 三条比较保持业务正文、断言 ID 和同源正对照，原不同端口反例现在稳定拒绝；NO_SAVE=0。O01～O08 独立边界覆盖真实安全谓词、validateIpc、main/companion 注册接线，没有用身份拒绝替代来源拒绝。R9 开发来源修复在这个缺陷范围内接受为 complete；执行方原 review 记录保留。

本次接受 R11 的 41 个独立节点、321 条配对唯一比较全部通过，以及单列的 109 项开发兼容通过。旧未运行 I07、U01～U31 已完成，不再重跑。生产包裁剪开发分支的证据与原范围保持；没有宣称生产包存在或消除了同一种可达攻击。

R11 整体仍为 blocked / finished。SEC-04 整项改为 blocked，仍缺完整 Windows 条件；SETTINGS-001 需要原 W2 四条首次页面样本，不能由源级水合或执行方 S1/S2 替代。LAZY-001、UI-02、CMP-06、P4-B 未关闭。矩阵为 **1 passed、2 failed、19 blocked、2 not_run**，P4-A 64 passed，C/D 32 not_run 不变。

## 总控复算与证据边界

| 对象 | 实际核对 |
| --- | --- |
| R11 起点 1438 项 | 审阅开始时 1434 不变、仅四份获准测试共享文档变化，无缺失 |
| 交付 / 工具 / 证据 | 110 / 11 / 93 项逐项匹配 |
| 正式来源 / 首次材料 / 源码归档 | 49 / 90 / 50 项逐项匹配，各按自己的基准根 |
| 正式结果与日志 | 41 个节点全部 passed；321 个 enter/terminal 比较唯一、完整配对、全部通过 |
| 兼容结果 | 四文件 109 个节点通过，未与独立或历史重复累计 |
| 固定 R9 构建 / 产物 / Python 资源 | 1432 / 140 / 67 项再次逐项匹配 |
| 矩阵与旧报告 | 120 个唯一 ID、12 列、原预期及 A/C/D 保持；仅 SEC-04 failed→blocked；两份旧报告为追加 |

R11 delivery.sha256 为 `b282382cf86dc5ccc9bf47439d0c3a591d9d57d546095bea6f7c3f46cd4cfc67`；tools 为 `277c33a4126279ab4972c009cab30e5b9dde313c093bbf2c0e83781beef82f01`；evidence 为 `bad03c55f08b65c5db23eca9d469b6b0ceedbd5daebb7ad8ae339571cb7612f6`。首次材料、归档与正式来源索引由原 delivery 绑定，不修改。

独立 runner 主进程退出 0，worker 退出 1；兼容 runner 主进程退出 0，其 worker 有 0 和 1。原报告将受控测试池退出与节点结果分开，总控没有把 worker 值改成 0，也没有当作产品退出证据。产品/helper 本轮新增均为 0，系列仍为 2/8、3/6。

总控首次清单读取器用错 evidence 基准根，随后依据清单实际路径纠正并全量匹配；矩阵读取器首次把非案例表行混入，改为精确案例 ID 后验证通过。两者均为只读核对错误，不涉及旧证据修改或目标重跑。内部只读复核确认原 I06 正文及 companion fixture 范围；辅助随后额度中断，未完成最终卡审阅，最终复核由总控完成。

## 原字节与格式记录

当前已跟踪文件的git diff --check退出0；新增冻结材料另有三处格式提示：`contract.test.tsx.diff`第15行的空白差异上下文，以及正式和first-source两份`r11-origin-settings-main-fixture.ts`第118行的EOF空行。总控保留原字节、摘要与首次材料，不为了格式改写Tester交付；完整暂存检查实际退出2，仅报告这三项；不宣称整个检查点零格式提示。Git用户级ignore读取权限和自动CRLF提示是已有环境记录，不据此修改系统或历史文件。

## 当前只读进程观察证据

原 [R11 capability](../tests/independent/desktop/evidence/r11-origin-settings/capability.json)只记录 CimException、HResult 和 unknown，没有原生错误码。其根因继续为 unknown，不能事后补签。

总控另做两次最小只读查询，原命令及安全结构回执保存在 [readability.json](coordination/diagnostics/p4-c12-r11-observer/readability.json)：

| 当前核对 | 实际结果 |
| --- | --- |
| 18:10:55 默认访问环境 | 275ms；CimException，NativeErrorCode=AccessDenied，StatusCode=2，PermissionDenied；未取得库存 |
| 18:11:48 标准工具审批后的只读环境 | 589ms；返回 359 项且自身 PID 存在，查询通过 |

这说明**本次访问环境会影响 CIM 查询权限**，为下一任务提供具体可用路线。没有改 Windows 权限、WMI 服务、安全软件、系统设置，也没有启动或结束目标进程。没有将库存中的路径/命令行内容保存到仓库。该结果不证明旧 R11 根因、不证明当前零遗留进程，也不证明 listener/UIA/Tray 能力；新任务仍须按实际目标核实。

标准工具审批不是 RunAs，也不授权让 Maris 以管理员身份运行。只读观察需要的审批必须在产品启动前完成，权限仍不可用就留在目标前停止，不把拒绝当作空库存。

旧 capability 代码的注释称排除观察器，但其匹配实际未排除。新副本只可按已核实的准确自身/控制器 PID 排除观察动作；不能一概忽略 PowerShell/Node 或根目录匹配，否则会漏报真实目标。

## 唯一续接任务

发布 [P4-C12-R11-R1-WINDOWS](coordination/prompts/p4-c12-r11-r1-windows-tester.md)，以[新起点](coordination/snapshots/p4-c12-r11-r1-windows-start.sha256)首次接单。Tester 负责，Executor/顾问停止，实际接单 unverified。

- 41/321 与 109、旧 H1/W1/冷入口/恢复/模块/退出及执行方 S1/S2 均只引用，不再运行。
- 只修新观察工具副本：保留实际 NativeErrorCode/StatusCode/阶段、分开身份与资源查询、准确匹配自身 PID，使用获准只读环境；不新建通用进程框架。
- 观察门禁通过后直接原 W2 首样，随后在同一任务继续 W3/H2/W4/H3/W5/H4/W6/W7，不每成功一步另派卡。
- 产品剩余最多 6 次、helper 最多 3 次，不重置系列计数；package/安装/开发服务器/H1 为 0。新包与原 W1 同内容虚拟副本保持。
- 正式失败或未知所有权异常保留首次并停止；目标前有限工具修正依新卡，不在运行后降低断言。

本次本地提交接受有限 IPC 修复并保存尚未完成的 Windows 检查点，不推送。首个 P4-C 前端设计或执行任务前，主动提醒用户复核两张参考图、高保真要求和届时模型分工的门禁继续有效。
