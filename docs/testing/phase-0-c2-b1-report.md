# 阶段 0 C2：B1 独立复验报告

复验时间：2026-09-14，Asia/Shanghai  
复验角色：测试智能体  
接口基线：`P0-IF-001`  
结论：`修复复验通过，等待总协调验收`

## 0. 2026-09-14 11:24 修复复验更新

执行智能体指出原并发测试使用 `Barrier(2)`，与“provider 只调用一次”的期望矛盾。测试智能体独立核对后确认该说法属实：正确单飞实现只会有一个 provider 调用，因此原夹具会等待第二个 provider 调用直至抛出 `BrokenBarrierError`，无法作为修复后的通过测试。

测试智能体只修改了 [`test_c2_b1_core_contract.py`](../../tests/independent/test_c2_b1_core_contract.py) 中该用例的同步基础设施：改用 `first_provider_entered`、`second_provider_entered`、`second_run_started` 和 `release_provider` 四个 `threading.Event`。首次 provider 调用可控阻塞，并确认第二请求已启动；若产品没有单飞，第二次 provider 进入会被直接观察；若产品正确单飞，释放首次调用后第二请求取得缓存结果。该变更是**测试基础设施修正，不是产品修复**。

与此同时，共享工作区中的执行智能体已经完成六项产品修复。修复后的源文件哈希为：

| 文件 | 修复复验 SHA-256 |
| --- | --- |
| `pyproject.toml` | `F4AE242A8EC504ED4E4F94961FA5B43ACBA67129E59EF55818AB41D39B5C812F` |
| `src/wife_system/tools.py` | `CF15005AF1F33565DFC3792E218AB90E17DFBF19BF0BDCFA23A000DB5CEE9782` |
| `src/wife_system/cli.py` | `46CDD406E0597C2B0005716DB4B7F85E2896D9CD96D5A4F702D2A76089E00994` |
| `src/wife_system/agent/types.py` | `ADBED39A42D59D7AFA172ED198623BAA4027BC819D9D78CB38213A9925CDBF31` |
| `src/wife_system/agent/providers.py` | `245602FDC80CBC99558D43430378301369DA1F1EF30920BC3671217440A586CE` |
| `src/wife_system/agent/loop.py` | `6A030C7985CE043F3F1D72BB8A010844CBFF66EB77010160334A3EF15BD03081` |

复验结果：

- 原六项失败定向复跑：`6 passed in 1.36s`。
- 独立测试套件：51 项全部通过，`51 passed in 1.57s`。
- 完整测试套件：77 项全部通过，`77 passed in 1.60s`。
- `pip check`：通过；`compileall -q src tests`：退出码 0。
- 安装后的离线 CLI：成功，事件包含工具调用 ID 与耗时。
- CLI `--timeout 0` 和 `--timeout nan`：均以参数错误退出，不含 traceback。

六项初测缺陷的当前状态：

| 缺陷 | 修复复验状态 | 独立观察 |
| --- | --- | --- |
| C2-B1-001 非法工具输出 | 通过 | 返回稳定 `tool_error`，未再泄出 `TypeError`。 |
| C2-B1-002 并发相同请求 | 通过 | 修正夹具后只进入 provider 一次，第二结果带 `cache_hit`。原产品缺陷确实存在，但原 Barrier 夹具不能验证正确修复。 |
| C2-B1-003 工具事件关联与耗时 | 通过 | 开始/结束事件含同一 `tool_call_id`，完成事件含非负 `duration_ms`。 |
| C2-B1-004 私人消息回显 | 通过 | 未注册工具名不再进入事件或错误文案。 |
| C2-B1-005 `NaN` 超时 | 通过 | 运行器拒绝非有限或非正超时。 |
| C2-B1-006 CLI 零超时堆栈 | 通过 | argparse 安全拒绝零值和 `nan`，无内部 traceback。 |

初测矩阵中的 4 个失败项现均通过；当前适用于 B1 的矩阵结果为 34 个通过、0 个失败、6 个未测/当前不适用。真实 DeepSeek、跨进程/重启去重、通用工具超时和 B2/微信范围仍保持未测或当前不支持。

## 1. 范围、快照与限制

本次只复验 B1 的 Agent 核心、虚拟预算工具、DeepSeek 适配边界、CLI 和结构化事件。没有访问真实网络，没有使用真实 API key，没有测试 B2、FastAPI、OpenClaw、微信或提醒。

