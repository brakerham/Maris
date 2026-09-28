import { spawn } from "node:child_process";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { cleanupPythonResources, stagePythonResources } from "./stage-python-resources.mjs";

const require = createRequire(import.meta.url);
const desktopRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");

async function runForgePackage() {
  const packageJsonPath = require.resolve("@electron-forge/cli/package.json");
  const packageJson = require(packageJsonPath);
  const relativeCli = typeof packageJson.bin === "string" ? packageJson.bin : packageJson.bin["electron-forge"];
  if (!relativeCli) throw new Error("electron_forge_cli_missing");
  const cliPath = resolve(dirname(packageJsonPath), relativeCli);
  return await new Promise((resolveExit, reject) => {
    const child = spawn(process.execPath, [cliPath, "package"], { cwd: desktopRoot, stdio: "inherit" });
    child.once("error", reject);
    child.once("exit", (code, signal) => {
      if (signal) reject(new Error(`electron_forge_signal:${signal}`));
      else resolveExit(code ?? 1);
    });
  });
}

let exitCode = 1;
try {
  await stagePythonResources({ desktopRoot });
  exitCode = await runForgePackage();
} finally {
  await cleanupPythonResources({ desktopRoot });
}
process.exitCode = exitCode;
