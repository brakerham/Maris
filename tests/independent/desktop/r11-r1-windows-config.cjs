const path=require('node:path');
const own=__dirname,repo=path.resolve(own,'../../..');
const ext='C:\\MarisC12\\C12-R11-R1-WINDOWS-20261103-002800',fixed='C:\\MarisIpcR9\\R9-20261101-161412';
module.exports={own,repo,ext,fixed,marker:'P4-C12-R11-R1-WINDOWS 20261103-002800',markerFile:path.join(ext,'r11-r1-owned-marker.txt'),
 node:path.join(fixed,'tools/node/node.exe'),electron:path.join(fixed,'workspace/node_modules/electron/dist/electron.exe'),
 product:path.join(fixed,'workspace/apps/desktop/out/Maris-win32-x64/Maris.exe'),
 pwsh:'C:\\Users\\xuhaolin\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\native\\powershell\\pwsh.exe',
 evidence:path.join(own,'evidence/r11-r1-windows'),observer:path.join(own,'r9-r2-observer.ps1'),parser:path.join(own,'r9-r2-parser.ps1'),
 controlVersion:'2026-11-03T00:05:00+08:00'};
