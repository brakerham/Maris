from pathlib import Path
import hashlib,json,mmap,subprocess,sys,re
from datetime import datetime,timedelta
ROOT=Path(__file__).resolve().parents[3]
OWN=ROOT/'tests/independent/desktop/evidence/r3'
EXTERNAL=Path('C:/MarisRouteR4/R4-20261002-164600')
ALLOWED={'docs/coordination/agents/tester.md','docs/testing/phase-4-c12-windows-shell-report.md','docs/testing/phase-4-c12-manual-checklist.md','docs/testing/phase-4-modular-agent-host-test-matrix.md'}
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(name,data):OWN.mkdir(parents=True,exist_ok=True);(OWN/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def check_manifest(file,root,tsv=False):
    good=[];bad=[];missing=[]
    for line in file.read_text(encoding='utf-8-sig').splitlines():
        bits=line.split('\t');p=bits[0];expected=bits[-1];target=root/p
        if not target.is_file():missing.append(p)
        elif sha(target.read_bytes())==expected:good.append(p)
        else:bad.append(p)
    return {'entries':len(good)+len(bad)+len(missing),'matched':len(good),'mismatch':bad,'missing':missing,'manifest_sha256':sha(file.read_bytes())}
def update(step,status,output,log):
    now=datetime.now();stamp=now.strftime('%Y-%m-%d %H:%M');nexttime=(now+timedelta(minutes=10)).strftime('%H:%M')
    p=ROOT/'docs/coordination/agents/tester.md';s=p.read_text(encoding='utf-8-sig')
    values={'当前任务':'P4-C12-R3 — 路径独立复验与剩余Windows验收','状态':f'`{status}`','最近更新':stamp+' Asia/Shanghai','运行状态':'`finished`' if status in ['blocked','review'] else '`active`','当前步骤':step,'步骤开始时间':stamp+' Asia/Shanghai','最近有效进展':stamp+' Asia/Shanghai','最近心跳':stamp+' Asia/Shanghai','下一检查点':'已停止，等待总控验收/裁定' if status in ['blocked','review'] else nexttime+'前取得当前步骤结果并更新','等待对象':'总控' if status in ['blocked','review'] else '无','活动进程或会话':'无；产品0/8、辅助Electron0/4','重试次数':'0','最近输出':output,'可修改范围':'仅新增r3-*、evidence/r3、新R3报告；旧主报告/清单追加、矩阵B状态备注、自身角色；所有旧测试/报告/evidence及产品只读'}
    for k,v in values.items():s=re.sub('^- '+re.escape(k)+'：.*$',f'- {k}：{v}',s,count=1,flags=re.M)
    s=s.replace('## 工作日志\n',f'## 工作日志\n\n### {stamp} Asia/Shanghai — C12-R3 {step}\n\n{log}\n\n',1)
    p.write_text(s,encoding='utf-8',newline='\n')
if sys.argv[1]=='start':
    assert not (OWN/'start-audit.json').exists()
    manifest=ROOT/'docs/coordination/snapshots/p4-c12-r3-start.sha256'
    result=check_manifest(manifest,ROOT)
    result['staged_paths']=subprocess.run(['git','diff','--cached','--name-only'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines()
    result['historical_repository_source']=check_manifest(ROOT/'apps/desktop/b7-r4-route-source.sha256',ROOT)
    coordinator_updates={'README.md','docs/coordination/agents/brainstorm.md','docs/coordination/control.md','docs/coordination/overview.md','docs/project-coordination.md'}
    assert set(result['historical_repository_source']['mismatch'])==coordinator_updates and not result['historical_repository_source']['missing']
    result['historical_repository_source']['classification']='five coordinator dispatch documents; all match authoritative new 356-file task snapshot'
    result['source']=check_manifest(EXTERNAL/'evidence/static/workspace-source.sha256',EXTERNAL/'workspace')
    result['out']=check_manifest(EXTERNAL/'evidence/static/out-manifest-v4.tsv',EXTERNAL/'workspace/apps/desktop/out/Maris-win32-x64',True)
    result['resources']=check_manifest(EXTERNAL/'evidence/static/python-resources-v4.tsv',EXTERNAL/'workspace/apps/desktop/out/Maris-win32-x64/resources',True)
    fixed={'apps/desktop/out/Maris-win32-x64/Maris.exe':'d5868736cbdf63f717f0ea853141b980d06cefc10a3c05196e8856cbe3a4de2b','apps/desktop/out/Maris-win32-x64/resources/app.asar':'9a4da50b2c5583e6f2337bdff43e399cd454c360fa6169b1667a1e4506c337d4','pnpm-lock.yaml':'5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a'}
    result['artifacts']={p:sha((EXTERNAL/'workspace'/p).read_bytes()) for p in fixed}
    with (EXTERNAL/'workspace/apps/desktop/out/Maris-win32-x64/Maris.exe').open('rb') as f:
        with mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as m:
            i=m.find(b'dL7pKGdnNz796PbbjQWNKmHXBZaB9tsX')+32;result['fuses']={'version':m[i],'wire':list(m[i+2:i+2+m[i+1]])}
    dump('start-audit.json',result)
    assert all(not result[k]['mismatch'] and not result[k]['missing'] for k in ['source','out','resources'])
    assert not result['missing'] and not result['mismatch'] and not result['staged_paths'] and result['artifacts']==fixed and result['fuses']['wire'][:6]==[48,49,48,48,49,49]
    matrix=(ROOT/'docs/testing/phase-4-modular-agent-host-test-matrix.md').read_bytes();a=matrix.index(b'### 5.2');z=matrix.index(b'### 5.3')
    rows=[[c.strip() for c in l.strip().strip('|').split('|')] for l in matrix.decode('utf-8-sig').splitlines() if re.match(r'^\| P4[ABCD]-',l)]
    dump('baseline.json',{'cases':rows,'outside_b_prefix':sha(matrix[:a]),'outside_b_suffix':sha(matrix[z:]),'append_files':{p:{'bytes':len((ROOT/p).read_bytes()),'sha256':sha((ROOT/p).read_bytes())} for p in ['docs/testing/phase-4-c12-windows-shell-report.md','docs/testing/phase-4-c12-manual-checklist.md']}})
    update('接单与新起点核对通过','in_progress',f"{result['entries']}/{result['matched']} matched；构建source352/out140/resources67；历史repo353中五协调更新已由新起点绑定；staged0，包/lock/fuses匹配",'- control 2026-10-02T18:25:00+08:00：唯一测试负责人，R4为稳定输入，旧OUTBOX/setting已关闭不重复。\n- 新起点/source/out/resources/包/fuses已独立复算，新start-audit和baseline保存；先原R2-UI-04-PATH一次，新增路径边界和必要未覆盖条件，随后Windows。\n- 写入限r3新增/证据/新报告、旧主报告和清单追加、B矩阵和自身状态；无外部profile或目标启动。')
    print(json.dumps(result,ensure_ascii=False,indent=2))
elif sys.argv[1]=='status':update(sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])
