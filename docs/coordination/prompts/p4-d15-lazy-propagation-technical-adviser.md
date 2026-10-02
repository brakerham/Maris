# P4-D15：异常传播链有限诊断

## 唯一角色与目标

你是既有技术顾问，唯一负责D15。不是重新执行D14，也不是产品实现或独立验收。用户已交C12-R4-R1：factory命中1次，#/daily，5秒无alert，Shell/nav/Agent存在，根因仍unverified。诊断错误停在import、实际loader、Router状态还是DOM提交哪一层；分清产品与测试环境因素。

按AGENTS读取README、project-coordination、coordination/README、最新control、自身technical-adviser和本任务。再读总控核对`docs/p4-c12-r4-r1-propagation-coordinator-review.md`、R4/R4-R1报告和原始观察/测试/配置、R5任务/运行说明、实际main/module-routes/Shell/registry/contribution及开发lazy测试。读取`docs/coordination/snapshots/p4-d15-start.sha256`并逐项复算；staged=0，登记接单/检查点。

不要预设Vitest、React Router、StrictMode或产品是根因。旧首次失败保留；延长等待、另一条throw或只看Shell存在都不能解决归因。

## 文件与环境边界

- 新文档：`docs/phase-4-d15-lazy-propagation-advice.md`。
- 自己的`docs/coordination/agents/technical-adviser.md`。
- 新诊断源码/脱敏记录仅`docs/coordination/diagnostics/p4-d15/**`。可含专用Vitest配置、独立探针文件与结果/清单，不放进tests/independent或开发测试。
- 自有临时cache只在上述新目录的`temp/`；验证后可清理，先核对解析绝对路径位于该专属根且无reparse。保留探针源码及首次结果，不删除失败证据。

产品、旧独立测试/证据/报告/矩阵、开发测试、依赖/lock/生成物、Forge/package/迁移/冻结/control/overview/snapshot和其他角色禁止修改。其他角色停止，技术顾问不调用其他智能体或创建后续Prompt/接口冻结。

复用R5普通依赖及固定工具：`C:\MarisLazyR5\R5-20261002-222300/workspace/node_modules`与同任务已有Node24.21.0/Vitest5.0.2，实际版本先只读核对。外部R5所有源码/依赖/包/profile/evidence只读。配置别名指向同一React/React DOM/Router；不要install/download/build/package，不修改PATH/代理/TUN/系统时钟/安全设置。

## 先静态核对

沿真实生产路径逐层标注入口、Promise、catch、路由状态、组件边界与Outlet。对照R4-R1实际mock/error factory、Host交集、global/DOM/act设置、StrictMode、生命周期/路由dispose、配置模块解析。尤其区分factory执行与调用方Promise已reject；记录之前缺失的证据。

可只读安装的Vitest/Vite/Router/React实现查传播机制；需要外部资料时仅官方文档/对应源代码，写清安装版本与资料是否一致。源码推断与实际探针分列，不把包装错误或transition存在写成根因。

## 最多三项一次性诊断

每项独立新文件/隔离Vitest worker，单项观察上限5秒、测试上限10秒，整个诊断会话上限60秒；使用实际时限及进程退出，不靠总进程数量阈值。静态已足够可少做，不为用满预算增加运行。运行前冻结探针源码/清单与预期分流，每项实际运行一次，首次stdout/stderr/exit保留。

1. **P1直接import终态**：仍以原DailyFinancePage模块mock factory抛固定虚拟错误；直接动态import相同源模块，观察factory进入、import resolve/reject/仍pending和安全错误类型。没有Router或UI。不能把另一条Promise.reject代替模块导入，也不能预先导入目标导致缓存污染。
2. **P2实际内置loader终态**：导入生产createModuleRoutes，用真实compileRegistry/daily contribution、默认内置loader，不传替代page loader；调用真实返回route.loader，记录enter→resolve/reject/pending，以及是否变成desktop_module_unavailable。没有替代实现/新catch改变原语义，观察层可以捕获结果并记录。
3. **P3生产入口路由→DOM**：使用与R4-R1一致的虚拟bridge、jsdom/global与模块mock，启动真实main。允许对实际react-router导出的createHashRouter作完全转发的观察包装：不改入参/route/errorElement、不提供另一套Router、不改返回对象，只保存真实对象并订阅其状态。真实main仍只拿原函数结果。记录router初始化/导航阶段、matches/错误槽的安全摘要、订阅/销毁、alert与内容状态的时间顺序；根据P1/P2定位是否有实际loader终态与当前route错误发布。不要通过额外navigate/revalidate/刷新改变首次启动现场。

P3若需要额外精确loader观察，可在**专用观察包装**中转发原loader并原样返回原Promise，旁路监听其终态；不得把它改成另一条reject、吞错、重新构造Promise或替换route对象来达成结果。必须记录包装方式/局限并说明是否改变时序。若做不到透明观察，保留unknown而不改产品增加调试hook。

Router错误只记录数量、目标route是否匹配、固定安全code匹配布尔和时刻；不序列化Error对象/stack/原路径或URL。DOM只记录已知提示/页面状态布尔，不导出完整正文。factory和Promise的关联以本探针隔离实例和时刻确认，不能拿P1的错误当P3的错误已传播。

生产root在finally卸载，观察订阅归零、DOM/global恢复、worker退出。异常日志用安全分类保留，不静默丢弃；遇未知所有权、无法收口或泄密停止。目标前无副作用配置/语法错误可一次定向更正，原错误保留；目标已执行的结果不能修改后重跑洗掉。不提高时限、不建立第4项探针。

这些是技术诊断，不是测试方独立通过统计。不要重跑旧R3/R4/R4-R1、开发八项/完整132或执行原24矩阵，不启动Electron/Maris/Python sidecar/Windows产品、Docker/OpenClaw/微信/provider，不要求用户点窗口。

## 输出与停止

文档用因果链表给出每层实际结果/证据/unknown，解释为什么执行方可控loader测试通过与真实入口故障失败不矛盾；假设要有支持/反证，不确定就写最小缺失条件。

必须选择有证据的后续范围：若测试模块mock/环境未把真实拒绝送入loader，建议最小测试接线修正及如何保留四条原断言；若loader/Router/DOM真实产品故障，给具体位置、影响/严重性建议、窄修复及原行为不变回归；若仍unknown，列唯一下一观察问题与本轮排除范围，不能建议再盲目等或重打包。

提交review/finished（仍有真实环境阻塞则blocked/finished），附新源码/证据逐文件摘要、输入不变核对、实际运行次数/首次失败/资源状态与限制。只更新自己的角色日志/执行快照，长操作前记检查点、有控制时十分钟心跳；外部操作前重读control。

不得宣布LAZY-001/UI-02/P4-B complete，不创建D15-R1、IF、执行或测试任务，不执行Git写操作。交付后停止，由总控决定后续。
