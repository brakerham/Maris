# 阶段 0 C2-B2a FastAPI 探针独立 HTTP 验收报告

验收时间：2026-09-14，Asia/Shanghai
接口冻结：`P0-IF-001`
状态：`review`
结论：B2a 的 FastAPI 探针功能契约通过独立验收；发现 1 项非功能性的测试依赖兼容性缺陷，不阻断当前普通模式功能验收，但会阻断“弃用警告视为错误”的测试门禁。

## 1. 范围与边界

本轮独立验证：

- `GET /healthz` 的固定响应及不调用探针服务；
- `POST /api/v1/probes` 的 OpenAPI Schema、运行时校验、错误结构和额外字段拒绝；
- 缺失、空白、256/257 字符边界的 `Idempotency-Key`；
- 缺失、空白、类型错误、128/129 字符边界的 `challenge`；
- 随机 UUID `request_id`、随机 receipt、`+08:00` 上海时区时间；
- 同键同载荷的顺序重放、并发单次创建、客户端超时后重试；
- 同键不同载荷冲突、不同键相同 challenge 独立处理；
- 内部异常的安全 500、失败后使用同键恢复且不缓存失败；
- 日志不包含 challenge、原始幂等键、输入/异常 canary、堆栈或内部路径；
- 本机真实回环 HTTP 进程停服与重启边界；
- FastAPI 路由、Schema、探针服务/存储分层，以及 FastAPI dependency override 可替换性；
- 当前 TestClient 依赖栈的弃用警告。

未进入本轮：真实 OpenClaw、微信账号、微信消息实收、身份绑定、外部网络和提醒。跨进程或重启后持久化去重按冻结契约不支持，本轮验证其不会被误报为重放。

## 2. 输入快照与环境

本仓库禁止本轮执行 git，因此使用 SHA-256 固定输入快照：

| 文件 | SHA-256 |
| --- | --- |
| `src/wife_system/api/app.py` | `B2A6BAAC665D099EB2D086C2B4EE83F6D1BD5E061BE66B7C20FF1C85067C68F7` |
| `src/wife_system/api/schemas.py` | `970C668D0045B27A04EAC13A4571E28CC24FA8AD7ACE6F67288B8A6B9BDCE647` |
| `src/wife_system/probes.py` | `A9F2F9FD0FC555733AED8F5B7B8F87599AC7C9ECD5E214B2488833B5D247B8F0` |
| 执行方 `tests/test_probe_api.py` | `1DF0C594902CA964DCD54746ED1F6E8176D13DBF8DCF167FEA7520A8AA0360B1` |
| 接单时已存在的 `tests/independent/test_c2_b2_probe_api.py` | `65FB6AE3FE82D277043E1D6DD741891DC1FD5984E00C749F3F9F578FEA897A92` |
| 本轮新增 `tests/independent/test_c2_b2_api.py` | `6540E3D6EF57B9BF9278021F8D481172950E2D6BFBFABE149C05FE572E703746` |

环境：Windows、Python 3.14.7、FastAPI 0.141.1、Starlette 1.6.0、AnyIO 4.15.1、Pydantic 2.13.5、Uvicorn 0.53.0、pytest 9.1.1、httpx 0.28.1、httpx2 2.12.0。

## 3. 验收结果

