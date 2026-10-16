# P4-C12-R9-QUIT 增量独立验收报告

2026-10-16，Asia/Shanghai，测试智能体。绑定 control `2026-10-16T00:51:00+08:00`、[R9任务卡](../coordination/prompts/p4-c12-r9-quit-windows-tester.md)和 P4-B7-R7-QUIT 固定新源码、新包与冻结依赖。

**结论：普通主窗口关闭缺陷的独立复验通过，建议总控关闭 QUIT-001 的该缺陷范围；剩余 Windows 验收因 H1 辅助的未知所有权观察错误停止。交付 blocked / finished，等待总控 review。** 没有新增已证实产品缺陷，没有修改产品、依赖、受验包、其他角色或 Git 状态。

## 实际结果与计数

| 集合 | 实际结果 | 证据口径 |
| --- | --- | --- |
| 固定起点 | 接单前 **937/937** 匹配，staged=0 | 原字节复算；清单摘要 `b1d8090aa0556dd4b08e6efbb718456850783da17acbc701a254a2cf0f43bf9e` |
| 独立退出边界 | **8 passed，235/235 正式比较 passed** | 实际 main + composition + companion + retention；外围 OS/存储/后端可控；一次 CLI |
| 必要开发兼容 | **5 文件、48 passed** | 19 main-quit + 1 composition-root + 14 outbox-retention + 13 supervisor-outbox + 1 window-lifecycle；一次 CLI，单列执行方测试 |
| 新包 Windows W1 | **1 场景 passed，62/62 比较 passed** | 继承旧测试方 W1 的公开前置与原退出断言，增加资源和期限观察；不是 62 个独立测试 |
| H1 启动前首次 | 清单列读取工具错误，未启动目标 | 实际摘要匹配；使用本卡唯一一次纯工具更正，新副本保留最小 diff |
| H1 实际辅助首次 | **blocked；unknown observer failure** | 在 release/解密之前，所有权观察错误；安全定向强制收口成功，不计产品失败或存储通过 |
| 后续 W2～W6、预留 W7～W8、H2～H4 | **not_run** | 按未知观察/所有权停止条件不扩大；W3 第二实例也未启动 |

累计 **产品 1/8、safeStorage 辅助 1/4**，真实 chunk 注入 0，工具更正 **1/1**。未重跑已通过的模块13节点、冷入口B、完整恢复集合、旧 outbox/registry 集合、旧六项公开检查或旧包。历史通过仅引用原报告，未加入本轮通过数量。

主要证据：[接单审计](../../tests/independent/desktop/evidence/r9-quit/start-audit.json)、[独立结果](../../tests/independent/desktop/evidence/r9-quit/lifecycle/result.json)、[独立即时比较](../../tests/independent/desktop/evidence/r9-quit/lifecycle/worker.journal.jsonl)、[兼容结果](../../tests/independent/desktop/evidence/r9-quit/compat/result.json)、[W1结果](../../tests/independent/desktop/evidence/r9-quit/windows-W1/result.json)、[W1即时记录](../../tests/independent/desktop/evidence/r9-quit/windows-W1/journal.jsonl)。

## 独立退出生命周期

节点与原要求在 [lifecycle-plan.json](../../tests/independent/desktop/evidence/r9-quit/lifecycle-plan.json) 冻结。实现入口为 [独立生命周期源码](../../tests/independent/desktop/r9-quit-lifecycle.test.ts)，首份副本及摘要保留在 `evidence/r9-quit/lifecycle-first-source/` 和 `lifecycle-source.sha256`。

