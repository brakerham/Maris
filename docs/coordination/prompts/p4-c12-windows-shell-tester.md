# P4-C12：Windows Shell 独立验收

## 唯一负责人和目标

你是用户启动的既有测试智能体，唯一负责 P4-C12。LOCALZIP 的 package 和最终 EXE 已取得真实通过证据，总控已核对；这是独立验收输入，不是独立结论。

按现有矩阵的 24 个 `P4B-*` ID 独立取证，验证 Windows Shell、安全边界、Host 生命周期、模块贡献、outbox、设置和毛毛。不要重新设计矩阵、实现产品或开始 P4-C 高保真界面。完成后停在 `review / finished`；产品 P0/P1 或明确环境阻塞时停在 `blocked / finished`。最终 complete 只由总控决定。

## 必读、接单和输入冻结

按 AGENTS 先读 README、project-coordination、coordination/README、最新 control、tester 状态和本任务卡，然后读取：

- `docs/p4-b7-r1-e5-localzip-coordinator-review.md`
- `docs/b7-r1-e5-localzip-running.md`
- `docs/phase-4-interface-freeze-003.md`
- `docs/phase-4-interface-freeze-004.md`
- `docs/phase-4-interface-freeze-005.md`
- `docs/phase-4-local-owner-scope-decision.md`
- `docs/testing/phase-4-modular-agent-host-test-matrix.md` 的 P4-B 段
- `docs/coordination/snapshots/p4-c12-windows-shell-start.sha256`

开始前复算固定清单，报告 entries/matched/mismatch/missing 和清单普通 SHA-256；Git staged paths 必须为 0。记录接单、实际角色和执行快照，新的任务覆盖 tester 中已完成 C11-R2 的旧当前任务。

冻结清单使用 UTF-8 无 BOM、LF、排序 `path<TAB>sha256<LF>`，排除自身。结束时除矩阵与 tester 状态两个授权路径可变化外，清单内其他路径必须精确不变；新增交付单独列出。不得更新执行方 source manifest 来掩盖输入漂移。

IF-004 覆盖 IF-003 的供应链与 desktop core readiness 条款；IF-005 及已接受返修覆盖对应 staging/诊断条款。Profile 使用 Python canonical `daily_finance.assistant@1`，不创建 alias。通用 `/readyz` 未配置 provider 时继续 fail-closed，不以此判定 desktop core 不在线。

## 文件所有权

只允许写：

1. 新目录 `tests/independent/desktop/**`，包含独立测试、配置和有界 runner。不得修改该目录以外既有独立测试。
2. `docs/testing/phase-4-c12-windows-shell-report.md`。
3. `docs/testing/phase-4-c12-manual-checklist.md`。
4. `docs/testing/phase-4-modular-agent-host-test-matrix.md` 的 P4-B 状态与必要证据备注；保留 120 个原 ID 和原预期，P4-A 64 passed、P4-C/D 32 not_run 不变。
5. `docs/coordination/agents/tester.md`。

禁止写产品、执行方测试、依赖、lock、Forge、package/staging、migration、Compose、生成物、冻结文档、control/overview/snapshot、其他角色文件和 Git 状态。`.claude/`、仓库 `.pnpm-store/` 不触碰。不启动执行智能体、技术顾问或任何新聊天。

## 可用环境与真实产物

已验证清洁环境根：

`C:\MarisE5Final\E5-PKG-FINAL-20260929-1732`

只读复用它的 task-local Node 24.21.0、pnpm 12.7.0、普通 node_modules、Electron dist、固定 lock，以及已经完成的 package。不重新安装、下载、联网 audit、build 或 package。E4/E5-R1/E5-R2 的污染依赖只读，不使用、不恢复、不删除。

受验产品：

`C:\MarisE5Final\E5-PKG-FINAL-20260929-1732\workspace\apps\desktop\out\Maris-win32-x64\Maris.exe`

