# R7断言映射（执行前冻结）

ID+group+operation+assertion共同定位；共享helper每次调用均落盘。legacy仅两个非阻断对照，SELF不计业务。原重复比较分别归组3重试后和静默后核验。

| R6行/原比较 | 稳定ID | 观测表达式 | 期望 | 运算符 | 判定 |
| --- | --- | --- | --- | --- | --- |
| [59]: expect(condition(), 'bounded public condition').toBe(true) | WAIT.CONDITION | condition() | true | eq | gate |
| [62]: expect(element, 'public control exists').not.toBeNull() | CLICK.PRESENT | element !== null | true | eq | gate |
| [70]: expect(q('main.shell')).toBe(shell) | SAFETY.SHELL_SAME | q('main.shell') === shell | true | eq | gate |
| [71]: expect(q('main.shell nav[aria-label="模块导航"]')).not.toBeNull() | SAFETY.NAV_PRESENT | q('main.shell nav[aria-label="模块导航"]') !== null | true | eq | gate |
| [72]: expect(q('main.shell aside[aria-label="统一 Agent 面板"]')).not.toBeNull() | SAFETY.AGENT_PRESENT | q('main.shell aside[aria-label="统一 Agent 面板"]') !== null | true | eq | gate |
| [73]: expect(leaked(dom.window.document.documentElement.outerHTML)).toBe(false) | SAFETY.DOM_LEAK | leaked(dom.window.document.documentElement.outerHTML) | false | eq | gate |
| [74]: expect(consoleLeak // incomplete).toBe(false) | SAFETY.CONSOLE_LEAK | consoleLeak // incomplete | false | eq | gate |
| [75]: expect(jsdomErrors).toBe(0) | SAFETY.JSDOM_ERRORS | jsdomErrors | 0 | eq | gate |
| [76]: expect(counts.denied).toBe(0) | SAFETY.DENIED | counts.denied | 0 | eq | gate |
| [82]: expect(counts.snapshots).toBe(baseline.snapshots) | STABLE.SNAPSHOTS | counts.snapshots | baseline.snapshots | eq | gate |
| [82]: expect(counts.modules).toBe(baseline.modules) | STABLE.MODULES | counts.modules | baseline.modules | eq | gate |
| [83]: expect(counts.subscribe).toBe(baseline.subscribe) | STABLE.SUBSCRIBE | counts.subscribe | baseline.subscribe | eq | gate |
| [83]: expect(counts.unsubscribe).toBe(baseline.unsubscribe) | STABLE.UNSUBSCRIBE | counts.unsubscribe | baseline.unsubscribe | eq | gate |
| [84]: expect(callbacks.size).toBe(1) | STABLE.ACTIVE | callbacks.size | 1 | eq | gate |
| [84]: expect(counts.writes).toBe(2) | STABLE.SETTINGS_WRITES | counts.writes | 2 | eq | gate |
| [85]: expect(q('main.shell')?.getAttribute('data-theme')).toBe('dark') | STABLE.THEME | q('main.shell')?.getAttribute('data-theme') | 'dark' | eq | gate |
| [86]: expect(q('main.shell')?.getAttribute('data-privacy')).toBe('on') | STABLE.PRIVACY | q('main.shell')?.getAttribute('data-privacy') | 'on' | eq | gate |
| [87]: expect(q('main.shell header [role="status"]')?.textContent).toContain('offline') | STABLE.RUNTIME_OFFLINE | Boolean(q('main.shell header [role="status"]')?.textContent?.includes('offline')) | true | eq | gate |
| [120]: expect(value).toEqual(counts.writes === 1 ? { theme: 'dark' } : { privacyMode: true }) | SETTINGS.PAYLOAD | matchesUpdate(value, counts.writes === 1 ? { theme: 'dark' } : { privacyMode: true }) | true | eq | gate |
| [140]: expect(counts.loads).toBe(1) | legacy_initial_exact_1 | counts.loads | 1 | eq | legacy |
| [141]: expect(dom.window.location.hash).toBe('#/broken') | G1.HASH | dom.window.location.hash | '#/broken' | eq | gate |
| [148]: expect(counts.loads).toBe(2) | legacy_first_retry_total_2 | counts.loads | 2 | eq | legacy |
| [154]: expect(counts.loads).toBe(initialFailureLoads) | G3.QUIET_INITIAL | counts.loads | initialFailureLoads | eq | gate |
| [156]: expect(counts.loads).toBe(initialFailureLoads + 1) | G3.RETRY_TOTAL | counts.loads | initialFailureLoads + 1 | eq | gate |
| [163]: expect(retry()?.disabled).toBe(true) | G4.PENDING_DISABLED | retry()?.disabled | true | eq | gate |
| [163]: expect(counts.loads).toBe(beforePending + 1) | G4.SINGLE_INFLIGHT | counts.loads | beforePending + 1 | eq | gate |
| [165]: expect(settleOld).toBeTypeOf('function') | G4.SETTLER_PRESENT | typeof settleOld === 'function' | true | eq | gate |
| [166]: expect(content()).toContain('R6 healthy page') | G4.HEALTHY_VISIBLE | content().includes('R6 healthy page') | true | eq | gate |
| [166]: expect(content()).not.toContain('R6 stale page') | G4.STALE_ABSENT | content().includes('R6 stale page') | false | eq | gate |
| [167]: expect(dom.window.location.hash).toBe('#/healthy') | G4.HASH | dom.window.location.hash | '#/healthy' | eq | gate |
| [172]: expect(counts.loads).toBe(beforeRenderRetry + 1) | G5.RETRY_TOTAL | counts.loads | beforeRenderRetry + 1 | eq | gate |
| [174]: expect(performance.now() - bodyStart).toBeLessThanOrEqual(10000) | BODY.BUDGET | performance.now() - bodyStart | 10000 | lte | gate |
| [200]: expect.soft(unmounted && closed && listenersRemoved && restored && !restoreFailed).toBe(true) | CLEANUP.RESOURCES | unmounted && closed && listenersRemoved && restored && !restoreFailed | true | eq | gate |
| [201]: expect.soft(activeAfterUnmount).toBe(0) | CLEANUP.ACTIVE | activeAfterUnmount | 0 | eq | gate |
| [201]: expect.soft(rescueUnsubscribe).toBe(0) | CLEANUP.RESCUE | rescueUnsubscribe | 0 | eq | gate |
| [201]: expect.soft(counts.subscribe).toBe(counts.unsubscribe) | CLEANUP.UNSUBSCRIBE | counts.subscribe | counts.unsubscribe | eq | gate |
| [202]: expect.soft(consoleLeak // incomplete).toBe(false) | CLEANUP.CONSOLE | consoleLeak // incomplete | false | eq | gate |
| [202]: expect.soft(jsdomErrors).toBe(0) | CLEANUP.JSDOM | jsdomErrors | 0 | eq | gate |
| [202]: expect.soft(counts.denied).toBe(0) | CLEANUP.DENIED | counts.denied | 0 | eq | gate |
| [203]: expect.soft(performance.now() - cleanupStart).toBeLessThanOrEqual(2000) | CLEANUP.BUDGET | performance.now() - cleanupStart | 2000 | lte | gate |
| 新增: R7 frozen baseline/action delta contract | G1.POSITIVE_INITIAL | initialBaseline | 0 | positive_integer | gate |
| 新增: R7 frozen baseline/action delta contract | G1.FIXED_QUIET | counts.loads | initialBaseline | eq | gate |
| 新增: R7 frozen baseline/action delta contract | G2.PRE_RETRY_BASELINE | preRetry | initialBaseline | eq | gate |
| 新增: R7 frozen baseline/action delta contract | G2.RETRY_TOTAL | postRetry | initialBaseline + 1 | eq | gate |
| 新增: R7 frozen baseline/action delta contract | G2.RETRY_DELTA | postRetry - preRetry | 1 | eq | gate |
| 新增: R7 frozen baseline/action delta contract | G3.HEALTHY_DELTA | counts.healthy - beforeHealthy | 1 | eq | gate |
| 新增: R7 frozen baseline/action delta contract | G3.LEAVE_NO_BROKEN_LOAD | counts.loads | beforeHealthyLoads | eq | gate |
| 新增: R7 frozen baseline/action delta contract | G3.SETTINGS_NO_LOAD | counts.loads | beforeSettingsLoads | eq | gate |
| 新增: R7 frozen baseline/action delta contract | G3.SETTINGS_NO_HEALTHY_LOAD | counts.healthy | beforeSettingsHealthy | eq | gate |
| 新增: R7 frozen baseline/action delta contract | G3.RETURN_DELTA | counts.loads - beforeReturn | 1 | eq | gate |
| [156]: expect(counts.loads).toBe(initialFailureLoads + 1) | G3.QUIET_AFTER_RETRY | counts.loads | initialFailureLoads + 1 | eq | gate |
| 新增: same-worker scalar recorder selftest | SELF.DIFFERENT | 7 | 9 | eq | selftest |
| 新增: same-worker scalar recorder selftest | SELF.BOOLEAN | true | true | eq | selftest |
