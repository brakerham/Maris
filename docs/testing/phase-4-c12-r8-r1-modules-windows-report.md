# P4-C12-R8-R1 增量独立验收报告

2026-10-14，测试智能体。绑定 control `2026-10-14T07:16:34+08:00`、R8-R1 任务卡和固定 P4-B7-R6-MODULE-READY。结论：**blocked / finished，交总控 review**。四节点续验、必要兼容及新增公开检查通过；真实 Windows W1 在“quit 策略关闭主窗口”处出现 P1 业务失败，按停止规则收口，不启动后续场景。未修改产品、依赖、受验包，也未执行 Git 写操作。

## 本轮结果及历史复用

| 证据集合 | 本轮实际结果 | 计数口径 |
| --- | --- | --- |
| 848 项固定起点 | 接单前 848/848 匹配、staged=0 | 原字节复算；清单 SHA-256 `ca700581d646b4a6cae694737642678c25195cbd8c0aeb0c4a38143b7196f837` |
| 旧 R8-01～09 | 历史 9 passed 只读复用 | 本轮过滤，不计新 pass/skip；旧 R8-10 首次工具失败保持 |
| 新 R8-10～13 | **4 passed**，184/184 正式比较完整配对 | 1 次 CLI、4 个独立生命周期；5 项同 worker 纯标量自检另列 |
| 必要开发兼容 | **28 passed** | module-readiness 18、lazy 8、Shell 1、composition 1；执行方测试的兼容结果单列 |
| 剩余公开条件 | **6 passed**，21 个比较 | 原 checker 的虚拟输入漂移 5 节点、真实启动接线与分支静态检查 1 节点 |
| Windows W1 | **失败**；57 对断言中 56 passed、1 failed | 固定新 EXE 首次真实启动；后台和页面分层；不是 57 个测试 |
| W2～后续 Windows / H1～H4 | 未执行，因 P1 停止 | 产品累计 **1/8**、辅助 **0/4**；真实 chunk 注入 0 |

证据根：[本轮 evidence](../../tests/independent/desktop/evidence/r8-r1)。逐节点、逐断言与实际耗时见 [四节点 result](../../tests/independent/desktop/evidence/r8-r1/modules/result.json)、[即时 journal](../../tests/independent/desktop/evidence/r8-r1/modules/worker.journal.jsonl)、[兼容 result](../../tests/independent/desktop/evidence/r8-r1/compat/result.json)、[公开 result](../../tests/independent/desktop/evidence/r8-r1/public/result.json)、[公开安全比较](../../tests/independent/desktop/evidence/r8-r1/public/assertions.jsonl)。旧证据不回写，未重跑 P、旧 A/B、D16、完整 R7 或旧 EXE。

## 四节点工具修正与可靠性

新副本保留全部原业务正文，唯一正文差异是 R8-10 链接断言前缀 `REMOVED.NAV` → `REMOVED.ALPHA_LINK`；整个 `chrome('REMOVED')` 保持。R8-13 主动卸载后的 FINAL 空 root 及 DOM_EMPTY、NO_MORE_READS、SUBSCRIPTIONS_ZERO 原样保留。选择器、期望、顺序、StrictMode、正文 15 秒/UI 5 秒/清理 5 秒/初始化 60 秒/CLI 300 秒均保持。

重复 ID 在抛错前走独立 `tool_error` 通道，保存 errorCode、nodeId、attemptedAssertionId、stage 和时间。scenario/reporter 分列产品比较失败、工具错误、unknown 和 cleanup；清理成功不能覆盖正文失败。未知异常只保存安全类型，不能降类为工具错误。

同 worker 在 jsdom 初始化、真实产品导入和 DOM 挂载之前完成 SELF.DISTINCT、SELF.DUPLICATE_RECORDED、SELF.CLEANUP_NOT_OVERRIDE、SELF.UNKNOWN、SELF.PRIVACY 五项自检。故意重复只在独立 SELF.DUPLICATE case 中记录 `kind=selftest / expectedFailure=true`，未进入正式首错统计。正式节点无 expectedFailure 豁免。静态 ID 展开数量分别 69、36、42、37，运行比较总数 184 与之相符；正式产品/tool/unknown 首错均 null。最小 diff、冻结源码和检查记录在 [preflight](../../tests/independent/desktop/evidence/r8-r1/preflight)。四节点额外纯工具 CLI 预算使用 **0/1**。

