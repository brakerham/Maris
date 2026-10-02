# P4-C12-R4-R2 冷入口传播复验与Windows验收报告

交付：**blocked / finished**。既有独立测试智能体、唯一负责人；依据 control `2026-10-03T03:16:00+08:00` 和 [R2任务卡](../coordination/prompts/p4-c12-r4-r2-cold-entry-tester.md)。全部使用虚拟输入。A首次失败后停止，B及后续未执行；LAZY-001/UI-02/P4-B未关闭，没有新增已定级产品缺陷。最终验收与后续接线裁定属于总控。

## 结果与明确传播阶段

本次取得了冷入口的完整阶段。实际main与React act均返回，观察门面由main正常依赖链首次加载。**同一Router实例1发起目标loader两次：尝试1先取消再以安全错误拒绝，尝试2未取消并成功resolve；活跃目标最终initialized=true/navigation=idle/errors=0，DOM无alert。** 被取消尝试的reject不能补签为当前Router错误。因此旧“5秒无提示”的上游关系已在本次条件下定位到取消/成功尝试分离，仍不能完成实际有效请求的故障隔离验收。

该链路只解释本轮为什么没有有效目标错误，不能反推旧R4/R4-R1或D15-P3的根因。第二次原始import为何resolve、并发mock缓存/调用上下文是否影响其结果，本轮没有对应内部事件，保持unverified。没有修改产品或原mock为另一种故障，不将取消请求分类为产品边界失败。默认索引/StrictMode等导航触发因素未逐个取证，也不指定某一因素为第二次调用根因。

| 节点 | 条件和结果 | 实际次数 |
| --- | --- | --- |
| A `R4-R2-UI-02-COLD-TRACE` | 同步ESM透传观察、空hash冷main、默认内置loader、原页面factory throw；0 passed/1 failed，真实CLI exit1 | CLI1 / worker1 / main1 |
| B `R4-R2-UI-02-COLD-PUBLIC` | 独立配置/缓存、直接真实Router、同四断言；**not_run**，不复用A数据补签 | 0 |
| 独立恢复与剩余公开行为 | 瞬时/持续失败、retry/切换/状态保持等 **not_run** | 0 |
| 开发兼容 | lazy八项及Shell/composition **not_run**，不计独立结果 | 0 |
| Windows | 产品0/8，辅助0/4，真实请求注入0；设备/会话条件 **not_run/unverified** | 0 |

## A与B的启动条件及观察扰动

| 条件 | A实际核对 | B准备状态 |
| --- | --- | --- |
| 冷入口 | setup只原生fs/path/url，测试静态import仅vitest/jsdom/React；无Router、module-routes、contribution或页面预载。seq7 main_import_enter后seq8 facade_loaded | 源码相同冷入口条件，尚未执行 |
| 产品链 | 仓库实际main→StrictMode DesktopApp→实际compileRegistry/contribution/Host交集→Shell/实际Router；没有替代路由或Shell | 同一真实入口，未执行 |
| Host与URL | 固定虚拟daily_finance1.0.0、canonical Profile、API摘要与实际贡献核对；初始空hash，未改#/daily入口 | 同样虚拟摘要/空hash，未执行 |
| 页面故障 | 原DailyFinancePage规范模块mock只增加factory次数日志并throw固定VIRTUAL_CHUNK_UNAVAILABLE；默认内置动态import与原生产route.loader不替换 | 同factory，未执行 |
| Router映射 | 精确裸react-router→新同步ESM门面；独立__c12_real_router→固定真实包；subpath不进门面，配置解析条件默认相同；没有async vi.mock/importOriginal | 裸Router直接相同固定真实包，没有门面或包装 |
| 导出/身份 | export*透传真实Context与其他导出；同步Reflect.apply原factory，返回原Router对象；实际日志确认factory函数、创建/订阅/合法Shell渲染 | 静态直连已核对，动态未验证 |
| 原loader语义 | 同route对象、this/args；返回原Promise身份；旁路then只记录终态，不另造业务Promise、不吞原错误 | 不加载loader包装 |
| 观察扰动 | **目标loader函数身份改变、Promise旁路监听、Router只读订阅、同步journal/fsync、React有界轮询**。未包装dispose/navigate/revalidate，未追加导航或retry | 只有原生journal/factory/DOM/cleanup记录，无Router遥测 |
| 活跃关系 | 按Router1/attempt1、2区分；signal.abort即时记录；Router状态与DOM关联。没有新Router/旧实例混签；dispose未额外包装，因此没有伪造dispose阶段 | 不读取或回填A的遥测 |

