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


## C12-R4 独立追加（2026-10-02）

- [R4报告](phase-4-c12-r4-lazy-windows-report.md)：blocked / finished。原R3-UI-02-LAZY精确节点一次失败，actual alert不存在、Shell/nav/Agent存在；无法确认故障命中/完成，不建议关闭LAZY-001，也不把结果新增定级为产品P1。
- 独立0 passed/1 failed；新增恢复/兼容均not_run。按原失败门禁停止，产品0/8、辅助Electron0/4、Windows chunk注入0；真实Windows/native/人工条件仍未执行。
- 旧OUTBOX/setting/PATH保持关闭，旧27成功与outbox42不重跑；B仍0 passed/1 failed/19 blocked/4 not_run。原首次代码/报告/evidence保持，当前主报告和清单仅追加。
- 首次JSON/log在evidence/r4/original-lazy，静态来源/观察限制在readonly-source-observation.json；交总控裁定有限测试观察契约，未改产品或Git。


## C12-R4-R1 可观察复验追加（2026-10-02）

- [R4-R1报告](phase-4-c12-r4-r1-observation-windows-report.md)：blocked / finished。新OBS节点一次0 passed/1 failed，确认mock factory1、#/daily，但5016ms仍无alert；Shell/nav/Agent在，原四条要求不降级，旧R4首次失败不改写。
- 原因不再能直接归于200ms，当前预期错误终态/错误传播原因仍unverified，不新增未经定位产品P1、不建议关闭LAZY-001。真实root卸载/订阅2→0/DOM/global清理有首次回执。
- 后续独立恢复/兼容/Windows未执行，产品0/8、辅助0/4、chunk注入0；旧已通过outbox/setting/path不重跑。B仍0 passed/1 failed/19 blocked/4 not_run，人工条件保持。
- 新首次log/JSON与observation-receipts在evidence/r4-r1，原所有资料不变；交总控裁定有限观察/核对范围，不改产品或Git、不自行续跑。


## C12-R4-R2 冷入口复验追加（2026-10-03）

- [R2独立报告](phase-4-c12-r4-r2-cold-entry-windows-report.md)：blocked / finished；A唯一一次0 passed/1 failed，B及后续not_run，LAZY-001未关闭。
- main/act完成，同一Router1的attempt1被取消后安全拒绝、attempt2未取消成功resolve，活跃目标idle/errors0，无alert；Shell/nav/Agent三断言通过，不能把取消错误补签为当前有效请求故障。
- 本次未建立活跃请求错误前置，不新增已定级产品P0/P1；第二次import解析原因仍unverified，交总控裁定测试接线。不继续延时/预热/重打包，不重跑首次结果。
- 产品0/8、辅助0/4、chunk注入0；系统枚举CimException明确未核实全树，已登记CLI/worker结束、真实root及订阅清理有记录。旧证据和24项原要求保持，人工条件不要求现在操作。


## C12-R4-R3 持续导入复验追加（2026-10-03）

- [R3报告](phase-4-c12-r4-r3-persistent-import-windows-report.md)：blocked / finished；P工具前置1 passed，真实默认loader两并发及随后3/3safe reject，零import ESM求值1/精确映射1；不是网络chunk404或UI通过。
- 全新A首次停在worker_start/journal_ready，正文/main/fixture/loader均0，CLI14595ms硬限定向收口；无runner JSON，四原断言not_run，不编造failed产品节点。B、恢复、兼容和Windows未执行，产品0/8、辅助0/4。
- 没有明确纯工具配置错误，不消耗额外前置worker盲重试；原P/A首次材料完整保留，LAZY-001/UI-02/P4-B未关闭，无新增产品缺陷。已登记CLI/worker结束，完整系统后代枚举CimException保持unverified。
- 原24项完整预期/历史保持，普通静态映射修正1与目标更正0分列；用户继续后的长可见性空档如实记录。交总控review后停止，不自动续跑。


## C12-R5-PUBLIC 公开冷入口追加（2026-10-04）

