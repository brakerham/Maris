# P4-C12-R9-R2：脚本路径身份与H1恢复增量报告

2026-10-18，Asia/Shanghai，测试智能体。绑定control `2026-10-17T09:03:00+08:00`和[R9-R2任务卡](../coordination/prompts/p4-c12-r9-r2-path-windows-tester.md)。实际动态执行在2026-10-17 23:40，报告收尾跨日。

**结论：blocked / finished，提交总控review。共享路径身份工具、唯一现场门禁及H1的真实身份/ready/release链通过；H1原生操作在availability通过后异常退出，owner/outbox基线未取得。按正式目标启动后的停止规则，不继续W2等场景、不修后重跑。** 没有新增已证实产品缺陷，也不将本轮H1异常倒写为旧H1原因。

## 结果分层与固定输入

| 集合 | 本轮实际结果 | 边界 |
| --- | --- | --- |
| 新固定起点 | 1077/1077匹配、唯一路径有序、UTF8无BOM/LF、staged0 | 接单前完成 |
| 纯工具局部开发第1轮 | 36/36通过 | 真Windows parser + 虚拟参数/临时文件/回执；无Electron |
| 纯工具局部开发第2轮 | 38/38通过 | 补足取消回执实际父PID；最终38唯一检查，不将两轮相加 |
| 现场Node工具门禁 | 1次passed，controller exit0；无更正 | 实际脚本参数、身份和resources查询；不是产品验收 |
| H1真实辅助 | 1次blocked，helper/controller exit1 | 原生availability 1 passed，其余6条业务比较not_run |
| W2/W3、H2、W4/H3、W5/H4、W6及保留额度 | not_run | H1未通过后停止 |
| R9 8节点/235比较、48开发兼容、W1 62比较 | 历史复用 | 未重跑、未计本轮通过 |

[1077起点回执](../../tests/independent/desktop/evidence/r9-r2/repository-gate.json)清单摘要：`c3d6731a6dc27062f2208e48c58c5aec3298675547d2ffa5dcca021b99d9b6e7`。接单后完整[start-audit](../../tests/independent/desktop/evidence/r9-r2/start-audit.json)复算：构建932、产物140、资源67、dist73、依赖12677、执行方证据157全部匹配；包/资源/dist/依赖实际路径库存一致。旧R9 68份首次、R9-R1 38份首次保持，旧交付仅本人状态发生接单授权变化。

唯一受验根 `C:/MarisQuitR7/R7-20261014-191500`。EXE `183758e3b25a5314da8bea157f92ec00385e9ed6e18f42bac1ad679cdd6f6a65`、asar `16f45da665693e9b606ffb6b839081a48fa6ed4ae3e4995b403f57237118aed3`、lock `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`保持。工具/依赖沿用固定版本，未安装、下载、构建或打包。

## 共享身份检查与局部开发

新[r9-r2-identity.cjs](../../tests/independent/desktop/r9-r2-identity.cjs)是局部案例、现场root、H1 root、native ready和observer取消回执共同使用的完整路径/文件/回执检查。现场控制器由[r9-r2-launch-live.mjs](../../tests/independent/desktop/r9-r2-launch-live.mjs)直接spawn固定Node，脚本是启动描述生成的唯一绝对参数；H1直接spawn固定stock Electron，使用同一描述生成实际参数和observer请求。

