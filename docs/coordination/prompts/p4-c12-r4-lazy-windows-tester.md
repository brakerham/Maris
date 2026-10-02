# P4-C12-R4：lazy隔离独立复验与剩余Windows验收

## 唯一负责人与任务

你是既有测试智能体，唯一负责本任务。R5-LAZY已由总控核对为稳定输入，LAZY-001尚待独立关闭；OUTBOX-001、设置键REGISTRY-001和PATH-001已关闭，不重开返修。

先原lazy失败复验，再独立检查隔离/恢复，成功后接续原24项未执行公开行为/Windows。新任务覆盖自身旧C12-R3等待步骤；review/finished或真实阻塞blocked/finished后停止。最终验收属于总控，不自行创建下一任务/启动其他角色/P4-C，不Git写入。

## 必读与权威起点

按AGENTS读README、project-coordination、coordination/README、最新control、tester和本任务；再读：

- `docs/p4-b7-r5-lazy-coordinator-review.md`、`docs/b7-r5-lazy-running.md`及UI-02完整开发映射。
- C12/R1/R2/R3任务、报告、原主报告/人工清单、原24项完整预期，IF-003/004/005与本地单主人范围。
- 原`r3-remaining.test.tsx`、evidence/r3/remaining-independent首次log/JSON，实际renderer/main、module-routes、Shell。
- `docs/coordination/snapshots/p4-c12-r4-start.sha256`。

开工逐行复算新起点、staged=0，登记接单/步骤/时刻/心跳/检查点。**新起点是当前仓库权威；R5历史source390中的总控协调文件在派发后已更新，不能直接拿旧摘要assert当前仓库。** 旧受验包构建输入389/out140/resources67按外部不可变清单分别核对；原清单不改写。外部操作前重读control，新指令优先。

## 精确写入范围

1. `tests/independent/desktop/`新增`r4-*`独立测试/配置/审计/有界Windows runner/helper；新增`evidence/r4/**`。
2. 新`docs/testing/phase-4-c12-r4-lazy-windows-report.md`。
3. 原C12主报告和人工清单只追加R4事实/链接，原字节prefix保持。
4. 原矩阵仅P4-B实际状态/证据备注，120 ID/完整预期及A64 passed、C20/D12 not_run保持。
5. 自己的tester角色日志。

全部旧public/r1/r2/r3测试、配置、报告、evidence（失败/通过）只读，尤其原r3-remaining断言不变。产品、开发测试、依赖/lock/生成物、build/package、migration/Compose/冻结/control/overview/总控snapshot/其他角色禁止修改。不删除或降级验收条件、不用替代路由实现冒充产品行为。

## 固定新包与普通环境

只读根：`C:\MarisLazyR5\R5-20261002-222300`，复用普通workspace/node_modules、固定Node24.21.0/pnpm12.7.0/Electron44.4.5/Playwright1.63.0和已验证Python。不得install/download/audit/build/package，不改永久PATH/代理/TUN/安全设置/系统时钟/fuses。

受验EXE：`workspace/apps/desktop/out/Maris-win32-x64/Maris.exe`。

