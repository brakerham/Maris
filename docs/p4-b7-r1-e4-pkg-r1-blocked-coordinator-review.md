# P4-B7-R1-E4-PKG-R1 阻塞总控核对

## 结论

`P4-B7-R1-E4-PKG-R1` 的停止符合任务卡，状态接受为 `blocked / finished`。阻塞来自执行方证据核对代码错误，不是 pnpm、Forge、package 或 Maris 产品失败。package 没有启动，次数保持 `0/1`。

总控基于冻结的原始文件独立判定六项预检实际全部通过。后续不得重跑 Q1～Q6；直接发布 package-only 任务。

## 六项真实结果

| 项目 | 总控核对结果 | 原始证据 |
| --- | --- | --- |
| Q1 | 第一条为任务专属 `pnpm.cmd` | `Q1.stdout.log`、`Q1.result.json` |
| Q2 | `12.7.0` | `Q2.stdout.log`、`Q2.result.json` |
| Q3 | `undefined` | `Q3.stdout.log`、`Q3.result.json` |
| Q4 | `undefined` | `Q4.stdout.log`、`Q4.result.json` |
| Q5 | `hoisted` | `Q5.stdout.log`、`Q5.result.json` |
| Q6 | Forge `spawnPackageManager` 四个查询全部成功 | `Q6.stdout.log`、`Q6/inner-1`～`inner-4` |

Q6 的 stdout 是严格 JSON：

```json
{"version":"12.7.0","hoistPattern":"undefined","publicHoistPattern":"undefined","nodeLinker":"hoisted"}
```

四个 inner result 均为 `exitCode: 0`、`signal: null`、`resolved: true`；四个 stderr 文件均为 0 字节，stdout 摘要分别与 Q2～Q5 一致。`probe-receipt.json` 记录固定 Node probe 的参数数量和进程 ID。

## 失败分类

执行方核对从 `inner-0-result.json` 开始读取，而冻结 probe 的序号范围是 `inner-1`～`inner-4`；同时读取了不匹配的 receipt 字段。异常发生在 Forge probe 已正常结束之后，所以：

- Q6 的真实工具调用已经成功；
- Q6 外层独立 result 和精确结束时间没有落盘；
- 缺少外层 result 不推翻已存在的 stdout、四组 inner start/result/streams 与 probe receipt；
- package 未启动，不能形成 package 结论；
- 不需要重跑 Q6 来补一个派生摘要文件。

## 摘要与边界

- 235/235 起点匹配；终点只有授权的执行日志变化和两份新增交付。
- 三份仓库交付摘要与报告一致；组合清单 SHA-256 为 `7ad794aa2906710fed7049ed0150bac4e688b81d54a06aaee57d1f781315b0be`。
- 外部 evidence 清单 45/45 逐项匹配，SHA-256 为 `776c58212d5b70af06968747c65cb1bd2456cc421bae98120ef04b5138b04391`。
- source、Electron dist、marker、node_modules 和 lock 均保持冻结值。
- PATH 与 `ELECTRON_CACHE` 已还原；任务自有进程为 0。
- `out` 与 staging 不存在；package、app.asar、最终 EXE、P4-C12 均 `not_run`。

## 后续裁定

发布 `P4-B7-R1-E4-PKG-R2`，范围严格为一次真实 package 和成功后的静态产物核对：

1. 只读复算本轮六项预检证据，不执行它们。
2. 用相同任务专属 PATH 配方执行一次现有 `pnpm run package`。
3. package 进程失败时立即停止，不修复后重跑。
4. package 成功后，静态检查 EXE、app.asar、fuse、资源 allowlist 与 staging 收口。
5. 静态核对代码若出错，可以在不改变 package 产物的前提下修正并继续只读核对；不得因此重新 package。
6. 不启动 app.asar、最终 EXE、Electron、sidecar 或 P4-C12。

