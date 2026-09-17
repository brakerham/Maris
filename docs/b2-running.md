# B2a FastAPI 探针运行说明

状态：执行智能体已交付 `review`，等待独立 HTTP 验收与总控核对。这里只验证 Python 服务健康状态、随机回执和进程内幂等，不表示 OpenClaw 或微信已经接通。

## 安装与启动

项目要求 Python 3.12 或更高版本。在项目虚拟环境中安装运行和开发依赖：

```powershell
python -m pip install -e ".[dev]"
```

仅监听本机地址启动服务：

```powershell
python -m uvicorn wife_system.api.app:app --host 127.0.0.1 --port 8000
```

健康检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/healthz
```

创建测试探针：

```powershell
$headers = @{ "Idempotency-Key" = "local-test-event-001" }
$body = @{ challenge = "V001" } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/api/v1/probes -Method Post -Headers $headers -ContentType "application/json" -Body $body
```

相同幂等键与相同 `challenge` 会返回第一次的请求编号、回执和时间，并将 `replayed` 改为 `true`。相同键配不同 `challenge` 返回 HTTP 409。缓存只存在于当前 Python 进程，服务重启或多进程部署不会共享记录。

## 自测

```powershell
python -m pytest
```

执行方测试覆盖健康检查、随机性、带时区时间、重复与冲突、Pydantic 错误、并发单次创建、日志隐私和安全的 HTTP 500。独立测试结论由测试智能体另行提交。

2026-09-14 执行方复核：当前工作区全量 pytest 为 `143 passed, 1 warning in 7.15s`；`pip check` 返回 `No broken requirements found.`；`python -m compileall -q src tests` 退出码为 0。早先记录的 89/90 项基线已被后续落地的独立验收用例替代。

## 测试客户端版本与弃用警告

复核环境为 Python 3.14.7、FastAPI 0.141.1、Starlette 1.6.0、HTTPX2 2.12.0、AnyIO 4.15.1 和 pytest 9.1.1。

- 旧的 Starlette 警告是因为 `starlette.testclient` 在未安装 `httpx2` 时回退到 `httpx 0.28.1`。Starlette 当前元数据和 TestClient 实现均把 `httpx2>=2` 列为官方迁移路径。开发依赖已改为 `httpx2>=2.12,<3`；`pytest tests/test_probe_api.py -W error::starlette.exceptions.StarletteDeprecationWarning` 为 `13 passed`，该警告已消失。
- 剩余的一条是 Starlette 1.6.0 内部 `testclient.py` 使用 `anyio.abc.BlockingPortal` 别名，AnyIO 4.15.1 要求改用 `anyio.from_thread.BlockingPortal`。`-W error::DeprecationWarning` 会在导入 TestClient 时精确失败于该上游行；常规测试和实际 HTTP 运行均正常。当前 Starlette 上游源码仍有同一引用，因此本任务不降级 AnyIO、不修改第三方包也不隐藏警告；这是非阻断的版本兼容风险，待 Starlette 发布对应修复后升级复验。

## 真实本机 HTTP 冒烟

2026-09-14 在 `127.0.0.1:49674` 启动实际 Uvicorn 会话，只访问本机回环地址：

- `GET /healthz` 返回 HTTP 200 和精确载荷 `{"status":"ok","service":"wife-system"}`。
- 首次探针返回 HTTP 200、`replayed:false`、带 `+08:00` 时区的时间和随机 `POC-` 回执。
- 同键同载荷重放返回 HTTP 200 和 `replayed:true`，`request_id`、`receipt` 及 `created_at` 与首次完全一致。
- 同键不同载荷返回 HTTP 409 和 `duplicate_request_conflict`，`request_id` 指向首次记录。
- 服务收到可控退出信号后输出 `Application shutdown complete` 和 `B2A_UVICORN_STOPPED`，进程正常退出且端口不再监听。

## 代码入口

- `src/wife_system/api/app.py`：FastAPI 端点、统一安全错误和结构化事件。
- `src/wife_system/api/schemas.py`：请求、成功响应和错误响应模型。
- `src/wife_system/probes.py`：随机回执、时间和并发安全的进程内幂等。
- `tests/test_probe_api.py`：执行智能体自测。
- `pyproject.toml`：FastAPI/Uvicorn 运行依赖和 HTTPX2/pytest 开发依赖。

明确未实现：OpenClaw TypeScript 桥接、真实微信、主动提醒、持久化/多进程幂等和 `POST /api/v1/agent/runs`。
