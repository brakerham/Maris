# P4-B7-R8-R1-LIFECYCLE：同包设置生命周期续验

唯一负责人：既有执行智能体。当前任务由头脑风暴总控冻结，交付状态最多review/finished，阻塞则blocked/finished。先读AGENTS、README、project-coordination、coordination/README、最新control、本人executor状态、本卡及[总控裁定](../../p4-b7-r8-settings-lifecycle-coordinator-review.md)。不创建新任务或自行进入独立验收。

## 目标与既有事实

R8设置修复及新包保留；217开发测试、TypeScript、lint、唯一package、7静态及8读取链检查已有证据，不重跑。原S1已启动但工具在页面取样前失败；原S2未启动。修复的目标是任务外身份时间转换和失败收口工具，然后对同一包取得S1保存/正常退出与S2原样重启恢复的完整执行方证据，不改产品。

先复算[本任务新起点](../snapshots/p4-b7-r8-r1-lifecycle-start.sha256)，所有条目匹配后登记接单。接单时核对历史12项交付；执行期间除本卡授权更新的executor.md外，其余11项保持原字节。历史[R8 source](../../../apps/desktop/b7-r8-settings-source.sha256)清单自身不改，executor新摘要只进入本次终点清单。历史source覆盖的5份总控协调文档已经更新，以本次新起点为准；它们不属于上述12项交付，不能把授权协调变化当产品漂移。

## 固定只读输入与路径边界

原根：`C:/MarisSettingsR8/R8-20261019-103900`。从其 `evidence/closeout.json` 及各绑定清单复核构建1365、out140、resources67、原工具14、原生命周期63、原证据108；清单摘要见总控裁定。旧依赖完整审计引用已绑定final-audit，核对实际使用Node、Playwright、Python、lock及关键入口摘要，不重新安装。启动前、终点复算固定产物和受影响输入；无需每个观察命令都重扫整棵依赖。

唯一产品路径：`C:/MarisSettingsR8/R8-20261019-103900/workspace/apps/desktop/out/Maris-win32-x64/Maris.exe`。

