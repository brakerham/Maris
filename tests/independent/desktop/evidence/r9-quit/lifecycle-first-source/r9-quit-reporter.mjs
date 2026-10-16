import { writeFileSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
export default class Reporter {
 onTestRunEnd(modules, errors) {
  const selected=new Set(['R9-Q01','R9-Q02','R9-Q03','R9-Q04','R9-Q05','R9-Q06','R9-Q07','R9-Q08']), nodes=[],selectionExcluded=[];
  function visit(t){if(t.type==='test'){
   const id=t.name.split(' | ')[0];
   if(selected.has(id))nodes.push({id,state:t.result?.state??'not_run',durationMs:t.result?.duration??null,errors:(t.result?.errors??[]).map(e=>({kind:['Error','TypeError','AssertionError'].includes(e.name)?e.name:'other',timeout:/timed out/i.test(e.message??'')}))});
   else selectionExcluded.push(id);
  }for(const c of t.tasks??[])visit(c);}
  modules.forEach(m=>visit(m.task));
  const out=path.join(path.dirname(fileURLToPath(import.meta.url)),'evidence/r9-quit/lifecycle');
  let events=[],journalComplete=false;
  try{const t=readFileSync(path.join(out,'worker.journal.jsonl'),'utf8');journalComplete=t.endsWith('\n');events=t.trimEnd().split('\n').map(JSON.parse);}catch{}
  const formal=events.filter(e=>e.details.kind!=='selftest');
  const starts=formal.filter(e=>e.event==='assert_enter'),ends=formal.filter(e=>['assert_pass','assert_fail'].includes(e.event));
  const firstProductFailure=formal.find(e=>e.event==='assert_fail')??null;
  const firstToolError=formal.find(e=>e.event==='tool_error')??null;
  const firstUnknownError=formal.find(e=>e.event==='unknown_error')??null;
  const terminal=formal.filter(e=>e.event==='node_terminal'),cleanup=formal.filter(e=>e.event==='cleanup_terminal');
  for(const n of nodes){n.scenarioPassed=terminal.find(e=>e.details.id===n.id)?.details.passed??null;n.cleanupPassed=cleanup.find(e=>e.details.id===n.id)?.details.passed??null;}
  const result={attempt:0,nodes,selectionExcluded,historicalReused:selectionExcluded,passed:nodes.filter(n=>n.state==='pass'&&n.scenarioPassed===true&&n.cleanupPassed===true).length,failed:nodes.filter(n=>n.state==='fail'||n.scenarioPassed===false||n.cleanupPassed===false).length,notRun:nodes.filter(n=>!['pass','fail'].includes(n.state)).length,
   unhandledErrors:errors.length,moduleErrors:modules.reduce((n,m)=>n+(m.task.result?.errors?.length??0),0),firstProductFailure,firstToolError,firstUnknownError,
   firstFailure:formal.find(e=>['assert_fail','tool_error','unknown_error','operation_fail'].includes(e.event))??null,nodeTerminals:terminal,cleanup,
   selftest:events.filter(e=>e.details.kind==='selftest'),formalComparisons:ends.length,formalPassed:ends.filter(e=>e.event==='assert_pass').length,
   entered:starts.length,terminal:ends.length,journalComplete,paired:starts.length===ends.length&&starts.every(s=>ends.filter(e=>e.details.id===s.details.id).length===1)};
  writeFileSync(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});
  process.stdout.write(JSON.stringify({event:'r9_result',passed:result.passed,failed:result.failed,notRun:result.notRun})+'\n');
 }
}
