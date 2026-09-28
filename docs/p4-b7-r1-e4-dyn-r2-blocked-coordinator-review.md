# P4-B7-R1-E4-DYN-R2 阻塞总控核对

- 核对角色：头脑风暴总控
- 核对结论：接受 `blocked / finished`；关闭 Playwright `_electron.launch()` 所有权识别路线，不创建 DYN-R3
- 产品结论：`unverified`；没有产品通过证据，也没有产品 crash 证据
- 下一任务：`P4-B7-R1-E5-FINAL`，只运行一次最终 `Maris.exe` 黑盒门禁

## 1. 总控复算

仓库交付摘要与执行方报告一致：

| 文件 | SHA-256 |
| --- | --- |
| `docs/b7-r1-e4-dyn-r2-running.md` | `190182acfc02c31f88d0557dbb630cff8d24126e14a00b485df0c43f234a4ef2` |
| `apps/desktop/b7-r1-e4-dyn-r2-source.sha256` | `5e3b788c6ec2f8e125dd345a6e833beb530cd8790de12817f9342711373ea228` |
| `docs/coordination/agents/executor.md` | `f9907bc03feb33c9c8cb8e11e35a7b71132b1f9b47b6d155df02e398075e4e3a` |

受限外部 `runtime-evidence.sha256` 使用 `path<TAB>bytes<TAB>sha256`。总控按该格式重新计算，79 项全部匹配，0 missing、0 mismatch；清单 SHA-256 为 `8872b541c2505e0a8b11df65c178ee0c7b3ca6d8ac6a66d277a31e48554e3aff`。

固定 EXE、app.asar、73 项 Electron dist、67 项 Python resources、140 项 package out 和 production fuses 均保持冻结值。最终产品进程、窗口和监听为 0，Git index staged paths 为 0。

## 2. 失败发生在哪里

DYN-R2 只运行一次 P1，持续 3,593 ms，没有超时。失败发生在任何 `window.maris` API、窗口断言、renderer 安全断言或 `runtime.recover()` 之前。

原始进程快照只观察到两层：

```text
Playwright 返回 PID：cmd.exe，仍存活
└── 直接子进程：冻结路径的 electron.exe
```

任务卡允许两种情形：返回 PID 本身就是 Electron；或者返回 PID 已退出后提升唯一 Electron 子进程。本轮出现第三种形态：返回 PID 是仍存活的命令包装进程。runner 正确遵守冻结规则，以 `browser_root_launch_identity_mismatch` 停止，没有临时放宽规则或重跑。

隔离 profile 已创建加密 owner session 和虚拟数据库，日志没有 `0xC0000135`、`0x80000003`、`Target crashed`、assertion、Application 或 Code Integrity 异常。这些只能证明应用启动到部分本地状态，不能替代尚未执行的产品门禁。

## 3. 路线裁定

`automation_route_exhausted=true` 成立。DYN-R1 和 DYN-R2 已经证明 `_electron.launch()` 返回的进程句柄在本机可能表现为退出的包装进程，也可能表现为仍存活的 `cmd.exe`。继续添加第三套 PID 提升分支只是在修测试工具，而不是验证用户最终运行的产品。

因此：

1. 不创建、不建议 DYN-R3；
2. 不再运行 packaged app.asar 中间门禁；
3. 不再使用 Playwright `_electron.launch()`；
4. 不重新安装、测试、构建或 package；
5. 直接验证用户实际使用的最终 `Maris.exe`。

## 4. 新路线

`P4-B7-R1-E5-FINAL` 只有一个动态 cell，预算 1/1：

1. Node `child_process.spawn()` 直接启动冻结 `Maris.exe`；返回 PID 必须是路径和启动时间都匹配的产品根；
2. 只使用全新隔离 profile、虚拟数据库、最终 resources 和已验证 Python；
3. CDP 使用 `--remote-debugging-address=127.0.0.1 --remote-debugging-port=0`；从新 profile 的 `DevToolsActivePort` 读取动态端点；
4. Playwright 只通过 Chromium `connectOverCDP()` 附加 renderer，不再启动 Electron；
5. 验证主窗口、毛毛、安全隔离、runtime、`daily_finance`、一次 recover、隐私和 bounded shutdown；
6. 使用 `MARIS_E2E_EXIT_MS` 触发产品现有的 `requestQuit → app.quit → bounded shutdown`，最终验证进程、Python sidecar、端口、窗口和 Tray 全部收口。

这条路线复用此前已经冻结但从未执行的最终 EXE P2 合同，只取消无产品价值的 app.asar 前置条件，不改变产品、安全设置、fuse、依赖或 package。

## 5. 后续门禁

E5-FINAL 通过只能形成执行方 `review / finished`，随后总控生成稳定终点快照并派发 P4-C12。P4-C12 仍负责 24 项独立矩阵和 Windows 人工门禁。

若 E5-FINAL 发现真实产品错误，交回执行智能体做产品返修；若 CDP 在不改变产品或 fuse 的前提下不可观察，记录真实黑盒边界并改由 P4-C12 的人工界面检查补足。不得再回到 `_electron.launch()` PID 识别路线。
