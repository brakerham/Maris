# P4-C12-R2：设置键缺陷独立复验与未执行 Windows 验收

## 唯一负责人和目标

你是既有测试智能体，唯一负责本任务。总控已接受R3-REGISTRY为新稳定输入，REGISTRY-001仍待独立关闭；旧OUTBOX-001已独立关闭，P4-B未complete。

先独立复验原设置键失败及相邻边界，随后继续原24项未执行的公开行为和真实Windows场景。新任务覆盖自身旧C12-R1 blocked等待步骤，不改验收标准或产品。正常交review/finished，产品P0/P1或无法安全收口交blocked/finished；最终接受属总控。不启动其他角色、不创建后续任务或P4-C、不执行Git写操作。

## 必读与固定输入

按AGENTS读取README、project-coordination、coordination/README、最新control、tester和本任务；再读：

- `docs/p4-b7-r3-registry-coordinator-review.md`和`docs/b7-r3-registry-running.md`
- C12/C12-R1原Prompt、独立报告、人工清单、原24项矩阵和REGISTRY-001首次log/JSON
- IF-003/004/005与本地单主人范围决定
- `docs/coordination/snapshots/p4-c12-r2-start.sha256`

复算新起点并记录接单/当前步骤/时刻/心跳/下个检查点，Git staged=0。历史C12/R1/R3清单和旧审计不改写，不用旧hard-coded产品路径/摘要执行新审计。外部操作前重读control；新指令优先。

## 授权写入边界

仅允许：

1. `tests/independent/desktop/`下新增`r2-*`独立配置、测试、审计、有界Windows runner/helper；新`evidence/r2/**`。
2. 新`docs/testing/phase-4-c12-r2-registry-windows-report.md`。
3. 原C12主报告和人工清单只追加R2事实/链接，原prefix保留。
4. 原P4矩阵仅P4-B实际状态及证据备注；原120 ID/完整预期不变，A64 passed、C20/D12 not_run保持。
5. 自己的`docs/coordination/agents/tester.md`。

原public-boundaries/config/audit、全部r1-*测试配置、C12-R1报告、所有旧evidence包括r1/首次失败/通过均只读。产品、开发测试、依赖/lock/生成物、build/package、迁移、Compose、冻结、control/overview/snapshot和其他角色禁止修改。新增单独列出，旧起点只允许上述主报告/清单/矩阵/tester变化。

## 新产物和环境（替换旧Prompt中的全部旧根/摘要）

固定工具/普通依赖/受验包只读根：`C:\MarisRegistryR3\R3-20261002-111556`。workspace普通node_modules、固定Node24.21.0/pnpm12.7.0/Electron44.4.5/Playwright1.63.0和已验证Python可复用，不install/download/audit/build/package。

受验EXE：`workspace\apps\desktop\out\Maris-win32-x64\Maris.exe`。