物理React/DOM/Router仅同一R5普通依赖alias根，JSX runtime走同一React根；真实Context透传且Shell与实际Router共同渲染。单包依据为静态alias/物理包元数据与本次运行链；没有枚举运行时全模块对象或声称额外第二实例检测。门面运行前标记动态未验证，本次确已加载并取得真实Router/loader终态，原静态文件仍保留not_run历史，动态结果单列。

## 首次持久时间线

以下相对时间从worker setup开始，不能与CLI开始混用。worker PID28308、parent自有CLI30912；34条连续seq。控制器活动读采用FileShare.ReadWrite且仅完整newline，首次双流、JSON、worker/controller journal均保留。

| seq | 阶段 | worker相对ms | 安全证据 |
| --- | --- | --- | --- |
| 1 | worker_start | 0.104 | 原生日志先于模块收集 |
| 2 | journal_ready | 4.066 | 同步落盘/fsync |
| 3 | hoisted_ready | 67.033 | factory计数器准备 |
| 4 | body_enter | 1176.064 | 测试正文开始 |
| 5 | virtual_dom_bridge_ready | 1253.461 | 空hash/虚拟bridge |
| 6 | act_enter | 1256.474 | 单独进入act |
| 7 | main_import_enter | 1259.668 | 原import Promise请求 |
| 8 | facade_loaded | 1600.756 | 正常依赖链取得真实Router函数 |
| 9 | main_import_resolved | 1652.500 | 原main Promise已返回 |
| 10 | root_created | 1654.237 | 实际desktopRoot存在 |
| 11 | router_create_enter | 1667.519 | 实际Router1开始创建 |
| 12 | router_created | 1671.248 | 原Router对象返回 |
| 13 | router_state | 1673.031 | active=True initialized=True navigation=idle targetMatch=False errors=0 |
| 14 | router_subscribed | 1674.643 | 只读观察订阅 |
| 15 | router_state | 1703.814 | active=True initialized=True navigation=loading targetMatch=False errors=0 |
| 16 | loader_enter | 1706.362 | Router1/attempt1；aborted=False |
| 17 | loader_aborted | 1709.326 | Router1/attempt1；aborted=True |
| 18 | router_state | 1711.365 | active=True initialized=True navigation=loading targetMatch=False errors=0 |
| 19 | loader_enter | 1713.262 | Router1/attempt2；aborted=False |
| 20 | virtual_factory_throw | 1718.657 | 原factory真实命中1 |
| 21 | loader_rejected | 1720.682 | Router1/attempt1；aborted=True；safeModuleCode=True |
| 22 | act_return | 1722.562 | React act另行返回 |
| 23 | dom_state | 1727.147 | fault=1 alert=False Shell/nav/Agent=True/True/True 活跃目标错误=False |
| 24 | loader_resolved | 1740.555 | Router1/attempt2；aborted=False |
| 25 | router_state | 1744.263 | active=True initialized=True navigation=idle targetMatch=True errors=0 |
| 26 | dom_state | 1758.451 | fault=1 alert=False Shell/nav/Agent=True/True/True 活跃目标错误=False |
| 27 | observation_finished | 6737.863 | fault=1 alert=False Shell/nav/Agent=True/True/True 活跃目标错误=False |
| 28 | assertions_enter | 6748.690 | 原四断言及关联前置开始 |
| 29 | assertions_finished | 6762.170 | 四软断言均执行；任一失败仍使节点failed |
| 30 | root_unmount_enter | 6764.153 | 卸载实际root |
| 31 | root_unmounted | 6767.438 | 实际卸载完成 |
| 32 | observer_unsubscribed | 6769.436 | 取消Router观察 |
| 33 | dom_globals_restored | 6772.149 | root空/全局恢复/bridge订阅0 |
| 34 | body_finished | 6774.198 | finally完成；不等于节点通过 |

