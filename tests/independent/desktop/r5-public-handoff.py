"""Write the authorized stopped-run report and appendices without running targets."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[3]
OWN = ROOT / 'tests/independent/desktop/evidence/r5-public'
REPORT = 'docs/testing/phase-4-c12-r5-public-windows-report.md'
MATRIX = 'docs/testing/phase-4-modular-agent-host-test-matrix.md'
assert not (ROOT / REPORT).exists(), 'handoff_once'


def load(name):
    return json.loads((OWN / name).read_text(encoding='utf-8-sig'))


def journal(name):
    return [json.loads(line) for line in (OWN / 'cold' / name).read_text(encoding='utf-8').splitlines()]


def save(name, data):
    (OWN / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


events = journal('worker.journal.jsonl')
controls = journal('controller.journal.jsonl')
configs = journal('config.journal.jsonl')
process = load('cold/process.json')
start = load('start-audit.json')
baseline = load('baseline.json')
assert [event['stage'] for event in events] == ['worker_start', 'journal_ready', 'test_module_enter', 'jsdom_import_enter']
assert process['mainImportRequests'] == process['fixtureEvaluations'] == 0 and process['limitStage'] == 'initialization'
assert process['rootExited'] and process['workerExited'] and process['timedOut']
assert not (OWN / 'cold/result.json').exists() and not (OWN / 'cold/resolver.journal.jsonl').exists()
root_start = next(event['elapsedMs'] for event in controls if event['stage'] == 'root_started')
termination = next(event['elapsedMs'] for event in controls if event['stage'] == 'deadline_termination_enter')
exit_checked = next(event['elapsedMs'] for event in controls if event['stage'] == 'exit_checked')
finished = controls[-1]['elapsedMs']
save('node-index.json', {'nodeId': 'R5-PUBLIC-UI-02-COLD', 'invocationStatus': 'initialization_blocked',
    'runnerJsonProduced': False, 'testNodesExecuted': 0, 'passed': 0, 'failed': 0,
    'cliStarts': 1, 'forkWorkers': 1, 'mainRequests': 0, 'fixtureEvaluations': 0,
    'originalFourAssertions': 'not_run', 'extraPreMainWorkers': 0, 'targetRetries': 0,
    'ordinaryStaticPredicateCorrections': 1, 'recovery': 'not_run', 'compatibility': 'not_run',
    'remainingPublic': 'not_run', 'windows': 'not_run', 'productStarts': 0, 'auxiliaryStarts': 0, 'chunkInjections': 0})
save('public-summary.json', {'classification': 'initialization_blocked', 'lastPersistentStage': 'jsdom_import_enter',
    'jsdomTerminal': 'not_received', 'reactImport': 'not_entered', 'body': 'not_entered',
    'faultSourceValid': 'not_evaluated', 'publicTargetResult': 'not_evaluated',
    'sourceMappingRecords': 0, 'workerEvaluationRecords': 0, 'currentHash': 'not_sampled',
    'fourAssertions': {name: 'not_run' for name in ['safeAlert', 'shell', 'moduleNavigation', 'unifiedAgentPanel']},
    'safetyAssertions': 'not_run', 'uiCleanup': 'not_run_resources_not_created', 'internalRouterAndAbort': 'not_collected',
    'controllerInitializationMs': termination - root_start, 'controllerShutdownToExitCheckedMs': exit_checked - termination,
    'controllerTotalMsIncludingReporting': finished, 'newProductDefects': 0, 'lazy001ClosureSuggested': False})

report = f'''# P4-C12-R5-PUBLIC 公开冷入口与Windows独立验收报告

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
'''
for event in events:
    report += f"| {event['seq']} | {event['stage']} | {event['elapsedMs']:.3f} |\n"
report += '\n| controller seq | 阶段 | controller相对ms |\n| --- | --- | --- |\n'
for event in controls:
    report += f"| {event['seq']} | {event['stage']} | {event['elapsedMs']} |\n"
report += f'''
config四条实际记录为config_evaluation_enter/object_ready/resolved/server_configured。config PID{configs[0]['pid']}、parent{configs[0]['parentPid']}；worker PID{process['workerPid']}、parent{process['rootPid']}与创建CLI对应。空stdout/stderr不是停点依据，以上即时append/fsync的记录才是依据。

| 冻结阶段 | 上限 | 本次实际 |
| --- | --- | --- |
| root启动→body_enter | 15000ms | root启动{root_start}ms，初始化收口{termination}ms，差{termination-root_start}ms；没有body_enter |
| 正文 | 10000ms | 未进入，main/act各自enter/terminal均未出现 |
| UI条件观察 | 5000ms | 未进入，不使用固定睡满或补延时 |
| 自有收口 | 2000ms | deadline→exit_checked {exit_checked-termination}ms；没有UI cleanup_enter，不宣称finally执行 |
| 总体CLI含报告开销 | 30000ms | process.json记录{process['durationMs']}ms；controller_finished实测{finished}ms，区别保留 |
| Vitest函数外层 | 12000ms，正文+finally | test正文未启动，未把12秒写成业务等待 |

父CLI实际exit {process['rootExitCode']}，timedOut=true/forcedRootTermination=true/forcedWorkerTermination=false。登记worker已退出，其自身exit事件0，exit code/机制unknown；不复制父退出码。双流独立收口完成，stdout/stderr原始与保存字节均0。journal完整无半行、evidenceReadUnverified=false。首次六文件已冻结在cold-first.sha256。

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

新起点**{start['matched']}/{start['entries']} matched**，0 mismatch/missing、staged0；清单SHA `{start['manifest_sha256']}`。既有P的52项交付与15项冻结源码只读全部匹配，源389/out140/Python资源67逐项匹配，EXE/asar/lock/fuses固定；7个普通依赖物理元数据与Node24.21.0/TypeScript6.0.3核对，没有重跑P或D16两次实验。

- EXE：`{start['artifacts']['apps/desktop/out/Maris-win32-x64/Maris.exe']}`。
- app.asar：`{start['artifacts']['apps/desktop/out/Maris-win32-x64/resources/app.asar']}`。
- lock：`{start['artifacts']['pnpm-lock.yaml']}`。

10项新目标源码在MJS/TSX/Python/PowerShell解析与静态谓词后冻结；静态首次r5_public_main_budget是检查器文本正则把擦除的typeof import与实际动态import一起计数，改为AST CallExpression后确认实际main导入仅1。首次verifier/test与脱敏错误保留。**普通静态谓词更正1、额外前置worker0、目标重试0**；普通语法检查进程不是Vitest worker或业务节点。

只读子任务r5_public_contract_review检查合同/新工具，指出局部采样、四断言排序、安全调用、阶段门禁、权限未知、原生退订及异常收口记录问题；父任务在首次目标前修正并静态核对/冻结。最后完整newline收口读取修正由父任务解析核对；子任务意见不是动态验收，没有写入或执行目标，回执见subagent-read-only-receipt.json。

本轮初始化停止没有收到jsdom rejected或其他原Error；最后脱敏失败证据是controller的initialization deadline。已采用分段await、原生即时日志、固定普通依赖、独立worker/cache和边界时限，仍未取得terminal。**没有明确纯工具配置错误**，unknown初始化超时不满足定向更正授权。首次材料/输入和资源收口保留，但不使用额外worker、不延时、不清OS缓存、不改产品/依赖/包、不新建诊断任务。由总控决定下一步；旧A原因unknown与本次B阶段证据分开。

## 原24项完整映射

矩阵120唯一ID/12字段/原前11列保持；A64 passed、C20/D12 not_run保持；B仍0 passed/1 failed/19 blocked/4 not_run。原失败历史不被初始化阻塞覆盖或洗成通过；各项完整原预期、已有证据、本轮事实和剩余缺口如下。

'''
old = (ROOT / 'docs/testing/phase-4-c12-r4-r3-persistent-import-windows-report.md').read_text(encoding='utf-8')
cases = [row for row in baseline['cases'] if row[1] == 'B']
assert len(cases) == 24
for row in cases:
    cid, _, source, layer, env, mode, pre, inp, steps, expected, risk, state = row
    section = re.search(r'### ' + re.escape(cid) + r' — .*?\n(.*?)(?=\n### |\n## |\Z)', old, re.S).group(1)
    prior = re.search(r'^- 已有历史部分：(.*)$', section, re.M).group(1)
    gap = re.search(r'^- 具体缺口与层级：(.*)$', section, re.M).group(1)
    if cid == 'P4B-UI-02':
        prior += '；R4-R3的P默认loader三次安全拒绝，A正文前阻塞、旧B未执行；D16两次实验不计界面通过。'
        gap = '本轮公开B独立启动，但未进入main/来源和局部DOM采样；初始隔离、恢复/健康切换/订阅与会话保持及真实Windows chunk/session均未验收。内部Router/abort按本轮合同未采集，不作为启动门禁；LAZY-001未关闭。'
    report += f'''### {cid} — {state}

- 来源/风险/层/环境/方式：{source} / {risk} / {layer} / {env} / {mode}。
- 前置：{pre}。
- 输入：{inp}。
- 操作：{steps}。
- **完整原预期**：{expected}。
- 已有历史部分：{prior}
- 本轮新增：公开B初始化限停止，最后jsdom_import_enter，正文/main/fixture0、四断言not_run；该项恢复/公开余项/兼容/Windows未执行。
- 具体缺口与层级：{gap}
- 当前状态：`{state}`；完整要求未满足不标passed。

'''
report += '''## 资源、终点核对和交接

自己的创建句柄/实时journal父子证明与登记worker句柄用于定向收口；worker身份与CLI实际对应。事后Get-Process明确NoProcessFoundForGivenId确认两登记PID不存在，访问失败不会当不存在；没有全局kill或精确进程数门禁。完整系统/历史后代枚举未执行、未核实；限制保留，不把父exit复制给worker。

native configLoader没有配置临时文件；本轮cache没有生成，经过绝对专属边界/no-reparse核对确认不存在，deletedFiles=0。首次六文件、10冻结源码、静态首次材料及所有同步journal/双流保留。没有外部Windows根/profile/会话/db/监听，没有产品或辅助Electron、Docker/PG/OpenClaw/微信/DeepSeek/provider操作，也不要求用户现在点击、注销、改主题或启动项。

终点由r5-public-delivery.py逐项复核当前638输入，除tester、旧主报告/人工清单追加、矩阵B备注四项外必须保持；受验源389/out140/resources67、固定包/fuses/7元数据/10冻结源码保持。原R3交付52项中48项保持、4个本轮授权共享文档更新，原15项源码保持；D16交付39项保持。矩阵120唯一ID/12字段/前11列/全部状态/B外字节及旧文档原字节prefix保持。实际结果见end-audit.json、delivery-verification.json及delivery.sha256，不写自引用摘要。

Git只读staged/diff-check与新全文件及授权新段的行尾扫描分列，旧R2历史空格不改；不以tracked-only检查代替新增格式核对。最终只到blocked / finished，供总控review。卡点是本轮具体jsdom import缺少terminal，根因unknown；需要总控根据固定源码/首次阶段裁定，而不是本角色盲重跑/延时或自动派新任务。公开B授权已独立使用，不再回到A先通过的旧门禁。
'''
(ROOT / REPORT).write_text(report, encoding='utf-8', newline='\n')
appendix = '''

## C12-R5-PUBLIC 公开冷入口追加（2026-10-04）

- [R5-PUBLIC报告](phase-4-c12-r5-public-windows-report.md)：blocked / finished；公开B独立启动，不依赖A。唯一新CLI/worker停在jsdom_import_enter缺少terminal，initialization_blocked；正文/main/fixture0，四断言not_run，没有runner JSON或产品failed节点。
- 主进程启动→初始化收口14953ms，process15113ms、controller_finished15120ms；正文/观察/UI cleanup未开始，自有CLI/登记worker已结束。worker exit code unknown，完整系统后代未核实；缓存未生成/未删除，首次六文件及10源码保留。
- 来源与公开结果都未计算，P旧成功只读不补签；恢复/兼容/剩余公开/Windows停止，产品0/8、辅助0/4、网络chunk注入0。普通静态谓词更正1、额外worker/目标重试0；根因unknown不作为工具重试授权。
- 原24项要求与状态保持，LAZY-001/UI-02/P4-B未关闭。只交总控review，不改产品/依赖/Git、不自动启动A或新任务。
'''
for name in baseline['append_files']:
    with (ROOT / name).open('ab') as file:
        file.write(appendix.encode('utf-8'))
note = '''
#### C12-R5-PUBLIC 独立公开最新备注（2026-10-04）

- [本轮报告](phase-4-c12-r5-public-windows-report.md)：公开B不依赖A，首次停在jsdom_import_enter未返回，初始化阻塞；正文/main/fixture0、来源与公开结果未计算，四断言not_run，没有runner JSON，不伪造failed节点或从P补签。
- 恢复/开发兼容/公开余项/Windows均not_run；产品0/8、辅助0/4、真实chunk注入0，LAZY-001/UI-02/P4-B未关闭。原120ID/12列/完整预期和原B0 passed/1 failed/19 blocked/4 not_run保持，A64/C20/D12保持。
- 固定源码先冻结，首次材料保留；CLI与登记worker已结束，worker exit code和完整历史后代未知。普通静态谓词更正1、额外worker/重试0；unknown初始化原因不授权盲重跑，交blocked / finished供总控review。

'''
data = (ROOT / MATRIX).read_bytes()
assert data.count(b'### 5.3') == 1
(ROOT / MATRIX).write_bytes(data.replace(b'### 5.3', note.encode('utf-8') + b'### 5.3', 1))
print('R5-PUBLIC stopped-run report and 24 full mappings delivered; no new target')
