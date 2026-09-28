# P4-B7-R1-E2 Electron 官方资产网络门禁

- 核对时间：2026-09-27 21:47～21:50，Asia/Shanghai
- 核对角色：头脑风暴总控
- 结论：`passed`；允许创建 E2 续跑任务

## 1. 网络条件变化

用户开启了可信代理软件的 TUN 模式，并要求总控先确认实际状态，再恢复当前阶段。

只读系统证据显示：

- 存在名为 `Meta Tunnel` 的虚拟网卡；
- 虚拟网卡地址为保留测试网段 `198.18.0.1/30`；
- 指向 `198.18.0.2` 的 IPv4 默认路由 metric 为 `0`，优先于物理 WLAN 默认路由；
- Windows WinINet 系统代理仍关闭，WinHTTP 仍为 direct，代理环境变量仍未设置。

这组证据符合透明 TUN 路由，而不是应用级 HTTP 代理。E2 不需要修改 Git、npm、Windows 系统代理或永久环境变量。

## 2. 限量正文门禁

目标保持为 Electron 官方 GitHub Release：

```text
Electron v44.4.5 / electron-v44.4.5-win32-x64.zip
```

总控只请求字节范围 `0-1048575`，输出丢弃，不把归档或临时签名 URL写入项目。

第一次在 Codex 受控沙箱内启动 Windows curl 时，Schannel 在正文请求前返回 `SEC_E_NO_CREDENTIALS`。该错误发生在沙箱的 Windows TLS 凭据初始化阶段，`HTTP=000`、`BYTES=0`，不作为 TUN 正文失败结论。

按沙箱规则使用完全相同的限量请求在沙箱外复验，结果为：

```text
HTTP=206
BYTES=1048576
TIME=3.108436
SPEED=337332
SSL_VERIFY=0
```

未记录重定向后的临时签名 URL、代理节点、凭据或个人网络标识。

## 3. 裁定

此前 Node 24 与 Windows curl 的正文 `ECONNRESET` 阻塞在当前 TUN 网络条件下已经解除。E2 可以从官方 Electron 安装与完整 SHA-256 校验继续。

当前 TUN 配置已通过正文门禁，不要求用户切换 GVisor/System/Mixed 栈、启用严格路由或调整 MTU。完整下载若再次失败，执行方只能按 E2 的两个检查点规则提交新证据，不得自行修改系统网络、镜像、安全软件或永久代理设置。
