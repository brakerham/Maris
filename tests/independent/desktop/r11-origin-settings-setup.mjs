import {appendFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {recorder} from './r11-origin-settings-record.mjs';
appendFileSync(process.env.R11_WORKERS,JSON.stringify({pid:process.pid,parentPid:process.ppid,time:new Date().toISOString()})+'\n');
if(process.env.R11_MODE==='independent'){
 const rec=recorder(process.env.R11_OUTPUT+'/journal.jsonl');globalThis.__r10=rec;
 rec.emit('worker_start');
 process.once('exit',code=>{rec.emit('worker_exit',{code});rec.close();});
 rec.emit('native_jsdom_enter');
 const req=createRequire('C:/MarisIpcR9/R9-20261101-161412/workspace/node_modules/jsdom/package.json');
 globalThis.__r10Dom=req('./lib/api.js');
 rec.emit('native_jsdom_ready');
}
