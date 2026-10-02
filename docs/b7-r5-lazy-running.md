# P4-B7-R5-LAZY 执行方运行说明

任务交付边界：执行方实现与自测；不关闭 LAZY-001，不宣布 UI-02/P4-B 独立验收。开发、单次 package 和单次 EXE 检查已通过，完成最终摘要后交 review / finished 并停止。

## 输入与实现

最新 control：2026-10-02T22:08:00+08:00。接单固定起点 387/387 matched，0 missing/mismatch，staged=0；起点清单 SHA-256：b610b2d0662119994558305798fdd89ef9a4b6866f20d88aa62198f116848389。旧 R4 仓库摘要不作为新起点，旧包输入使用其 workspace-source 独立核对。

根因：原模块 route.lazy 导入抛错后没有模块级 errorElement，错误冒泡至根路由并替换 Shell；原 retry 使用整页 reload。现在 main 实际启动 DesktopApp，贡献路由通过可信内置 loader 表装配，模块导入错误先映射安全错误，再进入模块 errorElement。模块渲染异常由内容区域的类边界处理，React caught-error 回调只输出固定安全诊断。根兜底保留可见错误。注册、模块贡献、业务页面、主进程、preload 和冻结依赖均未修改。

用户点击触发 useRevalidator 的真实 revalidate，重新运行页面 loader；进行中 ref 与禁用按钮合并重复点击。每次 loader 成功返回新的 attempt，重建局部渲染边界。无自动重试、随机 URL、整页 reload。等待 Host 模块列表后创建 Router，避免初始空模块路由与返回列表竞争造成首次双加载；主题/隐私/runtime 更新不重建 Router，订阅仅按组件生命周期清理。

生产 loader 仅包含 daily_finance_home 的固定动态 import。测试中第二健康模块与页面加载端口仅用于虚拟输入，没有第二业务模块进入生产，也没有开放 renderer 任意路径加载。

## 打包前 UI-02 完整开发对照

原矩阵 P4B-UI-02：两个 lazy route；chunk 加载失败、重试成功、切换模块；局部错误边界可重试，Shell/登录/其他模块可用；不循环加载或丢当前会话。当前产品的单主人会话合同保留，不添加暂停范围的登录 UI。

所有下列节点运行实际 DesktopApp、React Router、Shell 和模块边界；只注入虚拟 bridge、可信页面 loader。证据位于 C:/MarisLazyR5/R5-20261002-222300/evidence/tests/directed3.json 与 full.json。

| 原预期 | 实际代码/执行方节点 | 结果与具体观察 | 证据层级与限制 |
| --- | --- | --- | --- |
| 首次 chunk 失败保留 Shell、导航、Agent | main -> module-routes 的模块 errorElement；transient import 节点 | 首次 loader=1，安全 alert，三个入口仍在；后续 Shell DOM 身份保持 | jsdom 真实产品路径；首次修复前 red=1 failed 保存 |
| 明确重试从失败恢复 | useModuleRetry ->真实 revalidate ->同一 loader；transient import 节点 | 点击后 loader=2，成功页面可见，健康 loader=0 | 成功页面与实际次数断言；没有假成功回退 |
| 持续失败不循环 | persistent failures 节点 | 首次1，明确点击后2；两次50ms观测无额外调用；返回失败路由明确导航后3 | 有界运行观察，未声称无限时间观测 |
| 其他模块/设置可用，往返不污染 | persistent failures 与 missing trusted port 节点 | 两个独立贡献路由；健康页面、settings 可访问；返回错误后再次健康无 alert | 健康第二模块仅开发虚拟输入；真实第二业务应用 unverified |
| 重复点击与在途切换安全 | bounds pending retry 节点 | pending 禁用，双击不新增加载；失败路由调用2次；离开后旧加载完成不覆盖健康页面 | 真 Router 并发导航行为；不注入真实设备 chunk 故障 |
| 模块 render 错误局部恢复 | isolates a module render error 节点 | Shell 在，固定安全 console 诊断；点击重新 loader=2，边界重置后成功 | 真实类错误边界/React caught-error logger；虚拟敏感 canary 不进入 DOM/console |
| 主题/隐私/runtime 与订阅保持 | transient import 节点 | dark/on/offline 在错误和重试前后保留；getSnapshot/list/subscribe 各1；重试不 unsubscribe，最终卸载仅1次 | bridge 观察证明相关调用未新增；真实 token/session 持久化全验 unverified |
| 不丢当前会话，不新增 auth/recover/provider/写入 | transient 与 production entry 节点 | runtime.recover、outbox.enqueue、window.perform、external.open 均0；settings 仅用户明确两次更新；订阅状态保持 | renderer 不具备 owner/revoke/provider API；窄 bridge 调用证据不冒称真实会话故障全验 |
| 无 reload、敏感信息或空白掩盖 | 各节点 afterEach 公共 jsdom.virtualConsole、console canary 观察 | 无 jsdom 导航/reload 错误；DOM/console 不含虚拟路径/canary；持续失败仍显示 alert | 开发环境行为观察，不依赖源码字符串替代恢复验证 |
| 原成功/Host交集/空模块保持 | production entry、empty Host、disabled module、missing trusted port 节点 | 实际 main 导入与内置 daily 页面成功；空交集可访问设置；禁用模块不加载；未知 loader 安全失败 | 实际生产入口成功 + 虚拟 Host；认证设备路径由最终 EXE smoke 补充 |

