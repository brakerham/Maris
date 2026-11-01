# P4-B7-R9-IPC-ORIGIN：开发 IPC 来源精确校验

## 负责人、目标与固定输入

唯一负责人为既有执行智能体。按AGENTS读取必读、最新control、本人executor、本卡及[总控裁定](../../p4-c12-r10-ipc-origin-coordinator-review.md)、[R10报告](../../testing/phase-4-c12-r10-settings-windows-report.md)、IF-003 §4、SETTINGS-R8补充合同。Tester和顾问停止。本任务只修 `IPC-ORIGIN-001`，不重启旧R8/R10或处理其未完成Windows条件。

按仓库原字节复算[新起点](../snapshots/p4-b7-r9-ipc-origin-start.sha256)，路径唯一有序、UTF8无BOM/LF、`path<TAB>sha256`、不含自身，全匹配且staged=0后登记接单。R10的50交付/8正式来源/29首次清单按其实际根核对；4份共享测试文档以新起点为准。旧独立首次材料不可改写，不运行独立测试。

复用固定R8根 `C:/MarisSettingsR8/R8-20261019-103900` 的已验证工具/普通依赖和本地Electron ZIP，旧根全部只读。读取其 `evidence/closeout.json`、输入/产物清单及R8-R2收口记录；完整历史依赖审计引用绑定结果，核对实际使用入口，不每条命令重扫或重新安装。

| 固定项 | SHA-256 |
| --- | --- |
| pnpm-lock.yaml | `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |
| 原R8 EXE | `c80d27c8e31fa60df91065a770e669a553260cf8f883c55a0a7f83f8a430736b` |
| 原R8 app.asar | `05cdad34ba60b59773eebe671156c96260e69354568b9942da59058641f9c0b2` |
| 官方本地Electron ZIP | `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d` |

Node24.21.0、pnpm12.7.0、Electron44.4.5、Playwright1.63.0和已有Python保持，不下载/安装/换版本、修改永久PATH或系统设置。新外部根仅 `C:/MarisIpcR9/R9-<时间戳>`：先检查绝对范围、未存在、无reparse，再普通复制必要工具/依赖和按起点物化本次源码，不用junction，不污染源目录。旧profile无需复制，不解密，不创建产品profile。

## 精确文件范围

仓库最多7个交付路径：

1. `apps/desktop/electron/main/security.ts`：唯一产品修改。
2. `apps/desktop/tests/unit/security.test.ts`：来源比较边界。
3. `apps/desktop/tests/unit/ipc.test.ts`：实际validateIpc的来源/身份/参数邻接。
4. `apps/desktop/tests/unit/settings-snapshot.test.ts`：扩展既有虚拟main fixture的开发来源输入，验证真实注册handler；保留已有用例和断言。
5. 新 `docs/b7-r9-ipc-origin-running.md`。
6. 新 `apps/desktop/b7-r9-ipc-origin-source.sha256`。
7. 本人 `docs/coordination/agents/executor.md`。

不改main/index、ipc-contract、preload、renderer、settings-hydration、依赖/lock、Forge/wrapper/staging、migration、独立材料、其他角色、control/overview/矩阵或旧证据。不执行Git写操作。若所需修复超出这一安全谓词范围，报告具体证据后停止，不顺手重构架构。

## 开发来源合同

- 原反例受信配置为 `http://127.0.0.1:5173`（无尾斜杠）；同源 `/index.html` 应通过，`http://127.0.0.1:51730/index.html` 必须拒绝。带/不带尾斜杠的合法配置都应有效，不能只补一个斜杠绕过反例。
- 开发网络分支分别解析配置和实际URL，仅允许HTTP/HTTPS、无用户名密码的绝对URL，精确比较规范化origin（scheme、host、有效port）。不同scheme/主机/端口拒绝；同origin不同path/query/hash可以通过。用平台URL语义处理主机大小写与默认端口，不手写字符串截断、startsWith/includes/正则前缀，不做DNS或localhost/127.0.0.1别名等同。
- 无开发配置不额外放行网络URL。配置或请求解析失败、不允许的协议、credentials、opaque/null origin不放行开发网络分支，也不把解析异常向调用者泄露。blob中嵌套相同HTTP origin不能通过协议检查。空值/非法配置仍保持fail-closed网络行为。
- 现有生产 `file://` 和 `maris://app/` 分支语义保持，不能用所有URL的origin相等来把file/data等null来源都放行。该兼容要求不等于宣布这些生产路径完整安全验收通过。
- `validateIpc` 的sender/mainFrame优先检查、原参数严格schema和 `ipc_origin_rejected` 错误保持；实际main与companion各自只信任自身开发来源。不能把两窗口来源取并集、改参数协议或新增IPC能力。

