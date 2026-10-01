# P4-C12-R1：outbox 独立复验与剩余 Windows Shell 验收

## 唯一负责人和目标

你是既有测试智能体，唯一负责本任务。R2-OUTBOX 已完成开发修复、自测、新 package 和最终 EXE；总控接受为独立输入。P1 `P4-C12-OUTBOX-001` 尚未独立关闭，P4-B 未 complete。

先独立复验该 P1，再继续原 C12 尚未完成的 24 项矩阵。沿用原案例 ID/预期与证据分层，不重新设计矩阵、不实现产品。正常交付 review/finished；发现产品 P0/P1 或不能安全收口时 blocked/finished。最终接受属于总控。

## 必读与起点

按 AGENTS 读取 README、project-coordination、coordination/README、最新 control、tester、本任务卡，再读：

- `docs/p4-b7-r2-outbox-coordinator-review.md`
- `docs/b7-r2-outbox-running.md`
- 原 C12 Prompt、报告、人工清单及 C12-PUB-11 首次失败 log/JSON
- IF-003/004/005、本地单主人范围决定、P4-B 矩阵
- `docs/coordination/snapshots/p4-c12-r1-start.sha256`

新任务覆盖 tester 的旧 C12 blocked 当前步骤；复算新起点并记录接单/摘要/步骤/心跳。Git staged 必须为零。原 C12 起点和 R2 source 为历史清单，不因新协调状态变化重跑旧 audit 或修改旧摘要。

## 允许写入与不可变材料

仅允许：

1. `tests/independent/desktop/` 下新增 R1 独立用例、配置/审计/有界 runner 和 `evidence/r1/**`。
2. `docs/testing/phase-4-c12-r1-outbox-windows-report.md`。
3. 原 C12 主报告，保留原缺陷/首次结果，追加 R1 结论与链接；不得把首次失败改写为通过。
4. 原人工清单的实际状态与证据链接，不删除未覆盖条件。
5. 原 P4 矩阵仅 P4-B 状态及证据备注，原 120 ID/预期、A 64 passed、C/D 32 not_run 不变。
6. `docs/coordination/agents/tester.md`。

原 `public-boundaries.test.ts`、`vitest.config.mjs`、`audit_inputs.py` 及原 `evidence/` 中已有八项交付全部只读。为新环境新建 R1 config/audit，不改原路径/输出设置、不重用旧 audit 硬编码清单或旧 EXE 摘要。禁止覆盖原 log/JSON。

产品、执行方测试、依赖、lock、生成物、构建、migration、Compose、冻结、control/overview/snapshot 和其他角色文件禁止写入。仅上述既有报告/清单/矩阵/tester 可在起点中变化；新增单独列出。Git 只读，不启动其他角色，不创建新任务或 P4-C。

## 新环境与受验产物

只读使用新普通 workspace 和固定 Node/pnpm/Playwright/Vitest/Python：

`C:\MarisOutboxR2\R2-20261001-155509`

新 EXE：`workspace\apps\desktop\out\Maris-win32-x64\Maris.exe`。

