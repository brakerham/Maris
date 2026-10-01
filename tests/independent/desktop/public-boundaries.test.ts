import { createCipheriv, createDecipheriv, randomBytes } from 'node:crypto';
import { describe, expect, test } from 'vitest';
import { EncryptedOutbox } from '../../../apps/desktop/electron/main/outbox';
import { SecureStore } from '../../../apps/desktop/electron/main/secure-store';
import { productionCsp, secureWebPreferences } from '../../../apps/desktop/electron/main/security';
import { validateIpc } from '../../../apps/desktop/electron/main/ipc-contract';
import { compileRegistry, intersectModules } from '../../../apps/desktop/src/modules/registry';

const DAY = 86_400_000;
const START = Date.UTC(2026, 0, 1);

// Virtual encryption adapter, not Windows DPAPI acceptance or real credentials.
function fixture() {
  const key = randomBytes(32);
  const crypto = new SecureStore({
    isEncryptionAvailable: () => true,
    encryptString(value) {
      const iv = randomBytes(12);
      const cipher = createCipheriv('aes-256-gcm', key, iv);
      const ciphertext = Buffer.concat([cipher.update(value, 'utf8'), cipher.final()]);
      return Buffer.concat([iv, cipher.getAuthTag(), ciphertext]);
    },
    decryptString(blob) {
      const cipher = createDecipheriv('aes-256-gcm', key, blob.subarray(0, 12));
      cipher.setAuthTag(blob.subarray(12, 28));
      return Buffer.concat([cipher.update(blob.subarray(28)), cipher.final()]).toString('utf8');
    },
  });
  let blob: Buffer | null = null;
  let clock = START;
  let serial = 0;
  const storage = {
    async read() { return blob && Buffer.from(blob); },
    async write(value: Buffer) { blob = Buffer.from(value); },
  };
  const open = () => new EncryptedOutbox(storage, crypto, () => clock, () => `virtual-event-${++serial}`);
  return { crypto, storage, open, advance: (delta: number) => { clock += delta; } };
}

function contribution(moduleId: string) {
  return {
    moduleId, version: '1.0.0', hostUiMajor: 1,
    expectedApiPrefixes: [`/api/v1/${moduleId}`], navigation: { label: moduleId, order: 1 },
    routes: [{ routeId: moduleId, path: `/${moduleId}` }],
    agentPanel: { profileId: `${moduleId}.assistant@1`, title: 'Virtual panel' },
    settings: [{ key: 'virtual_setting', schemaVersion: 1 }],
    companion: { appearanceId: moduleId, label: 'Virtual companion' },
  };
}

