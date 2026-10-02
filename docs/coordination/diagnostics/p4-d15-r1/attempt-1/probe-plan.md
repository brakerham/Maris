# D15-R1 attempt-1 唯一main前观察修正冻结

控制版本仍2026-10-03T01:07:00+08:00。attempt-0完整源码/首次journal/双流/真实exit/原生共享证明/退出后门禁/输入核对已保存在原目录，delivery逐文件摘要冻结。初次724ms/exit-1、两条同步阶段、main0；首次controller异常类型因未捕获保持unknown。退出后journal的PID/parentPID证明worker39044父38256=自有root，两者已退出；463固定输入、旧D15其余30交付、389外部源码和140产物均一致。

新原生虚拟文件共享证明：活动writer句柄存在时ReadAllText出现IOException/HResult-2147024864/Win32=32；用FileShare.ReadWrite读取成功。这是已复验的controller观测接线问题，不把新异常冒充首次异常，不认定Vitest/Router或产品缺陷。

唯一修改：新controller实时读取用FileStream(Read, ShareReadWrite)+StreamReader，只解析完整newline；catch记录固定调用码/kind/HResult并保留unknown，不保存message/stack。增加首次门禁/不可变交付核对；expected root、attempt号、cache root分别指向新attempt-1。setup.mjs和bootstrap.test.tsx与attempt-0逐字同摘要，不改变原生journal/Router工厂/main/act语义。

阶段计划与原attempt-0一致：setup→hoisted→body/virtual bridge→Router preflight/factory/importOriginal terminal→act/main Promise terminal→act terminal→立即收口。真实default loader/入口/StrictMode及原虚拟故障不变；无导航/revalidate/DOM完整验收/恢复。未到达保持unknown。

这是第二个、最后一个隔离Vitest CLI/worker，修正预算1/1。实际main累计最多1；新CLI15秒含500ms采集预留、test10秒；累计目标执行小于60秒。源码整理与用户继续前后的离线墙钟间隔另列，不作为额外等待目标时间。main一旦请求或记录unknown、观察修正再次失败、所有权unknown、产品异常或无法收口均停止，不再attempt-2/新任务循环。
