# P4-B7-R1-E5-PKG-FINAL 隔离依赖、package 与最终 EXE 运行说明

## 结论

- 任务：`P4-B7-R1-E5-PKG-FINAL`
- 状态：`blocked / finished`
- E5-R2 parser 修复：接受总控结论，不重复修改或完整回归
- 离线 frozen install：1 次，成功
- 网络 fallback：0 次，未解锁
- Electron dist recovery：1 次，成功
- TypeScript：通过
- 三文件定向 Vitest：22 passed、0 failed、0 skipped
- package：1/1，exit 1，未重试
- 最终 EXE：0/1，未解锁
- P4-C12：未启动

本任务已在全新 C 盘根中物化任务专属 pnpm store、Electron cache、固定工具和 266 项 source，由 pnpm 创建了真实的 hoisted `node_modules` 普通目录。离线 frozen install、完整依赖列表、task-local `.modules.yaml`、Electron dist、TypeScript 与 22 项 Profile 相邻测试全部通过。

唯一 package 通过 Forge system check、pnpm 12.7.0 检查、Vite main/preload/两个 renderer production build，并进入 win32 x64 packaging。首个真实失败发生在 `Copying files`：`fetch failed`，最终抛出 `TypeError: fetch failed`。原始日志没有标识请求的远端 artifact，根因保持 `unverified`。按任务卡没有第二次 package，最终 EXE 没有解锁。

## 起点与任务边界

- control 版本：`2026-09-29T10:45:39+08:00`
- package 前最终 control SHA-256：`21e564fbdd5320677982bf01bacc22f83d3ed990f1bd99f7cb14bab763e7946d`
- 起点清单：266 entries、266 unique、266 matched、0 missing、0 mismatch
- 起点清单 SHA-256：`3f60f4e8df0b1f0fb01111f91d5804813524ee00ff3ed6760f75b4ae1ab9e7e4`
- 起点 Git index staged paths：0
- 新任务根：`C:\MarisE5Final\E5-PKG-FINAL-20260929-1732`

本轮没有修改产品、测试、依赖声明、lock、Forge、package wrapper、staging、Python、migration、接口冻结、control、overview、独立测试或其他角色文件。仓库只更新执行智能体日志，并新增本运行说明与 source manifest。没有执行 Git 写操作。

E5-R2 的以下结果由总控接受，本任务没有重复：

- TypeScript/Python canonical Profile parser 已精确一致；
- E5-R1 contribution 与三个 fixture 的真实 Profile 保持正确；
- OpenAPI、lint、52 项完整 desktop Vitest、29 项 Python 相邻回归、compileall 与 pip check 已通过；
- `P4-E5-PROFILE-PARSER-002` 在代码与执行方回归范围关闭。

旧 E4/E5-R1/E5-R2 `node_modules` 没有被读取、复制、链接、恢复、删除或执行。E5-R2 记录的 E4 43 项 `.bin` 漂移只作为总控已接受的历史事实保留。

## Donor 与 active cache

唯一 donor 为：

```text
C:\MarisE3\E3-20260928-0911\cache\pnpm\store
C:\MarisE3\E3-20260928-0911\cache\electron
```

两者根目录与内部均没有 reparse point。起点摘要：

| Donor | 文件数 | 字节数 | 有序 manifest SHA-256 |
| --- | ---: | ---: | --- |
| pnpm store | 10,975 | 178,708,341 | `14063134e63517e2b5f40a67c0d0c8c729bbb5bd9e1a2fa734d9651bee87c651` |
| Electron cache | 1 | 158,184,819 | `f9acc87b5d549090034a170b86f02b2d68fe02861609e1bf24a264cfd4f9a29e` |

Electron cache 唯一文件是官方 `electron-v44.4.5-win32-x64.zip`，158,184,819 bytes，SHA-256：

```text
11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d
```

两套 cache 物化复制到新任务根后逐文件差异为 0。package 失败后再次复算：

- donor pnpm store：10,975/10,975，起终点行差异 0；
- donor Electron cache：1/1，起终点行差异 0；
- active pnpm store：10,975/10,975，相对复制完成点差异 0；
- active Electron cache：1/1，相对复制完成点差异 0。

没有把 donor 本身作为 active store/cache，也没有复制 E3 workspace 的 `node_modules`。

## Source workspace 与固定工具

266 项固定 source 从当前仓库按起点路径集合物化到新 workspace，最终为 266/266、0 missing、0 mismatch。workspace copy manifest SHA-256：

```text
0629bcaa4f39d308bf06d438d705f12218805afbc3dc2f04a7ae7af18f8d2771
```

