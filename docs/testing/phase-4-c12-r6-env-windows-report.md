# P4-C12-R6-ENV 原生环境加载与公开验收增量报告

执行记录：2026-10-04；最终交付审计：2026-10-05，Asia/Shanghai。交付状态 **blocked / finished，提交总控 review**。测试智能体唯一负责人；control `2026-10-04T19:53:00+08:00`；[任务卡](../coordination/prompts/p4-c12-r6-env-tester.md)。仅使用虚拟数据，不改产品、依赖或 Git 状态。LAZY-001、UI-02、P4-B 均未自行关闭。

## 本轮结论和执行范围

**原生 jsdom 加载已实际返回，公开冷入口 B 首次通过；随后同任务进入独立恢复，但恢复节点的第一组出现断言失败。** 后续恢复、开发兼容与 Windows 停止，没有重复 B 或启动 A/P/D16。冷入口通过只证明本次初始故障隔离，尚不足完整恢复或设备验收。

| 范围 | 实际次数 / 结果 | 结论边界 |
| --- | --- | --- |
| `R6-ENV-UI-02-COLD` | CLI 1、main 1、fixture 1；独立节点 1 passed | 四原公开断言、安全、来源、清理通过 |
| `R6-ENV-RECOVERY-01` | CLI 1、main 0；独立节点 1 failed | 5 组场景中第 1 组失败，第 2～5 组 not_run；不是 5 个已执行节点 |
| 本轮独立合计 | 2 个唯一节点，1 passed / 1 failed | 两个 CLI 分属已授权 B 与后续恢复，不是 B 重试 |
| 动态工具更正 / 重试 | 0 / 0 | 冷入口默认 CLI 一次已使用；恢复已进入真实产品，不按前置工具错误重跑 |
| lazy 开发八项及 Shell/composition 兼容 | not_run | 恢复未通过，未扩大到相邻测试；不计为独立 passed |
| Windows 产品 / 辅助 safeStorage / chunk 注入 | 0/8、0/4、0 | 未创建外部测试根或真实 profile/session；不能以 jsdom 替代 |
| P、旧 A/B、D16、后端全量、Docker/OpenClaw/微信/provider | 0 | 未重复已完成实验及外部联调 |

原 R5 仍是初始化 blocked，main/四断言未执行；本轮成功不倒写旧结果。R6 同时改变环境加载入口和初始化预算，不是单变量根因实验，也未证明旧超时的充分原因。

## 固定输入、环境修正和静态差异

[start-audit.json](../../tests/independent/desktop/evidence/r6-env/start-audit.json)：**679/679** 原字节匹配、staged=0；起点清单 SHA-256 `3a1adb3b69f0c17d593c497149897e80d50d99a6e170c558035f18df41d3b966`。旧 R5 交付41、冻结源码10、首次记录6全部匹配，保留旧字节及行尾。外部固定源码389、out140、资源67和 EXE/asar/lock 匹配；7 个依赖元数据/物理根与 Node24.21.0核对。

| 文件组 | R5 → R6 的唯一有效差异 | 静态核验 |
| --- | --- | --- |
| setup | 日志建立后，Node `createRequire` 锚定固定 jsdom package.json 绝对 file URL；先核验版本/type/main、真实路径和摘要，再 require 同一 lib/api.js | 原始 JSDOM/VirtualConsole 浅容器传递，未包装、未冻结第三方对象；正文前未创建 DOM |
| cold test | 移除顶层 `await import('jsdom')`，读取上述原始引用 | React 仍真实动态 import；完整正文除 R6 标识外逐字一致 |
| config / resolver / fixture / reporter | 新标识、证据/cache路径 | native configLoader、node/fork/maxWorkers1/isolate、真实单根 React/Router、精确 resolver 和持续 throw 保持 |
| controller | 新 control 版本、R6标识路径、初始化60秒/总体75秒 | 正文10秒、UI5秒、清理2秒、Vitest外层12秒保持；独立外部单调计时 |
| verifier | 核验新原生入口、摘要及正文等价 | 静态仅 resolve/读文件，不 require jsdom，不运行依赖练习节点或产品 |

