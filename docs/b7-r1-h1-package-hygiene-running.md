# P4-B7-R1-H1 Python package resource 静态 staging 运行说明

## 1. 结论

- 任务状态：`review / finished`。
- 已实现 Python runtime source allowlist、确定性 staging、稳定 manifest、临时 sibling 验证、正式目标替换、失败回滚和 package 前后清理 wrapper。
- 专属 staging 与相邻 toolchain 测试：2 files、10 passed、0 failed、0 skipped。
- TypeScript、desktop lint、两个 Node 脚本语法检查和 Forge CLI metadata 静态解析均通过。
- 真实源码静态 staging：67 个 allowlisted source、67 个 payload 文件、0 个禁止文件、0 个必需文件缺失；manifest 不含工作区绝对路径；验证后 staging 已清理。
- source allowlist staging 与静态测试已通过；Electron/Forge package、app.asar、fuse、最终 resources 扫描、sidecar 和 EXE 启动均为 `not_run`。该结果没有解除 P4-B 的 Electron 环境阻塞，也不构成发布验收。

## 2. 起点门禁与边界

| 项目 | 结果 |
| --- | --- |
| 最新 control | `2026-09-28T00:06:00+08:00`；执行智能体为 H1 唯一负责人 |
| H1 起点 | 209 matched、0 mismatch、0 missing；清单 SHA-256 `24dbffd395af61c06a5ac3424163879084d2397576f7da4e4658aadccb1b3921` |
| E2-R1 source | 194 matched、0 mismatch、0 missing；manifest SHA-256 `d4a6619ff0769a6d329739543013c4ab279cca515613fa6d5cef88ea32edf715` |
| 起点环境 | 旧任务 Electron、Maris、项目 Python 进程为 0；`node_modules=false`、`.maris-staging=false` |
| Git | 未执行任何写操作 |
| 禁止范围 | 未修改根依赖/lock、Electron main/preload/renderer、E2E、fuses、Python、migration、业务语义、独立测试、冻结、control、overview、其他角色或 `.claude/**` |

本轮没有启动或停止 Electron、Forge package、app.asar、Maris.exe、sidecar、Python 服务、数据库、Docker、OpenClaw、微信或 DeepSeek，也没有启动 E3、P4-C12、技术顾问或测试智能体。

## 3. 固定 allowlist 与拒绝规则

正式 payload 精确允许：

```text
alembic.ini
migrations/env.py
migrations/versions/*.py
src/wife_system/**/*.py
```

实现忽略普通污染文件，并保证它们不会进入 payload：

```text
**/__pycache__/**
**/*.pyc
**/*.pyo
**/*.pyd
**/*.egg-info/**
tests/**
.pytest_cache/**
build/**
dist/**
scratch/**
非 .py 未知扩展
```

以下输入 fail closed：symlink、Windows junction/reparse、非普通文件/目录、绝对资源路径、空路径、反斜杠非 POSIX manifest 路径、`.`/`..` 段、realpath 越出 repository/source root、staging root 越出 desktop root，以及并发 staging lock。

`migrations/README` 与 `migrations/script.py.mako` 没有复制。静态核对只发现 `alembic.ini` 的 `script_location` 配置，以及 `desktop_sidecar.py` 设置 migration 根并调用 `command.upgrade(..., "head")`；运行时没有读取 README 或 template。`script.py.mako` 只用于生成新 revision，不属于既有 upgrade runtime。

## 4. staging、原子替换与 manifest

- 固定 staging 根：`apps/desktop/.maris-staging/python-runtime`；`.gitignore` 新增 `.maris-staging/`，但过滤安全不依赖 Git ignore。
- 每次执行创建带进程号与随机 UUID 的 task-owned 临时 sibling；正式目标、临时 sibling、backup 和 manifest 均被限定在 desktop staging root。
- 开始时清理已中断的 task-owned temp/backup sibling；旧正式 staging 中的普通未知文件不会被继承。旧目标或 staging root 若为 reparse/symlink，则拒绝操作。
- 复制前先发现 allowlist 并计算 source byte size/SHA-256；复制后重新遍历临时 payload，要求路径、大小和摘要与 source entries 完全一致。
- 全部验证通过后先把旧正式目标移到 backup，再用同卷 rename 安装新 payload；manifest 也使用临时文件与 rename。提交中任何异常都会移除新目标并恢复旧 payload/manifest。
- 成功和失败的 finally 都清理临时 sibling、backup 与 lock。
- package wrapper 在调用 Forge 前 staging，并在 `finally` 中清理，无论 Forge 成功、失败或抛出异常都不保留 generated staging。H1 只静态验证该控制流，没有运行 Forge。

manifest 为稳定排序的 JSON array，每项只包含：

```json
{"path":"POSIX relative path","bytes":123,"sha256":"64 lowercase hex characters"}
```

