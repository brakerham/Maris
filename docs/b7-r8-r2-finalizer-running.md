# P4-B7-R8-R2-FINALIZER 执行方运行说明

状态：`review / finished`。生成时间：2026-10-30T18:09:02.003289+08:00。唯一负责人：执行智能体。本轮继续同一 R2，未创建后续任务。执行方验证通过，独立验收与缺陷关闭由总控另行安排。

## 起点、范围及保留输入

- 最新 control 版本：2026-10-29T19:50:00+08:00。首次接单前按 AGENTS 读取必读文件、本人状态、完整原 R2 卡及总控裁定。
- v2 起点 1376 项全部匹配；清单 SHA-256：`e178777210b867ecb88cedb3798a1c17915d68aea43373644841ac0621a03cd8`。原 1375 清单与接单前 1374/1375 阻塞记录不变。本次才首次登记接单，之前只读核对不计工具或 EXE 额度。
- 中断续接、工具冻结前及交付时复核 1375 个非 executor 起点文件；唯一已有仓库文件变化为本人日志，另新增本说明和本轮 source 清单。没有忽略新的角色日志差异。
- 仓库精确三交付：[本说明](b7-r8-r2-finalizer-running.md)、[终点 source](../apps/desktop/b7-r8-r2-finalizer-source.sha256)、[executor 状态](coordination/agents/executor.md)。产品、测试、依赖和其他协调文件没有变化。
- 新外部根：`C:/MarisSettingsR8/R8-R2-20261030-040716`。创建前确认绝对范围、未存在和无 reparse；收口再次逐项确认新根无 symlink/junction。只使用新虚拟 profile/owner/数据库/AppData，旧 profile 未复制、未读取正文、未改写。
- 固定产品仍是 `C:/MarisSettingsR8/R8-20261019-103900/workspace/apps/desktop/out/Maris-win32-x64/Maris.exe`；EXE SHA-256 为 `c80d27c8e31fa60df91065a770e669a553260cf8f883c55a0a7f83f8a430736b`，asar 为 `05cdad34ba60b59773eebe671156c96260e69354568b9942da59058641f9c0b2`，lock 为 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。

## 最小工具修正和冻结

功能变化限任务外 controller 与单一 `finalizer.mjs` 及共用函数自检；native-process、node-fixture、settings-exe-runner 与原件的变化严格等于新根/任务标签机械替换。原件四文件副本、复制摘要、机械 diff、最终 diff、每版六文件输入均保留。

- 产品结果只读取一次，读取/解析/结构异常均受保护；核对真实生产者 schema/task/scenario、严格 success=true、26 项必需 gate、S1 的39项和S2的42项必需比较。失败对象不补成成功，空集合或缺项拒绝。
- 共用 record/save/append/fail 与 exit/stdout/stderr 回调捕获输出失败并通知主流程收口。保留首错，后续解析/输出/清理错误单列；默认 stderr 后备用同步 `fs.writeSync(2, ...)` 捕获管道错误。
- 原生回执先解析并消费身份再保存证据；证据写失败仍保留身份。worker marker 在启动前准备。操作请求文件自身不可写且没有有效缓存时，仍可能无法完成原生查询/清理，必须保留 unknown 和非零结果；不宣称所有磁盘故障都能生成 result 或完成清理。
- 内层 finally 逐项释放 stdout、stderr、child；一项失败不跳过其他动作。最终通过同时要求完整业务结果、真实 root/worker exit0且signal=null、三类资源0和墙钟未超限。没有增加进程管理层或改变身份算法。
- 工具共2版，约18分钟实际开发（首段约10分钟，17:53续接至17:59:48冻结；中断、审批等待不计），未达到25分钟/3版上限。冻结后未再编辑工具。
- 冻结清单 `evidence/frozen-tools.sha256`：6文件，SHA-256 `c2f231c2d30ad014bc87da919a50c6a0f441b755132680eb73e371b22b6e5472`。

