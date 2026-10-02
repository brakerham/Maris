# P4-C12 Windows Shell 独立验收报告

- 角色：用户启动的既有测试智能体，P4-C12 唯一负责人。
- 控制版本：2026-10-01T14:30:33+08:00；任务卡 `docs/coordination/prompts/p4-c12-windows-shell-tester.md`。
- 执行日期：2026-10-01，Asia/Shanghai；独立测试唯一运行开始 14:50:04，约 2.74 秒，退出码 1。
- 交付状态：**blocked / finished**。发现已实测的 P1 数据丢失缺陷后按任务卡停止；P4-B 未完成，最终裁定属于总控。

## 结论与统计

`P4-C12-OUTBOX-001`：未提交的草稿和队列消息超过 30 天后，应用启动时的 outbox cleanup 不经用户确认自动删除，并把空列表写回持久化存储。违反 IF-003 §10 的“30 天后提示用户确认删除”和 SUP-06 的内容保留合同。虚拟时间边界、密文持久化和重新加载得到独立复现，未修改产品。

| 统计口径 | 实际结果 | 限制 |
| --- | --- | --- |
| 独立公开行为测试节点 | 11 executed：10 passed、1 failed、0 skipped | 模拟 adapter；不是 11 个整项矩阵 passed |
| 原 24 项 P4-B 矩阵 | 0 passed、1 failed、19 blocked、4 not_run | 单项所有子条件必须满足；未冒充全绿 |
| 执行方 LOCALZIP 兼容复跑 | 0/30，未运行 | 严重缺陷停止规则优先；历史 30 passed 只属执行方输入 |
| 独立真实 EXE 场景 | 0/8 产品启动 | 停在动态前，无 CDP、无新 profile 或 Host |
| 本轮人工设备验收 | 0 项 | SUP-05、CMP-04/05/06 维持 not_run；Tray 子项也未实测 |
| 附加 ZIP/staging 独立行为检查 | not_run | 因严重缺陷停止，未继续附加构建检查 |
| 其他切片 | P4-A 64 passed；P4-C/D 32 not_run | 原状态和原案例文本不变 |

没有 harness/preflight 错误：独立配置 Node syntax check 一次通过，runner 首次运行即进入全部 11 个产品公开行为断言。没有失败后重跑、修改断言以转绿或额外产品启动。

## 固定输入与环境

必读的 AGENTS、README、协调规则、control、tester、C12 任务卡、LOCALZIP coordinator review/running、IF-003/004/005、单主人决定和 P4-B 矩阵已读取。IF-004 覆盖供应链/desktop core readiness，IF-005 覆盖诊断/staging，canonical Profile 采用 `daily_finance.assistant@1`。通用 `/readyz` provider fail-closed 不作 desktop core 离线结论。

起点清单 `docs/coordination/snapshots/p4-c12-windows-shell-start.sha256`：277 entries、277 matched、0 mismatch、0 missing；普通 SHA-256 为 `dfcd5a21fc34e36155e90d9fb1862ea878a664d438cf422e0ad8f537e68bc081`；起点 Git staged paths=0。

只读复用 `C:\MarisE5Final\E5-PKG-FINAL-20260929-1732` 的 Node v24.21.0、已安装 Vitest 5.0.2/Zod 与普通 node_modules；没有安装、联网 audit、build、package 或改依赖。Python 使用仓库既有 `.venv`，仅整理证据/报告。独立配置 root、输出和缓存均属于新 `tests/independent/desktop/`。

| 受验文件（clean workspace 下） | 起点及终点 SHA-256 | 状态 |
| --- | --- | --- |
| `apps/desktop/out/Maris-win32-x64/Maris.exe` | `f5cf7ad3b4d89a02cca925152ec8d7b5554ccba6ebff025bf04eb24195405641` | exact matched |
| `apps/desktop/out/Maris-win32-x64/resources/app.asar` | `bcdf6f889a5be95d7270fb249db8eff45b1421a5fdd7879d2342cb333d7f1274` | exact matched |
| `pnpm-lock.yaml` | `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` | exact matched |

旧 LOCALZIP 环境/profile/数据库/session/evidence 和所有旧失败现场只读；没有复用其私密状态或把其动态门禁算成本轮独立证据。

## 首次缺陷：P4-C12-OUTBOX-001

