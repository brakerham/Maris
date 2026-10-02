"""C12-R4 failed-original gate handoff; no target executions."""
from pathlib import Path
import json,re,hashlib,subprocess,mmap,sys
ROOT=Path(__file__).resolve().parents[3];OWN=ROOT/'tests/independent/desktop/evidence/r4';EXT=Path('C:/MarisLazyR5/R5-20261002-222300/workspace')
REPORT='docs/testing/phase-4-c12-r4-lazy-windows-report.md';MATRIX='docs/testing/phase-4-modular-agent-host-test-matrix.md';ROLE='docs/coordination/agents/tester.md';OLD='docs/testing/phase-4-c12-windows-shell-report.md';MANUAL='docs/testing/phase-4-c12-manual-checklist.md'
def sha(b):return hashlib.sha256(b).hexdigest()
def save(name,data):(OWN/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rows(b):return [[c.strip() for c in l.strip().strip('|').split('|')] for l in b.decode('utf-8-sig').splitlines() if re.match(r'^\| P4[ABCD]-',l)]
def nodeindex():
    j=json.loads((OWN/'original-lazy/result.json').read_text(encoding='utf-8-sig'));nodes=[{'name':a['fullName'],'status':a['status']} for f in j['testResults'] for a in f['assertionResults']]
    assert len(nodes)==1 and nodes[0]['status']=='failed';save('node-index.json',{'independent_executed':1,'passed':0,'failed':1,'nodes':nodes,'executor_compat_executed':0,'new_recovery_cases_executed':0,'product_starts':0,'auxiliary_electron_starts':0})
if sys.argv[1]=='prepare':
    assert not (ROOT/REPORT).exists(),'prepare_once'
    baseline=json.loads((OWN/'baseline.json').read_text(encoding='utf-8'));cases=[r for r in baseline['cases'] if r[1]=='B'];nodeindex()
    readpaths=['tests/independent/desktop/r3-remaining.test.tsx','apps/desktop/src/renderer/main.tsx','apps/desktop/src/renderer/module-routes.tsx','apps/desktop/src/shell/Shell.tsx']
    save('readonly-source-observation.json',{'source_sha256':{p:sha((ROOT/p).read_bytes()) for p in readpaths},'entry':'main imports actual DesktopApp + rendererRootOptions from ./module-routes and renders compiled registry','loader_source':'module-routes builtin daily_finance_home dynamically imports ../modules/daily-finance/DailyFinancePage','mock_target':'r3 test targets apps/desktop/src/modules/daily-finance/DailyFinancePage','module_resolution_static':'same canonical source file; not proof mock factory executed','observation_limit':'old test polls at most 20 iterations * 10ms; no lazy invocation or pending/finished instrumentation in original log','dynamic_cause':'unverified; no target rerun'})
    report='''# P4-C12-R4 lazy独立复验与Windows验收报告

- 角色：既有测试智能体、C12-R4唯一负责人；control 2026-10-02T23:25:00+08:00；2026-10-02 Asia/Shanghai。
- 任务卡：`docs/coordination/prompts/p4-c12-r4-lazy-windows-tester.md`。
- **交付 blocked / finished**：原lazy失败精确节点首次复验未通过，按任务卡第一阶段门禁停止。LAZY-001不能建议关闭；本轮没有足够证据新增产品P0/P1，也不声称旧Shell消失缺陷仍复现。最终结论由总控裁定。

## 本轮结果与停止原因

| 类别 | 实际结果 | 证据/限制 |
| --- | --- | --- |
| 原R3-UI-02-LAZY不变断言、精确节点、唯一一次 | **0 passed / 1 failed**，exit1 | evidence/r4/original-lazy/run.log、result.json |
| 新独立恢复/严格注册等 | **not_run，执行0** | 第一阶段未通过，不扩大测试 |
| lazy开发8+Shell/composition兼容 | **not_run，执行0** | 未进入兼容阶段，不跑registry52或完整132 |
| 真实Windows/临时chunk请求注入 | **not_run / unverified，执行0** | 产品0/8，辅助Electron0/4，注入0 |
| 原24项矩阵 | **0 passed、1 failed、19 blocked、4 not_run** | 状态不预写通过；UI-02旧failed保留未关闭，UI-04仍blocked |

不是再现原来的“Shell消失”：当前首次输出反而为Shell/nav/Agent全部存在，但预设chunk失败alert未出现。断言先期待alert文本，收到undefined，尚未执行后面的Shell断言；不能挑选前三个true冒充原节点passed，也不能把缺少alert当作产品已吞掉错误或修复无效的确定结论。

```json
{"caseId":"R3-UI-02-LAZY","chunkFailureShown":false,"shellPresent":true,"navigationPresent":true,"agentPanelPresent":true,"data":"virtual_only","evidenceLayer":"real_renderer_in_jsdom_with_virtual_bridge_and_failed_chunk"}
```

最后脱敏错误：`AssertionError: the given combination of arguments (undefined and string) is invalid for this assertion`，原r3-remaining.test.tsx:17期待alert.textContent包含“页面暂时无法打开”。Vitest JSON numTotalTests=1、passed0、failed1、pending0；23:30:53开始，节点761.2744ms。日志/JSON保留首次结果，未xfail/skip、未重跑覆盖、未改旧文件或放宽断言。

## 只读核对与尚未判定的原因

实际main已经导入并使用生产module-routes的DesktopApp和rendererRootOptions，registry为真实compileRegistry的daily contribution。module-routes仍以builtin daily_finance_home延迟import原页面，原测试mock指向同一规范源文件；新增R4配置只接R5普通依赖，没有替代Router/Shell/模块实现。静态来源摘要见readonly-source-observation.json。

原测试只轮询最多20×10ms，没有记录loader进入/完成或mock factory命中；Shell可来自新hydrateFallback/正常root，并不证明预期页面错误分支完成。**可能是异步路由/加载观测时限或mock解析接线，原因unverified**。现有静态同路径不证明动态mock命中，现有结果也不能排除产品分支问题。没有修改观察时限或插入诊断重跑，不能凭开发八项/正常EXE19成功宣布独立关闭。

已尝试：一次原断言精确执行；随后只读结果/原test/main/module-routes/Shell来源对照。无需操作用户电脑，没有运行辅助Electron、Windows产品或新测试。任务明确“若失败保留并停止，不重跑或进入Windows”，因此在本轮目标已运行后不适用“目标前无副作用配置错误一次更正”例外。

需要总控共同决定：下一步如何保留这次原始失败，建立可证实故障注入命中与加载完成的有限观察契约，再判断隔离/恢复行为。该决策属于测试证据/接线门禁，不预先要求产品返修。此角色不创建下一任务或自行续跑。

## 权威起点与外部包输入

新起点393/393 matched，0 missing/mismatch，staged0；manifest SHA `b248977db4d1b1aa84c843caa73cd1cac3ce25bcaa3ba5eb461b54863d963377`。外部构建输入389/389、out140/140、resources67/67分别匹配；历史R5 source390不直接assert派发后当前协调文件。原清单未修改，没有发生上一轮历史source误映射。

只读根C:\\MarisLazyR5\\R5-20261002-222300，已有Node24.21.0/Vitest5.0.2和普通依赖，未install/download/audit/build/package。

| 文件（workspace下） | 起终固定SHA-256 |
| --- | --- |
| apps/desktop/out/Maris-win32-x64/Maris.exe | 64ce71f3a7b3055f9ad27f6d611e28c4af7e9ba8b86d8b21399b7b422844a80e |
| resources/app.asar | 5ba47909537e1419dc275fa3ca1e5e076a1aa6d5c0205229f91defb92ddd0931 |
| pnpm-lock.yaml | 5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a |

终点以r4-delivery.py verify生成的end-audit.json及delivery-verification.json为准：393集只允许旧主报告/清单追加、matrix B备注、自身tester四项变更；所有旧public/r1/r2/r3代码/配置/报告/evidence精确保持。EXE/asar/lock/fuse字节、外部构建source389/out140/resources67不变。120唯一ID/12列/原前11列、B外字节及旧报告/清单prefix保持，A64 passed、C20/D12 not_run不变。

## UI-02 / UI-04 子条件与本轮缺口

- UI-02：原错误分支未成功观测，LAZY-001独立关闭门禁失败；局部隔离、明确retry实际成功、持续失败无循环、双route/settings切换、并发点击/离开后旧结果、render错误、安全DOM/console、主题/隐私/runtime/订阅保持和无额外auth/recover/provider/outbox写入均未新验收。仅Shell/nav/Agent采样存在不等于错误后的保持通过。
- Windows真实chunk、真实session故障持久化、CDP限定请求注入与撤销均未运行，也未声称file/asar工具不支持；尚未进入可行性检查阶段，不能虚构环境限制。
- UI-04：旧path/setting及身份校验独立通过证据输入不变，原27成功独立节点和outbox42不重跑。严格贡献对象/完整结构等剩余独立缺口因原lazy门禁停止而not_run；开发映射仅定位，整项blocked保持。路径大小写/尾斜杠/模式等未冻结语义不新增规则。

## 原24项完整映射

以下保留完整原预期。既有部分引自只读R3报告，明确为历史证据、未重跑；本轮没有把开发通过或静态source当整项passed。

'''
    previous=(ROOT/'docs/testing/phase-4-c12-r3-route-windows-report.md').read_text(encoding='utf-8-sig')
    for r in cases:
        cid,_,source,layer,env,mode,pre,inp,steps,expected,risk,state=r
        sec=re.search(r'### '+re.escape(cid)+r' — .*?\n(.*?)(?=\n### |\n## |\Z)',previous,re.S).group(1)
        prior=re.search(r'^- 已有部分.*?：(.*)$',sec,re.M).group(1);last=re.search(r'^- 本轮新增：(.*)$',sec,re.M).group(1);gap=re.search(r'^- 具体缺口与证据层级：(.*)$',sec,re.M).group(1)
        new='not_run；原lazy门禁首次失败后停止。'
        if cid=='P4B-UI-02':new='原R3-UI-02-LAZY唯一一次0pass/1fail，未观测alert但Shell/nav/Agent采样存在；不能确定故障注入命中或完成。';gap='原门禁未通过，旧LAZY-001不关闭；全部恢复边界/错误状态保持与Windows故障尚未验收。失败是独立节点结果，不新增已定级产品P1。'
        report+=f'### {cid} — {state}\n\n- 来源/风险/层/环境/方式：{source} / {risk} / {layer} / {env} / {mode}。\n- 前置：{pre}。\n- 输入：{inp}。\n- 操作：{steps}。\n- **完整原预期**：{expected}。\n- 已有历史部分：{prior}\n- 上轮R3新增（历史未重跑）：{last}\n- 本轮执行：{new}\n- 尚缺条件/证据层级：{gap}\n- 当前状态：`{state}`；无全部子条件通过不改passed。\n\n'
    report+='''## 安全收口、警告与交接

全部Vitest命令已退出1，没有活动session；产品0/8、辅助Electron0/4、chunk故障注入0。没有创建C:\\MarisC12\\C12-R4-*或任何虚拟profile/db/session，不访问真实AppData。没有owned产品/后端进程、实际窗口或监听需要终止；零资源源于未启动，不证明Tray/SUP-05通过。只清理本轮r4缓存，核对绝对专属范围且无reparse，首次result/log和审计保留。

真实native dialog/safeStorage老化提示unverified；Tray/普通closePolicy/注销/开机启动/多屏/DPI/主题/透明降级等旧人工条件not_run保持，原清单不删除/降级，不要求用户现在点击。未执行兼容8+2、新独立恢复、设置/ZIP/staging成功回归、Windows或后续注入。

初始只读查找猜module-routes在shell下，实际位于renderer，首次Get-Content不存在错误保留为搜索定位说明，随后按main相对import只读读取真实文件；没有配置/目标重试。原目标失败不是语法错误，不能套用前目标修正。Git仅只读diff，LF→CRLF提示记录，未改配置/stage/commit或其他Git状态。

只用虚拟bridge/模块，输出没有真实秘密/账目/原始消息/profile/session/db/blob/raw端点。没有Docker/PG/OpenClaw/微信/DeepSeek/provider/网络/系统设置/用户窗口或产品写入。新增本报告、r4-audit.py、r4-delivery.py、r4-vitest.config.mjs、evidence/r4；没有编写或运行后续独立恢复/Windows runner/helper来绕过停止门禁。

交接总控：接收原节点首次复验失败及其观测限制，决定故障命中/完成观测契约；旧LAZY-001尚不能关闭，UI-02设备条件/P4-B未验收。此角色停在 **blocked / finished**，不派发新任务/角色、不自行续跑、不进入P4-C。
'''
    (ROOT/REPORT).write_text(report,encoding='utf-8',newline='\n')
    appendix='\n\n## C12-R4 独立追加（2026-10-02）\n\n- [R4报告](phase-4-c12-r4-lazy-windows-report.md)：blocked / finished。原R3-UI-02-LAZY精确节点一次失败，actual alert不存在、Shell/nav/Agent存在；无法确认故障命中/完成，不建议关闭LAZY-001，也不把结果新增定级为产品P1。\n- 独立0 passed/1 failed；新增恢复/兼容均not_run。按原失败门禁停止，产品0/8、辅助Electron0/4、Windows chunk注入0；真实Windows/native/人工条件仍未执行。\n- 旧OUTBOX/setting/PATH保持关闭，旧27成功与outbox42不重跑；B仍0 passed/1 failed/19 blocked/4 not_run。原首次代码/报告/evidence保持，当前主报告和清单仅追加。\n- 首次JSON/log在evidence/r4/original-lazy，静态来源/观察限制在readonly-source-observation.json；交总控裁定有限测试观察契约，未改产品或Git。\n'
    for p in [OLD,MANUAL]:
        with (ROOT/p).open('ab') as f:f.write(appendix.encode('utf-8'))
    b=(ROOT/MATRIX).read_bytes();note='\n#### C12-R4 最新状态备注（2026-10-02）\n\n- 原lazy失败节点唯一一次复验失败：未观测alert，Shell/nav/Agent在；未确认注入命中/完成，不能建议关闭LAZY-001，也不报新已定级产品P1。\n- 第一阶段失败即停止：独立0 passed/1 failed，新恢复/兼容not_run，产品0/8、辅助0/4、chunk注入0。B整体仍0 passed/1 failed/19 blocked/4 not_run；UI-02旧failed未关闭，UI-04blocked与人工not_run保持。\n- 旧已通过outbox/setting/path不重跑、不重开。[R4完整报告](phase-4-c12-r4-lazy-windows-report.md)逐项保留预期/历史/本次/缺口。交blocked / finished等待总控裁定观察契约，不修改产品或Git。\n\n';(ROOT/MATRIX).write_bytes(b.replace(b'### 5.3',note.encode()+b'### 5.3',1))
    print('prepared R4 failed-gate report, append-only docs, B notes; no tests run')
elif sys.argv[1]=='verify':
    allowed={ROLE,MATRIX,OLD,MANUAL};matched=[];changed=[];bad=[];missing=[];manifest=ROOT/'docs/coordination/snapshots/p4-c12-r4-start.sha256'
    for line in manifest.read_text(encoding='utf-8-sig').splitlines():
        p,h=line.split('\t');file=ROOT/p
        if not file.is_file():missing.append(p)
        elif sha(file.read_bytes())==h:matched.append(p)
        elif p in allowed:changed.append(p)
        else:bad.append(p)
    start=json.loads((OWN/'start-audit.json').read_text(encoding='utf-8'));artifacts={p:sha((EXT/p).read_bytes()) for p in start['artifacts']};assert artifacts==start['artifacts']
    with (EXT/'apps/desktop/out/Maris-win32-x64/Maris.exe').open('rb') as f:
        with mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as m:
            i=m.find(b'dL7pKGdnNz796PbbjQWNKmHXBZaB9tsX')+32;fuses={'version':m[i],'wire':list(m[i+2:i+2+m[i+1]])}
    assert fuses==start['fuses'];counts={}
    for kind,rel,base in [('source','workspace-source.sha256',EXT),('out','out-manifest-v4.tsv',EXT/'apps/desktop/out/Maris-win32-x64'),('resources','python-resources-v4.tsv',EXT/'apps/desktop/out/Maris-win32-x64/resources')]:
        lines=(EXT.parent/'evidence/static'/rel).read_text(encoding='utf-8-sig').splitlines();assert all(sha((base/l.split('\t')[0]).read_bytes())==l.split('\t')[-1] for l in lines);counts[kind]=len(lines)
    staged=subprocess.run(['git','diff','--cached','--name-only'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines();audit={'entries':len(matched)+len(changed)+len(bad)+len(missing),'unchanged':len(matched),'authorized_changed':changed,'unauthorized_mismatch':bad,'missing':missing,'staged_paths':staged,'manifest_sha256':sha(manifest.read_bytes()),'artifacts':artifacts,'fuses':fuses,'package_inputs_manifests_matched':counts,'old_independent_files_unchanged':sum(p.startswith('tests/independent/desktop/') for p in matched)};save('end-audit.json',audit)
    assert audit['entries']==393 and len(matched)==389 and set(changed)==allowed and not bad and not missing and not staged
    baseline=json.loads((OWN/'baseline.json').read_text(encoding='utf-8'));b=(ROOT/MATRIX).read_bytes();cases=rows(b);assert len(cases)==len({r[0] for r in cases})==120 and all(len(r)==12 for r in cases);assert [r[:11] for r in cases]==[r[:11] for r in baseline['cases']];a=b.index(b'### 5.2');z=b.index(b'### 5.3');assert sha(b[:a])==baseline['outside_b_prefix'] and sha(b[z:])==baseline['outside_b_suffix'];assert [r[11] for r in cases]==[r[11] for r in baseline['cases']]
    prefixes={}
    for p,old in baseline['append_files'].items():
        b=(ROOT/p).read_bytes();assert sha(b[:old['bytes']])==old['sha256'];prefixes[p]={'prefix_preserved':True,'original_bytes':old['bytes'],'original_sha256':old['sha256'],'appended_bytes':len(b)-old['bytes']}
    nodeindex();files=[p for p in (ROOT/'tests/independent/desktop').glob('r4-*') if p.is_file()]+[ROOT/REPORT]+[p for p in OWN.rglob('*') if p.is_file() and not any(k in p.parts for k in ['tmp','cache','compat-cache']) and p.name!='delivery-verification.json'];save('delivery-verification.json',{'matrix_unique_ids':120,'columns':12,'all_original_first_11_columns_preserved':True,'all_case_statuses_preserved':True,'outside_b_bytes_preserved':True,'append_files':prefixes,'new_files_sha256':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in sorted(files)},'product_starts':0,'auxiliary_starts':0,'owned_resources':'not_started, not successful cleanup evidence','git_writes':0});print(json.dumps(audit,ensure_ascii=False,indent=2))