仓库当前没有 Git 提交，`HEAD` 不存在，所有项目文件均为未跟踪文件。因此初测以 2026-09-14 11:09 的工作区快照及以下 SHA-256 标识输入；修复复验快照见第 0 节：

| 文件 | SHA-256 |
| --- | --- |
| `pyproject.toml` | `F4AE242A8EC504ED4E4F94961FA5B43ACBA67129E59EF55818AB41D39B5C812F` |
| `src/wife_system/tools.py` | `4C5781C2EE21F3AB1B98726E635EBE7BCE48477520D309234A70E51731483479` |
| `src/wife_system/cli.py` | `E47088A2FE348BE65C8D43DE092CB3AE06214207AB9FD104A871A88F30609C6C` |
| `src/wife_system/agent/types.py` | `173ABE4A8B88A668D69774784D6874DF026DE9D969C7E08F91C162464E0F43D3` |
| `src/wife_system/agent/providers.py` | `245602FDC80CBC99558D43430378301369DA1F1EF30920BC3671217440A586CE` |
| `src/wife_system/agent/loop.py` | `82FC7CC4D21FEA8D03FE347DC30FC09CB51FBDB4EB10339468006D5B065BB736` |

环境：Windows，Python 3.14.7，Pydantic 2.13.5，pytest 9.1.1。项目声明 Python `>=3.12`、Pydantic `>=2.10,<3`、pytest `>=8,<10`，当前环境符合声明，但没有依赖锁文件，不能证明其他允许版本具有完全相同行为。

独立测试位于：

- [`test_c2_b1_core_contract.py`](../../tests/independent/test_c2_b1_core_contract.py)
- [`test_c2_b1_provider_cli.py`](../../tests/independent/test_c2_b1_provider_cli.py)

## 2. 初测总体结果

- 执行方原有测试基线：15 项全部通过。
- 加入独立测试后的完整测试集：66 项；60 项通过，6 项失败，退出码 1。
- 编译检查：通过。
- 依赖检查：通过，未发现破损依赖。
- 安装后的离线 CLI：通过；两次模型调用、一次真实注册表工具执行，返回虚拟预算 `121350` 分。
- DeepSeek：只使用注入的假传输或被测试替换的 `urlopen` 验证序列化和错误映射；缺少 key 的 CLI 在联网前明确失败。真实 DeepSeek 未测。

B1 初测不能通过 C2。阻断原因包括两个 P0 观察/隐私案例失败，以及工具非法输出没有被封装为结构化错误；这些缺陷的修复复验结果见第 0 节。

## 3. C1 案例初测清单

### Agent 核心与工具循环

| 案例 | 状态 | 实际结果与证据 |
| --- | --- | --- |
| A-01 | 通过 | 两次模型调用、一次工具执行；第二轮历史中的工具消息绑定原 `tool_call_id`，回答来自真实工具结果。 |
| A-02 | 通过 | 两份不同 `available_cents` 的虚拟夹具产生不同回答。 |
| A-03 | 通过 | 直接文本一次模型调用结束，无工具事件。 |
| A-04 | 通过 | DeepSeek 工具参数 JSON 截断时适配器返回 `model_invalid_response`，工具没有启动；中立核心不会接收原始 JSON 字符串。 |
| A-05 | 未测/当前不适用 | 阶段 0 唯一参数 `period` 有默认值，Schema 没有必填字段，无法构造“缺少必填字段”。 |
| A-06 | 通过 | 数组代替周期字符串，返回 `invalid_tool_arguments`。 |
| A-07 | 通过 | 额外字段被 Pydantic `extra="forbid"` 拒绝。 |
| A-08 | 通过 | `last_year` 等范围外值被拒绝。 |
| A-09 | 通过 | 未注册工具返回 `unknown_tool`，没有 `tool_finished`；隐私问题另见 C2-B1-004。 |
| A-10 | 通过 | 重复调用 ID、不同 ID 但工具名与规范化参数相同的两种情况均只执行一次。 |
| A-11 | 通过 | `max_model_turns=2` 时模型恰好最多调用两次，随后返回 `max_model_turns_exceeded`。 |
| A-12 | 通过 | 无文本且无工具调用返回 `empty_model_response`。 |
| A-13 | 通过 | 同一轮两个工具按返回顺序执行，工具消息分别绑定正确调用 ID。 |
| A-14 | 通过 | 处理函数抛出可预期 `ValueError` 时返回脱敏 `tool_error`。阶段 0未定义更细业务异常码。 |
| A-15 | 通过 | 未预期运行时异常返回脱敏 `tool_error`，同一运行器随后可处理正常请求。 |
| A-16 | 未测/当前不适用 | `P0-IF-001` 明确 B1 尚无通用工具超时；唯一工具为本地只读确定性函数。 |
| A-17 | 失败 | 不可 JSON 序列化的工具结果从 `AgentRunner.run` 泄出 `TypeError`；见 C2-B1-001。工具也没有输出模型可校验结果形状。 |
| A-18 | 通过 | 两个独立 run 的用户消息和结果没有互相继承。 |