| ID | 覆盖要求 | 正式比较数 / 结果 |
| --- | --- | --- |
| R9-Q01 | quit、未显示首次提示、毛毛可见；pending settings flush 和 owned stop 不提前销毁；重复 close/Tray 和最后窗口重入 | 41 / passed |
| R9-Q02 | 已显示提示且毛毛关闭的 quit 邻接变体 | 27 / passed |
| R9-Q03 | hide 首次提示保存完成后才隐藏；第二次关闭不重复提示；虚拟 Tray 走实际退出 | 34 / passed |
| R9-Q04 | ask 首次提示优先；之后 cancel、hide、quit 三种选择 | 34 / passed |
| R9-Q05 | 退出完成后的迟到首次提示响应不保存、不隐藏、不新增退出 | 29 / passed |
| R9-Q06 | 主窗口已销毁后的迟到 ask 响应不修改状态；清理独立记录 | 20 / passed |
| R9-Q07 | owned stop 拒绝不伪报退出、不释放产品资源；重复请求不重复保存/停止；日志只含安全错误码 | 23 / passed |
| R9-Q08 | 未显示提示、无毛毛时虚拟 session-end 走统一退出 | 27 / passed |

实际导入 `electron/main/index.ts`，没有复制生产 requestQuit/shutdown；composition-root、window-lifecycle、outbox-retention 运行实际代码。app.quit 替身会发出 before-quit 并尊重 preventDefault；最后窗口销毁发出 window-all-closed，只有未阻止且窗口清空才产生最终退出回执。各节点同时检查无新增 recover/revoke/refresh、无业务写入及无已观察到的未处理拒绝。虚拟 Tray/session-end 只构成组件证据，不能签收真实托盘或 Windows 注销。

235 个 ID 与静态展开完全一致；enter/terminal 一一配对，expected/actual/operator、stage、时间即时保存。5 项同 worker 工具自检在产品导入前完成，故意重复仅属 `kind=selftest`，没有正式失败豁免。正式产品/tool/unknown 首错均 null，未处理异常和模块错误为 0。最长节点正文约 502ms，清理均小于 12ms；保持正文15秒/清理5秒/初始化60秒/CLI300秒上限。Q07 的资源保留是预期业务行为；之后夹具清理不计成功退出。

独立 CLI 根 PID13468 exit0，worker7660实际 exit1；兼容根2308 exit0，5个已登记 worker 均实际 exit1并已结束。各 controller 无超时、无测试方强制结束。worker 原生码不改写为父进程码；固定 Vitest fork pool 的结束方式沿用原证据解释，不把它另算产品退出结果。中断恢复后只读检查这些 PID 均已不在。详见两组 `process.json`。

## 原正常关闭失败的新包复验

旧 [R8-R1首次失败](../../tests/independent/desktop/evidence/r8-r1/windows-W1/result.json) 与原 journal、源码、报告保持。新副本来自测试方 `r8-r1-windows-attempt1-run.mjs`，并非执行方25项 runner。最小适配见 [driver diff](../../tests/independent/desktop/evidence/r9-quit/windows-w1-driver.diff) 和 [OS helper diff](../../tests/independent/desktop/evidence/r9-quit/windows-w1-os.diff)：替换固定根、证据、新 profile，补充父进程/窗口/阶段/唯一ID/日志观察，不改原业务 selectors、动作和退出期望。

唯一受验包：`C:/MarisQuitR7/R7-20261014-191500/workspace/apps/desktop/out/Maris-win32-x64/Maris.exe`。本轮新隔离根：`C:/MarisC12/C12-R9-QUIT-20261016-011200`。profile、数据库、密文、原请求ID/虚拟正文与临时工具输出只保留在本轮外部根；仓库只保存脱敏标量和摘要。

启动前 `closePolicy=quit / closeHintShown=false / companionVisible=true`。固定 Node 直接 `spawn(shell:false)` 新 EXE；删除继承的 `MARIS_E2E_EXIT_MS`，Playwright 仅附加已核实属于本轮 root 的动态 loopback CDP。通过固定路径、创建时间、父子、本轮 profile/CDP、唯一 Maris 主窗口和外部 marker 绑定所有权。

