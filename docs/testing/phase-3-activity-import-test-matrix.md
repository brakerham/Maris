# P3 Markdown 活动模板导入独立验收矩阵

- 任务：`P3-C8`
- 状态：`review`（P3-C9-R2 已执行；89 项适用案例全部通过）
- 设计日期：2026-09-18（Asia/Shanghai）
- 性质：C8 设计经 P3-C9 和 P3-C9-R2 在各自固定快照上执行；当前逐案状态均为 `passed`
- 数据边界：只允许虚拟活动、虚拟账户和脱敏 canary；不得使用真实财务数据、聊天内容或账号标识
- 依据：`docs/phase-3-activity-import-brief.md`、`docs/project-plan.md`、`P1-IF-001`、`docs/coordination/prompts/p3-c8-tester.md` 及 `2026-09-18T15:20:00+08:00` 版控制文件

## P3-C9-R2 最终执行摘要

- R2 固定快照：开始前和结束前 22/22 单文件摘要与总摘要均匹配 `P3-B5-R1-SHA256:fb46b8fa4957c93bfd8f971b1fd987e45dd4779e8d6eac2907660fa2f1fef53c`；原 C9 报告原始字节摘要仍匹配 `d0b2189ec65d477a6fcefa9790898b5840d4f330f2ed713a6684346b8fada83b`。
- 返修边界：与原 C9 快照相比，只有 P3 migration 和执行方 migration 测试两个获准文件变化；外键名 `fk_activity_template_revision_import_candidate` 长 46，upgrade/downgrade 对称。
- 本地证据：独立 81 passed；执行方 144 passed；旧 migration 定向 4 passed。
- 真实 PostgreSQL：执行方 9 passed；独立 10 passed。空库与既有 P2 schema 升级、并发、事务回滚、约束和恢复均进入实际断言，无 skip、setup error 或产品失败。
- 最终逐案结论：89 `passed`、0 `failed`、0 `blocked`、0 `not_applicable`。`P3-C9-PG-001` 已由固定返修快照关闭，建议总控接受 P3-B5-R1；最终 `complete` 仍由总控决定。
- 资源：只启动 `finance-postgres`；结束时普通 `docker compose down`，未删除 volume，最终服务列表为空。
- 详细证据：[P3-C9-R2 独立验收报告](phase-3-c9-r2-activity-import-report.md)。

## P3-C9 历史执行摘要

- 固定快照：22/22 单文件摘要和总摘要在执行前、执行后均匹配 `P3-B5-SHA256:9fb36c653d20ff14f85ad9667de454900cca0c6e3ead17c2619df11fb7f63d6e`。
- 逐案结论：64 `passed`、1 `failed`、24 `blocked`、0 `not_applicable`，共 89 项。
- 本地独立证据：PU/SQLite/HTTP/迁移 81 passed；执行方 P3 本地复跑 143 passed；受影响旧回归 92 passed/4 skipped，随后真实 PostgreSQL 相邻 4 项定向通过。
- PostgreSQL 缺陷：`P3-C9-PG-001`。P3 migration 的显式外键名超过 PostgreSQL 63 字符上限，空 schema 无法升级到 P3 head；`P3-DB-03` 为 `failed`，其余必须取得 P3 SPG 证据的 24 项为 `blocked`。
- 资源：只启动 `finance-postgres`；结束时普通 `docker compose down`，未删除 volume，最终服务列表为空。
- 详细证据：[P3-C9 独立验收报告](phase-3-c9-activity-import-report.md)。

## 记号与判定规则

| 记号 | 含义 |
|---|---|
| PAR | Markdown 解析与规范化层 |
| PURE | 预览纯度与候选生成层 |
| DOM | 领域服务、确认与批处理层 |
| API | FastAPI/Pydantic HTTP 边界 |
| DB | 持久化、约束与事务层 |
| SEC | 安全、隐私与资源限制 |
| PU | 无数据库的纯函数环境 |
| SS | 临时 SQLite 环境 |
| SPG | 真实测试 PostgreSQL 环境 |
| HTTP | 本地应用 HTTP/TestClient 环境，不访问外网 |

“条件断言”表示 P3-IF-001 冻结后必须把唯一允许行为、错误码、上限或事务范围写入执行版测试；在冻结前不把任一候选方案当成产品结论。通过证据必须来自固定快照上的可重复断言，并包含输入摘要、返回/数据库观察和脱敏日志；设计文档本身不是通过证据。

## A. Markdown 语法与规范化

