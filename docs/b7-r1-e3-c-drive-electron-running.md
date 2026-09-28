# P4-B7-R1-E3 C 盘 Electron 最小三角验证运行说明

## 1. 结论

- 任务状态：`review / finished`。
- A1 C 盘 direct 只运行 1 次并通过；A2 C 盘 Playwright 默认 loader 在 A1 完全成功后只运行 1 次并通过。两个 cell 均未重试。
- 两次运行都使用同一份 C 盘 Electron 44.4.5 dist、同一份三文件最小 fixture、相同基线参数和各自独立的空 profile。A2 没有传 `executablePath`，默认 loader 解析到同一个 C 盘 `electron.exe`。
- 两次 browser 均退出 0、未超时；marker 与 run-id/cell 匹配；fixture 事件均为 `app-ready → did-finish-load → normal-exit`；driver/electron 日志均落盘且没有命中冻结故障模式；精确时间窗内没有 Application 或 Code Integrity 事件；dist/fixture 摘要前后不变；最终任务 Electron 进程为 0。
- 结论严格限定为：**C 盘同内容 direct 与 Playwright 均稳定；结合既有 D 盘 Playwright 失败，支持执行位置、继承 ACL、ADS 或路径元数据相关差异。** 本任务没有定位具体根因，也没有证明 P4-B、app.asar、Forge package 或最终 EXE 可运行。

## 2. 起点门禁与执行边界

| 门禁 | 结果 |
| --- | --- |
| 最新 control | `2026-09-28T08:57:00+08:00`；执行智能体为 E3 唯一负责人，只允许 A1 一次，A1 完全成功后才允许 A2 一次 |
| E3 起点清单 | 211 matched、0 mismatch、0 missing；manifest SHA-256 `b4ac70fa815314da1b3e4dd2341ee758d9e7a1eaa15687e443e15c1a7be62576` |
| H1 source | 198 matched、0 mismatch、0 missing；manifest SHA-256 `04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1` |
| repository lock | SHA-256 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |
| 起点进程 | 旧任务 Electron、Maris 和项目 sidecar 进程为 0；没有按名称结束用户其他进程 |
| C 盘任务根 | `C:\MarisE3\E3-20260928-0911`，全新短 ASCII、无空格；run-id `E3-20260928-0911` |
| Git | 未执行任何 Git 写操作 |

任务只运行冻结的 A1/A2。没有运行 D 盘基线、Procmon/F1、诊断开关组合、其他 Electron 版本、app.asar、Forge package、Maris.exe、Host、sidecar、Python、数据库、Docker、OpenClaw、微信、DeepSeek、P4-C12 或 `tests/independent/**`；没有修改产品、依赖、lock、H1 staging、测试、冻结文档、control、overview、其他角色或 `.claude/**`。

## 3. 固定工具、来源与安装

| 工具 | 固定版本与来源 | 核验结果 |
| --- | --- | --- |
| Node | 24.21.0；Node 官方发布 ZIP | 37,618,919 bytes；SHA-256 `158f7685b44de51f6c0df1d153526cbcd3e1bc739a8dfc607721cef75de9e541` |
| pnpm | 12.7.0；npm 官方 registry metadata/tarball | 1,010,447 bytes；SHA-1 `2734f196debfb5e42276568a1c9fc57a058263e0`；官方 SHA-512 `nFZHfjYAaNbp3KapLvtORrPcWlL86/PYTXi5c2wN7ViaVhYhpS9oIZp6OfrMY83AecMibvnJ1fArefdOaagHtg==`；metadata SHA-256 `320d50cadc29763f7ae1cf49e578c952f0ea46b17eea1f89b0554a9faa5f1524` |
| Electron | 44.4.5；Electron 官方 release ZIP | 158,184,819 bytes；archive SHA-256 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d` |
| `electron.exe` | 上述官方 archive 解压内容 | 246,032,896 bytes；SHA-256 `bd14928e0728366fd3f41499cb398ff3f4304dab259a3e605077899a6f8c748e` |
| Playwright | frozen lock 解析的 1.63.0 | A2 使用 `_electron.launch()` 默认 loader；没有传 `executablePath` |

C 盘 workspace 只复制根 `package.json`、`pnpm-workspace.yaml`、`pnpm-lock.yaml` 和 `apps/desktop/package.json`，执行 frozen install。仓库 lock 与 C 盘 lock 安装前后均为 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`；安装 275 packages，实际自动 lifecycle 只有 `esbuild`。Electron dist 最终通过任务专属 cache 的官方 archive 强制恢复并逐字节核验，未接受旧 package/out、第三方 mirror、全局 Electron、未知 cache 或第三方 DLL。