- 严重级别：P1。确定性、无需用户操作的持久化未提交内容丢失；本轮不证明重复真实写账。SUP-06 原矩阵风险 P0 保留，案例风险与本条已证实缺陷分级分开记录。
- 对应接口：IF-003 §10 未提交草稿 30 天后提示确认删除；IF-004/005 未覆盖或撤销该条。
- 产品位置：`apps/desktop/electron/main/outbox.ts` 的 `cleanup()` 用 createdAt cutoff 过滤全部非 terminal 条目，并调用 `#save()`；`apps/desktop/electron/main/index.ts:181` 启动直接 load→cleanup，退出回调也调用 cleanup（约第 89 行）。没有向 cleanup 提供删除确认。
- 可执行独立节点：`tests/independent/desktop/public-boundaries.test.ts` 的 `C12-PUB-11`；失败断言约第 169 行。测试代码没有访问 Electron/Windows，也没有调用 provider。

前置数据仅为两个虚拟条目：一个 draft，一个 queued；时间源从 2026-01-01 UTC 开始。虚拟 AES-GCM adapter 加密存储，clock 与 ID factory 注入公开 outbox constructor。没有真实主人、财务或凭据。

1. prepare 两条；将第一条 setState 为 draft，第二条保持 queued；存下预期正文/digest/clientEventId。
2. 推进 30 天并 cleanup，边界时两条仍在，此断言通过。
3. 再推进 1ms；创建新 outbox，执行公开 load→cleanup，模拟 main 启动调用序列。
4. 再创建第三个 outbox 并 load，检查持久化结果。测试从未提供用户删除确认，也从未发送消息。

预期：未获确认前两条均保留，正文与 clientEventId 不变；需要提示/确认的交互规则由总控冻结接口与执行方实施。本测试不自行定义新提示 UI。

实际脱敏证据：

```json
{"before":2,"after":0,"persisted":0,"statesBefore":["draft","queued"],"elapsedMilliseconds":2592000001,"userDeletionConsent":false,"actualIds":[],"expectedIds":["virtual-event-1","virtual-event-2"]}
```

失败：`AssertionError: expected [] to deeply equal [ { …(7) }, { …(7) } ]`。第一条失败保存在原始 JSON/log；未重跑或覆盖。实际持久化为空，因此不只是 UI 隐藏或 cache 丢失。30 天 + 1ms 是确定性时钟边界，不是等待真实时间。虚拟加密 provider 不冒充 OS DPAPI 验收；该缺陷位于加密之外的筛选规则。

影响：超过 30 天的未提交草稿/排队内容在下一次启动或统一退出清理被自动移除；同一内容重试的原 client_event_id 随条目消失。测试确认了公开逻辑和 main 调用路径，未声称真实 EXE 已进行老化现场验收。

已采取处理：只提交复现与报告，不修产品、不改变冻结、不要求用户立即操作。停止剩余公开行为扩展、执行方复跑和 Windows 动态。解除条件：总控确认缺陷及返修范围，执行方提供新固定快照，之后由单独明确任务安排独立复验和剩余门禁。本测试智能体不创建 C12-R1、不派发其他角色。

## 独立节点与证据

唯一测试命令（应仅在获准复验时重跑，本轮已停止）：

```powershell
& 'C:\MarisE5Final\E5-PKG-FINAL-20260929-1732\tools\node\node.exe' 'C:\MarisE5Final\E5-PKG-FINAL-20260929-1732\workspace\node_modules\vitest\vitest.mjs' run --config tests/independent/desktop/vitest.config.mjs
```

配置 `bail:1`、单 worker、5 秒节点上限。测试不 spawn 产品、无网络、虚拟加密仅内存持久化。并发用例 12 个 prepare 调用验证单条/单 ID；reload、容量和年龄边界检查读取新对象的持久化内容，避免只检查实现返回值。

| 节点 | 观察层/断言 | 实测状态 | 原矩阵映射 |
| --- | --- | --- | --- |
| C12-PUB-01 | SecureStore provider unavailable fail-closed | passed | SEC-05 partial |
| C12-PUB-02 | 虚拟密文 roundtrip、正文无明文、corruption safe error | passed | SEC-05/08 partial |
| C12-PUB-03 | preferences 返回值与生产 CSP 指令 | passed | SEC-01/02 partial |
| C12-PUB-04 | validateIpc sender/frame/origin/strict args | passed | SEC-04 partial |
| C12-PUB-05 | registry 与 Host canonical Profile/version/prefix/settings 交集 | passed | UI-01 partial |
| C12-PUB-06 | 并发相同 draft/body 单 ID/单条 | passed | SUP-06 partial |
| C12-PUB-07 | 加密 reload 后正文/digest/ID 稳定 | passed | SUP-06 partial |
| C12-PUB-08 | sending 后改正文新 ID | passed | SUP-06 partial |
| C12-PUB-09 | 第 21 条拒绝后 reload 保留原 20 条 | passed | SUP-06 partial |
| C12-PUB-10 | terminal 24h 临界和新未提交条目保持 | passed | SUP-06 partial |
| C12-PUB-11 | 未确认删除的老化 draft/queued 经过启动清理仍应持久化 | failed | SUP-06 |

