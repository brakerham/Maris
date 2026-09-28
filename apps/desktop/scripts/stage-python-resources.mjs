import { createHash, randomUUID } from "node:crypto";
import { createReadStream } from "node:fs";
import {
  copyFile,
  lstat,
  mkdir,
  open,
  readFile,
  readdir,
  realpath,
  rename,
  rm,
  rmdir,
  unlink,
  writeFile,
} from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
export const defaultDesktopRoot = path.resolve(scriptDirectory, "..");
export const defaultRepositoryRoot = path.resolve(defaultDesktopRoot, "..", "..");
export const stagingDirectoryName = ".maris-staging";
export const runtimeDirectoryName = "python-runtime";
export const manifestFileName = "python-runtime.manifest.json";

const rejectedSegments = new Set([
  "__pycache__",
  ".pytest_cache",
  "tests",
  "build",
  "dist",
  "scratch",
]);

function comparisonPath(value) {
  const resolved = path.resolve(value);
  return process.platform === "win32" ? resolved.toLowerCase() : resolved;
}

function isWithin(parent, candidate) {
  const normalizedParent = comparisonPath(parent);
  const normalizedCandidate = comparisonPath(candidate);
  return normalizedCandidate === normalizedParent || normalizedCandidate.startsWith(`${normalizedParent}${path.sep}`);
}

export function validateRelativeResourcePath(relativePath) {
  if (typeof relativePath !== "string" || relativePath.length === 0) throw new Error("resource_path_empty");
  if (path.isAbsolute(relativePath)) throw new Error("resource_path_absolute");
  if (relativePath.includes("\\")) throw new Error("resource_path_not_posix");
  const segments = relativePath.split("/");
  if (segments.some((segment) => segment === "" || segment === "." || segment === "..")) {
    throw new Error("resource_path_traversal");
  }
  return segments.join("/");
}

async function assertPlainPath(target, expectedType) {
  const information = await lstat(target);
  if (information.isSymbolicLink()) throw new Error(`resource_reparse_rejected:${target}`);
  if (expectedType === "file" && !information.isFile()) throw new Error(`resource_file_required:${target}`);
  if (expectedType === "directory" && !information.isDirectory()) throw new Error(`resource_directory_required:${target}`);
  return information;
}

async function assertCanonicalWithin(root, target) {
  const [canonicalRoot, canonicalTarget] = await Promise.all([realpath(root), realpath(target)]);
  if (!isWithin(canonicalRoot, canonicalTarget)) throw new Error(`resource_outside_root:${target}`);
}

function containsRejectedSegment(relativePath) {
  return relativePath.split("/").some((segment) => rejectedSegments.has(segment) || segment.endsWith(".egg-info"));
}

async function walkTree(root, current, visitor) {
  await assertPlainPath(current, "directory");
  await assertCanonicalWithin(root, current);
  const children = await readdir(current, { withFileTypes: true });
  children.sort((left, right) => left.name.localeCompare(right.name, "en"));
  for (const child of children) {
    const absolute = path.join(current, child.name);
    const information = await lstat(absolute);
    if (information.isSymbolicLink()) throw new Error(`resource_reparse_rejected:${absolute}`);
    await assertCanonicalWithin(root, absolute);
    if (information.isDirectory()) await walkTree(root, absolute, visitor);
    else if (information.isFile()) await visitor(absolute, information);
    else throw new Error(`resource_type_rejected:${absolute}`);
  }
}

async function sha256(filePath) {
  const digest = createHash("sha256");
  await new Promise((resolve, reject) => {
    const input = createReadStream(filePath);
    input.on("data", (chunk) => digest.update(chunk));
    input.on("error", reject);
    input.on("end", resolve);
  });
  return digest.digest("hex");
}

async function entryFor(repositoryRoot, relativePath) {
  const safePath = validateRelativeResourcePath(relativePath);
  const absolute = path.resolve(repositoryRoot, ...safePath.split("/"));
  if (!isWithin(repositoryRoot, absolute)) throw new Error(`resource_outside_root:${safePath}`);
  const information = await assertPlainPath(absolute, "file");
  await assertCanonicalWithin(repositoryRoot, absolute);
  return Object.freeze({ path: safePath, bytes: information.size, sha256: await sha256(absolute) });
}

export async function discoverPythonResources(repositoryRoot = defaultRepositoryRoot) {
  const absoluteRepositoryRoot = path.resolve(repositoryRoot);
  await assertPlainPath(absoluteRepositoryRoot, "directory");
  const relativePaths = new Set(["alembic.ini", "migrations/env.py"]);

  const versionsRoot = path.join(absoluteRepositoryRoot, "migrations", "versions");
  await walkTree(absoluteRepositoryRoot, versionsRoot, async (absolute) => {
    const relative = path.relative(absoluteRepositoryRoot, absolute).split(path.sep).join("/");
    if (path.dirname(relative) !== "migrations/versions") return;
    if (path.extname(relative) === ".py") relativePaths.add(relative);
  });

  const packageRoot = path.join(absoluteRepositoryRoot, "src", "wife_system");
  await walkTree(absoluteRepositoryRoot, packageRoot, async (absolute) => {
    const relative = path.relative(absoluteRepositoryRoot, absolute).split(path.sep).join("/");
    if (containsRejectedSegment(relative)) return;
    if (path.extname(relative) === ".py") relativePaths.add(relative);
  });

  const entries = [];
  for (const relativePath of [...relativePaths].sort((left, right) => left.localeCompare(right, "en"))) {
    entries.push(await entryFor(absoluteRepositoryRoot, relativePath));
  }
  return Object.freeze(entries);
}

