"""Read only first-run evidence, produce the authorized report and appendices once."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[3];OWN=ROOT/'tests/independent/desktop/evidence/r4-r2'
REPORT='docs/testing/phase-4-c12-r4-r2-cold-entry-windows-report.md'
MATRIX='docs/testing/phase-4-modular-agent-host-test-matrix.md'
assert not (ROOT/REPORT).exists(),'handoff_once'
def load(name):return json.loads((OWN/name).read_text(encoding='utf-8-sig'))
def save(name,value):(OWN/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
events=[json.loads(l) for l in (OWN/'cold-trace/worker.journal.jsonl').read_text(encoding='utf-8').splitlines()]
process=load('cold-trace/process.json');result=load('cold-trace/result.json');start=load('start-audit.json')
assert [e['seq'] for e in events]==list(range(1,len(events)+1))
assert process['rootExitCode']==1 and process['mainImportRequests']==1 and result['numFailedTests']==1
assert len({(e['pid'],e['parentPid']) for e in events})==1
def stage(name):return [e for e in events if e['stage']==name]
assert len(stage('virtual_factory_throw'))==1 and len(stage('router_created'))==1
assert len(stage('loader_enter'))==2 and stage('loader_aborted')[0]['attemptSeq']==1
rejected=stage('loader_rejected')[0];resolved=stage('loader_resolved')[0]
assert rejected['attemptSeq']==1 and rejected['aborted'] and rejected['safeModuleCode']
assert resolved['attemptSeq']==2 and not resolved['aborted']
terminal=stage('router_state')[-1];dom=stage('observation_finished')[0];cleanup=stage('dom_globals_restored')[0]
assert terminal['targetMatch'] and terminal['navigation']=='idle' and terminal['errorCount']==0
assert not dom['alertShown'] and all(dom[k] for k in ['shellPresent','navigationPresent','agentPanelPresent'])
assert cleanup['rootEmpty'] and cleanup['globalsRestored'] and cleanup['activeBridgeSubscriptions']==0
facts={'caseId':'R4-R2-UI-02-COLD-TRACE','classification':'cancelled_attempt_rejected_live_attempt_resolved_no_active_error',
 'events':len(events),'mainResolved':True,'actReturned':True,'routerInstances':1,'factoryHits':1,
 'attempts':[{'routerSeq':1,'attemptSeq':1,'aborted':True,'terminal':'rejected','safeModuleCode':True},
             {'routerSeq':1,'attemptSeq':2,'aborted':False,'terminal':'resolved'}],
 'activeRouterTerminal':terminal,'dom':dom,'cleanup':cleanup,
 'originalFourAssertions':{'alert':'failed','shell':'passed','navigation':'passed','agentPanel':'passed'},
 'additionalFailedAssertions':['active target error slot','unaborted active attempt safely rejected'],
 'additionalPassedAssertions':['factory hit','router initialized','navigation idle','root empty','globals restored','bridge subscriptions zero'],
 'productDefectNewlyGraded':False,'lazy001ClosureSuggested':False,'secondImportResolutionMechanism':'unverified',
 'B':'not_run','recovery':'not_run','compatibility':'not_run','windows':'not_run'}
save('propagation-summary.json',facts)
save('node-index.json',{'independentExecuted':1,'passed':0,'failed':1,'nodes':result['nodes'],
 'B':'not_run','recoveryExecuted':0,'executorCompatibilityExecuted':0,
 'vitestCliStarts':1,'actualMainRequests':1,'preMainCorrectionWorkers':0,
 'nativeStaticFormatCorrections':1,'productStarts':0,'auxiliaryStarts':0,'chunkRequestInjections':0})
baseline=load('baseline.json');cases=[r for r in baseline['cases'] if r[1]=='B'];assert len(cases)==24
old=(ROOT/'docs/testing/phase-4-c12-r4-r1-observation-windows-report.md').read_text(encoding='utf-8-sig')
report=f'''# P4-C12-R4-R2 冷入口传播复验与Windows验收报告

交付：**blocked / finished**。既有独立测试智能体、唯一负责人；依据 control `2026-10-03T03:16:00+08:00` 和 [R2任务卡](../coordination/prompts/p4-c12-r4-r2-cold-entry-tester.md)。全部使用虚拟输入。A首次失败后停止，B及后续未执行；LAZY-001/UI-02/P4-B未关闭，没有新增已定级产品缺陷。最终验收与后续接线裁定属于总控。

## 结果与明确传播阶段

本次取得了冷入口的完整阶段。实际main与React act均返回，观察门面由main正常依赖链首次加载。**同一Router实例1发起目标loader两次：尝试1先取消再以安全错误拒绝，尝试2未取消并成功resolve；活跃目标最终initialized=true/navigation=idle/errors=0，DOM无alert。** 被取消尝试的reject不能补签为当前Router错误。因此旧“5秒无提示”的上游关系已在本次条件下定位到取消/成功尝试分离，仍不能完成实际有效请求的故障隔离验收。

该链路只解释本轮为什么没有有效目标错误，不能反推旧R4/R4-R1或D15-P3的根因。第二次原始import为何resolve、并发mock缓存/调用上下文是否影响其结果，本轮没有对应内部事件，保持unverified。没有修改产品或原mock为另一种故障，不将取消请求分类为产品边界失败。默认索引/StrictMode等导航触发因素未逐个取证，也不指定某一因素为第二次调用根因。

| 节点 | 条件和结果 | 实际次数 |
| --- | --- | --- |
| A `R4-R2-UI-02-COLD-TRACE` | 同步ESM透传观察、空hash冷main、默认内置loader、原页面factory throw；0 passed/1 failed，真实CLI exit1 | CLI1 / worker1 / main1 |
| B `R4-R2-UI-02-COLD-PUBLIC` | 独立配置/缓存、直接真实Router、同四断言；**not_run**，不复用A数据补签 | 0 |
| 独立恢复与剩余公开行为 | 瞬时/持续失败、retry/切换/状态保持等 **not_run** | 0 |
| 开发兼容 | lazy八项及Shell/composition **not_run**，不计独立结果 | 0 |
| Windows | 产品0/8，辅助0/4，真实请求注入0；设备/会话条件 **not_run/unverified** | 0 |

## A与B的启动条件及观察扰动

| 条件 | A实际核对 | B准备状态 |
| --- | --- | --- |
| 冷入口 | setup只原生fs/path/url，测试静态import仅vitest/jsdom/React；无Router、module-routes、contribution或页面预载。seq7 main_import_enter后seq8 facade_loaded | 源码相同冷入口条件，尚未执行 |
| 产品链 | 仓库实际main→StrictMode DesktopApp→实际compileRegistry/contribution/Host交集→Shell/实际Router；没有替代路由或Shell | 同一真实入口，未执行 |
| Host与URL | 固定虚拟daily_finance1.0.0、canonical Profile、API摘要与实际贡献核对；初始空hash，未改#/daily入口 | 同样虚拟摘要/空hash，未执行 |
| 页面故障 | 原DailyFinancePage规范模块mock只增加factory次数日志并throw固定VIRTUAL_CHUNK_UNAVAILABLE；默认内置动态import与原生产route.loader不替换 | 同factory，未执行 |
| Router映射 | 精确裸react-router→新同步ESM门面；独立__c12_real_router→固定真实包；subpath不进门面，配置解析条件默认相同；没有async vi.mock/importOriginal | 裸Router直接相同固定真实包，没有门面或包装 |
| 导出/身份 | export*透传真实Context与其他导出；同步Reflect.apply原factory，返回原Router对象；实际日志确认factory函数、创建/订阅/合法Shell渲染 | 静态直连已核对，动态未验证 |
| 原loader语义 | 同route对象、this/args；返回原Promise身份；旁路then只记录终态，不另造业务Promise、不吞原错误 | 不加载loader包装 |
| 观察扰动 | **目标loader函数身份改变、Promise旁路监听、Router只读订阅、同步journal/fsync、React有界轮询**。未包装dispose/navigate/revalidate，未追加导航或retry | 只有原生journal/factory/DOM/cleanup记录，无Router遥测 |
| 活跃关系 | 按Router1/attempt1、2区分；signal.abort即时记录；Router状态与DOM关联。没有新Router/旧实例混签；dispose未额外包装，因此没有伪造dispose阶段 | 不读取或回填A的遥测 |

物理React/DOM/Router仅同一R5普通依赖alias根，JSX runtime走同一React根；真实Context透传且Shell与实际Router共同渲染。单包依据为静态alias/物理包元数据与本次运行链；没有枚举运行时全模块对象或声称额外第二实例检测。门面运行前标记动态未验证，本次确已加载并取得真实Router/loader终态，原静态文件仍保留not_run历史，动态结果单列。

## 首次持久时间线

以下相对时间从worker setup开始，不能与CLI开始混用。worker PID28308、parent自有CLI30912；{len(events)}条连续seq。控制器活动读采用FileShare.ReadWrite且仅完整newline，首次双流、JSON、worker/controller journal均保留。

| seq | 阶段 | worker相对ms | 安全证据 |
| --- | --- | --- | --- |
'''
detail={
 'worker_start':'原生日志先于模块收集', 'journal_ready':'同步落盘/fsync', 'hoisted_ready':'factory计数器准备',
 'body_enter':'测试正文开始', 'virtual_dom_bridge_ready':'空hash/虚拟bridge', 'act_enter':'单独进入act',
 'main_import_enter':'原import Promise请求', 'facade_loaded':'正常依赖链取得真实Router函数',
 'main_import_resolved':'原main Promise已返回', 'root_created':'实际desktopRoot存在',
 'router_create_enter':'实际Router1开始创建', 'router_created':'原Router对象返回',
 'router_subscribed':'只读观察订阅', 'virtual_factory_throw':'原factory真实命中1',
 'act_return':'React act另行返回', 'assertions_enter':'原四断言及关联前置开始',
 'assertions_finished':'四软断言均执行；任一失败仍使节点failed',
 'root_unmount_enter':'卸载实际root', 'root_unmounted':'实际卸载完成',
 'observer_unsubscribed':'取消Router观察', 'dom_globals_restored':'root空/全局恢复/bridge订阅0',
 'body_finished':'finally完成；不等于节点通过'}
for event in events:
    name=event['stage'];extra=detail.get(name,'')
    if name.startswith('loader_'):extra=f"Router{event['routerSeq']}/attempt{event['attemptSeq']}；aborted={event['aborted']}"+(f"；safeModuleCode={event['safeModuleCode']}" if 'safeModuleCode'in event else '')
    if name=='router_state':extra=f"active={event['active']} initialized={event['initialized']} navigation={event['navigation']} targetMatch={event['targetMatch']} errors={event['errorCount']}"
    if name in ['dom_state','observation_finished']:extra=f"fault={event['mockHits']} alert={event['alertShown']} Shell/nav/Agent={event['shellPresent']}/{event['navigationPresent']}/{event['agentPanelPresent']} 活跃目标错误={event['activeTargetError']}"
    report+=f"| {event['seq']} | {name} | {event['elapsedMs']:.3f} | {extra} |\n"
mainMs=stage('main_import_resolved')[0]['elapsedMs']-stage('main_import_enter')[0]['elapsedMs']
actMs=stage('act_return')[0]['elapsedMs']-stage('act_enter')[0]['elapsedMs']
report+=f'''
main导入{mainMs:.3f}ms、act总{actMs:.3f}ms，分别具备enter/terminal；没有main/act挂起。loader1 reject时已aborted=true；loader2 resolve后同实例目标match/idle/errors0，再关联DOM无alert。原factory不能精确归因到两个并发import的哪一个内部上下文，但route.loader1安全reject与route.loader2成功终态均由原Promise直接取得。

条件轮询以5000ms截止，每次使用min(20ms,remaining)有界计时。实际收口测量 **{dom['observationMs']:.3f}ms**，末次act/调度尾差 **{dom['observationMs']-5000:.3f}ms** 如实保留；没有把时限增大或执行固定五秒等待。CLI实际 **{process['durationMs']}ms**、测试 **{result['nodes'][0]['durationMs']:.3f}ms**，均在15秒/10秒上限内，无timeout/强制收口。计时尾差属于本轮观察限制，不改原首次值，也不以此延长或重跑。

## 原四断言及失败分类

| 要求 | 本轮实际执行 | 结果 |
| --- | --- | --- |
| 新前置：factory命中 | count1、hits>0 | passed |
| alert含“页面暂时无法打开” | 原textContent断言，无alert，值undefined | **failed** |
| main.shell存在 | 原not.toBeNull断言 | passed |
| 模块导航存在 | 原not.toBeNull断言 | passed |
| 统一Agent面板存在 | 原not.toBeNull断言 | passed |
| 当前有效目标错误槽/安全code关联 | 同实例错误槽不存在 | failed |
| 当前未取消loader安全拒绝 | 仅拒绝attempt1已abort；attempt2成功 | failed |
| Router initialized/nav idle | 当前Router1 true/idle | passed |

原四断言用expect.soft使四项均实际运行；任一失败仍失败，没有改成采样代替断言。runner记录3个AssertionError：alert、活跃错误槽、未取消安全拒绝；测试1 failed。没有Error/stack/模块对象/URL/完整DOM/raw秘密写入观察记录；安全reporter在源头保存真实状态/数量/错误类型，原JSON无需事后篡改。stdout为安全runner_result一行78 bytes，stderr0，流完成且无需删敏行。

任务卡分类适用“loader已安全reject，但已取消请求不能当产品缺陷”。**当前故障请求前置未建立，产品局部错误UI结论unverified**。旧P1 LAZY-001未独立关闭；不新定级P0/P1，不推断产品错误映射或边界失效，不凭Shell存在宣布UI-02通过。

最小复现材料是冻结A源码、cold-source.sha256与首次cold-trace目录。实际调用为固定Node运行Vitest、配置r4-r2-cold-trace.config.mjs、phase=cold-trace；已用过单次预算，控制器拒绝已有结果目录，**此处只供只读审阅，不授权重跑**。预期必须由当前有效加载产生安全错误且保留四入口；实际有效加载成功而取消加载失败。问题级别为独立门禁阻塞，非新定级产品缺陷。

需要总控决定的是：在仍保留真实冷main、默认loader和原导入故障意义的前提下，怎样让未取消的实际请求稳定收到模拟故障，以及是否需要修正测试接线。并发mock内部解析机制保持待核实。不建议延时、预热、重打包或另一纯bootstrap任务，不自行指定或实现产品返修。

## 输入、预算与旧材料

起点 **507/507 matched**，0 mismatch/missing，staged=0；SHA-256 `{start['manifest_sha256']}`。仓库新起点与历史R5源码390分开。只读受验根C:/MarisLazyR5/R5-20261002-222300：构建源389、out140、Python资源67逐项一致；EXE/asar/lock/fuses与任务固定值一致，Node24.21.0/Vitest5.0.2/React及React DOM19.3.0/Router8.4.0/jsdom30.1.1确认，Vite7.3.6/TypeScript6.0.3仅作为已装静态工具。

| 固定物 | SHA-256 |
| --- | --- |
'''
for name,value in start['artifacts'].items():report+=f'| {name} | {value} |\n'
report+='''
新冷入口源码11项先静态冻结（包括审计、setup、门面、A/B测试及配置、controller、安全reporter、verify）。MJS/TS/PowerShell解析、精确alias、防循环、相同真实包/React根与不预载核对通过。普通静态工具最初使用C:/绝对ESM import产生ERR_UNSUPPORTED_ESM_URL_SCHEME；首次源码/脱敏错误另存static-first-*，改file URL后静态通过。该普通静态工具没有Vitest、worker或main请求；它的格式修正1次与目标前额外worker预算0次分别记录。目标源码冻结后不变，A未修改/重跑，B无第三次main，目标前更正worker未使用。

此前成功27独立节点、outbox42及setting/PATH关闭证据沿用，不重新执行、不并入本轮计数。旧public/r1/r2/r3/r4/r4-r1、D15/D15-R1源码/报告/首次证据由起终快照核对，只读保持。总控D15-R1 finite complete属于输入，不计独立passed。

## 原24项完整映射

原120案例ID、12字段、前11列原要求保持。B整体仍0 passed/1 failed/19 blocked/4 not_run，A64 passed/C20与D12 not_run保持。下列原历史仅引用，不改写原失败、不将执行方正常EXE19门禁补成独立设备证据。

'''
for row in cases:
    cid,_,source,layer,env,mode,pre,inp,steps,expected,risk,state=row
    section=re.search(r'### '+re.escape(cid)+r' — .*?\n(.*?)(?=\n### |\n## |\Z)',old,re.S).group(1)
    prior=re.search(r'^- 已有历史部分：(.*)$',section,re.M).group(1)
    gap=re.search(r'^- 具体缺口与层级：(.*)$',section,re.M).group(1)
    new='not_run；A门禁失败，B/恢复/公开余项/兼容/Windows均停止扩大。'
    if cid=='P4B-UI-02':
        prior+='；R4-R1 factory1、5016ms无alert，Router终态未关联。'
        new='A一次0pass/1fail；main/act已完成，同Router两attempt：1 abort+safe reject，2未abort resolve，活跃idle/target match/errors0，无alert，Shell/nav/Agent三断言通过。'
        gap='有效请求故障前置未建立，LAZY-001不关闭；B未执行。独立恢复/健康切换/状态保持、真实Windows chunk与会话保持尚无证据。取消请求失败不能定级为新的产品缺陷。'
    report+=f'''### {cid} — {state}

- 来源/风险/层/环境/方式：{source} / {risk} / {layer} / {env} / {mode}。
- 前置：{pre}。
- 输入：{inp}。
- 操作：{steps}。
- **完整原预期**：{expected}。
- 已有历史部分：{prior}
- 本轮新增：{new}
- 具体缺口与层级：{gap}
- 当前状态：`{state}`；整项未满足时不标passed。

'''
report+='''## 资源、未执行范围和最终交接

真实desktopRoot已act unmount，rootEmpty/globalRestored/domClosed均true；观察Router订阅1次取消，signal旁路监听移除；bridge runtime/modules/subscribe各2，unsubscribe2/active0/settingsWrites0。StrictMode真实生命周期的两次外围读取不等于auth或provider重复调用。没有新增window/external/outbox/provider等端口或财务操作，也没有真实session内容读取。

CLI30912自然exit1、journal登记worker28308已结束、无timeout/强杀；worker自身exit事件没有落盘，具体worker exit code/方式unknown，不能复制父退出码。实际父子身份由创建句柄和journal验证，不用祖先PID猜测或精确总进程数门禁。之后Get-Process再次确认这两个PID已不存在；Win32_Process只读枚举抛CimException，childEnumerationVerified=false，空列表不能表示全树零残留。资源证据限这两个已登记对象及DOM/订阅，系统所有后代和历史全量枚举unverified；未再启动或全局结束任何进程。

产品0/8、辅助safeStorage Electron0/4、CDP注入0；没有建立C12-R4-R2外部profile/db/session、实际窗口/后端或测试监听。真实Windows chunk注入恢复、session持久化、CSP/秘密/恶意文本、generated drift、贡献严格结构余项、原生老化提示、Tray/closePolicy/单实例/毛毛状态均未执行。OS注销/重启、启动项、多屏/DPI/拔屏/系统主题/透明降级保持原人工not_run/unverified，不要求用户现在点击。

只清理经绝对专属边界/no-reparse核对的新r4-r2/cache，删除1个缓存文件、目录不存在；首次源码/双流/journal/JSON/静态首次错误均保留。Git仅只读staged/diff检查；无任何Git写操作。不修改产品、开发测试、依赖/lock/生成物/package/Forge/migration/冻结/control/overview/其他角色；不Docker/PG/OpenClaw/微信/DeepSeek/provider或系统配置、时钟、安全软件。

终点与交付复算由r4-r2-delivery.py独立读取首次证据：固定507仅tester/B备注/旧主报告与清单追加四路径获准变化，其余503精确不变；source389/out140/resources67与包/fuses保持，120唯一ID/12列/前11列/原全部状态/B外字节及旧文档原字节prefix保持。最终实际计数与交付哈希见evidence/r4-r2/end-audit.json、delivery-verification.json及delivery.sha256，以工具结果为准。

交付**blocked / finished**后停止。提交本报告、新增r4-r2测试/观察工具/首次证据、原文档追加、矩阵B备注及自身状态给总控review，等待精确接线裁定；不创建下一Prompt、调度其他角色、不自动续跑，不宣布总控接受或P4-B complete。
'''
(ROOT/REPORT).write_text(report,encoding='utf-8',newline='\n')
appendix='''

## C12-R4-R2 冷入口复验追加（2026-10-03）

- [R2独立报告](phase-4-c12-r4-r2-cold-entry-windows-report.md)：blocked / finished；A唯一一次0 passed/1 failed，B及后续not_run，LAZY-001未关闭。
- main/act完成，同一Router1的attempt1被取消后安全拒绝、attempt2未取消成功resolve，活跃目标idle/errors0，无alert；Shell/nav/Agent三断言通过，不能把取消错误补签为当前有效请求故障。
- 本次未建立活跃请求错误前置，不新增已定级产品P0/P1；第二次import解析原因仍unverified，交总控裁定测试接线。不继续延时/预热/重打包，不重跑首次结果。
- 产品0/8、辅助0/4、chunk注入0；系统枚举CimException明确未核实全树，已登记CLI/worker结束、真实root及订阅清理有记录。旧证据和24项原要求保持，人工条件不要求现在操作。
'''
for name in ['docs/testing/phase-4-c12-windows-shell-report.md','docs/testing/phase-4-c12-manual-checklist.md']:
    with (ROOT/name).open('ab') as f:f.write(appendix.encode('utf-8'))
note='''
#### C12-R4-R2 冷入口最新状态备注（2026-10-03）

- [R2完整报告](phase-4-c12-r4-r2-cold-entry-windows-report.md)：A唯一一次0 passed/1 failed；main/act完成，Router1目标attempt1先abort后安全reject，attempt2未abort且resolve，活跃target match/idle/errors0，DOM无alert，Shell/nav/Agent三断言通过。取消错误不补签活跃目标；LAZY-001不关闭，无新增已定级产品缺陷。
- B无门面节点及恢复/剩余公开/兼容/Windows均not_run；产品0/8、辅助0/4、实际注入0，旧成功证据只读沿用。B仍0 passed/1 failed/19 blocked/4 not_run，A64 passed/C20/D12 not_run及所有原预期保持。
- 原四要求全部保留，首次A/旧R4/R4-R1与D15材料不改；真实root、观察、bridge已收口，已登记CLI/worker结束；系统枚举权限错误保持unverified。交blocked / finished等总控针对有效请求故障接线裁定，不自动续跑。

'''
b=(ROOT/MATRIX).read_bytes();assert b.count(b'### 5.3')==1
(ROOT/MATRIX).write_bytes(b.replace(b'### 5.3',note.encode('utf-8')+b'### 5.3',1))
print('R2 report, 24 complete mappings and append-only handoff prepared; no target execution')
