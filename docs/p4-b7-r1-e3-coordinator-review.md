# P4-B7-R1-E3 总控核对：C 盘 Electron 最小三角验证

核对时间：2026-09-28，Asia/Shanghai

核对角色：头脑风暴总控

结论：接受 `P4-B7-R1-E3` 的 `review / finished` 交付和有限环境结论；允许进入一次性 package、app.asar 与最终 EXE 恢复门禁，不据此宣布 P4-B complete

## 1. 总控结论

总控接受 E3 的 A1 与 A2。两次动态 cell 都只执行了一次，使用同一份 Electron `44.4.5` 内容与同一最小 fixture，并且都完成了页面加载、成功 marker、日志、Windows 事件和进程收口门禁。

A1 原始 driver 返回码为 1，但这不是 Electron 进程失败。driver 把 `before-quit` 错列为必需事件，而 fixture 通过 `app.exit(0)` 退出；Electron 官方行为并不保证该路径产生 `before-quit`。原始结果已保留，没有覆盖或重跑。总控直接核对原始结果与后置合同验证后确认：browser 退出码为 0，实际事件顺序为 `app-ready → did-finish-load → normal-exit`，marker、日志、摘要、Windows 事件和 owned-process 收口全部满足 E3 任务卡的真实成功条件。因此 A1 记为通过，同时把 driver 的过严判定保留为测试编排勘误。

A2 通过 Playwright `1.63.0` 默认 Electron loader 启动，没有传 `executablePath`。Playwright 正常连接与关闭，Electron 退出码为 0，事件顺序、marker、日志、摘要、Windows 事件和 owned-process 收口均通过。

该结果只支持以下有限结论：C 盘同内容 direct 与默认 Playwright loader 均稳定；结合既有 D 盘 Playwright 最小 fixture 失败，证据优先指向执行位置、继承 ACL、ADS 或其他路径元数据相关差异。它不能区分其中哪一种机制，不能证明“D 盘本身就是根因”，也不能证明 app.asar、Forge package、最终 `Maris.exe` 或整个 P4-B 已通过。

## 2. 固定输入与仓库边界

| 核对项 | 总控结果 |
| --- | --- |
| E3 起点清单 | 211 项；210 matched，唯一 mismatch 是任务卡授权更新的 `docs/coordination/agents/executor.md`，0 missing |
| E3 source manifest | 198/198 matched，0 mismatch，0 missing |
| source manifest SHA-256 | `04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1` |
| E3 运行说明 SHA-256 | `f03fc8304bdfa0413a4bba5a3737b99082ebdd137e39c1edf7378f0d5ddec1cb` |
| executor 状态 SHA-256 | `2b240608e42cb75e5fb596b703eef06146fb9f6b75f3e02a3f07f978ac5b4985` |
| 产品/依赖/lock/H1 staging | 没有变化 |
| 独立测试、control、overview、其他角色 | 没有由执行智能体修改 |
| Git 写操作 | 执行智能体未执行 |

仓库交付只新增 E3 运行说明和 E3 source manifest，并更新执行角色日志。C 盘工具、fixture、profile、日志和二进制没有进入仓库或 Git 候选范围。

## 3. C 盘原始证据复算

受限原始现场保留在 E3 报告登记的 `C:\MarisE3\E3-20260928-0911`。总控进行只读复算，没有启动 Electron、Playwright、Maris 或 sidecar，也没有修改现场。

| 证据 | 总控结果 |
| --- | --- |
| final evidence manifest | 39/39 matched，0 mismatch，0 missing |
| final evidence manifest SHA-256 | `4b21b569e21a529a4743c53e115d1f035a6c51e75bd916948a2d37ccaac85b46` |
| Electron dist manifest | A1/A2 前后均为 `ffb4b389d5c454ca139cb6384f5ebb3d20633cf000960a8aa1b6c1794c9ebf8f` |
| fixture manifest | A1/A2 前后均为 `80e74627c3d2225567305e1ce425042b98598b0083556055276860a9ec0257bf` |
| A1 后置证据 | `66ede312d611251fe7152c4602473b21ad1797df3d8d78fb1820089c506120cb`；`taskContractSuccess=true` |
| A2 后置证据 | `da165cb856a141f10aaf3d0790a6254886de93497304bcc3e307d4b28e66001c`；`taskContractSuccess=true` |
| Windows 异常事件 | A1/A2 均为 0 |
| 最终 owned process | 0 |

A1 原始 JSON 明确保留 `expectedSequence=false` 与 `basicSuccess=false`，同时记录 browser `exitCode=0`、`timedOut=false`、marker 匹配以及实际三事件序列。后置验证没有篡改原始文件，只把任务卡要求与 driver 的额外 `before-quit` 要求分开判定。这足以解释返回码差异，不需要消耗第二次 A1 运行预算。

## 4. 关闭与保留的问题

本任务关闭的是“当前机器上的 Electron 44.4.5 是否在 C 盘同内容 direct/default Playwright 路线仍必然崩溃”这一门禁。答案是否定的：两条路线都稳定完成。

以下问题仍保持未验证：

- C/D 差异的具体根因；
- Forge 最终 package 是否精确使用 H1 allowlist；
- source tree 存在 `.pyc`、`.egg-info` 等污染时最终 resources 是否仍为零命中；
- packaged `app.asar` 是否能够驱动真实 Python Host、owner 会话、模块列表与 recover；
- production fuses 下的最终 `Maris.exe` 是否能够直接启动、通过 renderer 黑盒核对并完成 bounded shutdown；
- Tray 菜单真实点击、Windows 人工行为和 P4-B 的 24 项独立矩阵。

不再运行 D 盘最小 baseline、Procmon F1、诊断开关或 Electron 版本遍历。只要后续产品门禁在 C 盘稳定，就没有必要为了追求单一系统根因继续消耗当前产品开发轮次。

## 5. 后续门禁

下一任务为 `P4-B7-R1-E4`，固定在新的 C 盘短 ASCII 目录中执行：

1. 从 E3 198 文件稳定源码建立同摘要副本；
2. 在副本中故意放入 package 污染样本，再只运行一次 Forge package；
3. 核对 H1 staging、最终 resources、app.asar、fuses 和敏感信息扫描；
4. 只有 package 完全通过，才运行一次 packaged app.asar Playwright 门禁；
5. 只有 app.asar 完全通过，才直接启动一次最终 `Maris.exe`，通过动态 loopback CDP 只读调用现有 preload API；
6. 任一级失败立即停止，不在 E4 中边跑边改产品，也不自动创建返修任务。

最终 EXE 保持生产 fuses，不由 Playwright Electron launcher 启动。`MARIS_E2E_EXIT_MS` 只在隔离 profile 中触发与 Tray 共用的 `requestQuit → app.quit → bounded shutdown` 代码路径；真实 Tray 菜单点击仍属于 P4-C12 Windows 人工门禁，E4 不得将自动退出写成已经点击 Tray。

E4 通过后，总控再固定 B7 稳定终点并创建 P4-C12。测试智能体和技术顾问在此之前继续停止。