main导入392.832ms、act总466.088ms，分别具备enter/terminal；没有main/act挂起。loader1 reject时已aborted=true；loader2 resolve后同实例目标match/idle/errors0，再关联DOM无alert。原factory不能精确归因到两个并发import的哪一个内部上下文，但route.loader1安全reject与route.loader2成功终态均由原Promise直接取得。

条件轮询以5000ms截止，每次使用min(20ms,remaining)有界计时。实际收口测量 **5013.572ms**，末次act/调度尾差 **13.572ms** 如实保留；没有把时限增大或执行固定五秒等待。CLI实际 **7623ms**、测试 **5601.685ms**，均在15秒/10秒上限内，无timeout/强制收口。计时尾差属于本轮观察限制，不改原首次值，也不以此延长或重跑。

## 原四断言及失败分类

| 要求 | 本轮实际执行 | 结果 |
| --- | --- | --- |
| 新前置：factory命中 | count1、hits>0 | passed |
| alert含“页面暂时无法打开” | 原textContent断言，无alert，值undefined | **failed** |
| main.shell存在 | 原not.toBeNull断言 | passed |
| 模块导航存在 | 原not.toBeNull断言 | passed |
| 统一Agent面板存在 | 原not.toBeNull断言 | passed |
| 当前有效目标错误槽/安全code关联 | 同实例错误槽不存在 | failed |
| 当前未取消loader安全拒绝 | 仅拒绝attempt1已abort；attempt2成功 | failed |
| Router initialized/nav idle | 当前Router1 true/idle | passed |

原四断言用expect.soft使四项均实际运行；任一失败仍失败，没有改成采样代替断言。runner记录3个AssertionError：alert、活跃错误槽、未取消安全拒绝；测试1 failed。没有Error/stack/模块对象/URL/完整DOM/raw秘密写入观察记录；安全reporter在源头保存真实状态/数量/错误类型，原JSON无需事后篡改。stdout为安全runner_result一行78 bytes，stderr0，流完成且无需删敏行。

任务卡分类适用“loader已安全reject，但已取消请求不能当产品缺陷”。**当前故障请求前置未建立，产品局部错误UI结论unverified**。旧P1 LAZY-001未独立关闭；不新定级P0/P1，不推断产品错误映射或边界失效，不凭Shell存在宣布UI-02通过。

最小复现材料是冻结A源码、cold-source.sha256与首次cold-trace目录。实际调用为固定Node运行Vitest、配置r4-r2-cold-trace.config.mjs、phase=cold-trace；已用过单次预算，控制器拒绝已有结果目录，**此处只供只读审阅，不授权重跑**。预期必须由当前有效加载产生安全错误且保留四入口；实际有效加载成功而取消加载失败。问题级别为独立门禁阻塞，非新定级产品缺陷。

需要总控决定的是：在仍保留真实冷main、默认loader和原导入故障意义的前提下，怎样让未取消的实际请求稳定收到模拟故障，以及是否需要修正测试接线。并发mock内部解析机制保持待核实。不建议延时、预热、重打包或另一纯bootstrap任务，不自行指定或实现产品返修。

## 输入、预算与旧材料

起点 **507/507 matched**，0 mismatch/missing，staged=0；SHA-256 `fac063506c7aa11be925655b7001a0493c93d172bccb9a2e749544d687faa2b0`。仓库新起点与历史R5源码390分开。只读受验根C:/MarisLazyR5/R5-20261002-222300：构建源389、out140、Python资源67逐项一致；EXE/asar/lock/fuses与任务固定值一致，Node24.21.0/Vitest5.0.2/React及React DOM19.3.0/Router8.4.0/jsdom30.1.1确认，Vite7.3.6/TypeScript6.0.3仅作为已装静态工具。

| 固定物 | SHA-256 |
| --- | --- |
| apps/desktop/out/Maris-win32-x64/Maris.exe | 64ce71f3a7b3055f9ad27f6d611e28c4af7e9ba8b86d8b21399b7b422844a80e |
| apps/desktop/out/Maris-win32-x64/resources/app.asar | 5ba47909537e1419dc275fa3ca1e5e076a1aa6d5c0205229f91defb92ddd0931 |
| pnpm-lock.yaml | 5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a |

