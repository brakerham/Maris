# P4-C12-R10-SETTINGS 独立验收报告

2026-11-01，Asia/Shanghai。唯一负责人：测试智能体。结论：**blocked / finished，提交总控 review**。首个正式产品合同失败后停止，不关闭 SETTINGS-001、LAZY-001 或整个 P4-B。

## 实际结果

本轮独立计划 38 节点，唯一一次执行为 **5 passed、1 failed、32 not_run**；40 条正式比较中 39 passed、1 failed，40 对 enter/terminal 完整且 ID 唯一。新增设置读取在开发来源校验上存在反例，登记 **P4-C12-R10-IPC-ORIGIN-001，建议 P1，待总控裁定**。这是实际 main 注册的新 getter 的合同失败，不是测试工具错误、设备能力缺失，也不是旧 W2 的再次执行。

首次材料：[正式结果](../../tests/independent/desktop/evidence/r10-settings/independent/result.json)、[逐条断言](../../tests/independent/desktop/evidence/r10-settings/independent/journal.jsonl)、[进程回执](../../tests/independent/desktop/evidence/r10-settings/independent/process.json)、[停止回执](../../tests/independent/desktop/evidence/r10-settings/stop-receipt.json)。未执行的节点只能作为设计与源码交付，不是通过证据。

指定的 `settings-snapshot.test.ts` / `settings-hydration.test.tsx` 两文件 48 项兼容、原 W2 四条真实页面断言、W3/H2/W4/H3/W5/H4/W6/W7 **均未执行**。第一阶段未全过，后续放行条件不成立；没有调整顺序、减少节点或重跑以获取绿色结果。

## 输入、时间与隔离

- 指令版本 `2026-10-31T23:15:00+08:00`；以 R10 新卡为准，旧 R9 系列保持停止。接单时间 `2026-10-31T23:20:09.101239+08:00`，此前 1,381 项全匹配、staged=0，见[原接单回执](../../tests/independent/desktop/evidence/r10-settings/repository-gate.json)。清单 SHA-256：`7ebea7c1cd0866623acd4ffcdbeb7df0ff1cab25c96db2ee5b1c0fee66280ed8`。
- 接单后到 11 月 1 日恢复执行控制存在可见性间隔，不补造这段时间的工作、心跳或产品启动。恢复时控制版本未变；受验原项仅 tester 的授权接单更新。
- 固定根 `C:/MarisSettingsR8/R8-20261019-103900`；构建 1,365、产物 140、Python 资源 67 全匹配；EXE、asar、lock 和 R8-R2 closeout 摘要匹配，见[固定输入核对](../../tests/independent/desktop/evidence/r10-settings/fixed-input-audit.json)。受验产品源码来自本轮已匹配仓库，包未执行。
- 实际使用或预定的 14 个工具入口按历史冻结清单核对，Node 24.21.0、Python 3.14.7、Electron 44.4.5、Playwright 1.63.0；完整历史依赖审计只引用，不重新遍历 12,677 项。详见[入口证据](../../tests/independent/desktop/evidence/r10-settings/tool-entries.json)。
- 原 W1 根的 profile/continuity 63 项只读匹配；旧 H1 result 摘要 `f6c493c244f18832b0e69e5fa7c45a09108e304bd72fb685951c92252b7a62e3` 匹配。没有复制或运行新的 Windows profile，没有读取或解密真实个人数据，没有 H1 重跑。

## 目标前准备及首次工具错误

只读输入审计首次使用 Windows 默认 GBK 读取 UTF-8 清单，产生 `UnicodeDecodeError`。错误发生在正式测试或产品启动前，v1 源码与安全回执保留于 [preparation-v1](../../tests/independent/desktop/evidence/r10-settings/preparation-v1/result.json)。新 v2 仅显式指定 UTF-8，受验清单与输入未改。这不计产品缺陷，也不覆写首份文件。

必要记录器与配置以 v2 完成，17 项虚拟检查通过：[工具结果](../../tests/independent/desktop/evidence/r10-settings/preflight-v2/result.json)。覆盖安全标量、比较 ID 唯一/重复拒绝、首次比较错误保留、缺失/坏结果、finally 释放且不由清理错误覆盖首错、短写完整性、两份 TS/TSX 语法和 38 唯一计划节点。另完成 PowerShell 解析与三个 MJS 语法检查。工具检查没有导入产品或启动 Electron，不作为独立产品通过数。

