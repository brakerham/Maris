"""R10 final read-only audit. Does not run tests, product or native helper."""
import pathlib, hashlib, json, datetime, stat, re, subprocess
ROOT=pathlib.Path('D:/CodeX_gap/wife-system')
OWN=ROOT/'tests/independent/desktop'
EV=OWN/'evidence/r10-settings'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def verify(base,manifest,expected_count=None,expected_sha=None,allow=()):
    rows=manifest.read_text(encoding='utf-8').splitlines();paths=[];changes=[]
    for line in rows:
        cols=line.split('\t');assert len(cols) in (2,3),'column_count'
        rel=cols[0];assert rel not in paths and '..' not in pathlib.PurePosixPath(rel).parts and not pathlib.PurePosixPath(rel).is_absolute(),'manifest_path';paths.append(rel)
        p=base/rel
        if not p.is_file() or sha(p)!=cols[-1] or len(cols)==3 and p.stat().st_size!=int(cols[1]):changes.append(rel)
    result={'entries':len(rows),'matched':len(rows)-len(changes),'changes':changes,'manifestSha256':sha(manifest)}
    result['passed']=(expected_count is None or len(rows)==expected_count) and (expected_sha is None or sha(manifest)==expected_sha) and set(changes)<=set(allow)
    return result
def profile(base,mf,count):
    result=verify(base,mf,count)
    actual={p.relative_to(base).as_posix() for p in (base/'profile-main').rglob('*') if p.is_file()}|{'continuity.json'}
    wanted={s.split('\t')[0] for s in mf.read_text(encoding='utf-8').splitlines()}
    checked=[base,base/'profile-main',base/'continuity.json',*list((base/'profile-main').rglob('*'))]
    no_reparse=all(not p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT for p in checked)
    result.update(inventoryEqual=actual==wanted,noReparse=no_reparse)
    result['passed'] &= result['inventoryEqual'] and no_reparse
    return result
def matrix_rows(text):
    result={}
    for line in text.splitlines():
        if re.match(r'^\| P4[ABCD]-',line):
            cols=[s.strip() for s in line.strip('|').split('|')];assert len(cols)==12,'matrix_columns';assert cols[0] not in result,'duplicate_id';result[cols[0]]=cols
    return result
