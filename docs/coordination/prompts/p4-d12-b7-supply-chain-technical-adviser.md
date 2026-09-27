# P4-D12 技术顾问任务卡：B7 供应链处置与桌面真实接线续段方案

你是技术顾问，唯一负责 `P4-D12：B7 供应链处置与桌面真实接线续段方案`。

## 开始前必须按顺序读取

1. `AGENTS.md`
2. `README.md`
3. `docs/project-coordination.md`
4. `docs/coordination/README.md`
5. `docs/coordination/control.md`
6. `docs/coordination/agents/technical-adviser.md`
7. `docs/phase-4-d11-windows-shell-technical-advice.md`
8. `docs/p4-d11-coordinator-review.md`
9. `docs/phase-4-interface-freeze-003.md`
10. `docs/coordination/prompts/p4-b7-windows-shell-executor.md`
11. `docs/b7-windows-shell-running.md`
12. `apps/desktop/b7-source.sha256`
13. 根目录与 `apps/desktop/` 下的 `package.json`、`pnpm-lock.yaml`、`pnpm-workspace.yaml`、`.npmrc`、Forge/Vite 配置
14. Electron main、preload、renderer，以及 `LocalOwnerSession`、`BackendSupervisor`、`HostClient` 的实际实现和执行方测试

开始前和准备执行任何网络访问、依赖解析实验或用户动作前，再次读取最新 `docs/coordination/control.md`。若其中的任务、唯一负责人或停止指令与本任务卡冲突，以最新 control 为准，停止旧动作并报告。

## 背景与已确认事实

`P4-B7` 已完成大部分 Windows Shell 实现和执行方自测，但按 P0 门禁停在 `blocked / finished`，不能进入 `review`，也不能启动 P4-C12。

本次阻塞不是重新做桌面端。66 个 B7 源文件清单已经复算为 `matched=66`、`mismatch=0`、`missing=0`；打包、app.asar E2E、最终 `Maris.exe` smoke、16 项 Vitest、15 项 Python 定向测试均已有执行方证据。现有实现和测试必须作为续段输入保留。

当前存在两个独立问题：

1. `pnpm audit --audit-level high` 返回退出码 1，共 16 项：1 critical、11 high、3 moderate、1 low。主要路径位于冻结的 Electron Forge 7.11.2 构建链：
   - `@electron/rebuild`、Electron node-gyp 及其传递依赖中的旧 `tar`；
   - `@electron/packager@18.4.4` 使用的 `extract-zip@2.0.1`。
2. `LocalOwnerSession`、`BackendSupervisor`、`HostClient` 已实现并有单元测试，但 Electron main 尚未把它们组合成真实 managed Python Host 正常链路。当前实现安全地 fail closed，`modules:list` 返回空交集，UI 显示模块未连接。

已核实的上游事实包括：

- GitHub Advisory `GHSA-jmr9-qjv8-65gv` 和 `GHSA-7pqw-9j4j-h8q3` 均把 `extract-zip <= 2.0.1` 标为受影响，patched versions 为 None。
- Electron Forge issue `#4228` 记录 Forge 7.x 的 `@electron/rebuild@3`/`tar@6.2.1` 链；Forge 8 的 prerelease 线已转向 rebuild 4/tar 7。
- Electron Forge issue `#4082` 明确 Forge 8 仍按 alpha/beta/rc 推进；当前不能把 alpha 自动视作适合一般使用的稳定版本。
- `@electron/packager` 已有 20.x 稳定版本，当前仓库上游实现改用 `@electron-internal/extract-zip`；是否可以在 Forge 7.11.2 下安全覆盖或独立调用，必须以实际 API、peer/engine、打包行为和测试证据判断，不能只凭版本号推断。

这些事实只是调查起点，不等于已经选定方案。你必须核对当前锁文件和所有实际 advisory 路径。

## 目标

交付一份可供总控形成 `P4-IF-004` 和 `P4-B7-R1` 任务卡的窄范围技术方案，同时完成用户的工程学习讲解：

1. 完整解释 16 项 audit 的来源、可达性、严重度、修复状态和实际威胁面；
2. 推荐一个精确、可复现、维护成本可接受的依赖图处置方案；
3. 明确哪些冻结版本必须改变、哪些继续保持；
4. 设计 B7 续段如何完成 Electron main 到本地 Host 的真实组合；
5. 给出执行方自测、供应链门禁、Windows 打包/E2E、失败停止条件和独立验收入口；
6. 不修改产品、依赖、锁文件或执行方测试，不替执行智能体实施，也不替测试智能体作独立结论。

## 唯一负责人和文件边界

- 你是本任务唯一负责人。
- 允许修改：
  - `docs/phase-4-d12-b7-supply-chain-advice.md`
  - `docs/coordination/agents/technical-adviser.md`