| 矩阵项 | 结果 | 独立证据摘要 |
| --- | --- | --- |
| H-01 | 通过 | 注入调用即抛错的服务后访问 `/healthz`，仍精确返回 200 固定 JSON，服务未被触发 |
| H-02 | 通过 | OpenAPI 固定必填 header、1～256 长度、严格 body；缺失/空白/过长键及坏 JSON、坏类型、缺失/空白/过长 challenge、extra 全部安全 422 `invalid_request`，服务不启动 |
| H-03 | 通过 | 同键同载荷顺序请求复用首次 `request_id/receipt/created_at/challenge`，第二次 `replayed:true` |
| H-04 | 通过 | 同键不同载荷返回 409 `duplicate_request_conflict`，关联首次 `request_id`，receipt factory 只调用一次 |
| H-05 | 通过 | 24 个并发相同请求只调用一次 receipt factory，只产生一组 ID/receipt/time，1 个首次结果和 23 个 replay |
| H-06 | 通过 | 真实回环 HTTP 首次请求在客户端超时后由服务完成；随后同键两次重试均返回首次记录及 `replayed:true` |
| H-07 | 通过 | 注入内部 `RuntimeError` 后返回安全 500 `internal_error` 与 UUID request_id；响应和日志无异常消息、堆栈或路径 |
| H-08 | 通过 | 首次 factory 异常后用同一键重试成功，`replayed:false` 且使用新的 request_id，证明失败未污染缓存或进程 |
| W-02 | HTTP 层通过 | 响应原样含 challenge，UUID request_id、随机 receipt 与带 `+08:00` 的创建时间；日志含同一 request_id/receipt 用于桥接核对 |
| W-03 | HTTP 层通过 | 不同来源键、相同 challenge 生成不同 request_id 与 receipt |
| W-04 | HTTP 层通过 | 真实 Uvicorn 回环服务停止后 HTTP 请求连接失败，不可能获得旧成功回执；微信可见错误仍待 B2b 实测 |
| W-05 | HTTP 层通过 | 顺序、24 路并发和客户端超时重试均证明同来源键同载荷不重复创建 |
| W-06 | HTTP 层通过 | 两个不同来源键即使 challenge 完全相同，仍产生两份独立记录 |
| W-07 | HTTP 层通过 | 同来源键不同 challenge 返回冲突，不覆盖首次记录且不生成第二份 receipt |

响应时间以 ISO 8601 `+08:00` 输出，满足当前日期下 Asia/Shanghai。`request_id` 可解析为 UUID。默认 receipt 为 `POC-` 加 24 个随机十六进制字符；两个独立请求值不同。

## 4. 进程内与重启边界

独立测试实际启动 Uvicorn 子进程并走 `127.0.0.1` HTTP：

1. 首次进程用指定键创建成功；
2. 停止进程后，同一 URL 请求产生传输层连接错误，无成功响应；
3. 重启新进程后再次使用相同键，返回 200、`replayed:false`，且 request_id/receipt 均为新值。

这与 `P0-IF-001` 的“B2 仅承诺单进程、并发安全缓存”一致。跨重启持久化幂等当前不支持，正式账目写入前仍需数据库事务与持久化幂等键。

## 5. 分层与可测试性审查

- Pydantic 请求/响应模型位于 `src/wife_system/api/schemas.py`；HTTP 中间件、异常映射、路由与日志位于 `src/wife_system/api/app.py`；记录、进程内存储、锁和随机生成位于 `src/wife_system/probes.py`。
- 路由把业务创建委托给 `ProbeService.create`，没有在路由函数内维护去重字典或生成 receipt；`InMemoryProbeStore` 独立持有锁和记录。
- `create_app(probe_service=...)` 支持构造注入；`get_probe_service` 还是 FastAPI dependency，独立测试通过 `app.dependency_overrides` 替换服务并核对路由传入的键、challenge 和候选 request_id。
- 健康端点不依赖探针服务。异常 handler 只记录稳定码和异常类型，不记录异常消息或 traceback。

结论：当前分层满足冻结的薄 HTTP 边界与可替换依赖要求。

## 6. 日志与隐私

独立测试分别触发成功、重放、冲突、请求校验失败和内部异常。全部应用日志均可逐行解析为 JSON，并通过以下检查：

- 不含完整 challenge；
- 不含原始 `Idempotency-Key`，只含 SHA-256 摘要；
- 不含额外字段、私人消息或异常消息 canary；
- 不含 `Traceback`、测试注入的文件名或内部路径；
- 每条应用事件有 request_id；成功/重放事件保留按契约核对所需的 receipt。