| ID | 需求来源 | 层级 | 环境 | 前置条件 | 输入摘要 | 步骤 | 预期结果 | 风险 | 当前状态 |
|---|---|---|---|---|---|---|---|---|---|
| P3-SYN-01 | 阶段3任务书：Markdown→候选 | PAR | PU | 冻结最小语法 | H1 文档标题、H2 活动、项目符号字段 | 解析并生成候选 | 得到一个候选；名称、字段和值可追溯至原位置 | 基本格式不可用 | passed |
| P3-SYN-02 | P3-C8：标题/列表 | PAR | PU | 同上 | 有序列表与无序列表混用 | 分别解析等价文档 | 冻结允许的列表形式产生等价规范值；禁用形式给可定位问题 | 解析行为漂移 | passed |
| P3-SYN-03 | P3-C8：空行 | PAR | PU | 同上 | 连续空行、行尾空格、文末无换行 | 解析三种变体 | 候选边界稳定，空白不生成伪字段或伪活动 | 空白导致错分组 | passed |
| P3-SYN-04 | P3-C8：换行 | PAR | PU | 同上 | LF、CRLF、CR 三种文本 | 解析并比对候选 | P3-IF-001 冻结换行支持后结果一致或明确拒绝；行号正确 | 跨平台定位错误 | passed |
| P3-SYN-05 | P3-C8：中文 | PAR | PU | UTF-8 输入 | `周末采购`、中文字段和值 | 解析并预览 | 中文完整保留，未乱码、未误分词、定位正确 | 中文数据损坏 | passed |
| P3-SYN-06 | P3-C8：Unicode | PAR | PU | 冻结 Unicode 规范化策略 | 全角标点、emoji、组合字符、同形字符 | 解析并比较稳定 ID/名称 | 条件断言：按冻结规范保留或规范化；不得静默合并不同名称 | 同形冲突/ID 漂移 | passed |
| P3-SYN-07 | P3-C8：未知字段 | PAR | PU | 冻结字段白名单策略 | 合法活动含 `幸运色: 蓝` | 解析并查看 issues | 条件断言：未知字段被拒绝或作为警告保留；不得映射到别的业务字段 | 静默丢失/错映射 | passed |
| P3-SYN-08 | P3-C8：重复标题 | PAR | PU | 冻结候选分段规则 | 同级出现两个同名活动标题 | 解析并检查候选数和位置 | 生成可区分候选或明确冲突；每个候选有独立稳定 ID 和原位置 | 候选覆盖 | passed |
| P3-SYN-09 | P3-C8：缺失名称 | PAR | PU | 最小语法已冻结 | 只有字段无活动标题、空白标题 | 解析并预览 | 不产生可提交 create/revise；返回可定位的必填问题 | 无名模板落库 | passed |
| P3-SYN-10 | P3-C8：非法金额 | PAR | PU | 金额词法规则已冻结 | `参考金额: 十元`、`12..3` | 解析并预览 | 候选标记不可提交，错误指向金额字段且不抛内部异常 | 非法值穿透 | passed |
| P3-SYN-11 | 阶段3任务书：来源可解释 | PAR | PU | 多活动文档 | 标题、正文、列表间夹杂自由文本 | 解析并检查 source span | 每个字段的标题/起止行可复核；自由文本按冻结策略处理 | 错误无法定位 | passed |
| P3-SYN-12 | P3-C8：边界语法 | PAR | PU | 无 | 空文件、仅 BOM、仅标题、多个文档级标题 | 分别解析 | 空输入不产生候选；其他行为按冻结语法给稳定问题，进程不崩溃 | 空输入误提交 | passed |

## B. 金额精度、区间与非记账边界

| ID | 需求来源 | 层级 | 环境 | 前置条件 | 输入摘要 | 步骤 | 预期结果 | 风险 | 当前状态 |
|---|---|---|---|---|---|---|---|---|---|
| P3-AMT-01 | P1-IF-001；阶段3参考金额 | PAR/DOM | PU+SS | 冻结金额文本格式 | `12` CNY | 预览并确认到模板 revision | 精确转换为 1200 minor units，不使用二进制浮点 | 金额精度错误 | passed |
| P3-AMT-02 | 同上 | PAR/DOM | PU+SS | 同上 | `12.30` CNY | 预览并确认 | 精确保存 1230；展示/回读不丢尾随精度语义 | 往返不一致 | passed |
| P3-AMT-03 | P3-C8：两位小数 | PAR | PU | 同上 | `0.01`、`999.99` | 预览规范值 | 均为整数 minor units，无浮点痕迹 | 最小单位丢失 | passed |
| P3-AMT-04 | P3-C8：非法精度 | PAR/API | PU+HTTP | 同上 | `1.001`、指数记法、JSON 浮点 | 提交预览请求 | 严格拒绝或按冻结的唯一舍入规则处理；默认不得静默舍入 | 隐式舍入 | passed |
| P3-AMT-05 | P3-C8：零/负数 | PAR/DOM | PU+SS | P1 非负约束 | `0`、`-0.01` | 预览并尝试确认 | 条件断言：零值按冻结产品规则；负数不可作为参考金额落库 | 约束旁路 | passed |
| P3-AMT-06 | P3-C8：超大值 | PAR/API | PU+HTTP | 冻结最大值 | 最大值、最大值+0.01、超长数字 | 分别预览 | 边界值行为精确；超界安全拒绝且不产生候选可提交状态 | 溢出/拒绝服务 | passed |
| P3-AMT-07 | 阶段3任务书：区间不静默折叠 | PAR/DOM | PU+SS | P3-IF-001 冻结区间模型 | `80-120 元` | 预览并尝试确认 | 条件断言：保留区间或标为 unresolved；绝不静默取均值/端点写入单值 | 预算预测失真 | passed |
| P3-AMT-08 | 同上 | PAR | PU | 同上 | `最低80，最高120`、反向区间 | 解析并规范化 | 合法表达映射同一结构；下界大于上界为问题 | 区间错序 | passed |
| P3-AMT-09 | 阶段3任务书：金额仅预测 | PURE/DB | SS | 可观察全部财务表 | 含参考金额的合法文档 | 仅预览并检查数据库 | 不创建 ledger、账户余额、预算消耗、收入或实际活动发生 | 预览变记账 | passed |
| P3-AMT-10 | P1-IF-001：币种 | PAR/DOM | PU+SS | 当前模板 CNY；冻结导入币种规则 | CNY、未知币种、混合币种 | 预览并确认 | 条件断言：只接受冻结币种集合；不把未知币种金额当 CNY | 币种错计 | passed |