## 4. 固定 fixture、manifest 与环境摘要

fixture 只包含 `package.json`、CommonJS `main.cjs` 和静态 `index.html`。它在 ready 前关闭硬件加速，为每个 cell 设置独立 user-data profile，创建一个隐藏 BrowserWindow，并保持 renderer sandbox、context isolation 开启和 node integration 关闭。页面只加载本地 HTML；没有网络、preload、IPC、Host、Python、数据库、产品代码、真实用户 profile 或个人数据。

| 内容 | 文件数 | 有序 manifest SHA-256 | A1 前/后 | A2 前/后 |
| --- | ---: | --- | --- | --- |
| Electron dist | 73 | `ffb4b389d5c454ca139cb6384f5ebb3d20633cf000960a8aa1b6c1794c9ebf8f` | 相同 | 相同 |
| fixture | 3 | `80e74627c3d2225567305e1ce425042b98598b0083556055276860a9ec0257bf` | 相同 | 相同 |

Windows 摘要为 25H2、build `26200.9168`、OS/process architecture 均为 x64；显示适配器为 NVIDIA GeForce RTX 4060 Laptop GPU 与 Intel UHD Graphics。该信息只用于复现环境，没有据此归因驱动或混合显卡。

任务根和 Electron dist 都继承 5 条 ACL 规则，ACL protection 为 false，没有任务创建的显式 ACL。原始 owner 和完整 SDDL 只保留在 C 盘 evidence，不写入仓库。`electron.exe`、官方 ZIP 和三个 fixture 文件均只有默认 `:$DATA` stream，没有额外 ADS。记录的路径长度为：任务根 27、dist 64、`electron.exe` 77、官方 cache ZIP 138、三个 fixture 文件 44～48 个字符。

## 5. A1：C 盘 direct

| 项目 | 结果 |
| --- | --- |
| 唯一时间窗 | UTC `2026-09-28T01:36:31.690Z` 至 `2026-09-28T01:36:36.394Z`；本地约 `09:36:31.690+08:00` 至 `09:36:36.394+08:00` |
| launcher | C 盘 `electron.exe` direct；未经过 Playwright、inspector 或 CDP |
| 参数类别 | `--disable-gpu`、`--enable-logging=file`、`--log-level=0`、任务专属 `--log-file`，fixture app path 位于所有 Chromium switches 之后 |
| profile | 新建的任务专属 `profiles\a1` |
| PID / 超时 / 退出 | PID 25148；4.704 秒；未超时；browser exit 0、signal null |
| ready/load/marker | `app-ready → did-finish-load → normal-exit`；marker 的 status、run-id、cell 与三项 webPreferences 全部匹配 |
| 日志 | driver 1,121 bytes、electron 610 bytes、fixture event 393 bytes、stdout 2 bytes、stderr 0 bytes；所需文件均存在 |
| 故障模式 | `0xC0000135`、`0x80000003`、两个 STATUS 名称、render/child gone、Target crashed、assertion 命中 0 |
| Windows 事件 | 扩展后的精确时间窗内 Application 0、Code Integrity 0；两个日志均成功查询并返回 no events |
| 内容与收口 | dist/fixture 前后完全相同；任务 `electron.exe` 精确路径残留进程 0 |
| 后置证据 | `post-validation.json` SHA-256 `66ede312d611251fe7152c4602473b21ad1797df3d8d78fb1820089c506120cb`；task contract success `true` |

