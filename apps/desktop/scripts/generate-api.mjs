import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { existsSync } from "node:fs";

const desktop = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const root = path.resolve(desktop, "../..");
const schema = path.join(desktop, "openapi", "host.openapi.json");
const generated = path.join(desktop, "src", "generated", "host-api.ts");
const openApiCli = [path.join(desktop, "node_modules", "openapi-typescript", "bin", "cli.js"), path.join(root, "node_modules", "openapi-typescript", "bin", "cli.js")].find(existsSync);
if (!openApiCli) throw new Error("openapi_typescript_cli_missing");
const env = { ...process.env, PYTHONPATH: path.join(root, "src") };
const venvPython = path.join(root, ".venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python");
const python = process.env.MARIS_PYTHON ?? (existsSync(venvPython) ? venvPython : "python");

function run(command, args) {
  const result = spawnSync(command, args, { cwd: root, env, stdio: "inherit" });
  if (result.status !== 0) process.exit(result.status ?? 1);
}

run(python, [path.join(root, "tools", "openapi", "export_host_schema.py"), schema]);
run(process.execPath, [openApiCli, schema, "-o", generated]);
