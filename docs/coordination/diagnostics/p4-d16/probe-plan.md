# D16 新初始化实验计划

control 2026-10-03T16:08:00+08:00；技术顾问唯一执行。起点596/596普通SHA-256匹配，清单26bc182348d17ec4832125289adc8a0d2f1595f5ac402e445d2563c660391d23，UTF-8无BOM/路径ordinal排序/LF。本人角色接单变化单列授权。新写入仅本目录、D16报告、本人状态。

## 静态起点与问题

旧A测试在body之前只有vitest、jsdom、React静态运行时依赖；Router门面、main、页面、resolver fixture没有得到求值记录。Vitest先setup，再importFile(collect)并求值测试模块依赖，最后执行body。不能把旧2条journal推定为Router死锁。P不依赖jsdom，已通过的P不重做。

| 新实验 | 唯一问题 | 最少依赖/新增证据 | 条件 |
| --- | --- | --- | --- |
| E1 | 同一固定依赖下，正文前分阶段await jsdom和React能否返回，耗时在哪一段？ | vitest、jsdom、React；模块顶层逐个enter/terminal；config/plugin、setup、test registration/body即时记录 | 首次只执行此项，不导入Router/产品/旧fixture |
| E2候选 | 若E1返回，旧A同样静态依赖形式是否能完成收集，或是否只静态图路径阻塞？ | 新极小静态import模块、首个原生标记依赖；无旧A正文，无产品 | 根据E1新证据另写问题/源码并冻结；不预先运行 |
| E2/E3替代 | 若E1停在具体依赖，使用该依赖的原生加载或精确解析边界反证runner路径 | 只限已经定位的基础设施依赖，不运行目标业务 | 必须先记录新问题与原因；最多剩余预算，不同探针盲试禁止 |

最多3次Vitest诊断CLI，每次120秒总体硬限（118秒开始收口，2秒采集预留），累计动态≤360秒；无产品main、页面loader、故障fixture、旧P/A/B运行。10秒testTimeout仅控制新极小body，不能误标为收集超时。120秒是新实验的安全上限，不改旧15秒记录或业务5秒等待。第一失败及工具修正均保留，每次新实验独立目录/worker/cache。

## 即时证据与语义

controller先记录预算/root创建时间和PID；config执行时原生日志建立server journal，再记录configResolved、configureServer、必要模块resolve/load/transform hook；stage名字只表示该hook到达，不伪称最终模块完成。worker setup只原生fs/path/url；每条同步追加/fsync并带seq/相对ms/PID/parent。E1顶层await的enter/resolve/reject与test body分别计时。不同进程相对时钟不直接相减。

精确依赖仍来自固定R5 node_modules；同一React/DOM/Router物理根只读解析核对，不先求值Router。保留默认bundle config loader；每个新实验目录先建立空node_modules供Vite临时config缓存留在新目录，不安装依赖。Vite cacheDir也在新实验内。此空目录不是依赖副本，不修改外部根。

保护plugin对仓库apps/src、旧独立目标/fixture任何请求立即记录scope_violation并拒绝，controller见记录安全停机。探针代码本身不包含这些import；禁止靠间接请求获得产品证据。没有Router预热/产品/bridge/页面加载或故障注入。阶段明细只保留固定分类、ordinal、布尔、时长、PID，不输出原Error/stack、模块对象、路径/URL或DOM。

## 收口与交付

controller仅结束自有root树和已登记worker，FileShare.ReadWrite读取完整日志行；保存原始阶段、双流脱敏文本、真实退出/硬限/安全异常。没有worker事件保持unknown，不把父exit代给worker。任何所有权不明、输入变化、泄密或无法收口停止后续实验。每次结束核对固定输入；已执行文件不得改后覆盖结果。

后续独立验收建议仅写在正式裁定，不创建实际B源码任务，不执行B。A→B依赖重新评估，四公开断言与冷入口/持续真实ESM故障/当前有效请求/恢复与Windows要求保留。根因unknown也须交付可执行路线，不续建D16-R1。
