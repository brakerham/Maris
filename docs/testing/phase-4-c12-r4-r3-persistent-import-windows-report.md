# P4-C12-R4-R3 持续导入故障与Windows验收报告

交付：**blocked / finished**，供总控review。既有独立测试智能体、唯一负责人；control `2026-10-03T03:56:00+08:00`，[R3任务卡](../coordination/prompts/p4-c12-r4-r3-persistent-import-tester.md)。全部是虚拟输入，未修改产品或旧首次结果，LAZY-001/UI-02/P4-B未关闭。

## 已验证结果和停止位置

**持续导入故障P通过**：实际compileRegistry/真实contribution/createModuleRoutes默认内置loader，两次并发调用及等待二者终态后的第三次调用均安全reject，错误码desktop_module_unavailable；真实故障ESM求值一次，精确目标映射命中。

**全新冷入口A在测试模块初始化阶段达到硬限**：持久journal只有worker_start/journal_ready，尚未进入body，main/act/fixture/loader/DOM和原四断言均未开始。控制器在原15秒预算内定向结束已创建的自有树；登记CLI和worker均结束。A没有runner JSON，不伪造测试failed节点、正文异常或产品缺陷。B与全部后续停止。超时原因未定位，产品行为unverified，不扩大等待/缓存重置/预热或盲重跑。

| 节点 | 条件 | 首次结果 / 预算 |
| --- | --- | --- |
| P `R4-R3-INJECTION-PERSISTENT` | 无门面真实Router、真实默认loader、两并发+随后一次、没有main | **1 passed/0 failed**；CLI1/worker1/main0；3次调用不是3个节点 |
| A `R4-R3-UI-02-COLD-TRACE` | 全新worker/cache、空hash冷main、同步门面、同真实失败fixture；配置已冻结 | **blocked_pre_body_timeout**；CLI1/worker1/main0；业务断言未执行 |
| B `R4-R3-UI-02-COLD-PUBLIC` | 第三个独立worker、直接真实Router、无门面/loader包装 | **not_run**；CLI0/worker0/main0 |
| 独立恢复/公开余项 | 可控可信loader恢复，与初始持续失败fixture分列 | not_run |
| 开发兼容 | lazy八项及Shell/composition允许一次，单列 | not_run |
| Windows | 固定EXE/真实chunk网络故障及原生行为 | 产品0/8、辅助0/4、真实请求注入0 |

## 精确注入方案及实际命中

去掉新增测试中的目标vi.mock factory，旧R4/R4-R1/R4-R2全部原样保留。新增pre resolveId只允许已知DailyFinancePage绝对规范路径（无扩展或.tsx），或精确相对请求../modules/daily-finance/DailyFinancePage且importer是实际module-routes.tsx。只归一盘符/反斜杠以及单层已知/@id/、/@fs/；不全路径小写、不URL解码、不通配目录/Router/其他页面。未知query/hash不映射并报固定安全配置错误。

固定Vite module-runner.js的dynamicRequest会将相对请求解析为绝对路径再请求；Vitest Windows传输会包装/@id/，Vite root外可用/@fs/。新resolver同时精确支持这些已知形态，不能仅用未经证实的相对alias。**本次实际命中形态为相对请求、importerBound=true，targetOrdinal1→fixtureOrdinal1，unsupportedQuery=false，记录1条**；其他规范形态只完成静态谓词核对，不冒称实际动态命中。

fixture为新r4-r3-failing-page.tsx：纯JS、零JSX、零import，先通过原生global recorder同步记录fixture_evaluation_enter，再顶层throw固定VIRTUAL_CHUNK_UNAVAILABLE，声明不可达default导出。TypeScript静态转译确认未注入任何React/helper import；.tsx保留原已知扩展形态。只有目标模块被重定向，产品默认loader/route/errorElement、其他产品模块保持真实。

这是**真实ESM模块求值失败令import Promise拒绝**，不是网络chunk404，不改.default getter、Page、loader或Router错误槽。没有目标vi.mock/doMock/importActual、Router async mock、cache-bust、invalidate/reset、生产修改/外部monkeypatch。普通Vite解析/缓存是runner原有行为，未新增缓存操纵。

