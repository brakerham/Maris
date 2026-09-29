# P4-B7-R1-E5-R2 阻塞总控核对

- 核对角色：头脑风暴总控
- 核对结论：接受 `blocked / finished`；canonical Profile parser 已修复并通过全部 package 前回归，阻塞来自隔离构建目录错误使用 Junction
- 已关闭代码缺陷：`P4-E5-PROFILE-PARSER-002`（执行方代码与回归范围）
- 尚未完成：新 package、最终 EXE 黑盒门禁、P4-B 独立验收
- 下一任务：`P4-B7-R1-E5-PKG-FINAL`，重建任务专属真实依赖目录，随后完成一次 package 和一次最终 EXE 门禁

## 1. parser 修复接受结论

总控核对实际差异后确认：

- `apps/desktop/src/modules/registry.ts` 已使用与 Python `CANONICAL_ID_PATTERN` 语义一致的 ASCII 正则；
- 没有加入 `\d`、Unicode flag、trim、lowercase、normalization、隐式 major、旧别名或 fallback；
- `intersectModules()` 没有修改；
- `apps/desktop/tests/unit/registry.test.ts` 通过公开行为覆盖合法 Profile、`@0`、64/65 字符边界、非法字符/版本、严格模块求交以及五类 registry 冲突；
- E5-R1 的 contribution、composition-root 和 HostClient 真实 Profile 修改保持不变。

package 前执行方证据为：

| 范围 | 结果 |
| --- | --- |
| OpenAPI generated drift | 通过 |
| TypeScript | 通过 |
| desktop lint | 通过 |
| 定向 Vitest | 22 passed、0 failed、0 skipped |
| desktop 完整 Vitest | 52 passed、0 failed、0 skipped |
| Python 相邻回归 | 29 passed、0 failed、0 skipped |
| compileall / pip check | 通过 / 无损坏依赖 |

因此下一任务禁止再次修改 parser、贡献、测试或其他产品代码，也不重复完整 52/29 回归。`P4-E5-PROFILE-PARSER-002` 在代码与执行方回归范围关闭；最终产物中的实际接线仍需新 package 和最终 EXE 证明。

## 2. package 失败分类

唯一 package 失败发生在产品构建之前：新 E5-R2 workspace 的 `node_modules` 是指向 E4 依赖树的 Junction，而项目冻结为 `node-linker=hoisted`。pnpm 要求 workspace hoist 目录是普通目录，因此以以下错误退出：

```text
workspace hoist directory is not a real directory
```

这不是源码、lock、Forge 配置或 package wrapper 缺陷。它是隔离构建环境供应方式错误；R2 任务卡允许复用冻结依赖内容，却没有明确禁止把顶层 `node_modules` 做成 Junction，总控承担该边界遗漏。

package 实际次数为 1/1、退出码 1。没有生成 out、app.asar 或新 EXE，最终 EXE 为 0/1。执行方没有重试，符合任务卡。

## 3. E4 依赖树的状态

pnpm 在拒绝 Junction 前通过该 Junction 改写了旧 E4 依赖树中的 43 个 `.bin` shim：

- 文件数仍为 12,451，missing 0；
- 43 个内容/长度不匹配，每项增加 5 bytes；
- 总字节从 570,581,590 变为 570,581,805；
- 原聚合 `f06ce306...00c7` 变为 `d3d7728f...23aa`；
- Electron dist 的 73 项摘要保持不变；
- 仓库源码、lock 和项目内 `.pnpm-store` 没有发生相同漂移。

该 E4 目录继续作为失败证据保留，不恢复、不删除，也不再作为依赖输入。漂移不在 Git 仓库中，不影响已提交源码或用户数据。

## 4. 新依赖供应方式

下一任务不得复制、链接或运行任何 E4、E5-R1 或 E5-R2 `node_modules`。已只读确认 E3 现场仍具备：

- 普通目录形式的 hoisted `node_modules`；
- pnpm 12.7.0 的 v11 内容存储；
- Electron cache；
- 相同 lock SHA-256 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`；
- Electron 73 文件冻结摘要 `ffb4b389...f8f8f`。

新任务只把 E3 的 **pnpm 内容存储与 Electron cache** 物化复制到一个新的任务根，不复制 E3 `node_modules`。所有后续 pnpm 操作只指向新任务 cache。然后执行：

```text
pnpm install --offline --frozen-lockfile --store-dir <new-task-store>
```

由 pnpm 在新 workspace 中创建真实的 hoisted `node_modules`。如果且仅如果离线 store 缺少 lock 所需内容，允许在同一个新任务根清理未完成的任务内安装目录，并使用相同 lock 做一次 `--prefer-offline --frozen-lockfile` 受控补全；不得修改依赖声明或 lock。

## 5. 最终续段边界

依赖安装不是 package 预算。只有以下门禁通过后才允许消耗新的 package 1/1：

1. 顶层 `node_modules` 是普通目录，不是 Junction、symlink 或其他 reparse point；
2. `.modules.yaml` 的 store/virtual store 指向新任务根，不指向 E3/E4/E5；
3. lock、package manifests 与 source 固定快照一致；
4. `pnpm list`、TypeScript 和 22 项 Profile 相邻 Vitest 通过；
5. donor cache 起终点只读一致。

package 成功后在同一任务完成静态产物核对，并沿用已证明有效的 Node `spawn(shell:false)` 直接启动最终 `Maris.exe` 一次。验证 runtime、唯一 `daily_finance`、毛毛状态、一次 recover、隐私与自然退出。

产品/测试/安装合同失败时停止；尚未启动 package 或 EXE 时的无副作用 evidence 编排错误按原始记录就地修正。package 后的只读派生核对错误不得重新 package，EXE 后的报告错误不得重新启动产品。

## 6. 后续顺序

`P4-B7-R1-E5-PKG-FINAL` 全部通过后停在 `review / finished`。总控复算稳定终点后才派发 P4-C12。P4-C12 完成前仍不进入高保真财务驾驶舱开发，既定前端参考图和模型分工提醒门禁保持有效。