## 7. 验证命令与输出

| 检查 | 结果 |
| --- | --- |
| `.venv\Scripts\python.exe -m pytest -o addopts='' tests/independent/test_c2_b2_api.py -q -ra` | `25 passed, 1 warning in 4.41s`，退出码 0 |
| `.venv\Scripts\python.exe -m pytest -o addopts='' tests/independent -q -ra` | `104 passed, 1 warning in 6.38s`，退出码 0 |
| `.venv\Scripts\python.exe -m pytest -o addopts='' -q -ra` | `143 passed, 1 warning in 6.65s`，退出码 0 |
| `.venv\Scripts\python.exe -m pip check` | `No broken requirements found.`，退出码 0 |
| `.venv\Scripts\python.exe -m compileall -q src tests` | 无输出，退出码 0 |
| `.venv\Scripts\python.exe -m pytest -o addopts='' tests/independent/test_c2_b2_api.py -q -ra -W error::DeprecationWarning` | 收集阶段因弃用警告失败，退出码 1 |

## 8. 缺陷 C2-B2-DEP-001：TestClient 在 Python 3.14 产生弃用警告

稳定复现：导入 `fastapi.testclient.TestClient` 时，Starlette 1.6.0 的 `starlette/testclient.py:53` 访问已弃用的 `anyio.abc.BlockingPortal`，AnyIO 4.15.1 建议改用 `anyio.from_thread.BlockingPortal`。普通 pytest 模式每次测试进程报告 1 条 `DeprecationWarning`；把 DeprecationWarning 视为错误时，测试在收集阶段退出 1。

阻断程度建议：

- 对当前 B2a HTTP 功能验收：不阻断，全部功能、回归、依赖完整性和编译检查均通过；
- 对 warning-clean 或 `-W error::DeprecationWarning` CI 门禁：阻断；
- 对后续 Python/AnyIO 升级：中等兼容性风险，应由执行方在获配依赖/测试范围后统一对齐 FastAPI、Starlette、AnyIO 与测试客户端，或迁移独立测试客户端；本轮按任务边界未修改依赖、实现或执行方测试。

首轮环境曾额外报告 Starlette 的 httpx TestClient 弃用提示；最终快照已安装 httpx2 2.12.0，该提示不再稳定复现。因此本报告只把最终可重复的 AnyIO alias 警告列为缺陷。

## 9. 两份 B2 独立测试文件

- `tests/independent/test_c2_b2_probe_api.py` 在本轮重试接单时已经存在，本轮只读取和运行，没有修改。它保留并发不同载荷竞争、并发不同键、challenge 不静默规范化、naive clock 安全失败等独立场景。
- `tests/independent/test_c2_b2_api.py` 是本轮按派发路径新增的套件。它补充 OpenAPI 精确约束、256/257 键边界、UUID 与 `+08:00`、FastAPI dependency override、真实 HTTP 客户端超时重试、停服和跨进程重启。

两份文件有基础契约重叠，但各自含对方没有的风险场景。建议当前都保留，保证本次验收证据可追溯；后续若总控安排测试整理，可由测试所有者合并公共 helper 和重复的基础断言，再完整复跑，不能直接删除接单前已有文件。

## 10. 最终结论与剩余风险

B2a FastAPI 探针在 `P0-IF-001` 冻结范围内通过 C2 独立 HTTP 功能验收，可交总控进入 review。唯一缺陷 C2-B2-DEP-001 是测试依赖兼容性问题：当前普通模式可用，但严格弃用警告门禁失败。

剩余风险与未验证项：真实 OpenClaw/微信收发、微信端停服错误文案、账号绑定、插件版本、通知可达性均须在 B2b 与用户实测中取证；当前进程内存储不提供跨重启或多进程去重保证。
