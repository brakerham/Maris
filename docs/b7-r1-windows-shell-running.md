# P4-B7-R1 供应链续段运行说明与阻塞交付

- 任务：`P4-B7-R1`
- 角色：执行智能体
- 状态：`blocked / finished`
- 依据：`P4-IF-003`、`P4-IF-004`、P4-D12 与 R1 任务卡
- 停止时间：2026-09-27，Asia/Shanghai
- 最终结论：Forge 8 候选依赖图、旧包消失检查和候选锁文件的 full/prod audit 已通过；clean frozen install 与 generated/typecheck/lint 已通过。Electron `44.4.5` 官方资产在测试自动获取和显式官方安装两个连续检查点都返回 `TypeError: fetch failed`，且没有生成 `node_modules/electron/dist/electron.exe`。任务卡把同一问题连续两个检查点无有效新输出定义为 P0，因此本任务在 Host 接线前停止，没有改动 desktop sidecar、readiness、composition root 或运行时产品代码，也没有启动 P4-C12。

## 1. 起点与职责边界

开始前按任务卡顺序读取协调入口、最新 control、执行角色状态、两个接口冻结、B7 受阻交付、D12、总控审阅、固定输入和本任务卡。

两层起点门禁均通过：

| 门禁 | 结果 |
| --- | --- |
| `docs/coordination/snapshots/p4-b7-r1-start.sha256` | 182 matched、0 mismatch、0 missing；清单自身 SHA-256 `18ce1e965ea1fca41587a839b4dfff4a2671813315411c3ec4e4a07a9029441a` |
| `apps/desktop/b7-source.sha256` | 66 matched、0 mismatch、0 missing；清单自身 SHA-256 `de1f80c566faf165d7869bb4641477b3743bea80b72c65f137079e0f3993352a` |

本轮只修改依赖声明、workspace 安全配置、lock、供应链证据、运行说明、source manifest 和执行角色日志。没有修改 migration、Finance、Agent、pending、memory、activity import、`tests/independent/**`、矩阵、独立报告、control、overview、其他角色状态或 `.claude/**`；没有运行独立测试或执行 Git 写操作。

## 2. 精确项目本地工具

工具只放在工作区忽略目录 `.b7-tools`，使用绝对路径调用，没有修改系统 PATH、全局 npm、用户 profile 或系统安装。命令进程内临时 PATH 只用于让 npm scripts 找到同一份 portable Node/pnpm，结束后不持久化。

| 工具 | 来源与验证 | 实际版本 |
| --- | --- | --- |
| Node.js Windows x64 ZIP | `nodejs.org/dist/v24.21.0`；官方 `SHASUMS256.txt` 匹配 SHA-256 `158f7685b44de51f6c0df1d153526cbcd3e1bc739a8dfc607721cef75de9e541` | `v24.21.0` |
| pnpm package | `registry.npmjs.org/pnpm/-/pnpm-12.7.0.tgz`；registry SHA-512 integrity 匹配；包内 `package.json` SHA-256 `9bdc25a9aeca0318030cc4532572938e0b3a6d9d70a6ed8ec04f4e0f26c0c9d6` | `12.7.0` |

没有切换非官方 Node、pnpm 或 Electron 镜像，没有关闭安全软件或添加排除项。

## 3. Forge 8 候选图

直接依赖已按冻结值更新：四个 Forge 包全部为 `8.0.0-alpha.10`，`@electron/fuses` 为 `2.0.0`；Node、pnpm、Electron、React、TypeScript、Vite 和 React Router 保持冻结版本。workspace 继续使用 hoisted、strict peers、关闭 auto peer、阻止 exotic subdeps，并只允许 `electron` 和 `esbuild` 生命周期脚本；旧 Electron node-gyp 本地 override 已移除，`tar` 精确 override 为 `7.5.21`。

第一次 clean lockfile-only 正确触发 strict peer 失败：`@testing-library/react@16.3.3` 与 `@testing-library/user-event@14.6.7` 都需要显式 `@testing-library/dom`。没有降低 strict peer 或开启 auto peer；从 npm 官方 registry 核对后，增加精确 `@testing-library/dom@10.4.2`，第二次从空 lock 解析通过。

