# P4-C12-R9-QUIT：正常退出独立复验与剩余Windows验收

## 唯一负责人、必读与边界

你是既有测试智能体，本任务唯一负责人。执行方R7已review/finished并停止，技术顾问停止。先按AGENTS读取README、project-coordination、coordination/README、最新control、本人tester及本卡，再读：

- [总控核对](../../p4-b7-r7-quit-coordinator-review.md)、[R7执行说明](../../b7-r7-quit-running.md)、[R7实现合同](p4-b7-r7-quit-executor.md)及实际main/新开发测试。
- [R8-R1独立报告](../../testing/phase-4-c12-r8-r1-modules-windows-report.md)、其windows-W1首次result/journal、windows-first-analysis、windows-plan与实际Windows driver/OS helper。旧材料只读，不启动旧包。
- [R8 Windows合同](p4-c12-r8-modules-windows-tester.md)第二阶段、IF-003/004/005、[原矩阵](../../testing/phase-4-modular-agent-host-test-matrix.md)、[人工清单](../../testing/phase-4-c12-manual-checklist.md)。本卡替换旧输入、写入范围、前置集合及本轮预算；原业务要求不变。
- [新固定起点](../snapshots/p4-c12-r9-quit-start.sha256)：仓库根、原字节、POSIX路径排序、UTF8无BOM、path<TAB>sha256<LF>，不含自身。接单前全部匹配且staged=0，再更新本人状态。

UI-01与旧模块13节点、冷入口B、R7五组恢复/注册结构、旧outbox/registry集合及R8-R1六项公开通过保留，不重复执行。退出修复影响的必要新独立边界与相邻兼容明确单列。当前不是P4-C前端设计任务。

可写仅：

1. 新 `tests/independent/desktop/r9-quit-*` 测试、配置、controller/reporter与Windows工具。
2. 新 `tests/independent/desktop/evidence/r9-quit/**`，首次源码/回执/日志分attempt保存，已有首次记录不覆盖。
3. 新 `docs/testing/phase-4-c12-r9-quit-windows-report.md`，本人 `docs/coordination/agents/tester.md`。
4. 原C12主报告及人工清单仅追加；矩阵仅更新P4-B实证状态/备注，120ID、12列、原预期和A/C/D保持。

其他角色、控制/overview/snapshot、全部旧独立材料、产品/开发测试、依赖/lock/Forge/包只读。无Git写权限，不安装/下载/audit、构建、重打包、修改asar或production fuse，不增加产品接口、开关或测试专用旁路。

## 固定新包与新虚拟环境

唯一受验根 `C:/MarisQuitR7/R7-20261014-191500`，EXE位于其 `workspace/apps/desktop/out/Maris-win32-x64/Maris.exe`。新虚拟根 `C:/MarisC12/C12-R9-QUIT-<时间戳>`，cache/profile/DB/输出仅写新根，旧R7/R6及旧测试profile不读秘密、不回写。仓库只存脱敏标量；原始动态端点/加密文件保留受限外部根。

