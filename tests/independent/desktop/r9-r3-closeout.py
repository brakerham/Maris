"""Prepare/verify R3 documentation and evidence only; never launch targets."""
from pathlib import Path
import collections, datetime, hashlib, json, sys

ROOT = Path(__file__).resolve().parents[3]
E = ROOT/'tests/independent/desktop/evidence/r9-r3'
SHARED = ['docs/coordination/agents/tester.md','docs/testing/phase-4-c12-windows-shell-report.md',
          'docs/testing/phase-4-c12-manual-checklist.md','docs/testing/phase-4-modular-agent-host-test-matrix.md']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f:
        json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def manifest(dest, files):
    names=sorted({p.relative_to(ROOT).as_posix() for p in files})
    with dest.open('x',encoding='utf8',newline='\n') as f:
        for name in names: f.write(name+'\t'+sha(ROOT/name)+'\n')
    return names

def prepare():
    w=load(E/'windows-W2/result.json');h=load(E/'helper-H1/process.json')
    j=[json.loads(l) for l in (E/'windows-W2/journal.jsonl').read_text().splitlines()]
    sample=next(v for v in j if v['event']=='first_ui_sample')
    assert sample['details']['settingsBytesUnchanged'] and sample['details']['settingsWritesBeforeSample']==0
    assert h['passed'] and not w['passed'] and w['firstFailure']['id']=='W2-PERSISTED-UI-THEME'
    save(E/'w2-first-analysis.json',{'at':datetime.datetime.now().astimezone().isoformat(),
      'defect':'P4-C12-R9-R3-SETTINGS-001','severityProposed':'P1','category':'product_comparison_failure',
      'firstFailure':w['firstFailure'],'firstSample':sample,'failedComparisons':[v for v in w['comparisons'] if not v['passed']],
      'subsequentBusinessActionsRun':False,'knownOwnerIdentity':True,'deviceUnsupported':False,
      'sourcePointer':{'path':'apps/desktop/src/renderer/module-routes.tsx','sha256':sha(ROOT/'apps/desktop/src/renderer/module-routes.tsx'),'initialStateLines':[100,101],'saveCallbackLines':[168,169,170]},
      'sourceInference':'component initializes system/false and has update callbacks; actual UI evidence is authoritative',
      'realPersonalDataUsed':False,'actualFinancialDisclosureTested':False,
      'cleanup':{k:w[k] for k in ['forced','cleanupError','exit','remainingOwned','remainingListeners','remainingWindows']}})
    save(E/'budget-ledger.json',{'task':'P4-C12-R9-R3','product':{'before':1,'thisTask':w['productStarts'],'thisTaskLimit':7,'seriesUsed':2,'seriesLimit':8},
      'safeStorage':{'before':2,'thisTask':h['helperStarts'],'thisTaskLimit':4,'seriesUsed':3,'seriesLimit':6},
      'H1':{'used':1,'limit':1,'passed':True},'localToolRounds':{'used':1,'limit':3,'checks':30,'realDecryptCalls':0},
      'oldPassedCollectionsRerun':0,'liveNodeGateRun':0,'chunkInjections':0,'H2Seed':False,
      'notRun':['W2-PERSISTED-REQUEST-ID','W3','H2','W4','H3','W5','H4','W6','reservedWindowsScenarios'],
      'stopReason':'first valid W2 product comparison failed; remaining allocation is not rerun authority'})
    save(E/'scenario-status.json',{'H1':'passed','W2':'failed','W2BeforeFailure':{'comparisonsPassed':8,'comparisonsFailed':4},
      'remaining':[{'id':v,'status':'not_run','actual':None,'reason':'W2 first valid product failure stop'} for v in
        ['W2-PERSISTED-REQUEST-ID','W3-SECOND-EXIT','W3-FIRST-ALIVE','W3-HOST-IDENTITY-UNCHANGED','W2-HINT-PERSISTED','W2-FIRST-HIDE','W2-COMPANION-RESTORES','W2-CANCEL-ALIVE','W2-CANCEL-VISIBLE','W2-ASK-HIDE','H2','W4','H3','W5','H4','W6']],
      'manualConditions':'unverified; no user action requested; no device incapability inferred'})
    # Byte-preserving append only for legacy reports.
    appendix='''\n\n## R9-R3同源H1与W2首次恢复失败（2026-10-18）

[R9-R3独立增量报告](phase-4-c12-r9-r3-storage-windows-report.md)：1192起点匹配；唯一局部工具轮30/30通过。预置同源Local State、ready前绑定userData/sessionData并分段记录后，新H1原生7/7、helper/controller exit0、产品副本63项保持及资源全零。该成功不倒推旧operation_error精确阶段。

随后同任务唯一W2在首次设置界面比较失败：保存dark/隐私true，实际页面system/off、主题控件system/隐私checkbox false；设置取样前未写入且字节不变。登记P1 P4-C12-R9-R3-SETTINGS-001，四比较来自同一首样。产品普通WM_CLOSE后自然exit0、owned/listener/window=0，无强制结束；controller exit1保留失败。W3、H2、W4/H3、W5/H4、W6及剩余原生/人工条件not_run，不声称设备不支持。

本轮产品1/7、辅助1/4；系列产品2/8、辅助3/6（含两次旧失败H1）。旧退出/48兼容/W1/模块/冷入口/恢复/38路径及现场Node均未重跑。B为1 passed、2 failed、19 blocked、2 not_run：CMP-06仅因主题恢复子条件改failed，其余设备子条件未验；CMP-05多屏/金额隐藏/键盘等人工条件仍not_run，隐私开关恢复失败单独记录。UI-02/LAZY-001保持。原首次材料和本文旧字节保留，最终blocked / finished供总控review，不请求用户此刻操作。
'''
    for name in ['phase-4-c12-windows-shell-report.md','phase-4-c12-manual-checklist.md']:
        target=ROOT/'docs/testing'/name
        assert target.read_bytes()==(E/('baseline-'+name)).read_bytes(), 'legacy_already_changed'
        with target.open('ab') as f: f.write(appendix.encode('utf8'))
    matrix=ROOT/'docs/testing/phase-4-modular-agent-host-test-matrix.md'
    raw=matrix.read_bytes(); assert raw==(E/('baseline-'+matrix.name)).read_bytes()
    lines=raw.splitlines(keepends=True)
    count=0
    for i,line in enumerate(lines):
        if line.startswith(b'| P4B-CMP-06 |'):
            assert b'| not_run |' in line
            lines[i]=line.replace(b'| not_run |',b'| failed |'); count+=1
    assert count==1
    note='''R9-R3（2026-10-18）增量：1192起点通过；虚拟局部工具30/30与同源H1完整7/7通过，H1前后副本63项保持、原生/helper/controller exit0、资源全零。旧operation_error精确原因仍unknown，不倒写。唯一W2首样保存dark/隐私true，页面system/off及控件system/false，四比较失败；设置取样前未写且字节不变。新P1 P4-C12-R9-R3-SETTINGS-001；CMP-06主题恢复子条件failed，原风险P2/完整预期保持，透明/OS主题/对比/动效/颜色未验；隐私开关恢复失败不代替CMP-05多屏/金额隐藏等未运行条件。B为1passed、2failed、19blocked、2not_run。普通关窗自然exit0、无forced、资源全零；controller exit1。W3/H2及后续not_run。系列产品2/8、辅助3/6；旧集合不重跑，UI-02/LAZY-001和P4-B不关闭。详见[R9-R3报告](phase-4-c12-r9-r3-storage-windows-report.md)，blocked/finished供review。\n\n'''.encode('utf8')
    updated=b''.join(lines); marker=b'### 5.3'; at=updated.index(marker)
    matrix.write_bytes(updated[:at]+note+updated[at:])
    save(E/'documentation-preparation.json',{'at':datetime.datetime.now().astimezone().isoformat(),'appendedReports':2,'matrixStatusChanges':['P4B-CMP-06:not_run->failed'],'targetStarts':0})

