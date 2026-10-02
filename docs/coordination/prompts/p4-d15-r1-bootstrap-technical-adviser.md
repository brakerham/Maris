# P4-D15-R1：生产入口观察通道的前置阶段取证

## 角色与唯一问题

你是既有技术顾问，唯一负责D15-R1。原D15已停止在`blocked / finished`，本任务不是重复三项诊断，也不是产品返修或独立验收。

唯一问题：**同一隔离worker是否取得真实React Router导出并进入main；若没有，最后哪个持久阶段完成、下一步等待在哪个调用？** 分别记录main导入Promise终态与React act返回，不把两个await的整体超时当成同一原因。

按AGENTS读取README、project-coordination、coordination/README、最新control、自身角色日志和本任务，再读[总控裁定](../../p4-d15-bootstrap-coordinator-review.md)、原D15报告/冻结源码/首次结果，以及真实main、module-routes、Shell、contribution。逐项复算[新固定起点](../snapshots/p4-d15-r1-start.sha256)，staged=0，再登记接单/执行快照。外部操作前重读control；原任务停止、不重复已完成微信V002。

## 可写与不可写范围

- 新报告：`docs/phase-4-d15-r1-bootstrap-advice.md`。
- 自己的状态：`docs/coordination/agents/technical-adviser.md`。
- 新探针、配置、controller、源码清单及脱敏首次证据：仅`docs/coordination/diagnostics/p4-d15-r1/**`。attempt-0和必要的attempt-1分目录保存，旧材料不覆盖。
- 本任务专属缓存仅上述目录`temp/`；核对绝对边界、无reparse后可清理缓存，不能清理源码/首次证据。

产品、开发及独立测试、旧D15目录/报告/清单、测试报告/矩阵、依赖/lock/生成物、包、Forge、迁移、冻结、control/overview/snapshot和其他角色只读。不创建后续Prompt/接口冻结，不调度其他角色。唯一允许发生的旧顾问角色摘要变化是本人接单与交付日志，另列授权变化，不声称原D15 delivery整体仍与旧顾问日志匹配。

只读复用`C:\MarisLazyR5\R5-20261002-222300`既有固定Node24.21.0与workspace/node_modules。安装的Vitest5.0.2、React19.3.0、React DOM19.3.0、React Router8.4.0、jsdom30.1.1及对应元数据先核对。原R5源码/依赖/包/profile/evidence只读。不得install/download、修改PATH/代理/TUN/时钟/安全软件或开启任何服务。

## 先修正证据通道，再执行目标

先静态追踪Vitest的setup、hoisted mock、importOriginal、body和真实main的导入依赖。不要预设mock工厂在body之前执行，不要预设框架死锁。不重跑P1/P2、旧独立节点或开发回归，不为本任务另建故障类型。

使用专属`setupFiles`，仅通过原生文件能力建立阶段journal，不能先导入React、Router、产品入口或目标页面。最迟在测试模块初始化前同步写入`worker_start`，保存PID/parentPID、固定阶段码、顺序号、相对耗时；controller在启动前先建立自己的root/时限记录。setup的记录器和观察模块不能相互动态导入形成新循环。

每条阶段记录发生时就追加落盘，不能只写内存、stdout缓存或finally文件。journal独占创建、不覆盖；每个关键await有enter/terminal，写失败归类观察工具问题并停止。完整最终JSON只是补充，硬终止后仍可读取已追加的journal。记录器在mock工厂和测试body前可用；不得依赖body才设置的record函数。

至少保存以下阶段；未到达的阶段不得补造：

| 层 | 前置与终态记录 |
| --- | --- |
| worker/setup | worker_start、journal_ready |
| 测试模块初始化 | hoisted_ready或等价的可核查初始化事件 |
| Router观察工厂 | factory_enter、actual_import_enter、actual_import_resolved/rejected；resolved后只记录createHashRouter类型是否为function |
| 测试正文 | body_enter、virtual_dom_bridge_ready |
| main及React | act_enter、main_import_enter、main_import_resolved/rejected、act_return/rejected，各自独立保存 |
| 收口 | root是否建立/卸载、观察订阅取消、DOM/global恢复、worker与root实际退出；无证据的项目保持unknown |

