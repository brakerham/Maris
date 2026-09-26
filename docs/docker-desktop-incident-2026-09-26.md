# Docker Desktop 启动故障记录与恢复计划

## 1. 文档目的

本文记录 2026-09-26 在 Windows 开发机上反复发生的 Docker Desktop 启动故障。它用于：

- 让头脑风暴、执行、测试和技术顾问共享同一份环境事实；
- 防止后续任务把 Docker 环境故障误判为项目代码、PostgreSQL、migration 或测试失败；
- 避免不同智能体反复执行重启、改名目录、启动容器或要求用户重复操作；
- 明确恢复 Docker 后需要满足的验证门槛，以及 P4 后续应从哪里继续。

本文不包含密钥、账号、个人财务数据或未脱敏的诊断包。

## 2. 当前结论

截至 `2026-09-26 21:50 Asia/Shanghai`：

- 本机安装的是 Docker Desktop `4.91.0.239619`。
- 当前没有 `Docker Desktop`、`com.docker.backend` 或诊断进程在运行。
- `dockerDesktopLinuxEngine` 命名管道不存在，Docker Engine 和 Compose API 均不可访问。
- Docker Desktop 启动时会在初始化内部服务阶段失败，错误集中在两个 Windows AF_UNIX socket：
  - `%LOCALAPPDATA%\Docker\run\sailor-ingest.sock`
  - `%LOCALAPPDATA%\docker-secrets-engine\engine.sock`
- 两种错误都表现为 Docker 尝试把现有 socket 改名为 `.stale` 时，Windows 返回 `The file cannot be accessed by the system`。
- 这与项目容器、PostgreSQL 数据、Alembic migration、FastAPI、DeepSeek、OpenClaw 和微信无关。故障发生在项目容器创建之前。
- 当前最符合证据的机制是：Docker Desktop 非正常退出后，Windows 上的 AF_UNIX socket 留下不可正常覆盖或删除的 ReparsePoint；下次启动时 Docker 的 socket 清理失败，导致 Desktop 后端在内部服务初始化阶段退出。
- 该根因判断置信度较高，但最终厂商级根因仍应以 Docker 官方修复或支持结论为准。

因此，当前应把它记录为**本机 Docker Desktop 环境阻塞**，不记录为 P4 产品缺陷，也不继续让执行智能体无期限重试。

## 3. 用户界面中看到的错误

### 3.1 Ingest Server

Docker Desktop 弹窗显示：

```text
starting services: initializing Ingest server: listening on
unix://C:/Users/xuhaolin/AppData/Local/Docker/run/sailor-ingest.sock:
rename C:/Users/xuhaolin/AppData/Local/Docker/run/sailor-ingest.sock
C:/Users/xuhaolin/AppData/Local/Docker/run/sailor-ingest.sock.stale:
The file cannot be accessed by the system.
```

### 3.2 Secrets Engine

另一次启动显示：

```text
starting services: initializing Secrets Engine: listening on
unix://C:/Users/xuhaolin/AppData/Local/docker-secrets-engine/engine.sock:
rename C:/Users/xuhaolin/AppData/Local/docker-secrets-engine/engine.sock
C:/Users/xuhaolin/AppData/Local/docker-secrets-engine/engine.sock.stale:
The file cannot be accessed by the system.
```

两个错误不是两项独立的项目故障。它们属于同一类 Docker Desktop 内部 socket 生命周期问题，只是失败发生在不同内部服务。

## 4. 已确认的环境事实

| 项目 | 当前证据 | 结论 |
| --- | --- | --- |
| Docker Desktop 版本 | `4.91.0.239619` | 已确认 |
| Docker client/历史 Engine 版本 | client `29.8.0`；此前恢复窗口中 server `29.8.0` | 已确认 |
| Docker context | `desktop-linux` | 已确认 |
| Desktop/backend 进程 | 当前不存在 | 已确认 |
| `dockerDesktopLinuxEngine` 管道 | 当前不存在 | 已确认 |
| `%LOCALAPPDATA%\Docker\run` | 当前目录存在 | 已确认 |
| `%LOCALAPPDATA%\docker-secrets-engine` | 当前目录存在 | 已确认 |
| 项目容器是否在本轮成功启动 | 没有 | 已确认 |
| Compose 最终空列表 | Engine 不可达，因此本轮无法查询；操作系统未发现 Docker 后端 | `unverified` |
| 项目数据是否导致启动失败 | 错误发生在内部服务初始化和项目容器创建之前 | 已排除为直接原因 |

