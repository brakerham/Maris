import { createHash } from "node:crypto";
import { mkdtemp, mkdir, readFile, readdir, rm, symlink, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, test } from "vitest";
import {
  cleanupPythonResources,
  discoverPythonResources,
  manifestFileName,
  runtimeDirectoryName,
  stagePythonResources,
  stagingDirectoryName,
  validateRelativeResourcePath,
} from "../../scripts/stage-python-resources.mjs";

const unitDirectory = path.dirname(fileURLToPath(import.meta.url));
const repositoryRoot = path.resolve(unitDirectory, "..", "..", "..", "..");
const desktopSourceRoot = path.resolve(unitDirectory, "..", "..");
const temporaryRoots: string[] = [];

async function temporaryDirectory(name: string) {
  const root = await mkdtemp(path.join(os.tmpdir(), `maris-${name}-`));
  temporaryRoots.push(root);
  return root;
}

async function write(root: string, relative: string, value = relative) {
  const target = path.join(root, ...relative.split("/"));
  await mkdir(path.dirname(target), { recursive: true });
  await writeFile(target, value, "utf8");
  return target;
}

async function createFixtureRepository() {
  const root = await temporaryDirectory("python-source");
  await write(root, "alembic.ini", "[alembic]\nscript_location = migrations\n");
  await write(root, "migrations/env.py", "ENV = True\n");
  await write(root, "migrations/versions/a_revision.py", "revision = 'a'\n");
  await write(root, "src/wife_system/__init__.py", "__all__ = []\n");
  await write(root, "src/wife_system/api/service.py", "READY = True\n");
  return root;
}

async function collectPythonFiles(root: string, current = root): Promise<string[]> {
  const result: string[] = [];
  for (const entry of await readdir(current, { withFileTypes: true })) {
    const target = path.join(current, entry.name);
    if (entry.isDirectory()) result.push(...await collectPythonFiles(root, target));
    else if (entry.isFile() && entry.name.endsWith(".py")) {
      result.push(path.relative(repositoryRoot, target).split(path.sep).join("/"));
    }
  }
  return result;
}

async function collectRelativeFiles(root: string, current = root): Promise<string[]> {
  const result: string[] = [];
  for (const entry of await readdir(current, { withFileTypes: true })) {
    const target = path.join(current, entry.name);
    if (entry.isDirectory()) result.push(...await collectRelativeFiles(root, target));
    else if (entry.isFile()) result.push(path.relative(root, target).split(path.sep).join("/"));
  }
  return result.sort((left, right) => left.localeCompare(right, "en"));
}

async function expectCompletePair(desktop: string, expectedService: string) {
  const staging = path.join(desktop, stagingDirectoryName);
  const payload = path.join(staging, runtimeDirectoryName);
  const manifest = path.join(staging, manifestFileName);
  const entries = JSON.parse(await readFile(manifest, "utf8")) as Array<{ path: string; bytes: number; sha256: string }>;
  expect(await collectRelativeFiles(payload)).toEqual(entries.map((entry) => entry.path));
  for (const entry of entries) {
    const content = await readFile(path.join(payload, ...entry.path.split("/")));
    expect(content.byteLength).toBe(entry.bytes);
    expect(createHash("sha256").update(content).digest("hex")).toBe(entry.sha256);
  }
  expect(await readFile(path.join(payload, "src", "wife_system", "api", "service.py"), "utf8")).toBe(expectedService);
  return { staging, payload, manifest, entries };
}

async function prepareReplacementFixture() {
  const source = await createFixtureRepository();
  const desktop = await temporaryDirectory("atomic-replacement");
  const initial = await stagePythonResources({ repositoryRoot: source, desktopRoot: desktop });
  const initialManifest = await readFile(initial.manifest, "utf8");
  const oldService = "READY = True\n";
  const newService = "READY = 'replacement'\n";
  await write(source, "src/wife_system/api/service.py", newService);
  return { source, desktop, initialManifest, oldService, newService };
}

async function replacementSiblings(staging: string) {
  return (await readdir(staging))
    .filter((name) => name !== runtimeDirectoryName && name !== manifestFileName)
    .sort((left, right) => left.localeCompare(right, "en"));
}

