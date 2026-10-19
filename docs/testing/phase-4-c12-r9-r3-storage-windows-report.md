# P4-C12-R9-R3：同源原生上下文与Windows续验报告

2026-10-18，Asia/Shanghai，独立测试智能体。依据 control `2026-10-18T05:57:00+08:00`、[R9-R3任务卡](../coordination/prompts/p4-c12-r9-r3-storage-windows-tester.md)及原R9/R1业务预期。

**结论：blocked / finished，交总控review。新H1完整7条独立断言通过；随后同任务执行的唯一W2在首次持久设置页面比较中失败。登记P1 `P4-C12-R9-R3-SETTINGS-001`：已保存的深色主题和开启的隐私模式未恢复到续启页面。停止W3、H2及后续Windows场景；产品普通关窗后自然exit0，自有进程、监听和窗口均为0。** 不修改产品、不修后重跑，不宣布P4-B完成。

## 固定输入和实际范围

[接单门禁](../../tests/independent/desktop/evidence/r9-r3/repository-gate.json)：1192/1192原字节匹配，唯一有序、UTF8无BOM/LF、staged=0；起点清单SHA-256为`9b9b0f977fe96900b4d05cf977f222233034fc39f8882a82ff9c2b543e2181f1`。实际接单10:53:24。[起点审计](../../tests/independent/desktop/evidence/r9-r3/start-audit.json)核对构建932、包140、资源67、dist73、依赖12677、执行方证据157；旧R9/R1/R2首次材料68/38/89及R2目标源码9份保持。

固定受验根仍为`C:/MarisQuitR7/R7-20261014-191500`，Node 24.21.0、Electron 44.4.5及依赖不变：

