# P4-C12-R9-R1：H1观察工具与剩余Windows增量报告

2026-10-17，Asia/Shanghai，测试智能体。绑定 control `2026-10-16T18:15:00+08:00`、[R9-R1任务卡](../coordination/prompts/p4-c12-r9-r1-h1-windows-tester.md)和R7固定包。

**结论：blocked / finished，提交总控review。目标前现场工具自检在唯一一次工具更正后仍未通过，按卡停止；H1恢复和后续Windows均未启动。没有新增产品失败或产品通过，不把工具问题解释为设备不支持。** 旧H1底层原因继续unknown。已通过的R9独立8节点/235比较、48开发兼容和W1的62比较仅历史引用，未重跑、未累计为本轮通过。

## 接单与固定输入

接单前1017/1017原字节匹配、1017唯一路径、POSIX排序、UTF8无BOM/无CR、staged=0。[起点回执](../../tests/independent/desktop/evidence/r9-r1/repository-gate.json)的清单SHA-256：`e25b1743fe68f1fa0f8166013d3419feffb7d33cc919b3bbc512601fdddb9539`。23:45登记接单后只更改本人状态；外部复核记录见[start-audit.json](../../tests/independent/desktop/evidence/r9-r1/start-audit.json)。

| 固定范围 | 独立原字节结果 |
| --- | --- |
| 构建源码 | 932/932 |
| 产品包 | 140/140，实际文件库存一致 |
| Python资源 | 67/67，清单明确排除另外校验的asar |
| Electron dist | 73/73，三列path/bytes/hash正确读取 |
| 完整依赖 | 12677/12677，实际文件库存一致 |
| 执行方外部证据 | 157/157 |
| 旧R9交付 | 79中78匹配，本人状态为接单授权变化 |
| 旧R9首次材料 | 68/68，不变 |

固定根为 `C:/MarisQuitR7/R7-20261014-191500`。EXE SHA-256为 `183758e3b25a5314da8bea157f92ec00385e9ed6e18f42bac1ad679cdd6f6a65`；asar为 `16f45da665693e9b606ffb6b839081a48fa6ed4ae3e4995b403f57237118aed3`；lock为 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。未运行构建、package、依赖安装或升级。

## 已完成的工具修改及验证边界

新工具位于 `tests/independent/desktop/r9-r1-*`，没有改旧 `r9-quit-*`：

- 将同步observer改为直接spawn、可观察/可取消的异步子进程；调用enter、spawn、真实exit、terminal立即写入并flush。保留唯一call ID、起止/耗时、status/signal、安全error.code/type、stdout/stderr字节数与SHA-256。原始流仅在新的外部任务根。
- identity与resources分离；process query、类型准备、窗口查询、监听查询、JSON输出各有阶段回执。失败不以空数组或0代签，没有SilentlyContinue。
- 单次调用按8秒和当前阶段剩余预算取较小值；timeout取消需要本次observer PID、路径、脚本摘要、创建时间及call ID回执。工具代码具备这一限制，但本次没有真实timeout或目标清理，不能声称这些现场分支已通过。
- 新native H1副本增加ready PID/运行脚本路径/脚本摘要/marker及具ID的即时比较记录，保持原解密业务断言。**该副本未运行，H1控制器及目标门禁未进入，不能声称ready/release或60秒整体收口已实测通过。**

[虚拟自检](../../tests/independent/desktop/evidence/r9-r1/virtual-tool-selftest.json)：12条分类/列数/安全错误allowlist检查通过，覆盖成功、非零、timeout、parse失败、EACCES、成功空集合、unknown不可当0和schema。更正后另有1条纯虚拟参数检查通过。JS/PowerShell语法检查通过。这些只证明工具的有限静态/虚拟行为，没有导入产品、启动Electron或签收业务。

## 两次现场工具记录与唯一更正

现场只观察固定Node控制器本身，无helper试跑，无release。原始尝试与更正尝试分目录保存，源文件摘要分别在[live-source.sha256](../../tests/independent/desktop/evidence/r9-r1/live-source.sha256)、[live-attempt1-source.sha256](../../tests/independent/desktop/evidence/r9-r1/live-attempt1-source.sha256)。

| 观察 | 首次 | 唯一更正后 |
| --- | --- | --- |
| controller PID / 实际exit | 21836 / 1 | 21664 / 1 |
| observer PID / 实际status / signal | 11032 / 3 / null | 30052 / 3 / null |
| observer耗时 | 688.085ms | 635.269ms |
| stdout / stderr字节 | 147 / 0 | 180 / 0 |
| 首错阶段 | process_query | process_query身份比较 |
| error type / HResult | RuntimeException / -2146233087 | RuntimeException / -2146233087 |
| 安全code | 首次未细分，query_failed | root_identity_mismatch |
| timeout / forced cancellation | false / false | false / false |
| resource阶段 | not_run | not_run |

