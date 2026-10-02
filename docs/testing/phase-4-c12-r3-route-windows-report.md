# P4-C12-R3 路径独立复验与剩余Windows验收报告

- 角色：既有独立测试智能体，C12-R3唯一负责人；控制版本2026-10-02T18:25:00+08:00。
- 任务卡：`docs/coordination/prompts/p4-c12-r3-route-windows-tester.md`，2026-10-02，Asia/Shanghai。
- **交付 blocked / finished**：PATH-001原断言及相邻路径通过，建议关闭；未覆盖lazy故障发现新P1，按任务卡停止。OUTBOX-001/设置键REGISTRY-001保持关闭，不重复处理。P4-B不complete，最终接受属于总控。

## 实际运行与统计

| 分组 | 结果 | evidence/r3下首次JSON/log |
| --- | --- | --- |
| 原R2-UI-04-PATH不变断言，唯一一次 | 1 passed | original-path |
| 新路径双顺序/同模块/末尾/route ID/不变性/恢复 | 9 passed | path-independent |
| 未覆盖canonical ASCII末尾换行拒绝 | 1 passed | ui04-independent |
| 新设置3、ZIP6、staging7 | 16 passed | storage-build-independent |
| 真实renderer lazy失败隔离（虚拟端口、jsdom） | 1 failed | remaining-independent |
| **独立合计** | **28 unique executed：27 passed、1 failed** | node-index.json；各目标一次，不重复累加 |
| 开发registry兼容，单列、唯一一次 | **52 passed** | executor-compat |
| 原24项P4-B整项 | **0 passed、1 failed、19 blocked、4 not_run** | UI-02 blocked→failed；UI-04 failed→blocked |
| 产品/辅助Electron实际启动 | **0/8、0/4** | 新P1停止在Windows前，不是权限或设备故障 |

没有重跑旧outbox42、setting成功节点、R2成功15、完整开发124、Python/P0～P3/Host、Docker或任何外部服务。六组运行一次，五组退出0，lazy组退出1；未重跑失败、未放宽断言、无skip/xfail。原路径文件完全不变。

## 原PATH-001复验与关闭建议

原`r2-remaining.test.ts`只通过新R3配置/依赖执行精确R2-UI-04-PATH，结果从历史accepted:2变为desktop_registry_conflict，原断言不变。旧R2日志/JSON保持失败历史原样。新增9节点：跨module完全相同字符串两顺序；同module不同route ID同path两顺序；末module末route冲突；相同route ID不同path仍拒绝两顺序；不同路径合法且精确保留；冻结输入保持、无部分返回、失败后合法编译成功。不会把大小写/尾斜杠/模式归一化引入合同。

**建议总控关闭 P4-C12-R2-REGISTRY-PATH-001 的完全相同路径冲突问题。** 原设置键和outbox独立关闭不重开；路径通过不直接使UI-04/P4-B通过。

## 新P1：P4-C12-R3-LAZY-001

- 原案例：P4B-UI-02，风险P1；完整预期是局部错误边界可重试，Shell/登录/其他模块可用，不循环加载或丢当前会话。
- 测试节点：`r3-remaining.test.tsx` / R3-UI-02-LAZY。真正导入产品renderer/main.tsx，React、React DOM、React Router、Shell与RouteErrorBoundary均为实际代码；环境为jsdom，窄window.maris bridge返回虚拟在线已认证snapshot和合法daily_finance/日常管钱canonical Profile摘要；只对lazy页面的import端口注入VIRTUAL_CHUNK_UNAVAILABLE。没有替换路由器或错误边界。
- 前置：新内存DOM、没有网络/真实Host/DB，模块/状态均虚拟；生产lazy route已可由实际导航进入。
- 操作：运行实际renderer启动、等待effects与lazy拒绝进入实际错误边界，再读取Shell/模块导航/统一Agent面板DOM。
- 预期：安全错误只影响模块内容；Shell、模块导航、统一Agent入口仍可用。
- **实际**：安全错误页确实出现，但Shell、导航、Agent面板全部不存在。首次断言在Shell必须保留处失败，退出1。该核心局部隔离子条件已经失败，不需继续点击或实机重跑来抵消。
- 脱敏证据：`evidence/r3/remaining-independent/run.log`与result.json永久保留，最小复现为r3-remaining.test.tsx。没有声称实机丢失session/token/账目或真实其他模块执行失败，未运行成功重试/第二lazy route/Windows现场。
- 只读原因定位：renderer/main.tsx:24将errorElement放在包含Shell的父route，子lazy route没有局部errorElement；错误冒泡后父Shell被错误页替换。Shell.tsx的重试使用全页reload，只读观察未点击，不把它另计为实测缺陷或恢复结果。
- 严重级别 **P1**：单模块chunk故障使整个Shell入口不可用，违反明确冻结的隔离验收；不是harness/导入配置失败。按任务卡停止扩大测试，没有产品修复。

