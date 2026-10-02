# P4-B7-R4-ROUTE：路由路径冲突返修与UI-04完整开发核对

## 唯一负责人、目标与输入

你是既有执行智能体，唯一负责本任务。C12-R2确认P1 `P4-C12-R2-REGISTRY-PATH-001`：不同routeId共享完全相同path仍被compileRegistry接受。设置键REGISTRY-001与OUTBOX-001均已由总控独立关闭，不重新处理已关闭缺陷。

修复路径查重，先完整核对UI-04已定义注册条件、做开发回归，再生成新包和真实EXE检查。成功review/finished后停止；不自行独立关闭新缺陷或宣布P4-B complete，不运行/修改独立测试、不启动其他角色或P4-C。

按AGENTS读取README、project-coordination、coordination/README、最新control、executor与本任务；再读：

- `docs/p4-c12-r2-route-blocked-coordinator-review.md`
- `docs/testing/phase-4-c12-r2-registry-windows-report.md`及path首次代码/log（只读，不执行）
- IF-003 §5、原P4B-UI-04完整预期、IF-004/005；R3运行说明
- `docs/coordination/snapshots/p4-b7-r4-route-start.sha256`

开工复算新起点、staged=0，登记接单/摘要/步骤/时刻/心跳/下个检查点。新任务覆盖自己旧R3等待步骤，不改历史清单。外部操作前重读control，较新指令优先。

## 精确授权文件

1. `apps/desktop/src/modules/registry.ts`：仅加入route.path全局冲突拒绝，保留routeId和setting等已修行为。
2. `apps/desktop/tests/unit/registry.test.ts`：保留现有26项，新增路径和必要注册边界回归。
3. 新`docs/b7-r4-route-running.md`。
4. 新`apps/desktop/b7-r4-route-source.sha256`：最终路径有序逐文件摘要，排除自身。
5. 自己的`docs/coordination/agents/executor.md`。

