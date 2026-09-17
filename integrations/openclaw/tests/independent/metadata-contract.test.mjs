import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../../", import.meta.url);

async function readJson(path) {
  return JSON.parse(await readFile(new URL(path, root), "utf8"));
}

test("B2B-P01 manifest and package identify the same built plugin", async () => {
  const [manifest, packageJson] = await Promise.all([
    readJson("openclaw.plugin.json"),
    readJson("package.json"),
  ]);
  assert.equal(manifest.id, "wife-system-finance-probe");
  assert.equal(packageJson.type, "module");
  assert.equal(packageJson.main, "./dist/index.js");
  assert.equal(packageJson.exports["."], "./dist/index.js");
  assert.deepEqual(packageJson.openclaw.extensions, ["./dist/index.js"]);
  await access(new URL("dist/index.js", root));
});

test("manifest declares the exact command/tool contract and strict local config", async () => {
  const manifest = await readJson("openclaw.plugin.json");
  assert.deepEqual(manifest.contracts.tools, ["finance_probe"]);
  assert.deepEqual(manifest.commandAliases, [{ name: "finance-probe" }]);
  assert.deepEqual(manifest.activation.onCommands, ["finance-probe"]);
  assert.equal(manifest.activation.onStartup, true);
  assert.equal(manifest.configSchema.type, "object");
  assert.equal(manifest.configSchema.additionalProperties, false);
  assert.equal(manifest.configSchema.properties.backendBaseUrl.default, "http://127.0.0.1:8000");
  assert.equal(manifest.configSchema.properties.timeoutMs.default, 5000);
  assert.equal(manifest.configSchema.properties.timeoutMs.minimum, 1);
});

test("package and lock pin the verified OpenClaw host and keep it out of runtime dependencies", async () => {
  const [packageJson, lock] = await Promise.all([
    readJson("package.json"),
    readJson("package-lock.json"),
  ]);
  assert.equal(packageJson.peerDependencies.openclaw, "2026.8.2");
  assert.equal(packageJson.devDependencies.openclaw, "2026.8.2");
  assert.equal(packageJson.dependencies.openclaw, undefined);
  assert.equal(packageJson.openclaw.compat.pluginApi, "2026.8.2");
  assert.equal(packageJson.openclaw.compat.minGatewayVersion, "2026.8.2");
  assert.equal(packageJson.openclaw.build.openclawVersion, "2026.8.2");
  assert.equal(packageJson.openclaw.build.pluginSdkVersion, "2026.8.2");
  assert.equal(lock.packages["node_modules/openclaw"].version, "2026.8.2");
});

test("publish file allowlist includes only manifest and built runtime payload", async () => {
  const packageJson = await readJson("package.json");
  assert.deepEqual(packageJson.files, ["dist", "openclaw.plugin.json"]);
  for (const forbidden of ["src", "tests", ".env", "node_modules"]){
    assert.equal(packageJson.files.includes(forbidden), false);
  }
});
