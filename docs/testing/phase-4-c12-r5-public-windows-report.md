# P4-C12-R5-PUBLIC 公开冷入口与Windows独立验收报告

交付：**blocked / finished**，供总控review，2026-10-04 Asia/Shanghai。既有测试智能体唯一负责人，control `2026-10-03T23:49:00+08:00`，[本轮任务卡](../coordination/prompts/p4-c12-r5-public-tester.md)。只用虚拟输入；未修改产品/依赖/旧测试/旧首次证据或Git。LAZY-001/UI-02/P4-B未关闭，P4-C/D未开始。

## 首次结果、执行范围和停止位置

本轮公开B **独立启动，不依赖辅助A**。唯一节点 `R5-PUBLIC-UI-02-COLD` 的首次CLI停在初始化阶段：setup、测试模块进入以及jsdom导入进入有持久记录，但没有jsdom resolved/rejected、React import、body或实际main。分类 **initialization_blocked**，不是产品断言failed；没有runner JSON，不制造0/1 failed测试结果。

| 范围 | 本次实际运行 | 结果与限制 |
| --- | --- | --- |
| 新公开冷入口B | CLI1、新fork worker1、main0、fixture0 | initialization_blocked，四条公开断言未执行 |
| 故障来源计算/当前局部DOM | 尚未进入正文 | faultSourceValid/publicTargetResult均未计算，不能赋true或从P补签 |
| P、旧A/B、D15、D16实验 | 0 | 只读使用已接受证据，不计本轮passed |
| 独立恢复/剩余公开 | 0 | not_run；B未通过，按任务停止 |
| lazy八项与Shell/composition兼容 | 0 | not_run，未复制开发测试充当独立证据 |
| Windows/辅助safeStorage/真实chunk注入 | 产品0/8、辅助0/4、注入0 | not_run，未创建外部测试根或profile/session/db |

正文的安全调用断言和UI清理同样未执行。测试脚本尚未创建JSDOM实例、bridge、console spy、React root或订阅；不伪造unmount/退订/global恢复成功。依赖导入内部状态unknown，不能从这一停点推导jsdom、React、Router或产品的内部根因。

## 原生首次阶段与真实预算

三条时间轴独立：controller用自己的Stopwatch控制门禁，config使用CLI本地performance，worker使用原生hrtime。只在各自时间轴内计算差值，不直接拼接相对毫秒。

| worker seq | 真实阶段 | worker相对ms |
| --- | --- | --- |
| 1 | worker_start | 0.121 |
| 2 | journal_ready | 12.321 |
| 3 | test_module_enter | 1236.588 |
| 4 | jsdom_import_enter | 1249.318 |

| controller seq | 阶段 | controller相对ms |
| --- | --- | --- |
| 1 | controller_ready | 30 |
| 2 | root_started | 72 |
| 3 | worker_registered | 2831 |
| 4 | deadline_termination_enter | 15025 |
| 5 | exit_checked | 15082 |
| 6 | controller_finished | 15120 |

config四条实际记录为config_evaluation_enter/object_ready/resolved/server_configured。config PID16336、parent3932；worker PID14076、parent16336与创建CLI对应。空stdout/stderr不是停点依据，以上即时append/fsync的记录才是依据。

| 冻结阶段 | 上限 | 本次实际 |
| --- | --- | --- |
| root启动→body_enter | 15000ms | root启动72ms，初始化收口15025ms，差14953ms；没有body_enter |
| 正文 | 10000ms | 未进入，main/act各自enter/terminal均未出现 |
| UI条件观察 | 5000ms | 未进入，不使用固定睡满或补延时 |
| 自有收口 | 2000ms | deadline→exit_checked 57ms；没有UI cleanup_enter，不宣称finally执行 |
| 总体CLI含报告开销 | 30000ms | process.json记录15113ms；controller_finished实测15120ms，区别保留 |
| Vitest函数外层 | 12000ms，正文+finally | test正文未启动，未把12秒写成业务等待 |

父CLI实际exit -1，timedOut=true/forcedRootTermination=true/forcedWorkerTermination=false。登记worker已退出，其自身exit事件0，exit code/机制unknown；不复制父退出码。双流独立收口完成，stdout/stderr原始与保存字节均0。journal完整无半行、evidenceReadUnverified=false。首次六文件已冻结在cold-first.sha256。