### 模型适配、请求重复与恢复

| 案例 | 状态 | 实际结果与证据 |
| --- | --- | --- |
| M-01 | 通过 | socket 超时和 `ProviderTimeoutError` 均映射 `model_timeout`，无工具执行，无私密原文。 |
| M-02 | 通过 | HTTP 401 映射 `model_auth_failed` 且不可重试。 |
| M-03 | 通过 | HTTP 402 映射 `model_balance_exhausted` 且不可重试。 |
| M-04 | 通过 | HTTP 429 映射 `model_rate_limited` 且标记可重试；没有隐藏重试。 |
| M-05 | 通过 | 500/503/连接类故障映射 `model_unavailable`；失败后的独立 run 可恢复。 |
| M-06 | 通过 | 坏 JSON、空 choices、缺调用 ID、非对象参数和错误内容类型均映射 `model_invalid_response`。 |
| M-07 | 通过 | 普通测试和离线 CLI 在网络入口替换为禁止函数后仍通过。 |
| M-08 | 通过 | 显式 DeepSeek CLI 且移除 key 后，在启动前清楚失败且没有 traceback；这不代表真实 DeepSeek 已验证。 |
| H-03（B1 等价） | 通过 | 同实例顺序重放相同 ID 与输入，返回首次结果并追加 `cache_hit`，模型只调用一次。 |
| H-04（B1 等价） | 通过 | 同 ID 不同输入返回 `duplicate_request_conflict`，不启动新模型调用。 |
| H-05（B1 等价） | 失败 | 同实例并发相同请求执行模型两次；见 C2-B1-002。 |
| H-08（B1 等价） | 通过 | 模型或工具失败后，第二个独立核心请求仍可成功。 |
| H-01、H-02、H-06、H-07 | 未测 | 属于尚未实现的 HTTP/API 边界；核心错误分支已在 A/M 案例验证。 |

### 结构化事件与隐私

| 案例 | 状态 | 实际结果与证据 |
| --- | --- | --- |
| L-01 | 失败 | 可观察轮次、工具名和结果状态，但工具事件没有 `tool_call_id` 和耗时，无法满足调用级关联与时延证据；见 C2-B1-003。 |
| L-02 | 通过 | canary key 不进入适配器 repr、HTTP body、核心结果或事件；上游私密错误文本被替换。 |
| L-03 | 失败 | 普通输入和原始财务快照不进入事件，但模型把私人消息回显成未知工具名时，该消息原样进入事件和错误响应；见 C2-B1-004。 |
| L-04 | 通过 | 坏参数 canary、异常原文、堆栈和内部路径不进入结构化结果。CLI 参数错误例外见 C2-B1-006。 |
| L-05 | 通过 | 带换行和伪 JSON 的模型工具名经结果 JSON 序列化后被转义，不能注入另一条 JSON 记录。 |
| L-06 | 通过 | 两个不同 ID 的并发 run 各自返回正确请求 ID 和回答，未串结果。 |

以上适用于 B1 的矩阵项合计：30 个通过、4 个失败、6 个未测/当前不适用。另有 2 个 B1 配置与 CLI 补充失败，见 C2-B1-005 和 C2-B1-006。

## 4. 可复现缺陷

### C2-B1-001：非法工具输出导致未捕获异常（已修复并通过复验）

