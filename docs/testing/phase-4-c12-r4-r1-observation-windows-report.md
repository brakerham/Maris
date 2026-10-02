# P4-C12-R4-R1 可观察故障复验与Windows验收报告

- 角色：既有独立测试智能体、唯一负责人；control 2026-10-02T23:46:00+08:00；任务卡p4-c12-r4-r1-observation-tester.md。
- 复验于2026-10-02 23:55 Asia/Shanghai；具体执行时刻以首次JSON/log为准。
- **交付 blocked / finished**：本轮属于任务卡结果分类2，mock真实命中，但5秒内未出现预期alert。原四条业务要求不降低，旧LAZY-001不建议关闭；未确定实际错误处理终态及原因，不新增已定级产品P0/P1。后续恢复/兼容/Windows停止，最终裁定属总控。

## 新观察节点与事实

新增R4-R1-UI-02-OBSERVED-FAILURE只运行一次，**0 passed、1 failed，exit1**。它是新可观察节点，不把旧R4首次失败改成passed，也没有重跑旧r3代码。只有原DailyFinancePage mock factory增加vi.hoisted命中/时间回执；仍调用真实生产main启动，真实DesktopApp/React Router/Shell/compileRegistry与Host交集，不以替代Router或另一条throw冒充故障。

| 观测 | 首次实际证据 |
| --- | --- |
| mock factory | **1次真实命中**，固定虚拟throw；receipt epochMs=1790956538349 |
| route/hash | **#/daily**，合法daily_finance摘要/canonical Profile，API prefix count1、schemaVersion1 |
| 条件等待 | **5016ms**轮询结束（5秒上限加最后一次20ms轮询调度尾差16ms），未找到alert；testTimeout10秒，节点5416.4233ms |
| 错误提示 | alertShown=false，stopReason=fault_hit_alert_missing |
| Shell / 导航 / Agent面板 | DOM采样全部true；不能仅据此认为错误处理完成后的保持通过 |
| 内容/状态 | contentHasText=true、publicStatusCount1；未记录原始正文/URL，不能推断具体页面终态 |
| bridge调用 | runtime2、modules2、subscribe2、采样时unsubscribe1/active1；生产StrictMode真实生命周期，不将2计作不允许重复auth或产品缺陷 |
| VirtualConsole、console、未处理拒绝 | 已注册观察，安全事件数组为空；没有把异常全部静默丢弃 |
| 收口 | 真实desktopRoot已unmount、rootEmpty=true、unsubscribe2/active0、DOM closed/global restored；Vitest已exit1 |

条件等待每次把有界20ms轮询交给React act，看到mock与alert才判完成；没有在单个永不结束act中等待、没有固定睡5秒宣布通过。5秒无alert便停止，不延长或重启。实际超过旧200ms，但这只证明本次更长观察仍失败，**不证明旧200ms是唯一根因**，也不证明当前问题已定位。

## 原四条业务断言原样保留

| 原要求 | 本轮实际断言 / 采样 | 结论 |
| --- | --- | --- |
| 新前置：mock factory真实命中 | hits>0断言通过，receipt1 | 故障端口前置已建立 |
| alert包含“页面暂时无法打开” | alert不存在、textContent为undefined，首条业务断言失败 | **failed**，原要求未降低 |
| main.shell存在 | 源码断言保持；被首条失败阻止执行，采样true | not_reached；不冒称passed |
| 模块导航存在 | 源码断言保持；未执行，采样true | not_reached；不冒称passed |
| 统一Agent面板存在 | 源码断言保持；未执行，采样true | not_reached；不冒称passed |

首次错误仍为undefined/string组合的AssertionError，定位新r4-r1-observed.test.tsx:35。没有skip/xfail/重跑覆盖/另起失败任务，cleanup在finally执行并验证root与订阅清零。原R3/R4代码、配置、结果及失败历史一字不改。

原始证据：tests/independent/desktop/evidence/r4-r1/observed-failure/run.log、result.json；从首次log只读提取的observation-receipts.json。新增观测回执只含虚拟阶段/计数、公开hash、布尔DOM状态与时刻，不含token/原始URL/路径/真实profile/正文。

## 判断边界及停止分类

与R4相比，已确认故障factory命中，排除了“本轮从未进入该mock端口”这一解释；但单次命中不证明Router已将这一失败最终发布到当前可见route，也不记录其他loader尝试/终态。Host摘要合法且hash已到daily，不是无依据的空模块假设。当前源码中main确实使用module-routes，loader catch映射desktop_module_unavailable，子路由errorElement与render边界存在；这些静态接线仍不替代实际alert。