实际CIM CommandLine经共享[r9-r2-parser.ps1](../../tests/independent/desktop/r9-r2-parser.ps1)的Windows API取得参数数组，冻结为exe+absoluteScript两元素；不做整串Contains、空格split或后缀匹配。只规范化提取的脚本参数，拒绝相对/盘符相对/根相对、UNC、设备前缀、短名和大小写别名；核对完整路径、边界、reparse与文件摘要，同内容另一条路径仍拒绝。parser分配的内存于finally释放，依据[CommandLineToArgvW文档](https://learn.microsoft.com/en-us/windows/win32/api/shellapi/nf-shellapi-commandlinetoargvw)。启动使用参数数组与shell:false，异步捕获输出和退出，依据[Node child_process文档](https://nodejs.org/api/child_process.html#child_processspawncommand-args-options)；没有因文档最新版本改变固定Node版本。

局部覆盖：正反斜杠、中文/空格/引号、不同cwd、错误脚本/同名不同目录、目标仅出现在其他参数或较长文件名、额外/缺失参数、空/NUL命令行、非法相对路径、路径或摘要漂移、错误ready PID/旧目录/marker/path/hash/callID/缺失回执、取消回执的陈旧时间和父PID、root父进程及reparse拒绝。两个局部parser子进程与Node控制器实际exit0。语法与参数检查通过。

首轮、第二轮源码和结果分开保留：`local-round1-source/`、`local-round2-source/`及各自manifest；[第二轮差异](../../tests/independent/desktop/evidence/r9-r2/local-round2.diff)记录工具完善。2/3轮在30分钟限额内完成，无局部失败、无Electron试跑，不触碰密文。旧12条分类检查只引用R9-R1，不重跑。

现场前已经写好完整[H1控制器](../../tests/independent/desktop/r9-r2-h1-run.mjs)：绝对脚本启动→observer实际argv身份→ready PID/path/hash/marker→release→native比较→真实退出→资源/只读摘要。9份运行源码于23:39:38冻结在[target-source.sha256](../../tests/independent/desktop/evidence/r9-r2/target-source.sha256)及`target-first-source/`，包含live launcher/controller、H1 controller/native与共享依赖；不是现场成功后再另写H1。旧源码保持，[target-changes.diff](../../tests/independent/desktop/evidence/r9-r2/target-changes.diff)保留主要适配。

## 唯一现场前置

[现场结果](../../tests/independent/desktop/evidence/r9-r2/live/result.json)、[controller实际退出](../../tests/independent/desktop/evidence/r9-r2/live-controller.json)和即时journal：Node PID27508，父31636，实际exit0/signal null，未forced；controller约6.660秒，外层捕获6.750秒，小于20秒。identity与resources两次observer均真实exit0、无timeout。

两次实际root的exe、父PID、创建时间、完整两个argv、脚本完整路径/摘要、无reparse和任务marker均为true；每次call ID和stage enter/terminal独立保存。resources实际进程/窗口/监听查询成功；此时Node和本次观察器正在运行，不能把其存在写作资源应为0。raw stdout/stderr只留新外部根，仓库只存安全比较、owned登记、字节数和摘要。现场更正0/1；不使用R9-R1已耗更正额度，也不修改旧失败。

## H1实际首次结果

H1 root **22544**，父controller **31700**；启动时间`2026-10-17T15:40:46.5419100Z`。总耗时**8207ms**，辅助60秒总限和至少10秒收口预留保持。入口与helper userData独立于产品profile；没有产品main导入。

| ID/阶段 | 期望 | 实际 |
| --- | --- | --- |
| H1-OBS-1 root身份 | 全部true | exe/PID/parent/create/两个argv/path/hash/reparse/marker全部true |
| H1-READY | 本次PID/脚本/摘要/marker/输出/call ID匹配 | 全部true，ready PID22544 |
| H1-RELEASE | 身份通过后才release | `15:40:50.957Z`实际release |
| **H1-NATIVE-AVAILABLE** | **true** | **true / passed** |
| H1-OWNER-SCHEMA | true | 未取得actual / not_run |
| H1-OWNER-READY | true | 未取得actual / not_run |
| H1-OWNER-NO-PLAIN | true | 未取得actual / not_run |
| H1-OUTBOX-COUNT | 1 | 未取得actual / not_run |
| H1-OUTBOX-CONTINUITY | true | 未取得actual / not_run |
| H1-OUTBOX-NO-PLAIN | true | 未取得actual / not_run |
| H1原生总结果 | passed=true / 正常exit0 | **passed=false / exit1** |
| H1-PROFILE-UNCHANGED | true | true |
| 最终owned / listeners / windows | 0 / 0 / 0 | 0 / 0 / 0，查询成功 |

[native-result.json](../../tests/independent/desktop/evidence/r9-r2/helper-H1/native-result.json)保留`errorKind=Error / code=operation_error`；[native-checks](../../tests/independent/desktop/evidence/r9-r2/helper-H1/native-checks.jsonl)只包含availability的enter/terminal。helper于`15:40:50.994Z`自然exit1，controller实际exit1。自然结束仅表示未强杀，不是成功退出0。

**本次native记录仍有缺口**：沿用的native catch没有为owner文件读取、decryptString和JSON.parse分别记录enter/terminal，也未保存允许列举的原生错误码。只能将失败区间界定在availability之后、OWNER-SCHEMA之前；不能确定具体抛错操作。现存文件及其235字节/hash只能证明副本内容完整，不能补写“已读成功”或“已解密失败”。源代码只读核对表明产品SecureStore使用原始encryptString缓冲区，没有证据把问题归为产品损坏、设备不支持或某个密钥上下文。

最小复现是本次冻结H1源与同内容虚拟profile：身份/ready通过后release，availability=true，随后operation_error且exit1，未产生owner/outbox基线。严重级别为**独立验收阻断，产品缺陷未定级**。详见[首次只读分析](../../tests/independent/desktop/evidence/r9-r2/h1-first-analysis.json)。目标已经启动，不能用尚未使用的现场工具更正额度重跑；没有修native后再试，也没有填造缺失错误码。

清理observer H1-OBS-2真实exit0，各process/type/window/listener/JSON阶段均success，最终owned0、listeners0、windows0。无强制结束、无timeout、cleanupError=null。未知子进程自身退出码不由root1推导；仅登记它们随后已不存在。stdout2bytes、stderr0bytes，未保存敏感明文至仓库。

## 虚拟现场、预算与停止

新根 `C:/MarisC12/C12-R9-R2-20261017-233500`。旧R9及R9-R1两份profile均只读核对，63项清单SHA-256为`575f132e0bc44a949391c9ab7c31747e4e21e58fdb8a344dc29a00e6639ce7ee`。旧登记进程已退出后普通复制profile-main和continuity.json；所有深度无reparse，逐文件大小、摘要及路径集合一致，保留数据库边文件。[profile-copy.json](../../tests/independent/desktop/evidence/r9-r2/profile-copy.json)记录边界。

这是**W1关闭后的同内容虚拟profile副本**，产品续启仍not_run；不是原目录原地续启或真实用户迁移。H1只读条件下新副本63项字节保持，未seed、未改设置；没有取得owner/session稳定摘要和同请求ID重启结论。H2及H3/H4未执行，不能写成原生保留/删除已验。

| 范围 | 本轮实际 / 上限 | R9系列累计 / 上限 |
| --- | --- | --- |
| 固定产品EXE | **0 / 7** | **1 / 8** |
| safeStorage辅助 | **1 / 4** | **2 / 5** |
| H1恢复 | **1 / 1** | 旧失败H1另计并保留 |
| Node现场工具 | 1次 | 单列，不算产品/辅助 |
| 现场目标前更正 | 0 / 1 | 不可用于已启动H1失败 |

[预算账本](../../tests/independent/desktop/evidence/r9-r2/budget-ledger.json)保留旧R9/R9-R1各一次更正，没有重置历史。W2/W3、H2、W4/H3、W5/H4、W6和保留场景均not_run；真实chunk注入0。即使剩余辅助额度存在，也不能重跑H1恢复或越过未知原生失败。

23:40:54目标已完成安全收口，随后仅只读查看首次和冻结源。23:41后至00:10恢复执行可见性期间未新增目标，角色心跳未及时更新的空档如实记入本人日志；不把这段间隔记作H1运行时长，不伪造持续进展。没有旧集合重跑、系统/用户应用操作或后台目标遗留声明之外的扩大结论。

## 24项当前映射

本轮未形成任何整项新通过，B仍**1 passed、1 failed、19 blocked、3 not_run**。矩阵只加B证据备注；120唯一ID、12列、原预期和A/C/D保持。

| ID（P4B-） | 整项状态 | 增量与未验证条件 |
| --- | --- | --- |
| SEC-01 | blocked | 无新产品renderer检查，完整preload/内存边界仍缺 |
| SEC-02 | blocked | 无新产品导航/CSP/外链结果，完整组合仍缺 |
| SEC-03 | blocked | 历史窄bridge保持；工具身份检查不替代preload审计 |
| SEC-04 | blocked | 历史非法IPC保持，sender/origin/channel全组合仍缺 |
| SEC-05 | blocked | 原生availability=true；owner/outbox解密与跨重启session未完成，不能整项通过 |
| SEC-06 | blocked | nonce/origin/token/远程全组合未齐 |
| SEC-07 | blocked | HTML/RTL/长文本/布局完整组合未齐 |
| SEC-08 | blocked | 工具脱敏回执不替代产品日志/request ID，native分步错误记录仍有缺口 |
| SUP-01 | blocked | 辅助所有权与资源收口成功，不等同产品停止权及外来对照 |
| SUP-02 | blocked | 端口冲突/无ready/启动超时新场景未执行 |
| SUP-03 | blocked | W6未执行，真实崩溃/退避仍缺 |
| SUP-04 | blocked | W2/W3未执行，单实例和external_dev仍缺 |
| SUP-05 | blocked | 原普通关闭限定范围已由总控关闭；强关/注销/锁/外来对照仍缺 |
| SUP-06 | blocked | H1基线未取得，跨重启同ID/老化/一次提交GET未执行 |
| UI-01 | passed | 保持历史独立接受，不重跑 |
| UI-02 | failed | 旧LAZY-001及部分恢复证据保持，真实chunk/retry/session未齐 |
| UI-03 | blocked | 无新增export/CI/编译结果 |
| UI-04 | blocked | 旧注册通过保持，不扩大整项结论 |
| CMP-01 | blocked | 完整毛毛状态流/第二contribution设备条件未齐 |
| CMP-02 | blocked | 真实首次提示/Tray恢复/重复关闭未执行 |
| CMP-03 | blocked | 历史quit保持；真实hide/ask/cancel/Tray未执行 |
| CMP-04 | not_run | OS启动项未操作 |
| CMP-05 | not_run | 多屏/DPI/位置/全屏/键盘完整条件未执行 |
| CMP-06 | not_run | 透明降级/OS主题/对比/减少动效/颜色完整条件未执行 |

未要求用户此刻点击。未操作真实个人数据、外来程序、provider、Docker、OpenClaw、微信、系统注销/启动项/主题/多屏或安全软件；未启动其他角色。

## 交接决定

路径身份这一工具阻断已有真实H1接线证据，旧失败永久保留。下一步需要总控裁定native操作分段观察及读取上下文核对的最小范围、是否另授实际恢复额度；应先补齐安全错误码和操作阶段，再决定后续，不从当前Error推定产品返修。测试方本任务不改产品、不改已冻结工具重跑、不重打包或Git写入。

最终摘要/完整性见交付追加，任务以blocked / finished停止供总控review。LAZY-001/UI-02和P4-B仍由总控裁定。


## 最终完整性与交付

终点审计于2026-10-18 05:40执行并真实exit0：[end-audit.json](../../tests/independent/desktop/evidence/r9-r2/end-audit.json)、[真实退出回执](../../tests/independent/desktop/evidence/r9-r2/end-audit-process.json)。1077项中1073项原字节保持，仅tester、原主报告、人工清单、矩阵四项按授权变化；旧R9交付75/79保持、旧R9-R1交付55/59保持，差异均是同四份共享文档。旧首次68/68与38/38保持，本轮首次材料89/89保持。新现场/H1冻结源码9/9与两个局部源码归档11/11、11/11保持。

固定构建932、包140、资源67、dist73、依赖12677、执行方证据157均匹配。原R9、原R9-R1和本轮副本各63项大小/摘要与profile路径库存匹配。矩阵120唯一ID、12列、原预期和A/C/D保持；主报告/人工清单旧字节前缀完整。本轮未新增整项通过，B为1 passed、1 failed、19 blocked、3 not_run。

只读终点汇总脚本准备时，新增三份profile库存检查的内存文本出现缩进错误，语法检查即失败、未写入该错误源码且未执行审计。首次安全记录保留在[end-audit-preparation-first-error.json](../../tests/independent/desktop/evidence/r9-r2/end-audit-preparation-first-error.json)；修正仅涉及新的只读汇总脚本，随后冻结并执行一次终点审计。没有修改现场/H1冻结源码、重跑工具门禁或目标。

最后登记的00:25检查点没有按时形成终点回执，实际终点审计时间为05:40；该间隔没有可验证的连续心跳，不追溯补造。此前动态目标已于23:40安全结束，此间未新增产品/辅助启动，不把间隔计入动态运行时间。收尾只进行已授权文件整理、哈希与只读Git检查。

最终[delivery.sha256](../../tests/independent/desktop/evidence/r9-r2/delivery.sha256)绑定所有本轮源码、证据、新报告与四份共享文档；[delivery-verification.json](../../tests/independent/desktop/evidence/r9-r2/delivery-verification.json)记录实际条目数、摘要、逐项复核和预算。终点审计记录的是审计时tester摘要，最后交付摘要另绑定本次交付日志及finished状态；旧审计不回写。交付清单不包含自身及其验证回执，避免自引用；无Git写入、staged保持0。

最终为blocked / finished，报告交总控review；H1底层操作原因未验证、剩余Windows未执行，不宣称P4-B完成。