controller在阶段切换前核对上一阶段本地预算，退出前核对当前阶段及总体门禁，报告保留实测完成时间；总体/清理有报告余量，不能把余量当性能保证。初始化增加分段可见性没有证明旧A根因是“时间不够”。本轮最后具体边界是jsdom_import_enter缺少terminal，不声称依赖永久死锁或磁盘冷启动。

## 公开合同、来源定义与未执行状态

新配置environment=node、pool=forks、isolate、maxWorkers1，新worker/cache；Router裸包及subpath直接同一R5物理包、React/DOM单根，无观察门面、loader包装或内部Router/abort记录。顶层先原生logger，测试模块分段await jsdom/React；不在正文前求值Router/main/module-routes/contribution/页面。native configLoader经固定Vitest/Vite本地源码核对，避免bundled配置向上级或只读R5写临时文件；新cacheDir限定evidence/r5-public/cache/cold。本次未形成缓存，目录不存在。

新resolver的normalize/classify与旧R3 **文本一致**，只换新fixture/journal标识：唯一已知DailyFinancePage绝对规范ID或绑定真实module-routes importer的精确相对请求；仅单层已知Vite包装/盘符/斜杠归一，未知query/hash拒绝。新fixture与旧fixture除recorder全局标识外一致：零import/零JSX、真实顶层throw固定VIRTUAL_CHUNK_UNAVAILABLE、不可达default导出。它是ESM求值失败设计，不是网络chunk404；本次未实际命中。

faultSourceValid在冻结脚本中由本次映射、CLI/controller/worker身份、实际求值记录、仓库根、新源码与产品摘要、持续失败模块语义、真实默认loader及冷入口合同共同计算。**当前hash/alert/四断言不参与来源公式**。缺少安全提示不能把已经完整的来源循环归为无效。sourceProof只读本轮完整newline记录及摘要，不引用旧P成功来赋true。本轮尚未调用公式，来源保持未评估，而不是伪造来源有效或某个有效请求错误。

| 本轮原要求/附加条件 | 状态 | 未执行原因 |
| --- | --- | --- |
| 当前#/daily的main.shell .content内安全提示“页面暂时无法打开” | not_run | 尚无DOM/自然路由采样 |
| 同一采样main.shell | not_run | 未进入main/React |
| 同一Shell内模块导航 | not_run | 尚无DOM采样 |
| 同一Shell内统一Agent面板 | not_run | 尚无DOM采样 |
| 精确mapping与本worker顶层throw | not_run | resolver记录0、fixture求值0 |
| 主入口/main Promise与act分开终态 | not_run | enter均未出现，实际main0 |
| 安全DOM/console与零额外边界调用 | not_run | guards/bridge/spy尚未安装，不从缺少监测写成零调用通过 |
| 原生root卸载、订阅平衡及global/console恢复 | not_run | 自有UI资源未创建 |
| 内部逐请求abort/Router错误槽 | 未采集 | 本轮无包装合同，不作为B启动门禁，不拿取消请求补签 |

若已进入正文，新代码先同一局部样本执行全部四soft断言，再判来源；任何失败仍使节点失败。原虚拟bridge/Host交集/空hash/main/StrictMode/default loader保持；无额外navigate/revalidate/recover、成功替身、vi.mock/doMock、getter替身、reset/invalidate/cache-bust。本次只完成静态合同核对，不能写成这些动态断言通过。

安全观测设计覆盖完整MarisBridge方法、未知调用，以及global/window fetch/XHR/WebSocket/EventSource可达网络出口；阻断函数可调用/可构造，先记真实尝试再拒绝。真实renderer冷启动只需要getSnapshot/modules.list/runtime.subscribe；auth/provider/财务没有独立bridge API，结合冻结入口图和可达出口说明范围，不为未监测项造零计数。所有公开console参数、Error/message/stack/cause和own data fields及DOM属性只在内存检查，持久记录安全布尔；递归不完整也不签安全通过。

嵌套finally逐步尝试卸载/退订/DOM关闭/global与全部console恢复；在救援前记录产品unmount后的真实订阅，再核对全程边界和泄漏累计。救援成功不掩盖产品漏退订。上述机制本次尚未运行；不能预写cleanup成功。

## 静态首次问题、固定输入和修正预算

