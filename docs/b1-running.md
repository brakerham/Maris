# B1 最小 Agent 运行说明

状态：C2 缺陷修复后的执行智能体自测版本，等待独立复验与总控验收。这里的金额全部是阶段 0 虚拟数据。

## 环境与安装

项目要求 Python 3.12 或更高版本。在项目根目录创建并激活虚拟环境后安装：

```powershell
python -m pip install -e ".[dev]"
```

运行离线演示，无需 API 密钥或网络：

```powershell
wife-agent "查询本月虚拟预算"
```

也可以直接使用模块入口：

```powershell
python -m wife_system.cli "查询本月虚拟预算" --provider offline
```

输出是 JSON，包含请求编号、最终状态、回答和不含提示词/密钥的执行事件。工具事件用 `tool_call_id` 关联具体调用，并在完成事件中记录 `duration_ms`。离线提供者仍会先请求 `query_budget`，由真实工具注册表执行，然后根据工具结果形成回答，因此会经过完整工具循环。

`--timeout` 必须是有限且大于零的秒数。`0`、负数、`nan` 和无穷值会作为命令行参数错误安全退出，不打印 Python traceback。

## DeepSeek 适配边界

设置 `DEEPSEEK_API_KEY` 后可以选择 DeepSeek：

```powershell
$env:DEEPSEEK_API_KEY = "在本地安全设置的密钥"
python -m wife_system.cli "查询本月虚拟预算" --provider deepseek
```

密钥只进入 HTTP 授权头，不进入执行事件。当前适配器调用 OpenAI 兼容的 `/chat/completions` 工具调用接口；真实联网调用和具体模型版本尚未验证，需在 D1 建议与总控接口冻结后复核。

可通过 `DEEPSEEK_MODEL` 设置模型名；未设置时临时使用 `deepseek-chat`。适配器关闭 thinking mode、没有隐藏重试，并把上游错误归一为稳定的 `model_*` 错误码。模型默认值仍须服从总控最终冻结结果。

## 自测

```powershell
python -m pytest
```

自动化检查覆盖正常工具循环、Pydantic 参数拒绝、未知工具、重复工具调用、轮次上限、提供者超时/失败、非法工具输出、同一实例并发重复请求、事件关联与耗时、错误隐私、超时参数和 DeepSeek 协议映射。同一 `AgentRunner` 收到相同 ID 与输入的并发请求时只执行一次，等待者重放首个结果并取得 `cache_hit` 事件。B1 只提供进程内请求去重；跨进程持久化属于后续服务与数据库范围。

## 代码入口

- `src/wife_system/agent/loop.py`：有界工具调用循环和进程内重复请求处理。
- `src/wife_system/agent/providers.py`：模型协议、离线替身和 DeepSeek 薄适配器。
- `src/wife_system/tools.py`：Pydantic 工具参数、注册表和虚拟预算工具。
- `src/wife_system/cli.py`：离线或 DeepSeek 命令行入口。
- `tests/`：执行智能体自测；不能替代测试智能体 C2 的独立结论。

明确未实现：FastAPI/微信探针 B2、正式预算算法、数据库、LangGraph、RAG、Electron 和持久化幂等。
