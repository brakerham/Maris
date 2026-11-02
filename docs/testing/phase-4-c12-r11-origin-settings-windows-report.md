# P4-C12-R11-ORIGIN-SETTINGS 独立复验报告

2026-11-02，Asia/Shanghai。唯一负责人：Tester。结论：**blocked / finished，交总控 review**。独立41节点与四文件109兼容均通过；Windows前只读进程观察遇到未知工具错误，按卡停止。没有新增产品缺陷，不自行关闭P4-B。

## 1. 本轮结论与证据

- 独立：**41 passed、0 failed、0 not_run**；**321/321**具体比较通过，ID唯一、enter/terminal配对，41节点finally全部完成。[首次结果](../../tests/independent/desktop/evidence/r11-origin-settings/independent/result.json)、[原始逐条记录](../../tests/independent/desktop/evidence/r11-origin-settings/independent/journal.jsonl)、[321条expected/actual索引](../../tests/independent/desktop/evidence/r11-origin-settings/assertions.md)。
- 兼容：单独一次四文件 **45+12+25+27=109 passed**，0 failed/skip/未运行，0模块或未处理错误。[兼容结果](../../tests/independent/desktop/evidence/r11-origin-settings/compat/result.json)。该数不混入独立数；未跑旧48、全量217或执行方S1/S2。
- **IPC-ORIGIN-001建议总控限定关闭**：原I06三比较与八组来源边界全部独立通过。仅证明新源码开发来源校验；不声称生产包开发分支可达或原始泄露发生。SEC-04整体仍blocked。
- **SETTINGS-001仍未关闭**：源级独立水合已通过，但新包的W2四条首次有效页面比较尚未进入。UI-02/LAZY-001、CMP-06旧失败保留，不由开发通过替代Windows验收。
- Windows后续W2/W3/H2/W4/H3/W5/H4/W6/W7均**not_run**，后台与真实页面均无本轮新现场结果。没有创建新外部root/profile，没有原生辅助、Host、Docker、OpenClaw、微信或provider操作。

## 2. 固定输入、接单和工具范围

指令版本 `2026-11-02T11:30:00+08:00`；接单 `2026-11-02T11:41:37.822230+08:00`。[新起点](../../tests/independent/desktop/evidence/r11-origin-settings/repository-gate.json) **1438/1438**原字节匹配、staged=0，清单SHA-256 `5286d9c16aa862f61046080fafae3d5a37f205d2e1a4b27ed6d4616fb1524fc1`。旧R10已停止，不恢复旧文件或覆盖其失败。

