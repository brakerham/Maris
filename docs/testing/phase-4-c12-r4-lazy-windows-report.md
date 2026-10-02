# P4-C12-R4 lazy独立复验与Windows验收报告

- 角色：既有测试智能体、C12-R4唯一负责人；control 2026-10-02T23:25:00+08:00；2026-10-02 Asia/Shanghai。
- 任务卡：`docs/coordination/prompts/p4-c12-r4-lazy-windows-tester.md`。
- **交付 blocked / finished**：原lazy失败精确节点首次复验未通过，按任务卡第一阶段门禁停止。LAZY-001不能建议关闭；本轮没有足够证据新增产品P0/P1，也不声称旧Shell消失缺陷仍复现。最终结论由总控裁定。

## 本轮结果与停止原因

| 类别 | 实际结果 | 证据/限制 |
| --- | --- | --- |
| 原R3-UI-02-LAZY不变断言、精确节点、唯一一次 | **0 passed / 1 failed**，exit1 | evidence/r4/original-lazy/run.log、result.json |
| 新独立恢复/严格注册等 | **not_run，执行0** | 第一阶段未通过，不扩大测试 |
| lazy开发8+Shell/composition兼容 | **not_run，执行0** | 未进入兼容阶段，不跑registry52或完整132 |
| 真实Windows/临时chunk请求注入 | **not_run / unverified，执行0** | 产品0/8，辅助Electron0/4，注入0 |
| 原24项矩阵 | **0 passed、1 failed、19 blocked、4 not_run** | 状态不预写通过；UI-02旧failed保留未关闭，UI-04仍blocked |

不是再现原来的“Shell消失”：当前首次输出反而为Shell/nav/Agent全部存在，但预设chunk失败alert未出现。断言先期待alert文本，收到undefined，尚未执行后面的Shell断言；不能挑选前三个true冒充原节点passed，也不能把缺少alert当作产品已吞掉错误或修复无效的确定结论。

```json
{"caseId":"R3-UI-02-LAZY","chunkFailureShown":false,"shellPresent":true,"navigationPresent":true,"agentPanelPresent":true,"data":"virtual_only","evidenceLayer":"real_renderer_in_jsdom_with_virtual_bridge_and_failed_chunk"}
```

最后脱敏错误：`AssertionError: the given combination of arguments (undefined and string) is invalid for this assertion`，原r3-remaining.test.tsx:17期待alert.textContent包含“页面暂时无法打开”。Vitest JSON numTotalTests=1、passed0、failed1、pending0；23:30:53开始，节点761.2744ms。日志/JSON保留首次结果，未xfail/skip、未重跑覆盖、未改旧文件或放宽断言。

## 只读核对与尚未判定的原因

实际main已经导入并使用生产module-routes的DesktopApp和rendererRootOptions，registry为真实compileRegistry的daily contribution。module-routes仍以builtin daily_finance_home延迟import原页面，原测试mock指向同一规范源文件；新增R4配置只接R5普通依赖，没有替代Router/Shell/模块实现。静态来源摘要见readonly-source-observation.json。

原测试只轮询最多20×10ms，没有记录loader进入/完成或mock factory命中；Shell可来自新hydrateFallback/正常root，并不证明预期页面错误分支完成。**可能是异步路由/加载观测时限或mock解析接线，原因unverified**。现有静态同路径不证明动态mock命中，现有结果也不能排除产品分支问题。没有修改观察时限或插入诊断重跑，不能凭开发八项/正常EXE19成功宣布独立关闭。

已尝试：一次原断言精确执行；随后只读结果/原test/main/module-routes/Shell来源对照。无需操作用户电脑，没有运行辅助Electron、Windows产品或新测试。任务明确“若失败保留并停止，不重跑或进入Windows”，因此在本轮目标已运行后不适用“目标前无副作用配置错误一次更正”例外。

需要总控共同决定：下一步如何保留这次原始失败，建立可证实故障注入命中与加载完成的有限观察契约，再判断隔离/恢复行为。该决策属于测试证据/接线门禁，不预先要求产品返修。此角色不创建下一任务或自行续跑。