afterEach(async () => {
  while (temporaryRoots.length) await rm(temporaryRoots.pop()!, { recursive: true, force: true });
});

describe("Python package resource staging", () => {
  test("discovers the complete real runtime allowlist with stable sizes and hashes", async () => {
    const entries = await discoverPythonResources(repositoryRoot);
    const revisions = (await readdir(path.join(repositoryRoot, "migrations", "versions")))
      .filter((name) => name.endsWith(".py"))
      .map((name) => `migrations/versions/${name}`);
    const packageFiles = await collectPythonFiles(path.join(repositoryRoot, "src", "wife_system"));
    const expectedPaths = ["alembic.ini", "migrations/env.py", ...revisions, ...packageFiles]
      .sort((left, right) => left.localeCompare(right, "en"));
    expect(entries.map((entry) => entry.path)).toEqual(expectedPaths);
    for (const entry of entries) {
      const source = await readFile(path.join(repositoryRoot, ...entry.path.split("/")));
      expect(entry.bytes).toBe(source.byteLength);
      expect(entry.sha256).toBe(createHash("sha256").update(source).digest("hex"));
    }
  });

  test("copies only allowed Python runtime files from a polluted source tree", async () => {
    const source = await createFixtureRepository();
    const desktop = await temporaryDirectory("pollution-target");
    await write(source, "migrations/README");
    await write(source, "migrations/script.py.mako");
    await write(source, "migrations/versions/ignored.txt");
    await write(source, "src/wife_system/__pycache__/service.cpython-314.pyc");
    await write(source, "src/wife_system/cache.pyo");
    await write(source, "src/wife_system/native.pyd");
    await write(source, "src/wife_system/build/generated.py");
    await write(source, "src/wife_system/tests/test_private.py");
    await write(source, "src/wife_system/unknown.json");
    await write(source, "src/wife_system.egg-info/PKG-INFO");
    await write(source, "tests/test_not_runtime.py");
    await write(source, ".pytest_cache/cache.py");

    const result = await stagePythonResources({ repositoryRoot: source, desktopRoot: desktop });
    expect(result.entries.map((entry) => entry.path)).toEqual([
      "alembic.ini",
      "migrations/env.py",
      "migrations/versions/a_revision.py",
      "src/wife_system/__init__.py",
      "src/wife_system/api/service.py",
    ]);
    const serialized = JSON.stringify(result.entries);
    expect(serialized).not.toMatch(/__pycache__|\.py[co]|\.pyd|\.egg-info|test_private|unknown|README|script\.py\.mako/);
  });

  test("replaces an existing staging payload without retaining unknown files", async () => {
    const source = await createFixtureRepository();
    const desktop = await temporaryDirectory("replace-target");
    const staging = path.join(desktop, stagingDirectoryName);
    await write(staging, `${runtimeDirectoryName}/stale/private.bin`, "stale");
    await write(staging, manifestFileName, "stale manifest");
    await write(staging, `.${runtimeDirectoryName}.tmp-interrupted/ghost.bin`, "interrupted");
    const result = await stagePythonResources({ repositoryRoot: source, desktopRoot: desktop });
    await expect(readFile(path.join(result.target, "stale", "private.bin"), "utf8")).rejects.toMatchObject({ code: "ENOENT" });
    await expect(readFile(path.join(staging, `.${runtimeDirectoryName}.tmp-interrupted`, "ghost.bin"), "utf8")).rejects.toMatchObject({ code: "ENOENT" });
    expect(JSON.parse(await readFile(result.manifest, "utf8"))).toEqual(result.entries);
  });

  test("keeps the previous target intact and removes temporary siblings on failure", async () => {
    const source = await createFixtureRepository();
    const desktop = await temporaryDirectory("failure-target");
    const staging = path.join(desktop, stagingDirectoryName);
    const marker = await write(staging, `${runtimeDirectoryName}/previous.txt`, "previous");
    await write(staging, manifestFileName, "previous manifest");
    const outside = await temporaryDirectory("junction-outside");
    await write(outside, "outside.py", "SECRET = False\n");
    await symlink(outside, path.join(source, "src", "wife_system", "linked"), process.platform === "win32" ? "junction" : "dir");

    await expect(stagePythonResources({ repositoryRoot: source, desktopRoot: desktop })).rejects.toThrow(/resource_reparse_rejected/);
    expect(await readFile(marker, "utf8")).toBe("previous");
    expect(await readFile(path.join(staging, manifestFileName), "utf8")).toBe("previous manifest");
    expect((await readdir(staging)).filter((name) => name.includes(".tmp-") || name.includes(".backup-"))).toEqual([]);
  });

  test.each([
    ["move-old-manifest", "after the old payload moves and before the old manifest moves"],
    ["install-new-payload", "after both old objects move and before the new payload installs"],
    ["install-new-manifest", "after the new payload installs and before the new manifest installs"],
  ] as const)("restores the complete old pair when replacement fails %s (%s)", async (faultStep, _description) => {
    const fixture = await prepareReplacementFixture();
    await expect(stagePythonResources({
      repositoryRoot: fixture.source,
      desktopRoot: fixture.desktop,
      beforeReplacementStep(step) {
        if (step === faultStep) throw new Error(`injected_replacement_failure:${step}`);
      },
    })).rejects.toThrow(`injected_replacement_failure:${faultStep}`);

    const pair = await expectCompletePair(fixture.desktop, fixture.oldService);
    expect(await readFile(pair.manifest, "utf8")).toBe(fixture.initialManifest);
    expect(await replacementSiblings(pair.staging)).toEqual([]);
  });

  test("preserves the committed new pair and both recoverable backups when payload backup cleanup fails", async () => {
    const fixture = await prepareReplacementFixture();
    await expect(stagePythonResources({
      repositoryRoot: fixture.source,
      desktopRoot: fixture.desktop,
      beforeReplacementStep(step) {
        if (step === "remove-payload-backup") throw new Error("injected_payload_backup_cleanup_failure");
      },
    })).rejects.toMatchObject({
      code: "STAGING_COMMITTED_CLEANUP_FAILED",
      committed: true,
      cleanupStep: "remove-payload-backup",
    });

    const pair = await expectCompletePair(fixture.desktop, fixture.newService);
    const siblings = await replacementSiblings(pair.staging);
    const payloadBackup = siblings.find((name) => name.startsWith(`.${runtimeDirectoryName}.backup-`));
    const manifestBackup = siblings.find((name) => name.startsWith(`.${manifestFileName}.backup-`));
    expect(siblings).toHaveLength(2);
    expect(payloadBackup).toBeDefined();
    expect(manifestBackup).toBeDefined();
    expect(await readFile(path.join(pair.staging, payloadBackup!, "src", "wife_system", "api", "service.py"), "utf8")).toBe(fixture.oldService);
    expect(await readFile(path.join(pair.staging, manifestBackup!), "utf8")).toBe(fixture.initialManifest);
  });

  test("preserves the committed new pair after payload backup removal when manifest backup cleanup fails", async () => {
    const fixture = await prepareReplacementFixture();
    await expect(stagePythonResources({
      repositoryRoot: fixture.source,
      desktopRoot: fixture.desktop,
      beforeReplacementStep(step) {
        if (step === "remove-manifest-backup") throw new Error("injected_manifest_backup_cleanup_failure");
      },
    })).rejects.toMatchObject({
      code: "STAGING_COMMITTED_CLEANUP_FAILED",
      committed: true,
      cleanupStep: "remove-manifest-backup",
    });

    const pair = await expectCompletePair(fixture.desktop, fixture.newService);
    const siblings = await replacementSiblings(pair.staging);
    expect(siblings).toHaveLength(1);
    const manifestBackup = siblings[0]!;
    expect(manifestBackup).toMatch(new RegExp(`^\\.${manifestFileName.replaceAll(".", "\\.")}\\.backup-`));
    expect(await readFile(path.join(pair.staging, manifestBackup), "utf8")).toBe(fixture.initialManifest);
  });

  test("commits a complete new pair and removes every transition artifact on normal replacement", async () => {
    const fixture = await prepareReplacementFixture();
    const result = await stagePythonResources({ repositoryRoot: fixture.source, desktopRoot: fixture.desktop });
    const pair = await expectCompletePair(fixture.desktop, fixture.newService);
    expect(JSON.parse(await readFile(result.manifest, "utf8"))).toEqual(result.entries);
    expect(pair.entries).toEqual(result.entries);
    expect(await replacementSiblings(pair.staging)).toEqual([]);
  });

  test("fails closed for absolute paths, traversal and a reparse staging root", async () => {
    expect(() => validateRelativeResourcePath(path.resolve("outside.py"))).toThrow("resource_path_absolute");
    expect(() => validateRelativeResourcePath("../outside.py")).toThrow("resource_path_traversal");
    expect(() => validateRelativeResourcePath("src/../outside.py")).toThrow("resource_path_traversal");
    const source = await createFixtureRepository();
    const desktop = await temporaryDirectory("reparse-target");
    const outside = await temporaryDirectory("staging-outside");
    await symlink(outside, path.join(desktop, stagingDirectoryName), process.platform === "win32" ? "junction" : "dir");
    await expect(stagePythonResources({ repositoryRoot: source, desktopRoot: desktop })).rejects.toThrow(/resource_(directory_required|reparse_rejected)/);
  });

  test("produces a deterministic sorted manifest without absolute or personal paths", async () => {
    const source = await createFixtureRepository();
    const desktop = await temporaryDirectory("manifest-target");
    const first = await stagePythonResources({ repositoryRoot: source, desktopRoot: desktop });
    const firstManifest = await readFile(first.manifest, "utf8");
    const second = await stagePythonResources({ repositoryRoot: source, desktopRoot: desktop });
    const secondManifest = await readFile(second.manifest, "utf8");
    expect(secondManifest).toBe(firstManifest);
    const parsed = JSON.parse(secondManifest) as Array<Record<string, unknown>>;
    expect(parsed.map((entry) => entry.path)).toEqual([...parsed.map((entry) => entry.path)].sort((a, b) => String(a).localeCompare(String(b), "en")));
    expect(parsed.every((entry) => Object.keys(entry).sort().join(",") === "bytes,path,sha256")).toBe(true);
    expect(secondManifest).not.toContain(source);
    expect(secondManifest).not.toContain(os.homedir());
  });

  test("cleans the generated payload, manifest and task siblings", async () => {
    const source = await createFixtureRepository();
    const desktop = await temporaryDirectory("cleanup-target");
    await stagePythonResources({ repositoryRoot: source, desktopRoot: desktop });
    await cleanupPythonResources({ desktopRoot: desktop });
    await expect(readdir(path.join(desktop, stagingDirectoryName))).rejects.toMatchObject({ code: "ENOENT" });
  });

  test("Forge references only the three staged runtime entries and package uses the cleanup wrapper", async () => {
    const forge = await readFile(path.join(desktopSourceRoot, "forge.config.ts"), "utf8");
    const wrapper = await readFile(path.join(desktopSourceRoot, "scripts", "package-desktop.mjs"), "utf8");
    const packageJson = JSON.parse(await readFile(path.join(desktopSourceRoot, "package.json"), "utf8")) as { scripts: Record<string, string> };
    expect(forge).toContain('".maris-staging/python-runtime/alembic.ini"');
    expect(forge).toContain('".maris-staging/python-runtime/migrations"');
    expect(forge).toContain('".maris-staging/python-runtime/src"');
    expect(forge).not.toContain('"../../src"');
    expect(forge).not.toContain('"../../migrations"');
    expect(packageJson.scripts.package).toBe("node scripts/package-desktop.mjs");
    expect(packageJson.scripts["stage:python-resources"]).toBe("node scripts/stage-python-resources.mjs");
    expect(wrapper.indexOf("await stagePythonResources")).toBeLessThan(wrapper.indexOf("await runForgePackage"));
    expect(wrapper).toMatch(/finally\s*{\s*await cleanupPythonResources/);
  });
});
