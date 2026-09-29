# P4-B7-R1-E5-R1 阻塞总控核对

- 核对角色：头脑风暴总控
- 核对结论：接受 `blocked / finished`；E5-R1 的 Profile 引用修复方向正确，但发现桌面 canonical Profile 解析器违反既有冻结合同
- 原缺陷：`P4-E5-MODULE-001`，已完成第一层代码修复，尚未经过新 package 和最终 EXE 证明关闭
- 新缺陷：`P4-E5-PROFILE-PARSER-002`
- 下一任务：`P4-B7-R1-E5-R2`，精确同步 canonical Profile 语法，完成回归、一次 package 和一次最终 EXE 门禁

## 1. E5-R1 做对了什么

E5-R1 把 production contribution 和三个同源测试 fixture 从不存在的 `daily_finance.default` 改为后端真实 Profile `daily_finance.assistant@1`。总控复算以下七项仓库交付摘要，均与运行说明一致：

| 文件 | SHA-256 |
| --- | --- |
| `apps/desktop/src/modules/daily-finance/contribution.ts` | `5d5a72fb8a46bbcd18b7945bf0aaca610731ca096be8df32805b476b8e1d09b2` |
| `apps/desktop/tests/unit/registry.test.ts` | `08f8ad4190fcf62b2bc5b323029cea4563639edfee985e50073b1dc44a5ba375` |
| `apps/desktop/tests/unit/composition-root.test.ts` | `9b196a4cc4819aa8ee83ffa6111e903455cb4027a6b08340343ab588b0e14dcc` |
| `apps/desktop/tests/unit/host-client.test.ts` | `3d81cf9fac4ff6422ecc7ba573cf0384a05de5ca248433a9f3eed3a49d5598b3` |
| `apps/desktop/b7-r1-e5-r1-source.sha256` | `74b66ba69e71dcfec23dd7490a46290cd75a1d30c56841bb7d6bf72a822c88da` |
| `docs/b7-r1-e5-r1-module-contract-running.md` | `16ce863a9f9b2004f7d050107c2cd7c384e8c88e38fb1709cb15491708f6100a` |
| `docs/coordination/agents/executor.md` | `dfb428e3193d6daf8afdcf8e182a48f81b21e6fc9509b3a9352b1b1c220ca9e9` |

外部 `repository-delivery.sha256` 的 SHA-256 为 `75b5b806ccc5b270d6466d99e4e4297262d83f9cba747731ae33d41901e77786`。执行方记录的 12 项受限 evidence 清单 SHA-256 为 `a026bb620a89b710ff73ca789c7ae522be649695eba986c56b5a4a1678610827`。

OpenAPI drift、TypeScript 和 lint 均通过。定向 Vitest 的 3 个 HostClient 用例也通过，说明真实 Profile 摘要没有降低 HTTP DTO、401 single-flight refresh/retry 或错误边界。执行方在第一个产品断言失败后没有扩大范围、打包或启动最终 EXE，符合任务卡。

## 2. 新发现的精确缺陷

Python Host 的唯一 canonical 语法定义在 `src/wife_system/host/contracts.py`：

```text
^[a-z][a-z0-9_]{0,63}\.[a-z][a-z0-9_]{0,63}@(0|[1-9][0-9]*)$
```

其含义是：

- module 与 local 各为 1～64 个 ASCII 小写字母、数字或下划线，且首字符必须是小写字母；
- 中间使用一个点；
- 末尾必须有 `@major`；
- major 允许 `0` 或无前导零的非负十进制整数；
- 不接受空白、连字符、大写、Unicode 替代字符、trim、lowercase 或 normalization。

`apps/desktop/src/modules/registry.ts` 当前却使用：

```text
^[a-z][a-z0-9_.-]{0,139}$
```

它一方面拒绝必需的 `@major`，另一方面错误接受连字符、多个点以及没有版本的旧形状。D11 技术方案与 P4-IF-003 已明确要求桌面 module/Profile/SemVer 使用与 Python 相同的 ASCII 语法，因此这是既有实现违反冻结合同，不是新增架构需求。

E5-R1 把 contribution 改成正确值后，`compileRegistry()` 会在 Zod parse 阶段提前拒绝它，尚未进入 `intersectModules()`。定向 Vitest 的 3 个失败都来自这个 `invalid_format`。所以当前状态是：第一层错误引用已改正，但第二层旧解析器阻止正确合同生效。

## 3. 返修决定

不需要重新设计 Host，也不需要技术顾问。R2 只允许在 `registry.ts` 中把 Profile 正则精确同步为 Python `CANONICAL_ID_PATTERN`，并补上正反例测试。不得把规则放宽为“字符串里有一个 `@`”，不得增加 alias、fallback、trim、lowercase、Unicode normalization 或自动版本补全。

R2 必须同时证明：

1. `daily_finance.assistant@1` 和合法 `@0` 被接受；
2. module/local 的 64 字符边界与 Python 一致；
3. 缺少 `@major`、`@01`、负数、多个 `@`、连字符、多个点、大写、前后空白和全角字符被拒绝；
4. 原 E5-R1 的旧别名求交失败、module major 不兼容和全局冲突检查仍成立；
5. production contribution、Host 摘要和桌面 registry 能公开且只公开 `daily_finance`。

## 4. 为什么仍在同一 R2 完成 package 和最终 EXE

新缺陷只有一行产品解析合同及相邻测试，不形成新的阶段设计。为了避免“修一行、只跑一小段、再创建多个恢复任务”的局部循环，R2 在全部静态和执行方回归通过后直接获得：

- 新 C 盘 create-new 构建现场；
- package 预算 1/1；
- 新最终 `Maris.exe` 黑盒预算 1/1。

最终 EXE 必须重新证明两个窗口、安全隔离、runtime、`daily_finance`、毛毛状态、一次 recover、隐私和自然退出。失败时保留首个真实失败并停止；测试或 evidence 编排错误若尚未启动 package/产品，可按协调规则就地修正，不能把无副作用的核对脚本错误自动升级成新的完整返修。

## 5. 后续顺序

R2 全部通过后只提交 `review / finished`。总控复算 source、package 和动态 evidence 后固定 B7 稳定终点，再派发 P4-C12 独立验收。

P4-C12 完成以前不进入 P4-C 高保真财务驾驶舱开发。进入真实前端开发前，总控仍必须主动提醒用户复核两张参考图、页面/组件切片、视觉验收方式和当时的模型分工。
