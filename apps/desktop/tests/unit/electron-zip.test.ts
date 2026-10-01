import { createHash } from "node:crypto";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, describe, expect, test, vi } from "vitest";
import {
  officialElectronZipContract,
  parseElectronZipDirectory,
  verifyElectronZipDirectory,
  verifyElectronZipEnvironment,
} from "../../scripts/verify-electron-zip.mjs";

const temporaryRoots: string[] = [];
const originalZipDirectory = process.env.MARIS_ELECTRON_ZIP_DIR;
const originalCache = process.env.MARIS_ELECTRON_CACHE;

async function temporaryDirectory(name: string) {
  const root = await mkdtemp(path.join(os.tmpdir(), `maris-${name}-`));
  temporaryRoots.push(root);
  return root;
}

function fixtureContract(content: string, fileName = "electron-v44.4.5-win32-x64.zip") {
  const bytes = Buffer.byteLength(content);
  return {
    version: "44.4.5",
    platform: "win32",
    arch: "x64",
    fileName,
    bytes,
    sha256: createHash("sha256").update(content).digest("hex"),
  } as const;
}

async function writeFixture(directory: string, content: string, fileName = "electron-v44.4.5-win32-x64.zip") {
  await mkdir(directory, { recursive: true });
  await writeFile(path.join(directory, fileName), content);
}

function restoreEnvironment() {
  if (originalZipDirectory === undefined) delete process.env.MARIS_ELECTRON_ZIP_DIR;
  else process.env.MARIS_ELECTRON_ZIP_DIR = originalZipDirectory;
  if (originalCache === undefined) delete process.env.MARIS_ELECTRON_CACHE;
  else process.env.MARIS_ELECTRON_CACHE = originalCache;
}

afterEach(async () => {
  restoreEnvironment();
  vi.resetModules();
  while (temporaryRoots.length) await rm(temporaryRoots.pop()!, { recursive: true, force: true });
});

describe("local Electron ZIP contract", () => {
  test("pins the accepted official artifact and target", () => {
    expect(officialElectronZipContract).toEqual({
      version: "44.4.5",
      platform: "win32",
      arch: "x64",
      fileName: "electron-v44.4.5-win32-x64.zip",
      bytes: 158_184_819,
      sha256: "11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d",
    });
  });

  test.each(["", "   ", " relative ", "relative", "C:\\bad\0path"])("rejects an invalid directory value %j", (value) => {
    expect(() => parseElectronZipDirectory(value)).toThrow(/electron_zip_dir_/);
  });

  test("keeps the ordinary build path when the variable is absent", async () => {
    expect(await verifyElectronZipEnvironment({})).toBeUndefined();
  });

  test("rejects a missing directory and a non-directory", async () => {
    const root = await temporaryDirectory("zip-paths");
    await expect(verifyElectronZipDirectory(path.join(root, "missing"), fixtureContract("ok")))
      .rejects.toThrow("electron_zip_dir_missing");
    const file = path.join(root, "not-a-directory");
    await writeFile(file, "file");
    await expect(verifyElectronZipDirectory(file, fixtureContract("ok")))
      .rejects.toThrow("electron_zip_dir_not_ordinary");
  });

  test("rejects a wrong version or filename without selecting a fallback", async () => {
    const root = await temporaryDirectory("zip-name");
    await writeFixture(root, "ok", "electron-v44.4.4-win32-x64.zip");
    await expect(verifyElectronZipDirectory(root, fixtureContract("ok")))
      .rejects.toThrow("electron_zip_file_missing");
  });

  test("rejects length and digest mismatches", async () => {
    const root = await temporaryDirectory("zip-integrity");
    await writeFixture(root, "bad");
    await expect(verifyElectronZipDirectory(root, { ...fixtureContract("bad"), bytes: 99 }))
      .rejects.toThrow("electron_zip_length_mismatch");
    await expect(verifyElectronZipDirectory(root, { ...fixtureContract("bad"), sha256: "0".repeat(64) }))
      .rejects.toThrow("electron_zip_sha256_mismatch");
  });

  test("accepts a matching ordinary ZIP using an injected test contract", async () => {
    const root = await temporaryDirectory("zip-valid");
    const content = "small deterministic ZIP fixture";
    const contract = fixtureContract(content);
    await writeFixture(root, content);
    await expect(verifyElectronZipDirectory(root, contract)).resolves.toEqual({
      directory: path.normalize(root),
      file: path.join(root, contract.fileName),
      bytes: contract.bytes,
      sha256: contract.sha256,
      version: contract.version,
      platform: contract.platform,
      arch: contract.arch,
    });
  });

  test("wires the validated directory into Forge and suppresses cache download options", async () => {
    const root = await temporaryDirectory("zip-forge");
    process.env.MARIS_ELECTRON_ZIP_DIR = root;
    process.env.MARIS_ELECTRON_CACHE = path.join(root, "cache-must-not-win");
    const { default: config } = await import("../../forge.config");
    expect(config.packagerConfig).toBeDefined();
    const packagerConfig = config.packagerConfig!;
    expect(packagerConfig.electronZipDir).toBe(path.normalize(root));
    expect(packagerConfig.download).toBeUndefined();
  });

  test("preserves the prior cache option when local ZIP mode is unset", async () => {
    const root = await temporaryDirectory("zip-cache");
    delete process.env.MARIS_ELECTRON_ZIP_DIR;
    process.env.MARIS_ELECTRON_CACHE = root;
    const { default: config } = await import("../../forge.config");
    expect(config.packagerConfig).toBeDefined();
    const packagerConfig = config.packagerConfig!;
    expect(packagerConfig.electronZipDir).toBeUndefined();
    expect(packagerConfig.download).toEqual({ cacheRoot: root });
  });

  test("verifies before staging and passes the process environment to Forge", async () => {
    const wrapper = await readFile(path.resolve(__dirname, "../../scripts/package-desktop.mjs"), "utf8");
    expect(wrapper.indexOf("await verifyElectronZipEnvironment")).toBeLessThan(wrapper.indexOf("await stagePythonResources"));
    expect(wrapper).toContain("env: process.env");
    expect(wrapper).not.toContain("unsafelyDisableChecksums");
  });
});
