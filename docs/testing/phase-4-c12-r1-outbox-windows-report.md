# P4-C12-R1 outbox 独立复验与 Windows Shell 验收报告

- 角色：用户启动的既有测试智能体，C12-R1 唯一负责人。
- 控制版本：`2026-10-01T23:37:56+08:00`；任务卡 `docs/coordination/prompts/p4-c12-r1-outbox-windows-tester.md`。
- 本轮日期：2026-10-01 接单、2026-10-02 交付；Asia/Shanghai。各运行时刻以分组 JSON/log 为准。
- 交付：**blocked / finished**。原 OUTBOX-001 复验通过，建议关闭；新 P1 REGISTRY-001 导致停止扩大测试。P4-B 未 complete，最终接受由总控决定。

## 结论和分层统计

原 `P4-C12-OUTBOX-001` 的不变失败断言已唯一一次通过：未确认删除的两条虚拟消息，在 30 天 + 1ms load→cleanup→reload 后仍为两条，原正文/digest/clientEventId 保留。新增持久化、确认边界与main接线全部通过，可建议总控关闭原 P1 的公开持久删除逻辑问题。真实Windows原生提示未验证，关闭原P1不等于整个SUP-06或P4-B通过。

继续原矩阵时发现 `P4-C12-R1-REGISTRY-001`（P1）：两个不同虚拟模块共享同一个setting key，compileRegistry仍同时接受。违反IF-003 §5“module、Profile、route、setting和appearance全局唯一”和任一冲突整体fail-closed，映射P4B-UI-04。按任务卡停止在Windows前，没有产品或辅助Electron启动。

| 类别 | 本轮实际结果 | 证据 / 限制 |
| --- | --- | --- |
| 原 PUB-11 不变断言 | 唯一一次 1 passed | original-node/result.json；同文件其他10节点由filter排除 |
| 原其他十项 | 唯一一次 10 passed | remaining-original/result.json；PUB-11由filter排除，未重复 |
| 新outbox独立边界 | 26 passed | outbox-independent/result.json；虚拟AES-GCM/时间/持久化/dialog |
| 可执行main独立接线 | 5 passed | main-independent/result.json；真正导入main，OS/FS/Host ports虚拟 |
| 第一阶段独立总计 | **42 passed、0 failed** | 全过后才进入第二阶段 |
| 其余Shell公开行为 | 17 passed、1 failed | matrix-independent/result.json，首次REGISTRY失败保留 |
| 独立合计 | **60个唯一executed：59 passed、1 failed** | node-index.json；不将filter未选项累计为额外skip，也不重复原节点 |
| 执行方兼容 | **27 passed、0 failed**，2 files，一次 | executor-compat/result.json；和独立分开统计，未再跑完整90 |
| 原24项P4-B整项 | **0 passed、1 failed、19 blocked、4 not_run** | SUP-06 failed→blocked，UI-04 blocked→failed；部分通过不整项passed |
| 真正产品EXE / 辅助Electron | **0/8 / 0/4** | 因新P1停止；不是环境或审批失败 |
| 老化原生设备提示 | **unverified** | 不声称UIA、真实safeStorage seed/read、保留/明确删除设备验收已执行 |
| 人工设备场景 | **not_run** | Tray/注销/启动项/多屏/透明和主题等缺口保留，未要求用户现在操作 |

没有harness/config错误，没有用例重跑或放宽断言，没有产品修复；两次原文件运行用不同filter且输出分目录，合计原11节点只执行一次。最后矩阵组18节点全部进入断言，只有R1-SHELL-13失败，`bail:1`限制后续扩大。注册缺陷不是工具解析失败。

## 输入、版本与不可变性

必读AGENTS/README/协调规则/control/tester/任务卡、R2 coordinator review/running、原C12 prompt/report/checklist/首次log/JSON、IF-003/004/005、单主人决定及矩阵已读取。IF-004/005对应覆盖条款生效，IF-003 §5全局唯一没有被撤销；不擅自将其改为每模块局部唯一。

新起点 `docs/coordination/snapshots/p4-c12-r1-start.sha256`：**296 entries、296 matched、0 mismatch、0 missing**，普通SHA-256为 `0922a37c45e42fb28be69a2405eac8b6de8b05ea9e22d22309a5a74be767bd15`；Git staged paths=0。旧C12起点和R2 source历史清单未重跑、修改或刷新。

新环境只读为 `C:\MarisOutboxR2\R2-20261001-155509`，使用其固定Node/已装Vitest5.0.2与普通node_modules；repo没有node_modules。plain新配置显式指向新依赖，所有测试output/cache在新 `evidence/r1/`。没有安装、联网audit、build、package、永久PATH/TUN/代理/安全软件/系统时钟修改。测试时间只用注入clock，main fixture新鲜条目用当前Date.now，无系统时间调整。

