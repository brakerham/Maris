# P4-B7-R1-E5-FINAL 最终 EXE 黑盒运行说明

## 结论

- 任务：`P4-B7-R1-E5-FINAL`
- 交付状态：`blocked / finished`
- 唯一动态预算：`1/1`，没有重跑
- 黑盒启动方式：固定 Node `child_process.spawn()` 直接启动冻结的 `Maris.exe`，`shell:false`
- 观察方式：Playwright Chromium 只通过本轮新建的动态 loopback CDP 端点附加
- 运行时长：35,188 ms，低于 120 秒硬上限
- 第一个停止点：`daily_finance_missing`
- 根因：`unverified`

程序没有崩溃。直接启动、根进程所有权、CDP、两个窗口、preload bridge、安全隔离、首次 runtime、自然退出、资源清理、事件和固定产物均通过。唯一一次 `modules.list()` 观察返回空数组，未观察到已启用的 `daily_finance`，因此按冻结顺序立即停止后续产品调用并提交阻塞结果。

这个结果只证明本轮唯一观察时 module gate 未满足。它不证明模块永久缺失，也不支持在没有第二次运行的情况下确定根因。任务预算已经用完，不创建 E5-R1、DYN-R3、产品返修或独立验收。

## 输入和启动前门禁

- 最新 control 版本：`2026-09-29T03:00:00+08:00`
- 最新 control SHA-256：`c2f8123d3fbb85643cc80cd4a769558179b9bcf6b46d28695dd1b1874cedb48b`
- E5 起点快照：254 entries、254 unique、0 missing、0 mismatch
- E5 起点清单 SHA-256：`c8007e18e370004fdae62c3f836b767a69ae2c760d15aed2c5ec42c7705a48bd`
- PKG-R2 evidence：40/40 匹配，清单 SHA-256 `a082d25481adc94c61a50a0c96cc08cbfd141175c0adad85798e9157f274c01f`
- DYN-R1 evidence：84/84 匹配，清单 SHA-256 `db316ae191e295793edcded01f85ba81e54809d3696a61e364f11b372c6db8bf`
- DYN-R2 evidence：79/79 匹配，清单 SHA-256 `8872b541c2505e0a8b11df65c178ee0c7b3ca6d8ac6a66d277a31e48554e3aff`
- 冻结 source：198/198 匹配，清单 SHA-256 `04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1`
- Electron dist：73/73 匹配，清单 SHA-256 `ffb4b389d5c454ca139cb6384f5ebb3d20633cf000960a8aa1b6c1794c9ebf8f`
- Python resources：67/67 匹配，清单 SHA-256 `324845f07f050f2b90e3c1e0b89b6598c8748aca549f8f848b600d5a2a0da5d1`
- package out：140/140 匹配，清单 SHA-256 `97d72746ecfa2fd7ff3257cd183b5b033745e1e4b6519053264ab1cc400a15e6`
- 最终 EXE SHA-256：`149ccd6e2d71a8945ffef4ecba81e5121bc19c4816331ed5bcb6e72948174199`
- 最终 app.asar SHA-256：`c38cd0c7c5b42e4576d051f936d2942cd6a180b4386c62687a1886e991ae22f6`
- production fuses：version 1，冻结字节序列全部匹配
- 项目 Python：3.14.7
- 启动前产品进程和窗口：0
- 启动前 Git index staged paths：0

新 evidence 在启动前不存在，按 create-new 创建。没有覆盖、删除或复用旧 profile、数据库、PID、端口、marker 或运行结果。

## Runner 静态冻结

- Runner：640 行
- Runner SHA-256：`a2009876a8b1c2aba230d1573d644a3103109a15610ef129c1a803de790e0658`
- 固定 Node 语法检查：退出码 0
- direct `spawn()`：1 处
- `connectOverCDP()`：1 处
- `runtime.recover()` 调用点：1 处
- 定向根进程树清理后备路径：1 处
- Playwright `_electron`：0 处
- `--no-sandbox`：0 处
- `browser.close()`：0 处
- `app.quit()`：0 处

