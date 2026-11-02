export interface EncryptionProvider {
  isEncryptionAvailable(): boolean;
  encryptString(value: string): Buffer;
  decryptString(value: Buffer): string;
}

export class SecureStore {
  constructor(private readonly provider: EncryptionProvider) {}
  seal(value: unknown): Buffer {
    if (!this.provider.isEncryptionAvailable()) throw new Error("secure_storage_unavailable");
    return this.provider.encryptString(JSON.stringify(value));
  }
  open<T>(value: Buffer): T {
    if (!this.provider.isEncryptionAvailable()) throw new Error("secure_storage_unavailable");
    try { return JSON.parse(this.provider.decryptString(value)) as T; }
    catch { throw new Error("secure_storage_corrupt"); }
  }
}