新冷入口源码11项先静态冻结（包括审计、setup、门面、A/B测试及配置、controller、安全reporter、verify）。MJS/TS/PowerShell解析、精确alias、防循环、相同真实包/React根与不预载核对通过。普通静态工具最初使用C:/绝对ESM import产生ERR_UNSUPPORTED_ESM_URL_SCHEME；首次源码/脱敏错误另存static-first-*，改file URL后静态通过。该普通静态工具没有Vitest、worker或main请求；它的格式修正1次与目标前额外worker预算0次分别记录。目标源码冻结后不变，A未修改/重跑，B无第三次main，目标前更正worker未使用。

此前成功27独立节点、outbox42及setting/PATH关闭证据沿用，不重新执行、不并入本轮计数。旧public/r1/r2/r3/r4/r4-r1、D15/D15-R1源码/报告/首次证据由起终快照核对，只读保持。总控D15-R1 finite complete属于输入，不计独立passed。

## 原24项完整映射

原120案例ID、12字段、前11列原要求保持。B整体仍0 passed/1 failed/19 blocked/4 not_run，A64 passed/C20与D12 not_run保持。下列原历史仅引用，不改写原失败、不将执行方正常EXE19门禁补成独立设备证据。

### P4B-SEC-01 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：固定 Electron 构建。
- 输入：BrowserWindow 配置与运行时 renderer。
- 操作：静态检查并在 renderer 探测。
- **完整原预期**：sandbox/contextIsolation 开启、nodeIntegration 关闭；无 `require/process/fs/child_process` 或任意 preload 对象。
- 已有历史部分：原 PUB-03 在新依赖下再次通过；R1-MAIN-01 实际导入main但窗口是虚拟adapter。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：生产 preferences逻辑有证据；实际EXE renderer Node isolation未执行。
- 当前状态：`blocked`；整项未满足时不标passed。

### P4B-SEC-02 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：CSP/导航 allowlist 冻结。
- 输入：inline script、data/javascript URL、未知 origin、新窗口、外链。
- 操作：从不可信内容触发导航/打开。
- **完整原预期**：CSP 阻止执行；未知导航/窗口拒绝；获准外链只由 main 安全打开，不加载进应用权限域。
- 已有历史部分：原 PUB-03 CSP字符串再次通过；main安全默认/导航接线只读。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：未在真实页面触发 inline/data/javascript、导航/new-window和外链。
- 当前状态：`blocked`；整项未满足时不标passed。

### P4B-SEC-03 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / contract/unit / contract / auto。
- 前置：preload 类型合同可导入。
- 输入：枚举 contextBridge 暴露对象。
- 操作：与 allowlist 对比并尝试直接 ipcRenderer/send/invoke。
- **完整原预期**：只暴露窄 typed 方法；无通用 channel、Node require、密钥或进程控制。
- 已有历史部分：R1-SHELL-09实际导入main preload，capture contextBridge，枚举六组窄API/冻结对象，尝试读取通用invoke/send/ipcRenderer/require/process等均undefined，调用typed方法验证固定channel。companion preload只读为getState/openMain。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：main preload契约部分通过；未执行companion暴露对象与整个renderer域，保守保持blocked。
- 当前状态：`blocked`；整项未满足时不标passed。

### P4B-SEC-04 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：IPC handlers 已注册。
- 输入：伪造 sender、错 origin、额外/错型参数、未知 channel、重复调用。
- 操作：逐项 invoke/send。
- **完整原预期**：sender 与参数双校验；稳定拒绝；不得启动进程、改设置、打开窗口或泄露异常。
- 已有历史部分：原 PUB-04 sender/frame/origin/严格参数拒绝再次通过；R1 main导入注册真实handlers。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：未对注册handler执行未知channel/重复/全部无副作用断言或真实Electroninvoke。
- 当前状态：`blocked`；整项未满足时不标passed。

### P4B-SEC-05 — blocked