| 冻结工具 | SHA-256 |
| --- | --- |
| `controller.mjs` | `817ca219ab57980b75b9d9bd7e504420413eae16d35c72eadee29406169441b3` |
| `finalizer-selfcheck.mjs` | `c7d0485e58b413678894d618d062f189470f31ec4d0b69aadfc7c85a93116975` |
| `finalizer.mjs` | `9e23bbe43062e57ef573c18cbb934842adfaa725c154bae7fbf5fa2d4ca9b9f1` |
| `native-process.ps1` | `8657429cfcbe2bcdcb16e2642f8c8ac0a7338b2470a98e0d4466b6552d5d43f5` |
| `node-fixture.mjs` | `3810642947f17c16894a5b8ec611a5b9b4088032b1b39e9e57a577419f33f0ee` |
| `settings-exe-runner.mjs` | `8916ba5dd6d610a884fa0a2fd7d74481a2b568a6b940dd6ed25ad8031902c9e5` |

内部临时实现子任务只负责共用模块/只读审查，由父执行统一集成；没有启动 Tester 或技术顾问，没有独立验收。最后审查对应路径、字段、首错、期限、释放和S2放行；三项静态问题均已在冻结前修正。

## 开发自检与首次失败

| 分组 | 结果 | 口径 |
| --- | --- | --- |
| 第一版语法 | 5/5通过 | Node --check；无产品启动 |
| 共用注入IO自检 | 47场景、267唯一比较通过 | 实际使用同一finalizer，完整26gate/39比较合同；0失败 |
| 第二版受影响自检 | 10场景、69比较通过 | 仅IO/回调/回执/后备输出相关分支复验；不加算为336唯一比较 |
| 第二版语法 | 3/3通过 | 只检查变化的controller/finalizer/selfcheck |
| Node集成第一次 | failed，13,953ms，controller exit1 | Node真实自然exit0；监听查询失败，最终资源部分unknown；第一份证据保留 |
| Node集成第二次 | passed，11,381ms，controller exit0 | Node真实自然exit0/signal=null，进程/监听/窗口0，fixture=true/productStarts=0 |

自检逐项覆盖合法完整成功、完整/简化失败、ENOENT/EACCES、空/坏JSON、null/数组、错schema/task/scenario、success类型、缺/假gate、空/缺/假/重复/不一致comparison、首错叠加解析与输出异常、result/first-failure/journal/terminal/exit/双流写失败、native证据写失败后身份保持、cleanup失败叠加读取失败、三个释放动作分别抛错、过期、未知root/worker退出、残余资源和所有输出均不可用。267是唯一比较ID数，不把故障注入的预期错误当成测试失败。

首次集成首错是 `fixture_listeners_query_failed`。原控制器没有保存该查询的原始status/stderr，具体首次查询根因仍为unverified；后续只读同类查询2830ms返回0监听不改写原结果。已证实的本轮控制器缺口是该回执未保存及异步stderr后备风险；第二版保存原始查询回执、改同步后备，并在原15秒硬期限内调整查询局部预算（保留1750ms）。仅使用卡内最后一次定向补验，未执行第三次集成。第一次缺少虚拟结果引起的ENOENT和资源未核实错误也保留。

续接只读审计首条命令误将TAB清单按双空格拆分而exit1，在任何文件写入前停止；随后按实际TAB格式复算通过。记录见 `evidence/resume-readonly-error.json`。初始Git读取曾报告全局ignore权限警告；最终获准只读Git命令无stderr、暂存区为空。没有安装/build/test框架运行，因此没有相应新增skip；原217开发和25身份集合均明确未重跑，不记为本轮通过数。

## 同包S1/S2真实页面结果

| 项目 | S1 | S2 |
| --- | --- | --- |
| 产品启动 | 1次 | 1次；S1全过后顺序启动 |
| 必需gates | 26/26通过 | 26/26通过 |
| 唯一比较 | 39/39通过 | 42/42通过 |
| 控制器完整运行 | 40,560ms，exit0 | 33,646ms，exit0 |
| root与worker真实退出 | 各exit0、signal=null | 各exit0、signal=null |
| 首样主题/隐私 | light/off；select light、checkbox false | dark/on；select dark、checkbox true |
| 设置动作 | 真实界面保存dark/true | 设置写入0、seed0 |
| recover | 恰好1次；页面/路由/设置保持 | 0次 |
| 关闭 | 已核实可见主窗口正常WM_CLOSE | 已核实可见主窗口正常WM_CLOSE |
| 最终资源 | 进程0/监听0/窗口0 | 进程0/监听0/窗口0 |
| 强制收口 | 未使用 | 未使用 |