禁止其他产品、main/preload/IPC/outbox/renderer路由/Shell/contribution、Python/Host/migration、依赖/lock、Forge/staging/package/helpers、其他开发测试、全部tests/independent/**及报告/矩阵、control/overview/总控快照/冻结/其他角色文件。只读检查可用于完整映射；发现必须越界的真实缺口，在package前停止对应工作并交总控，不能顺手实现或降低预期。

## 路径修复合同

- 同一compileRegistry输入内routeId继续全局唯一，**route.path完全相同字符串也全局唯一**；同模块多route/跨模块不同routeId都必须检测。
- 两类冲突均稳定抛既有desktop_registry_conflict，不返回部分registry，不覆盖、不重命名、不选赢家、不降为warning。
- 交换贡献/路由顺序仍拒绝；冲突位于最后一个模块或route也整体拒绝，不留下跨次调用seen状态，不修改输入。
- 不同path、不同合法ID继续接受，settings全局唯一/canonical Profile/Host intersection/原daily_finance贡献保持。
- 不把routeId和path混成同一标识命名空间，避免合法ID与path内容相似时误拒绝。
- 不擅自改path schema、trim/lowercase/尾斜杠/动态参数/模式重叠语义；本轮已确认的是完全相同path。发现这类实际相关问题只读取证交总控，不声称未测语义全通过。

## 先完成UI-04，再打包

首先在开发测试添加跨模块同path原缺陷回归，允许修复前定向红灯并保留原结果；不执行独立失败节点。修复后覆盖双顺序、同模块多个不同ID同path、末尾冲突、不同路径合法、routeId原冲突、失败无部分返回/输入不变/下次合法成功。

**package前必须生成UI-04完整映射**：hostUiMajor不兼容、module/Profile/routeId/path/setting/appearance冲突、ASCII/SemVer严格解析、Host交集约束以及Shell/main/preload无具体moduleId业务分支。对照原冻结逐项列代码、现有/新增开发节点和实际结果；已有断言足够的不写镜像测试。主窗口/毛毛实机合同和lazy route错误隔离不是本轮开发注册回归的通过结论，不以静态字符串检查替代运行行为。

存在未满足的明确冻结条件时先报告，不仅修完新path案例就package。未定义的路由语义与已冻结UI-04缺口分开，不凭空追加契约。总控/开发映射不能代替测试方独立验收。

运行registry、相邻shell/composition开发测试、TypeScript和lint；最后一次完整desktop开发回归（当前98项+新增路径案例）。定向/红灯/完整重复节点不相加成唯一案例；保留原26全部断言，不加skip/xfail。不要重跑Python/P0～P3/Host全量、旧outbox42或旧独立16/60。

## 已验证环境与新产物

只读源为`C:\MarisRegistryR3\R3-20261002-111556`，使用其普通workspace/node_modules、固定Node24.21.0/pnpm12.7.0/Electron44.4.5/Playwright1.63.0和已验证Python。无需重新安装/下载/audit，不改系统代理或安全设置。

在全新`C:\MarisRouteR4\R4-<时间戳>`物化复制清单源码、普通依赖和必要工具，先核对解析后绝对路径属专属根。禁止Junction/symlink指向旧树，不改/删旧R3/R2/LOCALZIP依赖、产物、profile/evidence。只同步两个授权源码改动，专属evidence/虚拟profile新建；外部写入按工具审批处理。

固定lock为`5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`；工具解析沿用R3已成功的固定Node和任务局部pnpm/Forge接线，先验证实际第一候选/子进程目标，不再造R0/Job/精确进程数框架，不改永久PATH/pnpm。

沿用LOCALZIP：MARIS_ELECTRON_ZIP_DIR指向已验证官方普通目录，文件electron-v44.4.5-win32-x64.zip，158184819 bytes，SHA-256 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d`。不改校验/Forge/fuses/网络。

UI-04完整开发核对与回归通过后授权package **1次**。检查新EXE/asar、67 Python资源、fuses/污染/staging、完整out清单及registry source→新bundle来源；业务主要在asar，不要求EXE摘要必变，也不得套用旧asar作为新修复产物。

静态全过后授权最终EXE **1次**：固定Node spawn(shell:false)，Playwright仅loopback CDP附加，禁止_electron.launch/app.asar loader/PID提升。全新虚拟profile/db、固定Python，沿用R3实际19门禁：双窗口/窄bridge/renderer隔离、managed认证Host、daily_finance/canonical Profile、毛毛/openMain、一次recover、自然退出、零owned资源。硬上限120秒，自动退出仅用产品已支持1000～30000ms范围；不注入冲突真实模块或真实老化消息，不要求用户点窗口。

老化原生提示、真实Tray/注销/启动项/多屏等留独立任务，不能把执行方smoke当设备验收。不得Docker/PG/OpenClaw/微信/DeepSeek/真实provider操作，不重复V002/扫码。

## 有限修正、日志与停止

允许授权源码内正常开发调试；目标启动前无副作用语法/参数/证据映射问题可一次定向修正并保留原记录，不人为拆新任务或称产品P0。package/EXE已运行的失败不得重跑覆盖或追加预算；收口后汇总问题只读补证，不因此重启产品。

新P0/P1、必须越界、失控Windows异常弹窗/泄密、无法安全收口或同一外部阻塞两检查点无有效进展时安全停止、交blocked/finished。精确owned树按路径/时间/profile证明，不能全局按进程名kill。

接单/阶段/长操作/阻塞/交付写executor快照；五分钟以上操作前下一检查点，有控制时十分钟心跳或实质输出更新。报告根因、准确代码位置、UI-04完整映射、首次/最终测试、warning、旧材料不变、新package/EXE次数/源码与产物摘要、文件边界和零残留。

最终source清单由本轮起点更新授权摘要、加运行说明、排除自身；角色最后修改后复算。独立首次/通过材料精确保留，profile/session/db/blob/raw标识不进入仓库。清理只对已验证专属临时路径，保留产物/可复算脱敏证据。禁止Git写操作。

成功交review/finished后停止，不独立关闭PATH-001、不宣布UI-04/P4-B complete、不创建C12-R3；等总控核对稳定终点后再派独立复验及剩余Windows。