```json
{"caseId":"R3-UI-02-LAZY","chunkFailureShown":true,"shellPresent":false,"navigationPresent":false,"agentPanelPresent":false,"data":"virtual_only","evidenceLayer":"real_renderer_in_jsdom_with_virtual_bridge_and_failed_chunk"}
```

复现命令只作为交接材料，不表示本角色获准再次运行失败节点：

```powershell
$env:C12_R3_PHASE='remaining-independent'
& 'C:/MarisRouteR4/R4-20261002-164600/tools/node/node.exe' 'C:/MarisRouteR4/R4-20261002-164600/workspace/node_modules/vitest/vitest.mjs' run --config tests/independent/desktop/r3-vitest.config.mjs
```

## 新公开行为与适用层级

设置3：缺失/坏JSON/未知字段安全defaults，有效主题/隐私/虚拟DIP bounds经过新store恢复且无.tmp残留；额外token canary严格拒绝且原有效文件字节不变。均写测试专属tmp普通文件，不改真实AppData/用户settings。未注入全部FS故障，也不等于OS启动项/主题/窗口实际恢复通过。

ZIP6：无环境变量兼容、空值/空白/相对/边缘空白/NUL拒绝，使用小型虚拟archive和注入公开contract验证合法、文件不存在、错误长度、同长度错误SHA。只执行校验器，不下载/安装/Forge/package，不读真实ZIP缓存或伪称官方zip重新验收。

staging7：仅在新fixture source/desktop根运行真实stage函数，显式传两个根，绝不使用默认产品root。验证allowlist精确路径/hash，排除cache/egg-info/tests/pyc，路径绝对/越界/反斜杠拒绝；六个replacement阶段故障，提交前四阶段旧payload/manifest完整保留，提交后两阶段稳定committed错误且新完整pair保留；锁/tmp无残留。未运行symlink/junction/reparse注入与全部异常组合，不把7项代替完整package/污染源动态门禁。

## UI-04独立映射（原标准不改）

| 冻结子条件 | 独立证据及输入关系 | 层级/状态 |
| --- | --- | --- |
| hostUiMajor；module ASCII、SemVer、canonical Profile | 原R1-SHELL-12在R2 adjacent-original通过，相关schema输入不变，未重复；本轮R3-UI04-ASCII-01末尾换行拒绝 | 已有+新增contract行为；不将开发52当独立 |
| module/Profile/route ID/appearance全局冲突 | R2 adjacent-original中的R1-SHELL-11四类通过，身份token未变；本轮R3-PATH-04路由ID仍有效 | 已有独立证据+受影响路由ID新增 |
| setting全局冲突 | R2 original-registry及registry-independent15成功中的对应边界；setting token未变，缺陷已关闭，不重复 | 历史独立输入不变 |
| 完全相同path冲突、不部分返回、输入不变、失败恢复 | 本轮原路径1、新路径9通过，包含末尾与冻结输入 | 新独立contract行为通过，建议PATH关闭 |
| Host major/Profile/API prefixes/schema精确交集；未知/禁用排除 | 原C12-PUB-05及R1 remaining-original通过，intersectModules输入不变，未重复 | 历史fake Host fixture行为，实际Windows导航未验 |
| Shell/main/preload无具体module业务分支 | 只读Shell、renderer注册及限定rg定位未发现具体module比较分支；开发结构映射仅用于定位 | 结构观察，未完成本轮完整独立结构/严格贡献子条件复核，不冒称行为通过 |
| strict对象及全部未覆盖规范边界、启动验证 | 首次新P1后停止扩大；开发映射不是独立证据 | 未完成，UI-04保守blocked，不能仅以路径通过整项passed |

