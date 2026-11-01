import {openSync,writeSync,fsyncSync,closeSync} from 'node:fs';
export class CompareError extends Error {name='CompareError'}
export class ToolError extends Error {name='ToolError'}
const safeString=/^(R10|SELF)[A-Z0-9._-]*$|^(system|light|dark|high_contrast|on|off|unknown|body|cleanup|tool|comparison|parse|missing|passed|failed|not_run|Error|TypeError|SyntaxError|CompareError|ToolError|other|ipc_sender_rejected|ipc_origin_rejected|ZodError)$/;
export function safe(v){if(v===null||typeof v==='boolean'||typeof v==='number'&&Number.isFinite(v)||typeof v==='string'&&safeString.test(v))return v;throw new ToolError('unsafe_record_value');}
export function recorder(file,io={openSync,writeSync,fsyncSync,closeSync}){
 const fd=io.openSync(file,'wx'),ids=new Set();let seq=0,firstError=null;
 const emit=(event,data={})=>{for(const v of Object.values(data))safe(v);const b=Buffer.from(JSON.stringify({seq:++seq,at:new Date().toISOString(),pid:process.pid,parentPid:process.ppid,event,...data})+'\n');for(let o=0;o<b.length;)o+=io.writeSync(fd,b,o,b.length-o);io.fsyncSync(fd);};
 const error=(id,e,stage='body')=>{const value={id,stage,kind:e instanceof CompareError?'comparison':e instanceof ToolError?'tool':'unknown',name:['Error','TypeError','SyntaxError','CompareError','ToolError'].includes(e?.name)?e.name:'other'};firstError??=value;emit('error',value);};
 const check=(id,expected,actual)=>{if(ids.has(id))throw new ToolError('duplicate_id');ids.add(id);safe(expected);safe(actual);emit('assert_enter',{id,expected});const passed=Object.is(expected,actual);emit('assert_terminal',{id,expected,actual,passed});if(!passed)throw new CompareError(id);};
 return {emit,check,error,ids,get firstError(){return firstError;},close:()=>io.closeSync(fd)};
}
export function parseResult(text){if(text===null)throw new ToolError('missing');const v=JSON.parse(text);if(!v||typeof v.passed!=='boolean')throw new ToolError('result_schema');return v;}
export async function released(body,release){let first=null,value;try{value=await body();}catch(e){first=e;}finally{try{await release();}catch(e){first??=e;}}if(first)throw first;return value;}
