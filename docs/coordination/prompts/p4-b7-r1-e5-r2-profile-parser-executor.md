# P4-B7-R1-E5-R2：同步 canonical Profile 解析器并完成最终门禁

## 唯一目标

你是既有执行智能体，唯一负责 `P4-B7-R1-E5-R2`。E5-R1 已把 daily finance contribution 和三个 fixture 改为真实 Profile `daily_finance.assistant@1`，随后发现桌面 `registry.ts` 的旧 Profile 正则不接受 Python Host 已冻结的 `module.local@major` 语法。

本任务只修 `P4-E5-PROFILE-PARSER-002`，保留 E5-R1 的正确改动，完成静态/执行方回归、一次新 package 和一次最终 EXE 黑盒验证。全部通过后停在 `review / finished`；真实产品或门禁失败则安全收口为 `blocked / finished`。不得启动 P4-C12、测试智能体、技术顾问或高保真前端开发。

## 开工前必读

按 `AGENTS.md` 顺序读取：

1. `README.md`
2. `docs/project-coordination.md`
3. `docs/coordination/README.md`
4. 最新 `docs/coordination/control.md`
5. `docs/coordination/agents/executor.md`
6. 本任务卡
7. `docs/p4-b7-r1-e5-r1-blocked-coordinator-review.md`
8. `docs/b7-r1-e5-r1-module-contract-running.md`
9. `docs/p4-b7-r1-e5-final-blocked-coordinator-review.md`
10. `docs/phase-4-d11-windows-shell-technical-advice.md` 第 1.1、5 和 5.1 节
11. `docs/phase-4-interface-freeze-003.md` 第 5 节
12. `src/wife_system/host/contracts.py` 中 `CANONICAL_ID_PATTERN` 与 `canonical_parts()`
13. `docs/coordination/snapshots/p4-b7-r1-e5-r2-start.sha256`

逐行复算固定快照。最新 control 若不再分配本任务，立即停止。开始时确认 Git index staged paths 为 0；`.claude/`、`.pnpm-store/`、旧 E4/E5/E5-R1 C 盘现场、package、profile、数据库和 evidence 全部只读。

## 已确认事实

- Python canonical Profile 语法是：

  ```text
  ^[a-z][a-z0-9_]{0,63}\.[a-z][a-z0-9_]{0,63}@(0|[1-9][0-9]*)$
  ```

- `daily_finance.assistant@1` 是真实、已冻结的 Profile。
- E5-R1 的 contribution 与三个 fixture 修改方向正确，必须保留。
- 当前桌面旧正则 `^[a-z][a-z0-9_.-]{0,139}$` 拒绝 `@major`，还错误接受连字符、多个点和无版本形状。
- E5-R1 的定向 Vitest 为 3 passed、3 failed；三个失败都发生在 Zod Profile parse，package 与最终 EXE 均为 0 次。
- E5-FINAL 已证明最终 EXE 直接 `spawn(shell:false)`、managed Host、owner、双窗口、安全隔离与自然退出路线有效；不返回 Playwright Electron launcher。

## 仓库修改范围

允许修改：

- `apps/desktop/src/modules/registry.ts`
- `apps/desktop/src/modules/daily-finance/contribution.ts`，只保留或在必要时格式化 E5-R1 已有真实 Profile 修改，不扩大业务
- `apps/desktop/tests/unit/registry.test.ts`
- `apps/desktop/tests/unit/composition-root.test.ts`
- `apps/desktop/tests/unit/host-client.test.ts`
- 如现有组织确实需要，可新增一个只覆盖 canonical Profile parser 的执行方单元测试；不得复制一套平行 registry
- 更新 `docs/coordination/agents/executor.md`
- 新建 `docs/b7-r1-e5-r2-profile-parser-running.md`
- 新建 `apps/desktop/b7-r1-e5-r2-source.sha256`

禁止修改 Python Host、认证、Supervisor、IPC、preload、renderer 页面、依赖、lock、Forge、staging、migration、接口冻结、独立测试、control、overview、其他角色或 Git 状态。

## 精确实现合同

1. `profileId` 的 TypeScript 正则必须与 Python `CANONICAL_ID_PATTERN` 语义一致：

   ```ts
   /^[a-z][a-z0-9_]{0,63}\.[a-z][a-z0-9_]{0,63}@(0|[1-9][0-9]*)$/
   ```

2. 不使用 `\d`、Unicode flag、trim、lowercase、normalization、split 后容错或隐式默认 major。
3. 不增加 `daily_finance.default` alias、fallback 或自动迁移；旧形状必须 fail closed。
4. 不修改 `intersectModules()` 的精确相等、major、API prefix、setting version 或全局冲突逻辑。
5. E5-R1 的 production contribution 与 Host fixture 继续使用 `daily_finance.assistant@1`。

## 必需执行方测试

在 registry 相邻测试中证明：

- 接受 `daily_finance.assistant@1`；
- 接受 `a.b@0`；
- module 和 local 各 64 字符时接受，各 65 字符时拒绝；
- 拒绝缺少 `@major`、`@01`、负数、小数、多个 `@`、连字符、多个点、大写、前后空白、全角点/全角 `＠`；
- 旧 Profile 只出现在动态构造的反例中，`apps/desktop/src` 与 `apps/desktop/tests` 对 `daily_finance.default` 字面量仍为 0 命中；
- 真实 Profile 求交加载 `daily_finance`，旧形状、module major 不兼容、缺少 API prefix 和 setting version 不兼容均返回空交集；
- extra field 和全局 module/Profile/route/setting/appearance 冲突继续原子拒绝；
- composition root 用 production 同形 Host 摘要只公开 `daily_finance`；
- HostClient 的严格 DTO、401 single-flight refresh/retry、session revoke 和额外字段拒绝保持原断言。