本轮证据支持的结论是：**模拟页面故障已触发，5秒内预期错误UI未观察到，独立门禁未通过**。可能的Router/异步终态、mock模块错误传播或前后尝试关系尚未核实。没有用另外的可控loader测试代替原生产入口失败，也没有声称正常EXE19门禁或Shell采样能证明错误后隔离/恢复成功。

任务卡结果分类2要求保留并停止，因此尚未执行新增瞬时/持续失败、explicit retry、健康route/settings切换、在途重复点击/离开、render异常、主题/隐私/runtime/订阅保持及无额外auth/recover/provider/outbox写入。新增开发8项与Shell/composition兼容执行0；旧成功27、outbox42、setting/path关闭证据输入不变、不重复。

需总控共同决定：基于此次命中和公开状态，如何在有限范围只读区分实际Router错误是否发布到当前route、加载尝试/终态与mock错误传播；必要时再冻结精确观察或技术核对范围。此报告不预先指定产品返修，也不自行创建下一任务/扩大时限或第二次目标启动。

## 固定输入与不变性

权威新起点**410/410 matched**，0 mismatch/missing，staged0；manifest SHA **0f695dfc03286f0c2dfe3b1c30f9cb1538600a3657eab6e9f64eedd783e9bcaf**。外部389构建输入、140out、67resources全部匹配。旧393清单/R4交付与新410清单分开，不改旧历史或拿旧协调摘要assert派发后的仓库。

固定只读根C:\MarisLazyR5\R5-20261002-222300，已装普通依赖和Node24.21.0/Vitest5.0.2，不安装/下载/audit/build/package。新增R4-R1配置只接R5普通依赖、React/React DOM/Router单一解析根及实际生产source；mock规范路径与builtin import均指向原DailyFinancePage。

| 产物 | 起终固定SHA-256 |
| --- | --- |
| Maris.exe | 64ce71f3a7b3055f9ad27f6d611e28c4af7e9ba8b86d8b21399b7b422844a80e |
| app.asar | 5ba47909537e1419dc275fa3ca1e5e076a1aa6d5c0205229f91defb92ddd0931 |
| workspace lock | 5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a |

终点审计已通过：**410 entries：406 unchanged、4 authorized changed、0非授权变更、0缺失、staged0**；95项旧独立材料精确不变。实测end-audit.json/delivery-verification.json由新增r4-r1-delivery.py verify复算，仅tester/矩阵B备注/旧主报告与清单追加四路径变化；旧public/r1/r2/r3/r4测试、报告和evidence保持。包/lock/fuses和source389/out140/resources67不变；120ID/12列/前11列原预期与所有原状态、B外bytes及追加prefix保持，A64 passed/C20/D12 not_run不变。

## 原24项完整映射

旧R4及其引用的R3证据均是历史事实，不重复执行。每项保留完整预期；第一门禁未通过，不把其他已过节点或开发报告替代整项通过。

### P4B-SEC-01 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：固定 Electron 构建。
- 输入：BrowserWindow 配置与运行时 renderer。
- 操作：静态检查并在 renderer 探测。
- **完整原预期**：sandbox/contextIsolation 开启、nodeIntegration 关闭；无 `require/process/fs/child_process` 或任意 preload 对象。
- 已有历史部分：原 PUB-03 在新依赖下再次通过；R1-MAIN-01 实际导入main但窗口是虚拟adapter。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：生产 preferences逻辑有证据；实际EXE renderer Node isolation未执行。
- 当前状态：`blocked`，没有全子条件通过不改passed。

### P4B-SEC-02 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：CSP/导航 allowlist 冻结。
- 输入：inline script、data/javascript URL、未知 origin、新窗口、外链。
- 操作：从不可信内容触发导航/打开。
- **完整原预期**：CSP 阻止执行；未知导航/窗口拒绝；获准外链只由 main 安全打开，不加载进应用权限域。
- 已有历史部分：原 PUB-03 CSP字符串再次通过；main安全默认/导航接线只读。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：未在真实页面触发 inline/data/javascript、导航/new-window和外链。
- 当前状态：`blocked`，没有全子条件通过不改passed。

