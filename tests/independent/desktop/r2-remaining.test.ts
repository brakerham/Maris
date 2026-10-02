import { expect, test } from 'vitest';
import { compileRegistry } from '../../../apps/desktop/src/modules/registry';

test('R2-UI-04-PATH | different route IDs sharing a route path must fail closed', () => {
  function contribution(id: string) {
    return { moduleId: id, version: '1.0.0', hostUiMajor: 1,
      expectedApiPrefixes: [`/api/v1/${id}`], navigation: { label: 'Virtual', order: 1 },
      routes: [{ routeId: `${id}_route`, path: '/virtual_shared' }],
      agentPanel: { profileId: `${id}.assistant@1`, title: 'Virtual' },
      settings: [{ key: `${id}_setting`, schemaVersion: 1 }],
      companion: { appearanceId: `${id}_pet`, label: 'Virtual' } };
  }
  const values = [contribution('virtual_left'), contribution('virtual_right')];
  let actual: string;
  try { actual = `accepted:${compileRegistry(values).length}`; }
  catch (error) { actual = error instanceof Error ? error.message : 'non_error_throw'; }
  console.log(JSON.stringify({ caseId: 'R2-UI-04-PATH', path: '/virtual_shared',
    routeIds: values.map(value => value.routes[0].routeId),
    expected: 'desktop_registry_conflict', actual, data: 'virtual_only' }));
  expect(actual).toBe('desktop_registry_conflict');
});