`evidence/public-boundaries.json` 的 assertionResults 是节点计数依据；Vitest JSON 的 suite 计数包含容器层（2 failed suites），不能误读为 2 个失败文件/节点。实际为 1 个文件、11 个断言节点、1 failed。`public-boundaries.log` 保留实际输出，包括仅虚拟数据的失败 diff。所有部分通过均不替代整项原矩阵通过。

## 24 项原案例逐项映射

以下逐项保留原预期原文。输入/原步骤是原设计，不代表均已执行；“本轮实际”与限制决定本轮状态。未执行项目的统一原因是严重缺陷停止门禁，不是环境缺失，也不是对产品能力作失败推断。

### P4B-SEC-01 — blocked

- 原风险/方式/环境：P0 / auto / Windows/Electron。
- 原前置条件：固定 Electron 构建。
- 原输入/步骤：BrowserWindow 配置与运行时 renderer；静态检查并在 renderer 探测。
- **完整原预期**：sandbox/contextIsolation 开启、nodeIntegration 关闭；无 `require/process/fs/child_process` 或任意 preload 对象。
- 本轮实际/证据：C12-PUB-03 实测生产 preferences 函数返回 sandbox/contextIsolation=true、nodeIntegration=false，并检查 webSecurity 等配置。
- 证据层级、未覆盖与限制：独立公开函数；运行时 renderer 的 require/process/fs/child_process 与实际 BrowserWindow 未探测。
- 状态：`blocked`。未取得全部子条件通过证据。

### P4B-SEC-02 — blocked

- 原风险/方式/环境：P0 / auto / Windows/Electron。
- 原前置条件：CSP/导航 allowlist 冻结。
- 原输入/步骤：inline script、data/javascript URL、未知 origin、新窗口、外链；从不可信内容触发导航/打开。
- **完整原预期**：CSP 阻止执行；未知导航/窗口拒绝；获准外链只由 main 安全打开，不加载进应用权限域。
- 本轮实际/证据：C12-PUB-03 实测生产 CSP 字符串不含 unsafe-inline/unsafe-eval，script/connect/object/frame 指令符合断言。
- 证据层级、未覆盖与限制：独立公开函数；未实测 CSP 执行、导航、新窗口和外链 allowlist。
- 状态：`blocked`。未取得全部子条件通过证据。

### P4B-SEC-03 — blocked

- 原风险/方式/环境：P0 / auto / contract。
- 原前置条件：preload 类型合同可导入。
- 原输入/步骤：枚举 contextBridge 暴露对象；与 allowlist 对比并尝试直接 ipcRenderer/send/invoke。
- **完整原预期**：只暴露窄 typed 方法；无通用 channel、Node require、密钥或进程控制。
- 本轮实际/证据：仅只读查看 preload/IPC 分层；未执行 bridge 枚举或尝试通用 send/invoke。
- 证据层级、未覆盖与限制：静态阅读不替代完整 allowlist 行为验收。
- 状态：`blocked`。未取得全部子条件通过证据。

### P4B-SEC-04 — blocked

- 原风险/方式/环境：P0 / auto / Windows/Electron。
- 原前置条件：IPC handlers 已注册。
- 原输入/步骤：伪造 sender、错 origin、额外/错型参数、未知 channel、重复调用；逐项 invoke/send。
- **完整原预期**：sender 与参数双校验；稳定拒绝；不得启动进程、改设置、打开窗口或泄露异常。
- 本轮实际/证据：C12-PUB-04 用虚拟 sender/mainFrame 调用公开 validateIpc，正确请求接受；错误 sender、frame、origin、额外参数、错类型、非法 draft 参数拒绝。
- 证据层级、未覆盖与限制：独立公开函数；未验证真实 IPC handlers、未知 channel、重复事件、全部无副作用条件。
- 状态：`blocked`。未取得全部子条件通过证据。

### P4B-SEC-05 — blocked