直接启动只传动态 loopback 调试地址和随机端口两个参数，清除了继承环境中的 `NODE_OPTIONS` 与 `ELECTRON_RUN_AS_NODE`。运行使用全新隔离 profile、虚拟数据库、随机虚拟 owner 数据和新 marker；没有读取真实 AppData、真实凭据、真实账户或个人财务数据。

## 唯一动态运行结果

### 直接启动与所有权

- 直接 `spawn()` 返回的进程仍存活，executable 精确匹配冻结的 `Maris.exe`，creation time 位于本轮运行窗口：通过。
- owned set 由直接根及其递归后代建立：通过。
- 没有经命令包装器、PowerShell、Playwright Electron loader 或 Forge 启动。
- 动态运行次数：1；重跑次数：0。

### CDP

- `DevToolsActivePort` 由本轮新 profile 创建，创建和更新时间位于本轮窗口：通过。
- 动态端口非零，实际监听仅为 IPv4 loopback：通过。
- Playwright Chromium 仅使用 `connectOverCDP()` 观察 renderer：通过。
- CDP 端点、动态端口和 websocket path 只保存在受限 evidence，没有进入仓库文档。

### 窗口、bridge 与 renderer 安全

- 页面总数 2：一个主窗口 `Maris`，一个毛毛窗口：通过。
- 主窗口 `window.maris` 为冻结对象，顶层键为 `external`、`modules`、`outbox`、`runtime`、`settings`、`window`；嵌套键与冻结 preload 合同一致：通过。
- 毛毛窗口 `window.companion` 为冻结对象，键为 `getState`、`openMain`：通过。
- 两个 renderer 中 `require`、`process`、`Buffer`、`global`、`module`、`exports` 及内部文件名全局均不可用：通过。
- 主窗口未允许的 companion/Electron/IPC/API bridge 和毛毛窗口未允许的 maris/Electron/IPC/API bridge 均不可用：通过。
- 首次 DOM、local storage、session storage 和 bridge 采样未命中秘密、内部路径或运行身份模式；两类 storage 的键集合均为空：通过。

### Runtime、modules、recover 与毛毛

| 门禁 | 观察结果 | 结论 |
| --- | --- | --- |
| 首次 runtime | `state=online`、`mode=managed`、`authenticated=true`、`errorCode=null` | 通过 |
| 首次 modules | 唯一一次 `modules.list()` 返回空数组 | 失败：未观察到 `daily_finance` |
| `runtime.recover()` | 0/1 | `not_run_after_module_stop` |
| recover 后 runtime | 无结果 | `not_run_after_module_stop` |
| recover 后 modules | 无结果 | `not_run_after_module_stop` |
| 毛毛 `getState()` | 无结果 | `not_run_after_module_stop` |
| 毛毛 `openMain()` | 无结果 | `not_run_after_module_stop` |

Runner 的聚合 `runtime=false` 表示由 runtime、modules 和 recover 组成的完整阶段没有全部完成；它不表示首次 runtime 失败。首次 runtime 明确通过，首个实际失败断言是 `daily_finance_missing`。失败消息摘要为 `f0726b6742dbb0c2b19f0c8f30dc93de86482c653e1e738bf50631daabcc4b8f`。

### 隐私

- 启动后、modules 停止前的 DOM、storage、bridge、console、page error 与持久日志检查未发现 owner token、refresh token、nonce、bootstrap token 或真实个人数据：通过。
- stdout 和 Electron 日志未命中秘密、内部路径或运行身份模式：通过。
- stderr 只含预期的 CDP 调试端点提示；运行身份内容受限保存在外部 evidence，没有复制到仓库。
- recover 后的最终隐私复查：`not_run_after_module_stop`。
- 因最后一项未运行，runner 的完整 privacy 聚合 gate 为 false；这不否定停止点之前已经通过的隐私观察。

### 日志、事件与崩溃

