# P4-B7-R1-E5-PKG-FINAL：重建隔离依赖并完成最终产品门禁

## 唯一目标

你是既有执行智能体，唯一负责 `P4-B7-R1-E5-PKG-FINAL`。E5-R2 已修复 canonical Profile parser，并通过 OpenAPI、TypeScript、lint、22 项定向 Vitest、52 项完整 Vitest、29 项 Python 相邻回归、compileall 和 pip check。唯一 package 因新 workspace 的顶层 `node_modules` 是 Junction 而失败，且通过 Junction 改写了旧 E4 的 43 个 `.bin` shim。

本任务不再修改产品或测试。唯一目标是在全新 C 盘任务根中用任务专属 pnpm store 建立真实 hoisted `node_modules`，执行一次 package，并在成功产物上直接执行一次最终 `Maris.exe` 黑盒门禁。全部通过后停在 `review / finished`；真实安装、package 或产品门禁失败则安全收口为 `blocked / finished`。不得启动 P4-C12、测试智能体、技术顾问或高保真前端开发。

## 开工前必读

按 `AGENTS.md` 顺序读取：

1. `README.md`
2. `docs/project-coordination.md`
3. `docs/coordination/README.md`
4. 最新 `docs/coordination/control.md`
5. `docs/coordination/agents/executor.md`
6. 本任务卡
7. `docs/p4-b7-r1-e5-r2-blocked-coordinator-review.md`
8. `docs/b7-r1-e5-r2-profile-parser-running.md`
9. `docs/p4-b7-r1-e5-r1-blocked-coordinator-review.md`
10. `docs/p4-b7-r1-e4-pkg-r2-coordinator-review.md`
11. `docs/b7-r1-e5-final-exe-running.md`
12. `docs/coordination/snapshots/p4-b7-r1-e5-pkg-final-start.sha256`

逐行复算固定快照。最新 control 若不再分配本任务，立即停止。Git index staged paths 必须为 0。`.claude/`、仓库根 `.pnpm-store/`、所有旧 C 盘任务根、旧 package/profile/database/evidence 全部只读。

## 已确认且不得重复的结果

- parser 与 E5-R1 Profile 修改已完成，不得再改。
- package 前完整执行方回归已经通过，不重复 52 项 desktop 或 29 项 Python 全组。
- E5-R2 package 的 1/1 预算属于旧任务，已经消耗；本任务获得独立的新 package 1/1 和最终 EXE 1/1。
- E4 `node_modules` 已有 43 个 `.bin` shim 漂移，只作为 evidence，不得恢复、删除、复制、链接或执行。
- 不使用任何旧任务的顶层 `node_modules`，尤其禁止 Junction、symlink、directory link、`mklink`、`subst` 或指向旧 workspace 的 reparse point。
- 最终 EXE 继续采用 E5-FINAL 已证明有效的直接 `spawn(shell:false)` 路线，不使用 Playwright Electron launcher，不预跑 app.asar。

## 仓库写入范围

产品、测试、依赖声明、lock、Forge、package wrapper、staging、Python、migration、接口冻结和独立测试均为只读。

只允许：

- 更新 `docs/coordination/agents/executor.md`；
- 新建 `docs/b7-r1-e5-pkg-final-running.md`；
- 新建 `apps/desktop/b7-r1-e5-pkg-final-source.sha256`。

所有构建工具、cache、node_modules、out、profile、数据库、runner 与 evidence 只能位于新的 C 盘任务根。

## 新任务根与 donor 边界

创建：

```text
C:\MarisE5Final\E5-PKG-FINAL-<timestamp>
```

source workspace 从本任务 266 项固定快照复制，0 missing、0 mismatch。不得从旧 workspace 复制产品源码覆盖当前仓库。

唯一获准 donor：

```text
C:\MarisE3\E3-20260928-0911\cache\pnpm\store
C:\MarisE3\E3-20260928-0911\cache\electron
```

donor 只读。开始前记录存在性、普通目录/reparse 状态、文件数、总字节和确定性清单摘要。把两套 cache 物化复制到新任务根的 `cache` 下；复制后按同一算法逐项匹配。复制操作预计超过五分钟时，先更新执行快照和下一检查点，并按协作规则写心跳。

禁止复制 E3 `workspace/node_modules`。禁止读取或写入 E4/E5-R1/E5-R2 `node_modules`。不得把 donor cache 本身作为 pnpm 的 active store 或 active Electron cache；所有 active 路径必须在新任务根。

## 任务专属 clean install

安装前：