| 断言 / 观察 | 期望 | 本次实际 |
| --- | --- | --- |
| W1-NATIVE-CLOSE-POSTED | true | true；唯一主窗口，普通 WM_CLOSE |
| **W1-NORMAL-EXIT-OBSERVED** | **true，10秒内** | **true** |
| W1-NORMAL-EXIT-CODE | 0 | **0，自然退出** |
| 退出计时器 | 不使用 | 环境中不存在该变量 |
| 正常关闭后 owned / listeners / windows | 各0 | **0 / 0 / 0** |
| W1-NORMAL-RESOURCE-DEADLINE | 在10秒观察上限内 | true，3082ms观察到资源归零 |
| forced / timeout / cleanupError | false / false / null | 与期望一致 |

北京时间 10:48:33.768237 投递 WM_CLOSE，10:48:34.248 收到 root7576 exit0，约 **480ms**。10:48:36.850 记录自有资源清空，约 **3082ms**；整个 W1 32.203秒，未改变生产 owned stop 的5秒预算。累计登记8个对象，最终自有对象、监听、窗口均0。子进程自己的退出码没有独立句柄回执，保持 unverified，不由 root0 补写子码0。

W1 内两个真实页面终态（初始与一次 recover 后）均：DAILY/SHELL/NAV/AGENT 各 **exists=true、count=1、visible=true**，`#/daily`、`readyState=complete`，观察上限5秒。后台 online/authenticated 与 canonical daily_finance 模块单列。原 bridge/隔离、CSP、非法 IPC、同 ID、主题隐私、loopback/nonce/auth、一次 recover 等是本次退出复验前置，不重计模块独立节点。

本次原生 stderr 2926bytes，没有保存原文；固定安全识别串 `GetGpuDriverOverlayInfo: Failed to retrieve video device` 命中0，renderer pageerror0。未凭此宣称没有其他原生日志或所有错误普遍无害。执行方历史 GPU overlay ERROR 与旧证据仍保持，未扩大设备根因调查。真实日常 chunk 在附加时已载入，未获得有效故障注入与撤销后 retry 证据，注入次数0，保持 unverified。

## H1 首次材料、唯一工具更正与停止

计划见 [windows-plan.json](../../tests/independent/desktop/evidence/r9-quit/windows-plan.json)：W1后继续同 profile；H1只原生解密基线，不写草稿，H2在W2后核对owner并准备老化fixture，H3/H4分别读取保留/删除结果。产品与辅助合计预算提前分配，没有因切场景扩大。

H1首次 runner 在 mkdir/spawn 前返回 `helper_exe_changed`。只读核对显示固定 dist 清单为 `path / bytes / sha256` 三列，而工具把第2列作为摘要。实际 EXE 摘要为 `bd14928e0728366fd3f41499cb398ff3f4304dab259a3e605077899a6f8c748e`，与第3列一致；辅助输出和证据目录均尚未创建。依据任务卡唯一更正授权，保留首次源码及 [启动前结果/最小diff](../../tests/independent/desktop/evidence/r9-quit/h1-prelaunch-first/result.json)，新 attempt 只改摘要列与新清单路径，不改目标、预期、操作或时限。此次消耗工具更正1/1，未增加辅助启动数。

随后 H1 实际启动固定 stock Electron 辅助一次，未导入产品 main。首次结果如下：

| 阶段 | 实际证据 |
| --- | --- |
| ready | 已生成，仅含辅助 PID；fixture 等待 controller release |
| 首个失败 | `ownership_observer_error`，elapsed13925ms |
| 解密/seed | release文件不存在；native check文件0、native result不存在；safeStorage操作未进入 |
| 原因 | **unverified**；首次观察的实际 status/error/stderr 未保存，不能确定是超时、权限或其他原因 |
| 安全清理 | 后续观察核实root4616、父25980、创建时间、固定dist路径及3个自有对象；定向强制结束 |
| 清理结果 | root实际exit1，owned0/listeners0/windows0，cleanupError=null，总19.724秒 |

