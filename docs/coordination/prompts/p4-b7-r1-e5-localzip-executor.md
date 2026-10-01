# P4-B7-R1-E5-LOCALZIP：校验本地官方 ZIP 并完成产品门禁

## 唯一负责人和目标

你是既有执行智能体，唯一负责本任务。E5-PKG-FINAL 的真实普通 node_modules、离线安装、Electron dist、TypeScript 和 22 项相关测试已通过；唯一 package 在 Vite build 后出现 fetch failed。总控从实际依赖源码确认：ZIP cache hit 仍可能联网取 SHASUMS256，缓存不是离线合同。

实现一个明确的本地 ZIP 构建入口，验证后让官方 Packager 直接读取 ZIP，再完成 package 1/1 与最终 EXE 1/1。全部通过停在 review/finished；产品/安装/真实构建断言失败停在 blocked/finished。不得自动启动 C12、其他角色或前端设计。

## 必读及接单

先按 AGENTS 读取 README、project-coordination、coordination/README、最新 control、本角色状态和本任务卡；随后读取：

- `docs/p4-b7-r1-e5-pkg-final-blocked-coordinator-review.md`
- `docs/b7-r1-e5-pkg-final-running.md`
- `docs/coordination/snapshots/p4-b7-r1-e5-localzip-start.sha256`
- 上一份 E5-PKG-FINAL Prompt 的最终 EXE 门禁段，以及 E5-FINAL 运行说明。

复算最新固定清单，确认本任务是唯一授权任务，记录接单与当前执行快照。Git staged paths 必须为零。每次外部/安装/清理/用户操作前重读 control；完成后停止。

## 已接受的输入和文件边界

允许复用以下已验证的本轮普通目录环境：

`C:\MarisE5Final\E5-PKG-FINAL-20260929-1732`

仅复用其中 tools、真实 workspace/node_modules 与 cache。原 evidence 全部只读；新 evidence 必须 create-new 于 `localzip-resume-1`。先核对旧 evidence 58/58、依赖 manifest 12,443 项、dist 73 项、ZIP、lock 和干净进程状态。如果不匹配，停止并给出差异。不得读取/复用 E4/E5-R1/E5-R2 的污染依赖。

本任务禁止重新 pnpm install、缓存重建、依赖版本变化、联网补装、代理/TUN/系统配置修改。已有 Vite 中间产物可由唯一 package 正常覆盖，不作为通过依据。

允许修改的仓库文件仅为：

1. `apps/desktop/forge.config.ts`
2. `apps/desktop/scripts/package-desktop.mjs`
3. 必要时新增 `apps/desktop/scripts/verify-electron-zip.mjs` 和同名 `.d.mts`
4. 新增 `apps/desktop/tests/unit/electron-zip.test.ts`
5. 本角色日志 `docs/coordination/agents/executor.md`
6. 新增 `docs/b7-r1-e5-localzip-running.md`
7. 新增 `apps/desktop/b7-r1-e5-localzip-source.sha256`

业务/renderer/Host/Agent/Python、其他测试、lock、依赖、staging、fuses、冻结文档、独立验收、control、overview 和其他角色文件只读。Git 无写权限。

将明确授权的构建变更原样同步到上述 workspace。同步前把这些文件的原件及摘要保存进新 evidence，禁止覆盖旧 manifest；变更后生成本任务新 source manifest，并证明其余旧 source 不变。新 evidence/临时 fixture 可写在 localzip-resume-1 内；out/staging 只由现有 package wrapper 管理。

## 本地 ZIP 合同

- 可选环境变量：`MARIS_ELECTRON_ZIP_DIR`，由任务 driver 传递给构建子进程，不改用户或系统环境。
- Forge 设置对应 `packagerConfig.electronZipDir`。在该模式下不依赖 `download.cacheRoot`，不同时拼接矛盾选项。未设置变量时保留原常规行为。
- wrapper 必须在 staging 和 Forge spawn 前完成验证。给定变量为空白/非法路径、非绝对路径、目录或文件不存在、非普通 ZIP 文件、长度/摘要不符均明确拒绝，不能转为网络 fallback。
- 固定文件名：`electron-v44.4.5-win32-x64.zip`。
- 固定长度：158,184,819 bytes。
- 固定 SHA-256：`11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d`。
- 固定版本、平台、架构必须与当前冻结 package/target 相符；只支持本任务 win32 x64，不引入多平台供应机制。
- 在既有 task-local cache 中定位上述 ZIP，将包含 ZIP 的目录传给变量，无需移动、下载或复制 ZIP。
- 不加入 unsafelyDisableChecksums、第三方镜像、inspect/no-sandbox、版本 fallback。固定摘要必须源于已接受的官方证据，不能从待验证文件自行计算后当作期望值。
- 使用 Node 标准库，流式哈希即可；保持已有 staging/finally cleanup 和 Forge 子进程错误处理。