路径大小写、尾斜杠、动态参数、模式重叠、保留settings path等语义未另冻结；R4说明已指出这些风险。本轮没有添加归一化断言或将它们另报已实测缺陷，后续语义需总控裁定。

## 起点、首次审计问题及不可变性

新起点356/356 matched，0缺失/差异，staged0；manifest SHA-256 `4b6dcb45d27cb5a277636278564dcf8489e244929db9fa46cf7c4ca2bba32b0f`。新只读环境 C:\MarisRouteR4\R4-20261002-164600，Node24.21.0/Vitest5.0.2，已装普通依赖；不安装/构建/下载。

首次新增审计将历史repository source353与当前派发后仓库直接比较，遇到五份总控协调更新（README/control/overview/brainstorm/project-coordination）348匹配/5差异而assert退出1。此前356新起点、140out、67resources、EXE/asar/lock/fuses已匹配。保留initial-audit-failure.json，唯一一次目标前无副作用映射修正：这五份在权威新起点逐字节匹配，历史清单不改；实际包构建输入workspace-source352/352匹配。它不是产品漂移或业务失败，没有消耗EXE/辅助预算。工具失败保留，不用历史清单或旧包根覆盖本轮结论。

| 文件（只读workspace下） | 起终固定SHA-256 |
| --- | --- |
| Maris.exe | d5868736cbdf63f717f0ea853141b980d06cefc10a3c05196e8856cbe3a4de2b |
| resources/app.asar | 9a4da50b2c5583e6f2337bdff43e399cd454c360fa6169b1667a1e4506c337d4 |
| pnpm-lock.yaml | 5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a |

终点审计已通过：**356 entries：352 unchanged、4 authorized changed、0非授权变更、0缺失、staged0**；旧独立材料54项精确不变。证据见evidence/r3/end-audit.json和delivery-verification.json，由新增r3-delivery.py verify核对。固定356集仅tester、matrix B、旧主报告/人工清单四项变化；旧public/r1/r2测试、R1/R2报告和全部旧evidence/失败日志不可变；产品及当前control不变。追加prefix与B外字节段、120唯一ID/12列/原前11列保持；A64 passed、C20/D12 not_run不变。EXE/asar/lock与fuses起终保持，out140/resources67/构建输入352保持。

## 原24项逐项完整映射

已有部分明确为只读R2报告内的历史证据（本轮未重复，固定文件摘要核对）；每项仍列完整原预期、实际新增和缺口。单元/结构不替代设备条件。

### P4B-SEC-01 — blocked

- 来源/风险/层级/环境/方式：F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：固定 Electron 构建。
- 输入：BrowserWindow 配置与运行时 renderer。
- 操作：静态检查并在 renderer 探测。
- **完整原预期**：sandbox/contextIsolation 开启、nodeIntegration 关闭；无 `require/process/fs/child_process` 或任意 preload 对象。
- 已有部分（R2记载历史，未重复）：原 PUB-03 在新依赖下再次通过；R1-MAIN-01 实际导入main但窗口是虚拟adapter。
- 本轮新增：未新增执行；新P1停止扩大。
- 具体缺口与证据层级：生产 preferences逻辑有证据；实际EXE renderer Node isolation未执行。
- 当前状态：`blocked`；未完成全部子条件不标passed。

### P4B-SEC-02 — blocked

- 来源/风险/层级/环境/方式：F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：CSP/导航 allowlist 冻结。
- 输入：inline script、data/javascript URL、未知 origin、新窗口、外链。
- 操作：从不可信内容触发导航/打开。
- **完整原预期**：CSP 阻止执行；未知导航/窗口拒绝；获准外链只由 main 安全打开，不加载进应用权限域。
- 已有部分（R2记载历史，未重复）：原 PUB-03 CSP字符串再次通过；main安全默认/导航接线只读。
- 本轮新增：未新增执行；新P1停止扩大。
- 具体缺口与证据层级：未在真实页面触发 inline/data/javascript、导航/new-window和外链。
- 当前状态：`blocked`；未完成全部子条件不标passed。

### P4B-SEC-03 — blocked