## 权威起点与外部包输入

新起点393/393 matched，0 missing/mismatch，staged0；manifest SHA `b248977db4d1b1aa84c843caa73cd1cac3ce25bcaa3ba5eb461b54863d963377`。外部构建输入389/389、out140/140、resources67/67分别匹配；历史R5 source390不直接assert派发后当前协调文件。原清单未修改，没有发生上一轮历史source误映射。

只读根C:\MarisLazyR5\R5-20261002-222300，已有Node24.21.0/Vitest5.0.2和普通依赖，未install/download/audit/build/package。

| 文件（workspace下） | 起终固定SHA-256 |
| --- | --- |
| apps/desktop/out/Maris-win32-x64/Maris.exe | 64ce71f3a7b3055f9ad27f6d611e28c4af7e9ba8b86d8b21399b7b422844a80e |
| resources/app.asar | 5ba47909537e1419dc275fa3ca1e5e076a1aa6d5c0205229f91defb92ddd0931 |
| pnpm-lock.yaml | 5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a |

终点审计已通过：**393 entries：389 unchanged、4 authorized changed、0非授权变更、0缺失、staged0**；82项旧独立材料精确不变。证据为r4-delivery.py verify生成的end-audit.json及delivery-verification.json。四项仅旧主报告/清单追加、matrix B备注、自身tester；所有旧public/r1/r2/r3代码/配置/报告/evidence保持。EXE/asar/lock/fuse字节、外部构建source389/out140/resources67不变。120唯一ID/12列/原前11列、B外字节及旧报告/清单prefix保持，A64 passed、C20/D12 not_run不变。

## UI-02 / UI-04 子条件与本轮缺口

- UI-02：原错误分支未成功观测，LAZY-001独立关闭门禁失败；局部隔离、明确retry实际成功、持续失败无循环、双route/settings切换、并发点击/离开后旧结果、render错误、安全DOM/console、主题/隐私/runtime/订阅保持和无额外auth/recover/provider/outbox写入均未新验收。仅Shell/nav/Agent采样存在不等于错误后的保持通过。
- Windows真实chunk、真实session故障持久化、CDP限定请求注入与撤销均未运行，也未声称file/asar工具不支持；尚未进入可行性检查阶段，不能虚构环境限制。
- UI-04：旧path/setting及身份校验独立通过证据输入不变，原27成功独立节点和outbox42不重跑。严格贡献对象/完整结构等剩余独立缺口因原lazy门禁停止而not_run；开发映射仅定位，整项blocked保持。路径大小写/尾斜杠/模式等未冻结语义不新增规则。

## 原24项完整映射

以下保留完整原预期。既有部分引自只读R3报告，明确为历史证据、未重跑；本轮没有把开发通过或静态source当整项passed。

### P4B-SEC-01 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：固定 Electron 构建。
- 输入：BrowserWindow 配置与运行时 renderer。
- 操作：静态检查并在 renderer 探测。
- **完整原预期**：sandbox/contextIsolation 开启、nodeIntegration 关闭；无 `require/process/fs/child_process` 或任意 preload 对象。
- 已有历史部分：原 PUB-03 在新依赖下再次通过；R1-MAIN-01 实际导入main但窗口是虚拟adapter。
- 上轮R3新增（历史未重跑）：未新增执行；新P1停止扩大。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：生产 preferences逻辑有证据；实际EXE renderer Node isolation未执行。
- 当前状态：`blocked`；无全部子条件通过不改passed。

### P4B-SEC-02 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：CSP/导航 allowlist 冻结。
- 输入：inline script、data/javascript URL、未知 origin、新窗口、外链。
- 操作：从不可信内容触发导航/打开。
- **完整原预期**：CSP 阻止执行；未知导航/窗口拒绝；获准外链只由 main 安全打开，不加载进应用权限域。
- 已有历史部分：原 PUB-03 CSP字符串再次通过；main安全默认/导航接线只读。
- 上轮R3新增（历史未重跑）：未新增执行；新P1停止扩大。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：未在真实页面触发 inline/data/javascript、导航/new-window和外链。
- 当前状态：`blocked`；无全部子条件通过不改passed。

