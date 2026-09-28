# P4-B7-R1 阻塞交付总控核对

核对时间：2026-09-27，Asia/Shanghai
核对角色：头脑风暴总控
结论：接受 `blocked / finished` 结论；保留供应链成果，发布 `P4-B7-R1-E1` 恢复任务

## 1. 结论

执行智能体在 Electron `44.4.5` 官方 Windows x64 资产连续两个检查点返回 `TypeError: fetch failed` 后，按 P4 停止规则结束任务。停止行为正确：没有改用第三方镜像、复制旧包二进制、降低审计、跳过失败测试或继续 Host 接线，也没有启动 P4-C12。

本次失败不构成依赖版本不存在或产品实现缺陷。总控随后只读确认：Electron 官方 `v44.4.5` release 和 `electron-v44.4.5-win32-x64.zip` 均存在；本机 `curl` 跟随 GitHub 官方重定向得到 HTTP 200，本机 Node `fetch` 对同一资产也得到 HTTP 200。该结果只证明当前链路恢复，不替代任务规定的 Node `24.21.0`、官方校验下载、完整安装和运行测试。

因此不修改 P4-IF-004、不更换 Electron 版本、不返回技术顾问。下一步由原执行智能体从固定停止现场恢复。

## 2. 接受的有效成果

- 原 R1 起点 `182/182` 匹配；旧 B7 source manifest `66/66` 匹配。
- Node `24.21.0` 与 pnpm `12.7.0` 使用项目本地官方来源并核对摘要。
- 四个 Forge 包统一为 `8.0.0-alpha.10`，`@electron/fuses` 为 `2.0.0`。
- 明确补齐 `@testing-library/dom@10.4.2`，未放宽 strict peer。
- Packager `20.3.0`、Rebuild `4.2.0`、node-gyp `12.4.0`、tar `7.5.21`、internal extract `1.0.5` 精确命中。
- Forge 7 旧包、`extract-zip@2.0.1`、旧 rebuild/node-gyp、旧 tar、`tmp@0.0.33` 和 vendor file source 已从候选图消失。
- 候选 lock 的 full/prod audit 均为 0；clean frozen install、generated drift、TypeScript 和 lint 通过。
- R1 source manifest 为 `182/182` 匹配，摘要 `512439d5cb9f75d4d20722dd0bc8c634dc303650be1b4a12e8ddac39060691c9`。
- 进程、下载工具、任务内 store、`node_modules` 和临时证据已经安全收口；没有启动其他外部集成。

## 3. 仍未关闭的门禁

候选审计 lock 摘要为 `af0da9c...17b88`，停止时最终 lock 摘要为 `5ddc0a93...dcb4a`。已有两份零漏洞审计只能绑定候选 lock；恢复任务必须对最终 lock 重新运行 full/prod audit，不能继承候选结论。

Vitest 本轮结果是 8 个文件和 15 个测试通过、1 个 suite 在导入 Electron 时失败，不能表述为全绿。以下范围仍是 `not_run / unverified`：

- desktop sidecar 与 desktop core readiness；
- Supervisor、owner session、HostClient 和唯一 composition root；
- Python 定向回归与 managed Uvicorn smoke；
- Forge package、Packager 20 hooks 和 fuses；
- app.asar E2E 与真实 `Maris.exe` 冒烟；
- package 隐私检查和 P4-C12 独立验收。

## 4. 当前连通性证据

总控只做了不下载正文的 HEAD 检查：

- GitHub 官方资产经过重定向后返回 HTTP 200；
- 最终主机为 GitHub 官方 release asset 主机；
- 本机 Node `v26.8.1` 的 `fetch` HEAD 返回 200。

没有把临时签名 URL、token 或下载正文写入项目。Node 26 结果仅用于区分“官方资产不存在”和“执行时临时链路失败”；执行恢复仍必须使用冻结的 Node `24.21.0`。

## 5. 恢复决定

发布 `P4-B7-R1-E1`，仍由既有执行智能体唯一负责。恢复顺序固定为：

1. 复算 E1 固定输入和 R1 source manifest；
2. 恢复精确项目本地工具链；
3. 对停止时最终 lock 重新执行 full/prod audit；
4. clean frozen install 并确认 lock 不漂移；
5. 仅从 Electron 官方源获取 `44.4.5` Windows x64 资产并核对 SHA-256；
6. 完整复跑 Vitest；
7. 只有上述门禁全过，才继续 desktop readiness、真实 Host 组合、package、E2E 与 EXE 冒烟。

若同一 Electron 下载问题再次连续两个检查点无新信息，任务仍须停止并提交底层 `cause.code`、DNS/TLS/redirect 阶段等脱敏诊断；不得换镜像或反复盲重试。

P4-C12 继续 `not_started`。
