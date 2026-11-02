"""Read-only final verification; no test, product, native helper or service execution."""
from pathlib import Path
import hashlib,json,datetime,stat,re,subprocess,importlib.util
ROOT=Path('D:/CodeX_gap/wife-system');OWN=ROOT/'tests/independent/desktop';EV=OWN/'evidence/r11-origin-settings'
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,file);obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
base=load('r11audit',OWN/'r11-origin-settings-audit.py')
old=load('historical_read_only_audit_helpers',OWN/'r10-settings-end-audit.py')
sha=base.sha
def own_manifest(mf):
    rows=mf.read_text(encoding='utf-8').splitlines();bad=[];seen=set()
    for row in rows:
        rel,digest=row.split('\t');assert rel not in seen;seen.add(rel)
        p=(OWN/rel).resolve();assert p.is_relative_to(ROOT)
        if not p.is_file() or sha(p)!=digest:bad.append(rel)
    return {'entries':len(rows),'changed':bad,'sha256':sha(mf),'passed':not bad}
if __name__=='__main__':
    allowed=['docs/coordination/agents/tester.md','docs/testing/phase-4-c12-windows-shell-report.md','docs/testing/phase-4-c12-manual-checklist.md','docs/testing/phase-4-modular-agent-host-test-matrix.md']
    r={'startedAt':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()}
    r['repository']=old.verify(ROOT,ROOT/'docs/coordination/snapshots/p4-c12-r11-origin-settings-start.sha256',1438,'5286d9c16aa862f61046080fafae3d5a37f205d2e1a4b27ed6d4616fb1524fc1',allowed)
    fixed=json.loads((EV/'fixed-input-audit.json').read_text(encoding='utf-8'));r['fixed']={}
    overrides={rel:EV/('baseline-'+Path(rel).name) for rel in allowed}
    for k,v in fixed['results'].items():
        r['fixed'][k]=base.verify(Path(v['base']),Path(v['manifest']),v['entries'],v['sha256'],overrides if k=='R10delivery' else None)
    r['toolsAndSingles']=[{'path':v['path'],'sha256':sha(Path(v['path'])),'passed':sha(Path(v['path']))==v['sha256']}for v in fixed['actualToolEntries']+fixed['singles']]
    r['oldFirst']={folder:old.verify(ROOT,OWN/'evidence'/folder/'first-materials.sha256',count) for folder,count in [('r9-quit',68),('r9-r1',38),('r9-r2',89),('r9-r3',148)]}
    mf=OWN/'evidence/r9-r1/original-profile.tsv'
    r['oldProfiles']={label:old.profile(Path(p),mf,63)for label,p in [('W1','C:/MarisC12/C12-R9-QUIT-20261016-011200'),('R1','C:/MarisC12/C12-R9-R1-20261017-001500'),('R2','C:/MarisC12/C12-R9-R2-20261017-233500')]}
    r['oldProfiles']['R3afterW2']=old.profile(Path('C:/MarisC12/C12-R9-R3-20261018-105500'),OWN/'evidence/r9-r3/new-profile-after-W2.tsv',65)
    r['source']={mode:own_manifest(EV/(mode+'-source.sha256'))for mode in ['independent','compat']}
    r['firstMaterials']=base.verify(EV,EV/'first-materials.sha256',90)
    r['sourceArchive']=base.verify(EV,EV/'source-archive.sha256',50)
    before=old.matrix_rows((EV/'baseline-phase-4-modular-agent-host-test-matrix.md').read_text(encoding='utf-8'));after=old.matrix_rows((ROOT/'docs/testing/phase-4-modular-agent-host-test-matrix.md').read_text(encoding='utf-8'))
    changed=[k for k,v in after.items()if v!=before.get(k)];counts={s:sum(v[-1]==s for k,v in after.items()if k.startswith('P4B-'))for s in ['passed','failed','blocked','not_run']}
    r['matrix']={'entries':len(after),'columns':12,'uniqueSameIds':len(after)==120 and set(after)==set(before),'changedRows':changed,'expectationsAndRiskUnchanged':all(v[:-1]==before[k][:-1] for k,v in after.items()),'ACDUnchanged':all(v==before[k]for k,v in after.items()if not k.startswith('P4B-')),'B':counts}
    r['matrix']['passed']=all([r['matrix']['uniqueSameIds'],r['matrix']['expectationsAndRiskUnchanged'],r['matrix']['ACDUnchanged'],changed==['P4B-SEC-04'],counts=={'passed':1,'failed':2,'blocked':19,'not_run':2}])
    r['appendOnly']={name:(ROOT/'docs/testing'/name).read_bytes().startswith((EV/('baseline-'+name)).read_bytes())for name in ['phase-4-c12-windows-shell-report.md','phase-4-c12-manual-checklist.md']}
    journal=[json.loads(line)for line in (EV/'independent/journal.jsonl').read_text(encoding='utf-8').splitlines()];enters=[e for e in journal if e['event']=='assert_enter'];ends=[e for e in journal if e['event']=='assert_terminal'];cleanup=[e for e in journal if e['event']=='cleanup_terminal']
    r['comparisons']={'count':len(ends),'passedCount':sum(e['passed']for e in ends),'unique':len(set(e['id']for e in ends))==len(ends),'paired':len(enters)==len(ends) and all(sum(x['id']==e['id'] for x in ends)==1 for e in enters),'cleanupCount':len(cleanup),'cleanupPassed':all(e['passed']for e in cleanup)}
    r['runs']={}
    for mode,n in [('independent',41),('compat',109)]:
        v=json.loads((EV/mode/'result.json').read_text(encoding='utf-8'));p=json.loads((EV/mode/'process.json').read_text(encoding='utf-8'))
        r['runs'][mode]={'nodes':v['passed'],'failed':v['failed'],'notRun':v['notRun'],'rootExitCode':p['rootExitCode'],'rootExited':p['rootExited'],'workers':p['workers'],'forced':p['forced'],'timedOut':p['timedOut'],'passed':v['passed']==n and not any(v[k] for k in ['failed','notRun','unhandledErrors','moduleErrors']) and p['rootExitCode']==0 and p['rootExited'] and not any(p[k]for k in ['forced','timedOut','failure']) and all(w['exited']and w['identityVerified']and not w['forced']for w in p['workers'])}
    r['windows']={'productStarts':0,'nativeHelperStarts':0,'seriesProducts':2,'seriesHelpers':3,'profileCreated':False,'resourceQuery':'failed at process_query; unknown CimException; no global-zero claim','acceptance':'not_run'}
    r['stagedCount']=len(subprocess.run(['git','diff','--cached','--name-only'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines())
    diff=subprocess.run(['git','diff','--check','--',*allowed,'docs/testing/phase-4-c12-r11-origin-settings-windows-report.md'],cwd=ROOT,capture_output=True,text=True);r['sharedDiffCheck']={'exitCode':diff.returncode,'stdoutLines':len(diff.stdout.splitlines()),'stderrLines':len(diff.stderr.splitlines())}
    r['passed']=all([r['repository']['passed'],*(v['passed']for v in r['fixed'].values()),*(v['passed']for v in r['toolsAndSingles']),*(v['passed']for v in r['oldFirst'].values()),*(v['passed']for v in r['oldProfiles'].values()),*(v['passed']for v in r['source'].values()),r['firstMaterials']['passed'],r['sourceArchive']['passed'],r['matrix']['passed'],*r['appendOnly'].values(),r['comparisons']['unique'],r['comparisons']['paired'],r['comparisons']['cleanupPassed'],r['comparisons']['count']==321,*(v['passed']for v in r['runs'].values()),r['stagedCount']==0,diff.returncode==0])
    r['finishedAt']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
    with (EV/'end-audit.json').open('x',encoding='utf-8') as f:json.dump(r,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'passed':r['passed'],'repository':r['repository'],'fixed':{k:(v['entries'],v['matched'])for k,v in r['fixed'].items()},'matrix':r['matrix'],'source':r['source'],'first':r['firstMaterials']['entries'],'stagedCount':r['stagedCount'],'diffCheck':r['sharedDiffCheck']},ensure_ascii=False));raise SystemExit(0 if r['passed'] else 1)
