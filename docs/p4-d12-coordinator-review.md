# P4-D12 总控审阅：B7 供应链与真实 Host 接线

审阅时间：2026-09-27，Asia/Shanghai
审阅角色：头脑风暴总控
结论：`P4-D12 complete`；接受为 `P4-IF-004` 与 `P4-B7-R1` 的正式输入

## 1. 审阅结论

总控接受 [P4-D12 技术裁定](phase-4-d12-b7-supply-chain-advice.md)的主要事实、推荐路线、22 条冻结建议和执行/验收边界。

P4-B7 不需要重做。现有 66 文件 source manifest 已复算为 66 matched、0 mismatch、0 missing；B7 的类型、执行方测试、Python 定向、Windows package、app.asar E2E 与 `Maris.exe` smoke 继续作为受阻交付证据保留。供应链 P0 与 main 未真实组合 Host 是 B7-R1 的两个有限续段，不取消已经完成的 Shell、IPC、主题、Tray、毛毛、模块注册和安全边界。

## 2. 两项总控裁定

### 2.1 Forge 8 alpha

**批准** Electron Forge `8.0.0-alpha.10` 只作为正式发布前 `P4-B7-R1` 的受控验证基线。

批准理由：

1. 当前 Forge 7.11.2 的真实 lock 包含 `tar@6.2.1`、`extract-zip@2.0.1` 和 `tmp@0.0.33`，full audit 为 1 critical、11 high、3 moderate、1 low；冻结门禁不允许忽略。
2. D12 的隔离候选 C 使用同 cohort Forge 8 alpha、Packager 20、Rebuild 4、node-gyp 12、tar 7.5.21 和内部 extractor，lockfile-only resolution 与 audit 均为 0。
3. Forge 7 直接 major override Packager 20 虽可解析，但旧 callback hook 与新 Promise options hook 合同不同；不能把“lock 变绿”当作 package 兼容。
4. 现阶段产品尚未发布正式大版本，B7-R1 的目的正是验证上游 prerelease 对当前项目的真实行为，风险可由 package/E2E/EXE 门禁和立即停止规则控制。

批准限制：

- alpha 只允许进入本地开发和独立测试，不得作为正式发行、公开安装包或用户数据生产运行基线。
- 所有 Forge 包必须精确使用 `8.0.0-alpha.10` 同 cohort，不混用 7.x/8.x，不自由试其他 alpha。
- 任一 clean install、peer、audit、compile、Forge hook、package、fuses、app.asar E2E、真实 EXE 或资源收口门禁失败，B7-R1 立即停止，不回退到 Forge 7 + Packager 20 override。
- Forge 8 发布 beta、rc 或 stable 后必须另立升级与复验；正式版本优先采用当时可用且通过验收的 stable。

### 2.2 Managed desktop core readiness

**批准**新增带 startup nonce 的 `GET /api/v1/desktop/readyz`，同时保持通用 `GET /readyz` 的 provider readiness 语义不变。

批准理由：

1. P4-B 不配置或启动 DeepSeek，但需要证明本地数据库、migration、模块 registry 和 desktop sidecar 已能承载非模型桌面能力。
2. 当前通用 `/readyz` 在 provider 缺失时正确返回 `agent_provider_unconfigured`；若直接用它作为 P4-B online 条件，managed desktop 永远不能上线。
3. 把核心 Host readiness 和模型 provider readiness 分开，比注入假 provider、降低 `/readyz` 标准或把 `/healthz` 冒充 ready 更准确。

新端点边界：

- 只在 managed desktop profile 下成功；必须提供本次启动的 `X-Maris-Startup-Nonce`。
- 只验证 database connection、当前 Alembic head、非空 module registry 和 desktop gate；不验证或暗示模型 provider 可用。
- 缺 nonce、错 nonce、数据库不可用、migration 落后、registry 空或非 managed 调用均 fail closed，返回稳定且脱敏的错误。
- 通用 `/readyz` 继续验证完整 Host 和 provider；普通 `/healthz` 继续只表示进程存活。
- renderer 不取得 nonce、端口、PID、路径、token 或原始异常。

## 3. D12 证据核对

| 项目 | 总控结果 |
| --- | --- |
| D12 文档 | 728 行，SHA-256 `c88e5a0e06f56acb3347fbe0b19182e25bd27ee3b115b2a6764d86f8c9d64ed9` |
| 技术顾问状态 | `review / finished`，SHA-256 `b5db972f3040159a508428c498a0f6327eb3540d0027cfc689336ba1b11151e7` |
| 原始公告 | 16 项完整列出；12 tar、2 extract-zip、2 tmp |
| 当前 full audit | 1 critical、11 high、3 moderate、1 low |
| 候选 A | Forge 7 + Packager 20 override；audit 0，但 hook 合同不兼容，拒绝实施 |
| 候选 B | Forge 7 + tar/tmp 修复；仍有 2 high extract-zip，不能通过 |
| 候选 C | Forge 8 alpha 同 cohort；隔离解析与 audit 0，接受进入真实项目验证 |
| 临时实验 | 只写 `.codex-tmp/p4-d12`，完成后 `Test-Path=False` |
| 本地链接 | 技术顾问记录 36 个本地目标存在；总控抽查关键代码、冻结和交接链接有效 |
| Git/产品 | D12 未修改产品、依赖、锁文件、测试或 Git 状态 |

隔离候选只证明依赖解析和 advisory 匹配，不证明 Node 24 下的安装、Forge 8 hooks、Vite、fuses、Windows package 或真实 Host 组合。上述内容全部保留为 B7-R1 的实际门禁，不能在总控审阅阶段预先宣称通过。

## 4. 冻结和执行顺序

本审阅同时发布：

1. [P4-IF-004](phase-4-interface-freeze-004.md)：冻结依赖候选、退出条件、desktop core readiness、composition root、Supervisor、owner/token、IPC 与门禁。
2. [P4-B7-R1 执行任务卡](coordination/prompts/p4-b7-r1-windows-shell-supply-chain-runtime-executor.md)：由既有执行智能体在一个有限续段中实施。
3. [P4-B7-R1 固定输入快照](coordination/snapshots/p4-b7-r1-start.sha256)：绑定现有 P4-A、B7、D12、冻结与任务卡输入。

执行顺序固定为：

1. 复算固定输入；
2. 恢复精确 Node/pnpm 的项目本地工具；
3. 只更新候选依赖图并先通过 full/prod audit；
4. 通过静态和现有单元门禁；
5. 完成 desktop core readiness 与 Electron main composition root；
6. 执行 Python/Uvicorn managed smoke；
7. 执行 Windows package、app.asar E2E 与 `Maris.exe` smoke；
8. 生成终点快照并停在 `review / finished`。

依赖门禁在真实项目中失败时，执行智能体必须停止，不进入 Host 接线。P4-C12 在 B7-R1 形成稳定终点快照前继续 `not_started`。

## 5. Git 与发布状态

D12 是已接受的技术设计，但 B7 产品仍未通过执行续段和独立验收。本次不把受阻的 B7 产品实现提交为完成单元，也不推送远端。Forge 8 alpha 产生的包即使通过执行方和独立测试，也只是发布前候选，不构成首个正式大版本。