describe('C12 independent public boundaries (virtual adapters only; stop at first failure)', () => {
  test('C12-PUB-01 | SEC-05 partial | unavailable crypto fails closed', () => {
    const unavailable = new SecureStore({ isEncryptionAvailable: () => false,
      encryptString: () => { throw new Error('adapter_must_not_run'); },
      decryptString: () => { throw new Error('adapter_must_not_run'); } });
    expect(() => unavailable.seal({ body: 'VIRTUAL_ONLY' })).toThrow('secure_storage_unavailable');
    expect(() => unavailable.open(Buffer.from('VIRTUAL_ONLY'))).toThrow('secure_storage_unavailable');
  });

  test('C12-PUB-02 | SEC-05 partial | encrypted roundtrip and safe corruption error', () => {
    const { crypto } = fixture();
    const value = { body: 'C12_PUBLIC_VIRTUAL_TEXT' };
    const blob = crypto.seal(value);
    expect(blob.includes(Buffer.from(value.body))).toBe(false);
    expect(crypto.open(blob)).toEqual(value);
    blob[blob.length - 1] ^= 1;
    expect(() => crypto.open(blob)).toThrow(/^secure_storage_corrupt$/);
  });

  test('C12-PUB-03 | SEC-01/02 partial | production preferences and CSP', () => {
    expect(secureWebPreferences('VIRTUAL_PRELOAD')).toMatchObject({ sandbox: true,
      contextIsolation: true, nodeIntegration: false, webSecurity: true, allowRunningInsecureContent: false });
    for (const directive of ["script-src 'self'", "connect-src 'none'", "object-src 'none'", "frame-src 'none'"])
      expect(productionCsp.split('; ')).toContain(directive);
    expect(productionCsp).not.toMatch(/unsafe-inline|unsafe-eval/);
  });

  test('C12-PUB-04 | SEC-04 partial | wrong sender, frame, origin and parameters reject', () => {
    const frame = { url: 'file:///VIRTUAL/app/index.html' };
    const sender = { mainFrame: frame };
    const window = { webContents: sender } as any;
    const good = { sender, senderFrame: frame } as any;
    expect(validateIpc(good, window, 'runtime:get-snapshot@1', [])).toEqual([]);
    expect(() => validateIpc({ ...good, sender: {} }, window, 'runtime:recover@1', [])).toThrow('ipc_sender_rejected');
    expect(() => validateIpc({ ...good, senderFrame: { ...frame } }, window, 'runtime:recover@1', [])).toThrow('ipc_sender_rejected');
    frame.url = 'https://untrusted.invalid/';
    expect(() => validateIpc(good, window, 'runtime:recover@1', [])).toThrow('ipc_origin_rejected');
    frame.url = 'file:///VIRTUAL/app/index.html';
    for (const args of [[{ theme: 'dark', token: 'VIRTUAL_ONLY' }], [{ privacyMode: 'yes' }], [{ theme: 'dark' }, 'extra']])
      expect(() => validateIpc(good, window, 'settings:update@1', args)).toThrow();
    expect(() => validateIpc(good, window, 'outbox:enqueue@1', [{ draftId: 'not-a-uuid', body: '' }])).toThrow();
  });

  test('C12-PUB-05 | UI-01 partial | host intersection excludes incompatible contributions', () => {
    const ui = contribution('virtual_one');
    const registry = compileRegistry([ui]);
    const host = { module_id: ui.moduleId, version: '1.9.0', enabled: true,
      profile_ids: [ui.agentPanel.profileId], api_prefixes: [...ui.expectedApiPrefixes], settings_schema_version: 1 };
    expect(intersectModules(registry, [host])).toEqual(registry);
    for (const patch of [{ enabled: false }, { module_id: 'unknown' }, { version: '2.0.0' },
      { profile_ids: ['virtual_one.assistant@2'] }, { api_prefixes: [] }, { settings_schema_version: 2 }])
      expect(intersectModules(registry, [{ ...host, ...patch }])).toEqual([]);
  });

  test('C12-PUB-06 | SUP-06 partial | concurrent identical draft retains one ID and one entry', async () => {
    const outbox = fixture().open();
    const replies = await Promise.all(Array.from({ length: 12 }, () => outbox.prepare('virtual-draft', 'VIRTUAL_ONLY')));
    expect(new Set(replies.map(x => x.clientEventId)).size).toBe(1);
    expect(outbox.list()).toHaveLength(1);
  });

  test('C12-PUB-07 | SUP-06 partial | encrypted reload retains payload and event ID', async () => {
    const f = fixture(); const first = f.open();
    const before = await first.prepare('virtual-draft', 'VIRTUAL_RESTART');
    const restarted = f.open(); await restarted.load();
    const after = await restarted.prepare('virtual-draft', 'VIRTUAL_RESTART');
    expect(after.clientEventId).toBe(before.clientEventId);
    expect(after.digest).toBe(before.digest);
    expect(restarted.list()).toEqual([before]);
  });

  test('C12-PUB-08 | SUP-06 partial | changing submitted body derives a new ID', async () => {
    const outbox = fixture().open();
    const before = await outbox.prepare('virtual-draft', 'VIRTUAL_BEFORE');
    await outbox.setState(before.clientEventId, 'sending');
    const after = await outbox.prepare('virtual-draft', 'VIRTUAL_AFTER');
    expect(after.clientEventId).not.toBe(before.clientEventId);
    expect(after.digest).not.toBe(before.digest);
    expect(outbox.list()).toHaveLength(2);
  });

  test('C12-PUB-09 | SUP-06 partial | capacity refusal preserves all 20 entries on reload', async () => {
    const f = fixture(); const outbox = f.open();
    for (let i = 0; i < 20; i++) await outbox.prepare(`virtual-${i}`, `VIRTUAL_${i}`);
    const expected = outbox.list();
    await expect(outbox.prepare('virtual-overflow', 'VIRTUAL_OVERFLOW')).rejects.toThrow('outbox_capacity_reached');
    const restarted = f.open(); await restarted.load();
    expect(restarted.list()).toEqual(expected);
  });

  test('C12-PUB-10 | SUP-06 partial | terminal retention boundary and fresh unsent entry', async () => {
    const f = fixture(); const outbox = f.open();
    const terminal = await outbox.prepare('virtual-terminal', 'VIRTUAL_TERMINAL');
    await outbox.setState(terminal.clientEventId, 'terminal');
    const unsent = await outbox.prepare('virtual-unsent', 'VIRTUAL_UNSENT');
    f.advance(DAY); await outbox.cleanup();
    expect(outbox.list().map(x => x.clientEventId)).toContain(terminal.clientEventId);
    f.advance(1); await outbox.cleanup();
    expect(outbox.list()).toEqual([unsent]);
  });

  test('C12-PUB-11 | SUP-06 | old unsubmitted drafts survive startup cleanup without deletion consent', async () => {
    const f = fixture(); const outbox = f.open();
    const draft = await outbox.prepare('virtual-old-draft', 'VIRTUAL_OLD_DRAFT');
    await outbox.setState(draft.clientEventId, 'draft');
    const queued = await outbox.prepare('virtual-old-queue', 'VIRTUAL_OLD_QUEUE');
    const expected = outbox.list();
    f.advance(30 * DAY); await outbox.cleanup();
    expect(outbox.list()).toEqual(expected);
    // Startup calls load() then cleanup(); no user confirmation has been supplied.
    f.advance(1);
    const restarted = f.open(); await restarted.load(); await restarted.cleanup();
    const persisted = f.open(); await persisted.load();
    console.info('C12 aging evidence', JSON.stringify({ before: expected.length,
      after: restarted.list().length, persisted: persisted.list().length,
      statesBefore: expected.map(x => x.state), elapsedMilliseconds: 30 * DAY + 1,
      userDeletionConsent: false, actualIds: persisted.list().map(x => x.clientEventId),
      expectedIds: [draft.clientEventId, queued.clientEventId] }));
    expect(persisted.list()).toEqual(expected);
  });
});