后台online/authenticated、canonical daily模块列表，与实际页面daily/Shell/导航/Agent的存在、唯一数量和可见性分别记录；没有用后台正确替代DOM结果。两场景毛毛可见、closePolicy=quit，没有MARIS_E2E_EXIT_MS，没有app.quit/process.exit/CDP Browser.close或强杀替代自然退出。

S1实际界面保存后的设置、S2启动前、S2首次有效样本的设置文件SHA-256均为 `c4a59c9ec06fe45910a5eab4d1bf0e9a438856cdcd064489f7cd9b6c055ff622`，412字节。S2首次有效样本四条断言同时为dark/on/dark/true；driver设置写入0仅证明driver没有写，不能外推为监控产品全部内部写入。未通过刷新、再次设置或重启修正首样。

证据分别在 `evidence/settings-exe-S1`、`settings-exe-S2`（runner首次结果/比较/真实页面/原生回执）及 `controller-S1`、`controller-S2`（真实worker退出/收尾判定/释放）。安全摘要为 `S1-safe-summary.json`、`S2-safe-summary.json`。两场景总81个唯一产品比较，gate比较已包含，不再另加52。

## 资源、输入不变性和额度

- 最终资源复核18:05：任务标记进程0、已记录产品PID监听0；窗口0来自两份不可变场景原生终态回执，未声称额外枚举。没有额外终止进程。root与worker退出码来自实际事件，其他历史子进程退出码仍按runner记录unknown，不用root码替代。
- 原R8构建1365、out140、Python资源67、工具14、旧生命周期63和证据108项终点全部匹配；实际Node/Playwright/Python/lock关键入口匹配。完整旧依赖审计引用已绑定结果，未重扫或重装依赖。
- 原R1工具5、证据115以及旧报告/旧source两交付原字节保持；旧3交付清单自身保持，executor是本卡唯一授权覆盖项。旧closeout摘要保持 `6aa135ad767efa947179c6a7c4415bd0f8784269b40cad94d4dae168ad6c8644`。
- 本轮package0、EXE2/2、helper0；R8系列package1/1、EXE3/3、helper0。Tester原累计产品2/8、helper3/6不变。
- 新profile、虚拟数据和全部证据保留，无删除volume、全局设置或其他任务资源操作；未启动Docker、微信、OpenClaw、真实provider，未读取真实密钥或个人数据。

## 交付摘要与复算

仓库3文件；终点source 1377项（v2的1376项更新本人状态、加入本说明，排除source自身），UTF-8无BOM、LF、path TAB sha256、ordinal排序。外部工具6项、原输入副本4项，证据清单255项。所有逐文件摘要见对应清单；三份仓库交付摘要不写回自身，统一由外部 `evidence/delivery-three.sha256` 和 `evidence/closeout.json`绑定，避免循环。

- 外部证据：`C:/MarisSettingsR8/R8-R2-20261030-040716/evidence/evidence-manifest.tsv`，相对evidence根，排除自身、delivery-three.sha256、closeout.json；这三项的关联在closeout明确列出。
- 工具清单：`evidence/frozen-tools.sha256`，相对新根；输入副本清单：`evidence/inputs.sha256`，相对新根。
- 可复算总摘要：逐文件按ordinal路径排序写入规范清单后，直接对清单原字节做SHA-256；文件行是路径、TAB、字节SHA-256、LF。closeout给出各清单条目数和原字节摘要。
- 终点输入审计：`evidence/end-input-audit.json`；当前资源：`evidence/final-resource-check.json`；原始失败、工具每版和静态审查均保留。

没有执行任何Git写操作或暂存，旧`.pnpm-store`仅作为已存在的未跟踪目录保留。本任务交付停在review/finished，不关闭SETTINGS-001/CMP-06/LAZY-001/UI-02/P4-B，也不启动独立验收或其他后续任务。
