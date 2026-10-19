"""Read-only terminal audit and safe metadata collection; no target launches."""
from pathlib import Path
import collections, datetime, hashlib, importlib.util, json, re, stat, subprocess

ROOT = Path(__file__).resolve().parents[3]
E = ROOT / 'tests/independent/desktop/evidence/r9-r3'
spec = importlib.util.spec_from_file_location('r3_audit', ROOT / 'tests/independent/desktop/r9-r3-audit.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
sha, verify = audit.sha, audit.verify

def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def save(p, value):
    with p.open('x', encoding='utf8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def files(base):
    values = [base / 'continuity.json'] + [p for p in (base / 'profile-main').rglob('*') if p.is_file()]
    for p in [base, base / 'profile-main', *list((base / 'profile-main').rglob('*'))]:
        assert not (p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT), 'profile_reparse'
    return {p.relative_to(base).as_posix(): (p.stat().st_size, sha(p)) for p in values}

def main():
    result = {'at': datetime.datetime.now().astimezone().isoformat(), 'phase': 'end', 'inputs': {}}
    result['inputs']['repository'] = verify('repository', ROOT/'docs/coordination/snapshots/p4-c12-r9-r3-start.sha256', ROOT,
        '9b9b0f977fe96900b4d05cf977f222233034fc39f8882a82ff9c2b543e2181f1', audit.SHARED)
    assert result['inputs']['repository']['entries'] == 1192
    for name in ['buildSource','out','resources','dist','dependencies','executorEvidence']:
        s = audit.START[name]
        result['inputs'][name] = verify(name, Path(s['manifest']), Path(s['base']), s['sha256'], inventory=name in ('out','resources','dist','dependencies'))
        assert result['inputs'][name]['entries'] == s['entries']
    for rel, expected in audit.START['artifacts'].items():
        assert sha(Path(audit.START['buildSource']['base'])/rel) == expected, 'artifact_changed'
    result['artifacts'] = audit.START['artifacts']
    for name, folder, count, digest in [
        ('oldR9Delivery','r9-quit',79,'3d08ba6c8246cc4f6e994cdaa75060b411dc23b6c010f5bf60b8b1acedf9443d'),
        ('oldR1Delivery','r9-r1',59,'aacbc4e24f8b87e5af37ba815cc416fe83e6d5640f85cddc97886810092d8784'),
        ('oldR2Delivery','r9-r2',114,'31722e61175b5dec530fb596178352e77a31523cd7c20c9d8074808426173be3')]:
        result['inputs'][name] = verify(name, E.parent/folder/'delivery.sha256', ROOT, digest, audit.SHARED)
        assert result['inputs'][name]['entries'] == count
    for name, folder, count in [('oldR9First','r9-quit',68),('oldR1First','r9-r1',38),('oldR2First','r9-r2',89)]:
        result['inputs'][name] = verify(name, E.parent/folder/'first-materials.sha256', ROOT)
        assert result['inputs'][name]['entries'] == count
    result['inputs']['oldR2Target'] = verify('oldR2Target', E.parent/'r9-r2/target-source.sha256', ROOT/'tests/independent/desktop')
    frozen = {}
    for manifest, archive in [('local-round1-source.sha256','local-round1-source'),('target-source.sha256','target-first-source'),('windows-w2-source.sha256','windows-w2-first-source')]:
        frozen[archive] = verify(archive, E/manifest, E/archive)
        if not archive.startswith('local-'):
            frozen[manifest] = verify(manifest, E/manifest, ROOT/'tests/independent/desktop')
    result['frozenSources'] = frozen
    expected = {r[0]:(int(r[1]),r[2]) for r in [line.split('\t') for line in (E/'original-profile.tsv').read_text().splitlines()]}
    result['oldProfiles'] = {}
    for name, base in [('R9','C:/MarisC12/C12-R9-QUIT-20261016-011200'),('R1','C:/MarisC12/C12-R9-R1-20261017-001500'),('R2','C:/MarisC12/C12-R9-R2-20261017-233500')]:
        current = files(Path(base))
        assert current == expected, 'old_profile_changed_'+name
        result['oldProfiles'][name] = {'entries':len(current),'inventoryBytesHashesEqual':True,'noReparse':True}
    base = Path(load(E/'profile-copy.json')['copyRoot'])
    current = files(base)
    inventory = ''.join(f'{name}\t{size}\t{digest}\n' for name,(size,digest) in sorted(current.items()))
    with (E/'new-profile-after-W2.tsv').open('x',encoding='utf8',newline='\n') as f: f.write(inventory)
    changed = sorted(k for k in current.keys() & expected.keys() if current[k] != expected[k])
    result['newProfile'] = {'entries':len(current), 'added':sorted(current.keys()-expected.keys()), 'removed':sorted(expected.keys()-current.keys()), 'changed':changed,
        'manifestSha256':sha(E/'new-profile-after-W2.tsv'), 'scope':'current synthetic copy after authorized product W2; no H2 seed', 'noReparse':True,
        'deviceSettingsBytesUnchanged':current['profile-main/device-settings.json']==expected['profile-main/device-settings.json'],
        'continuityBytesUnchanged':current['continuity.json']==expected['continuity.json']}
    result['H1ReadOnlyStage'] = {'passed':load(E/'helper-H1/process.json')['profileUnchanged'], 'evidence':'helper-H1/process.json; checked before W2'}
    assert result['H1ReadOnlyStage']['passed']
    h1 = load(E/'helper-H1/native-result.json'); w2 = load(E/'windows-W2/result.json')
    stages = [json.loads(l) for l in (E/'helper-H1/native-stages.jsonl').read_text().splitlines()]
    result['nativeStagesCollection'] = load(E/'helper-H1/native-collection.json')
    assert result['nativeStagesCollection']['uniqueIds'] and result['nativeStagesCollection']['stageEnters']==result['nativeStagesCollection']['stageTerminals']==39
    assert h1['passed'] and len(h1['checks'])==7 and all(c['passed'] for c in h1['checks'])
    assert not w2['passed'] and w2['firstFailure']['id']=='W2-PERSISTED-UI-THEME'
    assert len(w2['comparisons'])==len({c['id'] for c in w2['comparisons']})==12
    assert sum(c['passed'] for c in w2['comparisons'])==8
    assert w2['exit']['code']==0 and not w2['forced'] and w2['cleanupError'] is None
    assert w2['remainingOwned']==w2['remainingListeners']==w2['remainingWindows']==0
    assert load(E/'h1-controller-exit.json')['exit']==0 and load(E/'w2-controller-exit.json')['exit']==1
    result['results'] = {'H1BusinessPassed':7,'W2ComparisonsPassed':8,'W2ComparisonsFailed':4,'W2ProductExit':0,'W2ControllerExit':1,'forced':False,'remainingOwned':0,'remainingListeners':0,'remainingWindows':0}
    matrix=ROOT/'docs/testing/phase-4-modular-agent-host-test-matrix.md'
    before=(E/('baseline-'+matrix.name)).read_bytes(); after=matrix.read_bytes()
    def cases(data): return [[c.strip() for c in l.strip('|').split('|')] for l in data.decode('utf8').splitlines() if re.match(r'^\| P4[ABCD]-[A-Z]+-\d{2} \|',l)]
    a,z=cases(before),cases(after); assert len(a)==len(z)==len({v[0] for v in z})==120
    for x,y in zip(a,z):
        assert len(y)==12 and x[:-1]==y[:-1]
        if x[1]!='B': assert x==y
    for portion in [lambda b:b[:b.index(b'### 5.2')],lambda b:b[b.index(b'### 5.3'):]]: assert portion(before)==portion(after)
    result['matrix']={'uniqueIds':120,'columns':12,'expectationsAndNonBPreserved':True,'B':dict(collections.Counter(v[-1] for v in z if v[1]=='B'))}
    for name in ['phase-4-c12-windows-shell-report.md','phase-4-c12-manual-checklist.md']:
        assert (ROOT/'docs/testing'/name).read_bytes().startswith((E/('baseline-'+name)).read_bytes())
    result['appendOnly']=True
    result['firstMaterials']=verify('firstMaterials',E/'first-materials.sha256',ROOT)
    for args in [['git','diff','--cached','--name-only'],['git','diff','--check']]:
        p=subprocess.run(args,cwd=ROOT,capture_output=True)
        assert p.returncode==0, 'readonly_git_check_failed'
        if '--cached' in args: assert not p.stdout.strip(), 'staged_nonempty'
    result.update(stagedCount=0,gitWrites=0,readonlyDiffCheck=True,passed=True)
    save(E/'end-audit.json',result)
    print(json.dumps({'passed':True,'repository':result['inputs']['repository']['matched'],'firstMaterials':result['firstMaterials']['entries'],'newProfileEntries':len(current),'matrix':result['matrix']['B']}))

if __name__ == '__main__': main()
