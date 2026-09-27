# P4-D12：B7 供应链处置与桌面真实 Host 接线技术裁定

- 任务：P4-D12
- 角色：技术顾问
- 日期：2026-09-27，Asia/Shanghai
- 输入控制版本：2026-09-27T18:23:00+08:00
- 输入实现：P4-B7 保留的 66 文件工作区快照
- 输入 source manifest SHA-256：de1f80c566faf165d7869bb4641477b3743bea80b72c65f137079e0f3993352a
- 当前项目 lockfile SHA-256：426249eaff7a8e60b5ad68d0ab9532adf29322559de4423fe500012260780441
- 状态：实现前技术建议；不代表依赖已经修复、main 已经接线或 P4-B 已验收

本文只裁定后续路线。它没有修改产品代码、依赖、锁文件、测试、矩阵、接口冻结或 Git 状态，也没有启动 Electron、FastAPI、Docker、PostgreSQL、DeepSeek、OpenClaw 或微信。

## 1. 结论先行

当前 B7 应继续保持 blocked。现有 full audit 确实有 16 条公告：1 critical、11 high、3 moderate、1 low；Electron main 也确实仍以固定 stopped、空模块和 backend_not_configured 回执代替真实 Host 组合。两件事都不能用文档声明绕过。

供应链首选是由总控和用户明确批准后，把 P4-B 的发布前续作基线整体迁到同一批 Electron Forge 8.0.0-alpha.10 包，并使用它上游配套的 Packager 20.3.0、Rebuild 4.2.0、node-gyp 12.4.0、tar 7.5.21 和 @electron-internal/extract-zip 1.0.5。Node 24.21.0、Electron 44.4.5、React 19.3.0、TypeScript 6.0.3、Vite 7.3.6 与 pnpm 12.7.0保持不变；@electron/fuses 随 Forge 8 的 peer 要求升到 2.0.0。这个选择只适合当前尚未正式发布的开发切片，并必须附带“alpha 不得成为正式发行基线”的退出条件。

