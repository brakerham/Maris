# P4-B7-R1-E4 总控核对：Forge package 的 pnpm 命令解析阻塞

核对时间：2026-09-28，Asia/Shanghai

核对角色：头脑风暴总控

结论：接受 `P4-B7-R1-E4` 的 `blocked / finished` 停止结论；阻塞发生在 Forge 真正构建前的 package-manager 系统检查，已用同一 Forge `spawnPackageManager` 完成零产品变更的修复预检，允许发布一次 `P4-B7-R1-E4-R1` 恢复任务

## 1. E4 交付结论

执行智能体正确遵守了唯一 package 预算和 P0 停止规则。阶段 A 全部通过，随后唯一一次 package 在 Forge 的 `Checking package manager version` 阶段退出 1；Packager、Vite、app.asar、fuse、最终 resources、P1 和 P2 都没有开始。执行智能体没有用第二次 package 覆盖失败，也没有修改产品、测试、依赖、lock、系统 pnpm 或协调控制面。

这次失败没有形成产品运行缺陷证据。失败命令是 Forge 内部的裸命令：

```text
pnpm config get hoist-pattern
```

E4 的正式 wrapper 通过绝对 Node 路径启动 Forge，但 wrapper 没有给 Forge 后续的裸 `pnpm` 子进程提供一个确定性的命令解析入口。Windows 最终命中了用户目录中的失效 shim；该 shim 指向 pnpm store 中一个不能由 `cmd.exe` 直接执行的无扩展目标，于是 Forge 在读取 `.npmrc` 前退出。

## 2. 固定输入与证据复算

| 核对项 | 总控结果 |
| --- | --- |
| E4 起点 | 215 项；214 matched，唯一 mismatch 是授权更新的 executor 日志，0 missing |
| E4 source | 198/198 matched，0 mismatch，0 missing |
| E4 source manifest SHA-256 | `04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1` |
| E4 运行说明 SHA-256 | `7eee9462c77fb20582fdacd171540960e1d903254a61f3f98ee64fe62940121e` |
| executor 状态 SHA-256 | `e324148686a64a3871d5cd5196f1f5e54d514ab9d327f815aa9c165982cfa60a` |
| C 盘 evidence | 26/26 matched，0 mismatch，0 missing |
| evidence manifest SHA-256 | `5958703ccea01cd0b8ef3bd72b681dfbdb7b5b398c7b8c7bc5ee7cd2fb1ba2d1` |
| package 原始日志 SHA-256 | `e9c841c4d23cbf93a41e62680aaaf493db9ff2764323b4fe41155680afb3b0d6` |
| package 后资源 | `out=false`、`.maris-staging=false`、transition artifacts 0、owned process 0 |

总控只读复算了 E4 原始 evidence。源代码、Node/pnpm/Electron/Playwright、lock、node_modules 和九个污染 marker 均保留；E4 现场没有由总控补写或覆盖。

## 3. 阶段 A 有效证据

阶段 A 不是失败点，保留为 R1 的固定输入，不再重复：

- OpenAPI generated drift 通过；
- TypeScript 退出 0；
- desktop lint 退出 0；
- desktop Vitest 12 files、36 passed；
- H1 package/toolchain 2 files、16 passed；
- Python 定向 55 passed；
- Python compile 退出 0；
- `pip check` 无破损依赖；
- 0 failed、0 skipped、0 xfail。

九个虚拟污染 marker 在 package 前和失败后均为 9/9，能继续用于真正的最终 resources hygiene 门禁。

## 4. 总控同构预检

总控没有运行 package、Electron、Maris 或 sidecar。总控在仓库内创建短期临时目录，并生成一个只指向 E4 已验证 `pnpm-native.exe` 的 `pnpm.cmd`；随后把该目录置于子进程 PATH 第一位，调用 E4 固定 Node 和 E4 安装的 Forge `@electron-forge/core-utils` 中同一个 `spawnPackageManager` 实现。

实际输出：

```json
{
  "version": "12.7.0",
  "hoistPattern": "undefined",
  "publicHoistPattern": "undefined",
  "nodeLinker": "hoisted"
}
```

补充门禁：

- `where pnpm` 的第一项是任务临时 `pnpm.cmd`；
- 直接 pnpm 版本为 `12.7.0`；
- Forge 同构预检退出码为 `0`；
- 临时目录最终不存在；
- 仓库、E4 现场、用户级 pnpm 和系统环境变量均未修改。

这说明当前缺陷不需要技术方案重做，也不需要修改系统级 pnpm。最小恢复方式是：在 E4 任务根内创建任务专属、可复算、可删除的 `pnpm.cmd`，把它放到本次 wrapper/Forge 进程环境 PATH 的第一位，在消耗 package 预算前运行上述同构预检。

## 5. 是否需要修改 package wrapper

本轮不修改 `apps/desktop/scripts/package-desktop.mjs`。现有 wrapper 已正确完成：

- 直接解析 Forge CLI 文件；
- 通过当前 Node 启动 Forge；
- package 前 stage；
- package 成功或失败后 cleanup。

它的问题只是继承了调用方环境中的裸 `pnpm` 解析顺序。R1 可以通过任务环境把这一顺序固定下来，并且同构预检已经证明可行。只有 R1 通过后、独立验收或未来普通开发环境再次证明 package wrapper 本身必须独立于调用环境时，才考虑把 PATH 构造做成持久产品工具链逻辑。现在修改 wrapper会扩大快照和回归范围，没有必要。

## 6. R1 顺序

`P4-B7-R1-E4-R1` 固定复用保留的 E4 任务根，不重复源码复制、frozen install 或阶段 A：

1. 复算仓库 R1 快照、E4 source、C 盘 source copy、工具、lock、node_modules、Electron dist、污染 marker 和旧 evidence；
2. 在新的 R1 evidence/shim 子目录创建任务专属 `pnpm.cmd`；
3. 以 package 将继承的同一 PATH 运行 `where pnpm`、版本、三个 config 查询和 Forge `spawnPackageManager` 同构预检；
4. 预检全部通过后，直接用 E4 固定 Node 启动正式 `package-desktop.mjs`，授予 R1 唯一一次 package 预算；
5. package 通过后完成 H1 最终 resources、app.asar、fuses 和隐私扫描；
6. 只有 package 后门禁通过才运行一次 P1 app.asar；
7. 只有 P1 通过才运行一次 P2 最终 `Maris.exe`；
8. 任一级失败立即停止，不在 R1 内改产品或第二次运行对应 cell。

R1 仍然不启动测试智能体或 P4-C12。只有 package、P1、P2 和资源收口全部通过，总控才固定 B7 稳定终点并派发独立验收。
