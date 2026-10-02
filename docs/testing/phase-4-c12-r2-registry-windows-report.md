# P4-C12-R2 registry 独立复验与 Windows 验收报告

- 控制版本：2026-10-02T15:22:00+08:00；角色：既有独立测试智能体、唯一负责人。
- 任务卡：`docs/coordination/prompts/p4-c12-r2-registry-windows-tester.md`。
- 交付：**blocked / finished**。原设置键缺陷建议关闭；新 P1 路由路径冲突导致按任务卡停止扩展。P4-B 不 complete，最终接受属于总控。

## 实测结论与独立统计

原 `P4-C12-R1-REGISTRY-001` 的 R1-SHELL-13 原断言唯一一次通过，旧测试及首次失败证据完全未改。相邻 registry 六节点和新独立八节点通过；但 UI-04 完整契约中的 path 冲突首次失败。不能由设置键修复或开发测试全绿推导 UI-04 passed。

| 分组 | 实际结果 | 本轮证据（tests/independent/desktop/evidence/r2/ 下） |
| --- | --- | --- |
| 原R1-SHELL-13不变断言、唯一一次 | 1 passed | original-registry/result.json、run.log |
| 原R1-SHELL-10/11/12、排除13和其他旧节点 | 6 passed | adjacent-original/result.json、run.log |
| 新双顺序/schema/同模块重复/合法键/失败恢复 | 8 passed | registry-independent/result.json、run.log |
| 新UI-04 path边界首次复现 | 1 failed | remaining-independent/result.json、run.log |
| 独立合计 | **16 unique executed：15 passed、1 failed** | node-index.json；filter未选节点不算实际执行 |
| 开发registry兼容、唯一一次 | **26 passed**，单列 | executor-compat/result.json、run.log |
| P4-B整项24 | **0 passed、1 failed、19 blocked、4 not_run** | 局部成功不替代整项/设备条件 |
| 产品 / 辅助Electron启动 | **0/8 / 0/4** | 因新P1停止，非环境或审批失败 |

未重复已通过的outbox42、旧60、Host/session/supervisor或完整开发98；没有Python/数据库全量、安装、下载、build或package。五组各只执行一次，原失败复验、相邻原节点、新registry、开发兼容四组退出0；随后路径组退出1。配置无失败/修正重试。所有命令已返回，无活动session。失败非harness故障，原断言没有放宽。

## 新P1：P4-C12-R2-REGISTRY-PATH-001

- 依据：原矩阵 P4B-UI-04 明列 `hostUiMajor、route/path/setting/profile/companion 冲突`，预期不兼容或冲突稳定失败；IF-003 §5 全局route唯一且任一冲突不部分加载。IF-004/005及当前control没有撤销此条件。
- 前置：两个各自合法的纯虚拟 contribution，moduleId 为 virtual_left/virtual_right；version=1.0.0、hostUiMajor=1。Profile、route ID、setting key、appearance和API prefix分别不同；只有路径均为 `/virtual_shared`。不创建第二产品业务模块。
- 操作：`r2-remaining.test.ts` 中 `R2-UI-04-PATH` 调用公开 compileRegistry 一次并记录返回/异常。
- 预期：整体拒绝，稳定错误 desktop_registry_conflict。
- 实际：无异常，返回两个贡献；控制台 `actual: accepted:2`，断言退出1。
- 严重级别：**P1**，与UI-04原风险一致；路径冲突未在编译注册期fail closed，破坏模块路由唯一性和启动边界。没有声称真实daily_finance导航误路由、财务损失或权限利用已发生，未执行实际renderer验证。
- 最小复现、日志与JSON：`tests/independent/desktop/r2-remaining.test.ts`；`evidence/r2/remaining-independent/run.log`、`result.json`。首次现场永久保留，不修改产品、不重跑覆盖。

```json
{"caseId":"R2-UI-04-PATH","path":"/virtual_shared","routeIds":["virtual_left_route","virtual_right_route"],"expected":"desktop_registry_conflict","actual":"accepted:2","data":"virtual_only"}
```

复现命令（仅供总控复算，不表示授权本测试角色重跑）：

