# P4-B7-R1-E4-PKG-R2 执行记录

- 角色：执行智能体，PKG-R2 唯一执行负责人。
- 状态：`review / finished`。
- 执行日期：2026-09-29，Asia/Shanghai。
- 结论：复用总控已经接受的 Q1～Q6 原始证据，没有重跑任何预检；固定 C 盘 workspace 中唯一一次真实 package 退出 0。预期 Windows package、Maris.exe、app.asar、production fuses、H1 Python resources、污染扫描、staging 清理和固定输入终点复算全部通过。没有启动任何 package 产物，最终接受权仍属于头脑风暴总控。

## 1. 控制、起点和任务边界

已按 `AGENTS.md` 顺序读取项目入口、协作文档、最新 control、执行角色状态和完整任务卡，并读取 PKG-R1 总控核对、PKG-R1 运行说明及 H1/H1-R1 运行记录。

- 最新 control 版本：`2026-09-29T00:52:00+08:00`。
- control SHA-256：`76d904948e40d7544f89c8d8b4d920f0e9b5845e10bd0a30e2665de0131d63a9`。
- [PKG-R2 起点清单](coordination/snapshots/p4-b7-r1-e4-pkg-r2-start.sha256)：240 项，240 个唯一路径，Ordinal 有序；开工前 240/240 匹配、0 missing、0 mismatch。
- 起点清单 SHA-256：`7bd97e11d6803d9bbbf4a500a35b027f68e8cbb6c9ffa1394f6fdda63849a9d2`。
- 任务卡引用的 `docs/b7-r1-h1-r1-staging-atomicity-running.md` 不存在；实际 H1/H1-R1 记录合并在 [H1 package hygiene 运行说明](b7-r1-h1-package-hygiene-running.md)，其中第 10 节是 H1-R1 staging 原子替换返修。已完整读取，没有重复运行 H1 测试。

本任务只写本角色日志、本运行说明、PKG-R2 source manifest、`package-resume-2` 新 evidence，以及现有 wrapper/Forge 被授权生成并清理的 staging 和 `out`。没有修改产品、测试、Forge 配置、wrapper、staging 实现、依赖、lock、`.npmrc` 或永久环境；没有执行 Git 写操作。

## 2. PKG-R1 证据只读复算

`C:\MarisE4\E4-20260928-1255\package-resume-1` 始终只读。其 `delivery-evidence.sha256` 自身 SHA-256 为 `776c58212d5b70af06968747c65cb1bd2456cc421bae98120ef04b5138b04391`；45/45 条目按 bytes 和 SHA-256 复算匹配。

Q1～Q6 在本轮统一记为：

```text
accepted_from_previous_evidence / not_rerun
```

只读结果如下：

| 预检 | 接受的原始结果 | 本轮动作 |
| --- | --- | --- |
| Q1 | 专属 shim 为第一条 pnpm 路径，exit 0，stderr 0 | not_rerun |
| Q2 | `12.7.0`，exit 0，stderr 0 | not_rerun |
| Q3 | `undefined`，exit 0，stderr 0 | not_rerun |
| Q4 | `undefined`，exit 0，stderr 0 | not_rerun |
| Q5 | `hoisted`，exit 0，stderr 0 | not_rerun |
| Q6 | stdout 是完整四字段 JSON；inner-1～4 均 exit 0、resolved true、signal null、stderr 0 | not_rerun |

没有补写或覆盖 PKG-R1 的 result、receipt、时间或日志。新 shim 从 PKG-R1 专属 shim create-new 复制，源和目标 SHA-256 均为 `57785cc51fff3a94b68815e46f48a400f1cb016f9edc82d2cb9606cbdb088bdf`。

## 3. 固定 C 盘输入门禁

固定位置：

```text
C:\MarisE4\E4-20260928-1255
C:\MarisE4\E4-20260928-1255\workspace
C:\MarisE4\E4-20260928-1255\workspace\apps\desktop
```

真实 package 前和 package 后的完整复算一致：

