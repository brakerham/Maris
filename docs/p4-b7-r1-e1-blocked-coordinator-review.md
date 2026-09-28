# P4-B7-R1-E1 重复网络阻塞总控核对

核对时间：2026-09-27，Asia/Shanghai
核对角色：头脑风暴总控
结论：接受 `blocked / finished`；停止重复执行任务，等待网络条件变化

## 1. 接受的执行结论

E1 已关闭 R1 遗留的最终 lock 证据缺口：full 与 production-only audit 均为 0 critical/high，clean frozen install 前后 lock 摘要保持 `5ddc0a93d097e0e67c6fa7c48eef250bb5be6b18530f0871d620434ef93dcb4a`，冻结 F04 图、旧包消失、peer、exotic/file source 和 lifecycle 门禁全部通过。

Electron `44.4.5` 官方资产仍未取得。冻结 Node 24 的首个 GET 写入 31,817,728-byte 未校验 partial 后长期未完成；第二检查点在清理 partial 后返回 `TypeError: fetch failed`，底层 `cause.code=ECONNRESET`。执行智能体按 P0 停止，没有第三次重试、镜像、旧 binary、安全软件例外、产品修改或后续 Host 接线。

E1 source manifest 186/186 匹配，摘要 `fd40e4b2d609b998c255c5a33bb172d53d81a043c41c98fc91f01cd5c5afd5fe`。运行说明和执行角色摘要与交接一致。

## 2. 总控补充诊断

总控在 E1 之后执行了一次不落盘的官方资产 1 MiB Range GET。结果同样为：

```text
curl: (56) Recv failure: Connection was reset
http=000
bytes=0
```

这推翻了“只有 Node 24 fetch 有问题”的假设。当前事实是：

- GitHub release 页面和资产 HEAD 可达；
- DNS 成功；
- TLS 起点成功；
- Node 24 与 Windows curl 的正文传输都会遇到连接重置；
- WinINet 代理关闭；
- WinHTTP 为 direct access；
- 没有 HTTP/HTTPS/ALL_PROXY、Electron mirror 或 npm proxy 环境变量。

因此当前阻塞位于本机网络路径、上游网络策略或网络过滤层，不在 Electron package、Node 安装脚本、项目代码、lock 或缓存权限。

## 3. 官方支持的安全恢复路线

Electron 官方安装文档明确把 `ECONNRESET` 归类为网络问题，并建议切换网络、稍后重试或直接从 Electron GitHub Releases 下载。官方同时支持已有本地缓存；Windows 默认缓存位于 `%LOCALAPPDATA%/electron/Cache`，也可以通过 `electron_config_cache` 指向任务专用目录，缓存布局为 `[checksum]/[filename]`。

本项目后续只允许：

1. 在网络正文读取恢复后，从同一个 Electron 官方 GitHub Release URL 下载；
2. 核对归档 SHA-256 必须为 `11c395820a5aaa8ebcc0686b476d0ac98a730274ebfbdc8cf5538a7c2815cb5d`；
3. 把已校验官方 ZIP 放入任务专用 Electron cache；
4. 让 Electron 官方安装入口从该 cache 完成安装；
5. 继续 Vitest、Host 组合和后续门禁。

这不是第三方镜像，也不是绕过校验。禁止把未校验 partial、浏览器未知下载、旧 package binary 或第三方缓存作为输入。

## 4. 当前停止点与解除条件

现在不创建 E2 Prompt，不让执行智能体再次下载。用户需要先完成以下任一网络条件变化：

- 切换电脑到另一条网络，优先手机热点；或
- 启用用户平时用于稳定访问 GitHub Releases 的可信系统代理。

用户告知网络已经切换后，由头脑风暴总控先运行一次不落盘的 1 MiB 官方 Range GET。只有返回成功且取得预期字节，才生成 E2 固定快照和执行任务卡。

如果替代网络上的正文测试仍被重置，则停止 Electron 开发续段，转为单独的本机网络/安全软件诊断，不再消耗执行智能体开发轮次。

P4-C12 继续 `not_started`。
