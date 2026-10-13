"""Read-only input/first-evidence audit; writes only this task's new audit receipt."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OWN = ROOT / 'tests/independent/desktop'
EV = OWN / 'evidence/r8-modules'
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

start = read_json(EV/'start-audit.json')
audit = {'at': datetime.datetime.now().astimezone().isoformat(), 'inputs': {}}
for key in ['start','r6Source','buildSource','out','resources','dependencies','dist','r7Delivery']:
    item=start[key]
    allowed = SHARED | COORDINATOR if key=='r6Source' else SHARED if key in ['start','r7Delivery'] else set()
    audit['inputs'][key]=verify(Path(item['manifest']),Path(item['base']),allowed,item['sha256'],key in ['out','resources','dist'],['app.asar'] if key=='resources' else [])
full_dependencies=Path(start['dependencies']['manifest']).with_name('old-r5-full-node-modules.sha256')
audit['fullDependencyCopyAdditionalEndCheck']=verify(full_dependencies,Path(start['dependencies']['base']),inventory=True)
for name, base in [('modules-source.sha256',OWN),('modules-first.sha256',ROOT)]:
    audit[name]=verify(EV/name,base)
build=Path(start['buildSource']['base'])
for rel,digest in start['artifacts'].items():
    assert sha((build/rel).read_bytes())==digest, 'artifact_changed'
audit['artifactDigestsMatched']=len(start['artifacts'])
for info in start['versions'].values():
    data=Path(info['path']).read_bytes()
    assert sha(data)==info['packageSha256'] and json.loads(data)['version']==info['version'], 'dependency_metadata_changed'
audit['versionMetadataMatched']=len(start['versions'])
baseline=read_json(EV/'baseline.json')
matrix=(ROOT/'docs/testing/phase-4-modular-agent-host-test-matrix.md').read_bytes()
rows=[[c.strip() for c in line.strip().strip('|').split('|')] for line in matrix.decode('utf-8').splitlines() if line.startswith('| P4')]
rows=[c for c in rows if len(c)==12 and c[0].startswith(('P4A-','P4B-','P4C-','P4D-'))]
assert rows==baseline['cases'] and len(rows)==120 and len({row[0] for row in rows})==120, 'matrix_rows_changed'
assert sha(matrix.split(b'### 5.2')[0])==baseline['outside_b_prefix'], 'matrix_a_changed'
assert sha(b'### 5.3'+matrix.split(b'### 5.3',1)[1])==baseline['outside_b_suffix'], 'matrix_cd_changed'
for rel,info in baseline['append_files'].items():
    data=(ROOT/rel).read_bytes()
    assert len(data)>info['bytes'] and sha(data[:info['bytes']])==info['sha256'], 'old_document_prefix_changed'
audit['matrix']={'uniqueRows':120,'columns':12,'allOriginalRowsUnchanged':True,'outsideBBytesUnchanged':True,'BStates':{s:sum(row[1]=='B' and row[-1]==s for row in rows)for s in ['passed','failed','blocked','not_run']}}
audit['appendOnlyDocumentPrefixesMatched']=2
events=[json.loads(line)for line in (EV/'modules/worker.journal.jsonl').read_text(encoding='utf-8').splitlines()]
starts=[e for e in events if e['event']=='assert_enter']
ends=[e for e in events if e['event']in ['assert_pass','assert_fail']]
assert len(starts)==len(ends)==395 and len({e['details']['id']for e in starts})==395
assert all(sum(t['details']['id']==e['details']['id']for t in ends)==1 for e in starts)
audit['firstResult']={'nodes':read_json(EV/'modules/result.json')['nodes'],'formalComparisons':393,'comparisonPairs':395,'runtimeProductStarts':0,'helperStarts':0,'reruns':0,'compatibilityExecuted':0,'firstFailureLabelLimitation':'Helper duplicate-ID exception is outside reporter firstFailure field; original null retained, explained by first-run-analysis.json.'}
audit['process']=read_json(EV/'modules/process.json')
checks={}
for name,args in [('staged',['git','diff','--cached','--name-only']),('diffCheck',['git','diff','--check'])]:
    result=subprocess.run(args,cwd=ROOT,capture_output=True)
    checks[name]={'exitCode':result.returncode,'stdoutBytes':len(result.stdout),'stderrBytes':len(result.stderr),'warningCategories':[]}
    if result.stderr:
        txt=result.stderr.decode('utf-8',errors='replace')
        for needle,label in [('Permission denied','global_config_permission_denied'),('LF will be replaced by CRLF','line_ending_conversion_warning')]:
            if needle in txt: checks[name]['warningCategories'].append(label)
        if not checks[name]['warningCategories']: checks[name]['warningCategories'].append('other_read_only_git_warning')
    assert result.returncode==0 and not result.stdout.strip(), 'git_read_only_gate'
audit['readOnlyGit']=checks
audit['passed']=True
(EV/'end-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'auditPassed':True,'inputs':{k:{f:v for f,v in row.items()if f in ['entries','unchanged','authorizedChanges']}for k,row in audit['inputs'].items()},'readOnlyGit':checks},ensure_ascii=False))