- 原风险/方式/环境：P0 / auto / Windows/Electron。
- 原前置条件：假 token 与假 API key。
- 原输入/步骤：localStorage/sessionStorage/IndexedDB/renderer 内存转储、main safeStorage；登录/刷新/重启并检查各层。
- **完整原预期**：refresh/device token 与 API key 只在 main/OS 保护边界；renderer 无持久原文；日志与 crash dump 无值。
- 本轮实际/证据：C12-PUB-01/02 用虚拟 AES-GCM provider 实测 SecureStore 不可用时 fail-closed、密文 roundtrip 和损坏错误。
- 证据层级、未覆盖与限制：独立模拟加密；没有 Windows DPAPI、真实 token/API key、renderer storage/内存、登录刷新或 crash dump 证据。
- 状态：`blocked`。未取得全部子条件通过证据。

### P4B-SEC-06 — blocked

- 原风险/方式/环境：P0 / auto / Windows/Electron。
- 原前置条件：后端绑定随机 loopback port。
- 原输入/步骤：只知道端口、错 nonce、错 origin、过期 access、远程地址；绕过 main 直连 Host。
- **完整原预期**：端口不是认证；nonce/origin/token 均校验；只绑定 loopback，远程连接拒绝。
- 本轮实际/证据：只读查看 Host 接线与 nonce/readiness；未启动后端或绕过 main 连接。
- 证据层级、未覆盖与限制：真实 loopback/nonce/Bearer/origin/远程拒绝全部未执行。
- 状态：`blocked`。未取得全部子条件通过证据。

### P4B-SEC-07 — blocked

- 原风险/方式/环境：P0 / auto / Windows/Electron。
- 原前置条件：模块标签、错误、消息均含虚拟恶意 HTML。
- 原输入/步骤：script/img/event handler/RTL/超长文本；渲染导航、通知、Agent panel、错误。
- **完整原预期**：文本安全编码、布局有界且不执行；不得改变 IPC、模块注册或权限。
- 本轮实际/证据：未渲染恶意 HTML、RTL 或超长文本。
- 证据层级、未覆盖与限制：无 UI 注入执行证据；严重缺陷停止后不扩大测试。
- 状态：`blocked`。未取得全部子条件通过证据。

### P4B-SEC-08 — blocked

- 原风险/方式/环境：P0 / auto / Windows/Electron。
- 原前置条件：可注入 preload/backend/lazy-load 故障。
- 原输入/步骤：内部路径、SQL、堆栈、token canary；触发并查看 UI、console、日志。
- **完整原预期**：用户只见稳定安全错误和 request ID；renderer console/日志无秘密或未授权数据。
- 本轮实际/证据：C12-PUB-02 对密文损坏实测稳定 secure_storage_corrupt。
- 证据层级、未覆盖与限制：该局部异常不等于 UI request ID、preload/backend/lazy 故障、renderer console/日志的完整脱敏验收。
- 状态：`blocked`。未取得全部子条件通过证据。

### P4B-SUP-01 — blocked

- 原风险/方式/环境：P0 / auto / Windows/Electron。
- 原前置条件：supervisor 可记录 PID+nonce。
- 原输入/步骤：自己启动、手工启动、伪造同 PID；请求停止/应用退出。
- **完整原预期**：只停止 PID+nonce 匹配且由本实例启动的子进程；手工/他实例进程保持。
- 本轮实际/证据：只读阅读 supervisor ownership 和 managed Host adapter，未执行 stop。
- 证据层级、未覆盖与限制：PID+nonce 自有/外来进程隔离与 Windows 退出未取得独立证据。
- 状态：`blocked`。未取得全部子条件通过证据。

### P4B-SUP-02 — blocked

- 原风险/方式/环境：P1 / auto / Windows/Electron。
- 原前置条件：端口分配与 ready 协议冻结。
- 原输入/步骤：端口冲突、无 ready、坏 nonce、ready 超时；启动后端。
- **完整原预期**：使用随机可用 loopback 端口；超时进入离线/诊断并清理自有子进程，不把 health 当 ready。
- 本轮实际/证据：只读阅读端口/nonce/readiness 合同和代码；未启动端口冲突或超时场景。
- 证据层级、未覆盖与限制：随机 loopback 端口、坏 nonce、readiness 超时清理未执行。
- 状态：`blocked`。未取得全部子条件通过证据。

### P4B-SUP-03 — blocked