执行日志文件历史上包含混合 CRLF/LF，Git blob 为全 LF，而起点快照绑定 Windows 工作树的混合行尾字节。最初两种物化方式分别得到全 LF 与全 CRLF 摘要，均未冒充匹配；最终从当前混合行尾工作树副本精确反向去掉本任务日志改动，恢复固定起点的 221,987 bytes 和 SHA-256 `f4df31b9a4d8bce2063e08a6bece6bf95def038c1778be676399d2348a18da13`。该纠正只发生在新 workspace，不修改产品或仓库历史。

固定工具物化到新任务根：

| 工具 | 版本 | SHA-256 |
| --- | --- | --- |
| Node | 24.21.0 | `ba4e6d110e8c1592a1ecd390f6b05f3da124b13871a5be62b341a07a853c6c32` |
| pnpm native | 12.7.0 | `3e1a5bb3aba371d4c1bb5bb87f8ef1bd8dea41e0cd39d4bddf7c3dfbaae665ce` |
| task-local `pnpm.exe` binary alias | 12.7.0 | `3e1a5bb3aba371d4c1bb5bb87f8ef1bd8dea41e0cd39d4bddf7c3dfbaae665ce` |

Forge 的 PATH 第一项为 task-local `pnpm.exe`，其后为 task-local Node 与 pnpm 目录；不会解析系统 pnpm。所有 PATH 与 cache 环境变量都只在子进程范围设置，User/Machine PATH 在 package 前后保持不变。

## 离线 frozen install

安装前：

- 顶层 `node_modules` 不存在；
- active cache 是新任务根中的普通目录；
- `pnpm-lock.yaml` SHA-256 为 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`；
- 根 package、workspace 配置、desktop package 与 `.npmrc` 匹配 266 项固定输入；
- 任务进程 0，Git staged paths 0。

唯一 pnpm install：

```text
pnpm install --offline --frozen-lockfile --store-dir <task-local-store>
```

| 字段 | 结果 |
| --- | --- |
| 实际次数 | 1 |
| 开始 | `2026-09-29T17:51:22.1589401+08:00` |
| 时长 | 4,053 ms |
| exit code | 0 |
| stderr | 0 bytes |
| resolved/reused/downloaded/added | 274 / 274 / 0 / 275 |
| 终点任务进程 | 0 |
| 网络 fallback | 0 次；未解锁 |

原始 stdout 为 752 bytes，SHA-256 `e79b3b5af3671d042bccef46192299ebac7fd40a81bbff6f20434b09fc77370c`。

安装后：

- 顶层 `node_modules`：普通目录，LinkType 为空，非 reparse point；
- `.modules.yaml`：实际为 JSON 格式；
- `nodeLinker=hoisted`；
- `packageManager=pnpm@12.7.0`；
- `storeDir=C:\MarisE5Final\E5-PKG-FINAL-20260929-1732\cache\pnpm\store\v11`；
- `virtualStoreDir=C:\MarisE5Final\E5-PKG-FINAL-20260929-1732\workspace\node_modules\.pnpm`；
- E3/E4/E5-R1/E5-R2 路径命中数：0；
- `pnpm list --depth Infinity`：exit 0、stdout 23,274 bytes、stderr 0；
- node_modules：12,443 files、570,582,052 bytes、最终 manifest SHA-256 `15f5613ce7744083a81c05c68ab06e06b6aa0b6e30f0c9c98ed933d87899e04c`。

## Electron dist 环境供应

Electron 44.4.5 的冻结 package manifest 不含 postinstall script，所以 pnpm install 成功后 `node_modules/electron/dist` 尚不存在。E3 已接受的同版本环境供应路线是由固定 Node 直接运行冻结的 `electron/install.js`；该脚本读取 `electron_config_cache`，并使用 package 内 `checksums.json` 校验 cache hit。

本任务同时设置任务卡要求的 `ELECTRON_CACHE` 和 installer 实际读取的 `electron_config_cache`，两者都指向 task-local cache。唯一实际 recovery：

- 次数：1/1；
- 时长：1,380 ms；
- exit code：0；
- stdout/stderr：0/0 bytes；
- 终点任务进程：0；
- 没有下载或修改 donor。

第一次 pre-launch 检查误用了 PowerShell 不存在的 `Select-Object -Single`，发生在 Process.Start 前：started/result evidence 不存在、dist 不存在、任务进程 0、recovery 预算仍为 0/1。修正为 bounded collection 后才执行上述唯一实际 recovery。

最终 Electron dist：73 files、385,243,397 bytes，逐文件集合与 E3 冻结清单完全相同，冻结 manifest SHA-256：

```text
ffb4b389d5c454ca139cb6384f5ebb3d20633cf000960a8aa1b6c1794c9ebf8f
```

首次派生清单使用 Ordinal 路径排序得到 `3e0fccde...`；与 E3 清单比较确认 73 行内容集合完全相同，差异只在路径排序。保留该派生 warning 后，按 E3 冻结的 PowerShell `Sort-Object` 文化排序复算为 `ffb4...f8f`，没有修改 Electron 文件。

## Package 前定向回归

本任务没有重复完整 52 项 desktop 或 29 项 Python 回归，只执行任务卡要求的两组：

| 检查 | 结果 | passed | failed | skipped | warning |
| --- | --- | ---: | ---: | ---: | --- |
| TypeScript `tsc --noEmit` | exit 0 | 1 gate | 0 | 0 | stderr 15 bytes，仅 `$ tsc --noEmit` lifecycle 回显 |
| registry/composition-root/HostClient Vitest | 通过 | 22 | 0 | 0 | 3 files，Vitest 5.0.2 |

package 前最终门禁再次证明：source 266/266、lock、普通 node_modules、task-local store/virtual store、Electron dist、donor、零 out、零任务进程、零 staged paths全部通过；package 与最终 EXE 预算均为 0 次。

## 唯一 package 失败

| 字段 | 结果 |
| --- | --- |
| 实际次数 | 1/1 |
| 开始 | `2026-09-29T18:08:45.9026694+08:00` |
| 结束 | `2026-09-29T18:09:37.1595181+08:00` |
| 时长 | 51,257 ms |
| exit code | 1 |
| timed out | false |
| stdout | 1,144 bytes；SHA-256 `27af27bcdb48123edd36cbe2d4cd101b6479d6795cb7e83e9a4d735dcedf13aa` |
| stderr | 404 bytes；SHA-256 `de6063690200261146ca4eab102fce36d87451adca13d8c2ccffc588ca70a517` |
| 终点任务进程 | 0 |
| User/Machine PATH | 均未变化 |

已经通过的 package 阶段：

1. Forge system check；
2. pnpm 12.7.0 解析；
3. generateAssets hook；
4. prePackage hook；
5. Vite main、两个 preload、main window 与 companion window production build；
6. 进入 win32 x64 packaging、target determination 与 finalize 流程。

首个真实失败原文：

```text
× Copying files [FAILED: fetch failed]
× Preparing native dependencies [FAILED: fetch failed]
× Finalizing package [FAILED: fetch failed]
× Packaging for x64 on win32 [FAILED: fetch failed]
× Packaging application [FAILED: fetch failed]

