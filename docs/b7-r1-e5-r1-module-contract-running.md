# P4-B7-R1-E5-R1 module Profile 合同返修运行说明

## 结论

- 任务：`P4-B7-R1-E5-R1`
- 状态：`blocked / finished`
- 原缺陷：`P4-E5-MODULE-001`
- 新阻塞：desktop Profile ID runtime parser 不接受冻结的 canonical Profile 语法 `module.local@major`
- package：0/1，未启动
- 最终 EXE：0/1，未启动
- P4-C12：未启动

本轮已把 daily finance contribution 和三个同源单元 fixture 从错误别名改为冻结的真实 Profile `daily_finance.assistant@1`，并补上旧别名必须 fail closed、major version 不兼容必须拒绝的 registry 反例。OpenAPI generated drift、TypeScript `tsc --noEmit` 和 desktop lint 均通过。

首次定向 Vitest 随后发现：`compileRegistry()` 在模块求交之前用 `^[a-z][a-z0-9_.-]{0,139}$` 校验 Profile ID，该表达式不允许 canonical ID 必需的 `@major` 后缀。因此 registry 与 composition root 测试在解析 `daily_finance.assistant@1` 时抛出 ZodError。Python Host 的冻结语法是 `module.local@major`，daily finance 真实 Profile 也是 `daily_finance.assistant@1`。

任务卡禁止修改 `apps/desktop/src/modules/registry.ts`，并规定任何产品断言失败立即停止、不得进入 package。执行方因此保留失败现场，不扩大范围，不增加 alias、fallback、宽松匹配或自动改写，也不继续完整 Vitest、Python 回归、package 或最终 EXE。

## 起点门禁

- control 版本：`2026-09-29T03:33:00+08:00`
- control SHA-256：`6dd1768f073bad07718956b14e5200dace2586ed0f96183fad8c25e7b346e0be`
- 起点清单：258 entries、258 unique、0 missing、0 mismatch
- 起点清单 SHA-256：`8898793403f5bcc8aafbf969173a870e84f173b8c7cbb96070436840eab63be0`
- Git index staged paths：0
- 旧 `.claude/`、`.pnpm-store/`、E4/E5 evidence、package 和 profile：保持原样

## `P4-E5-MODULE-001` 根因与修复

旧生产链的值为：

| 层 | 旧值或行为 |
| --- | --- |
| Python Host Profile | `daily_finance.assistant@1` |
| D11 冻结桌面引用 | `daily_finance.assistant@1` |
| desktop contribution | `daily_finance.default` |
| registry fixture | `daily_finance.default` |
| composition root fixture | `daily_finance.default` |
| HostClient fixture | `daily_finance.default` |
| `intersectModules()` | Profile 不精确匹配时 fail closed |

同源 fixture 复制了 production contribution 的错误别名，因而原测试同时伪造了 Host 响应和桌面期望，错误地形成自洽交集，掩盖了真实 Host 合同。

本轮修改：

1. `apps/desktop/src/modules/daily-finance/contribution.ts` 的 `agentPanel.profileId` 改为 `daily_finance.assistant@1`。
2. registry、composition root 和 HostClient fixture 改为真实 Profile。
3. registry 测试用真实 Profile 证明当前 major 可以加载。
4. registry 测试动态构造旧别名，证明旧值仍返回空交集；源码和测试中不保留旧别名字面量。
5. registry 测试继续证明 module major version `2.0.0` 被拒绝。
6. composition root 使用生产同形 Host 摘要，同时带一个未知模块，并断言公开列表只包含 `daily_finance`。
7. HostClient 的严格 DTO、401 single-flight refresh/retry、session revoke 和额外字段拒绝断言保持不变。

`rg` 在 `apps/desktop/src` 和 `apps/desktop/tests` 中对旧别名字面量的结果为 0 命中。

## 新发现的合同阻塞

准确代码位置：

- Python canonical ID：`src/wife_system/host/contracts.py` 的 `CANONICAL_ID_PATTERN`，要求 `module.local@major`。
- 真实 Profile：`src/wife_system/modules/daily_finance.py`，值为 `daily_finance.assistant@1`。
- desktop parser：`apps/desktop/src/modules/registry.ts` 的 `profileId` 正则，只允许小写字母、数字、下划线、点和连字符，不允许 `@`。