### P4B-SEC-03 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / contract/unit / contract / auto。
- 前置：preload 类型合同可导入。
- 输入：枚举 contextBridge 暴露对象。
- 操作：与 allowlist 对比并尝试直接 ipcRenderer/send/invoke。
- **完整原预期**：只暴露窄 typed 方法；无通用 channel、Node require、密钥或进程控制。
- 已有历史部分：R1-SHELL-09实际导入main preload，capture contextBridge，枚举六组窄API/冻结对象，尝试读取通用invoke/send/ipcRenderer/require/process等均undefined，调用typed方法验证固定channel。companion preload只读为getState/openMain。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：main preload契约部分通过；未执行companion暴露对象与整个renderer域，保守保持blocked。
- 当前状态：`blocked`，没有全子条件通过不改passed。

### P4B-SEC-04 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：IPC handlers 已注册。
- 输入：伪造 sender、错 origin、额外/错型参数、未知 channel、重复调用。
- 操作：逐项 invoke/send。
- **完整原预期**：sender 与参数双校验；稳定拒绝；不得启动进程、改设置、打开窗口或泄露异常。
- 已有历史部分：原 PUB-04 sender/frame/origin/严格参数拒绝再次通过；R1 main导入注册真实handlers。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：未对注册handler执行未知channel/重复/全部无副作用断言或真实Electroninvoke。
- 当前状态：`blocked`，没有全子条件通过不改passed。

### P4B-SEC-05 — blocked

- 来源/风险/层/环境/方式：F07/F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：假 token 与假 API key。
- 输入：localStorage/sessionStorage/IndexedDB/renderer 内存转储、main safeStorage。
- 操作：登录/刷新/重启并检查各层。
- **完整原预期**：refresh/device token 与 API key 只在 main/OS 保护边界；renderer 无持久原文；日志与 crash dump 无值。
- 已有历史部分：原PUB-01/02虚拟加密失败闭合/损坏/密文通过；R1-SHELL-05虚拟owner bootstrap/refresh/revoke通过，R1-OB容量/密文逻辑保持。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：非Windows safeStorage；未检查真实renderer storage/内存、secret/crash dump或OS DPAPI。
- 当前状态：`blocked`，没有全子条件通过不改passed。

### P4B-SEC-06 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / API/integration / Windows/Electron / auto。
- 前置：后端绑定随机 loopback port。
- 输入：只知道端口、错 nonce、错 origin、过期 access、远程地址。
- 操作：绕过 main 直连 Host。
- **完整原预期**：端口不是认证；nonce/origin/token 均校验；只绑定 loopback，远程连接拒绝。
- 已有历史部分：R1-SHELL-01拒绝非HTTP127.0.0.1 endpoint；02 main-only Bearer与并发401刷新；07 managed坏nonce拒绝。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：HTTP为fake fetch，nonce为fake child；实际随机监听/origin/access到期/远程连接未运行。
- 当前状态：`blocked`，没有全子条件通过不改passed。

### P4B-SEC-07 — blocked

- 来源/风险/层/环境/方式：F11/F12 / P0 / security/manual / Windows/Electron / auto。
- 前置：模块标签、错误、消息均含虚拟恶意 HTML。
- 输入：script/img/event handler/RTL/超长文本。
- 操作：渲染导航、通知、Agent panel、错误。
- **完整原预期**：文本安全编码、布局有界且不执行；不得改变 IPC、模块注册或权限。
- 已有历史部分：未做恶意文本UI渲染。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：真实HTML/RTL/长文本编码布局与无脚本执行证据缺失。
- 当前状态：`blocked`，没有全子条件通过不改passed。

### P4B-SEC-08 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / desktop/e2e / Windows/Electron / auto。
- 前置：可注入 preload/backend/lazy-load 故障。
- 输入：内部路径、SQL、堆栈、token canary。
- 操作：触发并查看 UI、console、日志。
- **完整原预期**：用户只见稳定安全错误和 request ID；renderer console/日志无秘密或未授权数据。
- 已有历史部分：原PUB-02 corruption安全错误；R1-SHELL-03/04在401刷新失败、503、非法DTO、network异常下安全error不含虚拟canary；R1-OB-07 dialog rejection无raw console输出。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：未实测实际UI/request ID/preload/lazy故障或真实console/log/crash dump。
- 当前状态：`blocked`，没有全子条件通过不改passed。

### P4B-SUP-01 — blocked

