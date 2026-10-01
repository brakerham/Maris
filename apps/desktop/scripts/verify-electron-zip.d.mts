export interface ElectronZipContract {
  readonly version: string;
  readonly platform: string;
  readonly arch: string;
  readonly fileName: string;
  readonly bytes: number;
  readonly sha256: string;
}

export interface VerifiedElectronZip {
  readonly directory: string;
  readonly file: string;
  readonly bytes: number;
  readonly sha256: string;
  readonly version: string;
  readonly platform: string;
  readonly arch: string;
}

export const electronZipEnvironmentVariable: "MARIS_ELECTRON_ZIP_DIR";
export const officialElectronZipContract: Readonly<ElectronZipContract>;
export function parseElectronZipDirectory(value: string | undefined): string | undefined;
export function verifyElectronZipDirectory(
  value: string | undefined,
  contract?: Readonly<ElectronZipContract>,
): Promise<Readonly<VerifiedElectronZip> | undefined>;
export function verifyElectronZipEnvironment(
  environment?: Readonly<Record<string, string | undefined>>,
): Promise<Readonly<VerifiedElectronZip> | undefined>;