| 新受验文件（workspace 下） | 起终点固定SHA-256 |
| --- | --- |
| apps/desktop/out/Maris-win32-x64/Maris.exe | `8eb56f3f63b923471a9239e2a01f29a8111067a6093d8c9d118e62e1ccfb5c2a` |
| apps/desktop/out/Maris-win32-x64/resources/app.asar | `74225ea63dbc7201dc7f7f3299a099ac573f51680ef705536e560a9d9df6b6c7` |
| pnpm-lock.yaml | `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |

只读终点fuse wire v1前六项为 `48/49/48/48/49/49`，与输入冻结一致；EXE全文件起終摘要相同即证明包括fuse wire在内全部字节保持。未flip fuses或改production inspect。新artifact只读哈希与mmap解析，不执行EXE。

原八项独立交付均在新清单内并精确保持：原public-boundaries.test.ts、vitest.config.mjs、audit_inputs.py，以及原evidence五项。原首次JSON仍为10 passed/1 failed，原log仍保留2→0。原主报告和人工清单仅追加R1部分，既有字节作为prefix保持，不将首次失败改写为通过。旧R2/LOCALZIP profile/session/db/evidence/依赖/out没有写入或复用。

## 原 P1 复验与关闭建议

证据：`evidence/r1/original-node/run.log` 与 `result.json`，原test文件完全不变，只用新R1config和新依赖。命令：

```powershell
$env:C12_R1_PHASE='original-node'
& 'C:\MarisOutboxR2\R2-20261001-155509\tools\node\node.exe' 'C:\MarisOutboxR2\R2-20261001-155509\workspace\node_modules\vitest\vitest.mjs' run --config tests/independent/desktop/r1-vitest.config.mjs -t C12-PUB-11
```

实际安全输出：

```json
{"before":2,"after":2,"persisted":2,"statesBefore":["draft","queued"],"elapsedMilliseconds":2592000001,"userDeletionConsent":false,"actualIds":["virtual-event-1","virtual-event-2"],"expectedIds":["virtual-event-1","virtual-event-2"]}
```

新增R1-OB26节点提供独立相邻证据：三种非terminal状态在30天/+1ms/远超期限的load→两次cleanup→新对象reload保持全部字段；terminal恰好24h保留、+1ms清理；候选严格>30天且仅draft/queued；没有候选不提示，一次attach最多一次，默认/取消为保留且提示无正文/ID；取消/非明确返回、dialog rejection、stop/quitting/destroy/closed/ready前停止均保留；明确确认只删除仍为同对象、仍符合年龄/状态的旧候选，sending/新条目/更新/reload/同钟同状态/重复确认受保护。

prepare/state/cleanup/delete四种保存失败检查memory与原ciphertext均不变、新对象reload仍为旧状态，后续队列继续；pending write不提前发布，重复prepare/容量并发有界，20条上限明确拒绝，密文不含虚拟正文。独立fixture使用随机内存AES-GCM key，不冒充Windows DPAPI。

R1-MAIN5节点真正导入产品main并运行whenReady/ready-to-show/before-quit/closed：证明Host.start在dialog决定前开始，native adapter将正确main window和默认保留参数交给dialog，退出前ready及未决退出/销毁不会提交删除，明确确认仅删除老draft/queued。OS Electron、文件和Host ports为测试方自有mock，main/retention/outbox/schema/IPC注册为真实代码；不会通过主源码字符串搜索冒充执行测试。

**建议关闭原P1 `P4-C12-OUTBOX-001`，范围为公开持久化清理与确认边界。** 设备原生提示仍unverified；SUP-06仍blocked，恢复后实际提交一次/GET/UI和真实old draft确认还未取得独立现场证据。最终关闭由总控确认。

## 新缺陷 P4-C12-R1-REGISTRY-001

- 严重级别：**P1**，与P4B-UI-04冻结契约风险一致。跨模块设置键冲突没有fail-closed，破坏已冻结模块贡献注册边界；本轮不声称已有真实财务数据覆盖、权限利用或当前daily_finance故障。
- 依据：IF-003 §5第150行global setting uniqueness及第154行任一冲突不部分加载；原UI-04预期不兼容或冲突稳定失败。
- 最小复现节点：`r1-shell-boundaries.test.ts` 的R1-SHELL-13，约第128～141行。仅纯测试contribution，无产品模块创建、后端、网络或EXE。
- 前置：两个各自合法的模块virtual_alpha与virtual_beta，module/Profile/route ID/path/appearance全部不同、UI major=1、version=1.0.0。只把各自settings[0].key设为同一个 `virtual_shared_setting`，schemaVersion=1。
- 操作：公开compileRegistry([first, second])，仅调用一次，捕获返回/异常。
- 预期：稳定抛出desktop_registry_conflict并整体拒绝，不能同时接受冲突贡献。
- 实际：没有异常，返回两个模块。

```json
{"globalSettingKey":"virtual_shared_setting","moduleIds":["virtual_alpha","virtual_beta"],"accepted":true,"acceptedModules":2,"rejectionCode":null,"contract":"IF-003 section 5 global setting uniqueness"}
```

首次错误：`AssertionError: expected undefined to be 'desktop_registry_conflict'`。首次log/JSON位于 `evidence/r1/matrix-independent/`，没有失败后重跑。

根因定位：`apps/desktop/src/modules/registry.ts` 的compileRegistry使用 `setting:${item.moduleId}:${setting.key}` 作为seen key。同一设置键跨module得到两个不同seen值，因此违反“全局唯一”。同文件对module/profile/route ID/appearance的全局重复拒绝已独立通过，可排除fixture整体未生效；正常两个贡献compile也通过。没有自行修改技术合同为局部namespace规则。

影响：即使采用合法canonical贡献，编译注册也可接受冲突设置键；缺少跨模块全局约束，扩展性fail-closed门禁失败。是否未来引起实际路由/设置覆盖需另有实现与场景证据，本报告不外推。route path等未执行疑点不另报产品缺陷。

处理：按任务卡立即停止扩大测试，保留复现和未执行列表；不改产品，不运行Windows覆盖失败，不创建新返修任务。下一步由总控确认冻结要求与执行方返修范围、提供新固定快照后安排独立复验。

## 60 节点索引与运行记录

下列节点均为本轮实际executed；filter未选项不在表中。完整assertionResults包含参数化子节点。全部结果由首次JSON汇总，索引与统计可复算。

| 分组 | 节点 | 状态 |
| --- | --- | --- |
| original-node | C12-PUB-11 \| SUP-06 \| old unsubmitted drafts survive startup cleanup without deletion consent | passed |
| remaining-original | C12-PUB-01 \| SEC-05 partial \| unavailable crypto fails closed | passed |
| remaining-original | C12-PUB-02 \| SEC-05 partial \| encrypted roundtrip and safe corruption error | passed |
| remaining-original | C12-PUB-03 \| SEC-01/02 partial \| production preferences and CSP | passed |
| remaining-original | C12-PUB-04 \| SEC-04 partial \| wrong sender, frame, origin and parameters reject | passed |
| remaining-original | C12-PUB-05 \| UI-01 partial \| host intersection excludes incompatible contributions | passed |
| remaining-original | C12-PUB-06 \| SUP-06 partial \| concurrent identical draft retains one ID and one entry | passed |
| remaining-original | C12-PUB-07 \| SUP-06 partial \| encrypted reload retains payload and event ID | passed |
| remaining-original | C12-PUB-08 \| SUP-06 partial \| changing submitted body derives a new ID | passed |
| remaining-original | C12-PUB-09 \| SUP-06 partial \| capacity refusal preserves all 20 entries on reload | passed |
| remaining-original | C12-PUB-10 \| SUP-06 partial \| terminal retention boundary and fresh unsent entry | passed |
| outbox-independent | R1-OB-01/draft \| start/exit/reload preserve every nonterminal age | passed |
| outbox-independent | R1-OB-01/queued \| start/exit/reload preserve every nonterminal age | passed |
| outbox-independent | R1-OB-01/sending \| start/exit/reload preserve every nonterminal age | passed |
| outbox-independent | R1-OB-02 \| terminal cutoff retains exactly 24h then removes after 1ms | passed |
| outbox-independent | R1-OB-03 \| strict age, eligible states and fresh entries constrain candidates | passed |
| outbox-independent | R1-OB-04 \| no candidates produces no dialog, even after duplicate attach | passed |
| outbox-independent | R1-OB-05 \| one prompt, safe count only, explicit default/cancel retain | passed |
| outbox-independent | R1-OB-06/response=0 \| nonexplicit response preserves persisted content | passed |
| outbox-independent | R1-OB-06/response=-1 \| nonexplicit response preserves persisted content | passed |
| outbox-independent | R1-OB-06/response=2 \| nonexplicit response preserves persisted content | passed |
| outbox-independent | R1-OB-07 \| dialog rejection preserves data without logging raw error | passed |
| outbox-independent | R1-OB-08/stop \| unresolved dialog cannot delete after lifecycle stop | passed |
| outbox-independent | R1-OB-08/quitting \| unresolved dialog cannot delete after lifecycle stop | passed |
| outbox-independent | R1-OB-08/destroyed \| unresolved dialog cannot delete after lifecycle stop | passed |
| outbox-independent | R1-OB-08/closed \| unresolved dialog cannot delete after lifecycle stop | passed |
| outbox-independent | R1-OB-09 \| stop/destroy before ready cannot prompt or delete | passed |
| outbox-independent | R1-OB-10 \| explicit consent deletes only unchanged shown candidates, persisted after reload | passed |
| outbox-independent | R1-OB-11 \| same-clock same-state update invalidates old consent identity | passed |
| outbox-independent | R1-OB-12 \| reload invalidates old consent, repeats cannot delete newer old items | passed |
| outbox-independent | R1-OB-13/prepare \| write failure keeps memory/disk consistent and queue recoverable | passed |
| outbox-independent | R1-OB-13/state \| write failure keeps memory/disk consistent and queue recoverable | passed |
| outbox-independent | R1-OB-13/cleanup \| write failure keeps memory/disk consistent and queue recoverable | passed |
| outbox-independent | R1-OB-13/delete \| write failure keeps memory/disk consistent and queue recoverable | passed |
| outbox-independent | R1-OB-14 \| pending save publishes no premature state; concurrent operations serialize | passed |
| outbox-independent | R1-OB-15 \| concurrent capacity limit refuses overflow without loss, encrypted blob stays opaque | passed |
| outbox-independent | R1-OB-16 \| inactive consent and dialog save failure retain content | passed |
| main-independent | R1-MAIN-01 \| real main starts Host before native dialog response; cancel preserves disk | passed |
| main-independent | R1-MAIN-02 \| before-quit before window ready stops retention and runs persistence cleanup | passed |
| main-independent | R1-MAIN-03 \| before-quit while dialog pending ignores later affirmative response | passed |
| main-independent | R1-MAIN-04 \| main destruction during dialog preserves all virtual data | passed |
| main-independent | R1-MAIN-05 \| real native adapter affirmative deletes exactly aged draft/queued | passed |
| matrix-independent | R1-SHELL-01 \| HostClient accepts only HTTP IPv4 loopback | passed |
| matrix-independent | R1-SHELL-02 \| concurrent 401 shares refresh, retries once using main-only bearer | passed |
| matrix-independent | R1-SHELL-03 \| expired refresh revokes and exposes only safe error | passed |
| matrix-independent | R1-SHELL-04/503 \| backend failures do not expose body/exception | passed |
| matrix-independent | R1-SHELL-04/invalid-dto \| backend failures do not expose body/exception | passed |
| matrix-independent | R1-SHELL-04/network \| backend failures do not expose body/exception | passed |
| matrix-independent | R1-SHELL-05 \| local owner bootstrap single-flight, refresh and revoke states | passed |
| matrix-independent | R1-SHELL-06 \| managed start/recover single-flight and bounded retry | passed |
| matrix-independent | R1-SHELL-07 \| bad managed nonce is rejected and candidate cleaned | passed |
| matrix-independent | R1-SHELL-08 \| external observation never acquires stop rights | passed |
| matrix-independent | R1-SHELL-09 \| preload exports narrow typed methods, no generic IPC | passed |
| matrix-independent | R1-SHELL-10 \| two distinct virtual contributions compile, no product module created | passed |
| matrix-independent | R1-SHELL-11/module \| duplicate identity fails closed | passed |
| matrix-independent | R1-SHELL-11/profile \| duplicate identity fails closed | passed |
| matrix-independent | R1-SHELL-11/route \| duplicate identity fails closed | passed |
| matrix-independent | R1-SHELL-11/appearance \| duplicate identity fails closed | passed |
| matrix-independent | R1-SHELL-12 \| incompatible UI major and noncanonical ASCII/version reject | passed |
| matrix-independent | R1-SHELL-13 \| UI-04 \| setting keys must be globally unique across contributions | failed |

执行方仅一次兼容命令使用 `r1-compat-vitest.config.mjs`，root指向新普通workspace/apps/desktop，仅include原supervisor-outbox和outbox-retention两文件。13+14=27 passed。cache/output仍在R1独立根；执行方测试内容只读，没有复制改名为独立测试，也没有运行全部90。

第一原节点时刻2026-10-01 23:51:42；原十项23:52:05。新增outbox为2026-10-02 10:25:30，main10:27:41，compat10:29:10，矩阵10:32:11。中间不同工具回合没有连续外部状态监测，保持unverified；没有产品或外部服务会话在该时段运行。角色在工具控制返回时按实际输出补记，不把时刻差异推断为持续执行。

## 24 项原案例逐项结果

完整原预期保留；“原输入/步骤”是设计，不代表本轮均已执行。旧C12与本轮证据分开，只有实测子条件作判断。

### P4B-SEC-01 — blocked

- 原风险/环境/方式：P0 / Windows/Electron / auto。
- 原前置条件：固定 Electron 构建。
- 原输入/步骤：BrowserWindow 配置与运行时 renderer；静态检查并在 renderer 探测。
- **完整原预期**：sandbox/contextIsolation 开启、nodeIntegration 关闭；无 `require/process/fs/child_process` 或任意 preload 对象。
- 实测节点/证据：原 PUB-03 在新依赖下再次通过；R1-MAIN-01 实际导入main但窗口是虚拟adapter。
- 证据层级和缺口：生产 preferences逻辑有证据；实际EXE renderer Node isolation未执行。
- 本轮状态：`blocked`。全部原子条件尚未完整通过。

### P4B-SEC-02 — blocked

- 原风险/环境/方式：P0 / Windows/Electron / auto。
- 原前置条件：CSP/导航 allowlist 冻结。
- 原输入/步骤：inline script、data/javascript URL、未知 origin、新窗口、外链；从不可信内容触发导航/打开。
- **完整原预期**：CSP 阻止执行；未知导航/窗口拒绝；获准外链只由 main 安全打开，不加载进应用权限域。
- 实测节点/证据：原 PUB-03 CSP字符串再次通过；main安全默认/导航接线只读。
- 证据层级和缺口：未在真实页面触发 inline/data/javascript、导航/new-window和外链。
- 本轮状态：`blocked`。全部原子条件尚未完整通过。

### P4B-SEC-03 — blocked

- 原风险/环境/方式：P0 / contract / auto。
- 原前置条件：preload 类型合同可导入。
- 原输入/步骤：枚举 contextBridge 暴露对象；与 allowlist 对比并尝试直接 ipcRenderer/send/invoke。
- **完整原预期**：只暴露窄 typed 方法；无通用 channel、Node require、密钥或进程控制。
- 实测节点/证据：R1-SHELL-09实际导入main preload，capture contextBridge，枚举六组窄API/冻结对象，尝试读取通用invoke/send/ipcRenderer/require/process等均undefined，调用typed方法验证固定channel。companion preload只读为getState/openMain。
- 证据层级和缺口：main preload契约部分通过；未执行companion暴露对象与整个renderer域，保守保持blocked。
- 本轮状态：`blocked`。全部原子条件尚未完整通过。

### P4B-SEC-04 — blocked

- 原风险/环境/方式：P0 / Windows/Electron / auto。
- 原前置条件：IPC handlers 已注册。
- 原输入/步骤：伪造 sender、错 origin、额外/错型参数、未知 channel、重复调用；逐项 invoke/send。
- **完整原预期**：sender 与参数双校验；稳定拒绝；不得启动进程、改设置、打开窗口或泄露异常。
- 实测节点/证据：原 PUB-04 sender/frame/origin/严格参数拒绝再次通过；R1 main导入注册真实handlers。
- 证据层级和缺口：未对注册handler执行未知channel/重复/全部无副作用断言或真实Electroninvoke。
- 本轮状态：`blocked`。全部原子条件尚未完整通过。

### P4B-SEC-05 — blocked

- 原风险/环境/方式：P0 / Windows/Electron / auto。
- 原前置条件：假 token 与假 API key。
- 原输入/步骤：localStorage/sessionStorage/IndexedDB/renderer 内存转储、main safeStorage；登录/刷新/重启并检查各层。
- **完整原预期**：refresh/device token 与 API key 只在 main/OS 保护边界；renderer 无持久原文；日志与 crash dump 无值。
- 实测节点/证据：原PUB-01/02虚拟加密失败闭合/损坏/密文通过；R1-SHELL-05虚拟owner bootstrap/refresh/revoke通过，R1-OB容量/密文逻辑保持。
- 证据层级和缺口：非Windows safeStorage；未检查真实renderer storage/内存、secret/crash dump或OS DPAPI。
- 本轮状态：`blocked`。全部原子条件尚未完整通过。

### P4B-SEC-06 — blocked

- 原风险/环境/方式：P0 / Windows/Electron / auto。
- 原前置条件：后端绑定随机 loopback port。
- 原输入/步骤：只知道端口、错 nonce、错 origin、过期 access、远程地址；绕过 main 直连 Host。
- **完整原预期**：端口不是认证；nonce/origin/token 均校验；只绑定 loopback，远程连接拒绝。
- 实测节点/证据：R1-SHELL-01拒绝非HTTP127.0.0.1 endpoint；02 main-only Bearer与并发401刷新；07 managed坏nonce拒绝。
- 证据层级和缺口：HTTP为fake fetch，nonce为fake child；实际随机监听/origin/access到期/远程连接未运行。
- 本轮状态：`blocked`。全部原子条件尚未完整通过。

### P4B-SEC-07 — blocked

- 原风险/环境/方式：P0 / Windows/Electron / auto。
- 原前置条件：模块标签、错误、消息均含虚拟恶意 HTML。
- 原输入/步骤：script/img/event handler/RTL/超长文本；渲染导航、通知、Agent panel、错误。
- **完整原预期**：文本安全编码、布局有界且不执行；不得改变 IPC、模块注册或权限。
- 实测节点/证据：未做恶意文本UI渲染。
- 证据层级和缺口：真实HTML/RTL/长文本编码布局与无脚本执行证据缺失。
- 本轮状态：`blocked`。全部原子条件尚未完整通过。

### P4B-SEC-08 — blocked

- 原风险/环境/方式：P0 / Windows/Electron / auto。
- 原前置条件：可注入 preload/backend/lazy-load 故障。
- 原输入/步骤：内部路径、SQL、堆栈、token canary；触发并查看 UI、console、日志。
- **完整原预期**：用户只见稳定安全错误和 request ID；renderer console/日志无秘密或未授权数据。
- 实测节点/证据：原PUB-02 corruption安全错误；R1-SHELL-03/04在401刷新失败、503、非法DTO、network异常下安全error不含虚拟canary；R1-OB-07 dialog rejection无raw console输出。
- 证据层级和缺口：未实测实际UI/request ID/preload/lazy故障或真实console/log/crash dump。
- 本轮状态：`blocked`。全部原子条件尚未完整通过。

### P4B-SUP-01 — blocked

- 原风险/环境/方式：P0 / Windows/Electron / auto。
- 原前置条件：supervisor 可记录 PID+nonce。
- 原输入/步骤：自己启动、手工启动、伪造同 PID；请求停止/应用退出。
- **完整原预期**：只停止 PID+nonce 匹配且由本实例启动的子进程；手工/他实例进程保持。
- 实测节点/证据：R1-SHELL-07错误managed nonce拒绝并清理候选；08external observed child shutdown不调用stop/forceStop。
- 证据层级和缺口：虚拟adapter；真实PID/nonce、外来同PID和进程树隔离未执行。
- 本轮状态：`blocked`。全部原子条件尚未完整通过。

### P4B-SUP-02 — blocked

- 原风险/环境/方式：P1 / Windows/Electron / auto。
- 原前置条件：端口分配与 ready 协议冻结。
- 原输入/步骤：端口冲突、无 ready、坏 nonce、ready 超时；启动后端。
- **完整原预期**：使用随机可用 loopback 端口；超时进入离线/诊断并清理自有子进程，不把 health 当 ready。
- 实测节点/证据：R1-SHELL-07坏nonce fail-closed且不进入ready；06成功fake ready。
- 证据层级和缺口：端口冲突、ready总超时、随机loopback和真实自有清理未覆盖，不能把health当ready。
- 本轮状态：`blocked`。全部原子条件尚未完整通过。

### P4B-SUP-03 — blocked

- 原风险/环境/方式：P1 / Windows/Electron / auto。
- 原前置条件：假后端可崩溃。
- 原输入/步骤：启动前崩溃、ready 后崩溃、连续崩溃；观察重启策略。
- **完整原预期**：状态转 offline；重启次数/退避有界，不形成重启风暴或重复 run；用户可恢复。
- 实测节点/证据：R1-SHELL-06 fake child exit→offline，recover退避1/2/4秒、三次上限，第四次exhausted，shutdown阻止再start。
- 证据层级和缺口：注入delay/child，不是Windows真实崩溃；启动前崩溃、健康循环与全部UI状态未覆盖。
- 本轮状态：`blocked`。全部原子条件尚未完整通过。

### P4B-SUP-04 — blocked

- 原风险/环境/方式：P1 / Windows/Electron / auto。
- 原前置条件：已有手动后端或两个 app 启动请求。
- 原输入/步骤：重复启动、开发连接模式；启动/关闭两个客户端。
- **完整原预期**：不产生重复 owned 后端；连接手动后端时不取得停止权；状态可区分。
- 实测节点/证据：R1-SHELL-06并发start/recover single-flight不增重复start；08external不启动owned也无停止权。
- 证据层级和缺口：未执行双真实客户端/单实例EXE场景。
- 本轮状态：`blocked`。全部原子条件尚未完整通过。

### P4B-SUP-05 — not_run

- 原风险/环境/方式：P1 / Windows/Electron / manual。
- 原前置条件：目标 Windows，后端含子线程/连接。
- 原输入/步骤：正常退出、强关主窗口、系统注销；检查进程树/端口/文件锁。
- **完整原预期**：自有后端按冻结时限退出，无僵尸/孤儿/占用端口；未拥有进程不受影响。
- 实测节点/证据：真实退出、强关和注销均未执行；R1-MAIN-02/03仅虚拟Hostshutdown/窗口destroy。
- 证据层级和缺口：manual not_run；无owned资源仅表示没启动，不能推断cleanup通过。
- 本轮状态：`not_run`。全部原子条件尚未完整通过。

### P4B-SUP-06 — blocked

- 原风险/环境/方式：P0 / Windows/Electron / auto。
- 原前置条件：renderer 有未发送虚拟消息。
- 原输入/步骤：后端离线→恢复、应用重启、重复点击；发送并观察 client_event_id/GET。
- **完整原预期**：未发送内容和同一 ID 保留；恢复后只提交一次；UI 不凭新 ID 制造重复账候选。
- 实测节点/证据：原PUB-11不变断言1 passed，原其他10再次通过；新增R1-OB26覆盖持久保留/确认/身份/故障/容量，加R1-MAIN5实际main接线。建议关闭原OUTBOX-001的公开持久化P1。
- 证据层级和缺口：真实老化原生提示unverified、恢复后GET/只提交一次与实际UI缺失；整项从failed改blocked，原P0风险不变。
- 本轮状态：`blocked`。全部原子条件尚未完整通过。

### P4B-UI-01 — blocked

- 原风险/环境/方式：P1 / contract / auto。
- 原前置条件：compiled registry 与 `/modules` fixture。
- 原输入/步骤：后端启用/禁用、桌面缺失、版本不兼容、未知模块；计算交集。
- **完整原预期**：只渲染两侧均存在且兼容的模块；未知/禁用不导航、不预加载。
- 实测节点/证据：原PUB-05canonical registry/Host交集再次通过，R1-SHELL-10两纯测试contribution正常compile。
- 证据层级和缺口：实际导航/preload未运行；没有创建真实第二产品模块。
- 本轮状态：`blocked`。全部原子条件尚未完整通过。

### P4B-UI-02 — blocked

- 原风险/环境/方式：P1 / Windows/Electron / auto。
- 原前置条件：两个 lazy route。
- 原输入/步骤：chunk 加载失败、重试成功、切换模块；导航并恢复。
- **完整原预期**：局部错误边界可重试，Shell/登录/其他模块可用；不循环加载或丢当前会话。
- 实测节点/证据：未执行两个lazy routes的chunk故障/局部retry。
- 证据层级和缺口：Shell/会话/其他模块保留和无循环未验证。
- 本轮状态：`blocked`。全部原子条件尚未完整通过。

### P4B-UI-03 — blocked

- 原风险/环境/方式：P1 / contract / auto。
- 原前置条件：冻结 OpenAPI 与生成命令。
- 原输入/步骤：后端 DTO 字段/枚举/required 改变；生成物陈旧；CI 比较生成差异并编译。
- **完整原预期**：漂移门禁失败并定位；不得靠手写 API 类型掩盖差异或运行时下载 schema。
- 实测节点/证据：生成物和OpenAPI保持冻结输入，没有运行生成/类型漂移mutation。
- 证据层级和缺口：未取得失败定位或CI drift独立证据。
- 本轮状态：`blocked`。全部原子条件尚未完整通过。

### P4B-UI-04 — failed

- 原风险/环境/方式：P1 / contract / auto。
- 原前置条件：UI contribution 合同冻结。
- 原输入/步骤：hostUiMajor、route/path/setting/profile/companion 冲突；编译期注册和启动验证。
- **完整原预期**：不兼容或冲突稳定失败；Shell 无 `if moduleId` 业务分支。
- 实测节点/证据：R1-SHELL-11四种module/profile/route ID/appearance冲突拒绝，12不兼容major和非canonical输入拒绝；13跨module相同setting key仍接受两模块，首次失败。
- 证据层级和缺口：已执行的setting全局唯一违反IF-003 §5，登记P1 REGISTRY-001；path碰撞与无具体module分支的其余子条件未完整验收。
- 本轮状态：`failed`。setting冲突子条件已失败，其他通过不能抵消。

### P4B-CMP-01 — blocked

- 原风险/环境/方式：P1 / Windows/Electron / auto。
- 原前置条件：daily/wealth contributions 与假状态流。
- 原输入/步骤：切换模块及 idle/thinking/tool/confirmation/error/offline；观察窗口、Profile 和状态。
- **完整原预期**：始终只有一个毛毛窗口/Agent 入口；主形态随 contribution，子状态不创建第二 Agent或触发写入。
- 实测节点/证据：R1-MAIN-01虚拟BrowserWindow构造仅Maris和毛毛，Host启动不被dialog等待。
- 证据层级和缺口：实际单毛毛/Agent入口、contribution主形态和完整子状态流未运行。
- 本轮状态：`blocked`。全部原子条件尚未完整通过。

### P4B-CMP-02 — blocked

- 原风险/环境/方式：P1 / Windows/Electron / auto。
- 原前置条件：新设备设置。
- 原输入/步骤：首次和第二次关闭主窗口；关闭、从 Tray 恢复、再次关闭。
- **完整原预期**：首次隐藏并只提示一次；第二次不重复提示；Host/毛毛按设置驻留且无数据丢失。
- 实测节点/证据：未执行真实close/Tray恢复/提示一次场景。
- 证据层级和缺口：虚拟ready-to-show retention不等于首次close提示；真实设备not_run子项保持。
- 本轮状态：`blocked`。全部原子条件尚未完整通过。

### P4B-CMP-03 — blocked

- 原风险/环境/方式：P1 / Windows/Electron / auto。
- 原前置条件：关闭策略可切换。
- 原输入/步骤：退出/每次询问/隐藏，Tray 打开/隐藏；每种设置执行关闭与取消。
- **完整原预期**：行为精确对应设置；“退出”清理自有后端；询问取消不退出；Tray 状态一致。
- 实测节点/证据：未测试三种closePolicy与询问取消/Tray；R1-MAIN before-quit仅退出接线。
- 证据层级和缺口：不以mock app.quit或E2E timer当生产关闭策略证明。
- 本轮状态：`blocked`。全部原子条件尚未完整通过。

### P4B-CMP-04 — not_run

- 原风险/环境/方式：P1 / Windows/Electron / manual。
- 原前置条件：新安装测试 profile。
- 原输入/步骤：首次运行、显式启用/禁用开机启动；检查 OS 启动项和 UI。
- **完整原预期**：默认关闭且无启动项；只有明确操作才创建；禁用清理本应用项，不改其他应用。
- 实测节点/证据：未创建/删除OS启动项；main fixture app.setLoginItemSettings是mock。
- 证据层级和缺口：manual not_run；E2E抑制启动项不等于OS合同通过。
- 本轮状态：`not_run`。全部原子条件尚未完整通过。

### P4B-CMP-05 — not_run

- 原风险/环境/方式：P1 / external/manual / manual。
- 原前置条件：多显示器/缩放/全屏测试设备。
- 原输入/步骤：拖动、置顶、重启、拔屏、分辨率变化、全屏、隐私、键盘；逐项操作并重启。
- **完整原预期**：位置用临时文件原子替换并恢复/夹取；全屏按规则隐藏；隐私不显示金额；键盘入口可达。
- 实测节点/证据：未修改显示器/缩放/全屏/窗口坐标或测试隐私键盘。
- 证据层级和缺口：manual not_run；settings原子保存/重启夹取也未取得本轮独立证据。
- 本轮状态：`not_run`。全部原子条件尚未完整通过。

### P4B-CMP-06 — not_run

- 原风险/环境/方式：P2 / external/manual / manual。
- 原前置条件：支持/不支持透明窗口设备。
- 原输入/步骤：透明失败、普通迷你窗降级；light/dark/system/high-contrast/reduced-motion；中外行情色；切换设备条件和主题。
- **完整原预期**：可安全降级且合同不变；文本对比/焦点可辨；reduced motion 生效；收入/支出色不复用涨跌色。
- 实测节点/证据：未启动透明/降级窗口或切换系统主题。
- 证据层级和缺口：manual not_run；真实对比度/焦点/reduced motion/颜色语义未测试。
- 本轮状态：`not_run`。全部原子条件尚未完整通过。

## Windows、辅助预算、隐私与未执行项

产品0/8、辅助Electron0/4，没有Node spawn目标、CDP/UIA或系统对话框操作；未创建C:\MarisC12\C12-R1-*、外部profile/虚拟数据库、真实AppData或safeStorage fixture。没有权限/环境错误阻止Windows：停止原因是已实测新P1。原生老化提示保留为unverified，不将mock或CDP页数量算设备证据。

main fixture的“虚拟窗口”和“virtual-main-profile”只是EventEmitter及Map路径键，不是真实窗口/磁盘profile；没有UI、process ownership、端口或窗口需要终止。所有Vitest命令均已退出（4组独立退出0、末组退出1、兼容退出0），没有活动session。零owned资源源于未启动，不证明SUP-05/Tray关闭通过。

剩余未执行：真实managed/auth/recover/双窗口/单实例/closePolicy/Tray、原生保留/关闭/明确删除提示；实际CSP/导航/窗口allowlist/renderer秘密和恶意文本；实际lazy route/schema drift/settings/主题/毛毛状态流；ZIP显式无效值/长度/摘要和staging原子性/禁止文件；OS启动项/多屏/透明/注销等。首次C12已经未覆盖且本轮仍未完成的条件完整保留在人工清单，未要求用户现在操作。

隐私：只用VIRTUAL文本、虚拟owner/token/模块、随机内存加密key和虚拟ciphertext；不读取真实API key/财务/消息或旧owner session。失败输出仅公开虚拟模块/setting键，报告和仓库没有原始profile/session/db、秘密或dump。没有Docker/PG/OpenClaw/微信/DeepSeek/provider、扫码或V002，也没有系统时钟、显示器、启动项、网络/代理/安全软件修改。

只清理本轮独立新cache且先核对绝对路径。保留所有result/log、baseline和审计证据；不删除旧环境/profile/out/evidence，也不清理用户或仓库其他内容。Git仅diff等只读，staged=0；如有既有ignore权限/LF→CRLF warning只记录，不改配置。

## 终点交付和边界

新清单终点为 **296 entries：292 unchanged、4 authorized changed、0 unauthorized mismatch、0 missing**。四项只为tester、旧主报告追加、旧人工清单追加、矩阵B段。原8项独立交付精确不变；新EXE/asar/lock固定摘要不变，fuse wire保持production约束；Git staged=0。终点实际证据 `evidence/r1/end-audit.json`，verifier `r1-audit-inputs.py`。该新审计没有重用旧硬编码清单/EXE。

矩阵120个唯一ID和12字段不变；原B前11列/预期逐项不变，B外prefix/suffix字节摘要保持；A64 passed、C20 not_run、D12 not_run。旧主报告/清单原字节prefix精确保留，R1只追加，原首次失败永久可读。终点文件/计数/追加边界摘要见 `evidence/r1/delivery-verification.json`。

新增：本R1报告；r1-vitest.config.mjs、r1-compat-vitest.config.mjs、r1-fixtures.ts、r1-outbox.test.ts、r1-main.test.ts、r1-shell-boundaries.test.ts、r1-audit-inputs.py；evidence/r1内start/end audit、五独立分组和兼容分组首次JSON/log、matrix-baseline、node-index及delivery verification。没有有界Windows runner或seed/read helper的实际交付/运行，因为新P1已停止该阶段，不伪造执行证据。

更新：原C12报告只追加R1链接/关闭建议；人工清单只追加现状/证据/仍缺条件；矩阵B状态备注；自身角色日志。产品、执行方测试、依赖/lock、生成物/build/migration/Compose、冻结/control/overview/snapshot、其他角色和Git均未写。

交接：建议总控关闭原OUTBOX-001，接受新REGISTRY-001缺陷并裁定窄范围返修/新快照。随后安排registry独立复验和剩余Windows/设备门禁；不自动续跑、不改冻结、不派发角色或P4-C。停在 **blocked / finished**。