- 来源/风险/层/环境/方式：D9 BackendSupervisor / P0 / desktop/e2e / Windows/Electron / auto。
- 前置：supervisor 可记录 PID+nonce。
- 输入：自己启动、手工启动、伪造同 PID。
- 操作：请求停止/应用退出。
- **完整原预期**：只停止 PID+nonce 匹配且由本实例启动的子进程；手工/他实例进程保持。
- 已有历史部分：R1-SHELL-07错误managed nonce拒绝并清理候选；08external observed child shutdown不调用stop/forceStop。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：虚拟adapter；真实PID/nonce、外来同PID和进程树隔离未执行。
- 当前状态：`blocked`，没有全子条件通过不改passed。

### P4B-SUP-02 — blocked

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：端口分配与 ready 协议冻结。
- 输入：端口冲突、无 ready、坏 nonce、ready 超时。
- 操作：启动后端。
- **完整原预期**：使用随机可用 loopback 端口；超时进入离线/诊断并清理自有子进程，不把 health 当 ready。
- 已有历史部分：R1-SHELL-07坏nonce fail-closed且不进入ready；06成功fake ready。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：端口冲突、ready总超时、随机loopback和真实自有清理未覆盖，不能把health当ready。
- 当前状态：`blocked`，没有全子条件通过不改passed。

### P4B-SUP-03 — blocked

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：假后端可崩溃。
- 输入：启动前崩溃、ready 后崩溃、连续崩溃。
- 操作：观察重启策略。
- **完整原预期**：状态转 offline；重启次数/退避有界，不形成重启风暴或重复 run；用户可恢复。
- 已有历史部分：R1-SHELL-06 fake child exit→offline，recover退避1/2/4秒、三次上限，第四次exhausted，shutdown阻止再start。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：注入delay/child，不是Windows真实崩溃；启动前崩溃、健康循环与全部UI状态未覆盖。
- 当前状态：`blocked`，没有全子条件通过不改passed。

### P4B-SUP-04 — blocked

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：已有手动后端或两个 app 启动请求。
- 输入：重复启动、开发连接模式。
- 操作：启动/关闭两个客户端。
- **完整原预期**：不产生重复 owned 后端；连接手动后端时不取得停止权；状态可区分。
- 已有历史部分：R1-SHELL-06并发start/recover single-flight不增重复start；08external不启动owned也无停止权。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：未执行双真实客户端/单实例EXE场景。
- 当前状态：`blocked`，没有全子条件通过不改passed。

### P4B-SUP-05 — not_run

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / security/manual / Windows/Electron / manual。
- 前置：目标 Windows，后端含子线程/连接。
- 输入：正常退出、强关主窗口、系统注销。
- 操作：检查进程树/端口/文件锁。
- **完整原预期**：自有后端按冻结时限退出，无僵尸/孤儿/占用端口；未拥有进程不受影响。
- 已有历史部分：真实退出、强关和注销均未执行；R1-MAIN-02/03仅虚拟Hostshutdown/窗口destroy。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：manual not_run；无owned资源仅表示没启动，不能推断cleanup通过。
- 当前状态：`not_run`，没有全子条件通过不改passed。

### P4B-SUP-06 — blocked

- 来源/风险/层/环境/方式：D9 offline recovery / P0 / desktop/e2e / Windows/Electron / auto。
- 前置：renderer 有未发送虚拟消息。
- 输入：后端离线→恢复、应用重启、重复点击。
- 操作：发送并观察 client_event_id/GET。
- **完整原预期**：未发送内容和同一 ID 保留；恢复后只提交一次；UI 不凭新 ID 制造重复账候选。
- 已有历史部分：原PUB-11不变断言1 passed，原其他10再次通过；新增R1-OB26覆盖持久保留/确认/身份/故障/容量，加R1-MAIN5实际main接线。建议关闭原OUTBOX-001的公开持久化P1。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：真实老化原生提示unverified、恢复后GET/只提交一次与实际UI缺失；整项从failed改blocked，原P0风险不变。
- 当前状态：`blocked`，没有全子条件通过不改passed。

### P4B-UI-01 — blocked

