export type PythonResourceEntry = Readonly<{ path: string; bytes: number; sha256: string }>;

export const defaultDesktopRoot: string;
export const defaultRepositoryRoot: string;
export const stagingDirectoryName: string;
export const runtimeDirectoryName: string;
export const manifestFileName: string;

export type ReplacementStep =
  | "move-old-payload"
  | "move-old-manifest"
  | "install-new-payload"
  | "install-new-manifest"
  | "remove-payload-backup"
  | "remove-manifest-backup";

export function validateRelativeResourcePath(relativePath: string): string;
export function discoverPythonResources(repositoryRoot?: string): Promise<readonly PythonResourceEntry[]>;
export function stagePythonResources(options?: Readonly<{
  repositoryRoot?: string;
  desktopRoot?: string;
  beforeReplacementStep?: (step: ReplacementStep) => void | Promise<void>;
}>): Promise<Readonly<{
  target: string;
  manifest: string;
  entries: readonly PythonResourceEntry[];
}>>;
export function cleanupPythonResources(options?: Readonly<{ desktopRoot?: string }>): Promise<void>;
