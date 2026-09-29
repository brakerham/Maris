# P4-B7-R1-E5-R2 canonical Profile parser 返修运行说明

## 结论

- 任务：`P4-B7-R1-E5-R2`
- 修复缺陷：`P4-E5-PROFILE-PARSER-002`
- 状态：`blocked / finished`
- parser 实现与 package 前回归：通过
- package：1/1，exit 1，未重试
- 最终 EXE：0/1，未解锁
- P4-C12 与独立验收：未启动

桌面 registry 的 Profile parser 已精确同步 Python Host 冻结的 ASCII 语法 `module.local@major`。公开 `compileRegistry()` 与 `intersectModules()` 行为覆盖了全部正反例、64/65 字符边界、严格求交及所有全局冲突；E5-R1 的真实 contribution 和三个合同 fixture 保持正确。OpenAPI、TypeScript、lint、22 项定向 Vitest、52 项完整 desktop Vitest、29 项 Python 相邻回归、compileall 和 pip check 全部通过。

唯一 package 于依赖安装阶段失败。新 C 盘 workspace 的 `node_modules` 是指向冻结 E4 依赖树的 Junction，而 pnpm 的 `node-linker=hoisted` 要求 workspace hoist 目录是普通目录。package 退出码 1 后按任务卡立即停止，没有修复后重跑，也没有启动最终 EXE。

失败前 pnpm 已通过 Junction 改写冻结依赖树中的 43 个 `.bin` shim；因此本任务除 package 失败外还形成了可复算的依赖输入漂移。执行方没有删除、恢复或覆盖该现场，已把 package 原始输出、43 项逐文件差异、package 前后聚合与资源收口固化在 create-new evidence 中，交由总控审阅。

## 起点门禁

- control 版本：`2026-09-29T08:37:19+08:00`
- control SHA-256：`bb2660c64d579009a46859157dad8f570a5e75962b7b3e18a820ef90ac9ffaab`
- 起点清单：262 entries、262 unique、0 missing、0 mismatch
- 起点清单 SHA-256：`ef39bc87953701db7e076e07b54e811cb3191915ecc8bcaac342328c1a50e36c`
- Git index staged paths：0
- 起点未跟踪项：`.claude/`、`.pnpm-store/`，保持未暂存
- 旧 E4/E5/E5-R1 package、profile、database 和 evidence：开工时只读核对，没有删除或覆盖

## Parser 合同与修复

Python `src/wife_system/host/contracts.py` 的冻结表达式为：

```text
^[a-z][a-z0-9_]{0,63}\.[a-z][a-z0-9_]{0,63}@(0|[1-9][0-9]*)$
```

`apps/desktop/src/modules/registry.ts` 的 `profileId` 已改为语义相同的 TypeScript 正则：

```ts
/^[a-z][a-z0-9_]{0,63}\.[a-z][a-z0-9_]{0,63}@(0|[1-9][0-9]*)$/
```

实现没有使用 `\d`、Unicode flag、trim、lowercase、normalization、split 后容错、隐式 major、alias、fallback 或自动迁移。`intersectModules()` 没有修改，仍按 Profile 精确相等、module major、API prefix、setting version 和全局唯一性失败关闭。

公开行为证明：

- 接受 `daily_finance.assistant@1` 与 `a.b@0`；
- module/local 各 64 个 ASCII 字符时接受，各 65 个字符时拒绝；
- 拒绝缺少 major、前导零、负数、小数、多个 `@`、连字符、多个点、大写、前后空白、全角点和全角 `＠`；
- 正确 Profile 可加载 `daily_finance`；动态构造的旧形状、module major 2、缺 API prefix 和 setting version 不兼容均返回空交集；
- extra field、module/Profile/route/setting/appearance 冲突均原子拒绝。

`apps/desktop/src` 与 `apps/desktop/tests` 对旧别名字面量 `daily_finance.default` 为 0 命中。新 C 盘工作副本中正确 Profile 在 production/fixture 的可见命中数为 9。

## E5-R1 改动保留

E5-R1 的四项正确改动均未在 R2 中再次修改：

