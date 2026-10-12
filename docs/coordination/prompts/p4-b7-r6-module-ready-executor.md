# P4-B7-R6-MODULE-READY：后台就绪后的模块与页面同步

## 唯一负责人和目标

你是既有执行智能体，唯一负责本任务。先用明确控制的启动顺序验证真实DesktopApp是否会停留在首次空模块列表；复现后在同一任务完成最小修复、开发验证和新包/EXE检查。总控只确认源码存在缺少后续模块同步的路径，R7 W1现场根因仍unverified，不能把假设写成独立确认的产品缺陷。

R7恢复5组、独立结构8项和开发兼容10项已经核对，不重复测试方节点。LAZY-001/UI-02/P4-B仍未关闭。当前是已有Shell接线维护；不进入驾驶舱、账本图表或聊天界面设计。

## 必读、起点和文件边界

按AGENTS依次读取README、project-coordination、coordination/README、最新control、本人executor、本卡，再读：

- [总控裁定](../../p4-c12-r7-recovery-windows-coordinator-review.md)、[R7报告](../../testing/phase-4-c12-r7-recovery-windows-report.md)及Windows首次result/journal/runner，只读参考、不执行。
- IF-003/004/005、原UI-01/UI-02及[R5执行合同](p4-b7-r5-lazy-executor.md)。R5普通工具/产物来源、局部错误隔离及安全要求继续适用，本文替换任务范围与验证预算。
- [新固定起点](../snapshots/p4-b7-r6-module-ready-start.sha256)：仓库根、原字节、UTF8无BOM、按完整POSIX相对路径排序、`path<TAB>sha256<LF>`。接单前复算、staged=0，登记快照和下一检查点。

仓库允许写入仅5个文件：

1. `apps/desktop/src/renderer/module-routes.tsx`：模块读取/更新及router稳定性所需最小修复。
2. 新`apps/desktop/tests/unit/module-readiness.test.tsx`：执行方实际组件/时序回归。
3. 新`docs/b7-r6-module-ready-running.md`。
4. 新`apps/desktop/b7-r6-module-ready-source.sha256`。
5. 自己的`docs/coordination/agents/executor.md`。

其余产品、Shell/styles/财务页面、main/preload/IPC、Host/Python、registry、已有开发测试、独立测试与报告/矩阵、依赖/lock/Forge/staging/package、control/overview/其他角色只读。需要超出范围或新接口先交总控，不能顺手修改。允许任务专属C盘根内自有driver/evidence/profile/cache，但须冻结driver源码和摘要；不改旧C盘现场。

## 先证明再修复

用真实DesktopApp、compileRegistry、React Router和Shell；虚拟bridge仅控制已有modules/runtime边界，可信页面loader为外围虚拟端口。主回归先在原代码运行并保存首次红灯：

1. 挂载时runtime尚未完成连接，首次modules读取明确返回空列表；必须有这一步已发生的证据。
2. 显式完成后台连接/模块取回，发布与实际composition一致的就绪通知，后续modules应提供合法的启用模块。
3. 不点击、刷新、重新挂载或主动调用runtime.recover，真实模块导航/页面应出现，Shell及Agent存在。断言记录expected/actual，不能只证明后端接口有模块。

不得用随机sleep碰竞态、在mock里直接改产品state、替换Router或删除StrictMode制造红绿。至少覆盖StrictMode与普通挂载；页面未出现时保留模块调用次数、每次返回类别、runtime通知顺序、hash枚举和DOM存在布尔。若原实现已通过该精确顺序，停止猜测性返修，报告证据。

## 修复约束与开发覆盖

保持现有窄bridge和runtime语义，由实现者选择最小renderer内实现。接受以下行为，不冻结具体API技巧：

- 初次空列表不能永久锁住界面；后台随后发布有效模块后，界面自动同步。后台已就绪再挂载也正常；合法的就绪后空列表仍为空，不凭空注入daily_finance。
- composition在认证完成/模块赋值附近可能发布字段相同的runtime快照。**不能仅用state/authenticated字段去重，漏掉最终模块更新。** 模拟先online/authenticated但列表尚空、随后相同字段通知且列表有效。
- 订阅与初始快照/模块读取间不丢通知；并发读取有有限合并/代次保护。旧请求晚到不能覆盖较新状态，较旧getSnapshot回包不能覆盖已接收的更新订阅值；卸载或StrictMode清理后的回包不写入状态；读取拒绝安全处理，不泄漏raw error或产生unhandled rejection。
- 内容相同的新列表或重复runtime通知不重建当前router、不重新调用页面loader、不自动重试失败页面。合并通知可以在当前请求完成后按需再读一次，不允许定时轮询、无事件循环重试或无界并发。
- runtime离线观察本身不破坏已展示模块/Shell状态；同一有效模块集合下主题、隐私、当前健康/设置路由和订阅保持。真正模块交集变化仍按原registry合同更新；禁用、不兼容或未知模块不能加载，不改变Profile/路径/权限规则。
- 保留局部lazy/render错误与显式重试、在途去重、旧结果不能覆盖新路由、无自动页面reload/owner重建/revoke/outbox/provider/财务写入。

