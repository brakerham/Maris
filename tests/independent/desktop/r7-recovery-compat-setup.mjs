import {appendFileSync} from 'node:fs';
appendFileSync(process.env.R7_COMPAT_WORKERS,JSON.stringify({pid:process.pid,parentPid:process.ppid,time:new Date().toISOString()})+'\n');
