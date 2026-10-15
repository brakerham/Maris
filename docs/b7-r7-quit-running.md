# P4-B7-R7-QUIT 执行方运行说明

任务状态：**review / finished**。本文记录执行方开发和本轮新包/新 EXE 验证，不是独立验收。交付严格为 main 退出接线、新开发测试、本文、source 清单和本人日志五个仓库文件；没有 Git 写操作。

## 起点与首次失败

接单前已复算 931/931 项原字节固定起点，0 missing/mismatch，staged=0。UTF-8 无 BOM、LF、ordinal 排序的起点清单 SHA-256 为 `7276dd5d78a43bdaa1b570461cf5981e2cbcbf9d1ed6543ac5bfb98c179c376f`。恢复时重新核对，仅 main 与本人日志为任务授权变化；原始独立证据不覆盖。

新测试导入实际 `electron/main/index.ts`、`DesktopCompositionRoot`、`CompanionController` 和 `OutboxRetentionController`。虚拟边界仅为 Electron/窗口/系统、持久化及 Supervisor/owner/Host 端口。`app.quit()` 替身触发真实注册的 `before-quit`，尊重 `preventDefault`；窗口销毁维护存活集合并同步触发 `window-all-closed`。fixture 先证明主/毛毛可见、Tray 创建和 composition 在线认证，再发送正常主窗口 close。

原实现 red：0 passed / 1 failed / 0 skipped。`quit`、`closeHintShown=false`、毛毛可见时：closeReceived=1，prevented=false，shutdownCalls=0，mainDestroyed=true，liveWindows=1，trayDestroyed=false，finalExits=0。不是 fixture 启动失败；首次原始 JSON、事件和受验源码摘要保留于 `evidence/tests/red*`，原测试源码保留于 `evidence/inputs/red-main-quit.test.ts`。

## 最小修复与证据层级

普通主窗口 close 在统一退出完成前阻止默认销毁。显式 quit 进入既有 requestQuit，其他策略沿用现有提示；退出中重复 close 只阻止提前释放。before-quit 在开始异步 shutdown 前建立单次启动守卫；最后窗口同步发出 window-all-closed 再次进入 before-quit 时，不重复清理或注册完成回调。

退出顺序为实际 main → composition.shutdown → 原 settings/outbox flush → Supervisor owned stop → Tray/毛毛/主窗口销毁 → 最终 app.quit。保留 composition 内部原有 flush 异常语义，不声称本次修改增强了其数据保存故障处理。owned stop 拒绝时 main 仅记录安全错误码 `desktop_shutdown_failed`，不标记完成或释放窗口。提示框迟到响应/保存完成时若已退出，不再隐藏失效窗口。

未新增 IPC、设置项、接口、timer、owner 重建、恢复、撤销或业务写入；未改 composition/supervisor/Host、renderer、outbox、registry、旧开发测试或独立材料。

## 开发合同映射

| 条件 | 新开发节点 | 结果 |
| --- | --- | --- |
| quit × 首次提示 false/true × 毛毛可见/不可见 | 原红灯节点 + 3 参数节点 | 定向 4 passed；显式 quit 不提示或 hide |
| 保存 pending、停止 pending、顺序与资源释放 | 1 节点及各退出节点公共检查 | 定向 passed；保存前不 stop，stop 完成前不销毁 |
| 重复 close / before-quit / Tray，最后窗口同步重入 | 1 节点 | 定向 passed；flush/stop 各 1、最终 exit 1、quitCalls=3 |
| owned stop 拒绝 | 1 节点 | 定向 passed；不假报成功，安全日志不输出异常原文 |
| 默认隐藏和首次提示、ask 首次提示优先级 | 2 节点 | 定向 passed |
| ask 已提示后的隐藏/退出/取消 | 3 参数节点 | 定向 passed；取消不 shutdown/撤销 |
| 虚拟 Tray / session-end 统一退出 | 2 参数节点 | 定向 passed；不代表真实系统注销/Tray 验收 |
| 退出后迟到提示响应及保存完成 | 3 节点 | 定向 passed；不隐藏已失效窗口、不新增退出保存 |
| 实际老化提示未开始/正在等待时退出保护 | 2 参数节点 | 定向 passed；不再提示/删除草稿 |