| 输入 | 条目/字节 | 前后结果 | 清单或聚合 SHA-256 |
| --- | ---: | --- | --- |
| 固定 workspace source | 198 项 | 198/198 匹配 | `4a4a73508d400ddb557de2a3235d6c6cf39c4fecdac01c854c2aea0dc9656ce2` |
| 固定 Electron dist | 73 项 | 73/73 匹配 | `ffb4b389d5c454ca139cb6384f5ebb3d20633cf000960a8aa1b6c1794c9ebf8f` |
| node_modules | 12,451 文件 / 570,581,590 bytes | 前后相同 | `f06ce306456134f7f78176e64d3f9a7e54133607d3e9202ff6bb1a9fcbf800c7` |
| pnpm-lock.yaml | 1 文件 | 前后相同 | `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |

package 前 `out=false`、staging=false、transition 0、固定 C 根任务相关进程 0。新 `package-resume-2` 在门禁时不存在，随后 create-new；没有删除或复用旧 evidence。

## 4. pre-launch 会话错误和真实执行次数

第一次普通 PowerShell 会话在调用 `Process.Start()` 前，被执行方自己的 `Test-Path` 布尔表达式解析错误拦住。原始结果保留在 `session-result.json`：

- package result 为 null；
- `knownTaskPids=[]`；
- package 目录中没有 started/stdout/stderr/result；
- process-local PATH 和 `ELECTRON_CACHE` 已还原；
- User/Machine PATH 未变。

该事件分类为 `executor_prelaunch_expression_error`，实际 package 次数仍为 0/1。分析保存在 `prelaunch-failure-analysis.json`。只给三个 `Test-Path` 子表达式增加括号后，新会话才调用固定 pnpm native；没有修改产品、环境或预检，也没有覆盖第一次错误。

这符合任务中的“package 实际次数”口径：**native package 只启动一次，最终次数 1/1**。不存在第二次 native package。

## 5. 唯一真实 package

同一普通持续 PowerShell 会话仅为自身和子进程设置：

1. PATH 第一项为 `package-resume-2\forge-pnpm-bin`；
2. PATH 第二项为固定 Node 目录；
3. 后续 PATH 原样继承；
4. `ELECTRON_CACHE` 指向 E4 既有固定 cache。

命令和结果：

| 字段 | 实际值 |
| --- | --- |
| 命令标签 | `fixed pnpm-native.exe run package` |
| 参数 | `run`, `package`，共 2 个 |
| cwd | 固定 desktop 目录 |
| PowerShell PID | 6424 |
| package native PID | 7340 |
| 开始时间 | `2026-09-29T01:14:33.8857859+08:00` |
| 结束时间 | `2026-09-29T01:14:44.1662946+08:00` |
| 耗时 | 10,252 ms |
| 超时 | false |
| 真实退出码 | 0 |
| stdout | 1,339 bytes；SHA-256 `9423dd069c0b36e154588bd5a5ab15cf5b3735cae60e01312202cef4c7af4856` |
| stderr | 35 bytes；SHA-256 `e7266701f226f730bccd6a2ea4ec1ca115fb6eb9ab9035ca54a497bba6804dab` |

stdout 完整记录 Forge 检查 pnpm 12.7.0、Vite 五个 target build、win32 x64 copy/native dependency/finalize 和 postPackage hook 全部成功。stderr 的唯一内容是 pnpm lifecycle 命令回显：

```text
$ node scripts/package-desktop.mjs
```

它不是错误、warning 或 stack trace。原始双流、started、result 和 PID observations 均保存在 `package-resume-2\package`。会话观察到 27 个任务 PID；退出时残留 0。

## 6. 静态产物核对

package 退出 0 后只读取同一份不可变产物。没有执行、导入或启动 `Maris.exe`、app.asar 中的程序、Electron renderer/main、Playwright 或 sidecar。

| 产物 | bytes | SHA-256 |
| --- | ---: | --- |
| `out/Maris-win32-x64/Maris.exe` | 246,032,896 | `149ccd6e2d71a8945ffef4ecba81e5121bc19c4816331ed5bcb6e72948174199` |
| `out/Maris-win32-x64/resources/app.asar` | 758,263 | `c38cd0c7c5b42e4576d051f936d2942cd6a180b4386c62687a1886e991ae22f6` |

`out/Maris-win32-x64` 共 140 个文件、386,491,445 bytes。逐文件相对路径、bytes 和 SHA-256 在 `static/out-manifest-v4.tsv`。该清单同时覆盖 Electron runtime 文件、EXE、app.asar 和额外 resources；没有启动其中任何文件。

### 6.1 production fuses

使用已安装 `@electron/fuses` 的只读 `getCurrentFuseWire()` 读取 Maris.exe：

| 索引 | 冻结含义 | 期望 | 实际 |
| ---: | --- | ---: | ---: |
| 0 | RunAsNode | 48 / DISABLE | 48 |
| 1 | EnableCookieEncryption | 49 / ENABLE | 49 |
| 2 | EnableNodeOptionsEnvironmentVariable | 48 / DISABLE | 48 |
| 3 | EnableNodeCliInspectArguments | 48 / DISABLE | 48 |
| 4 | EnableEmbeddedAsarIntegrityValidation | 49 / ENABLE | 49 |
| 5 | OnlyLoadAppFromAsar | 49 / ENABLE | 49 |

Fuse wire version 为 1；冻结前六项全部匹配。额外可见索引 6/7/8 分别为 48/49/49，按实际值记录，没有把它们改写成冻结合同的一部分。读取 API 没有调用 `flipFuses()`，EXE 未修改。

### 6.2 H1 Python resources

静态检查直接调用既有 `discoverPythonResources(workspace)` 得到冻结 source allowlist，并与 package `resources` 中除 app.asar 外的全部文件比较：

- 期望 67，实际 67；
- missing 0、extra 0、bytes/hash mismatch 0；
- `.pyc`、`.pyo`、`.pyd`、`.egg-info`、`__pycache__`、tests、`.pytest_cache`、build、dist、scratch 命中 0；
- `alembic.ini`、`migrations/env.py`、七个 revision 和 `src/wife_system/**/*.py` 均与固定 source 字节一致。

最终清单为 `static/python-resources-v4.tsv`。H1 manifest 语义保持 67 项且没有扩大 allowlist。

### 6.3 app.asar 与污染扫描

app.asar 只读列举为 18 个 archive entries，其中 11 个普通文件、0 links、0 unpacked files。逐文件 bytes 和 SHA-256 为 `static/asar-manifest-v4.tsv`。

对 app.asar 普通文件内容和外部 Python resources 执行高置信模式扫描，并对 out/archive 路径执行禁止项扫描：

- package-resume、R0 driver、E4 任务根等任务 evidence：0；
- Windows/macOS/Linux 用户路径：0；
- PEM private key：0；
- OpenAI 风格密钥、GitHub token、AWS access key、JWT：0；
- Python bytecode、egg-info、cache、tests 和 scratch 路径：0。

内容命中 0、路径命中 0，总命中 0。扫描只记录分类和路径，不输出任何候选秘密内容。

### 6.4 staging 和 transition artifacts

`.maris-staging` 不存在；desktop 下 staging、backup、lock、temporary sibling 和 transition artifacts 均为 0。现有 wrapper 的 finally 已完成清理，成功 `out` 按任务要求保留。

## 7. 静态读取器修正记录

任务卡允许静态读取逻辑错误在 `package-resume-2` 内修正并重新读取同一份不可变产物；全部失败和修正均保留：

1. 初版已验证 EXE/out/fuses/Python resources，随后把 app.asar POSIX 路径直接传给 Windows asar API，读取 `.vite/build/companion.js` 时返回 `not found`。`reader-failure.json`、`execution.json` 和原脚本均保留。
2. v2 生成时换行被写成字面转义；v2 **未执行**，脚本仍保留。`correction-2.json` 明确记录生成错误。
3. v3 修正 Windows archive lookup 后完整运行。它正确通过 artifact、fuse、67 项 H1、内容扫描和 staging，但全局路径规则把三个必要的 `.vite/build/*.js` production bundles 误判成 build cache，退出 3。完整 `result-v3.json` 和日志保留。
4. v4 只从全局 archive 路径污染规则移除 `build/dist`；Python resource 的 build/dist 禁止规则保持不变。v4 退出 0，七项静态 gates 全为 true，stderr 0。

创建 v4 后，一个仅用于显示验证结果的 PowerShell 命令使用了当前 PowerShell 不支持的 `Select-Object -SkipWhile`，因此该命令末尾返回参数错误；v4 文件与 correction-3 已在错误前 create-new 写入。随后的纯只读检查确认 v4 的 Python 规则仍含 build/dist、全局规则已移除它们、目标为 `result-v4.json`，再执行 v4 成功。该 PowerShell 显示错误没有运行或改变 package。

以上静态重读不计为 package 重试；真实 package 始终 1/1，产物在所有静态读取期间未修改。

## 8. 资源和环境收口

- package 会话的 27 个已知任务 PID 残留为 0。
- 最终固定 C 根自有 pnpm、Node、Forge、Electron、Maris、Python/Pythonw 进程为 0。
- process-local PATH 和 `ELECTRON_CACHE` 已在 finally 原样还原。
- User PATH 和 Machine PATH 前后相同；没有写永久 PATH、注册表、代理、安全软件或 ACL。
- 固定 source、lock、node_modules、Electron dist 和 PKG-R1 evidence 终点复算均匹配。
- 成功 out 保留；staging 与临时 transition 已清理。
- 没有删除 workspace、node_modules、cache、旧 evidence 或成功 package 产物；没有终止非任务进程，也没有按 conhost 名称进行统计或清理。

## 9. 未运行范围、失败、skip 和 warning

明确 `not_run`：app.asar 动态启动、最终 Maris.exe 启动、Electron、Playwright、Python sidecar、Host/数据库、OpenClaw、微信、DeepSeek、P4-C12、独立测试。没有启动其他智能体。

- package failed：0；真实退出码 0。
- 静态最终 failed：0；v4 七项 gates 全通过。
- tests：本任务没有测试套件，0 run；不存在把 skip 计为通过。
- package stderr：只有 pnpm lifecycle 命令回显，不是 warning。
- 执行方错误：一次 pre-launch PowerShell 表达式错误；实际 package 启动前停止。
- 静态读取错误/误报：初版 asar 分隔符错误、未执行的 v2 生成错误、v3 对 production bundle 的路径误报；全部保留并按任务授权只读修正。
- 最终只读 `git diff --check` 退出 0、无 whitespace error；Git 仅提示执行角色日志在未来由 Git 触碰时可能把 LF 转成 CRLF。三个交付文件的尾随空格行均为 0；没有 Git 写操作。

## 10. 仓库交付和复算算法

仓库内只有三个任务交付：

1. [PKG-R2 运行说明](b7-r1-e4-pkg-r2-running.md)；
2. [执行智能体日志](coordination/agents/executor.md)；
3. [198 项 PKG-R2 source manifest](../apps/desktop/b7-r1-e4-pkg-r2-source.sha256)。

PKG-R2 source manifest 与 PKG-R1 manifest 字节一致，198 entries、20,165 bytes，SHA-256 `04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1`。

三个仓库交付文件的最终逐文件摘要写入外部 `package-resume-2\repository-delivery.sha256`。为了避免报告摘要自引用，报告不把自己的最终 SHA 写回自身；逐文件值和组合摘要随最终交付消息发布。

外部 evidence 最终为 41 个文件；`delivery-evidence.sha256` 覆盖其余 40 个文件并排除自身。仓库交付清单和外部 evidence 清单均使用：

```text
relative POSIX path<TAB>bytes<TAB>lowercase SHA-256<LF>
```

路径按 `StringComparer.Ordinal` 排序，UTF-8 无 BOM；清单原始字节的 SHA-256 是组合摘要。外部清单生成后逐行重新检查文件存在、bytes 和 SHA-256，差异必须为 0。

node_modules 冻结聚合沿用起点算法：相对 node_modules 的 POSIX 路径按既有 PowerShell排序，每行记录 path、bytes、文件 SHA-256 和 LF，12,451 行；package 前后使用同一算法。

本交付只是执行方 package 与静态门禁结果，状态最多为 `review / finished`；不表示 app.asar、最终 EXE、P4-C12、P4-B 或发布已经验收通过。
