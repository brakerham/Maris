import { createHash } from "node:crypto";
import { createReadStream } from "node:fs";
import { lstat } from "node:fs/promises";
import path from "node:path";

export const electronZipEnvironmentVariable = "MARIS_ELECTRON_ZIP_DIR";

export const officialElectronZipContract = Object.freeze({
  version: "44.4.5",
  platform: "win32",
  arch: "x64",
  fileName: "electron-v44.4.5-win32-x64.zip",
  bytes: 158_184_819,
  sha256: "11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d",
});

function contractError(code, cause) {
  return Object.assign(new Error(code, cause ? { cause } : undefined), { code });
}

export function parseElectronZipDirectory(value) {
  if (value === undefined) return undefined;
  if (typeof value !== "string" || value.length === 0 || value.trim().length === 0) {
    throw contractError("electron_zip_dir_empty");
  }
  if (value !== value.trim() || value.includes("\0")) {
    throw contractError("electron_zip_dir_invalid");
  }
  if (!path.isAbsolute(value)) {
    throw contractError("electron_zip_dir_absolute_required");
  }
  return path.normalize(value);
}

async function requireOrdinaryDirectory(directory) {
  let details;
  try {
    details = await lstat(directory);
  } catch (error) {
    if (error?.code === "ENOENT") throw contractError("electron_zip_dir_missing", error);
    throw contractError("electron_zip_dir_unreadable", error);
  }
  if (!details.isDirectory() || details.isSymbolicLink()) {
    throw contractError("electron_zip_dir_not_ordinary", undefined);
  }
}

async function requireOrdinaryFile(file) {
  let details;
  try {
    details = await lstat(file);
  } catch (error) {
    if (error?.code === "ENOENT") throw contractError("electron_zip_file_missing", error);
    throw contractError("electron_zip_file_unreadable", error);
  }
  if (!details.isFile() || details.isSymbolicLink()) {
    throw contractError("electron_zip_file_not_ordinary");
  }
  return details;
}

async function sha256File(file) {
  const hash = createHash("sha256");
  try {
    for await (const chunk of createReadStream(file)) hash.update(chunk);
  } catch (error) {
    throw contractError("electron_zip_file_unreadable", error);
  }
  return hash.digest("hex");
}

export async function verifyElectronZipDirectory(value, contract = officialElectronZipContract) {
  const directory = parseElectronZipDirectory(value);
  if (directory === undefined) return undefined;
  await requireOrdinaryDirectory(directory);
  const file = path.join(directory, contract.fileName);
  const details = await requireOrdinaryFile(file);
  if (details.size !== contract.bytes) throw contractError("electron_zip_length_mismatch");
  const sha256 = await sha256File(file);
  if (sha256 !== contract.sha256) throw contractError("electron_zip_sha256_mismatch");
  return Object.freeze({
    directory,
    file,
    bytes: details.size,
    sha256,
    version: contract.version,
    platform: contract.platform,
    arch: contract.arch,
  });
}

export async function verifyElectronZipEnvironment(environment = process.env) {
  return await verifyElectronZipDirectory(environment[electronZipEnvironmentVariable]);
}