A1 driver 的原始 `result.json` 把 `before-quit` 误设为必需事件，因此 driver 自身退出 1、`basicSuccess=false`。fixture 使用 `app.exit(0)`，该调用不保证产生 `before-quit`；冻结任务合同要求的是 ready、隐藏窗口、本地页面加载、匹配 marker、browser exit 0、日志、无异常、内容不漂移和进程收口，并未要求 `before-quit`。本任务没有重跑 A1，而是保留原始 result/driver，以独立后置汇总按任务卡七项实际条件核对为 `true`。browser 本身退出 0，且所有七项证据均通过。

## 6. A2：C 盘 Playwright 默认 loader

A1 完全成功并且任务资源收口后，再次读取 control，才执行 A2。

| 项目 | 结果 |
| --- | --- |
| 唯一时间窗 | UTC `2026-09-28T02:42:44.078Z` 至 `2026-09-28T02:42:47.539Z`；本地约 `10:42:44.078+08:00` 至 `10:42:47.539+08:00` |
| launcher | C 盘 frozen Playwright 1.63.0 的 `_electron.launch()`；`executablePathOption=false` |
| 默认解析 | `workspace\node_modules\electron\index.js` 默认解析到同一 C 盘 `electron.exe`；可执行文件 SHA-256 `bd14928e0728366fd3f41499cb398ff3f4304dab259a3e605077899a6f8c748e` |
| 参数类别 | 与 A1 相同的 `--disable-gpu`、file logging、最低日志级别、任务专属 log file 和最后一个 fixture app path；Playwright 自身使用默认 loader/inspector/CDP 流程 |
| profile | 新建的任务专属 `profiles\a2` |
| PID / 超时 / 退出 | PID 22596；3.461 秒；未超时；Electron exit 0、signal null；Playwright connected=true、close observed=true、driver exit 0 |
| ready/load/marker | `app-ready → did-finish-load → normal-exit`；marker 的 status、run-id、cell 与三项 webPreferences 全部匹配 |
| 日志 | driver 1,604 bytes、electron 608 bytes、fixture event 393 bytes；所需文件均存在 |
| 故障模式 | 冻结的异常码、STATUS 名称、gone、Target crashed 和 assertion 命中 0 |
| Windows 事件 | 扩展后的精确时间窗内 Application 0、Code Integrity 0；两个日志均成功查询并返回 no events |
| 内容与收口 | dist/fixture 前后完全相同；任务 `electron.exe` 精确路径残留进程 0 |
| 后置证据 | `post-validation.json` SHA-256 `da165cb856a141f10aaf3d0790a6254886de93497304bcc3e307d4b28e66001c`；task contract success `true` |

## 7. 失败、warning 与处置记录

下列准备或证据脚本问题均发生在 Electron 启动外，没有增加 A1/A2 运行次数，也没有改变产品或固定内容：

1. H1 历史运行说明中的 pnpm integrity 与当前 npm 官方 registry metadata 不一致。任务没有接受旧字符串；重新取得官方 12.7.0 metadata 后，本地 tarball 同时匹配当前官方 SHA-1 和 SHA-512，来源与版本未改变。
2. 第一次 Electron install 使用了不适用于该 install script 的 cache 环境变量，可能命中用户默认 cache。该结果未纳入证据；只删除任务拥有的 C 盘 dist/path 文件后，以 `electron_config_cache` 和 `force_no_cache` 从官方 URL重新恢复，最终 archive 大小与 SHA-256 均匹配冻结值。
3. 初次组合生成预检证据的脚本在写证据前失败；之后拆成确定性步骤生成，Electron 未启动。
4. 初次 A1 driver 静态检查误用 PowerShell parser 检查 `.cjs`，产生语言不匹配错误；随后固定 Node `--check` 通过，Electron 未启动。
5. 第一次 A1 control 门禁正则没有匹配 Markdown 反引号格式，在创建 profile 和进程前停止；随后改为精确读取版本行，A1 仍只运行一次。
6. A1 后置汇总首次对 0 字节 stderr 使用正则时得到 null 输入；原始日志/事件已成功保存，随后只重建汇总，没有重启 Electron。
7. A2 驱动语法检查会话返回较慢，但最终正常完成；Electron 尚未启动时没有强制终止。
8. 最终 evidence manifest 命令第一次被外层脚本解析器拒绝制表符转义；命令未执行，随后改用字符码生成清单。
9. 初次 WMI/CIM 进程枚举被当前权限拒绝；所有启动前后门禁均改用 `Get-Process.Path` 对任务 C 盘 `electron.exe` 做精确路径比较，没有申请管理员权限，也没有按进程名清理其他进程。
10. 最终只读 `git diff --check` 退出 0且没有 whitespace error；Git 提示执行角色文件下次触碰时可能由 LF 转为 CRLF，并提示用户级 `%USERPROFILE%\.config\git\ignore` 无读取权限。显式路径 status 和边界核对仍完整返回，没有执行 Git 写操作。