主进程 26900 实际退出 0，worker 5156 实际退出 1；兼容与公开 CLI 根退出 0，登记 worker 亦已退出，原生码 1 原样保留。固定 Vitest `dist/chunks/index.C-uw7tH9.js` 的 fork pool `stop()` 调用 `fork.kill()`，与此收口方式相符；没有拿父码替代子码，也没有把框架结束 worker 写成测试方强制清理。各 controller 均未超时或主动强制，四场景订阅归零、DOM 卸载、全局恢复均有独立比较。

## 新 P1：quit 策略关闭主窗口后应用和后端继续驻留

**缺陷 ID：P4-C12-R8-R1-QUIT-001；严重级别 P1。** 对应 P4B-CMP-03 和 P4B-SUP-05 的正常退出子条件。冻结依据：P4-IF-003 关闭策略规定 quit 走统一退出且只清理自有后端；P4-IF-004-F19 定义统一退出。未观察到数据丢失，不推断未测的其他关闭策略。

最小复现路径（从本次首次运行提取，未另起简化复跑）：

1. 使用固定 R6 EXE 和本轮新虚拟 profile，`closePolicy=quit`、`companionVisible=true`，无产品退出定时器。
2. 等真实 managed/认证/canonical daily 模块及日常页面就绪；完成同 ID、设置及一次 recover，恢复后的日常页面仍可用。
3. 仅向路径、创建时间、父子关系和本轮 CDP/profile 已核实的 root PID 28308 的唯一标题 Maris 主窗口发送正常 WM_CLOSE。
4. 保留原生窗口请求成功证据，观察退出 10 秒。不得通过 Tray 或另一次退出请求替代此场景结果。

| 断言/观察 | 期望 | 首次实际 |
| --- | --- | --- |
| W1-NATIVE-CLOSE-POSTED | true | true |
| **W1-NORMAL-EXIT-OBSERVED** | **true** | **false** |
| 停止后只读 device-settings.closePolicy | quit | quit |
| 失败后的自有资源观察 | 产品应已退出并清理 | root 仍存在且身份匹配；7 个当前自有进程、2 个 loopback 监听 |
| W1-NORMAL-EXIT-CODE | 0 | not_run；前一比较失败后停止 |

失败发生于 `normal-close`，北京时间 13:55:18。完整首次来源：[Windows result](../../tests/independent/desktop/evidence/r8-r1/windows-W1/result.json)、[Windows journal](../../tests/independent/desktop/evidence/r8-r1/windows-W1/journal.jsonl) 的 seq 121～126，以及 [只读分析](../../tests/independent/desktop/evidence/r8-r1/windows-first-analysis.json)。安全值和事件 stage 独立保存，没有复用旧 R7 缺失的终态样本。

只读源码线索：`electron/main/index.ts` 的 close 监听器仅在策略不是 quit 时调用 handleClose；quit 分支允许主窗口默认关闭，但该分支没有调用 requestQuit/统一 shutdown。毛毛窗口/Tray 仍存在时，不能由主窗口关闭推导 app.quit 已执行。这是与实测吻合的定位线索，修复有效性仍需执行方修改后独立复验；本测试方没有修改实现。

安全收口：控制器按已验证 root 和其自有树定向终止，实际 root 退出码 1，**这是测试方强制收口，不是产品正常退出通过**。W1 总耗时 45.776 秒，无整场景超时。累计登记 11 个对象，最后观察自有对象 0、监听 0；历史各子进程原生退出码没有句柄证据，记 unverified，不用 root 码代替。虚拟 profile、DB、加密 blob、同 ID 连续性文件留在专属外部根，不读取旧/真实 profile；未将秘密、消息正文或原始 stderr 入库。

## Windows 已取得和未取得的证据

新外部根与场景/profile 关系见 [windows-plan.json](../../tests/independent/desktop/evidence/r8-r1/windows-plan.json)。产品使用固定 Node `spawn(shell:false)` 直接启动新 EXE，Playwright 仅附加本轮 owned loopback CDP。没有 Electron launcher、asar 注入、fuse 或设备设置修改。

W1 后台 online/authenticated、canonical daily_finance/profile 通过。首次页面与 recover 后的两个最终样本中，DAILY/SHELL/NAV/AGENT 各自 **exists=true、count=1、visible=true**；hash 为 `#/daily`，readyState 为 `complete`，两次观察上限均 5 秒。真实页面和后台结果分别记录；新成功不回填旧 R7 W1 未记录的 DOM 或原因。

