# P4-B7-R7-QUIT：主窗口quit策略统一退出修复

## 负责人、目标与必读

你是既有执行智能体，本任务唯一负责人。处理P1 `P4-C12-R8-R1-QUIT-001`：closePolicy=quit时，主窗口正常关闭后应用及owned后端未退出。测试方/顾问停止。本次是已有Shell生命周期修复，不做真实财务界面，不改冻结架构或权限。

先按AGENTS读取README、project-coordination、coordination/README、最新control、本人executor、本卡，再读：

- [总控裁定](../../p4-c12-r8-r1-quit-coordinator-review.md)、[R8-R1独立报告](../../testing/phase-4-c12-r8-r1-modules-windows-report.md)、其windows-W1首次result/journal、windows-first-analysis、实际Windows driver/OS helper。只读，不运行或修改独立材料。
- [IF-003](../../phase-4-interface-freeze-003.md)关闭策略、[IF-004-F19](../../phase-4-interface-freeze-004.md#p4-if-004-f19统一退出)、IF-005；[R6执行运行说明](../../b7-r6-module-ready-running.md)和[R6任务](p4-b7-r6-module-ready-executor.md)的普通工具/LOCALZIP/产物门禁。
- [新固定起点](../snapshots/p4-b7-r7-quit-start.sha256)：仓库根、原字节、排序 `path<TAB>sha256<LF>`、UTF8无BOM、排除自身。接单前全部匹配且staged=0，登记接单和下一检查点。

已独立通过的模块13节点、旧冷B/完整R7恢复、开发兼容28及其他旧独立集合不运行。UI-01已接受passed；退出缺陷、LAZY-001/UI-02/P4-B未关闭。

## 精确五文件边界

仓库可写仅：

1. `apps/desktop/electron/main/index.ts`：close/quit/shutdown接线和该修复必要的幂等保护。
2. 新 `apps/desktop/tests/unit/main-quit.test.ts`：真实main入口执行方关闭/退出回归。
3. 新 `docs/b7-r7-quit-running.md`。
4. 新 `apps/desktop/b7-r7-quit-source.sha256`。
5. 本人 `docs/coordination/agents/executor.md`。

其他产品（含composition/supervisor/Host、renderer/Shell、outbox、registry）、已有开发测试、独立测试/报告/矩阵、依赖/lock/Forge/staging、接口冻结、control/overview和其他角色只读。需要扩大产品范围则报告具体阻断点，不顺手改邻接模块。允许新C盘任务根自有driver/evidence/cache/profile，源码在正式目标前冻结；旧环境不回写。

## 先复现真实接线，再最小修复

在新测试中导入实际 `electron/main/index.ts`，模拟Electron/窗口/OS边界与可控composition端口。不能只测试复制出的handleClose或在测试直接调用内部requestQuit来代替主窗口close。app.quit的替身应按Electron生命周期语义触发before-quit、尊重preventDefault，记录最终退出，避免仅用无行为spy制造通过。

窗口替身的destroy/closed须维护存活窗口集合，最后窗口销毁时触发实际已注册的window-all-closed。验证shutdown尚在尾声时由此引发的quit重入不会重复清理已销毁窗口或无限循环；不能因替身省略此事件而漏过真实生命周期问题。

先在原产品代码运行并保存最小红灯：已创建主窗口、毛毛和Tray、composition已就绪，配置quit且closeHintShown=false；向实际main注册的主窗口close handler送正常关闭事件，要求进入统一shutdown。关闭请求必须真正被该handler接收；未启动/fixture错误不能作为产品红灯。该开发红灯不启动旧EXE、不复跑独立W1。若精确条件原实现已通过，停止猜测性修改并报告差异。

最小修复应让显式quit进入现有统一退出，允许等待自有后端安全停止后释放窗口/Tray；不得用app.exit/process.exit、关闭安全检查、强杀所有同名进程或E2E专用分支制造退出成功。只修实际接线/必要幂等，不增加新IPC、设置项、退出timer或新接口。

新执行方回归至少覆盖：

- quit策略、closeHintShown=false/true、毛毛可见/不可见均走同一退出路径；显式quit不误显示“继续在托盘运行”或仅hide。
- composition.shutdown处于可控pending时，不绕开flush/owned stop或提前宣告完成；结束后Tray/毛毛/主窗口释放、最终app.quit正常完成。保留原flush/owned停止语义，不能吞异常然后假报成功。
- 重复close、before-quit或Tray quit在退出进行中不重复flush/停止后端、不重复产生未处理错误，不递归无限quit；允许Electron必要的第二次quit完成退出，不能硬断言app.quit总调用只能1次。
- 默认hide_to_tray及首次提示仍按原合同；closeHintShown=true的ask_every_time分别隐藏、取消、退出，取消保留窗口/会话且不shutdown。沿用既有首次提示优先级，不借此重写关闭体验。
- Tray quit和session-end仍进入统一退出；这里只是虚拟事件的开发保护，不宣称真实Tray/Windows注销通过。
- 退出时不新增recover、owner重建、撤销、provider/财务写入；outbox/设置保存和原生老化提示退出保护保持。若只需透传现有composition，不复制其生产内部实现。

允许正常开发调试和有理由的定向复跑，保留红灯及各次失败；不把一次预算规则套到开发编辑循环。新测试+composition/outbox-retention/window-lifecycle/supervisor-outbox等必要邻接、TypeScript、lint通过后，完整desktop开发回归运行一次（原16文件150项加本轮新增）。不修改旧断言、不重复独立集合或Python/P0～P3。新增测试数量如实统计，不把定向和全组重复计作唯一节点。

## 固定普通环境与一次新package

固定只读来源 `C:/MarisModulesR6/R6-20261013-002100`，沿用R8-R1 start/end的813构建源码、140产物、67资源、73dist、12443冻结依赖及12677完整inventory。仓库当前文档以新起点为准，不能把协调文档差异当产品漂移；外部旧源码必须保持原字节。

新根 `C:/MarisQuitR7/R7-<时间戳>`。先核实绝对边界/无reparse，再普通物化所需工具/依赖/源码到新根，不用junction、不改旧根。沿用固定Node24.21.0、pnpm12.7.0、Electron44.4.5、Playwright1.63.0及已验证Python。lock SHA-256 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`，本地官方Electron ZIP SHA-256 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d`。不安装/下载/audit或修改永久PATH/代理/安全软件；使用已经成功的任务局部pnpm和LOCALZIP。

开发门禁完成后冻结新构建输入，package最多1次。原7项静态检查、production fuses、完整out/67资源、污染/staging零残留均须通过；新asar实际包含main修复并与受验源码绑定。失败保存首次后停止，不补第二次package。R6旧EXE/asar保持只读，不以协调或driver变化冒充新产品修复。

## 唯一新EXE：必须从普通关闭退出

静态通过后只启动新EXE一次，硬上限120秒。使用Node spawn(shell:false)，Playwright只附加本轮动态loopback CDP；不用Electron launcher/app.asar/PID提升。新虚拟profile/owner/数据库，固定Python；不读旧或个人AppData。

启动前新profile明确 `closePolicy=quit`、`closeHintShown=false`、`companionVisible=true`。隔离的MARIS_E2E仅保留已冻结的profile/设备操作抑制等用途；**删除继承的MARIS_E2E_EXIT_MS，不能启用自动退出timer**。不在runner通过app.quit、process.exit或强杀完成正常退出断言。

同一次运行先核验原R6新包的后端认证/canonical daily、主/毛毛窗口与窄bridge、renderer隔离、安全状态；真实daily/Shell/导航/Agent分别采样exists/count/visible/hash/readyState。一次recover及theme/privacy/settings状态保持、切回daily真实可见继续保留，避免仅后端通过就关闭。就绪采样单次5秒，记录unknown原因与安全实际值。

随后仅向本轮已核实root路径/创建时间/父子关系和profile下的唯一Maris主窗口发送一次正常WM_CLOSE：

1. 保存身份/唯一窗口与请求成功投递布尔；未找到或投递失败属于来源不成立，不得算产品通过。
2. 自投递后最多10秒等待root自然退出；保留实际耗时、真实exit code，要求exit0。正常owned停止预算仍为冻结5秒，不延长生产预算。
3. 用已登记身份核对所有本轮产品/毛毛/owned Python/监听与窗口为0；保留完整观察范围和未知子进程退出码，不用root码替代。虚拟设置及未完成outbox不得因退出丢失；可只读核对文件存在/摘要和开发flush证据，不启动第二次产品验证重启。
4. timeout、非零退出或资源残留保留首次、停止扩大；只做身份明确的自有进程安全清理，强制收口不计正常退出。不第二次启动、不换Tray/计时器退出来覆盖该失败。

driver在正式运行前做静态语法/参数/路径和日志格式检查；显式UTF8、兼容清单CRLF，不用PowerShell自动变量Args存业务参数。事件名与details.stage分离，UI数值和首错独立记录；纯工具问题仅在产品未启动前允许定向修正一次并换新attempt。产品启动后的失败不重跑。

## 收口与交付

本轮package上限1、新EXE上限1，不运行旧R6产品、旧独立W1、其余独立测试、Docker/微信V002/OpenClaw或真实provider。不得操作系统注销/重启、启动项/系统主题/多屏，不要求用户立即点击。

运行说明给出：首次红灯与main退出数据流、最小diff、开发节点映射/所有失败、真实新EXE关闭请求/等待/自然退出与资源结果、工具警告及证据层级。自测通过只交review/finished，不关闭QUIT-001、CMP-03、SUP-05或P4-B。

停止修改后生成source清单（新起点更新授权摘要、加入新测试/运行说明、排除自身），5交付逐项摘要复算；外部新构建/产物/资源绑定。旧R6环境与R8-R1原始证据及专属虚拟profile前后保持；不要读取或输出其秘密内容。保留新产物/虚拟profile/原始记录，只清理已核实绝对边界和无reparse的本任务临时项。

接单/红灯/修复/开发/打包与启动/收口更新本人状态和执行快照；超过5分钟操作前记录检查点，有控制时至少10分钟心跳，中断不算持续工作。新严重缺陷、需扩大产品文件范围、接口变化、秘密泄漏、不受控弹窗、所有权不明、无法收口立即停止；相同外部问题两检查点无新证据停止。无Git写权限，不自行启动其他角色或后续任务，最终交review/finished或blocked/finished。
