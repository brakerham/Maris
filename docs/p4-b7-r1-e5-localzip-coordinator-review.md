# LOCALZIP 总控审阅与 P4-C12 交接

- 角色：头脑风暴总控。
- 审阅时间：2026-10-01 13:04，Asia/Shanghai。
- 结论：接受 LOCALZIP 的实现、自测、真实 package 与最终 EXE 门禁作为 P4-C12 稳定输入。LOCALZIP 与整体 P4-B 保持 `review`，尚未独立验收，不宣布 `complete`。
- 下一任务：既有测试智能体执行 [P4-C12](coordination/prompts/p4-c12-windows-shell-tester.md)。执行智能体与技术顾问停止。

## 实际复算结果

总控只读核对代码、原始结构化结果和清单，没有重复安装、测试、package 或启动产品。

| 核对对象 | 本轮总控实际结果 |
| --- | --- |
| LOCALZIP 外部 evidence | 115/115 匹配，长度与 SHA-256 均一致 |
| 仓库八项交付 | 8/8 匹配，长度与 SHA-256 均一致 |
| LOCALZIP source 清单 | 274/274 匹配 |
| 270 项起点边界 | 267 unchanged、3 authorized changed、0 missing |
| 当前真实 package out | 140/140 匹配；0 extra、0 missing |

三项起点变化严格为 Forge 配置、package wrapper 和执行角色日志；五项新增为 ZIP helper、声明、专属测试、运行说明和 source 清单。没有发现产品运行代码、依赖、lock、独立测试或其他角色文件变化。

| 清单 | 普通 SHA-256 |
| --- | --- |
| 外部 `evidence-manifest.sha256` | `8de482784b4506419d6eb5629176fca89ffe51be945287ba1b6272207bc310da` |
| 外部 `repository-delivery.sha256` | `64a572deb04c81e82adb4b369579037b4d036cdb759078acae4246d5995461a2` |
| 仓库 LOCALZIP source | `b1d5aa03b6f59c22ecfe8b84c85256e832d5b8664343f7a80cf1cd9621524ad0` |
| 执行运行说明 | `d08e8529a47a5c2b0134be2be78ac081ac6a3fb7147150af27252d5414001c04` |

外部证据根：`C:\MarisE5Final\E5-PKG-FINAL-20260929-1732\localzip-resume-1`。该目录及旧 profile 只读保留，凭据、数据库和运行身份不复制到仓库。

## 实现与实际运行证据

已核对构建入口：未设置 `MARIS_ELECTRON_ZIP_DIR` 时保留常规路径；显式设置时先验证绝对路径、普通目录/文件、固定文件名、长度和流式 SHA-256，再进入 staging 和 Forge。本地模式使用 `electronZipDir`，不设置 `download`。没有依赖新增、校验关闭、代理修改或生产 fuse 放宽。

执行方定向 ZIP/package/toolchain 测试为 30 passed，TypeScript、lint 和真实 ZIP/config 验证通过。总控没有把这些结果当作独立验收。

唯一 package 为 1/1，12,701 ms、exit 0。最终受验对象：

| 对象 | 字节数 | SHA-256 |
| --- | --- | --- |
| `Maris.exe` | 246032896 | `f5cf7ad3b4d89a02cca925152ec8d7b5554ccba6ebff025bf04eb24195405641` |
| `resources/app.asar` | 758341 | `bcdf6f889a5be95d7270fb249db8eff45b1421a5fdd7879d2342cb333d7f1274` |

实际产物位于 `C:\MarisE5Final\E5-PKG-FINAL-20260929-1732\workspace\apps\desktop\out\Maris-win32-x64`。140 项产物及 67 项 Python resources 静态门禁通过，fuses V1 前六项保持 48/49/48/48/49/49，禁止污染扫描零命中。

最终 EXE 使用 Node direct spawn（shell false），Playwright 只附加 loopback CDP。唯一动态运行 34,796 ms、exit 0、没有超时或强制清理。原始 result 的 19 个 gates 全部 true，failure null、success true；恢复调用恰好一次。

总控核对到恢复前后均为 online/managed/authenticated，唯一 enabled 模块为 `daily_finance`，Profile 为 `daily_finance.assistant@1`。主窗口与毛毛窗口各一个，preload/renderer 隔离、毛毛状态与 openMain、隐私和退出后进程/监听/窗口清理均有结构化通过证据。

## 保留的限制和 warning

1. raw runner 的 task/schema 沿用 E5-FINAL 标签；当前 prelaunch、code map、closeout、时间窗和 classification 均指向本次 LOCALZIP，同一 EXE/asar 摘要一致。保留原始记录，不改标签覆盖历史，也不为标签重启产品。
2. 新测试最初 TypeScript 可选字段收窄错误、两次 source-reader 基线选择错误已有原始记录；最终静态结果通过，不构成产品失败。
3. 用户级 Git ignore 读取权限与 LF/CRLF 提示保持为环境 warning。
4. Tray 为产品树退出后的零残留推断，尚不等于真实 Tray 菜单操作验收。多屏、注销、开机启动及完整主题/无障碍仍须按矩阵独立取证；不能用本次 19 gates 覆盖全部 24 个矩阵案例。
5. 原 fetch failure 的实际 URL/代理原因仍为 unverified；本次本地 ZIP 成功解决受验构建入口，不宣称系统网络已修复，也不宣称所有第三方工具完全离线。
6. Forge alpha、unsigned package、外部已验证 Python 仍是发布前限制，不构成正式可分发产品。

## 下一步及 Git 口径

绑定 [C12 固定起点](coordination/snapshots/p4-c12-windows-shell-start.sha256)，复用原 24 个 P4-B ID。测试方独立编写案例并区分自动、人工、历史执行方证据；不重做矩阵，不重复 package，不重跑 P0～P3/Host 全量，不要求微信扫码。

本轮本地 Git 保存为明确的 `checkpoint`，保留尚未独立接受的交付与 C12 任务，默认不推送。C12 独立证据经总控核对后再决定 P4-B complete。

真实前端提醒门禁继续有效：P4-C Prompt 创建前主动提醒用户，复核两张参考效果图、组件/数据合同、截图验收和届时的模型分工，不把 Shell 占位页作为最终设计。