唯一新增节点为 19 项。定向实际 5 文件、48 passed / 0 failed / 0 skipped（新 19 + 原邻接 29）；JSON suite 数含 describe，不当文件数。TypeScript 和 lint 均 exit 0。唯一完整开发回归于2026-10-15 11:12:47—11:13:10完成，17文件、169 passed / 0 failed / 0 skipped（原150+新19），exit0；原断言未修改。日志未输出warning；不累计定向与全组重复节点，不运行独立测试或 Python/P0～P3。

## 普通环境与中断

新根 `C:/MarisQuitR7/R7-20261014-191500`；固定旧来源 `C:/MarisModulesR6/R6-20261013-002100` 只读。新源码 931 项普通复制，依赖冻结 12443 项/完整库存 12677 项、Electron dist 73 项和工具 3 项全部摘要一致，无 junction/reparse。源码起点差异只为已授权接单日志。

旧来源已核对 source 813、out 140、资源 67、deps 12443/full 12677、dist 73、evidence 172（含其虚拟 profile）；R8-R1 外部 65 项清单 SHA-256 为 `196e5d4487ac09952b110129e677d268f104f359d47d7992027ef9fc740b7cac`，只读摘要而不读取/输出秘密内容。最终前后复算全部匹配。

固定 Node 24.21.0、pnpm 12.7.0、Electron 44.4.5、Playwright 1.63.0、Python 3.14.7；lock SHA-256 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`；LOCALZIP SHA-256 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d`。本轮不安装、下载、audit 或修改永久环境。

2026-10-15 00:07 附近完整回归被自动审批额度限制拦截，工具明确未执行；11:12 用户继续后核对无 full/package/EXE 启动记录，从原检查点恢复。中断期间不计持续工作。旧辅助只完成新外部 helper 草案；恢复后的内部辅助也遇到模型额度限制，复核没有新写入。主执行接回两驱动完成、审阅、集成和启动，不作为独立验收。

## 唯一新包及实际 main 绑定

package **1/1**：2026-10-15 11:22:12.170—11:22:18.345+08，6175ms、exit0、stderr0。实际 Forge 进程使用固定 Node/pnpm/LOCALZIP；8 项打包前门禁全部通过。构建输入冻结为 **932 项**（931 起点 + 新测试），未随收口文档/日志更新而回写。

静态 **7/7**：out 140、Python 资源 67、asar 11 文件，无链接或 unpacked 项；production fuses 前六项为48/49/48/48/49/49；污染0、staging与过渡目录残留0。实际 asar `.vite/build/main.js` 与构建输出逐字节相同，并包含普通close接线、单飞守卫、安全失败码及session-end接线；静态字串只作来源绑定，行为由开发红绿和新EXE另证。

| 输入/产物 | SHA-256 |
| --- | --- |
| 冻结932项构建输入清单 | `e7cec440e4420bec3f6fec274b6521ecd413d0d4c4fc1f304a584823ea9732a0` |
| 新Maris.exe | `183758e3b25a5314da8bea157f92ec00385e9ed6e18f42bac1ad679cdd6f6a65` |
| 新app.asar | `16f45da665693e9b606ffb6b839081a48fa6ed4ae3e4995b403f57237118aed3` |
| 实际asar main，120384bytes | `80c09819f4e433715ee530c73a328c6bb0535f3c175074759d35db31052bb71c` |
| 完整out140清单 | `1953b0f91d94b4d64850d4d81c5da8c803bb1da5eebda6bf32eda64935214521` |
| Python资源67清单 | `324845f07f050f2b90e3c1e0b89b6598c8748aca549f8f848b600d5a2a0da5d1` |
| 启动前final-exe-runner.mjs | `dec61e6fc889ccc730fe3ca3146afa318fc01e18962f7cd8d8eb11c7308124c4` |
| 启动前normal-close.ps1 | `0dd449843d43fcdbd19c09d10d2a9b99cd1f6255c4010658c9098d4e511f75c7` |