resolver命中回执在CLI进程的独立resolver.journal中同步追加/fsync；fixture/loader记录在worker.setup建立的journal。两者起点不同，不把相对毫秒直接排成跨进程因果时序。只保存ordinal/安全布尔/PID，不输出请求路径、URL、模块对象或raw错误。

## P的默认loader终态证据

P在正文动态导入真实contribution、compileRegistry与createModuleRoutes，调用createModuleRoutes(registry)而不传loaders。没有导入main，也没有构造Router导航或DOM。对原route.loader的调用只做诊断catch，原Promise的拒绝和安全码被记录；两个并发await完成后才调用第三次。

| seq | worker阶段 | worker相对ms | 实际终态 |
| --- | --- | --- | --- |
| 1 | worker_start | 0.098 |  |
| 2 | journal_ready | 11.758 |  |
| 3 | body_enter | 73.685 |  |
| 4 | p_call_enter | 3150.586 | call1 / defaultLoader=true |
| 5 | p_call_enter | 3154.070 | call2 / defaultLoader=true |
| 6 | fixture_evaluation_enter | 3174.721 | fixtureOrdinal1，实际求值count1 |
| 7 | p_call_terminal | 3178.360 | call1 reject=True safeModuleCode=True rawVirtualError=False |
| 8 | p_call_terminal | 3180.586 | call2 reject=True safeModuleCode=True rawVirtualError=False |
| 9 | p_call_enter | 3182.708 | call3 / defaultLoader=true |
| 10 | p_call_terminal | 3184.421 | call3 reject=True safeModuleCode=True rawVirtualError=False |
| 11 | assertions_enter | 3186.305 |  |
| 12 | assertions_finished | 3189.440 |  |
| 13 | body_finished | 3191.512 |  |

call1/2均安全拒绝后call3进入，三次均不透传原虚拟错误。实际fixture求值1次，不从调用次数推定三次求值。当前结果证明固定runner/配置下并发与随后请求持续拒绝；不反推旧manual mock的实际内部分支，也不计为UI或Windows通过。

P测试3129.658ms、CLI 8494ms，实际exit0，无timeout/强杀；13条连续worker记录、1条resolver映射、JSON1 passed、stdout安全摘要78bytes/stderr0。首次文件均保留。

## A首次未进入正文的阶段与纠正预算

| 记录 | 实际证据 |
| --- | --- |
| 自有CLI启动 | PID15796；startedUtc=2026-10-03T07:19:04.5664849+00:00 |
| worker登记 | PID16464、parent15796；controller运行中确认身份 |
| setup第一条 | seq1 worker_start，0.116ms |
| setup第二条 | seq2 journal_ready，11.964ms；此后没有其他完整事件 |
| 正文/主入口 | body_enter、main_import_enter、act_enter均不存在；main请求0 |
| fixture/loader/Router | 实际求值/loader调用0；无resolver映射journal，Router状态未取得 |
| 时限收口 | controller 14512ms进入deadline_termination_enter；process耗时14595ms、自然退出false、强制定向收口true，父exit-1 |
| 最后持久阶段 | journal_ready；不是某个被推定的React/jsdom/Router内部等待 |
| JSON/双流 | runner JSON未生成，stdout/stderr均0bytes，独立流收口完成 |

原生setup先于测试模块初始化，日志每条同步写入/fsync、写失败立即退出；冻结正文在产品调用之前首先写body_enter。这支持本次尚未进入正文、没有fixture/loader/main目标阶段。不能从空stdout独自作此结论，也不能宣称15秒test断言超时：本轮是**CLI收集/初始化硬限**，test10秒规则保留但正文尚未启动。

当前没有定位到可更正的纯工具配置错误。目标前修正授权同时要求错误范围可证明与首次材料冻结/输入不变/自有进程退出；仅“main没开始”不构成盲重试理由。于是**额外前置worker0、目标更正0、目标重跑0**。cold-trace-first.sha256冻结5个首次文件；pre-main-no-retry-ruling.json记录不追加理由。没有修改A配置/源码或复跑，B与后续not_run。

