import { test, expect } from 'vitest';
const record=(globalThis as any).__d16Record;
record('test_module_evaluation_enter');
record('jsdom_import_enter');
let domModule: typeof import('jsdom');
try { domModule=await import('jsdom'); record('jsdom_import_resolved',{jsdomIsFunction:typeof domModule.JSDOM==='function',consoleIsFunction:typeof domModule.VirtualConsole==='function'}); }
catch {record('jsdom_import_rejected');throw Error('d16_jsdom_import_rejected');}
record('react_import_enter');
let reactModule: typeof import('react');
try {reactModule=await import('react');record('react_import_resolved',{actIsFunction:typeof reactModule.act==='function'});}
catch {record('react_import_rejected');throw Error('d16_react_import_rejected');}
test('D16 E1 dependency evaluation only',()=>{
  record('body_enter');
  expect(typeof domModule.JSDOM).toBe('function');expect(typeof domModule.VirtualConsole).toBe('function');expect(typeof reactModule.act).toBe('function');
  record('body_finished');
});
record('test_module_evaluation_complete');
