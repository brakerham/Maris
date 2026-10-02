# P4-C12-R3：路径缺陷独立复验与剩余Windows验收

## 唯一负责人与目标

你是既有测试智能体，唯一负责本任务。R4-ROUTE已由总控核对为稳定输入；PATH-001仍待独立关闭，OUTBOX-001及设置键REGISTRY-001已独立关闭，不重复处理。先复验原路径失败和必要注册边界，成功后继续原24项未执行公开行为/Windows条件。

新任务覆盖你旧C12-R2 blocked等待步骤。正常交review/finished，发现产品P0/P1或无法安全收口交blocked/finished；最终验收属于总控。不得创建后续任务、启动其他角色/P4-C或执行Git写操作。

## 必读与起点

按AGENTS读取README、project-coordination、coordination/README、最新control、tester与本任务；再读：

- `docs/p4-b7-r4-route-coordinator-review.md`、`docs/b7-r4-route-running.md`及UI-04开发映射。
- C12原任务、R1/R2任务与报告、原主报告、人工清单、120项矩阵中24项P4-B完整预期。
- IF-003/004/005、本地单主人范围；R2首次路径失败代码/log/JSON。
- `docs/coordination/snapshots/p4-c12-r3-start.sha256`。

开始前逐行复算新起点、staged=0；登记接单、当前步骤、时刻/心跳和下一检查点。旧清单与历史审计只读，不用旧根/摘要套入本轮。外部操作前重读control，较新指令优先。

## 精确写入授权

1. `tests/independent/desktop/`新增`r3-*`测试/配置/审计/有界Windows runner与helper；新增`evidence/r3/**`。
2. 新`docs/testing/phase-4-c12-r3-route-windows-report.md`。
3. 原C12主报告和人工清单只追加R3事实/链接，原字节prefix保留。
4. P4矩阵仅P4-B实际状态/证据备注；原120 ID、完整预期和A64 passed、C20/D12 not_run保持。
5. 自己的`docs/coordination/agents/tester.md`。

所有旧public-boundaries/r1/r2测试配置、报告和evidence（失败与通过）只读，尤其不改原r2-remaining.test.ts断言。产品、开发测试、依赖/lock/产物、build/package、迁移、Compose、冻结、control/overview/snapshot和其他角色禁止修改。R3新增单列；新起点只允许上述原主报告/人工清单/矩阵/tester变化。

## 受验新包与普通依赖

只读工具/普通node_modules/包根为`C:\MarisRouteR4\R4-20261002-164600`。固定Node24.21.0/pnpm12.7.0/Electron44.4.5/Playwright1.63.0和已验证Python沿用，不install/download/audit/build/package。

受验EXE为`workspace/apps/desktop/out/Maris-win32-x64/Maris.exe`；SHA-256：