- 来源/风险/层/环境/方式：F12 / P1 / contract/unit / contract / auto。
- 前置：compiled registry 与 `/modules` fixture。
- 输入：后端启用/禁用、桌面缺失、版本不兼容、未知模块。
- 操作：计算交集。
- **完整原预期**：只渲染两侧均存在且兼容的模块；未知/禁用不导航、不预加载。
- 已有历史部分：原PUB-05canonical registry/Host交集再次通过，R1-SHELL-10两纯测试contribution正常compile。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：实际导航/preload未运行；没有创建真实第二产品模块。
- 当前状态：`blocked`，没有全子条件通过不改passed。

### P4B-UI-02 — failed

- 来源/风险/层/环境/方式：F12 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：两个 lazy route。
- 输入：chunk 加载失败、重试成功、切换模块。
- 操作：导航并恢复。
- **完整原预期**：局部错误边界可重试，Shell/登录/其他模块可用；不循环加载或丢当前会话。
- 已有历史部分：未执行两个lazy routes的chunk故障/局部retry。
- 本轮新增：新OBS节点一次0pass/1fail：mock1、#/daily、5016ms无alert，Shell/nav/Agent采样在，真实root/订阅清理完成。
- 具体缺口与层级：已建立故障端口，未完成预期错误终态；LAZY-001不能关闭，恢复/切换/状态边界和Windows均未执行，不新增未经定位产品P1。
- 当前状态：`failed`，没有全子条件通过不改passed。

### P4B-UI-03 — blocked

- 来源/风险/层/环境/方式：F12 / P1 / contract/unit / contract / auto。
- 前置：冻结 OpenAPI 与生成命令。
- 输入：后端 DTO 字段/枚举/required 改变；生成物陈旧。
- 操作：CI 比较生成差异并编译。
- **完整原预期**：漂移门禁失败并定位；不得靠手写 API 类型掩盖差异或运行时下载 schema。
- 已有历史部分：生成物和OpenAPI保持冻结输入，没有运行生成/类型漂移mutation。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：未取得失败定位或CI drift独立证据。
- 当前状态：`blocked`，没有全子条件通过不改passed。

### P4B-UI-04 — blocked

- 来源/风险/层/环境/方式：F12 / P1 / contract/unit / contract / auto。
- 前置：UI contribution 合同冻结。
- 输入：hostUiMajor、route/path/setting/profile/companion 冲突。
- 操作：编译期注册和启动验证。
- **完整原预期**：不兼容或冲突稳定失败；Shell 无 `if moduleId` 业务分支。
- 已有历史部分：R1-SHELL-11四种module/profile/route ID/appearance冲突拒绝，12不兼容major和非canonical输入拒绝；13跨module相同setting key仍接受两模块，首次失败。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：UI-04完整独立结构/strict贡献及启动验证映射尚未完成，新P1停止；不能由路径通过直接passed。
- 当前状态：`blocked`，没有全子条件通过不改passed。

### P4B-CMP-01 — blocked

- 来源/风险/层/环境/方式：F13；U02 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：daily/wealth contributions 与假状态流。
- 输入：切换模块及 idle/thinking/tool/confirmation/error/offline。
- 操作：观察窗口、Profile 和状态。
- **完整原预期**：始终只有一个毛毛窗口/Agent 入口；主形态随 contribution，子状态不创建第二 Agent或触发写入。
- 已有历史部分：R1-MAIN-01虚拟BrowserWindow构造仅Maris和毛毛，Host启动不被dialog等待。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：实际单毛毛/Agent入口、contribution主形态和完整子状态流未运行。
- 当前状态：`blocked`，没有全子条件通过不改passed。

### P4B-CMP-02 — blocked

- 来源/风险/层/环境/方式：U01/F13 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：新设备设置。
- 输入：首次和第二次关闭主窗口。
- 操作：关闭、从 Tray 恢复、再次关闭。
- **完整原预期**：首次隐藏并只提示一次；第二次不重复提示；Host/毛毛按设置驻留且无数据丢失。
- 已有历史部分：未执行真实close/Tray恢复/提示一次场景。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：虚拟ready-to-show retention不等于首次close提示；真实设备not_run子项保持。
- 当前状态：`blocked`，没有全子条件通过不改passed。

### P4B-CMP-03 — blocked

- 来源/风险/层/环境/方式：U01 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：关闭策略可切换。
- 输入：退出/每次询问/隐藏，Tray 打开/隐藏。
- 操作：每种设置执行关闭与取消。
- **完整原预期**：行为精确对应设置；“退出”清理自有后端；询问取消不退出；Tray 状态一致。
- 已有历史部分：未测试三种closePolicy与询问取消/Tray；R1-MAIN before-quit仅退出接线。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：不以mock app.quit或E2E timer当生产关闭策略证明。
- 当前状态：`blocked`，没有全子条件通过不改passed。