首次时间线和安全值见 [H1 journal](../../tests/independent/desktop/evidence/r9-quit/helper-H1/journal.jsonl)、[H1 process](../../tests/independent/desktop/evidence/r9-quit/helper-H1/process.json)、[只读分析](../../tests/independent/desktop/evidence/r9-quit/h1-first-analysis.json)。共享 OS observer 的 `kind=product` 是固定可执行文件分类标签；该记录中的3个对象实际属于 H1 stock Electron 辅助，**不增加产品启动次数**。

这不是已证实产品失败，也不是已明确不支持、可跳过的设备条件。根据任务卡“未知异常、超时……不得归类工具问题逃过停止”及所有权停止要求，停止后续动态扩大；没有进行第二次辅助或 W2 试跑。后续清理时观察成功只能证明资源收口，不能倒填第一次观察失败的原因或把H1记作通过。

需要总控决定：是否另立有限的观察工具修复/续验任务，补足原生调用 status/error/耗时的脱敏即时回执及首次来源，再授权尚缺场景。当前证据不足选择超时、权限或设备修复方案；不需要用户立即改系统设置或点击窗口。

## 24 项增量映射

原完整要求见 [120项矩阵](phase-4-modular-agent-host-test-matrix.md)，本轮仅改B实证状态/备注，原预期、风险、12列及全部ID保持。B当前 **1 passed、1 failed、19 blocked、3 not_run**。

| ID（P4B-） | 当前整项状态 | R9增量与仍缺条件 |
| --- | --- | --- |
| SEC-01 | blocked | W1双renderer隔离通过；完整非枚举/任意preload与内存边界未齐 |
| SEC-02 | blocked | W1 CSP/inline/未知新窗通过；完整data/javascript导航及批准外链路径仍缺 |
| SEC-03 | blocked | W1精确窄bridge键集合通过；不扩大为全部preload域审计 |
| SEC-04 | blocked | W1四类非法IPC拒绝、无设置和新窗副作用；sender/origin/未知channel组合仍缺 |
| SEC-05 | blocked | W1认证/storage特征检查通过；H1未进入native解密，真实session重启、memory/dump仍缺 |
| SEC-06 | blocked | W1 owned loopback、错nonce503、无认证拒绝通过；origin/过期access/远程全组合仍缺 |
| SEC-07 | blocked | 历史安全标签证据复用；完整HTML/RTL/长文本/布局未齐 |
| SEC-08 | blocked | Q07安全退出错误码、W1 console特征检查通过；完整preload/backend/chunk故障与request ID/日志仍缺 |
| SUP-01 | blocked | W1产品正常清理自有资源通过；伪造PID/外来对照/产品停止权全组合未齐 |
| SUP-02 | blocked | W1 managed随机loopback就绪通过；端口冲突/无ready/启动超时场景仍缺 |
| SUP-03 | blocked | W1一次显式recover通过；真实崩溃/连续退避未执行 |
| SUP-04 | blocked | 相邻composition兼容通过；W2/W3第二实例和external_dev未执行 |
| SUP-05 | **blocked** | 原普通关闭失败在新包独立通过，移除当前failed；强关/注销/锁/外来对照仍缺 |
| SUP-06 | blocked | W1同draft同event ID通过；H1未完成，跨重启/真实老化/恢复一次提交GET未执行 |
| UI-01 | **passed** | 保持已接受模块13节点，不重跑；W1真实页面仅增量前置证据 |
| UI-02 | failed | 旧首次失败及历史冷B/恢复部分通过保持；真实chunk命中/重试/session完整条件未齐，不关闭LAZY-001 |
| UI-03 | blocked | 旧公开虚拟漂移证据复用；未新增真实export/CI/编译 |
| UI-04 | blocked | 旧注册/分支公开证据复用；本轮不重复或扩大整项结论 |
| CMP-01 | blocked | W1单毛毛/canonical idle通过；完整状态流和第二contribution设备条件仍缺 |
| CMP-02 | blocked | Q03/Q04组件首次提示通过；真实Tray恢复及重复关闭未执行 |
| CMP-03 | **blocked** | quit普通关闭独立通过；组件hide/ask/cancel通过；真实其他策略/Tray未执行，不能整项passed |
| CMP-04 | not_run | 未操作OS启动项，E2E抑制不算设备证据 |
| CMP-05 | not_run | 多屏/DPI/拔屏/位置夹取/全屏/键盘整项未执行 |
| CMP-06 | not_run | 透明降级/OS主题/高对比/减少动效/颜色语义完整设备条件未执行 |