UI-02 已定义的开发部分通过，没有需越界处理的明确合同缺口。真实 Windows chunk 故障恢复、设备级原生行为、真实会话故障持久化仍 unverified，交固定快照后由总控派独立任务。正常 EXE smoke 不替代这些故障验收。

## 执行方检查与首次失败

时间以原始 JSON UTC 为准，本地时间为 +08:00；没有改系统时钟。红灯/定向/完整重复节点不叠加称唯一案例。

- 首次 red：22:26:46.881—22:27:05.148，1 failed，复现模块导入错误后 Shell 消失。
- directed：22:35:55.065—22:35:57.241，54 passed/8 failed/0 skip；测试 setup 使用 window 私有 virtualConsole 不可用，尚未进入八项业务断言。修正为 Vitest 提供的 global jsdom.virtualConsole 公共接口，原结果保留。
- directed2：22:55:11.505—22:55:15.237，58 passed/4 failed/0 skip；首次 loader 重复调用，transient/persistent/pending/render 断言失败。修复启动路由竞争，保留次数要求与原始结果。
- directed3：22:56:27.294—22:56:30.138，4 文件/62 passed/0 failed/0 skip（52 registry + shell + composition + 新8项）。
- TypeScript：22:56:30.199—22:56:31.960，exit0；lint：22:56:32.054—22:56:32.146，exit0。
- 唯一一次完整 desktop 开发回归：22:57:30.589—22:57:33.634，15 实际测试文件/132 passed/0 failed/0 skip（原124 + 新8）。Vitest numTotalTestSuites 含 describe 组，不当成文件数。无 skip/xfail；独立测试运行0。
- 额外只读查找中旧猜测 matrix.json 路径不存在、rg Windows wildcard 路径错误；随后已定位真实 Markdown 矩阵。不属于测试通过或产品失败，未因此重跑目标。初始与调试记录均保留。

## 普通环境与后续门禁

新根 C:/MarisLazyR5/R5-20261002-222300；只读来源 C:/MarisRouteR4/R4-20261002-164600。普通物化复制，无链接，无安装/下载/网络：首次源码388、冻结依赖12443/实际12677、electron dist73、工具3逐文件匹配。固定 Node24.21.0/pnpm12.7.0；lock 5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a。最终构建输入清单将在授权源同步后刷新并复算。

打包前记录时预算0/1、EXE0/1；最终各使用1/1。UI-02 对照与上述开发检查先于 package，原映射摘要/时间存 evidence/inputs/ui02-prepackage.json。本说明下面是运行后补充，不能反推为打包前已经完成 EXE。

## 新包与实际 EXE 结果