- 来源/风险/层/环境/方式：F07/F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：假 token 与假 API key。
- 输入：localStorage/sessionStorage/IndexedDB/renderer 内存转储、main safeStorage。
- 操作：登录/刷新/重启并检查各层。
- **完整原预期**：refresh/device token 与 API key 只在 main/OS 保护边界；renderer 无持久原文；日志与 crash dump 无值。
- 已有历史部分：原PUB-01/02虚拟加密失败闭合/损坏/密文通过；R1-SHELL-05虚拟owner bootstrap/refresh/revoke通过，R1-OB容量/密文逻辑保持。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：非Windows safeStorage；未检查真实renderer storage/内存、secret/crash dump或OS DPAPI。
- 当前状态：`blocked`；整项未满足时不标passed。

### P4B-SEC-06 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / API/integration / Windows/Electron / auto。
- 前置：后端绑定随机 loopback port。
- 输入：只知道端口、错 nonce、错 origin、过期 access、远程地址。
- 操作：绕过 main 直连 Host。
- **完整原预期**：端口不是认证；nonce/origin/token 均校验；只绑定 loopback，远程连接拒绝。
- 已有历史部分：R1-SHELL-01拒绝非HTTP127.0.0.1 endpoint；02 main-only Bearer与并发401刷新；07 managed坏nonce拒绝。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：HTTP为fake fetch，nonce为fake child；实际随机监听/origin/access到期/远程连接未运行。
- 当前状态：`blocked`；整项未满足时不标passed。

### P4B-SEC-07 — blocked

- 来源/风险/层/环境/方式：F11/F12 / P0 / security/manual / Windows/Electron / auto。
- 前置：模块标签、错误、消息均含虚拟恶意 HTML。
- 输入：script/img/event handler/RTL/超长文本。
- 操作：渲染导航、通知、Agent panel、错误。
- **完整原预期**：文本安全编码、布局有界且不执行；不得改变 IPC、模块注册或权限。
- 已有历史部分：未做恶意文本UI渲染。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：真实HTML/RTL/长文本编码布局与无脚本执行证据缺失。
- 当前状态：`blocked`；整项未满足时不标passed。

### P4B-SEC-08 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / desktop/e2e / Windows/Electron / auto。
- 前置：可注入 preload/backend/lazy-load 故障。
- 输入：内部路径、SQL、堆栈、token canary。
- 操作：触发并查看 UI、console、日志。
- **完整原预期**：用户只见稳定安全错误和 request ID；renderer console/日志无秘密或未授权数据。
- 已有历史部分：原PUB-02 corruption安全错误；R1-SHELL-03/04在401刷新失败、503、非法DTO、network异常下安全error不含虚拟canary；R1-OB-07 dialog rejection无raw console输出。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：未实测实际UI/request ID/preload/lazy故障或真实console/log/crash dump。
- 当前状态：`blocked`；整项未满足时不标passed。

### P4B-SUP-01 — blocked

- 来源/风险/层/环境/方式：D9 BackendSupervisor / P0 / desktop/e2e / Windows/Electron / auto。
- 前置：supervisor 可记录 PID+nonce。
- 输入：自己启动、手工启动、伪造同 PID。
- 操作：请求停止/应用退出。
- **完整原预期**：只停止 PID+nonce 匹配且由本实例启动的子进程；手工/他实例进程保持。
- 已有历史部分：R1-SHELL-07错误managed nonce拒绝并清理候选；08external observed child shutdown不调用stop/forceStop。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：虚拟adapter；真实PID/nonce、外来同PID和进程树隔离未执行。
- 当前状态：`blocked`；整项未满足时不标passed。

### P4B-SUP-02 — blocked

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：端口分配与 ready 协议冻结。
- 输入：端口冲突、无 ready、坏 nonce、ready 超时。
- 操作：启动后端。
- **完整原预期**：使用随机可用 loopback 端口；超时进入离线/诊断并清理自有子进程，不把 health 当 ready。
- 已有历史部分：R1-SHELL-07坏nonce fail-closed且不进入ready；06成功fake ready。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：端口冲突、ready总超时、随机loopback和真实自有清理未覆盖，不能把health当ready。
- 当前状态：`blocked`；整项未满足时不标passed。

