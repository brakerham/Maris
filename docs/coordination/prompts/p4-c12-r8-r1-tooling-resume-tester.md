# P4-C12-R8-R1：测试工具更正与剩余模块、Windows续验

## 唯一负责人和读取顺序

你是既有测试智能体。本任务继续R8未完成范围，原R8保持blocked/finished和首次证据。执行方与顾问停止，无产品返修授权。按AGENTS读取README、project-coordination、coordination/README、最新control、本人tester、本卡，再读：

- [总控裁定](../../p4-c12-r8-tooling-coordinator-review.md)、[R8报告](../../testing/phase-4-c12-r8-modules-windows-report.md)、R8首次result/journal/process和first-run-analysis。
- [原R8完整合同](p4-c12-r8-modules-windows-tester.md)，其固定R6输入、原公开条件、Windows方式、安全/设备边界与结论要求继续适用；本卡仅覆盖新的起点、写入路径、四节点选择及工具修正规则。禁止重新执行旧R8整组。
- [新固定起点](../snapshots/p4-c12-r8-r1-start.sha256)：仓库根、原字节、排序的 `path<TAB>sha256<LF>`、UTF8无BOM、不含自身。接单前全部匹配且staged=0，再登记本人接单和下一检查点。

旧R8九节点通过保留；393个正式比较不是393个测试。旧B、完整R7五组/结构、P/A/D15/D16、旧EXE不重复。本任务不是前端界面开发。

## 写入范围与固定输入

可写仅：

1. 新 `tests/independent/desktop/r8-r1-*`：复制旧R8的必要test/config/setup/reporter/controller为新副本；新增必要剩余公开/Windows工具亦用此前缀。
2. 新 `tests/independent/desktop/evidence/r8-r1/**`，首次源码、日志、diff、输入/退出/交付回执分目录保存，已有文件不覆盖。
3. 新 `docs/testing/phase-4-c12-r8-r1-modules-windows-report.md`、本人 `docs/coordination/agents/tester.md`。
4. C12原主报告、人工清单仅追加；矩阵仅更新P4-B实际状态与备注，120个ID、12列、原预期及A/C/D保持。

旧R8所有源码/报告/证据、其他旧独立材料、产品/开发测试、依赖/lock、包、控制/overview/snapshot和其他角色只读；无Git写权限。不安装、下载、构建、重打包、增加IPC/开关或改production fuse。

受验根仍 `C:/MarisModulesR6/R6-20261013-002100`，工具版本、813构建源码/140产物/67资源/73dist/12443依赖及EXE/asar/lock摘要精确沿用原R8表，不重新选包。本次接单/结束核对这些输入；旧仓库清单的测试方四项和总控五项协调变化按来源明确列举，不改外部副本。

原R8交付29项、源码7项、首次6项必须匹配总控裁定所列摘要。交付29项中本人日志、主报告、人工清单、矩阵四项在本轮开始后允许指定变化，另25项保持；源码7/首次6始终精确不变。以后复算旧R7等含共享文档的清单，逐项列已授权变化，不误报全清单不变。

新虚拟根 `C:/MarisC12/C12-R8-R1-<时间戳>`。配置输出/cache指向本轮自有路径，不写固定依赖、旧evidence/profile。外部秘密/端点/加密profile只留受限自有根；仓库只保存脱敏标量证据。普通副本、reparse检查、临时项清理沿用原R8安全边界。

## 第一阶段：准备与四个剩余节点

更正新副本，逐项保存与旧源码的最小diff：

1. R8-10仅把链接断言前缀 `REMOVED.NAV` 改为 `REMOVED.ALPHA_LINK`； `chrome('REMOVED')` 的整个导航区域检查保持。selector、expected、exists/count/visible、操作顺序、等待上限和业务要求均不改。
2. 重复ID保护继续存在，但抛错前独立记录 `tool_error`：稳定errorCode、nodeId、attemptedAssertionId、阶段和时刻；该诊断事件不能再次经重复ID的check通道。未知异常只记录安全类型和阶段，分类unknown，不能兜底写成工具问题。
3. scenario结束、reporter分别记录节点结果、首次产品比较失败、首次工具错误、未分类错误和清理结果。安全expected/actual、operator及enter/terminal仍完整；节点抛错不能因cleanup成功而写pass。保存首次发生顺序，不能只剩 `firstFailure=null` 或一个AssertionError。
4. R8-13已有主动卸载后的FINAL空root合同，保持原实现及DOM_EMPTY/NO_MORE_READS/SUBSCRIPTIONS_ZERO，不把它改成必须有导航，也不删卸载断言。
5. 配置和输出路径转向新目录；精确选择 `R8-10`、`R8-11`、`R8-12`、`R8-13`。保留原节点ID及业务正文，标注本轮/attempt；01至09过滤不运行，报告为历史通过复用，不冒充本轮passed或新增skip。

正式目标前做语法/路径静态检查，以及在同worker启动真实组件前的纯标量/ID自检：不同语义ID不冲突；故意重复ID能生成tool_error且节点失败；清理成功不能改写节点失败；未知异常不会被自动标为工具错误。自检不导入产品、不挂载DOM、不计业务节点，不新建进程预算实验或通用观察框架。检查已知ui/chrome展开前缀与动态编号，冻结源码/配置/自检记录后才执行目标。

