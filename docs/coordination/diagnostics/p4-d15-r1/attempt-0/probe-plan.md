# D15-R1 attempt-0 冻结计划

控制版本2026-10-03T01:07:00+08:00；新起点464/464已匹配，manifest SHA-256 1a170a063dcee793aa0310809da8fe215dbd1a005a6fbdfd33530f5e67b27225，staged=0。自身角色接单/交付变化单列授权；其余463项不得漂移。

唯一目标：同一隔离worker是否取得真实Router导出，再请求main；严格区分main import Promise终态与act返回。不是旧P1/P2/P3、独立用例或产品恢复。真实main最多一次；CLI/test/有限会话原预算15/10/60秒。controller于14.5秒开始定向收口，预留原15秒内500ms采集；不能延长。没有自动第二次启动。

## 原生证据与顺序

setup.mjs只导入node:fs/path/url，以wx独占建立journal，每条同步write/fsync后返回。worker_start、journal_ready发生于测试模块初始化前；global记录器在vi.hoisted与mock工厂可用，没有互相动态import。每行seq、相对ms、PID/parentPID和固定安全字段；日志失败退出91，不能继续无记录目标。controller在Start前独占建立controller journal/预算，再登记实际root与worker父子关系。

预期顺序为worker_start→journal_ready→hoisted_ready→body_enter→virtual_dom_bridge_ready→router_preflight_enter→factory_enter→actual_import_enter→actual_import_resolved/rejected。resolved仅保存createHashRouter为function的布尔。未到达不补写。

取得真实Router后才act_enter→main_import_enter→main_import_resolved/rejected；act_return/rejected另记。Promise旁路只记录，不向act交替代Promise、不吞错误。root_created是读取实际main导出后的确认，不能把main_import_enter解释为main模块正文已执行。

结束立即卸载实际root、取消Router观察订阅、恢复DOM/global/console/bridge；没有DOM轮询/导航/revalidate/recover。worker正常exit记录与controller外部PID退出核对分别保存；硬终止没有finally证据保持unknown。

## 与旧D15的差别及语义边界

先单独await同一个react-router specifier，令async观察工厂的importOriginal成为可记录的main前置条件；这是观察依赖预热，不能倒写旧P3时间线。不预加载目标页面，不用vi.resetModules。

createHashRouter完整展开真实导出，Reflect.apply转发原args/route/errorElement与原返回对象；仅加入空状态回调订阅供收口。不再包装loader、采集Router状态或DOM；这些旧完整观察不属于R1目标。实际main/default loader/StrictMode原样；DailyFinancePage同一个VIRTUAL_CHUNK_UNAVAILABLE factory，jsdom/global/虚拟bridge与原P3一致。不创造另一条reject。

## 预算例外与停止

只在持久序列、线性前置await源码及已退出的自有root/worker共同证明main严格未开始、首次材料保存、463固定输入未变时，才可决定一次新attempt-1的前置观察修正；不自动执行。main已开始/是否开始unknown/所有权unknown/产品错误/无法收口立即停止。新attempt-1须另冻，main总1、worker总2；不第三次、不新任务循环。两次之间不延长运行时限。

双流分开保留原行序，除固定RUN/记录器错误码外全部整行脱敏，无原Error/stack/URL/路径/DOM/私密字段。process.json保存真实exit/timeout/forcekill/字节和脱敏行计数；不把无stdout当作无事件。资源核对限自有root、setup登记worker，不使用全Node kill或进程数阈值。