冷入口 [9项冻结源码](../../tests/independent/desktop/evidence/r6-env/cold-source.sha256)、[逐行差异](../../tests/independent/desktop/evidence/r6-env/static-differences.diff)、[静态核验](../../tests/independent/desktop/evidence/r6-env/static-preflight.json)。恢复另有5项源码及独立冻结，不修改这9项冷源码。

固定 jsdom：30.1.1、commonjs、main `./lib/api.js`，真实 API 为 `C:/MarisLazyR5/R5-20261002-222300/workspace/node_modules/jsdom/lib/api.js`；package SHA `72dff7780a7791071ebd9cb219262522fc28d0ce5570c41dc7bb69b2700db067`，API SHA `bcf577e0fe48db5b9b6a917228f8be8e62d83696b87eb6711d705d28772adba7`。两次 worker 均即时记录 identityMatched、native_jsdom_enter/resolved，未回退系统/用户依赖。没有安装、构建、打包、修改 lock 或 node_modules。

## 公开 B 的同次来源、四断言和安全

[first result](../../tests/independent/desktop/evidence/r6-env/cold/result.json)、[worker journal](../../tests/independent/desktop/evidence/r6-env/cold/worker.journal.jsonl)、[resolver journal](../../tests/independent/desktop/evidence/r6-env/cold/resolver.journal.jsonl)：新 worker **35656**，父CLI **32404**（以原始journal为准）。真实 main/StrictMode/默认loader一次，初始空hash；main import resolved与act_return分别存在，fixture一次真实持续throw，无手动mock、二次成功替身或cache操纵。

| 同一样本 ordinal=1 | 实际 |
| --- | --- |
| 当前自然 hash | `#/daily` |
| `main.shell .content [role="alert"]` 安全文案 | “页面暂时无法打开”，passed |
| Shell | passed |
| Shell 内模块导航 | passed |
| Shell 内统一 Agent 面板 | passed |

四条软断言均实际执行、4/4 passed；`faultSourceValid=true` 与 `publicTargetResult=true` 分列。来源依据本次精确映射、importer、父子身份、真实求值记录、固定fixture、新源码/产品摘要及冷入口合同，**不使用 hash/alert 反算来源**。未采集内部 Router/abort 字段。

DOM无原始虚拟异常/路径/堆栈；console监测0条泄漏、warning0。真实观测的 recover、settings、outbox、windowAction、external、unknownBridge、fetch、XHR、WebSocket、EventSource 共10类额外调用均0；runtime读2、Host模块读2、订阅2符合实际StrictMode生命周期。上述桥接/网络边界覆盖额外auth/provider/财务写入入口，未把未监测的全系统状态写成零。

真实 root 卸载、DOM关闭、监听移除、global/console恢复全部记录；生产退订2/2、active0、备用退订0、root空，清理后额外调用仍0。CLI exit0、登记worker已退出，无强杀、无timeout、无runner/unhandled错误。

## 实际时限与首次材料

| 阶段 | 上限 | 冷入口 B | 独立恢复 |
| --- | --- | --- | --- |
| controller root→完整 body_enter | 60000ms | 22479ms | 1348ms |
| 原生 jsdom enter→resolved（worker本地） | 计入初始化 | 18178.412ms | 647.019ms |
| React enter→resolved（worker本地） | 计入初始化 | 47.942ms | 8.377ms |
| 正文（worker body→cleanup） | 10000ms | 3281.987ms | 335.061ms |
| controller 收到正文→清理标记 | 10000ms | 3274ms | 323ms |
| UI条件观察 | 5000ms | 28.457ms | 第一组未保留单独观察时长 |
| UI清理（worker本地） | 2000ms | 8.317ms | 1.080ms |
| controller总体含首次报告 | 75000ms | 25881ms | 1781ms |