- 来源/风险/层级/环境/方式：F11 / P0 / contract/unit / contract / auto。
- 前置：preload 类型合同可导入。
- 输入：枚举 contextBridge 暴露对象。
- 操作：与 allowlist 对比并尝试直接 ipcRenderer/send/invoke。
- **完整原预期**：只暴露窄 typed 方法；无通用 channel、Node require、密钥或进程控制。
- 已有部分（R2记载历史，未重复）：R1-SHELL-09实际导入main preload，capture contextBridge，枚举六组窄API/冻结对象，尝试读取通用invoke/send/ipcRenderer/require/process等均undefined，调用typed方法验证固定channel。companion preload只读为getState/openMain。
- 本轮新增：未新增执行；新P1停止扩大。
- 具体缺口与证据层级：main preload契约部分通过；未执行companion暴露对象与整个renderer域，保守保持blocked。
- 当前状态：`blocked`；未完成全部子条件不标passed。

### P4B-SEC-04 — blocked

- 来源/风险/层级/环境/方式：F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：IPC handlers 已注册。
- 输入：伪造 sender、错 origin、额外/错型参数、未知 channel、重复调用。
- 操作：逐项 invoke/send。
- **完整原预期**：sender 与参数双校验；稳定拒绝；不得启动进程、改设置、打开窗口或泄露异常。
- 已有部分（R2记载历史，未重复）：原 PUB-04 sender/frame/origin/严格参数拒绝再次通过；R1 main导入注册真实handlers。
- 本轮新增：未新增执行；新P1停止扩大。
- 具体缺口与证据层级：未对注册handler执行未知channel/重复/全部无副作用断言或真实Electroninvoke。
- 当前状态：`blocked`；未完成全部子条件不标passed。

### P4B-SEC-05 — blocked

- 来源/风险/层级/环境/方式：F07/F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：假 token 与假 API key。
- 输入：localStorage/sessionStorage/IndexedDB/renderer 内存转储、main safeStorage。
- 操作：登录/刷新/重启并检查各层。
- **完整原预期**：refresh/device token 与 API key 只在 main/OS 保护边界；renderer 无持久原文；日志与 crash dump 无值。
- 已有部分（R2记载历史，未重复）：原PUB-01/02虚拟加密失败闭合/损坏/密文通过；R1-SHELL-05虚拟owner bootstrap/refresh/revoke通过，R1-OB容量/密文逻辑保持。
- 本轮新增：未新增执行；新P1停止扩大。
- 具体缺口与证据层级：非Windows safeStorage；未检查真实renderer storage/内存、secret/crash dump或OS DPAPI。
- 当前状态：`blocked`；未完成全部子条件不标passed。

### P4B-SEC-06 — blocked

- 来源/风险/层级/环境/方式：F11 / P0 / API/integration / Windows/Electron / auto。
- 前置：后端绑定随机 loopback port。
- 输入：只知道端口、错 nonce、错 origin、过期 access、远程地址。
- 操作：绕过 main 直连 Host。
- **完整原预期**：端口不是认证；nonce/origin/token 均校验；只绑定 loopback，远程连接拒绝。
- 已有部分（R2记载历史，未重复）：R1-SHELL-01拒绝非HTTP127.0.0.1 endpoint；02 main-only Bearer与并发401刷新；07 managed坏nonce拒绝。
- 本轮新增：未新增执行；新P1停止扩大。
- 具体缺口与证据层级：HTTP为fake fetch，nonce为fake child；实际随机监听/origin/access到期/远程连接未运行。
- 当前状态：`blocked`；未完成全部子条件不标passed。

### P4B-SEC-07 — blocked

- 来源/风险/层级/环境/方式：F11/F12 / P0 / security/manual / Windows/Electron / auto。
- 前置：模块标签、错误、消息均含虚拟恶意 HTML。
- 输入：script/img/event handler/RTL/超长文本。
- 操作：渲染导航、通知、Agent panel、错误。
- **完整原预期**：文本安全编码、布局有界且不执行；不得改变 IPC、模块注册或权限。
- 已有部分（R2记载历史，未重复）：未做恶意文本UI渲染。
- 本轮新增：未新增执行；新P1停止扩大。
- 具体缺口与证据层级：真实HTML/RTL/长文本编码布局与无脚本执行证据缺失。
- 当前状态：`blocked`；未完成全部子条件不标passed。

