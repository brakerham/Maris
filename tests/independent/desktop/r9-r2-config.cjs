const path=require('node:path');
const own=__dirname,repo=path.resolve(own,'../../..');
const ext='C:\\MarisC12\\C12-R9-R2-20261017-233500',fixed='C:\\MarisQuitR7\\R7-20261014-191500';
module.exports={own,repo,ext,fixed,marker:'P4-C12-R9-R2 20261017-233500',markerFile:path.join(ext,'r9-r2-owned-marker.txt'),
 node:path.join(fixed,'tools/node/node.exe'),electron:path.join(fixed,'workspace/node_modules/electron/dist/electron.exe'),
 product:path.join(fixed,'workspace/apps/desktop/out/Maris-win32-x64/Maris.exe'),
 pwsh:'C:\\Users\\xuhaolin\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\native\\powershell\\pwsh.exe',
 evidence:path.join(own,'evidence/r9-r2'),observer:path.join(own,'r9-r2-observer.ps1'),parser:path.join(own,'r9-r2-parser.ps1'),
 controlVersion:'2026-10-17T09:03:00+08:00'};
