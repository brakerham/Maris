import {writeFileSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const own=path.dirname(fileURLToPath(import.meta.url));
const safe=v=>typeof v==='boolean'||typeof v==='number'&&Number.isFinite(v)?v:'unknown';
export default class Reporter {
 onInit(){this.started=Date.now()}
 onTestRunEnd(modules,errors){const nodes=[];
 const visit=(task,file)=>{if(task.type==='test')nodes.push({file,name:task.name,state:task.result?.state??'unknown',durationMs:task.result?.duration??null,errors:(task.result?.errors??[]).map(e=>({kind:['AssertionError','Error','TypeError'].includes(e.name)?e.name:'other',expected:safe(e.expected),actual:safe(e.actual),timeout:/timed out/i.test(e.message??'')}))});for(const sub of task.tasks??[])visit(sub,file)};
 for(const m of modules)visit(m.task,path.basename(m.task.filepath));
 const result={started:this.started,ended:Date.now(),nodes,total:nodes.length,passed:nodes.filter(n=>n.state==='pass').length,failed:nodes.filter(n=>n.state==='fail').length,moduleErrors:modules.reduce((n,m)=>n+(m.task.result?.errors?.length??0),0),unhandled:errors.length};
 writeFileSync(path.join(own,'evidence/r7-recovery/public/result.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
 process.stdout.write(JSON.stringify({stage:'public_result',total:result.total,passed:result.passed,failed:result.failed})+'\n');
 }
}