| 文件 | 保留内容 | SHA-256 |
| --- | --- | --- |
| `apps/desktop/src/modules/daily-finance/contribution.ts` | production Profile 为 `daily_finance.assistant@1` | `5d5a72fb8a46bbcd18b7945bf0aaca610731ca096be8df32805b476b8e1d09b2` |
| `apps/desktop/tests/unit/registry.test.ts` | 真实 Profile fixture；R2 在同文件补 parser 与交集回归 | `3fb341f708b7a094d5fcb8af4d1a6a3c7b1e7caac96ca88719cd4f2753a00778` |
| `apps/desktop/tests/unit/composition-root.test.ts` | production 同形 Host 摘要只公开 `daily_finance` | `9b196a4cc4819aa8ee83ffa6111e903455cb4027a6b08340343ab588b0e14dcc` |
| `apps/desktop/tests/unit/host-client.test.ts` | 严格 DTO、401 single-flight、revoke 与 extra-field 拒绝 | `3d81cf9fac4ff6422ecc7ba573cf0384a05de5ca248433a9f3eed3a49d5598b3` |

相对 R2 起点，实际产品/测试修改只有 `registry.ts` 和 `registry.test.ts`。contribution、composition-root 与 HostClient 文件保持起点字节一致。

## 静态与执行方回归

| 顺序 | 检查 | 结果 | passed | failed | skipped | warning/说明 |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 1 | 格式与 `git diff --check` | 通过 | 1 gate | 0 | 0 | Git 仅提示 LF→CRLF 的工作区行尾 warning |
| 2 | OpenAPI generated drift | 通过 | 1 gate | 0 | 0 | `openapi-typescript 7.13.0`，生成结果匹配 |
| 3 | TypeScript `tsc --noEmit` | 通过 | 1 gate | 0 | 0 | exit 0 |
| 4 | desktop lint | 通过 | 1 gate | 0 | 0 | `desktop lint checks passed` |
| 5 | registry/composition-root/HostClient 定向 Vitest | 通过 | 22 | 0 | 0 | 3 files |
| 6 | desktop 完整 Vitest | 通过 | 52 | 0 | 0 | 12 files |
| 7 | Host registry/runtime/sidecar/production Python 相邻回归 | 通过 | 29 | 0 | 0 | 1 个 Starlette/AnyIO alias 弃用 warning |
| 8 | Python compileall | 通过 | 1 gate | 0 | 0 | exit 0；生成的 14 个 `__pycache__` 已从新 workspace 清理 |
| 9 | `pip check` | 通过 | 1 gate | 0 | 0 | `No broken requirements found` |
| 10 | 旧别名/正确 Profile 字面量核对 | 通过 | 1 gate | 0 | 0 | 旧别名 0；正确 Profile 9 |

初次静态 driver 使用 PowerShell 自动变量 `$args` 作为函数参数，导致三次无参数 Node 进程和零字节日志；它们不计为通过。参数改名后只重跑对应静态脚本，未启动 package 或产品。package 前另有两个只读依赖摘要 reader 编排错误，均保留原记录并离线修正，没有修改产品、依赖或预算。

## 新 C 盘现场与固定输入

新现场：`C:\MarisE5R2\E5-R2-20260929-0911`，按 create-new 建立；workspace、evidence 与 package 日志均未复用旧任务结果。