## 唯一新EXE与普通关闭

新EXE **1/1，25/25门禁通过**：原R6执行方22项加普通关闭来源、数据文件保存观察和无timer三项。主进程观察窗口为2026-10-15 11:31:09.300—11:31:34.318+08，25018ms；驱动收尾结果于11:31:39.614记录。直接固定Node spawn(shell:false)，Playwright仅附加本轮动态loopback CDP。没有Electron launcher、app.asar启动、PID提升或第二次运行。

新虚拟profile在启动前明确quit、closeHintShown=false、companionVisible=true；删除继承MARIS_E2E_EXIT_MS。驱动总上限120秒，关闭前阶段上限90秒，每次页面就绪观察不超过5秒。只调用一次recover、一次虚拟草稿enqueue，不触发真实provider或财务写入。

| 阶段 | 后台结果 | 真实页面结果 |
| --- | --- | --- |
| 初始就绪 | managed/online/authenticated=true、errorCode=null；唯一enabled daily_finance及canonical daily_finance.assistant@1 | daily/Shell/导航/Agent/daily导航均exists=true、count=1、visible=true；hash=#/daily、readyState=complete |
| 恢复前设置 | 无额外恢复 | hash=#/settings、theme=dark、privacy=on；Shell/导航/Agent可见；daily count=0为设置页正确状态 |
| 唯一recover后 | 再次在线认证、同canonical模块 | 设置hash/theme/privacy和Shell/导航/Agent保持 |
| 切回日常页 | 后台单独记录 | 首次采样daily count=0；约71ms后count=1、visible=true，Shell等始终可见；在5秒门限内通过，保留中间态 |

真实主窗口和毛毛、两侧窄bridge、renderer Node隔离、安全/隐私、owner和数据库均通过。旧独立模块13节点、冷入口B、完整R7恢复和旧EXE/W1没有重跑。

关闭来源使用spawn root的准确PID、EXE路径、创建时间、父进程、marker及新profile/CDP共同核对；EnumWindows找到唯一可见Maris主窗口和1个可见毛毛。一次WM_CLOSE于 **11:31:33.8178995+08** 成功投递，root于 **11:31:34.318+08** 观察到自然 **exit0 / signal=null**；按驱动毫秒时间戳计算 **501ms**，小于10秒。没有自动退出timer、timeout或强制清理，未延长生产owned stop的5秒预算。

PostMessage成功只证明投递，不伪称已直接观测到真实main内部handler计数；正常退出与开发层真实接线红绿分别提供证据。最终登记的本轮产品/毛毛/owned进程0、监听0、全部顶层窗口0，包含观察到的2个Python后代。子进程原生退出码均保持unknown，不能用root的0代替。Tray关闭以进程树消失作有限推断，不宣称真实Tray点击或Windows注销验证通过。

## 数据与资源保留

新虚拟未完成草稿只通过现有窄桥接enqueue一次。关闭前后设置均412bytes、SHA-256 `c4a59c9ec06fe45910a5eab4d1bf0e9a438856cdcd064489f7cd9b6c055ff622`，安全字段quit/falsehint/毛毛可见/dark/privacy=true保持，`.tmp`不存在。outbox均325bytes且无`.tmp`；关闭前SHA为`76343201b4bd5b0608e16423fa9f1bbc4451ee4d5abf58ad21116320c40ea77d`，关闭后为`1a7f0b1c49658525623fc20a96f231800c7e1745da34f304f4fa0af4c070d929`。cleanup重新seal可以改变密文，不要求密文hash相等；结合实际flush接线和相邻outbox保留回归，不冒称解密内容相等或重启持久化已独立验证。

新包、62文件虚拟profile、owner/db/outbox及原始记录全部保留。最终只删除新根`evidence/tests/tmp`内76个临时文件；删除前核实绝对边界、全部祖先及后代无reparse，删除后不存在。没有清理其他目录、volume或用户资源。