## C. 预览纯度

| ID | 需求来源 | 层级 | 环境 | 前置条件 | 输入摘要 | 步骤 | 预期结果 | 风险 | 当前状态 |
|---|---|---|---|---|---|---|---|---|---|
| P3-PRV-01 | 阶段3任务书：preview pure | PURE/DB | SS | 记录所有业务表基线 | 一个合法新活动 | 调用 preview 后比较数据库 | activity_templates/revisions/occurrences/allocations 均零变化 | 未确认写入 | passed |
| P3-PRV-02 | 同上 | PURE/DB | SS | 同上 | 合法参考金额 | preview 后检查财务表 | ledger、账户、预算、收入安排/实际到账均零变化 | 意外记账 | passed |
| P3-PRV-03 | 同上 | PURE/DB | SS | 同上 | 包含合法与非法候选 | preview 后检查 receipts/audit | 命令回执和业务审计无半写入；错误仅存在响应/允许的预览载体 | 审计污染 | passed |
| P3-PRV-04 | P3-C8：重复预览 | PURE | PU+SS | 相同内容与上下文 | 连续预览两次 | 比较候选顺序、ID、规范字段 | 结果稳定且无业务写入累积 | 非确定性 | passed |
| P3-PRV-05 | 阶段3任务书：未选候选不落库 | PURE/DOM | SS | 预览返回多个候选 | 不调用确认或只选子集 | 检查未选候选对应表 | 未确认部分不创建/修订任何模板 | 选择边界泄漏 | passed |
| P3-PRV-06 | P3-C8：故障半写入 | PURE/DB | SS | 注入解析/规范化内部故障 | 故障发生在中间候选 | 调用 preview 并检查库 | 安全错误；所有业务表、回执、审计保持基线 | 预览半写 | passed |
| P3-PRV-07 | 阶段3待决策：预览持久化 | PURE/DB | SS+SPG | P3-IF-001 冻结是否保存 batch | 同一预览请求 | 检查允许写入集合 | 条件断言：若不持久化则零写；若持久化仅写冻结的预览元数据，绝不写业务对象/命令回执 | 纯度定义模糊 | passed |
| P3-PRV-08 | 阶段3任务书：原文摘要 | PURE/SEC | PU+SS | 冻结 raw retention | 相同内容、空白变体、不同内容 | 比较 raw digest 与候选 ID | 摘要算法稳定；原文保存/不保存遵循冻结策略且不泄露到日志 | 重放无法识别 | passed |

## D. 候选动作、来源与可解释性