- 当前固定 source 集复制：262/262、0 copy failure；复制清单 SHA-256 `8cd02722094d3f9e0f40283b8212be351a9d01af13c7eee5cbd97467b1fe34c2`。
- package 后复算工作副本：262 files、0 missing、0 mismatch；规范聚合 `5ad4f919d77df8af25a1b877f8b5ce04d2c312f69e86659bcf67b92225c75dbe`。
- Node SHA-256：`ba4e6d110e8c1592a1ecd390f6b05f3da124b13871a5be62b341a07a853c6c32`。
- pnpm SHA-256：`3e1a5bb3aba371d4c1bb5bb87f8ef1bd8dea41e0cd39d4bddf7c3dfbaae665ce`。
- process-local shim SHA-256：`57785cc51fff3a94b68815e46f48a400f1cb016f9edc82d2cb9606cbdb088bdf`。
- `pnpm-lock.yaml` SHA-256：`5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。
- package 前 node_modules：12,451 files、570,581,590 bytes、聚合 `f06ce306456134f7f78176e64d3f9a7e54133607d3e9202ff6bb1a9fcbf800c7`，与冻结值一致。
- Electron dist：73 files、385,243,397 bytes、聚合 `ffb4b389d5c454ca139cb6384f5ebb3d20633cf000960a8aa1b6c1794c9ebf8f`，package 前后一致。
- package 前 out/profile/database 均不存在；没有复制旧 owner session、PID、端口或动态结果。

## 唯一 package 失败

| 字段 | 结果 |
| --- | --- |
| 实际次数 | 1/1 |
| 开始 | `2026-09-29T09:24:38.5201032+08:00` |
| 结束 | `2026-09-29T09:24:46.7630309+08:00` |
| 时长 | 7,971 ms |
| 超时 | false |
| exit code | 1 |
| 已观察任务进程 | 2；终点 0 |
| stdout | 0 bytes；SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| stderr | 728 bytes；SHA-256 `769425f1552094af526a970acb2035339546e27843871b2e8a11bb76a57f6c6f` |
| 首失败 | `workspace_hoist_directory_not_real_directory` |

pnpm 原始错误为：

```text
Failed to create directory at "C:\MarisE5R2\E5-R2-20260929-0911\workspace\node_modules": workspace hoist directory is not a real directory
```

`.npmrc` 使用 `node-linker=hoisted`。新 workspace 的 `node_modules` 为 Junction，目标是 `C:\MarisE4\E4-20260928-1255\workspace\node_modules`，所以 pnpm 在 `installing dependencies` 阶段拒绝把它当作 hoist 目录。stderr 的进度最高显示 `downloaded 94, added 0`；没有成功安装依赖，项目 `.pnpm-store` 在 package 起点后 0 个文件改动。执行方没有把该字段推断为已发生或未发生外网访问，外网活动本身未独立观测。

任务卡规定任何真实 package 失败都必须安全收口且不得第二次打包。因此 package 预算 1/1 已耗尽，执行方没有把 Junction 改为普通目录、没有安装依赖、没有重试，也没有修改用户或系统 PATH。

## 依赖副作用与产物状态

package 前后逐文件复算发现：

- 冻结 node_modules：12,451 files、0 missing、43 mismatch；总字节从 570,581,590 增至 570,581,805。
- 43 个内容漂移均为 `.bin` 启动 shim，每项增加 5 bytes；另有 129 个文件时间戳晚于 package 起点。
- package 后 node_modules 聚合：`d3d7728fab1f4b26d7cf9ec6e5a025a06db9ac6d2a33b43ab6f9fb47a4d223aa`。
- 逐项漂移清单 SHA-256：`7cb9012259e7d026add439e7e12e54e2da4010011fbf5ba608003a3a67640c6c`。
- Electron dist 73/73、0 mismatch；聚合仍为 `ffb4b389d5c454ca139cb6384f5ebb3d20633cf000960a8aa1b6c1794c9ebf8f`。
- C 盘 workspace source 262/262、0 mismatch；项目 `.pnpm-store` 起点后 0 项改动。

该副作用发生在旧 E4 冻结依赖目标中，违反了本任务对旧现场只读的预期。执行方遵守禁止恢复/覆盖其他现场的边界，没有执行 Git restore/reset、文件删除、重新安装、volume/prune 或任何修复性写入。总控在后续任务中不能继续把该 node_modules 聚合作为原冻结值使用，必须先决定隔离环境的重新供应方式。

package 没有生成：

- `out`、`dist`、`release`、staging 或 transition artifact；
- 新 `Maris.exe` 或 `resources/app.asar`；
- 可供检查的 production fuses、67 项 Python resources 或 app.asar 内容。

因此 fuses、resource allowlist、app.asar Profile 字面量、package 污染扫描和产物隐私检查准确记为 `not_run_after_package_failure`，不写成通过。

## 最终 EXE 与资源收口

| 项目 | 预算 | 实际次数 | 结果 |
| --- | ---: | ---: | --- |
| `pnpm run package` | 1 | 1 | exit 1；不重试 |
| 最终 `Maris.exe` | 1 | 0 | `not_run_after_package_failure` |
| `runtime.recover()` | 1 | 0 | 最终 EXE 未运行 |

窗口、preload bridge、Node 隔离、runtime、modules、毛毛状态、openMain、recover、DOM/storage/log 隐私、Windows Application/Code Integrity、自然退出和 Tray 检查均未运行。没有 app.asar 预跑、fixture 运行或产品启动。

收口状态：

- E5-R2 任务进程：0。
- 产品、Electron、Maris.exe 和受管 sidecar 进程：0。
- 新 out/staging/release/transition artifact：0。
- 最终 EXE 尝试：0/1。
- Git index staged paths：0；没有 Git 写操作。
- 没有读取真实账户、密钥、真实数据库或个人财务数据。

## 文件边界与摘要

相对 262 项起点为 259 unchanged、3 changed、0 missing。三个 changed 均在允许范围：

1. `apps/desktop/src/modules/registry.ts`
2. `apps/desktop/tests/unit/registry.test.ts`
3. `docs/coordination/agents/executor.md`

新增两项允许交付：本运行说明与 `apps/desktop/b7-r1-e5-r2-source.sha256`。没有修改 Python Host、认证、Supervisor、IPC、preload、renderer、依赖声明、lock、Forge、migration、接口冻结、独立测试、control、overview、其他角色或 Git 状态。

最终普通文件摘要：

| 文件 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `apps/desktop/src/modules/registry.ts` | 2,882 | `1965f28dd092e070cabe2fec36c634588c3875f0af49bcd70ae45c252abb080c` |
| `apps/desktop/tests/unit/registry.test.ts` | 3,945 | `3fb341f708b7a094d5fcb8af4d1a6a3c7b1e7caac96ca88719cd4f2753a00778` |
| `docs/coordination/agents/executor.md` | 221,987 | `f4df31b9a4d8bce2063e08a6bece6bf95def038c1778be676399d2348a18da13` |
| `apps/desktop/b7-r1-e5-r2-source.sha256` | 27,309 | `025d46df0f31d1f4fd87100e01209f2e44b8c7dba6f232af52e5ac7a6e2d9fb4` |

运行说明自身的最终摘要与上述四项一起写入外部 `repository-delivery.sha256`，避免在正文中形成自引用摘要。

## Evidence 与复算

仓库 source manifest 使用起点 262 路径集合，按相对路径 Ordinal 排序，每行格式：

```text
relative/path<TAB>sha256
```

UTF-8 无 BOM，行尾为 LF。最终 source manifest 为 262 entries、262 unique、0 missing、0 mismatch，SHA-256 `025d46df0f31d1f4fd87100e01209f2e44b8c7dba6f232af52e5ac7a6e2d9fb4`。

外部 evidence 位于 `C:\MarisE5R2\E5-R2-20260929-0911\evidence`，包含：workspace 复制清单、固定工具摘要、所有静态/测试 stdout 与 stderr、package 原始日志和结构化结果、package 前依赖清单、package 后完整性复算、43 项漂移清单、失败分类与资源收口。外部 evidence manifest 排除自身与仓库 delivery manifest，使用 `relative/path<TAB>bytes<TAB>sha256`、UTF-8 无 BOM 和 LF。最终为 42 entries、42 unique、0 mismatch，清单 SHA-256 `ca8cf0bef3e506b7a10a7995ce791d3291ea6bd2d730d74c09dc147fea6b7b4b`。

外部 `repository-delivery.sha256` 在仓库交付冻结后生成，覆盖两项修改文件、执行日志、运行说明和 source manifest。

## 未运行与交接

- 独立测试、测试智能体、技术顾问和 P4-C12：未启动。
- 高保真前端、OpenClaw、微信和 DeepSeek：未启动。
- Docker/PostgreSQL：未启动。
- 真实账户、真实密钥、真实个人财务数据：未读取。
- 最终 EXE、recover 和产品动态门禁：未运行。

执行智能体以 `blocked / finished` 停止。parser 代码与执行方回归已经通过，但 package 预算已耗尽，且旧冻结 node_modules 已发生 43 项可复算漂移。后续必须由头脑风暴总控审阅本次失败与环境副作用，发布新的纯环境续段或其他明确任务；当前执行方不得自行重跑 package、启动最终 EXE 或 P4-C12。