主/毛毛窗口 Node API 隔离、窄 bridge 键集合、CSP inline 阻止、未知新窗口拒绝、4 类非法 IPC、设置无副作用、同 draft ID 返回同 event ID、dark/privacy 设置及文件保存、renderer storage 秘密模式检查、owned loopback、错 nonce 503、无认证拒绝、一次 recover 后真实页及主题/隐私保持均通过。这里没有完整内存/dump、全部 sender/channel、真实 provider 或财务写入验收；console 只记录脱敏布尔/类别，pageerror=0。

真实 chunk：附加时当前真实日常模块已载入，记录了实际 file 页面/已完成资源状态；未获得可控故障命中、撤销后 retry、跨故障真实会话保持，注入次数 0，保持 unverified。没有为补足它重启已成功场景。真正会话重启、同 ID 跨重启、安全存储辅助、单实例、Tray、其他关闭策略、原生老化保留/明确删除因新 P1 未执行。OS 注销/重启、启动项、系统主题、多屏/DPI 等无授权条件继续保留人工缺口，没有请求用户立即操作。

## 工具与证据限制

- 接单输入复算于 07:26 完成落盘；会话随后中断，13:30 恢复读取输出，没有把该间隔写成持续工作或重复接单。当前控制版本未变。
- 准备阶段 TypeScript 静态检查首次使用 Windows 路径而非 file URL，错误 ERR_UNSUPPORTED_ESM_URL_SCHEME；目标尚未导入，改用 file URL 后语法检查通过，记录在 preflight。公开 checker 的虚拟 CommonJS 环境在正式启动前静态补足 esModuleInterop，初版和最终清单均保留，6 节点只运行一次。
- 普通沙箱 CIM 只读查询拒绝；受控权限下对自进程路径/创建时间的只读检查成功，才启动 Windows。没有关闭安全软件或改系统设置。Windows 使用该权限取得实际 scoped owned 观察；不据此宣称任意系统进程状态。
- 首份 Windows 驱动在创建外部根和 spawn 之前报 runner_source_changed：CRLF 清单首行摘要末尾被保留回车，真实源码摘要均匹配。产品 0、目录未创建的证据和首份源码留在 windows-prelaunch-first。新副本只改换行解析与新清单路径，使用一次明确的启动前工具修正；W1 产品实际仅启动一次。业务失败后无重试。
- 新公共漂移案例使用真实 check-generated 控制流、固定 openapi-typescript 和 TypeScript，但 fs/子进程端口均虚拟；没有实际 Python export/CI 进程或网络取 schema，也没有重编译产品。此有限证据不足将 UI-03 整项关闭。

## 24 项增量映射

原完整预期沿用 [原矩阵](phase-4-modular-agent-host-test-matrix.md)、[R3 原要求](phase-4-c12-r3-route-windows-report.md) 和 [R7 缺口](phase-4-c12-r7-recovery-windows-report.md)。120 唯一 ID、12 列、原预期及 A/C/D 不变。本轮 B 为 **1 passed、3 failed、17 blocked、3 not_run**。