沿用既有独立 R9 的外部边界 fixture，仅为本轮补 mainFrame、真实 handler 注册捕获及开发来源输入；没有运行任何旧退出业务断言。[适配差异](../../tests/independent/desktop/evidence/r10-settings/main-fixture-adaptation.diff)明确范围。实际 main、validateIpc、security、严格 schema、composition、retention、companion 控制逻辑仍使用产品源码；OS、持久化和 Host 端口使用虚拟输入。没有 mock 掉被验的 getter 或来源校验。

UI 计划使用已通过的 native `createRequire` 装配 jsdom，新的虚拟 bridge getter 只是本轮输入适配，不改旧文件。38 节点及 8 份实际来源在 `2026-11-01T09:38:58.488605+08:00` 冻结，[冻结记录](../../tests/independent/desktop/evidence/r10-settings/independent-freeze.json)、[来源清单](../../tests/independent/desktop/evidence/r10-settings/independent-source.sha256)。必要工具计时记录为 09:34:25 至冻结约 273 秒，目标前 2/3 版本；此前只读审计错误另列，未接近 30 分钟上限。正式失败后不修改冻结源码或再次运行目标。

本轮未到 Windows 工具阶段，因此老化提示、关闭对话框、Tray、原生 H2/H3/H4 及真实 chunk 操作能力均为 **unverified / not_attempted**，未选择任何“设备不支持”的降级分支，也没有将未准备或未验证的工具视为可用。

## 新缺陷的最小复现与边界

**P4-C12-R10-IPC-ORIGIN-001：开发来源按字符串前缀匹配，新增设置 getter 接受不同端口。** 建议严重级别 P1（桌面 IPC 信任来源合同失效），最终定级归总控。原矩阵 SEC-04 的风险列 P0 保持，不将该列直接当作本反例已证明的影响。

前置为纯虚拟、未打包 main fixture，`MAIN_WINDOW_VITE_DEV_SERVER_URL = "http://127.0.0.1:5173"`（无尾斜杠）；getter 真实注册，sender 为实际 fixture 主窗口 webContents，senderFrame 为同一个 mainFrame。受信同源 `http://127.0.0.1:5173/index.html` 调用已先取得合法 `theme=dark`。

唯一反例操作：将该 mainFrame 的受测 URL 输入设为 `http://127.0.0.1:51730/index.html`，对真实注册的 `settings:get-snapshot@1` handler 传零参数。两个 URL 的端口不同，属于不同 origin；参数和窗口身份保持不变。

| 首次断言 ID | 期望 | 实际 | 分类 |
| --- | --- | --- | --- |
| `R10-I06.TRUSTED` | `dark` | `dark` | passed；同源正对照 |
| `R10-I06.DIFFERENT_PORT_REJECTED` | `ipc_origin_rejected` | `null`：调用没有抛出拒绝异常 | failed；首个有效产品比较 |

`null` 是本测试 `failure()` 返回“未抛异常”的明确值，不是未观察、丢失输出或 unknown。失败于 `2026-11-01T09:39:09.768+08:00`，原始 journal 第 104 条保留具体比较；随后只执行 finally 收尾。I06 后置 NO_SAVE 未到达，不补写为通过。

只读原因定位：[security.ts](../../apps/desktop/electron/main/security.ts) 的 `isTrustedRenderer` 对 developmentOrigin 使用 `url.startsWith(developmentOrigin)`；[ipc-contract.ts](../../apps/desktop/electron/main/ipc-contract.ts) 从该函数取得 origin 判定；[main/index.ts](../../apps/desktop/electron/main/index.ts) 的真实 registerMainHandler 将当前开发来源传入该校验。由于 `51730` 以 `5173` 为前缀，该反例被放行。测试没有重写这些函数或将其源字符串作为行为结果。

依据为 SETTINGS-R8 第 1 条及 IF-003 §4“错误 origin 一律拒绝”。建议返修保持原接口，仅精确验证受信来源；测试方没有实施修复或派发其他角色。

**影响限界：**本次证明的是带上述合法开发来源配置的真实 IPC handler 校验反例。没有启动开发服务器或 EXE，没有证明打包生产场景可达、实际导航绕过、任意 IPC 调用、token/owner 泄露或真实个人数据曝光。该缺陷利用了既有 security 路径，不能断言是 R8 新增的实现回归；它由本轮新增 getter 独立验收暴露。它也不等同于 SETTINGS-001 仍然发生，后者的新包 W2 尚未复验。