async function listPayloadFiles(root) {
  const files = [];
  await walkTree(root, root, async (absolute, information) => {
    const relative = path.relative(root, absolute).split(path.sep).join("/");
    files.push({ path: validateRelativeResourcePath(relative), bytes: information.size, sha256: await sha256(absolute) });
  });
  return files.sort((left, right) => left.path.localeCompare(right.path, "en"));
}

function manifestText(entries) {
  return `${JSON.stringify(entries.map(({ path: relativePath, bytes, sha256: digest }) => ({ path: relativePath, bytes, sha256: digest })), null, 2)}\n`;
}

async function verifyInstalledPair(target, targetManifest, entries) {
  const [installedEntries, installedManifest] = await Promise.all([
    listPayloadFiles(target),
    readFile(targetManifest, "utf8"),
  ]);
  if (JSON.stringify(installedEntries) !== JSON.stringify(entries)) throw new Error("staging_installed_payload_mismatch");
  if (installedManifest !== manifestText(entries)) throw new Error("staging_installed_manifest_mismatch");
}

async function runReplacementStep(step, beforeReplacementStep, operation) {
  if (beforeReplacementStep) await beforeReplacementStep(step);
  return await operation();
}

function committedCleanupError(step, cause, recoverableBackups) {
  const error = new Error(`staging_committed_cleanup_failed:${step}`, { cause });
  error.code = "STAGING_COMMITTED_CLEANUP_FAILED";
  error.committed = true;
  error.cleanupStep = step;
  error.recoverableBackups = Object.freeze([...recoverableBackups]);
  return error;
}

async function exists(target) {
  try {
    await lstat(target);
    return true;
  } catch (error) {
    if (error?.code === "ENOENT") return false;
    throw error;
  }
}

async function rejectReparseTree(target) {
  if (!(await exists(target))) return;
  const information = await lstat(target);
  if (information.isSymbolicLink()) throw new Error(`staging_reparse_rejected:${target}`);
  if (!information.isDirectory()) return;
  await walkTree(target, target, async () => undefined);
}

async function removeOwned(target) {
  if (!(await exists(target))) return;
  const information = await lstat(target);
  if (information.isSymbolicLink()) await unlink(target);
  else await rm(target, { recursive: true, force: true });
}

async function cleanupInterruptedSiblings(stagingRoot) {
  const names = await readdir(stagingRoot);
  for (const name of names) {
    if (
      name.startsWith(`.${runtimeDirectoryName}.tmp-`) ||
      name.startsWith(`.${runtimeDirectoryName}.backup-`) ||
      name.startsWith(`.${manifestFileName}.tmp-`) ||
      name.startsWith(`.${manifestFileName}.backup-`)
    ) await removeOwned(path.join(stagingRoot, name));
  }
}

export async function cleanupPythonResources({ desktopRoot = defaultDesktopRoot } = {}) {
  const absoluteDesktopRoot = path.resolve(desktopRoot);
  const stagingRoot = path.join(absoluteDesktopRoot, stagingDirectoryName);
  if (!(await exists(stagingRoot))) return;
  await assertPlainPath(stagingRoot, "directory");
  await removeOwned(path.join(stagingRoot, runtimeDirectoryName));
  await removeOwned(path.join(stagingRoot, manifestFileName));
  await cleanupInterruptedSiblings(stagingRoot);
  await rmdir(stagingRoot).catch((error) => {
    if (error?.code !== "ENOTEMPTY" && error?.code !== "ENOENT") throw error;
  });
}

