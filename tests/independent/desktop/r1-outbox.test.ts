import { describe, expect, test, vi } from 'vitest';
import { OutboxRetentionController } from '../../../apps/desktop/electron/main/outbox-retention';
import { DAY, deferred, encryptedFixture, settle, VirtualWindow } from './r1-fixtures';

async function oldDrafts(count = 1) {
  const fixture = encryptedFixture(); const box = fixture.open();
  for (let n = 0; n < count; n++) await box.prepare(`virtual-draft-${n}`, `VIRTUAL_BODY_${n}`);
  fixture.advance(31 * DAY);
  return { fixture, box };
}

describe('R1 outbox independent persistence and consent', () => {
  test.each(['draft', 'queued', 'sending'] as const)('R1-OB-01/%s | start/exit/reload preserve every nonterminal age', async state => {
    const f = encryptedFixture(); let box = f.open();
    const entry = await box.prepare('virtual-aging', 'VIRTUAL_PERSISTENCE');
    await box.setState(entry.clientEventId, state); const expected = box.list();
    for (const delta of [30 * DAY, 1, 335 * DAY]) {
      f.advance(delta); box = f.open(); await box.load(); await box.cleanup(); await box.cleanup();
      const reader = f.open(); await reader.load(); expect(reader.list()).toEqual(expected);
    }
  });
  test('R1-OB-02 | terminal cutoff retains exactly 24h then removes after 1ms', async () => {
    const f = encryptedFixture(); const box = f.open();
    const terminal = await box.prepare('virtual-terminal', 'VIRTUAL_DONE');
    await box.setState(terminal.clientEventId, 'terminal');
    f.advance(DAY); await box.cleanup(); expect(box.list()).toHaveLength(1);
    f.advance(1); await box.cleanup(); const reader = f.open(); await reader.load(); expect(reader.list()).toEqual([]);
  });
  test('R1-OB-03 | strict age, eligible states and fresh entries constrain candidates', async () => {
    const f = encryptedFixture(); const box = f.open();
    const draft = await box.prepare('draft', 'VIRTUAL_DRAFT'); await box.setState(draft.clientEventId, 'draft');
    const queued = await box.prepare('queue', 'VIRTUAL_QUEUE');
    const sending = await box.prepare('sending', 'VIRTUAL_SENDING'); await box.setState(sending.clientEventId, 'sending');
    f.advance(30 * DAY); expect(await box.retentionCandidates()).toEqual([]);
    f.advance(1); await box.prepare('fresh', 'VIRTUAL_FRESH');
    expect((await box.retentionCandidates()).map(x => x.clientEventId)).toEqual([draft.clientEventId, queued.clientEventId]);
  });
  test('R1-OB-04 | no candidates produces no dialog, even after duplicate attach', async () => {
    const f = encryptedFixture(); const box = f.open(); await box.prepare('fresh', 'VIRTUAL_FRESH');
    const dialog = { showMessageBox: vi.fn(async () => ({ response: 1 })) };
    const controller = new OutboxRetentionController(box, dialog, () => false); const window = new VirtualWindow();
    controller.attach(window); controller.attach(window); window.emit('ready-to-show'); await settle();
    expect(dialog.showMessageBox).not.toHaveBeenCalled(); expect(box.list()).toHaveLength(1);
  });
  test('R1-OB-05 | one prompt, safe count only, explicit default/cancel retain', async () => {
    const { box } = await oldDrafts(2); const pending = deferred<{ response: number }>();
    const dialog = { showMessageBox: vi.fn(() => pending.promise) };
    const controller = new OutboxRetentionController(box, dialog, () => false); const window = new VirtualWindow();
    controller.attach(window); controller.attach(window); window.emit('ready-to-show'); await settle();
    window.emit('ready-to-show'); controller.attach(new VirtualWindow()); await settle();
    expect(dialog.showMessageBox).toHaveBeenCalledTimes(1);
    const options = dialog.showMessageBox.mock.calls[0][1];
    expect(options).toMatchObject({ buttons: ['保留', '明确删除'], defaultId: 0, cancelId: 0 });
    expect(options.message).toContain('2');
    for (const item of box.list()) { expect(JSON.stringify(options)).not.toContain(item.body); expect(JSON.stringify(options)).not.toContain(item.clientEventId); }
    pending.resolve({ response: 0 }); await settle(); expect(box.list()).toHaveLength(2);
  });
  test.each([0, -1, 2])('R1-OB-06/response=%s | nonexplicit response preserves persisted content', async response => {
    const { fixture, box } = await oldDrafts(); const expected = box.list(); const window = new VirtualWindow();
    new OutboxRetentionController(box, { showMessageBox: async () => ({ response }) }, () => false).attach(window);
    window.emit('ready-to-show'); await settle(); const reader = fixture.open(); await reader.load(); expect(reader.list()).toEqual(expected);
  });
  test('R1-OB-07 | dialog rejection preserves data without logging raw error', async () => {
    const { fixture, box } = await oldDrafts(); const expected = box.list(); const window = new VirtualWindow();
    const errors = vi.spyOn(console, 'error'); const warnings = vi.spyOn(console, 'warn');
    new OutboxRetentionController(box, { showMessageBox: async () => { throw new Error('VIRTUAL_SECRET_CANARY'); } }, () => false).attach(window);
    window.emit('ready-to-show'); await settle(); const reader = fixture.open(); await reader.load();
    expect(reader.list()).toEqual(expected); expect(errors).not.toHaveBeenCalled(); expect(warnings).not.toHaveBeenCalled();
    errors.mockRestore(); warnings.mockRestore();
  });
  test.each(['stop', 'quitting', 'destroyed', 'closed'] as const)('R1-OB-08/%s | unresolved dialog cannot delete after lifecycle stop', async action => {
    const { fixture, box } = await oldDrafts(); const expected = box.list(); const pending = deferred<{ response: number }>();
    const window = new VirtualWindow(); let quitting = false;
    const controller = new OutboxRetentionController(box, { showMessageBox: () => pending.promise }, () => quitting);
    controller.attach(window); window.emit('ready-to-show'); await settle();
    if (action === 'stop') controller.stop(); if (action === 'quitting') quitting = true;
    if (action === 'destroyed') window.destroyed = true; if (action === 'closed') window.emit('closed');
    pending.resolve({ response: 1 }); await settle(); const reader = fixture.open(); await reader.load(); expect(reader.list()).toEqual(expected);
  });
  test('R1-OB-09 | stop/destroy before ready cannot prompt or delete', async () => {
    const { box } = await oldDrafts(); const dialog = { showMessageBox: vi.fn(async () => ({ response: 1 })) };
    const controller = new OutboxRetentionController(box, dialog, () => false); const window = new VirtualWindow();
    controller.attach(window); window.destroy(); controller.stop(); window.emit('ready-to-show'); await settle();
    expect(dialog.showMessageBox).not.toHaveBeenCalled(); expect(box.list()).toHaveLength(1);
  });
  test('R1-OB-10 | explicit consent deletes only unchanged shown candidates, persisted after reload', async () => {
    const { fixture, box } = await oldDrafts(3); const original = box.list(); const pending = deferred<{ response: number }>();
    const window = new VirtualWindow(); new OutboxRetentionController(box, { showMessageBox: () => pending.promise }, () => false).attach(window);
    window.emit('ready-to-show'); await settle();
    await box.setState(original[0].clientEventId, 'sending'); await box.setState(original[1].clientEventId, 'queued');
    const fresh = await box.prepare('new', 'VIRTUAL_NEW'); pending.resolve({ response: 1 }); await settle();
    const reader = fixture.open(); await reader.load();
    expect(reader.list().map(x => x.clientEventId)).toEqual([original[0].clientEventId, original[1].clientEventId, fresh.clientEventId]);
  });
  test('R1-OB-11 | same-clock same-state update invalidates old consent identity', async () => {
    const { box } = await oldDrafts(); const id = box.list()[0].clientEventId;
    await box.setState(id, 'queued'); const shown = await box.retentionCandidates(); const before = box.list();
    await box.setState(id, 'queued'); expect(box.list()).toEqual(before);
    expect(await box.deleteConfirmed(shown)).toBe(0); expect(box.list()).toEqual(before);
  });
  test('R1-OB-12 | reload invalidates old consent, repeats cannot delete newer old items', async () => {
    const { fixture, box } = await oldDrafts(); const shown = await box.retentionCandidates(); await box.load();
    expect(await box.deleteConfirmed(shown)).toBe(0);
    const live = await box.retentionCandidates(); expect(await box.deleteConfirmed(live)).toBe(1);
    const newer = await box.prepare('newer', 'VIRTUAL_NEWER'); fixture.advance(31 * DAY);
    expect(await box.deleteConfirmed(live)).toBe(0); expect(box.list().map(x => x.clientEventId)).toEqual([newer.clientEventId]);
  });
  test.each(['prepare', 'state', 'cleanup', 'delete'] as const)('R1-OB-13/%s | write failure keeps memory/disk consistent and queue recoverable', async operation => {
    const { fixture, box } = await oldDrafts();
    if (operation === 'cleanup') await box.setState(box.list()[0].clientEventId, 'terminal');
    fixture.advance(2 * DAY); const before = box.list(); const diskBefore = fixture.bytes();
    const candidates = await box.retentionCandidates(); fixture.fail();
    const call = operation === 'prepare' ? box.prepare('fault', 'VIRTUAL_FAULT') :
      operation === 'state' ? box.setState(before[0].clientEventId, 'sending') :
      operation === 'cleanup' ? box.cleanup() : box.deleteConfirmed(candidates);
    await expect(call).rejects.toThrow('VIRTUAL_DISK_FAILURE');
    expect(box.list()).toEqual(before); expect(fixture.bytes()).toEqual(diskBefore);
    const reader = fixture.open(); await reader.load(); expect(reader.list()).toEqual(before);
    await box.prepare('recovered', 'VIRTUAL_RECOVERED'); expect(box.list()).toHaveLength(before.length + 1);
  });
  test('R1-OB-14 | pending save publishes no premature state; concurrent operations serialize', async () => {
    const f = encryptedFixture(); const box = f.open(); const gate = f.blockWrite();
    const first = box.prepare('virtual-one', 'VIRTUAL_ONE'); await settle(); expect(box.list()).toEqual([]); expect(f.bytes()).toBeNull();
    const same = box.prepare('virtual-one', 'VIRTUAL_ONE'); const second = box.prepare('virtual-two', 'VIRTUAL_TWO');
    gate.resolve(); const [one, repeated] = await Promise.all([first, same, second]);
    expect(repeated.clientEventId).toBe(one.clientEventId); expect(box.list()).toHaveLength(2);
  });
  test('R1-OB-15 | concurrent capacity limit refuses overflow without loss, encrypted blob stays opaque', async () => {
    const f = encryptedFixture(); const box = f.open();
    const replies = await Promise.allSettled(Array.from({ length: 24 }, (_, n) => box.prepare(`virtual-${n}`, `VIRTUAL_BODY_${n}`)));
    expect(replies.filter(x => x.status === 'fulfilled')).toHaveLength(20);
    const errors = replies.filter(x => x.status === 'rejected') as PromiseRejectedResult[];
    expect(errors).toHaveLength(4); expect(errors.every(x => x.reason.message === 'outbox_capacity_reached')).toBe(true);
    const reader = f.open(); await reader.load(); expect(reader.list()).toEqual(box.list());
    for (const entry of box.list()) expect(f.bytes()!.includes(Buffer.from(entry.body))).toBe(false);
  });
  test('R1-OB-16 | inactive consent and dialog save failure retain content', async () => {
    const { fixture, box } = await oldDrafts(); const before = box.list();
    expect(await box.deleteConfirmed(await box.retentionCandidates(), () => false)).toBe(0);
    fixture.fail(); const window = new VirtualWindow();
    new OutboxRetentionController(box, { showMessageBox: async () => ({ response: 1 }) }, () => false).attach(window);
    window.emit('ready-to-show'); await settle(); const reader = fixture.open(); await reader.load(); expect(reader.list()).toEqual(before);
    await box.prepare('after-dialog-fault', 'VIRTUAL_RECOVERY'); expect(box.list()).toHaveLength(2);
  });
});