```powershell
$env:C12_R2_PHASE='remaining-independent'
& 'C:/MarisRegistryR3/R3-20261002-111556/tools/node/node.exe' 'C:/MarisRegistryR3/R3-20261002-111556/workspace/node_modules/vitest/vitest.mjs' run --config tests/independent/desktop/r2-vitest.config.mjs
```

原REGISTRY-001独立关闭建议限于设置键：跨模块不同顺序、同/异schemaVersion均拒绝，同模块重复拒绝，不同全局键合法；冻结输入未修改，没有部分返回，失败后合法compile仍成功。UI major/ASCII/SemVer、module/Profile/route ID/appearance相邻冲突拒绝也通过。**设置键修复通过与路径新失败分别记录，不能抵消。** Shell无具体moduleId业务分支及真实启动/导航仍未完整独立验收。

## 固定输入及审计

起点327/327 matched，0 missing/mismatch；清单 `docs/coordination/snapshots/p4-c12-r2-start.sha256` SHA-256为 `0547e289b34619b491478fedc153a3f0c169635550ab9d4f881343ce1d613b9b`，staged=0。只读根 `C:\MarisRegistryR3\R3-20261002-111556`；固定Node24.21.0及已有Vitest5.0.2，配置cache与结果仅写本轮evidence/r2。旧R3/R2/LOCALZIP用户现场不复用、不写。

| 文件（只读根workspace下） | 起终固定SHA-256 |
| --- | --- |
| apps/desktop/out/Maris-win32-x64/Maris.exe | 1df694c0ca39818d1b2af7aad09eefa13383af186a8d0638d96a13882d604a94 |
| apps/desktop/out/Maris-win32-x64/resources/app.asar | 64f84ddde164c4dea81ab3fcb6933728eda5acf3cfe4917828fe0f4f6dc3e161 |
| pnpm-lock.yaml | 5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a |

终点已用新增 `r2-delivery.py verify` 复算通过：**327 entries：323 unchanged、4 authorized changed、0非授权变更、0缺失；staged=0**。32项旧独立材料全部不变，包含旧R1测试/evidence；旧C12-R1报告及所有首次失败证据保持。EXE/asar/lock与固定起点相同，EXE fuse wire前六项48/49/48/48/49/49保持。旧主报告/人工清单原byte prefix精确保留，matrix B外prefix/suffix不变，120唯一ID/12列/原B前11列不变，A64 passed、C20/D12 not_run保持。实测证据为 evidence/r2/end-audit.json、delivery-verification.json。

定向 `git diff --check` 退出0，仅报告四个既有文档的LF→CRLF提示；没有改Git配置或执行Git写操作。新增报告和测试在独立终点交付摘要中逐文件记录，快照冻结集之外的新增交付不伪装为起点文件。

## 原24项完整映射

“已有部分”引自只读C12-R1报告，仅表明输入未变部分的历史证据，未重复执行；所有旧证据摘要在终点复算。每项保留完整原预期、具体缺口和状态，不把静态/单元或兼容证据代替设备验收。

### P4B-SEC-01 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：固定 Electron 构建。
- 输入：BrowserWindow 配置与运行时 renderer。
- 步骤：静态检查并在 renderer 探测。
- **完整原预期**：sandbox/contextIsolation 开启、nodeIntegration 关闭；无 `require/process/fs/child_process` 或任意 preload 对象。
- 已有部分（C12-R1历史证据，未重跑）：原 PUB-03 在新依赖下再次通过；R1-MAIN-01 实际导入main但窗口是虚拟adapter。
- 本次新执行：未新增执行；新P1停止规则生效。
- 证据层级与具体缺口：生产 preferences逻辑有证据；实际EXE renderer Node isolation未执行。
- 当前状态：`blocked`，未完整验收不能写passed。