### P4B-SEC-03 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / contract/unit / contract / auto。
- 前置：preload 类型合同可导入。
- 输入：枚举 contextBridge 暴露对象。
- 操作：与 allowlist 对比并尝试直接 ipcRenderer/send/invoke。
- **完整原预期**：只暴露窄 typed 方法；无通用 channel、Node require、密钥或进程控制。
- 已有历史部分：R1-SHELL-09实际导入main preload，capture contextBridge，枚举六组窄API/冻结对象，尝试读取通用invoke/send/ipcRenderer/require/process等均undefined，调用typed方法验证固定channel。companion preload只读为getState/openMain。
- 上轮R3新增（历史未重跑）：未新增执行；新P1停止扩大。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：main preload契约部分通过；未执行companion暴露对象与整个renderer域，保守保持blocked。
- 当前状态：`blocked`；无全部子条件通过不改passed。

### P4B-SEC-04 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：IPC handlers 已注册。
- 输入：伪造 sender、错 origin、额外/错型参数、未知 channel、重复调用。
- 操作：逐项 invoke/send。
- **完整原预期**：sender 与参数双校验；稳定拒绝；不得启动进程、改设置、打开窗口或泄露异常。
- 已有历史部分：原 PUB-04 sender/frame/origin/严格参数拒绝再次通过；R1 main导入注册真实handlers。
- 上轮R3新增（历史未重跑）：未新增执行；新P1停止扩大。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：未对注册handler执行未知channel/重复/全部无副作用断言或真实Electroninvoke。
- 当前状态：`blocked`；无全部子条件通过不改passed。

### P4B-SEC-05 — blocked

- 来源/风险/层/环境/方式：F07/F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：假 token 与假 API key。
- 输入：localStorage/sessionStorage/IndexedDB/renderer 内存转储、main safeStorage。
- 操作：登录/刷新/重启并检查各层。
- **完整原预期**：refresh/device token 与 API key 只在 main/OS 保护边界；renderer 无持久原文；日志与 crash dump 无值。
- 已有历史部分：原PUB-01/02虚拟加密失败闭合/损坏/密文通过；R1-SHELL-05虚拟owner bootstrap/refresh/revoke通过，R1-OB容量/密文逻辑保持。
- 上轮R3新增（历史未重跑）：未新增执行；新P1停止扩大。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：非Windows safeStorage；未检查真实renderer storage/内存、secret/crash dump或OS DPAPI。
- 当前状态：`blocked`；无全部子条件通过不改passed。

### P4B-SEC-06 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / API/integration / Windows/Electron / auto。
- 前置：后端绑定随机 loopback port。
- 输入：只知道端口、错 nonce、错 origin、过期 access、远程地址。
- 操作：绕过 main 直连 Host。
- **完整原预期**：端口不是认证；nonce/origin/token 均校验；只绑定 loopback，远程连接拒绝。
- 已有历史部分：R1-SHELL-01拒绝非HTTP127.0.0.1 endpoint；02 main-only Bearer与并发401刷新；07 managed坏nonce拒绝。
- 上轮R3新增（历史未重跑）：未新增执行；新P1停止扩大。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：HTTP为fake fetch，nonce为fake child；实际随机监听/origin/access到期/远程连接未运行。
- 当前状态：`blocked`；无全部子条件通过不改passed。

### P4B-SEC-07 — blocked

- 来源/风险/层/环境/方式：F11/F12 / P0 / security/manual / Windows/Electron / auto。
- 前置：模块标签、错误、消息均含虚拟恶意 HTML。
- 输入：script/img/event handler/RTL/超长文本。
- 操作：渲染导航、通知、Agent panel、错误。
- **完整原预期**：文本安全编码、布局有界且不执行；不得改变 IPC、模块注册或权限。
- 已有历史部分：未做恶意文本UI渲染。
- 上轮R3新增（历史未重跑）：未新增执行；新P1停止扩大。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：真实HTML/RTL/长文本编码布局与无脚本执行证据缺失。
- 当前状态：`blocked`；无全部子条件通过不改passed。