| ID | 需求来源 | 层级 | 环境 | 前置条件 | 输入摘要 | 步骤 | 预期结果 | 风险 | 当前状态 |
|---|---|---|---|---|---|---|---|---|---|
| P3-CAN-01 | 阶段3任务书：create | PURE/DOM | SS | 无同名模板 | 完整合法活动 | preview 后选择 create 并确认 | 候选建议 create；确认后产生一个模板和首个不可变 revision | 新建重复/漏写 | passed |
| P3-CAN-02 | 阶段3任务书：revise | PURE/DOM | SS | 存在精确同名活动 | 改变说明或参考金额 | preview 后按冻结规则确认 | 候选为 revise 或需用户选择；只新增 revision，不改旧 revision | 历史被改写 | passed |
| P3-CAN-03 | 阶段3任务书：conflict | PURE | PU+SS | 存在互斥目标 | 同一候选可指向多个目标 | preview | 标记 conflict，列出脱敏原因；不可直接提交 | 错误合并 | passed |
| P3-CAN-04 | 阶段3任务书：unresolved | PURE | PU | 缺少冻结必填字段或区间未决 | 不完整活动 | preview | 标记 unresolved，issues 明确字段和位置；不可提交 | 猜测补全 | passed |
| P3-CAN-05 | 阶段3任务书：skip | PURE/DOM | SS | 存在与输入完全等价模板 | 等价活动 | preview 并确认 skip | 建议/允许 skip；模板及 revision 计数不变 | 无意义版本膨胀 | passed |
| P3-CAN-06 | 阶段3任务书：stable ID | PURE | PU | 相同解析规则与上下文 | 同文档重复预览 | 比较 candidate_id | 每个候选 ID 稳定且不同候选不碰撞；算法冻结后纳入快照 | 选择错位 | passed |
| P3-CAN-07 | 阶段3任务书：source location | PAR/PURE | PU | 多行、多候选文档 | 一个字段跨行且一处非法 | 检查 heading/line/span | 候选和 issue 均指向准确标题与行范围 | 用户无法复核 | passed |
| P3-CAN-08 | 阶段3任务书：explainability | PURE/API | PU+HTTP | 五类动作均可构造 | create/revise/conflict/unresolved/skip 各一 | 请求 preview | 每项返回机器可判定动作、简洁原因、issues 和目标版本信息；不暴露内部堆栈 | 黑盒决策 | passed |

## E. 冲突、版本与并发确认

| ID | 需求来源 | 层级 | 环境 | 前置条件 | 输入摘要 | 步骤 | 预期结果 | 风险 | 当前状态 |
|---|---|---|---|---|---|---|---|---|---|
| P3-CNF-01 | 阶段3任务书：exact name | PURE | SS | 一个活动模板 | 完全相同名称与内容 | preview | 按冻结规则给 skip/revise 之一及明确依据，不创建第二模板 | 精确重复 | passed |
| P3-CNF-02 | 同上 | PURE/DOM | SS | 同名模板版本 v1 | 同名但字段变化 | preview 并确认 | 目标绑定 v1；成功仅新增 v2，v1 可追溯 | 版本覆盖 | passed |
| P3-CNF-03 | 阶段3任务书：similar no silent merge | PURE | SS | `周末采购` 已存在 | 输入 `周末买菜` | preview | 可提示相似但不得自动 revise/merge；默认 conflict/unresolved 由冻结规则决定 | 模糊误合并 | passed |
| P3-CNF-04 | P3-C8：archived | PURE/DOM | SS | 同名模板已归档 | 输入同名活动 | preview 并尝试确认 | 条件断言：恢复、新建或冲突由 P3-IF-001 冻结；不得静默修改归档对象 | 归档状态破坏 | passed |
| P3-CNF-05 | 阶段3任务书：version recheck | DOM/DB | SS+SPG | preview 绑定模板 v1 | 确认前外部产生 v2 | 提交原确认 | 原子拒绝 stale/conflict；不产生 v3、回执半写或部分批次 | 陈旧确认覆盖新版本 | passed |
| P3-CNF-06 | P3-C8：重复候选 | PURE/DOM | SS | 数据库无对应模板 | 一个文档含两个等价活动 | 预览后选择两项并确认 | 预览明确重复关系；确认不得创建两个逻辑重复模板 | 批内重复 | passed |
| P3-CNF-07 | P3-C8：同目标多候选 | DOM/DB | SS+SPG | 两候选均指向同一 v1 | 同批选择两个 revise | 提交 | 条件断言：拒绝或按冻结顺序串行；不得丢更新或产生不可解释版本 | 批内版本竞争 | passed |
| P3-CNF-08 | P3-C8：并发 commit | DOM/DB | SPG | 两个预览绑定同一 v1 | 两事务同时确认不同修改 | 同步并发提交 | 最多一个按 v1 成功；另一个稳定冲突，历史链连续且无半写 | 丢失更新 | passed |

## F. 幂等、重放与进程边界