### P4B-SEC-02 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：CSP/导航 allowlist 冻结。
- 输入：inline script、data/javascript URL、未知 origin、新窗口、外链。
- 步骤：从不可信内容触发导航/打开。
- **完整原预期**：CSP 阻止执行；未知导航/窗口拒绝；获准外链只由 main 安全打开，不加载进应用权限域。
- 已有部分（C12-R1历史证据，未重跑）：原 PUB-03 CSP字符串再次通过；main安全默认/导航接线只读。
- 本次新执行：未新增执行；新P1停止规则生效。
- 证据层级与具体缺口：未在真实页面触发 inline/data/javascript、导航/new-window和外链。
- 当前状态：`blocked`，未完整验收不能写passed。

### P4B-SEC-03 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / contract/unit / contract / auto。
- 前置：preload 类型合同可导入。
- 输入：枚举 contextBridge 暴露对象。
- 步骤：与 allowlist 对比并尝试直接 ipcRenderer/send/invoke。
- **完整原预期**：只暴露窄 typed 方法；无通用 channel、Node require、密钥或进程控制。
- 已有部分（C12-R1历史证据，未重跑）：R1-SHELL-09实际导入main preload，capture contextBridge，枚举六组窄API/冻结对象，尝试读取通用invoke/send/ipcRenderer/require/process等均undefined，调用typed方法验证固定channel。companion preload只读为getState/openMain。
- 本次新执行：未新增执行；新P1停止规则生效。
- 证据层级与具体缺口：main preload契约部分通过；未执行companion暴露对象与整个renderer域，保守保持blocked。
- 当前状态：`blocked`，未完整验收不能写passed。

### P4B-SEC-04 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：IPC handlers 已注册。
- 输入：伪造 sender、错 origin、额外/错型参数、未知 channel、重复调用。
- 步骤：逐项 invoke/send。
- **完整原预期**：sender 与参数双校验；稳定拒绝；不得启动进程、改设置、打开窗口或泄露异常。
- 已有部分（C12-R1历史证据，未重跑）：原 PUB-04 sender/frame/origin/严格参数拒绝再次通过；R1 main导入注册真实handlers。
- 本次新执行：未新增执行；新P1停止规则生效。
- 证据层级与具体缺口：未对注册handler执行未知channel/重复/全部无副作用断言或真实Electroninvoke。
- 当前状态：`blocked`，未完整验收不能写passed。

### P4B-SEC-05 — blocked

- 来源/风险/层/环境/方式：F07/F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：假 token 与假 API key。
- 输入：localStorage/sessionStorage/IndexedDB/renderer 内存转储、main safeStorage。
- 步骤：登录/刷新/重启并检查各层。
- **完整原预期**：refresh/device token 与 API key 只在 main/OS 保护边界；renderer 无持久原文；日志与 crash dump 无值。
- 已有部分（C12-R1历史证据，未重跑）：原PUB-01/02虚拟加密失败闭合/损坏/密文通过；R1-SHELL-05虚拟owner bootstrap/refresh/revoke通过，R1-OB容量/密文逻辑保持。
- 本次新执行：未新增执行；新P1停止规则生效。
- 证据层级与具体缺口：非Windows safeStorage；未检查真实renderer storage/内存、secret/crash dump或OS DPAPI。
- 当前状态：`blocked`，未完整验收不能写passed。

### P4B-SEC-06 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / API/integration / Windows/Electron / auto。
- 前置：后端绑定随机 loopback port。
- 输入：只知道端口、错 nonce、错 origin、过期 access、远程地址。
- 步骤：绕过 main 直连 Host。
- **完整原预期**：端口不是认证；nonce/origin/token 均校验；只绑定 loopback，远程连接拒绝。
- 已有部分（C12-R1历史证据，未重跑）：R1-SHELL-01拒绝非HTTP127.0.0.1 endpoint；02 main-only Bearer与并发401刷新；07 managed坏nonce拒绝。
- 本次新执行：未新增执行；新P1停止规则生效。
- 证据层级与具体缺口：HTTP为fake fetch，nonce为fake child；实际随机监听/origin/access到期/远程连接未运行。
- 当前状态：`blocked`，未完整验收不能写passed。

### P4B-SEC-07 — blocked