候选图精确命中：

| 包 | 唯一 resolved 版本 |
| --- | --- |
| `@electron/packager` | `20.3.0` |
| `@electron/rebuild` | `4.2.0` |
| `node-gyp` | `12.4.0` |
| `tar` | `7.5.21` |
| `@electron-internal/extract-zip` | `1.0.5` |

锁文件、`pnpm list` 和 `pnpm why` 证明以下条目均不存在：Packager 18.4.4、`extract-zip@2.0.1`、Rebuild 3.7.2、Electron node-gyp 10.2.0 fork、任何低于 7.5.21 的 tar、`tmp@0.0.33`、Git/exotic/file vendor 来源。旧 vendor tarball仅在 lock 已确认不再引用后删除。

[依赖图证据](../apps/desktop/b7-r1-dependency-graph.json)记录明确边、策略和摘要。安装后的 depth-30 JSON 依赖图为 639313 bytes，SHA-256 `390253e44cfa8c615306a2c9690ab1b10f308235432fc356f26d3f3a93db39e1`；该临时完整图在资源收口时删除。安装日志没有 deprecated transitive warning，已安装 package manifest 扫描也未发现 deprecated 字段，因此本候选记录为 0 个 deprecated transitive。

## 4. 审计与 clean install

候选 lockfile-only SHA-256 为 `af0da9c6d57ee3fc2c901afa111d22fdb21c591b9bcf2cefb42822d6d2f17b88`。该候选上的审计结果：

| 审计 | exit | critical | high | moderate | low | 原始 JSON SHA-256 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| full `--audit-level high` | 0 | 0 | 0 | 0 | 0 | `d20129a79a7582e655a88d5fc089251f59c4fb61d5234ee028cf8000fa0c27ac` |
| production-only `--audit-level high` | 0 | 0 | 0 | 0 | 0 | `4c15eda170c34a4224755da68f3bea1320dd4bf7adebd3577d09154a929988c3` |

随后从不存在项目 `node_modules` 的状态执行 `--frozen-lockfile`，下载 274 个解析项、安装 275 个 package，退出 0。实际执行的 lifecycle 只有允许名单内的 `esbuild postinstall`；Electron 44.4.5 当前 package 没有自动 install script，未出现新 install script、Git/exotic dependency 或未知应用 native helper。

pnpm 的 package-manager 管理在 frozen install 后把原始锁中也存在的 `@pnpm/exe@12.7.0` package-manager dependency 补回 lock；最终 lock SHA-256 因而为 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`。这是 pnpm 工具自身的既有固定 dependency，不改变 Forge F04 图。由于 Electron 官方资产随后连续失败并触发 P0，任务按规则停止，没有用第三次外部操作重跑最终 lock audit；因此上述两个 0 漏洞结果严格绑定候选 audit lock，而不被描述成停止后最终 lock 的新审计证据。

## 5. 静态门禁与原始失败

| 检查 | 结果 |
| --- | --- |
| clean candidate lock + strict peers | 通过；首次缺 peer 失败已通过显式精确依赖修正 |
| forbidden/exotic/file source scan | 通过；旧六类依赖与 vendor source 均为 0 |
| clean frozen install | 通过；275 packages；只执行 `esbuild` allowlisted lifecycle |
| OpenAPI `check:generated` | 通过；schema 与 TypeScript 生成物匹配 |
| TypeScript | 通过，退出 0 |
| desktop lint | 通过，退出 0 |
| Vitest | **未通过**；8 files passed、1 suite failed；15 tests passed；失败发生在测试导入 Electron 时自动下载 binary，错误为 `TypeError: fetch failed` |

Vitest 首次失败后没有改测试、skip/xfail 或放宽断言。按任务卡重新读取 control 并使用外部网络权限显式运行 Electron 44.4.5 官方安装入口；没有设置 `ELECTRON_MIRROR` 或 `npm_config_electron_mirror`。第二次仍得到同一个 `TypeError: fetch failed`，`node_modules/electron/dist/electron.exe` 仍不存在。package 自带 checksums 指定 `electron-v44.4.5-win32-x64.zip` 的官方 SHA-256 为 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d`，但没有下载到可供核验的归档。