- 原风险/方式/环境：P1 / auto / Windows/Electron。
- 原前置条件：假后端可崩溃。
- 原输入/步骤：启动前崩溃、ready 后崩溃、连续崩溃；观察重启策略。
- **完整原预期**：状态转 offline；重启次数/退避有界，不形成重启风暴或重复 run；用户可恢复。
- 本轮实际/证据：未启动假后端崩溃、恢复退避或真实 EXE。
- 证据层级、未覆盖与限制：offline、限次恢复与无重复 run 的独立断言未执行。
- 状态：`blocked`。未取得全部子条件通过证据。

### P4B-SUP-04 — blocked

- 原风险/方式/环境：P1 / auto / Windows/Electron。
- 原前置条件：已有手动后端或两个 app 启动请求。
- 原输入/步骤：重复启动、开发连接模式；启动/关闭两个客户端。
- **完整原预期**：不产生重复 owned 后端；连接手动后端时不取得停止权；状态可区分。
- 本轮实际/证据：未运行双客户端、启动 single-flight 或 external_dev 连接。
- 证据层级、未覆盖与限制：不从源码推导无重复 owned 后端或手工后端停止权通过。
- 状态：`blocked`。未取得全部子条件通过证据。

### P4B-SUP-05 — not_run

- 原风险/方式/环境：P1 / manual / Windows/Electron。
- 原前置条件：目标 Windows，后端含子线程/连接。
- 原输入/步骤：正常退出、强关主窗口、系统注销；检查进程树/端口/文件锁。
- **完整原预期**：自有后端按冻结时限退出，无僵尸/孤儿/占用端口；未拥有进程不受影响。
- 本轮实际/证据：未进行 Windows 正常退出、强关或注销。
- 证据层级、未覆盖与限制：人工设备条件未执行，详见人工清单；本任务从未拥有产品进程，零启动不能替代 cleanup 验收。
- 状态：`not_run`。未取得全部子条件通过证据。

### P4B-SUP-06 — failed

- 原风险/方式/环境：P0 / auto / Windows/Electron。
- 原前置条件：renderer 有未发送虚拟消息。
- 原输入/步骤：后端离线→恢复、应用重启、重复点击；发送并观察 client_event_id/GET。
- **完整原预期**：未发送内容和同一 ID 保留；恢复后只提交一次；UI 不凭新 ID 制造重复账候选。
- 本轮实际/证据：C12-PUB-06～10 五个局部断言通过：相同内容 12 个并发 prepare 一条/一 ID、加密 reload 稳定、sending 后改正文新 ID、20 条容量拒绝不丢失、terminal 24h 边界。C12-PUB-11：draft/queued 两条保留至 30 天，推进 1ms 后 load→cleanup→再 load 为零条，且无用户删除确认。
- 证据层级、未覆盖与限制：公开 outbox + 虚拟加密/时间/持久化 adapter 的可执行失败；真实 Windows、恢复提交一次、GET 和 UI 状态尚未执行。缺陷 P4-C12-OUTBOX-001，P1；原案例风险仍 P0。
- 状态：`failed`。SUP-06 内容保留子条件已失败，不能以其他通过节点抵消。

### P4B-UI-01 — blocked

- 原风险/方式/环境：P1 / auto / contract。
- 原前置条件：compiled registry 与 `/modules` fixture。
- 原输入/步骤：后端启用/禁用、桌面缺失、版本不兼容、未知模块；计算交集。
- **完整原预期**：只渲染两侧均存在且兼容的模块；未知/禁用不导航、不预加载。
- 本轮实际/证据：C12-PUB-05 用虚拟 canonical contribution 与 Host summary 计算交集；兼容保留，disabled/unknown/major/profile/prefix/settings version 不兼容均过滤。
- 证据层级、未覆盖与限制：独立 registry 函数；实际模块导航和 lazy preload 未验证，不能整项 passed。
- 状态：`blocked`。未取得全部子条件通过证据。

### P4B-UI-02 — blocked

- 原风险/方式/环境：P1 / auto / Windows/Electron。
- 原前置条件：两个 lazy route。
- 原输入/步骤：chunk 加载失败、重试成功、切换模块；导航并恢复。
- **完整原预期**：局部错误边界可重试，Shell/登录/其他模块可用；不循环加载或丢当前会话。
- 本轮实际/证据：只读查看 Shell route 错误边界；未注入 lazy chunk 失败、重试或两个测试 contribution 导航。
- 证据层级、未覆盖与限制：会话保持、局部隔离和其他模块可用没有执行证据。
- 状态：`blocked`。未取得全部子条件通过证据。

### P4B-UI-03 — blocked

