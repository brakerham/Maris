import { expect, test } from 'vitest';
import { compileRegistry } from '../../../apps/desktop/src/modules/registry';

function ui(moduleId: string, key: string, schemaVersion = 1) {
  return { moduleId, version: '1.0.0', hostUiMajor: 1, expectedApiPrefixes: [`/api/v1/${moduleId}`],
    navigation: { label: 'Virtual', order: 1 }, routes: [{ routeId: `${moduleId}_route`, path: `/${moduleId}` }],
    agentPanel: { profileId: `${moduleId}.assistant@1`, title: 'Virtual' },
    settings: [{ key, schemaVersion }], companion: { appearanceId: `${moduleId}_pet`, label: 'Virtual' } };
}

test.each([[false,1],[true,1],[false,2],[true,2]] as const)('R2-REG-01/reverse=%s/schema=%s | cross-module setting rejects atomically', (reverse, version) => {
  const values = [ui('virtual_left', 'shared_setting'), ui('virtual_right', 'shared_setting', version)];
  if (reverse) values.reverse();
  const before = JSON.stringify(values); let registry: unknown = 'no_return';
  expect(() => { registry = compileRegistry(values); }).toThrow('desktop_registry_conflict');
  expect(registry).toBe('no_return'); expect(JSON.stringify(values)).toBe(before);
});
test.each([1,2])('R2-REG-02/schema=%s | duplicate key within one module rejects', version => {
  const value = ui('virtual_left', 'shared_setting'); value.settings.push({ key: 'shared_setting', schemaVersion: version });
  expect(() => compileRegistry([value])).toThrow('desktop_registry_conflict');
});
test('R2-REG-03 | distinct global keys remain legal in both module orders', () => {
  const values = [ui('virtual_left', 'left_setting'), ui('virtual_right', 'right_setting')];
  expect(compileRegistry(values).map(v => v.moduleId)).toEqual(['virtual_left','virtual_right']);
  expect(compileRegistry([...values].reverse()).map(v => v.moduleId)).toEqual(['virtual_right','virtual_left']);
});
test('R2-REG-04 | failed compilation cannot poison subsequent legal registry or mutate frozen input', () => {
  const left = ui('virtual_left', 'shared_setting'); const right = ui('virtual_right', 'shared_setting');
  function freeze(value: any): any { if (value && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); } return value; }
  freeze(left); freeze(right); const before = JSON.stringify([left,right]);
  expect(() => compileRegistry([left,right])).toThrow('desktop_registry_conflict');
  expect(JSON.stringify([left,right])).toBe(before);
  expect(compileRegistry([left])).toHaveLength(1);
  expect(compileRegistry([ui('virtual_left','left_setting'),ui('virtual_right','right_setting')])).toHaveLength(2);
});
