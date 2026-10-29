# P4-B7-R8-R1-LIFECYCLE 执行记录

交付状态：**blocked / finished**。停止点在产品启动前。本轮 S1、S2 均 not_run，package 0、EXE 0、Electron/safeStorage helper 0。三轮工具开发结束后仍有控制器收口缺口，没有达到全部前置检查通过的条件；驱动作为受阻候选固定，不能作为获准启动版本。

## 授权、起点和文件边界

依据任务卡 docs/coordination/prompts/p4-b7-r8-r1-lifecycle-executor.md，control 版本为 2026-10-21T13:48:00+08:00。10月21日读完 AGENTS、README、项目协调说明、协调README、control、本人状态、任务卡及总控裁定后，复算1370项新起点和历史12项交付，通过后接单。起点清单摘要：

6129ee75453b3db5a2fed9839dbf108de84cd2a08d2c0b57344de7d7683b4a7e

UTF8无BOM、LF、唯一ordinal排序、排除自身和暂存区为空均已核对。本轮只更新executor.md、新增本说明及apps/desktop/b7-r8-r1-lifecycle-source.sha256，共3路径。终点source由1370起点更新executor摘要、加入本说明，形成1371项，排除清单自身。历史另外11项交付保留原字节；旧R8 source自身未改。

旧根 C:/MarisSettingsR8/R8-20261019-103900 全只读。新根 C:/MarisSettingsR8/R8-R1-20261021-143209 创建前核对绝对边界、不存在和reparse。inputs保留原两驱动副本；tools仅含任务工具；evidence保留每轮输入、结果、diff及审计。没有建立新产品profile，也没有复制旧owner/profile。

## 保留的产品结果与固定输入

原R8修复、修复前红灯1failed、定向99、完整19文件217passed、类型/lint、唯一package、7静态和8读取链结果保持，本轮均未重跑。旧S1首次失败及旧S2 not_run保持。R8系列仍package1/1、EXE1/3、helper0。本轮未消耗两次新EXE额度，但不能自行继续使用。

| 固定范围 | 条目 | 起止复算 |
| --- | ---: | --- |
| 旧构建源码 | 1365 | 全匹配 |
| 固定安装包 | 140 | 全匹配 |
| Python资源 | 67 | 全匹配 |
| 旧工具 | 14 | 全匹配 |
| 旧生命周期profile | 63 | 全匹配 |
| 旧证据 | 108 | 全匹配 |

固定EXE SHA-256：c80d27c8e31fa60df91065a770e669a553260cf8f883c55a0a7f83f8a430736b。

固定app.asar SHA-256：05cdad34ba60b59773eebe671156c96260e69354568b9942da59058641f9c0b2。

固定lock SHA-256：5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a。

旧依赖完整审计引用旧根evidence/inputs/final-audit.json，摘要465624f22064e7c9ccb5915932d325254e0dced7c43db5f9f3c779b62941d269。没有重扫或安装全依赖。实际Node、Playwright package/入口、Python和lock共6项起止摘要相同，详见新evidence/start-audit.json、end-audit.json。PowerShell实测7.6.5。

## 工具修复及静态核对

原生身份统一为CIM UTC ticks十进制字符串，JSON/Node不转Number或毫秒日期。root、known、后代、普通关闭和cleanup共用身份比较，PID、parent、path、ticks同时匹配。CIM微秒精度与Process原始100ns时间实测后，仅去掉Process末位100ns作CIM同源比较，不扩大时间匹配窗口。读旧exe/Node与写新profile分别限制。

cleanup在窗口类加载及枚举之前独立执行，重查精确身份后操作Process对象。竞态退出仅在CIM确认已不存在后跳过。runner即时保存已核实身份和root真实退出，原生阶段、错误类型、状态及信号分别保留，firstFailure与cleanupFailure分开。controller与产品退出分别记录。

只读静态核对11组通过：

- 新旧runner完整产品gates块逐字符一致。
- 固定输入读旧根，profile/证据/AppData/TEMP写新根。
- settings键集保持getSnapshot/update。
- S1的seed、真实控件写入、唯一recover仍在S1分支。
- S2要求S1成功、自然0/null、固定包摘要及同profile/文件摘要连续。
- S2无重新seed、设置更新或recover。
- 首个有效页面样本同时记录四项主题/隐私DOM及控件值；失败立即抛出。
- 比较ID唯一，保存expected、actual、时间及passed。
- OS/CDP受剩余预算限制，页面条件最多5秒，普通关闭最多10秒。
- 原生cleanup实际由finally和残留资源分支调用，partial root身份即时消费。
- controller收紧注入失败判据、真实root退出判据和末段记录预算。

**仍未通过的收口检查：** controller在finally的success表达式中直接readFileSync/JSON.parse产品result.json。若文件缺失或损坏，异常可再次逃出finally，跳过控制器结果落盘及句柄释放。此路径仅静态发现，没有启动产品复现。三轮及活动时间已到限，因此没有继续修第四轮或启动S1。这属于工具阻塞，不能归为本轮产品缺陷。

## 执行方工具自检

