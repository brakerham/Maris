# R10：开发来源校验反例与最小返修裁定

2026-11-01，Asia/Shanghai，头脑风暴总控。输入为 [R10 独立报告](testing/phase-4-c12-r10-settings-windows-report.md)、[首次结果](../tests/independent/desktop/evidence/r10-settings/independent/result.json)和[逐条比较](../tests/independent/desktop/evidence/r10-settings/independent/journal.jsonl)。总控只读核对，没有重跑测试、启动产品、辅助程序或服务。

## 接受的事实和定级

接受 `P4-C12-R10-IPC-ORIGIN-001` 为 **P1 开发模式 IPC 来源校验缺陷**。受信配置 `http://127.0.0.1:5173` 下，真实 main 注册的 `settings:get-snapshot@1` handler 先接受同源正对照，然后错误接受 `http://127.0.0.1:51730/index.html`。sender、mainFrame 和零参数条件保持，校验函数没有被 mock。首次 `R10-I06.DIFFERENT_PORT_REJECTED` 的 expected 为 `ipc_origin_rejected`、actual 为 `null`，明确表示没有抛出拒绝异常，不是丢失观察值。

[security.ts](../apps/desktop/electron/main/security.ts)第25行附近的 `isTrustedRenderer` 使用 `url.startsWith(developmentOrigin)`；[validateIpc](../apps/desktop/electron/main/ipc-contract.ts)在参数解析前调用它；[实际 main](../apps/desktop/electron/main/index.ts)将 MAIN_WINDOW/COMPANION_WINDOW 各自开发地址传给共享校验。这条源码链与首次结果一致，不需要靠延长等待、重启或新增诊断框架定位。

影响范围严格限定为上述开发来源配置下的信任判定；共享校验函数是修复位置，但本次实际反例来自设置 getter。没有证明打包程序攻击可达、实际导航绕过、任意接口利用或真实数据泄露。不能把它归为R8设置修复新引入的回归，也不能据此认定新包的设置恢复再次失败。矩阵SEC-04原风险列P0保持，具体缺陷P1与矩阵风险列分开。

## 独立证据审计

| 核对 | 总控结果 |
| --- | --- |
| R10起点1381 | 修改总控文档前仅tester、主报告、人工清单、矩阵4项授权变化，无缺失 |
| 50项交付 | 全部匹配；清单SHA-256 `f128dac56c7743a9d2928532e7cfe840a49a11468cb284911875b7fa0a734a21` |
| 8份正式来源 | 全部匹配；清单SHA-256 `7b1a207b0356579c76f1d3f62f7fbc64cee18eec5e73ef5a081ae215e879d5af` |
| 29份首次材料 | 全部匹配；清单SHA-256 `2e3e373e50113dbb7182e32aa65a73abbe13a1b892008b2ecaf4f4747735e2da` |
| 正式结果 | 38计划节点：5 passed、1 failed、32 not_run；40对比较，39通过、1失败，唯一ID与配对完整 |
| 报告与矩阵 | 两旧文档仅追加；120ID、12列、原预期/A/C/D不变，仅SEC-04 blocked→failed及B备注追加 |

总控另亲自复算固定构建1365、产物140、资源67及EXE/asar/lock/closeout/H1结果摘要，全部匹配。14工具入口、旧首次及四份虚拟资料的本轮测试方审计由上述交付绑定；完整历史依赖不重复遍历。本轮没有自行解密profile或重新枚举测试进程。测试root/worker正常返回exit1、无超时/强制，只证明首次失败后测试进程结束，不把它写成产品正常退出。

17项目标前记录器检查单列，不计独立产品通过。原I01～I05的有限通过保留；I07和全部31项页面水合尚未执行。两文件48项兼容、原W2四条首样及后续Windows均未运行。产品/helper本轮新增0/0，Tester系列仍2/8、3/6。SETTINGS-001、LAZY-001和P4-B未关闭，B保持1 passed、3 failed、18 blocked、2 not_run。

## 返修合同与验证安排

发布 [P4-B7-R9-IPC-ORIGIN](coordination/prompts/p4-b7-r9-ipc-origin-executor.md)及[新起点](coordination/snapshots/p4-b7-r9-ipc-origin-start.sha256)。唯一负责人为既有执行智能体，Tester停止；不另立技术顾问诊断。临时只读子审阅因额度错误终止，没有形成结论；本裁定由总控亲自核对实际调用链和原断言后作出。

1. 产品变更仅限 `security.ts` 开发来源分支。用URL解析和精确origin比较替代字符串前缀，限定HTTP/HTTPS，非法或含credentials的开发配置/请求拒绝；不让opaque/null origin相等或blob嵌套来源放行。路径/query/hash不属于origin；标准主机大小写、有效端口按URL规范解析，不能自行做DNS/localhost别名合并。
2. 保持sender/mainFrame、参数schema、错误码及main/preload接线，生产file/maris分支原有行为不在本次改写范围。不得给renderer新增能力或为测试放宽closePolicy。没有独立证据的生产来源问题不预先宣布关闭；发现新实质问题须报告。
3. 执行方先保留精确开发反例红灯，再修共享函数。覆盖相邻来源边界和真实main getter、毛毛handler的各自来源；对变更涉及的生产分支保留正反对照，错误来源拒绝时无handler副作用。开发可正常定向调试，不把预期红灯当正式验收失败，也不修改独立源码。
4. 本次不重复完整217项或S1/S2。仅security/ipc/settings-snapshot及settings-hydration必要兼容、类型/lint；通过后最多一次新package和既有静态门禁，证明修复进入新产物。**EXE/helper/开发服务器均0次**。新包动态能力保持not_run，交后续Tester使用；旧R8包只读保留，不能拿旧包替代修复产物。

一份新包是为了给后续独立续验提供与修复源码一致的输入，不是本轮再次证明设置恢复或正式发布。包装器、锁文件、依赖和已验证本地Electron ZIP保持不变，不新建Windows观察驱动。新包实际EXE摘要可能与旧包相同，不能只凭EXE摘要判断JS修复入包；必须核对app.asar及main bundle的具体来源。

执行方交review后，总控另行冻结独立IPC失败节点及必要邻接复验、剩余未运行设置节点和Windows续验，不重置旧首次或Tester剩余额度。本轮只保存明确未完成的本地检查点，不推送。真正P4-C前端的效果图和模型分工提醒保持。
