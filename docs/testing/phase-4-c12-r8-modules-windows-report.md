# P4-C12-R8-MODULES 独立模块同步与 Windows 增量报告

日期：2026-10-13，Asia/Shanghai。角色：既有测试智能体。依据 [R8任务卡](../coordination/prompts/p4-c12-r8-modules-windows-tester.md)、control `2026-10-13T13:43:00+08:00`。**交付供总控 review；执行状态 blocked / finished。**

## 结论与停止原因

唯一一次独立运行取得 **9 passed、1 failed、3 not_run**。失败节点 `R8-10` 属于本轮测试辅助的重复断言 ID 中断，**没有观察到失败的产品行为比较，不提交新的产品 P0/P1**。该节点未完成，独立模块/最小邻接门禁整体没有通过，28 项开发兼容及 Windows 全部未运行。执行方 150 开发节点和 22 项 EXE 门禁不计入本报告。

这是测试方编写的取证代码错误。先单独检查移除后的导航，随后以同一前缀调用 Shell/导航/Agent 公共检查，产生重复 `R8-10.REMOVED.NAV.EXISTS`，触发测试辅助的唯一性保护。测试此前已执行真实 DesktopApp，任务卡“产品已开始后的失败不得修后重跑”适用；没有改名重试、降低要求、修产品或绕过前置门禁启动兼容/Windows。

原 R6 冷入口 B、R7 恢复五组、R7 结构八项只读保留。本轮未重复 B、P/A、D15/D16、完整 R7 或旧 EXE；旧 W1 原因仍 unverified，不以新的模块同步成功倒写旧现场。

## 固定输入与授权边界

[接单审计](../../tests/independent/desktop/evidence/r8-modules/start-audit.json)记录 **818/818** 原字节匹配、staged=0。起点清单摘要 `8423b70bbaff05c7b37d888a836ec3f6c880c2a74d07a324b42a0e4c2f407337`。14:03 接单后到 19:06 用户继续之间没有持续可观察执行记录，没有把空档计作持续运行；[恢复核对](../../tests/independent/desktop/evidence/r8-modules/resume-audit.json)为 817 不变、本角色一项授权变化，目标仍零启动。

绑定 **P4-B7-R6-MODULE-READY**，固定外部根 `C:/MarisModulesR6/R6-20261013-002100`：