- 来源/风险/层/环境/方式：F11/F12 / P0 / security/manual / Windows/Electron / auto。
- 前置：模块标签、错误、消息均含虚拟恶意 HTML。
- 输入：script/img/event handler/RTL/超长文本。
- 步骤：渲染导航、通知、Agent panel、错误。
- **完整原预期**：文本安全编码、布局有界且不执行；不得改变 IPC、模块注册或权限。
- 已有部分（C12-R1历史证据，未重跑）：未做恶意文本UI渲染。
- 本次新执行：未新增执行；新P1停止规则生效。
- 证据层级与具体缺口：真实HTML/RTL/长文本编码布局与无脚本执行证据缺失。
- 当前状态：`blocked`，未完整验收不能写passed。

### P4B-SEC-08 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / desktop/e2e / Windows/Electron / auto。
- 前置：可注入 preload/backend/lazy-load 故障。
- 输入：内部路径、SQL、堆栈、token canary。
- 步骤：触发并查看 UI、console、日志。
- **完整原预期**：用户只见稳定安全错误和 request ID；renderer console/日志无秘密或未授权数据。
- 已有部分（C12-R1历史证据，未重跑）：原PUB-02 corruption安全错误；R1-SHELL-03/04在401刷新失败、503、非法DTO、network异常下安全error不含虚拟canary；R1-OB-07 dialog rejection无raw console输出。
- 本次新执行：未新增执行；新P1停止规则生效。
- 证据层级与具体缺口：未实测实际UI/request ID/preload/lazy故障或真实console/log/crash dump。
- 当前状态：`blocked`，未完整验收不能写passed。

### P4B-SUP-01 — blocked

- 来源/风险/层/环境/方式：D9 BackendSupervisor / P0 / desktop/e2e / Windows/Electron / auto。
- 前置：supervisor 可记录 PID+nonce。
- 输入：自己启动、手工启动、伪造同 PID。
- 步骤：请求停止/应用退出。
- **完整原预期**：只停止 PID+nonce 匹配且由本实例启动的子进程；手工/他实例进程保持。
- 已有部分（C12-R1历史证据，未重跑）：R1-SHELL-07错误managed nonce拒绝并清理候选；08external observed child shutdown不调用stop/forceStop。
- 本次新执行：未新增执行；新P1停止规则生效。
- 证据层级与具体缺口：虚拟adapter；真实PID/nonce、外来同PID和进程树隔离未执行。
- 当前状态：`blocked`，未完整验收不能写passed。

### P4B-SUP-02 — blocked

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：端口分配与 ready 协议冻结。
- 输入：端口冲突、无 ready、坏 nonce、ready 超时。
- 步骤：启动后端。
- **完整原预期**：使用随机可用 loopback 端口；超时进入离线/诊断并清理自有子进程，不把 health 当 ready。
- 已有部分（C12-R1历史证据，未重跑）：R1-SHELL-07坏nonce fail-closed且不进入ready；06成功fake ready。
- 本次新执行：未新增执行；新P1停止规则生效。
- 证据层级与具体缺口：端口冲突、ready总超时、随机loopback和真实自有清理未覆盖，不能把health当ready。
- 当前状态：`blocked`，未完整验收不能写passed。

### P4B-SUP-03 — blocked

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：假后端可崩溃。
- 输入：启动前崩溃、ready 后崩溃、连续崩溃。
- 步骤：观察重启策略。
- **完整原预期**：状态转 offline；重启次数/退避有界，不形成重启风暴或重复 run；用户可恢复。
- 已有部分（C12-R1历史证据，未重跑）：R1-SHELL-06 fake child exit→offline，recover退避1/2/4秒、三次上限，第四次exhausted，shutdown阻止再start。
- 本次新执行：未新增执行；新P1停止规则生效。
- 证据层级与具体缺口：注入delay/child，不是Windows真实崩溃；启动前崩溃、健康循环与全部UI状态未覆盖。
- 当前状态：`blocked`，未完整验收不能写passed。

