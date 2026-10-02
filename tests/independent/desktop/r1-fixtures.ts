import { createCipheriv, createDecipheriv, randomBytes } from 'node:crypto';
import { EventEmitter } from 'node:events';
import { EncryptedOutbox } from '../../../apps/desktop/electron/main/outbox';
import { SecureStore } from '../../../apps/desktop/electron/main/secure-store';

export const DAY = 86_400_000;
export function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
export async function settle() {
  for (let n = 0; n < 4; n++) await new Promise<void>(resolve => setImmediate(resolve));
}
export function encryptedFixture() {
  const key = randomBytes(32);
  const provider = {
    isEncryptionAvailable: () => true,
    encryptString(value: string) {
      const iv = randomBytes(12); const c = createCipheriv('aes-256-gcm', key, iv);
      const bytes = Buffer.concat([c.update(value, 'utf8'), c.final()]);
      return Buffer.concat([iv, c.getAuthTag(), bytes]);
    },
    decryptString(value: Buffer) {
      const c = createDecipheriv('aes-256-gcm', key, value.subarray(0, 12));
      c.setAuthTag(value.subarray(12, 28));
      return Buffer.concat([c.update(value.subarray(28)), c.final()]).toString('utf8');
    },
  };
  const crypto = new SecureStore(provider);
  let clock = Date.UTC(2026, 0, 1), serial = 0, blob: Buffer | null = null;
  let failNext = false, gate: ReturnType<typeof deferred<void>> | null = null;
  const storage = {
    async read() { return blob && Buffer.from(blob); },
    async write(value: Buffer) {
      const activeGate = gate; gate = null;
      if (activeGate) await activeGate.promise;
      if (failNext) { failNext = false; throw new Error('VIRTUAL_DISK_FAILURE'); }
      blob = Buffer.from(value);
    },
  };
  return { crypto, provider, storage,
    open: () => new EncryptedOutbox(storage, crypto, () => clock, () => `00000000-0000-4000-8000-${String(++serial).padStart(12, '0')}`),
    advance: (ms: number) => { clock += ms; },
    fail: () => { failNext = true; },
    blockWrite: () => { gate = deferred<void>(); return gate; },
    bytes: () => blob && Buffer.from(blob),
  };
}
export class VirtualWindow extends EventEmitter {
  destroyed = false;
  isDestroyed() { return this.destroyed; }
  destroy() { this.destroyed = true; this.emit('closed'); }
}
