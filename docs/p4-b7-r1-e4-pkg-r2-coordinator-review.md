# P4-B7-R1-E4-PKG-R2 总控核对：Windows package 与静态产物门禁

核对时间：2026-09-29，Asia/Shanghai

核对角色：头脑风暴总控

结论：接受 `P4-B7-R1-E4-PKG-R2` 的 `review / finished` 交付；真实 package 与全部静态产物门禁通过，允许对同一份不可变产物执行一次条件式 app.asar 与最终 EXE 动态门禁，不据此宣布 P4-B complete

## 1. 总控结论

总控确认此前围绕 pnpm、R0 和证据 driver 的循环已经结束。PKG-R2 没有重跑 Q1～Q6，而是复用总控已接受的真实预检证据，使用固定 `pnpm-native.exe` 与任务专属 PATH 执行了唯一一次真实 package。该进程退出码为 0，Forge 完成 system check、Vite production build、Windows x64 package 和 post-package hook。

本次通过只说明桌面应用可以从冻结源码和依赖生成结构正确、资源干净、production fuses 正确的 Windows package。app.asar、最终 `Maris.exe`、真实 sidecar 生命周期、owner 会话、模块发现和 recover 仍未动态验证，P4-B 尚未完成独立验收。

## 2. package 与静态产物证据

| 核对项 | 总控结果 |
| --- | --- |
| package 实际次数 | 1/1 |
| package 退出 | 0；未超时；约 10.3 秒 |
| package stdout/stderr | 摘要与原始日志一致；stderr 只有 pnpm lifecycle 命令回显 |
| 最终 package | 140 files，386,491,445 bytes |
| `Maris.exe` | 246,032,896 bytes；SHA-256 `149ccd6e2d71a8945ffef4ecba81e5121bc19c4816331ed5bcb6e72948174199` |
| `resources/app.asar` | 758,263 bytes；SHA-256 `c38cd0c7c5b42e4576d051f936d2942cd6a180b4386c62687a1886e991ae22f6` |
| production fuses | 冻结的前六项全部匹配 |
| Python resources | expected 67、actual 67；0 missing、0 extra、0 mismatch |
| app.asar | 18 entries、11 normal files、0 links、0 unpacked |
| 污染与隐私扫描 | 0 hits |
| staging/transition | 已清理，0 残留 |
| 任务进程 | 27 个 observed PID 全部退出，0 owned residual |

总控直接复算 `Maris.exe` 和 `app.asar`，摘要与报告一致。C 盘 `package-resume-2` 的 evidence manifest 含 40 个唯一条目，40/40 文件的长度与 SHA-256 均匹配；manifest SHA-256 为 `a082d25481adc94c61a50a0c96cc08cbfd141175c0adad85798e9157f274c01f`。

静态 reader 在同一份不可变 package 上经历三次读取逻辑纠正。原始错误和修正记录均被保留，没有重新运行 package，也没有修改产物。最终 v4 reader 退出 0，七项静态 gate 全部为 true。此类只读核对修正符合 PKG-R2 任务卡边界。

## 3. 仓库边界

执行方交付摘要与实际文件一致：

- `apps/desktop/b7-r1-e4-pkg-r2-source.sha256`：`04c2e344be3ffdf691a5062b9d623bd71c34016cfa365063e79b59c4a06b1dc1`
- `docs/b7-r1-e4-pkg-r2-running.md`：`e96f3ddbc41764fb187fe6371866534ed97ea97b6a37627e1b0d2720075150d2`
- `docs/coordination/agents/executor.md`：`2a2cbddb4cef6402460fa39ce14ad95b507a6a4ad4ec8ef85eb1e12ebc959896`

相对 240 文件起点，239 个文件保持不变，唯一变化是授权更新的执行智能体日志，另有两份授权新增交付。产品代码、测试、依赖、lock、Forge 配置、staging 实现、接口冻结和独立验收材料均未变化。执行智能体没有执行 Git 写操作。

## 4. 下一步边界

下一任务为 `P4-B7-R1-E4-DYN-R1`，直接复用本次不可变 package：

1. 不再运行 Q1～Q6、install、测试、build 或 package；
2. 先执行一次 packaged app.asar 门禁；
3. P1 完全通过后，才执行一次最终 `Maris.exe` 黑盒门禁；
4. 使用独立的虚拟数据库和隔离 profile，不读取真实账户、真实财务数据或全局 AppData；
5. 只调用冻结的 preload API，验证 runtime、owner、`daily_finance`、recover 和 bounded shutdown；
6. 任一级出现弹窗、crash、超时、秘密泄露或残留进程时立即停止，不在同一任务中修改产品或重跑该级；
7. P2 通过后才允许创建 P4-C12 独立验收任务。

本任务不会把当前简化界面解释成用户已经接受的财务驾驶舱。丰富仪表盘、消费记录管理、Agent 对话和财富管理属于 P4-C/P4-D 产品实现，仍需在 Shell 地基独立验收后开始。
