# P4-B7-R6-MODULE-READY 执行方运行说明

任务状态：review / finished；本文记录执行方开发、新包及一次新EXE验证，不是独立验收。固定起点812项已全部匹配，原字节清单SHA-256为`019fd0033279e272c7b088e8097f864bdb78536d61f88933b1f8dc9c863102d6`。只改任务卡列出的5个仓库文件，无Git写操作。

## 可控复现与最小修复

实际DesktopCompositionRoot配虚拟supervisor/owner/Host，实际DesktopApp、compileRegistry、Router和Shell；页面loader仅为虚拟外围端口。初读明确为空，认证发布online/authenticated但模块尚空，再赋值模块并发布字段相同的通知。无点击、刷新、重新挂载或recover。

原产品red为0passed/2failed；JSON reporter未保留console标量。仅补安全JSONL观察后red2仍0passed/2failed：普通读取1次、StrictMode读取2次，后台均enabled=true、两次online/authenticated通知；loader均0，hash=#/，Shell/导航/Agent存在，daily导航/页面false。原始两轮不覆盖，不将未捕获数据写成已观察。

修复先建立订阅，再读取快照和列表；每次online且authenticated通知都可请求重读，同值通知不按字段去重。单飞合并、代次检查、effect active保护防止过期提交；旧getSnapshot不能覆盖订阅新值；拒绝只保留安全界面，不记录raw error。无轮询或无事件重试。按实际贡献对象和顺序稳定有效交集，相同交集保持Router和失败页，不重复加载或自动retry；离线仅更新runtime。

真正交集变化重新建立路由及RouterProvider；index绑定该路由自己的贡献列表，避免新context与旧router错配；已移除的路径在Shell内部展示空页。主题、隐私保存在DesktopApp，同集合健康/设置路由与订阅保持。未扩展IPC、模块权限或Profile规则。

修复后精确顺序：普通modules3/loader1；StrictMode modules4/loader2（初始Navigate在开发Strict effect下执行两次）。两者最终hash=#/daily、模块页和导航/Shell/Agent均true。同集合更新及失败页不自动重试有普通/Strict分别断言，不能把初次Strict导航次数写成每次通知重复加载。

## 开发合同与节点映射（打包前）

| 预期 | 新开发节点/实现 | 结果与层级 |
| --- | --- | --- |
| 首次空→真实composition认证/模块通知→真实页面 | 主顺序普通/Strict 2项，DesktopApp订阅刷新 | 开发通过；后端和DOM分别记录 |
| 已就绪再挂载；合法就绪空列表 | 已就绪普通/Strict 2项及交集节点 | 开发通过 |
| 订阅与初始读取不丢通知；旧snapshot不覆盖 | 晚snapshot普通/Strict、同步getSnapshot通知、读取内通知 | 开发4项通过 |
| 并发有界、旧模块回包不提交 | 20通知合并、Strict旧effect、卸载成功/拒绝 | 开发4项通过；单effect最大并发1，20通知合计2读取 |
| 初始/后续拒绝不泄密、不无事件retry | 拒绝节点、每项cleanup safety | 开发通过；jsdomError/unhandled/console canary均0 |
| 同集合稳定主题/隐私/健康及设置路由/订阅；离线仅观察 | 真实双贡献虚拟页面、原Shell、稳定引用 | 开发通过；没有恢复/owner/outbox/provider/财务写入 |
| 同集合不自动重试失败模块 | 普通/Strict 2项；明确点击重试 | 开发通过，原lazy局部错误/在途/跨路由断言保留 |
| UI-01完整交集：缺失、禁用、不兼容、未知不能导航/预载 | 新交集变化/当前模块删除、原registry开发节点 | 开发通过；不改独立矩阵 |
| UI-02局部lazy/render错误、重试、Shell/其他路由/会话保持 | 原lazy8项+新同集合节点，未替换真实Router/Shell | 开发层证据；真实chunk故障、真实session故障和完整独立UI-02仍未闭环 |