- [R5-PUBLIC报告](phase-4-c12-r5-public-windows-report.md)：blocked / finished；公开B独立启动，不依赖A。唯一新CLI/worker停在jsdom_import_enter缺少terminal，initialization_blocked；正文/main/fixture0，四断言not_run，没有runner JSON或产品failed节点。
- 主进程启动→初始化收口14953ms，process15113ms、controller_finished15120ms；正文/观察/UI cleanup未开始，自有CLI/登记worker已结束。worker exit code unknown，完整系统后代未核实；缓存未生成/未删除，首次六文件及10源码保留。
- 来源与公开结果都未计算，P旧成功只读不补签；恢复/兼容/剩余公开/Windows停止，产品0/8、辅助0/4、网络chunk注入0。普通静态谓词更正1、额外worker/目标重试0；根因unknown不作为工具重试授权。
- 原24项要求与状态保持，LAZY-001/UI-02/P4-B未关闭。只交总控review，不改产品/依赖/Git、不自动启动A或新任务。


## P4-C12-R6-ENV 增量（2026-10-04）

- [R6独立报告](phase-4-c12-r6-env-windows-report.md)：原生固定jsdom已返回；公开B首次1/1 passed，main1/fixture1、四原断言4/4、同次来源/安全/清理通过。旧R5初始化阻塞证据不倒写。
- 同任务已继续独立恢复，首场景出现AssertionError，runner1 failed；具体比较值未留存，产品归因unverified，第2～5场景及相邻兼容/Windows未执行。目标已进入，不自动重跑。
- root/worker均已退出，界面卸载/退订/global/console/DOM实际清理；全系统历史后代及worker自身exit code未核实。缓存仅清理本轮专属路径，首次材料保留。
- B整项0 passed/1 failed/19 blocked/4 not_run保持；Windows0/8、辅助0/4、真实chunk0。实际Tray、老化原生提示、session/系统注销/启动项/多屏/OS主题等原缺口保持，不要求用户现在操作。
- blocked / finished，供总控review；LAZY-001/UI-02/P4-B未关闭，未修改产品/依赖或Git，不进入P4-C/D。


## P4-C12-R7-RECOVERY 增量（2026-10-12）

- [R7增量报告](phase-4-c12-r7-recovery-windows-report.md)：新恢复合同1节点5/5组通过、208正式比较通过；两个旧计数对照为expected1/actual2、expected2/actual3，旧R6失败保留。独立结构8 passed，必要开发兼容10 passed单列；R6公开冷B不重跑。
- 真实固定EXE首次W1运行，13比较passed/1观察failed；首ID W1-DAILY-PAGE expected=true actual=unknown，5000ms等待没有页面就绪样本。真实后端online/认证/canonical模块、安全窄bridge/CSP部分通过；未取得页面初读模块/终态DOM，根因和产品定级unverified。
- 产品1/8、辅助0/4、chunk注入0。首错后停止动态扩大，root3448按已验证身份定向收口，8登记进程与监听均无；这是强制清理，不是正常关闭/Tray通过。虚拟加密profile/db仅在本轮C:/MarisC12专属根保留，仓库无原文。
- 原24项整项状态保持：B0 passed/1 failed/19 blocked/4 not_run；真实session重启、原生老化提示、关闭策略/单实例、OS注销/启动项/多屏/主题等缺口未通过，不要求用户立即操作。R7首次材料和新命名/取证限制详见报告，交付blocked / finished供总控review；不自动复跑或进入后续场景。


## P4-C12-R8-MODULES 增量（2026-10-13）

- [R8报告](phase-4-c12-r8-modules-windows-report.md)：提交总控review，blocked / finished。新818起点与R6源码/包/依赖已绑定；独立首次runner9 passed/1 failed/3 not_run，393正式比较passed。R8-10为测试辅助重复断言ID中断（R8-TOOL-ID-001），非新增产品缺陷；部分模块移除观察不代表节点通过。
- 已取得普通/Strict空列表→同值就绪通知、已就绪启动、晚快照、同步通知、突发合并/旧列表、拒绝保页及同集合retry+1/状态保持证据。旧冷B/完整R7不重跑，旧W1原因仍unverified；jsdom样式可见性与真实Windows分别统计。
- 目标已进入后不能修后重跑，保留首次源码/日志。后3节点、开发兼容28和Windows均not_run；产品0/8、辅助0/4、chunk0。root30140/worker22216实际exit1、无强杀/超时，真实卸载/退订/global恢复通过。
- 原24项仍0 passed/1 failed/19 blocked/4 not_run；所有Tray、真实session/同ID重启、老化原生提示、设备条件继续未验证。无新外部profile或OS/用户操作，不请求即时点击；原预期及历史材料保持。