| ID | 需求来源 | 层级 | 环境 | 前置条件 | 输入摘要 | 步骤 | 预期结果 | 风险 | 当前状态 |
|---|---|---|---|---|---|---|---|---|---|
| P3-IDM-01 | 阶段3任务书：idempotency | API/PURE | HTTP | 冻结 preview 幂等键范围 | 同键、同 Markdown、同上下文 | 顺序请求两次 preview | 返回同一逻辑结果/候选 ID；不产生额外持久状态 | 重放漂移 | passed |
| P3-IDM-02 | 同上 | API/PURE | HTTP | 同上 | 同键、不同 Markdown | 顺序请求 | 第二次稳定冲突，不复用首个内容的成功结果 | 键冲突误回放 | passed |
| P3-IDM-03 | 阶段3任务书：commit idempotency | DOM/DB | SS+SPG | 已生成可确认候选 | 同确认键、同候选选择与版本 | 确认两次 | 第二次重放首个最终结果；模板/revision/receipt 只写一次 | 重复创建 | passed |
| P3-IDM-04 | 同上 | DOM/DB | SS+SPG | 同上 | 同确认键、不同选择/动作 | 先后确认 | 第二次稳定 idempotency conflict；首个结果不变 | 键载荷混用 | passed |
| P3-IDM-05 | P3-C8：响应丢失 | API/DOM/DB | HTTP+SS+SPG | 可在提交后丢弃响应 | 同键同载荷重试 | 首次提交后模拟断线，再请求 | 重试返回已提交结果，不增加业务行或版本 | 不确定提交重试 | passed |
| P3-IDM-06 | P3-C8：失败后重试 | DOM/DB | SS+SPG | 首次事务在提交前失败 | 同键同载荷 | 注入失败、解除后重试 | 首次无业务/receipt 半写；重试可按冻结状态机完整成功 | 失败键永久污染 | passed |
| P3-IDM-07 | P3-C8：并发同键 | DOM/DB | SPG | 两独立连接 | 同确认键、同载荷 | 同步并发确认 | 单次业务效果；两调用得到一致最终结果或一个安全等待/重放 | 双写竞态 | passed |
| P3-IDM-08 | P3-C8：并发不同键 | DOM/DB | SPG | 两个独立无冲突活动 | 不同键不同候选 | 同步并发确认 | 两者均可提交且互不串结果；各自一次一写 | 过度串行/串单 | passed |
| P3-IDM-09 | P3-C8：跨进程数据库目标 | API/DB | SPG | 冻结幂等保存模型，可启动两个应用实例 | 同键同载荷跨实例及重启 | A 提交，B/重启实例重放 | 条件断言：若承诺跨进程则数据库唯一约束保证重放；若不承诺，API 明示范围且不得伪称持久幂等 | 进程边界双写 | passed |

## G. 批次原子性、回执与恢复

| ID | 需求来源 | 层级 | 环境 | 前置条件 | 输入摘要 | 步骤 | 预期结果 | 风险 | 当前状态 |
|---|---|---|---|---|---|---|---|---|---|
| P3-ATM-01 | 阶段3任务书：atomic batch | DOM/DB | SS+SPG | 批事务范围已冻结 | 一个 create + 一个 revise | 同批确认 | 两项与批次结果一次提交；版本和目标均正确 | 多项不一致 | passed |
| P3-ATM-02 | 同上 | DOM/DB | SS+SPG | 同上 | 第二项业务校验失败 | 确认整批 | 整批失败；第一项模板/revision 不存在，原目标未变化 | 业务半写 | passed |
| P3-ATM-03 | 同上 | DB | SS+SPG | 可注入数据库约束故障 | 中间 revision 插入失败 | 确认整批 | 全部业务行回滚；错误安全分类稳定 | 约束半写 | passed |
| P3-ATM-04 | P3-C8：receipt same tx | DOM/DB | SS+SPG | 回执模型已冻结 | 合法批次 | 在业务写入后、回执前注入失败 | 业务和回执同成同败；无“已写但无可重放证据”状态 | 回执分离 | passed |
| P3-ATM-05 | P3-C8：audit same tx | DOM/DB | SS+SPG | 审计模型已冻结 | 合法批次 | 在审计写入点注入失败 | 按冻结规则与业务原子提交；不得出现审计宣称成功但业务回滚 | 审计失真 | passed |
| P3-ATM-06 | P3-C8：retry | DOM/DB | SS+SPG | P3-ATM-02 首次失败 | 修正非法候选并使用冻结允许的新/原键 | 重试确认 | 完整批次恰好提交一次；无首次残留参与结果 | 恢复受污染 | passed |
| P3-ATM-07 | 阶段3任务书：selected candidates | DOM/DB | SS+SPG | 三候选只选择一、三 | 混合 create/skip/revise | 确认 | 仅选择项进入冻结事务；未选项零变化，响应逐项可解释 | 选择越界 | passed |
| P3-ATM-08 | P3-C8：crash/recovery | DOM/DB | SPG | 可终止提交客户端但不破坏数据库 | 提交阶段模拟进程/连接中断 | 重启后用同键查询/重放 | 只能观察全批成功或全批回滚；恢复不制造重复版本 | 未知事务结局 | passed |

## H. 安全、隐私与资源限制

