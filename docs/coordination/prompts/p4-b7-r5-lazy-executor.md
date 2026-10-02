# P4-B7-R5-LAZY：模块页面故障局部隔离与可控恢复

## 唯一负责人及目标

你是既有执行智能体，唯一负责本任务。C12-R3确认P1 `P4-C12-R3-LAZY-001`：模块lazy导入失败后父路由错误页替换整个Shell，导航和统一Agent入口消失。PATH-001、设置键REGISTRY-001和OUTBOX-001已独立关闭，不重新返修。

修复现有Shell路由的局部错误隔离和原UI-02恢复合同。不是P4-C高保真财务界面开发，不设计驾驶舱、真实聊天或第二业务模块；不引入新框架/依赖。自测通过只能review/finished，不独立关闭缺陷或宣布P4-B complete，不启动其他角色或后续任务。

## 必读与固定起点

按AGENTS读README、project-coordination、coordination/README、最新control、executor、本任务；再读：

- `docs/p4-c12-r3-lazy-blocked-coordinator-review.md`。
- `docs/testing/phase-4-c12-r3-route-windows-report.md`、原UI-02完整预期、IF-003/004/005。
- C12-R3首次`r3-remaining.test.tsx`及evidence/r3/remaining-independent（只读、不执行）。
- renderer/main.tsx、Shell.tsx、原Shell开发测试、R4说明和UI-04映射。
- `docs/coordination/snapshots/p4-b7-r5-lazy-start.sha256`。

逐行复算新起点、staged=0；登记接单/当前步骤/时刻/心跳和下一检查点。旧R4 source摘要与派发后协调文件不再完全相同是正常的，总控新起点才是仓库权威输入；受验旧包构建输入另用其旧workspace-source验证。外部操作前重读control，新指令优先。

## 精确允许写入

1. `apps/desktop/src/renderer/main.tsx`：局部路由错误与恢复接线；保留Host交集、主题/隐私和窄bridge。
2. `apps/desktop/src/shell/Shell.tsx`：安全模块错误呈现/重试；保留Shell导航/Agent入口及原组件公开功能。
3. 必要时新增`apps/desktop/src/renderer/module-routes.tsx`，作为**实际产品使用**的类型化路由装配/可信loader辅助入口，不是测试专用旁路。
4. 新`apps/desktop/tests/unit/lazy-isolation.test.tsx`；允许对原`tests/unit/shell.test.tsx`作必要追加，保留原断言。新测试自行声明jsdom，不改全局Vitest配置。
5. 新`docs/b7-r5-lazy-running.md`、`apps/desktop/b7-r5-lazy-source.sha256`；自己的executor角色日志。

其他产品（registry、contribution、daily finance页面、styles、main/preload/IPC、outbox/settings/auth/Host/Python）、其他开发测试、依赖/lock/配置、Forge/staging/package/helpers、全部独立测试/报告/矩阵、冻结/control/overview/总控快照/其他角色禁止修改。必须越界或改变冻结语义时在package前取证交总控，不能顺手扩大范围。

## UI-02行为合同与最小实现原则

- 模块页面的lazy导入/页面渲染错误由模块内容区域内的边界处理；Shell、模块导航、统一Agent入口仍在，正常设置/健康页面可访问。根级不可恢复错误可保留兜底，不能把模块故障交给替换整个Shell的父兜底。
- 局部错误只显示既有安全通用信息；不能把chunk地址、stack、内部路径、token或任意error.message渲染/新写到renderer console。不得通过吞掉所有错误、返回空白或伪造成功掩盖失败。
- 用户明确点击才触发一次有界局部重试；真实React Router及真实loader路径必须重新尝试，瞬时失败后可恢复，持续失败仍安全显示并可导航。不新增自动轮询/循环加载、缓存绕过下载、随机URL或全页location.reload来假装模块恢复。
- 错误、切换和重试期间保留Shell主题/隐私、当前runtime认证观察及有效订阅；不能重新初始化owner、revoke session、调用runtime.recover/provider、删除outbox或创建财务写入。fake bridge只能证明相关调用未新增，不能冒称真实session持久化全验。
- 路由装配来自现有模块贡献，不加if moduleId特殊故障修补分支，不改已关闭registry的ID/path规则。若提取辅助函数，必须由实际main启动使用，loader解析仍限定可信内置集合；不开放renderer任意路径import/MCP/IPC。
- 虚拟第二route/模块只在开发测试输入存在；不把第二业务应用编入生产，不伪称P4-D扩展性已实现。保持原index、settings、Host交集/空模块/日常财务成功路径。

实现方案由你在现有React Router合同内选择，并通过实际运行证明retry能重新调用loader。不要仅照抄API名称假定其会清除失败状态，也不要为可测试性走不被产品使用的替代路由。