### P4B-SUP-03 — blocked

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：假后端可崩溃。
- 输入：启动前崩溃、ready 后崩溃、连续崩溃。
- 操作：观察重启策略。
- **完整原预期**：状态转 offline；重启次数/退避有界，不形成重启风暴或重复 run；用户可恢复。
- 已有历史部分：R1-SHELL-06 fake child exit→offline，recover退避1/2/4秒、三次上限，第四次exhausted，shutdown阻止再start。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：注入delay/child，不是Windows真实崩溃；启动前崩溃、健康循环与全部UI状态未覆盖。
- 当前状态：`blocked`；整项未满足时不标passed。

### P4B-SUP-04 — blocked

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：已有手动后端或两个 app 启动请求。
- 输入：重复启动、开发连接模式。
- 操作：启动/关闭两个客户端。
- **完整原预期**：不产生重复 owned 后端；连接手动后端时不取得停止权；状态可区分。
- 已有历史部分：R1-SHELL-06并发start/recover single-flight不增重复start；08external不启动owned也无停止权。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：未执行双真实客户端/单实例EXE场景。
- 当前状态：`blocked`；整项未满足时不标passed。

### P4B-SUP-05 — not_run

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / security/manual / Windows/Electron / manual。
- 前置：目标 Windows，后端含子线程/连接。
- 输入：正常退出、强关主窗口、系统注销。
- 操作：检查进程树/端口/文件锁。
- **完整原预期**：自有后端按冻结时限退出，无僵尸/孤儿/占用端口；未拥有进程不受影响。
- 已有历史部分：真实退出、强关和注销均未执行；R1-MAIN-02/03仅虚拟Hostshutdown/窗口destroy。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：manual not_run；无owned资源仅表示没启动，不能推断cleanup通过。
- 当前状态：`not_run`；整项未满足时不标passed。

### P4B-SUP-06 — blocked

- 来源/风险/层/环境/方式：D9 offline recovery / P0 / desktop/e2e / Windows/Electron / auto。
- 前置：renderer 有未发送虚拟消息。
- 输入：后端离线→恢复、应用重启、重复点击。
- 操作：发送并观察 client_event_id/GET。
- **完整原预期**：未发送内容和同一 ID 保留；恢复后只提交一次；UI 不凭新 ID 制造重复账候选。
- 已有历史部分：原PUB-11不变断言1 passed，原其他10再次通过；新增R1-OB26覆盖持久保留/确认/身份/故障/容量，加R1-MAIN5实际main接线。建议关闭原OUTBOX-001的公开持久化P1。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：真实老化原生提示unverified、恢复后GET/只提交一次与实际UI缺失；整项从failed改blocked，原P0风险不变。
- 当前状态：`blocked`；整项未满足时不标passed。

### P4B-UI-01 — blocked

- 来源/风险/层/环境/方式：F12 / P1 / contract/unit / contract / auto。
- 前置：compiled registry 与 `/modules` fixture。
- 输入：后端启用/禁用、桌面缺失、版本不兼容、未知模块。
- 操作：计算交集。
- **完整原预期**：只渲染两侧均存在且兼容的模块；未知/禁用不导航、不预加载。
- 已有历史部分：原PUB-05canonical registry/Host交集再次通过，R1-SHELL-10两纯测试contribution正常compile。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：实际导航/preload未运行；没有创建真实第二产品模块。
- 当前状态：`blocked`；整项未满足时不标passed。

### P4B-UI-02 — failed

- 来源/风险/层/环境/方式：F12 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：两个 lazy route。
- 输入：chunk 加载失败、重试成功、切换模块。
- 操作：导航并恢复。
- **完整原预期**：局部错误边界可重试，Shell/登录/其他模块可用；不循环加载或丢当前会话。
- 已有历史部分：未执行两个lazy routes的chunk故障/局部retry。；R4-R1 factory1、5016ms无alert，Router终态未关联。
- 本轮新增：A一次0pass/1fail；main/act已完成，同Router两attempt：1 abort+safe reject，2未abort resolve，活跃idle/target match/errors0，无alert，Shell/nav/Agent三断言通过。
- 具体缺口与层级：有效请求故障前置未建立，LAZY-001不关闭；B未执行。独立恢复/健康切换/状态保持、真实Windows chunk与会话保持尚无证据。取消请求失败不能定级为新的产品缺陷。
- 当前状态：`failed`；整项未满足时不标passed。

