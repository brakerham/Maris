"""Authorized R3 report/append-only handoff from first-run evidence; no targets."""
from pathlib import Path
import json,re,hashlib
ROOT=Path(__file__).resolve().parents[3];OWN=ROOT/'tests/independent/desktop/evidence/r4-r3'
REPORT='docs/testing/phase-4-c12-r4-r3-persistent-import-windows-report.md';MATRIX='docs/testing/phase-4-modular-agent-host-test-matrix.md'
assert not (ROOT/REPORT).exists(),'handoff_once'
def load(name):return json.loads((OWN/name).read_text(encoding='utf-8-sig'))
def journal(phase):return [json.loads(l) for l in (OWN/phase/'worker.journal.jsonl').read_text(encoding='utf-8').splitlines()]
def save(name,value):(OWN/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=journal('injection');a=journal('cold-trace');pr=load('injection/result.json');pp=load('injection/process.json');ap=load('cold-trace/process.json')
mapping=[json.loads(l) for l in (OWN/'injection/resolver.journal.jsonl').read_text(encoding='utf-8').splitlines()]
terminals=[e for e in p if e['stage']=='p_call_terminal'];assert len(terminals)==3
assert all(e['rejected'] and e['safeModuleCode'] and not e['virtualRawError'] for e in terminals)
assert pr['numTotalTests']==pr['numPassedTests']==1 and pr['numFailedTests']==0
assert [e['stage'] for e in a]==['worker_start','journal_ready'] and ap['timedOut'] and ap['mainImportRequests']==0
assert not (OWN/'cold-trace/result.json').exists() and not (OWN/'cold-public').exists()
assert len(mapping)>0 and all(e['fixtureOrdinal']==e['targetOrdinal']==1 and not e['unsupportedQuery'] for e in mapping)
save('propagation-summary.json',{'P':{'caseId':'R4-R3-INJECTION-PERSISTENT','status':'passed','calls':terminals,
 'fixtureEvaluations':len([e for e in p if e['stage']=='fixture_evaluation_enter']),'mappingRecords':mapping,
 'mainRequests':0,'isUiAcceptance':False},'A':{'caseId':'R4-R3-UI-02-COLD-TRACE','status':'blocked_pre_body_timeout',
 'lastPersistentStage':'journal_ready','bodyEntered':False,'mainRequests':0,'fixtureEvaluations':0,'loaderCalls':0,
 'originalFourAssertions':'not_run','runnerJsonProduced':False,'productConclusion':'unverified'},'B':'not_run',
 'recovery':'not_run','compatibility':'not_run','windows':'not_run','newProductDefects':0,'lazy001ClosureSuggested':False})
save('node-index.json',{'injectionNodesExecuted':1,'injectionPassed':1,'injectionFailed':0,
 'uiNodesExecuted':0,'uiPassed':0,'uiFailed':0,'AInvocationStatus':'blocked_pre_body_timeout','B':'not_run',
 'vitestCliStarts':2,'workersStarted':2,'actualMainRequests':0,'extraPreMainWorkers':0,'targetRetries':0,
 'ordinaryStaticMappingCorrections':1,'recoveryNodesExecuted':0,'executorCompatibilityExecuted':0,
 'productStarts':0,'auxiliaryStarts':0,'chunkNetworkInjections':0})
start=load('start-audit.json');baseline=load('baseline.json');cases=[r for r in baseline['cases'] if r[1]=='B'];assert len(cases)==24
old=(ROOT/'docs/testing/phase-4-c12-r4-r2-cold-entry-windows-report.md').read_text(encoding='utf-8-sig')
report=f'''# P4-C12-R4-R3 持续导入故障与Windows验收报告

交付：**blocked / finished**，供总控review。既有独立测试智能体、唯一负责人；control `2026-10-03T03:56:00+08:00`，[R3任务卡](../coordination/prompts/p4-c12-r4-r3-persistent-import-tester.md)。全部是虚拟输入，未修改产品或旧首次结果，LAZY-001/UI-02/P4-B未关闭。

## 已验证结果和停止位置

**持续导入故障P通过**：实际compileRegistry/真实contribution/createModuleRoutes默认内置loader，两次并发调用及等待二者终态后的第三次调用均安全reject，错误码desktop_module_unavailable；真实故障ESM求值一次，精确目标映射命中。

**全新冷入口A在测试模块初始化阶段达到硬限**：持久journal只有worker_start/journal_ready，尚未进入body，main/act/fixture/loader/DOM和原四断言均未开始。控制器在原15秒预算内定向结束已创建的自有树；登记CLI和worker均结束。A没有runner JSON，不伪造测试failed节点、正文异常或产品缺陷。B与全部后续停止。超时原因未定位，产品行为unverified，不扩大等待/缓存重置/预热或盲重跑。

| 节点 | 条件 | 首次结果 / 预算 |
| --- | --- | --- |
| P `R4-R3-INJECTION-PERSISTENT` | 无门面真实Router、真实默认loader、两并发+随后一次、没有main | **1 passed/0 failed**；CLI1/worker1/main0；3次调用不是3个节点 |
| A `R4-R3-UI-02-COLD-TRACE` | 全新worker/cache、空hash冷main、同步门面、同真实失败fixture；配置已冻结 | **blocked_pre_body_timeout**；CLI1/worker1/main0；业务断言未执行 |
| B `R4-R3-UI-02-COLD-PUBLIC` | 第三个独立worker、直接真实Router、无门面/loader包装 | **not_run**；CLI0/worker0/main0 |
| 独立恢复/公开余项 | 可控可信loader恢复，与初始持续失败fixture分列 | not_run |
| 开发兼容 | lazy八项及Shell/composition允许一次，单列 | not_run |
| Windows | 固定EXE/真实chunk网络故障及原生行为 | 产品0/8、辅助0/4、真实请求注入0 |

## 精确注入方案及实际命中

去掉新增测试中的目标vi.mock factory，旧R4/R4-R1/R4-R2全部原样保留。新增pre resolveId只允许已知DailyFinancePage绝对规范路径（无扩展或.tsx），或精确相对请求../modules/daily-finance/DailyFinancePage且importer是实际module-routes.tsx。只归一盘符/反斜杠以及单层已知/@id/、/@fs/；不全路径小写、不URL解码、不通配目录/Router/其他页面。未知query/hash不映射并报固定安全配置错误。

固定Vite module-runner.js的dynamicRequest会将相对请求解析为绝对路径再请求；Vitest Windows传输会包装/@id/，Vite root外可用/@fs/。新resolver同时精确支持这些已知形态，不能仅用未经证实的相对alias。**本次实际命中形态为相对请求、importerBound=true，targetOrdinal1→fixtureOrdinal1，unsupportedQuery=false，记录1条**；其他规范形态只完成静态谓词核对，不冒称实际动态命中。

fixture为新r4-r3-failing-page.tsx：纯JS、零JSX、零import，先通过原生global recorder同步记录fixture_evaluation_enter，再顶层throw固定VIRTUAL_CHUNK_UNAVAILABLE，声明不可达default导出。TypeScript静态转译确认未注入任何React/helper import；.tsx保留原已知扩展形态。只有目标模块被重定向，产品默认loader/route/errorElement、其他产品模块保持真实。

这是**真实ESM模块求值失败令import Promise拒绝**，不是网络chunk404，不改.default getter、Page、loader或Router错误槽。没有目标vi.mock/doMock/importActual、Router async mock、cache-bust、invalidate/reset、生产修改/外部monkeypatch。普通Vite解析/缓存是runner原有行为，未新增缓存操纵。

resolver命中回执在CLI进程的独立resolver.journal中同步追加/fsync；fixture/loader记录在worker.setup建立的journal。两者起点不同，不把相对毫秒直接排成跨进程因果时序。只保存ordinal/安全布尔/PID，不输出请求路径、URL、模块对象或raw错误。

## P的默认loader终态证据

P在正文动态导入真实contribution、compileRegistry与createModuleRoutes，调用createModuleRoutes(registry)而不传loaders。没有导入main，也没有构造Router导航或DOM。对原route.loader的调用只做诊断catch，原Promise的拒绝和安全码被记录；两个并发await完成后才调用第三次。

| seq | worker阶段 | worker相对ms | 实际终态 |
| --- | --- | --- | --- |
'''
for e in p:
    detail=''
    if e['stage']=='p_call_enter':detail=f"call{e['callSeq']} / defaultLoader=true"
    elif e['stage']=='p_call_terminal':detail=f"call{e['callSeq']} reject={e['rejected']} safeModuleCode={e['safeModuleCode']} rawVirtualError={e['virtualRawError']}"
    elif e['stage']=='fixture_evaluation_enter':detail='fixtureOrdinal1，实际求值count1'
    report+=f"| {e['seq']} | {e['stage']} | {e['elapsedMs']:.3f} | {detail} |\n"
report+=f'''
call1/2均安全拒绝后call3进入，三次均不透传原虚拟错误。实际fixture求值1次，不从调用次数推定三次求值。当前结果证明固定runner/配置下并发与随后请求持续拒绝；不反推旧manual mock的实际内部分支，也不计为UI或Windows通过。

P测试{pr['nodes'][0]['durationMs']:.3f}ms、CLI {pp['durationMs']}ms，实际exit0，无timeout/强杀；13条连续worker记录、1条resolver映射、JSON1 passed、stdout安全摘要78bytes/stderr0。首次文件均保留。

## A首次未进入正文的阶段与纠正预算

| 记录 | 实际证据 |
| --- | --- |
| 自有CLI启动 | PID15796；startedUtc={ap['startedUtc']} |
| worker登记 | PID16464、parent15796；controller运行中确认身份 |
| setup第一条 | seq1 worker_start，0.116ms |
| setup第二条 | seq2 journal_ready，11.964ms；此后没有其他完整事件 |
| 正文/主入口 | body_enter、main_import_enter、act_enter均不存在；main请求0 |
| fixture/loader/Router | 实际求值/loader调用0；无resolver映射journal，Router状态未取得 |
| 时限收口 | controller 14512ms进入deadline_termination_enter；process耗时{ap['durationMs']}ms、自然退出false、强制定向收口true，父exit-1 |
| 最后持久阶段 | journal_ready；不是某个被推定的React/jsdom/Router内部等待 |
| JSON/双流 | runner JSON未生成，stdout/stderr均0bytes，独立流收口完成 |

原生setup先于测试模块初始化，日志每条同步写入/fsync、写失败立即退出；冻结正文在产品调用之前首先写body_enter。这支持本次尚未进入正文、没有fixture/loader/main目标阶段。不能从空stdout独自作此结论，也不能宣称15秒test断言超时：本轮是**CLI收集/初始化硬限**，test10秒规则保留但正文尚未启动。

当前没有定位到可更正的纯工具配置错误。目标前修正授权同时要求错误范围可证明与首次材料冻结/输入不变/自有进程退出；仅“main没开始”不构成盲重试理由。于是**额外前置worker0、目标更正0、目标重跑0**。cold-trace-first.sha256冻结5个首次文件；pre-main-no-retry-ruling.json记录不追加理由。没有修改A配置/源码或复跑，B与后续not_run。

## A/B原四断言和传播要求

| 原业务要求/前置 | A | B |
| --- | --- | --- |
| alert含“页面暂时无法打开” | not_run | not_run |
| main.shell存在 | not_run | not_run |
| 模块导航存在 | not_run | not_run |
| 统一Agent面板存在 | not_run | not_run |
| 当前未取消loader安全reject | 未启动，不从P补签 | not_run |
| 同活跃Router目标错误槽安全code | Router未取得 | not_run |
| main与act分别enter/terminal | 均未开始 | not_run |

新A/B保留同原虚拟bridge/jsdom/global、空hashURL、真实StrictMode/main/contribution/Host交集。A的同步ESM透传门面及Promise/Router身份保持静态检查通过：精确裸Router映射、独立真实alias、防循环/单物理React根、export*真实Context，仅包装目标loader并返回原Promise/Router。它的函数身份变化/旁路监听/订阅/fsync扰动均披露。**本次A没有动态加载到门面，不能借R2的门面运行写成本轮动态通过**。B直连真实包、不安装门面、不回填A遥测。

本轮没有有效目标的取消/错误槽/DOM关联，产品结论unverified，无新增已定级产品P0/P1，不建议关闭LAZY-001；原R2取消attempt1/有效attempt2的历史仍独立保留。P故障接线已经证明，后续需总控针对这次正文前初始化硬限裁定下一步，本角色不自行修改或再生成bootstrap/延时任务。

## 固定输入、静态首错和可见性间隔

新起点**544/544 matched**、暂存空、0 mismatch/missing；清单SHA `{start['manifest_sha256']}`。旧受验包构建源389/out140/Python资源67逐项匹配，EXE/asar/lock/fuses保持任务固定值。Node24.21.0、Vitest5.0.2、Vite7.3.6、React/DOM19.3.0、Router8.4.0、jsdom30.1.1及已装TypeScript6.0.3元数据核对；不安装/下载/build/package，不修改PATH/代理/时钟/安全配置。

'''
for name,value in start['artifacts'].items():report+=f'- {name}：`{value}`。\n'
report+='''
15项新目标源码语法/静态解析后先冻结cold-source.sha256；includes P/A/B各配置与测试、精确resolver/fixture、同步门面、原生setup/controller/safe reporter/审计/verify。MJS/TS/PowerShell解析、零import零JSX、目标/未知query/单包根/无预载/不使用manual mock核对通过。普通静态谓词首错known_canonical_id_missing来自五字符Vite包装误切六，首次resolver/verify和安全错误保留；改为精确五字符后通过。当时worker/fixture/loader/main均0，**普通静态修正1**与**额外前置worker0**分别统计。

04:08接单后至15:15可见控制返回有长聊天/控制空档，期间缺少连续检查点，不能宣称持续工作或外部角色状态。没有本轮目标后台运行；用户“继续”后重读同版control，记录限制并重设检查点，恢复静态准备。动态P于15:18、A于15:19，实际进程耗时按各process.json列出，不把整段聊天间隔当目标耗时。系统时钟未修改。

只读子任务review_test_handoff给出规范ID、importer缺失与单层Vite包装、.tsx零JSX建议，未执行目标或获准写入；由父任务采纳并独立静态核对。最终当前源码复核回执未取得，最后工具状态pending_init，父任务中断；只把已收到的静态信息作为输入，不冒称子任务验收或持续运行，见subagent-read-only-receipt.json。

旧成功27独立、outbox42/setting/PATH关闭、R4/R4-R1/R4-R2及D15/D15-R1材料只读沿用，不复跑或加入本轮passed统计。新P只1个工具前置验证，UI节点实际执行0、A执行尝试1且blocked，兼容0、产品0/8、辅助0/4。

## 原24项完整验收映射

P不替代UI/设备验收。矩阵120 ID/12字段/原前11列保持；B仍0 passed/1 failed/19 blocked/4 not_run，A64 passed、C20/D12 not_run保持。原完整要求、已有部分证据、本轮和缺口逐项如下。

'''
for row in cases:
    cid,_,source,layer,env,mode,pre,inp,steps,expected,risk,state=row
    sec=re.search(r'### '+re.escape(cid)+r' — .*?\n(.*?)(?=\n### |\n## |\Z)',old,re.S).group(1)
    prior=re.search(r'^- 已有历史部分：(.*)$',sec,re.M).group(1)
    gap=re.search(r'^- 具体缺口与层级：(.*)$',sec,re.M).group(1)
    new='not_run；A在正文前硬限后停止B/恢复/公开余项/兼容/Windows。'
    if cid=='P4B-UI-02':
        prior+='；R4-R2同Router取消加载安全reject、有效加载成功，无alert，原1失败/3通过，未关闭。'
        new='P工具前置1passed：真实默认loader两并发+随后3/3safe reject、fixture1。全新A初始化硬限，正文/main均0、四断言not_run；Bnot_run。'
        gap='持续导入故障已验证，但冷main有效请求/活跃Router错误槽/局部DOM隔离未验证；恢复/健康切换/状态保持及Windows chunk/session持久化全部未执行，不关闭LAZY-001。'
    report+=f'''### {cid} — {state}

- 来源/风险/层/环境/方式：{source} / {risk} / {layer} / {env} / {mode}。
- 前置：{pre}。
- 输入：{inp}。
- 操作：{steps}。
- **完整原预期**：{expected}。
- 已有历史部分：{prior}
- 本轮新增：{new}
- 具体缺口与层级：{gap}
- 当前状态：`{state}`；整体要求未满足不标passed。

'''
report+='''## 资源、格式核对和交接

P无main/Router实例/DOM资源创建，只导入真实模块并调用默认loader；P CLI3920自然exit0、登记worker19592已结束。A在正文前没有创建root/bridge订阅/Router观察/DOM/global/console spy，所以没有伪造unmount或cleanup事件；CLI15796硬限定向结束、自有worker16464结束。worker自己的exit事件缺失，具体exit code/机制unknown，父退出码不复制给worker。控制器身份来自创建句柄和即时journal parent，未用祖先猜测或总进程数阈值。

事后Get-Process确认这四个已登记PID不存在；系统Win32_Process枚举抛CimException，enumerationVerified=false，空列表不能等同全树零残留。完整历史后代未核实，范围限制明确；不全局杀Node/Electron/Maris/Python。没有建立外部C12-R4-R3 profile/session/db/窗口/监听，Windows设备行为不能从测试进程退出推导。

新r4-r3/cache经绝对专属边界/no-reparse核对清理1个缓存文件，目录已不存在；所有首次源码、worker/controller/resolver journal、双流、JSON和静态首错保留。旧包、旧缓存/资料、真实AppData不读写。没有Docker/PG/OpenClaw/微信V002/DeepSeek/provider或用户点击要求。

最终r4-r3-delivery.py复核544输入：除tester、旧主报告/人工清单追加、矩阵B备注四项外保持；受验源389/out140/resources67、固定包/fuses、7包元数据及15冻结源码保持。矩阵120唯一ID/12列/前11列/全部原状态/B外字节、旧文档原字节prefix保持；37项旧R2交付里除四个本轮允许更新的共享文档外33保持，不声称旧37整体仍同摘要。

只读Git staged/diff-check与新增全文件行尾扫描分列：历史R2 controller行158尾随空格保持不修改；本轮新增源/报告及追加段独立扫描，不拿tracked-only检查代替新文件格式检查。准确实际计数和新交付摘要见end-audit.json、delivery-verification.json、delivery.sha256。

交**blocked / finished**并停止，供总控review。P持续导入验证已完成；A正文前硬限和初始化原因、全部业务断言及Windows尚未解决。后续由总控依据首次阶段裁定，本角色不使用额外worker盲重跑、不改产品/依赖或Git、不建下一Prompt、不进入P4-C/D、不宣布总控接受。
'''
(ROOT/REPORT).write_text(report,encoding='utf-8',newline='\n')
appendix='''

## C12-R4-R3 持续导入复验追加（2026-10-03）

- [R3报告](phase-4-c12-r4-r3-persistent-import-windows-report.md)：blocked / finished；P工具前置1 passed，真实默认loader两并发及随后3/3safe reject，零import ESM求值1/精确映射1；不是网络chunk404或UI通过。
- 全新A首次停在worker_start/journal_ready，正文/main/fixture/loader均0，CLI14595ms硬限定向收口；无runner JSON，四原断言not_run，不编造failed产品节点。B、恢复、兼容和Windows未执行，产品0/8、辅助0/4。
- 没有明确纯工具配置错误，不消耗额外前置worker盲重试；原P/A首次材料完整保留，LAZY-001/UI-02/P4-B未关闭，无新增产品缺陷。已登记CLI/worker结束，完整系统后代枚举CimException保持unverified。
- 原24项完整预期/历史保持，普通静态映射修正1与目标更正0分列；用户继续后的长可见性空档如实记录。交总控review后停止，不自动续跑。
'''
for name in ['docs/testing/phase-4-c12-windows-shell-report.md','docs/testing/phase-4-c12-manual-checklist.md']:
    with (ROOT/name).open('ab') as f:f.write(appendix.encode('utf-8'))
note='''
#### C12-R4-R3 持续导入最新状态备注（2026-10-03）

- [R3完整报告](phase-4-c12-r4-r3-persistent-import-windows-report.md)：P工具注入1 passed，默认loader两并发+随后3/3 safe reject、fixture1、精确映射1，不计UI通过。A首次在正文前初始化硬限，journal只worker_start/journal_ready，main/fixture/loader0、四原断言not_run；无runner JSON，不伪造failed业务节点。
- B/独立恢复/剩余公开/开发兼容/Windows均not_run，产品0/8、辅助0/4、真实网络注入0；LAZY-001不关闭，无新增产品缺陷。原B0 passed/1 failed/19 blocked/4 not_run及所有原要求保持，A64/C20/D12保持。
- 首次材料保留；已登记CLI/worker结束、完整系统后代枚举未核实；额外前置worker/目标重试0，普通静态修正1。交blocked / finished等总控针对正文前初始化阶段裁定，不自动扩大或重跑。

'''
b=(ROOT/MATRIX).read_bytes();assert b.count(b'### 5.3')==1
(ROOT/MATRIX).write_bytes(b.replace(b'### 5.3',note.encode('utf-8')+b'### 5.3',1))
print('R3 report, first-run classification and 24 complete mappings delivered; no new target')
