# P4-C12-R7-RECOVERY 恢复与 Windows 增量验收报告

执行日期：2026-10-09、2026-10-12，Asia/Shanghai。测试智能体唯一负责人；control `2026-10-09T09:21:45+08:00`，[任务卡](../coordination/prompts/p4-c12-r7-recovery-tester.md)。交付状态：**blocked / finished，提交总控 review**。本报告不宣布 LAZY-001、UI-02 或 P4-B 整体验收完成。

## 结论与统计口径

**新恢复合同首次通过，5 组全部执行；必要兼容 10 项、补充独立结构 8 项全部通过。随后执行首次真实 Windows W1，在日常财务页面就绪观察处失败，已按任务停止并清理自有进程。** 没有重跑 R6 冷入口 B、旧 P/A/B、D15/D16，没有改产品、依赖、受验包或执行 Git 写操作。

| 范围 | 本轮实际结果 | 统计边界 |
| --- | --- | --- |
| 独立 `R7-RECOVERY-01` | 1 passed；5/5 组完成 | 一次挂载、一个 CLI/worker，不把组数当测试数 |
| 恢复逐比较记录 | 212 enter / 212 terminal，完整配对 | 208 正式比较 passed；2 旧计数对照不同；2 标量自检比较，不另计业务节点 |
| 补充严格注册结构 | 8 passed / 0 failed | 一个文件一次；6 处额外字段、必需结构、非法结构输入 |
| 本轮独立 Vitest 合计 | 9 passed / 0 failed | 不包括历史 R6 B，不包括开发测试和 Windows 场景 |
| 必要开发兼容 | lazy 8 + Shell 1 + composition 1 = 10 passed | 三个文件各一次，独立列出；module/unhandled error 均 0 |
| 真实 Windows W1 | 场景未通过；13 个比较通过、1 个观察失败 | 14 个比较不是 14 个独立测试；首次错误 `W1-DAILY-PAGE` |
| 真实产品 / safeStorage 辅助 / chunk 注入 | 1/8、0/4、0 | W2～W5 未启动；原生老化提示、会话重启与关闭策略尚未验收 |
| 动态重试 | 0 | 已进入目标后的首次结果永久保留，没有修脚本后复跑 |