各计时只在本进程单调轴内相减；controller接收完整日志有采样延迟，不与worker毫秒拼接。controller为初始化/整体收口预留余量，阈值59950/74500ms；本轮均自然结束，未触发阈值。cold/process.json的写报告前25876ms与最终25881ms区分保留，恢复对应1776/1781ms。native返回不是 React 或产品可用的替代证据，后续阶段均有自身记录。

冷入口 [cold-first.sha256](../../tests/independent/desktop/evidence/r6-env/cold-first.sha256)与恢复 [recovery-first.sha256](../../tests/independent/desktop/evidence/r6-env/recovery-first.sha256)永久保留各首次journal/runner/双流/进程记录。stdout只有安全计数行，stderr为空；没有原始异常/DOM正文/会话值。

## 恢复失败与证据限制

独立恢复使用同一原生环境方法；在正文导入真实 DesktopApp/Router/Shell/compileRegistry，两个虚拟模块 `/broken` 与 `/healthy`，外围bridge及可信页面loader可控，未导入main或生产第二业务模块。采用独立步骤和断言，没有复制开发八项来充当独立证据。

| 场景 | 本次状态 | 原设计覆盖 |
| --- | --- | --- |
| 1 初始隔离 | failed | 挂载实际StrictMode/DesktopApp，等待局部安全alert，核验初始loader次数、hash及Shell/导航/Agent/隐私边界 |
| 2 显式恢复及状态保持 | not_run | 一次明确retry成功、主题/隐私/runtime和订阅保持，仅两次用户设置写入，无额外写入 |
| 3 持续失败与导航 | not_run | 无自动循环、一次显式失败重试、健康/settings可切换 |
| 4 重复点击与在途离开 | not_run | 多次点击只有有限请求，在途离开后旧结果不覆盖健康页 |
| 5 render异常及重试 | not_run | 局部render边界、安全console、有限retry恢复 |

**复现入口**为 [r6-env-recovery.test.tsx](../../tests/independent/desktop/r6-env-recovery.test.tsx) 的 `R6-ENV-RECOVERY-01`，固定[5项源码](../../tests/independent/desktop/evidence/r6-env/recovery-source.sha256)及其配置/controller；本报告不授权再运行。预期场景1完整通过后继续2～5；实际场景1进入后出现 **1条 AssertionError，timeout=false**，runner 0 passed/1 failed、moduleError0、unhandled0，root exit1。

脱敏 reporter 只保留错误类型、数量与超时布尔，没有具体 assertion名称、expected/actual或操作序号。因此不能从这份首次记录确认究竟是初始loader精确次数、hash或其他公开断言失败，也不能把测试中的预期1次伪写成实际1次/2次。只读缓存补证仅有文件级duration/failed，不含比较值；见[cache-inspection.json](../../tests/independent/desktop/evidence/r6-env/cache-inspection.json)。该证据缺口本身阻塞产品归因；**产品严重级别 unverified，不新建已证实P0/P1产品缺陷**，也不因工具疑点忽略实际失败。

已经尝试：核对首次worker/runner/controller、只读查询缓存结构及静态失败位置，均未能恢复具体比较值。可能是独立工具的精确次数预期或产品行为，当前无法区分；这只是待判定方向，不是根因结论。目标已求值，不符合“前置工具错误且目标未开始”的一次更正条件；没有改脚本后重跑，也未通过第二次B/新诊断来补证。需总控裁定在保留首次失败前提下的最小断言取证范围，之后才能判断产品是否需返修。

恢复finally实际完成：root卸载、DOM/监听/global/console恢复，订阅2/2、active0、备用退订0、denied0、consoleLeak=false、jsdomError0；这些是清理与监测部分证据，不补签恢复场景通过。无后续 Windows 或相邻回归。

