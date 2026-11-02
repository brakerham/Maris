import pathlib, hashlib, json, datetime, subprocess
ROOT=pathlib.Path('D:/CodeX_gap/wife-system'); OWN=ROOT/'tests/independent/desktop'; EV=OWN/'evidence/r11-origin-settings'; FIXED=pathlib.Path('C:/MarisIpcR9/R9-20261101-161412')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def verify(base,mf,count=None,digest=None,overrides=None):
    rows=mf.read_text(encoding='utf-8').splitlines();paths=[];changes=[]
    for line in rows:
        c=line.split('\t');assert len(c) in (2,3)
        rel=c[0];assert rel not in paths and '..' not in pathlib.PurePosixPath(rel).parts;paths.append(rel)
        p=(overrides or {}).get(rel,base/rel)
        if not p.is_file() or sha(p)!=c[-1] or len(c)==3 and p.stat().st_size!=int(c[1]):changes.append(rel)
    return {'base':str(base),'manifest':str(mf),'entries':len(rows),'matched':len(rows)-len(changes),'changes':changes,'sha256':sha(mf),'passed':not changes and (count is None or len(rows)==count) and (digest is None or sha(mf)==digest)}
if __name__=='__main__':
    close=FIXED/'evidence/closeout.json';assert sha(close)=='a0dacd4ff8969e4b0045d1238f7635b47221400df00896d3599a2f70c1d2eef4'
    c=json.loads(close.read_text(encoding='utf-8'));results={}
    for key in ['delivery','buildInput','out','pythonResources','tools','runtimeTools','developmentInputs','evidence']:
        v=c[key];results[key]=verify(pathlib.Path(v['base']),pathlib.Path(v['manifest']),v['entries'],v['sha256'])
    old=OWN/'evidence/r10-settings';overrides={'docs/coordination/agents/tester.md':EV/'baseline-tester.md'}
    results['R10delivery']=verify(ROOT,old/'delivery.sha256',50,overrides=overrides)
    results['R10source']=verify(OWN,old/'independent-source.sha256',8)
    results['R10first']=verify(old,old/'first-materials.sha256',29)
    prior=json.loads((old/'tool-entries.json').read_text(encoding='utf-8'));tools=[]
    for v in prior['checks']:
        p=pathlib.Path(v['path'].replace('C:\\MarisSettingsR8\\R8-20261019-103900',str(FIXED)));tools.append({'path':str(p),'sha256':sha(p),'passed':sha(p)==v['sha256']})
    singles=[]
    for rel,h in [('workspace/apps/desktop/out/Maris-win32-x64/Maris.exe','c80d27c8e31fa60df91065a770e669a553260cf8f883c55a0a7f83f8a430736b'),('workspace/apps/desktop/out/Maris-win32-x64/resources/app.asar','05cdad34ba60b59773eebe671156c96260e69354568b9942da59058641f9c0b2'),('workspace/pnpm-lock.yaml','5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a')]:
        p=FIXED/rel;singles.append({'path':str(p),'sha256':sha(p),'passed':sha(p)==h})
    result={'at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'results':results,'actualToolEntries':tools,'singles':singles,'oldDeliveryTesterComparedToPreAcceptanceCopy':True,'fullDependencyRescan':False,'passed':all(v['passed'] for v in results.values()) and all(v['passed'] for v in tools+singles)}
    with (EV/'fixed-input-audit.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'passed':result['passed'],'sets':{k:{'entries':v['entries'],'matched':v['matched'],'changes':v['changes']} for k,v in results.items()},'tools':len(tools)}));raise SystemExit(0 if result['passed'] else 1)