### P4B-SEC-08 — blocked

- 来源/风险/层级/环境/方式：F11 / P0 / desktop/e2e / Windows/Electron / auto。
- 前置：可注入 preload/backend/lazy-load 故障。
- 输入：内部路径、SQL、堆栈、token canary。
- 操作：触发并查看 UI、console、日志。
- **完整原预期**：用户只见稳定安全错误和 request ID；renderer console/日志无秘密或未授权数据。
- 已有部分（R2记载历史，未重复）：原PUB-02 corruption安全错误；R1-SHELL-03/04在401刷新失败、503、非法DTO、network异常下安全error不含虚拟canary；R1-OB-07 dialog rejection无raw console输出。
- 本轮新增：未新增执行；新P1停止扩大。
- 具体缺口与证据层级：未实测实际UI/request ID/preload/lazy故障或真实console/log/crash dump。
- 当前状态：`blocked`；未完成全部子条件不标passed。

### P4B-SUP-01 — blocked

- 来源/风险/层级/环境/方式：D9 BackendSupervisor / P0 / desktop/e2e / Windows/Electron / auto。
- 前置：supervisor 可记录 PID+nonce。
- 输入：自己启动、手工启动、伪造同 PID。
- 操作：请求停止/应用退出。
- **完整原预期**：只停止 PID+nonce 匹配且由本实例启动的子进程；手工/他实例进程保持。
- 已有部分（R2记载历史，未重复）：R1-SHELL-07错误managed nonce拒绝并清理候选；08external observed child shutdown不调用stop/forceStop。
- 本轮新增：未新增执行；新P1停止扩大。
- 具体缺口与证据层级：虚拟adapter；真实PID/nonce、外来同PID和进程树隔离未执行。
- 当前状态：`blocked`；未完成全部子条件不标passed。

### P4B-SUP-02 — blocked

- 来源/风险/层级/环境/方式：D9 lifecycle / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：端口分配与 ready 协议冻结。
- 输入：端口冲突、无 ready、坏 nonce、ready 超时。
- 操作：启动后端。
- **完整原预期**：使用随机可用 loopback 端口；超时进入离线/诊断并清理自有子进程，不把 health 当 ready。
- 已有部分（R2记载历史，未重复）：R1-SHELL-07坏nonce fail-closed且不进入ready；06成功fake ready。
- 本轮新增：未新增执行；新P1停止扩大。
- 具体缺口与证据层级：端口冲突、ready总超时、随机loopback和真实自有清理未覆盖，不能把health当ready。
- 当前状态：`blocked`；未完成全部子条件不标passed。

### P4B-SUP-03 — blocked

- 来源/风险/层级/环境/方式：D9 lifecycle / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：假后端可崩溃。
- 输入：启动前崩溃、ready 后崩溃、连续崩溃。
- 操作：观察重启策略。
- **完整原预期**：状态转 offline；重启次数/退避有界，不形成重启风暴或重复 run；用户可恢复。
- 已有部分（R2记载历史，未重复）：R1-SHELL-06 fake child exit→offline，recover退避1/2/4秒、三次上限，第四次exhausted，shutdown阻止再start。
- 本轮新增：未新增执行；新P1停止扩大。
- 具体缺口与证据层级：注入delay/child，不是Windows真实崩溃；启动前崩溃、健康循环与全部UI状态未覆盖。
- 当前状态：`blocked`；未完成全部子条件不标passed。

### P4B-SUP-04 — blocked

- 来源/风险/层级/环境/方式：D9 lifecycle / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：已有手动后端或两个 app 启动请求。
- 输入：重复启动、开发连接模式。
- 操作：启动/关闭两个客户端。
- **完整原预期**：不产生重复 owned 后端；连接手动后端时不取得停止权；状态可区分。
- 已有部分（R2记载历史，未重复）：R1-SHELL-06并发start/recover single-flight不增重复start；08external不启动owned也无停止权。
- 本轮新增：未新增执行；新P1停止扩大。
- 具体缺口与证据层级：未执行双真实客户端/单实例EXE场景。
- 当前状态：`blocked`；未完成全部子条件不标passed。

### P4B-SUP-05 — not_run