- 原风险/方式/环境：P1 / auto / contract。
- 原前置条件：冻结 OpenAPI 与生成命令。
- 原输入/步骤：后端 DTO 字段/枚举/required 改变；生成物陈旧；CI 比较生成差异并编译。
- **完整原预期**：漂移门禁失败并定位；不得靠手写 API 类型掩盖差异或运行时下载 schema。
- 本轮实际/证据：未运行 OpenAPI 漂移 mutation 或生成/编译门禁；生成物保持输入原样。
- 证据层级、未覆盖与限制：没有 DTO 漂移失败定位证据，不将执行方历史类型检查计为独立通过。
- 状态：`blocked`。未取得全部子条件通过证据。

### P4B-UI-04 — blocked

- 原风险/方式/环境：P1 / auto / contract。
- 原前置条件：UI contribution 合同冻结。
- 原输入/步骤：hostUiMajor、route/path/setting/profile/companion 冲突；编译期注册和启动验证。
- **完整原预期**：不兼容或冲突稳定失败；Shell 无 `if moduleId` 业务分支。
- 本轮实际/证据：只读查看 compileRegistry；未运行 hostUiMajor、route/path/setting/profile/companion 冲突断言。
- 证据层级、未覆盖与限制：未执行的静态疑点不登记为产品缺陷；只报告本轮已实测的 outbox 缺陷。
- 状态：`blocked`。未取得全部子条件通过证据。

### P4B-CMP-01 — blocked

- 原风险/方式/环境：P1 / auto / Windows/Electron。
- 原前置条件：daily/wealth contributions 与假状态流。
- 原输入/步骤：切换模块及 idle/thinking/tool/confirmation/error/offline；观察窗口、Profile 和状态。
- **完整原预期**：始终只有一个毛毛窗口/Agent 入口；主形态随 contribution，子状态不创建第二 Agent或触发写入。
- 本轮实际/证据：未启动毛毛窗口或虚拟第二 contribution 状态流。
- 证据层级、未覆盖与限制：单窗口、主形态/子状态分离、无业务写入均未实测。wealth 产品模块未创建。
- 状态：`blocked`。未取得全部子条件通过证据。

### P4B-CMP-02 — blocked

- 原风险/方式/环境：P1 / auto / Windows/Electron。
- 原前置条件：新设备设置。
- 原输入/步骤：首次和第二次关闭主窗口；关闭、从 Tray 恢复、再次关闭。
- **完整原预期**：首次隐藏并只提示一次；第二次不重复提示；Host/毛毛按设置驻留且无数据丢失。
- 本轮实际/证据：未关闭真实主窗口或操作 Tray；新 profile 未创建。
- 证据层级、未覆盖与限制：首次提示、二次不提示、Tray 恢复和 Host/毛毛驻留待后续验收。
- 状态：`blocked`。未取得全部子条件通过证据。

### P4B-CMP-03 — blocked

- 原风险/方式/环境：P1 / auto / Windows/Electron。
- 原前置条件：关闭策略可切换。
- 原输入/步骤：退出/每次询问/隐藏，Tray 打开/隐藏；每种设置执行关闭与取消。
- **完整原预期**：行为精确对应设置；“退出”清理自有后端；询问取消不退出；Tray 状态一致。
- 本轮实际/证据：未执行三种关闭策略、询问取消或 Tray 操作。
- 证据层级、未覆盖与限制：策略行为及自有后端退出未实测；不把 E2E timer 当普通退出策略。
- 状态：`blocked`。未取得全部子条件通过证据。

### P4B-CMP-04 — not_run

- 原风险/方式/环境：P1 / manual / Windows/Electron。
- 原前置条件：新安装测试 profile。
- 原输入/步骤：首次运行、显式启用/禁用开机启动；检查 OS 启动项和 UI。
- **完整原预期**：默认关闭且无启动项；只有明确操作才创建；禁用清理本应用项，不改其他应用。
- 本轮实际/证据：未创建/删除任何 OS 启动项或修改真实 AppData。
- 证据层级、未覆盖与限制：人工未执行；E2E 模式抑制 setLoginItemSettings，不能证明 OS 合同。
- 状态：`not_run`。未取得全部子条件通过证据。

### P4B-CMP-05 — not_run

- 原风险/方式/环境：P1 / manual / external/manual。
- 原前置条件：多显示器/缩放/全屏测试设备。
- 原输入/步骤：拖动、置顶、重启、拔屏、分辨率变化、全屏、隐私、键盘；逐项操作并重启。
- **完整原预期**：位置用临时文件原子替换并恢复/夹取；全屏按规则隐藏；隐私不显示金额；键盘入口可达。
- 本轮实际/证据：未改显示器/缩放/全屏、移动用户窗口或测试设备位置恢复。
- 证据层级、未覆盖与限制：人工多屏、拔屏、隐私、键盘与原子持久化未执行。
- 状态：`not_run`。未取得全部子条件通过证据。