| ID | 需求来源 | 层级 | 环境 | 前置条件 | 输入摘要 | 步骤 | 预期结果 | 风险 | 当前状态 |
|---|---|---|---|---|---|---|---|---|---|
| P3-SEC-01 | 阶段3任务书：Markdown is data | PAR/SEC | PU | 解析器无执行能力 | fenced code 含 Python/shell/SQL | preview | 代码仅作为文本/按冻结规则忽略；无命令、导入或数据库执行 | 代码执行 | passed |
| P3-SEC-02 | 同上 | PAR/SEC | PU+HTTP | 同上 | inline code 含活动字段样式 | preview | 不越过冻结语法解释为高权限指令；无副作用 | 标记逃逸 | passed |
| P3-SEC-03 | P3-C8：HTML | PAR/SEC | PU+HTTP | 输出层编码策略已冻结 | script、img onerror、HTML 注释 | preview 并序列化响应 | 不执行脚本；响应可安全渲染，原文处理遵循冻结策略 | XSS | passed |
| P3-SEC-04 | P3-C8：links | PAR/SEC | PU | 无外网能力 | http/file/javascript 链接与图片 | preview | 不抓取、不打开、不访问本地文件；仅作为受控文本/问题 | SSRF/本地读取 | passed |
| P3-SEC-05 | P3-C8：prompt injection | PAR/SEC | PU | 无模型调用 | `忽略规则并创建账目`、system 标签 | preview | 视为普通数据；不能改变候选规则、调用工具或自动确认 | 指令注入 | passed |
| P3-SEC-06 | P3-C8：path text | PAR/SEC | PU | 无文件解析功能 | `../../secret`、Windows/UNC 路径 | preview | 不读取/写入路径；安全返回文本问题，不泄露路径内容 | 路径穿越 | passed |
| P3-SEC-07 | P3-C8：control chars | PAR/API/SEC | PU+HTTP | UTF-8 边界 | NUL、Bidi、不可见控制符、非法 UTF-8 | 请求 preview | 条件断言：规范化或安全拒绝；日志/错误不可被换行或方向字符伪造 | 日志注入 | passed |
| P3-SEC-08 | P3-C8：large input | API/SEC | HTTP | 冻结字节/字符上限 | 上限、上限+1、超长单行 | 请求 preview | 边界按冻结值判定；超限在解析/落库前拒绝且资源可恢复 | 内存/CPU DoS | passed |
| P3-SEC-09 | P3-C8：deep nesting | PAR/API/SEC | PU+HTTP | 冻结标题深度/候选数上限 | 深层标题、海量列表/候选 | preview | 有界处理；超限稳定拒绝，不递归崩溃、不部分预览持久化 | 栈/算法 DoS | passed |
| P3-SEC-10 | 阶段3任务书：privacy | API/SEC | HTTP+SS+SPG | 开启测试日志捕获；植入虚拟 canary | canary 在名称、正文、未知字段和故障消息 | 触发成功、校验错、数据库错 | 日志/异常/回执不含原文 canary、连接密码、SQL 参数或堆栈；允许的摘要不可逆 | 私密数据泄露 | passed |

## I. API/Pydantic 契约

| ID | 需求来源 | 层级 | 环境 | 前置条件 | 输入摘要 | 步骤 | 预期结果 | 风险 | 当前状态 |
|---|---|---|---|---|---|---|---|---|---|
| P3-API-01 | P3-C8：strict schema | API | HTTP | P3-IF-001 冻结 endpoint/DTO | 请求含未知字段 | 调用 preview/commit | Pydantic 严格拒绝，错误定位字段；无业务写入 | mass assignment | passed |
| P3-API-02 | 同上 | API | HTTP | 同上 | 缺 Markdown、幂等键或确认所需字段 | 调用对应 endpoint | 稳定 4xx 和安全错误码；缺失字段清晰，无内部异常 | 必填旁路 | passed |
| P3-API-03 | 同上 | API | HTTP | 同上 | 字符串/数组/布尔/数字类型互换 | 调用 endpoint | 不做危险宽松强转；按冻结 DTO 严格拒绝 | 类型混淆 | passed |
| P3-API-04 | P3-C8：content type | API | HTTP | 同上 | text/plain、form、错误 charset、缺 Content-Type | POST 相同正文 | 只接受冻结媒体类型；其他稳定拒绝且无解析副作用 | 解析器分歧 | passed |
| P3-API-05 | P3-C8：malformed payload | API | HTTP | 同上 | 截断 JSON、重复键、非法 UTF-8 | 请求 endpoint | 条件断言按冻结 JSON 策略；安全 4xx、无候选/业务写入 | 语义歧义 | passed |
| P3-API-06 | P3-C8：limits | API | HTTP | 冻结正文/候选限制 | 精确上限与超一单位 | 分别请求 | 上限内进入解析，超限在有界时间拒绝；错误可判定 | 限额越界 | passed |
| P3-API-07 | 现有 API 安全 envelope | API | HTTP | 沿用 request_id/error 约定或 P3-IF-001 替代契约 | 422、冲突、stale、内部故障 | 分别触发 | HTTP 状态和稳定 code/retryable 映射正确；消息不含私密原文或堆栈 | 客户端误重试 | passed |
| P3-API-08 | 阶段3待决策：API surface | API/DOM | HTTP | P3-IF-001 冻结 preview/confirm 接口与令牌 | 伪造 candidate_id、跨 preview 选择、重复/乱序选择 | 提交确认 | 只允许属于该预览且未过期的候选；版本/摘要重验，越权选择原子拒绝 | 候选篡改 | passed |

