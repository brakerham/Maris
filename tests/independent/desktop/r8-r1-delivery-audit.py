"""Read-only input/first-evidence audit; writes only this task's new audit receipt."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OWN = ROOT / 'tests/independent/desktop'
EV = OWN / 'evidence/r8-r1'
SHARED = {
    'docs/coordination/agents/tester.md',
    'docs/testing/phase-4-modular-agent-host-test-matrix.md',
    'docs/testing/phase-4-c12-windows-shell-report.md',
    'docs/testing/phase-4-c12-manual-checklist.md',
}
COORDINATOR = {'README.md', 'docs/project-coordination.md', 'docs/coordination/control.md',
               'docs/coordination/overview.md', 'docs/coordination/agents/brainstorm.md'}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))

def verify(manifest, base, allowed=(), expected_digest=None, inventory=False, excluded_files=()):
    raw = manifest.read_bytes()
    if expected_digest:
        assert sha(raw) == expected_digest, 'manifest_changed'
    lines = raw.decode('utf-8').splitlines()
    paths, changes = [], []
    for line in lines:
        fields = line.split('\t')
        assert len(fields) in (2, 3), 'bad_manifest_columns'
        rel, digest = fields[0], fields[-1]
        assert not Path(rel).is_absolute() and '..' not in Path(rel).parts, 'manifest_boundary'
        data = (base / rel).read_bytes()
        if sha(data) != digest:
            changes.append(rel)
        if len(fields) == 3 and rel not in allowed:
            assert len(data) == int(fields[1]), 'manifest_size'
        paths.append(rel)
    assert len(paths) == len(set(paths)), 'manifest_duplicate'
    assert set(changes) <= set(allowed), 'unauthorized_change'
    result = {'entries': len(paths), 'unchanged': len(paths)-len(changes),
              'authorizedChanges': changes, 'manifestSha256': sha(raw)}
    if inventory:
        actual = {p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file()}
        result['unlistedFiles'] = sorted(actual-set(paths)-set(excluded_files))
        result['separatelyCoveredFiles'] = sorted(set(excluded_files)&actual)
        result['missingFiles'] = sorted(set(paths)-actual)
        assert not result['unlistedFiles'] and not result['missingFiles'], 'inventory_drift'
    return result

start=read_json(EV/'start-audit.json')
audit={'at':datetime.datetime.now().astimezone().isoformat(),'inputs':{}}
for key in ['start','r6Source','buildSource','out','resources','dependencies','dist','r8Delivery','r8Source','r8First']:
    item=start[key]
    allowed=SHARED|COORDINATOR if key=='r6Source' else SHARED if key in ['start','r8Delivery'] else set()
    audit['inputs'][key]=verify(Path(item['manifest']),Path(item['base']),allowed,item['sha256'],key in ['out','resources','dist'],['app.asar'] if key=='resources' else [])
    print(json.dumps({'checked':key,'entries':audit['inputs'][key]['entries'],'unchanged':audit['inputs'][key]['unchanged']}),flush=True)
old=read_json(OWN/'evidence/r8-modules/start-audit.json')['r7Delivery']
audit['inputs']['r7Delivery']=verify(Path(old['manifest']),Path(old['base']),SHARED,old['sha256'])
full=Path(start['dependencies']['manifest']).with_name('old-r5-full-node-modules.sha256')
audit['fullDependencyInventory']=verify(full,Path(start['dependencies']['base']),inventory=True)
print(json.dumps({'checked':'fullDependencyInventory','entries':audit['fullDependencyInventory']['entries']}),flush=True)
for name in ['modules-source.sha256','compat-source.sha256','public-source-final.sha256','windows-source.sha256','windows-attempt1-source.sha256']:
    audit[name]=verify(EV/name,OWN)
for name in ['modules-first.sha256','compat-first.sha256','public-first.sha256','windows-first.sha256']:
    audit[name]=verify(EV/name,ROOT)
build=Path(start['buildSource']['base'])
for rel,digest in start['artifacts'].items():assert sha((build/rel).read_bytes())==digest,'artifact_changed'
for info in start['versions'].values():
    data=Path(info['path']).read_bytes();assert sha(data)==info['packageSha256'] and json.loads(data)['version']==info['version'],'dependency_metadata_changed'
audit['artifactDigestsMatched']=len(start['artifacts']);audit['versionMetadataMatched']=len(start['versions'])
baseline=read_json(EV/'baseline.json');matrix=(ROOT/'docs/testing/phase-4-modular-agent-host-test-matrix.md').read_bytes()
rows=[[c.strip() for c in line.strip().strip('|').split('|')] for line in matrix.decode('utf-8').splitlines() if line.startswith('| P4')]
rows=[r for r in rows if len(r)==12 and r[0].startswith(('P4A-','P4B-','P4C-','P4D-'))]
assert len(rows)==120 and len({r[0] for r in rows})==120,'matrix_id_count'
for before,after in zip(baseline['cases'],rows):
    assert before[:11]==after[:11],'matrix_contract_changed'
    if before[1]!='B':assert before==after,'non_b_state_changed'
assert sha(matrix.split(b'### 5.2')[0])==baseline['outside_b_prefix'],'matrix_a_bytes_changed'
assert sha(b'### 5.3'+matrix.split(b'### 5.3',1)[1])==baseline['outside_b_suffix'],'matrix_cd_bytes_changed'
for rel,info in baseline['append_files'].items():
    data=(ROOT/rel).read_bytes();assert len(data)>info['bytes'] and sha(data[:info['bytes']])==info['sha256'],'append_prefix_changed'
audit['matrix']={'uniqueRows':120,'columns':12,'allOriginalExpectedUnchanged':True,'outsideBBytesUnchanged':True,'BStates':{s:sum(r[1]=='B' and r[-1]==s for r in rows) for s in ['passed','failed','blocked','not_run']}}
assert audit['matrix']['BStates']=={'passed':1,'failed':3,'blocked':17,'not_run':3}
audit['appendOnlyDocumentPrefixesMatched']=2
for group in ['modules','compat','public']:
    result=read_json(EV/group/'result.json');process=read_json(EV/group/'process.json')
    assert process['rootExited'] and all(w['exited'] for w in process['workers']) and not process['forced'] and not process['timedOut'],'test_process_unclean'
    audit[group]={'passed':result['passed'],'rootExitCode':process['rootExitCode'],'workerExitCodes':[w['nativeExitCode'] for w in process['workers']]}
w=read_json(EV/'windows-W1/result.json');assert w['rootExit'] and w['remainingOwned']==0 and w['remainingListeners']==0 and not w['cleanupError'],'windows_unclean'
audit['windows']={'productStarts':1,'helperStarts':0,'forcedCleanup':w['forced'],'normalExitPassed':False,'firstFailure':w['firstFailure'],'remainingOwned':0,'remainingListeners':0,'childExitCodes':'unverified'}
audit['readOnlyGit']={}
for name,args in [('staged',['git','diff','--cached','--name-only']),('diffCheck',['git','diff','--check'])]:
    r=subprocess.run(args,cwd=ROOT,capture_output=True)
    audit['readOnlyGit'][name]={'exitCode':r.returncode,'stdoutBytes':len(r.stdout),'stderrBytes':len(r.stderr)}
    assert r.returncode==0 and not r.stdout.strip(),'read_only_git_gate'
audit['passed']=True
with (EV/'end-audit.json').open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'auditPassed':True,'matrix':audit['matrix'],'windows':audit['windows']}),flush=True)
