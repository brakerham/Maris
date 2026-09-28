# P4-B7-R1-E5-FINAL 阻塞总控核对

- 核对角色：头脑风暴总控
- 核对结论：接受 `blocked / finished`；最终 EXE 启动路线有效，确认一个 P0 桌面模块合同接线缺陷
- 缺陷编号：`P4-E5-MODULE-001`
- 下一任务：`P4-B7-R1-E5-R1`，修正 Profile ID、补强真实合同回归、重新打包并单次复验最终 EXE

## 1. 已经证明有效的产品范围

E5-FINAL 不再受 Electron launcher 包装进程影响。Node `spawn(shell:false)` 返回的根进程就是冻结 `Maris.exe`，产品完成了受管 Python Host、认证、两个窗口、CDP、安全隔离和自然退出。

总控复算三份仓库交付摘要与报告一致。受限外部 `runtime-evidence.sha256` 共 82 个唯一条目，按 `path<TAB>bytes<TAB>sha256` 重新计算为 82/82 匹配、0 missing、0 mismatch；清单 SHA-256 为 `c8f93a29857c0a3dce89a78a72c8e1785be1be907579f10bd4369c19a262f5fc`。

本轮确认通过的门禁包括：

- 最终 EXE 直接根进程身份；
- 动态 loopback CDP；
- 一个主窗口和一个毛毛窗口；
- 两套冻结 preload bridge 与 renderer Node 隔离；
- 首次 runtime `online / managed / authenticated`；
- 隔离 owner session 和虚拟数据库；
- 日志、DOM、storage 与 bridge 的阶段性隐私扫描；
- 无 renderer crash、Windows Application 或 Code Integrity 异常；
- EXE、app.asar、source、Electron dist、Python resources、package out 与 fuses 不变；
- 产品自然退出码 0，最终产品进程、sidecar、监听和窗口为 0。

因此直接最终 EXE 黑盒路线继续采用，不返回 `_electron.launch()`，也不需要新的 Electron 环境诊断。

## 2. 首个真实产品失败

唯一一次 `window.maris.modules.list()` 返回 `[]`。执行方按冻结顺序以 `daily_finance_missing` 停止，没有调用 recover 或通过重跑覆盖结果。

该结果不是模块永久缺失的直接证明，但代码、冻结合同、隔离数据库和 package 内容共同给出充分根因：

| 层 | 实际值 |
| --- | --- |
| Python `daily_finance` manifest | `daily_finance.assistant@1` |
| D11 已冻结的桌面引用 | 必须精确使用 `daily_finance.assistant@1` |
| TypeScript contribution | `daily_finance.default` |
| registry/composition/host-client 单元 fixture | `daily_finance.default` |
| 全新隔离数据库的 `module_setting` | 0 行，没有禁用 override |
| 冻结 app.asar | 错误别名出现 2 次；正确 Profile 出现 0 次 |

`DesktopCompositionRoot` 会把 Host 模块安全摘要与本地 compiled registry 求交集。`intersectModules()` 要求 Host 的 `profile_ids` 包含 contribution 的 `agentPanel.profileId`。生产 Host 返回真实 Profile，而桌面 contribution 要求不存在的别名，因而 `daily_finance` 被 fail-closed 过滤，renderer 最终看到空数组。

现有单元测试没有发现问题，因为三个 fixture 与错误 contribution 使用了同一个伪造别名。这是测试数据复制实现错误而形成的同源盲点。

## 3. 返修边界

本缺陷不需要技术顾问重新设计，也不修改 Python Host、模块注册算法、认证、IPC、fuse、依赖或迁移。最小产品改动是把桌面 contribution 的 Profile 改为已冻结的真实 ID，并让相关单元 fixture 使用真实 Host 合同。

返修必须补充以下反例：

1. `daily_finance.assistant@1` 与当前 Host 摘要求交后加载模块；
2. 旧的 `daily_finance.default` 不得再次作为兼容 Profile；
3. composition root 使用真实 Profile 时公开 `daily_finance`；
4. HostClient 的严格 DTO fixture 使用真实生产摘要；
5. 全仓桌面源码和测试中 `daily_finance.default` 为 0 命中。

源代码修复会改变 app.asar，因此不能复用旧 package。执行方在静态回归通过后，只允许重新 package 一次，并在新产物上直接运行最终 EXE 一次。package 或动态门禁任一失败立即停止，不得在同一任务内修复后重跑。

## 4. 后续顺序

`P4-B7-R1-E5-R1` 通过后只能提交 `review / finished`。总控复算新 source、package 和动态证据，形成 B7 稳定终点，再派发 P4-C12 独立验收。

P4-C12 前仍不进入 P4-C 高保真财务驾驶舱开发。真实前端提醒和模型分工门禁保持不变。
