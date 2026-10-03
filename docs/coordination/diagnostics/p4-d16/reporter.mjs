export default class SafeReporter {
  onTestRunStart(){globalThis.__d16ServerRecord('run_start');}
  onTestModuleCollected(){globalThis.__d16ServerRecord('test_module_collected');}
  onTestRunEnd(modules,errors){globalThis.__d16ServerRecord('run_end',{moduleCount:modules.length,unhandledCount:errors.length});}
}