### P4B-SEC-08 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / desktop/e2e / Windows/Electron / auto。
- 前置：可注入 preload/backend/lazy-load 故障。
- 输入：内部路径、SQL、堆栈、token canary。
- 操作：触发并查看 UI、console、日志。
- **完整原预期**：用户只见稳定安全错误和 request ID；renderer console/日志无秘密或未授权数据。
- 已有历史部分：原PUB-02 corruption安全错误；R1-SHELL-03/04在401刷新失败、503、非法DTO、network异常下安全error不含虚拟canary；R1-OB-07 dialog rejection无raw console输出。
- 上轮R3新增（历史未重跑）：未新增执行；新P1停止扩大。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：未实测实际UI/request ID/preload/lazy故障或真实console/log/crash dump。
- 当前状态：`blocked`；无全部子条件通过不改passed。

### P4B-SUP-01 — blocked

- 来源/风险/层/环境/方式：D9 BackendSupervisor / P0 / desktop/e2e / Windows/Electron / auto。
- 前置：supervisor 可记录 PID+nonce。
- 输入：自己启动、手工启动、伪造同 PID。
- 操作：请求停止/应用退出。
- **完整原预期**：只停止 PID+nonce 匹配且由本实例启动的子进程；手工/他实例进程保持。
- 已有历史部分：R1-SHELL-07错误managed nonce拒绝并清理候选；08external observed child shutdown不调用stop/forceStop。
- 上轮R3新增（历史未重跑）：未新增执行；新P1停止扩大。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：虚拟adapter；真实PID/nonce、外来同PID和进程树隔离未执行。
- 当前状态：`blocked`；无全部子条件通过不改passed。

### P4B-SUP-02 — blocked

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：端口分配与 ready 协议冻结。
- 输入：端口冲突、无 ready、坏 nonce、ready 超时。
- 操作：启动后端。
- **完整原预期**：使用随机可用 loopback 端口；超时进入离线/诊断并清理自有子进程，不把 health 当 ready。
- 已有历史部分：R1-SHELL-07坏nonce fail-closed且不进入ready；06成功fake ready。
- 上轮R3新增（历史未重跑）：未新增执行；新P1停止扩大。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：端口冲突、ready总超时、随机loopback和真实自有清理未覆盖，不能把health当ready。
- 当前状态：`blocked`；无全部子条件通过不改passed。

### P4B-SUP-03 — blocked

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：假后端可崩溃。
- 输入：启动前崩溃、ready 后崩溃、连续崩溃。
- 操作：观察重启策略。
- **完整原预期**：状态转 offline；重启次数/退避有界，不形成重启风暴或重复 run；用户可恢复。
- 已有历史部分：R1-SHELL-06 fake child exit→offline，recover退避1/2/4秒、三次上限，第四次exhausted，shutdown阻止再start。
- 上轮R3新增（历史未重跑）：未新增执行；新P1停止扩大。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：注入delay/child，不是Windows真实崩溃；启动前崩溃、健康循环与全部UI状态未覆盖。
- 当前状态：`blocked`；无全部子条件通过不改passed。

### P4B-SUP-04 — blocked

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：已有手动后端或两个 app 启动请求。
- 输入：重复启动、开发连接模式。
- 操作：启动/关闭两个客户端。
- **完整原预期**：不产生重复 owned 后端；连接手动后端时不取得停止权；状态可区分。
- 已有历史部分：R1-SHELL-06并发start/recover single-flight不增重复start；08external不启动owned也无停止权。
- 上轮R3新增（历史未重跑）：未新增执行；新P1停止扩大。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：未执行双真实客户端/单实例EXE场景。
- 当前状态：`blocked`；无全部子条件通过不改passed。

