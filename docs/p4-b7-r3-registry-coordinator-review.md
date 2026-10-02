# R3-REGISTRY 总控交付核对与 C12-R2 进入条件

- 日期：2026-10-02，Asia/Shanghai。
- 角色：头脑风暴总控，只读证据和定向差异核对，未运行产品或测试。
- 输入：[R3运行说明](b7-r3-registry-running.md)、源/外部清单、原始开发/静态/真实EXE JSON；[R3任务](coordination/prompts/p4-b7-r3-registry-executor.md)。
- 决定：**接受R3为独立复验输入**。R3仍review/finished，REGISTRY-001没有独立关闭，P4-B未complete。

## 代码与范围

`apps/desktop/src/modules/registry.ts`唯一产品差异：`setting:${item.moduleId}:${setting.key}`改为`setting:${setting.key}`。错误仍为desktop_registry_conflict、seen仍每次调用局部、任一冲突整次抛出；其他身份、canonical Profile/Host intersection、schema和返回合同未变化。

开发测试保留原18项，新增8项跨模块双顺序/同异schema、同模块重复、不同键合法与输入不变/失败后合法编译。独立材料完全不变，没有修改或运行测试方用例。

## 本轮实际复算与原始证据

| 对象 | 核对结果 |
| --- | --- |
| R3最终source清单 | 324/324 matched，0 missing/mismatch |
| 5文件repository-delivery | 5/5 matched |
| 脱敏evidence-manifest | 52/52 matched，含长度/内容摘要 |
| 新package完整out | 140/140 matched，含长度/内容摘要 |
| 323起点 | 320 unchanged，3授权变化，0 missing/越界 |
| 开发原始JSON | 修复前4 failed/22未选；后定向28 passed，完整98 passed/0 failed/0 skip |
| package结果 | 1/1、exit0、7509ms；未追加执行 |
| 静态结果 | 7/7、67 Python资源一致，production fuses、污染/staging收口通过 |
| 新EXE原始结果 | 1/1、19/19 gates，recover1次、34535ms，natural exit0，无timeout/forced cleanup |
| 运行收口原始记录 | owned进程0、监听0、窗口0；Tray仅按产品树结束推断，不当作真实菜单验收 |

三项起点变化仅registry.ts、registry.test.ts、executor.md。outbox、main、preload、contribution、依赖/lock、构建配置、Python和全部独立材料保持。旧R2完整物理依赖和profile不重复读取正文；执行方不变性证据已冻结，本轮只复算其脱敏清单/证据和关键产物，未重做全量依赖扫描。

source清单SHA-256：`454042cd8fe580126dc083930d4a23553f4172487bbd47c5fb0c6832e15154ad`。

外部delivery：`bf65c30ea23fed4f44dd08e4560458d34bc274d0e76a4ceb78f263a9d3079e94`；evidence：`4d5afa06793e446c4b7585196f9655478074547f6c9b48e0e7fb1c7eda253438`；out：`6bc7042f47c1637deb58bdfe26550150cb80d77071eb9b9353d576b5d8ee8d34`。

## 新受验包

目录：`C:\MarisRegistryR3\R3-20261002-111556\workspace\apps\desktop\out\Maris-win32-x64`。

| 文件 | bytes | SHA-256 |
| --- | --- | --- |
| Maris.exe | 246032896 | `1df694c0ca39818d1b2af7aad09eefa13383af186a8d0638d96a13882d604a94` |
| resources/app.asar | 759792 | `64f84ddde164c4dea81ab3fcb6933728eda5acf3cfe4917828fe0f4f6dc3e161` |
| workspace lock | 固定 | `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |

新asar main/renderer中setting token与新源一致；token检查仅为来源证明，行为由开发回归和后续独立复验验证。

## 下一步

发布[C12-R2独立任务](coordination/prompts/p4-c12-r2-registry-windows-tester.md)：先原R1-SHELL-13不变断言一次，相关registry独立相邻边界；通过后继续原24项尚未执行Windows/公开行为。原C12/R1首次失败和通过证据保持不变，不重新设计矩阵。

原OUTBOX-001已独立关闭，且本次outbox/main未变，不重复42独立节点或完整98开发回归。SUP-06整项、真实老化原生提示、Tray/注销/开机启动/多屏等未获设备证据条件如实保留。未完整通过时不能把整项passed或P4-B complete。

总控不重复package/EXE；技术顾问和执行智能体停止。用户发送新Prompt后测试方登记接单，当前仍ready/waiting_user。保存本地未验收检查点，不推送远程；高保真前端/模型策略提醒门禁保持。