- 官方 ZIP：electron-v44.4.5-win32-x64.zip，158184819 bytes，SHA-256 11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d；保留原 LOCALZIP，只读使用。Get-Command 首项和真实裸 pnpm 均为新根固定 pnpm.exe/12.7.0；实际 Forge resolve/spawn 12.7.0，实际 child execPath 为新根 Node24.21.0。Python 为已验证3.14.7。没有安装、下载、audit、永久环境改动。
- 最终构建源389项，workspace-source.sha256 总摘要 8d104d1e84382cb1fe0228618545d0e7585f3f91a2b3f387f067e2e50e148af9；相较仓库最终快照不包含新运行说明，executor 是复制时版本，产品四项与交付一致。源清单不会把复制旧角色日志误称为最新交付日志。
- package **1/1**：23:02:59.283—23:03:05.627，6344ms，exit0/signal null，stderr0 bytes。真实 Forge 环境证据 evidence/actual-forge-env.jsonl。没有重打包。
- static **7/7**；67 Python资源逐文件精确一致，无多余/缺失/bytecode/egg-info；out140文件、386495022 bytes，asar11文件、0link/0unpacked；fuses version1，前六48/49/48/48/49/49符合冻结，污染0/staging0。
- EXE SHA-256：64ce71f3a7b3055f9ad27f6d611e28c4af7e9ba8b86d8b21399b7b422844a80e；app.asar：5ba47909537e1419dc275fa3ca1e5e076a1aa6d5c0205229f91defb92ddd0931。
- 新主renderer assets/index-DXFn8qNJ.js，410191 bytes，SHA-256 71c0ebfb4fa08462f19b176e3d7eff4e6c2f9e2811b71f134a10b2b2ec9ae6c4。asar提取字节与实际构建bundle完全相同，包含可信route/安全错误/有限重试实现；main实际导入module-routes，新asar不同于旧包。static/lazy-source-binding-final.json 与执行方实际Router测试一起作为来源证据，字符串扫描本身不证明行为。
- 首次 bundle “完全无 location.reload” 扫描 false：命中 React Router 自带 framework route-module loader 的 reload 代码。只读定位后保留首次 static/lazy-source-binding.json，限定产品源+真实Router/no-navigation行为观察补充 final.json；本产品使用 data loader，不使用 framework modules。没有改依赖/包或重新启动。
- 最终 EXE **1/1**：23:06:25.901—23:07:00.605，34704ms，**19/19**。固定Node直接spawn(shell:false)，Playwright只附加动态loopback CDP，120秒硬限，原30秒退出timer；两个窗口、窄bridge/Node隔离、managed/online/authenticated、daily_finance/canonical Profile、毛毛/openMain、recover恰好1次、隐私与日志门禁均通过。此recover是冻结正常smoke动作，模块错误/重试开发测试recover仍0。
- 自然exit0/signal null，无timeout/forced cleanup；2个自有Python后代退出；0自有进程、监听、窗口残留。新虚拟profile62文件保留；owner/session/db只做摘要证据，不读取真实数据，不加入仓库。renderer console/pageErrors/crashEvents 均0；Windows Application/CodeIntegrity相关事件0。
- Electron日志无敏感信息/内部路径/异常；原生stderr100 bytes含预期CDP地址身份，仅保留在外部受限日志，未进入renderer、仓库或公开文档。没有将此诊断端点称为可发布日志。

## 最终交付、复算与剩余边界

仓库仅7个交付文件：main.tsx、Shell.tsx、新module-routes.tsx、新lazy-isolation.test.tsx、本运行说明、executor.md、b7-r5-lazy-source.sha256。原shell.test.tsx与其他执行/独立测试不变。固定387起点为384精确不变、3授权修改；新增实现/测试/说明3项，最终source390项，排除清单自身。清单行按相对路径ordinal排序，UTF-8无BOM、LF；两列为“路径 TAB SHA-256”，直接对文件原始字节求SHA256，不做换行归一化。清单总摘要为对清单自身求SHA256，准确值由外部closeout.json和交付回复提供，避免本说明的摘要自引用。

证据根 C:/MarisLazyR5/R5-20261002-222300/evidence：tests/red、directed、directed2首次失败保留；directed3、full与typecheck/lint真实exit；inputs/prepackage、ui02-prepackage、final-immutable-audit；static/out-manifest-v4、python-resources-v4、asar-manifest-v4、result-v4与lazy-source-binding-final；final-exe/result；resource-closeout；repository-delivery.sha256、evidence-manifest.sha256、closeout.json。最终external清单排除自身、closeout与raw/profile/os-env/logs及测试cache/tmp，完整out单独清单；不将私人runtime资料加入仓库。

旧R4 source352、冻结deps12443/full12677、dist73、out140、脱敏evidence59、profile62打包前后逐文件核对；完整依赖仅234个已物化@maris/desktop额外文件，前后目录数量也核对。旧R3/R2/LOCALZIP无写操作，不将未单独重跑旧环境动态验证称为新增验收。

仅清理验证解析绝对边界且无reparse的新tests/tmp；新产物/虚拟profile/证据和旧树保留。最终Git只读检查staged=0、diff --check无内容错误；Git ignore权限与LF→CRLF提示保留为环境警告，不进行Git写操作，原.claude/.pnpm-store不改。工具中断前后未连续观测的间隔unverified，不推断外部角色活动，未更改系统时钟。

禁止范围全部保持：没有独立测试执行/改动、独立报告/矩阵/冻结/control/overview/其他角色修改；没有Docker/PG/OpenClaw/微信/DeepSeek/provider、登录/扫码/用户点击要求；没有启动C12-R4、P4-C/D或其他角色。最终review/finished只是交开发交付；LAZY-001独立关闭、UI-02真实Windows故障恢复、真实会话故障持久化、原生Tray/注销/启动项/多屏等留总控和测试方授权阶段。本执行方在固定摘要后停止。