## R8-R1 独立续验增量（2026-10-14）

[R8-R1增量报告](phase-4-c12-r8-r1-modules-windows-report.md)：新4独立节点、28必要兼容、6剩余公开节点通过。旧R8九节点保留而不重跑。固定新包W1真实日常页及一次recover后页面通过；quit关闭策略出现P1 `P4-C12-R8-R1-QUIT-001`，正常关闭请求已发出但10秒后root及自有后端仍在，安全值expected=true/actual=false。

已停止后续Windows/辅助场景。产品1/8、辅助0/4；测试方按核实所有权定向强制清理后登记对象0/监听0，不将此写作产品正常退出通过。虚拟根和首次证据保留。原人工范围仍未授权：OS注销/重启、启动项、OS主题、多屏/DPI。真实Tray/其他关闭策略、原生老化保留与明确删除、跨重启session/同ID、真实chunk故障均不得由本轮部分通过代签；待总控处理P1并授权后再按原清单执行，本轮没有要求用户点击。

矩阵仅B实际状态更新为1passed、3failed、17blocked、3not_run：UI-01 passed；CMP-03及SUP-05正常退出子条件failed；旧UI-02 failed保留。SUP-05的注销等人工子条件仍not_run。测试角色blocked/finished，交总控review，不自行关闭LAZY-001或P4-B。


## R9-QUIT 独立退出复验与剩余条件（2026-10-16）

[R9增量报告](phase-4-c12-r9-quit-windows-report.md)：独立退出8节点/235条正式比较、指定48项开发兼容及新包W1的62条比较通过。普通主窗口WM_CLOSE后约480ms自然exit0，3082ms时自有进程/监听/窗口均0，没有退出计时器或强制结束。建议关闭QUIT-001普通关闭逻辑；旧R8-R1首次失败和所有历史记录保留。

W1之后同任务继续H1辅助，实际启动前清单摘要列误读使用本卡唯一工具更正，后续H1首次启动发生未知ownership观察错误，解密和fixture写入未进入。按任务卡停止动态扩大；辅助定向强制清理后自有对象/监听/窗口归零，不写为产品正常退出或safeStorage通过。累计产品1/8、辅助1/4。W2以后跨重启session/设置/同ID、原生提示/Tray、老化保留/删除及剩余owned故障条件未执行；实际chunk注入0。未要求用户点击、修改启动项/主题/多屏或注销系统。

矩阵SUP-05/CMP-03正常退出子条件通过，整项改blocked；B为1passed、1failed、19blocked、3not_run。UI-01既有通过保持，UI-02/LAZY-001和P4-B尚未完整验收。测试角色完成报告及终点核对后停在blocked/finished，交总控review；本轮不修改产品、不重打包、不Git写入、不自行启动其他角色。


## R9-R1 H1观察工具续验（2026-10-17）

[R9-R1增量报告](phase-4-c12-r9-r1-h1-windows-report.md)：1017起点全匹配，固定包/依赖和旧首次证据通过复核。复制63项W1关闭后的同内容虚拟profile到新根，尚未启动续验。12条虚拟工具检查及1条更正参数检查通过；首次现场工具控制器因脚本身份路径参数不匹配退出，使用唯一目标前更正后仍出现scriptArgumentEqual expected=true/actual=false，其余三个身份比较true；observer实际exit3/controller exit1。保留两次首次材料，按卡停止，不将工具失败写为产品缺陷或设备不支持。

H1恢复、后续W2/W3及原生保留/删除等全部not_run；新产品0/7、辅助0/4，跨R9累计产品1/8、辅助1/5。旧失败H1及旧工具更正不抹除。R9独立8/235、48兼容、W1/62仅历史复用，不重跑。新/原profile均未解密或seed，未要求用户点击，未操作OS主题、启动项、多屏或注销。

B仍1passed、1failed、19blocked、3not_run；UI-01通过保持，QUIT-001普通关闭范围已由总控关闭，其余条件不扩大通过。测试角色blocked/finished交总控review，不自行续跑或修改产品/依赖/包/Git。


## R9-R2路径身份与H1续验追加（2026-10-18）