| 文件 | SHA-256 |
| --- | --- |
| EXE | `f5cf7ad3b4d89a02cca925152ec8d7b5554ccba6ebff025bf04eb24195405641` |
| `resources/app.asar` | `bcdf6f889a5be95d7270fb249db8eff45b1421a5fdd7879d2342cb333d7f1274` |
| workspace lock | `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |

旧 `localzip-resume-1` 及其 profile、数据库、owner/session、115 项 evidence 全部只读；旧记录只用于输入核对与执行方兼容证据，不能算你的独立测试。

独立动态 evidence/profile/虚拟数据库在全新 `C:\MarisC12\C12-<时间戳>` 下建立，路径需先解析并确认在该专属根内；受控外部目录写入按工具审批处理。若审批或环境阻止创建，停在环境阻塞，不换用真实 AppData profile。只测试虚拟身份与财务数据，不读取个人数据或真实 API key。

复用已经验证的项目 Python；不安装新 Python、不捆绑 runtime。受验产物不改内容/ACL/ADS/fuses，profile/outbox/设置只写新测试根。不通过修改永久 PATH、系统 pnpm、TUN、代理、安全软件或 Docker 解决问题。

## 验收顺序与证据层级

1. 快照/产物核对与静态审查。
2. 独立公开行为测试：registry/IPC/HostClient/session/supervisor/outbox/settings/生命周期/ZIP 与 staging。使用测试方自有断言，不把执行方测试复制改名。复用既有 Vitest 与 Node loader；独立配置指向自身文件且使用测试专属临时目录，不修改产品配置。
3. 最终 EXE 的必要真实 Windows 场景。运行前在 tester 日志列出场景、目的、预期、最大时长、隔离 profile 与清理负责人；先从安全/Host/模块/recover 主链路开始，再执行必要生命周期与设置场景。
4. 生成人工检查清单与逐项报告；尚未取得的实际设备/用户证据保留 not_run 或 blocked。

主链路沿用有效启动方式：固定 Node `spawn(Maris.exe, ..., {shell:false})`；Playwright 只使用 loopback `connectOverCDP()`，不使用 `_electron.launch()`、app.asar loader、PID promotion 或产品 inspect fuse。先以实际 ChildProcess、固定 executable、创建时间和专属 profile 确认 ownership；不要以精确进程数量判断安全（合法 conhost/GPU/utility 进程不等于异常）。

每个真实场景硬上限 120 秒；本任务至多 8 次有计划的产品启动，单实例场景内第二次启动也计数。测试动作和 run ID 分开记录，按计划覆盖后不重复成功场景。120 秒内未收口时只清理已证实属于本任务的树；不得广泛按进程名杀进程。不要把现有 30 秒 E2E 自动退出误认为用户的普通关闭策略；需要生命周期观察的场景可使用源码已支持的有界 E2E 时限，最大仍为 120 秒，并明确记录。

开发用测试参数须与生产合同区分；E2E 开关抑制的开机启动等系统行为不能报为实际 OS 通过。生产 inspect fuse、sandbox/contextIsolation/Node isolation 和静态安全合同不放宽。

独立报告对 24 个案例逐项给出：完整原预期、输入/步骤、测试节点或 evidence、实测结果、证据层级、状态、限制。一个 ID 包含多个子条件时，不以其中一项代替整项 passed。单元模拟可证明程序逻辑，不能替代明确要求的 Windows/多屏/注销/启动项现场；静态检查同理。

## 重点场景及边界

- SEC：CSP、导航/窗口 allowlist、窄 preload、sender/origin/参数拒绝、秘密隔离、main-only HTTP、nonce/Bearer 区分、恶意文本与错误脱敏。测试中的公开 canary 不要把真实秘密写入报告。
- SUP：真实 managed Host 首次与恢复状态、nonce/readiness、single-flight、限次恢复、owned stop；external_dev 只用自建虚拟后端或注入 adapter，不能取得真实手工服务停止权。outbox 的相同 client_event_id、重放/重启与内容变更边界用假 adapter/虚拟数据取证，不调用模型或记真实账。
- UI：Host 与贡献交集、canonical Profile、错误版本/冲突、lazy route 错误隔离、生成物漂移。第二模块只用测试方虚拟 contribution，真实 wealth 模块属于 P4-D；不得为通过 CMP/扩展性创建产品模块。
- CMP：只有一个毛毛、模块主形态与运行子状态分开、close policy、首次提示、Tray 恢复、设备设置和主题。P4-B 的占位毛毛/财务页是受验 Shell 范围，不声称高保真驾驶舱已实现。
- 额外覆盖本轮本地 ZIP 显式无效值/错误长度/摘要拒绝、常规入口兼容、staging 原子性和禁止文件；这些证据作为附加构建安全检查，不新增或挤占原 24 ID。

不得注销/重启 Windows、强关用户真实程序、修改实际开机启动项、切换显示器配置或要求用户立即操作。SUP-05 与 CMP-04/05/06 等需要真实设备条件的未覆盖子项写入人工清单，先交回总控；用户后续完成单一步骤后再补证，不伪装全绿。

不运行 Docker/PostgreSQL、OpenClaw/微信、DeepSeek 或真实 provider。不重复微信 V002、扫码、旧 P0 回环超时、P0～P3/Host 全量回归。只复跑本次相关执行方测试并单独统计；LOCALZIP 的 30 项可一次兼容复跑，其他只在输入变化或明确缺陷关联时增加。

## 防止验收工具循环

没有目标启动、没有领域写入的语法/参数/字段映射错误归类为 harness/preflight，不冒充产品 P0。先对 driver 用静态检查和小型离线 fixture 验证参数/JSON mapping/清理；不要新增完整 Job Object synthetic 系统或精确两个进程预算。

目标启动前的无副作用编排错误允许在本任务内一次定向修正，保留首次错误后再验证；无需虚构新返修任务。目标启动后的产品断言失败原样保留，不重启覆盖。若只是证据读取/标签错误，且进程与副作用已安全收口，可只读补充核对并保留原始结果；不能因此重新启动产品。

未知 ownership、失控 Windows 异常弹窗、真实秘密泄露、产品 P0/P1、不能安全收口或同一问题连续两个检查点无新证据：停止扩大测试，保存已获得结果与未执行列表，安全清理后交回总控。不要无限重试、随意增加预算或擅自修产品。

## 日志与最终交付

接单、环境核对、独立用例里程碑、动态开始/结束、阻塞和完成均更新 tester 日志。超过五分钟操作前记录下一检查点；可控制时至少每十分钟心跳，报告实际步骤和 session 引用，不写猜测百分比。

报告至少包含：24 个原 ID 逐项映射、独立/执行方/人工三类统计、首次失败与根因证据、所有 not_run/blocked、snapshot 起终点、授权文件边界、产物不变性、启动次数、进程/端口/窗口收口、隐私检查、warning 和下一步建议。

结束时只清理自己新建的临时工作目录且先核对绝对路径，保留可复算证据与脱敏日志；旧 LOCALZIP 环境/证据不删除。不把 profile/session/db 原件提交到仓库。未测的真实 Tray、注销/多屏/开机启动不能由退出后 PID=0 推导 passed。

提交 `review / finished` 或 `blocked / finished` 后停止。不要宣布 P4-B complete、创建 C12-R1、派发 P4-C、修改控制面或运行 Git 写操作。