- 新 workspace 顶层 `node_modules` 必须不存在；
- lock SHA-256 必须为 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`；
- 固定 Node、pnpm 12.7.0 与 source snapshot 匹配；
- process-local `ELECTRON_CACHE` 指向新任务 electron cache；
- process-local PATH 只使用已验证固定 Node/pnpm；不修改用户或系统环境。

首先在 workspace 根执行一次离线 frozen install：

```text
pnpm install --offline --frozen-lockfile --store-dir <new-task-pnpm-store>
```

这是环境供应步骤，不计入 package 预算。原始 stdout、stderr、退出码、起止时间和进程收口必须保存。

如果离线安装退出非零：

- 若原因不是明确的 offline store 内容缺失，立即停止；
- 若明确是 lock 所需包或元数据不在 copied store，允许一次网络 fallback；
- fallback 前只可清理新任务根内由失败安装创建的不完整 `node_modules` 和 active store 临时文件。递归操作前解析并核对绝对路径仍位于本任务根；不得触碰 donor 或其他 C 盘任务；
- 重新读取最新 control 后，用同一 lock、同一 pnpm 和新任务 store 执行一次：

  ```text
  pnpm install --prefer-offline --frozen-lockfile --store-dir <new-task-pnpm-store>
  ```

- 不允许第三次 install，不允许修改 package.json、workspace 配置、`.npmrc` 或 lock，也不要求用户切换代理，除非实际网络错误使授权 fallback 无法完成。

安装成功后必须证明：

1. 顶层 `node_modules` 是普通目录，`LinkType` 为空且不是 reparse point；
2. `.modules.yaml` 的 `storeDir`、`virtualStoreDir` 都属于新任务根，不含 E3/E4/E5-R1/E5-R2 路径；
3. `nodeLinker=hoisted`、pnpm 12.7.0、lock 和 manifests 保持冻结值；
4. `pnpm list --depth Infinity` 退出 0，实际包版本与 lock 一致；
5. Electron dist 73 项匹配冻结摘要 `ffb4b389d5c454ca139cb6384f5ebb3d20633cf000960a8aa1b6c1794c9ebf8f`；
6. donor cache 起终点摘要完全不变；
7. 新任务 source、lock 和 manifests 没有安装副作用。

随后只运行 TypeScript `tsc --noEmit` 和 registry/composition-root/HostClient 的 22 项定向 Vitest。两者通过才进入 package；不重复完整 52/29 回归。

## 唯一 package

package 预算 1/1。使用任务专属真实 `node_modules`、任务专属 store/cache、固定 Node/pnpm 和现有 `pnpm run package`。不得在 package 前把目录替换为 link，也不得让 Forge 解析到系统 pnpm。

记录实际进程启动点。package 非零、超时、crash、污染或残留时立即停止；不得修改后第二次 package。

package 成功后只读验证同一份产物：

- 新 `Maris.exe`、`resources/app.asar`、140 项左右的实际 out 清单及 production fuses；
- app.asar 中 `daily_finance.assistant@1` 至少出现一次，旧别名字面量为 0；
- 67 项 Python resources 精确符合 H1 allowlist；
- `.pyc`、`.egg-info`、测试、task evidence、用户/工作区绝对路径、凭据样式和私钥为 0 命中；
- staging、backup、lock 与 transition artifacts 已清理；
- source、lock、manifests、Electron dist 和 donor cache 无漂移。

package 后的只读 evidence 核对错误不允许重打包。保留原始错误，只离线修正派生读取；若产物本身不符合合同则停止。

## 最终 EXE 单次黑盒门禁

只有 package 和静态产物检查全部通过才进入。最终 EXE 预算 1/1、硬超时 120 秒，不运行 fixture、不预跑 app.asar、不重试。

- 固定 Node `child_process.spawn()` 直接启动新 package 的 `Maris.exe`；
- `shell:false`，根 PID 精确对应新 EXE；
- 新隔离 profile、虚拟数据库、随机 owner marker、最终 resources 和已验证 Python；
- 动态 CDP 端口非零且只监听 `127.0.0.1`；Playwright 只经 `connectOverCDP()` 观察；
- 不传 `--no-sandbox`，不启用 inspect，不改变 fuses。

依次验证：

1. owned set、CDP、一个主窗口和一个毛毛窗口；
2. 两个冻结 preload bridge、Node 隔离与未授权 API 缺失；
3. runtime `online / managed / authenticated / errorCode=null`；
4. `modules.list()` 含且只含兼容 `daily_finance`，其 `profile_ids` 含 `daily_finance.assistant@1`；
5. 毛毛 `getState()` 为 daily finance 形态，`openMain()` 成功且不创建重复主窗口；
6. `runtime.recover()` 精确调用一次；恢复后 runtime 与 modules 仍通过；
7. DOM、storage、bridge、console、page error、crash event、Windows Application/Code Integrity 与日志隐私；
8. 产品现有 bounded shutdown，自然退出码 0；最终产品、sidecar、监听、窗口和 Tray 归零。

产品启动后的派生报告/摘要错误不允许重新启动产品；在原始证据不变时离线修正。真实产品断言、crash、超时、秘密泄露或资源无法收口则立即停止。

## 交付

运行说明必须包含：

- E5-R2 parser 修复的接受来源与不重复范围；
- donor/active cache 边界、复制摘要、离线 install 与可选 fallback 的真实次数；
- 顶层 node_modules 普通目录及 `.modules.yaml` 任务内路径证明；
- TypeScript 与 22 项定向测试结果；
- package 真实次数、产物摘要、fuses/resources/污染与收口；
- 最终 EXE 真实次数、每个动态门禁、recover 次数、隐私与收口；
- 266 项起点/终点边界、新 source manifest 和外部 evidence 清单；
- 旧 E4 漂移现场未触碰；P4-C12、高保真前端、微信、DeepSeek 和个人数据未运行。

全部通过后提交 `review / finished` 并停止。不得自行宣布 P4-B complete，不得启动测试智能体或前端开发。