## 5. 故障发展过程

### 5.1 第一次复现与临时恢复

1. Docker Desktop 在 `sailor-ingest.sock` 处启动失败。
2. 停止 Docker Desktop、backend 和 diagnostics 进程，并执行 `wsl --shutdown`。
3. 将 `%LOCALAPPDATA%\Docker\run` 改名为带时间戳的保留目录。
4. 再次启动后，失败位置转移到 `docker-secrets-engine\engine.sock`。
5. 用户在管理员 PowerShell 中同时隔离当前 `Docker\run` 和 `docker-secrets-engine` 两个父目录，然后重新启动 Docker Desktop。
6. Docker Desktop 临时恢复，Engine `29.8.0` 可访问，项目 Compose 服务列表为空。

### 5.2 临时恢复期间完成的项目工作

在 Docker Engine 可用的窗口内，`P4-B6-R2-S2` 已取得以下真实 PostgreSQL 证据：

- 新增 R2 PostgreSQL：`9 passed`；
- Finance PostgreSQL：`4 passed`；
- activity import PostgreSQL：`10 passed`；
- Host R1 PostgreSQL：`7 passed, 1 failed`。

Host R1 唯一失败已诊断为测试时钟问题：测试用固定时间创建十分钟有效的绑定码，HTTP 路由却读取真实时间，导致两枚码在进入并发 INSERT 前都已过期。它不是 PostgreSQL 产品并发缺陷。

### 5.3 T1 修复后 Docker 再次不可用

`P4-B6-R2-S2-T1` 已完成单测试文件的可控时钟修复，并通过编译与 pytest 收集检查。随后执行方准备运行真实 PostgreSQL 时：

- 连续两个检查点都找不到 `dockerDesktopLinuxEngine` 管道；
- 没有 Docker Desktop/backend 进程；
- 精确失败节点、R1 8 项和 R2 9 项均未实际运行；
- 执行方依照停止规则将任务标为 `blocked / finished`，没有用历史结果、skip 或 collect-only 假装本轮通过。

之后人工启动 Docker Desktop，又再次出现 `sailor-ingest.sock` 的 `.stale` 改名错误。这说明父目录改名可以临时恢复启动，但在 Docker 后端再次异常退出后，4.91.0 环境仍会复发。

## 6. 已执行的处置与结果

| 已执行操作 | 结果 | 是否解决根因 |
| --- | --- | --- |
| 重启 Windows | 故障仍可复现 | 否 |
| 强制停止 Docker Desktop/backend/diagnostics | 能释放普通进程，但不能保证失效 socket 自动恢复 | 否 |
| `wsl --shutdown` | 是清理运行状态的必要步骤之一 | 单独不足 |
| 改名 `%LOCALAPPDATA%\Docker\run` | 让 Docker 创建新目录；失败随后可能转移到 Secrets Engine | 临时绕过 |
| 改名 `%LOCALAPPDATA%\docker-secrets-engine` | 与前一目录同时隔离后曾恢复 Engine | 临时绕过 |
| 启动 `finance-postgres` 并普通 `compose down` | 恢复窗口内测试正常，服务最终正常停止 | 证明项目 Compose 不是启动根因 |
| Docker Desktop 图形界面 Gather diagnostics | 用户观察到长时间加载；没有把它当作恢复成功证据 | 未解决 |
| Factory reset | 未执行 | 不适用 |
| 删除 volume / `prune` | 未执行 | 不适用 |
| 卸载重装 Docker Desktop | 未执行 | 尚未进入该级别 |
| 修改 Docker Desktop 全局设置 | 未执行 | 尚未授权 |

## 7. 为什么不是项目代码或 PostgreSQL 的问题

故障发生顺序是：