没有 Electron popup、browser/child 非零退出、硬超时、内容漂移、日志缺失、Windows 异常事件或无法收口的任务进程。A1 原始 driver 的 `before-quit` 过严断言已在第 5 节单独保留和解释，没有被隐藏或改写。

## 8. 解释边界与未运行项

A1 与 A2 同时成功，说明 C 盘短 ASCII、继承 ACL、无额外 ADS 的同内容环境中，direct 和 Playwright 默认 loader 都能稳定运行。结合既有 D 盘 Playwright 首故障证据，这支持“执行位置、继承 ACL、ADS 或路径元数据相关”的假设类别，但仍不能区分这些因素，也不能排除时序或机器状态差异。这里的“支持”不是根因证明。

以下全部为 `not_run`：D 盘对照、F1/Procmon、DLL 归因、Code Integrity 深挖、额外 Chromium 开关、GPU sandbox 变体、其他 Electron 版本、app.asar、Forge package、production fuses、最终 resources scan、Maris.exe、Host/sidecar、Python、数据库、Docker、OpenClaw、微信、DeepSeek、P4-C12 和独立验收。没有把 E2/E2-R1 的历史结果计入本轮通过项。

## 9. 仓库交付与 source manifest

仓库内只交付：

- 本运行说明；
- `apps/desktop/b7-r1-e3-source.sha256`；
- 执行智能体角色日志更新。

[E3 source manifest](../apps/desktop/b7-r1-e3-source.sha256)严格复用 H1 的 198 个 source 路径，按 POSIX 相对路径排序并记录 `path<TAB>sha256`。最终复算为 198 matched、0 mismatch、0 missing；其内容与 H1 source manifest 逐字节相同，自身 SHA-256 仍为 `04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1`。它不包含自身、本报告、角色日志、C 盘证据、task tools、profile、cache、`node_modules`、日志、截图或 `.claude/**`。

产品、依赖、lock、H1 staging 和测试文件均未变化。本轮自测只有冻结的 A1/A2 动态矩阵及其内容/事件/收口验证；这不是 P4-C12 独立验收。

相对 211 文件 E3 起点清单，最终为 210 unchanged、1 changed、0 missing；唯一 changed 是任务卡允许更新的 `docs/coordination/agents/executor.md`。本报告与 E3 source manifest 是任务卡允许的两个新增文件，不在起点清单内。`tests/independent/**`、control 和 overview 的显式 Git status 均为空。

## 10. C 盘原始证据与资源状态

整个任务根 `C:\MarisE3\E3-20260928-0911` 按任务卡保留，没有清理或覆盖。保留内容包括固定 Node/pnpm 工具、官方下载与 cache、frozen workspace、Electron dist、三文件 fixture、两个独立 profile、driver、marker、Electron/fixture 日志、Windows 事件查询结果、前后内容 manifests 和最终证据清单。

最终 `evidence/final-evidence.sha256` 覆盖其自身以外的 39 个 evidence 文件，清单 SHA-256 为 `4b21b569e21a529a4743c53e115d1f035a6c51e75bd916948a2d37ccaac85b46`。A1 profile 保留 55 个文件，A2 profile 保留 56 个文件；这些均在各自任务 profile 内。最终任务 Electron 精确路径进程数为 0，没有测试窗口、Tray 或任务进程残留。

执行智能体已停止，不创建 F1、P1、P2 或 P4-C12，不启动技术顾问或测试智能体，等待头脑风暴总控复算与决定下一任务。