纯时间15个唯一断言通过，覆盖原7位UTC、等价+08、typed DateTime/DateTimeOffset、JSON往返、非法值及1tick拒绝。实际Node往返共有25个唯一断言，包含上述15项及10项真实身份断言；第二/三轮两类fixture各25/25，重复不累计成100个独立案例。实际CIM/Process精度、root/known、斜杠等价、不同PID/parent/path/ticks拒绝均有回执。

| 轮次/夹具 | 结果 | 毫秒 | root真实退出code/signal | 末态进程 |
| --- | --- | ---: | --- | --- |
| 1 / natural | failed | 2326 | unknown | 首次unknown |
| 1 / failure | not_run | — | — | — |
| 2 / natural | passed | 8212 | 0/null | 0 |
| 2 / failure | passed，预期错误及清理 | 6831 | 4294967295/null | 0 |
| 3 / natural | passed | 8177 | 0/null | 0 |
| 3 / failure | passed，预期错误及清理 | 6839 | 4294967295/null | 0 |

合计5次普通夹具运行，4通过、1失败。强制结束只用于失败工具夹具，绝不算产品正常退出。失败夹具保留窗口首错、等待超时注入记录、精确停止回执及未知子退出码；父对照存活。没有加载Electron、Maris、Python Host或safeStorage。每轮输入及摘要在tool-round-1/2/3，原result不覆盖。

第一轮误拒正常conhost后代，具体为fixture_descendant_path_rejected；后续cleanup因root_creation_missing失败。原root退出未回收记录，保持unknown，不能用后续不存在倒推自然0。第二轮去掉“全部后代必须Node”的错误限制，保留根固定路径、已核实父链、创建时间和精确身份；第三轮受影响复验通过。整体前置门禁仍因上述finally缺口为blocked。

活动开发预算此前预留约5分钟、10月23日约17分钟，10月26日续接约8分钟上限；中断及审批等待不计持续开发。三轮全部使用后不再新增修复/fixture。末轮结果回收后仅做只读审计、文档和摘要收口，没有用新任务名规避轮次。

## 失败、警告与未验证项

- 初次审计使用猜测的Playwright browserType.js路径，FileNotFoundError保留；查看实际布局后绑定真实index.js。
- 保存审计错误时漏导入json，NameError保留；后续start-audit成功不抹去前序错误。
- runner辅助生成器替换断言失败未落盘，由辅助报告；输入原件保留。辅助后因模型额度中断，未计完整交付，父接回。
- 第三轮写入自动审批超时，命令未执行；按工具允许唯一重试获准。不是安全策略否决。重试中GBK读runner失败，controller已落盘而runner未改；明确UTF8后保存，准备错误保留。
- 第一轮实际观察及cleanup失败保留；第二/三轮窗口注入错误为预期条件。第一轮实际退出unknown，不补造0。
- 最终静态发现的finally结果读取缺口未修；没有启动产品验证该路径。
- 生成交付文本的一次工具调用因JavaScript语法错误未执行，改用文件补丁保存说明；不影响冻结候选字节。
- 首次终点清单已生成，但复读时默认GBK遇中文路径失败；保留该首版清单和错误，清单复算统一显式UTF8后续完。没有重跑工具夹具或改候选驱动。
- Git只读有全局ignore权限警告；原有.claude及.pnpm-store未修改，暂存区为空。
- S1/S2真实页面、保存、recover、WM_CLOSE及同profile恢复均not_run；后台与页面均无本轮产品成功证据。旧217项结果不代表生命周期通过。

## 当前资源与可复算交付

2026-10-26 20:56只读核对：任务随机标记匹配进程0、已核实历史夹具身份当前存活0、自有监听0。产品从未启动，新产品profile不存在。窗口没有独立枚举，原回执ownedWindows=null保留，不能把未测窗口计为实际观测0。第一轮历史实际退出仍unknown。没有额外结束其他进程，没有删除旧或新证据。

外部证据根为C:/MarisSettingsR8/R8-R1-20261021-143209/evidence：

- tool-results-summary.json：逐轮结果及原result摘要。
- static-review.json：11组静态通过和1项未解决阻塞。
- start-audit.json、end-audit.json：固定输入起止核对。
- final-resource-audit.json：当前资源和历史未知范围。
- tools-blocked-candidate.tsv：5份外部工具逐文件SHA-256。
- evidence-manifest.tsv：外部证据逐文件清单，排除自身、delivery-three.sha256和closeout.json，避免自引用。
- delivery-three.sha256：三条仓库交付逐文件SHA-256。
- closeout.json：各清单准确条目数、自身SHA-256、复算结果及停止状态。

清单为UTF8/LF，按相对路径ordinal排序，逐文件摘要基于原始字节；总摘要为清单文件原始字节SHA-256。终点source为1371项，仅3个仓库交付路径。所有原始失败、新候选和差异保存，没有将候选标为可启动的已通过driver。

状态停在blocked / finished，交头脑风暴总控。没有独立验收、Tester/顾问/后续任务或Git写操作。SETTINGS-001、CMP-06、LAZY-001/UI-02和P4-B均不关闭。