- EXE SHA：`64ce71f3a7b3055f9ad27f6d611e28c4af7e9ba8b86d8b21399b7b422844a80e`。
- resources/app.asar SHA：`5ba47909537e1419dc275fa3ca1e5e076a1aa6d5c0205229f91defb92ddd0931`。
- lock SHA：`5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。

R5/R4/R3/R2/LOCALZIP源码、工具、依赖、产物、profile/session/db/evidence只读，不使用旧虚拟profile或真实AppData。新外部证据/虚拟profile/db在`C:\MarisC12\C12-R4-<时间戳>`，先验证解析绝对路径属专属根且无链接，外部写入按工具审批。

## 第一阶段：原lazy失败和独立恢复

用新R4配置指向R5普通依赖，**唯一一次执行原r3-remaining.test.tsx精确R3-UI-02-LAZY节点**，不改旧断言，输出到evidence/r4/original-lazy。只改新增配置对模块解析的接线；产品main/Shell/Router/边界实际运行，原mock失败页面端口保留。若失败保留并停止，不重跑或进入Windows。

通过后编写自己的公开行为测试，运行真实生产main或其实际使用的DesktopApp/路由装配、React Router、Shell、模块边界。仅外围bridge/可信页面loader虚拟；至少失败和健康两route，注册器用实际compileRegistry，不创建生产第二业务模块。

独立覆盖：错误只在内容区域，Shell/导航/Agent仍在；健康页面和settings切换可用；用户明确retry重新loader且成功页面实际出现；持续失败无自动循环；在途重复点击有限、离开后旧结果不覆盖健康页面；页面render异常局部处理；主题/隐私/runtime与订阅不因retry重建，无整页reload/额外auth/recover/provider/outbox写入。检查安全DOM/console和真实调用/订阅变化，不能只看错误文案或复制开发测试/内部seen与attempt实现。

这些jsdom/虚拟端口结果明确单列，不能替代Windows真实chunk、真实session持久化。新helper路径是生产main实际使用入口，来源需要核对；只检测helper但没检查生产接线不算完整。

原27成功独立节点（path/UI04-ASCII/settings/ZIP/staging）、此前outbox42/setting/path已关闭证据输入不变时沿用。R5改变错误组件与路由装配，必要相关旧Shell/安全断言可定向复跑并说明关联，不重跑不受影响集合。允许新lazy开发8项和Shell/composition相邻一次兼容复跑单列；registry52不变不再跑、完整132/Python/P0～P3/Host全量不跑。

按原UI-02/04完整子条件映射独立证据和具体缺口，开发映射仅用于定位。先原失败及相关恢复，再完成仍未测的注册严格对象/结构等公开缺口；不凭部分成功把UI-02/04整项写passed。发现新实际P0/P1按停止门禁交接。

## 第二阶段：原24项公开缺口与Windows

第一阶段通过后，从C12-R3报告逐项缺口接续。每项列原完整预期、已有证据来源和输入关系、本轮新增、尚缺条件与真实状态。未被本文替换的旧C12/R1/R2/R3授权继续适用，但全部受验根/摘要以本轮为准。静态/单元不替代设备要求，原B0passed/1failed/19blocked/4not_run不预写全绿。

产品仅固定Node spawn(shell:false)直接启动冻结EXE，Playwright仅动态loopback CDP附加；禁止_electron.launch/app.asar loader/PID提升/启用production inspect fuse。owned树须按路径/创建时间/profile建立，不设精确进程数门禁，不全局kill。

本轮产品最多8次有计划启动（单实例第二次也计入），每场景<=120秒，启动前日志列覆盖条件/预算/退出入口。优先安全/Host/daily_finance/canonical Profile/恢复/毛毛，以及必要故障与关闭策略/单实例/设置/Tray。不是必须用满预算；普通成功场景不重复。产品timer仅1000～30000ms；长场景不设该timer，runner硬时限和正确退出入口仍需保留。

Windows chunk故障如能安全用**本轮owned页面/会话上的临时CDP请求故障注入**验证，只允许限定实际页面chunk请求，保留命中、真实失败、Shell状态和retry后的实际恢复证据，及时撤销拦截；不得修改EXE/asar/resources/受验源码、删除chunk、改变生产fuses、开启Node注入或使用test-only产品开关。file/asar请求若工具不支持、无法在正确阶段附加或浏览器缓存使故障不可控，先静态确认限制，记录具体unverified并交总控，不盲目追加启动，也不能以虚拟loader次数/正常smoke冒充设备通过。已有jsdom关闭证据和设备未覆盖分开。

真实session持久化仅用新虚拟owner/profile，不导出token正文；runtime在线或文件存在不能替代故障前后会话保持的实际证据。UI中不存在的公网注册/登录产品不新增。

真实Tray/普通closePolicy/注销/开机启动不能由自然exit或PID归零推导。E2E抑制的OS行为不当实测；external_dev只自建虚拟adapter/backend，不接管用户服务/真实provider。

## 原生老化提示与人工条件

沿用旧隔离safeStorage seed/read方案，只换本轮新虚拟根/R5包；最多4次辅助Electron、各<=60秒，仅无用户窗口的虚拟加密fixture seed/read/count/digest，固定dist/direct spawn，无旧profile读取/产品代码注入/新IPC。

真实原生dialog自动化只用限定owned PID/标题/按钮的Windows UI Automation，不全局坐标或操作其他程序。默认保留/取消/关闭与明确删除后的有限持久化分别取证；普通双窗口正常不替代提示。无法安全准备fixture/自动化则准确unverified/人工步骤，不改系统时钟。

真实注销/重启、修改实际启动项、多屏切换/拔屏、改OS主题、要求用户立即点按钮均未授权，准备单步人工清单交总控。缺少条件不虚报产品失败，也不删除/降低预期；整项保持blocked/not_run并解释。

## 停止、证据与交付

目标启动前无副作用配置/语法/映射错误可一次定向修正并保留首次结果，不人为拆任务。目标业务失败不重跑覆盖；收口后的读取/标签错误只读补证，不重启产品。新P0/P1、泄密/失控弹窗、未知ownership、无法收口或同问题两检查点无新输出时停止扩大并安全收口。

接单/里程碑/动态开始结束/阻塞/交付写自己的快照；长操作前检查点、有控制时十分钟心跳。报告原节点/缺陷建议、独立与兼容分列、24项完整映射和人工缺口、固定起终/旧材料不变、实际启动/注入次数、资源状态与首次失败/warning。已验证的缺陷逻辑关闭建议不等于UI-02设备条件或P4-B complete。

保留脱敏可复算材料，profile/session/db/blob/raw端点/个人内容不进仓库。清理前核对专属绝对边界/无链接，只清理自有临时项。不Docker/PG/OpenClaw/微信/DeepSeek、不重复V002/扫码、不Git写入。交review/finished或blocked/finished后停止，不启动下一任务。