| ID（P4B-） | 当前整项状态 | 本轮增量 / 仍缺 |
| --- | --- | --- |
| SEC-01 | blocked | 新真实双 renderer Node API 隔离通过；非枚举/跨域/完整内存边界仍缺 |
| SEC-02 | blocked | CSP/inline/未知新窗通过；data/javascript 导航与批准外链完整路径仍缺 |
| SEC-03 | blocked | 新包主/毛毛窄 bridge 精确键集合通过；不能扩大到任意 preload 域审计 |
| SEC-04 | blocked | 4 类真实非法 IPC 拒绝且无设置/额外窗口副作用；sender/origin/未知 channel 全组合仍缺 |
| SEC-05 | blocked | 新虚拟 owner 认证、renderer storage 模式检查通过；native safeStorage、重启连续性和 dump 未执行 |
| SEC-06 | blocked | owned loopback、错 nonce 503、无认证拒绝通过；远程/origin/access 全组合仍缺 |
| SEC-07 | blocked | 沿用历史标签与恢复安全证据；独立全 HTML/RTL/长文本和设备布局仍缺 |
| SEC-08 | blocked | 四节点错误局部安全、W1 console 无被测秘密特征；实际 preload/backend/chunk 故障、request ID、完整日志仍缺 |
| SUP-01 | blocked | 测试方安全 scoped 收口通过；不代表产品停止权/伪造 PID/外来对照全通过 |
| SUP-02 | blocked | 新 managed 随机 loopback ready/认证通过；端口冲突、无 ready/超时及产品清理仍缺 |
| SUP-03 | blocked | 一次显式 recover 和真实页面恢复通过；崩溃/连续退避未执行 |
| SUP-04 | blocked | composition 兼容通过；W2/W3 单实例、external_dev 未执行 |
| SUP-05 | **failed** | 正常退出子条件实际执行失败；系统注销/其他设备条件仍 not_run，不因总体风险为 manual 而掩盖已观察失败 |
| SUP-06 | blocked | 真实同 draft ID 返回同 event ID；跨重启、native 老化、恢复一次提交/GET 尚缺；旧 outbox 42 不重跑 |
| UI-01 | **passed** | 旧 R8-01～09与新 R8-10～13共同覆盖真实注册器/路由的缺失、禁用、不兼容、未知不导航/不预载，合法交集显示；W1 新包日常页增量通过 |
| UI-02 | failed | 新四节点补邻接保护，W1 页面/recover通过；旧失败历史保留，真实 chunk 故障/会话条件仍缺，LAZY-001 不自行关闭 |
| UI-03 | blocked | 新 PUB01～05 虚拟漂移与定位通过；真实 export/CI 比较/编译流程未执行 |
| UI-04 | blocked | 新 PUB06 主入口编译与 Shell/路由无 moduleId 条件分支检查通过；旧冲突/strict 证据复用，整套启动验证映射待总控组合复核 |
| CMP-01 | blocked | 单毛毛窗口/canonical idle/主入口存在；完整假状态流和第二 contribution 设备条件仍缺 |
| CMP-02 | blocked | 首次提示/Tray 恢复/二次关闭未执行 |
| CMP-03 | **failed** | quit 关闭后不退出；hide/ask/cancel/真实 Tray 仍未执行 |
| CMP-04 | not_run | 未操作真实启动项，人工条件保留 |
| CMP-05 | not_run | 未操作多屏/DPI/拔屏；jsdom/W1 主题隐私不替代整项设备证据 |
| CMP-06 | not_run | 未验证透明设备降级/OS主题/高对比等完整人工条件 |

## 输入完整性与交接

起点核对记录在 [start-audit.json](../../tests/independent/desktop/evidence/r8-r1/start-audit.json)：外部构建源码 813、产物 140、Python 资源 67、冻结依赖 12443、Electron dist 73 全匹配，EXE/asar/lock 与 9 份依赖元数据保持固定；旧 R8 交付 29、源码 7、首次 6 全匹配。R6 旧仓库 814 清单的 9 项差异明确区分总控 5 项与测试方共享 4 项。

**终点审计已通过**：848起点中844原项保持/4共享授权变化，外部813/140/67/12443/73全保持，完整12677依赖副本inventory匹配，旧R8源码7/首次6不变，矩阵/追加前缀与只读Git门禁通过。逐项结果以 [end-audit.json](../../tests/independent/desktop/evidence/r8-r1/end-audit.json) 为准：检查新起点仅四份授权共享文档变化，旧 R8 其余 25 项和全部源码/首次材料保持，旧 R7 清单共享变化逐项列举，外部 R6 输入不变；同时核对完整依赖副本 inventory、原文档字节前缀、矩阵结构/非 B 字节以及本轮各次源码和首次结果。新交付文件摘要由 [delivery.sha256](../../tests/independent/desktop/evidence/r8-r1/delivery.sha256) 与 [delivery-verification.json](../../tests/independent/desktop/evidence/r8-r1/delivery-verification.json) 记录，均不包含自身形成循环。

交总控裁定：接受本轮有限独立通过集合、审阅 UI-01 的整项通过建议；将 P1 QUIT-001 交执行方处理后再另行授权独立复验。UI-02、LAZY-001、P4-B 和项目整体没有完成。测试角色已停止动态验收，完成只读核对及报告后停在 **blocked / finished，等待总控 review**，不自行派发、修产品、重跑或进入 P4-C/D。
