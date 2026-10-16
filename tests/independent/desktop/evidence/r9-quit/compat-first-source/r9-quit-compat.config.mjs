import path from 'node:path';
import {fileURLToPath} from 'node:url';
const own=path.dirname(fileURLToPath(import.meta.url));
const deps='C:/MarisQuitR7/R7-20261014-191500/workspace/node_modules';
export default {
 root:'D:/CodeX_gap/wife-system/apps/desktop',cacheDir:'C:/MarisC12/C12-R9-QUIT-20261016-011200/cache/compat',
 esbuild:{jsx:'automatic'},
 resolve:{alias:[{find:/^vitest$/,replacement:deps+'/vitest/dist/index.js'},...['electron','zod'].map(find=>({find,replacement:deps+'/'+find}))]},
 test:{include:['tests/unit/main-quit.test.ts','tests/unit/composition-root.test.ts','tests/unit/outbox-retention.test.ts','tests/unit/supervisor-outbox.test.ts','tests/unit/window-lifecycle.test.ts'],
 setupFiles:[path.join(own,'r9-quit-compat-setup.mjs')],environment:'node',pool:'forks',maxWorkers:1,fileParallelism:false,isolate:true,bail:1,testTimeout:20000,hookTimeout:5000,
 reporters:[path.join(own,'r9-quit-compat-reporter.mjs')]}
};