manifest 不含时间戳、绝对路径、用户名、源根、目标根或随机字段。真实源码运行得到 67 项；manifest SHA-256 为 `b6657c8342ed15a7256815127a5f642f84760f5aaf4e3bbfaaeef72a13e6f8d7`。该 manifest 属于生成内容，验证后随 staging 一起清理，不进入 source manifest。

## 5. Forge 静态接线

`forge.config.ts` 的 `extraResource` 只引用：

```text
.maris-staging/python-runtime/alembic.ini
.maris-staging/python-runtime/migrations
.maris-staging/python-runtime/src
```

旧的 `../../src` 与 `../../migrations` 整树复制合同已经消失。Packager 仍会以三个 basename 保持最终相对布局为 `resources/alembic.ini`、`resources/migrations` 和 `resources/src`。

desktop `package` script 现在进入 `scripts/package-desktop.mjs`。wrapper 通过当前 `@electron-forge/cli` package metadata 解析 CLI 文件，不增加依赖；执行顺序固定为 `stagePythonResources → Forge package → finally cleanupPythonResources`。

## 6. 执行方测试

专属测试 `package-resources.test.ts` 共 8 项，覆盖：

1. 真实 source tree 的完整 allowlist、字节数和 source SHA-256；
2. `.pyc`、`.pyo`、`.pyd`、`__pycache__`、`.egg-info`、tests、build 与未知扩展零进入；
3. 旧 target 未知文件与中断 temp sibling 不继承；
4. 外部 junction 触发失败时旧正式 target/manifest 保持不变，temp/backup 清零；
5. 绝对路径、`..` traversal 和 reparse staging root fail closed；
6. manifest 排序、字段、内容确定且不含 source root 或用户 home；
7. cleanup 删除 payload、manifest 和 staging root；
8. Forge 三入口、旧整树合同消失、package wrapper staging/Forge/finally cleanup 顺序。

最终测试与静态结果：

| 检查 | 结果 |
| --- | --- |
| package resources 专属 Vitest | 1 file、8 passed |
| 专属 + 相邻 toolchain Vitest | 2 files、10 passed、0 failed、0 skipped |
| TypeScript `tsc --noEmit` | 通过 |
| desktop lint | 通过 |
| `node --check` staging/wrapper | 2/2 通过 |
| Forge CLI metadata 静态解析 | 通过；没有启动 Forge |
| 默认真实源码 stage/verify/clean | 67 entries、67 payload、0 forbidden、0 required missing、最终 staging=false |

## 7. 工具、lock、warning 与未运行项目

- Node `24.21.0` 官方 ZIP SHA-256：`158f7685b44de51f6c0df1d153526cbcd3e1bc739a8dfc607721cef75de9e541`，与官方 SHASUMS 匹配。
- pnpm `12.7.0` registry integrity：`sha512-3p5QdoIi1oNH+1U6/SH0h6jdF02xMGXoDhBYkwcqSqYsjGJmYBpsZf17T87QE1kzLuUwA0f0IA0vUYCxQEj0aA==`，与 metadata 匹配。
- frozen install：275 packages；实际 lifecycle 只有允许的 `esbuild postinstall`。
- `pnpm-lock.yaml` 安装前后均为 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。
- 安装只有七条下载速度低于 50 KiB/s 的 warning，分别来自 `minizlib`、`yaml-ast-parser`、`es-module-lexer`、`decimal.js`、`@babel/generator`、`type-fest` 和 `@bramus/specificity`；没有安装、来源、版本或 lock 失败。
- 最终只读 `git diff --check` 退出 0、没有 whitespace error；Git 提示 executor 日志及五个本轮未修改的既有 Python/test 文件在 Git 下次触碰时可能由 LF 转为 CRLF。显式路径 `git status` 另提示无法读取用户级 `%USERPROFILE%\.config\git\ignore`，但仍完整返回本轮指定文件状态；没有执行 Git 写操作。

本轮明确 `not_run`：Electron、Playwright/E2E、Forge package、app.asar、production fuses、最终 package resources 扫描、sidecar、Python 服务/回归、数据库和真实 EXE。E2/E2-R1 的历史运行结果没有计入本轮通过数。

## 8. 变更文件与 source manifest

产品行为和 Python runtime 代码未修改。H1 源码变化限定为：

- `apps/desktop/.gitignore`
- `apps/desktop/forge.config.ts`
- `apps/desktop/package.json`
- `apps/desktop/scripts/stage-python-resources.mjs`
- `apps/desktop/scripts/stage-python-resources.d.mts`
- `apps/desktop/scripts/package-desktop.mjs`
- `apps/desktop/tests/unit/package-resources.test.ts`