### P4B-SUP-05 — not_run

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / security/manual / Windows/Electron / manual。
- 前置：目标 Windows，后端含子线程/连接。
- 输入：正常退出、强关主窗口、系统注销。
- 操作：检查进程树/端口/文件锁。
- **完整原预期**：自有后端按冻结时限退出，无僵尸/孤儿/占用端口；未拥有进程不受影响。
- 已有历史部分：真实退出、强关和注销均未执行；R1-MAIN-02/03仅虚拟Hostshutdown/窗口destroy。
- 上轮R3新增（历史未重跑）：未新增执行；新P1停止扩大。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：manual not_run；无owned资源仅表示没启动，不能推断cleanup通过。
- 当前状态：`not_run`；无全部子条件通过不改passed。

### P4B-SUP-06 — blocked

- 来源/风险/层/环境/方式：D9 offline recovery / P0 / desktop/e2e / Windows/Electron / auto。
- 前置：renderer 有未发送虚拟消息。
- 输入：后端离线→恢复、应用重启、重复点击。
- 操作：发送并观察 client_event_id/GET。
- **完整原预期**：未发送内容和同一 ID 保留；恢复后只提交一次；UI 不凭新 ID 制造重复账候选。
- 已有历史部分：原PUB-11不变断言1 passed，原其他10再次通过；新增R1-OB26覆盖持久保留/确认/身份/故障/容量，加R1-MAIN5实际main接线。建议关闭原OUTBOX-001的公开持久化P1。
- 上轮R3新增（历史未重跑）：未新增执行；新P1停止扩大。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：真实老化原生提示unverified、恢复后GET/只提交一次与实际UI缺失；整项从failed改blocked，原P0风险不变。
- 当前状态：`blocked`；无全部子条件通过不改passed。

### P4B-UI-01 — blocked

- 来源/风险/层/环境/方式：F12 / P1 / contract/unit / contract / auto。
- 前置：compiled registry 与 `/modules` fixture。
- 输入：后端启用/禁用、桌面缺失、版本不兼容、未知模块。
- 操作：计算交集。
- **完整原预期**：只渲染两侧均存在且兼容的模块；未知/禁用不导航、不预加载。
- 已有历史部分：原PUB-05canonical registry/Host交集再次通过，R1-SHELL-10两纯测试contribution正常compile。
- 上轮R3新增（历史未重跑）：未新增执行；新P1停止扩大。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：实际导航/preload未运行；没有创建真实第二产品模块。
- 当前状态：`blocked`；无全部子条件通过不改passed。

### P4B-UI-02 — failed

- 来源/风险/层/环境/方式：F12 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：两个 lazy route。
- 输入：chunk 加载失败、重试成功、切换模块。
- 操作：导航并恢复。
- **完整原预期**：局部错误边界可重试，Shell/登录/其他模块可用；不循环加载或丢当前会话。
- 已有历史部分：未执行两个lazy routes的chunk故障/局部retry。
- 上轮R3新增（历史未重跑）：R3-UI-02-LAZY首次失败：真实renderer/jsdom，安全错误页出现但Shell/nav/Agent入口全部消失。
- 本轮执行：原R3-UI-02-LAZY唯一一次0pass/1fail，未观测alert但Shell/nav/Agent采样存在；不能确定故障注入命中或完成。
- 尚缺条件/证据层级：原门禁未通过，旧LAZY-001不关闭；全部恢复边界/错误状态保持与Windows故障尚未验收。失败是独立节点结果，不新增已定级产品P1。
- 当前状态：`failed`；无全部子条件通过不改passed。

### P4B-UI-03 — blocked

- 来源/风险/层/环境/方式：F12 / P1 / contract/unit / contract / auto。
- 前置：冻结 OpenAPI 与生成命令。
- 输入：后端 DTO 字段/枚举/required 改变；生成物陈旧。
- 操作：CI 比较生成差异并编译。
- **完整原预期**：漂移门禁失败并定位；不得靠手写 API 类型掩盖差异或运行时下载 schema。
- 已有历史部分：生成物和OpenAPI保持冻结输入，没有运行生成/类型漂移mutation。
- 上轮R3新增（历史未重跑）：未新增执行；新P1停止扩大。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：未取得失败定位或CI drift独立证据。
- 当前状态：`blocked`；无全部子条件通过不改passed。

