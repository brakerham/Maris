"""C12-R2 document handoff; prepare once, verify is read-only except own evidence."""
from pathlib import Path
import hashlib, json, re, subprocess, sys, mmap
ROOT = Path(__file__).resolve().parents[3]
OWN = ROOT / 'tests/independent/desktop/evidence/r2'
MATRIX = 'docs/testing/phase-4-modular-agent-host-test-matrix.md'
REPORT = 'docs/testing/phase-4-c12-r2-registry-windows-report.md'
OLD_REPORT = 'docs/testing/phase-4-c12-windows-shell-report.md'
MANUAL = 'docs/testing/phase-4-c12-manual-checklist.md'
ROLE = 'docs/coordination/agents/tester.md'
ALLOWED = {MATRIX, OLD_REPORT, MANUAL, ROLE}
def digest(b): return hashlib.sha256(b).hexdigest()
def read(p): return (ROOT / p).read_bytes()
def save(name, value): (OWN / name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def rows(text): return [[c.strip() for c in line.strip().strip('|').split('|')] for line in text.splitlines() if re.match(r'^\| P4[ABCD]-',line)]
def split_matrix(b):
    start=b.index(b'### 5.2'); end=b.index(b'### 5.3')
    return b[:start],b[start:end],b[end:]
def phase_nodes():
    result=[]
    for phase in ['original-registry','adjacent-original','registry-independent','remaining-independent','executor-compat']:
        data=json.loads((OWN/phase/'result.json').read_text(encoding='utf-8-sig'))
        nodes=[{'name':a['fullName'],'status':a['status']} for f in data['testResults'] for a in f['assertionResults'] if a['status'] in ['passed','failed']]
        result.append({'phase':phase,'started_epoch_ms':data['startTime'],'selected_executed':len(nodes),'passed':sum(a['status']=='passed' for a in nodes),'failed':sum(a['status']=='failed' for a in nodes),'nodes':nodes})
    independent=[n['name'] for p in result if p['phase']!='executor-compat' for n in p['nodes']]
    assert len(independent)==len(set(independent))==16
    save('node-index.json',result)
    return result
def update_role(step, state, clock, output, checkpoint, log):
    p=ROOT/ROLE; text=p.read_text(encoding='utf-8-sig')
    replacements={'状态':f'`{state}`','最近更新':f'{clock} Asia/Shanghai','运行状态':'`finished`' if state=='blocked' else '`active`','当前步骤':step,'步骤开始时间':f'{clock} Asia/Shanghai','最近有效进展':f'{clock} Asia/Shanghai','最近心跳':f'{clock} Asia/Shanghai','下一检查点':checkpoint,'等待对象':'总控裁定新P1与交付' if state=='blocked' else '无','活动进程或会话':'无；全部Vitest已退出，产品0/8、辅助Electron0/4；未创建外部profile','最近输出':output,'可修改范围':'仅新增 r2-*、evidence/r2、新R2报告；旧主报告/清单只追加、矩阵仅B状态备注、自身角色；旧R1及产品只读'}
    for key,value in replacements.items(): text=re.sub(r'^- '+re.escape(key)+r'：.*$',f'- {key}：{value}',text,count=1,flags=re.M)
    text=text.replace('## 工作日志\n','## 工作日志\n\n'+log+'\n',1)
    p.write_text(text,encoding='utf-8',newline='\n')
if sys.argv[1]=='prepare':
    assert not (OWN/'matrix-baseline.json').exists(), 'prepare_once_only'
    b=read(MATRIX); prefix,_,suffix=split_matrix(b); cases=rows(b.decode('utf-8-sig'))
    original=json.loads(read('tests/independent/desktop/evidence/matrix-original-cases.json').decode('utf-8-sig'))['cases']
    current=[r for r in cases if r[1]=='B']; assert len(current)==24
    assert [r[:11] for r in current]==[r[:11] for r in original]
    baseline={'matrix_sha256':digest(b),'prefix_sha256':digest(prefix),'suffix_sha256':digest(suffix),'cases':current,'append_files':{p:{'length':len(read(p)),'sha256':digest(read(p))} for p in [OLD_REPORT,MANUAL]}}
    save('matrix-baseline.json',baseline); nodes=phase_nodes()
    update_role('发现新P1路径冲突，已停止测试；编写完整24项映射与终点边界审计','in_progress','2026-10-02 15:44','独立16 executed：15 passed/1 failed；兼容26 passed；首次accepted:2，未重跑','报告和终点审计，15:54前；不启动Windows', '### 2026-10-02 15:44 Asia/Shanghai — 原registry复验通过与新P1停止\n\n- 原R1-SHELL-13一次不变断言通过，相邻10/11/12共6通过，新增registry8通过；开发registry26一次兼容通过。\n- 新R2-UI-04-PATH首次失败：不同route ID同/virtual_shared path仍accepted:2，登记P1 P4-C12-R2-REGISTRY-PATH-001；停止扩大测试，原日志/JSON永久保留。\n- 原REGISTRY-001建议关闭仅setting边界，UI-04仍failed；后续自动/Windows未执行，不降低预期。\n- 产品0/8、辅助Electron0/4；没有owned窗口/端口/进程或外部profile需要关闭；所有Vitest退出。进入脱敏报告和终点审核，不修产品、不Git写入。\n')
    report='''# P4-C12-R2 registry 独立复验与 Windows 验收报告

- 控制版本：2026-10-02T15:22:00+08:00；角色：既有独立测试智能体、唯一负责人。
- 任务卡：`docs/coordination/prompts/p4-c12-r2-registry-windows-tester.md`。
- 交付：**blocked / finished**。原设置键缺陷建议关闭；新 P1 路由路径冲突导致按任务卡停止扩展。P4-B 不 complete，最终接受属于总控。

## 实测结论与独立统计

原 `P4-C12-R1-REGISTRY-001` 的 R1-SHELL-13 原断言唯一一次通过，旧测试及首次失败证据完全未改。相邻 registry 六节点和新独立八节点通过；但 UI-04 完整契约中的 path 冲突首次失败。不能由设置键修复或开发测试全绿推导 UI-04 passed。

| 分组 | 实际结果 | 本轮证据（tests/independent/desktop/evidence/r2/ 下） |
| --- | --- | --- |
| 原R1-SHELL-13不变断言、唯一一次 | 1 passed | original-registry/result.json、run.log |
| 原R1-SHELL-10/11/12、排除13和其他旧节点 | 6 passed | adjacent-original/result.json、run.log |
| 新双顺序/schema/同模块重复/合法键/失败恢复 | 8 passed | registry-independent/result.json、run.log |
| 新UI-04 path边界首次复现 | 1 failed | remaining-independent/result.json、run.log |
| 独立合计 | **16 unique executed：15 passed、1 failed** | node-index.json；filter未选节点不算实际执行 |
| 开发registry兼容、唯一一次 | **26 passed**，单列 | executor-compat/result.json、run.log |
| P4-B整项24 | **0 passed、1 failed、19 blocked、4 not_run** | 局部成功不替代整项/设备条件 |
| 产品 / 辅助Electron启动 | **0/8 / 0/4** | 因新P1停止，非环境或审批失败 |

未重复已通过的outbox42、旧60、Host/session/supervisor或完整开发98；没有Python/数据库全量、安装、下载、build或package。五组各只执行一次，原失败复验、相邻原节点、新registry、开发兼容四组退出0；随后路径组退出1。配置无失败/修正重试。所有命令已返回，无活动session。失败非harness故障，原断言没有放宽。

## 新P1：P4-C12-R2-REGISTRY-PATH-001

- 依据：原矩阵 P4B-UI-04 明列 `hostUiMajor、route/path/setting/profile/companion 冲突`，预期不兼容或冲突稳定失败；IF-003 §5 全局route唯一且任一冲突不部分加载。IF-004/005及当前control没有撤销此条件。
- 前置：两个各自合法的纯虚拟 contribution，moduleId 为 virtual_left/virtual_right；version=1.0.0、hostUiMajor=1。Profile、route ID、setting key、appearance和API prefix分别不同；只有路径均为 `/virtual_shared`。不创建第二产品业务模块。
- 操作：`r2-remaining.test.ts` 中 `R2-UI-04-PATH` 调用公开 compileRegistry 一次并记录返回/异常。
- 预期：整体拒绝，稳定错误 desktop_registry_conflict。
- 实际：无异常，返回两个贡献；控制台 `actual: accepted:2`，断言退出1。
- 严重级别：**P1**，与UI-04原风险一致；路径冲突未在编译注册期fail closed，破坏模块路由唯一性和启动边界。没有声称真实daily_finance导航误路由、财务损失或权限利用已发生，未执行实际renderer验证。
- 最小复现、日志与JSON：`tests/independent/desktop/r2-remaining.test.ts`；`evidence/r2/remaining-independent/run.log`、`result.json`。首次现场永久保留，不修改产品、不重跑覆盖。

```json
{"caseId":"R2-UI-04-PATH","path":"/virtual_shared","routeIds":["virtual_left_route","virtual_right_route"],"expected":"desktop_registry_conflict","actual":"accepted:2","data":"virtual_only"}
```

复现命令（仅供总控复算，不表示授权本测试角色重跑）：

```powershell
$env:C12_R2_PHASE='remaining-independent'
& 'C:/MarisRegistryR3/R3-20261002-111556/tools/node/node.exe' 'C:/MarisRegistryR3/R3-20261002-111556/workspace/node_modules/vitest/vitest.mjs' run --config tests/independent/desktop/r2-vitest.config.mjs
```

原REGISTRY-001独立关闭建议限于设置键：跨模块不同顺序、同/异schemaVersion均拒绝，同模块重复拒绝，不同全局键合法；冻结输入未修改，没有部分返回，失败后合法compile仍成功。UI major/ASCII/SemVer、module/Profile/route ID/appearance相邻冲突拒绝也通过。**设置键修复通过与路径新失败分别记录，不能抵消。** Shell无具体moduleId业务分支及真实启动/导航仍未完整独立验收。

## 固定输入及审计

起点327/327 matched，0 missing/mismatch；清单 `docs/coordination/snapshots/p4-c12-r2-start.sha256` SHA-256为 `0547e289b34619b491478fedc153a3f0c169635550ab9d4f881343ce1d613b9b`，staged=0。只读根 `C:\\MarisRegistryR3\\R3-20261002-111556`；固定Node24.21.0及已有Vitest5.0.2，配置cache与结果仅写本轮evidence/r2。旧R3/R2/LOCALZIP用户现场不复用、不写。

| 文件（只读根workspace下） | 起终固定SHA-256 |
| --- | --- |
| apps/desktop/out/Maris-win32-x64/Maris.exe | 1df694c0ca39818d1b2af7aad09eefa13383af186a8d0638d96a13882d604a94 |
| apps/desktop/out/Maris-win32-x64/resources/app.asar | 64f84ddde164c4dea81ab3fcb6933728eda5acf3cfe4917828fe0f4f6dc3e161 |
| pnpm-lock.yaml | 5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a |

终点以新增 `r2-delivery.py verify` 和 evidence/r2/end-audit.json、delivery-verification.json复算：预期323 unchanged+4 authorized changed，0非授权变更/缺失，原R1全部测试/报告/evidence与首次失败不可变；EXE/asar/lock保持，EXE fuse wire前六项48/49/48/48/49/49保持。旧主报告/人工清单原byte prefix精确保留，matrix B外prefix/suffix不变，120唯一ID/12列/原B前11列不变，A64 passed、C20/D12 not_run保持。**最终实测审计结果见上述JSON，不以本段预期代替实测。**

## 原24项完整映射

“已有部分”引自只读C12-R1报告，仅表明输入未变部分的历史证据，未重复执行；所有旧证据摘要在终点复算。每项保留完整原预期、具体缺口和状态，不把静态/单元或兼容证据代替设备验收。

'''
    old=(ROOT/'docs/testing/phase-4-c12-r1-outbox-windows-report.md').read_text(encoding='utf-8-sig')
    for row in current:
        cid,_,source,layer,env,mode,pre,inputs,steps,expected,risk,state=row
        section=re.search(r'### '+re.escape(cid)+r' — .*?\n(.*?)(?=\n### |\n## |\Z)',old,re.S).group(1)
        historical=re.search(r'^- 实测节点/证据：(.*)$',section,re.M).group(1)
        gap=re.search(r'^- 证据层级和缺口：(.*)$',section,re.M).group(1)
        new='未新增执行；新P1停止规则生效。'
        if cid=='P4B-UI-04':
            new='原13一次通过；原10/11/12六通过、新registry八通过；R2-UI-04-PATH失败。开发26仅兼容。'
            gap='setting缺陷建议关闭；path同路径不同route ID首次失败，登记新P1；Shell无具体module分支与实际启动/导航未完整验收。'
        elif cid=='P4B-UI-01': new='原R1-SHELL-10及新R2-REG-03合法贡献compile通过；真实Host交集/导航不重复且未新执行。'
        report+=f'### {cid} — {state}\n\n- 来源/风险/层/环境/方式：{source} / {risk} / {layer} / {env} / {mode}。\n- 前置：{pre}。\n- 输入：{inputs}。\n- 步骤：{steps}。\n- **完整原预期**：{expected}。\n- 已有部分（C12-R1历史证据，未重跑）：{historical}\n- 本次新执行：{new}\n- 证据层级与具体缺口：{gap}\n- 当前状态：`{state}`，未完整验收不能写passed。\n\n'
    report+='''## 停止、Windows预算、隐私和交接

15:41:51路径组开始，首次失败后停止扩展；产品0/8、辅助Electron0/4，未创建外部C12-R2 profile/db/session/safeStorage fixture，没有CDP/UIA、原生dialog、实际Tray/closePolicy/窗口/后端或OS动作。无owned进程、端口、窗口需要关闭源于未启动，不能计作SUP-05清理通过；没有全局kill或用户即时操作请求。

剩余设置原子保存/恢复、真实安全/恶意文本布局、lazy route、生成物漂移、ZIP边界、staging故障原子性均因新P1未执行；真实managed/auth/recover/GET一次提交/毛毛主链路、单实例、Tray和closePolicy未执行。原生老化提示保留unverified；注销/重启/实际开机启动项、多屏/拔屏/主题/透明降级等人工条件仍not_run，完整旧清单保持并追加R2现状。没有使用开发EXE19 gates冒充独立设备通过。

只用虚拟module/key/path数据，控制台不含秘密、真实财务、消息、session/db/blob/raw endpoint。没有Docker/PG/OpenClaw/微信/DeepSeek/provider、网络、系统设置、Git写入或产品修改。只清理新r2 cache/compat-cache并验证绝对范围/无链接；结果/日志/审计永久保留。旧profile/cache/evidence不清理。

新增独立交付：本报告；r2-vitest.config.mjs、r2-compat-vitest.config.mjs、r2-registry.test.ts、r2-remaining.test.ts、r2-delivery.py；evidence/r2起终审计、五组首次log/JSON、node-index、matrix-baseline及delivery verification。没有Windows runner/helper执行交付，因新P1停止动态前。更新仅旧主报告/人工清单追加、matrix B备注、自身角色日志。

交接总控：独立建议关闭原设置键REGISTRY-001，接收新路径P1最小复现并裁定后续；本轮不派发返修/新任务、不修改接口、不进入P4-C、不自行续跑。停在 **blocked / finished**。
'''
    (ROOT/REPORT).write_text(report,encoding='utf-8',newline='\n')
    appendix='\n\n## C12-R2 独立追加（2026-10-02）\n\n- [R2完整报告](phase-4-c12-r2-registry-windows-report.md)：blocked / finished。原setting REGISTRY-001不变断言一次通过、独立相邻共15 passed；新P1 P4-C12-R2-REGISTRY-PATH-001，同路径不同route ID仍accepted:2，首次失败已保留。开发26 passed单列，不抵消路径失败。\n- P4-B仍0 passed、1 failed、19 blocked、4 not_run；UI-04 failed原因现为path冲突，旧setting首次失败保持历史原样；OUTBOX-001关闭及旧outbox42证据不重复。\n- 产品0/8、辅助Electron0/4，因新P1停止。真实老化原生提示unverified，Windows/Tray/启动项/多屏/主题等原人工步骤继续not_run，未要求用户立即操作；未执行设置/安全/HTML/lazy/generated/ZIP/staging新门禁。\n- 证据：`tests/independent/desktop/evidence/r2/original-registry/`及`remaining-independent/`首次log/JSON；原文prefix、旧R1报告/evidence不改写。没有产品或Git写操作，交总控裁定。\n'
    for p in [OLD_REPORT,MANUAL]:
        with (ROOT/p).open('ab') as f:f.write(appendix.encode('utf-8'))
    note='\n#### C12-R2 最新状态备注（2026-10-02）\n\n- 原setting REGISTRY-001原断言唯一一次通过，建议关闭；新P1 `P4-C12-R2-REGISTRY-PATH-001`：不同route ID同path被接受，原UI-04仍failed；历史首次失败/备注不改写。\n- 独立16 unique executed：15 passed、1 failed；开发registry26 passed兼容单列。整项仍0 passed、1 failed、19 blocked、4 not_run；产品0/8、辅助Electron0/4，因新P1停止，不将部分成功计入整项。\n- 旧outbox42不重跑；原生老化提示unverified、真实Windows及原人工条件未执行。[R2完整报告](phase-4-c12-r2-registry-windows-report.md)逐项保留完整原预期、历史部分、本轮执行和缺口。停止blocked / finished，最终接受归总控。\n\n'
    new=b.replace(b'### 5.3',note.encode('utf-8')+b'### 5.3',1); (ROOT/MATRIX).write_bytes(new)
    print('prepared: report, append-only historical documents, B-only notes, role milestone; no tests executed')
elif sys.argv[1]=='finalize':
    from datetime import datetime
    clock=datetime.now().strftime('%Y-%m-%d %H:%M')
    update_role('C12-R2脱敏报告与24项完整映射交付；原setting建议关闭，新path P1阻塞，停止','blocked',clock,'独立16：15 passed/1 failed；兼容26 passed；327终点审核与交付证据见evidence/r2','已安全停止；等待总控接收报告和裁定新路径P1，不自行续跑',f'### {clock} Asia/Shanghai — C12-R2 blocked / finished交付与停止\n\n- [R2完整报告](../../testing/phase-4-c12-r2-registry-windows-report.md)含24项完整原预期/历史部分/本次执行/具体缺口，原主报告和人工清单仅追加；矩阵仅B备注、状态仍0 passed/1 failed/19 blocked/4 not_run。\n- 原REGISTRY-001独立建议关闭：原13一次通过，相邻6、新registry8通过；新P1 P4-C12-R2-REGISTRY-PATH-001首次accepted:2，日志/JSON和最小复现保留，未改产品或重跑失败。开发26兼容单列；旧outbox42不重复。\n- 产品0/8、辅助Electron0/4；无外部profile/窗口/端口或owned进程，所有Vitest命令已退出。实际native dialog unverified，Windows与人工条件未执行。\n- 终点审核以 [end-audit](../../../tests/independent/desktop/evidence/r2/end-audit.json) 和 [delivery verification](../../../tests/independent/desktop/evidence/r2/delivery-verification.json) 为准；旧独立/R1报告/evidence精确保留，EXE/asar/lock/fuses不变；只清理本轮缓存，结果永久保留。\n- 交接总控：关闭旧设置键缺陷建议与新路由路径P1分别裁定；不派发后续角色、不进入P4-C、不Git写入，停在blocked / finished。\n')
    print('role finalized blocked / finished; audit verification follows, no target tests')
elif sys.argv[1]=='verify':
    manifest=ROOT/'docs/coordination/snapshots/p4-c12-r2-start.sha256'; unchanged=[]; changed=[]; bad=[]; missing=[]
    for line in manifest.read_text(encoding='utf-8-sig').splitlines():
        p,sha=line.split('\t'); file=ROOT/p
        if not file.is_file(): missing.append(p)
        elif digest(file.read_bytes())==sha: unchanged.append(p)
        elif p in ALLOWED: changed.append(p)
        else: bad.append(p)
    staged=subprocess.run(['git','diff','--cached','--name-only'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines()
    external=Path('C:/MarisRegistryR3/R3-20261002-111556/workspace'); start=json.loads((OWN/'start-audit.json').read_text(encoding='utf-8-sig')); artifacts={}
    for p in ['apps/desktop/out/Maris-win32-x64/Maris.exe','apps/desktop/out/Maris-win32-x64/resources/app.asar','pnpm-lock.yaml']:
        artifacts[p]=digest((external/p).read_bytes()); assert artifacts[p]==start[p]
    with (external/'apps/desktop/out/Maris-win32-x64/Maris.exe').open('rb') as f:
        with mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as m:
            sentinel=b'dL7pKGdnNz796PbbjQWNKmHXBZaB9tsX'; index=m.find(sentinel); assert index>=0
            offset=index+len(sentinel); version,length=m[offset],m[offset+1]; wire=list(m[offset+2:offset+2+length])
    assert version==1 and wire[:6]==[48,49,48,48,49,49]
    audit={'entries':len(unchanged)+len(changed)+len(bad)+len(missing),'unchanged':len(unchanged),'authorized_changed':changed,'unauthorized_mismatch':bad,'missing':missing,'manifest_sha256':digest(manifest.read_bytes()),'staged_paths':staged,'artifacts':artifacts,'fuses':{'version':version,'wire':wire},'old_independent_unchanged':sum(p.startswith('tests/independent/desktop/') for p in unchanged)}
    save('end-audit.json',audit)
    assert audit['entries']==327 and len(unchanged)==323 and set(changed)==ALLOWED and not bad and not missing and not staged
    baseline=json.loads((OWN/'matrix-baseline.json').read_text(encoding='utf-8')); b=read(MATRIX); prefix,_,suffix=split_matrix(b); allrows=rows(b.decode('utf-8-sig')); brows=[r for r in allrows if r[1]=='B']
    assert len(allrows)==len({r[0] for r in allrows})==120 and all(len(r)==12 for r in allrows)
    assert [r[:11] for r in brows]==[r[:11] for r in baseline['cases']]
    assert digest(prefix)==baseline['prefix_sha256'] and digest(suffix)==baseline['suffix_sha256']
    counts={s:{state:sum(r[1]==s and r[11]==state for r in allrows) for state in ['passed','failed','blocked','not_run']} for s in 'ABCD'}
    assert counts['A']['passed']==64 and counts['C']['not_run']==20 and counts['D']['not_run']==12 and counts['B']=={'passed':0,'failed':1,'blocked':19,'not_run':4}
    appendproof={}
    for p,old in baseline['append_files'].items():
        data=read(p); assert digest(data[:old['length']])==old['sha256']; appendproof[p]={'original_prefix_sha256':old['sha256'],'original_prefix_bytes':old['length'],'appended_bytes':len(data)-old['length'],'prefix_preserved':True}
    phase_nodes()
    newfiles=[p for p in (ROOT/'tests/independent/desktop').glob('r2-*') if p.is_file()]+[ROOT/REPORT]+[p for p in OWN.rglob('*') if p.is_file() and 'cache' not in p.parts and 'compat-cache' not in p.parts and p.name!='delivery-verification.json']
    save('delivery-verification.json',{'matrix_unique_ids':120,'columns':12,'counts':counts,'original_b_first_11_columns_preserved':True,'outside_b_prefix_suffix_preserved':True,'append_files':appendproof,'new_files_sha256':{p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in sorted(newfiles)},'product_starts':0,'auxiliary_electron_starts':0,'owned_resources':'not_started; not a cleanup test','git_writes':0})
    print(json.dumps({'audit':audit,'matrix_counts':counts,'append_only_verified':True},ensure_ascii=False,indent=2))
else: raise SystemExit('prepare or verify required')