因此 contribution 修复后，执行路径在 `compileRegistry()` 的 Zod schema parse 阶段失败，还没有进入 `intersectModules()`。这与 E5-FINAL 的旧故障不同：旧 package 可以编译 registry，但以错误别名求交得到空数组；本轮正确 ID 会被更早的 desktop runtime schema 拒绝。

执行方没有修改该 parser，因为它不在本任务允许写入范围，并且任务卡明确禁止修改 registry 算法。后续任务若由总控派发，必须让 desktop canonical Profile parser 与 Python `CANONICAL_ID_PATTERN` 对齐，同时保留精确 ASCII、无 trim/lowercase/Unicode normalization、旧别名失败关闭和全局冲突检查。

## 静态与执行方回归

| 顺序 | 检查 | 结果 | passed | failed | skipped | warning/说明 |
| ---: | --- | --- | ---: | ---: | ---: | --- |
| 1 | 修改文件字面量与 diff 检查 | 通过 | 不适用 | 0 | 0 | Git 仅提示既有 LF→CRLF 行尾转换 |
| 2 | 固定 pnpm 调用 `check:generated` | 编排失败 | 0 | 0 | 0 | 用户级 pnpm store operation lock 拒绝访问；项目脚本未启动，没有安装依赖 |
| 3 | 固定 Node 直接运行 OpenAPI drift 脚本 | 通过 | 1 gate | 0 | 0 | `openapi-typescript 7.13.0`，生成结果匹配 |
| 4 | TypeScript `tsc --noEmit` | 通过 | 1 gate | 0 | 0 | stderr 0 bytes |
| 5 | desktop lint | 通过 | 1 gate | 0 | 0 | `desktop lint checks passed` |
| 6 | registry、composition root、HostClient 定向 Vitest | 失败并停止 | 3 | 3 | 0 | 3 files、6 tests；registry 2 failed、composition root 1 failed、HostClient 3 passed |
| 7 | desktop 完整 Vitest | `not_run_after_product_assertion` | 0 | 0 | 0 | 按停止条件未运行 |
| 8 | desktop sidecar/module Python 定向测试 | `not_run_after_product_assertion` | 0 | 0 | 0 | 未运行 |
| 9 | Python compileall | `not_run_after_product_assertion` | 0 | 0 | 0 | 未运行 |
| 10 | pip check | `not_run_after_product_assertion` | 0 | 0 | 0 | 未运行 |

定向 Vitest 的首类失败信息是 Profile ID Zod `invalid_format`，正则为 `^[a-z][a-z0-9_.-]{0,139}$`。三个 HostClient 用例通过，说明真实 Profile DTO 不会降低 HostClient 的严格响应校验、401 refresh/retry 或错误边界。

## 新 C 盘现场