## A/B原四断言和传播要求

| 原业务要求/前置 | A | B |
| --- | --- | --- |
| alert含“页面暂时无法打开” | not_run | not_run |
| main.shell存在 | not_run | not_run |
| 模块导航存在 | not_run | not_run |
| 统一Agent面板存在 | not_run | not_run |
| 当前未取消loader安全reject | 未启动，不从P补签 | not_run |
| 同活跃Router目标错误槽安全code | Router未取得 | not_run |
| main与act分别enter/terminal | 均未开始 | not_run |

新A/B保留同原虚拟bridge/jsdom/global、空hashURL、真实StrictMode/main/contribution/Host交集。A的同步ESM透传门面及Promise/Router身份保持静态检查通过：精确裸Router映射、独立真实alias、防循环/单物理React根、export*真实Context，仅包装目标loader并返回原Promise/Router。它的函数身份变化/旁路监听/订阅/fsync扰动均披露。**本次A没有动态加载到门面，不能借R2的门面运行写成本轮动态通过**。B直连真实包、不安装门面、不回填A遥测。

本轮没有有效目标的取消/错误槽/DOM关联，产品结论unverified，无新增已定级产品P0/P1，不建议关闭LAZY-001；原R2取消attempt1/有效attempt2的历史仍独立保留。P故障接线已经证明，后续需总控针对这次正文前初始化硬限裁定下一步，本角色不自行修改或再生成bootstrap/延时任务。

## 固定输入、静态首错和可见性间隔

新起点**544/544 matched**、暂存空、0 mismatch/missing；清单SHA `45be10a1817a82ab7fb0fee3c851954c13455b7eef729c7bf7a39125ec2fccb0`。旧受验包构建源389/out140/Python资源67逐项匹配，EXE/asar/lock/fuses保持任务固定值。Node24.21.0、Vitest5.0.2、Vite7.3.6、React/DOM19.3.0、Router8.4.0、jsdom30.1.1及已装TypeScript6.0.3元数据核对；不安装/下载/build/package，不修改PATH/代理/时钟/安全配置。

