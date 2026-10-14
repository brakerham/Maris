import {appendFileSync} from 'node:fs';
appendFileSync(process.env.R8R1_PUBLIC_WORKERS,JSON.stringify({pid:process.pid,parentPid:process.ppid,time:new Date().toISOString()})+'\n');