### P4B-CMP-06 — not_run

- 原风险/方式/环境：P2 / manual / external/manual。
- 原前置条件：支持/不支持透明窗口设备。
- 原输入/步骤：透明失败、普通迷你窗降级；light/dark/system/high-contrast/reduced-motion；中外行情色；切换设备条件和主题。
- **完整原预期**：可安全降级且合同不变；文本对比/焦点可辨；reduced motion 生效；收入/支出色不复用涨跌色。
- 本轮实际/证据：未启动透明/降级设备窗口或切换系统主题。
- 证据层级、未覆盖与限制：人工透明失败、对比度、焦点、reduced motion 和颜色语义全部未执行。
- 状态：`not_run`。未取得全部子条件通过证据。

## 运行、收口、隐私与未执行列表

产品 EXE 0/8 次，Host 0 次；没有使用 `_electron.launch`、app.asar loader、PID promotion、inspect fuse 或目标 CDP。没有创建 `C:\MarisC12` 新 profile/evidence/db，没有外部目录写入审批需要，没有真实 AppData 写入。唯一 runner 子进程已退出 1；没有本任务产品进程/窗口/端口/文件锁需要终止。这里的零资源只说明未启动，**不证明** SUP-05 cleanup 或 Tray/OS 行为通过。

缓存仅在新独立目录 `.cache`，终点核对绝对路径后清除；JSON/log 和 baseline/audit 证据保留。旧证据/profile/session/db 未删除、重置或修改。

未执行：HostClient/session/supervisor 的进一步独立 adapter 测试、settings/lifecycle、registry conflict/lazy-route/schema drift、ZIP 显式无效值/长度/摘要、staging 原子性/禁止文件、执行方 30 项兼容，以及所有真实 EXE/人工场景。本轮只读审查发现但未执行的疑点不另报缺陷。没有 Docker/PostgreSQL、OpenClaw、微信/扫码、DeepSeek、真实 provider 或 P0～P3 全量回归。

隐私：输入仅 `VIRTUAL_*` 文本、虚拟 ID/模块、随机内存加密 key；没有真实 token、API key、账号、个人财务数据、profile/session/db 原件或 crash dump。日志的 product/source/toolchain 路径是定位证据，不是用户个人资料。没有触发未受控弹窗或未知 ownership。

Warning：只读 Git 命令提示用户全局 Git ignore 无读取权限；命令退出 0、staged=0。未修改 Git 配置或修复用户目录权限。此 warning 不归为产品缺陷。`git diff --check` 退出 0，另有既有 LF→CRLF 提示，未改变 Git 设置。

源码支持的 MARIS_E2E_EXIT_MS 范围实际为 1000～30000ms（index.ts 约第 190 行），任务卡每场景总预算为 120s；两者须区分。后续不得把 30s 自动退出当普通 close policy，或为延长观察修改产品。本轮未设置任何 E2E 参数。

过程记录限制：报告编写期间角色文件心跳从 14:51 到 15:23 未按 10 分钟刷新，最终已补记；期间持续产出矩阵、报告与人工清单，不属于连续两检查点无新输出。严重缺陷后的测试扩展始终停止，产品未启动。该心跳延迟不影响已保存的首次失败，但属于本轮进度记录不足。

## 终点边界与交付

终点 277 entries：**276 unchanged、1 authorized changed、0 unauthorized mismatch、0 missing**；清单内唯一变化是 P4-B 矩阵。tester 状态不在该固定清单中，其作为第二个授权更新路径另行核对。清单普通 SHA-256 不变；固定 EXE/asar/lock 三项保持原摘要；Git staged paths=0。复算证据为 `tests/independent/desktop/evidence/final-input-audit.json`，只读 verifier 为 `audit_inputs.py`。

原矩阵 120 个唯一 ID、12 字段；P4-B 原前 11 列和原预期逐项不变，只有状态和 B 段必要证据备注改变。B 段之前/之后的字节内容与独立保存的起点摘要完全一致；P4-A 64 passed、P4-C/D 32 not_run 未改。

本轮新增交付：