[H1 source manifest](../apps/desktop/b7-r1-h1-source.sha256)包含 198 entries，按 POSIX 相对路径排序并逐行记录 `path<TAB>sha256`；manifest 自身 SHA-256 为 `9e152288b5b1aaa2cb2fa979c877de617c8cdead08680e3d85430fb0b066f32e`。manifest 排除自身、角色日志、本报告、`node_modules`、H1 工具/cache、generated staging、package/out、profile、trace、临时日志和 `.claude/**`。

清理后最终复算为 198 matched、0 mismatch、0 missing。相对 209 文件起点为 4 个既有文件变化、0 missing：三个允许的 desktop 配置文件和 executor 角色日志；新增 4 个实现/执行方测试源文件、本报告和 H1 manifest，共 6 个允许文件。其余固定输入没有变化。

## 9. 临时资源收口

已删除 H1 task tools、`node_modules`、任务 store/temp/download、所有 generated staging/temp/backup/manifest、测试临时目录以及可能的 out/test-results；任务前已存在的根 `.pnpm-store` 保持不变。最终 `node_modules=false`、`.b7-h1-tools=false`、`.maris-staging=false`、out=false、test-results=false；Electron、Maris、Python、Pythonw 相关进程为 0。

执行智能体完成 H1 后停止，不启动 E3 或 P4-C12，等待头脑风暴总控复算终点快照。

## 10. P4-B7-R1-H1-R1 staging 原子替换返修

### 10.1 状态、起点与缺陷机制

- 返修状态：`review / finished`；只关闭 `P4-H1-ATOMIC-001`，没有重做 allowlist、Forge 接线或 Electron 诊断。
- 最新 control：`2026-09-28T00:55:00+08:00`；执行智能体为 H1-R1 唯一负责人，E3、技术顾问、测试智能体和 P4-C12 均停止。
- H1-R1 起点：209 matched、0 mismatch、0 missing；起点 manifest SHA-256 `cd77aa32af97f6a3b894d05a563583c745c3090b49cea7d47737a5fc697fcbe7`。
- 旧 H1 source：198 matched、0 mismatch、0 missing；旧 manifest SHA-256 `9e152288b5b1aaa2cb2fa979c877de617c8cdead08680e3d85430fb0b066f32e`。
- 旧 H1 报告 SHA-256 `f11c99898c08565d9c0596b6c79853465cc034a39f3703923c7d05d992cc147d`；lock SHA-256 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`；相关 Electron、Maris 和项目 sidecar 进程为 0。

原实现把“安装新 pair”和“清理旧 backup”放在同一个会触发 pre-commit rollback 的 `try/catch` 中。若 payload backup 已成功删除，而 manifest backup 删除失败，catch 会先删掉完整新 pair，再因 payload backup 已不存在而只能恢复旧 manifest，最终破坏正式 pair。

### 10.2 明确 commit point 与错误语义

返修后的 commit point 位于以下条件全部成立之后：

1. 新 payload 已安装到正式 `python-runtime`；
2. 新 manifest 已安装到正式 `python-runtime.manifest.json`；
3. 重新遍历正式 payload 后，路径、bytes 和 SHA-256 与本次 source entries 完全一致；
4. 正式 manifest 文本与同一 entries 的确定性序列化完全一致。

只有上述验证完成后才设置 `committed=true`。

- **pre-commit 失败**：删除已安装的新正式对象，按 payload→manifest 顺序恢复旧 backup；成功回滚后清除 temp/backup/lock。若真实回滚本身失败，则抛出 `staging_precommit_rollback_failed` 的 `AggregateError`，保留原错误与回滚错误，并且不删除仍可用于恢复的 backup。
- **post-commit cleanup 失败**：不再进入旧 pair rollback，完整新 pair 保留。函数抛出带 `STAGING_COMMITTED_CLEANUP_FAILED`、`committed=true`、精确 `cleanupStep` 和 `recoverableBackups` 的错误；未成功清理的旧 backup 保留为显式、可重试清理的恢复对象。下一次 staging 开始时仍由既有 interrupted-sibling 清理逻辑处理。
- 正常成功：新 pair 完整且同版本，temp、backup 和 lock 全部不存在。
- 额外 fail-closed：开始 replacement 前要求旧 payload 与旧 manifest 同时存在或同时不存在；只存在一侧时返回 `staging_existing_pair_incomplete`。

测试注入只有 `beforeReplacementStep(step)` 这一窄 hook；默认生产路径不传 hook，仍直接使用 Node 标准库。没有新增 npm 依赖、全局状态、环境变量后门或 Electron 测试接口。

### 10.3 六类确定性 replacement 测试

| # | 注入检查点 | 预期正式 pair | 实际正式 pair | temp / backup / lock | 结果 |
| --- | --- | --- | --- | --- | --- |
| 1 | 旧 payload 已移动；移动旧 manifest 前失败 | 完整旧 pair | 旧 payload 与旧 manifest 均恢复，逐文件 bytes/hash 匹配 | 全部 0 | passed |
| 2 | 两个旧对象已移动；安装新 payload 前失败 | 完整旧 pair | 两个旧对象均恢复，逐文件 bytes/hash 匹配 | 全部 0 | passed |
| 3 | 新 payload 已安装；安装新 manifest 前失败 | 完整旧 pair | 新 payload 删除，两个旧对象均恢复 | 全部 0 | passed |
| 4 | 新 pair 已验证 committed；清理 payload backup 失败 | 完整新 pair | 新 pair 保留且逐文件与新 manifest 一致 | 旧 payload+manifest backup 各 1；temp/lock 0 | passed |
| 5 | payload backup 已删除；清理 manifest backup 失败 | 完整新 pair | 新 pair 保留；精确关闭原缺陷 | 仅旧 manifest backup 1；temp/lock 0 | passed |
| 6 | 正常 replacement | 完整新 pair | 新 pair 与返回 entries 完全一致 | temp/backup/lock 全部 0 | passed |

所有失败由内存中的确定性 step hook 触发；没有修改 ACL、申请管理员权限、占用系统文件、依赖随机竞态或使用 sleep。

### 10.4 有限验证

| 检查 | 结果 |
| --- | --- |
| package resources 专属 Vitest | 1 file、14 passed；包含原 8 项和新增 6 类 replacement 测试 |
| 专属 + 相邻 toolchain Vitest | 2 files、16 passed、0 failed、0 skipped |
| TypeScript `tsc --noEmit` | 最终通过；首次只发现新增测试回调参数与数组窄化两个编译问题，修正后复跑通过 |
| desktop lint | 通过 |
| staging/package wrapper `node --check` | 2/2 通过 |
| Forge CLI metadata 静态解析 | 通过；解析到冻结 CLI metadata/bin，没有启动 Forge |
| 真实 source stage→verify→clean | 67 entries、67 payload、0 forbidden、0 required missing、最终 staging=false |
| 真实 source manifest | SHA-256 `b6657c8342ed15a7256815127a5f642f84760f5aaf4e3bbfaaeef72a13e6f8d7`，与 H1 相同 |
| `git diff --check` | 退出 0、无 whitespace error；仅有既有工作树文件的 LF→CRLF 提示 |

依赖恢复使用 Node `24.21.0` 和 pnpm `12.7.0`。Node 官方 ZIP 为 37,618,919 bytes，SHA-256 `158f7685b44de51f6c0df1d153526cbcd3e1bc739a8dfc607721cef75de9e541`。第一次离线 frozen install 因项目 store 缺少 `magic-string@1.4.2` tarball 停止；随后按同一 frozen lock 从官方 registry 补齐，安装 275 packages，实际 lifecycle 只有 `esbuild postinstall`。lock 前后均为 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`，没有版本或来源漂移。

