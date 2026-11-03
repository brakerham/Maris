# P4-C12-R11-R1-WINDOWS 独立验收报告

2026-11-03，Asia/Shanghai。Tester唯一负责人。**blocked / finished，提交总控review**。W2/W3及H2通过；W4在原生按钮身份定位处发生工具错误，保留首次并安全收口，后续停止。没有新增产品业务缺陷，不自行关闭P4-B。

## 结果与边界

| 范围 | 本轮实际结果 | 结论范围 |
| --- | --- | --- |
| 新固定起点 | 1550/1550匹配，staged=0后接单 | 输入门禁通过 |
| R11 41节点/321比较、109兼容 | 只引用总控已接受证据，0次重跑 | IPC-ORIGIN-001已限定关闭 |
| 目标前只读观察 | 标准审批后v3通过；身份/监听/UIA/Tray根分别记录 | 不把根可读当操作适配可用 |
| W2/W3 | 18/18比较通过，首次页面四比较通过，正常退出和资源收口通过 | 真实新包与W1同内容虚拟副本续启 |
| H2 | 13/13原生比较通过；之后才加入4条冻结老化数据 | 稳定owner/原草稿实际读回；不重复H1 |
| W4 | 2项前置身份比较通过；按钮定位失败，保留操作未执行 | 工具阻塞；不是产品业务比较失败 |
| H3/W5/H4/W6/W7 | not_run | 正式停止后未继续，不补签 |

建议总控**限定关闭 SETTINGS-001**：既有R11独立水合已被接受，本轮原W2四条首次有效页面比较均满足。CMP-06整项仍缺真实设备视觉等完整条件，由failed改blocked；UI-02/LAZY-001仍failed，整个P4-B未关闭。矩阵B为 **1 passed、1 failed、20 blocked、2 not_run**。

核心证据：[W2/W3结果](../../tests/independent/desktop/evidence/r11-r1-windows/windows-W2/result.json)、[H2原生结果](../../tests/independent/desktop/evidence/r11-r1-windows/helper-H2/native-result.json)、[W4首次结果](../../tests/independent/desktop/evidence/r11-r1-windows/windows-W4/result.json)、[停止回执](../../tests/independent/desktop/evidence/r11-r1-windows/stop-receipt.json)、[所有已执行比较](../../tests/independent/desktop/evidence/r11-r1-windows/assertions.json)。33条已到达比较全部通过，分为18个W2/W3、13个H2及2个W4前置；这个总数不表示W4业务通过。

## 接单、输入与准备

control版本`2026-11-03T00:05:00+08:00`；接单时间 **2026-11-03T00:17:47.579040+08:00**，新1550项清单SHA-256 `5fd65684cf41177c7d072f066887995f3820c08dc7f3a7e46434ef29d796e6d8`。[起点回执](../../tests/independent/desktop/evidence/r11-r1-windows/repository-gate.json)。已按AGENTS读取角色规则、最新控制、本角色、新卡及R11裁定/报告、观察回执、冻结接口与矩阵。

R11交付110、工具11、证据93、正式来源49、首次90、归档50按各自基准根逐项匹配；tester接单后用接单前副本对照旧交付。固定R9七交付、1432实际构建、140产物、67资源、75证据及实际工具入口匹配。[输入审计](../../tests/independent/desktop/evidence/r11-r1-windows/input-audit.json)。没有全扫历史依赖、安装、打包或更换工具版本。

