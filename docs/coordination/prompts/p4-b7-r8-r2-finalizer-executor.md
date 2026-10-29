# P4-B7-R8-R2-FINALIZER：控制器收尾修正与剩余同包验证

唯一负责人：既有执行智能体。先读 AGENTS、README、project-coordination、coordination/README、最新 control、本人 executor 状态、本卡及[总控裁定](../../p4-b7-r8-r1-finalizer-coordinator-review.md)。本卡 supersede 原 R1 的工具开发额度；原 R1 保持 blocked/finished，不在旧目录继续修改。

## 目标、输入与边界

只解决 R1 controller 收尾遇到结果文件/输出异常后逃逸的缺口。保留已通过的 25 项身份检查（包含 15 项时间检查）、第三轮 Node 夹具、217 项产品开发测试及固定新包。禁止重建身份算法、重新安装、重新打包或重复这些测试。先复算[当前起点 v2](../snapshots/p4-b7-r8-r2-finalizer-start-v2.sha256)，全部匹配后首次登记接单。

2026-10-29 接单前起点刷新：Tester 误收旧卡后仅更新本人停止记录，总控已核实其历史记录和产品输入保持。原[1375项清单](../snapshots/p4-b7-r8-r2-finalizer-start.sha256)原字节保留，SHA-256为 `cb0a4e078923d34cc3da383e501f55d75efc8753c80f73ae2cc24dbb80b3b368`；首次1374匹配/1个tester日志变化的结果不改写。当前v2为1376项，纳入此次授权日志、总控协调变化及原清单自身。任务仍是R2，不创建R3，不改变下述范围/预算；接单前只读核对不消耗工具修正轮次或S1/S2额度。不得跳过新清单，或普遍忽略后续角色日志漂移。

旧 R1 根为 `C:/MarisSettingsR8/R8-R1-20261021-143209`。核对其 3 项仓库交付、5 项工具、115 项证据及 closeout；接单后仅 executor 状态允许变化。旧 source 中总控协调变化以新起点为准，历史清单不覆盖。旧 R8 输入沿用[原 R1 卡](p4-b7-r8-r1-lifecycle-executor.md)及其绑定清单，完整旧依赖审计引用原已绑定结果，核对本轮实际使用入口，不重装或每条命令重扫依赖。

唯一产品：`C:/MarisSettingsR8/R8-20261019-103900/workspace/apps/desktop/out/Maris-win32-x64/Maris.exe`。