### P4B-SUP-04 — blocked

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：已有手动后端或两个 app 启动请求。
- 输入：重复启动、开发连接模式。
- 步骤：启动/关闭两个客户端。
- **完整原预期**：不产生重复 owned 后端；连接手动后端时不取得停止权；状态可区分。
- 已有部分（C12-R1历史证据，未重跑）：R1-SHELL-06并发start/recover single-flight不增重复start；08external不启动owned也无停止权。
- 本次新执行：未新增执行；新P1停止规则生效。
- 证据层级与具体缺口：未执行双真实客户端/单实例EXE场景。
- 当前状态：`blocked`，未完整验收不能写passed。

### P4B-SUP-05 — not_run

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / security/manual / Windows/Electron / manual。
- 前置：目标 Windows，后端含子线程/连接。
- 输入：正常退出、强关主窗口、系统注销。
- 步骤：检查进程树/端口/文件锁。
- **完整原预期**：自有后端按冻结时限退出，无僵尸/孤儿/占用端口；未拥有进程不受影响。
- 已有部分（C12-R1历史证据，未重跑）：真实退出、强关和注销均未执行；R1-MAIN-02/03仅虚拟Hostshutdown/窗口destroy。
- 本次新执行：未新增执行；新P1停止规则生效。
- 证据层级与具体缺口：manual not_run；无owned资源仅表示没启动，不能推断cleanup通过。
- 当前状态：`not_run`，未完整验收不能写passed。

### P4B-SUP-06 — blocked

- 来源/风险/层/环境/方式：D9 offline recovery / P0 / desktop/e2e / Windows/Electron / auto。
- 前置：renderer 有未发送虚拟消息。
- 输入：后端离线→恢复、应用重启、重复点击。
- 步骤：发送并观察 client_event_id/GET。
- **完整原预期**：未发送内容和同一 ID 保留；恢复后只提交一次；UI 不凭新 ID 制造重复账候选。
- 已有部分（C12-R1历史证据，未重跑）：原PUB-11不变断言1 passed，原其他10再次通过；新增R1-OB26覆盖持久保留/确认/身份/故障/容量，加R1-MAIN5实际main接线。建议关闭原OUTBOX-001的公开持久化P1。
- 本次新执行：未新增执行；新P1停止规则生效。
- 证据层级与具体缺口：真实老化原生提示unverified、恢复后GET/只提交一次与实际UI缺失；整项从failed改blocked，原P0风险不变。
- 当前状态：`blocked`，未完整验收不能写passed。

### P4B-UI-01 — blocked

- 来源/风险/层/环境/方式：F12 / P1 / contract/unit / contract / auto。
- 前置：compiled registry 与 `/modules` fixture。
- 输入：后端启用/禁用、桌面缺失、版本不兼容、未知模块。
- 步骤：计算交集。
- **完整原预期**：只渲染两侧均存在且兼容的模块；未知/禁用不导航、不预加载。
- 已有部分（C12-R1历史证据，未重跑）：原PUB-05canonical registry/Host交集再次通过，R1-SHELL-10两纯测试contribution正常compile。
- 本次新执行：原R1-SHELL-10及新R2-REG-03合法贡献compile通过；真实Host交集/导航不重复且未新执行。
- 证据层级与具体缺口：实际导航/preload未运行；没有创建真实第二产品模块。
- 当前状态：`blocked`，未完整验收不能写passed。

### P4B-UI-02 — blocked

- 来源/风险/层/环境/方式：F12 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：两个 lazy route。
- 输入：chunk 加载失败、重试成功、切换模块。
- 步骤：导航并恢复。
- **完整原预期**：局部错误边界可重试，Shell/登录/其他模块可用；不循环加载或丢当前会话。
- 已有部分（C12-R1历史证据，未重跑）：未执行两个lazy routes的chunk故障/局部retry。
- 本次新执行：未新增执行；新P1停止规则生效。
- 证据层级与具体缺口：Shell/会话/其他模块保留和无循环未验证。
- 当前状态：`blocked`，未完整验收不能写passed。

### P4B-UI-03 — blocked