已在 [主报告](phase-4-c12-windows-shell-report.md) 和 [人工清单](phase-4-c12-manual-checklist.md) 追加本轮结果，旧正文不回写。真实Tray、Windows注销/重启、启动项、OS主题和多屏条件不由虚拟组件或代理观察代签。没有启动 Docker、微信V002、OpenClaw、真实provider、其他角色或P4-C/D。

## 完整性、暂停间隔与交付

接单核对：937起点、R7仓库933中928匹配+5项总控协调变化；外部构建932、产物140、Python资源67、dist73、完整依赖12677、执行方证据157及旧R8-R1交付82均匹配。固定 EXE/asar/lock 摘要分别为 `183758e3...f6a65`、`16f45da6...aed3`、`5ddc0a93...cb4a`，完整值在接单和终点审计。

用户继续和工具host握手中断之间没有伪造持续执行；本次复验实际时间以 journal 为准。独立组件于北京时间09:55:53进入，兼容随后一次完成；10:43用户继续后读取记录并核对，未重跑。角色文件先前遗留的01:30/01:36检查点文字已明确记录并校正，不把跨时段间隔算作测试运行或超时。

**终点审计通过**：[end-audit.json](../../tests/independent/desktop/evidence/r9-quit/end-audit.json)。937起点中933项不变/4份授权共享文档变化；R7仓库933中924不变/总控5+测试共享4变化。外部构建932、产物140、资源67、dist73、完整依赖12677、执行方证据157全部匹配，包/资源/dist/依赖的实际路径库存亦精确匹配。旧R8-R1交付82中78不变/4共享变化，全部旧首次源码和证据保持。68份新首次材料及各次源码清单匹配；主报告/人工清单原字节前缀完整，120个唯一ID、12列、原预期及A/C/D字节保持，staged0、只读diff检查退出0。

首轮终点汇总把P4-A/B/C/D四条切片摘要行计入案例，宽匹配124导致计数AssertionError；此前完整输入/旧首次/新材料核对已通过。保留原审计源码和 [首次汇总记录](../../tests/independent/desktop/evidence/r9-quit/end-audit-first-summary-error.json)，新只读副本仅收紧case ID匹配，精确120后完成审计。这属于任务卡允许的结束后只读汇总补证，没有重启产品、辅助或测试目标，也没有增加动态工具重试预算。另一次临时只读文档汇总因默认GBK读取UTF8文件失败，未写入文件或影响目标；最终正式审计显式UTF8通过。

最终 [delivery.sha256](../../tests/independent/desktop/evidence/r9-quit/delivery.sha256) 绑定所有新交付与四份授权共享文档，且不包含自身或验证回执形成循环；[delivery-verification.json](../../tests/independent/desktop/evidence/r9-quit/delivery-verification.json)记录数量、摘要及最终状态。终点审计中的共享文档摘要对应审计时刻，最后角色收口/报告补齐以最终交付清单为准。

本轮仅保留新虚拟现场与缓存，没有删除数据卷、重置数据库或运行系统清理；不需要删除旧profile/包。所有本轮已登记运行目标已收口。最终由总控裁定 QUIT-001关闭及后续授权，测试角色停在 blocked / finished，交付供 review。