## 打包前完整UI-02开发对照

先添加执行方自有最小行为回归，运行真实renderer/Shell/React Router，虚拟bridge及一次失败loader；允许修复前红灯，保留首次结果，不运行或修改测试方节点。

覆盖原UI-02所有已定义部分：首次chunk失败保留Shell/导航/Agent；可切换健康route和settings；显式重试从失败恢复；持续失败不自动循环；切换回来后错误状态不污染健康route；主题/隐私/runtime订阅与会话相关bridge调用保持。至少两个lazy route的测试输入，包含一个失败、一个健康；注册和路由装配使用真实产品辅助入口。必要的模块render错误也取局部行为证据，不把只测纯error组件称全链通过。

测试stub只有外围bridge/可信页面loader端口；React Router、Shell、边界和装配路径用真实实现。恢复验证要断言页面成功及loader实际次数；无reload/额外auth/provider/recover/write要有具体观察，不凭结构字符串或错误文案存在替代。

在运行说明先列UI-02原预期→代码→开发节点→结果→证据层级，再允许package。缺真实Windows、第二业务模块/真实session证据明确留独立阶段；明确合同失败必须先解决/报告，不能只让原Shell存在断言变绿。

运行新lazy/Shell及必要composition/registry相邻开发测试、TypeScript/lint；最后**一次完整desktop开发回归**（当前124项+新增），红灯/定向/完整重复节点不叠加称唯一案例，原断言保留、不skip/xfail。不跑已成功27独立节点、旧outbox42、Python/P0～P3/Host全量。

## 普通隔离环境、新包与EXE

只读源`C:\MarisRouteR4\R4-20261002-164600`，复用其普通依赖与Node24.21.0/pnpm12.7.0/Electron44.4.5/Playwright1.63.0/已验证Python。无需安装、下载、audit，不修改永久PATH/代理/安全配置。

新普通根`C:\MarisLazyR5\R5-<时间戳>`，创建/复制前验证解析绝对边界、无链接；普通物化源码/依赖/工具，不junction指向旧树。只同步授权源文件；新evidence/虚拟profile/db独立。旧R4/R3/R2/LOCALZIP源码、依赖、产物、profile/session/evidence保持不变，外部写入按工具审批。

固定lock `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。沿用R4已成功任务局部工具解析及LOCALZIP，官方ZIP electron-v44.4.5-win32-x64.zip，158184819 bytes、SHA `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d`。不造新R0/Job框架，不改package/fuses。

全部UI-02开发对照和回归通过后授权package **1次**；新asar/renderer修复来源绑定、EXE摘要、67 Python资源、完整out清单、fuses/污染/staging核对。不会要求EXE摘要因业务源码必变，必须证明使用新asar。

静态全过后最终EXE **1次**：固定Node spawn(shell:false)，Playwright仅动态loopback CDP附加，禁止_electron.launch/app.asar loader/PID提升。沿用R4实际19门禁，双窗口/窄bridge/Node隔离、managed认证Host/daily_finance/canonical Profile、毛毛/openMain、recover一次、自然退出和零owned资源；硬上限120秒，退出timer在产品1000～30000ms范围。不注入真实chunk破坏/用户消息或要求用户点击。该smoke不替代独立Windows UI-02故障/恢复验收。

## 有限调试、停止与交付

允许授权产品/开发测试内正常调试；目标前无副作用配置/语法/映射错误允许一次定向修正、保留首次证据，不人为拆成任务。package或EXE已运行失败不能重跑覆盖或追加预算；收口后的读取/标签问题只读补证，不因此重启产品。

新P0/P1、需越界/架构调整、失控弹窗/泄密、无法安全收口或同一外部阻塞两检查点无新输出时安全停止交blocked/finished。owned树按路径/时间/profile证明，不能全局按进程名kill。不要操作Docker/PG/OpenClaw/微信/DeepSeek/provider、系统时钟/OS启动项或重复V002/扫码。

接单/阶段/长操作/阻塞/交付记录executor快照；五分钟以上操作前登记检查点，有控制时十分钟心跳。只读技术分析不替独立验收；保留首次错误、warning、代码位置、数据流、完整UI-02映射、准确调用/测试统计、新package/EXE次数、旧输入不变和最终资源状态。

最终source清单按新起点更新获准摘要、加入新增实现/测试/运行说明，排除清单自身；角色停止修改后复算。脱敏材料保留，profile/session/db/raw端点/个人财务不进仓库；清理前验证专属绝对路径/无链接，只删自有临时项。禁止Git写操作。

交review/finished后停止，不关闭LAZY-001、不宣布UI-02/P4-B complete、不创建C12-R4。总控先核对稳定快照，再派原失败独立复验和剩余Windows。