- 新根按 create-new 建立，没有覆盖旧 E4/E5 现场。
- 从起点快照的路径集合复制当前仓库 258 项文件：258/258、0 copy failure。
- workspace copy manifest SHA-256：`6341e5eccc6328a384f8037e6aa39964674b4e228aab32c40dd542e56ed5ac5e`。
- 固定 Node 24.21.0 SHA-256：`ba4e6d110e8c1592a1ecd390f6b05f3da124b13871a5be62b341a07a853c6c32`。
- 固定 pnpm 12.7.0 native SHA-256：`3e1a5bb3aba371d4c1bb5bb87f8ef1bd8dea41e0cd39d4bddf7c3dfbaae665ce`。
- `pnpm-lock.yaml` SHA-256：`5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。
- node_modules 以只读意图的 junction 指向已验证的冻结 E4 workspace 依赖；没有联网安装或更新依赖。
- 没有复制旧 out、profile、数据库、evidence 或动态结果。

由于定向产品断言失败，新的 `out`、profile 和数据库均未创建；package 和最终 EXE 的 evidence 目录也未创建。

## Package 与最终 EXE

| 项目 | 预算 | 实际次数 | 结果 |
| --- | ---: | ---: | --- |
| `pnpm run package` | 1 | 0 | 未解锁；定向产品断言先失败 |
| 最终 `Maris.exe` | 1 | 0 | 未解锁；package 未运行 |
| `runtime.recover()` | 1 | 0 | 最终 EXE 未运行 |

因此没有新 EXE/app.asar/out 摘要、fuse/resource/污染动态结果，也没有窗口、bridge、runtime/modules/recover、隐私、退出或 Tray 结果。不得把这些项目写成通过或失败；准确状态都是 `not_run_after_product_assertion`。

## 资源收口

- 新现场相关残留任务进程：0。
- 新现场产品进程：0。
- 新 out：不存在。
- 新 profile：不存在。
- 新数据库：不存在。
- package 尝试：0。
- 最终 EXE 尝试：0。
- 旧 E4/E5 package、workspace、profile、evidence 和工具没有被覆盖或删除。
- 没有修改用户/系统 PATH、registry、代理、安全软件、ACL 或 Docker 设置。

## 文件边界

允许且实际修改的产品/执行方测试文件为 4 个：

1. `apps/desktop/src/modules/daily-finance/contribution.ts`
2. `apps/desktop/tests/unit/registry.test.ts`
3. `apps/desktop/tests/unit/composition-root.test.ts`
4. `apps/desktop/tests/unit/host-client.test.ts`

协调交付为本运行说明、`apps/desktop/b7-r1-e5-r1-source.sha256` 和执行智能体日志。相对 258 项起点为 253 unchanged、5 changed、0 missing；5 个 changed 是四个允许的产品/执行测试文件和执行智能体日志。另新增本运行说明与 source manifest 两项允许交付。没有修改 `registry.ts`、Python Host、认证、Supervisor、IPC、preload、renderer、依赖、lock、Forge、staging、migration、接口冻结、独立测试、control、overview 或其他角色文件；没有执行 Git 写操作。

最终普通文件摘要：

| 文件 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `apps/desktop/src/modules/daily-finance/contribution.ts` | 596 | `5d5a72fb8a46bbcd18b7945bf0aaca610731ca096be8df32805b476b8e1d09b2` |
| `apps/desktop/tests/unit/registry.test.ts` | 1,261 | `08f8ad4190fcf62b2bc5b323029cea4563639edfee985e50073b1dc44a5ba375` |
| `apps/desktop/tests/unit/composition-root.test.ts` | 2,197 | `9b196a4cc4819aa8ee83ffa6111e903455cb4027a6b08340343ab588b0e14dcc` |
| `apps/desktop/tests/unit/host-client.test.ts` | 2,017 | `3d81cf9fac4ff6422ecc7ba573cf0384a05de5ca248433a9f3eed3a49d5598b3` |
| `apps/desktop/b7-r1-e5-r1-source.sha256` | 27,106 | `74b66ba69e71dcfec23dd7490a46290cd75a1d30c56841bb7d6bf72a822c88da` |
| `docs/coordination/agents/executor.md` | 216,592 | `dfb428e3193d6daf8afdcf8e182a48f81b21e6fc9509b3a9352b1b1c220ca9e9` |

运行说明自身的最终摘要与上述六项一起写入受限外部 `repository-delivery.sha256`，避免在文件正文中形成自引用摘要。

## Evidence 与复算

外部 evidence 包含：起点与 workspace 复制证明、OpenAPI/tsc/lint 原始 stdout/stderr、定向 Vitest 原始 stdout/stderr、失败分类和资源收口。仓库 source manifest 为 258 entries、258 unique、0 missing、0 mismatch，SHA-256 `74b66ba69e71dcfec23dd7490a46290cd75a1d30c56841bb7d6bf72a822c88da`。最终外部清单按相对路径序数排序，每行使用：

```text
relative/path<TAB>bytes<TAB>sha256
```

清单使用 UTF-8 无 BOM；复算时逐文件检查存在性、字节数和 SHA-256。最终外部 evidence 为 12 entries、12 unique、0 mismatch，清单 SHA-256 `a026bb620a89b710ff73ca789c7ae522be649695eba986c56b5a4a1678610827`。仓库交付清单在三项文件冻结后生成。

## 未运行与交接

- 独立测试和 P4-C12：未运行。
- 真实微信和 DeepSeek：未运行。
- Docker/PostgreSQL：未运行。
- 真实账户、密钥和个人财务数据：未读取。
- 高保真前端开发：未开始。

执行智能体以 `blocked / finished` 停止。总控需要先冻结 desktop canonical Profile parser 的窄修复范围，再决定新的静态回归、package 和最终 EXE 预算；当前执行方不得自行修改 `registry.ts`、重跑定向测试、进入 package 或创建新的动态任务。