- 来源/风险/层/环境/方式：F12 / P1 / contract/unit / contract / auto。
- 前置：冻结 OpenAPI 与生成命令。
- 输入：后端 DTO 字段/枚举/required 改变；生成物陈旧。
- 步骤：CI 比较生成差异并编译。
- **完整原预期**：漂移门禁失败并定位；不得靠手写 API 类型掩盖差异或运行时下载 schema。
- 已有部分（C12-R1历史证据，未重跑）：生成物和OpenAPI保持冻结输入，没有运行生成/类型漂移mutation。
- 本次新执行：未新增执行；新P1停止规则生效。
- 证据层级与具体缺口：未取得失败定位或CI drift独立证据。
- 当前状态：`blocked`，未完整验收不能写passed。

### P4B-UI-04 — failed

- 来源/风险/层/环境/方式：F12 / P1 / contract/unit / contract / auto。
- 前置：UI contribution 合同冻结。
- 输入：hostUiMajor、route/path/setting/profile/companion 冲突。
- 步骤：编译期注册和启动验证。
- **完整原预期**：不兼容或冲突稳定失败；Shell 无 `if moduleId` 业务分支。
- 已有部分（C12-R1历史证据，未重跑）：R1-SHELL-11四种module/profile/route ID/appearance冲突拒绝，12不兼容major和非canonical输入拒绝；13跨module相同setting key仍接受两模块，首次失败。
- 本次新执行：原13一次通过；原10/11/12六通过、新registry八通过；R2-UI-04-PATH失败。开发26仅兼容。
- 证据层级与具体缺口：setting缺陷建议关闭；path同路径不同route ID首次失败，登记新P1；Shell无具体module分支与实际启动/导航未完整验收。
- 当前状态：`failed`，未完整验收不能写passed。

### P4B-CMP-01 — blocked

- 来源/风险/层/环境/方式：F13；U02 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：daily/wealth contributions 与假状态流。
- 输入：切换模块及 idle/thinking/tool/confirmation/error/offline。
- 步骤：观察窗口、Profile 和状态。
- **完整原预期**：始终只有一个毛毛窗口/Agent 入口；主形态随 contribution，子状态不创建第二 Agent或触发写入。
- 已有部分（C12-R1历史证据，未重跑）：R1-MAIN-01虚拟BrowserWindow构造仅Maris和毛毛，Host启动不被dialog等待。
- 本次新执行：未新增执行；新P1停止规则生效。
- 证据层级与具体缺口：实际单毛毛/Agent入口、contribution主形态和完整子状态流未运行。
- 当前状态：`blocked`，未完整验收不能写passed。

### P4B-CMP-02 — blocked

- 来源/风险/层/环境/方式：U01/F13 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：新设备设置。
- 输入：首次和第二次关闭主窗口。
- 步骤：关闭、从 Tray 恢复、再次关闭。
- **完整原预期**：首次隐藏并只提示一次；第二次不重复提示；Host/毛毛按设置驻留且无数据丢失。
- 已有部分（C12-R1历史证据，未重跑）：未执行真实close/Tray恢复/提示一次场景。
- 本次新执行：未新增执行；新P1停止规则生效。
- 证据层级与具体缺口：虚拟ready-to-show retention不等于首次close提示；真实设备not_run子项保持。
- 当前状态：`blocked`，未完整验收不能写passed。

### P4B-CMP-03 — blocked

- 来源/风险/层/环境/方式：U01 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：关闭策略可切换。
- 输入：退出/每次询问/隐藏，Tray 打开/隐藏。
- 步骤：每种设置执行关闭与取消。
- **完整原预期**：行为精确对应设置；“退出”清理自有后端；询问取消不退出；Tray 状态一致。
- 已有部分（C12-R1历史证据，未重跑）：未测试三种closePolicy与询问取消/Tray；R1-MAIN before-quit仅退出接线。
- 本次新执行：未新增执行；新P1停止规则生效。
- 证据层级与具体缺口：不以mock app.quit或E2E timer当生产关闭策略证明。
- 当前状态：`blocked`，未完整验收不能写passed。

### P4B-CMP-04 — not_run

