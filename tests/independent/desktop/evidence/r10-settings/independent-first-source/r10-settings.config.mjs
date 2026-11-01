import path from 'node:path';
import {fileURLToPath} from 'node:url';
const own=path.dirname(fileURLToPath(import.meta.url));
const deps='C:/MarisSettingsR8/R8-20261019-103900/workspace/node_modules';
const compat=process.env.R10_MODE==='compat';
export default {
 root:compat?'D:/CodeX_gap/wife-system/apps/desktop':own,
 cacheDir:path.join(own,'evidence/r10-settings/cache',compat?'compat':'independent'),esbuild:{jsx:'automatic'},
 resolve:{alias:[{find:/^vitest$/,replacement:deps+'/vitest/dist/index.js'},...['react-router','react-dom','react','zod','electron','@testing-library/react','@testing-library/user-event'].map(find=>({find,replacement:deps+'/'+find}))]},
 test:{include:compat?['tests/unit/settings-snapshot.test.ts','tests/unit/settings-hydration.test.tsx']:['r10-settings-contract.test.tsx'],setupFiles:[path.join(own,'r10-settings-setup.mjs')],environment:'node',pool:'forks',maxWorkers:1,fileParallelism:false,isolate:true,bail:1,testTimeout:20000,hookTimeout:5000,
 reporters:[path.join(own,'r10-settings-reporter.mjs')]}
};