唯一包根`C:/MarisIpcR9/R9-20261101-161412`，EXE `c80d27c8e31fa60df91065a770e669a553260cf8f883c55a0a7f83f8a430736b`；asar `05cdad34ba60b59773eebe671156c96260e69354568b9942da59058641f9c0b2`；lock `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。没有以摘要相同换回旧R8路径。

本轮外部根`C:/MarisC12/C12-R11-R1-WINDOWS-20261103-002800`。确认边界、无reparse、未存在、源无相关进程后，普通复制原`C:/MarisC12/C12-R9-QUIT-20261016-011200`的profile-main及continuity.json，63项路径/大小/摘要完全一致；不用S1/S2、旧失败W2profile或新owner。[复制回执](../../tests/independent/desktop/evidence/r11-r1-windows/profile-copy.json)。后续新副本保留，不重置或删除。

工具准备原始00:20开始；执行控制中断时无目标运行，不补造心跳。10:28继续时保守计此前10分钟，余20分钟；W2来源在10:31冻结，H2/老化来源在10:36冻结，计约18分钟以内，标准审批等待另列。观察器最多3版，v1虚拟12项、v2虚拟15项、v3虚拟18项、W2静态9项及同一H数据函数虚拟10项分别保留，不累加成产品通过。v3实际观察通过后没有重跑旧41/109或H1/W1/S1/S2。

W2正式来源14项、helper14项、retention11项已分别冻结，包含实际controller/native/observer/config/公共identity/parser/storage/计划及旧基线输入。[W2冻结](../../tests/independent/desktop/evidence/r11-r1-windows/windows-w2-freeze.json)、[helper/老化冻结](../../tests/independent/desktop/evidence/r11-r1-windows/retention-freeze.json)。固定EXE/resources及真实Node/PowerShell/Electron/Playwright入口由输入审计绑定，不以开发源码替代包。正式首次后不改已冻结来源；30份合并源码归档保留。

## 观察权限与工具更正

旧R11 CimException根因仍unknown，未倒填。本轮不为重现AccessDenied做默认循环；经工具标准审批执行只读前置检查，未修改WMI/服务/ACL、安全软件或永久权限。产品实际启动另按真实动作申请，未混入“只读”申请；当前token实际检查`elevatedAdministrator=false`，不RunAs。

v2第一份现场检查实际取得437条进程并核实自身PID37748，但旧父进程假设仍是PowerShell，未排除本轮Node34512及其launcher1200，产生明确`target_process_present`；不是发现外来产品。按目标前允许修正建立新v3，仅排除已核实的准确self/Node/launcher PID、exe、脚本参数、创建时间及父子关系，不按进程名批量忽略。v2源码/回执原样保存。

v3实际进程self37620/Node37188/launcher22996身份全部true、相关目标0；监听查询成功、相关监听0；UIA顶层14与Tray根1读取成功，各阶段独立记录。总耗时3594ms、实际exit0、signal=null、无timeout。Tray操作适配器为`not_implemented`，不是device_unavailable。00:24至10:27执行间隔后，另做必要当前进程核对，self9036身份true/相关0/非管理员，未重跑整个能力试验。[v3结果](../../tests/independent/desktop/evidence/r11-r1-windows/observe-v3.json)、[实际进程回执](../../tests/independent/desktop/evidence/r11-r1-windows/observer-v3-process.json)、[恢复后进程检查](../../tests/independent/desktop/evidence/r11-r1-windows/fresh-process-check.json)。

每次观察使用原异步captured机制，上限8秒；CIM进程内部3秒、监听2秒。CIM日期对象直接转换UTC，只有原始字符串才解析。阶段enter/result即时写盘，异常类型/HResult/NativeErrorCode/StatusCode/Category分别留存，缺失为null，未输出全机命令行或原始账户内容。曾准备的未执行跨调用请求草稿已在首次冻结前移除，实际使用原异步子调用结构，没有建立后台权限服务。

## W2四条原首样、W3与正常关闭

Node直接spawn固定新EXE，shell=false，Playwright只connectOverCDP。动态loopback、实际PID/创建时间/父子关系、marker和固定路径核实。首样前无设置update、seed、recover、refresh或页面刷新；保留原quit/dark/true。后台实际online/authenticated与实际daily/Shell/nav/Agent取样分别完成；安全DOM结构、可见性、路由hash、设置摘要及driver写入数保存在首次journal。[首样日志](../../tests/independent/desktop/evidence/r11-r1-windows/windows-W2/journal.jsonl)。

| 原断言ID | expected | actual | 结果 |
| --- | --- | --- | --- |
| W2-PERSISTED-UI-THEME | dark | dark | passed |
| W2-PERSISTED-UI-PRIVACY | on | on | passed |
| W2-PERSISTED-THEME-CONTROL | dark | dark | passed |
| W2-PERSISTED-PRIVACY-CONTROL | true | true | passed |

四比较来自同一首个有效样本，不以getSnapshot回包替代页面；首样前driver设置写入数0，设置文件摘要相等。之后使用原draft/body重复prepare取得原clientEventId，未提交provider或写财务数据。

W3同profile第二实例22100直接ChildProcess身份、创建请求时间、父PID与固定exe另记，实际exit0；原主22292仍在，Python PID+创建时间列表保持。随后原主窗口普通WM_CLOSE、10秒上限、自然exit0，owned/listener/window均0，无退出计时器或强杀。W2/W3共14894ms，controller exit0；资源查询回执成功，不把未查询当空集。

## H2实际续启基线与老化准备

H2 spawn前，从本轮产品副本复制完整Local State到全新helper-profile-H2，字节/摘要相等；ready前绑定userData/sessionData，ready后与结束前核对加密字段同源。核实固定Electron、脚本/路径/marker/PID及release后才读取。只使用safeStorage和测试数据函数，不加载产品main或会repair/write的产品初始化。

实际owner schema、稳定ownerIdentityDigest、refresh存在及原draft/event/body摘要均通过，原outbox count1。刷新token可轮换，不要求token原值相同。全部基线比较通过后才seed：过期draft、过期queued、近期queued、过期sending各1，原continuity条目保留，共5项。仅变更新副本outbox.bin；owner及其余产品profile文件逐字保持。H2 process.json的`profileUnchanged=true`明确指**排除已授权outbox.bin**的库存，不表示没有seed。13条比较含种子加密写入读回和owner原字节保持。

helper16520实际exit0，controller exit0，5745ms，无forced，owned/listener/window0。[H2进程](../../tests/independent/desktop/evidence/r11-r1-windows/helper-H2/process.json)、[上下文复制](../../tests/independent/desktop/evidence/r11-r1-windows/helper-H2/context-preparation.json)、[原生逐阶段记录](../../tests/independent/desktop/evidence/r11-r1-windows/helper-H2/native-stages.jsonl)。H2成功不倒推旧H1未知错误、不替代后续H3/H4语义读回。

## W4首次定位阻塞与安全收口

W4新启动1596及CDP监听归属两比较通过、实际runtime online。首错发生于`2026-11-03T10:36:54.555+08:00`：为原生老化提示定位默认“保留”按钮，观察器W4-OS-3返回exit3。

| 字段 | 首次实际值 |
| --- | --- |
| 操作阶段 | retention_dialog → owned_button |
| 安全错误码 | owned_dialog_button_ambiguous |
| 异常类型 | System.Management.Automation.RuntimeException |
| HResult | -2146233087 |
| NativeErrorCode / StatusCode | null / null，未提供，不补造 |
| Category | OperationStopped |
| observer status / signal / timeout | 3 / null / false |
| 期望定位数 | 1个本轮窗口内“保留”按钮 |
| 实际定位数 | 未记录；只证实不满足唯一性，不能断言0或多个 |
| 点击结果 | 未调用Invoke；W4-RETENTION-CHOICE-INVOKED未到达 |

该错误是在现有owned按钮适配器定位阶段，**不能证明保留功能失败、数据删除或设备不支持**。未进一步点击其他窗口或修改定位器重跑。实际原生按钮匹配数量缺失是工具证据限制，下一修正应先保留安全的候选数量与层级/身份，不应凭当前记录猜测具体窗口结构。

finally尝试普通关闭时另有W4-OS-4 `native_close / owned_main_ambiguous`，未获得唯一可关闭的Maris窗口，因此未PostMessage；同样RuntimeException/HResult -2146233087/Native与Status null/OperationStopped，observer exit3。该后续错误与首错分开，不能将它记作普通退出产品回归。

随后重新核实1596及本轮后代的exe/父子/创建时间，定向taskkill该自有树；实际root exit1、signal=null、forced=true。最终成功资源查询owned/listener/window=0，controller exit1，耗时13858ms，无超时。`cleanupError=null`只表示最终有界资源清理成功，前面的普通收口错误仍在journal，不表示正常退出通过。[W4逐阶段记录](../../tests/independent/desktop/evidence/r11-r1-windows/windows-W4/journal.jsonl)。

已按首次正式工具错误停止，H3/W5/H4/W6/W7均not_run。没有再次启动产品/helper、修定位器、尝试另一按钮或借撤销/重试覆盖失败。已seed的新副本保留在现场，后续保存/删除语义未验；不删除/reset该资料。新profile共68项，比原63项新增5、字节变化13、删除0，详见[新资料变化清单](../../tests/independent/desktop/evidence/r11-r1-windows/profile-delta.json)。outbox密文字节不等于H2seed摘要，不能凭此推定内容被删或改写，也不能代替尚未执行的H3实际解密比较。

## 启动预算与未执行范围

| 项目 | 本轮新增/额度 | 系列累计/上限 |
| --- | --- | --- |
| 产品EXE | 3/6：W2、W3、W4各一次 | 5/8 |
| 原生helper | 1/3：H2一次 | 4/6 |
| H1/W1/执行方S1/S2/旧通过集合 | 0次重跑 | 不增加旧预算 |
| 41独立/321比较、109兼容 | 0次重跑 | 仅历史接受引用 |
| 安装/package/开发服务器 | 0 | 未执行 |

剩余额度不构成自动续跑许可；正式失败已触发停止。本轮未改产品/依赖/包/旧证据，未操作Git写入、系统权限/安全设置、OS注销/重启/启动项/主题/多屏、真实财务/provider、Docker/OpenClaw/微信。W6真实后端故障/chunk/Tray与W7原生关闭策略未运行；Tray读取成功而动作适配未实现，不归类设备缺失。

## 原24项完整要求与覆盖映射

原120ID/12列、完整预期/风险和A/C/D保持；只有CMP-06当前状态行failed→blocked，旧首次失败仍原样保留。逐项历史/本轮/剩余如下。

| ID | 原完整预期与禁止副作用 | 当前状态 | 历史引用 / 本轮结果 / 剩余条件 |
| --- | --- | --- | --- |
| P4B-SEC-01 | sandbox/contextIsolation 开启、nodeIntegration 关闭；无 `require/process/fs/child_process` 或任意 preload 对象 | blocked | 历史隔离/窄bridge局部证据保持；本轮实际Shell运行，但未执行完整renderer Node能力探测，不能整项通过。 |
| P4B-SEC-02 | CSP 阻止执行；未知导航/窗口拒绝；获准外链只由 main 安全打开，不加载进应用权限域 | blocked | R11来源谓词证据已接受只引用；本轮没有完整真实CSP/导航/新窗口/外链攻击矩阵。 |
| P4B-SEC-03 | 只暴露窄 typed 方法；无通用 channel、Node require、密钥或进程控制 | blocked | R11 I07真实preload窄方法已接受；本轮只调用固定runtime/outbox接口，未重跑其测试或扩签整项。 |
| P4B-SEC-04 | sender 与参数双校验；稳定拒绝；不得启动进程、改设置、打开窗口或泄露异常 | blocked | IPC-ORIGIN-001已由总控限定关闭，41/321独立来源只引用；原整项Windows未知channel/重复调用与拒绝副作用仍缺。 |
| P4B-SEC-05 | refresh/device token 与 API key 只在 main/OS 保护边界；renderer 无持久原文；日志与 crash dump 无值 | blocked | H2实际同源safeStorage读回稳定owner、refresh存在及草稿摘要通过；不比较可轮换token相等。renderer各存储/内存、crash/log完整秘密边界仍缺。 |
| P4B-SEC-06 | 端口不是认证；nonce/origin/token 均校验；只绑定 loopback，远程连接拒绝 | blocked | W2/W4 CDP监听为本轮owned且loopback通过；不等于Host所有nonce/token/origin/远程绕过组合，整项仍blocked。 |
| P4B-SEC-07 | 文本安全编码、布局有界且不执行；不得改变 IPC、模块注册或权限 | blocked | 本轮未执行恶意HTML/RTL/超长文本安全和布局矩阵，历史证据只引用。 |
| P4B-SEC-08 | 用户只见稳定安全错误和 request ID；renderer console/日志无秘密或未授权数据 | blocked | 本轮工具错误脱敏与旧U非法响应安全证据不代替全产品UI/console/log/reqID/crash组合；仍缺完整实际故障注入。 |
| P4B-SUP-01 | 只停止 PID+nonce 匹配且由本实例启动的子进程；手工/他实例进程保持 | blocked | W2普通退出、W4按PID/创建时间/父子树核实后定向清理；未处理其他程序，外来/手工/伪造PID完整对照仍缺。 |
| P4B-SUP-02 | 使用随机可用 loopback 端口；超时进入离线/诊断并清理自有子进程，不把 health 当 ready | blocked | W2真实managed启动online与owned loopback通过；坏ready/nonce、冲突/超时完整组合未执行。 |
| P4B-SUP-03 | 状态转 offline；重启次数/退避有界，不形成重启风暴或重复 run；用户可恢复 | blocked | W6未运行，真实后端故障/恢复次数/退避/页面保持无本轮增量；不由本轮正常online代签。 |
| P4B-SUP-04 | 不产生重复 owned 后端；连接手动后端时不取得停止权；状态可区分 | blocked | W3一次第二实例直接spawn身份/时间/退出记录，exit0且原主实例与Python PID/创建时间保持；external_dev手工后端停止权对照未执行。 |
| P4B-SUP-05 | 自有后端按冻结时限退出，无僵尸/孤儿/占用端口；未拥有进程不受影响 | blocked | W2普通WM_CLOSE自然exit0且10秒内资源0；W4模态定位工具失败后强制exit1另列，不当普通退出通过或旧QUIT-001回归。注销/系统结束/外来对照未验。 |
| P4B-SUP-06 | 未发送内容和同一 ID 保留；恢复后只提交一次；UI 不凭新 ID 制造重复账候选 | blocked | W2相同draft/body返回原event ID，H2稳定owner与原draft/event/body实际原生保持；H2另seed4条。W4未完成保留选择，H3/W5/H4未执行，不能签保留/删除或完整恢复一次一写。 |
| P4B-UI-01 | 只渲染两侧均存在且兼容的模块；未知/禁用不导航、不预加载 | passed | 旧模块13节点与真实日常页已接受；本轮daily/Shell/nav/Agent实际就绪，不重跑旧模块集合，整项passed保持。 |
| P4B-UI-02 | 局部错误边界可重试，Shell/登录/其他模块可用；不循环加载或丢当前会话 | failed | 旧LAZY-001整项failed保留；W6真实chunk与retry未执行，不能借W2成功关闭。 |
| P4B-UI-03 | 漂移门禁失败并定位；不得靠手写 API 类型掩盖差异或运行时下载 schema | blocked | 本轮不重跑generated或CI漂移门禁，旧部分证据保持，完整条件仍缺。 |
| P4B-UI-04 | 不兼容或冲突稳定失败；Shell 无 `if moduleId` 业务分支 | blocked | 本轮使用固定注册装配，无新冲突矩阵/业务分支组合，旧证据只引用。 |
| P4B-CMP-01 | 始终只有一个毛毛窗口/Agent 入口；主形态随 contribution，子状态不创建第二 Agent或触发写入 | blocked | W2取到真实毛毛页面，未执行多contribution与完整子状态流、单Agent/无写入全条件。 |
| P4B-CMP-02 | 首次隐藏并只提示一次；第二次不重复提示；Host/毛毛按设置驻留且无数据丢失 | blocked | W7未运行；W4老化提示属于不同条件，不等于首次关闭提示。首次隐藏/提示一次/Tray恢复/驻留保持仍缺。 |
| P4B-CMP-03 | 行为精确对应设置；“退出”清理自有后端；询问取消不退出；Tray 状态一致 | blocked | W2保留原quit策略普通退出通过；hide/ask/cancel/真实Tray未运行，未使用非法closePolicy IPC。 |
| P4B-CMP-04 | 默认关闭且无启动项；只有明确操作才创建；禁用清理本应用项，不改其他应用 | not_run | OS启动项未操作；人工默认关闭/显式启禁/仅影响本应用仍未验证。 |
| P4B-CMP-05 | 位置用临时文件原子替换并恢复/夹取；全屏按规则隐藏；隐私不显示金额；键盘入口可达 | not_run | W2实际privacy=on、checkbox=true通过；多屏/DPI/位置/拔屏/全屏/金额隐藏/键盘完整人工条件仍未验。 |
| P4B-CMP-06 | 可安全降级且合同不变；文本对比/焦点可辨；reduced motion 生效；收入/支出色不复用涨跌色 | blocked | 既有R11源级水合加本轮W2主题dark/控件dark实际通过，建议限定关闭SETTINGS-001，整项从failed转blocked。透明降级/对比/焦点/OS主题/动效/颜色仍缺，不签passed。 |

## 最终核对与交接

终点核对覆盖1550原起点仅四共享测试文档的授权变化、固定新包/资源/实际入口、旧R11及R9系列首次材料、原W1及其他旧profile、所有本轮冻结来源、首份源码/结果、68项新profile库存及矩阵/追加性。详见[终点审计](../../tests/independent/desktop/evidence/r11-r1-windows/end-audit.json)和[最终交付核对](../../tests/independent/desktop/evidence/r11-r1-windows/delivery-verification.json)。身份、首次结果和清理分别保留，不因审计通过改写W4业务未验证。

交总控审阅：限定关闭SETTINGS-001建议与完整CMP-06/P4-B接受分开；决定下一原生模态定位工具的精确授权、停止后新起点及剩余额度。旧R11权限未知不倒填，本轮v2自进程排除错误已明确修正；当前新阻塞是W4实际owned_button与普通收口窗口定位。不得直接重启带老化数据的新profile进行未授权试探。测试角色停止于blocked / finished；真正P4-C前端参考图和模型分工提醒继续由总控执行。

终点审计实际于 `2026-11-03T10:54:12.974760+08:00` 完成，exit0、passed=true（仅证据完整性，不是W4业务通过）。1550项中1546保持，四共享测试文档为授权变化；R9固定1432/140/67、17实际入口、R11交付110/工具11/证据93/两套正式来源各49/首次90/归档50保持；R9系列旧首次68/38/89/148与四旧profile63/63/63/65保持。新来源14/14/11、首次103、归档30及新profile68项全匹配。33条已到达比较ID唯一且expected/actual完整；W2的18和W4的2条enter/terminal配对、H2的45个操作阶段配对。120ID/12列/原预期及A/C/D不变，两旧文档追加性通过，staged=0，diff check exit0。