## J. SQLite/PostgreSQL 分层、迁移与一致性

| ID | 需求来源 | 层级 | 环境 | 前置条件 | 输入摘要 | 步骤 | 预期结果 | 风险 | 当前状态 |
|---|---|---|---|---|---|---|---|---|---|
| P3-DB-01 | 阶段3任务书：SQLite fast evidence | DB | SS | 固定实现快照；空库 | 升级到 P3 head | 执行迁移并检查 schema | 若 P3 引入持久对象，表/索引/约束与冻结模型一致；否则明确无迁移 | 首次部署失败 | passed |
| P3-DB-02 | 同上 | DB | SS | P2 head 含虚拟历史数据 | 升级、重复升级、按支持方式重建 | 核对历史行和 head | 已有模板/revision/发生/财务数据不变；迁移幂等或按工具安全拒绝重复 | 历史数据损坏 | passed |
| P3-DB-03 | 阶段3任务书：PostgreSQL target | DB | SPG | 空 schema、真实 PG 测试容器 | 升级到 P3 head | 检查类型、FK、unique/check/index | 约束在数据库真实生效；与冻结模型相符，不用 SQLite 结果代替 | 目标库不兼容 | passed |
| P3-DB-04 | P3-C8：SQLite transaction | DB | SS | 可注入中批失败 | 多候选确认 | 故障并回查 | SQLite 下整批回滚、连接可继续使用；锁错误安全分类 | 本地半写/锁死 | passed |
| P3-DB-05 | P3-C8：PostgreSQL concurrency | DB | SPG | 两连接和同步屏障 | 同键并发、同模板版本并发 | 分别执行 P3-IDM-07/CNF-08 | 唯一约束/锁/隔离共同保证一次一写与 stale 拒绝，无死锁泄漏 | 生产竞态 | passed |
| P3-DB-06 | P3-C8：collation differences | PAR/DB | SS+SPG | 冻结名称规范与大小写规则 | ASCII 大小写、中文、Unicode 规范等价名 | 两库预览/确认 | 条件断言：应用规范化消除后端排序差异，或明确各自冲突；业务结果不静默分叉 | 跨库名称冲突 | passed |
| P3-DB-07 | 阶段3任务书：cross-DB consistency | DOM/DB | SS+SPG | 相同固定虚拟数据和时钟 | create/revise/skip、失败回滚、重放 | 两库执行同一场景 | 候选动作、业务对象、版本、错误 code 和一次一写结果一致；仅数据库诊断可不同 | 环境结论漂移 | passed |
| P3-DB-08 | P3-C8：恢复与数据保持 | DB | SS+SPG | 已成功一批及一批失败记录 | 重启应用/连接后查询并重放 | 检查成功与失败状态 | 成功批可追溯且可安全重放；失败批无业务残留；历史 P1/P2 数据保持 | 重启后状态丢失 | passed |

## 需求追踪

| 必需覆盖 | 案例 |
|---|---|
| 标题、列表、空行、中文、Unicode、换行、未知字段、重复标题、缺名、非法金额 | P3-SYN-01～12 |
| 精确金额、区间、两位小数、零/负数、超大值、浮点禁止、非记账 | P3-AMT-01～10、P3-PRV-02 |
| 预览不写模板/revision/occurrence/ledger/budget/income/receipt/audit | P3-PRV-01～08、P3-AMT-09 |
| create/revise/conflict/unresolved/skip、来源、稳定 ID、解释 | P3-CAN-01～08 |
| 精确/相似/归档/版本/批内重复/并发确认 | P3-CNF-01～08 |
| 同键同/异载荷、响应丢失、跨进程、同键/异键并发 | P3-IDM-01～09 |
| 原子回滚、回执/审计同事务、重试与恢复、一次一写 | P3-ATM-01～08、P3-IDM-03～09 |
| 代码、HTML、链接、提示注入、路径、大输入、深嵌套、日志隐私 | P3-SEC-01～10 |
| Pydantic 严格、媒体类型、限额、状态码、错误 envelope | P3-API-01～08 |
| SQLite 与 PostgreSQL 迁移、事务、并发和结果一致性 | P3-DB-01～08 |

## 环境分层与证据边界