| 固定项 | SHA-256 |
| --- | --- |
| Maris.exe | `c80d27c8e31fa60df91065a770e669a553260cf8f883c55a0a7f83f8a430736b` |
| resources/app.asar | `05cdad34ba60b59773eebe671156c96260e69354568b9942da59058641f9c0b2` |
| workspace lock | `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |

新外部根仅为 `C:/MarisSettingsR8/R8-R1-<时间戳>`，创建前检查绝对边界、无既有目录和reparse。新driver、fixture、证据、缓存、隔离profile和AppData只写新根。**读取旧exe/tools/python与写新profile是两个独立allowlist**，不能把它们都硬编码为同一taskRoot，也不能放宽为任意C盘路径。旧根及旧profile全只读，旧driver/result不覆盖；不复制旧owner/profile作为S1输入。

仓库只允许三条交付路径：

1. 新增 `docs/b7-r8-r1-lifecycle-running.md`。
2. 新增 `apps/desktop/b7-r8-r1-lifecycle-source.sha256`。
3. 更新本人 `docs/coordination/agents/executor.md`。

产品、开发/独立测试、依赖/lock、Forge、打包脚本、控制/矩阵/其他角色文件均只读。无Git写权限。禁止build/package、下载/安装、更换运行时、Docker、微信/OpenClaw、真实provider及个人数据操作。不得重跑旧H1/W1/W2、旧冷入口/恢复、旧模块测试。Tester累计产品2/8、helper3/6保持冻结。

## 一次完整修复工具链

在新根复制必要原driver，保留对原件的diff与摘要。修复范围限于以下工具链，不改S1/S2的原产品期望：

1. **统一身份表示。** CIM创建时间在PowerShell端先转UTC ticks，再以十进制字符串输出 `createdUtcTicks`；root、known集合、后代、WM_CLOSE和cleanup共用同一规范化/比较逻辑。ticks不能经过JS Number、毫秒Date或本地化字符串。不得再对已为DateTime的字段使用字符串Parse；显示用ISO不作为另一套身份真值。CIM/Process对象可能存在精度差异，目标前实测，保留同源精度而非扩大匹配窗口。PID、固定exe、parent、marker/profile仍共同绑定；排除PID复用或路径/创建时间变化。
2. **观察与清理解耦。** 窗口/CDP/日志失败要记录具体安全阶段、真实status/signal/error类型，不能只留下哈希或统一unknown；不得把查询拒绝/异常映射为空集合。进程身份核心及定向清理无需成功枚举窗口。清理前重核可执行文件、PID及创建身份，不能按名称广泛结束进程、忽略身份不匹配或杀掉其他聊天/应用。
3. **失败路径有界。** 修复原finally清理失败仍clearTimeout的路径；用明确的控制器/runner收口状态保证保护持续到自然退出和资源核验完成，或进入失败收口。正式场景墙钟硬上限120秒，预留末段最多15秒用于停止和记录；每个OS/CDP调用受剩余预算限制，不能因spawnSync或未完成promise无限等待。无后续模型交互/审批才能继续的清理依赖；所需查询/终止权限在普通Node自检前置确认。不能用强制退出或超时作为正常关闭通过。
4. **失败落盘。** firstFailure只写首次，后续cleanupFailure单列；每阶段enter/terminal即时写，比较ID唯一且记录expected/actual。保留root真实exit/signal、子进程未知码、observer错误及最后已知资源，控制器异常也写出result。原失败不覆盖；不要把工具的exit0代替产品exit0。

普通工具开发最多3轮/30分钟，保留每轮输入/失败和受影响复验；这些是可修正的开发自检，不是每错一次就创建新完整返修卡。禁止把正式产品启动伪装为工具自检。全部通过后冻结本次driver并停止编辑，再进入S1。

目标前必做且只用虚拟值/本任务固定Node fixture：

- 原7位小数UTC样本、等价+08偏移、typed DateTime/DateTimeOffset、JSON往返均保持同一ticks；1 tick差异、缺失/非法值和不同身份必须拒绝。不输出其他进程命令行或秘密。
- 实际PowerShell版本与原生CIM→JSON→Node→JSON→PowerShell链往返；同一自有Node进程的根/known比较均真，篡改创建时间/path/PID/parent能拒绝，路径斜杠规范化不改变文件身份。
- 一次普通Node fixture自然结束，真实退出值和资源状态完整；另一次自有Node fixture及其子进程模拟窗口观察抛错/等待超时，证明失败仍记录、定向收口完成且非任务对照对象不受影响。每轮最多这两种fixture，全部受30分钟总预算和各自不超过15秒的寿命约束；正常无关系统伴生进程不按固定数量误判。工具fixture不加载Electron、Maris、Python Host或safeStorage，不计EXE/helper预算，也不计产品通过。
- 静态核对全部S1/S2路径、settings键集getSnapshot/update、结果字段、唯一ID、剩余预算、S2禁止seed/设置写入和S1全过放行逻辑；包含真实调用的cleanup分支，不能只校验未被使用的函数。

如权限不足或无法建立有界收口，停在目标前，禁止先启动EXE后再寻找权限。三轮仍失败，报告已完成自检和具体差异，不自行扩大工具框架或启动目标。

## 两步真实验证，顺序执行

本次 **package0、EXE最多2次、Electron/safeStorage helper0**：S1新增一次恢复授权；S2沿用原未用一次。R8系列累计package1/1、EXE上限3（旧已用1、本次至多2）、helper0。不得把旧S1计为未启动，也不得失败后再开第三次。S1全过后在同任务直接执行S2，不要求再次申请。

沿用原卡真实产品门禁及固定工具版本。直接Node spawn(shell:false)启动上面的原R8 EXE，Playwright仅connectOverCDP；本任务profile/虚拟owner/数据库/动态loopback隔离，不使用外部个人profile。清除MARIS_E2E_EXIT_MS，禁止测试退出计时器、app.quit/process.exit、CDP关闭浏览器或强杀替代普通主窗口关闭。每次页面条件观察最多5秒，普通关窗最多10秒，受整体120秒限额约束。

**S1：真实控件保存后正常退出。** 新profile仅启动前seed合法设置：light/false、closePolicy=quit、closeHintShown=false、毛毛可见。原双窗口、窄bridge/renderer隔离、online/authenticated、canonical daily及daily/Shell/导航/Agent实际存在/数量/可见性门禁保留，后台和DOM分别记录。通过真实控件顺序设dark、privacy=true，核验文件已保存；一次recover后页面、路由与主题/隐私保持。再向核实身份的唯一可见主窗口发WM_CLOSE，root自然exit0、无强制清理，自有进程/监听/窗口0才算S1通过。

**S2：同profile原样续启。** 仅在新S1全部通过后，用同一EXE、profile、虚拟数据库续启；中间不得重新seed、修改theme/privacy、复制回初始文件或发设置更新。先记录S1保存的dark/true与文件摘要；真实页面ready后的首次有效样本同时核验dataset theme=dark/privacy=on、select=dark、checkbox=true。取样前driver设置写入数0仅代表driver没有写，不能声称已监测所有产品内部写入；另记录设置文件前后是否保持。getter/Host正确不能替代四条DOM/控件断言。任一首样失败保留，不通过再设置/刷新/重启转绿。S2通过后普通关窗及资源核验，不追加recover或其他场景。

正式EXE启动后任何产品比较失败、未知工具错误、身份不明、意外弹窗或隐私泄漏即停止后续业务；必须继续获准的只读观察和身份核实的定向收口，停止规则不禁止必要清理。强制清理不得计普通退出通过。失败后只读检查可补当前状态，但不能推断中断期间退出码或覆盖首次样本。任何产品返修需求返回总控，本卡不修产品。

## 收口交付

每步保留独立首次result、阶段日志、冻结driver、真实退出回执、设置安全值/摘要及资源状态；不把marker、端口、PID、owner或token正文复制进仓库文档。旧R8工具、profile63、证据108及固定构建/包前后保持。新profile/证据保留；仅删除经边界和reparse核实的本任务临时项。

新source基于本任务新起点，仅更新executor并加入运行说明，排除清单自身；另提供三路径交付摘要及外部工具/证据清单。成功也只review/finished，不关闭SETTINGS-001、CMP-06、LAZY-001/UI-02或P4-B，不启动Tester/顾问或P4-C。接单、前置工具通过、每个S场景及收口更新本人快照；长操作前记录检查点，有控制时至少10分钟心跳。结束后等待总控，不自动追加任务。