最终只读 Git 检查还提示用户级 `%USERPROFILE%\.config\git\ignore` 无读取权限，但显式路径状态仍完整返回；没有执行 Git 写操作。LF→CRLF 和用户级 ignore 均为环境提示，不是测试失败，也没有改变 198 文件 source manifest 的内容核对结果。

### 10.5 文件边界、摘要与资源收口

返修只改变以下三个 source/test 文件：

| 文件 | SHA-256 |
| --- | --- |
| `apps/desktop/scripts/stage-python-resources.mjs` | `8a81d9671e3789ce0d21ffbaad657f83ddf737c6188e3d87f9adcc7d76c17f9c` |
| `apps/desktop/scripts/stage-python-resources.d.mts` | `a945fdab17b256b388fc24b610f833d380e3dddd4fcc977364dd50b222af63c3` |
| `apps/desktop/tests/unit/package-resources.test.ts` | `1fc77f04469df00b350455f4d682a0704f7410626e000eac071473c3435132e1` |

更新后的 H1 source manifest 仍为 198 entries，SHA-256 `04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1`。它记录全部 198 个 source 文件的逐文件 SHA-256；`.gitignore`、Forge 配置、package wrapper、package.json、lock、allowlist 内容和其他产品源均未修改。

最终 `node_modules`、desktop `node_modules`、`.b7-h1-r1-tools`、`.maris-staging`、out、Vite、test-results 和 Playwright report 均不存在；任务前已有根 `.pnpm-store` 保持不变。未启动 Electron、Forge package、app.asar、Maris.exe、sidecar、Python 服务、数据库、Docker、OpenClaw、微信、DeepSeek、E3 或 P4-C12；未修改或运行 `tests/independent/**`，未执行 Git 写操作。

H1-R1 的原子替换返修与执行方有限自测已通过；该结论只提交为 `review / finished`，不构成独立验收、P4-B complete 或发布验收。执行智能体停止，等待头脑风暴总控复算终点快照。