- Electron console 事件：0
- page error：0
- renderer crash event：0
- Windows Application 时间窗事件：0
- Windows Code Integrity 时间窗事件：0
- 冻结 crash/assertion/forbidden 模式：0
- 产品崩溃：未观察到
- Electron 日志只有一条 GPU overlay 信息；没有将其归类为 crash 或产品失败。

### 自然退出与资源收口

- `MARIS_E2E_EXIT_MS=30000` 触发现有退出链路。
- 根进程自然退出：是。
- 退出码：0；signal：无。
- 硬超时：否。
- forced cleanup：否。
- 运行中观察到一个受管 Python sidecar；结束后为 0。
- 根及记录后代：0。
- 捕获端口监听：0。
- 产品窗口：0。
- 产品 Tray 所属进程推断：0，因为记录的直接产品树已经完全退出。
- 隔离 profile 外本任务写入：0。

## 前后产物一致性

| 对象 | 结果 |
| --- | --- |
| `Maris.exe` | 前后 SHA-256 相同，匹配冻结值 |
| `resources/app.asar` | 前后 SHA-256 相同，匹配冻结值 |
| frozen source | 198/198，0 failure |
| Electron dist | 73/73，0 failure |
| Python resources | 67/67，0 failure |
| package out | 140/140，0 failure |
| production fuses | version 1，全部匹配 |

没有修改产品、测试、独立测试、依赖、lock、Forge、staging、migration、接口冻结、control、overview 或其他角色文件。没有运行测试、build、package、app.asar、Docker、OpenClaw、微信、DeepSeek 或 P4-C12；没有执行 Git 写操作。

## Warning

唯一产品启动之前，一次只读 PowerShell 门禁命令因内联表达式缺少右括号而被 parser 拒绝。该命令没有启动产品，动态预算仍为 0/1；原错误已保存在受限 evidence。随后只把 Node 语法检查拆成独立语句并重新执行静态门禁，结果全部匹配。此项属于执行方读取器 warning，不是产品失败，也没有造成第二次动态运行。

stderr 的预期调试端点文本触发了通用内部身份正则。原文只留在受限 evidence；它没有包含仓库文档可公开的端口、websocket path 或文件系统路径，也没有被归类为秘密泄漏。

## 未验证项

- 为什么唯一一次 `modules.list()` 返回空数组：未验证。
- `daily_finance` 是否在另一个时间点可见：未验证；禁止用本轮单次结果外推。
- recover 后 runtime 和 modules：未运行。
- 毛毛 `getState()`、`openMain()` 及不新增窗口：未运行。
- recover 后最终隐私复查：未运行。
- 真实 Tray 菜单：未运行，仍属于后续独立验收范围。
- P4-C12：未启动。

## Evidence 与摘要

- 受限外部运行证据：82 entries、82 unique、0 failure。
- 外部运行证据清单 SHA-256：`c8f93a29857c0a3dce89a78a72c8e1785be1be907579f10bd4369c19a262f5fc`。
- 仓库 source manifest：`apps/desktop/b7-r1-e5-final-exe-source.sha256`，198 entries、198 unique、0 missing、0 mismatch，SHA-256 `a45bf73570369c0595da436076949d723b3249dfc2af40a810a0182fcd0ca74e`。
- 仓库交付文件清单保存在受限 evidence，包含本运行说明、source manifest 和执行智能体日志；最终摘要在交付后复算。

外部 evidence manifest 每行为 `相对路径<TAB>字节数<TAB>SHA-256`，按相对路径序数排序，UTF-8 无 BOM；校验时逐项复算字节数和 SHA-256。仓库 source manifest 每行为 `相对路径<TAB>SHA-256`，路径集合沿用冻结的 198 项 source 清单并逐项重算。

## 交接

执行方在 `blocked / finished` 停止。总控可以复算三项仓库交付、198 项 source 和受限 evidence，并据唯一失败点决定是否另行冻结产品返修任务。当前不得重跑最终 EXE、创建 E5-R1/DYN-R3、修改 runner 后重试或启动 P4-C12。