新执行方测试覆盖上述可控时序、相同集合去重、旧回包、拒绝、卸载、空/禁用交集。可在新测试中组合真实DesktopCompositionRoot与虚拟supervisor/owner/Host，验证实际发布顺序；不要求另开诊断任务，不运行或修改独立测试。

允许正常开发调试和有理由的定向复跑，保留修复前红灯及各次失败。新文件加现有lazy/Shell/composition必要定向、TypeScript、lint通过后，运行一次完整desktop开发回归（原132项加新增）。旧断言保持；若新增事件读取导致原合同断言冲突，先核对真实触发，不得改旧断言来过关。不重复Python/P0～P3/Host或旧独立集合。

## 普通隔离环境与唯一新包

固定只读来源`C:/MarisLazyR5/R5-20261002-222300`，按R7 start-audit绑定389构建源码、140产物、67Python资源、版本和依赖元数据。仓库当前输入以新快照为准；旧source清单仍用于旧包，不拿协调文档差异当产品漂移。

新根`C:/MarisModulesR6/R6-<时间戳>`。创建、复制、清理前验证解析绝对边界及无reparse；普通物化R5工具/依赖/源码，旧根只读，不用junction。同步新仓库受验源及本次授权修改，冻结新构建输入；不重新安装/下载/audit，不改永久PATH/代理/安全软件。

继续固定Node24.21.0、pnpm12.7.0、Electron44.4.5、Playwright1.63.0及已验证Python；lock SHA `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`，官方Electron ZIP SHA `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d`。用已通过的任务局部pnpm解析和LOCALZIP，不重造R0/Job框架。

全部开发门禁通过后，package最多1次；失败保存原记录后停止，不能第二次覆盖。新asar/renderer来源必须绑定修复，检查原7项静态门禁、production fuses、67资源、完整out清单与污染/staging零残留。不要求EXE摘要必随业务源码改变，必须证明新asar绑定。

## 唯一最终EXE验证和失败时的证据

静态通过后仅启动新EXE1次，硬上限120秒，Node直接spawn(shell:false)，Playwright仅动态loopback CDP附加；禁用Electron launcher/app.asar启动/PID提升。新虚拟profile、owner、数据库和专属OS环境；不读个人AppData或真实密钥，不修改OS启动项。不启动旧R5/R7产品。

沿用R5执行方19门禁，增加**真实页面门禁**：初始managed在线且认证、启用daily_finance及canonical Profile、`#daily-title`存在且可见、Shell导航及Agent；一次授权recover后后端和页面仍正确、主题/隐私/路由要求保持。不得只凭modules.list通过代替页面。窗口与毛毛交互、renderer隔离、秘密隔离及最终进程/监听/窗口收口保留。

实际模块列表与runtime取样仅保留合法模块ID/版本类别和布尔，不输出token或路径。页面每项独立采集exists/count/visible/hash枚举/readyState；就绪后UI观察仍最多5秒。超时前后在同次运行有界取得最后标量，分清0/false与unknown；若采样异常保存安全错误类型/阶段/耗时，不输出raw message/stack/DOM。journal的event名与details的stage分开，避免覆盖首错事件名。失败后不再点击/recover或改变产品状态，只做有界只读取证与身份清理，不重启。

退出采用冻结的R5 E2E退出链路，或在本轮虚拟profile设closePolicy=quit后发送普通WM_CLOSE；两者执行前选定并记录，不能让退出timer抢在页面断言前结束程序。自然退出必须exit0并证明owned资源为0；失败后的强制清理单列，不能算正常退出通过。所有原始首次材料保留，新driver在执行前静态校验/freeze；纯工具错误发生在产品开始前时可定向修正一次并留痕，产品实际开始后的失败不重跑。

## 交付与停止

记录接单、首次红灯、修复、开发门禁、package/EXE、资源收口及最终心跳；5分钟以上操作前记录下一检查点，有控制时至少10分钟刷新。不把中断时间计为持续工作。

运行说明须给出可控复现是否成立、修复前后数据流、代码与开发节点映射、全部失败/警告、不同证据层级、新包及EXE的后端/页面独立结果。W1旧现场原因仍不可回填；执行方只交review/finished或blocked/finished，不关闭独立缺陷/矩阵。

最终source清单以新起点更新授权文件摘要、加入新测试和运行说明，排除清单自身；停止修改后复算，自己的角色日志差异单列。保存旧R5、R7首次证据和旧环境的不变性，产物及虚拟profile留外部，仓库文档脱敏。清理只限验证过的任务自有临时路径，不删保留现场。

新的P0/P1、越界需求、接口变化、泄密、失控弹窗、所有权不明或无法收口立即停止扩大；外部同一问题连续两检查点无新输出停止等待。不得自行启动测试方/顾问、下一任务、Docker、OpenClaw、微信/V002或真实provider。不得Git写操作。正式前端阶段仍等待用户的参考图与模型策略复核。