新起点**638/638 matched**，0 mismatch/missing、staged0；清单SHA `d6b30f1b9de498d5cdee733a51b21c8cf845c4b64045b40c5f7671d5bde0a747`。既有P的52项交付与15项冻结源码只读全部匹配，源389/out140/Python资源67逐项匹配，EXE/asar/lock/fuses固定；7个普通依赖物理元数据与Node24.21.0/TypeScript6.0.3核对，没有重跑P或D16两次实验。

- EXE：`64ce71f3a7b3055f9ad27f6d611e28c4af7e9ba8b86d8b21399b7b422844a80e`。
- app.asar：`5ba47909537e1419dc275fa3ca1e5e076a1aa6d5c0205229f91defb92ddd0931`。
- lock：`5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。

10项新目标源码在MJS/TSX/Python/PowerShell解析与静态谓词后冻结；静态首次r5_public_main_budget是检查器文本正则把擦除的typeof import与实际动态import一起计数，改为AST CallExpression后确认实际main导入仅1。首次verifier/test与脱敏错误保留。**普通静态谓词更正1、额外前置worker0、目标重试0**；普通语法检查进程不是Vitest worker或业务节点。

只读子任务r5_public_contract_review检查合同/新工具，指出局部采样、四断言排序、安全调用、阶段门禁、权限未知、原生退订及异常收口记录问题；父任务在首次目标前修正并静态核对/冻结。最后完整newline收口读取修正由父任务解析核对；子任务意见不是动态验收，没有写入或执行目标，回执见subagent-read-only-receipt.json。

本轮初始化停止没有收到jsdom rejected或其他原Error；最后脱敏失败证据是controller的initialization deadline。已采用分段await、原生即时日志、固定普通依赖、独立worker/cache和边界时限，仍未取得terminal。**没有明确纯工具配置错误**，unknown初始化超时不满足定向更正授权。首次材料/输入和资源收口保留，但不使用额外worker、不延时、不清OS缓存、不改产品/依赖/包、不新建诊断任务。由总控决定下一步；旧A原因unknown与本次B阶段证据分开。

报告生成后，角色日志更新工具曾在打开自身文件时出现OSError/errno22；原文件仍完整。通过限定自身文件的补丁补齐里程碑，未重启任何目标或修改冻结工具；该交付写入异常不回填为jsdom初始化原因。

## 原24项完整映射

矩阵120唯一ID/12字段/原前11列保持；A64 passed、C20/D12 not_run保持；B仍0 passed/1 failed/19 blocked/4 not_run。原失败历史不被初始化阻塞覆盖或洗成通过；各项完整原预期、已有证据、本轮事实和剩余缺口如下。

### P4B-SEC-01 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：固定 Electron 构建。
- 输入：BrowserWindow 配置与运行时 renderer。
- 操作：静态检查并在 renderer 探测。
- **完整原预期**：sandbox/contextIsolation 开启、nodeIntegration 关闭；无 `require/process/fs/child_process` 或任意 preload 对象。
- 已有历史部分：原 PUB-03 在新依赖下再次通过；R1-MAIN-01 实际导入main但窗口是虚拟adapter。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：生产 preferences逻辑有证据；实际EXE renderer Node isolation未执行。
- 当前状态：`blocked`；完整要求未满足不标passed。

### P4B-SEC-02 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：CSP/导航 allowlist 冻结。
- 输入：inline script、data/javascript URL、未知 origin、新窗口、外链。
- 操作：从不可信内容触发导航/打开。
- **完整原预期**：CSP 阻止执行；未知导航/窗口拒绝；获准外链只由 main 安全打开，不加载进应用权限域。
- 已有历史部分：原 PUB-03 CSP字符串再次通过；main安全默认/导航接线只读。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：未在真实页面触发 inline/data/javascript、导航/new-window和外链。
- 当前状态：`blocked`；完整要求未满足不标passed。

### P4B-SEC-03 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / contract/unit / contract / auto。
- 前置：preload 类型合同可导入。
- 输入：枚举 contextBridge 暴露对象。
- 操作：与 allowlist 对比并尝试直接 ipcRenderer/send/invoke。
- **完整原预期**：只暴露窄 typed 方法；无通用 channel、Node require、密钥或进程控制。
- 已有历史部分：R1-SHELL-09实际导入main preload，capture contextBridge，枚举六组窄API/冻结对象，尝试读取通用invoke/send/ipcRenderer/require/process等均undefined，调用typed方法验证固定channel。companion preload只读为getState/openMain。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：main preload契约部分通过；未执行companion暴露对象与整个renderer域，保守保持blocked。
- 当前状态：`blocked`；完整要求未满足不标passed。

### P4B-SEC-04 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：IPC handlers 已注册。
- 输入：伪造 sender、错 origin、额外/错型参数、未知 channel、重复调用。
- 操作：逐项 invoke/send。
- **完整原预期**：sender 与参数双校验；稳定拒绝；不得启动进程、改设置、打开窗口或泄露异常。
- 已有历史部分：原 PUB-04 sender/frame/origin/严格参数拒绝再次通过；R1 main导入注册真实handlers。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：未对注册handler执行未知channel/重复/全部无副作用断言或真实Electroninvoke。
- 当前状态：`blocked`；完整要求未满足不标passed。

### P4B-SEC-05 — blocked

- 来源/风险/层/环境/方式：F07/F11 / P0 / security/manual / Windows/Electron / auto。
- 前置：假 token 与假 API key。
- 输入：localStorage/sessionStorage/IndexedDB/renderer 内存转储、main safeStorage。
- 操作：登录/刷新/重启并检查各层。
- **完整原预期**：refresh/device token 与 API key 只在 main/OS 保护边界；renderer 无持久原文；日志与 crash dump 无值。
- 已有历史部分：原PUB-01/02虚拟加密失败闭合/损坏/密文通过；R1-SHELL-05虚拟owner bootstrap/refresh/revoke通过，R1-OB容量/密文逻辑保持。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：非Windows safeStorage；未检查真实renderer storage/内存、secret/crash dump或OS DPAPI。
- 当前状态：`blocked`；完整要求未满足不标passed。

### P4B-SEC-06 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / API/integration / Windows/Electron / auto。
- 前置：后端绑定随机 loopback port。
- 输入：只知道端口、错 nonce、错 origin、过期 access、远程地址。
- 操作：绕过 main 直连 Host。
- **完整原预期**：端口不是认证；nonce/origin/token 均校验；只绑定 loopback，远程连接拒绝。
- 已有历史部分：R1-SHELL-01拒绝非HTTP127.0.0.1 endpoint；02 main-only Bearer与并发401刷新；07 managed坏nonce拒绝。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：HTTP为fake fetch，nonce为fake child；实际随机监听/origin/access到期/远程连接未运行。
- 当前状态：`blocked`；完整要求未满足不标passed。

### P4B-SEC-07 — blocked

- 来源/风险/层/环境/方式：F11/F12 / P0 / security/manual / Windows/Electron / auto。
- 前置：模块标签、错误、消息均含虚拟恶意 HTML。
- 输入：script/img/event handler/RTL/超长文本。
- 操作：渲染导航、通知、Agent panel、错误。
- **完整原预期**：文本安全编码、布局有界且不执行；不得改变 IPC、模块注册或权限。
- 已有历史部分：未做恶意文本UI渲染。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：真实HTML/RTL/长文本编码布局与无脚本执行证据缺失。
- 当前状态：`blocked`；完整要求未满足不标passed。

### P4B-SEC-08 — blocked

- 来源/风险/层/环境/方式：F11 / P0 / desktop/e2e / Windows/Electron / auto。
- 前置：可注入 preload/backend/lazy-load 故障。
- 输入：内部路径、SQL、堆栈、token canary。
- 操作：触发并查看 UI、console、日志。
- **完整原预期**：用户只见稳定安全错误和 request ID；renderer console/日志无秘密或未授权数据。
- 已有历史部分：原PUB-02 corruption安全错误；R1-SHELL-03/04在401刷新失败、503、非法DTO、network异常下安全error不含虚拟canary；R1-OB-07 dialog rejection无raw console输出。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：未实测实际UI/request ID/preload/lazy故障或真实console/log/crash dump。
- 当前状态：`blocked`；完整要求未满足不标passed。

### P4B-SUP-01 — blocked

- 来源/风险/层/环境/方式：D9 BackendSupervisor / P0 / desktop/e2e / Windows/Electron / auto。
- 前置：supervisor 可记录 PID+nonce。
- 输入：自己启动、手工启动、伪造同 PID。
- 操作：请求停止/应用退出。
- **完整原预期**：只停止 PID+nonce 匹配且由本实例启动的子进程；手工/他实例进程保持。
- 已有历史部分：R1-SHELL-07错误managed nonce拒绝并清理候选；08external observed child shutdown不调用stop/forceStop。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：虚拟adapter；真实PID/nonce、外来同PID和进程树隔离未执行。
- 当前状态：`blocked`；完整要求未满足不标passed。

### P4B-SUP-02 — blocked

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：端口分配与 ready 协议冻结。
- 输入：端口冲突、无 ready、坏 nonce、ready 超时。
- 操作：启动后端。
- **完整原预期**：使用随机可用 loopback 端口；超时进入离线/诊断并清理自有子进程，不把 health 当 ready。
- 已有历史部分：R1-SHELL-07坏nonce fail-closed且不进入ready；06成功fake ready。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：端口冲突、ready总超时、随机loopback和真实自有清理未覆盖，不能把health当ready。
- 当前状态：`blocked`；完整要求未满足不标passed。

### P4B-SUP-03 — blocked

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：假后端可崩溃。
- 输入：启动前崩溃、ready 后崩溃、连续崩溃。
- 操作：观察重启策略。
- **完整原预期**：状态转 offline；重启次数/退避有界，不形成重启风暴或重复 run；用户可恢复。
- 已有历史部分：R1-SHELL-06 fake child exit→offline，recover退避1/2/4秒、三次上限，第四次exhausted，shutdown阻止再start。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：注入delay/child，不是Windows真实崩溃；启动前崩溃、健康循环与全部UI状态未覆盖。
- 当前状态：`blocked`；完整要求未满足不标passed。

### P4B-SUP-04 — blocked

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：已有手动后端或两个 app 启动请求。
- 输入：重复启动、开发连接模式。
- 操作：启动/关闭两个客户端。
- **完整原预期**：不产生重复 owned 后端；连接手动后端时不取得停止权；状态可区分。
- 已有历史部分：R1-SHELL-06并发start/recover single-flight不增重复start；08external不启动owned也无停止权。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：未执行双真实客户端/单实例EXE场景。
- 当前状态：`blocked`；完整要求未满足不标passed。

### P4B-SUP-05 — not_run

- 来源/风险/层/环境/方式：D9 lifecycle / P1 / security/manual / Windows/Electron / manual。
- 前置：目标 Windows，后端含子线程/连接。
- 输入：正常退出、强关主窗口、系统注销。
- 操作：检查进程树/端口/文件锁。
- **完整原预期**：自有后端按冻结时限退出，无僵尸/孤儿/占用端口；未拥有进程不受影响。
- 已有历史部分：真实退出、强关和注销均未执行；R1-MAIN-02/03仅虚拟Hostshutdown/窗口destroy。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：manual not_run；无owned资源仅表示没启动，不能推断cleanup通过。
- 当前状态：`not_run`；完整要求未满足不标passed。

### P4B-SUP-06 — blocked

- 来源/风险/层/环境/方式：D9 offline recovery / P0 / desktop/e2e / Windows/Electron / auto。
- 前置：renderer 有未发送虚拟消息。
- 输入：后端离线→恢复、应用重启、重复点击。
- 操作：发送并观察 client_event_id/GET。
- **完整原预期**：未发送内容和同一 ID 保留；恢复后只提交一次；UI 不凭新 ID 制造重复账候选。
- 已有历史部分：原PUB-11不变断言1 passed，原其他10再次通过；新增R1-OB26覆盖持久保留/确认/身份/故障/容量，加R1-MAIN5实际main接线。建议关闭原OUTBOX-001的公开持久化P1。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：真实老化原生提示unverified、恢复后GET/只提交一次与实际UI缺失；整项从failed改blocked，原P0风险不变。
- 当前状态：`blocked`；完整要求未满足不标passed。

### P4B-UI-01 — blocked

- 来源/风险/层/环境/方式：F12 / P1 / contract/unit / contract / auto。
- 前置：compiled registry 与 `/modules` fixture。
- 输入：后端启用/禁用、桌面缺失、版本不兼容、未知模块。
- 操作：计算交集。
- **完整原预期**：只渲染两侧均存在且兼容的模块；未知/禁用不导航、不预加载。
- 已有历史部分：原PUB-05canonical registry/Host交集再次通过，R1-SHELL-10两纯测试contribution正常compile。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：实际导航/preload未运行；没有创建真实第二产品模块。
- 当前状态：`blocked`；完整要求未满足不标passed。

### P4B-UI-02 — failed

- 来源/风险/层/环境/方式：F12 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：两个 lazy route。
- 输入：chunk 加载失败、重试成功、切换模块。
- 操作：导航并恢复。
- **完整原预期**：局部错误边界可重试，Shell/登录/其他模块可用；不循环加载或丢当前会话。
- 已有历史部分：未执行两个lazy routes的chunk故障/局部retry。；R4-R1 factory1、5016ms无alert，Router终态未关联。；R4-R2同Router取消加载安全reject、有效加载成功，无alert，原1失败/3通过，未关闭。；R4-R3的P默认loader三次安全拒绝，A正文前阻塞、旧B未执行；D16两次实验不计界面通过。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：本轮公开B独立启动，但未进入main/来源和局部DOM采样；初始隔离、恢复/健康切换/订阅与会话保持及真实Windows chunk/session均未验收。内部Router/abort按本轮合同未采集，不作为启动门禁；LAZY-001未关闭。
- 当前状态：`failed`；完整要求未满足不标passed。

### P4B-UI-03 — blocked

- 来源/风险/层/环境/方式：F12 / P1 / contract/unit / contract / auto。
- 前置：冻结 OpenAPI 与生成命令。
- 输入：后端 DTO 字段/枚举/required 改变；生成物陈旧。
- 操作：CI 比较生成差异并编译。
- **完整原预期**：漂移门禁失败并定位；不得靠手写 API 类型掩盖差异或运行时下载 schema。
- 已有历史部分：生成物和OpenAPI保持冻结输入，没有运行生成/类型漂移mutation。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：未取得失败定位或CI drift独立证据。
- 当前状态：`blocked`；完整要求未满足不标passed。

### P4B-UI-04 — blocked

- 来源/风险/层/环境/方式：F12 / P1 / contract/unit / contract / auto。
- 前置：UI contribution 合同冻结。
- 输入：hostUiMajor、route/path/setting/profile/companion 冲突。
- 操作：编译期注册和启动验证。
- **完整原预期**：不兼容或冲突稳定失败；Shell 无 `if moduleId` 业务分支。
- 已有历史部分：R1-SHELL-11四种module/profile/route ID/appearance冲突拒绝，12不兼容major和非canonical输入拒绝；13跨module相同setting key仍接受两模块，首次失败。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：UI-04完整独立结构/strict贡献及启动验证映射尚未完成，新P1停止；不能由路径通过直接passed。
- 当前状态：`blocked`；完整要求未满足不标passed。

### P4B-CMP-01 — blocked

- 来源/风险/层/环境/方式：F13；U02 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：daily/wealth contributions 与假状态流。
- 输入：切换模块及 idle/thinking/tool/confirmation/error/offline。
- 操作：观察窗口、Profile 和状态。
- **完整原预期**：始终只有一个毛毛窗口/Agent 入口；主形态随 contribution，子状态不创建第二 Agent或触发写入。
- 已有历史部分：R1-MAIN-01虚拟BrowserWindow构造仅Maris和毛毛，Host启动不被dialog等待。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：实际单毛毛/Agent入口、contribution主形态和完整子状态流未运行。
- 当前状态：`blocked`；完整要求未满足不标passed。

### P4B-CMP-02 — blocked

- 来源/风险/层/环境/方式：U01/F13 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：新设备设置。
- 输入：首次和第二次关闭主窗口。
- 操作：关闭、从 Tray 恢复、再次关闭。
- **完整原预期**：首次隐藏并只提示一次；第二次不重复提示；Host/毛毛按设置驻留且无数据丢失。
- 已有历史部分：未执行真实close/Tray恢复/提示一次场景。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：虚拟ready-to-show retention不等于首次close提示；真实设备not_run子项保持。
- 当前状态：`blocked`；完整要求未满足不标passed。

### P4B-CMP-03 — blocked

- 来源/风险/层/环境/方式：U01 / P1 / desktop/e2e / Windows/Electron / auto。
- 前置：关闭策略可切换。
- 输入：退出/每次询问/隐藏，Tray 打开/隐藏。
- 操作：每种设置执行关闭与取消。
- **完整原预期**：行为精确对应设置；“退出”清理自有后端；询问取消不退出；Tray 状态一致。
- 已有历史部分：未测试三种closePolicy与询问取消/Tray；R1-MAIN before-quit仅退出接线。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：不以mock app.quit或E2E timer当生产关闭策略证明。
- 当前状态：`blocked`；完整要求未满足不标passed。

### P4B-CMP-04 — not_run

- 来源/风险/层/环境/方式：U05 / P1 / security/manual / Windows/Electron / manual。
- 前置：新安装测试 profile。
- 输入：首次运行、显式启用/禁用开机启动。
- 操作：检查 OS 启动项和 UI。
- **完整原预期**：默认关闭且无启动项；只有明确操作才创建；禁用清理本应用项，不改其他应用。
- 已有历史部分：未创建/删除OS启动项；main fixture app.setLoginItemSettings是mock。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：manual not_run；E2E抑制启动项不等于OS合同通过。
- 当前状态：`not_run`；完整要求未满足不标passed。

### P4B-CMP-05 — not_run

- 来源/风险/层/环境/方式：F13 / P1 / desktop/e2e / external/manual / manual。
- 前置：多显示器/缩放/全屏测试设备。
- 输入：拖动、置顶、重启、拔屏、分辨率变化、全屏、隐私、键盘。
- 操作：逐项操作并重启。
- **完整原预期**：位置用临时文件原子替换并恢复/夹取；全屏按规则隐藏；隐私不显示金额；键盘入口可达。
- 已有历史部分：未修改显示器/缩放/全屏/窗口坐标或测试隐私键盘。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：实际位置夹取/重启/多屏/全屏/键盘/隐私UI与全部人工设备条件未执行，整项manual not_run保持。
- 当前状态：`not_run`；完整要求未满足不标passed。

### P4B-CMP-06 — not_run

- 来源/风险/层/环境/方式：U02；主题要求 / P2 / desktop/e2e / external/manual / manual。
- 前置：支持/不支持透明窗口设备。
- 输入：透明失败、普通迷你窗降级；light/dark/system/high-contrast/reduced-motion；中外行情色。
- 操作：切换设备条件和主题。
- **完整原预期**：可安全降级且合同不变；文本对比/焦点可辨；reduced motion 生效；收入/支出色不复用涨跌色。
- 已有历史部分：未启动透明/降级窗口或切换系统主题。
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：manual not_run；真实对比度/焦点/reduced motion/颜色语义未测试。
- 当前状态：`not_run`；完整要求未满足不标passed。

## 资源、终点核对和交接

自己的创建句柄/实时journal父子证明与登记worker句柄用于定向收口；worker身份与CLI实际对应。事后Get-Process明确NoProcessFoundForGivenId确认两登记PID不存在，访问失败不会当不存在；没有全局kill或精确进程数门禁。完整系统/历史后代枚举未执行、未核实；限制保留，不把父exit复制给worker。

native configLoader没有配置临时文件；本轮cache没有生成，经过绝对专属边界/no-reparse核对确认不存在，deletedFiles=0。首次六文件、10冻结源码、静态首次材料及所有同步journal/双流保留。没有外部Windows根/profile/会话/db/监听，没有产品或辅助Electron、Docker/PG/OpenClaw/微信/DeepSeek/provider操作，也不要求用户现在点击、注销、改主题或启动项。

终点由r5-public-delivery.py实际逐项复核通过：638输入中634保持，tester、旧主报告/人工清单追加、矩阵B备注四项授权变化，0越界/缺失、staged0；受验源389/out140/resources67、固定包/fuses/7元数据/10冻结源码保持。191旧独立文件、69旧D15文件保持。原R3交付52项中48项保持、4个本轮授权共享文档更新，原15项源码保持；D16交付39项保持。矩阵120唯一ID/12字段/前11列/全部状态/B外字节及旧文档原字节prefix保持，旧主报告/人工清单各追加1027bytes。最终41项交付摘要逐项核对；实际结果见end-audit.json、delivery-verification.json及delivery.sha256，不写自引用摘要。

Git只读staged/diff-check exit0，只有Git环境warning；新全文件及授权新段行尾扫描通过，旧R2历史空格不改，不以tracked-only检查代替新增格式核对。最终只到blocked / finished，供总控review。卡点是本轮具体jsdom import缺少terminal，根因unknown；需要总控根据固定源码/首次阶段裁定，而不是本角色盲重跑/延时或自动派新任务。公开B授权已独立使用，不再回到A先通过的旧门禁。
