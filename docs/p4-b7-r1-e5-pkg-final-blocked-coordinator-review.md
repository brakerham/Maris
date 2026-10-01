# E5-PKG-FINAL 总控核对与本地 ZIP 恢复裁定

- 角色：头脑风暴总控；核对日期：2026-10-01，Asia/Shanghai。
- 接受本轮 `blocked / finished`，不接受 P4-B complete。
- 已解决：Junction/hoisted 依赖隔离问题。
- 当前阻塞：Forge 在完成 Vite production build 后，以未标识 URL 的 `fetch failed` 结束唯一 package。
- 下一任务：`P4-B7-R1-E5-LOCALZIP`，补齐本地官方 ZIP 校验与 Packager 接线，再完成一次 package 和一次最终 EXE 验证。

## 核对证据

总控已读取完整报告和原始 stdout/stderr/result，复算 58/58 外部 evidence 与三份仓库交付，无缺失或摘要差异。

| 对象 | 已核对结果 |
| --- | --- |
| 外部 evidence manifest | 58 entries；`072127d72a6d444452b1bbb52f72a33613387954aa8e561c1fa7506b83d6ec4a` |
| source manifest | 266 entries；`f2b8a0fdd7642037b531673597a88bac6516cf237fa4cb276e029cd1aba19e1d` |
| 执行说明 | `906196bf546e9ef24f5ef421375a7c51e72816fca0f2fd21e0d9931afac2315c` |
| 执行角色日志 | `b218c07abdd409b14435d6e72a068875535f9c7a7d58da34799650e09646cb88` |

新任务根 `C:\MarisE5Final\E5-PKG-FINAL-20260929-1732` 的离线安装一次成功，fallback 为零；顶层 node_modules 为普通目录，task-local store/virtual store 均正确。依赖树 12,443 files、570,582,052 bytes，package 前后摘要相同；Electron dist 73 项保持冻结值。donor 和 active cache 起终点不变。

TypeScript 与三个相关 Vitest 文件的 22 项均通过。唯一 package 运行 51,257 ms、exit 1；原始日志证明 Forge system check、pnpm 检查和 main/preload/两个 renderer production build 已通过。out、EXE、app.asar 未形成，最终 EXE 是 0/1。原任务停止正确。

## 新发现：ZIP cache 不能保证离线

总控只读审计了本轮实际安装的冻结依赖，而非推测系统代理状态：

1. `apps/desktop/forge.config.ts` 仅在 `MARIS_ELECTRON_CACHE` 存在时显式传递 `download.cacheRoot`。安装阶段使用的 `ELECTRON_CACHE`、`electron_config_cache` 不能自动替代该配置。当前 package receipt 只保存了一个 electronCache 路径，不能完整证明三个环境变量的实际值；因此不能断言本轮必然遗漏 MARIS 变量。
2. 本轮 `node_modules/@electron/get/dist/Cache.js` 按下载 URL 的父路径哈希查找 ZIP。
3. `@electron/get/dist/index.js` 在 cache hit 后仍调用 `validateArtifact()`。没有显式 `checksums` 时，它请求 `SHASUMS256.txt`，并将 `cacheMode` 设为 Bypass，明确绕过校验文件缓存。
4. 验证阶段异常会进入重下载路径。因此即使 ZIP 在本地且正确，也可能依赖网络才能完成 package。
5. `@electron/packager/dist/packager.js:getElectronZipPath()` 对 `electronZipDir` 有独立分支：查找固定文件名并直接返回本地 ZIP；未设置才调用 `downloadElectronZip()`。

上述离线缺口由实际源码确认。但旧日志没有 URL/stack，旧失败请求仍为 `unverified`；不得事后声称已经抓到某个远端 URL，或认定用户代理故障。

Packager 官方文档也明确支持本地 ZIP 目录，设置后跳过 download 选项：[electronZipDir 官方说明](https://electron.github.io/packager/main/interfaces/Options.html#electronZipDir)。

## 窄范围恢复合同

这是现有构建输入的补充接线，不改变 Agent Host、财务业务、窗口安全、依赖版本或发布策略。总控授权执行智能体：

- 在 Forge 中增加可选 `MARIS_ELECTRON_ZIP_DIR` → `packagerConfig.electronZipDir` 接线；显式本地模式优先于已有 cache 模式。
- 在 package wrapper 启动 staging/Forge 之前，验证本地目录和固定 ZIP，执行 SHA-256/长度核对。目录无效、文件缺失、非普通文件、版本或摘要不符即明确失败，不能回退联网。
- 固定文件：`electron-v44.4.5-win32-x64.zip`；158,184,819 bytes；SHA-256 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d`。其官方来源已由 E3/E2 的供应链证据核对。
- 使用 Node 标准库；可增加一个小型验证 helper 与声明文件及单元测试，不新增依赖。
- 不设置 `unsafelyDisableChecksums`，不替换镜像，不修改 Electron/lock/fuses，不把 ZIP 提交到 Git。
- 没有设置本地变量时保留已有常规构建行为。新的执行验收必须显式设置本地变量并记录最终 Packager 选项。

本轮已经建立的普通依赖目录、工具、ZIP 可以复用；无需重新安装或创建 Junction。原 `evidence` 永久只读，新任务使用新的证据子目录。仅明确授权的构建文件可同步进该 workspace，保存原件摘要及副本，并生成新的 source 清单；旧 source 清单继续描述旧状态，不能覆盖。

构建接线及定向测试先完成，再消耗新的 package 1/1；成功后执行最终 EXE 1/1。DEBUG 日志应记录 Packager/get 阶段，若仍 fetch failed，保留脱敏 URL、stack/cause；不可假定本地 ZIP 选项保证其他所有构建步骤无网络。

## 状态与后续

旧 E5-PKG-FINAL 保持 blocked/finished，普通目录依赖成果接受为新任务输入。下一任务完成后仍只提交 review/finished，最终模块、recover、毛毛与独立结论均不得提前宣称通过。

P4-C12 保持 not_started；技术顾问和测试智能体当前停止。真实高保真前端启动前的参考图及模型分工提醒继续有效。
