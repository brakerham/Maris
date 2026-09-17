import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);

test("manifest declares the registered tool and command activation", async () => {
  const manifest = JSON.parse(await readFile(new URL("openclaw.plugin.json", root), "utf8"));
  assert.equal(manifest.id, "wife-system-finance-probe");
  assert.deepEqual(manifest.contracts.tools, ["finance_probe"]);
  assert.deepEqual(manifest.activation.onCommands, ["finance-probe"]);
  assert.equal(manifest.activation.onStartup, true);
  assert.equal(manifest.configSchema.additionalProperties, false);
  assert.equal(manifest.configSchema.properties.timeoutMs.default, 5000);
});

test("package pins the locally verified OpenClaw version and built runtime entry", async () => {
  const packageJson = JSON.parse(await readFile(new URL("package.json", root), "utf8"));
  assert.equal(packageJson.peerDependencies.openclaw, "2026.8.2");
  assert.equal(packageJson.devDependencies.openclaw, "2026.8.2");
  assert.equal(packageJson.dependencies.typebox, "1.3.17");
  assert.deepEqual(packageJson.openclaw.extensions, ["./dist/index.js"]);
  assert.equal(packageJson.openclaw.compat.pluginApi, "2026.8.2");
});