不要写只重复正则源码的脆弱字符串测试；测试必须通过公开的 `compileRegistry()`/`intersectModules()` 行为。

## 静态与执行方回归

在 package 前依次完成：

1. 修改文件格式与 `git diff --check`；
2. OpenAPI generated drift；
3. TypeScript `tsc --noEmit`；
4. desktop lint；
5. registry、composition root、HostClient 定向 Vitest；
6. desktop 完整 Vitest；
7. desktop sidecar/module 相关 Python 定向测试；
8. Python `compileall` 和 `pip check`；
9. `rg` 确认旧别名字面量为 0，正确 Profile 位于 production contribution 与合同 fixture。

产品断言失败时停止，不进入 package。尚未启动 package 或产品时，命令拼接、证据文件名、临时目录父级、权限或测试 runner 编排错误可以记录后就地修正一次；不得删除测试、降低断言、增加 skip/xfail、修改系统环境或把 collect-only 写成通过。相同编排错误连续两个检查点没有新信息时停止并报告。

## 新 C 盘构建现场

E5-R1 的 `C:\MarisE5R1\E5-R1-20260929-0813` 与所有旧 E4/E5 现场保持只读。创建全新的：

```text
C:\MarisE5R2\E5-R2-<timestamp>
```

要求：

- 从当前固定 source 集复制，不能用旧 workspace 覆盖 R1/R2 修改；
- 复用已验证工具、Electron cache 与冻结依赖内容，不联网安装或升级；
- `pnpm-lock.yaml`、Node、pnpm、Electron dist 和依赖聚合摘要必须匹配已冻结值；
- workspace、out、profile、数据库与 evidence 全部 create-new；
- 不读取或复用旧 owner session、PID、端口、数据库或动态结果；
- 使用 PKG-R2 已通过的进程级 Node/pnpm PATH 配方，不修改用户或系统 PATH。

## 唯一 package

全部前置回归通过后执行现有 `pnpm run package` 一次，预算 1/1。package 失败、超时、崩溃、污染或残留时安全收口并停止，不得修改后第二次打包。

成功后只读验证：

- 新 `Maris.exe`、`resources/app.asar`、out 清单和 production fuses；
- app.asar 中 `daily_finance.assistant@1` 至少出现一次，旧别名字面量为 0；
- 67 项 Python resources 仍符合 H1 allowlist；
- `.pyc`、`.egg-info`、测试、task evidence、用户名/绝对工作区路径、凭据样式和私钥为 0 命中；
- staging、backup、lock 和 transition artifacts 已清理；
- source、lock、node_modules 与 Electron dist 无非授权漂移。

package 之后的只读 evidence 核对错误不消耗第二次 package 预算。保留原始错误，在不改变产物的前提下修正派生核对；若产物本身缺失或不符合合同则停止。

## 最终 EXE 单次黑盒复验

只有 package 与静态产物检查全部通过才进入。最终 EXE 动态预算 1/1，硬超时 120 秒；不预跑 app.asar、不运行 fixture、不重试。

沿用 E5-FINAL 已证明有效的直接路线：

- 固定 Node `child_process.spawn()` 直接启动新 package 的 `Maris.exe`；
- `shell:false`，返回 PID 精确对应新 EXE；
- 新隔离 profile、虚拟数据库、随机 owner marker、最终 resources 和已验证 Python；
- 动态非零 CDP 只监听 `127.0.0.1`；Playwright 只经 `connectOverCDP()` 观察；
- 不传 `--no-sandbox`，不启用 inspect，不改变 fuses。

依次验证：

1. 根进程、owned set、CDP、一个主窗口和一个毛毛窗口；
2. 两个 preload bridge、Node 隔离和未授权 API 缺失；
3. 首次 runtime 为 `online / managed / authenticated / errorCode=null`；
4. `modules.list()` 含且只含兼容 `daily_finance`，Host `profile_ids` 含 `daily_finance.assistant@1`；
5. 毛毛 `getState()` 是 daily finance 形态，`openMain()` 成功且不产生重复主窗口；
6. `runtime.recover()` 精确调用一次；恢复后 runtime 与 modules 仍通过；
7. DOM、storage、bridge、console、page error、crash event、Windows Application/Code Integrity 与日志隐私；
8. 产品现有 bounded shutdown，自然退出码 0；最终产品、sidecar、监听、窗口和 Tray 归零。

动态 runner 在产品启动前必须先对自己做静态语法与目标路径检查。产品启动之后的派生摘要、只读 evidence 或报告字段错误不允许重启产品；保留原始动态证据，在不改变产品运行事实的前提下离线修正派生核对。产品断言失败、崩溃、超时或资源无法收口则立即停止。

## 交付与状态

运行说明必须包含：

- `P4-E5-PROFILE-PARSER-002` 的代码位置、精确合同和修复；
- E5-R1 四项改动的保留情况；
- canonical 正反例与每组回归的 passed/failed/skipped/warning；
- package 真实次数、产物摘要、fuse/resource/污染检查；
- 最终 EXE 真实次数、每个动态门禁、recover 次数和资源收口；
- 起点/终点文件边界、逐文件 SHA-256 和新 source manifest；
- 新 C 盘 evidence 清单与复算算法；
- 独立验收、P4-C12、高保真前端、微信、DeepSeek 和个人数据仍未运行。

全部通过后提交 `review / finished` 并停止。不得自行宣布 P4-B complete，不得启动测试智能体或真实前端开发。
