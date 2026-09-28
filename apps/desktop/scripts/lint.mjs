import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

const roots = ["electron", "src"];
const forbidden = ["dangerouslySetInnerHTML", "eval(", "nodeIntegration: true", "contextIsolation: false"];

async function files(root) {
  const result = [];
  for (const entry of await readdir(root, { withFileTypes: true })) {
    const target = path.join(root, entry.name);
    if (entry.isDirectory()) result.push(...await files(target));
    else if (/\.(ts|tsx|css|html)$/.test(entry.name)) result.push(target);
  }
  return result;
}

for (const root of roots) {
  for (const file of await files(root)) {
    const source = await readFile(file, "utf8");
    for (const token of forbidden) {
      if (source.includes(token)) throw new Error(`${file}: forbidden token ${token}`);
    }
  }
}
console.log("desktop lint checks passed");