### P4B-UI-03 — blocked

- 来源/风险/层/环境/方式：F12 / P1 / contract/unit / contract / auto。
- 前置：冻结 OpenAPI 与生成命令。
- 输入：后端 DTO 字段/枚举/required 改变；生成物陈旧。
- 操作：CI 比较生成差异并编译。
- **完整原预期**：漂移门禁失败并定位；不得靠手写 API 类型掩盖差异或运行时下载 schema。
- 已有历史部分：生成物和OpenAPI保持冻结输入，没有运行生成/类型漂移mutation。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：未取得失败定位或CI drift独立证据。
- 当前状态：`blocked`；整项未满足时不标passed。

### P4B-UI-04 — blocked

- 来源/风险/层/环境/方式：F12 / P1 / contract/unit / contract / auto。
- 前置：UI contribution 合同冻结。
- 输入：hostUiMajor、route/path/setting/profile/companion 冲突。
- 操作：编译期注册和启动验证。
- **完整原预期**：不兼容或冲突稳定失败；Shell 无 `if moduleId` 业务分支。
- 已有历史部分：R1-SHELL-11四种module/profile/route ID/appearance冲突拒绝，12不兼容major和非canonical输入拒绝；13跨module相同setting key仍接受两模块，首次失败。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：UI-04完整独立结构/strict贡献及启动验证映射尚未完成，新P1停止；不能由路径通过直接passed。
- 当前状态：`blocked`；整项未满足时不标passed。

### P4B-CMP-01 — blocked

- 来源/风险/层/环境/方式：F13；U02 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：daily/wealth contributions 与假状态流。
- 输入：切换模块及 idle/thinking/tool/confirmation/error/offline。
- 操作：观察窗口、Profile 和状态。
- **完整原预期**：始终只有一个毛毛窗口/Agent 入口；主形态随 contribution，子状态不创建第二 Agent或触发写入。
- 已有历史部分：R1-MAIN-01虚拟BrowserWindow构造仅Maris和毛毛，Host启动不被dialog等待。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：实际单毛毛/Agent入口、contribution主形态和完整子状态流未运行。
- 当前状态：`blocked`；整项未满足时不标passed。

### P4B-CMP-02 — blocked

- 来源/风险/层/环境/方式：U01/F13 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：新设备设置。
- 输入：首次和第二次关闭主窗口。
- 操作：关闭、从 Tray 恢复、再次关闭。
- **完整原预期**：首次隐藏并只提示一次；第二次不重复提示；Host/毛毛按设置驻留且无数据丢失。
- 已有历史部分：未执行真实close/Tray恢复/提示一次场景。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：虚拟ready-to-show retention不等于首次close提示；真实设备not_run子项保持。
- 当前状态：`blocked`；整项未满足时不标passed。

### P4B-CMP-03 — blocked

- 来源/风险/层/环境/方式：U01 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：关闭策略可切换。
- 输入：退出/每次询问/隐藏，Tray 打开/隐藏。
- 操作：每种设置执行关闭与取消。
- **完整原预期**：行为精确对应设置；“退出”清理自有后端；询问取消不退出；Tray 状态一致。
- 已有历史部分：未测试三种closePolicy与询问取消/Tray；R1-MAIN before-quit仅退出接线。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：不以mock app.quit或E2E timer当生产关闭策略证明。
- 当前状态：`blocked`；整项未满足时不标passed。

### P4B-CMP-04 — not_run

- 来源/风险/层/环境/方式：U05 / P1 / security/manual / Windows/Electron / manual。
- 前置：新安装测试 profile。
- 输入：首次运行、显式启用/禁用开机启动。
- 操作：检查 OS 启动项和 UI。
- **完整原预期**：默认关闭且无启动项；只有明确操作才创建；禁用清理本应用项，不改其他应用。
- 已有历史部分：未创建/删除OS启动项；main fixture app.setLoginItemSettings是mock。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：manual not_run；E2E抑制启动项不等于OS合同通过。
- 当前状态：`not_run`；整项未满足时不标passed。

### P4B-CMP-05 — not_run