[R6 冷入口首次报告](phase-4-c12-r6-env-windows-report.md#公开-b-的同次来源四断言和安全)只读复用：四条原公开断言、来源、安全与清理已获总控接受。本轮不把它计为新执行。旧 R6 恢复节点仍为 failed；新计数值不能补造旧 R6 的实际比较。

## 输入绑定与可复算材料

[start-audit.json](../../tests/independent/desktop/evidence/r7-recovery/start-audit.json)记录接单时 **743/743** 原字节匹配；起点清单 SHA-256 为 `244d5246c6c7a8479c40fb2d13388badfc78701fc081aba22cad1fa5682b8842`。R6 交付63、冷/恢复源码9/5、首次9/7均匹配。外部固定根为 `C:/MarisLazyR5/R5-20261002-222300`，源码389、产物140、资源67及 EXE/asar/lock 保持。固定 EXE SHA-256 `64ce71f3a7b3055f9ad27f6d611e28c4af7e9ba8b86d8b21399b7b422844a80e`；asar `5ba47909537e1419dc275fa3ca1e5e076a1aa6d5c0205229f91defb92ddd0931`。

Node24.21.0、原生 jsdom30.1.1 及真实 React/DOM/Router 使用冻结物理根；7 个依赖元数据和 jsdom API 摘要核对。没有安装、下载、构建、重新打包、依赖实验或系统环境修改。[resume-audit.json](../../tests/independent/desktop/evidence/r7-recovery/resume-audit.json)记录 10 月 12 日用户继续后的核对：742 项未变、本人角色1项授权变化；恢复与兼容冻结材料保持。中断期间没有连续可观察运行的证据，未把旧 active 标签当成持续执行。

| 材料 | 用途 |
| --- | --- |
| [assertion-map.md](../../tests/independent/desktop/evidence/r7-recovery/assertion-map.md)、[JSON](../../tests/independent/desktop/evidence/r7-recovery/assertion-map.json) | 53 个比较定义、17 类操作；原 R6 行/表达式、新 ID、预期/观测、正式/旧对照/自检映射 |
| [recovery-source.sha256](../../tests/independent/desktop/evidence/r7-recovery/recovery-source.sha256)、[recovery-first.sha256](../../tests/independent/desktop/evidence/r7-recovery/recovery-first.sha256) | 恢复7项源码/映射与首次结果冻结 |
| [compat-source.sha256](../../tests/independent/desktop/evidence/r7-recovery/compat-source.sha256)、[compat-first.sha256](../../tests/independent/desktop/evidence/r7-recovery/compat-first.sha256) | 兼容4项工具与三个文件首次结果 |
| [public-source.sha256](../../tests/independent/desktop/evidence/r7-recovery/public-source.sha256)、[public-first.sha256](../../tests/independent/desktop/evidence/r7-recovery/public-first.sha256) | 公开结构5项源码及首次结果 |
| [windows-source.sha256](../../tests/independent/desktop/evidence/r7-recovery/windows-source.sha256)、[windows-first.sha256](../../tests/independent/desktop/evidence/r7-recovery/windows-first.sha256) | W1 runner、限定 OS helper、启动计划与首次两文件 |
| [end-audit.json](../../tests/independent/desktop/evidence/r7-recovery/end-audit.json) | 起终输入、旧证据、矩阵/前缀、实际执行、资源和只读 Git 检查 |
| [delivery.sha256](../../tests/independent/desktop/evidence/r7-recovery/delivery.sha256)、[verification](../../tests/independent/desktop/evidence/r7-recovery/delivery-verification.json) | 最终交付清单及逐文件复算；完整仓库相对 POSIX 路径排序、UTF-8无BOM、TAB、LF |

## 恢复正式门禁与旧对照

真实 StrictMode/DesktopApp/compileRegistry/Router/Shell，一次生命周期；两个虚拟模块，外围 bridge 与可信页面 loader 可控。没有生产 main 再导入、内部 Router 观察器、loader 包装或真实第二业务模块。每条比较进入前写稳定 ID、组/操作号及 operator，观测一次后即时写安全 expected/actual。记录器同 worker、产品导入前标量自检通过：不同数字保留两个值，布尔通过，禁止字段原文未写入。

[恢复 result](../../tests/independent/desktop/evidence/r7-recovery/recovery/result.json)和[完整 journal](../../tests/independent/desktop/evidence/r7-recovery/recovery/worker.journal.jsonl)保留全部比较；首个正式失败为 null，cleanup/operation failures 均为空。

| 组 | 主要正式要求及实际结果 | 状态 |
| --- | --- | --- |
| 1 初始隔离 | 局部错误、hash、Shell/nav/Agent与安全正确；固定 N0=2，60ms 结束仍2，无重新选基线 | passed |
| 2 明确恢复 | dark/privacy/runtime 操作后仍2；一次 retry 到3，严格增量1，页面恢复；原状态/订阅/Shell身份及两次设置写入保持 | passed |
| 3 持续失败与切换 | 健康页/settings可切换；明确失败重试按原增量，无操作观察不增长 | passed |
| 4 在途与离开 | 多次点击只增加一次请求；pending状态正确，离开后旧结果不覆盖健康页/hash | passed |
| 5 render异常 | 错误局部且安全；明确retry仅增加一次loader并恢复；状态与额外调用保持 | passed |

| 仅旧计数对照 | 原 expected | 本次 actual | 处理 |
| --- | --- | --- | --- |
| `legacy_initial_exact_1` | 1 | 2 | 对照 failed；正式固定基线门禁 passed |
| `legacy_first_retry_total_2` | 2 | 3 | 对照 failed；正式单次 retry 增量1 passed |

这是“新恢复合同通过，旧计数对照差异”，不是旧 R6 不变节点通过，也不是允许任意自动重试。60ms 观察不外推无限期无增长。

## 时限与实际清理

恢复初始化25049ms、controller正文4656ms、报告前总体29888ms；实际UI清理收尾比较46.01ms。满足初始化60秒、正文10秒、清理2秒、总体75秒及单次UI观察5秒限制。真实 root/DOM/global/console/监听恢复，订阅2/2、active0、rescue0、denied0、consoleLeak=false、jsdomError0。

恢复 CLI17700、worker18984 均退出；CLI exit0，worker句柄实际 exit1，原因未核实，不能复制父退出码或声称同码。兼容8995ms、公开结构646ms，均 root exit0、登记 worker exit1，身份已核对、全部退出，无超时、强杀或观察错误；这些 worker 的终止原因也未额外诊断。上述原始退出码与 runner 的全通过结果并列保存。

## Windows 首次发现：W1-DAILY-PAGE

跟踪号 **P4-C12-R7-WIN-001**。分类：页面就绪验收受阻；涉及 UI-01/02 原 P1 风险，**产品根因和严重级别待定，不提交为已证实产品 P1**。最后脱敏错误为 `id=W1-DAILY-PAGE, kind=other, code=operation_error`。没有原始异常文本或堆栈。

最小复现事实如下；这是已执行记录，不授权再运行：

1. 按[冻结计划](../../tests/independent/desktop/evidence/r7-recovery/windows-plan.json)，用固定 Node 直接 `spawn(shell:false)` 启动固定 EXE。新虚拟根 `C:/MarisC12/C12-R7-RECOVERY-20261012-1103`，新 main profile，仅为普通退出准备 `closePolicy=quit`；其它初始项按现有虚拟设备合同。E2E 隔离真实 AppData，抑制 OS 启动项修改，没有退出 timer。
2. 按路径、创建时间、专属标记、祖先关系核验 root3448；从新 profile 的动态 loopback CDP 端口附加。只使用 Playwright CDP，没有 Electron launcher、app.asar启动、PID提升或 fuse修改。
3. 主/毛毛 Node 隔离、窄 bridge、CSP合同/inline拒绝和未知新窗拒绝通过。17.75秒附近，实际 runtime online/managed/authenticated 且 errorCode=null；`modules.list()`有且仅有启用的 daily_finance、canonical `daily_finance.assistant@1`，通过。
4. 随后等待实际 `#daily-title` 可见，观察窗口5000ms。预期该页面及 Shell 导航/Agent 成立，**expected=true；actual=unknown**。等待调用约5008.65ms未返回有效样本，后两项组合观测没有执行。没有 DOM数量/可见性/hash 的终态取样或截图，不能把 actual 写成 false、0 或“Shell消失”。
5. 首错后停止后续状态改变和场景。按已验证 root 身份定向清理树，30.075秒收口，root exit1、forced=true、timeout=false、cleanupError=null；8个登记进程和其监听均无残留。后续只读核对再次确认原创建时间对应的8个进程已不存在。

[首次 result](../../tests/independent/desktop/evidence/r7-recovery/windows-W1/result.json)、[首次 journal](../../tests/independent/desktop/evidence/r7-recovery/windows-W1/journal.jsonl)、[只读分析](../../tests/independent/desktop/evidence/r7-recovery/windows-first-analysis.json)、[资源后检](../../tests/independent/desktop/evidence/r7-recovery/resource-postcheck.json)均保留。W1共13个比较passed、1个观察failed；场景整体不通过。正常关闭阶段未到达，不能把定向强制清理当正常退出、Tray或SUP-05通过。

只读源码核对显示：[DesktopApp](../../apps/desktop/src/renderer/module-routes.tsx)在挂载 effect 中读取一次 modules，runtime订阅仅更新runtime；[composition-root](../../apps/desktop/electron/main/composition-root.ts)初始模块为空、连接认证完成后才更新模块并发布runtime。因此初读发生在就绪之前是**可能原因**。当前未记录 renderer 最初收到的 modules 值，不能把这个静态解释升级为本次已证实因果，也不能用延长等待或页面重载补签。

### Windows 取证限制与停止理由

- Playwright等待异常被既有安全白名单归为 `other`；错误原文未保存。`first_failure` journal写入时被详情中的stage覆盖为 `runtime`，但 result.json明确保留 firstFailure、ID及阶段。首次文件不更改，只读分析单列此工具问题。
- W1未收集页面终态组合条件的各独立值。**R7恢复要求的212对比较完整**；W1不能沿用该完整性结论。缺失值明确unknown，不签产品通过或已确认失败原因。
- 没有从本次失败提取到真实chunk命中/撤销/重试证据；chunk可控性步骤尚未执行，不能将计划中的file/asar限制写成实测结论。注入0。
- safeStorage辅助未启动，专属虚拟加密profile/db保留在仓库外；文件存在不算会话保持或DPAPI验收。无个人数据、token或数据库正文入库。
- 当前登记进程及监听清零已观察；完整历史后代枚举和各子进程自身退出码没有证据。强制收口不会补签产品退出合同。
- 已经尝试的定位仅为首次journal/result、既有固定源码接线和资源后检。目标已经开始，不符合“明确产品启动前工具错误”的一次更正规则；没有新诊断目标或动态重试。需总控决定页面就绪与初读模块时序的最小后续取证/返修范围。

## 24项增量映射

原完整预期、历史通过/失败及缺口见[R3完整映射](phase-4-c12-r3-route-windows-report.md)和[R6增量](phase-4-c12-r6-env-windows-report.md#24项增量映射)。本轮只追加下列事实；120唯一ID/12列/原要求保持。**B仍0 passed、1 failed、19 blocked、4 not_run；A64 passed，C20/D12 not_run。** UI-02整项与LAZY-001由总控接受后裁定，本轮不自行关闭。

| ID | 整项状态 | 本轮新增证据 | 仍缺 / 边界 |
| --- | --- | --- | --- |
| P4B-SEC-01 | blocked | 真实主/毛毛renderer无require/process/Buffer/ipcRenderer，固定preferences来源沿用 | 该探测不是完整内存/任意preload域审计；整项待总控组合核对 |
| P4B-SEC-02 | blocked | 真实CSP合同、inline不执行、未知新窗拒绝 | data/javascript/未知导航、批准外链主进程路径未完成 |
| P4B-SEC-03 | blocked | 真实主bridge六组方法及companion两方法精确键集合；companion无main bridge | 不把枚举与typeof探测扩大到所有非枚举属性/跨域攻击 |
| P4B-SEC-04 | blocked | 沿用历史公开校验；W1非法参数阶段未到达 | 真实sender/origin/未知channel/副作用全组合仍缺 |
| P4B-SEC-05 | blocked | 实际新虚拟owner已认证；没有导出秘密 | safeStorage辅助、重启刷新、renderer持久/内存与dump均未完成 |
| P4B-SEC-06 | blocked | 本次CDP所有权及loopback验证；收口时Host监听为loopback | 错nonce/origin/access/远程等请求阶段未到达；不把CDP当Host认证 |
| P4B-SEC-07 | blocked | 开发Shell恶意标签兼容1项单列；恢复安全DOM正式比较通过 | 独立全场景HTML/RTL/长文本与实际布局仍缺 |
| P4B-SEC-08 | blocked | 恢复DOM/console无异常正文泄漏；W1已观察console一条无被测秘密/路径特征 | 未测实际preload/backend/chunk故障与request ID、完整日志/dump |
| P4B-SUP-01 | blocked | 本轮限定owned root/祖先/创建时间清理，8登记资源退出 | 产品自己停止权限、伪造同PID、外来进程对照仍缺 |
| P4B-SUP-02 | blocked | 实际managed进入online且认证成功，随机loopback Host已观察 | 端口冲突、坏nonce、ready超时及产品自身清理仍缺 |
| P4B-SUP-03 | blocked | 沿用历史逻辑证据 | 未执行真实故障/退避/手动恢复；不扩大故障注入 |
| P4B-SUP-04 | blocked | 必要composition开发单次回归通过 | W2/W3单实例与external_dev真实场景未执行 |
| P4B-SUP-05 | not_run | 测试方失败收口已完成，不是本项业务验收 | 正常退出/强关行为/注销、端口锁与外来对照仍缺；注销无授权 |
| P4B-SUP-06 | blocked | 旧outbox42保持不重跑；W1同ID阶段未到达 | 原生老化保留/删除、重启同ID、恢复GET一次写均未执行 |
| P4B-UI-01 | blocked | 真实接口canonical模块通过，公开结构8项通过 | W1实际日常页面就绪未取得证据；全部启/禁/版本/未知导航组合未完成 |
| P4B-UI-02 | failed | R6冷B只读复用；新恢复5组/208正式比较通过 | 旧failed历史保留；Windows真实chunk/session仍缺，W1页面就绪受阻 |
| P4B-UI-03 | blocked | 未重复旧集合 | 生成物过期/DTO漂移与CI失败定位独立门禁未执行 |
| P4B-UI-04 | blocked | 6处strict额外字段、缺6类结构、6类结构非法输入共8节点通过 | 原路径/setting/ASCII证据沿用；全部启动/编译映射和分支审阅尚未整体关闭 |
| P4B-CMP-01 | blocked | 真实主/毛毛页面及不同窄bridge存在，未知新窗后仍2页 | 全状态流、第二虚拟contribution、Agent入口/无写入设备证据不完整 |
| P4B-CMP-02 | blocked | 未到达首次关闭/提示场景 | 默认提示一次、Tray恢复、重复关闭/内容保持仍缺 |
| P4B-CMP-03 | blocked | 仅准备虚拟quit设置，普通WM_CLOSE阶段未执行 | hide/ask/cancel/quit和真实Tray行为全部未通过 |
| P4B-CMP-04 | not_run | E2E禁止OS启动项变更 | 实际默认/启用/禁用启动项无授权，保持人工缺口 |
| P4B-CMP-05 | not_run | jsdom主题/隐私状态保持通过，不作设备证据 | 多屏/DPI/拔屏/位置夹取/全屏/键盘条件未执行 |
| P4B-CMP-06 | not_run | 未修改OS主题；没有透明降级现场 | 透明fallback、高对比/动效/焦点/色彩语义等原人工条件保持 |

## 工具更正、文件边界与交接

本轮静态问题与动态业务结果分列：最初普通exec在创建进程前失败，已授权的另一执行路径恢复读取；公开文件生成的config点号/连字符错误1次已修正；Node `--check`不适用于该TS注解而报错，外层PowerShell未阻断随后首次Vitest执行，其8 passed保留，不能写成该静态门禁事先通过；Windows helper生成曾发生外层here-string解析冲突，未启动产品，改用结构化文件写入后正常解析。均没有目标动态重试。公开process记录的scope字面值误称three_public_files，实际include/result均明确只有一个文件8项，保留原记录并在此纠正标签。

两份早期新增恢复文件使用了 `r7-recovery.test.tsx`、`r7-recovery.config.mjs` 名字，未严格带任务卡通配式 `r7-recovery-*` 的末尾连字符；属于测试文件命名偏差。它们处于测试专属目录、内容与执行前冻结摘要一致。为保留首次源路径与摘要，未擅自改名/改写冻结清单；交总控审阅该偏差。没有修改执行方文件、其他角色或控制面。

原C12报告与人工清单只追加，旧字节前缀保持；矩阵只追加B证据备注，原120行保持。终点审计核对起点743中的739项保持、4份授权共享文档变化，R6交付59项保持、4份共享变化，所有R6源码/首次及本轮冻结源码/首次不变。具体最终交付数量和清单摘要见 delivery-verification.json，不用手工估数替代复算。

本轮没有OS注销/重启、启动项/主题/多屏修改、要求用户点击、真实provider/DeepSeek、Docker/PG、OpenClaw/微信或V002操作。遗留人工清单保留。唯一新虚拟外部根保留为只读取证现场；无活动owned进程、监听或测试会话。新Vitest专属cache保留在R7证据树，不清旧缓存或不可变环境。

交接总控：接受新恢复合同、结构补充和必要兼容的有限通过证据；审阅首次 W1-DAILY-PAGE 页面就绪观察及上述工具限制，再决定是否允许有界补充观察或分配产品返修。本测试角色 **blocked / finished**，等待review；不自行创建后续任务、不重跑W1、不启动W2～W5或辅助Electron，不进入P4-C/D。