- apps/desktop/out/Maris-win32-x64/Maris.exe：`64ce71f3a7b3055f9ad27f6d611e28c4af7e9ba8b86d8b21399b7b422844a80e`。
- apps/desktop/out/Maris-win32-x64/resources/app.asar：`5ba47909537e1419dc275fa3ca1e5e076a1aa6d5c0205229f91defb92ddd0931`。
- pnpm-lock.yaml：`5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。

15项新目标源码语法/静态解析后先冻结cold-source.sha256；includes P/A/B各配置与测试、精确resolver/fixture、同步门面、原生setup/controller/safe reporter/审计/verify。MJS/TS/PowerShell解析、零import零JSX、目标/未知query/单包根/无预载/不使用manual mock核对通过。普通静态谓词首错known_canonical_id_missing来自五字符Vite包装误切六，首次resolver/verify和安全错误保留；改为精确五字符后通过。当时worker/fixture/loader/main均0，**普通静态修正1**与**额外前置worker0**分别统计。

04:08接单后至15:15可见控制返回有长聊天/控制空档，期间缺少连续检查点，不能宣称持续工作或外部角色状态。没有本轮目标后台运行；用户“继续”后重读同版control，记录限制并重设检查点，恢复静态准备。动态P于15:18、A于15:19，实际进程耗时按各process.json列出，不把整段聊天间隔当目标耗时。系统时钟未修改。

只读子任务review_test_handoff给出规范ID、importer缺失与单层Vite包装、.tsx零JSX建议，未执行目标或获准写入；由父任务采纳并独立静态核对。最终当前源码复核回执未取得，最后工具状态pending_init，父任务中断；只把已收到的静态信息作为输入，不冒称子任务验收或持续运行，见subagent-read-only-receipt.json。

旧成功27独立、outbox42/setting/PATH关闭、R4/R4-R1/R4-R2及D15/D15-R1材料只读沿用，不复跑或加入本轮passed统计。新P只1个工具前置验证，UI节点实际执行0、A执行尝试1且blocked，兼容0、产品0/8、辅助0/4。

## 原24项完整验收映射

P不替代UI/设备验收。矩阵120 ID/12字段/原前11列保持；B仍0 passed/1 failed/19 blocked/4 not_run，A64 passed、C20/D12 not_run保持。原完整要求、已有部分证据、本轮和缺口逐项如下。

### P4B-SEC-01 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：固定 Electron 构建。
- 输入：BrowserWindow 配置与运行时 renderer。
- 操作：静态检查并在 renderer 探测。
- **完整原预期**：sandbox/contextIsolation 开启、nodeIntegration 关闭；无 `require/process/fs/child_process` 或任意 preload 对象。
- 已有历史部分：原 PUB-03 在新依赖下再次通过；R1-MAIN-01 实际导入main但窗口是虚拟adapter。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：生产 preferences逻辑有证据；实际EXE renderer Node isolation未执行。
- 当前状态：`blocked`；整体要求未满足不标passed。

### P4B-SEC-02 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：CSP/导航 allowlist 冻结。
- 输入：inline script、data/javascript URL、未知 origin、新窗口、外链。
- 操作：从不可信内容触发导航/打开。
- **完整原预期**：CSP 阻止执行；未知导航/窗口拒绝；获准外链只由 main 安全打开，不加载进应用权限域。
- 已有历史部分：原 PUB-03 CSP字符串再次通过；main安全默认/导航接线只读。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：未在真实页面触发 inline/data/javascript、导航/new-window和外链。
- 当前状态：`blocked`；整体要求未满足不标passed。

### P4B-SEC-03 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / contract/unit / contract / auto。
- 前置：preload 类型合同可导入。
- 输入：枚举 contextBridge 暴露对象。
- 操作：与 allowlist 对比并尝试直接 ipcRenderer/send/invoke。
- **完整原预期**：只暴露窄 typed 方法；无通用 channel、Node require、密钥或进程控制。
- 已有历史部分：R1-SHELL-09实际导入main preload，capture contextBridge，枚举六组窄API/冻结对象，尝试读取通用invoke/send/ipcRenderer/require/process等均undefined，调用typed方法验证固定channel。companion preload只读为getState/openMain。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：main preload契约部分通过；未执行companion暴露对象与整个renderer域，保守保持blocked。
- 当前状态：`blocked`；整体要求未满足不标passed。

### P4B-SEC-04 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：IPC handlers 已注册。
- 输入：伪造 sender、错 origin、额外/错型参数、未知 channel、重复调用。
- 操作：逐项 invoke/send。
- **完整原预期**：sender 与参数双校验；稳定拒绝；不得启动进程、改设置、打开窗口或泄露异常。
- 已有历史部分：原 PUB-04 sender/frame/origin/严格参数拒绝再次通过；R1 main导入注册真实handlers。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：未对注册handler执行未知channel/重复/全部无副作用断言或真实Electroninvoke。
- 当前状态：`blocked`；整体要求未满足不标passed。

### P4B-SEC-05 — blocked

- 来源/风险/层/环境/方式：F07/F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：假 token 与假 API key。
- 输入：localStorage/sessionStorage/IndexedDB/renderer 内存转储、main safeStorage。
- 操作：登录/刷新/重启并检查各层。
- **完整原预期**：refresh/device token 与 API key 只在 main/OS 保护边界；renderer 无持久原文；日志与 crash dump 无值。
- 已有历史部分：原PUB-01/02虚拟加密失败闭合/损坏/密文通过；R1-SHELL-05虚拟owner bootstrap/refresh/revoke通过，R1-OB容量/密文逻辑保持。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：非Windows safeStorage；未检查真实renderer storage/内存、secret/crash dump或OS DPAPI。
- 当前状态：`blocked`；整体要求未满足不标passed。

### P4B-SEC-06 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / API/integration / Windows/Electron / auto。
- 前置：后端绑定随机 loopback port。
- 输入：只知道端口、错 nonce、错 origin、过期 access、远程地址。
- 操作：绕过 main 直连 Host。
- **完整原预期**：端口不是认证；nonce/origin/token 均校验；只绑定 loopback，远程连接拒绝。
- 已有历史部分：R1-SHELL-01拒绝非HTTP127.0.0.1 endpoint；02 main-only Bearer与并发401刷新；07 managed坏nonce拒绝。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：HTTP为fake fetch，nonce为fake child；实际随机监听/origin/access到期/远程连接未运行。
- 当前状态：`blocked`；整体要求未满足不标passed。

### P4B-SEC-07 — blocked

- 来源/风险/层/环境/方式：F11/F12 / P0 / security/manual / Windows/Electron / auto。
- 前置：模块标签、错误、消息均含虚拟恶意 HTML。
- 输入：script/img/event handler/RTL/超长文本。
- 操作：渲染导航、通知、Agent panel、错误。
- **完整原预期**：文本安全编码、布局有界且不执行；不得改变 IPC、模块注册或权限。
- 已有历史部分：未做恶意文本UI渲染。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：真实HTML/RTL/长文本编码布局与无脚本执行证据缺失。
- 当前状态：`blocked`；整体要求未满足不标passed。

### P4B-SEC-08 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / desktop/e2e / Windows/Electron / auto。
- 前置：可注入 preload/backend/lazy-load 故障。
- 输入：内部路径、SQL、堆栈、token canary。
- 操作：触发并查看 UI、console、日志。
- **完整原预期**：用户只见稳定安全错误和 request ID；renderer console/日志无秘密或未授权数据。
- 已有历史部分：原PUB-02 corruption安全错误；R1-SHELL-03/04在401刷新失败、503、非法DTO、network异常下安全error不含虚拟canary；R1-OB-07 dialog rejection无raw console输出。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：未实测实际UI/request ID/preload/lazy故障或真实console/log/crash dump。
- 当前状态：`blocked`；整体要求未满足不标passed。

### P4B-SUP-01 — blocked

- 来源/风险/层/环境/方式：D9 BackendSupervisor / P0 / desktop/e2e / Windows/Electron / auto。
- 前置：supervisor 可记录 PID+nonce。
- 输入：自己启动、手工启动、伪造同 PID。
- 操作：请求停止/应用退出。
- **完整原预期**：只停止 PID+nonce 匹配且由本实例启动的子进程；手工/他实例进程保持。
- 已有历史部分：R1-SHELL-07错误managed nonce拒绝并清理候选；08external observed child shutdown不调用stop/forceStop。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：虚拟adapter；真实PID/nonce、外来同PID和进程树隔离未执行。
- 当前状态：`blocked`；整体要求未满足不标passed。

### P4B-SUP-02 — blocked

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：端口分配与 ready 协议冻结。
- 输入：端口冲突、无 ready、坏 nonce、ready 超时。
- 操作：启动后端。
- **完整原预期**：使用随机可用 loopback 端口；超时进入离线/诊断并清理自有子进程，不把 health 当 ready。
- 已有历史部分：R1-SHELL-07坏nonce fail-closed且不进入ready；06成功fake ready。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：端口冲突、ready总超时、随机loopback和真实自有清理未覆盖，不能把health当ready。
- 当前状态：`blocked`；整体要求未满足不标passed。

### P4B-SUP-03 — blocked

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：假后端可崩溃。
- 输入：启动前崩溃、ready 后崩溃、连续崩溃。
- 操作：观察重启策略。
- **完整原预期**：状态转 offline；重启次数/退避有界，不形成重启风暴或重复 run；用户可恢复。
- 已有历史部分：R1-SHELL-06 fake child exit→offline，recover退避1/2/4秒、三次上限，第四次exhausted，shutdown阻止再start。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：注入delay/child，不是Windows真实崩溃；启动前崩溃、健康循环与全部UI状态未覆盖。
- 当前状态：`blocked`；整体要求未满足不标passed。

### P4B-SUP-04 — blocked

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：已有手动后端或两个 app 启动请求。
- 输入：重复启动、开发连接模式。
- 操作：启动/关闭两个客户端。
- **完整原预期**：不产生重复 owned 后端；连接手动后端时不取得停止权；状态可区分。
- 已有历史部分：R1-SHELL-06并发start/recover single-flight不增重复start；08external不启动owned也无停止权。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：未执行双真实客户端/单实例EXE场景。
- 当前状态：`blocked`；整体要求未满足不标passed。

### P4B-SUP-05 — not_run

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / security/manual / Windows/Electron / manual。
- 前置：目标 Windows，后端含子线程/连接。
- 输入：正常退出、强关主窗口、系统注销。
- 操作：检查进程树/端口/文件锁。
- **完整原预期**：自有后端按冻结时限退出，无僵尸/孤儿/占用端口；未拥有进程不受影响。
- 已有历史部分：真实退出、强关和注销均未执行；R1-MAIN-02/03仅虚拟Hostshutdown/窗口destroy。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：manual not_run；无owned资源仅表示没启动，不能推断cleanup通过。
- 当前状态：`not_run`；整体要求未满足不标passed。

### P4B-SUP-06 — blocked

- 来源/风险/层/环境/方式：D9 offline recovery / P0 / desktop/e2e / Windows/Electron / auto。
- 前置：renderer 有未发送虚拟消息。
- 输入：后端离线→恢复、应用重启、重复点击。
- 操作：发送并观察 client_event_id/GET。
- **完整原预期**：未发送内容和同一 ID 保留；恢复后只提交一次；UI 不凭新 ID 制造重复账候选。
- 已有历史部分：原PUB-11不变断言1 passed，原其他10再次通过；新增R1-OB26覆盖持久保留/确认/身份/故障/容量，加R1-MAIN5实际main接线。建议关闭原OUTBOX-001的公开持久化P1。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：真实老化原生提示unverified、恢复后GET/只提交一次与实际UI缺失；整项从failed改blocked，原P0风险不变。
- 当前状态：`blocked`；整体要求未满足不标passed。

### P4B-UI-01 — blocked

- 来源/风险/层/环境/方式：F12 / P1 / contract/unit / contract / auto。
- 前置：compiled registry 与 `/modules` fixture。
- 输入：后端启用/禁用、桌面缺失、版本不兼容、未知模块。
- 操作：计算交集。
- **完整原预期**：只渲染两侧均存在且兼容的模块；未知/禁用不导航、不预加载。
- 已有历史部分：原PUB-05canonical registry/Host交集再次通过，R1-SHELL-10两纯测试contribution正常compile。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：实际导航/preload未运行；没有创建真实第二产品模块。
- 当前状态：`blocked`；整体要求未满足不标passed。

### P4B-UI-02 — failed

- 来源/风险/层/环境/方式：F12 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：两个 lazy route。
- 输入：chunk 加载失败、重试成功、切换模块。
- 操作：导航并恢复。
- **完整原预期**：局部错误边界可重试，Shell/登录/其他模块可用；不循环加载或丢当前会话。
- 已有历史部分：未执行两个lazy routes的chunk故障/局部retry。；R4-R1 factory1、5016ms无alert，Router终态未关联。；R4-R2同Router取消加载安全reject、有效加载成功，无alert，原1失败/3通过，未关闭。
- 本轮新增：P工具前置1passed：真实默认loader两并发+随后3/3safe reject、fixture1。全新A初始化硬限，正文/main均0、四断言not_run；Bnot_run。
- 具体缺口与层级：持续导入故障已验证，但冷main有效请求/活跃Router错误槽/局部DOM隔离未验证；恢复/健康切换/状态保持及Windows chunk/session持久化全部未执行，不关闭LAZY-001。
- 当前状态：`failed`；整体要求未满足不标passed。

### P4B-UI-03 — blocked

- 来源/风险/层/环境/方式：F12 / P1 / contract/unit / contract / auto。
- 前置：冻结 OpenAPI 与生成命令。
- 输入：后端 DTO 字段/枚举/required 改变；生成物陈旧。
- 操作：CI 比较生成差异并编译。
- **完整原预期**：漂移门禁失败并定位；不得靠手写 API 类型掩盖差异或运行时下载 schema。
- 已有历史部分：生成物和OpenAPI保持冻结输入，没有运行生成/类型漂移mutation。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：未取得失败定位或CI drift独立证据。
- 当前状态：`blocked`；整体要求未满足不标passed。

### P4B-UI-04 — blocked

- 来源/风险/层/环境/方式：F12 / P1 / contract/unit / contract / auto。
- 前置：UI contribution 合同冻结。
- 输入：hostUiMajor、route/path/setting/profile/companion 冲突。
- 操作：编译期注册和启动验证。
- **完整原预期**：不兼容或冲突稳定失败；Shell 无 `if moduleId` 业务分支。
- 已有历史部分：R1-SHELL-11四种module/profile/route ID/appearance冲突拒绝，12不兼容major和非canonical输入拒绝；13跨module相同setting key仍接受两模块，首次失败。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：UI-04完整独立结构/strict贡献及启动验证映射尚未完成，新P1停止；不能由路径通过直接passed。
- 当前状态：`blocked`；整体要求未满足不标passed。

### P4B-CMP-01 — blocked

- 来源/风险/层/环境/方式：F13；U02 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：daily/wealth contributions 与假状态流。
- 输入：切换模块及 idle/thinking/tool/confirmation/error/offline。
- 操作：观察窗口、Profile 和状态。
- **完整原预期**：始终只有一个毛毛窗口/Agent 入口；主形态随 contribution，子状态不创建第二 Agent或触发写入。
- 已有历史部分：R1-MAIN-01虚拟BrowserWindow构造仅Maris和毛毛，Host启动不被dialog等待。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：实际单毛毛/Agent入口、contribution主形态和完整子状态流未运行。
- 当前状态：`blocked`；整体要求未满足不标passed。

### P4B-CMP-02 — blocked

- 来源/风险/层/环境/方式：U01/F13 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：新设备设置。
- 输入：首次和第二次关闭主窗口。
- 操作：关闭、从 Tray 恢复、再次关闭。
- **完整原预期**：首次隐藏并只提示一次；第二次不重复提示；Host/毛毛按设置驻留且无数据丢失。
- 已有历史部分：未执行真实close/Tray恢复/提示一次场景。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：虚拟ready-to-show retention不等于首次close提示；真实设备not_run子项保持。
- 当前状态：`blocked`；整体要求未满足不标passed。

### P4B-CMP-03 — blocked

- 来源/风险/层/环境/方式：U01 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：关闭策略可切换。
- 输入：退出/每次询问/隐藏，Tray 打开/隐藏。
- 操作：每种设置执行关闭与取消。
- **完整原预期**：行为精确对应设置；“退出”清理自有后端；询问取消不退出；Tray 状态一致。
- 已有历史部分：未测试三种closePolicy与询问取消/Tray；R1-MAIN before-quit仅退出接线。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：不以mock app.quit或E2E timer当生产关闭策略证明。
- 当前状态：`blocked`；整体要求未满足不标passed。

### P4B-CMP-04 — not_run

- 来源/风险/层/环境/方式：U05 / P1 / security/manual / Windows/Electron / manual。
- 前置：新安装测试 profile。
- 输入：首次运行、显式启用/禁用开机启动。
- 操作：检查 OS 启动项和 UI。
- **完整原预期**：默认关闭且无启动项；只有明确操作才创建；禁用清理本应用项，不改其他应用。
- 已有历史部分：未创建/删除OS启动项；main fixture app.setLoginItemSettings是mock。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：manual not_run；E2E抑制启动项不等于OS合同通过。
- 当前状态：`not_run`；整体要求未满足不标passed。

### P4B-CMP-05 — not_run

- 来源/风险/层/环境/方式：F13 / P1 / desktop/e2e / external/manual / manual。
- 前置：多显示器/缩放/全屏测试设备。
- 输入：拖动、置顶、重启、拔屏、分辨率变化、全屏、隐私、键盘。
- 操作：逐项操作并重启。
- **完整原预期**：位置用临时文件原子替换并恢复/夹取；全屏按规则隐藏；隐私不显示金额；键盘入口可达。
- 已有历史部分：未修改显示器/缩放/全屏/窗口坐标或测试隐私键盘。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：实际位置夹取/重启/多屏/全屏/键盘/隐私UI与全部人工设备条件未执行，整项manual not_run保持。
- 当前状态：`not_run`；整体要求未满足不标passed。

### P4B-CMP-06 — not_run

- 来源/风险/层/环境/方式：U02；主题要求 / P2 / desktop/e2e / external/manual / manual。
- 前置：支持/不支持透明窗口设备。
- 输入：透明失败、普通迷你窗降级；light/dark/system/high-contrast/reduced-motion；中外行情色。
- 操作：切换设备条件和主题。
- **完整原预期**：可安全降级且合同不变；文本对比/焦点可辨；reduced motion 生效；收入/支出色不复用涨跌色。
- 已有历史部分：未启动透明/降级窗口或切换系统主题。
- 本轮新增：not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。
- 具体缺口与层级：manual not_run；真实对比度/焦点/reduced motion/颜色语义未测试。
- 当前状态：`not_run`；整体要求未满足不标passed。

## 资源、格式核对和交接

P无main/Router实例/DOM资源创建，只导入真实模块并调用默认loader；P CLI3920自然exit0、登记worker19592已结束。A在正文前没有创建root/bridge订阅/Router观察/DOM/global/console spy，所以没有伪造unmount或cleanup事件；CLI15796硬限定向结束、自有worker16464结束。worker自己的exit事件缺失，具体exit code/机制unknown，父退出码不复制给worker。控制器身份来自创建句柄和即时journal parent，未用祖先猜测或总进程数阈值。

事后Get-Process确认这四个已登记PID不存在；系统Win32_Process枚举抛CimException，enumerationVerified=false，空列表不能等同全树零残留。完整历史后代未核实，范围限制明确；不全局杀Node/Electron/Maris/Python。没有建立外部C12-R4-R3 profile/session/db/窗口/监听，Windows设备行为不能从测试进程退出推导。

新r4-r3/cache经绝对专属边界/no-reparse核对清理1个缓存文件，目录已不存在；所有首次源码、worker/controller/resolver journal、双流、JSON和静态首错保留。旧包、旧缓存/资料、真实AppData不读写。没有Docker/PG/OpenClaw/微信V002/DeepSeek/provider或用户点击要求。

最终r4-r3-delivery.py实际复核通过：544输入中540保持，tester、旧主报告/人工清单追加、矩阵B备注四项授权变化，0越界变化/缺失、staged0；受验源389/out140/resources67、固定包/fuses、7包元数据及15冻结源码保持。143项旧独立文件、69项D15诊断保持。矩阵120唯一ID/12列/前11列/全部原状态/B外字节、旧文档原字节prefix保持；旧主报告与人工清单各新增980bytes。37项旧R2交付里除四个本轮允许更新的共享文档外33保持，不声称旧37整体仍同摘要。

只读Git staged/diff-check exit0与新增全文件行尾扫描通过分列，Git环境warning不当成格式失败：历史R2 controller行158尾随空格保持不修改；本轮新增源/报告及追加段独立扫描，不拿tracked-only检查代替新文件格式检查。最终交付52项，全部摘要逐项复核；准确计数和最终摘要见end-audit.json、delivery-verification.json、delivery.sha256。摘要清单不包含清单自身，也不向本报告写入自引用摘要。

交**blocked / finished**并停止，供总控review。P持续导入验证已完成；A正文前硬限和初始化原因、全部业务断言及Windows尚未解决。后续由总控依据首次阶段裁定，本角色不使用额外worker盲重跑、不改产品/依赖或Git、不建下一Prompt、不进入P4-C/D、不宣布总控接受。