首次以相对脚本参数启动，观察请求要求绝对脚本路径；静态核对证实字面串不匹配。按卡使用唯一一次目标前工具更正，新副本只改变输出路径/调用ID、绝对脚本参数传递及安全身份比较记录；预期、业务、时限均不改。更正diff和依据在[pretarget-tool-correction.json](../../tests/independent/desktop/evidence/r9-r1/pretarget-tool-correction.json)及同名.diff。

更正后的具体安全值：

| ID / 身份谓词 | 期望 | 实际 |
| --- | --- | --- |
| LIVE1-IDENTITY-EXE / executableEqual | true | true |
| LIVE1-IDENTITY-PARENT / parentEqual | true | true |
| LIVE1-IDENTITY-CREATED / creationWithinStart | true | true |
| **LIVE1-IDENTITY-SCRIPT / scriptArgumentEqual** | **true** | **false** |

[阶段回执](../../tests/independent/desktop/evidence/r9-r1/live-tool-attempt1/LIVE1-identity.stages.jsonl)给出以上实际值。启动参数使用正斜杠绝对路径，观察请求保存Windows反斜杠路径；[只读分析](../../tests/independent/desktop/evidence/r9-r1/tool-stop-analysis.json)确认两者规范化指向同一文件，但ordinal子串比较为false。**已证实失败点是工具脚本身份谓词；静态参数对照指向路径表示差异。** 没有保存全机命令行，不扩大为旧H1根因或产品身份异常。

唯一更正额度1/1已用，未作第二次修正或第三次现场尝试。更正副本仍保留失败状态，没有偷偷修正后重新冻结成功源码。现场工具测试没有到resource query，窗口/监听通道仍未验证；后续H1必须取得新授权的完整前置门禁。

## 虚拟profile与进程边界

原R9根 `C:/MarisC12/C12-R9-QUIT-20261016-011200` 的marker及W1通过来源已核对；旧W1/H1共11条登记对象均未在系统中以相同PID/创建时间/父子身份存活。[旧进程检查](../../tests/independent/desktop/evidence/r9-r1/old-process-check.json)成功后，将其完整profile-main与continuity.json普通复制到新根 `C:/MarisC12/C12-R9-R1-20261017-001500`。

63项逐文件大小与SHA-256相等、边界及所有深度reparse检查通过、复制后原文件不变，见[profile-copy.json](../../tests/independent/desktop/evidence/r9-r1/profile-copy.json)和[original-profile.tsv](../../tests/independent/desktop/evidence/r9-r1/original-profile.tsv)。保留数据库边文件；未解密、未seed、未回写原目录、未使用真实个人数据。

本轮仅准备了“**W1关闭后的同内容虚拟profile副本续启**”条件，产品实际续启not_run；不能写为原目录原地重启或用户迁移验收。新副本也保持原字节，未取得owner/session/native基线，refresh token轮换未观察。H2的老化seed及H3/H4读回均not_run。

两次controller/observer均由真实退出记录确认结束；结束时只读核对这4个PID以及完成审计的2个登记PID均已不存在，未强制结束。[进程终点](../../tests/independent/desktop/evidence/r9-r1/tool-process-end.json)只涵盖这6个ID；没有完整全系统后代清理结论。没有本轮产品、辅助、后端、窗口或监听的验收运行，不能用零启动声称资源验收通过。

前期只读审计会话28781失去可见性且未留下完成回执；保留该事实，不将其记为成功。一次审计进程查询在沙箱中拒绝访问，未操作进程；正式授权外部根准备时查询成功，未把前次拒绝算产品失败。随后只读审计以落盘流/真实exit0完成，没有重启产品或业务测试。接单后的可见性/心跳空档已在本人日志记录；不伪造持续执行。

## 本轮及跨任务预算

[预算账本](../../tests/independent/desktop/evidence/r9-r1/budget-ledger.json)：

| 范围 | 旧R9实际 | 本轮实际 / 本轮上限 | 跨两轮实际 / 上限 |
| --- | --- | --- | --- |
| 产品EXE | 1（W1） | **0 / 7** | **1 / 8** |
| safeStorage辅助 | 1（旧失败H1） | **0 / 4** | **1 / 5** |
| 目标前工具更正 | 旧R9的1次保持 | **1 / 1** | 各任务单列，不重置旧消耗 |

2次Node现场工具控制器不是产品或safeStorage辅助启动。真实chunk注入0。H1恢复、W2/W3、H2、W4/H3、W5/H4、W6和有条件保留额度全为not_run；没有消耗H1恢复额度，也没有因额度尚余越过停止条件。

## 24项当前映射

本轮没有新增业务验收证据。矩阵仍为 **1 passed、1 failed、19 blocked、3 not_run**；仅增加本轮B证据备注，120个唯一ID、12列、原预期与A/C/D保持。以下历史证据只引用，不重新执行。