- 其余项目文件全部只读，包括产品代码、测试、独立矩阵、依赖文件、锁文件、冻结文件、control、overview、snapshot、其他角色日志和 Git 状态。
- 不得修改 `package.json`、`pnpm-lock.yaml`、`pnpm-workspace.yaml`、`.npmrc`、Forge/Vite 配置或 `apps/desktop/**` 实现。
- 不得安装或更新项目依赖，不得创建/覆盖项目 `node_modules`、pnpm store、构建产物或 OpenAPI 生成物。
- 如确有必要验证“能否解析出某个候选依赖图”，只允许在可删除的 `.codex-tmp/p4-d12/**` 中做与项目隔离的最小 lockfile-only/只读解析实验；开始前必须重新读取 control，并在报告中记录命令、网络来源、结果和清理状态。不得把实验结果直接写回项目依赖文件。
- 不得启动 Electron、FastAPI、Uvicorn、Docker、PostgreSQL、OpenClaw、微信、DeepSeek 或真实 provider。
- 不得运行或修改 `tests/independent/**`，不得启动 P4-C12。
- 不得执行任何 Git 写操作。允许只读查看 `git status`、`git diff`、`git log` 和文件摘要。

## 必须完成的分析与裁定

### 1. 完整 audit 清单与依赖路径

逐项列出 16 个 advisory，至少包含：

- GHSA/CVE、包名、当前版本、严重度；
- 从项目直接依赖到受影响包的完整依赖路径；
- 属于 packaged runtime、开发服务器、测试、下载、重建、打包或发布中的哪一段；
- 是否进入最终 `app.asar` 或 `Maris.exe` 运行时；
- 攻击前提、受影响输入是否来自网络/第三方归档/开发者机器；
- 官方 patched version、无修复版本或替代包状态；
- 当前可接受的处置类型：升级、override、替代、隔离、暂缓，或必须拒绝。

不得只讨论 `tar` 和 `extract-zip` 两个包；必须解释剩余 advisory 为什么会随主路径一起消失，或者为什么仍然存在。

### 2. 比较五类候选方案

至少比较以下路线，并给出明确的推荐顺序：

1. 保持 Forge 7.11.2，对 `tar` 和 `@electron/packager` 等传递依赖做精确 pnpm override；
2. 保持 Forge 7.11.2，但把新版 Packager 作为独立可控打包步骤，Forge 仅负责其余开发流程；
3. 升级 Forge 8 prerelease；
4. 对旧 `extract-zip` 或上游调用方做 vendored patch/`pnpm patch`；
5. 换用另一套 Windows 打包工具链。

每个方案说明：

- 能否消除全部 critical/high；
- semver/API/ESM/Node/Forge plugin 兼容性；
- 对 `package`、最终 EXE、asar、native module rebuild、缓存和 Windows 路径的影响；
- 长期维护责任；
- 对用户学习价值与复杂度的影响；
- 需要哪些实验才能证明，而不是依赖推测。

不得把“仅开发依赖”自动当作安全通过，也不得通过降低 audit 等级、忽略 GHSA、增加无期限 allowlist 或删除门禁来获得绿色结果。若建议临时例外，必须给出具体到 advisory 的威胁模型、到期条件、补偿控制和退出计划；默认优先实际消除 critical/high。

### 3. `tar` 兼容性

核对 `tar@6 -> tar@7.5.21+` override 是否与当前 `@electron/rebuild@3`、Electron node-gyp、`cacache`/`make-fetch-happen` 调用方式兼容。必须区分：

- lockfile 能解析；
- 单元/API 表面兼容；
- 真实 Electron rebuild/package 行为通过。

如果不能可靠证明直接 override，说明是否必须升级 rebuild、node-gyp 或改用另一条打包路径。

### 4. Packager 与 `extract-zip` 处置

核对 `@electron/packager@20.3.0` 或当前稳定 20.x：

- Node engine、模块格式、API 和 Forge 7 调用兼容性；
- Forge 7 对 Packager 18 的版本约束和内部调用假设；
- 新 Packager 使用 `@electron-internal/extract-zip` 的实际路径及其安全含义；
- pnpm override 到 major 20 是否可能工作，以及必须用哪些测试证明；
- 若不宜 major override，能否由项目脚本显式调用 Packager 20 并保留 Forge dev/Vite 流程。

### 5. 推荐的精确依赖图

给出推荐方案的精确版本、修改位置和预期锁文件变化，包括：

- 根/desktop `package.json`；
- `pnpm-workspace.yaml` overrides；
- `.npmrc`；
- Forge package script 或独立 Packager script；
- 是否保留 `node-linker=hoisted`、block exotic subdeps 和当前 node-gyp 固定方式；
- 哪些包从依赖树中必须完全消失。

把建议组织成总控可直接写入 `P4-IF-004-F01...` 的冻结条目。若证据不足以冻结单一方案，必须明确列出最小验证实验、通过标准和失败后的备选顺序，而不是让执行智能体自由选择。

### 6. Electron main 的真实 Host 组合

基于当前实际代码，给出最小续段数据流和组合根：