- 关联：A-17。
- 复现：`.venv\Scripts\python.exe -m pytest -o addopts='' tests\independent\test_c2_b1_core_contract.py::test_a17_invalid_tool_output_is_rejected_as_a_structured_error`
- 输入：工具处理函数返回一个不可 JSON 序列化的对象。
- 预期：在结果进入模型历史前拒绝，返回稳定 `tool_error` 或冻结后的工具协议错误，不向调用方抛堆栈。
- 实际：`src/wife_system/agent/loop.py:158` 的 `json.dumps` 位于工具异常保护之外，抛出 `TypeError: Object of type NotJsonSerializable is not JSON serializable`。
- 影响：工具实现错误可越过 Agent 稳定结果边界；CLI/API 调用方可能看到堆栈，运行结果也不会写入去重缓存。

### C2-B1-002：并发相同请求没有去重（已修复并通过修正后用例复验）

- 关联：H-05 的 B1 同实例等价场景；`P0-IF-001` 第 4 节同实例请求去重。
- 复现：`.venv\Scripts\python.exe -m pytest -o addopts='' tests\independent\test_c2_b1_core_contract.py::test_concurrent_same_request_is_executed_only_once --tb=short`
- 输入：两个线程同时对同一 `AgentRunner` 调用相同 `request_id` 和输入；模型替身在两线程会合后返回。
- 预期：只执行一个 run；另一个返回首次结果或明确的进行中状态。
- 实际：两个线程都在缓存写入前通过检查，`provider.calls == 2`，两个结果都没有 `cache_hit`。
- 影响：重复模型计费和重复只读工具调用；未来接入有副作用工具前不能依赖该去重实现。

### C2-B1-003：结构化工具事件缺少调用关联和耗时（已修复并通过复验）

- 关联：L-01，优先级 P0。
- 复现：`.venv\Scripts\python.exe -m pytest -o addopts='' tests\independent\test_c2_b1_core_contract.py::test_l01_tool_events_identify_the_call_and_include_duration`
- 输入：一次调用 ID 为 `observable-call` 的正常工具循环。
- 预期：工具开始/结束事件可关联该调用 ID，并提供本次工具执行耗时。
- 实际：事件只有 `sequence/kind/model_turn/tool_name/outcome`；没有调用 ID 或任何耗时字段。
- 影响：同轮多工具时无法仅从交付事件证明每个开始/结束对应哪个调用，也不能验证超时和性能证据。

### C2-B1-004：未知工具名可把私人消息写入事件和错误响应（已修复并通过复验）

- 关联：L-03，优先级 P0；`P0-IF-001` 第 2 节用户可见错误隐私要求。
- 复现：`.venv\Scripts\python.exe -m pytest -o addopts='' tests\independent\test_c2_b1_core_contract.py::test_l03_unknown_tool_name_cannot_echo_a_private_message`
- 输入：用户消息使用虚构私人 canary；确定性模型把同一字符串作为未注册工具名返回。
- 预期：返回稳定 `unknown_tool`，事件和用户错误只含安全标识，不回显模型控制的原始名称。
- 实际：`tool_started.tool_name` 与 `error_message` 都包含完整 canary。
- 影响：模型只要回显输入，就能把完整私人消息带入执行记录和上层响应。

### C2-B1-005：`NaN` 模型超时被当作有效值（已修复并通过复验）

- 关联：冻结的“超时必须大于 0”约束。
- 复现：`.venv\Scripts\python.exe -m pytest -o addopts='' "tests\independent\test_c2_b1_core_contract.py::test_invalid_runner_limits_are_rejected[kwargs3-provider_timeout_seconds]"`
- 输入：`provider_timeout_seconds=float("nan")`。
- 预期：构造运行器时拒绝非有效正数。
- 实际：`nan <= 0` 为假，当前检查放行该值。
- 影响：在线提供者会收到无意义的超时参数；错误可能在更深的网络层以不稳定形式出现。

### C2-B1-006：CLI 零超时打印内部堆栈和路径（已修复并通过复验）

- 关联：B1 CLI、坏参数与用户可见错误隐私约束。
- 复现：`.venv\Scripts\python.exe -m wife_system.cli x --provider offline --timeout 0`
- 预期：参数边界清楚拒绝，非零退出且不显示内部堆栈。
- 实际：退出码 1，并打印从 `cli.py` 到 `loop.py` 的完整 traceback 和本地绝对路径。
- 影响：普通参数错误暴露内部实现路径，CLI 错误体验不稳定。

## 5. 结构审查

符合冻结边界的部分：