### P4B-UI-04 — blocked

- 来源/风险/层/环境/方式：F12 / P1 / contract/unit / contract / auto。
- 前置：UI contribution 合同冻结。
- 输入：hostUiMajor、route/path/setting/profile/companion 冲突。
- 操作：编译期注册和启动验证。
- **完整原预期**：不兼容或冲突稳定失败；Shell 无 `if moduleId` 业务分支。
- 已有历史部分：R1-SHELL-11四种module/profile/route ID/appearance冲突拒绝，12不兼容major和非canonical输入拒绝；13跨module相同setting key仍接受两模块，首次失败。
- 上轮R3新增（历史未重跑）：原路径1+新路径9+ASCII1通过；旧setting及身份相邻不重跑；建议关闭PATH-001。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：UI-04完整独立结构/strict贡献及启动验证映射尚未完成，新P1停止；不能由路径通过直接passed。
- 当前状态：`blocked`；无全部子条件通过不改passed。

### P4B-CMP-01 — blocked

- 来源/风险/层/环境/方式：F13；U02 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：daily/wealth contributions 与假状态流。
- 输入：切换模块及 idle/thinking/tool/confirmation/error/offline。
- 操作：观察窗口、Profile 和状态。
- **完整原预期**：始终只有一个毛毛窗口/Agent 入口；主形态随 contribution，子状态不创建第二 Agent或触发写入。
- 已有历史部分：R1-MAIN-01虚拟BrowserWindow构造仅Maris和毛毛，Host启动不被dialog等待。
- 上轮R3新增（历史未重跑）：未新增执行；新P1停止扩大。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：实际单毛毛/Agent入口、contribution主形态和完整子状态流未运行。
- 当前状态：`blocked`；无全部子条件通过不改passed。

### P4B-CMP-02 — blocked

- 来源/风险/层/环境/方式：U01/F13 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：新设备设置。
- 输入：首次和第二次关闭主窗口。
- 操作：关闭、从 Tray 恢复、再次关闭。
- **完整原预期**：首次隐藏并只提示一次；第二次不重复提示；Host/毛毛按设置驻留且无数据丢失。
- 已有历史部分：未执行真实close/Tray恢复/提示一次场景。
- 上轮R3新增（历史未重跑）：未新增执行；新P1停止扩大。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：虚拟ready-to-show retention不等于首次close提示；真实设备not_run子项保持。
- 当前状态：`blocked`；无全部子条件通过不改passed。

### P4B-CMP-03 — blocked

- 来源/风险/层/环境/方式：U01 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：关闭策略可切换。
- 输入：退出/每次询问/隐藏，Tray 打开/隐藏。
- 操作：每种设置执行关闭与取消。
- **完整原预期**：行为精确对应设置；“退出”清理自有后端；询问取消不退出；Tray 状态一致。
- 已有历史部分：未测试三种closePolicy与询问取消/Tray；R1-MAIN before-quit仅退出接线。
- 上轮R3新增（历史未重跑）：未新增执行；新P1停止扩大。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：不以mock app.quit或E2E timer当生产关闭策略证明。
- 当前状态：`blocked`；无全部子条件通过不改passed。

### P4B-CMP-04 — not_run

- 来源/风险/层/环境/方式：U05 / P1 / security/manual / Windows/Electron / manual。
- 前置：新安装测试 profile。
- 输入：首次运行、显式启用/禁用开机启动。
- 操作：检查 OS 启动项和 UI。
- **完整原预期**：默认关闭且无启动项；只有明确操作才创建；禁用清理本应用项，不改其他应用。
- 已有历史部分：未创建/删除OS启动项；main fixture app.setLoginItemSettings是mock。
- 上轮R3新增（历史未重跑）：未新增执行；新P1停止扩大。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：manual not_run；E2E抑制启动项不等于OS合同通过。
- 当前状态：`not_run`；无全部子条件通过不改passed。