1. single-instance/app ready；
2. 读取设备设置与启动模式；
3. `BackendSupervisor` 启动或连接 Python Host；
4. `/healthz` 与带 nonce 的 `/readyz`；
5. `LocalOwnerSession` bootstrap/refresh/login fallback；
6. 创建 main-only `HostClient`；
7. 拉取 Host `/modules`；
8. 与 compiled desktop registry 做交集；
9. 通过窄 IPC 返回 renderer；
10. 后端离线、恢复、会话失效和应用退出时的状态与资源收口。

必须指出实际文件、工厂或函数应承担的职责，避免把业务逻辑塞进 `main.ts`。保持 renderer 无 token、无任意网络、无 Node/文件系统能力。不得提前实现 P4-C 财务驾驶舱、真实账本写入或 P4-D 财富管理。

### 7. B7-R1 文件边界和实施顺序

给出一个执行任务内的有限步骤，建议顺序至少包括：

1. 先做隔离依赖解析和 audit 验证；
2. 冻结的新依赖图能消除 critical/high 后再更新项目依赖；
3. 重跑 type/lint/unit/component/IPC；
4. 完成真实 Host 组合；
5. 运行 Python 定向回归和自有 Uvicorn smoke；
6. Forge/Packager Windows package；
7. 最终 package 的 app.asar E2E 与真实 `Maris.exe` smoke；
8. 终点 source manifest 和完整交接。

明确可修改文件类别、禁止修改 `tests/independent/**`、禁止修改 P4 矩阵/报告和禁止扩展业务范围。

### 8. 门禁与停止条件

至少冻结：

- `pnpm audit --audit-level high` 的通过定义；
- 是否还要单独检查 production-only 与 full dependency tree；
- lockfile-only 安装、frozen lockfile、peer dependency、deprecated transitive 的处理；
- 软件物料清单或依赖图证据；
- TypeScript、lint、Vitest、Python、OpenAPI drift、package、E2E、EXE smoke；
- packaged runtime 中不得包含开发秘密、token、个人数据或任意更新/下载入口；
- 发现新的 critical/high、major override 行为不兼容、打包失败、真实 Host 不能上线、owned process 泄漏时的立即停止条件。

说明哪些是执行方自测，哪些留给 P4-C12 独立验证。

### 9. 用户学习讲解

用当前 B7 实例讲清楚：

- 直接依赖、传递依赖、lockfile 和 override；
- 为什么“漏洞在构建工具里”仍需要评估；
- 为什么 audit 结果不能直接等同于产品一定可被攻击；
- 为什么安全门禁失败时先停下，比盲目 `audit fix --force` 更正确；
- dependency graph、攻击面、可达性、补偿控制、风险接受和退出计划；
- main/preload/renderer/Host 的组合根与依赖注入。

每节给出实际项目文件位置、一个小练习和一个检查题。教学内容写在同一 D12 文档中，不另建 PDF。

## 官方来源最低要求

优先引用官方/原始来源，至少核对并链接：

- GitHub Advisory Database 的两个 `extract-zip` GHSA；
- Electron Forge `#4228` 和 Forge 8 `#4082`；
- Electron Forge、Packager、Rebuild、Electron security 官方仓库或文档；
- npm/pnpm 官方的 override、audit 与 lockfile 文档。

对来源日期、版本和“事实/推断/建议”做区分。不得只引用二手博客作为关键结论。

## 交付物

1. `docs/phase-4-d12-b7-supply-chain-advice.md`
2. 更新 `docs/coordination/agents/technical-adviser.md`

D12 文档至少包含：

- 执行摘要与推荐方案；
- 16 项 advisory 表；
- 当前依赖图；
- 五类方案比较；
- `tar` 与 Packager 20 兼容分析；
- 推荐精确依赖图；
- `P4-IF-004` 建议冻结项；
- main 到 Host 的真实组合数据流与 Mermaid 图；
- B7-R1 文件边界、实施顺序和停止条件；
- 执行方与独立验收分层；
- 用户教学章节、练习和检查题；
- 尚未验证的事实、风险和复评触发条件；
- 所有修改文件的 SHA-256。

## 完成与停止规则

- 接单、重要调查结果、阻塞和完成都要更新技术顾问自己的状态文件及 `Current execution snapshot`。
- 若网络或工具执行连续两个检查点没有进展，停止重试，保留现有证据并说明卡点；不要无限等待。
- 如果发现推荐方案需要改变 Electron 主版本、放弃 Forge、修改 Python Host 公开合同或扩大 P4-C/P4-D 业务范围，停止对应实施建议并将该范围标为需要总控与用户裁定。
- 只有两份允许文件完成、分析覆盖全部 16 项、给出明确首选和备选、所有本地链接有效且摘要可复算时，才提交 `review / finished`。
- `review` 不等于项目验收或允许 Git 提交。最终是否形成 P4-IF-004、是否派发 B7-R1、何时启动 C12，均由头脑风暴总控决定。
- 完成后停止修改，不自动启动执行智能体、测试智能体、P4-B7-R1 或 P4-C12。