- 来源/风险/层/环境/方式：F13 / P1 / desktop/e2e / external/manual / manual。
- 前置：多显示器/缩放/全屏测试设备。
- 输入：拖动、置顶、重启、拔屏、分辨率变化、全屏、隐私、键盘。
- 操作：逐项操作并重启。
- **完整原预期**：位置用临时文件原子替换并恢复/夹取；全屏按规则隐藏；隐私不显示金额；键盘入口可达。
- 已有历史部分：未修改显示器/缩放/全屏/窗口坐标或测试隐私键盘。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：实际位置夹取/重启/多屏/全屏/键盘/隐私UI与全部人工设备条件未执行，整项manual not_run保持。
- 当前状态：`not_run`；整项未满足时不标passed。

### P4B-CMP-06 — not_run

- 来源/风险/层/环境/方式：U02；主题要求 / P2 / desktop/e2e / external/manual / manual。
- 前置：支持/不支持透明窗口设备。
- 输入：透明失败、普通迷你窗降级；light/dark/system/high-contrast/reduced-motion；中外行情色。
- 操作：切换设备条件和主题。
- **完整原预期**：可安全降级且合同不变；文本对比/焦点可辨；reduced motion 生效；收入/支出色不复用涨跌色。
- 已有历史部分：未启动透明/降级窗口或切换系统主题。
- 本轮新增：not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。
- 具体缺口与层级：manual not_run；真实对比度/焦点/reduced motion/颜色语义未测试。
- 当前状态：`not_run`；整项未满足时不标passed。

## 资源、未执行范围和最终交接

真实desktopRoot已act unmount，rootEmpty/globalRestored/domClosed均true；观察Router订阅1次取消，signal旁路监听移除；bridge runtime/modules/subscribe各2，unsubscribe2/active0/settingsWrites0。StrictMode真实生命周期的两次外围读取不等于auth或provider重复调用。没有新增window/external/outbox/provider等端口或财务操作，也没有真实session内容读取。

CLI30912自然exit1、journal登记worker28308已结束、无timeout/强杀；worker自身exit事件没有落盘，具体worker exit code/方式unknown，不能复制父退出码。实际父子身份由创建句柄和journal验证，不用祖先PID猜测或精确总进程数门禁。之后Get-Process再次确认这两个PID已不存在；Win32_Process只读枚举抛CimException，childEnumerationVerified=false，空列表不能表示全树零残留。资源证据限这两个已登记对象及DOM/订阅，系统所有后代和历史全量枚举unverified；未再启动或全局结束任何进程。

产品0/8、辅助safeStorage Electron0/4、CDP注入0；没有建立C12-R4-R2外部profile/db/session、实际窗口/后端或测试监听。真实Windows chunk注入恢复、session持久化、CSP/秘密/恶意文本、generated drift、贡献严格结构余项、原生老化提示、Tray/closePolicy/单实例/毛毛状态均未执行。OS注销/重启、启动项、多屏/DPI/拔屏/系统主题/透明降级保持原人工not_run/unverified，不要求用户现在点击。

只清理经绝对专属边界/no-reparse核对的新r4-r2/cache，删除1个缓存文件、目录不存在；首次源码/双流/journal/JSON/静态首次错误均保留。Git仅只读staged/diff检查；无任何Git写操作。不修改产品、开发测试、依赖/lock/生成物/package/Forge/migration/冻结/control/overview/其他角色；不Docker/PG/OpenClaw/微信/DeepSeek/provider或系统配置、时钟、安全软件。

终点与交付复算由r4-r2-delivery.py独立读取首次证据：固定507仅tester/B备注/旧主报告与清单追加四路径获准变化，其余503精确不变；source389/out140/resources67与包/fuses保持，120唯一ID/12列/前11列/原全部状态/B外字节及旧文档原字节prefix保持。最终实际计数与交付哈希见evidence/r4-r2/end-audit.json、delivery-verification.json及delivery.sha256，以工具结果为准。

交付**blocked / finished**后停止。提交本报告、新增r4-r2测试/观察工具/首次证据、原文档追加、矩阵B备注及自身状态给总控review，等待精确接线裁定；不创建下一Prompt、调度其他角色、不自动续跑，不宣布总控接受或P4-B complete。