这两个连续检查点没有有效新输出，符合任务卡 P0 停止条件。执行方没有改用上轮使用过的第三方镜像、没有从旧 package 复制 Electron binary、没有把 8/9 test files 当作全绿，也没有继续 Forge package、Host 接线或运行时验证。

## 6. 未执行范围

因 P0 在里程碑 3 出现，以下全部保持 `not_run / unverified`：

- desktop core readiness、`desktop_sidecar.py` 和 Python sidecar handshake；
- `BackendSupervisor` single-flight、health loop、cleanup 和恢复预算返修；
- OwnerSecretStore、OwnerAuthClient、LocalOwnerSession、HostClient 和唯一 composition root；
- Python 定向测试、managed Uvicorn smoke；
- Forge 8 Windows package、Packager 20 hooks、fuses、app.asar E2E；
- 真实 `Maris.exe` startup/owner/modules/recover/Tray quit/owned child cleanup smoke；
- package 内 secret、token、个人数据和更新 URL 扫描。

因此本交付不能提交为 `review`，不能证明 main 已真实接线 Host，也不能启动 P4-C12。

## 7. 文件结果与摘要

相对 182 文件起点，停止点在生成最终 source manifest 前为 178 unchanged、3 changed、1 intentionally removed；另有依赖图、本文和最终 source manifest 三份 R1 证据文件。唯一删除项是已不再被 lock 引用的：

```text
apps/desktop/vendor/electron-node-gyp-06b29aafb7708acef8b3669835c8a7857ebc92d2.tgz
```

当前核心文件：

| 文件 | SHA-256 |
| --- | --- |
| `apps/desktop/package.json` | `a0a53625999fb43bc0e338a877fb579dea8f1933959a1bf46f108705828c7e48` |
| `pnpm-workspace.yaml` | `fd1cba09a8ded0d5625cf04c18668eb15088903bd870c57ebe941430f6deb6fd` |
| `pnpm-lock.yaml` | `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a` |
| `apps/desktop/b7-r1-dependency-graph.json` | `532f626426d04d8e99217b28bb9b14b1938b65c62b7c7742cfa5bab2d9681fdf` |

`apps/desktop/b7-r1-source.sha256` 采用与起点相同的逐行 `relative/path<TAB>sha256` 格式，按 ordinal 路径排序，不递归包含自身。它覆盖所有仍存在的起点项目文件以及本轮依赖图；执行证据文档和角色日志不作为产品 source 输入，工具、cache、`node_modules`、package/out、测试 profile、trace、临时日志和 `.claude/**` 也全部排除。清单为 182 entries，自身 SHA-256 为 `512439d5cb9f75d4d20722dd0bc8c634dc303650be1b4a12e8ddac39060691c9`。

## 8. 资源收口

- 本轮没有成功启动 Electron、Maris、Python sidecar、Uvicorn、Docker、PostgreSQL、OpenClaw、微信或 DeepSeek。
- 停止检查时没有 Electron 或 Maris 进程；没有本任务 child、端口、窗口或 Tray。
- `node_modules`、`.b7-tools` 内的 Node/pnpm、store、audit JSON、完整依赖图、下载和 temp 在证据写入后删除；预先存在的根 `.pnpm-store` 不归本任务所有，保持原状且不把它计作本轮清理成功。
- 没有读取真实密钥、账户或个人财务数据；没有 Git 写操作。

## 9. 交回总控

本任务停为 `blocked / finished`。供应链 Forge F04 图与候选 audit 已取得有效证据，但完整里程碑不能完成，原因是 Electron 44.4.5 官方资产下载在正常受限环境和获准外部网络环境均失败。总控若要续跑，应在官方 Electron 发布源可达后发布新的恢复任务，并从固定 source manifest 重新核对；执行方不得自行使用非官方镜像或从旧 package 注入 binary。