export async function stagePythonResources({
  repositoryRoot = defaultRepositoryRoot,
  desktopRoot = defaultDesktopRoot,
  beforeReplacementStep,
} = {}) {
  const absoluteRepositoryRoot = path.resolve(repositoryRoot);
  const absoluteDesktopRoot = path.resolve(desktopRoot);
  const stagingRoot = path.join(absoluteDesktopRoot, stagingDirectoryName);
  if (!isWithin(absoluteDesktopRoot, stagingRoot)) throw new Error("staging_outside_desktop");
  await mkdir(stagingRoot, { recursive: true });
  await assertPlainPath(stagingRoot, "directory");
  await assertCanonicalWithin(absoluteDesktopRoot, stagingRoot);

  const lockPath = path.join(stagingRoot, `.${runtimeDirectoryName}.lock`);
  const lock = await open(lockPath, "wx").catch((error) => {
    if (error?.code === "EEXIST") throw new Error("staging_already_active");
    throw error;
  });
  const identifier = `${process.pid}-${randomUUID()}`;
  const target = path.join(stagingRoot, runtimeDirectoryName);
  const targetManifest = path.join(stagingRoot, manifestFileName);
  const temporary = path.join(stagingRoot, `.${runtimeDirectoryName}.tmp-${identifier}`);
  const temporaryManifest = path.join(stagingRoot, `.${manifestFileName}.tmp-${identifier}`);
  const backup = path.join(stagingRoot, `.${runtimeDirectoryName}.backup-${identifier}`);
  const backupManifest = path.join(stagingRoot, `.${manifestFileName}.backup-${identifier}`);
  let oldTargetMoved = false;
  let oldManifestMoved = false;
  let newTargetInstalled = false;
  let newManifestInstalled = false;
  let committed = false;
  let rollbackComplete = true;

  try {
    await cleanupInterruptedSiblings(stagingRoot);
    const targetExists = await exists(target);
    const manifestExists = await exists(targetManifest);
    if (targetExists !== manifestExists) throw new Error("staging_existing_pair_incomplete");
    if (targetExists) await rejectReparseTree(target);
    if (manifestExists) await assertPlainPath(targetManifest, "file");
    const entries = await discoverPythonResources(absoluteRepositoryRoot);
    await mkdir(temporary, { recursive: false });
    for (const entry of entries) {
      const source = path.resolve(absoluteRepositoryRoot, ...entry.path.split("/"));
      const destination = path.resolve(temporary, ...entry.path.split("/"));
      if (!isWithin(temporary, destination)) throw new Error(`staging_path_escape:${entry.path}`);
      await mkdir(path.dirname(destination), { recursive: true });
      await copyFile(source, destination);
    }
    const stagedEntries = await listPayloadFiles(temporary);
    if (JSON.stringify(stagedEntries) !== JSON.stringify(entries)) throw new Error("staging_manifest_mismatch");
    await writeFile(temporaryManifest, manifestText(entries), { encoding: "utf8", flag: "wx" });

    if (targetExists) {
      await runReplacementStep("move-old-payload", beforeReplacementStep, () => rename(target, backup));
      oldTargetMoved = true;
    }
    if (manifestExists) {
      await runReplacementStep("move-old-manifest", beforeReplacementStep, () => rename(targetManifest, backupManifest));
      oldManifestMoved = true;
    }
    await runReplacementStep("install-new-payload", beforeReplacementStep, () => rename(temporary, target));
    newTargetInstalled = true;
    await runReplacementStep("install-new-manifest", beforeReplacementStep, () => rename(temporaryManifest, targetManifest));
    newManifestInstalled = true;
    await verifyInstalledPair(target, targetManifest, entries);
    // This is the commit point: both formal objects exist and describe the same verified payload.
    // Cleanup failures after this line must preserve the new pair and must never enter rollback.
    committed = true;
    if (oldTargetMoved) {
      try {
        await runReplacementStep("remove-payload-backup", beforeReplacementStep, () => removeOwned(backup));
      } catch (error) {
        throw committedCleanupError("remove-payload-backup", error, [backup, backupManifest]);
      }
    }
    if (oldManifestMoved) {
      try {
        await runReplacementStep("remove-manifest-backup", beforeReplacementStep, () => removeOwned(backupManifest));
      } catch (error) {
        throw committedCleanupError("remove-manifest-backup", error, [backupManifest]);
      }
    }
    return Object.freeze({ target, manifest: targetManifest, entries });
  } catch (error) {
    if (committed) throw error;
    try {
      if (newManifestInstalled) await removeOwned(targetManifest);
      if (newTargetInstalled) await removeOwned(target);
      if (oldTargetMoved && await exists(backup)) await rename(backup, target);
      if (oldManifestMoved && await exists(backupManifest)) await rename(backupManifest, targetManifest);
    } catch (rollbackError) {
      rollbackComplete = false;
      throw new AggregateError([error, rollbackError], "staging_precommit_rollback_failed", { cause: error });
    }
    throw error;
  } finally {
    await removeOwned(temporary);
    await removeOwned(temporaryManifest);
    if (!committed && rollbackComplete) {
      await removeOwned(backup);
      await removeOwned(backupManifest);
    }
    await lock.close();
    await unlink(lockPath).catch((error) => {
      if (error?.code !== "ENOENT") throw error;
    });
  }
}

async function main() {
  if (process.argv.slice(2).includes("--clean")) {
    await cleanupPythonResources();
    return;
  }
  const result = await stagePythonResources();
  process.stdout.write(`${result.entries.length} Python runtime resources staged\n`);
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  await main().catch((error) => {
    process.stderr.write(`${error?.message ?? String(error)}\n`);
    process.exitCode = 1;
  });
}