| 对象 | 固定 SHA-256 |
| --- | --- |
| EXE | `8eb56f3f63b923471a9239e2a01f29a8111067a6093d8c9d118e62e1ccfb5c2a` |
| app.asar | `74225ea63dbc7201dc7f7f3299a099ac573f51680ef705536e560a9d9df6b6c7` |
| lock | `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |

受验包、旧 R2/LOCALZIP evidence/profile/out/依赖全部只读。新的 dynamic evidence/profile/虚拟数据库在全新 `C:\MarisC12\C12-R1-<时间戳>` 下建立，先核对解析后绝对路径在专属根内，外部写入按工具审批处理。不得载入真实 AppData、个人消息/财务、真实凭据或旧 owner session。

不重新安装、build、package 或联网 audit。不改 PATH 永久设置、TUN/代理、系统安全、production fuses 或系统时钟。现有 repo 无 node_modules，R1 config 指向新 R2 普通依赖；使用 plain config/已安装 loader，避免重复 vitest/config 解析错误。

## 第一阶段：P1 独立复验

首先只运行**原 C12-PUB-11**的原断言一次，新 config 输出到 `evidence/r1/original-node/`。若仍失败，原样保留并停止，不继续 Windows。原 log/JSON 不覆盖。成功后再执行原其他十个公开节点（排除已运行 PUB-11），输出另一个 R1 目录，独立统计不重复计数。

新增自有公开行为测试，覆盖：

- draft/queued/sending 在 30 天、+1ms、远超期限经过 load/start cleanup/退出 cleanup/reload 均保留正文/digest/原 ID；terminal 24h/+1ms 行为保持。
- 没有候选不提示；严格 >30天仅 draft/queued；一次启动最多一个提示，默认/取消保留，提示无正文/ID。
- 取消、关闭、dialog rejection、shutdown、window destroy 均保留；明确确认仅删除当次仍未变候选。
- 未决 dialog 中 prepare/state 更新、同一时钟更新/reload、sending/新条目保护和重复确认边界。
- prepare/state/cleanup/delete 保存失败时内存/持久状态一致；队列能继续；20 条容量仍明确拒绝，ID/加密语义保持。
- main 原生 dialog adapter 与 Host startup/lifecycle 接线。测试方自有 fixture/断言，不能复制执行方测试改名；模拟结果与真实设备证据分开。

公开函数和注入行为足以证明原 P1 的持久删除逻辑是否关闭；真实原生提示尚未测时单独列为设备覆盖缺口，不能称全部 Shell 已通过。所有 fixture 只含虚拟数据。

## 第二阶段：继续原 C12 矩阵

第一阶段全过后继续原 C12 中未覆盖的安全、registry、IPC/HostClient/session、supervisor、outbox、设置、主题、毛毛、lazy route、生成物及 staging/ZIP 行为。原 C12 Prompt 未被本文明确替换的边界继续有效；本任务使用新版本、新快照与新输出，不能直接重跑旧命令覆盖结果。

相关执行方 outbox/main 定向 27 项可一次兼容复跑并单独统计；完整 90 项已有可信开发证据，不无理由再跑。只有新的改动/失败关联才能扩展相邻回归，不重跑 P0～P3/Host/Python 全量、不用执行方测试替代独立案例。

真实 EXE 仅 Node direct spawn、shell false、Playwright 仅 loopback CDP 附加。独立 runner，不使用 `_electron.launch()`、app.asar loader、PID promotion、宽泛 kill 或精确进程数预算。明确 owned process/路径/创建时间/profile；每个产品场景 <=120秒，本任务最多8次有计划产品启动，单实例第二次计数。

运行前在 tester 日志列出有限场景与预算，避免重复成功项。已有 E2E 自动退出参数仅支持 1000～30000ms；需要用户关闭策略观察时不设置该自动退出，runner 自己仍施加120秒上限并按正确退出入口收口。不修改产品去扩展测试参数。

优先新 EXE 主链路：双窗口、sandbox/contextIsolation/Node隔离、窄bridge、安全日志、managed/online/authenticated、daily_finance/canonical Profile、一次recover、毛毛/openMain、自然退出与零owned资源。之后必要单实例、closePolicy/Tray等场景。通用 provider `/readyz` fail-closed 不等于 desktop readiness 失败。

## 真实老化原生提示：单独设备证据

允许为本任务新隔离 profile 准备符合原 outbox JSON 格式的**虚拟**老化 draft/queued、sending、新鲜条目，使用已验证 C盘 Electron dist 的真实 safeStorage 生成/读取加密 fixture；不改变受验 asar/EXE 或生产接口。辅助 Electron 只做专属根内 seed/read/count/digest，Node direct spawn，不使用 Playwright Electron loader、不创建用户窗口或访问旧 profile，最多4次、每次<=60秒，有完整owned/退出核对。

不能把模拟加密 blob 交给真实应用或绕过 safeStorage；如果无法安全准备真实加密 fixture，停止该设备分项，保留 unverified 和具体阻塞，不擅自改系统时钟/注入产品脚本/新增删除 IPC。

使用新包在该虚拟 profile 观察真实原生提示。若能可靠自动化，只能通过 Windows UI Automation 精确限定本轮owned窗口、标题/按钮/进程后操作“保留”或“明确删除”；禁止通用鼠标坐标或操控其他程序。至少区分保留/关闭后的持久保留与明确确认后的有限删除，以辅助读取验证，记录安全截图/数量/摘要，秘密和原始会话不入报告。

原生对话框不属于 CDP 页面，不能因为 CDP 只看见两页而声称已测。若需要用户点按钮、真实Tray菜单、多屏、注销/启动项等动作，本轮先列人工步骤与待验收项交回总控，不直接要求用户立即操作或自行改变OS设置。尚未具备人工条件不冒充 passed，也不凭空增加产品缺陷。

## 结果、停止及日志

完整保留首次问题和 warning。无目标启动、无副作用的配置/证据读写错误允许一次定向修正；产品断言失败不重跑覆盖。未知ownership、失控异常弹窗、真实秘密泄露、P0/P1、无法收口或同阻塞两检查点无新证据时停止扩大测试、安全清理并交回总控。

每个原 ID 逐项给出完整预期、实测子条件、证据层级、节点/产物绑定、缺口和状态；部分成功不得整项 passed。原 SUP-06 风险等级保留，缺陷P1关闭建议与整个SUP-06/P4-B接受分开。

新报告记录：独立复验及新增节点、兼容测试、24项原矩阵、人工/设备未测项、新清单起终点/授权变化、原失败材料不变、新EXE/asar/lock/fuses前后不变、产品/辅助启动预算、进程/监听/窗口收口、隐私、warning和建议。建议关闭P1须链接实际持久化复验。

接单、阶段进展、动态开始/结束、阻塞、交付更新tester快照；长操作前下个检查点，可控制时至少十分钟心跳。只清理自己已核对绝对路径的临时内容，保留可复算安全证据。不启动Docker/PG/OpenClaw/微信/DeepSeek/真实provider，不重复V002或扫码，不执行Git写操作。

完成交 review/finished 或 blocked/finished 后停止，不自行宣布 P4-B complete、不创建新返修任务或 P4-C。执行智能体与技术顾问保持停止。