- 来源/风险/层级/环境/方式：D9 lifecycle / P1 / security/manual / Windows/Electron / manual。
- 前置：目标 Windows，后端含子线程/连接。
- 输入：正常退出、强关主窗口、系统注销。
- 操作：检查进程树/端口/文件锁。
- **完整原预期**：自有后端按冻结时限退出，无僵尸/孤儿/占用端口；未拥有进程不受影响。
- 已有部分（R2记载历史，未重复）：真实退出、强关和注销均未执行；R1-MAIN-02/03仅虚拟Hostshutdown/窗口destroy。
- 本轮新增：未新增执行；新P1停止扩大。
- 具体缺口与证据层级：manual not_run；无owned资源仅表示没启动，不能推断cleanup通过。
- 当前状态：`not_run`；未完成全部子条件不标passed。

### P4B-SUP-06 — blocked

- 来源/风险/层级/环境/方式：D9 offline recovery / P0 / desktop/e2e / Windows/Electron / auto。
- 前置：renderer 有未发送虚拟消息。
- 输入：后端离线→恢复、应用重启、重复点击。
- 操作：发送并观察 client_event_id/GET。
- **完整原预期**：未发送内容和同一 ID 保留；恢复后只提交一次；UI 不凭新 ID 制造重复账候选。
- 已有部分（R2记载历史，未重复）：原PUB-11不变断言1 passed，原其他10再次通过；新增R1-OB26覆盖持久保留/确认/身份/故障/容量，加R1-MAIN5实际main接线。建议关闭原OUTBOX-001的公开持久化P1。
- 本轮新增：未新增执行；新P1停止扩大。
- 具体缺口与证据层级：真实老化原生提示unverified、恢复后GET/只提交一次与实际UI缺失；整项从failed改blocked，原P0风险不变。
- 当前状态：`blocked`；未完成全部子条件不标passed。

### P4B-UI-01 — blocked

- 来源/风险/层级/环境/方式：F12 / P1 / contract/unit / contract / auto。
- 前置：compiled registry 与 `/modules` fixture。
- 输入：后端启用/禁用、桌面缺失、版本不兼容、未知模块。
- 操作：计算交集。
- **完整原预期**：只渲染两侧均存在且兼容的模块；未知/禁用不导航、不预加载。
- 已有部分（R2记载历史，未重复）：原PUB-05canonical registry/Host交集再次通过，R1-SHELL-10两纯测试contribution正常compile。
- 本轮新增：未新增执行；新P1停止扩大。
- 具体缺口与证据层级：实际导航/preload未运行；没有创建真实第二产品模块。
- 当前状态：`blocked`；未完成全部子条件不标passed。

### P4B-UI-02 — failed

- 来源/风险/层级/环境/方式：F12 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：两个 lazy route。
- 输入：chunk 加载失败、重试成功、切换模块。
- 操作：导航并恢复。
- **完整原预期**：局部错误边界可重试，Shell/登录/其他模块可用；不循环加载或丢当前会话。
- 已有部分（R2记载历史，未重复）：未执行两个lazy routes的chunk故障/局部retry。
- 本轮新增：R3-UI-02-LAZY首次失败：真实renderer/jsdom，安全错误页出现但Shell/nav/Agent入口全部消失。
- 具体缺口与证据层级：核心局部隔离已失败；重试成功/其他lazy route/session保持/无循环与Windows未执行。
- 当前状态：`failed`；未完成全部子条件不标passed。

### P4B-UI-03 — blocked

- 来源/风险/层级/环境/方式：F12 / P1 / contract/unit / contract / auto。
- 前置：冻结 OpenAPI 与生成命令。
- 输入：后端 DTO 字段/枚举/required 改变；生成物陈旧。
- 操作：CI 比较生成差异并编译。
- **完整原预期**：漂移门禁失败并定位；不得靠手写 API 类型掩盖差异或运行时下载 schema。
- 已有部分（R2记载历史，未重复）：生成物和OpenAPI保持冻结输入，没有运行生成/类型漂移mutation。
- 本轮新增：未新增执行；新P1停止扩大。
- 具体缺口与证据层级：未取得失败定位或CI drift独立证据。
- 当前状态：`blocked`；未完成全部子条件不标passed。