保留原DailyFinancePage mock、实际main、默认loader、虚拟bridge与相同jsdom/global、StrictMode入口。Router观察必须完全转发真实导出，保持原参数、原route/errorElement、原返回Router。可为消除**已证实的观察接线问题**更改新探针的包装方式，但必须写出变更与原语义一致性证明；不能拿替代Router、替代loader或另一条reject制造预期结果。

main导入Promise可以旁路监听终态，但不能替换或吞错；act仍围绕真实入口启动，分别记录两者结束。已知虚拟factory和safe code只用布尔/安全类型分类，不导出Error/stack、整个模块、URL/路径、完整DOM、token/nonce或真实数据。不要额外navigate/revalidate、整页刷新、recover或财务写入。

本任务只定位bootstrap和入口等待位置，不扩展DOM/Router状态完整验收或恢复流程。main完成后安全收口即可；若act或import仍pending，保留阶段记录并按原硬限结束。不能为得到错误提示而延长时限。

## 有限预算及修正边界

运行前冻结源码、配置、controller和预期阶段清单。真实main启动总预算**1次**，进程上限仍**15秒**（含收集），测试上限**10秒**；无需进入5秒DOM观察。有限会话上限**60秒**，不用Windows Job或总进程数阈值。静态语法检查不是main执行，不用collect-only替代实际阶段证据。

允许一次前置观察工具修正，条件必须全部成立：持久回执能证明失败严格发生在`main_import_enter`之前；固定输入不变；首次源码/日志/退出已保存；本次自有root/worker已退出；修正只涉及本任务新观察源码/配置/controller。修正后重新冻结到attempt-1，最多第二个隔离worker，不第三次尝试、不新任务循环。此预算不会授权重复已启动的main。

如果main已开始、缺失阶段无法证明是否开始、已经使用修正预算、产品相关异常、未知进程所有权、泄密或无法收口，立即停止。不能把15秒超时自动称为产品/框架故障，不能修改已执行目标后重跑覆盖首次失败。

controller记录自己创建的root身份，在setup journal取得worker身份/parentPID；保留分开的stdout/stderr、真实exit、timeout和强制终止状态。硬限只定向终止自己创建的已知进程树，不按进程名广泛结束Node。权限失败后的空集合不得当作零残留；能核对root/已登记worker及固定Node元数据时明确验证范围，无法证明正常finally则保持unknown。

## 交付、归因与停止

报告按持久阶段顺序给出实际证据、最后完成阶段、未完成调用和范围限制。若确定观察包装/解析接线问题，给出最小观察或测试基础设施修正建议及原四条业务断言如何保持；若取得产品链证据，只给精确位置和窄后续建议，不修改产品。根因仍unknown时必须收窄到一个具体缺失事件或调用，不能建议再等更久、再打包或盲目重试。

原四条要求保持：安全错误提示、Shell存在、模块导航存在、统一Agent入口存在。后续显式有限重试、持续失败不循环、健康页面切换与状态保持也未被本任务替代。诊断成功只证明观察问题定位，不计入独立通过，不关闭LAZY-001/UI-02/P4-B。

交付新报告、冻结源码、每次原始journal/双流/实际退出、逐文件摘要、固定输入不变核对及资源限制。只有本人角色日志可更新，长操作前记检查点、有效输出时更新心跳。解决本任务问题则`review / finished`；仍无法定位则`blocked / finished`，完整列实际执行次数和修正预算。

不启动Electron/Maris/辅助fixture/EXE、Python Host/sidecar、Docker/PG、OpenClaw/微信/provider，不运行测试矩阵、独立恢复或Windows，不build/package，不要求用户点击窗口，不执行Git写操作，不创建D15-R2或后续角色任务。交付后停止，由总控核对与裁定。