## 独立、兼容与资源分别记录

| 范围 | 实际结果 | 覆盖与限制 |
| --- | --- | --- |
| R10-I01 | passed，9 比较 | loaded 三字段投影、新对象、外部修改不污染、读取无副作用 |
| R10-I02 | passed，9 比较 | 原 update 三字段、accepted 回执、一次保存、禁止扩大字段 |
| R10-I03 | passed，9 比较 | getter 八种非零参数形状拒绝，无保存 |
| R10-I04 | passed，5 比较 | other sender、subframe、companion 拒绝，无保存 |
| R10-I05 | passed，6 比较 | 五种生产非信任来源拒绝，无保存 |
| R10-I06 | failed，2 比较 | 同源正对照通过，不同端口前缀反例失败 |
| R10-I07 | not_run | 新 preload getter 与 companion 暴露对象待执行 |
| R10-U01～U16 | not_run | 四主题 × 隐私布尔 × reducedMotion 布尔的合法恢复 |
| R10-U17～U24 | not_run | 非法枚举/类型/缺失/额外字段/null/数组 |
| R10-U25～U31 | not_run | pending、拒绝、StrictMode、卸载、通知/recover、空模块、故障页面不隐式重试 |
| 开发两文件 48 项 | not_run | 尚未满足独立全过门禁，执行方既有通过只引用 |
| Windows W2～W7 / H2～H4 | not_run | 第一阶段停止，真实页面与后台均无本轮新证据 |

独立 CLI root 29676 和登记 worker 3196 实际均 exit1，signal 不适用（Windows Process 退出回执没有单独 signal 字段，未补造）。控制器进程结束为 exit1；测量 2,331ms，无 timeout、无强制结束，stdout/stderr 读取完成。6 个已进入节点 finally 均成功，firstError 为 comparison，0 unhandled/module errors。清理成功不抵消产品断言失败。

资源结论限于已登记测试 root/worker 及 fixture 清理；未进行全机历史后代/窗口/监听枚举，不把未查询写成全系统资源零。没有新产品/原生 helper/Host、外部 profile 或数据库，本轮无需 compose down、终止产品或删除外部目录；生成的本轮测试缓存与证据保留。

| 启动预算 | 本轮新增 / 授权 | 系列累计 / 上限 |
| --- | --- | --- |
| 产品 EXE | 0 / 6 | 2 / 8 |
| 原生 helper | 0 / 3 | 3 / 6 |
| H1、安装、package | 0 / 0 | 不增加旧预算 |
| 正式独立 Vitest | 1 次；未重跑 | 不混入产品/helper 额度 |

## 原 24 项完整要求与状态

下表按原矩阵完整预期逐项列出，历史证据只引用、不计本轮重跑。SEC-04 因本次来源反例由 blocked 改 failed；B 为 **1 passed、3 failed、18 blocked、2 not_run**。UI-01 既有通过保持；UI-02 和 CMP-06 历史 failed 保持。120 唯一 ID、12 列、风险、原预期及 A/C/D 不变。

