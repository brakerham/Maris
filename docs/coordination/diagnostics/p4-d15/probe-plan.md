# D15 一次性诊断冻结计划

控制版本：2026-10-03T00:13:00+08:00。技术顾问单独执行，不调用其他智能体。此计划与 probe-source.sha256 必须在首次目标执行前固定；结果写入新 results，目录一旦存在 controller 拒绝重跑。

## 固定版本与解析

Node24.21.0，Vitest5.0.2，Vite7.3.6，React19.3.0，React DOM19.3.0，React Router8.4.0，jsdom30.1.1；复用任务卡指定 R5 普通依赖。别名及 node 环境、fork worker、JSX automatic 同 R4-R1；仅改新 root/include/cache。每项不同文件/不同 Vitest 进程/不同 worker；不提前导入被 mock 页面，不使用 vi.resetModules 改变缓存。

## 三项预期分流

| 探针 | 原操作与观察点 | 拒绝分支 | 其他分支与结论限制 |
| --- | --- | --- | --- |
| P1 | 原 DailyFinancePage 动态 import，原 fixed throw factory | 保存原 import reject 的类型、Vitest wrapper/虚拟 cause 布尔 | resolve 或 pending 说明故障未按预期成为调用方拒绝；不推断 Router |
| P2 | 真实 compileRegistry/contribution/createModuleRoutes，省略 loaders 参数，调用实际 route.loader | 应映射 desktop_module_unavailable；记录精确终态 | import 已拒绝而 loader pending/resolve 才继续定位 loader；不启动 UI |
| P3 | R4-R1 同样虚拟 bridge/jsdom/global/act，启动真实 main 和 StrictMode | 逐层记录本 worker 的 factory、实际 loader、安全 route error 槽、局部 DOM alert | loader pending 则 Router/DOM 无 alert 不作错误页缺陷；loader reject 而无 error 槽定位路由发布；槽已发布而无 alert定位提交/边界，不能仅凭 transition 源码定根因 |

P3 的 createHashRouter 使用 actual 导出并转发原 args，原 route 对象、errorElement、原返回 Router 均保留。专用 loader 观察函数在既有 route 上转发原函数的 this/实参，原样返回原 Promise，旁路 then 只记录终态，不重构 Promise、不吞错、不另造 reject，不导航/revalidate/刷新。函数身份变化及旁路微任务可能轻微改变时序，是明确局限；不能把本轮终态倒写为旧 R4-R1 终态。

Router 只记录初始化/导航枚举、目标匹配/错误槽布尔、错误数量与安全 code 布尔，不序列化 Error/stack/路径/URL。DOM 只保存固定提示和页面状态布尔，不导出正文。console/VirtualConsole/未处理拒绝安全分类记录，不静默忽略。

## 时间、首次结果与收口

每项观察截止5秒，不延长；调度尾差单独记录，不把轮询尾差写成新预算。Vitest testTimeout10秒；单进程15秒包含加载/测试/退出，整个目标会话60秒。真实退出码、首次分开的stdout/stderr、worker PID与父PID关系、实际worker退出保存；无精确总进程数量阈值。收到首个非清洁目标退出/未知所有权即停止下一项，不洗掉结果；配置/语法仅目标前允许一次定向更正。

P3 finally unmount真实root，清理bridge订阅与观察订阅，显式dispose已保存真实Router，disconnect MutationObserver、close DOM、恢复原globals/console。观察层dispose是额外幂等收口，不能冒称已经动态记录产品effect每次dispose调用。CLI退出后核实已登记worker退出。仅自有temp允许清理，保留全部源码和首次结果。

未授权：产品/旧测试/依赖改动、旧节点或开发回归、Electron/EXE/sidecar/package/外部服务、用户点击、Git写操作。三个探针是技术诊断，不计为独立验收通过案例。