故意失败的自检必须有独立caseId、`kind=selftest`和限定于自检的`expectedFailure=true`；与正式节点/首错统计分开。只有自检行为不符合预期才阻止产品启动。正式节点不允许使用expectedFailure豁免，不能把新增tool_error自检误计为正式首错。

| 节点 | 必须保留的公开要求 |
| --- | --- |
| R8-10 | 禁用/不兼容/未知不导航、不预载；合法模块出现；移除当前模块后旧页/旧链接消失，整个Shell/导航/Agent仍在；状态保持、新模块可打开 |
| R8-11 | 在途旧页完成不得复活已移除模块；当前beta页面和hash保持 |
| R8-12 | 变更模块集合后的render错误局部隔离；等价通知不自动重试 |
| R8-13 | StrictMode旧effect回包不得覆盖当前页；主动卸载后的回包不写DOM、不增加读取且订阅归零 |

四节点按原顺序正式运行一次；每节点独立scenario，不复制/共享上一节点的挂载或缓存状态来续跑。保留StrictMode和真实DesktopApp/Router/Shell，不重新导入main重做冷B。每节点15秒正文、每次UI观察5秒、清理5秒，原生初始化60秒，整CLI最多300秒。

## 一次有限的纯工具修正授权

本卡事先授权：若上述新四节点运行再次遇到**已证明的纯取证工具错误**，即使组件已挂载，也可在本任务更正一次。必须同时满足：

- 实际代码及即时记录证明是ID/记录器/输出读取或汇总错误；没有失败的产品比较、来源/隐私/安全断言，且不是未知异常或超时。
- 已执行的操作和清理有证据；root/worker以及订阅/环境均安全收口。不能用“没记录到失败”代替丢失阶段的证明。
- 原源码和首次记录不覆盖；新attempt保存最小diff与修正依据，产品、selectors、expected、操作顺序/次数、时限和原四节点要求不变。
- 最多一次额外定向CLI，仅重启被工具中断节点的完整新生命周期及其后未执行节点，已通过节点不重跑。明确分开首轮和修后结果，唯一节点去重。

此预算不追溯授权重跑旧R8，也不适用于Windows或兼容业务失败。首次目标前无副作用配置错误仍可静态更正；修正后先冻结，再运行。真实比较失败、未知原因、超时、秘密泄漏、所有权不明或清理失败立即停止扩大，提交具体断言，不“修测试直到绿”。额外预算用完仍中断则停止，不另建无限attempt。

## 第二阶段：兼容、剩余公开条件与Windows

四节点全部通过后，结合旧01至09构成13个独立节点的证据集合；旧R8-10失败仍保留，不回写。随后**同任务**继续原R8尚未执行的：

1. 必要开发兼容一次：module-readiness18、lazy8、Shell1、composition1，共28项，独立结果单列。不跑完整150或无关Python/registry。
2. 原24项尚缺的可执行公开条件可用新 `r8-r1-*` 另组一次；先列原要求、已存在证据和新增覆盖，不重复旧已通过节点。
3. 固定R6新EXE的Windows计划最多8次产品启动、4次辅助safeStorage启动，继承原R8完整第二阶段合同及R7/原R4逐项要求。开工先列每次新增覆盖和profile关系，预算不因任务更名累计增长，旧R8为0/8、0/4。单产品120秒、辅助60秒、页面就绪观察5秒。

仅用spawn(shell:false)启动固定EXE，CDP只观察owned loopback；分开记录backend在线、modules和真实页面exists/count/visible/hash/readyState。继续真正会话重启、同请求ID、设置/主题、recover、关闭策略/Tray、原生过期提示等原尚缺条件。具体不支持的chunk注入/设备条件保留未验证，可在安全收口后继续无依赖计划场景；不能把它们写为产品失败或通过。

无真实注销/系统重启、启动项/系统主题/多屏修改、用户立即点击授权；只更新人工清单。不改包、fuse、系统安全设置，不重复Docker/微信V002/OpenClaw/真实provider；本任务不接管其他用户程序。实际P0/P1与安全/资源失败沿用停止规则。

## 交付与状态

提交增量报告、最小工具diff/自检、四节点首次及可能的一次工具修正、必要兼容、Windows计划/实际预算、逐断言安全值/来源/清理。列旧9与新4来源，不累计重复比较冒充唯一节点。保留旧失败与unknown范围；原24项只填本次增量及剩余缺口，不再复制全部历史报告。

起点/外部包/旧首次材料终点复算，授权共享文档变化明确列出；保留产物、虚拟profile和原始证据，只清理本轮明确自有临时项。root/worker分别记录真实退出，权限拿不到全系统状态就写unverified。

接单、里程碑、阻塞、交付更新本人日志及当前执行快照；有控制时至少每10分钟心跳，中断不伪造持续工作。最终只交review/finished或blocked/finished，总控决定缺陷/UI-02/P4-B关闭；不自行启动执行方、顾问、P4-C/D。当前实际接单unverified。