不得为了证明此路径再次 package 或运行最小 Electron fixture。先做必要单元/集成边界检查：缺失、错版本/文件名、长度或摘要错误、有效文件、显式本地选项接线；错误必须在 staging/Forge spawn 前阻止。可以以小型临时文件和注入验证期望值测试 helper，但 production 固定值不能可由任意 env 覆盖。

## package 前检查

运行 TypeScript、lint、ZIP 专属测试、package-resources/toolchain 相邻测试；不重复全部 desktop/Python 回归或 22 项未修改模块测试。

使用真实官方 ZIP 调用生产验证入口，并实际解析 Forge config，证明 `electronZipDir` 最终指向同一目录/文件。保存摘要、长度、选项和子进程 env 传递证据。普通 node_modules、lock 和 dist 再核对无漂移；out/staging/transition 不存在。

实现/只读 evidence 编排的笔误允许在 package 尚未启动时就地修正，保留首个失败并复验受影响节点；不要再为文件编号、空数组或参数转发的无副作用错误创建整轮恢复任务。真实产品、资源或来源问题必须停止。

## 唯一 package 与静态产物

新预算 package 1/1；使用既有 task-local Node/pnpm/PATH，显式设置本地 ZIP 变量。开启 `DEBUG=electron-packager,@electron/get:*`（仅构建子进程），保存原始 stdout/stderr、exit、起止时刻和可观察会话。不得输出秘密；如失败应捕获脱敏 stack/cause/公开 artifact URL。进入长操作前登记快照；同一问题连续两个无进展检查点停止，不盲目重试。

唯一 package 非零、超时、来源漂移或资源不可收口时停止，不进行第二次 package。不把 Copying files 的并行失败重复统计成多个产品缺陷。

成功后核对 EXE/app.asar 摘要、production fuses、Python resources allowlist、零 pyc/egg-info/个人路径/秘密/任务证据污染、正确 Profile 字面量及旧别名零命中、staging 清理。实际 out 清单按本次产物生成，不把历史 140 文件数量当作唯一固定断言。

## 最终 EXE 单次门禁

只有 package 与静态门禁全通过才能执行 EXE 1/1，硬时限 120 秒。采用已接受的 Node spawn(shell:false) 直接启动新 EXE，Playwright 只 connectOverCDP 观察；新隔离 profile/虚拟数据库/owner marker、受管 Python、loopback 动态端口。

依次取得实际证据：根 PID/owned set；主窗口与毛毛窗口各一个；冻结 bridge、renderer Node/IPC 隔离；runtime online/managed/authenticated/errorCode=null；modules 唯一兼容 daily_finance，真实 Profile daily_finance.assistant@1；毛毛 getState/openMain；recover 精确一次及恢复后 runtime/modules；隐私、console/page/crash 与 Windows 事件；自然退出 0，产品/sidecar/监听/窗口/Tray 归零。

沿用 `src/shared/contracts.ts` 的实际响应结构：`modules.list()` 返回 HostModuleSummary 数组，应核对其 `profile_ids` 包含正确 Profile；毛毛 `getState()` 返回 `state` 与 `appearanceId`，不能假定毛毛响应带 module_id/Profile 字段，也不能修改业务 DTO 迁就 runner。

启动后真实断言失败立即停止，保存首次失败；派生报告错误可离线修正，不能重启产品。窗口/GPU overlay 信息不自动当作 crash；明确记录事件等级和业务结果。

## 收口与交付

不删除旧 evidence、node_modules/cache 或真实数据。只收口本任务确有所有权的进程/监听，保留已成功产物。运行说明记录接受的历史结果、本地 ZIP 来源/校验、改动文件、定向验证、env 与最终 config、package/EXE 次数、动态门禁、失败或通过的精确范围、resource cleanup 和完整文件摘要。

完整 source、变更边界和 evidence 使用独立 manifest，避免自引用。全部通过交付 review/finished；失败 blocked/finished。不宣布 P4-B complete、不推 Git、不启动 C12/其他角色、不提前实现高保真界面。