定向directed 26passed/0failed/0skip；补充directed2 27passed/1failed/0skip：当前模块移除后daily导航false但旧dailyPage=true，Shell/Agent为true（不采用只读审查的Shell消失假设）。允许renderer内修复后directed3 28passed/0failed/0skip。TypeScript、lint两次均exit0；最终唯一全量desktop为16文件、150passed/0failed/0skip（原132+新18，不累计定向重复）。未运行独立测试、Python/P0-P3/Host全量或旧EXE。

## 普通环境与失败留存

新根`C:/MarisModulesR6/R6-20261013-002100`；旧R5只读普通来源`C:/MarisLazyR5/R5-20261002-222300`。已复制source812、冻结deps12443/实际12677、Electron dist73、tools3，无junction/reparse。固定lock、官方LOCALZIP、Node24.21.0、pnpm12.7.0、Electron44.4.5、Playwright1.63.0及既有Python；不安装、下载、重新audit或改永久环境。

所有开发原始输出位于新根`evidence/tests`，driver位于`evidence/tools`，每次运行前源码摘要位于对应`*-source.sha256`。red/red2和directed2失败永久保留。首次复制Robocopy /LOG参数在产品启动前修正一次；人工native exit16推断已由clarification作废，可靠观察仅外层exit1/原生>=8。JSON reporter安全观察补充属于开发测试记录调整，不改变产品。一次只读CIM沙箱拒绝、只读路径猜测/rg通配符错误不属于产品结果。

00:43附近外部同步/测试自动审批因额度未完成，操作未执行；07:54用户继续后原步骤运行。中断期间不计持续工作。Git只读查询可能出现ignore权限/LF→CRLF提示，逐文件原字节摘要为准。

## 新包与最终EXE

package **1/1**：2026-10-13 08:02:55.789—08:03:01.525+08，5736ms、exit0、stderr0。固定工具的真实Forge进程环境已记录。静态 **7/7**；production fuses前六项48/49/48/48/49/49；Python资源67/67、out140文件/386495405bytes、asar11文件，0链接/解包项，污染0、staging/transition残留0。

| 实际新产物或冻结输入 | SHA-256 |
| --- | --- |
| 构建输入813项清单 | `05677054bf73b1a40c60a844f7cad99cc2654bf638ea3798a2081d04212851b4` |
| Maris.exe | `4ef5bce604fc61fc2b815300edee8a29ab593083d308e849445c6c97235c5f1e` |
| app.asar | `5eb153002f4c48ce704f1d0f90b3bf441d5edf3799ea5fe4428f706aee7c69db` |
| 实际asar renderer index-aNesQSwa.js，410574bytes | `fe85f460874450cbfd65a511818be1d18032e94179ff9f6fa0aa8e0eb691b453` |
| 完整out140清单 | `ebb3521d71bb45d03b692dc0eacda52db540bd722e1aee414c9c025211a28694` |
| 启动前冻结final-exe-runner.mjs | `679580c6b209256746e2a0efef80004611edbea656c01badd1b8385d77bc604b` |

实际main导入module-routes，仓库/副本源码相同；asar renderer与构建输出逐字节相同，包含新的revision/instance/模块读取和订阅代码。沿用带来源区分的R5绑定，不对整个框架bundle做“没有reload字符串”的错误判断。静态来源证据与实际行为分开。

新EXE **1/1，22/22门禁通过**（原R5执行方19项+初始真实页面、recover后真实页面、设置状态保持3项）。验证窗口2026-10-13 08:07:37.106—08:08:14.239+08、37133ms，直接Node spawn(shell:false)，Playwright仅loopback CDP附加。新虚拟profile、owner和数据库，专属OS路径；没有真实个人数据或provider。

| 阶段 | 后台独立结果 | 真实页面独立结果 |
| --- | --- | --- |
| 初始就绪 | managed/online/authenticated=true、errorCode=null；唯一启用daily_finance、兼容major1、canonical Profile | daily/Shell/导航/Agent/daily导航均exists=true/count=1/visible=true；hash=#/daily、readyState=complete；采样7ms |
| recover前设置 | 没有额外recover | hash=#/settings、theme=dark、privacy=on；Shell/导航/Agent可见；daily count=0（设置页的正确结果）；采样4ms |
| 唯一recover后 | recoverCalls=1；再次managed/online/认证、同canonical模块 | 设置hash/theme/privacy及Shell/导航/Agent保持；采样7ms |
| 切回日常页 | 后台结果与上项分别保存 | daily/Shell/导航/Agent均可见，hash=#/daily，dark/on保持；采样2ms |