### P4B-CMP-05 — not_run

- 来源/风险/层/环境/方式：F13 / P1 / desktop/e2e / external/manual / manual。
- 前置：多显示器/缩放/全屏测试设备。
- 输入：拖动、置顶、重启、拔屏、分辨率变化、全屏、隐私、键盘。
- 操作：逐项操作并重启。
- **完整原预期**：位置用临时文件原子替换并恢复/夹取；全屏按规则隐藏；隐私不显示金额；键盘入口可达。
- 已有历史部分：未修改显示器/缩放/全屏/窗口坐标或测试隐私键盘。
- 上轮R3新增（历史未重跑）：R3-SET-01/02/03本地设置defaults/有效持久化/非法字段拒绝通过；只有虚拟bounds字段。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：实际位置夹取/重启/多屏/全屏/键盘/隐私UI与全部人工设备条件未执行，整项manual not_run保持。
- 当前状态：`not_run`；无全部子条件通过不改passed。

### P4B-CMP-06 — not_run

- 来源/风险/层/环境/方式：U02；主题要求 / P2 / desktop/e2e / external/manual / manual。
- 前置：支持/不支持透明窗口设备。
- 输入：透明失败、普通迷你窗降级；light/dark/system/high-contrast/reduced-motion；中外行情色。
- 操作：切换设备条件和主题。
- **完整原预期**：可安全降级且合同不变；文本对比/焦点可辨；reduced motion 生效；收入/支出色不复用涨跌色。
- 已有历史部分：未启动透明/降级窗口或切换系统主题。
- 上轮R3新增（历史未重跑）：未新增执行；新P1停止扩大。
- 本轮执行：not_run；原lazy门禁首次失败后停止。
- 尚缺条件/证据层级：manual not_run；真实对比度/焦点/reduced motion/颜色语义未测试。
- 当前状态：`not_run`；无全部子条件通过不改passed。

## 安全收口、警告与交接

全部Vitest命令已退出1，没有活动session；产品0/8、辅助Electron0/4、chunk故障注入0。没有创建C:\MarisC12\C12-R4-*或任何虚拟profile/db/session，不访问真实AppData。没有owned产品/后端进程、实际窗口或监听需要终止；零资源源于未启动，不证明Tray/SUP-05通过。只清理本轮r4缓存，核对绝对专属范围且无reparse，首次result/log和审计保留。

真实native dialog/safeStorage老化提示unverified；Tray/普通closePolicy/注销/开机启动/多屏/DPI/主题/透明降级等旧人工条件not_run保持，原清单不删除/降级，不要求用户现在点击。未执行兼容8+2、新独立恢复、设置/ZIP/staging成功回归、Windows或后续注入。

初始只读查找猜module-routes在shell下，实际位于renderer，首次Get-Content不存在错误保留为搜索定位说明，随后按main相对import只读读取真实文件；没有配置/目标重试。原目标失败不是语法错误，不能套用前目标修正。Git定向diff --check退出0，仅四份既有文档LF→CRLF提示，日志在evidence/r4/diff-check.log；未改配置/stage/commit或其他Git状态。

只用虚拟bridge/模块，输出没有真实秘密/账目/原始消息/profile/session/db/blob/raw端点。没有Docker/PG/OpenClaw/微信/DeepSeek/provider/网络/系统设置/用户窗口或产品写入。新增本报告、r4-audit.py、r4-delivery.py、r4-vitest.config.mjs、evidence/r4；没有编写或运行后续独立恢复/Windows runner/helper来绕过停止门禁。

交接总控：接收原节点首次复验失败及其观测限制，决定故障命中/完成观测契约；旧LAZY-001尚不能关闭，UI-02设备条件/P4-B未验收。此角色停在 **blocked / finished**，不派发新任务/角色、不自行续跑、不进入P4-C。
