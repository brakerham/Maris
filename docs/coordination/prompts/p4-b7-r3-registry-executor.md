# P4-B7-R3-REGISTRY：设置键全局唯一的窄范围返修

## 唯一负责人、目标与交付状态

你是既有执行智能体，唯一负责本任务。测试方C12-R1已确认P1 `P4-C12-R1-REGISTRY-001`：跨模块同名setting key被compileRegistry接受，违反IF-003 §5全局唯一/整体拒绝。总控已独立关闭旧OUTBOX-001；不要继续修改outbox或重新处理旧缺陷。

修复注册器、补执行方回归、完成新版package/EXE门禁，交付review/finished后停止。开发测试不等于独立关闭或P4-B complete；不运行/修改tests/independent/**，不启动测试智能体、技术顾问或P4-C。用户自行派发后续。

## 必读与接单

按AGENTS读取README、project-coordination、coordination/README、最新control、executor和本任务，再读：

- `docs/p4-c12-r1-registry-blocked-coordinator-review.md`
- `docs/testing/phase-4-c12-r1-outbox-windows-report.md`（只读，尤其REGISTRY-001与首次失败）
- IF-003 §5，IF-004/005生效条款
- `apps/desktop/src/modules/registry.ts`及相关开发测试
- `docs/b7-r2-outbox-running.md`中的已验证工具、package/EXE和资源收口
- `docs/coordination/snapshots/p4-b7-r3-registry-start.sha256`

开始前复算新固定起点，记录接单、摘要、当前步骤/时间/心跳/下个检查点，Git暂存为零。新任务取代执行角色旧R2等待步骤，不重跑旧起点或旧独立审计。外部操作前重读control；新指令优先。

## 唯一允许修改的文件

1. `apps/desktop/src/modules/registry.ts`：只改setting冲突判断。
2. `apps/desktop/tests/unit/registry.test.ts`：保留原断言，补相关开发回归。
3. `docs/b7-r3-registry-running.md`：新增运行与交付说明。
4. `apps/desktop/b7-r3-registry-source.sha256`：新增最终有序逐文件清单，排除自身。
5. `docs/coordination/agents/executor.md`。

禁止改其他产品、outbox/main/preload/IPC、contribution、Python/Host/数据库/migration、package/staging/Forge、依赖/lock、独立测试/证据/报告/矩阵、冻结/control/overview/总控快照及其他角色文件。需要扩大范围时停止对应部分并交回总控，不自动改合同。

## 冻结修复行为

- 所有合法贡献中的setting.key在同一次compileRegistry输入内全局唯一；跨module重复也抛出既有`desktop_registry_conflict`，不返回部分registry。
- 不自动加module前缀、重命名键、只保留赢家或改为告警；不把冻结合同改成每模块局部唯一。
- 同模块重复也拒绝，schemaVersion相同或不同均不能绕过；交换贡献顺序结果相同。
- 两个合法模块使用不同键继续成功；当前daily_finance的preferences、canonical Profile和Host intersection保持。
- module/Profile/route ID/appearance冲突、严格解析、错误合同和返回类型保持；不顺便扩大route path或其他校验需求。
- 不修改输入贡献；一次失败后新的合法compile不受先前seen状态影响。测试使用虚拟贡献，不新增真实第二业务模块。

## 有限开发验证

首次利用已保留独立失败作为事实输入，不运行独立节点。先在自己的registry测试补跨模块同键回归，可在修复前定向运行取得红灯；保留首次结果。修复后运行registry开发测试，覆盖双顺序、同/异schemaVersion、同模块重复、不同键成功、输入不变和失败后合法编译。保留原canonical长度和其他冲突断言。

执行TypeScript、lint和相邻shell模块消费测试。最后允许一次完整desktop开发单元回归（当前14文件、90项基线，加本轮新增）；不以定向与完整回归重复节点相加宣称唯一案例。不要重跑Python/P0～P3/Host全量、独立60节点或outbox全套独立复验。完整桌面回归中已有outbox开发测试自然运行不算重新派发旧任务。

失败先区分产品断言、测试编排和基础设施；开发调试可在范围内修正并保留首次记录，不能删/放宽原断言、加skip/xfail或掩盖失败。

## 普通隔离副本、新产物与一次EXE检查

只读工具/普通依赖来源为 `C:\MarisOutboxR2\R2-20261001-155509`，其workspace/node_modules已验证；使用固定Node24.21.0、pnpm12.7.0、Electron44.4.5、Playwright1.63.0和已验证Python。无需联网安装、换版本、重造R0/Job框架或修系统代理。

新任务根 `C:\MarisRegistryR3\R3-<时间戳>`，先验证解析后的绝对路径属于该专属根，外部写入按工具审批处理。在新普通副本物化复制清单源码、普通依赖和必要固定工具；禁止Junction/symlink指向旧树，禁止改写或删除旧R2依赖/产物/profile/evidence。只同步两个获准源码变更；证据和虚拟profile也在新根。

复算fixed lock `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`、复制源码/依赖及Electron dist。使用已验证任务局部PATH/shim，先检查裸pnpm和Forge子进程解析，不改永久环境，不设置精确进程数量门禁。

沿用已通过LOCALZIP的现有校验/接线，`MARIS_ELECTRON_ZIP_DIR`指向冻结官方ZIP普通目录：`electron-v44.4.5-win32-x64.zip`，158184819 bytes，SHA-256 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d`。不改fuses/构建/校验或联网下载。

开发验证全过后授权新package **1次**。检查新EXE/asar、67 Python资源、生产fuses、污染零命中及staging收口，生成新完整out清单；新asar摘要必须绑定本轮源码，不能引用R2旧包作为修复包。不把EXE自身摘要与旧版相同误判为失败，实际业务资源主要在asar。

静态通过后授权新最终EXE **1次**，只用固定Node `spawn(shell:false)`，Playwright仅loopback CDP观察，不用_electron.launch/app.asar loader/PID提升。全新虚拟profile/数据库、已验证Python；沿用R2成功的19项实际门禁：双窗口、窄bridge及renderer隔离、managed/online/authenticated、daily_finance/canonical Profile、毛毛、一次recover、自然退出、自有资源零残留。硬上限120秒，原自动退出参数只用实际支持范围，不修改产品或测试接口。

不要注入冲突真实模块、真实老化消息或要求用户点击窗口；原生提示和其他独立Windows场景留给测试方。禁止启动Docker/PostgreSQL/OpenClaw/微信/DeepSeek/真实provider，不重复V002或扫码。

## 停止规则、证据与交付

本轮开发代码调试与目标启动前无副作用编排修正，不人为拆成新任务：保留错误，允许一次定向修正；不得用“只能一次”把未启动目标的脚本笔误虚报成产品失败。目标已运行的package/EXE失败不能重跑覆盖或追加预算。

发现新产品P0/P1、失控Windows异常弹窗/泄露/无法安全收口、必须越界或同一外部阻塞两个检查点无新信息时停止扩大操作，交blocked/finished。只按路径/时间/profile核实自有进程树后收口，不按全局进程名杀其他程序；有用户正常窗口反馈时记录，不冒充独立验收。

长操作前记录下一检查点/可观察会话，有控制时十分钟心跳或实质输出更新。运行说明列根因、准确代码位置、每组测试首次失败与最终结果、警告、源码与产物摘要、旧证据不变性、package/EXE实际次数和零残留证据。所有数据虚拟，秘密/profile/blob不提交仓库。

起点其余文件精确保持，新增单独列出；原C12/R1独立材料不变。最终source清单从本任务起点列表更新获准文件摘要，加入本轮运行说明，排除清单自身；executor角色文件在最终停止修改后复算。禁止Git写操作。

交review/finished后停止；总控核对新稳定快照再派测试续跑。不要宣布REGISTRY-001独立关闭，不创建C12-R2或P4-C。
