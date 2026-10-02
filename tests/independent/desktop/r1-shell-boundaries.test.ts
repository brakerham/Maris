import { createHash } from 'node:crypto';
import { afterEach, describe, expect, test, vi } from 'vitest';
import { HostClient } from '../../../apps/desktop/electron/main/host-client';
import { LocalOwnerSession } from '../../../apps/desktop/electron/main/owner-session';
import { BackendSupervisor } from '../../../apps/desktop/electron/main/backend-supervisor';
import { compileRegistry } from '../../../apps/desktop/src/modules/registry';
import { deferred, settle } from './r1-fixtures';

afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); vi.doUnmock('electron'); });
const summary = { module_id: 'virtual_one', version: '1.0.0', display_name: 'Virtual', enabled: true,
  profile_ids: ['virtual_one.assistant@1'], api_prefixes: ['/api/v1/virtual_one'], settings_schema_version: 1 };

describe('R1 remaining Shell boundaries; virtual ports, no desktop or network', () => {
  test('R1-SHELL-01 | HostClient accepts only HTTP IPv4 loopback', () => {
    const fetch = vi.fn(); vi.stubGlobal('fetch', fetch);
    for (const url of ['https://127.0.0.1:1234', 'http://localhost:1234', 'http://192.0.2.1:1234', 'http://[::1]:1234'])
      expect(() => new HostClient(new URL(url), async () => 'VIRTUAL')).toThrow('Host address is invalid.');
    expect(fetch).not.toHaveBeenCalled();
  });
  test('R1-SHELL-02 | concurrent 401 shares refresh, retries once using main-only bearer', async () => {
    const refreshed = deferred<string>(); const refresh = vi.fn(() => refreshed.promise);
    const fetch = vi.fn(async (_url, options) => options.headers.Authorization === 'Bearer VIRTUAL_OLD' ?
      new Response('', { status: 401 }) : new Response(JSON.stringify([summary]), { status: 200 }));
    vi.stubGlobal('fetch', fetch); const client = new HostClient(new URL('http://127.0.0.1:12345'), refresh);
    client.setAccessToken('VIRTUAL_OLD'); const requests = [client.modules(), client.modules()]; await settle();
    expect(refresh).toHaveBeenCalledTimes(1); refreshed.resolve('VIRTUAL_NEW');
    expect(await Promise.all(requests)).toEqual([[summary], [summary]]); expect(fetch).toHaveBeenCalledTimes(4);
    expect(fetch.mock.calls.every(([url]) => String(url).startsWith('http://127.0.0.1:12345/'))).toBe(true);
  });
  test('R1-SHELL-03 | expired refresh revokes and exposes only safe error', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('', { status: 401 })));
    const revoke = vi.fn(async () => {}); const client = new HostClient(new URL('http://127.0.0.1:12345'),
      async () => { throw new Error('VIRTUAL_PRIVATE_SQL_PATH'); }, revoke);
    await expect(client.modules()).rejects.toMatchObject({ code: 'session_expired', message: 'The local session expired.' });
    expect(revoke).toHaveBeenCalledTimes(1);
  });
  test.each(['503', 'invalid-dto', 'network'])('R1-SHELL-04/%s | backend failures do not expose body/exception', async fault => {
    vi.stubGlobal('fetch', vi.fn(async () => {
      if (fault === 'network') throw new Error('VIRTUAL_PRIVATE_SQL_PATH');
      return new Response(fault === '503' ? 'VIRTUAL_PRIVATE_SQL_PATH' : JSON.stringify([{ unexpected: 'VIRTUAL_PRIVATE_SQL_PATH' }]), { status: fault === '503' ? 503 : 200 });
    }));
    const client = new HostClient(new URL('http://127.0.0.1:12345'), async () => 'VIRTUAL');
    try { await client.modules(); throw new Error('test_expected_failure'); }
    catch (error: any) { expect(error.code).toBe(fault === 'network' ? 'backend_offline' : 'module_unavailable'); expect(JSON.stringify(error.toSafePayload())).not.toContain('VIRTUAL_PRIVATE_SQL_PATH'); }
  });
  test('R1-SHELL-05 | local owner bootstrap single-flight, refresh and revoke states', async () => {
    let saved: any = null;
    const secrets = { read: async () => saved, stage: async (v: any) => { saved = { ...v, refreshToken: null, repairRequired: false }; },
      commit: async (v: any) => { saved = { ...v, repairRequired: false }; }, markRepair: async () => { saved = { ...saved, refreshToken: null, repairRequired: true }; } };
    const host = { bootstrapStatus: vi.fn(async () => ({ needsInitialization: true })), initialize: vi.fn(async () => {}),
      login: vi.fn(async () => ({ accessToken: 'VIRTUAL_ACCESS', refreshToken: 'VIRTUAL_REFRESH' })),
      refresh: vi.fn(async () => ({ accessToken: 'VIRTUAL_NEXT', refreshToken: 'VIRTUAL_NEXT_REFRESH' })) };
    const owner = new LocalOwnerSession(host, secrets, () => ({ handle: 'virtual_owner', password: 'VIRTUAL_PASSWORD' }));
    expect(await Promise.all([owner.establish(), owner.establish()])).toEqual(['authenticated', 'authenticated']);
    expect(host.initialize).toHaveBeenCalledTimes(1); expect(host.login).toHaveBeenCalledTimes(1);
    expect(await Promise.all([owner.refresh(), owner.refresh()])).toEqual(['VIRTUAL_NEXT', 'VIRTUAL_NEXT']);
    expect(host.refresh).toHaveBeenCalledTimes(1); await owner.revoke(); expect(owner.safeState).toBe('needs_repair');
    expect(() => owner.accessToken()).toThrow('owner_session_needs_repair'); expect(await owner.establish()).toBe('needs_repair');
    expect(host.login).toHaveBeenCalledTimes(1);
  });

  function supervisorPort(badIdentity = false) {
    let child: any; let exit: (() => void) | undefined;
    const port = {
      start: vi.fn(async ({ instanceId, nonce }) => {
        child = { instanceId, nonceDigest: badIdentity ? '0'.repeat(64) : createHash('sha256').update(nonce).digest('hex'), port: 12345,
          handle: {}, stop: vi.fn(async () => {}), forceStopTree: vi.fn(async () => {}),
          onExit: (cb: () => void) => { exit = cb; return () => { exit = undefined; }; } }; return child;
      }),
      ready: vi.fn(async () => true), health: vi.fn(async () => true), baseUrl: () => new URL('http://127.0.0.1:12345'),
      delay: vi.fn((ms: number) => ms === 5000 ? new Promise<void>(() => {}) : Promise.resolve()),
    };
    return { port, child: () => child, exit: () => exit?.() };
  }
  test('R1-SHELL-06 | managed start/recover single-flight and bounded retry', async () => {
    const f = supervisorPort(); const supervisor = new BackendSupervisor('managed', f.port);
    expect((await Promise.all([supervisor.start(), supervisor.start()])).every(x => x.state === 'online')).toBe(true);
    expect(f.port.start).toHaveBeenCalledTimes(1); f.exit(); expect(supervisor.snapshot().state).toBe('offline');
    await Promise.all([supervisor.recover(), supervisor.recover()]); await supervisor.recover(); await supervisor.recover();
    expect(f.port.start).toHaveBeenCalledTimes(4);
    expect((await supervisor.recover()).errorCode).toBe('backend_recovery_exhausted');
    expect(f.port.delay.mock.calls.map(x => x[0]).filter(ms => ms !== 5000)).toEqual([1000, 2000, 4000]);
    await supervisor.shutdown(); const count = f.port.start.mock.calls.length; await supervisor.start(); expect(f.port.start).toHaveBeenCalledTimes(count);
  });
  test('R1-SHELL-07 | bad managed nonce is rejected and candidate cleaned', async () => {
    const f = supervisorPort(true); const supervisor = new BackendSupervisor('managed', f.port);
    expect((await supervisor.start()).errorCode).toBe('backend_identity_rejected'); expect(f.child().stop).toHaveBeenCalledTimes(1);
    expect(f.port.ready).not.toHaveBeenCalled(); await supervisor.shutdown();
  });
  test('R1-SHELL-08 | external observation never acquires stop rights', async () => {
    const f = supervisorPort(); const external = { instanceId: 'virtual_external', nonceDigest: '0'.repeat(64), port: 12345, handle: {},
      stop: vi.fn(async () => {}), forceStopTree: vi.fn(async () => {}) };
    const observeExternal = vi.fn(async () => external);
    const supervisor = new BackendSupervisor('external_dev', { ...f.port, observeExternal }, Date.now, 'VIRTUAL_NONCE_'+'x'.repeat(32));
    expect((await supervisor.start()).mode).toBe('external_dev'); await supervisor.shutdown();
    expect(f.port.start).not.toHaveBeenCalled(); expect(external.stop).not.toHaveBeenCalled(); expect(external.forceStopTree).not.toHaveBeenCalled();
  });
  test('R1-SHELL-09 | preload exports narrow typed methods, no generic IPC', async () => {
    vi.resetModules(); let bridge: any; const invoke = vi.fn(async () => ({ accepted: true }));
    vi.doMock('electron', () => ({ contextBridge: { exposeInMainWorld: (name: string, value: unknown) => { expect(name).toBe('maris'); bridge = value; } },
      ipcRenderer: { invoke, on: vi.fn(), removeListener: vi.fn() } }));
    await import('../../../apps/desktop/electron/preload/index');
    expect(Object.keys(bridge).sort()).toEqual(['external','modules','outbox','runtime','settings','window']); expect(Object.isFrozen(bridge)).toBe(true);
    expect(Object.keys(bridge.runtime).sort()).toEqual(['getSnapshot','recover','subscribe']);
    for (const forbidden of ['invoke','send','ipcRenderer','require','process','token','nonce']) expect(bridge[forbidden]).toBeUndefined();
    await bridge.runtime.getSnapshot(); await bridge.runtime.recover(); await bridge.modules.list(); await bridge.settings.update({ privacyMode: true });
    await bridge.window.perform('show_main'); await bridge.external.open('privacy');
    expect(invoke.mock.calls.map(x => x[0])).toEqual(['runtime:get-snapshot@1','runtime:recover@1','modules:list@1','settings:update@1','window:perform@1','external:open@1']);
  });

  function contribution(moduleId: string) {
    return { moduleId, version: '1.0.0', hostUiMajor: 1, expectedApiPrefixes: [`/api/v1/${moduleId}`],
      navigation: { label: 'Virtual module', order: 1 }, routes: [{ routeId: `${moduleId}_route`, path: `/${moduleId}` }],
      agentPanel: { profileId: `${moduleId}.assistant@1`, title: 'Virtual' }, settings: [{ key: `${moduleId}_setting`, schemaVersion: 1 }],
      companion: { appearanceId: `${moduleId}_pet`, label: 'Virtual pet' } };
  }
  test('R1-SHELL-10 | two distinct virtual contributions compile, no product module created', () => {
    expect(compileRegistry([contribution('virtual_alpha'), contribution('virtual_beta')])).toHaveLength(2);
  });
  test.each(['module','profile','route','appearance'])('R1-SHELL-11/%s | duplicate identity fails closed', kind => {
    const first = contribution('virtual_alpha'); const second = contribution('virtual_beta');
    if (kind === 'module') second.moduleId = first.moduleId;
    if (kind === 'profile') second.agentPanel.profileId = first.agentPanel.profileId;
    if (kind === 'route') second.routes[0].routeId = first.routes[0].routeId;
    if (kind === 'appearance') second.companion.appearanceId = first.companion.appearanceId;
    expect(() => compileRegistry([first, second])).toThrow('desktop_registry_conflict');
  });
  test('R1-SHELL-12 | incompatible UI major and noncanonical ASCII/version reject', () => {
    const good = contribution('virtual_alpha');
    for (const patch of [{ hostUiMajor: 2 }, { moduleId: ' Virtual_alpha' }, { moduleId: '虚拟' }, { version: '01.0.0' },
      { agentPanel: { profileId: 'virtual_alpha.assistant@01', title: 'Virtual' } }]) expect(() => compileRegistry([{ ...good, ...patch }])).toThrow();
  });
  test('R1-SHELL-13 | UI-04 | setting keys must be globally unique across contributions', () => {
    const first = contribution('virtual_alpha'); const second = contribution('virtual_beta');
    first.settings[0].key = 'virtual_shared_setting'; second.settings[0].key = 'virtual_shared_setting';
    let returned: any; let failure: any;
    try { returned = compileRegistry([first, second]); } catch (error) { failure = error; }
    console.info('R1 registry collision evidence', JSON.stringify({ globalSettingKey: 'virtual_shared_setting',
      moduleIds: [first.moduleId, second.moduleId], accepted: !failure, acceptedModules: returned?.length ?? 0,
      rejectionCode: failure?.message ?? null, contract: 'IF-003 section 5 global setting uniqueness' }));
    expect(failure?.message).toBe('desktop_registry_conflict');
  });
});