### P4B-UI-04 — blocked

- 来源/风险/层级/环境/方式：F12 / P1 / contract/unit / contract / auto。
- 前置：UI contribution 合同冻结。
- 输入：hostUiMajor、route/path/setting/profile/companion 冲突。
- 操作：编译期注册和启动验证。
- **完整原预期**：不兼容或冲突稳定失败；Shell 无 `if moduleId` 业务分支。
- 已有部分（R2记载历史，未重复）：R1-SHELL-11四种module/profile/route ID/appearance冲突拒绝，12不兼容major和非canonical输入拒绝；13跨module相同setting key仍接受两模块，首次失败。
- 本轮新增：原路径1+新路径9+ASCII1通过；旧setting及身份相邻不重跑；建议关闭PATH-001。
- 具体缺口与证据层级：UI-04完整独立结构/strict贡献及启动验证映射尚未完成，新P1停止；不能由路径通过直接passed。
- 当前状态：`blocked`；未完成全部子条件不标passed。

### P4B-CMP-01 — blocked

- 来源/风险/层级/环境/方式：F13；U02 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：daily/wealth contributions 与假状态流。
- 输入：切换模块及 idle/thinking/tool/confirmation/error/offline。
- 操作：观察窗口、Profile 和状态。
- **完整原预期**：始终只有一个毛毛窗口/Agent 入口；主形态随 contribution，子状态不创建第二 Agent或触发写入。
- 已有部分（R2记载历史，未重复）：R1-MAIN-01虚拟BrowserWindow构造仅Maris和毛毛，Host启动不被dialog等待。
- 本轮新增：未新增执行；新P1停止扩大。
- 具体缺口与证据层级：实际单毛毛/Agent入口、contribution主形态和完整子状态流未运行。
- 当前状态：`blocked`；未完成全部子条件不标passed。

### P4B-CMP-02 — blocked

- 来源/风险/层级/环境/方式：U01/F13 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：新设备设置。
- 输入：首次和第二次关闭主窗口。
- 操作：关闭、从 Tray 恢复、再次关闭。
- **完整原预期**：首次隐藏并只提示一次；第二次不重复提示；Host/毛毛按设置驻留且无数据丢失。
- 已有部分（R2记载历史，未重复）：未执行真实close/Tray恢复/提示一次场景。
- 本轮新增：未新增执行；新P1停止扩大。
- 具体缺口与证据层级：虚拟ready-to-show retention不等于首次close提示；真实设备not_run子项保持。
- 当前状态：`blocked`；未完成全部子条件不标passed。

### P4B-CMP-03 — blocked

- 来源/风险/层级/环境/方式：U01 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：关闭策略可切换。
- 输入：退出/每次询问/隐藏，Tray 打开/隐藏。
- 操作：每种设置执行关闭与取消。
- **完整原预期**：行为精确对应设置；“退出”清理自有后端；询问取消不退出；Tray 状态一致。
- 已有部分（R2记载历史，未重复）：未测试三种closePolicy与询问取消/Tray；R1-MAIN before-quit仅退出接线。
- 本轮新增：未新增执行；新P1停止扩大。
- 具体缺口与证据层级：不以mock app.quit或E2E timer当生产关闭策略证明。
- 当前状态：`blocked`；未完成全部子条件不标passed。

### P4B-CMP-04 — not_run

- 来源/风险/层级/环境/方式：U05 / P1 / security/manual / Windows/Electron / manual。
- 前置：新安装测试 profile。
- 输入：首次运行、显式启用/禁用开机启动。
- 操作：检查 OS 启动项和 UI。
- **完整原预期**：默认关闭且无启动项；只有明确操作才创建；禁用清理本应用项，不改其他应用。
- 已有部分（R2记载历史，未重复）：未创建/删除OS启动项；main fixture app.setLoginItemSettings是mock。
- 本轮新增：未新增执行；新P1停止扩大。
- 具体缺口与证据层级：manual not_run；E2E抑制启动项不等于OS合同通过。
- 当前状态：`not_run`；未完成全部子条件不标passed。

### P4B-CMP-05 — not_run