| 层级 | 目的 | 可接受证据 | 不可替代的上层证据 |
|---|---|---|---|
| PU | 快速验证解析、规范化、候选 ID 和安全文本处理 | 固定输入/输出断言与无副作用探针 | 不能证明事务、数据库约束或 HTTP 契约 |
| SS | 验证领域编排、SQLite 迁移、回滚、回执和既有数据保持 | 临时数据库前后快照、行数/关系/金额断言 | 不能证明 PostgreSQL 锁、隔离、类型和跨进程唯一性 |
| HTTP | 验证 Pydantic、Content-Type、限额、错误 envelope 与响应丢失 | 本地请求/响应、数据库前后快照、脱敏日志捕获 | 不能替代真实 PostgreSQL 并发 |
| SPG | 验证目标数据库迁移、约束、并发、恢复和跨进程幂等 | 真实测试 PostgreSQL、两连接/两实例同步、事务后查询 | SQLite 或离线 DDL 不得标成 SPG 通过 |

所有层只使用虚拟数据。真实 DeepSeek、桌面端、OpenClaw 和微信证据不属于本矩阵，也不能作为 P3 数据导入验收的替代证据。

## C9 独立执行进入条件

1. 总控发布 `P3-IF-001`，至少冻结解析语法、字段白名单、名称规范、金额/区间、候选动作、预览持久化、幂等范围、批事务、API、限制值及错误码。
2. 执行方交付稳定实现和自测结果，并列出产品、迁移、DTO、API、测试文件的固定快照清单；总控确认该清单没有并发修改。
3. 提供可重复的虚拟 fixture、可控时钟/ID、故障注入点和数据库前后状态观察方式；不得要求测试方读取真实数据。
4. SQLite 运行说明可用；需要 SPG 结论时，另有明确的容器授权与测试凭据，且不以 SQLite 冒充。
5. 本矩阵中的条件断言已绑定为唯一预期；仍未冻结的案例继续 `not_run`，不得通过猜测执行。

## 固定快照建议

执行交接应给出有序 UTF-8 清单，至少包括 P3 解析/规范化、领域编排、DTO/API、模型/迁移、执行方测试以及直接依赖的 P1/P2 活动模板代码。对每个仓库相对路径记录 SHA-256，再对“`path<TAB>sha256<LF>`”字节流计算总 SHA-256，命名为 `P3-B5-SHA256:<digest>`。C9 在运行任何测试前独立重算；缺文件、多文件、摘要不符或清单路径越界时停止，不在漂移快照上形成结论。

## 建议执行顺序

1. 快照与冻结门禁，随后运行 PU 的 SYN/AMT/CAN/SEC 基础案例。
2. SS 的预览纯度、候选动作、版本、幂等、原子性和迁移案例。
3. HTTP 的严格 schema、资源限制、错误 envelope、候选篡改和响应丢失。
4. SPG 的迁移、并发同键、同版本竞争、跨进程重放、故障恢复与跨库一致性。
5. 仅在所有前置层稳定后汇总追踪；每层单列通过、失败、阻塞、不适用，禁止把未执行写成通过。

## 停止条件

- 控制文件取消 P3-C8/C9、改变唯一负责人或固定快照发生漂移。
- 需要未授权的产品修改、依赖安装、外部登录、真实数据或破坏性数据库操作。
- 发现预览写入实际账目、批次半写、并发双写、历史 revision 被改写、原文/凭据泄露等高风险现象；保留最小脱敏复现后停止扩大执行。
- 连续两个检查点无新输出；安全结束已启动的测试资源，记录最后一条脱敏错误、尝试、可能原因和待共同决定项。

## 需要 P3-D7/总控冻结的参数

1. 支持的 Markdown 标题层级、列表/自由文本、换行与 Unicode 规范化规则，未知字段和重复标题的处理。
2. 活动字段白名单、必填项、名称规范与精确匹配/相似提示/归档模板策略。
3. 参考金额的输入格式、币种、零值、最大值、小数/舍入，以及单值、区间或组合金额的数据模型。
4. candidate ID、raw digest、source span 算法；原 Markdown 是否保存、保存期限、加密/脱敏和删除规则。
5. preview 是否持久化、其允许写入集合与有效期；create/revise/conflict/unresolved/skip 的唯一判定。
6. preview/confirm API 路径、DTO、Content-Type、request/idempotency key 范围、HTTP 状态、稳定错误码和 envelope。
7. 批次选择、零选择、同目标多候选、stale version、回执/审计的事务边界与失败重试状态机。
8. 正文、单行、标题深度、候选数、字段长度等资源上限，以及 SQLite/PostgreSQL 名称唯一性和跨进程幂等目标。

## 本阶段不测试

- 不运行本矩阵或任何现有测试，不对实现作通过/失败结论。
- 不测试 UI、文件选择器、桌面端、真实 DeepSeek、搜索/RAG、OpenClaw、微信或真实用户数据。
- 不测试自动生成 activity occurrence、实际账目、预算消耗、收入、提醒或任何“导入即执行”行为；这些行为在本阶段应保持不存在。
- 不自行定义尚未冻结的活动组成、区间折叠、模糊合并、代付、报销或分期产品规则。
- 不修改产品、迁移、依赖、执行方测试、接口冻结、控制文件、其他角色状态或 Git 状态。