选择R5既有30000ms E2E正常退出链路，页面断言截止25000ms，每阶段UI观察≤5000ms。实际全部页面断言在启动后约21354ms内完成；没有timer抢先关闭页面。退出code0、signal=null、自然退出=true、timeout=false、forcedCleanup=false。最终owned进程0、监听0、窗口0，已观察的2个Python后代均退出；毛毛/openMain、双窗口、窄bridge、renderer隔离、owner/db、隐私和产物不变性均通过。

驱动启动前内部执行只读审查指出的4项观察问题（elapsed计算顺序、初始模块合法中间状态、有界IPC/页面读取、已观察安全失败立即停止）均在唯一启动前完成静态完善。event与details.stage分开，失败路径仅有界标量取证和身份清理；此实现路径本轮没有发生产品失败，不能声称验证了故障清理的实际触发效果。

旧R7 W1页面unknown的现场原因仍unverified；本次可控复现不能回填旧证据，LAZY-001/UI-02/P4-B不关闭。真实Windows chunk故障、真实session故障与完整独立设备验收未执行。

## 交付与资源

最终旧R5：source389、冻结deps12443/full12677、dist73、out140、evidence60、虚拟profile62全部前后匹配；旧R7外部64文件摘要`dddbfd72ffaa74aafec685518ea60d4508795e9660c915d700da6bf957b49367`前后匹配。812起点中810不变，仅允许的module-routes和executor日志变化；独立报告/矩阵/测试及其他产品文件不变。构建副本813清单固定，不用最终日志/运行说明后写变化回写旧构建输入。

最终[source清单](../apps/desktop/b7-r6-module-ready-source.sha256)为**814项**：812起点更新授权项，加新测试和本说明，排除清单自身；每行完整POSIX相对路径、TAB、原字节SHA-256、LF，UTF8无BOM，按路径ordinal排序。清单文件本身及5项交付摘要见新根`evidence/inputs/delivery-five.sha256`和`closeout.json`，避免在被摘要文档内嵌自身摘要造成循环。可在仓库根按每行路径读取原字节，逐项计算SHA256，再对清单原字节计算总摘要。

执行方日志已同步接单、红灯、开发失败、修复、门禁、包/EXE、收口及最终心跳；只读辅助任务经主执行整合，无辅助编辑或独立验收。没有启动测试智能体、技术顾问或后续任务，没有Git写操作；staged=0，原.claude/.pnpm-store未动。

临时目录只清理新根`evidence/tests/tmp`：删除前绝对边界/所有祖先与后代无reparse，110个临时文件，删除后不存在。新包、62文件虚拟profile、运行证据保留；项目未启动Docker/OpenClaw/微信/DeepSeek。当前无本任务活动产品、验证会话或待用户点击操作。

完整失败/警告边界：red与red2各2项、directed2的1项失败均保留，最终0failed/skip；两次工具编排JS模板解析错误发生于目标调用前，无执行；首次复制参数与exit推断纠正见前文。一次自动审批额度阻塞已恢复。只读路径/通配符探查失败不作产品缺陷。Git ignore权限及LF→CRLF提示保留，摘要按原字节。package.stderr为0；EXE console/pageerror/crash均0、Application/CodeIntegrity窗口事件0。EXE原生stderr100bytes包含动态CDP端点身份，internalPath/runtimeIdentity=true，敏感模式=false，仅留专属外部证据，不混入产品DOM或仓库日志。测试捕获console的安全断言只证明无canary，不宣称所有被捕获的React warning数量为0。

主要外部证据（均在`C:/MarisModulesR6/R6-20261013-002100/evidence`）：`tests/{red,red2,directed,directed2,directed3,full}.json`及各自exit/observations/source文件；`inputs/prepackage.json`、`static/result-v4.json`、`static/module-ready-source-binding.json`、`inputs/final-driver-freeze.json`、`final-exe/result.json`及`raw/driver-events.jsonl`、`inputs/final-immutable-audit.json`、`inputs/r7-boundary-final.json`、`inputs/temp-cleanup.json`、`inputs/closeout.json`。