- 核心通过 `ModelProvider`、`ConversationMessage`、`AssistantTurn` 和 `ToolCall` 依赖中立类型；`loop.py` 没有 DeepSeek HTTP 字段。
- DeepSeek URL、授权头、OpenAI 兼容 payload 和响应转换集中在 `providers.py`，CLI 只负责选择提供者和环境配置。
- 工具输入 Schema 由 Pydantic v2 生成，额外字段被拒绝；虚拟金额使用整数分、币种固定 `CNY`。
- 同轮多工具按顺序执行，结果消息绑定各自调用 ID；运行消息历史和重复工具集合都是 run 局部状态。
- 自动化测试可注入传输层，不需要 key 和网络；API key 使用 `repr=False`，没有进入执行事件。

需要修复或在下一版冻结中明确的部分：

- `Tool` 只有输入模型，没有输出模型；结果序列化发生在受保护的工具执行块之外，对应 C2-B1-001。
- `_completed` 是无锁普通字典，检查与执行/写入不是原子操作，对应 C2-B1-002；缓存也没有容量或生命周期上限，长进程会持续增长。
- `ExecutionEvent` 缺少工具调用 ID 和耗时，对应 C2-B1-003；未知工具名是未受信任的模型输出，却被直接写入事件，对应 C2-B1-004。
- 超时只检查 `<= 0`，没有检查有限数；CLI 把核心构造异常直接暴露给用户，对应 C2-B1-005/006。
- 核心只捕获 `ProviderError` 和超时类；提供者实现若抛出其他异常仍会越过稳定结果边界。默认 DeepSeek 传输的已知 HTTP、URL 和超时错误已有映射，本次把其他异常保留为剩余风险。

## 6. 未测、当前不支持与剩余风险

- 真实 DeepSeek 调用、真实模型名和线上供应商行为：未测；本报告不能宣称 DeepSeek 联网通过。
- 跨进程重启和多进程共享请求去重：按冻结记录当前不支持。
- 通用工具超时、取消和迟到结果：按冻结记录当前不适用；引入网络、文件或写工具前必须实现。
- Agent HTTP 请求、断线重试和 HTTP 错误状态：B2/后续接口范围，本次未测。
- FastAPI、OpenClaw、微信、身份绑定、探针和提醒：B2/微信范围，本次全部未测。
- 当前没有提交号或锁文件；修复复验前应重新记录源文件哈希或提交号，避免把不同工作区快照混为同一版本。

初测建议的六项修复均已完成并通过第 0 节所列复验。剩余未测边界不影响 B1 的局部 C2 通过结论，也不能据此宣称真实 DeepSeek、B2 或阶段 0 整体完成。

## 7. 验证命令与输出摘要

```powershell
.venv\Scripts\python.exe --version
# Python 3.14.7

.venv\Scripts\python.exe -m pytest
# 执行方基线：15 passed in 0.14s

.venv\Scripts\python.exe -m pip check
# No broken requirements found.

.venv\Scripts\python.exe -m compileall -q src tests
# 退出码 0

.venv\Scripts\wife-agent.exe "查询本月虚拟预算" --provider offline --request-id C2-INSTALLED-CLI-001
# 退出码 0；status=success；两次模型请求、一次 query_budget、available_cents=121350 对应回答 1213.50 元

.venv\Scripts\python.exe -m pytest -o addopts='' --tb=no
# collected 66 items
# 6 failed, 60 passed in 0.65s
```

测试失败是按冻结契约编写的独立断言产生的预期证据；本次没有修改 `src/wife_system/` 实现代码。

修复复验追加命令与结果：

```powershell
# 原六项失败定向复跑
.venv\Scripts\python.exe -m pytest -o addopts='' --tb=short <六个原失败 node id>
# 6 passed in 1.36s

.venv\Scripts\python.exe -m pytest -o addopts='' tests\independent --tb=short
# 51 passed in 1.57s

.venv\Scripts\python.exe -m pytest -o addopts='' --tb=short
# 77 passed in 1.60s

.venv\Scripts\python.exe -m pip check
# No broken requirements found.

.venv\Scripts\python.exe -m compileall -q src tests
# 退出码 0
```

测试智能体只修改了并发独立测试的同步夹具、本文档和自己的状态文件；六项产品修复来自执行智能体的 `src/` 与执行方测试改动。