### P4B-CMP-04 — not_run

- 来源/风险/层/环境/方式：U05 / P1 / security/manual / Windows/Electron / manual。
- 前置：新安装测试 profile。
- 输入：首次运行、显式启用/禁用开机启动。
- 操作：检查 OS 启动项和 UI。
- **完整原预期**：默认关闭且无启动项；只有明确操作才创建；禁用清理本应用项，不改其他应用。
- 已有历史部分：未创建/删除OS启动项；main fixture app.setLoginItemSettings是mock。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：manual not_run；E2E抑制启动项不等于OS合同通过。
- 当前状态：`not_run`，没有全子条件通过不改passed。

### P4B-CMP-05 — not_run

- 来源/风险/层/环境/方式：F13 / P1 / desktop/e2e / external/manual / manual。
- 前置：多显示器/缩放/全屏测试设备。
- 输入：拖动、置顶、重启、拔屏、分辨率变化、全屏、隐私、键盘。
- 操作：逐项操作并重启。
- **完整原预期**：位置用临时文件原子替换并恢复/夹取；全屏按规则隐藏；隐私不显示金额；键盘入口可达。
- 已有历史部分：未修改显示器/缩放/全屏/窗口坐标或测试隐私键盘。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：实际位置夹取/重启/多屏/全屏/键盘/隐私UI与全部人工设备条件未执行，整项manual not_run保持。
- 当前状态：`not_run`，没有全子条件通过不改passed。

### P4B-CMP-06 — not_run

- 来源/风险/层/环境/方式：U02；主题要求 / P2 / desktop/e2e / external/manual / manual。
- 前置：支持/不支持透明窗口设备。
- 输入：透明失败、普通迷你窗降级；light/dark/system/high-contrast/reduced-motion；中外行情色。
- 操作：切换设备条件和主题。
- **完整原预期**：可安全降级且合同不变；文本对比/焦点可辨；reduced motion 生效；收入/支出色不复用涨跌色。
- 已有历史部分：未启动透明/降级窗口或切换系统主题。
- 本轮新增：not_run，观察门禁失败后停止扩大。
- 具体缺口与层级：manual not_run；真实对比度/焦点/reduced motion/颜色语义未测试。
- 当前状态：`not_run`，没有全子条件通过不改passed。

## 启动预算、安全收口、warning和交接

独立1 executed：0passed/1failed；后续独立与兼容0。产品**0/8**、辅助Electron**0/4**、Windows/CDP请求注入**0**；未建立外部C12-R4-R1 root/profile/db/session，无实际owned进程/窗口/监听需要停止。jsdom实际root卸载、订阅2→0、DOM/global清理有回执；它不证明生产Tray/后端cleanup通过。

真实chunk/会话持久化、安全CSP/导航/renderer秘密/恶意文本、generated drift、严格贡献结构余项、safeStorage/native老化提示、Tray/closePolicy/单实例/毛毛设备状态等未执行。OS注销/重启/启动项/多屏/DPI/拔屏/系统主题/透明降级人工条件保持原not_run/unverified，不要求用户现在点击，不删降验收条件。

本轮不存在配置/语法修正或目标重试；首次assert失败保留。只清理新增专属cache前重读control、验证绝对范围/无reparse，首次log/JSON及所有审计保留；不清理旧环境或个人资料。定向diff --check退出0，仅四份既有文档LF→CRLF提示，记录在evidence/r4-r1/diff-check.log，不修改Git配置；Git staged0，无Git写操作。

无产品/开发测试/依赖/lock/build/package/迁移/冻结/control/overview/其他角色写入，无Docker/PG/OpenClaw/微信/DeepSeek/provider/真实账户/财务/原始秘密或系统设置操作。新报告、r4-r1-audit.py、r4-r1-vitest.config.mjs、r4-r1-observed.test.tsx、r4-r1-delivery.py、r4-r1-handoff.py与evidence/r4-r1单列；旧主报告/人工清单只追加、B矩阵仅备注、自身日志更新。

交付停在 **blocked / finished**。总控接收确认mock命中但预期终态缺失的新证据，裁定有限后续核对；本角色不创建新任务、启动其他角色/P4-C、不自行续跑，LAZY-001/UI-02/P4-B仍未接受。