[R9-R2报告](phase-4-c12-r9-r2-path-windows-report.md)：1077起点通过，纯工具两轮36/38均通过（最终38唯一检查），唯一Node现场身份/resources通过。完整H1控制器与共享argv/绝对路径/摘要/ready/cancel链已在现场前冻结；H1实际身份/ready/release通过、原生availability=true，随后owner读取/解密/解析区间operation_error，helper/controller真实exit1。native分步回执及原生错误码未留存，原因unverified，不定级产品缺陷、不判设备不支持。

H1约8.207秒自然异常退出，无强制结束，最终owned/监听/窗口0，profile原字节保持。按正式目标停止规则，不执行W2等后续、不修后重跑。产品新增0/7，辅助新增1/4，系列累计1/8及2/5；H1恢复1/1已用，现场更正0/1不能用于目标失败。旧8/235、48、W1/62及模块/冷B/完整恢复只引用。

原R9/R9-R1两份profile只读，新63项同内容副本不等于产品续启通过；未seed，owner/outbox基线、同ID重启、真实保留/删除/Tray等仍未验。B整项仍1passed/1failed/19blocked/3not_run。人工条件保持，未要求用户立即操作。blocked/finished交总控review，无产品/依赖/包/Git写，不启动其他角色。


## R9-R3同源H1与W2首次恢复失败（2026-10-18）

[R9-R3独立增量报告](phase-4-c12-r9-r3-storage-windows-report.md)：1192起点匹配；唯一局部工具轮30/30通过。预置同源Local State、ready前绑定userData/sessionData并分段记录后，新H1原生7/7、helper/controller exit0、产品副本63项保持及资源全零。该成功不倒推旧operation_error精确阶段。

随后同任务唯一W2在首次设置界面比较失败：保存dark/隐私true，实际页面system/off、主题控件system/隐私checkbox false；设置取样前未写入且字节不变。登记P1 P4-C12-R9-R3-SETTINGS-001，四比较来自同一首样。产品普通WM_CLOSE后自然exit0、owned/listener/window=0，无强制结束；controller exit1保留失败。W3、H2、W4/H3、W5/H4、W6及剩余原生/人工条件not_run，不声称设备不支持。

本轮产品1/7、辅助1/4；系列产品2/8、辅助3/6（含两次旧失败H1）。旧退出/48兼容/W1/模块/冷入口/恢复/38路径及现场Node均未重跑。B为1 passed、2 failed、19 blocked、2 not_run：CMP-06仅因主题恢复子条件改failed，其余设备子条件未验；CMP-05多屏/金额隐藏/键盘等人工条件仍not_run，隐私开关恢复失败单独记录。UI-02/LAZY-001保持。原首次材料和本文旧字节保留，最终blocked / finished供总控review，不请求用户此刻操作。


## P4-C12-R10-SETTINGS 独立增量（2026-11-01）

[R10完整报告](phase-4-c12-r10-settings-windows-report.md)：blocked / finished，交总控review。1381新起点全匹配后接单；固定R8构建1365、产物140、资源67与原W1虚拟profile63匹配，旧资料只读。

独立38节点唯一执行5 passed、1 failed、32 not_run；40条比较39通过。首错R10-I06.DIFFERENT_PORT_REJECTED：开发来源配置为http://127.0.0.1:5173（无尾斜杠）时，实际main新设置getter对http://127.0.0.1:51730/index.html未拒绝，expected=ipc_origin_rejected、actual=null。提出P1 P4-C12-R10-IPC-ORIGIN-001，待总控定级；这是合同反例，不是工具故障/设备不支持，不外推为打包攻击可达或真实数据泄露。

来源失败后停止。新preload/水合32节点、指定两文件48兼容、W2四首样与W3/H2/W4/H3/W5/H4/W6/W7均未执行；SETTINGS-001旧四条失败保持，未建议关闭。设备UIA/Tray/chunk能力未尝试，不选择降级分支、不要求用户立即操作。旧H1、W1、退出/48、模块/冷入口/恢复不重跑。

本轮产品0/6、helper0/3，系列产品2/8、helper3/6；没有新外部profile或数据库。独立CLI root29676/worker3196实际exit1，无超时/强杀，6节点finally均完成。工具17项检查单列；首次UTF8/GBK输入审计错误及新v2保持，不覆写首次源码或正式结果。

矩阵仅SEC-04改failed，B为1 passed、3 failed、18 blocked、2 not_run；原24项完整要求及未验人工范围不变。不修改产品/依赖/包，不安装/打包/Git写入，不关闭P4-B、不自动启动其他角色。