最终旧R6 source813/deps12443/full12677/dist73/out140/resources67/evidence172及R8-R1外部65全部匹配；新source932/full12677/dist73/out140/resources67和两驱动、62文件虚拟profile也匹配。931项起点中929项未改，只main与本人日志2项授权变化；新测试/本文/source清单3项新增，总交付5项。原`.claude/`、`.pnpm-store/`不动，staged=0，无Git写操作。

## 全部失败、警告和未验证边界

- 原实现red 1failed永久保留；最终定向48及full169均0failed/skip，TypeScript/lint exit0。开发日志未输出warning，不把这一点扩写为所有被测试代码内部都没有warning。
- 一次functions编排JS转义解析错误发生在工具调用前，无目标执行，已纠正；helper草案的Split-Path参数集问题在静态审阅中修正，未启动产品。
- 首次helper静态检查使用Windows PowerShell时因既有脚本签名策略拒绝，exit1、产品0次。保留`static-helper-first-failure.json`，按允许的一次定向纠正使用旧R8-R1同一路径的已安装PowerShell7.6.5；第二次AST/参数/C#声明编译通过。未设置ExecutionPolicy、未修改系统安全配置，不执行旧独立helper。两次静态检查都没有执行关闭或清理函数。
- 完整回归曾被自动审批额度限制拦截；内部辅助后续又遇模型额度限制。前者未执行、用户继续后恢复；后者没有新写入，由主执行完成。间隔不计连续运行。
- 只读Git产生用户ignore权限警告及LF→CRLF提示；清单始终计算原字节，不据此改行尾或Git状态。
- 新EXE原生日志保留一条`ERROR`：`GetGpuDriverOverlayInfo: Failed to retrieve video device`（126bytes日志，摘要`b1f9cf58c6e6e78c74e6cac5c313215fbda338ff78ad475f1b2fcf2a255aa24e`）。本轮页面、毛毛、退出均通过，未出现冻结崩溃码/页面错误或崩溃事件；不推断该日志根因或普遍无害，不扩展设备诊断。
- EXE console/pageerror/crash均0，Application/CodeIntegrity匹配事件0。原生stderr100bytes包含动态CDP身份，仅保留在本轮外部证据；敏感模式=false，不复制到产品界面或仓库日志。stdout2bytes，package stderr0且stdout无warn/error命中。

本轮执行方证据提交review，不自行关闭QUIT-001、CMP-03、SUP-05、LAZY-001/UI-02/P4-B，不启动测试方、技术顾问、真实provider、Docker/OpenClaw/微信或后续任务。真实Tray/Windows注销、真实chunk/session故障、重启持久化和独立验收没有执行。

## 最终清单与复算

停止修改后生成`apps/desktop/b7-r7-quit-source.sha256`：**933项**，为931起点更新授权摘要，加新测试及本文，排除清单自身。UTF-8无BOM、LF、路径ordinal排序，每行`POSIX相对路径<TAB>原字节SHA-256<LF>`。读取每行路径并重新计算原字节SHA-256可核对逐项；对清单本身原字节计算SHA-256得到可复算总摘要。

source自身及5项交付逐文件摘要位于新根`evidence/inputs/delivery-five.sha256`，总数/总摘要与构建、产物、测试结果见`evidence/inputs/closeout.json`；避免把本文自身摘要嵌回本文形成循环。外部证据清单`evidence/evidence-manifest.sha256`包含其余证据文件，排除清单自身。

主要证据均位于新根`evidence`：`tests/{red,directed,full}.json`及各自exit/source/observations、`inputs/prepackage.json`、`package-result.json`、`static/result-v4.json`、`static/main-quit-source-binding.json`、`inputs/final-driver-freeze.json`、`final-exe/result.json`、`final-exe/raw/driver-events.jsonl`和原生close回执、`inputs/final-immutable-audit.json`、`inputs/temp-cleanup.json`、`inputs/closeout.json`。执行方至此停止，交总控核对。