def first():
    paths=[p for p in E.rglob('*') if p.is_file()]
    assert not (E/'first-materials.sha256').exists()
    names=manifest(E/'first-materials.sha256',paths)
    print(json.dumps({'firstMaterials':len(names),'sha256':sha(E/'first-materials.sha256')}))

def seal():
    assert load(E/'end-audit.json')['passed']
    assert load(E/'end-audit-process.json')['exit']==0
    allfiles=[p for p in E.rglob('*') if p.is_file() and p.name not in ('delivery.sha256','delivery-verification.json')]
    allfiles += [p for p in (ROOT/'tests/independent/desktop').glob('r9-r3-*') if p.is_file()]
    allfiles += [ROOT/p for p in SHARED]
    allfiles += [ROOT/'docs/testing/phase-4-c12-r9-r3-storage-windows-report.md']
    names=manifest(E/'delivery.sha256',allfiles)
    b=(E/'delivery.sha256').read_bytes(); assert not b.startswith(b'\xef\xbb\xbf') and b'\r' not in b
    for line in b.decode('utf8').splitlines():
        name,digest=line.split('\t'); assert sha(ROOT/name)==digest
    value={'at':datetime.datetime.now().astimezone().isoformat(),'entries':len(names),'matched':len(names),'unique':True,'sorted':True,'utf8NoBomLf':True,
      'manifestSha256':sha(E/'delivery.sha256'),'firstMaterialsSha256':sha(E/'first-materials.sha256'),
      'status':'blocked','runtimeStatus':'finished','handoff':'review','productStarts':1,'helperStarts':1,'seriesProductStarts':2,'seriesHelperStarts':3,
      'newDefect':'P4-C12-R9-R3-SETTINGS-001','H1':'passed','W2':'failed','targetReruns':0,'gitWrites':0,'passed':True}
    save(E/'delivery-verification.json',value); print(json.dumps(value))

if __name__=='__main__': {'prepare':prepare,'first':first,'seal':seal}[sys.argv[1]]()