## 回归和开发门禁

先在执行方测试中保留原反例红灯，使用真实生产isTrustedRenderer/validateIpc及真实main注册路径；不复制独立测试代码或运行 `tests/independent/**`。保持sender与同一个mainFrame对象，仅改变frame.url，使失败确实来自origin而非sender不匹配。红灯预期失败保留，不限制正常开发阶段的定向修改调试。

| 覆盖组 | 必要证据 |
| --- | --- |
| 正向与原反例 | 同源正对照，5173/51730反例，配置尾斜杠两形态，同origin不同路径/query/hash |
| 近邻来源 | scheme变化、不同主机与主机后缀欺骗、不同端口、带credentials；两个方向按各自配置核对 |
| 解析与协议 | 非法/相对/空配置或请求，不允许的data/javascript/blob等；安全拒绝且无原始异常泄露；HTTP/HTTPS默认端口与主机大小写正向对照 |
| 生产邻接 | 未配开发地址时合法file/maris仍通过，原不可信网络/maris相似主机仍拒绝，sandbox/CSP不变 |
| 实际接线 | main设置getter同源返回三字段，错origin拒绝且不保存/恢复Host/改outbox/开窗口；至少一个写handler证明在业务执行前拒绝。companion的真实handler使用独立开发配置，正确来源通过、另一窗口来源拒绝 |
| 原合同 | 错sender/subframe与错误参数仍分别拒绝，三字段getter/update不扩大；已有断言不降低 |

可在原settings-snapshot fixture增加可选开发地址和必要安全计数，默认仍保持原用例行为；不得mock掉isTrustedRenderer/validateIpc/被测handler。比较安全的值或调用增量，不把启动阶段已有调用当作拒绝后的新副作用。

最后定向运行security、ipc、settings-snapshot三文件及未修改settings-hydration一次，分列唯一节点与复跑；TypeScript/lint通过。完整217项、旧模块/退出/冷入口/H1/独立集合不重复。若新变更引出明确相邻失败，可在开发范围内定位修正并保留首次；修复必须扩大产品文件范围则停止。无skip/xfail或减少原断言。

## 一次新包，动态目标零次

开发门禁通过后冻结构建输入，只用已验证的任务局部pnpm与LOCALZIP路径执行原package wrapper。先静态确认子进程PATH、本地ZIP、清单格式和新根参数；不重新开发Windows身份/收尾驱动，不触碰旧失败现场。

本轮 **package最多1次，EXE/Electron应用启动0、helper0、开发服务器0**。这是新的执行方返修打包额度；旧R8 package1/1、EXE3/3实际使用不改写。Tester产品2/8、helper3/6继续冻结。仅打包工具自身必要Node进程不算产品启动；不得运行新EXE或electron夹具作“工具自检”。

保留原7项静态产物门禁：生产fuses、完整out及67项Python资源、污染文件和staging残留、包完整性；核对实际main bundle中本次origin校验进入app.asar及来源映射。production构建可能内联/裁剪代码，按构建映射和实际调用证明，不能单靠全包字符串搜索或EXE hash判断修复。不要修改bundle或测试正式产物的动态入口。

唯一package失败时保留首次并停止，不换版本、不再打包。成功也将新包真实运行明确记not_run，旧S1/S2只能列历史执行方结果，不作为新包动态通过。新包、构建/资源/工具/证据清单保留供独立复验。

## 交付和停止

运行说明记录红灯、开发变更/唯一节点、原行为保持与新包静态结果、错误和未验范围。终点source由本起点更新授权路径并加入新说明，排除自身；逐文件清单与总摘要可复算，包及实际构建输入单独绑定。只清理本轮已核实绝对边界且无reparse的临时项；旧profile/证据不动。

接单、修复与定向验证、package前后、阻塞/交付更新本人状态；长操作先记下一检查点，有控制时至少10分钟心跳。没有有效新输出的相同环境阻塞连续两个检查点停止，不盲目重试；普通开发调试不冒充独立验收。完成交 `review / finished`，未通过则 `blocked / finished`；不关闭IPC-ORIGIN-001、SETTINGS-001、SEC-04或P4-B，不启动Tester/顾问或P4-C。真实前端阶段的参考图和模型策略提醒继续保留。