| 对象 | SHA-256 |
| --- | --- |
| Maris.exe | `183758e3b25a5314da8bea157f92ec00385e9ed6e18f42bac1ad679cdd6f6a65` |
| app.asar | `16f45da665693e9b606ffb6b839081a48fa6ed4ae3e4995b403f57237118aed3` |
| pnpm-lock.yaml | `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |

新虚拟现场`C:/MarisC12/C12-R9-R3-20261018-105500`。14个旧登记进程实例已退出后，核对marker、路径边界和无reparse，普通复制原R9的profile-main与continuity.json；[63项副本回执](../../tests/independent/desktop/evidence/r9-r3/profile-copy.json)证明大小、摘要和完整路径库存一致。三个旧现场全部只读。这是**W1结束后的同内容虚拟profile副本续启**，不是原目录原地恢复或真实用户迁移。全程仅虚拟数据。

| 集合 | 本轮结果 | 不扩大之处 |
| --- | --- | --- |
| 纯工具局部第1轮 | 30/30 passed，真实Node exit0 | 虚拟JSON/密文替身；Electron和真实加解密调用0 |
| H1 | 7/7 passed；helper/controller exit0 | 当前Windows、当前复制的虚拟owner/outbox |
| W2 | 8条比较passed、4条failed；场景failed | 四条失败来自同一次首样，不是四次重试 |
| W3、H2、W4/H3、W5/H4、W6及保留场景 | not_run | 有效产品比较失败后立即停止扩展 |
| R9独立退出8节点/235比较、48开发兼容、W1 62比较 | 历史引用 | 不重跑，不计本轮通过 |
| R2路径38项、现场Node门禁；旧模块13、冷入口B、完整恢复集合 | 历史引用 | 不重跑，未以历史身份代签新PID |

## 工具修正与冻结

新[r9-r3-storage.cjs](../../tests/independent/desktop/r9-r3-storage.cjs)同时用于局部检查和实际H1，复用原R2 identity/observation/parser/observer，原文件保持。每个helper必须全新；spawn前仅把新产品副本的完整Local State原字节复制进helper，核验JSON、必要字段、文件大小/摘要、内存字段相等及源文件保持。没有导出、解密或重新构造key，仓库不保存Local State原文。

辅助顶层同步绑定userData与sessionData，早于ready；ready和业务后核对实际双路径及来源加密字段。spawn前要求完整字节相等；ready后允许无关字段自然变化。helper不导入产品main、OwnerSecretStore或修复逻辑，H1不seed，不把helper配置回写产品。

原生操作拆成上下文、availability、owner读取/解密/解析/比较、continuity读取/解析、outbox读取/解密/解析/比较、baseline和result写入。每阶段fsync保存enter与terminal；错误仅保存安全阶段、枚举name/code，不保存原始message/stack/cause或解密对象。已知原生错误分类依据[Electron 44.4.5固定safeStorage源码](https://raw.githubusercontent.com/electron/electron/v44.4.5/shell/browser/api/electron_api_safe_storage.cc)；不能匹配的错误为unknown。控制器先收集已落盘原生首错，再判断真实退出码；结果写入失败另有安全终止回执。

[唯一局部轮结果](../../tests/independent/desktop/evidence/r9-r3/local-round1/result.json)包含30个唯一检查：同源复制及缺失/非法/不同来源拒绝；ready双路径；即时落盘与唯一ID；owner/continuity/outbox读、解密和解析分别失败；schema/continuity失败；非零下结果收集、结果写入失败、保留先前首错及错误码allowlist。故障注入均为虚拟工具检查，不是实际产品失败。[真实进程回执](../../tests/independent/desktop/evidence/r9-r3/local-round1-process.json)为exit0。

纯工具开发10:55:03开始，11:02:38完成并冻结H1全链8份源码，1/3轮，处于30分钟上限内。`local-round1-source/`、`target-first-source/`及清单保存首次版本。W2/W3首样预期、预算与源码在11:10:33冻结，见[Windows计划](../../tests/independent/desktop/evidence/r9-r3/windows-plan.json)、[W2计划](../../tests/independent/desktop/evidence/r9-r3/windows-w2-plan.json)、[5份来源清单](../../tests/independent/desktop/evidence/r9-r3/windows-w2-source.sha256)。W2沿用原R9产品exe/PID/parent/create身份谓词，原R2辅助身份和取消回执语义保持；补充原生操作阶段及明确的监听查询失败传播。没有重跑旧38项或新增现场Node实验。

## H1首次真实结果

H1于11:03:10启动，root3420、controller27404；原生总耗时7456ms。spawn前同源Local State为490字节，安全摘要/字段比较全部通过；本次真实身份、ready及release通过。39个原生阶段enter/terminal配对且唯一，首错null。

| ID | 期望 | 实际 | 结果 |
| --- | --- | --- | --- |
| H1-NATIVE-AVAILABLE | true | true | passed |
| H1-OWNER-SCHEMA | true | true | passed |
| H1-OWNER-READY | true | true | passed |
| H1-OWNER-NO-PLAIN | true | true | passed |
| H1-OUTBOX-COUNT | 1 | 1 | passed |
| H1-OUTBOX-CONTINUITY | true | true | passed |
| H1-OUTBOX-NO-PLAIN | true | true | passed |

证据：[native-result](../../tests/independent/desktop/evidence/r9-r3/helper-H1/native-result.json)、[分段记录](../../tests/independent/desktop/evidence/r9-r3/helper-H1/native-stages.jsonl)、[独立收集回执](../../tests/independent/desktop/evidence/r9-r3/helper-H1/native-collection.json)、[进程与资源](../../tests/independent/desktop/evidence/r9-r3/helper-H1/process.json)。helper及controller实际exit0，无forced，剩余owned/listener/window均0，H1前后产品副本63项保持。

基线只记录稳定owner身份摘要、draft/event/payload摘要及数量，未要求可轮换refreshToken相等。H1通过证明这次同源辅助读取成立；**不能反证旧R9/R2 operation_error的精确抛错阶段或唯一原因**。H2跨产品续启后再次比对稳定owner/session仍未执行。

## W2首次失败与最小复现

**P4-C12-R9-R3-SETTINGS-001，建议严重级别P1。** 已持久选择的隐私开关和主题没有进入续启的Shell状态。隐私开关默认为关闭构成隐私意图丢失风险；本轮使用虚拟内容，未验证真实金额/持仓展示，不声称已经泄露真实个人数据。主题子项映射P4B-CMP-06，矩阵原风险P2保持不改；缺陷综合分级P1提交总控裁定。

复现前置：固定R7包、原W1同内容63项虚拟副本、H1成功；device-settings保存theme=dark、privacyMode=true、closePolicy=quit、closeHintShown=false。直接启动固定EXE，等待受验实例的Host online/authenticated及Shell/日常页ready；在任何设置写入前读取一次真实页面dataset与主题select/隐私checkbox。

实际19:32:50启动，root14764、controller19684。owned/CDP身份通过，首样时间19:32:59.008；页面Shell与日常页均存在、document complete。首样记录settingsWritesBeforeSample=0、settingsBytesUnchanged=true，排除本次测试先重写设置掩盖问题。

| ID | 期望 | 实际 | 结果 |
| --- | --- | --- | --- |
| W2-STORED-THEME | dark | dark | passed |
| W2-STORED-PRIVACY | true | true | passed |
| W2-STORED-CLOSE-POLICY | quit | quit | passed |
| W2-STORED-HINT | false | false | passed |
| W2-CONTINUITY-FIXTURE | true | true | passed |
| W2-OWN-ROOT | true | true | passed |
| W2-CDP-OWNED | true | true | passed |
| W2-PAGE-READY | true | true | passed |
| **W2-PERSISTED-UI-THEME** | **dark** | **system** | **failed，首错** |
| W2-PERSISTED-UI-PRIVACY | on | off | failed，同次首样 |
| W2-PERSISTED-THEME-CONTROL | dark | system | failed，同次首样 |
| W2-PERSISTED-PRIVACY-CONTROL | true | false | failed，同次首样 |

[首次结果](../../tests/independent/desktop/evidence/r9-r3/windows-W2/result.json)与[即时journal](../../tests/independent/desktop/evidence/r9-r3/windows-W2/journal.jsonl)永久保留；安全首错为`stage=first_persisted_ui / id=W2-PERSISTED-UI-THEME / name=Error / code=comparison_failed`。四个比较全部使用已取得的同一次样本，首个有效失败后没有新业务操作、再次取样或重启。W2-PERSISTED-REQUEST-ID及W3等后续断言not_run，不能由continuity摘要一致推断同ID重提成功。

只读源码定位：[module-routes.tsx](../../apps/desktop/src/renderer/module-routes.tsx)的DesktopApp第100—101行将theme/privacy初始化为system/false；第168—170行只在交互回调更新并保存设置。本轮读取的该组件没有启动时恢复这些设置的路径。这与实际首样一致，是返修定位线索；测试方没有修改实现或把源码推断代替界面证据。冻结依据为[IF-003 §11—13](../phase-4-interface-freeze-003.md)及本轮W2首次持久状态要求。

## 失败后普通关闭与预算

使用原已保存quit策略向已核实的唯一主窗口发WM_CLOSE，没有退出计时器。19:32:59.973926发出，19:33:00.341收到root自然exit0，约367ms；19:33:03.401资源查询成功，owned/listener/window均0，处于10秒关闭观察上限。controller实际exit1正确保留失败。四次OS observer分别实际exit0、无timeout；W2整体约12800ms，未超120秒。cleanupError=null、forced=false。

阶段记录明确：root identity、进程/监听/窗口查询及close操作成功；后代进程自己的退出码没有捕获，不能由root0推导，只证明登记实例最终不存在。窗口枚举使用既有R9实现；没有把未执行的Tray/原生提示按钮能力写为通过。原始stdout/stderr仅留本轮外部根，仓库仅保存大小、摘要和安全结构化证据。

| 范围 | 本轮实际 / 上限 | R9系列累计 / 上限 |
| --- | --- | --- |
| 产品EXE | **1 / 7** | **2 / 8** |
| safeStorage辅助 | **1 / 4** | **3 / 6** |
| 新H1恢复 | **1 / 1，已通过** | 原R9及R2失败各1次仍计入累计 |
| 纯工具局部检查 | 1 / 3轮 | 30项；旧38项及现场Node新增0次 |
| 真实chunk注入 / H2老化seed | 0 / 0次 | 未执行 |

11:10冻结到19:32实际运行存在执行控制间隔，没有可验证的连续心跳；不追溯补造、不把这段间隔计作产品运行或新增工具开发。19:35恢复取得最终会话回执后立即登记阻塞；此后只做报告、哈希和只读检查，不再启动目标。

## 24项矩阵映射及未验证条件

B更新为**1 passed、2 failed、19 blocked、2 not_run**。仅CMP-06由not_run变failed，依据是明确的主题恢复子条件失败；其透明降级、OS主题/high contrast、对比、动效和颜色等其余子条件仍未执行。隐私恢复失败独立登记，但没有据此补签CMP-05多屏/金额隐藏等实际未运行的人工条件。UI-02/LAZY-001原失败保持。

| ID（P4B-） | 整项状态 | 本轮增量与缺口 |
| --- | --- | --- |
| SEC-01 | blocked | 本轮非完整renderer隔离检查，历史局部证据保持 |
| SEC-02 | blocked | 完整CSP/导航/外链组合未齐 |
| SEC-03 | blocked | 旧窄bridge局部证据保持，工具修正不替代完整审计 |
| SEC-04 | blocked | sender/origin/channel和非法输入完整组合未齐 |
| SEC-05 | blocked | H1原生owner/outbox读取及非明文通过；跨产品session、renderer存储/内存和日志边界未齐 |
| SEC-06 | blocked | nonce/origin/token/远程组合未齐 |
| SEC-07 | blocked | HTML/RTL/长文本布局完整组合未齐 |
| SEC-08 | blocked | 工具分段脱敏通过不等同产品日志/错误信息完整验收 |
| SUP-01 | blocked | 本次自有资源正常清理；外来/手工后端对照未齐 |
| SUP-02 | blocked | 本次online不覆盖端口冲突、坏ready、启动超时 |
| SUP-03 | blocked | W6未执行，真实崩溃/退避仍缺 |
| SUP-04 | blocked | W3未启动，第二实例及external_dev未验 |
| SUP-05 | blocked | W2清理正常；不重复W1已关范围，强关/注销/锁/外来对照仍缺 |
| SUP-06 | blocked | H1原始outbox 1项及continuity通过；跨重启重提同ID、老化保留/删除、一次提交GET未验 |
| UI-01 | passed | 保持既有独立接受，未重跑模块集合 |
| UI-02 | failed | LAZY-001保持；本轮无chunk/retry/session结果 |
| UI-03 | blocked | 无新增真实export/CI漂移结果 |
| UI-04 | blocked | 旧注册器通过集合保持，不扩大整项结论 |
| CMP-01 | blocked | 不以页面存在替代完整毛毛状态流/第二contribution |
| CMP-02 | blocked | 首次提示、Tray恢复和第二次关闭未到达 |
| CMP-03 | blocked | quit清理通过；hide/ask/cancel/Tray尚未执行 |
| CMP-04 | not_run | 没有操作OS启动项 |
| CMP-05 | not_run | 隐私恢复开关失败另有证据；多屏/DPI/位置/全屏/键盘和金额隐藏人工条件未执行 |
| CMP-06 | failed | 已保存dark续启变system；其余透明/OS主题/对比/动效/颜色条件未执行 |

不要求用户此刻点击；未测试真实DeepSeek、OpenClaw、微信、Docker、真实财务、系统注销、开机启动、系统时钟/主题/网络/安全设置。没有启动其他角色，真正前端阶段的参考图及模型分工仍由总控按既定门禁提醒。

## 交接与完整性

H1本轮原生读取阻断已经消除；新的产品设置恢复失败需要总控定级、派发最小返修并另授独立复验快照与启动额度。建议保持此次四条界面期望，先复验同内容副本首次启动；通过后才继续既定W2/W3→H2→W4/H3→W5/H4→W6。测试方没有修改产品或派发其他角色。

终点审计、首次材料和最终交付摘要在本报告末尾追加实际结果；旧失败、旧现场、原报告前缀与全部未验证条件保留。本任务最终blocked / finished供review，不将缺陷收口写作项目complete。

## 最终审计与交付

[终点审计](../../tests/independent/desktop/evidence/r9-r3/end-audit.json)于19:42:18—19:42:35执行，真实exit0，见[退出回执](../../tests/independent/desktop/evidence/r9-r3/end-audit-process.json)。1192起点中1188项原字节保持，变化仅授权的tester、主报告、人工清单和矩阵四份共享文档。旧R9/R1/R2交付分别75/79、55/59、110/114保持，差异同为这四份共享文档；旧首次68/68、38/38、89/89以及R2目标源码9/9完整保持。

固定构建932、包140、资源67、dist73、依赖12677、执行方证据157全部匹配，要求完整库存的集合也匹配。三个旧虚拟profile各63项大小、摘要、库存及无reparse核对通过。新H1只读阶段的63项保持由当时回执证明；W2运行后的新副本为65项，新增2项日志、13项文件字节变化、0项删除，详见[new-profile-after-W2.tsv](../../tests/independent/desktop/evidence/r9-r3/new-profile-after-W2.tsv)。这些变化在授权的产品续启后独立记录，不要求新运行现场永久等同旧字节；device-settings和continuity仍保持。owner/outbox和数据库变化不被哈希审计解释为内容正确，H2未运行，不补签跨重启稳定身份或同ID结论。

局部首次源码归档5份、H1首次源码归档及运行来源8份、W2首次源码归档及运行来源5份全部匹配。首批材料148/148复核，清单SHA-256为`ee47682828cf4341c6cf78b7330446ec5329186998eea42d635ee4f7b1ea8e87`。原报告/人工清单的旧字节前缀完整；矩阵120唯一ID、12列、原预期及A/C/D保持，B计数1/2/19/2。只读diff检查通过、staged=0、Git写操作0。

最终[交付清单](../../tests/independent/desktop/evidence/r9-r3/delivery.sha256)绑定本轮测试工具、首次与终点证据、报告及四份共享文档；[交付验证](../../tests/independent/desktop/evidence/r9-r3/delivery-verification.json)记录实际数量和摘要。清单不包含自身与验证回执，避免循环引用。终点审计记录当时tester摘要，最终清单另绑定最后finished日志，不回写旧审计。最终blocked / finished供总控review，新增缺陷、LAZY-001及剩余Windows未闭环；无再次启动或继续其他角色的授权推断。
