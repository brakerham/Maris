"""C12-R4 failed-original gate handoff; no target executions."""
from pathlib import Path
import json,re,hashlib,subprocess,mmap,sys
ROOT=Path(__file__).resolve().parents[3];OWN=ROOT/'tests/independent/desktop/evidence/r4-r1';EXT=Path('C:/MarisLazyR5/R5-20261002-222300/workspace')
REPORT='docs/testing/phase-4-c12-r4-r1-observation-windows-report.md';MATRIX='docs/testing/phase-4-modular-agent-host-test-matrix.md';ROLE='docs/coordination/agents/tester.md';OLD='docs/testing/phase-4-c12-windows-shell-report.md';MANUAL='docs/testing/phase-4-c12-manual-checklist.md'
def sha(b):return hashlib.sha256(b).hexdigest()
def save(name,data):(OWN/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rows(b):return [[c.strip() for c in l.strip().strip('|').split('|')] for l in b.decode('utf-8-sig').splitlines() if re.match(r'^\| P4[ABCD]-',l)]
def nodeindex():
    j=json.loads((OWN/'observed-failure/result.json').read_text(encoding='utf-8-sig'));nodes=[{'name':a['fullName'],'status':a['status']} for f in j['testResults'] for a in f['assertionResults']]
    assert len(nodes)==1 and nodes[0]['status']=='failed';save('node-index.json',{'independent_executed':1,'passed':0,'failed':1,'nodes':nodes,'executor_compat_executed':0,'new_recovery_cases_executed':0,'product_starts':0,'auxiliary_electron_starts':0})
if sys.argv[1]=='verify':
    allowed={ROLE,MATRIX,OLD,MANUAL};matched=[];changed=[];bad=[];missing=[];manifest=ROOT/'docs/coordination/snapshots/p4-c12-r4-r1-start.sha256'
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
    assert audit['entries']==410 and len(matched)==406 and set(changed)==allowed and not bad and not missing and not staged
    baseline=json.loads((OWN/'baseline.json').read_text(encoding='utf-8'));b=(ROOT/MATRIX).read_bytes();cases=rows(b);assert len(cases)==len({r[0] for r in cases})==120 and all(len(r)==12 for r in cases);assert [r[:11] for r in cases]==[r[:11] for r in baseline['cases']];a=b.index(b'### 5.2');z=b.index(b'### 5.3');assert sha(b[:a])==baseline['outside_b_prefix'] and sha(b[z:])==baseline['outside_b_suffix'];assert [r[11] for r in cases]==[r[11] for r in baseline['cases']]
    prefixes={}
    for p,old in baseline['append_files'].items():
        b=(ROOT/p).read_bytes();assert sha(b[:old['bytes']])==old['sha256'];prefixes[p]={'prefix_preserved':True,'original_bytes':old['bytes'],'original_sha256':old['sha256'],'appended_bytes':len(b)-old['bytes']}
    nodeindex();files=[p for p in (ROOT/'tests/independent/desktop').glob('r4-r1-*') if p.is_file()]+[ROOT/REPORT]+[p for p in OWN.rglob('*') if p.is_file() and not any(k in p.parts for k in ['tmp','cache','compat-cache']) and p.name!='delivery-verification.json'];save('delivery-verification.json',{'matrix_unique_ids':120,'columns':12,'all_original_first_11_columns_preserved':True,'all_case_statuses_preserved':True,'outside_b_bytes_preserved':True,'append_files':prefixes,'new_files_sha256':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in sorted(files)},'product_starts':0,'auxiliary_starts':0,'owned_resources':'not_started, not successful cleanup evidence','git_writes':0});print(json.dumps(audit,ensure_ascii=False,indent=2))