- 来源/风险/层/环境/方式：U05 / P1 / security/manual / Windows/Electron / manual。
- 前置：新安装测试 profile。
- 输入：首次运行、显式启用/禁用开机启动。
- 步骤：检查 OS 启动项和 UI。
- **完整原预期**：默认关闭且无启动项；只有明确操作才创建；禁用清理本应用项，不改其他应用。
- 已有部分（C12-R1历史证据，未重跑）：未创建/删除OS启动项；main fixture app.setLoginItemSettings是mock。
- 本次新执行：未新增执行；新P1停止规则生效。
- 证据层级与具体缺口：manual not_run；E2E抑制启动项不等于OS合同通过。
- 当前状态：`not_run`，未完整验收不能写passed。

### P4B-CMP-05 — not_run

- 来源/风险/层/环境/方式：F13 / P1 / desktop/e2e / external/manual / manual。
- 前置：多显示器/缩放/全屏测试设备。
- 输入：拖动、置顶、重启、拔屏、分辨率变化、全屏、隐私、键盘。
- 步骤：逐项操作并重启。
- **完整原预期**：位置用临时文件原子替换并恢复/夹取；全屏按规则隐藏；隐私不显示金额；键盘入口可达。
- 已有部分（C12-R1历史证据，未重跑）：未修改显示器/缩放/全屏/窗口坐标或测试隐私键盘。
- 本次新执行：未新增执行；新P1停止规则生效。
- 证据层级与具体缺口：manual not_run；settings原子保存/重启夹取也未取得本轮独立证据。
- 当前状态：`not_run`，未完整验收不能写passed。

### P4B-CMP-06 — not_run

- 来源/风险/层/环境/方式：U02；主题要求 / P2 / desktop/e2e / external/manual / manual。
- 前置：支持/不支持透明窗口设备。
- 输入：透明失败、普通迷你窗降级；light/dark/system/high-contrast/reduced-motion；中外行情色。
- 步骤：切换设备条件和主题。
- **完整原预期**：可安全降级且合同不变；文本对比/焦点可辨；reduced motion 生效；收入/支出色不复用涨跌色。
- 已有部分（C12-R1历史证据，未重跑）：未启动透明/降级窗口或切换系统主题。
- 本次新执行：未新增执行；新P1停止规则生效。
- 证据层级与具体缺口：manual not_run；真实对比度/焦点/reduced motion/颜色语义未测试。
- 当前状态：`not_run`，未完整验收不能写passed。

## 停止、Windows预算、隐私和交接

15:41:51路径组开始，首次失败后停止扩展；产品0/8、辅助Electron0/4，未创建外部C12-R2 profile/db/session/safeStorage fixture，没有CDP/UIA、原生dialog、实际Tray/closePolicy/窗口/后端或OS动作。无owned进程、端口、窗口需要关闭源于未启动，不能计作SUP-05清理通过；没有全局kill或用户即时操作请求。

剩余设置原子保存/恢复、真实安全/恶意文本布局、lazy route、生成物漂移、ZIP边界、staging故障原子性均因新P1未执行；真实managed/auth/recover/GET一次提交/毛毛主链路、单实例、Tray和closePolicy未执行。原生老化提示保留unverified；注销/重启/实际开机启动项、多屏/拔屏/主题/透明降级等人工条件仍not_run，完整旧清单保持并追加R2现状。没有使用开发EXE19 gates冒充独立设备通过。

只用虚拟module/key/path数据，控制台不含秘密、真实财务、消息、session/db/blob/raw endpoint。没有Docker/PG/OpenClaw/微信/DeepSeek/provider、网络、系统设置、Git写入或产品修改。只清理新r2 cache/compat-cache并验证绝对范围/无链接；结果/日志/审计永久保留。旧profile/cache/evidence不清理。

新增独立交付：本报告；r2-vitest.config.mjs、r2-compat-vitest.config.mjs、r2-registry.test.ts、r2-remaining.test.ts、r2-delivery.py；evidence/r2起终审计、五组首次log/JSON、node-index、matrix-baseline及delivery verification。没有Windows runner/helper执行交付，因新P1停止动态前。更新仅旧主报告/人工清单追加、matrix B备注、自身角色日志。

交接总控：独立建议关闭原设置键REGISTRY-001，接收新路径P1最小复现并裁定后续；本轮不派发返修/新任务、不修改接口、不进入P4-C、不自行续跑。停在 **blocked / finished**。
