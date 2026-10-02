"""Prepare C12-R3 handoff once; verify immutable boundaries without running target tests."""
from pathlib import Path
import json,hashlib,re,subprocess,sys,mmap
ROOT=Path(__file__).resolve().parents[3];OWN=ROOT/'tests/independent/desktop/evidence/r3'
MATRIX='docs/testing/phase-4-modular-agent-host-test-matrix.md';REPORT='docs/testing/phase-4-c12-r3-route-windows-report.md'
OLD_REPORT='docs/testing/phase-4-c12-windows-shell-report.md';MANUAL='docs/testing/phase-4-c12-manual-checklist.md';ROLE='docs/coordination/agents/tester.md'
def sha(b):return hashlib.sha256(b).hexdigest()
def save(name,data):(OWN/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rows(b):return [[c.strip() for c in l.strip().strip('|').split('|')] for l in b.decode('utf-8-sig').splitlines() if re.match(r'^\| P4[ABCD]-',l)]
def index():
    groups=[]
    for phase in ['original-path','path-independent','ui04-independent','storage-build-independent','remaining-independent','executor-compat']:
        j=json.loads((OWN/phase/'result.json').read_text(encoding='utf-8-sig'));nodes=[{'name':a['fullName'],'status':a['status']} for f in j['testResults'] for a in f['assertionResults'] if a['status'] in ['passed','failed']]
        groups.append({'phase':phase,'start_time_epoch_ms':j['startTime'],'nodes':nodes,'passed':sum(n['status']=='passed' for n in nodes),'failed':sum(n['status']=='failed' for n in nodes)})
    independent=[n for g in groups if g['phase']!='executor-compat' for n in g['nodes']]
    assert len(independent)==len({n['name'] for n in independent})==28 and sum(n['status']=='failed' for n in independent)==1
    save('node-index.json',groups);return groups
if sys.argv[1]=='prepare':
    assert not (ROOT/REPORT).exists(),'prepare_once'
    baseline=json.loads((OWN/'baseline.json').read_text(encoding='utf-8'));cases=[r.copy() for r in baseline['cases'] if r[1]=='B']
    for r in cases:
        if r[0]=='P4B-UI-02':r[11]='failed'
        if r[0]=='P4B-UI-04':r[11]='blocked'
    index()
    report='''# P4-C12-R3 路径独立复验与剩余Windows验收报告

- 角色：既有独立测试智能体，C12-R3唯一负责人；控制版本2026-10-02T18:25:00+08:00。
- 任务卡：`docs/coordination/prompts/p4-c12-r3-route-windows-tester.md`，2026-10-02，Asia/Shanghai。
- **交付 blocked / finished**：PATH-001原断言及相邻路径通过，建议关闭；未覆盖lazy故障发现新P1，按任务卡停止。OUTBOX-001/设置键REGISTRY-001保持关闭，不重复处理。P4-B不complete，最终接受属于总控。

## 实际运行与统计

| 分组 | 结果 | evidence/r3下首次JSON/log |
| --- | --- | --- |
| 原R2-UI-04-PATH不变断言，唯一一次 | 1 passed | original-path |
| 新路径双顺序/同模块/末尾/route ID/不变性/恢复 | 9 passed | path-independent |
| 未覆盖canonical ASCII末尾换行拒绝 | 1 passed | ui04-independent |
| 新设置3、ZIP6、staging7 | 16 passed | storage-build-independent |
| 真实renderer lazy失败隔离（虚拟端口、jsdom） | 1 failed | remaining-independent |
| **独立合计** | **28 unique executed：27 passed、1 failed** | node-index.json；各目标一次，不重复累加 |
| 开发registry兼容，单列、唯一一次 | **52 passed** | executor-compat |
| 原24项P4-B整项 | **0 passed、1 failed、19 blocked、4 not_run** | UI-02 blocked→failed；UI-04 failed→blocked |
| 产品/辅助Electron实际启动 | **0/8、0/4** | 新P1停止在Windows前，不是权限或设备故障 |

没有重跑旧outbox42、setting成功节点、R2成功15、完整开发124、Python/P0～P3/Host、Docker或任何外部服务。六组运行一次，五组退出0，lazy组退出1；未重跑失败、未放宽断言、无skip/xfail。原路径文件完全不变。

## 原PATH-001复验与关闭建议

原`r2-remaining.test.ts`只通过新R3配置/依赖执行精确R2-UI-04-PATH，结果从历史accepted:2变为desktop_registry_conflict，原断言不变。旧R2日志/JSON保持失败历史原样。新增9节点：跨module完全相同字符串两顺序；同module不同route ID同path两顺序；末module末route冲突；相同route ID不同path仍拒绝两顺序；不同路径合法且精确保留；冻结输入保持、无部分返回、失败后合法编译成功。不会把大小写/尾斜杠/模式归一化引入合同。

**建议总控关闭 P4-C12-R2-REGISTRY-PATH-001 的完全相同路径冲突问题。** 原设置键和outbox独立关闭不重开；路径通过不直接使UI-04/P4-B通过。

## 新P1：P4-C12-R3-LAZY-001

- 原案例：P4B-UI-02，风险P1；完整预期是局部错误边界可重试，Shell/登录/其他模块可用，不循环加载或丢当前会话。
- 测试节点：`r3-remaining.test.tsx` / R3-UI-02-LAZY。真正导入产品renderer/main.tsx，React、React DOM、React Router、Shell与RouteErrorBoundary均为实际代码；环境为jsdom，窄window.maris bridge返回虚拟在线已认证snapshot和合法daily_finance/日常管钱canonical Profile摘要；只对lazy页面的import端口注入VIRTUAL_CHUNK_UNAVAILABLE。没有替换路由器或错误边界。
- 前置：新内存DOM、没有网络/真实Host/DB，模块/状态均虚拟；生产lazy route已可由实际导航进入。
- 操作：运行实际renderer启动、等待effects与lazy拒绝进入实际错误边界，再读取Shell/模块导航/统一Agent面板DOM。
- 预期：安全错误只影响模块内容；Shell、模块导航、统一Agent入口仍可用。
- **实际**：安全错误页确实出现，但Shell、导航、Agent面板全部不存在。首次断言在Shell必须保留处失败，退出1。该核心局部隔离子条件已经失败，不需继续点击或实机重跑来抵消。
- 脱敏证据：`evidence/r3/remaining-independent/run.log`与result.json永久保留，最小复现为r3-remaining.test.tsx。没有声称实机丢失session/token/账目或真实其他模块执行失败，未运行成功重试/第二lazy route/Windows现场。
- 只读原因定位：renderer/main.tsx:24将errorElement放在包含Shell的父route，子lazy route没有局部errorElement；错误冒泡后父Shell被错误页替换。Shell.tsx的重试使用全页reload，只读观察未点击，不把它另计为实测缺陷或恢复结果。
- 严重级别 **P1**：单模块chunk故障使整个Shell入口不可用，违反明确冻结的隔离验收；不是harness/导入配置失败。按任务卡停止扩大测试，没有产品修复。

```json
{"caseId":"R3-UI-02-LAZY","chunkFailureShown":true,"shellPresent":false,"navigationPresent":false,"agentPanelPresent":false,"data":"virtual_only","evidenceLayer":"real_renderer_in_jsdom_with_virtual_bridge_and_failed_chunk"}
```

复现命令只作为交接材料，不表示本角色获准再次运行失败节点：

```powershell
$env:C12_R3_PHASE='remaining-independent'
& 'C:/MarisRouteR4/R4-20261002-164600/tools/node/node.exe' 'C:/MarisRouteR4/R4-20261002-164600/workspace/node_modules/vitest/vitest.mjs' run --config tests/independent/desktop/r3-vitest.config.mjs
```

## 新公开行为与适用层级

设置3：缺失/坏JSON/未知字段安全defaults，有效主题/隐私/虚拟DIP bounds经过新store恢复且无.tmp残留；额外token canary严格拒绝且原有效文件字节不变。均写测试专属tmp普通文件，不改真实AppData/用户settings。未注入全部FS故障，也不等于OS启动项/主题/窗口实际恢复通过。

ZIP6：无环境变量兼容、空值/空白/相对/边缘空白/NUL拒绝，使用小型虚拟archive和注入公开contract验证合法、文件不存在、错误长度、同长度错误SHA。只执行校验器，不下载/安装/Forge/package，不读真实ZIP缓存或伪称官方zip重新验收。

staging7：仅在新fixture source/desktop根运行真实stage函数，显式传两个根，绝不使用默认产品root。验证allowlist精确路径/hash，排除cache/egg-info/tests/pyc，路径绝对/越界/反斜杠拒绝；六个replacement阶段故障，提交前四阶段旧payload/manifest完整保留，提交后两阶段稳定committed错误且新完整pair保留；锁/tmp无残留。未运行symlink/junction/reparse注入与全部异常组合，不把7项代替完整package/污染源动态门禁。

## UI-04独立映射（原标准不改）

| 冻结子条件 | 独立证据及输入关系 | 层级/状态 |
| --- | --- | --- |
| hostUiMajor；module ASCII、SemVer、canonical Profile | 原R1-SHELL-12在R2 adjacent-original通过，相关schema输入不变，未重复；本轮R3-UI04-ASCII-01末尾换行拒绝 | 已有+新增contract行为；不将开发52当独立 |
| module/Profile/route ID/appearance全局冲突 | R2 adjacent-original中的R1-SHELL-11四类通过，身份token未变；本轮R3-PATH-04路由ID仍有效 | 已有独立证据+受影响路由ID新增 |
| setting全局冲突 | R2 original-registry及registry-independent15成功中的对应边界；setting token未变，缺陷已关闭，不重复 | 历史独立输入不变 |
| 完全相同path冲突、不部分返回、输入不变、失败恢复 | 本轮原路径1、新路径9通过，包含末尾与冻结输入 | 新独立contract行为通过，建议PATH关闭 |
| Host major/Profile/API prefixes/schema精确交集；未知/禁用排除 | 原C12-PUB-05及R1 remaining-original通过，intersectModules输入不变，未重复 | 历史fake Host fixture行为，实际Windows导航未验 |
| Shell/main/preload无具体module业务分支 | 只读Shell、renderer注册及限定rg定位未发现具体module比较分支；开发结构映射仅用于定位 | 结构观察，未完成本轮完整独立结构/严格贡献子条件复核，不冒称行为通过 |
| strict对象及全部未覆盖规范边界、启动验证 | 首次新P1后停止扩大；开发映射不是独立证据 | 未完成，UI-04保守blocked，不能仅以路径通过整项passed |

路径大小写、尾斜杠、动态参数、模式重叠、保留settings path等语义未另冻结；R4说明已指出这些风险。本轮没有添加归一化断言或将它们另报已实测缺陷，后续语义需总控裁定。

## 起点、首次审计问题及不可变性

新起点356/356 matched，0缺失/差异，staged0；manifest SHA-256 `4b6dcb45d27cb5a277636278564dcf8489e244929db9fa46cf7c4ca2bba32b0f`。新只读环境 C:\\MarisRouteR4\\R4-20261002-164600，Node24.21.0/Vitest5.0.2，已装普通依赖；不安装/构建/下载。

首次新增审计将历史repository source353与当前派发后仓库直接比较，遇到五份总控协调更新（README/control/overview/brainstorm/project-coordination）348匹配/5差异而assert退出1。此前356新起点、140out、67resources、EXE/asar/lock/fuses已匹配。保留initial-audit-failure.json，唯一一次目标前无副作用映射修正：这五份在权威新起点逐字节匹配，历史清单不改；实际包构建输入workspace-source352/352匹配。它不是产品漂移或业务失败，没有消耗EXE/辅助预算。工具失败保留，不用历史清单或旧包根覆盖本轮结论。

| 文件（只读workspace下） | 起终固定SHA-256 |
| --- | --- |
| Maris.exe | d5868736cbdf63f717f0ea853141b980d06cefc10a3c05196e8856cbe3a4de2b |
| resources/app.asar | 9a4da50b2c5583e6f2337bdff43e399cd454c360fa6169b1667a1e4506c337d4 |
| pnpm-lock.yaml | 5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a |

终点实测见evidence/r3/end-audit.json和delivery-verification.json，由新增r3-delivery.py verify核对。固定356集只允许tester、matrix B、旧主报告/人工清单四项变化；旧public/r1/r2测试、R1/R2报告和全部旧evidence/失败日志不可变；产品及当前control不变。追加prefix与B外字节段、120唯一ID/12列/原B前11列保持；A64 passed、C20/D12 not_run不变。EXE/asar/lock与fuses起终保持，out140/resources67/构建输入352保持。

## 原24项逐项完整映射

已有部分明确为只读R2报告内的历史证据（本轮未重复，固定文件摘要核对）；每项仍列完整原预期、实际新增和缺口。单元/结构不替代设备条件。

'''
    old=(ROOT/'docs/testing/phase-4-c12-r2-registry-windows-report.md').read_text(encoding='utf-8-sig')
    for r in cases:
        cid,_,source,layer,env,mode,pre,inp,steps,expected,risk,state=r
        sec=re.search(r'### '+re.escape(cid)+r' — .*?\n(.*?)(?=\n### |\n## |\Z)',old,re.S).group(1)
        prior=re.search(r'^- 已有部分.*?：(.*)$',sec,re.M).group(1)
        gap=re.search(r'^- 证据层级与具体缺口：(.*)$',sec,re.M).group(1)
        new='未新增执行；新P1停止扩大。'
        if cid=='P4B-UI-02':new='R3-UI-02-LAZY首次失败：真实renderer/jsdom，安全错误页出现但Shell/nav/Agent入口全部消失。';gap='核心局部隔离已失败；重试成功/其他lazy route/session保持/无循环与Windows未执行。'
        if cid=='P4B-UI-04':new='原路径1+新路径9+ASCII1通过；旧setting及身份相邻不重跑；建议关闭PATH-001。';gap='UI-04完整独立结构/strict贡献及启动验证映射尚未完成，新P1停止；不能由路径通过直接passed。'
        if cid=='P4B-CMP-05':new='R3-SET-01/02/03本地设置defaults/有效持久化/非法字段拒绝通过；只有虚拟bounds字段。';gap='实际位置夹取/重启/多屏/全屏/键盘/隐私UI与全部人工设备条件未执行，整项manual not_run保持。'
        report+=f'### {cid} — {state}\n\n- 来源/风险/层级/环境/方式：{source} / {risk} / {layer} / {env} / {mode}。\n- 前置：{pre}。\n- 输入：{inp}。\n- 操作：{steps}。\n- **完整原预期**：{expected}。\n- 已有部分（R2记载历史，未重复）：{prior}\n- 本轮新增：{new}\n- 具体缺口与证据层级：{gap}\n- 当前状态：`{state}`；未完成全部子条件不标passed。\n\n'
    report+='''## 停止、资源、人工缺口和交接

lazy组18:52:03开始，首次失败后立即停止扩展。全部Vitest已退出，无活动session；产品0/8、辅助Electron0/4，未创建C:\\MarisC12\\C12-R3-*，没有owned实际窗口/监听/进程需要终止。零资源来自未启动，不是SUP-05或Tray关闭成功证据。没有CDP/UIA、safeStorage fixture或原生dialog，真实老化提示unverified；不请求用户现在点击。

尚未执行：实际安全CSP/导航/秘密/恶意文本布局、生成物漂移、staging链接/全部错误、设置写盘失败、真实managed/认证/recover/GET一次提交/单毛毛/单实例/closePolicy/Tray。普通退出与注销、启动项、多屏/DPI/拔屏/全屏/透明降级/OS主题人工条件not_run保持；实际UI恢复不由jsdom单位行为替代。保留原人工清单仅追加，未删降原预期。

只用虚拟模块/账目身份字段/canary/文件，不访问真实provider/秘密/旧AppData/profile/session/db。没有Docker/PG/OpenClaw/微信/DeepSeek、网络、系统设置、产品/执行方/依赖/冻结/控制文件/其他角色或Git写操作。自身tmp/cache清理前重读control、验证绝对专属路径无reparse；所有首次log/JSON、审计保留。旧环境与evidence不清理。

新增：本报告；r3-audit.py、r3-delivery.py、r3-vitest.config.mjs、r3-compat-vitest.config.mjs、r3-path.test.ts、r3-ui04.test.ts、r3-storage-build.test.ts、r3-remaining.test.tsx及evidence/r3。没有交付/运行Windows runner/helper，因为新P1停止前未进入该阶段。

交接总控：建议关闭原PATH-001，并接收新P1 P4-C12-R3-LAZY-001最小复现、预期/实际、层级限制与首次证据；裁定后续范围。此角色停在 **blocked / finished**，不派发角色/返修/后续任务、不进入P4-C，不宣布P4-B complete。
'''
    (ROOT/REPORT).write_text(report,encoding='utf-8',newline='\n')
    appendix='\n\n## C12-R3 独立追加（2026-10-02）\n\n- [R3完整报告](phase-4-c12-r3-route-windows-report.md)：blocked / finished。原PATH-001不变断言及新路径9通过，建议关闭；新P1 P4-C12-R3-LAZY-001：lazy import故障后整个Shell/nav/Agent入口消失，首次证据在evidence/r3/remaining-independent，未重跑或修产品。\n- 独立28 unique：27 passed/1 failed；开发registry52 passed单列。设置3/ZIP6/staging7通过限逻辑证据；产品0/8、辅助Electron0/4，Windows未执行。\n- UI-02现failed；UI-04路径问题复验通过但完整独立复核未完成为blocked，P4-B仍0 passed/1 failed/19 blocked/4 not_run。旧OUTBOX/setting保持关闭，旧outbox42/setting节点不重复。\n- 真实native dialog unverified、Tray/启动项/注销/多屏/主题人工步骤原样保留未执行，不要求用户即时动作。旧正文prefix和旧R1/R2报告/evidence保持。交总控裁定新lazy故障，测试角色停止。\n'
    for p in [OLD_REPORT,MANUAL]:
        with (ROOT/p).open('ab') as f:f.write(appendix.encode('utf-8'))
    matrix=(ROOT/MATRIX).read_bytes()
    for cid,state in [('P4B-UI-02','failed'),('P4B-UI-04','blocked')]:
        pattern=rb'(?m)^(\| '+cid.encode()+rb' .*?\| )[^|\r\n]+(\|\r?$)'
        matrix,n=re.subn(pattern,lambda m:m[1]+state.encode()+b' '+m[2],matrix);assert n==1
    note='\n#### C12-R3 最新状态备注（2026-10-02）\n\n- PATH-001原断言与新路径9通过，建议关闭；新增ASCII1/设置3/ZIP6/staging7通过。旧OUTBOX/setting保持关闭，不重跑已过节点。\n- 新P1 `P4-C12-R3-LAZY-001`：实际renderer/jsdom的lazy故障替换整个Shell，导航和Agent入口消失。UI-02 blocked→failed；UI-04路径通过但完整独立复核因新P1停止，failed→blocked。历史备注不改写。\n- 独立28 unique：27 passed/1 failed；开发52兼容单列。B整项仍0 passed/1 failed/19 blocked/4 not_run；产品0/8、辅助Electron0/4，Windows/native/人工条件未验，停止blocked / finished。\n- [R3报告](phase-4-c12-r3-route-windows-report.md)保留24项完整原预期/历史/本轮/缺口，实际审计在evidence/r3，最终接受属总控。\n\n'
    matrix=matrix.replace(b'### 5.3',note.encode()+b'### 5.3',1);(ROOT/MATRIX).write_bytes(matrix)
    print('R3 report + append-only historical docs + B-only changes prepared; no tests run')
elif sys.argv[1]=='verify':
    allowed={MATRIX,OLD_REPORT,MANUAL,ROLE};unchanged=[];changed=[];bad=[];missing=[];manifest=ROOT/'docs/coordination/snapshots/p4-c12-r3-start.sha256'
    for line in manifest.read_text(encoding='utf-8-sig').splitlines():
        p,h=line.split('\t');target=ROOT/p
        if not target.is_file():missing.append(p)
        elif sha(target.read_bytes())==h:unchanged.append(p)
        elif p in allowed:changed.append(p)
        else:bad.append(p)
    start=json.loads((OWN/'start-audit.json').read_text(encoding='utf-8'));ext=Path('C:/MarisRouteR4/R4-20261002-164600/workspace');artifacts={p:sha((ext/p).read_bytes()) for p in start['artifacts']};assert artifacts==start['artifacts']
    with (ext/'apps/desktop/out/Maris-win32-x64/Maris.exe').open('rb') as f:
        with mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as m:
            i=m.find(b'dL7pKGdnNz796PbbjQWNKmHXBZaB9tsX')+32;fuses={'version':m[i],'wire':list(m[i+2:i+2+m[i+1]])}
    assert fuses==start['fuses']
    manifests={}
    for label,rel,base in [('source','workspace-source.sha256',ext),('out','out-manifest-v4.tsv',ext/'apps/desktop/out/Maris-win32-x64'),('resources','python-resources-v4.tsv',ext/'apps/desktop/out/Maris-win32-x64/resources')]:
        lines=(ext.parent/'evidence/static'/rel).read_text(encoding='utf-8-sig').splitlines();assert all(sha((base/l.split('\t')[0]).read_bytes())==l.split('\t')[-1] for l in lines);manifests[label]=len(lines)
    staged=subprocess.run(['git','diff','--cached','--name-only'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines()
    audit={'entries':len(unchanged)+len(changed)+len(bad)+len(missing),'unchanged':len(unchanged),'authorized_changed':changed,'unauthorized_mismatch':bad,'missing':missing,'staged_paths':staged,'manifest_sha256':sha(manifest.read_bytes()),'artifacts':artifacts,'fuses':fuses,'package_inputs_manifests_matched':manifests,'old_independent_files_unchanged':sum(p.startswith('tests/independent/desktop/') for p in unchanged)}
    save('end-audit.json',audit);assert audit['entries']==356 and len(unchanged)==352 and set(changed)==allowed and not bad and not missing and not staged
    baseline=json.loads((OWN/'baseline.json').read_text(encoding='utf-8'));matrix=(ROOT/MATRIX).read_bytes();cases=rows(matrix);assert len(cases)==len({r[0] for r in cases})==120 and all(len(r)==12 for r in cases)
    assert [r[:11] for r in cases]==[r[:11] for r in baseline['cases']]
    a=matrix.index(b'### 5.2');z=matrix.index(b'### 5.3');assert sha(matrix[:a])==baseline['outside_b_prefix'] and sha(matrix[z:])==baseline['outside_b_suffix']
    counts={s:{state:sum(r[1]==s and r[11]==state for r in cases) for state in ['passed','failed','blocked','not_run']} for s in 'ABCD'}
    assert counts['A']['passed']==64 and counts['C']['not_run']==20 and counts['D']['not_run']==12 and counts['B']=={'passed':0,'failed':1,'blocked':19,'not_run':4}
    prefixes={}
    for p,old in baseline['append_files'].items():
        b=(ROOT/p).read_bytes();assert sha(b[:old['bytes']])==old['sha256'];prefixes[p]={'original_prefix_bytes':old['bytes'],'original_prefix_sha256':old['sha256'],'prefix_preserved':True,'appended_bytes':len(b)-old['bytes']}
    index();files=[p for p in (ROOT/'tests/independent/desktop').glob('r3-*') if p.is_file()]+[ROOT/REPORT]+[p for p in OWN.rglob('*') if p.is_file() and not any(k in p.parts for k in ['tmp','cache','compat-cache']) and p.name!='delivery-verification.json']
    save('delivery-verification.json',{'matrix_unique_ids':120,'columns':12,'all_original_first_11_columns_preserved':True,'outside_b_byte_prefix_suffix_preserved':True,'counts':counts,'case_status':{r[0]:r[11] for r in cases if r[1]=='B'},'append_files':prefixes,'new_files_sha256':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in sorted(files)},'product_starts':0,'auxiliary_electron_starts':0,'owned_resources':'not_started; not a successful cleanup test','git_writes':0})
    print(json.dumps({'audit':audit,'matrix':counts,'append_only':True},ensure_ascii=False,indent=2))