唯一固定新根 `C:/MarisIpcR9/R9-20261101-161412`，未因摘要相同换回R8。接单前R9七交付、1432实际构建、140产物、67资源、75证据与工具7/运行入口3/开发输入7均匹配；R10交付50（tester用接单前副本）、来源8、首次29匹配；14实际工具入口匹配。EXE SHA-256 `c80d27c8e31fa60df91065a770e669a553260cf8f883c55a0a7f83f8a430736b`，asar `05cdad34ba60b59773eebe671156c96260e69354568b9942da59058641f9c0b2`，lock `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。[固定输入审计](../../tests/independent/desktop/evidence/r11-origin-settings/fixed-input-audit.json)。没有完整重扫历史依赖、安装或重新打包。

源码测试工作目录为本仓库tests/independent/desktop；兼容root为apps/desktop；Node/Vitest/jsdom及别名依赖来自固定R9根。缓存只写本轮evidence/cache。真实security.ts、validateIpc、注册handlers、preload、DesktopApp/Router/Shell使用仓库新起点源码；仅OS/持久化/Host端口与外部bridge使用虚拟输入。[配置](../../tests/independent/desktop/evidence/r11-origin-settings/configuration.json)、[产品输入映射](../../tests/independent/desktop/evidence/r11-origin-settings/product-input-map.json)。映射是37项保守源码全集，包含4兼容文件及package/lock，不声明其中每一项都执行。

正式来源在 `2026-11-02T17:47:09.175036+08:00` 冻结49项，包含实际test/fixture/record/setup/config/reporter/controller、前置工具/计划和产品映射及产品输入，不沿用旧局部清单缺项。清单SHA-256 `6e574c9784fae35c0b8243316bc41fb4fc6870fd37470378461343a766b91a63`。[冻结记录](../../tests/independent/desktop/evidence/r11-origin-settings/freeze.json)、[正式来源](../../tests/independent/desktop/evidence/r11-origin-settings/independent-source.sha256)。正式运行后没有改写这些源码；首份归档另保留49项及能力检查脚本。

11:42工具副本落盘到17:42恢复之间没有连续执行控制，不补造进展或心跳。实际工具准备预算保守计此前5分钟＋本次17:42:56至17:49:41约6分45秒，少于30分钟；v1/最多3版，未重置启动额度。后续审计/报告不属于工具开发重试。[预算续记](../../tests/independent/desktop/evidence/r11-origin-settings/tool-budget-resume.json)。23项虚拟记录/缺损结果/首错/finally/短写/语法/注册collector检查通过，另PowerShell语法0错误；collector不执行回调、不导入产品正文。[前置结果](../../tests/independent/desktop/evidence/r11-origin-settings/preflight-v1/result.json)。

## 3. 原反例和新增来源结果

原I06业务正文保持同一sender/mainFrame和三条比较；I07～U31原尾部保持。[新旧差异](../../tests/independent/desktop/evidence/r11-origin-settings/contract.test.tsx.diff)、[fixture差异](../../tests/independent/desktop/evidence/r11-origin-settings/main-fixture.diff)。新增fixture只接受companion独立origin并观察show/focus，不替换生产oracle。

| 原ID | expected | 本轮actual | 结果 |
| --- | --- | --- | --- |
| R10-I06.TRUSTED | dark | dark | passed |
| R10-I06.DIFFERENT_PORT_REJECTED | ipc_origin_rejected | ipc_origin_rejected | passed；旧actual=null失败仍在R10原目录 |
| R10-I06.NO_SAVE | 0 | 0 | passed；旧失败后未运行，此次实际完成 |

| 独立节点 | 结果 | 输入和边界 |
| --- | --- | --- |
| R11-O01 | passed | 有/无尾斜杠、不同path/query/hash、HTTP/HTTPS大小写及默认/显式端口正对照 |
| R11-O02 | passed | 5173/51730双向、协议/主机/后缀、localhost/IP不同源拒绝 |
| R11-O03 | passed | 空/相对/非法/越界端口/用户密码配置与请求安全拒绝，不传播原始解析错误 |
| R11-O04 | passed | data/javascript/ftp/blob/null拒绝；合法/非法dev配置下原file/maris正反对照保持 |
| R11-O05 | passed | real validateIpc身份/子frame优先、origin先于参数；getter零参数和update严格三字段 |
| R11-O06 | passed | real main getter/update正向、错来源拒绝，启动后设置/Host/outbox/窗口增量不变 |
| R11-O07 | passed | real companion两handler仅自身配置；可信openMain一次show/focus，错误主窗来源及身份/参数拒绝 |
| R11-O08 | passed | 主窗5173/毛毛51730双向隔离；同身份只变URL证明origin拒绝，无增量副作用 |
| R10-I07 | passed | 真实preload窄方法、getter固定零参数、companion无settings或generic invoke |
| R10-U01～U16 | 16 passed | 四主题×隐私布尔×reducedMotion布尔，实际Shell属性/控件一致、一次读/零写 |
| R10-U17～U24 | 8 passed | 非法枚举/类型/缺字段/额外字段/null/数组进入有限安全错误，不展示业务/写回/循环 |
| R10-U25～U31 | 7 passed | 等待、拒绝、StrictMode晚到、卸载、runtime/recover不覆盖选择、空模块水合、故障页不隐式重试 |

旧I01～I05仅引用R10既有通过；不计本轮，不删改旧文件。全部本轮41个节点均首次或唯一授权复验，无skip/xfail/重试。

## 4. Windows工具阻塞与停止

首错时间 `2026-11-02T17:49:41.5641481+08:00`，新只读能力检查在第一阶段 `process_query` 调用 `Get-CimInstance Win32_Process` 抛错；尚未取得进程快照，监听、UIA、Tray及原生对话框能力步骤均未到达。[首次能力回执](../../tests/independent/desktop/evidence/r11-origin-settings/capability.json)、[停止回执](../../tests/independent/desktop/evidence/r11-origin-settings/stop-receipt.json)。

| 观测项 | 期望 | 实际 | 分类 |
| --- | --- | --- | --- |
| Windows前进程归属观察 | 可取得只读进程库存并核实无旧目标占用 | 未取得库存；CimException | 工具/环境阻塞 |
| operation/stage | process_query成功 | process_query失败 | 首次工具失败 |
| 安全错误 | 无异常 | code=unknown；HResult=-2146233088 | 原因未知，不改写为权限拒绝或设备不支持 |
| listener/UIA/Tray能力 | 分别实际检查 | not_run | 不能选择unavailable分支 |
| W2四页面首样 | dark / on / dark / true | 全部not_run，无本轮样本 | 不填历史值或默认值 |

只尝试了1次只读查询；没有重试、提升权限、改系统设置、换观察工具或启动目标来诊断。该HResult不足以确定WMI服务、权限或运行环境中的具体原因；这些仅是待裁定方向。本报告不提交产品P0/P1缺陷。下一共同决定是由总控授权如何验证只读进程观察权限/运行环境，并给出新的续验起点；已通过41/109不应为工具问题自动重跑。

本轮不创建W1副本、不执行H1，不使用R8旧根或S1/S2profile。W2四首样及后续W3/H2/W4/H3/W5/H4/W6/W7未进入；不能用源级水合/compat代替实机结果。原生老化/Tray/关闭能力均unverified，未触发“明确能力缺失”的合法降级分支。

## 5. 退出、资源与预算

独立控制器/CLI root30544实际exit0、worker23388实际nativeExitCode1，执行4547ms；41节点cleanup完成。兼容root23832实际exit0、4个worker退出（19760=0，28060/12524/26768=1），执行3272ms。两个控制器无timeout/forced/error，流读取完整。worker原始退出值保留，signal未观测，未填0；固定Vitest池stop源码明确fork.kill收口，其机制与完成结果/root0一致，不称worker自然exit0，也不把它作为产品正常退出证据。[独立进程](../../tests/independent/desktop/evidence/r11-origin-settings/independent/process.json)、[兼容进程](../../tests/independent/desktop/evidence/r11-origin-settings/compat/process.json)、[解释及固定源码摘要](../../tests/independent/desktop/evidence/r11-origin-settings/independent-verification.json)。

本轮产品/原生helper/Host启动0，没有本轮目标需要关闭。进程系统查询失败，全机历史进程/端口/窗口保持unverified；不将其写成资源零。未删除volume/profile/目录，保留首次材料与测试缓存；无任何Git写操作。

| 类别 | 本轮新增/额度 | 系列累计/上限 |
| --- | --- | --- |
| 产品EXE | 0/6 | 2/8 |
| 原生helper | 0/3 | 3/6 |
| H1/安装/package/开发服务器 | 0/0 | 历史额度不重置 |
| 正式独立Vitest | 1次，未重跑 | 不混入产品额度 |
| 四文件兼容 | 1次109 | 不混入独立节点 |
| Windows只读能力检查 | 1次，首阶段失败 | 不算产品/helper，保留原错误 |

## 6. 原24项完整要求、历史与剩余条件

SEC-04由failed改blocked，仅反映本轮已证明来源反例修复，整项仍缺完整Windows证据；UI-01历史passed、UI-02/CMP-06历史failed保持。B为**1 passed、2 failed、19 blocked、2 not_run**。原120ID/12列、风险、完整预期及A/C/D不变。历史总体依据[R10完整逐项表](phase-4-c12-r10-settings-windows-report.md#原-24-项完整要求与状态)，本轮增量如下。

| ID | 原完整预期与禁止副作用 | 当前状态 | 历史引用 / 本轮证据 / 剩余条件 |
| --- | --- | --- | --- |
| P4B-SEC-01 | sandbox/contextIsolation 开启、nodeIntegration 关闭；无 `require/process/fs/child_process` 或任意 preload 对象 | blocked | 历史隔离/窄bridge局部证据保持；本轮未运行Windows renderer隔离探测，完整Node能力枚举仍缺。 |
| P4B-SEC-02 | CSP 阻止执行；未知导航/窗口拒绝；获准外链只由 main 安全打开，不加载进应用权限域 | blocked | 旧CSP/新窗局部证据保持；O04验证原生产URL谓词正反对照，不代替实际CSP/导航/外链安全组合。 |
| P4B-SEC-03 | 只暴露窄 typed 方法；无通用 channel、Node require、密钥或进程控制 | blocked | I07真实main/companion preload窄接口5条通过（settings仅getSnapshot/update、getter零参数、companion仅getState/openMain）；Windows运行时暴露/密钥/Node完整组合未验。 |
| P4B-SEC-04 | sender 与参数双校验；稳定拒绝；不得启动进程、改设置、打开窗口或泄露异常 | blocked | 旧I01～05仅引用；本轮I06+O01～08真实predicate/validateIpc/main/companion行为全部通过。建议仅关闭IPC-ORIGIN-001；未知channel、重复调用及完整Windows动态安全组合未验，整项blocked。 |
| P4B-SEC-05 | refresh/device token 与 API key 只在 main/OS 保护边界；renderer 无持久原文；日志与 crash dump 无值 | blocked | 旧H1原生owner/outbox通过只引用；本轮无解密/登录/续启。renderer存储/内存及全日志/crash边界仍缺。 |
| P4B-SEC-06 | 端口不是认证；nonce/origin/token 均校验；只绑定 loopback，远程连接拒绝 | blocked | 本轮无Host/HTTP；随机端口监听查询未到达。nonce/token/远程/绕过完整组合保持未验。 |
| P4B-SEC-07 | 文本安全编码、布局有界且不执行；不得改变 IPC、模块注册或权限 | blocked | 真实DesktopApp承载虚拟页面，但未执行HTML/RTL/超长文本矩阵；旧局部证据不扩签布局与安全整项。 |
| P4B-SEC-08 | 用户只见稳定安全错误和 request ID；renderer console/日志无秘密或未授权数据 | blocked | U17～24/U26实际非法设置与拒绝响应进入有限安全错误，通过canary及零写/不循环检查；U31局部错误保持Shell/Agent。真实Windows日志/内部路径/SQL/reqID与crash全组合仍缺。 |
| P4B-SUP-01 | 只停止 PID+nonce 匹配且由本实例启动的子进程；手工/他实例进程保持 | blocked | 既有owned清理证据保持；本轮进程查询unknown，未执行任何Host故障或停止。外来/手工/伪造身份对照仍缺。 |
| P4B-SUP-02 | 使用随机可用 loopback 端口；超时进入离线/诊断并清理自有子进程，不把 health 当 ready | blocked | 历史online局部证据保持；本轮Windows未启动，坏ready/端口冲突/超时与自有清理组合仍缺。 |
| P4B-SUP-03 | 状态转 offline；重启次数/退避有界，不形成重启风暴或重复 run；用户可恢复 | blocked | 本轮W6未运行。U29虚拟bridge的recover通知保持页面状态，不代签真实崩溃/退避/恢复预算。 |
| P4B-SUP-04 | 不产生重复 owned 后端；连接手动后端时不取得停止权；状态可区分 | blocked | W3与手工外部模式未运行，第二实例正常退出/原Host保持仍缺。 |
| P4B-SUP-05 | 自有后端按冻结时限退出，无僵尸/孤儿/占用端口；未拥有进程不受影响 | blocked | QUIT-001普通关闭历史通过仅引用；本轮只有测试runner/worker退出。产品正常退出/强关/注销和外来对照无增量；全机资源未知。 |
| P4B-SUP-06 | 未发送内容和同一 ID 保留；恢复后只提交一次；UI 不凭新 ID 制造重复账候选 | blocked | 旧H1草稿读取基线保持；W2/H2及老化保留删除未运行，同ID续启/重提/一次写/GET尚缺。 |
| P4B-UI-01 | 只渲染两侧均存在且兼容的模块；未知/禁用不导航、不预加载 | passed | 旧13节点模块交集及真实日常页已被接受，整项passed保持，不重跑；本轮U30只增加设置先于模块就绪的保护。 |
| P4B-UI-02 | 局部错误边界可重试，Shell/登录/其他模块可用；不循环加载或丢当前会话 | failed | 旧LAZY-001整项failed保持；U29/U31通过不隐式重建/重试且保持用户选择与Shell/Agent；真实chunk/W6显式retry/其他模块/会话范围未执行。 |
| P4B-UI-03 | 漂移门禁失败并定位；不得靠手写 API 类型掩盖差异或运行时下载 schema | blocked | 既有生成物静态证据保持；本轮未运行export或CI漂移门禁，不签整项。 |
| P4B-UI-04 | 不兼容或冲突稳定失败；Shell 无 `if moduleId` 业务分支 | blocked | 旧冲突修复与注册结构证据保持；本轮只用真实registry装配UI，未重跑注册冲突集合或签完整启动组合。 |
| P4B-CMP-01 | 始终只有一个毛毛窗口/Agent 入口；主形态随 contribution，子状态不创建第二 Agent或触发写入 | blocked | O07/O08为main/companion来源与打开主窗的虚拟OS边界，非真实窗口数量/形态状态流验收；真实多contribution/单Agent范围仍缺。 |
| P4B-CMP-02 | 首次隐藏并只提示一次；第二次不重复提示；Host/毛毛按设置驻留且无数据丢失 | blocked | W7未运行，首次提示/二次关闭/Tray恢复/驻留数据连续性仍缺；本轮没有判UIA或Tray不可用。 |
| P4B-CMP-03 | 行为精确对应设置；“退出”清理自有后端；询问取消不退出；Tray 状态一致 | blocked | 普通quit历史通过仅引用；W6/W7未运行，hide/ask/cancel/Tray行为仍缺，未使用非法closePolicy IPC。 |
| P4B-CMP-04 | 默认关闭且无启动项；只有明确操作才创建；禁用清理本应用项，不改其他应用 | not_run | OS启动项未操作；默认关闭、显式启禁及仅修改本应用项仍未验证。 |
| P4B-CMP-05 | 位置用临时文件原子替换并恢复/夹取；全屏按规则隐藏；隐私不显示金额；键盘入口可达 | not_run | 独立16组合隐私水合及等待/晚响应保护通过；本轮真实W2未执行，金额隐藏、键盘、多屏/DPI/位置/拔屏/全屏均未验证。 |
| P4B-CMP-06 | 可安全降级且合同不变；文本对比/焦点可辨；reduced motion 生效；收入/支出色不复用涨跌色 | failed | U01～16四主题/隐私/reducedMotion输入组合水合通过，不等于视觉/动效或设备实测。旧W2主题恢复failed仍保留；新包W2、透明降级/焦点/对比/颜色仍未验。 |

## 7. 不测试范围与交付

不操作真实财务数据/provider、微信/OpenClaw/Docker，不注销或重启系统、不改OS主题/启动项/多屏/安全软件，不安装/打包/改产品/依赖/固定包。完整P4-C/D未开始，不自行派发其他角色或宣布P4-B complete。真正P4-C前端开始前的参考图与模型分工提醒仍由总控执行。

终点只读审计将核对：1438原项中四份共享测试文档的授权变化；R9固定交付/构建/产物/资源与实际工具入口；旧R10和R9系列首次材料及四旧profile；49正式来源、首份源码归档、321比较配对、120ID/12列/A/C/D、两旧文档追加性及staged=0。结果见[终点审计](../../tests/independent/desktop/evidence/r11-origin-settings/end-audit.json)。首次材料、工具与最终交付采用不自引用的逐项清单。最终交付摘要见[交付核对](../../tests/independent/desktop/evidence/r11-origin-settings/delivery-verification.json)，角色收口见[tester](../coordination/agents/tester.md)。

### 实际终点结果

终点审计实际通过：1438原项中1434保持，变化精确为tester、C12主报告、人工清单、P4矩阵四个授权文件；其余产品、执行方/总控文件和旧证据未变化。R9七交付/1432构建/140产物/67资源/75证据、工具与入口保持；R10交付50按本轮接单前四文档副本校对，来源8/首次29保持。R9旧首次68/38/89/148以及旧profile63/63/63/65全部匹配；49正式来源与50份归档、90首次材料均保持。矩阵120唯一ID/12列、所有原预期/风险及A/C/D保持，只有SEC-04状态行变化；两旧文档只追加。staged=0，diff-check实际exit0。

本报告、tester和最终清单在该审计后完成交付落盘；最终逐项摘要再次验证覆盖这些最终字节。状态为blocked / finished，等待总控review。这里的终点审计通过只说明边界和证据完整，不把Windows阻塞改成验收通过。
