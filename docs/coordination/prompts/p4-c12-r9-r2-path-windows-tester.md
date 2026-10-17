# P4-C12-R9-R2：脚本路径身份修正与剩余 Windows 续验

## 负责人、输入及不重复范围

既有测试智能体是唯一负责人；执行方和顾问停止。先读AGENTS所列必读、最新control、本人状态、本卡，再读 [总控裁定](../../p4-c12-r9-r1-path-coordinator-review.md)、[R9-R1报告](../../testing/phase-4-c12-r9-r1-h1-windows-report.md)、[原R9-R1完整卡](p4-c12-r9-r1-h1-windows-tester.md)及其引用的原R9输入/Windows合同。本卡覆盖新路径范围、工具开发/现场预算；原产品业务要求、固定包、时限和不重复清单保持。

接单前 [本轮起点](../snapshots/p4-c12-r9-r2-start.sha256) 全部原字节匹配、路径唯一有序且staged=0。清单以仓库为基准，UTF8无BOM、LF、`path<TAB>sha256`，不含自身。

读实际 `r9-r1-observer-attempt1.ps1`、`r9-r1-observation.mjs`、`r9-r1-tool-live-attempt1.mjs`、未执行的 `r9-r1-h1-native.cjs`，以及 `evidence/r9-r1/tool-stop-analysis.json`、pretarget-tool-correction及live-tool-attempt1首次材料。更正后前三身份true、scriptArgument=false；旧H1根因仍unknown。不要将本次路径问题倒写为旧H1的原因。

R9的8节点/235比较、48开发兼容及W1的62比较保留，不重跑；原模块13、冷入口B、完整恢复、注册/outbox等通过同样只引用。普通关闭QUIT-001已限定关闭，不重新派产品返修。

## 允许写入

- 新 `tests/independent/desktop/r9-r2-*` 工具、共享路径检查及其局部测试、必要H1控制器。
- 新 `tests/independent/desktop/evidence/r9-r2/**`，每轮源码、日志、比较和真实退出分别保留，不覆盖首次。
- 新 `docs/testing/phase-4-c12-r9-r2-path-windows-report.md` 和本人tester。
- 原C12主报告/人工清单仅追加；矩阵只更新有证据的B状态/备注，120ID、12列、原预期和A/C/D保持。

旧工具/证据、产品/开发测试、包、依赖/lock、Forge、控制/overview/snapshot及其他角色只读。无安装、下载、打包、产品/系统配置修改或Git写操作。不要新建通用runner、Windows Job或精确进程数预算。

## 一次修完整的脚本身份合同

1. 本任务只支持固定Node/stock Electron的直接启动 `spawn(exe, [absoluteScript], {shell:false,...})`，无命令包装、无额外Node/Electron CLI参数。参数数组中的脚本字符串不手工加引号，由spawn处理。由同一启动描述生成规范绝对脚本路径、observer请求和预期摘要，不手写三套路径。native内现有GPU开关不改变这一CLI合同。
2. 从实际CIM `CommandLine`取得**完整参数边界**，验证冻结的参数数量及脚本位置。允许用Windows `CommandLineToArgvW` 并在finally释放结果；不手写空格split、全串Replace、Contains、basename或后缀匹配。参数不符合这一本任务的固定结构则拒绝，不扩展为任意命令行解析框架。
3. 仅对提取的脚本参数和期望路径分别规范化：要求完整盘符绝对路径，统一分隔符并解析完整路径；相对路径、`C:foo`、`\foo`不能用observer自己的cwd解释为合法。路径在指定任务边界内、无reparse、对应预先冻结的文件；比较完整路径及实际文件摘要。相同内容的另一个路径也不能冒充目标文件。不增加UNC、8.3、设备前缀、大小写别名或符号链接支持。
4. 同一规则用于现场自检、H1 root、native ready及observer取消回执；不得只给自检放宽。exe、父PID、创建时间、call ID、marker、ready PID及源摘要条件全部保留。当前root不可验证时不能release；未知枚举不能当空集合。
5. 在现场运行之前，完成并冻结 **H1 controller** 与上述接线：绝对脚本启动→observer请求→实际参数身份→ready PID/path/hash/marker→release→native检查→退出/资源。保留原native业务断言，仅适配新根、标识、路径共享与即时记录。不能现场自检通过后再临时另写一套H1身份拼接。

固定的两个argv元素（exe、absoluteScript）只约束被观察的Node/Electron root。PowerShell observer自身仍保留固定的`-NoProfile/-NonInteractive/-File/-RequestPath`形态；其取消回执复用路径等价/摘要规则，不要求PowerShell也只有两个参数。新控制版本、任务根/marker和证据路径适配属于本卡授权范围，须与所有受影响副本一致。

路径检查的局部正反例至少包括：正反斜杠表示同一绝对文件、带空格及中文的完整参数、正常引号、不同cwd下同一绝对参数；错误脚本、同名不同目录、目标路径只是另一个参数/较长文件名的子串、额外参数、缺失脚本、空/不可解析CommandLine、相对及盘符相对/根相对路径、路径或摘要漂移。构造反例不启动真实目标；同一比较函数需接入现场与H1，不能测试独立替身。