这是一个有意的受控例外。Forge 官方把 alpha 定义为“不适合一般使用”，所以总控若不接受 prerelease，正确结果是继续 blocked，等待 beta、rc 或 stable，而不是让执行方自行尝试 override、忽略公告或维护长期安全 fork。[Forge 8 跟踪项 #4082](https://github.com/electron/forge/issues/4082)明确给出了 alpha、beta、rc 的含义。

不推荐把 Packager 20 直接 override 进 Forge 7。隔离 lockfile 可以解析并得到 0 条公告，但 Forge 7 为 Packager 18 构造五参数 callback hooks，Packager 20 改为单一 options 对象的 Promise hooks；这不是版本号能掩盖的差异。Node 24 可以同步 require 某些 ESM，因此 ESM 本身不是唯一阻断点，真正的阻断点是 hook 合同已经变化。

main 到 Host 的接线还存在一个需要总控和用户明确冻结的合同矛盾：P4-B 不配置或启动真实模型 provider，但当前 production factory 在 provider 缺失时让通用 /readyz 返回 503 agent_provider_unconfigured。建议新增仅限 managed desktop 的核心 readiness 端点，保留通用 /readyz 语义不变。若不批准这一窄公开合同变更，B7-R1 不能诚实地把桌面状态推进到 online。

## 2. 证据范围与当前事实

### 2.1 已核对的项目文件

依赖与构建事实来自：

- [根 package.json](../package.json)
- [桌面 package.json](../apps/desktop/package.json)
- [pnpm workspace 配置](../pnpm-workspace.yaml)
- [当前 lockfile](../pnpm-lock.yaml)
- [Forge 配置](../apps/desktop/forge.config.ts)
- [B7 阻塞运行说明](b7-windows-shell-running.md)
- [P4-IF-003](phase-4-interface-freeze-003.md)

真实接线事实来自：

- [当前 Electron main](../apps/desktop/electron/main/index.ts#L16)
- [BackendSupervisor](../apps/desktop/electron/main/backend-supervisor.ts#L18)
- [LocalOwnerSession](../apps/desktop/electron/main/owner-session.ts#L15)
- [HostClient](../apps/desktop/electron/main/host-client.ts#L5)
- [preload bridge](../apps/desktop/electron/preload/index.ts#L1)
- [renderer 启动与模块交集](../apps/desktop/src/renderer/main.tsx#L1)
- [桌面模块 registry](../apps/desktop/src/modules/registry.ts#L31)
- [managed desktop nonce gate](../src/wife_system/api/desktop_runtime.py#L16)
- [production factory](../src/wife_system/api/production.py#L105)
- [Host readiness](../src/wife_system/host/runtime.py#L32)
- [readyz 路由](../src/wife_system/api/host_routes.py#L706)

### 2.2 已有实现能证明什么

当前 B7 已有过 typecheck、lint、generated diff、16 项 Vitest、15 项 Python 定向测试、Forge package、app.asar E2E 与 Maris.exe smoke 的执行方证据。这证明保留快照曾经能构建和启动安全空壳。它不能抵消 full audit P0，也不能证明 main 已组合 Host。

当前 [main](../apps/desktop/electron/main/index.ts#L69) 的三个关键 handler 分别返回静态 runtime、backend_not_configured 和空数组。文件没有导入 BackendSupervisor、LocalOwnerSession 或 HostClient。已有三个类的单元测试使用 fake port、fake auth 和 fake secrets；这些测试证明局部算法，不证明真实 Python 进程、HTTP、owner 会话、模块摘要和退出清理已经串起来。

### 2.3 full audit 重放

在项目隔离目录 .codex-tmp/p4-d12 中使用 pnpm 12.7.0 对现有 lockfile 执行只读 full audit：

~~~text
pnpm audit --json --store-dir <isolated-store>
~~~

网络来源是 npm registry 的安全公告接口；pnpm 官方说明 v11 以后 audit 使用 registry 的 bulk advisory endpoint，并以 GHSA 作为公告标识。[pnpm audit 文档](https://pnpm.io/cli/audit)

原始结果：

| 项目 | 值 |
| --- | --- |
| advisory 数 | 16 |
| critical / high / moderate / low | 1 / 11 / 3 / 1 |
| production / dev / optional / total dependency count | 13 / 626 / 90 / 653 |
| audit JSON SHA-256 | 601e031929b404c7650f001c7911a402173c98e2be55a1f77b88102597b611cf |

原始 16 项只汇聚到三个 resolved package：tar 6.2.1 有 12 项，extract-zip 2.0.1 有 2 项，tmp 0.0.33 有 2 项。

## 3. 当前依赖图

~~~mermaid
flowchart TD
    D[apps/desktop]
    D --> F7[Forge 7.11.2 cohort]
    F7 --> ST[shared-types/core/core-utils]
    ST --> R3[rebuild 3.7.2]
    ST --> P18[packager 18.4.4]
    F7 --> CLI[Forge CLI]

    R3 --> T6A[tar 6.2.1]
    R3 --> ENG[vendor Electron node-gyp 10.2.0-electron.1]
    ENG --> T6B[tar 6.2.1]
    ENG --> MFH[make-fetch-happen 10.2.1]
    MFH --> CAC[cacache 16.1.3]
    CAC --> T6C[tar 6.2.1]

    P18 --> EZ[extract-zip 2.0.1]
    CLI --> INQ[Inquirer / external-editor]
    INQ --> TMP[tmp 0.0.33]

    T6A --> A12[12 tar advisories]
    T6B --> A12
    T6C --> A12
    EZ --> A2[2 extract-zip advisories]
    TMP --> A2T[2 tmp advisories]
~~~

以下路径代号在逐项表中使用；每个代号都给出完整路径：

- T1：apps/desktop（lock importer `apps__desktop`）> @electron-forge/plugin-fuses > @electron-forge/shared-types > @electron/rebuild > tar
- T2：apps/desktop（lock importer `apps__desktop`）> @electron-forge/plugin-fuses > @electron-forge/shared-types > @electron/rebuild > @electron/node-gyp > tar
- T3：apps/desktop（lock importer `apps__desktop`）> @electron-forge/plugin-fuses > @electron-forge/shared-types > @electron/rebuild > @electron/node-gyp > make-fetch-happen > cacache > tar
- Z1：apps/desktop（lock importer `apps__desktop`）> @electron-forge/plugin-fuses > @electron-forge/shared-types > @electron/packager > extract-zip
- Z2：apps/desktop（lock importer `apps__desktop`）> @electron-forge/cli > @electron-forge/core-utils > @electron-forge/shared-types > @electron/packager > extract-zip
- M1：apps/desktop（lock importer `apps__desktop`）> @electron-forge/cli > @listr2/prompt-adapter-inquirer > @inquirer/prompts > @inquirer/editor > external-editor > tmp
- M2：apps/desktop（lock importer `apps__desktop`）> @electron-forge/cli > @inquirer/prompts > @inquirer/editor > external-editor > tmp

不同 Forge 包还会形成等价重复路径。逐项处置按最终 resolved package 判断：只要 tar 6.2.1、extract-zip 2.0.1 或 tmp 0.0.33 仍在完整 lockfile 中，对应公告就没有真正消失。

## 4. 16 项 advisory 的完整处置

表中“产物”表示当前 final app.asar 是否包含该包。现有 B7 package 证据和依赖角色都指向“否”；这些包仍在开发者机器上以构建权限运行，所以“未进 app.asar”只降低最终用户运行时暴露，不等于可以通过 full audit。

| # | GHSA / CVE | 包、版本、级别 | 完整路径 | 阶段与产物 | 攻击前提与输入 | 修复或替代 | 本任务处置 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | [GHSA-23hp-3jrh-7fpw](https://github.com/advisories/GHSA-23hp-3jrh-7fpw) / CVE-2026-59873 | tar 6.2.1；critical | T1、T2、T3 | headers/源码下载与解压；不进 app.asar | 攻击者控制或替换压缩 tar 输入，利用高膨胀率、无限总量或大量 entry 耗尽磁盘/CPU | 受影响 <=7.5.18；>=7.5.19；统一到 7.5.21 | 必须消除；不得风险接受 |
| 2 | [GHSA-34x7-hfp2-rc4v](https://github.com/advisories/GHSA-34x7-hfp2-rc4v) / CVE-2026-24842 | tar 6.2.1；high | T1、T2、T3 | 解压；不进 app.asar | 恶意 tar hardlink 利用校验与实际路径解析起点差异，越出目标目录 | 受影响 <7.5.7；审计给出 >=7.5.8；统一到 7.5.21 | 必须消除 |
| 3 | [GHSA-83g3-92jg-28cx](https://github.com/advisories/GHSA-83g3-92jg-28cx) / CVE-2026-26960 | tar 6.2.1；high | T1、T2、T3 | 解压；不进 app.asar | 恶意 hardlink 目标穿过 symlink chain，造成越界读写 | 受影响 <7.5.8；>=7.5.8；统一到 7.5.21 | 必须消除 |
| 4 | [GHSA-8qq5-rm4j-mr97](https://github.com/advisories/GHSA-8qq5-rm4j-mr97) / CVE-2026-23745 | tar 6.2.1；high | T1、T2、T3 | 解压；不进 app.asar | 恶意 entry 名称、symlink 与已存在路径组合，污染目标或覆盖文件 | 受影响 <=7.5.2；>=7.5.8；统一到 7.5.21 | 必须消除 |
| 5 | [GHSA-8x88-c5mf-7j5w](https://github.com/advisories/GHSA-8x88-c5mf-7j5w) / CVE-2026-59874 | tar 6.2.1；high | T1、T2、T3 | tar.replace；不进 app.asar | 调用 replace 处理攻击者控制的负数 entry size tar；当前 B7 未发现 replace 调用，直接可达性低 | 受影响 <=7.5.17；>=7.5.18；统一到 7.5.21 | 仍随 resolved package 一起消除 |
| 6 | [GHSA-9ppj-qmqm-q256](https://github.com/advisories/GHSA-9ppj-qmqm-q256) / CVE-2026-31802 | tar 6.2.1；high | T1、T2、T3 | Windows 解压；不进 app.asar | 恶意 drive-relative symlink linkpath 在 Windows 路径语义下越界 | 受影响 <=7.5.10；>=7.5.11；统一到 7.5.21 | Windows 构建链重点消除 |
| 7 | [GHSA-qffp-2rhf-9h96](https://github.com/advisories/GHSA-qffp-2rhf-9h96) / CVE-2026-29786 | tar 6.2.1；high | T1、T2、T3 | Windows 解压；不进 app.asar | 恶意 drive-relative hardlink linkpath 越出 extraction root | 受影响 <=7.5.9；>=7.5.10；统一到 7.5.21 | Windows 构建链重点消除 |
| 8 | [GHSA-r292-9mhp-454m](https://github.com/advisories/GHSA-r292-9mhp-454m) / CVE-2026-73566 | tar 6.2.1；high | T1、T2、T3 | 解析/筛选 tar；不进 app.asar | 超长路径加成员选择触发递归栈溢出；需要恶意 tar | 受影响 <=7.5.20；>=7.5.21 | 这条决定统一下限必须是 7.5.21 |
| 9 | [GHSA-r6q2-hw4h-h46w](https://github.com/advisories/GHSA-r6q2-hw4h-h46w) / CVE-2026-23950 | tar 6.2.1；high | T1、T2、T3 | macOS APFS 解压；不进 app.asar | Unicode ligature 路径碰撞与并发 reservation race；当前 Windows 主目标不可达，但跨平台开发仍受影响 | 受影响 <=7.5.3；>=7.5.8；统一到 7.5.21 | 不因当前 OS 忽略 |
| 10 | [GHSA-gvwx-54wh-qm9j](https://github.com/advisories/GHSA-gvwx-54wh-qm9j) / CVE-2026-59875 | tar 6.2.1；moderate | T1、T2、T3 | PAX 解析；不进 app.asar | 恶意 PAX path/linkpath 包含 NUL，异常越过普通 Promise catch 并终止进程 | 受影响 <=7.5.16；>=7.5.17；统一到 7.5.21 | 随 critical/high 修复一并消除 |
| 11 | [GHSA-vmf3-w455-68vh](https://github.com/advisories/GHSA-vmf3-w455-68vh) / CVE-2026-53655 | tar 6.2.1；moderate | T1、T2、T3 | PAX/GNU header 解析；不进 app.asar | 扫描器与 extractor 使用不同 parser，恶意 archive 利用解释差异隐藏 member | 受影响 <=7.5.15；>=7.5.16；统一到 7.5.21 | 随图消除；不可把扫描当唯一控制 |
| 12 | [GHSA-w8wr-v893-vjvp](https://github.com/advisories/GHSA-w8wr-v893-vjvp) / CVE-2026-59871 | tar 6.2.1；moderate | T1、T2、T3 | PAX 解析；不进 app.asar | 恶意 numeric path 类型混淆造成进程 crash | 受影响 <=7.5.17；>=7.5.18；统一到 7.5.21 | 随图消除 |
| 13 | [GHSA-7pqw-9j4j-h8q3](https://github.com/advisories/GHSA-7pqw-9j4j-h8q3) / CVE-2026-19693 | extract-zip 2.0.1；high | Z1、Z2 | Packager 解压 Electron zip；不进 app.asar | 恶意 zip symlink entry 指向 extraction root 之外；前提通常是下载源、缓存或镜像被替换或完整性控制失效 | 所有 <=2.0.1 受影响且无该包修复版；改用 Packager 20 的内部 hardened extractor | 必须把旧包从图中移除 |
| 14 | [GHSA-jmr9-qjv8-65gv](https://github.com/advisories/GHSA-jmr9-qjv8-65gv) / CVE-2026-56876 | extract-zip 2.0.1；high | Z1、Z2 | Packager 解压 Electron zip；不进 app.asar | 未验证 symlink 路径可目录穿越并写任意可写路径；需要恶意 zip | 所有 <=2.0.1 受影响且无该包修复版；由 Packager 20 移除 | 必须把旧包从图中移除 |
| 15 | [GHSA-ph9p-34f9-6g65](https://github.com/advisories/GHSA-ph9p-34f9-6g65) / CVE-2026-44705 | tmp 0.0.33；high | M1、M2 | Forge CLI 交互编辑临时文件；不进 app.asar | 调用方把攻击者可控 prefix/postfix 直接传入 tmp，目录穿越；当前固定 CLI 输入降低远程可达性，但被污染配置/插件仍可在开发者权限下运行 | 原公告 >=0.2.6；当前还要考虑后续公告，因此最低 0.2.7 | Forge 8 候选图中应完全消失；若再出现只允许 >=0.2.7 |
| 16 | [GHSA-52f5-9888-hmc6](https://github.com/advisories/GHSA-52f5-9888-hmc6) / CVE-2025-54798 | tmp 0.0.33；low | M1、M2 | 临时目录/文件；不进 app.asar | 攻击者控制 dir symlink 或相关路径，在进程权限下把临时写引向外部 | 受影响 <=0.2.3；>=0.2.4；当前统一下限 0.2.7 | 随旧 tmp 移除 |

处置时发现一条不属于原始 16 项的新公告：[GHSA-7c78-jf6q-g5cm / CVE-2026-49982](https://github.com/advisories/GHSA-7c78-jf6q-g5cm)。它影响 tmp >=0.2.6 且 <0.2.7，说明简单把旧 tmp override 到 0.2.6 会从旧告警切换到新 high，而不是得到安全图。因此本文把临时兼容下限定为 0.2.7。

## 5. 风险解释：audit 不等于已被利用，也不等于可以忽略

当前三个 vulnerable package 都在 dev/build graph，不在最终 app.asar 的业务运行时。普通用户打开 Maris 后不会通过 renderer 直接调用 tar、extract-zip 或 tmp。这使“互联网上任何人直接向桌面端提交压缩包”的攻击叙述不符合当前代码。

真实威胁面位于构建者机器：Forge/Packager/Rebuild 会下载或解压 Electron zip、Node/Electron headers、原生模块输入并创建临时文件。若 registry、mirror、cache、代理、本地插件或输入档案被污染，代码以开发者权限运行，可能覆盖源码、构建输出或其他可写文件。lockfile integrity、registry 签名、固定下载源和只允许审查过的 install scripts 能降低概率，但不能修复解析器自身的路径与资源限制缺陷。

因此本项目的正确结论是：

1. 原始审计不能证明 Maris 已经被攻击；
2. full high/critical gate 已冻结，不能仅因依赖是 devDependency 而忽略；
3. 先停止比 audit fix --force 更正确，因为 force 可能跨 major 改写 Packager、hook 和打包行为；
4. 风险处置终点是从实际 lockfile 移除旧 resolved package，并用真实 package 行为证明新图可用。

## 6. 五条路线比较

| 顺序 | 路线 | 安全结果 | 兼容与行为风险 | 维护/学习成本 | 裁定 |
| --- | --- | --- | --- | --- | --- |
| 1 | Forge 8.0.0-alpha.10 全 cohort + 上游 Packager 20/Rebuild 4 | 隔离候选 audit 为 0；旧 tar/extract/tmp 消失 | 官方明确是 alpha；Forge 全线 ESM；需要真实项目 type/lint/unit/package/E2E | 依赖关系最清楚，长期可回归上游 stable；能学习 ESM、lock 与打包生命周期 | **条件首选**：只用于发布前 B7-R1；需总控/用户改冻；不得成为正式发行基线 |
| 2 | 放弃 Forge package lifecycle，直接 Vite + Packager 20 + Rebuild 4 | 可建立稳定上游图，理论上能去掉旧包 | 必须自行重建 dev、Vite hooks、ASAR、fuses、资源复制与 package 输出；现有 Forge E2E 需重写 | 学习价值高但范围明显扩大，失去 Forge 集成收益 | 若不能等 Forge stable 且拒绝 alpha，另立架构任务；不塞进 B7-R1 |
| 3 | Forge 7 + vendored Packager/extract backport 或 pnpm patch | 只有 fork 改包身份、修复两条 symlink 缺陷并通过专项测试，audit 才可能为 0 | 无上游 extract-zip 修复版；补丁正确性、Windows symlink、zip bomb和未来公告由项目承担 | 维护负担最高；学习者要同时审安全补丁与打包器 | 最后手段；需独立安全评审、到期日和退出到 Forge stable 的计划 |
| 4 | Forge 7 + tar/tmp/Packager 20 精确 pnpm override | lockfile 可解析且候选 audit 为 0 | Packager 20 hook 合同与 Forge 7 不兼容；解析成功不等于 package 成功 | override 看似小，实际隐含维护一条未被上游支持的组合 | **拒绝作为实施方案** |
| 5 | 保留 Forge 7，另加 Packager 20 独立 package step，Forge 只做 dev | Packager 18 仍被 Forge core/shared-types 拉入 full lock，两个 extract high 仍在 | 双打包路径会漂移；若拆锁规避 full audit，门禁语义被削弱 | 两套输出、hook 和测试，学习负担高 | **拒绝**；若移除 Forge 后才转化为顺序 2 |

推荐回退顺序固定如下，执行方不能自行选择：

1. 总控与用户接受“仅发布前”的 Forge 8 alpha 路线，B7-R1 进行真实验证。
2. 任一真实 gate 失败，立即停止，不在同一任务里自由换版本。
3. 若用户不接受 alpha，B7 保持 blocked，等待 Forge 8 beta、rc 或 stable。
4. 若产品时间要求不能等待，先另立“直接 Vite + Packager 20”架构任务和冻结，再派新的实现；它不是 B7-R1 的临场备选。
5. vendored security fork 只有在前述两条均明确否决并有专门安全验收时才讨论。

[Forge #4228](https://github.com/electron/forge/issues/4228)记录了 Forge 7 的 Rebuild 3/tar 6 链，并指出 Forge 8 已转向 Rebuild 4。它是上游问题记录，不是 Forge 7 任意 major override 已兼容的证明。

## 7. tar 6 到 tar 7.5.21 的兼容分析

### 7.1 已证明的层次

**lockfile 解析：通过。** Forge 7 候选中对 tar 统一 override 到 7.5.21 后，Rebuild 3、vendored Electron node-gyp、make-fetch-happen 与 cacache 路径都能解析。

**模块入口表面：有支持证据。** tar 7.5.21 的 npm 元数据同时提供 import 与 require exports，Node 要求 >=18；项目冻结 Node 24.21.0 满足。vendored node-gyp 的实际 install.js 使用 require('tar') 和 tar.extract，这两个入口在 tar 7 仍存在。vendored tarball SHA-256 为 f357931ae77e0e49f2044de30a75f5bb096fc76948e5baa26c29aa0fac285f31。

**真实 rebuild/package：未证明。** Rebuild 3 的声明范围是 tar ^6.0.5，node-gyp fork 声明 ^6.2.1，cacache 16 声明 ^6.1.11。major override 越过了上游测试范围。选项默认值、stream、warning、filter、Windows path 与错误时机都可能影响下载 headers 和 native rebuild。D12 的 lockfile-only 实验没有安装包、执行 lifecycle script、下载 headers 或运行 Forge package。

### 7.2 为什么首选 Rebuild 4 图

Rebuild 4.2.0 要求 Node >=22.12，是 ESM，并依赖 registry node-gyp 12.2+；候选实际解析 node-gyp 12.4.0 与 tar 7.5.21。它移除了 Rebuild 3 对 Electron node-gyp Git fork和 tar 6 的直接依赖。这个图由 Forge 8 上游共同使用，维护责任比在 Forge 7 中强压 tar major 更清楚。

### 7.3 B7-R1 对 tar 的通过条件

只有以下证据一起通过，才能说 tar 路线完成：

1. Node 24.21.0 和 pnpm 12.7.0 下 clean frozen install；
2. lock 中只有 tar 7.5.21，不存在 tar 6.x 或低于 7.5.21 的副本；
3. full 与 production-only high audit 都返回 0；
4. Electron headers 获取、无 native module 和至少一个受控 native fixture 的 rebuild 路径有明确结果；
5. Forge package 生成 Windows 目录；
6. app.asar E2E 与 Maris.exe smoke 通过；
7. 没有额外 install script、未知二进制或网络下载入口进入 packaged runtime。

## 8. Packager 20 与 extract-zip

### 8.1 上游事实

Packager 18.4.4 是 CommonJS，Node >=16.13，依赖 extract-zip ^2.0.0。Packager 20.3.0 是 ESM，Node >=22.12，使用 exports，并依赖 @electron-internal/extract-zip ^1.0.1；当前候选解析 1.0.5。官方 [Packager 文档](https://electron.github.io/packager/main/)说明 Forge 内部使用 Packager。

Packager 20 的 [unzip 源码](https://raw.githubusercontent.com/electron/packager/v20.3.0/src/unzip.ts)调用 Electron 内部 extractor；该 extractor 官方仓库描述了 Zip Slip、symlink escape、absolute path、NUL、Windows reserved name 和 zip bomb 防护，但同时明确它只供 Electron 工具内部使用。[Electron internal extract-zip](https://github.com/electron/extract-zip)

因此 Maris 不应直接把内部 extractor 当公共应用依赖。让受支持的 Packager 20 持有它，边界更合理。

### 8.2 Forge 7 major override 为什么不冻结

Forge 7 源码从 Packager 导入 packager、Options 和 hook types，并用 callback 适配器构造以下旧形式：

~~~text
(buildPath, electronVersion, platform, arch, done) => ...
~~~

Packager 20 的 HookFunction 改为：

~~~text
({ buildPath, electronVersion, platform, arch }) => void | Promise<void>
~~~

Packager 20 的 runHooks 只用一个 options 对象调用 hook，并等待返回 Promise；callback-style functions 不受 serialHooks 支持。[Packager 20 hook types](https://raw.githubusercontent.com/electron/packager/v20.3.0/src/types.ts)与 [hook runner](https://raw.githubusercontent.com/electron/packager/v20.3.0/src/hooks.ts)可以直接核对这一点。Forge 8 已改用 Packager 的 serialHooks。[Forge 8 package 源码](https://raw.githubusercontent.com/electron/forge/v8.0.0-alpha.10/packages/api/core/src/api/package.ts)

Node 24 对同步 ESM 的 require 支持意味着 Forge 7 的 CommonJS 不一定立刻抛 ERR_REQUIRE_ESM；Node 官方要求被加载的 ESM graph 没有 top-level await。[Node require(esm)](https://nodejs.org/api/modules.html#loading-ecmascript-modules-using-require) 但即便模块能加载，旧 callback hook 的实参仍与 Packager 20 不匹配，真实 package 高概率在 afterExtract/afterCopy 等阶段失败或跳过预期同步。因此候选 audit 0 只证明安全数据库不再识别旧包，不证明行为正确。

### 8.3 独立 Packager 20 为什么也不能和 Forge 7 并存

Forge 7 core/shared-types 自己声明 @electron/packager ^18.3.5。新增一个直接 Packager 20 不会移除 Packager 18；full lock 仍包含 extract-zip 2.0.1。若为了得到绿色结果拆分 lock、只审新 package workspace 或忽略 Forge dev graph，就改变了“full dependency audit”门禁含义。

独立 Packager 20 只有在彻底移除 Forge package lifecycle，并由项目显式承担 Vite build、hook、ASAR、fuses、资源复制与输出布局后才成为完整路线。这需要新的架构冻结。

## 9. 隔离候选实验

开始网络访问和解析前重新读取了最新 control，版本仍为 2026-09-27T18:23:00+08:00。实验只写 .codex-tmp/p4-d12，没有触碰项目 package.json、pnpm-workspace.yaml、pnpm-lock.yaml 或 node_modules。

实际解析入口均为隔离安装的 `node .codex-tmp/p4-d12/tool/node_modules/pnpm/bin/pnpm.mjs`。对现有项目只执行 `audit --json`，将标准输出保存在隔离目录的 `audit-full.json`；没有 install 或写项目 lock。对三个候选分别执行以下命令，其中 `<candidate>` 精确替换为 `candidate-a`、`candidate-b` 或 `candidate-c`：

~~~text
node .codex-tmp/p4-d12/tool/node_modules/pnpm/bin/pnpm.mjs install --dir .codex-tmp/p4-d12/<candidate> --lockfile-only --ignore-scripts --store-dir .codex-tmp/p4-d12/stores/<candidate>
node .codex-tmp/p4-d12/tool/node_modules/pnpm/bin/pnpm.mjs audit --dir .codex-tmp/p4-d12/<candidate> --json --store-dir .codex-tmp/p4-d12/stores/<candidate>
~~~

依赖元数据与 tarball 只来自 `https://registry.npmjs.org/`，audit 请求只发往该 registry 的 bulk advisory endpoint；未访问私有 registry、项目账户或外部登录。实验进程实际显示 Node 26.8.1，因此结果只属于依赖解析；不能替代冻结 Node 24.21.0 的真实安装和打包。

| 候选 | 关键差异 | lock SHA-256 | audit 结果 | audit JSON SHA-256 | 能证明 / 不能证明 |
| --- | --- | --- | --- | --- | --- |
| A | Forge 7.11.2；Packager 20.3.0 major override；tar 7.5.21；tmp 0.2.7 | 6264530e04fc79e9b84a6738c60657d221e8b0db3a5cf0f7d15919a965b3a226 | 0 | 9907fe81fe959e0344b9c733eae75373cce585c7db3d3c30bca2b7e153507716 | 证明 lock 和 audit 可绿；不能证明 Forge 7/Packager 20 hooks 或 package |
| B | Forge 7.11.2；tar 7.5.21；tmp 0.2.7；保留 Packager 18 | 87b612f8f4f287770978e1547c7e8d5e63aaa680270514127e283fd9c2b5d7c8 | 2 high | ffe4b99dba08de99acd9930a28475e313a77f3373641d073aed2650f4d7578ad | 证明 tar/tmp 能消除 14 条；两个 extract GHSA 仍阻塞 |
| C | Forge 8.0.0-alpha.10 cohort；fuses 2.0.0；tar 7.5.21 | b25a85e028033b0a70eaa97845a7e3256cc65fff948063e322475e7eae16a1ac | 0 | cf7f239b3c0c4def23dd518df1860c6305ce08a6622d14272b39a668f8dae26a | 证明上游配套图能解析且已知 audit 绿；不能证明当前项目 compile/package/E2E |

最初用 tmp 0.2.6 的候选 A/B 各新增一条 GHSA-7c78-jf6q-g5cm high；改到 0.2.7 后才消失。这一重试有有效新输出，不属于无进展重试。

完成前已把解析目标核验为 `D:\CodeX_gap\wife-system\.codex-tmp\p4-d12`，确认它位于工作区 `.codex-tmp` 下，再用同一 PowerShell 进程按 literal path 递归清理；清理后 `Test-Path` 为 `False`。上述 hash 保留为不可变摘要，临时 JSON、候选 lock、store、cache 和工具均不属于交付物。

## 10. 推荐的精确依赖图

### 10.1 需总控和用户先接受的发布前候选

直接依赖保持精确 pin：

| 包 | 候选值 | 修改位置 | 说明 |
| --- | --- | --- | --- |
| Node | 24.21.0 | 根 package.json | 保持 P4-IF-003 |
| pnpm | 12.7.0 | 根 package.json | 保持 |
| Electron | 44.4.5 | apps/desktop/package.json | 保持，不做 Electron major 变更 |
| React / React DOM | 19.3.0 | apps/desktop/package.json | 保持 |
| TypeScript | 6.0.3 | apps/desktop/package.json | 保持 |
| Vite | 7.3.6 | apps/desktop/package.json | 保持，需用真实 Forge 8 plugin 构建验证 |
| @electron-forge/cli | 8.0.0-alpha.10 | apps/desktop/package.json | 与所有 Forge 包同 cohort |
| @electron-forge/plugin-fuses | 8.0.0-alpha.10 | apps/desktop/package.json | 同 cohort |
| @electron-forge/plugin-vite | 8.0.0-alpha.10 | apps/desktop/package.json | 同 cohort |
| @electron-forge/shared-types | 8.0.0-alpha.10 | apps/desktop/package.json | 同 cohort |
| @electron/fuses | 2.0.0 | apps/desktop/package.json | 满足 Forge 8 plugin peer |

候选 lock 必须精确解析：

| 传递包 | 精确 resolved 值 |
| --- | --- |
| @electron/packager | 20.3.0 |
| @electron/rebuild | 4.2.0 |
| node-gyp | 12.4.0 |
| tar | 7.5.21 |
| @electron-internal/extract-zip | 1.0.5 |

预期图必须保持为同一条上游支持链：

~~~mermaid
flowchart TD
    D[apps/desktop]
    D --> F8[Forge cohort 8.0.0-alpha.10]
    D --> FU[@electron/fuses 2.0.0]
    F8 --> P20[@electron/packager 20.3.0]
    P20 --> IEZ[@electron-internal/extract-zip 1.0.5]
    F8 --> R4[@electron/rebuild 4.2.0]
    R4 --> NG[node-gyp 12.4.0]
    NG --> T7[tar 7.5.21]
    F8 --> PV[plugin-vite alpha.10]
    PV --> V[Vite 7.3.6]
~~~

### 10.2 pnpm workspace 与 npmrc

继续保留：

- nodeLinker: hoisted；
- autoInstallPeers: false；
- strictPeerDependencies: true；
- blockExoticSubdeps: true；
- allowBuilds 只允许经过复核的 electron 与 esbuild；真实 frozen install 若要求新增脚本，先停止审查，不自动放行；
- .npmrc 的 node-linker=hoisted、save-exact=true 和 strict peer 设置。

`apps/desktop/package.json` 继续使用现有 Forge package 入口，不新增独立 Packager 20 script；否则会重新引入双打包生命周期。Forge 8 的 package config、Vite hooks、ASAR、资源复制和 fuses 适配由 B7-R1 在真实 package gate 中验证。

建议移除旧 Electron node-gyp 本地 tarball override，因为 Rebuild 4 使用 registry node-gyp 12；对应 vendor 文件只有在最终 lock 完全不引用后才由 B7-R1 删除。增加精确 tar 7.5.21 override，用于锁住 node-gyp 的安全修复下限：

~~~yaml
overrides:
  tar: 7.5.21
~~~

不建议长期写 tmp override。Forge 8 候选图中 tmp 已消失；若实际完整图重新出现 tmp，必须解析到 0.2.7 或更高并重新 full audit。

Packager、Rebuild、node-gyp 和内部 extractor 优先由 Forge 8 cohort 的上游依赖加 lockfile 固定，不用跨 major override 拼装。若 clean resolution 得到与表中不同的版本，停止并由总控更新 P4-IF-004，而不是执行方顺手接受。

### 10.3 必须从图中完全消失

- @electron/packager 18.4.4；
- extract-zip 2.0.1；
- @electron/rebuild 3.7.2；
- @electron/node-gyp 10.2.0-electron.1 本地 fork；
- tar 6.2.1 和所有低于 7.5.21 的 tar；
- tmp 0.0.33；若 tmp 再出现，不得低于 0.2.7。

deprecated 传递依赖不是和 CVE 等价的硬失败，但 B7-R1 必须列出并说明来源。出现新的 critical/high、安全敏感 install script、Git/exotic dependency 或未知原生二进制时立即停止。

## 11. 给总控的 P4-IF-004-Fxx 冻结建议

### 供应链

- **P4-IF-004-F01：候选性质。** Forge 8.0.0-alpha.10 只用于发布前 B7-R1；不得据此发布正式版本。用户宣布发行前必须升级到当时已验收的 beta/rc/stable，优先 stable。
- **P4-IF-004-F02：同 cohort。** cli、plugin-fuses、plugin-vite、shared-types 全部精确为 8.0.0-alpha.10；禁止混用 Forge 7/8。
- **P4-IF-004-F03：保留版本。** Node 24.21.0、pnpm 12.7.0、Electron 44.4.5、React 19.3.0、TypeScript 6.0.3、Vite 7.3.6 保持精确值；fuses 升到 2.0.0。
- **P4-IF-004-F04：解析图。** Packager 20.3.0、Rebuild 4.2.0、node-gyp 12.4.0、tar 7.5.21、internal extract 1.0.5 为候选精确 resolved 图。
- **P4-IF-004-F05：workspace。** 保留 hoisted、strict peers、关闭自动 peer、block exotic subdeps 和生命周期脚本 allowlist；移除旧 Electron node-gyp override；tar 精确 override 7.5.21。
- **P4-IF-004-F06：消失清单。** Packager 18、extract-zip 2、Rebuild 3、Electron node-gyp fork、tar 6、tmp 0.0.33 必须从 lock 完全消失。
- **P4-IF-004-F07：审计。** full 与 production-only audit 的 high/critical 均为 0；不降低级别、不 ignore GHSA、不使用无到期日 allowlist。
- **P4-IF-004-F08：禁止 Forge 7 major override。** Forge 7 + Packager 20 lockfile 解析成功不构成兼容证据；不得作为默认修复。
- **P4-IF-004-F09：alpha 退出。** Forge 8 beta/rc/stable 发布后另立升级快照；alpha package、hook、Vite、fuses 任一真实 gate 失败即停止，不在 B7-R1 内自由试版本。

### Host 公开合同与组合

- **P4-IF-004-F10：需总控/用户明确决定。** 新增 managed desktop 专用 GET /api/v1/desktop/readyz；它要求 startup nonce，只检查数据库、Alembic head 和 module registry 的核心 readiness，不要求模型 provider。通用 /readyz 保持现有 provider readiness 语义。若不接受这一公开合同变更，B7-R1 的 managed online 路径停止。
- **P4-IF-004-F11：不伪造 provider。** 禁止注入一个永远失败却自称 ready 的假 ModelProvider，也禁止为 P4-B 启动 DeepSeek。未来 Agent 调用仍由通用 provider 状态和业务错误 fail closed。
- **P4-IF-004-F12：唯一 composition root。** Electron main 创建且只创建一套 Supervisor、OwnerSession、HostClient、OwnerSecretStore 和 runtime publisher；renderer、preload 不参与依赖构造。
- **P4-IF-004-F13：sidecar handshake。** managed child 在专用 pipe 输出协议版本、instance_id、loopback port 与 nonce digest；不输出原 nonce。health 成功加 desktop core ready 成功后才进入 online。
- **P4-IF-004-F14：Supervisor。** ready 失败必须清理本次 owned child；recover 先停止旧 owned child再启动新实例；online 每 5 秒 health，连续 3 次失败进入 offline；5 分钟最多 3 次，退避 1/2/4 秒；正常停止 5 秒后只强停自有进程树。
- **P4-IF-004-F15：external dev。** 只允许 development build、显式 loopback URL 和本次 nonce；不传空 nonce；永不 stop/restart 外部进程。
- **P4-IF-004-F16：owner/token。** OwnerSession 的 access token 只经 main 内部方法交给 HostClient；refresh single-flight；revoke 同时清内存 token并标记 repair；token、密码、nonce不进入 IPC、日志或错误。
- **P4-IF-004-F17：module 回执。** HostClient 只返回严格解析后的安全 ModuleSummary 数组；不得把 openapi-fetch 的 Response、raw error、header 或 URL透传 renderer。失败返回稳定 DesktopError code。
- **P4-IF-004-F18：runtime 发布。** snapshot 由 Supervisor state 加 OwnerSession safeState 合成；每次真实状态变化向主 renderer 发送 runtime:state@1；不包含 PID、port、路径、命令、token、nonce或原始异常。
- **P4-IF-004-F19：统一退出。** Tray quit、应用 quit、session end 走同一 bounded shutdown；隐藏窗口不停止 Host；退出期间拒绝新恢复，flush 设置/outbox后停止 owned child。

### 执行与验收

- **P4-IF-004-F20：实现方边界。** B7-R1 可改供应链、Electron main 与执行方测试，以及 F10 被批准后的最小 Python desktop readiness/sidecar 和对应执行方测试；不得改 Finance、Agent、pending、memory、activity import 语义。
- **P4-IF-004-F21：测试边界。** 禁止修改 tests/independent、P4 矩阵和独立报告；执行方自测只到 review/finished。
- **P4-IF-004-F22：真实 gate。** lockfile、clean frozen install、peers、full/prod audit、type/lint/generated、Vitest、Python 定向、Uvicorn managed smoke、Forge package、app.asar E2E、Maris.exe smoke 和资源收口缺一不可。

## 12. 为什么需要 desktop core readiness

[production factory](../src/wife_system/api/production.py#L130)把 agent_provider_ready 设置为 provider is not None；[HostRuntime.readiness](../src/wife_system/host/runtime.py#L41)在 provider 缺失时返回 agent_provider_unconfigured；[执行方测试](../tests/host/test_production.py#L56)也固定了这个行为。

P4-IF-003 同时规定 P4-B 不启动 DeepSeek、只交付 Shell/模块占位/连接能力，并要求 nonce + 现有 readiness 后进入 online。三者组合后出现矛盾：

~~~text
P4-B 不配置 provider
        |
production /readyz 必然 503
        |
Supervisor 永远不能 online
~~~

建议把“进程是否能承载桌面核心 API”与“模型 provider 是否可运行”分成两个探针：

| 探针 | 含义 | provider 缺失 |
| --- | --- | --- |
| /healthz | 进程存活 | 仍为 200 |
| /api/v1/desktop/readyz | managed desktop 的 DB、migration、registry 和 nonce 已就绪 | 可为 200 |
| /readyz | 完整 Host，包括 provider readiness | 仍为 503 agent_provider_unconfigured |

新端点只在 managed desktop profile 启用；缺 nonce、错 nonce、数据库失败、migration 落后或 registry 空都返回稳定 503。它不提供认证、不开放业务 API、不改变 /readyz，也不表示 Agent 可用。桌面可以显示“Host 已连接，Agent provider 未配置”的安全占位，但 P4-B 不调用模型。

这是 Python Host 公开合同变化，D12 无权直接冻结。总控/用户若不接受，唯一诚实选择是维持 blocked，不能把 healthz 200 偷换成完整 ready，也不能注入虚假 provider。

## 13. Electron main 到真实 Host 的组合

### 13.1 当前缺口

1. main 的 runtime 是常量，recover 不调用 Supervisor，modules 永远为空。
2. BackendSupervisor 没有真正的 child process port、状态订阅或健康循环。
3. ready 失败后当前代码保留 owned child；recover 会再次 start，可能遗留旧进程。
4. external_dev 目前用空 nonce 调 ready，与冻结要求不符。
5. LocalOwnerSession 建立会话后没有把 access token交给 HostClient 的公开 main-only方式。
6. 现有 SecureStore 只负责 seal/open，没有实现 OwnerSecretPort 的原子持久化、stage/commit/repair。
7. HostClient 只实现 modules 与一次 401 refresh，且返回 openapi-fetch 原始结果；OwnerAuthPort 适配尚不存在。
8. Python sidecar launcher、bound machine line、shutdown adapter 与 production composition entry 尚不存在。

### 13.2 推荐文件职责

| 文件 | 职责 |
| --- | --- |
| electron/main/composition-root.ts | 唯一构造顺序、状态合成、启动/恢复/退出 |
| electron/main/managed-host-port.ts | spawn、专用 pipe、bound 消息、loopback HTTP health/core ready、owned stop |
| electron/main/backend-supervisor.ts | 纯状态机、single-flight start/recover、health loop、预算、owned cleanup |
| electron/main/owner-auth-client.ts | bootstrap status、initialize、login、refresh；只返回严格 token pair |
| electron/main/owner-secret-store.ts | safeStorage 加密、stage/commit/repair、原子文件 |
| electron/main/owner-session.ts | 建立、single-flight refresh、main-only access token读取、revoke |
| electron/main/host-client.ts | main-only Bearer、401 一次 refresh、modules 严格解析、安全错误映射 |
| electron/main/index.ts | 窗口/Tray/IPC 入口，调用 composition root，不再持有静态假 runtime |
| src/wife_system/api/desktop_sidecar.py | 受控 production app、loopback bind、machine handshake、bounded shutdown |
| src/wife_system/api/desktop_runtime.py | nonce gate；若 F10 接受，保留专用核心 readiness 规则 |
| src/wife_system/api/host_routes.py | F10 的窄路由；不改变通用 /readyz |

内部类名可以调整，但上述所有权不可打散。不要把 spawn、token 或 HTTP 分给 renderer。

### 13.3 构造顺序

1. main 读取严格设备设置，确定 managed 或 development-only external_dev。
2. 构造 OwnerSecretStore；此时不解密到 renderer。
3. 构造 ManagedHostPort 与 BackendSupervisor。
4. Supervisor 启动或连接，验证 instance、nonce digest、loopback、health 和 desktop core ready。
5. 构造 OwnerAuthClient，建立 LocalOwnerSession。
6. 通过 main-only access token 初始化 HostClient；HostClient 的 refresh callback 指向同一个 OwnerSession。
7. 调用 HostClient.modules，严格验证安全摘要。
8. IPC 注册后只暴露合成 snapshot、恢复动作与摘要数组。
9. renderer 用现有 compiled registry 做交集；交集为空时继续 fail closed。

### 13.4 完整数据流

~~~mermaid
sequenceDiagram
    participant R as React renderer
    participant P as typed preload
    participant M as Electron main composition root
    participant S as BackendSupervisor
    participant C as managed Python child
    participant A as LocalOwnerSession
    participant H as HostClient
    participant F as FastAPI Host

    M->>S: start(managed)
    S->>C: spawn(instance_id, nonce, loopback only)
    C-->>S: MARIS_READY protocol/port/nonce_digest
    S->>F: GET /healthz
    S->>F: GET /api/v1/desktop/readyz + nonce
    F-->>S: core ready
    S-->>M: state=online

    M->>A: establish()
    A->>F: bootstrap-status / initialize? / login or refresh
    F-->>A: access + rotating refresh token
    A-->>M: authenticated; access remains main-only
    M->>H: setAccessToken
    H->>F: GET /api/v1/modules + Bearer
    F-->>H: safe module summaries
    H-->>M: validated summaries only

    R->>P: modules.list()
    P->>M: modules:list@1
    M-->>P: safe summaries
    P-->>R: safe summaries
    Note over R: compiled contribution 与 Host 摘要取交集

    R->>P: runtime.recover()
    P->>M: runtime:recover@1
    M->>S: bounded recover
    S->>C: stop old owned child before new start
    S-->>M: new safe snapshot
    M-->>R: runtime:state@1
~~~

### 13.5 错误与安全映射

| 内部错误 | renderer 可见 |
| --- | --- |
| child 早退、bind 失败、ready timeout | backend_start_failed 或 backend_timeout |
| nonce/instance/digest 不匹配 | backend_identity_rejected |
| database/migration/registry 未就绪 | backend_not_ready |
| owner 本地状态损坏或 refresh/login 均失败 | needs_repair |
| Host 401 且 single-flight refresh 后仍 401 | session_expired |
| modules schema/major/profile/prefix 不匹配 | 模块不进入交集；稳定 module_unavailable |
| 原始 traceback、URL、PID、port、path、token | 永不进入 renderer/日志 |

## 14. BackendSupervisor 必须补齐的状态规则

当前类提供了基础状态和恢复预算，但 B7-R1 至少修正：

1. start 和 recover single-flight，避免双击与启动事件并发创建两个 child；
2. managed start 获得 child 后，任一 handshake/ready 失败都在返回前 bounded cleanup；
3. recover 若已有 owned child，先停止该 child并确认 ownership，再等待退避、生成新 instance/nonce；
4. online 后启动一个可取消的 5 秒 health loop；连续三次失败才 offline，child exit 立即 offline；
5. online 稳定 10 分钟后才重置 recovery budget；
6. stop 幂等；重复 quit 不把 stopped 变成 failed；
7. external_dev 必须带开发者明确提供的 nonce，只观察，不 stop、不 forceStopTree；
8. 所有状态变化经单一 publisher 发安全 snapshot；
9. app quit 时先禁止新的 recover，再 flush，再停止 child；
10. 测试要覆盖 ready false 清理、recover 旧 child 清理、并发 start/recover、健康三连败、预算耗尽、重复 stop、外部模式不 kill。

## 15. B7-R1 的有限实施顺序

### 第 0 步：进入快照

- 总控先接受 D12，并冻结 P4-IF-004。
- 明确 F01 的 alpha 决定和 F10 的 desktop core readiness 决定。
- 执行方记录开始 source manifest；不得用本 D12 临时目录作为输入。

### 第 1 步：供应链图

- 一次性更新 Forge cohort 与 fuses；
- 移除旧 Electron node-gyp override和已不再引用的 vendor tarball；
- 保留 workspace 安全设置，增加 tar 7.5.21 精确 override；
- 只做 lockfile resolution，检查 peers、exotic dependencies、lifecycle script 请求和消失清单；
- full/prod audit 任一 high/critical 非零立即停止。

### 第 2 步：新图的静态与单元证据

- 在 Node 24.21.0 下 clean frozen install；
- typecheck、lint、generated diff 和现有 Vitest；
- 针对 Forge 8 config、fuses 2 与新 package hook 变化修正执行方代码/测试；
- 不开始真实 Host 组合，直到工具链静态证据通过。

### 第 3 步：真实 composition root

- 先实现 sidecar/managed port 与 Supervisor cleanup；
- 再实现 OwnerSecretStore、OwnerAuthClient、OwnerSession token handoff；
- 再把 HostClient modules 与 main IPC 接入；
- 最后把 fake runtime 替换为真实 publisher；
- 不扩展财务、Agent、活动导入或 P4-C 页面。

### 第 4 步：Python 定向与自有 Uvicorn smoke

- 只运行 desktop runtime、production、auth、modules 和 readiness 受影响测试；
- 执行方可以新增自身 desktop sidecar/contract 测试；
- 用自己启动的 loopback、单 worker、无 reload Uvicorn 验证 nonce、core ready、owner、modules、stop 和资源收口；
- 不启动 DeepSeek、Docker、PostgreSQL 或独立测试。

### 第 5 步：Windows package

- 在 frozen lock 下运行 Forge package；
- 检查 Packager 20 hooks、Vite 输出、ASAR、preload、fuses、资源复制；
- 包内不得出现旧构建依赖、secret、token、个人数据、任意更新 URL 或开发配置；
- package 失败立即停止，不退回 Forge 7 major override。

### 第 6 步：包后行为

- 对最终 app.asar 运行 packaged E2E；
- 对真实 Maris.exe 做 startup、owner、modules、recover、Tray quit 与 owned child cleanup smoke；
- 验证 renderer 不能直接网络/Node，模块交集仍 fail closed；
- 记录 Windows 目标环境与未自动化人工项。

### 第 7 步：终点快照与交接

- 生成有序 source manifest、lock hash、依赖图或 SBOM、package 摘要和测试摘要；
- 更新 B7 运行说明，只写实际证据；
- 状态只到 review/finished，停止并等待 P4-C12；不得自行启动独立测试。

### 可修改类别

B7-R1 任务卡可授权：

- 根 Node/pnpm 依赖与锁配置；
- apps/desktop 的 package/Forge/Vite/main/preload/shared 和执行方 tests；
- F10 获批后的最小 desktop sidecar/readiness Python 文件及 tests/host 执行方用例；
- B7 运行说明、source manifest 和执行角色状态。

必须继续禁止：

- tests/independent；
- P4 测试矩阵、独立报告、control、overview、其他角色状态；
- FinanceService、Agent 工具、pending、memory、activity import 的业务语义；
- OpenClaw、微信、DeepSeek、真实个人数据；
- Git 写操作，除非由总控按仓库规则执行。

## 16. 门禁、证据和停止条件

### 16.1 依赖门禁

| 门禁 | 通过定义 |
| --- | --- |
| 工具版本 | node --version 精确 v24.21.0；pnpm 精确 12.7.0 |
| lockfile-only | clean candidate 可以只生成预期 lock；无 peer/exotic/policy 错误 |
| frozen install | 从空 node_modules 使用 frozen lock 成功；只执行 allowlist scripts |
| full audit | audit-level high 退出码 0；critical/high 都是 0 |
| production audit | prod audit-level high 退出码 0；不能替代 full |
| 消失清单 | 六类旧包在 lock 与 list/why 中均不存在 |
| deprecated | 列出来源、是否执行、退出计划；安全相关项不得只登记 |
| signatures/SBOM | registry 提供签名时验证；输出依赖图或 SBOM 与摘要；它们不替代 audit |

pnpm 官方允许用 overrides 强制安全版本，也支持 audit --fix；本任务只允许评审后的手工精确 override，不运行自动 force。[pnpm overrides](https://pnpm.io/settings#overrides)、[pnpm audit](https://pnpm.io/cli/audit)

### 16.2 产品与行为门禁

- TypeScript compile、lint、generated diff；
- 现有与新增执行方 Vitest；
- Python desktop/production/auth/modules 定向回归；
- 自有 Uvicorn managed smoke；
- Forge Windows package；
- package app.asar E2E；
- Maris.exe smoke；
- app.asar/资源 secret 与个人数据扫描；
- 端口、child、窗口、Tray 和临时目录收口。

### 16.3 执行方自测与独立验收分层

B7-R1 执行方负责生成修复本身的可复算证据：开始/结束 source manifest、精确 lock hash、依赖图或 SBOM、full 与 production audit 原始摘要、peer 与 lifecycle script 检查、type/lint/generated、执行方 Vitest、受影响 Python 定向测试、自有 Uvicorn managed smoke、Forge package、packaged app.asar E2E、Maris.exe smoke，以及进程、端口、窗口和临时资源收口。它只能据此提交 `review / finished`，不能宣称独立验收通过。

总控接受 B7-R1 后才可单独派发 P4-C12。独立测试方从冻结 source manifest 和 lock hash 开始，独立复算完整依赖图与两个 audit，重点攻击新图安装/打包可复现性、managed child ownership 与泄漏、nonce/owner/token 隔离、并发恢复、模块交集、IPC allowlist、离线降级、包内秘密扫描和真实 EXE 退出收口。独立测试方不修改执行方代码、lock、矩阵既有口径或 D12 结论；发现问题只报告可复现证据，由总控决定返工。

### 16.4 立即停止

出现任一项即停止受影响范围并交回总控：

- 新 full critical/high；
- alpha 的 config/plugin/package API 要求重写业务或换 Electron major；
- 未知 install script、未审计 native helper、Git/exotic dependency；
- Packager 20/Forge 8 真实 package 行为失败；
- F10 未决定却试图用 healthz 或假 provider宣称 online；
- ready 失败后 child 遗留、错误进程被停止、PID 被当 ownership；
- token、nonce、密码、财务数据或原始私密日志进入 renderer/产物；
- 需要改 tests/independent、矩阵或独立报告；
- 同一阻塞连续两个检查点没有有效新输出。

### 16.5 复评触发条件

出现以下任一变化必须重新核对依赖图和威胁模型：Forge 8 发布新的 beta/rc/stable；Forge alpha、Packager、Rebuild、node-gyp、tar 或内部 extractor 版本变化；GitHub Advisory Database 出现影响候选图的新 critical/high；Node 24 或 Electron 44 patch 改变 engine/打包行为；项目增加 native module、自动更新、下载镜像、代码签名或发布上传；总控改变 provider readiness、managed sidecar 或 full audit 的冻结语义。复评前不沿用“候选 C 为 0”的历史数字。

## 17. 工程教学地图

每个练习只用虚拟名字、虚拟路径和虚拟 token，不使用真实个人数据。

| 主题 | 在当前 B7 的含义 | 对应文件 | 小练习 | 检查题 |
| --- | --- | --- | --- | --- |
| 直接依赖 | 桌面 package.json 主动声明 Forge CLI、Electron、React | [桌面 package.json](../apps/desktop/package.json) | 圈出四个 Forge direct dependency，写出谁负责 dev、package、Vite、fuses | 为什么 package.json 没写 tar，audit 仍会报告 tar？ |
| 传递依赖 | Forge 拉入 Packager、Rebuild，再拉入 tar/extract/tmp | [lockfile](../pnpm-lock.yaml) | 从 Forge CLI 手写一条到 extract-zip 的完整路径 | 删除 direct Packager 20 能否自动删除 Forge 7 的 Packager 18？ |
| lockfile | 把范围解析成确定版本、来源和 integrity | [lockfile](../pnpm-lock.yaml) | 比较 package.json 的 ^18.3.5 与 lock 的 18.4.4，解释两者职责 | 为什么只改 package.json、不审 lock 不足以证明修复？ |
| override | 在根解析层改写传递版本，责任转移给项目 | [workspace 配置](../pnpm-workspace.yaml) | 用纸面例子把 tar 6 强制为 7.5.21，再列三项必须复验的行为 | override 能证明 API 兼容吗？ |
| 构建工具威胁 | devDependency 在开发者权限下解压下载物和写临时文件 | [Forge 配置](../apps/desktop/forge.config.ts) | 画出 registry → cache → extractor → build output 的信任边界 | 为什么“不进 app.asar”仍不能自动通过 full audit？ |
| audit 与 exploit | audit 匹配包版本；exploit 还要看调用 API、输入控制和平台 | [B7 运行说明](b7-windows-shell-running.md) | 分别给 tar.replace 和 Windows drive-relative symlink 写可达/不可达条件 | 0 个 audit 告警是否等于打包一定正确？ |
| 停止与 force | 自动 force 可能跨 major 改 hook，安全数字变绿而行为损坏 | 本文第 6～9 节 | 对候选 A 写“解析通过/行为未证”的两列表 | 为什么 P0 门禁失败时先停比盲目 audit fix --force 更好？ |
| 依赖图 | 节点是包版本，边是“谁依赖谁”，同名包可能有多副本 | [lockfile](../pnpm-lock.yaml) | 把 T1、T2、T3 画成一张图，标出共同 resolved tar | 修复一条路径但保留另一份 tar 6，结果是什么？ |
| 攻击面 | 能接收什么输入、以什么权限运行、能影响哪些文件 | [node-gyp vendor 包](../apps/desktop/vendor/electron-node-gyp-06b29aafb7708acef8b3669835c8a7857ebc92d2.tgz) | 写出 headers tar 的来源、校验、解压目录和进程权限 | 风险为什么主要落在构建者机器？ |
| 可达性 | 脆弱函数是否被当前调用路径执行 | [BackendSupervisor](../apps/desktop/electron/main/backend-supervisor.ts#L24) | 把“包存在”和“函数被恶意输入调用”分开列证据 | tar.replace 公告与当前 extract 路径的可达性相同吗？ |
| 补偿控制 | lock integrity、loopback、nonce、allowBuilds 降低概率/影响 | [desktop nonce gate](../src/wife_system/api/desktop_runtime.py#L16) | 为恶意 Electron zip 列三项补偿控制和一项它们修不了的缺陷 | 完整性校验能修复 extractor 的 symlink bug 吗？ |
| 风险接受 | 明确谁批准、哪条 GHSA、期限、控制和剩余影响 | [control](coordination/control.md) | 为一个虚构 moderate 写 7 天例外；再说明为何本次 high 不接受 | “dev only”能否成为风险接受理由？ |
| 退出标准 | 用可观察证据结束临时方案 | 本文 F01/F09 | 为 alpha 写 beta/rc/stable、package、audit 三个退出触发器 | 没有到期条件的 allowlist 会发生什么？ |
| composition root | 唯一地点创建进程、session、client 并控制生命周期 | [当前 main](../apps/desktop/electron/main/index.ts#L93) | 用五个方框画 main 的构造顺序，不把 token连到 renderer | 为什么不能在每个 IPC handler 新建一套 HostClient？ |
| 依赖注入 | Supervisor 接收 port、OwnerSession 接收 auth/secrets，测试可用 fake | [Supervisor](../apps/desktop/electron/main/backend-supervisor.ts#L22)、[OwnerSession](../apps/desktop/electron/main/owner-session.ts#L18) | 为 ready false 写一个 fake port，并断言 owned child 被清理 | DI 与“为了测试加 if test”有什么差别？ |

### 建议学习顺序

1. 先读 package.json 和 lockfile，能顺着一条依赖路径走到底；
2. 再读 16 项表，区分包匹配、调用可达和攻击输入；
3. 对照候选 A/B/C，理解 lockfile 绿和真实 package 绿是两层证据；
4. 读 BackendSupervisor、OwnerSession、HostClient 三个小类，画依赖；
5. 读 main，找出它没有 composition root 的证据；
6. 读 production readiness 三个 Python 位置，解释 provider 矛盾；
7. 最后跟着 B7-R1 的 gate 看实现证据，不先背完整 Electron 生态。

## 18. 官方来源与事实等级

以下页面在 2026-09-27 核对：

- 两条 extract 公告：[GHSA-7pqw-9j4j-h8q3](https://github.com/advisories/GHSA-7pqw-9j4j-h8q3)、[GHSA-jmr9-qjv8-65gv](https://github.com/advisories/GHSA-jmr9-qjv8-65gv)
- tar critical 与最终 7.5.21 下限：[GHSA-23hp-3jrh-7fpw](https://github.com/advisories/GHSA-23hp-3jrh-7fpw)、[GHSA-r292-9mhp-454m](https://github.com/advisories/GHSA-r292-9mhp-454m)
- Forge 7 tar 链：[Forge #4228](https://github.com/electron/forge/issues/4228)
- Forge 8 release process：[Forge #4082](https://github.com/electron/forge/issues/4082)
- Forge：[官方文档](https://www.electronforge.io/)、[官方仓库](https://github.com/electron/forge)
- Forge 7 package 实际调用：[Forge 7 package.ts](https://raw.githubusercontent.com/electron/forge/v7.11.2/packages/api/core/src/api/package.ts)
- Forge 8 Promise hook 适配：[Forge 8 package.ts](https://raw.githubusercontent.com/electron/forge/v8.0.0-alpha.10/packages/api/core/src/api/package.ts)
- Packager：[官方文档](https://electron.github.io/packager/main/)、[20.3.0 releases](https://github.com/electron/packager/releases)
- Rebuild：[官方仓库与说明](https://github.com/electron/rebuild)
- Electron 构建与安全：[Electron packaging tutorial](https://www.electronjs.org/docs/latest/tutorial/tutorial-packaging)、[security checklist](https://www.electronjs.org/docs/latest/tutorial/security)、[fuses](https://www.electronjs.org/docs/latest/tutorial/fuses)
- pnpm：[overrides](https://pnpm.io/settings#overrides)、[audit](https://pnpm.io/cli/audit)、[lockfile 设置](https://pnpm.io/settings#lockfile-settings)
- npm：[package.json overrides](https://docs.npmjs.com/cli/v11/configuring-npm/package-json#overrides)、[npm audit](https://docs.npmjs.com/cli/v11/commands/npm-audit)、[package-lock.json](https://docs.npmjs.com/cli/v11/configuring-npm/package-lock-json)
- Node CJS/ESM interop：[require(esm)](https://nodejs.org/api/modules.html#loading-ecmascript-modules-using-require)

事实等级：

- **已验证项目事实**：当前 lock、full audit JSON、当前 main/三个类/测试和 production readiness 代码。
- **已验证上游事实**：npm registry 元数据、官方源码、GHSA、Forge issues 和官方文档。
- **隔离解析事实**：三个候选 lock 与 audit；只证明解析和公告匹配。
- **项目建议**：Forge 8 alpha 的条件首选、desktop core readiness 和 B7-R1 顺序。
- **仍未验证**：Node 24 下的 clean install、Forge 8 + Vite 7 当前项目编译、真实 Windows package、native rebuild、managed child、owner HTTP、app.asar E2E 与 EXE smoke。

## 19. 交给总控决定的问题

1. 是否接受 Forge 8.0.0-alpha.10 只作为发布前 B7-R1 基线，并冻结“不允许正式发布”的退出条件？
2. 若不接受，是否确认 B7 继续 blocked，等待 beta/rc/stable，而不是建立本地安全 fork？
3. 是否接受新的 managed desktop core readiness 端点，同时保持通用 /readyz 的 provider 语义不变？
4. 若 F10 不接受，是否确认 P4-B managed online 暂停，不用 healthz 或假 provider替代？
5. 是否把“直接 Vite + Packager 20”保留为独立架构任务，而不是 B7-R1 自由回退？

总控冻结这些问题后，才应发布 B7-R1。D12 不自动创建 P4-IF-004、B7-R1 或 P4-C12。

## 20. review 检查表

- [x] 原始 16 项逐条列出 GHSA/CVE、包版本、级别、完整路径、阶段、产物、前提、修复和处置。
- [x] 比较五条路线并给出固定推荐与回退顺序。
- [x] 区分 tar 的 lock 解析、API 表面和真实 rebuild/package。
- [x] 核对 Packager 20 engine、ESM、hook API、Forge 7 假设与内部 extractor。
- [x] 给出精确候选图、workspace 设置和必须消失的包。
- [x] 给出 P4-IF-004-F01～F22。
- [x] 设计 main → Supervisor → owner → HostClient → modules 的真实组合和 Mermaid。
- [x] 给出 B7-R1 的顺序、文件类别、门禁、停止和交接边界。
- [x] 教学覆盖依赖、构建威胁、audit/利用、停止、风险工程、composition root 和 DI。
- [x] 明确候选尚未实现，未使用真实个人数据，未替独立测试下结论。

## 21. 交付文件与摘要口径

本任务只修改本文和技术顾问角色状态文件。完整文件不能真实地内嵌自己的最终 SHA-256，因为写入摘要会再次改变被摘要的字节；角色状态文件也有同样的自引用问题。为避免记录一个在写入瞬间就失效的值，完成时采用单向可复算链：技术顾问完成日志记录本文冻结后的完整文件 SHA-256，最终交付消息再记录角色状态文件完成后的完整 SHA-256。两项摘要都在文件停止修改后计算；总控可直接用 SHA-256 复算。没有另建不在授权范围内的 checksum 文件。