静态阶段曾有一次新文件UTF8被Python默认GBK读取的UnicodeDecodeError，失败命令未写文件、未运行目标。保留了[首次静态五文件](../../tests/independent/desktop/evidence/r6-env/recovery-static-first/recovery-source.sha256)及[更正说明](../../tests/independent/desktop/evidence/r6-env/recovery-static-correction.json)，明确UTF8后完成预定rejected terminal/备用退订，再语法核对并冻结。该静态更正与动态AssertionError分开，不占用或伪称动态重试。

## 24项增量映射

完整原预期、历史来源及原缺口见 [R5报告的24项映射](phase-4-c12-r5-public-windows-report.md#原24项完整映射)；本表只记录本次增量。矩阵120 ID/12列/原预期不变，A64 passed、C20/D12 not_run；B继续0 passed、1 failed、19 blocked、4 not_run。UI-02的failed保留未关闭历史状态，不将本轮尚未归因的恢复断言升级为新产品缺陷。

| ID | 整项状态 | 本轮增量 | 仍缺 |
| --- | --- | --- | --- |
| P4B-SEC-01 | blocked | 未执行本项后续；沿用原证据。 | 生产 preferences逻辑有证据；实际EXE renderer Node isolation未执行。 |
| P4B-SEC-02 | blocked | 未执行本项后续；沿用原证据。 | 未在真实页面触发 inline/data/javascript、导航/new-window和外链。 |
| P4B-SEC-03 | blocked | 未执行本项后续；沿用原证据。 | main preload契约部分通过；未执行companion暴露对象与整个renderer域，保守保持blocked。 |
| P4B-SEC-04 | blocked | 未执行本项后续；沿用原证据。 | 未对注册handler执行未知channel/重复/全部无副作用断言或真实Electroninvoke。 |
| P4B-SEC-05 | blocked | 未执行本项后续；沿用原证据。 | 非Windows safeStorage；未检查真实renderer storage/内存、secret/crash dump或OS DPAPI。 |
| P4B-SEC-06 | blocked | 未执行本项后续；沿用原证据。 | HTTP为fake fetch，nonce为fake child；实际随机监听/origin/access到期/远程连接未运行。 |
| P4B-SEC-07 | blocked | 未执行本项后续；沿用原证据。 | 真实HTML/RTL/长文本编码布局与无脚本执行证据缺失。 |
| P4B-SEC-08 | blocked | 本次持续模块故障的局部DOM/console无原始错误、路径、堆栈；未替代真实设备。 | 未实测实际UI/request ID/preload/lazy故障或真实console/log/crash dump。 |
| P4B-SUP-01 | blocked | 未执行本项后续；沿用原证据。 | 虚拟adapter；真实PID/nonce、外来同PID和进程树隔离未执行。 |
| P4B-SUP-02 | blocked | 未执行本项后续；沿用原证据。 | 端口冲突、ready总超时、随机loopback和真实自有清理未覆盖，不能把health当ready。 |
| P4B-SUP-03 | blocked | 未执行本项后续；沿用原证据。 | 注入delay/child，不是Windows真实崩溃；启动前崩溃、健康循环与全部UI状态未覆盖。 |
| P4B-SUP-04 | blocked | 未执行本项后续；沿用原证据。 | 未执行双真实客户端/单实例EXE场景。 |
| P4B-SUP-05 | not_run | 未执行本项后续；沿用原证据。 | manual not_run；无owned资源仅表示没启动，不能推断cleanup通过。 |
| P4B-SUP-06 | blocked | 未执行本项后续；沿用原证据。 | 真实老化原生提示unverified、恢复后GET/只提交一次与实际UI缺失；整项从failed改blocked，原P0风险不变。 |
| P4B-UI-01 | blocked | B实际贡献与Host交集接线已运行；未执行其他交集组合。 | 实际导航/preload未运行；没有创建真实第二产品模块。 |
| P4B-UI-02 | failed | 冷入口4/4、安全/来源/清理通过；恢复场景1失败且归因未核实。 | 显式重试、持续失败/无循环、健康/settings切换、并发离开、状态/会话保持、render恢复及Windows真实chunk/session。 |
| P4B-UI-03 | blocked | 未执行本项后续；沿用原证据。 | 未取得失败定位或CI drift独立证据。 |
| P4B-UI-04 | blocked | 恢复使用真实compileRegistry创建两虚拟模块；未执行冲突/严格对象余项。 | UI-04完整独立结构/strict贡献及启动验证映射仍未补足；本轮没有确认新产品P1，不能由路径或冷入口通过直接passed。 |
| P4B-CMP-01 | blocked | 未执行本项后续；沿用原证据。 | 实际单毛毛/Agent入口、contribution主形态和完整子状态流未运行。 |
| P4B-CMP-02 | blocked | 未执行本项后续；沿用原证据。 | 虚拟ready-to-show retention不等于首次close提示；真实设备not_run子项保持。 |
| P4B-CMP-03 | blocked | 未执行本项后续；沿用原证据。 | 不以mock app.quit或E2E timer当生产关闭策略证明。 |
| P4B-CMP-04 | not_run | 未执行本项后续；沿用原证据。 | manual not_run；E2E抑制启动项不等于OS合同通过。 |
| P4B-CMP-05 | not_run | 未执行本项后续；沿用原证据。 | 实际位置夹取/重启/多屏/全屏/键盘/隐私UI与全部人工设备条件未执行，整项manual not_run保持。 |
| P4B-CMP-06 | not_run | 未执行本项后续；沿用原证据。 | manual not_run；真实对比度/焦点/reduced motion/颜色语义未测试。 |

## 资源边界、交付和停止

两轮 root 与登记worker通过创建句柄、固定Node启动入口及实时父子journal管理。B为32404/35656，恢复13964/31692，controller均记录已退出，没有强制终止。随后四个PID逐项返回NoProcessFoundForGivenId；[resource-postcheck.json](../../tests/independent/desktop/evidence/r6-env/resource-postcheck.json)只确认这四个登记PID。B额外“live”身份采样实际上发生退出后，未取得进程exe/startTime，不能补签已获取；worker自身退出码及完整历史后代/全系统枚举仍unverified，未复制父exit或按名称kill。

新cache两个results.json只读检查并各自保存首次副本，重读control后核对专属绝对路径/祖先及子项无reparse，只删除`evidence/r6-env/cache`的2个缓存文件，见[cache-cleanup.json](../../tests/independent/desktop/evidence/r6-env/cache-cleanup.json)。没有外部Windows虚拟根、个人AppData、数据库/端口/产品进程需清理，没有系统注销/重启/主题/启动项操作或要求用户点击。

最终可复算输入、矩阵/追加文档约束见[end-audit.json](../../tests/independent/desktop/evidence/r6-env/end-audit.json)；交付文件清单见[delivery.sha256](../../tests/independent/desktop/evidence/r6-env/delivery.sha256)，清单普通SHA及逐项复算结果见[delivery-verification.json](../../tests/independent/desktop/evidence/r6-env/delivery-verification.json)，避免报告与清单自引用。原R5、冷B与恢复首次材料均不覆盖。终点679项为675保持+4授权共享文档变化，0越界/缺失；旧R5源码10/首次6、本轮冷源码9/恢复源码5与首次9/7全部匹配。原主报告/人工清单各追加1034bytes，prefix保持，120矩阵行及B外字节保持；63项交付逐文件复算通过，staged=0、diff-check exit0。

本轮停止于 **blocked / finished，等待总控review**。已取得冷入口新通过证据，尚未取得完整恢复证据；下一步需要的是有边界的断言定位裁定，不是重复P/A/D16、延长预算或重跑已通过B。LAZY-001/UI-02/P4-B未关闭，不开始P4-C/D。
