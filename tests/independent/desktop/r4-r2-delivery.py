"""Final read-only verification; writes only new R2 audit/evidence files."""
from pathlib import Path
import hashlib,json,re,subprocess,mmap
ROOT=Path(__file__).resolve().parents[3];OWN=ROOT/'tests/independent/desktop/evidence/r4-r2';EXT=Path('C:/MarisLazyR5/R5-20261002-222300/workspace')
ROLE='docs/coordination/agents/tester.md';MATRIX='docs/testing/phase-4-modular-agent-host-test-matrix.md'
OLD='docs/testing/phase-4-c12-windows-shell-report.md';MANUAL='docs/testing/phase-4-c12-manual-checklist.md'
REPORT='docs/testing/phase-4-c12-r4-r2-cold-entry-windows-report.md'
def sha(b):return hashlib.sha256(b).hexdigest()
def save(name,value):(OWN/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def load(name):return json.loads((OWN/name).read_text(encoding='utf-8-sig'))
def rows(b):return [[c.strip() for c in l.strip().strip('|').split('|')] for l in b.decode('utf-8-sig').splitlines() if re.match(r'^\| P4[ABCD]-',l)]
allowed={ROLE,MATRIX,OLD,MANUAL};matched=[];changed=[];bad=[];missing=[]
manifest=ROOT/'docs/coordination/snapshots/p4-c12-r4-r2-start.sha256'
for line in manifest.read_text(encoding='utf-8-sig').splitlines():
    name,h=line.split('\t');file=ROOT/name
    if not file.is_file():missing.append(name)
    elif sha(file.read_bytes())==h:matched.append(name)
    elif name in allowed:changed.append(name)
    else:bad.append(name)
assert len(matched)==503 and set(changed)==allowed and not bad and not missing
start=load('start-audit.json');artifacts={p:sha((EXT/p).read_bytes()) for p in start['artifacts']};assert artifacts==start['artifacts']
with (EXT/'apps/desktop/out/Maris-win32-x64/Maris.exe').open('rb') as f:
    with mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as m:
        i=m.find(b'dL7pKGdnNz796PbbjQWNKmHXBZaB9tsX')+32;fuses={'version':m[i],'wire':list(m[i+2:i+2+m[i+1]])}
assert fuses==start['fuses'];counts={}
for kind,rel,base in [('source','workspace-source.sha256',EXT),('out','out-manifest-v4.tsv',EXT/'apps/desktop/out/Maris-win32-x64'),('resources','python-resources-v4.tsv',EXT/'apps/desktop/out/Maris-win32-x64/resources')]:
    file=EXT.parent/'evidence/static'/rel
    assert sha(file.read_bytes())==start[kind]['manifest_sha256']
    lines=file.read_text(encoding='utf-8-sig').splitlines()
    assert all(sha((base/l.split('\t')[0]).read_bytes())==l.split('\t')[-1] for l in lines);counts[kind]=len(lines)
metadata=load('static-preflight.json')['versions']
assert all(sha((Path(v['physicalRoot'])/'package.json').read_bytes())==v['packageJsonSha256'] for v in metadata.values())
for line in (OWN/'cold-source.sha256').read_text(encoding='utf-8').splitlines():
    name,h=line.split('\t');assert sha((ROOT/'tests/independent/desktop'/name).read_bytes())==h
baseline=load('baseline.json');b=(ROOT/MATRIX).read_bytes();cases=rows(b)
assert len(cases)==len({r[0] for r in cases})==120 and all(len(r)==12 for r in cases)
assert [r[:11] for r in cases]==[r[:11] for r in baseline['cases']]
assert [r[11] for r in cases]==[r[11] for r in baseline['cases']]
a=b.index(b'### 5.2');z=b.index(b'### 5.3')
assert sha(b[:a])==baseline['outside_b_prefix'] and sha(b[z:])==baseline['outside_b_suffix']
prefixes={}
for name,old in baseline['append_files'].items():
    b=(ROOT/name).read_bytes();assert sha(b[:old['bytes']])==old['sha256']
    prefixes[name]={'prefixPreserved':True,'originalBytes':old['bytes'],'appendedBytes':len(b)-old['bytes']}
report=(ROOT/REPORT).read_text(encoding='utf-8');ids=re.findall(r'^### (P4B-[A-Z]+-\d+) — ',report,re.M)
assert len(ids)==len(set(ids))==24 and set(ids)=={r[0] for r in cases if r[1]=='B'}
assert all(r[9] in report for r in cases if r[1]=='B')
events=[json.loads(l) for l in (OWN/'cold-trace/worker.journal.jsonl').read_text(encoding='utf-8').splitlines()]
process=load('cold-trace/process.json');result=load('cold-trace/result.json')
assert len(events)==34 and [e['seq'] for e in events]==list(range(1,35))
assert sum(e['stage']=='main_import_enter' for e in events)==1
assert process['mainImportRequests']==1 and process['rootExited'] and process['workerExited'] and process['rootExitCode']==1
assert not process['timedOut'] and not process['forcedRootTermination'] and not process['forcedWorkerTermination'] and process['streamsComplete']
assert result['numTotalTests']==1 and result['numFailedTests']==1 and not result['numPassedTests']
assert not (OWN/'cold-public').exists()
assert load('temp-cleanup.json')['absentAfter'] and not (OWN/'cache').exists()
role=(ROOT/ROLE).read_text(encoding='utf-8');assert '- 状态：`blocked`' in role and '- 运行状态：`finished`' in role
staged=subprocess.run(['git','diff','--cached','--name-only'],cwd=ROOT,capture_output=True,text=True,check=True)
assert not staged.stdout.splitlines()
diff=subprocess.run(['git','diff','--check','--',ROLE,MATRIX,OLD,MANUAL,REPORT,'tests/independent/desktop/r4-r2-*','tests/independent/desktop/evidence/r4-r2'],cwd=ROOT,capture_output=True,text=True)
(OWN/'diff-check.log').write_text(diff.stdout+diff.stderr,encoding='utf-8');assert diff.returncode==0
audit={'entries':507,'unchanged':len(matched),'authorizedChanged':sorted(changed),'unauthorizedMismatch':bad,'missing':missing,'stagedPaths':[],
 'manifestSha256':sha(manifest.read_bytes()),'artifacts':artifacts,'fuses':fuses,'packageInputsMatched':counts,
 'oldIndependentFilesUnchanged':sum(p.startswith('tests/independent/desktop/') for p in matched),
 'oldD15DiagnosticFilesUnchanged':sum(p.startswith('docs/coordination/diagnostics/p4-d15') for p in matched),
 'frozenColdSourceFilesMatched':len((OWN/'cold-source.sha256').read_text(encoding='utf-8').splitlines()),
 'fixedDependencyMetadataMatched':len(metadata)}
save('end-audit.json',audit)
verification={'matrixUniqueIds':120,'columns':12,'firstElevenColumnsPreserved':True,'allStatusesPreserved':True,
 'outsideBBytesPreserved':True,'appendFiles':prefixes,'reportFullCaseMappings':24,'A':'failed','B':'not_run',
 'vitestCliStarts':1,'mainRequests':1,'targetRetries':0,'preMainCorrectionWorkers':0,'nativeStaticFormatCorrections':1,
 'productStarts':0,'auxiliaryStarts':0,'chunkInjections':0,'gitWrites':0,'diffCheckExitCode':diff.returncode,
 'gitWarning':bool(diff.stderr.strip() or staged.stderr.strip()),'resourceScope':'owned CLI and journal worker exited; DOM/observer/bridge cleaned; OS enumeration unverified'}
save('delivery-verification.json',verification)
files=[p for p in (ROOT/'tests/independent/desktop').glob('r4-r2-*') if p.is_file()]
files += [ROOT/p for p in [REPORT,ROLE,MATRIX,OLD,MANUAL]]
files += [p for p in OWN.rglob('*') if p.is_file() and p.name!='delivery.sha256']
files=sorted(set(files));lines=[p.relative_to(ROOT).as_posix()+'\t'+sha(p.read_bytes()) for p in files]
(OWN/'delivery.sha256').write_text('\n'.join(lines)+'\n',encoding='utf-8')
assert len(lines)==len(set(p.relative_to(ROOT).as_posix() for p in files))
assert all(sha((ROOT/l.split('\t')[0]).read_bytes())==l.split('\t')[1] for l in lines)
print(json.dumps({'audit':audit,'deliveryFiles':len(files),'deliverySha256':sha((OWN/'delivery.sha256').read_bytes()),'verification':verification},ensure_ascii=False,indent=2))
