import { test, expect, vi } from 'vitest';
import { JSDOM, VirtualConsole } from 'jsdom';
import { act } from 'react';
const record=(globalThis as any).__d16Record;
record('test_module_evaluation_complete');
test('D16 E2 static dependency collection only',()=>{
  record('body_enter');
  expect(typeof JSDOM).toBe('function');expect(typeof VirtualConsole).toBe('function');
  expect(typeof act).toBe('function');expect(typeof vi.spyOn).toBe('function');
  record('body_finished');
});
record('test_registration_complete');