An unhandled rejection has occurred inside Forge:
TypeError: fetch failed
```

`Copying files` 是日志中的第一个失败阶段；后续 native dependencies/finalize 是同一失败传播。原始日志没有 URL、artifact 名或调用栈，因此不能把失败确定归因于 Electron ZIP、Node headers、代理、DNS 或其他具体资源。准确代码为 `forge_fetch_failed_during_copying_files`，请求对象和根因均为 `unverified`。

任务卡规定真实 package 失败后立即停止且不得修改后第二次打包。本轮没有更换 cache、联网补装、修改 Forge/package wrapper、调整代理或重试。

## Package 后状态与完整性

- `out`：不存在；
- `Maris.exe`：不存在；
- `resources/app.asar`：不存在；
- `.maris-staging`：不存在；
- backup/lock/transition artifact：0；
- Vite 中间产物：10 files、755,009 bytes，manifest SHA-256 `f3264c20fe72f681aacf856b8df6771f72219a5ecd7eab91a415f146006022cd7`；
- 任务进程：0；
- Git index staged paths：0。

package 后逐文件复算：

| 对象 | 结果 |
| --- | --- |
| source workspace | 266/266、0 missing、0 mismatch |
| donor pnpm store | 10,975 files，起终点差异 0 |
| donor Electron cache | 1 file，起终点差异 0 |
| active pnpm store | 10,975 files，相对复制点差异 0 |
| active Electron cache | 1 file，相对复制点差异 0 |
| node_modules | 12,443 files、570,582,052 bytes，摘要与 package 前相同 |
| Electron dist | 73 files、385,243,397 bytes，`ffb4...f8f` |

第一次 package 后 closeout reader 因 PowerShell `foreach` 静态语法缺少括号而在读取前停止。原 warning 保留，修正派生读取后完成上述收口；没有重跑 package或启动产品。

## 最终 EXE

最终 EXE 只有 package 与全部静态产物门禁通过才允许执行。本轮没有生成 EXE/app.asar，因此：

| 项目 | 预算 | 实际次数 | 状态 |
| --- | ---: | ---: | --- |
| package | 1 | 1 | exit 1；不重试 |
| 最终 `Maris.exe` | 1 | 0 | `not_run_after_package_failure` |
| `runtime.recover()` | 1 | 0 | 最终 EXE 未运行 |

owned set、CDP、两个窗口、preload bridge、Node 隔离、runtime、modules、`daily_finance.assistant@1`、毛毛状态、openMain、recover、隐私、Windows 事件、自然退出和 Tray 收口全部未运行，不能写成通过或失败。

由于 app.asar、EXE 和最终 resources 不存在，production fuses、67 项 Python resources、app.asar Profile 字面量、`.pyc`/`.egg-info`/测试/evidence/绝对路径/凭据样式/私钥扫描也都是 `not_run_after_package_failure`。

## 文件边界与 source manifest

相对 266 项起点，仓库内只有允许的执行智能体日志发生变化；新增两项允许交付：

1. `docs/b7-r1-e5-pkg-final-running.md`
2. `apps/desktop/b7-r1-e5-pkg-final-source.sha256`

source manifest 沿用起点 266 路径集合，每行格式为：

```text
relative/path<TAB>sha256
```

UTF-8 无 BOM、LF 行尾。最终为 266 entries、266 unique、0 missing、0 mismatch；文件 27,773 bytes，SHA-256：

```text
f2b8a0fdd7642037b531673597a88bac6516cf237fa4cb276e029cd1aba19e1d
```

最终普通文件摘要：

| 文件 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `docs/coordination/agents/executor.md` | 231,538 | `b218c07abdd409b14435d6e72a068875535f9c7a7d58da34799650e09646cb88` |
| `apps/desktop/b7-r1-e5-pkg-final-source.sha256` | 27,773 | `f2b8a0fdd7642037b531673597a88bac6516cf237fa4cb276e029cd1aba19e1d` |

运行说明自身与上述两项一起写入外部 `repository-delivery.sha256`，避免自引用摘要。

## Evidence 与复算

外部 evidence 位于：

```text
C:\MarisE5Final\E5-PKG-FINAL-20260929-1732\evidence
```

内容包括 donor/active cache 清单、source copy、固定工具、离线 install、`.modules.yaml`、pnpm list、Electron recovery、TypeScript/Vitest、package 原始双流与 PID 观察、失败分类、package 后完整性与资源收口，以及所有派生读取器 warning。

外部 evidence manifest 排除自身与 repository delivery，采用 `relative/path<TAB>bytes<TAB>sha256`、UTF-8 无 BOM、LF，并按 Ordinal 路径排序。最终为 58 entries、58 unique、0 missing、0 mismatch，SHA-256 `072127d72a6d444452b1bbb52f72a33613387954aa8e561c1fa7506b83d6ec4a`。

## 执行 warning 汇总

以下均发生在 package/产品预算之外，原记录保留，没有被冒充为通过：

1. 首次 donor 内存汇总结束后没有返回可用 stdout；改为新 evidence 内的流式 manifest。
2. donor v1 summary 捕获了函数进度输出；用已完成 manifest 离线生成 v2 summary，没有重新读取或修改 donor。
3. fixed workspace 执行日志的全 LF/全 CRLF 两种物化都不匹配混合行尾快照；最终通过精确反向本任务日志改动恢复原字节。
4. `.modules.yaml` 首次按 line-oriented YAML 读取字段为空；实际文件为 JSON，离线改用 JSON parser。
5. Electron recovery pre-launch 使用不存在的 `Select-Object -Single`；Process.Start 前停止，实际 recovery 仍为 0/1。
6. Electron dist 首次派生清单使用 Ordinal 排序；内容集合正确，但冻结 E3 采用 PowerShell 文化排序，离线重排后得到冻结摘要。
7. package 后 closeout reader、source manifest 与 evidence manifest 脚本各有一次 PowerShell `foreach` parser error；都没有启动 package/产品，修正派生读取后完成。
8. 一次只读文件摘要 helper 重复了同类 `foreach` 空格语法错误；没有文件写入或运行产品，修正后取得实际摘要。

## 未运行与交接

- 最终 EXE、runtime、modules、recover 与产品隐私门禁：未运行。
- 独立测试、测试智能体、技术顾问和 P4-C12：未启动。
- 高保真前端、OpenClaw、微信和 DeepSeek：未启动。
- Docker/PostgreSQL：未启动。
- 真实账户、真实密钥、真实数据库和个人财务数据：未读取。

执行智能体以 `blocked / finished` 停止。依赖隔离问题已经解决并形成可复算证据；当前首个阻塞是唯一 package 在 Forge `Copying files` 阶段的未标识 `fetch failed`。package 预算已耗尽，执行方不得自行修改环境后重试、启动最终 EXE 或提前进入 P4-C12；下一步由头脑风暴总控审阅原始网络/缓存证据并发布新的精确续段。