| 文件 | SHA-256 |
| --- | --- |
| EXE | `1df694c0ca39818d1b2af7aad09eefa13383af186a8d0638d96a13882d604a94` |
| resources/app.asar | `64f84ddde164c4dea81ab3fcb6933728eda5acf3cfe4917828fe0f4f6dc3e161` |
| workspace lock | `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |

旧R3/R2/LOCALZIP profile/db/session/out/evidence/依赖保持只读；不得用旧profile或真实AppData。新动态证据/虚拟profile/db在新`C:\MarisC12\C12-R2-<时间戳>`，先验证解析绝对路径属专属根，外部写入按工具审批处理。不改永久PATH/TUN/代理/安全配置、系统时钟或生产fuses。

## 第一阶段：注册缺陷独立复验

用新R2 config指向新R3依赖，输出evidence/r2/original-registry/；唯一一次运行原r1-shell-boundaries.test.ts中的**R1-SHELL-13原断言**，旧文件不变。若失败保留并停止，不进入Windows。不重跑整个R1 18节点文件。

通过后运行同一原文件中registry相关R1-SHELL-10/11/12，排除已跑13与HostClient/session/supervisor已通过节点。可新增自有虚拟贡献公开测试补双顺序、同/异schemaVersion、同模块重复、不同键合法、失败无部分返回/不修改输入/后续合法compile；不复制开发测试，不新增真实业务模块。

给出REGISTRY-001独立关闭建议和UI-04完整子条件映射；单个缺陷通过不直接代替整个UI-04 passed。原outbox42独立节点已通过且源码不变，不重跑；其逻辑证据链接C12-R1。允许registry开发26项一次兼容复跑并单列，不再跑完整98或Python/P0～P3/Host全量。无输入变化和明确缺陷关联不扩大成功回归。

## 第二阶段：原24项未覆盖公开行为与真实Windows

第一阶段通过后，从C12-R1逐项缺口继续：剩余设置/安全/恶意文本/lazy route/生成物/ZIP和staging逻辑，以及尚未执行的Windows条件。已成功公开节点用历史证据并标输入不变，不重复全部60独立节点；新增用例围绕未覆盖子条件，原C12 Prompt边界在未被本文明确替换处继续有效。

每个ID记录完整原预期、已有部分、这次新执行、具体缺口与状态。原24项是整项验收，不将部分成功或静态/单元证据替代明确的设备条件；original B1failed/19blocked/4not_run不预写为通过。优先先完成能安全取得的自动证据，再列实际人工条件。

产品直接固定Node spawn(shell:false)，Playwright仅动态loopback CDP观察，不用_electron.launch/app.asar loader/PID提升或开启inspect fuse。按可验证路径/创建时间/profile建立owned set；不设置精确进程数门禁，不能把GPU/conhost存在当异常。

每产品场景<=120秒，本轮最多8次有计划启动，单实例第二次计入。运行前tester日志列场景/目的/预算/退出入口；先安全/Host/daily_finance/canonical Profile/recover/毛毛主链路，再必要单实例、closePolicy/设置/Tray等。不是必须用满8次，不重复成功场景。产品原自动退出仅支持1000～30000ms，长生命周期场景不设置该timer，runner仍硬上限120秒并通过正确退出入口收口；不改产品支持范围。

不要从自然exit或PID=0推导真实Tray菜单、普通关闭策略、注销/OS启动项通过。E2E抑制的OS行为不当实测。external_dev用自建虚拟adapter/backend，不接管用户服务；所有账目、消息、身份和模型接口均虚拟，不访问真实provider。

## 原生老化提示和人工设备条件

沿用C12-R1获准的隔离safeStorage seed/read方案，但全部根和受验包换为本轮新根/R3包。最多4次辅助Electron、各<=60秒，只做新专属profile内虚拟加密fixture seed/read/count/digest，使用固定dist/direct spawn，无用户窗口、无旧profile读取、无产品注入或新增IPC。真实原生dialog操作若自动化，Windows UI Automation必须限定owned PID/标题/按钮；禁止全局鼠标坐标或操控其他程序。设备证据与之前模拟逻辑分开。

无法安全准备实际加密fixture或自动化真实提示时记录具体unverified/人工步骤并交总控，不冒充passed、不擅改系统时钟。保留/关闭及明确确认后的有限持久化结果要有真实读取证据，普通双窗口正常不替代该项。

注销/重启Windows、改实际启动项、多屏切换/拔屏、改OS主题或要求用户立即点按钮，均不在本轮授权内；先准备准确单步人工清单交总控。缺少人工设备条件不虚报产品故障，但整项状态保持not_run/blocked并解释。不要为凑全绿删除人工条件或自动降验收范围。

## 停止、证据和交付

目标启动前无副作用配置/语法/映射错误允许一次定向修正，保留首次结果，不拆新任务。目标已启动的业务失败不重跑覆盖；收口后的读取/标签问题只读补证，不能因此重启产品。未知ownership、失控异常弹窗、真实秘密泄露、新P0/P1、不能收口或同问题两检查点无新证据时停止扩大测试并安全收口。禁止按全局进程名杀其他程序。

接单/里程碑/动态开始结束/阻塞/交付记录tester快照；长操作前检查点，有控制时至少十分钟心跳。报告独立与兼容分列、原节点复验与缺陷结论、24项完整映射、人工未测条件、新起点授权边界、旧证据不变、新包/lock/fuses起终不变、实际启动次数和进程/端口/窗口收口、首次失败/warning与限制。

保留脱敏可复算证据，虚拟profile/session/db/blob/raw endpoint和真实秘密不提交仓库。临时清理前核对绝对路径无越界/链接，只清理自有临时项。不启动Docker/PG/OpenClaw/微信/DeepSeek、不重复V002/扫码、不Git写入。提交review/finished或blocked/finished后停止，不自行宣布P4-B complete或创建下一任务。
