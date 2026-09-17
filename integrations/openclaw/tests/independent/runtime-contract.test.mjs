import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { dirname, join, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import test from "node:test";

const execFileAsync = promisify(execFile);
const pluginRoot = fileURLToPath(new URL("../../", import.meta.url));

test("manifest and package describe the same OpenClaw 2026.8.2 runtime entry", async () => {
  const manifest = JSON.parse(await readFile(join(pluginRoot, "openclaw.plugin.json"), "utf8"));
  const packageJson = JSON.parse(await readFile(join(pluginRoot, "package.json"), "utf8"));
  const lock = JSON.parse(await readFile(join(pluginRoot, "package-lock.json"), "utf8"));

  assert.equal(manifest.id, "wife-system-finance-probe");
  assert.deepEqual(manifest.contracts.tools, ["finance_probe"]);
  assert.deepEqual(manifest.activation.onCommands, ["finance-probe"]);
  assert.equal(manifest.configSchema.additionalProperties, false);
  assert.equal(packageJson.type, "module");
  assert.equal(packageJson.main, "./dist/index.js");
  assert.deepEqual(packageJson.openclaw.extensions, ["./dist/index.js"]);
  assert.equal(packageJson.peerDependencies.openclaw, "2026.8.2");
  assert.equal(packageJson.devDependencies.openclaw, "2026.8.2");
  assert.equal(packageJson.openclaw.compat.pluginApi, "2026.8.2");
  assert.equal(packageJson.openclaw.compat.minGatewayVersion, "2026.8.2");
  assert.equal(lock.packages["node_modules/openclaw"].version, "2026.8.2");
  await readFile(join(pluginRoot, "dist", "index.js"), "utf8");
});

test("OpenClaw runtime inspection loads command and tool from isolated state", async () => {
  const ownedTestDir = dirname(fileURLToPath(import.meta.url));
  const stateDir = await mkdtemp(join(ownedTestDir, ".runtime-state-"));
  const expectedTempRoot = `${resolve(ownedTestDir)}${sep}`.toLowerCase();
  assert.equal(`${resolve(stateDir)}${sep}`.toLowerCase().startsWith(expectedTempRoot), true);
  const configPath = join(stateDir, "openclaw.json");
  const workspaceDir = join(stateDir, "workspace");
  await mkdir(workspaceDir, { recursive: true });
  await mkdir(join(stateDir, "state"), { recursive: true });
  await writeFile(
    configPath,
    JSON.stringify({
      plugins: {
        enabled: true,
        allow: ["wife-system-finance-probe"],
        load: { paths: [pluginRoot] },
        entries: {
          "wife-system-finance-probe": {
            enabled: true,
            config: {
              backendBaseUrl: "http://127.0.0.1:8000",
              timeoutMs: 5000,
            },
          },
        },
      },
    }),
    "utf8",
  );

  try {
    const openclawEntry = join(pluginRoot, "node_modules", "openclaw", "openclaw.mjs");
    const { stdout, stderr } = await execFileAsync(
      process.execPath,
      [
        openclawEntry,
        "plugins",
        "inspect",
        "wife-system-finance-probe",
        "--runtime",
        "--json",
      ],
      {
        cwd: pluginRoot,
        env: {
          ...process.env,
          NO_COLOR: "1",
          OPENCLAW_CONFIG_PATH: configPath,
          OPENCLAW_STATE_DIR: stateDir,
          OPENCLAW_WORKSPACE_DIR: workspaceDir,
        },
        timeout: 30_000,
        maxBuffer: 2 * 1024 * 1024,
      },
    );
    const inspection = JSON.parse(stdout);
    const evidence = `${stderr}\n${JSON.stringify(inspection, null, 2)}`;
    assert.equal(inspection.plugin.id, "wife-system-finance-probe", evidence);
    assert.equal(inspection.plugin.enabled, true, evidence);
    assert.equal(inspection.plugin.status, "loaded", evidence);
    assert.equal(inspection.plugin.imported, true, evidence);
    assert.equal(inspection.plugin.dependencyStatus.requiredInstalled, true, evidence);
    assert.deepEqual(inspection.plugin.toolNames, ["finance_probe"], evidence);
    assert.deepEqual(inspection.plugin.commands, ["finance-probe"], evidence);
    assert.deepEqual(inspection.commands, ["finance-probe"], evidence);
    assert.deepEqual(inspection.tools, [{ names: ["finance_probe"], optional: false }], evidence);
    assert.deepEqual(inspection.diagnostics, [], evidence);
  } finally {
    const resolvedStateDir = resolve(stateDir);
    assert.equal(`${resolvedStateDir}${sep}`.toLowerCase().startsWith(expectedTempRoot), true);
    await rm(resolvedStateDir, { recursive: true, force: true });
  }
});
