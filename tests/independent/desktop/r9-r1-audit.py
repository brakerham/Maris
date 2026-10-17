"""R9-R1 read-only byte audits; never launches a product or writes fixed inputs."""
from pathlib import Path
import hashlib, json, datetime, subprocess, sys, re, collections

ROOT = Path(__file__).resolve().parents[3]
E = ROOT / 'tests/independent/desktop/evidence/r9-r1'
OLD = ROOT / 'tests/independent/desktop/evidence/r9-quit'
START = json.loads((OLD / 'start-audit.json').read_text(encoding='utf8'))
SHARED = {'docs/coordination/agents/tester.md', 'docs/testing/phase-4-modular-agent-host-test-matrix.md',
          'docs/testing/phase-4-c12-windows-shell-report.md', 'docs/testing/phase-4-c12-manual-checklist.md'}

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576), b''): h.update(b)
    return h.hexdigest()

def verify(name, manifest, base, expected=None, allowed=(), inventory=False):
    b=manifest.read_bytes()
    if expected: assert sha(manifest)==expected, (name,'manifest')
    rows=[l.split('\t') for l in b.decode('utf8').splitlines()]; paths=[]; changes=[]
    for row in rows:
        assert len(row) in (2,3), (name,'columns')
        p,h=row[0],row[-1]; paths.append(p); f=base/p
        assert not Path(p).is_absolute() and '..' not in Path(p).parts
        assert f.is_file() and not f.is_symlink(),(name,p,'missing')
        if len(row)==3: assert f.stat().st_size==int(row[1]),(name,p,'bytes')
        actual=sha(f)
        if actual!=h:
            assert p in allowed,(name,p,'changed')
            changes.append({'path':p,'sha256':actual})
    assert len(paths)==len(set(paths)),(name,'duplicate')
    if inventory:
        actual={p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file()}
        if name=='resources': actual.discard('app.asar')
        assert actual==set(paths),(name,'inventory')
    result={'entries':len(paths),'matched':len(paths)-len(changes),'changes':changes,'manifestSha256':sha(manifest),'inventoryVerified':inventory}
    print(json.dumps({'checked':name,**result}),flush=True)
    return result

def main():
    phase=sys.argv[1]; assert phase in ('start','end')
    result={'at':datetime.datetime.now().astimezone().isoformat(),'phase':phase,'inputs':{}}
    result['inputs']['repository']=verify('repository',ROOT/'docs/coordination/snapshots/p4-c12-r9-r1-start.sha256',ROOT,
        'e25b1743fe68f1fa0f8166013d3419feffb7d33cc919b3bbc512601fdddb9539',SHARED)
    for name in ['buildSource','out','resources','dist','dependencies','executorEvidence']:
        s=START[name]
        result['inputs'][name]=verify(name,Path(s['manifest']),Path(s['base']),s['sha256'],inventory=name in ('out','resources','dist','dependencies'))
        assert result['inputs'][name]['entries']==s['entries']
    result['inputs']['oldR9Delivery']=verify('oldR9Delivery',OLD/'delivery.sha256',ROOT,
        '3d08ba6c8246cc4f6e994cdaa75060b411dc23b6c010f5bf60b8b1acedf9443d',SHARED)
    result['inputs']['oldR9First']=verify('oldR9First',OLD/'first-materials.sha256',ROOT)
    for rel,expected in START['artifacts'].items(): assert sha(Path(START['buildSource']['base'])/rel)==expected,(rel,'artifact')
    result['artifacts']=START['artifacts']
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
        baseline=(E/('baseline-'+name)).read_bytes();assert (ROOT/'docs/testing'/name).read_bytes().startswith(baseline)
    result['appendOnly']=True
    if phase=='end' and (E/'profile-copy.json').exists():
        p=json.loads((E/'profile-copy.json').read_text(encoding='utf8'))
        result['originalProfile']=verify('originalProfile',E/'original-profile.tsv',Path(p['sourceRoot']),inventory=False)
        result['unusedProfileCopy']=verify('unusedProfileCopy',E/'original-profile.tsv',Path(p['copyRoot']),inventory=False)
        expected={l.split('\t')[0] for l in (E/'original-profile.tsv').read_text(encoding='utf8').splitlines()}
        for key in ['sourceRoot','copyRoot']:
            base=Path(p[key]); actual={v.relative_to(base).as_posix() for v in (base/'profile-main').rglob('*') if v.is_file()}|{'continuity.json'}
            assert actual==expected,('profile_inventory',key)
        result['profileInventoriesEqual']=True
        result['frozenNewSources']={}
        for manifest in sorted(E.glob('*-source.sha256')):
            result['frozenNewSources'][manifest.name]=verify(manifest.name,manifest,ROOT/'tests/independent/desktop')
        result['firstMaterials']=verify('firstMaterials',E/'first-materials.sha256',ROOT)
    staged=subprocess.run(['git','diff','--cached','--name-only'],cwd=ROOT,capture_output=True,check=True)
    assert not staged.stdout.strip()
    result.update(stagedCount=0,gitWrites=0,passed=True)
    with (E/(phase+'-audit.json')).open('x',encoding='utf8',newline='\n') as f: json.dump(result,f,indent=2);f.write('\n')

if __name__=='__main__': main()
