"""Read-only bound input audit; outputs only R10 evidence, no dependency rescan."""
import hashlib, json, pathlib, datetime, subprocess
ROOT = pathlib.Path('D:/CodeX_gap/wife-system')
EV = ROOT / 'tests/independent/desktop/evidence/r10-settings'
FIXED = pathlib.Path('C:/MarisSettingsR8/R8-20261019-103900')
def digest(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
def manifest(base, file, count, expected):
    data=file.read_bytes(); rows=data.decode('utf-8-sig').splitlines(); seen=set(); changes=[]
    for row in rows:
        cols=row.split('\t'); assert len(cols) in (2,3), 'manifest_columns'
        rel=cols[0]; assert rel not in seen and not pathlib.PurePosixPath(rel).is_absolute() and '..' not in pathlib.PurePosixPath(rel).parts
        seen.add(rel); p=base/rel
        if not p.is_file() or digest(p)!=cols[-1] or len(cols)==3 and p.stat().st_size!=int(cols[1]): changes.append(rel)
    return {'base':str(base),'manifest':str(file),'entries':len(rows),'matched':len(rows)-len(changes),'sha256':digest(file),'changes':changes,'passed':len(rows)==count and digest(file)==expected and not changes}
if __name__=='__main__':
    close=json.loads((FIXED/'evidence/closeout.json').read_text())
    results={k:manifest(pathlib.Path(v['base']),pathlib.Path(v['manifest']),v['entries'],v['sha256']) for k,v in close['newFixed'].items()}
    expected={
      str(FIXED/'workspace/apps/desktop/out/Maris-win32-x64/Maris.exe'):'c80d27c8e31fa60df91065a770e669a553260cf8f883c55a0a7f83f8a430736b',
      str(FIXED/'workspace/apps/desktop/out/Maris-win32-x64/resources/app.asar'):'05cdad34ba60b59773eebe671156c96260e69354568b9942da59058641f9c0b2',
      str(ROOT/'pnpm-lock.yaml'):'5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a',
      'C:/MarisSettingsR8/R8-R2-20261030-040716/evidence/closeout.json':'7f1c23ab0c9cbfa578b5e9b136ec3b728b17917f4621917ca20882eff78edf24',
      str(ROOT/'tests/independent/desktop/evidence/r9-r3/helper-H1/native-result.json'):'f6c493c244f18832b0e69e5fa7c45a09108e304bd72fb685951c92252b7a62e3'}
    singles=[{'path':p,'sha256':digest(pathlib.Path(p)),'passed':digest(pathlib.Path(p))==h} for p,h in expected.items()]
    profile=manifest(pathlib.Path('C:/MarisC12/C12-R9-QUIT-20261016-011200'),ROOT/'tests/independent/desktop/evidence/r9-r1/original-profile.tsv',63,'575f132e0bc44a949391c9ab7c31747e4e21e58fdb8a344dc29a00e6639ce7ee')
    allowed={'docs/coordination/agents/tester.md'}; changes=[]
    for line in (ROOT/'docs/coordination/snapshots/p4-c12-r10-settings-start.sha256').read_text().splitlines():
        rel,h=line.split('\t')
        if digest(ROOT/rel)!=h: changes.append(rel)
    staged=subprocess.run(['git','diff','--cached','--name-only'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines()
    result={'at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'fixed':results,'singles':singles,'oldW1Profile':profile,'repositoryChangesSinceAcceptance':changes,'stagedCount':len(staged),'passed':all(v['passed'] for v in results.values()) and all(x['passed'] for x in singles) and profile['passed'] and set(changes)<=allowed and not staged}
    with (EV/'fixed-input-audit.json').open('x',encoding='utf-8',newline='\n') as f: json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(result,ensure_ascii=False)); raise SystemExit(0 if result['passed'] else 1)
