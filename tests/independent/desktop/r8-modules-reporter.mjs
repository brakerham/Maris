import { writeFileSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
export default class Reporter {
 onTestRunEnd(modules, errors) {
  const nodes=[];
  function visit(t){if(t.type==='test')nodes.push({id:t.name.split(' | ')[0],state:t.result?.state??'not_run',durationMs:t.result?.duration??null,errors:(t.result?.errors??[]).map(e=>({kind:['Error','TypeError','AssertionError'].includes(e.name)?e.name:'other',timeout:/timed out/i.test(e.message??'')}))});for(const c of t.tasks??[])visit(c);}
  modules.forEach(m=>visit(m.task));
  const out=path.join(path.dirname(fileURLToPath(import.meta.url)),'evidence/r8-modules/modules');
  let events=[],journalComplete=false;
  try {const t=readFileSync(path.join(out,'worker.journal.jsonl'),'utf8');journalComplete=t.endsWith('\n');events=t.trimEnd().split('\n').map(JSON.parse);}catch{}
  const starts=events.filter(e=>e.event==='assert_enter'),ends=events.filter(e=>['assert_pass','assert_fail'].includes(e.event));
  const result={nodes,passed:nodes.filter(n=>n.state==='pass').length,failed:nodes.filter(n=>n.state==='fail').length,notRun:nodes.filter(n=>!['pass','fail'].includes(n.state)).length,unhandledErrors:errors.length,moduleErrors:modules.reduce((n,m)=>n+(m.task.result?.errors?.length??0),0),
   firstFailure:events.find(e=>e.event==='assert_fail'&&e.details.kind==='gate')??events.find(e=>e.event==='operation_fail')??null,
   formalComparisons:ends.filter(e=>e.details.kind==='gate').length,formalPassed:ends.filter(e=>e.details.kind==='gate'&&e.event==='assert_pass').length,
   entered:starts.length,terminal:ends.length,journalComplete,paired:starts.length===ends.length&&starts.every(s=>ends.filter(e=>e.details.id===s.details.id).length===1)};
  writeFileSync(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
  process.stdout.write(JSON.stringify({event:'r8_result',passed:result.passed,failed:result.failed,notRun:result.notRun})+'\n');
 }
}