| 固定项 | SHA-256 |
| --- | --- |
| EXE | `c80d27c8e31fa60df91065a770e669a553260cf8f883c55a0a7f83f8a430736b` |
| app.asar | `05cdad34ba60b59773eebe671156c96260e69354568b9942da59058641f9c0b2` |
| lock | `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |

只创建新的 `C:/MarisSettingsR8/R8-R2-<时间戳>`，先验证绝对范围、非既有目录及无 reparse。所有工具差异、自检、证据、新 profile/虚拟数据/AppData 写新根；读取旧固定 exe/Node/Python/Playwright 是独立 allowlist。不得复制或改写旧 profile。仓库精确三路径：

1. 新增 `docs/b7-r8-r2-finalizer-running.md`。
2. 新增 `apps/desktop/b7-r8-r2-finalizer-source.sha256`。
3. 更新本人 `docs/coordination/agents/executor.md`。

产品、开发/独立测试、依赖、lock、Forge、旧 evidence、总控/其他角色/矩阵只读。无 Git 写权限。不启动顾问、Tester、Docker、微信/OpenClaw、真实 provider，不改系统/用户环境。

## 最小工具改动

从 R1 冻结候选普通复制必要文件。功能改动限 `controller.mjs` 的以下路径及可选单一小收口模块、自检文件；原 native-process、node-fixture、settings runner 的逻辑不变。新 taskRoot、证据目录、任务标签可机械重定位，schema/scenario/原门禁不变；复制前后摘要和机械差异单列，不把跨目录路径错误留到 EXE 后发现。

- 将产品结果读取从成功布尔表达式取出，只读一次、捕获缺失/损坏及结构异常。成功对象按实际生产者的 schema/task/scenario、严格 success=true 和完整原 gates/comparisons 检查；固定必需门禁缺失或比较集合为空不得借 every() 空真放行。异常结果或 false 对象保留其失败信息，不能强行补全为通过。启动前确认读取路径和生产者字段，拒绝错场景/旧结果，不新增不存在的字段要求。
- 先确定首错、后续输出/cleanup 错误及最后已核实资源，再分别尝试保存控制器 result、terminal 和可用的安全后备输出。输出失败也必须令控制器失败，不能把 exit0 先写死。原首错不能被解析或写盘错误覆盖。
- 以不可跳过的内层 finally 逐项尝试流释放和 child unref；一个动作失败不能阻止剩余动作。释放/输出/解析错误不能取消仍必要的身份核验和有界定向清理。释放流不等于进程已退出；未知值仍未知。
- record/save/failure 及 exit/stdout/stderr 事件回调使用同一受保护输出路径；回调不允许抛出未捕获异常。记录失败以内存安全状态通知主控制流进入原定收口，不能只吞错后继续业务。清理不得依赖日志能够写入。
- 原生查询实际返回后，即使保存其证据失败，也必须继续解析并保留真实回执中的身份信息供既有定向清理使用；不能因为输出失败丢掉已取得的身份，也不能因此忽略失败继续业务。
- 成功必须同时满足原业务结果、真实 root/worker exit、资源核验与墙钟未超限；证据不可读/写、清理未核实或退出未知均不成功。磁盘不可写时可记录“持久化失败”，独立尝试 stderr；不得声称所有故障下必有 result 文件。禁止用 process.exit/app.quit 或全局 uncaughtException 吞错冒充可靠收口。

所有路径仍受原剩余 deadline 约束，不增加 Windows Job、观察服务或新的通用进程管理层。不改原 UTC ticks 精度/身份谓词或资源归属范围。

## 有限前置自检和冻结

这是可修正的工具开发，最多 **25 分钟实际操作、3 版定向修正**；审批/等待不计实际操作。保留每版输入、首错及受影响复验；无变化且已通过的分支不反复跑全套。达到边界未通过则停止于目标前。不得把 EXE/Electron/Host 启动称为工具自检。

使用实际供控制器调用的同一收口函数和安全输出函数做虚拟文件/注入 IO 自检，不复制一份仅用于测试的实现。至少逐项证明：

| 分支 | 必须观察 |
| --- | --- |
| 合法完整成功 / success=false / 简化失败 | 前者按全部原门禁通过，后两者不成功；首错信息保留 |
| 缺失或不可读文件 / 空或坏 JSON / null或数组 / 错场景 | 明确安全错误类型与阶段、非零结论、资源释放均执行 |
| success类型错 / 缺必需gate / 空或失败comparison | 不放行S2，不以空集合全真代替完整门禁 |
| 既有产品首错叠加解析或输出失败 | 首错不覆盖，后续错误单列，资源未知不写零 |
| result、firstFailure或journal写失败 / terminal写失败 / exit与双流callback写失败 | 每条独立注入；主控制流可收口，释放不被跳过，输出缺失如实记录 |
| 原生回执写盘失败 / 清理失败叠加结果不可读 | 前者保留实际身份用于清理；后者分别记录两类失败，未知资源不填零 |
| 某一释放动作抛错 | 后续释放仍尝试，非零退出，不能只验证调用了未被使用的函数 |
| 超期或真实退出未知 | 不因 JSON 中 success=true 而变为通过 |

IO 故障使用新根虚拟文件或注入函数，不改系统 ACL、不制造真实磁盘耗尽。即时保存安全阶段和比较 expected/actual；不读取旧私密 profile 正文。

纯分支通过后，**一次**普通 Node 自然结束集成验证实际新控制器：日志、真实退出、收尾结果和自有资源完整，最多 15 秒。原 natural 分支会自动执行 probePrecision/selfcheck；本卡明确允许仅在工具集成分支跳过这两段已通过的完整自检，保留实际 Node 身份快照和同一归属/收口逻辑。该集成使用新根虚拟结果文件调用与 S1/S2 共用的受保护读取/判定函数，实际安全输出和释放函数也必须共用；结果明确标为fixture、产品启动0，不作为产品证据。不得复制简化实现，或对正式产品分支豁免身份检查。

允许一次仅用于已证实本轮控制器缺陷的修后定向补验，总集成最多 2 次；不重复原完整 25 项身份集合或原观察失败/超时夹具。工具自检成功不计产品验收。前置确认已有查询/必要清理权限，不留运行后审批依赖。

最后静态核对实际调用链、结果字段、S1/S2 路径、成功/失败分支、首错/超时及不可跳过的释放；不得在发现未保护 IO 后仍冻结放行。冻结工具及摘要后停止编辑，直接进入以下 S1/S2，不返回总控只申请第二步。

## 同包 S1 / S2：沿用未消耗额度

本次 **package0、EXE最多2、helper0**。这两次来自 R1 未用额度，系列上限不增加：R8 package1/1、EXE已用1/总3。Tester 原累计产品2/8、helper3/6保持冻结。

原 R1 卡的“双步真实验证”全部业务条件继续适用。固定 Node 直接 spawn(shell:false) 固定 EXE，Playwright 仅 connectOverCDP。每场景硬上限120秒，业务段最多105秒、末段最多15秒收口；页面条件5秒、普通关窗10秒，不延长。动态 loopback、新虚拟 owner/数据库/profile 隔离。无退出计时器、app.quit/process.exit、CDP Browser.close 或强杀替代正常退出。

**S1一次：** 新profile启动前只seed合法 light/false、closePolicy=quit、closeHintShown=false、毛毛可见；核验双窗口、bridge隔离、后台和实际daily/Shell/导航/Agent。通过真实控件改为dark/true并证明保存，一次recover后状态/路由保持；向身份核实的主窗口发正常WM_CLOSE，root自然exit0及自有进程/监听/窗口0。控制器与runner都满足全部门禁才放行S2。

**S2一次：** 同EXE和S1保存后的原样profile续启，中间不seed/修改设置或重新复制。页面ready的首次有效样本同时验证theme=dark、privacy=on、select=dark、checkbox=true，记录设置文件摘要和driver设置写入数0；不把driver零写入外推为监控了产品所有写入。不追加recover，不通过再设置/刷新/重启转绿；完成后普通关窗并核验退出/资源。

正式产品启动后的任一产品比较失败、工具未知故障、身份不明、意外弹窗或隐私问题，立即停止后续业务，不修后重跑；必要的身份核实和定向收口继续。保留首样、真实root/worker退出、子进程未知值及最后已知资源，强制收口不算正常退出通过。

## 交付

新根保留冻结工具、分支自检、实际集成、S1/S2首次结果/阶段日志、安全设置值及摘要、资源回执。旧 R8/R1 profile、工具、证据全部不变；核对固定包和受影响输入的终点摘要，不重复完整历史测试。仅清理验证边界与reparse后的本任务临时项。

终点source以新起点为基础，只更新executor并加入本次运行说明，排除source自身；另给三路径交付和外部工具/证据摘要。接单、工具通过、每个S及收口更新本人状态/当前快照，有执行控制时至少每10分钟心跳。成功只 `review / finished`，未通过则 `blocked / finished`；不关闭SETTINGS-001/CMP-06/LAZY-001/UI-02/P4-B，不自行启动其他角色或P4-C。