| ID | 原完整预期与禁止副作用 | 当前状态 | 历史 / 本轮 / 剩余条件 |
| --- | --- | --- | --- |
| P4B-SEC-01 | sandbox/contextIsolation 开启、nodeIntegration 关闭；无 `require/process/fs/child_process` 或任意 preload 对象 | blocked | 历史有真实窄bridge/隔离局部证据；本轮未增加renderer运行时隔离；完整探测仍缺。 |
| P4B-SEC-02 | CSP 阻止执行；未知导航/窗口拒绝；获准外链只由 main 安全打开，不加载进应用权限域 | blocked | 历史CSP/新窗部分证据保持；本轮未做真实导航/外链；完整CSP与导航组合仍缺。 |
| P4B-SEC-03 | 只暴露窄 typed 方法；无通用 channel、Node require、密钥或进程控制 | blocked | 本轮I07未运行；旧窄bridge局部证据保持，新getter白名单实际preload仍待独立检查。 |
| P4B-SEC-04 | sender 与参数双校验；稳定拒绝；不得启动进程、改设置、打开窗口或泄露异常 | failed | 本轮I01～I05通过；I06不同开发端口来源错误接受，新增IPC-ORIGIN-001；Windows可达性、未知channel等完整组合未验。 |
| P4B-SEC-05 | refresh/device token 与 API key 只在 main/OS 保护边界；renderer 无持久原文；日志与 crash dump 无值 | blocked | 旧H1仅原生owner/outbox有限读取通过；本轮未解密/续启，renderer存储/内存、session与完整日志边界仍缺。 |
| P4B-SEC-06 | 端口不是认证；nonce/origin/token 均校验；只绑定 loopback，远程连接拒绝 | blocked | 本轮没有Host或HTTP；历史nonce部分证据不替代错token、远程与绕过组合。 |
| P4B-SEC-07 | 文本安全编码、布局有界且不执行；不得改变 IPC、模块注册或权限 | blocked | 本轮未渲染页面；HTML/RTL/长文本安全与布局完整条件未验。 |
| P4B-SEC-08 | 用户只见稳定安全错误和 request ID；renderer console/日志无秘密或未授权数据 | blocked | 本轮记录器脱敏仅工具证据；U非法响应/拒绝错误未运行，产品UI/console/log完整故障组合仍缺。 |
| P4B-SUP-01 | 只停止 PID+nonce 匹配且由本实例启动的子进程；手工/他实例进程保持 | blocked | 历史owned清理部分证据保持；本轮无Host或产品，手工/外来/伪造PID对照仍缺。 |
| P4B-SUP-02 | 使用随机可用 loopback 端口；超时进入离线/诊断并清理自有子进程，不把 health 当 ready | blocked | 历史online部分证据保持；本轮无后端，端口冲突、坏ready、超时等仍缺。 |
| P4B-SUP-03 | 状态转 offline；重启次数/退避有界，不形成重启风暴或重复 run；用户可恢复 | blocked | 本轮W6 not_run；真实崩溃/退避/恢复预算和UI保持仍待验。 |
| P4B-SUP-04 | 不产生重复 owned 后端；连接手动后端时不取得停止权；状态可区分 | blocked | 本轮W3 not_run；第二实例与external_dev对照仍缺。 |
| P4B-SUP-05 | 自有后端按冻结时限退出，无僵尸/孤儿/占用端口；未拥有进程不受影响 | blocked | QUIT-001普通关闭范围历史已关闭；本轮仅测试CLI退出，无产品普通关闭、强关、注销/外来对照新增证据。 |
| P4B-SUP-06 | 未发送内容和同一 ID 保留；恢复后只提交一次；UI 不凭新 ID 制造重复账候选 | blocked | 旧H1草稿基线只引用；本轮W2/H2及老化保留删除未运行，同ID续启/重提、一次提交与GET仍缺。 |
| P4B-UI-01 | 只渲染两侧均存在且兼容的模块；未知/禁用不导航、不预加载 | passed | 既有独立模块交集及真实日常页范围已接受；本轮未重跑，passed保持。 |
| P4B-UI-02 | 局部错误边界可重试，Shell/登录/其他模块可用；不循环加载或丢当前会话 | failed | 历史LAZY-001整项failed保持；U31与W6 chunk/retry/session未运行，不凭执行方或旧局部通过关闭。 |
| P4B-UI-03 | 漂移门禁失败并定位；不得靠手写 API 类型掩盖差异或运行时下载 schema | blocked | 旧DTO静态部分证据保持；本轮无新真实export/CI漂移证据。 |
| P4B-UI-04 | 不兼容或冲突稳定失败；Shell 无 `if moduleId` 业务分支 | blocked | 旧冲突修复与注册结构部分证据保持；完整启动/业务分支组合无本轮增量。 |
| P4B-CMP-01 | 始终只有一个毛毛窗口/Agent 入口；主形态随 contribution，子状态不创建第二 Agent或触发写入 | blocked | 本轮无实际窗口；完整毛毛状态流、第二contribution与单一Agent/无写入仍缺。 |
| P4B-CMP-02 | 首次隐藏并只提示一次；第二次不重复提示；Host/毛毛按设置驻留且无数据丢失 | blocked | W7未运行；原生首次提示、第二次关闭、真实Tray恢复及状态连续性仍缺。 |
| P4B-CMP-03 | 行为精确对应设置；“退出”清理自有后端；询问取消不退出；Tray 状态一致 | blocked | 普通quit历史已通过；W6/W7未运行，hide/ask/cancel/Tray完整条件仍缺。 |
| P4B-CMP-04 | 默认关闭且无启动项；只有明确操作才创建；禁用清理本应用项，不改其他应用 | not_run | 本轮未操作OS启动项；默认关闭、显式启禁及仅影响本应用的人工条件仍未验。 |
| P4B-CMP-05 | 位置用临时文件原子替换并恢复/夹取；全屏按规则隐藏；隐私不显示金额；键盘入口可达 | not_run | 本轮W2隐私首样及UI水合未运行；多屏/DPI/位置/拔屏/全屏/隐私金额/键盘等原人工条件保持未验。 |
| P4B-CMP-06 | 可安全降级且合同不变；文本对比/焦点可辨；reduced motion 生效；收入/支出色不复用涨跌色 | failed | 旧W2主题恢复failed保持；本轮U合法恢复与W2未运行，透明/降级/OS主题/对比/焦点/动效/颜色完整条件仍未验。 |