- `docs/testing/phase-4-c12-windows-shell-report.md`（本报告）。
- `docs/testing/phase-4-c12-manual-checklist.md`（未执行设备场景与后续证据需求）。
- `tests/independent/desktop/public-boundaries.test.ts`、`vitest.config.mjs`、`audit_inputs.py`。
- `tests/independent/desktop/evidence/public-boundaries.json`、`public-boundaries.log`、`matrix-original-cases.json`、`final-input-audit.json`、`delivery-verification.json`。

更新交付：P4 矩阵仅 B 段；测试智能体自身状态/日志。无产品、执行方测试、依赖/lock、冻结、snapshot、control/overview、其他角色、OpenClaw 或 Git 写操作。

下一步交给总控：确认 P1 缺陷和草稿删除确认合同的返修边界，安排执行方修复与新快照，然后指定复验和剩余 Windows/人工门禁。人工清单不要求用户现在注销、改显示器或改启动项。本轮安全停在 `blocked / finished`，不宣布 P4-B complete，不继续 P4-C。

## C12-R1 独立复验追加（2026-10-02）

原正文、首次10 passed/1 failed、OUTBOX-001缺陷和2→0证据保持历史原样。新版本与任务见 [C12-R1独立报告](phase-4-c12-r1-outbox-windows-report.md)。

- 原PUB-11不变断言一次通过：30天+1ms后持久化仍2条，正文/digest/原ID保持；[新输出](../../tests/independent/desktop/evidence/r1/original-node/run.log)与[result](../../tests/independent/desktop/evidence/r1/original-node/result.json)。
- 原其他10项、新outbox26、新可执行main5均通过。建议总控关闭原P1 OUTBOX-001公开持久删除逻辑；真实Windows老化原生提示仍unverified，SUP-06仅改blocked，不整项passed。
- 本轮独立60个唯一执行节点：59 passed、1 failed；执行方定向27 passed另列。
- 新P1 P4-C12-R1-REGISTRY-001：跨module相同setting key仍接受，违反IF-003 §5全局唯一；[首次新失败](../../tests/independent/desktop/evidence/r1/matrix-independent/run.log)。UI-04变failed，其他不完整案例仍blocked/manual not_run。
- R1整体blocked / finished，P4-B仍0 passed、1 failed、19 blocked、4 not_run；产品0/8、辅助Electron0/4，未进入Windows，不用原执行方EXE证据代替独立通过。
- 原8项测试/首次交付不变，新清单/产物和授权边界见R1审计。本轮没有修产品或Git写操作，交回总控返修registry并安排剩余验收。


## C12-R2 独立追加（2026-10-02）

- [R2完整报告](phase-4-c12-r2-registry-windows-report.md)：blocked / finished。原setting REGISTRY-001不变断言一次通过、独立相邻共15 passed；新P1 P4-C12-R2-REGISTRY-PATH-001，同路径不同route ID仍accepted:2，首次失败已保留。开发26 passed单列，不抵消路径失败。
- P4-B仍0 passed、1 failed、19 blocked、4 not_run；UI-04 failed原因现为path冲突，旧setting首次失败保持历史原样；OUTBOX-001关闭及旧outbox42证据不重复。
- 产品0/8、辅助Electron0/4，因新P1停止。真实老化原生提示unverified，Windows/Tray/启动项/多屏/主题等原人工步骤继续not_run，未要求用户立即操作；未执行设置/安全/HTML/lazy/generated/ZIP/staging新门禁。
- 证据：`tests/independent/desktop/evidence/r2/original-registry/`及`remaining-independent/`首次log/JSON；原文prefix、旧R1报告/evidence不改写。没有产品或Git写操作，交总控裁定。


## C12-R3 独立追加（2026-10-02）

- [R3完整报告](phase-4-c12-r3-route-windows-report.md)：blocked / finished。原PATH-001不变断言及新路径9通过，建议关闭；新P1 P4-C12-R3-LAZY-001：lazy import故障后整个Shell/nav/Agent入口消失，首次证据在evidence/r3/remaining-independent，未重跑或修产品。
- 独立28 unique：27 passed/1 failed；开发registry52 passed单列。设置3/ZIP6/staging7通过限逻辑证据；产品0/8、辅助Electron0/4，Windows未执行。
- UI-02现failed；UI-04路径问题复验通过但完整独立复核未完成为blocked，P4-B仍0 passed/1 failed/19 blocked/4 not_run。旧OUTBOX/setting保持关闭，旧outbox42/setting节点不重复。
- 真实native dialog unverified、Tray/启动项/注销/多屏/主题人工步骤原样保留未执行，不要求用户即时动作。旧正文prefix和旧R1/R2报告/evidence保持。交总控裁定新lazy故障，测试角色停止。