if __name__=='__main__':
    start=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
    allowed=['docs/coordination/agents/tester.md','docs/testing/phase-4-c12-windows-shell-report.md','docs/testing/phase-4-c12-manual-checklist.md','docs/testing/phase-4-modular-agent-host-test-matrix.md']
    result={'startedAt':start}
    result['repository']=verify(ROOT,ROOT/'docs/coordination/snapshots/p4-c12-r10-settings-start.sha256',1381,'7ebea7c1cd0866623acd4ffcdbeb7df0ff1cab25c96db2ee5b1c0fee66280ed8',allowed)
    fixed=json.loads((EV/'fixed-input-audit.json').read_text(encoding='utf-8'))
    result['fixed']={k:verify(pathlib.Path(v['base']),pathlib.Path(v['manifest']),v['entries'],v['sha256']) for k,v in fixed['fixed'].items()}
    result['singles']=[{'path':v['path'],'sha256':sha(pathlib.Path(v['path'])),'passed':sha(pathlib.Path(v['path']))==v['sha256']} for v in fixed['singles']]
    tool=json.loads((EV/'tool-entries.json').read_text(encoding='utf-8'))
    result['toolEntries']=[{'path':v['path'],'passed':sha(pathlib.Path(v['path']))==v['sha256']} for v in tool['checks']]
    result['fullDependencyRescan']=False
    result['oldFirst']={folder:verify(ROOT,OWN/'evidence'/folder/'first-materials.sha256',count) for folder,count in [('r9-quit',68),('r9-r1',38),('r9-r2',89),('r9-r3',148)]}
    oldmf=OWN/'evidence/r9-r1/original-profile.tsv'
    result['oldProfiles']={label:profile(pathlib.Path(base),oldmf,63) for label,base in [('R9','C:/MarisC12/C12-R9-QUIT-20261016-011200'),('R1','C:/MarisC12/C12-R9-R1-20261017-001500'),('R2','C:/MarisC12/C12-R9-R2-20261017-233500')]}
    result['oldProfiles']['R3afterW2']=profile(pathlib.Path('C:/MarisC12/C12-R9-R3-20261018-105500'),OWN/'evidence/r9-r3/new-profile-after-W2.tsv',65)
    result['newFirst']=verify(EV,EV/'first-materials.sha256')
    result['formalSource']=verify(OWN,EV/'independent-source.sha256',8,'7b1a207b0356579c76f1d3f62f7fbc64cee18eec5e73ef5a081ae215e879d5af')
    result['sourceArchive']={'passed':all(sha(EV/'independent-first-source'/pathlib.Path(line.split('\t')[0]).name)==line.split('\t')[1] for line in (EV/'independent-source.sha256').read_text(encoding='utf-8').splitlines()),'entries':8}
    before=matrix_rows((EV/'baseline-phase-4-modular-agent-host-test-matrix.md').read_text(encoding='utf-8'))
    after=matrix_rows((ROOT/'docs/testing/phase-4-modular-agent-host-test-matrix.md').read_text(encoding='utf-8'))
    same_ids=set(before)==set(after) and len(after)==120
    changed=[k for k,v in after.items() if v!=before.get(k)]
    expectations=all(after[k][:-1]==before[k][:-1] for k in after)
    acd=all(v==before[k] for k,v in after.items() if not k.startswith('P4B-'))
    counts={s:sum(v[-1]==s for k,v in after.items() if k.startswith('P4B-')) for s in ['passed','failed','blocked','not_run']}
    result['matrix']={'entries':len(after),'sameUniqueIds':same_ids,'columns':12,'changedRows':changed,'allExpectationsAndRiskUnchanged':expectations,'ACDUnchanged':acd,'B':counts,'passed':same_ids and expectations and acd and changed==['P4B-SEC-04'] and counts=={'passed':1,'failed':3,'blocked':18,'not_run':2}}
    result['appendOnly']={name:(ROOT/'docs/testing'/name).read_bytes().startswith((EV/('baseline-'+name)).read_bytes()) for name in ['phase-4-c12-windows-shell-report.md','phase-4-c12-manual-checklist.md']}
    events=[json.loads(s) for s in (EV/'independent/journal.jsonl').read_text(encoding='utf-8').splitlines()]
    enters=[s for s in events if s['event']=='assert_enter'];ends=[s for s in events if s['event']=='assert_terminal']
    cleanup=[s for s in events if s['event']=='cleanup_terminal']
    result['formalEvidence']={'comparisons':len(ends),'passedComparisons':sum(s['passed'] for s in ends),'unique':len({s['id'] for s in enters})==len(enters),'paired':len(enters)==len(ends) and all(sum(e['id']==s['id'] for e in ends)==1 for s in enters),'cleanupCount':len(cleanup),'cleanupPassed':all(s['passed'] for s in cleanup)}
    proc=json.loads((EV/'independent/process.json').read_text(encoding='utf-8'))
    result['process']={'actualRootExit':proc['rootExitCode'],'rootExited':proc['rootExited'],'workers':proc['workers'],'forced':proc['forced'],'timedOut':proc['timedOut'],'fullSystemResourceQuery':'not_run'}
    staged=subprocess.run(['git','diff','--cached','--name-only'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines()
    result['stagedCount']=len(staged)
    diff=subprocess.run(['git','diff','--check','--',*allowed],cwd=ROOT,capture_output=True,text=True)
    result['sharedDiffCheck']={'exitCode':diff.returncode,'outputLines':len(diff.stdout.splitlines()),'stderrLines':len(diff.stderr.splitlines())}
    result['passed']=all([result['repository']['passed'],*(v['passed'] for v in result['fixed'].values()),*(v['passed'] for v in result['singles']),*(v['passed'] for v in result['toolEntries']),*(v['passed'] for v in result['oldFirst'].values()),*(v['passed'] for v in result['oldProfiles'].values()),result['newFirst']['passed'],result['formalSource']['passed'],result['sourceArchive']['passed'],result['matrix']['passed'],*result['appendOnly'].values(),result['formalEvidence']['unique'],result['formalEvidence']['paired'],result['formalEvidence']['cleanupPassed'],not staged,diff.returncode==0])
    result['finishedAt']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
    with (EV/'end-audit.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(result,ensure_ascii=False));raise SystemExit(0 if result['passed'] else 1)