| ID（P4B-） | 整项状态 | 本轮增量及仍缺条件 |
| --- | --- | --- |
| SEC-01 | blocked | 无新增；完整非枚举/preload及内存边界仍缺 |
| SEC-02 | blocked | 无新增；完整导航、data/javascript及批准外链仍缺 |
| SEC-03 | blocked | 历史窄bridge证据保留；完整域审计仍缺 |
| SEC-04 | blocked | 历史非法IPC证据保留；sender/origin/未知channel组合仍缺 |
| SEC-05 | blocked | H1未启动，native owner/outbox、session重启及memory/dump仍未验 |
| SEC-06 | blocked | 历史loopback/nonce/auth证据保留；origin/过期access/远程组合仍缺 |
| SEC-07 | blocked | HTML/RTL/长文本与布局完整组合未齐 |
| SEC-08 | blocked | 本轮工具日志脱敏不替代产品日志；完整故障/request ID仍缺 |
| SUP-01 | blocked | 无产品停止权新增证据；伪造PID/外来对照仍缺 |
| SUP-02 | blocked | 无新增；端口冲突/无ready/启动超时仍缺 |
| SUP-03 | blocked | W6未启动，真实崩溃/退避仍缺 |
| SUP-04 | blocked | W2/W3未启动，单实例及external_dev仍缺 |
| SUP-05 | blocked | 总控已关闭普通主窗口退出缺陷；强关/注销/锁/对照仍缺 |
| SUP-06 | blocked | 只有同内容副本，不能证明跨重启同ID；H1/H2/真实老化/一次提交GET仍缺 |
| UI-01 | passed | 保持已接受的模块独立结果，不重跑 |
| UI-02 | failed | 旧LAZY-001证据及历史部分恢复保持；真实chunk命中/retry/session仍缺 |
| UI-03 | blocked | 无新增；不重跑真实export/CI/编译 |
| UI-04 | blocked | 历史注册证据保持；不扩大为整项通过 |
| CMP-01 | blocked | 完整毛毛状态流/第二contribution设备条件未齐 |
| CMP-02 | blocked | 真实首次提示/Tray恢复/重复关闭not_run |
| CMP-03 | blocked | 历史quit通过保持；真实hide/ask/cancel/Tray未执行 |
| CMP-04 | not_run | OS启动项未操作，仍为人工条件 |
| CMP-05 | not_run | 多屏/DPI/拔屏/位置/全屏/键盘完整条件未执行 |
| CMP-06 | not_run | 透明降级/主题/对比/减少动效/颜色完整设备条件未执行 |

未请求用户立即点击、扫码或调整系统。未运行OS注销/重启、启动项/主题/多屏、安全软件、Docker、OpenClaw、微信、真实provider，也未启动其他角色。

## 停止与交接

最小复现属于测试工具：以正斜杠绝对脚本参数启动固定Node；observer将脚本路径规范化为Windows反斜杠后，对原CommandLine做字面Contains。期望四身份条件均true，实际前三true/脚本false，observer3/controller1。严重级别：**验收工具阻断，不定级产品缺陷**。首次与唯一更正材料均保留，不修改产品或再运行目标。

需要总控决定的最小问题：是否另授一次只修脚本参数身份绑定的工具门禁及受影响自检；应保留严格的实际运行路径验证，不能仅因规范化同路径就跳过真实身份核验。待工具与资源查询门禁通过，才可使用未消耗的H1恢复额度并沿原计划继续。当前不需要用户修改系统或依赖。

终点核对和最终文件摘要见下方交付追加；最终由总控review，不自行续跑、关闭LAZY-001/P4-B、提交或推送Git。

## 终点核对与交付清单

[终点审计](../../tests/independent/desktop/evidence/r9-r1/end-audit.json)通过，审计控制器实际exit0。1017项固定起点中1013原项保持，仅四份授权共享文档变化：`docs/coordination/agents/tester.md`、`docs/testing/phase-4-c12-manual-checklist.md`、`docs/testing/phase-4-c12-windows-shell-report.md`、`docs/testing/phase-4-modular-agent-host-test-matrix.md`。旧R9交付79中75不变/同四份共享变化，旧68份首次材料全部匹配。

外部932构建、140包、67资源、73dist、12677依赖和157执行方证据全部复算一致；包/资源/dist/依赖路径库存一致。原R9 profile和新副本各63/63原字节及路径集合一致。新38份首次材料、两次现场源码与未执行H1/审计源码清单全部匹配。主报告和人工清单旧字节前缀保持；矩阵120唯一ID、12列、原预期、A/C/D字节保持，B仍1passed/1failed/19blocked/3not_run。

只读Git检查staged=0，diff检查exit0，仅有工作区未来换行策略提示，未进行Git写操作。最后身份四谓词的ID表为已有阶段回执的只读投影，不是重新观察或新增测试通过。终点审计时共享文档摘要与最后收口更新分开：最终内容由[delivery.sha256](../../tests/independent/desktop/evidence/r9-r1/delivery.sha256)和[delivery-verification.json](../../tests/independent/desktop/evidence/r9-r1/delivery-verification.json)绑定，不宣称共享文档旧摘要仍全部相等。

所有新材料和虚拟副本保留，没有清理旧现场、删除数据或结束外来进程。任务停在blocked / finished，交总控review，禁止自动进入H1或其他角色。