| 固定输入 | 清单或SHA-256 |
| --- | --- |
| 仓库R7 source 933项 | `apps/desktop/b7-r7-quit-source.sha256`：`3dc1f54d632de331515404174bce8686f03114da4695e5a8bb8d5a8c89af0f46` |
| 构建932项 | 新根`evidence/static/workspace-source.sha256`：`e7cec440e4420bec3f6fec274b6521ecd413d0d4c4fc1f304a584823ea9732a0`；基准新根workspace |
| 140项产物 | `evidence/static/out-manifest-v4.tsv`：`1953b0f91d94b4d64850d4d81c5da8c803bb1da5eebda6bf32eda64935214521`；基准包根 |
| 67项资源 | `evidence/static/python-resources-v4.tsv`：`324845f07f050f2b90e3c1e0b89b6598c8748aca549f8f848b600d5a2a0da5d1`；基准包内resources |
| 73项dist | `evidence/inputs/electron-dist-final.sha256`：`ffb4b389d5c454ca139cb6384f5ebb3d20633cf000960a8aa1b6c1794c9ebf8f`；基准workspace/node_modules/electron/dist |
| 完整12677项依赖 | `evidence/inputs/old-r6-full-node-modules.sha256`：`035c05bffbbf5f297ac098e7fbda16d5bd48cf76a89e4036c3dc35ddb64b3ef8`；该库存同样绑定新根workspace/node_modules，不因文件名含old就运行旧包 |
| EXE / asar | `183758e3b25a5314da8bea157f92ec00385e9ed6e18f42bac1ad679cdd6f6a65` / `16f45da665693e9b606ffb6b839081a48fa6ed4ae3e4995b403f57237118aed3` |
| lock | `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |
| R7外部157项证据 | `evidence/evidence-manifest.sha256`：`63a94a2177dbe0107f1c9ea327d9d26b694137a91824d2733ad038aaf9d99615`；基准evidence |

上述“新根”在表中指固定R7受验根，非R9虚拟根。固定Node24.21.0、pnpm12.7.0、Electron44.4.5、Playwright1.63.0、Python3.14.7，复用已有普通工具与依赖。需要jsdom时沿用已验证原生createRequire入口，不再试旧转换器加载路线。普通物化先核实绝对路径和无reparse，不用junction、不改永久PATH/系统安全设置。

接单/结束复算新起点、受验输入及旧首次源码/证据。R7仓库933清单中README、project-coordination、control、overview、brainstorm五项为本轮总控协调变更，按来源列举；其余必须匹配。旧测试清单中的tester、主报告、人工清单、矩阵四项在本任务后允许指定更新；原首次记录/旧测试源码始终不变，不声称包含共享文档的整个旧清单字节不变。

## 第一阶段：独立退出边界与有限兼容

针对这次main diff独立设计一组公开生命周期测试。实际导入main和现有composition，外围Electron/窗口/系统及owned backend可控；不得复制生产退出函数或只断言shutdownStarted内部变量。app.quit替身要触发已注册before-quit、尊重preventDefault，最后窗口销毁触发window-all-closed；只spy app.quit不能证明退出。

最小覆盖可按生命周期合并，不为了增加节点拆分：

- quit、首次提示未显示、毛毛可见时的主窗口close确实触发统一退出；pending flush/owned stop完成前不提前销毁，完成后自然收尾。必要的hint/毛毛邻接变体保留。
- 重复close、退出中Tray请求、最后窗口销毁引起的重入：保存/停止不重复，最终退出一次，无无限循环、未处理拒绝或额外业务副作用。
- hide/首次提示及ask已提示后的取消/隐藏/退出保持；迟到提示响应在退出或窗口销毁后不改变状态。不会新增recover、provider、撤销、财务写入。
- 停止拒绝不能伪报成功或泄漏原错误；虚拟session-end/Tray只记组件证据，不冒称真实注销/托盘验收。

先冻结节点ID、公开要求/原预期、输入及日志。正式组运行一次；原生初始化60秒、每节点15秒正文/5秒清理、CLI300秒上限。正式比较必须即时保存唯一ID、operator、安全expected/actual、阶段/耗时与enter/terminal；工具错误、产品比较失败、unknown、cleanup分别记录。标量/ID自检在产品导入前完成，故意错误仅用于selftest，不能污染正式首错或豁免正式失败。

通过后仅一次相邻开发兼容：`main-quit.test.ts`、`composition-root.test.ts`、`outbox-retention.test.ts`、`supervisor-outbox.test.ts`、`window-lifecycle.test.ts`，固定 **5文件48项**。与独立结果分列，不跑完整169、模块13/旧28兼容、Python或旧B/恢复集合。

## 第二阶段：原退出失败的新包独立复验

前置通过后，使用新 `r9-quit-*` 副本沿用测试方R8-R1 W1的公开检查与退出失败断言；只适配固定输入/新输出路径及必要记录补强，保存最小diff。不得把执行方25项runner换名当独立证据，也不得先启动额外产品“试一下”。

本轮W1须保留原 `W1-NORMAL-EXIT-OBSERVED` 的期望true、普通主窗口关闭入口和10秒上限。新虚拟profile启动前quit、closeHintShown=false、companionVisible=true；显式删除继承MARIS_E2E_EXIT_MS。原先成功的页面/auth等作为这一复验的前置来源，不能计作新独立节点。真实daily/Shell/导航/Agent的exists/count/visible/hash/readyState与backend/modules单列，观察最多5秒，未知不能写成0。

仅Node spawn(shell:false)启动固定新EXE，Playwright只附加owned动态loopback CDP。无Electron launcher、PID提升或product app.quit注入。核实root路径/创建时间/父子/profile及唯一主窗口；投递正常WM_CLOSE，记录投递来源，随后最多10秒观察root自然exit0和owned Python/端口/窗口消失。生产owned stop的5秒预算不改。没有退出计时器、强杀或辅助退出代签；强制收口只能记失败后的安全清理。不能因主进程0就给未知子退出码补0。

独立关闭逻辑的观察成功后可建议关闭QUIT-001，但不据此签收CMP-03、SUP-05的全部原要求。原R8-R1失败永远保留，不用新包成功倒写旧结果。

## 同任务继续剩余Windows条件

W1通过且资源关闭后，无需再次请求派发，按冻结的新覆盖计划继续原剩余条件。**本轮最多8次产品、4次safeStorage辅助**；这是修复包1次必要复验及原计划尚缺条件的合计上限，不能因切场景或改任务名增长。单实例第二进程计一次产品启动，旧包不再启动。每产品最多120秒，每辅助60秒；每次事先列新增覆盖、profile关系、退出入口及不重复依据。

1. 后续启动复用本轮W1虚拟profile，验证真实owner/session连续性、设置及同请求ID跨重启；设置/草稿文件存在或密文摘要不同都不能替代实际重新读取的安全count/digest/ID比较。原请求ID和正文只留受限虚拟现场，仓库保存脱敏相等布尔/摘要。
2. 合并单实例第二启动、首次关闭提示、hide/ask/cancel/quit、毛毛恢复与Tray等尚缺条件，保留原第一次提示优先级。原生按钮只能通过已核实owned PID/窗口/按钮标识的UI Automation，禁止全局坐标盲点。E2E抑制的真实行为要明确未验证，不能用API替代Tray点击证明。
3. 原生老化提示可用本轮safeStorage辅助对纯虚拟fixture seed/read/count/digest：超过30天默认保留/取消/明确删除后的有限持久化；不改系统时钟，不读旧profile，不改包。4次辅助总预算先分配，不能临时追加“观察”启动。
4. 尚缺的owned后端故障/恢复、安全入口条件沿用原R8限定owned环境与接口。只能作用本轮经核实的虚拟进程，外来对照不得采用用户程序。
5. 真实chunk注入仅允许本轮实际chunk请求的临时CDP拦截，并取得命中、当前有效失败、局部错误/会话保持、撤销后明确retry成功。不得改asar、删chunk或塞假页；file/asar/cache等使注入不成立时记录具体限制，保留unverified，不反复冷启动追求命中。

工具/设备条件明确不具备只阻塞对应条件；资源安全关闭后继续无依赖计划条件。产品真实比较失败、来源有效却行为不符、安全/所有权/收口问题则停止扩大。无真实系统注销/重启、启动项/OS主题/多屏更改或用户立即点击授权，仅更新人工清单。Docker/微信V002/OpenClaw/真实provider不运行。

## 有限工具更正与首次证据

目标前先检查语法、Windows参数/UTF8/CRLF、输入清单、输出路径与唯一断言ID，代码在正式运行前冻结。不要再建通用取证框架或固定进程数预算。

本卡允许 **最多一次已证实的纯工具修正**：仅ID、记录、文件读取/汇总或配置传递错误，且原目标尚未启动；或组件测试已启动但没有失败的产品/来源/安全比较、阶段记录完整且组件/worker清理可证。保留原源码/首次结果，新attempt给最小diff，不改变selectors、expected、业务操作或时限；仅续跑被中断的完整组件节点及未执行节点，已通过节点不重复。仅凭缺日志不能认定纯工具错误。

Windows产品启动后不适用重跑授权；未知异常、超时、业务比较失败不得归类工具问题逃过停止。结束后的文件命名/汇总错误可只读补证，不重启目标。辅助/产品实际启动即计预算，审批未执行不计。

## 报告、矩阵与停止

提交增量报告：独立退出节点、48兼容、本轮每次Windows/辅助的新增覆盖、实际比较及首错、normal/forced退出、日志/设备限制、历史复用来源和24项剩余缺口。不要再次复制全部旧报告/清单。原生GPU overlay ERROR按实际发生记录，不隐藏、不自动扩大根因调查。

完整行所有原条件有独立证据才更新passed；可把原缺陷修复通过但尚有设备条件的行更新blocked并写明缺口，不机械保持旧failed，也不预设必须全绿。UI-01保持已有接受结论；LAZY-001/UI-02、CMP-03、SUP-05、P4-B分层提出建议，最终由总控裁定，不改原预期。

起点、固定外部包/依赖/旧首次记录终点复算，仅列授权共享文档变化。保留新虚拟profile和首次材料，只清理本轮核实绝对边界/无reparse的临时项。root/worker分别记录退出范围；系统枚举受限保持unverified，禁止按名称批量终止。

接单/里程碑/阻塞/收口更新本人快照，超过5分钟操作先记下一检查点，有控制时至少10分钟心跳；中断不伪造持续执行。最终review/finished或blocked/finished后停止，不自行启动执行方/顾问/P4-C/D。前端参考图与模型策略提醒由总控在真正界面阶段触发。
