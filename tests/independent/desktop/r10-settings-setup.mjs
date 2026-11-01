import {appendFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {recorder} from './r10-settings-record.mjs';
appendFileSync(process.env.R10_WORKERS,JSON.stringify({pid:process.pid,parentPid:process.ppid,time:new Date().toISOString()})+'\n');
if(process.env.R10_MODE==='independent'){
 const rec=recorder(process.env.R10_OUTPUT+'/journal.jsonl');globalThis.__r10=rec;
 rec.emit('worker_start');
 process.once('exit',code=>{rec.emit('worker_exit',{code});rec.close();});
 rec.emit('native_jsdom_enter');
 const req=createRequire('C:/MarisSettingsR8/R8-20261019-103900/workspace/node_modules/jsdom/package.json');
 globalThis.__r10Dom=req('./lib/api.js');
 rec.emit('native_jsdom_ready');
}
