"""Prepare observation handoff once from actual first-run receipts; no target execution."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[3];OWN=ROOT/'tests/independent/desktop/evidence/r4-r1'
REPORT='docs/testing/phase-4-c12-r4-r1-observation-windows-report.md';MATRIX='docs/testing/phase-4-modular-agent-host-test-matrix.md'
assert not (ROOT/REPORT).exists(),'handoff_once'
log=(OWN/'observed-failure/run.log').read_text(encoding='utf-8-sig');receipts=[json.loads(line) for line in log.splitlines() if line.startswith('{')];assert len(receipts)==2
sample,cleanup=receipts;assert sample['state']['mockHits']==1 and not sample['state']['alertShown'] and cleanup['rootEmpty'] and cleanup['activeSubscriptions']==0
(OWN/'observation-receipts.json').write_text(json.dumps({'sample':sample,'cleanup':cleanup},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
baseline=json.loads((OWN/'baseline.json').read_text(encoding='utf-8'));cases=[r for r in baseline['cases'] if r[1]=='B']
report='''# P4-C12-R4-R1 可观察故障复验与Windows验收报告

- 角色：既有独立测试智能体、唯一负责人；control 2026-10-02T23:46:00+08:00；任务卡p4-c12-r4-r1-observation-tester.md。
- 复验于2026-10-02 23:55 Asia/Shanghai；具体执行时刻以首次JSON/log为准。
- **交付 blocked / finished**：本轮属于任务卡结果分类2，mock真实命中，但5秒内未出现预期alert。原四条业务要求不降低，旧LAZY-001不建议关闭；未确定实际错误处理终态及原因，不新增已定级产品P0/P1。后续恢复/兼容/Windows停止，最终裁定属总控。

## 新观察节点与事实

新增R4-R1-UI-02-OBSERVED-FAILURE只运行一次，**0 passed、1 failed，exit1**。它是新可观察节点，不把旧R4首次失败改成passed，也没有重跑旧r3代码。只有原DailyFinancePage mock factory增加vi.hoisted命中/时间回执；仍调用真实生产main启动，真实DesktopApp/React Router/Shell/compileRegistry与Host交集，不以替代Router或另一条throw冒充故障。

| 观测 | 首次实际证据 |
| --- | --- |
| mock factory | **1次真实命中**，固定虚拟throw；receipt epochMs=1790956538349 |
| route/hash | **#/daily**，合法daily_finance摘要/canonical Profile，API prefix count1、schemaVersion1 |
| 条件等待 | **5016ms**轮询结束（5秒上限加最后一次20ms轮询调度尾差16ms），未找到alert；testTimeout10秒，节点5416.4233ms |
| 错误提示 | alertShown=false，stopReason=fault_hit_alert_missing |
| Shell / 导航 / Agent面板 | DOM采样全部true；不能仅据此认为错误处理完成后的保持通过 |
| 内容/状态 | contentHasText=true、publicStatusCount1；未记录原始正文/URL，不能推断具体页面终态 |
| bridge调用 | runtime2、modules2、subscribe2、采样时unsubscribe1/active1；生产StrictMode真实生命周期，不将2计作不允许重复auth或产品缺陷 |
| VirtualConsole、console、未处理拒绝 | 已注册观察，安全事件数组为空；没有把异常全部静默丢弃 |
| 收口 | 真实desktopRoot已unmount、rootEmpty=true、unsubscribe2/active0、DOM closed/global restored；Vitest已exit1 |

条件等待每次把有界20ms轮询交给React act，看到mock与alert才判完成；没有在单个永不结束act中等待、没有固定睡5秒宣布通过。5秒无alert便停止，不延长或重启。实际超过旧200ms，但这只证明本次更长观察仍失败，**不证明旧200ms是唯一根因**，也不证明当前问题已定位。

## 原四条业务断言原样保留

| 原要求 | 本轮实际断言 / 采样 | 结论 |
| --- | --- | --- |
| 新前置：mock factory真实命中 | hits>0断言通过，receipt1 | 故障端口前置已建立 |
| alert包含“页面暂时无法打开” | alert不存在、textContent为undefined，首条业务断言失败 | **failed**，原要求未降低 |
| main.shell存在 | 源码断言保持；被首条失败阻止执行，采样true | not_reached；不冒称passed |
| 模块导航存在 | 源码断言保持；未执行，采样true | not_reached；不冒称passed |
| 统一Agent面板存在 | 源码断言保持；未执行，采样true | not_reached；不冒称passed |

首次错误仍为undefined/string组合的AssertionError，定位新r4-r1-observed.test.tsx:35。没有skip/xfail/重跑覆盖/另起失败任务，cleanup在finally执行并验证root与订阅清零。原R3/R4代码、配置、结果及失败历史一字不改。

原始证据：tests/independent/desktop/evidence/r4-r1/observed-failure/run.log、result.json；从首次log只读提取的observation-receipts.json。新增观测回执只含虚拟阶段/计数、公开hash、布尔DOM状态与时刻，不含token/原始URL/路径/真实profile/正文。

## 判断边界及停止分类

与R4相比，已确认故障factory命中，排除了“本轮从未进入该mock端口”这一解释；但单次命中不证明Router已将这一失败最终发布到当前可见route，也不记录其他loader尝试/终态。Host摘要合法且hash已到daily，不是无依据的空模块假设。当前源码中main确实使用module-routes，loader catch映射desktop_module_unavailable，子路由errorElement与render边界存在；这些静态接线仍不替代实际alert。

本轮证据支持的结论是：**模拟页面故障已触发，5秒内预期错误UI未观察到，独立门禁未通过**。可能的Router/异步终态、mock模块错误传播或前后尝试关系尚未核实。没有用另外的可控loader测试代替原生产入口失败，也没有声称正常EXE19门禁或Shell采样能证明错误后隔离/恢复成功。

任务卡结果分类2要求保留并停止，因此尚未执行新增瞬时/持续失败、explicit retry、健康route/settings切换、在途重复点击/离开、render异常、主题/隐私/runtime/订阅保持及无额外auth/recover/provider/outbox写入。新增开发8项与Shell/composition兼容执行0；旧成功27、outbox42、setting/path关闭证据输入不变、不重复。

需总控共同决定：基于此次命中和公开状态，如何在有限范围只读区分实际Router错误是否发布到当前route、加载尝试/终态与mock错误传播；必要时再冻结精确观察或技术核对范围。此报告不预先指定产品返修，也不自行创建下一任务/扩大时限或第二次目标启动。

## 固定输入与不变性

权威新起点**410/410 matched**，0 mismatch/missing，staged0；manifest SHA **0f695dfc03286f0c2dfe3b1c30f9cb1538600a3657eab6e9f64eedd783e9bcaf**。外部389构建输入、140out、67resources全部匹配。旧393清单/R4交付与新410清单分开，不改旧历史或拿旧协调摘要assert派发后的仓库。

固定只读根C:\\MarisLazyR5\\R5-20261002-222300，已装普通依赖和Node24.21.0/Vitest5.0.2，不安装/下载/audit/build/package。新增R4-R1配置只接R5普通依赖、React/React DOM/Router单一解析根及实际生产source；mock规范路径与builtin import均指向原DailyFinancePage。

| 产物 | 起终固定SHA-256 |
| --- | --- |
| Maris.exe | 64ce71f3a7b3055f9ad27f6d611e28c4af7e9ba8b86d8b21399b7b422844a80e |
| app.asar | 5ba47909537e1419dc275fa3ca1e5e076a1aa6d5c0205229f91defb92ddd0931 |
| workspace lock | 5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a |

终点实测end-audit.json/delivery-verification.json由新增r4-r1-delivery.py verify复算，固定410集仅tester/矩阵B备注/旧主报告与清单追加四路径变化，其余不可变；旧public/r1/r2/r3/r4测试、报告和evidence精确保持。包/lock/fuses和source389/out140/resources67不变；120ID/12列/前11列原预期与所有原状态、B外bytes及追加prefix保持，A64 passed/C20/D12 not_run不变。

## 原24项完整映射

旧R4及其引用的R3证据均是历史事实，不重复执行。每项保留完整预期；第一门禁未通过，不把其他已过节点或开发报告替代整项通过。

'''
old=(ROOT/'docs/testing/phase-4-c12-r4-lazy-windows-report.md').read_text(encoding='utf-8-sig')
for r in cases:
    cid,_,source,layer,env,mode,pre,inp,steps,expected,risk,state=r
    sec=re.search(r'### '+re.escape(cid)+r' — .*?\n(.*?)(?=\n### |\n## |\Z)',old,re.S).group(1)
    prior=re.search(r'^- 已有历史部分：(.*)$',sec,re.M).group(1);gap=re.search(r'^- 尚缺条件/证据层级：(.*)$',sec,re.M).group(1);new='not_run，观察门禁失败后停止扩大。'
    if cid=='P4B-UI-02':new='新OBS节点一次0pass/1fail：mock1、#/daily、5016ms无alert，Shell/nav/Agent采样在，真实root/订阅清理完成。';gap='已建立故障端口，未完成预期错误终态；LAZY-001不能关闭，恢复/切换/状态边界和Windows均未执行，不新增未经定位产品P1。'
    report+=f'### {cid} — {state}\n\n- 来源/风险/层/环境/方式：{source} / {risk} / {layer} / {env} / {mode}。\n- 前置：{pre}。\n- 输入：{inp}。\n- 操作：{steps}。\n- **完整原预期**：{expected}。\n- 已有历史部分：{prior}\n- 本轮新增：{new}\n- 具体缺口与层级：{gap}\n- 当前状态：`{state}`，没有全子条件通过不改passed。\n\n'
report+='''## 启动预算、安全收口、warning和交接

独立1 executed：0passed/1failed；后续独立与兼容0。产品**0/8**、辅助Electron**0/4**、Windows/CDP请求注入**0**；未建立外部C12-R4-R1 root/profile/db/session，无实际owned进程/窗口/监听需要停止。jsdom实际root卸载、订阅2→0、DOM/global清理有回执；它不证明生产Tray/后端cleanup通过。

真实chunk/会话持久化、安全CSP/导航/renderer秘密/恶意文本、generated drift、严格贡献结构余项、safeStorage/native老化提示、Tray/closePolicy/单实例/毛毛设备状态等未执行。OS注销/重启/启动项/多屏/DPI/拔屏/系统主题/透明降级人工条件保持原not_run/unverified，不要求用户现在点击，不删降验收条件。

本轮不存在配置/语法修正或目标重试；首次assert失败保留。只清理新增专属cache前重读control、验证绝对范围/无reparse，首次log/JSON及所有审计保留；不清理旧环境或个人资料。diff --check仅只读，LF→CRLF提示记录而不修改Git配置；Git staged0，无Git写操作。

无产品/开发测试/依赖/lock/build/package/迁移/冻结/control/overview/其他角色写入，无Docker/PG/OpenClaw/微信/DeepSeek/provider/真实账户/财务/原始秘密或系统设置操作。新报告、r4-r1-audit.py、r4-r1-vitest.config.mjs、r4-r1-observed.test.tsx、r4-r1-delivery.py、r4-r1-handoff.py与evidence/r4-r1单列；旧主报告/人工清单只追加、B矩阵仅备注、自身日志更新。

交付停在 **blocked / finished**。总控接收确认mock命中但预期终态缺失的新证据，裁定有限后续核对；本角色不创建新任务、启动其他角色/P4-C、不自行续跑，LAZY-001/UI-02/P4-B仍未接受。
'''
(ROOT/REPORT).write_text(report,encoding='utf-8',newline='\n')
appendix='\n\n## C12-R4-R1 可观察复验追加（2026-10-02）\n\n- [R4-R1报告](phase-4-c12-r4-r1-observation-windows-report.md)：blocked / finished。新OBS节点一次0 passed/1 failed，确认mock factory1、#/daily，但5016ms仍无alert；Shell/nav/Agent在，原四条要求不降级，旧R4首次失败不改写。\n- 原因不再能直接归于200ms，当前预期错误终态/错误传播原因仍unverified，不新增未经定位产品P1、不建议关闭LAZY-001。真实root卸载/订阅2→0/DOM/global清理有首次回执。\n- 后续独立恢复/兼容/Windows未执行，产品0/8、辅助0/4、chunk注入0；旧已通过outbox/setting/path不重跑。B仍0 passed/1 failed/19 blocked/4 not_run，人工条件保持。\n- 新首次log/JSON与observation-receipts在evidence/r4-r1，原所有资料不变；交总控裁定有限观察/核对范围，不改产品或Git、不自行续跑。\n'
for p in ['docs/testing/phase-4-c12-windows-shell-report.md','docs/testing/phase-4-c12-manual-checklist.md']:
    with (ROOT/p).open('ab')as f:f.write(appendix.encode('utf-8'))
b=(ROOT/MATRIX).read_bytes();note='\n#### C12-R4-R1 最新状态备注（2026-10-02）\n\n- 新OBS节点一次失败：mock1、#/daily、5016ms无alert，Shell/nav/Agent在，root卸载/订阅0；原四业务要求不降级，旧首次失败保留。\n- 属于结果分类2：故障端口已触发，预期错误终态未观测；LAZY-001/UI-02不关闭，不新增未经定位P1。后续独立/兼容/Windows停止；B0 passed/1 failed/19 blocked/4 not_run保持。\n- 产品0/8、辅助0/4、请求注入0；旧已过节点不重跑。[R4-R1报告](phase-4-c12-r4-r1-observation-windows-report.md)保留24项完整预期/历史/本次/缺口，交blocked / finished等总控裁定。\n\n';(ROOT/MATRIX).write_bytes(b.replace(b'### 5.3',note.encode()+b'### 5.3',1))
print('Observation report and append-only handoff prepared; no further tests executed')