| 输入 | 开始时结果 |
|---|---|
| 仓库 R6 source 814 | 809 保持；README、project-coordination、control、overview、brainstorm 五项为任务卡列明的总控变化 |
| 实际构建源码 / 产物 / Python资源 | 813/813、140/140、67/67 |
| 依赖 / Electron dist | 12443/12443、73/73 |
| 旧 R7 交付 | 68/68 保持 |
| EXE | `4ef5bce604fc61fc2b815300edee8a29ab593083d308e849445c6c97235c5f1e` |
| asar | `5eb153002f4c48ce704f1d0f90b3bf441d5edf3799ea5fe4428f706aee7c69db` |
| lock | `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |

使用新根的 Node24.21.0、Vitest5.0.2、原生 createRequire/jsdom30.1.1、同一物理根 React19.3.0/ReactDOM/Router8.4.0。没有运行旧根工具、安装、下载、audit、build/package 或写入冻结依赖。本轮尚未创建 Windows 虚拟 profile/数据库或新外部工作根。

## 独立设计与首次结果

[节点/合同映射](../../tests/independent/desktop/evidence/r8-modules/assertion-map.json)、[静态核对](../../tests/independent/desktop/evidence/r8-modules/static-audit.json)、[七项运行前冻结](../../tests/independent/desktop/evidence/r8-modules/modules-source.sha256)。生产 main 使用真实 DesktopApp、compileRegistry 与 StrictMode 的接线已核对；未导入生产 main 重做冷 B。

| 节点 | 新独立条件 | 实际状态 |
|---|---|---|
| R8-01 | 普通挂载明确空列表，再同字段就绪通知，导航与页面自动出现 | passed |
| R8-02 | 同一启动顺序，StrictMode；无手动 remount/recover | passed |
| R8-03 | 后台已就绪后普通挂载 | passed |
| R8-04 | 后台已就绪后 StrictMode 挂载 | passed |
| R8-05 | 初始快照晚到不得覆盖已收到的在线通知和页面 | passed |
| R8-06 | 初次读取内同步通知不丢失；受控两次读取 | passed |
| R8-07 | 12 次突发通知、在途旧模块列表；合并读取与最后列表可见 | passed |
| R8-08 | 初始/后续读取拒绝安全；离线和拒绝不清空可用页面 | passed |
| R8-09 | 等价交集/无关 Host 条目/设置/runtime 不隐式重载；明确 retry +1、状态/订阅保持；健康及设置路由保持 | passed |
| R8-10 | 缺失/禁用/不兼容/未知拒绝，合法新增与当前模块移除 | runner failed：工具重复 ID；已有部分比较通过，不计节点 passed |
| R8-11 | 改变路由集合后旧在途页面结果不能复活 | not_run |
| R8-12 | 改变路由集合后的局部 render 边界 | not_run |
| R8-13 | StrictMode 旧 effect 与卸载后回包不可写状态 | not_run |

[首次 runner result](../../tests/independent/desktop/evidence/r8-modules/modules/result.json)、[逐条 journal](../../tests/independent/desktop/evidence/r8-modules/modules/worker.journal.jsonl)、[六项首次材料冻结](../../tests/independent/desktop/evidence/r8-modules/modules-first.sha256)。395 个 assert_enter 与 395 个 terminal 唯一配对，其中 **393 正式比较全部 passed**，另两项为同 worker 标量记录器自检。比较数不是测试节点数；393 个比较不能把未完成节点变成通过。

每条正式比较记录 ID、operator、安全 expected/actual 和时刻；UI exists/count/CSS_VISIBLE 分别记录。这里的 CSS_VISIBLE 只表示 jsdom 的隐藏属性/样式检查，**没有 Windows 布局、屏幕几何或实际窗口可见性的证明力**。

| 代表性断言 | operator | expected | actual |
|---|---|---|---|
| R8-06.READS.BOUNDED | eq | 2 | 2 |
| R8-07.READS.COALESCED | eq | 2 | 2 |
| R8-09.LOADS.POSITIVE_BASE | positive | 大于0的安全整数 | 2 |
| R8-09.NO_IMPLICIT_LOAD | eq | 固定基线2 | 2 |
| R8-09.RETRY.EXACT_INCREMENT | eq | 1 | 1 |
| R8-09.RETRY.SHELL_STABLE | eq | true | true |
| R8-09.RETRY.SUBSCRIPTIONS_STABLE | eq | 2 | 2 |
| R8-09.SETTINGS.TWO | eq | 2 | 2 |
| R8-10.REMOVED.PAGE.EXISTS / COUNT / CSS_VISIBLE | eq | false / 0 / false | false / 0 / false |
| R8-10.REMOVED.NAV.EXISTS / COUNT / CSS_VISIBLE | eq | false / 0 / false | false / 0 / false |
| R8-10.ADDED.NAV.EXISTS / COUNT / CSS_VISIBLE | eq | true / 1 / true | true / 1 / true |
| R8-10.REMOVED.SHELL.EXISTS / COUNT / CSS_VISIBLE | eq | true / 1 / true | true / 1 / true |

同值通知/设置后的加载基线未重新选取。无事件轮询只证明各记录中的 60/80ms 窗口，不外推无限时间。初始 Strict 加载实际为2，不以初始必须1作为门禁。

## 测试工具问题：R8-TOOL-ID-001

分类：**验收工具阻塞，非产品缺陷**。测试工具优先级 P1（阻断本轮后续门禁）；不映射为产品 P1。最小复现与证据为已执行源码/时间线的只读分析，未再运行目标：

1. `R8-10` 单独调用 `ui('REMOVED.NAV', selector, false)`，其三个比较均通过；序号914～919。
2. 后续调用 `chrome('REMOVED')`。其中 Shell 的存在、数量、样式可见性均通过，终点为序号931。
3. `chrome` 下一步展开同前缀 `REMOVED.NAV`。测试的 `used.has(aid)` 检查在写入第二个 assert_enter 前抛出错误。两个逻辑观察还对应不同 selector/预期：一个检查已移除模块链接不存在，一个应检查整个导航仍在，不能共用同一个 ID。
4. 直接进入 finally，序号932为 cleanup_enter；未执行后续 Agent、theme/privacy、新 beta 页面及节点11～13。未取得的实际值保留 unknown/not_run，不用旧值填补。

期望：各独立观察有不同稳定 ID，完整执行原断言。实际：辅助唯一性保护阻断重复 ID，runner 给出该节点 Error / timeout=false。[只读定位](../../tests/independent/desktop/evidence/r8-modules/first-run-analysis.json)保存冻结源行与已存在记录。

**证据限制：**原始 Error.message 没有保留；上述定位是冻结源码与 journal 顺序重建，不宣称从原始异常恢复了错误文本。`result.firstFailure=null` 仅代表没有被记录的 assert_fail/operation_fail，不代表节点没有异常；`cleanup_terminal.passed=true` 只反映已有比较标记，不能覆盖 runner failed。这个辅助抛错没有单独 terminal，是本轮取证缺口，一并提交审阅。

没有修正冻结测试后重跑。任务卡只允许“目标开始前”的无副作用工具错误定向更正一次，本次不满足；也不是某个 Windows 设备条件不可用而可跳过的情形。尚需总控决定下一轮是否允许仅修测试 ID/辅助异常记录并执行剩余门禁，不需要执行方修改产品。

## 时限、资源与未执行范围

[进程回执](../../tests/independent/desktop/evidence/r8-modules/modules/process.json)、[控制器时间线](../../tests/independent/desktop/evidence/r8-modules/modules/controller.journal.jsonl)：CLI 总计5909ms，初始化到首个 body 约3164ms；最长 body680.12ms，最长 cleanup58.65ms，均在60秒初始化、每节点15秒正文、5秒清理、300秒CLI内。无硬超时、无强制清理。

CLI PID30140 和登记 worker PID22216 均经路径/父子/创建时间核实并实际退出，分别 exit1/exit1。没有用父退出码代替子退出码；不推断完整历史系统后代。10个已进入节点的真实 root 卸载、订阅平衡/active0、globals恢复、安全 canary、unhandled/jsdom及禁止调用计数检查全部通过。未输出原始错误、DOM、秘密或财务正文，数据均为虚拟。

开发兼容 `module-readiness18 + lazy8 + Shell1 + composition1 = 28`：**0 executed / 28 not_run**，独立前置未通过。补充公开缺口 suite：not_run。Windows产品 **0/8**、safeStorage辅助 **0/4**、真实chunk注入 **0**。因此后台 managed/认证/canonical 模块、新包真实页面、session/同ID重启、recover、普通关闭/Tray、原生老化提示全部未产生本轮设备证据，不能引用执行方结果代签。

## 原24项增量映射

原预期保持 [120项矩阵](phase-4-modular-agent-host-test-matrix.md#52-p4-bwindows-shell设置和毛毛24-项)和 [R7完整缺口](phase-4-c12-r7-recovery-windows-report.md)。本轮只追加B备注，整项状态不变：**0 passed / 1 failed / 19 blocked / 4 not_run**；UI-02 failed 来自历史验收状态，不是本轮新产品失败。

| 原ID | 整项状态 | 本轮增量与尚缺条件 |
|---|---|---|
| P4B-SEC-01 | blocked | 未启动新包；真实 renderer 隔离未补齐 |
| P4B-SEC-02 | blocked | 真实 CSP/导航/窗口/外链未执行 |
| P4B-SEC-03 | blocked | 未新增实际 preload 枚举；旧证据只读保留 |
| P4B-SEC-04 | blocked | 真正 IPC sender/origin/参数拒绝与副作用未执行 |
| P4B-SEC-05 | blocked | 虚拟 jsdom 安全检查不等于 main DPAPI、会话重启及存储/转储检查 |
| P4B-SEC-06 | blocked | 新包 loopback/nonce/Bearer/origin 门禁未执行 |
| P4B-SEC-07 | blocked | 全部恶意文本/布局矩阵未补齐；只检查本轮错误canary不泄漏 |
| P4B-SEC-08 | blocked | 模块读取/lazy拒绝 DOM/console canary检查通过；局部render邻接未执行，真实包故障/日志仍缺 |
| P4B-SUP-01 | blocked | owned真实后端/非owned对照未执行 |
| P4B-SUP-02 | blocked | 端口冲突、ready/nonce/超时等真实故障未执行 |
| P4B-SUP-03 | blocked | renderer离线保页通过；Supervisor崩溃/退避/次数边界未执行 |
| P4B-SUP-04 | blocked | 单实例第二启动和 external_dev对照未执行 |
| P4B-SUP-05 | not_run | 正常退出/强关/注销完整场景没有新证据；注销无授权 |
| P4B-SUP-06 | blocked | 额外outbox调用为0只是无副作用；同ID恢复/重启/一次提交及原生老化提示未执行 |
| P4B-UI-01 | blocked | 新同步01～08通过，10部分证据；10未完成、13旧effect/卸载未运行，不签完整通过 |
| P4B-UI-02 | failed | 09明确retry+1/状态保持通过；11/12邻接未运行，新包chunk/session仍缺；历史failed保持 |
| P4B-UI-03 | blocked | DTO漂移/生成物公开缺口未执行 |
| P4B-UI-04 | blocked | 旧路径/setting/严格结构证据只读保留；未新增完整注册/分支独立复核 |
| P4B-CMP-01 | blocked | jsdom Agent入口局部检查通过；真实单毛毛/形态子状态完整条件未执行 |
| P4B-CMP-02 | blocked | 首次提示、隐藏、Tray恢复、第二次关闭未执行 |
| P4B-CMP-03 | blocked | 三种closePolicy/取消/Tray及真实退出未执行 |
| P4B-CMP-04 | not_run | OS启动项无授权，E2E不得代签 |
| P4B-CMP-05 | not_run | jsdom主题隐私保持不等于多屏/DPI/拔屏/夹取/全屏/键盘设备证据 |
| P4B-CMP-06 | not_run | 透明降级、高对比/动效/焦点/颜色等设备条件未执行 |

## 交付完整性与后续决定

[终点审计](../../tests/independent/desktop/evidence/r8-modules/end-audit.json)列818起点、旧R6/R7材料、外部冻结输入及授权差异；[交付清单](../../tests/independent/desktop/evidence/r8-modules/delivery.sha256)与[复算回执](../../tests/independent/desktop/evidence/r8-modules/delivery-verification.json)以完整POSIX相对路径排序、UTF8无BOM/TAB/LF形成。原始源码/首次证据保持；旧主报告和人工清单仅追加，120行/12列/原预期/A64与C20/D12状态保持。

终点实际结果：818起点 **814项保持+4项授权文档变化**；旧R6清单805保持+5项既有总控变化+4项本轮文档变化；旧R7交付64保持+相同4项授权文档变化。外部813/140/67/12443/73全部逐项匹配；另外核对完整依赖副本12677项匹配。EXE/asar/lock与9份依赖元数据保持，7项运行前冻结、6项首次结果保持。只读diff-check exit0、staged0；全局ignore读取权限与行尾转换warning分别保留。

终点工具初次将67项Python资源清单误当整个resources目录集合，遇到另行冻结的app.asar而报inventory_drift；同理12443冻结依赖是执行方已说明的12677完整副本子集。已保留[只读审计更正](../../tests/independent/desktop/evidence/r8-modules/audit-tool-correction.json)：所有原摘要照常逐项核验，只把asar放在完整out清单核对，并补验交付的完整依赖清单。此更正不改变冻结测试或重启任何目标；未发现受验材料漂移。

普通只读文件定位曾使用错误路径，已用文件列表纠正；一次只读Python显示读取遗漏UTF8产生UnicodeDecodeError，显式UTF8读取后核对原baseline与120行完全相同，未改变任何基线或动态结果。Git只读检查出现用户全局ignore配置权限warning时按原样登记，不修改系统配置。没有Git写操作、其他角色启动、产品/依赖/包修改、真实provider/Docker/OpenClaw/微信、设备设置变更或要求用户即时操作。

本轮可以接受9个节点的有限独立证据，但不建议关闭完整 LAZY-001、UI-02 或 P4-B。下一步只需总控裁定测试工具修正与剩余验收的范围、快照和单次预算；测试方在此停止，不自行启动返修或下一任务。
