import { journal } from './native-journal.mjs';
const record=journal('worker');
globalThis.__d16Record=record;
record('worker_start'); record('journal_ready');
process.once('exit', code=>record('worker_exit',{exitCode:code}));