```mermaid
flowchart LR
    A[启动 Docker Desktop] --> B[初始化 Ingest 或 Secrets Engine]
    B --> C[处理 Windows AF_UNIX socket]
    C --> D[改名为 .stale 失败]
    D --> E[Docker backend 退出]
    E --> F[dockerDesktopLinuxEngine 管道不存在]
    F --> G[Compose 无法连接]
    G --> H[项目 PostgreSQL 根本没有启动]
```

项目代码、migration 和 PostgreSQL 测试位于流程末端。当前故障在 Docker 内部服务初始化阶段已经终止，因此：

- PostgreSQL 没有机会读取 migration；
- pytest 没有机会建立测试 schema；
- 项目 Compose 配置没有机会创建容器；
- `docker compose down` 只是停止项目服务，不会创建上述 Docker 内部 socket；
- T1 的时钟修复与 Docker Desktop 进程生命周期没有关联。

## 8. 与 Docker 官方资料的对应关系

Docker 官方问题跟踪器中的 [desktop-feedback #536](https://github.com/docker/desktop-feedback/issues/536) 描述了相同的 `docker-secrets-engine\engine.sock` 现象：Docker 非正常退出后，0 字节 socket 成为 ReparsePoint，下一次启动在删除或覆盖 socket 时失败；问题页给出的临时办法同样是改名两个父目录。该问题当前仍处于 open 状态。

Docker Desktop [4.90.0 发布说明](https://docs.docker.com/desktop/release-notes/#4900)曾记录 Windows 上“非正常关机遗留 stuck socket 导致无法启动”的修复，但本机 `4.91.0` 仍在 `sailor-ingest.sock` 和 `engine.sock` 上复现。因此不能把“4.90 已写修复”直接理解为本机问题已经被完全覆盖；它可能是未覆盖的第二类 socket、回归或特定 Windows/WSL 组合问题。

截至本记录时间，官方最新版本是 [Docker Desktop 4.92.0](https://docs.docker.com/desktop/release-notes/#4920)。4.92.0 没有明确点名本机这两个 socket，因此升级是合理的第一步，但不能承诺一定修复。

Docker 官方[备份与恢复文档](https://docs.docker.com/desktop/settings-and-maintenance/backup-and-restore/)说明：如果 Desktop 无法启动且后续需要重装或重置，应在 Docker 完全停止后备份 `%LOCALAPPDATA%\Docker\wsl\data\docker_data.vhdx`。只有进入重装或 reset 路径时才需要这一步；当前不应直接恢复出厂设置。

## 9. 当前项目影响

### 9.1 不受影响的内容

- P0～P3 已验收的基座；
- P4-B6-R1/F1 已完成的代码与测试证据；
- P4-B6-R2-S1 的结构修复和本地测试；
- S2 已实际通过的 R2 9 项、Finance 4 项和 activity import 10 项；
- T1 已写入的测试时钟修复、编译检查和测试收集结果；
- Git 历史与 `checkpoint/p3-foundation`。

### 9.2 当前被阻塞的内容

- T1 修复后的目标 PostgreSQL 用例实际运行；
- Host R1 PostgreSQL 完整收口；
- R2 PostgreSQL 复验；
- `P4-B6-R2` 从 `blocked` 进入 `review`；
- P4-C11 独立验收派发。

### 9.3 当前状态

- `P4-B6-R2-S2-T1`：代码修复已完成，运行门禁 `blocked / finished`；
- `P4-B6-R2-S2`：`blocked / finished`；
- `P4-B6-R2`：`blocked / finished`；
- P4-C11：未启动；
- 执行、测试和技术顾问：全部停止；
- 当前没有项目容器操作负责人，直到总控确认 Docker 恢复并派发新的有限验证任务。

## 10. 当前禁止重复的操作

在总控更新控制文件前，任何智能体都不得：

- 反复启动 Docker Desktop 或 Compose；
- 再次要求用户机械重复同一组目录改名命令；
- 删除已有 `.broken-*`、`.bak`、volume、镜像或 VHDX；
- 执行 `docker system prune`、`docker volume prune` 或 `docker compose down -v`；
- 点击 Factory reset；
- 修改 Docker context、WSL 全局设置或 Docker Desktop 全局设置；
- 把 Engine 不可用记为项目测试失败；
- 启动 P4-C11，或让测试智能体用旧快照提前验收；
- 重跑已经通过且与本故障无关的全量本地测试。

## 11. 推荐恢复方案

### 11.1 第一阶段：停止重复恢复，采用版本升级

推荐先执行 Docker Desktop `4.91.0 → 4.92.0` 的**原位升级**：

1. 从 Docker 官方发布说明中的 Windows 下载入口取得 4.92.0 安装程序。
2. 保留当前 Docker 数据，不卸载、不 reset、不删除 volume。
3. 关闭 Docker Desktop 与 backend，并执行一次 `wsl --shutdown`。
4. 用官方安装程序覆盖升级现有 4.91.0。
5. 如果安装后的首次启动仍被当前旧 socket 阻塞，再在一个受控步骤中同时改名两个当前父目录；仍然只改名保留，不直接删除。

升级不能保证修复，但它比在 4.91.0 上无限重复临时绕过更合理，也能排除已经由后续版本修正的相邻启动问题。

### 11.2 第二阶段：恢复后做稳定性验证

Docker 首次显示运行并不等于恢复完成。总控应依次确认：

1. Docker Desktop 版本为 4.92.0；
2. `Docker Desktop` 和 `com.docker.backend` 进程存在；
3. `dockerDesktopLinuxEngine` 管道存在；
4. `docker version` 同时返回 client 与 server；
5. `docker info` 返回 Linux Docker Desktop Engine；
6. `docker compose ps --format json` 对本项目退出 0，且没有意外服务；
7. 正常退出 Docker Desktop，再正常启动一次；
8. 第二次启动仍能通过第 3～6 项。

第 7～8 步用于验证“这次能启动”是否已经变成“能够稳定重启”，避免执行智能体刚接单后 Docker 又立即失效。

### 11.3 第三阶段：只运行剩余的有限 PostgreSQL 门禁

Docker 稳定后，由总控新建有限验证任务，不重开原 T1 实现范围。建议只运行：

- 修复过的精确 Host R1 节点；
- Host R1 剩余 7 项；
- Host R2 9 项。

这样共覆盖 17 个唯一 PostgreSQL 用例，不重复 S2 已通过的 Finance 4 项、activity import 10 项、S1 44 项或 326 项非 PostgreSQL 回归。测试结束后普通 `docker compose down`，并确认项目服务列表为空。

### 11.4 如果 4.92.0 仍复现

如果升级后仍出现相同 socket 错误，应停止继续改名和重启，进入单独的 Docker 环境任务：

1. 保存版本、时间、`backend.error.json` 和相关 Desktop/backend 日志；
2. 生成诊断包；若 UI 继续卡住，改用 Docker 官方诊断工具的受控路径；
3. 将本机证据与 Docker `desktop-feedback #536` 对照并提交给 Docker；
4. 评估关闭不参与本项目的 Docker AI/Ingest/Secrets 相关功能，但这属于全局设置变更，必须由用户和总控单独决定；
5. 只有升级和受控设置调整都失败，才考虑重装；
6. 重装或 Factory reset 前，按照官方文档备份 `docker_data.vhdx` 和用户确实需要保留的其他 Docker/WSL 数据。

## 12. 恢复完成标准

只有同时满足以下条件，Docker 环境才能从 `blocked` 改为 `ready`：

- 版本和 Engine 检查通过；
- 至少完成一次正常退出和再次启动；
- 两次启动都没有 `sailor-ingest.sock` 或 `engine.sock` 的 `.stale` 错误；
- 项目 Compose 状态可查询；
- 没有误删 volume、镜像、VHDX 或已有备份目录；
- 总控已更新 `docs/coordination/control.md`，指定新的唯一环境负责人；
- 执行智能体收到新的有限验证 Prompt 后才开始 PostgreSQL 测试。

## 13. 一句话判断

当前项目卡住的关键不是重新设计 P4，也不是继续修改业务代码，而是先把反复复发的 Docker Desktop 4.91.0 socket 启动故障作为独立环境事件处理。P4 已有实现和测试证据仍然有效；Docker 稳定后，只需补跑剩余 17 个唯一 PostgreSQL 用例，再决定是否进入 P4-C11。