同一局部集合还要拒绝错误ready PID、旧输出目录/marker、错误路径/摘要及缺失回执。它们仅是虚拟回执检查，不启动额外Electron来制造反例。依据可直接查阅 [Node spawn](https://nodejs.org/api/child_process.html#child_processspawncommand-args-options)、[Windows CommandLineToArgvW](https://learn.microsoft.com/en-us/windows/win32/api/shellapi/nf-shellapi-commandlinetoargvw) 和 [Path.GetFullPath](https://learn.microsoft.com/en-us/dotnet/api/system.io.path.getfullpath)；仅使用当前固定范围所需能力。

纯工具开发阶段允许最多30分钟、最多3轮局部回归。此阶段仅虚拟输入/受控临时文件和parser调用，不导入产品、不启动Electron，不接触密文。保留首轮和后续结果、代码差异；已证明未受影响的12项旧分类检查只引用。语法/参数/记录schema与全部路径边界通过后再冻结现场及H1源码。该额度不是重新运行产品失败的授权。

## 现场前置与不变的动态额度

冻结后仅一次Node控制器现场自检，核实其实际脚本参数与完整identity/resources查询。observer单调用最多8秒，现场controller沿用20秒总预算；异步即时记录、退出码/信号/安全expected/actual、成功空结果与unknown区分保持。任何调用都受剩余总时间裁剪，不能用同步查询阻塞截止。

如果这次现场自检出现**已证实的纯目标前工具配置/记录错误**，可保留原材料后仅一次更正和受影响自检；产品/辅助仍不得已启动，不能改安全谓词、预期或时限。未知错误、权限失败、资源不明不适用。原R9/R9-R1更正均保持已使用，不追溯改写。正式目标启动后禁止修后重跑。

该更正如影响共享身份逻辑，必须同次同步并重新冻结全部受影响副本，包括H1 controller和native接线；不得只改live自检留下另一套旧规则。原冻结版本仍完整保留。

| 目标 | 系列已用 | 本轮最多剩余 | 系列累计上限 |
| --- | --- | --- | --- |
| 产品EXE | 1（已过W1） | 7 | 8 |
| safeStorage辅助 | 1（旧失败H1） | 4（恢复H1、H2、H3、H4各一次） | 5 |

**本轮不增加产品或辅助额度。** H1恢复仍只可一次；Node/observer工具自检分列，不能冒充产品验收。每产品最多120秒、辅助60秒且预留10秒收口，普通关闭10秒、页面观察5秒等保持原卡。

## 虚拟现场与同任务续验

固定受验根继续为 `C:/MarisQuitR7/R7-20261014-191500`，原R9输入清单及EXE/asar/lock不变。新虚拟根用 `C:/MarisC12/C12-R9-R2-<时间戳>`。原R9与R9-R1根全部只读；核对 `evidence/r9-r1/original-profile.tsv`（63项、SHA-256 `575f132e0bc44a949391c9ab7c31747e4e21e58fdb8a344dc29a00e6639ce7ee`）和原登记进程退出后，普通复制其中profile-main及continuity.json到新根，逐文件大小/摘要/路径集合匹配、所有深度无reparse。禁止复制失败后改用旧根可写。

前置通过后直接执行H1，再按原R9-R1卡原序继续W2/W3、H2、W4/H3、W5/H4及具备条件的W6/预先说明新增覆盖的保留场景，不另等派发。H1只读，helper userData独立；H2才可在新副本seed有界虚拟老化数据；W2首次持久状态取样前不写设置。相同owner、同请求ID、原生保留/删除后的读回都要实际安全比较，文件存在和密文变化不能代替。

原生UIA只操作已核实owned窗口/按钮；真实chunk只允许实际请求的临时CDP拦截，不改包或反复启动找命中。无权限或明确缺少设备能力保留对应条件未验；安全收口后继续无依赖且已冻结场景。未知所有权/收口、有效来源下业务失败立即停止扩大。

不触碰真实用户数据、外来进程、provider、Docker、OpenClaw、微信V002或系统注销/启动项/主题/多屏。原设备人工清单不要求用户此刻操作。

## 收口

报告区分纯工具开发/现场自检、实际H1和Windows、历史复用与剩余缺口；每次失败保留具体安全ID/expected/actual、阶段与真实退出，不能退回只有错误类型的记录。整项矩阵要求全部完成才passed；副本续启不写为原目录或真实用户迁移验收。

接单/里程碑/阻塞/交付更新本人快照；5分钟以上操作先写下一检查点，至少10分钟心跳。结束复算新起点、旧首次、固定包/依赖及原两份profile，仅四份测试共享文档可变，原文件不回写。最终review/finished或blocked/finished后停止，不自行创建任务或启动其他角色。LAZY-001/UI-02/P4-B最终由总控裁定；前端参考图和模型策略提醒继续保持。
