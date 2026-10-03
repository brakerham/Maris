from pathlib import Path
from datetime import datetime,timedelta
import hashlib,json,subprocess,mmap,re,sys
ROOT=Path(__file__).resolve().parents[3];OWN=ROOT/'tests/independent/desktop/evidence/r4-r3';EXT=Path('C:/MarisLazyR5/R5-20261002-222300')
def sha(b):return hashlib.sha256(b).hexdigest()
def save(name,data):OWN.mkdir(parents=True,exist_ok=True);(OWN/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def check(file,root):
    matched=[];bad=[];missing=[]
    for line in file.read_text(encoding='utf-8-sig').splitlines():
        cols=line.split('\t');p=cols[0];target=root/p
        if not target.is_file():missing.append(p)
        elif sha(target.read_bytes())==cols[-1]:matched.append(p)
        else:bad.append(p)
    return {'entries':len(matched)+len(bad)+len(missing),'matched':len(matched),'mismatch':bad,'missing':missing,'manifest_sha256':sha(file.read_bytes())}
def status(step,state,out,log):
    now=datetime.now();stamp=now.strftime('%Y-%m-%d %H:%M');p=ROOT/'docs/coordination/agents/tester.md';text=p.read_text(encoding='utf-8-sig')
    v={'当前任务':'P4-C12-R4-R3 — 持续导入故障与冷入口复验与原R4续跑','状态':f'`{state}`','最近更新':stamp+' Asia/Shanghai','运行状态':'`finished`' if state in ['review','blocked'] else '`active`','当前步骤':step,'步骤开始时间':stamp+' Asia/Shanghai','最近有效进展':stamp+' Asia/Shanghai','最近心跳':stamp+' Asia/Shanghai','下一检查点':'已停止，交总控验收/裁定' if state in ['review','blocked'] else (now+timedelta(minutes=10)).strftime('%H:%M')+'前当前步骤输出','等待对象':'总控' if state in ['review','blocked'] else '无','活动进程或会话':'当前阶段尚无活动目标；各次资源与会话以本轮process/journal为准；产品0/8、辅助0/4','最近输出':out,'可修改范围':'仅新增r4-r3-*、evidence/r4-r3、新R4-R3报告；旧主报告/清单追加、矩阵B状态备注、自身角色；旧public/r1/r2/r3/r4/r4-r1/r4-r2/D15与产品全部只读'}
    for k,val in v.items():text=re.sub(r'^- '+re.escape(k)+r'：.*$',f'- {k}：{val}',text,count=1,flags=re.M)
    text=text.replace('## 工作日志\n',f'## 工作日志\n\n### {stamp} Asia/Shanghai — C12-R4-R3 {step}\n\n{log}\n\n',1);p.write_text(text,encoding='utf-8',newline='\n')
if sys.argv[1]=='start':
    assert not (OWN/'start-audit.json').exists()
    result=check(ROOT/'docs/coordination/snapshots/p4-c12-r4-r3-start.sha256',ROOT)
    result['source']=check(EXT/'evidence/static/workspace-source.sha256',EXT/'workspace')
    result['out']=check(EXT/'evidence/static/out-manifest-v4.tsv',EXT/'workspace/apps/desktop/out/Maris-win32-x64')
    result['resources']=check(EXT/'evidence/static/python-resources-v4.tsv',EXT/'workspace/apps/desktop/out/Maris-win32-x64/resources')
    fixed={'apps/desktop/out/Maris-win32-x64/Maris.exe':'64ce71f3a7b3055f9ad27f6d611e28c4af7e9ba8b86d8b21399b7b422844a80e','apps/desktop/out/Maris-win32-x64/resources/app.asar':'5ba47909537e1419dc275fa3ca1e5e076a1aa6d5c0205229f91defb92ddd0931','pnpm-lock.yaml':'5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a'}
    result['artifacts']={p:sha((EXT/'workspace'/p).read_bytes()) for p in fixed}
    with (EXT/'workspace/apps/desktop/out/Maris-win32-x64/Maris.exe').open('rb') as f:
        with mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as m:
            i=m.find(b'dL7pKGdnNz796PbbjQWNKmHXBZaB9tsX')+32;result['fuses']={'version':m[i],'wire':list(m[i+2:i+2+m[i+1]])}
    result['staged_paths']=subprocess.run(['git','diff','--cached','--name-only'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines();save('start-audit.json',result)
    assert not result['missing'] and not result['mismatch'] and not result['staged_paths'] and result['artifacts']==fixed and result['fuses']['wire'][:6]==[48,49,48,48,49,49]
    assert all(not result[k]['missing'] and not result[k]['mismatch'] for k in ['source','out','resources'])
    b=(ROOT/'docs/testing/phase-4-modular-agent-host-test-matrix.md').read_bytes();a=b.index(b'### 5.2');z=b.index(b'### 5.3');rows=[[c.strip() for c in line.strip().strip('|').split('|')] for line in b.decode('utf-8-sig').splitlines() if re.match(r'^\| P4[ABCD]-',line)]
    save('baseline.json',{'cases':rows,'outside_b_prefix':sha(b[:a]),'outside_b_suffix':sha(b[z:]),'append_files':{p:{'bytes':len((ROOT/p).read_bytes()),'sha256':sha((ROOT/p).read_bytes())} for p in ['docs/testing/phase-4-c12-windows-shell-report.md','docs/testing/phase-4-c12-manual-checklist.md']}})
    status('接单与权威新起点通过','in_progress',f"{result['entries']}/{result['matched']} matched，389构建输入/140产物/67资源匹配，staged0，包/lock/fuses匹配",'- control 2026-10-03T03:56:00+08:00，既有测试唯一负责人；R5稳定输入、旧OUTBOX/setting/PATH不重开。\n- 新起点及外部不可变包输入分开核对，无历史协调漂移误assert。先P默认loader两并发+随后调用一次都安全拒绝，再全新worker冷main A/B；全部通过才进入独立恢复/Windows。\n- 原public/r1/r2/r3/r4/r4-r1和D15/D15-R1全部只读；新增r4输出与自身日志，动态根需要审批且不使用真实AppData。')
    print(json.dumps(result,ensure_ascii=False,indent=2))
elif sys.argv[1]=='status':status(*sys.argv[2:6])