## 交接、未执行条件与完整性

SETTINGS-001 的关闭需要本轮独立水合及原 W2 四条真实首样证据，目前两者都未执行，不能建议关闭。原 W2 `dark/on/dark/true` 的四条期望不变，旧 `system/off/system/false` 首次材料保持。旧 H1 7/7、W1/退出边界、旧 48 兼容、模块 13、冷入口 B、完整恢复、注册/outbox 集合仅历史引用，无重复执行。

后续需总控核定本次来源反例、明确返修或范围裁定，并提供可继续的固定输入与任务；本角色不自行缩小来源断言以绕过失败，不恢复旧 R9 卡，也不自行重启 R10 剩余节点。剩余产品 6/helper 3 并未消费，不代表自动获得新尝试。

本轮未要求用户点击、扫码或调整电脑，没有真实 DeepSeek/provider、Docker、OpenClaw/微信、个人财务数据、OS 注销/重启、时钟、主题、安全设置、多屏或启动项操作。没有安装、打包、产品/依赖/包修改、Git 写操作或其他角色启动。真正 P4-C 开始前的参考图与模型分工提醒仍按总控门禁保留。

终点核对和最终交付清单在以下追加实际回执；原主报告和人工清单只追加，不覆写旧首次结果。

## 最终核对与交付回执

[终点审计](../../tests/independent/desktop/evidence/r10-settings/end-audit.json)于2026-11-01 09:43:53～09:43:56执行，实际exit0。1,381个起点原项中1,377保持，变化准确为tester、原C12主报告、人工清单、P4矩阵四份授权文档，没有其他原项漂移。固定构建1,365/产物140/资源67、EXE/asar/lock、R8-R2 closeout及实际工具入口14均匹配；未重复全量依赖扫描。

旧首次材料R9/R1/R2/R3分别68/38/89/148项匹配。旧R9、R1、R2虚拟profile各63项，旧R3在失败W2后的profile65项，均大小/摘要/完整库存一致且无reparse；没有回写旧现场。本轮首次材料29项、正式来源8份及归档8份保持。

矩阵120唯一ID、12列、原预期/风险及A/C/D保持，整行唯一变化SEC-04的执行状态；B计数1/3/18/2。主报告与人工清单的旧字节前缀完整。只读Git差异检查exit0、staged=0；四条stderr为既有LF将转换为CRLF的行尾提示，不代表本轮执行了Git写操作。新增工具源码的文本检查单列于[交付文本检查](../../tests/independent/desktop/evidence/r10-settings/delivery-text-check.json)，不依靠Git已跟踪文件检查覆盖未跟踪文件。

最终[交付清单](../../tests/independent/desktop/evidence/r10-settings/delivery.sha256)逐项绑定本轮工具、首次及终点证据、报告、四份共享文档；[交付验证](../../tests/independent/desktop/evidence/r10-settings/delivery-verification.json)给出实际数量和摘要。清单排除自身、验证回执与可变缓存以避免自引用，已保留的测试缓存不作为业务证据。终点审计保留当时字节结论，最终清单另绑定最后状态和本追加段。

测试角色停止于blocked / finished，等待总控review。没有消耗新产品/helper启动，未建议关闭SETTINGS-001或整个P4-B，不继续其他任务。