- EXE `d5868736cbdf63f717f0ea853141b980d06cefc10a3c05196e8856cbe3a4de2b`。
- resources/app.asar `9a4da50b2c5583e6f2337bdff43e399cd454c360fa6169b1667a1e4506c337d4`。
- workspace lock `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。

先复算source/out/resources/fuses与固定值。R4/R3/R2/LOCALZIP源码、工具、依赖、包、profile/session/db/evidence只读。独立动态数据/证据用新`C:\MarisC12\C12-R3-<时间戳>`，验证解析绝对路径属专属根、无链接；外部写入按工具审批，不读真实AppData、不改永久PATH/系统时钟/TUN/代理/安全配置/fuses。

## 第一阶段：原路径失败与UI-04独立核对

新R3 config使用R4普通依赖；唯一一次执行旧`r2-remaining.test.ts`精确节点`R2-UI-04-PATH`，原文件/断言不变，新输出放evidence/r3/original-path。失败保留原结果并停止，不进入动态阶段。

通过后新增公开输入的必要独立边界：跨模块交换顺序、同模块不同ID同path、末模块/末route冲突、不同path成功、route ID不因path检查失效、输入不变/无部分输出/失败后合法编译。用虚拟贡献、公开compileRegistry行为，不复制开发测试或内部seen实现；不新增真实业务模块。

按原UI-04完整冻结条件作独立证据映射。沿用已通过且输入不变的设置键/其他注册独立证据，补此前未覆盖条件；开发映射只能定位，不能成为独立通过证据。结构检查和实机行为分别标记。路径合同限完全相同字符串，不新增大小写/尾斜杠/动态模式归一化要求；实际未冻结歧义带具体代码/风险交总控，不假称全通过或擅改产品。

原outbox42节点、已关闭setting及原R2成功15节点不受path改动影响的不重跑。允许registry开发52项一次兼容复跑并单列；不跑完整124或Python/P0～P3/Host全量。新增独立行为结果与兼容分开计数，不重复累加。路径独立通过只支持PATH-001关闭建议，不直接替代整个UI-04/P4-B通过。

## 第二阶段：未执行公开行为和Windows

第一阶段通过后，以C12-R2报告的原24项逐项缺口接续剩余公开边界和真实Windows；原C12/R1/R2任务中未被本文明确替换的范围继续有效。优先取得安全自动证据，再列实际人工条件。每ID列完整原预期、既有证据及来源、此次新增、尚缺条件和真实状态；不把部分成功/单元/静态证据替代设备条件，不预写B全通过。

产品由固定Node spawn(shell:false)直接启动新EXE，Playwright仅动态loopback CDP观察。禁止_electron.launch/app.asar loader/PID提升、开启production inspect fuse。按路径/创建时间/profile验证owned树，不设精确进程数量门禁、不把正常GPU/conhost派生当失败。

本轮最多8次有计划产品启动（单实例第二次也计入）；每场景<=120秒。运行前日志列目的、覆盖条件、预算和正确退出入口；先安全/认证Host/daily_finance/canonical Profile/recover/毛毛，再必要单实例、关闭策略、设置/Tray等。不是必须用满预算，也不重复成功场景。产品自动退出仅1000～30000ms；长场景不设该timer，保留runner硬时限并通过正确退出入口安全收口。

真实Tray菜单、普通closePolicy、注销/启动项不能由自然exit或PID=0代替。E2E抑制的OS行为不当实测；external_dev只用自建虚拟adapter/backend，不接管用户服务。账目/消息/身份/provider均虚拟，不访问真实模型或账户。

## 原生过期提示与人工条件

沿用C12-R1/R2授权的隔离safeStorage seed/read方案，但全换本轮新虚拟根与R4包；最多4次辅助Electron、各<=60秒，仅无用户窗口的虚拟加密fixture seed/read/count/digest。使用固定dist/direct spawn，不读旧profile，不注入产品/新增IPC。

真实原生dialog自动化只能Windows UI Automation限定owned PID/标题/按钮，禁止全局坐标和控制其他程序。默认保留/取消/关闭及明确删除后的有限持久化结果分别取证；普通双窗口正常不替代真实老化提示。不能安全准备fixture或操作dialog则记录准确unverified/人工步骤，不能改系统时钟或冒称通过。

真实注销/重启、修改启动项、多屏切换/拔屏、改OS主题、要求用户立即点击均不在本轮授权内，准备单步人工清单交总控。缺少现场条件不虚报产品故障，也不删除/降级原预期，相关整项保持blocked/not_run并解释。

## 有限修正、停止与交付

目标启动前无副作用配置/语法/映射错误允许一次定向修正、保留首次结果；不人为拆新任务。目标业务断言失败保留，禁止重跑覆盖；退出后的读取/标签问题只读补证，不因此重启产品。产品P0/P1、失控异常/泄密、未知ownership、不能收口或同问题两个检查点无新证据时停止扩大测试、安全收口。禁止按全局进程名杀其他程序。

接单/里程碑/动态开始结束/阻塞/交付更新自己的快照；长操作前检查点、有控制时十分钟心跳。报告包含原路径节点及关闭建议、独立/兼容分列、24项完整映射、人工缺口、旧证据和新包/lock/fuses起终不变、起点与授权边界、实际启动次数、进程/监听/窗口最终状态、首次失败/warning。

保留脱敏可复算材料；profile/session/db/blob/raw端点/个人内容不进仓库。清理前核对绝对专属路径、无链接，只清理自有临时项。不Docker/PG/OpenClaw/微信/DeepSeek、不重复V002/扫码、不Git写入。交review/finished或blocked/finished后停止，不宣布P4-B complete或创建下一任务。
