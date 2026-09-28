import { existsSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const desktop = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const root = path.resolve(desktop, "../..");
const temp = mkdtempSync(path.join(tmpdir(), "maris-openapi-"));
const schema = path.join(temp, "host.openapi.json");
const generated = path.join(temp, "host-api.ts");
const env = { ...process.env, PYTHONPATH: path.join(root, "src") };
const openApiCli = [path.join(desktop, "node_modules", "openapi-typescript", "bin", "cli.js"), path.join(root, "node_modules", "openapi-typescript", "bin", "cli.js")].find(existsSync);
if (!openApiCli) throw new Error("openapi_typescript_cli_missing");
const venvPython = path.join(root, ".venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python");
const python = process.env.MARIS_PYTHON ?? (existsSync(venvPython) ? venvPython : "python");

try {
  const exportResult = spawnSync(python, [path.join(root, "tools", "openapi", "export_host_schema.py"), schema], { cwd: root, env, stdio: "inherit" });
  if (exportResult.status !== 0) process.exit(exportResult.status ?? 1);
  const typeResult = spawnSync(process.execPath, [openApiCli, schema, "-o", generated], { cwd: root, env, stdio: "inherit" });
  if (typeResult.status !== 0) process.exit(typeResult.status ?? 1);
  const pairs = [
    [schema, path.join(desktop, "openapi", "host.openapi.json")],
    [generated, path.join(desktop, "src", "generated", "host-api.ts")]
  ];
  for (const [actual, checkedIn] of pairs) {
    if (readFileSync(actual, "utf8") !== readFileSync(checkedIn, "utf8")) {
      console.error(`generated artifact is stale: ${path.relative(root, checkedIn)}`);
      process.exit(1);
    }
  }
  console.log("generated OpenAPI artifacts match");
} finally {
  rmSync(temp, { recursive: true, force: true });
}