- 来源/风险/层级/环境/方式：F13 / P1 / desktop/e2e / external/manual / manual。
- 前置：多显示器/缩放/全屏测试设备。
- 输入：拖动、置顶、重启、拔屏、分辨率变化、全屏、隐私、键盘。
- 操作：逐项操作并重启。
- **完整原预期**：位置用临时文件原子替换并恢复/夹取；全屏按规则隐藏；隐私不显示金额；键盘入口可达。
- 已有部分（R2记载历史，未重复）：未修改显示器/缩放/全屏/窗口坐标或测试隐私键盘。
- 本轮新增：R3-SET-01/02/03本地设置defaults/有效持久化/非法字段拒绝通过；只有虚拟bounds字段。
- 具体缺口与证据层级：实际位置夹取/重启/多屏/全屏/键盘/隐私UI与全部人工设备条件未执行，整项manual not_run保持。
- 当前状态：`not_run`；未完成全部子条件不标passed。

### P4B-CMP-06 — not_run

- 来源/风险/层级/环境/方式：U02；主题要求 / P2 / desktop/e2e / external/manual / manual。
- 前置：支持/不支持透明窗口设备。
- 输入：透明失败、普通迷你窗降级；light/dark/system/high-contrast/reduced-motion；中外行情色。
- 操作：切换设备条件和主题。
- **完整原预期**：可安全降级且合同不变；文本对比/焦点可辨；reduced motion 生效；收入/支出色不复用涨跌色。
- 已有部分（R2记载历史，未重复）：未启动透明/降级窗口或切换系统主题。
- 本轮新增：未新增执行；新P1停止扩大。
- 具体缺口与证据层级：manual not_run；真实对比度/焦点/reduced motion/颜色语义未测试。
- 当前状态：`not_run`；未完成全部子条件不标passed。

## 停止、资源、人工缺口和交接

lazy组18:52:03开始，首次失败后立即停止扩展。全部Vitest已退出，无活动session；产品0/8、辅助Electron0/4，未创建C:\MarisC12\C12-R3-*，没有owned实际窗口/监听/进程需要终止。零资源来自未启动，不是SUP-05或Tray关闭成功证据。没有CDP/UIA、safeStorage fixture或原生dialog，真实老化提示unverified；不请求用户现在点击。

18:53里程碑之后到21:52报告落盘存在连续心跳空档，不能将其描述为持续可观测运行。业务目标此前已经因P1安全停止；恢复可控后立即补记限制并只执行收口/审计，没有重新运行测试、增加启动或消耗外部预算。日志记录最后脱敏错误、已用方法、原因定位和需总控裁定的问题。

尚未执行：实际安全CSP/导航/秘密/恶意文本布局、生成物漂移、staging链接/全部错误、设置写盘失败、真实managed/认证/recover/GET一次提交/单毛毛/单实例/closePolicy/Tray。普通退出与注销、启动项、多屏/DPI/拔屏/全屏/透明降级/OS主题人工条件not_run保持；实际UI恢复不由jsdom单位行为替代。保留原人工清单仅追加，未删降原预期。

只用虚拟模块/账目身份字段/canary/文件，不访问真实provider/秘密/旧AppData/profile/session/db。没有Docker/PG/OpenClaw/微信/DeepSeek、网络、系统设置、产品/执行方/依赖/冻结/控制文件/其他角色或Git写操作。自身tmp/cache清理前重读control、验证绝对专属路径无reparse；所有首次log/JSON、审计保留。旧环境与evidence不清理。

定向git diff --check退出0；仅四份已修改文档的LF→CRLF提示，原始warning保留evidence/r3/diff-check.log，没有修改Git配置。首次审计assert与首次lazy业务失败分别保留、不同分类；没有业务目标重试或失败覆盖。

新增：本报告；r3-audit.py、r3-delivery.py、r3-vitest.config.mjs、r3-compat-vitest.config.mjs、r3-path.test.ts、r3-ui04.test.ts、r3-storage-build.test.ts、r3-remaining.test.tsx及evidence/r3。没有交付/运行Windows runner/helper，因为新P1停止前未进入该阶段。

交接总控：建议关闭原PATH-001，并接收新P1 P4-C12-R3-LAZY-001最小复现、预期/实际、层级限制与首次证据；裁定后续范围。此角色停在 **blocked / finished**，不派发角色/返修/后续任务、不进入P4-C，不宣布P4-B complete。
