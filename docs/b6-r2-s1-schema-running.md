# P4-B6-R2-S1 运行时结构补全执行记录

## 状态与边界

- 任务：`P4-B6-R2-S1`。
- S1 状态：`review / finished`。
- 整体 `P4-B6-R2` 状态：继续 `blocked`，等待单独派发的 S2 真实 PostgreSQL 验证。
- 本轮仅完成三个冻结结构缺口及本地执行方验证；没有启动 Docker、PostgreSQL、S2、C11、Electron、OpenClaw、微信、DeepSeek 或真实 provider。
- 未读取真实密钥、账户或个人/财务数据；未修改或运行 `tests/independent/**`；未执行 Git 写操作。

## 起点门禁

- 起点清单：`docs/coordination/snapshots/p4-b6-r2-s1-start.sha256`。
- 清单自身普通 SHA-256：`d6357a6e2612e5cc56217759780eaa3ab205930455e459eb4326f318965b194b`。
- 清单条目：100。
- 接单后逐行复算：`100/100` 匹配，`missing=0`，`mismatch=0`；通过后才修改产品文件。

## 三个结构缺口与数据流

| 缺口 | 代码位置与迁移语义 | 运行时数据流 | 执行方覆盖 |
| --- | --- | --- | --- |
| run module version | `p4_host_state.py` 在既有 `agent_run` 增加 `module_version VARCHAR(32)`；P0～P3 虚拟历史随 `module_id='daily_finance'` 回填 `1.0.0`，再改为 non-null；downgrade 与同批 P4 run 列一同删除。ORM 在 `agent/models.py` 使用独立非空字段。 | `ExecutionPlanCompiler.preflight` 分别返回 manifest version 和 Profile version；`_claim_run` 分别持久化；start、重放接管和执行前 compile 分别比较 `definition.manifest.version == row.module_version` 与 `profile.version == row.profile_version`。任一漂移返回 409 `profile_changed`，provider/tool/领域写均未开始。 | SQLite 空库/历史/round-trip 对字段 non-null、长度 32、回填和单一 head 断言；合法 manifest 使用 module `1.8.0`、Profile `1.4.0` 可正常完成；两种持久版本漂移分别在过期接管路径 fail closed，provider 调用为 0、财务写为 0。 |
| candidate Profile version | `memory_candidate` 新表定义增加非空 `proposed_by_profile_version VARCHAR(32)`；ORM 同步为必填字段，不伪造旧候选历史。 | propose 经 `ModuleRegistry.resolve_profile` 解析实际 Profile，检查模块启用、source module、固定 target 的 grant/kind/operation，并保存实际 ID/version。confirm 使用 candidate 保存的 ID/version 和固定 target 重新解析并复查 grant；Profile 消失、模块禁用、版本变化或 grant 撤销统一为 409 `memory_candidate_conflict`。失败事务不留下 item 或未完成 receipt；reject 不调用 grant validator，模块后来失效仍可减少数据。 | 保存 ID/version、固定 target、四类 confirm 失效、零 item/receipt，以及失效后的 reject 均有定向断言。 |
| memory invalidation | migration 与 ORM 的 `memory_item.status` check 允许 `active/deleted/superseded/invalidated`。 | `MemoryService.invalidate` 先以 operation/key/payload claim receipt，再用 `(user_id,id,status='active',version)` 单语句 CAS；成功时清空 value/tags、保留审计字段、递增 version，并在同事务完成 receipt；提交后才发布脱敏 `memory.changed@1`。retrieve 只读 active；delete 接受 active/superseded/invalidated。supersede 和 invalidate 共用同一 status/version 竞争条件，因此只有一个胜者。 | 正常 invalidation、同键重放、同键异 payload、旧 version、检索排除、事件隐私、delete invalidated，以及 supersede/invalidate 两种先后顺序的单胜者、零败方 receipt/replacement/event 均有断言。 |

## 实际文件变化

相对 100 文件起点清单：`changed=10`、`missing/deleted=0`。另新增本运行说明，并按协作规则更新执行智能体自己的角色日志。

产品文件：

- `migrations/versions/p4_host_state.py`
- `src/wife_system/agent/models.py`
- `src/wife_system/agent/application.py`
- `src/wife_system/host/state_models.py`
- `src/wife_system/host/state.py`
- `src/wife_system/host/factory.py`

执行方测试：

- `tests/agent_finance/test_r2_runtime.py`
- `tests/host/test_migrations.py`
- `tests/host/test_state.py`
- `tests/host/test_postgresql_r1.py`：只同步新增非空字段所需的直接 SQL fixture；本轮未运行该 PostgreSQL 测试。

交付记录：

- `docs/b6-r2-s1-schema-running.md`：新增。
- `docs/coordination/agents/executor.md`：仅更新执行智能体日志与当前执行快照。

未修改 `tests/host/test_api.py`、`tests/host/test_workflows.py`、`tests/agent_finance/test_tools_and_http.py`；它们仍进入相关本地回归。

## 执行方验证

| 检查组 | 结果 | 说明 |
| --- | --- | --- |
| S1 四文件定向 | `44 passed, 1 warning in 40.61s` | migration 8、memory/state 19、module/profile runtime 7、Host API 10。 |
| R2 Host/Agent 定向 | `62 passed, 1 warning in 27.62s` | runtime、state、API、registry、workflow、production factory。 |
| Agent 执行方 | `35 passed, 1 warning in 28.89s` | `tests/agent_finance/**`。 |
| Host 本地执行方 | `79 passed, 1 warning in 61.82s` | `tests/host/**`，显式排除 `test_postgresql_r1.py`。 |
| 全仓非独立、非 PostgreSQL | `326 passed, 1 warning in 112.24s` | `tests --ignore=tests/independent`，并显式排除 activity import、finance、Host 三份 PostgreSQL 文件；无 skip。 |
| Python 编译 | 退出码 0 | `.venv\\Scripts\\python.exe -m compileall -q src tests migrations`。 |
| 依赖检查 | `No broken requirements found.` | `.venv\\Scripts\\python.exe -m pip check`。 |
| 差异格式 | 退出码 0 | `git diff --check` 无空白错误；只输出既有工作树的 LF→CRLF 提示。 |

首次定向运行使用系统默认 Temp 时出现 `4 passed, 40 setup errors`，全部错误均为 pytest 无权读取 `C:\\Users\\xuhaolin\\AppData\\Local\\Temp\\pytest-of-xuhaolin`。改用项目内专用 `--basetemp` 后，第一次因父目录尚不存在再次得到相同 `4 passed, 40 setup errors`；建立专用父目录后重跑为上述 `44 passed`。这两次是测试环境 setup 错误，没有产品断言失败。专用临时目录已在验证后删除。

最终验证没有 failed 或 skipped。唯一 warning 是 Starlette `TestClient` 仍引用 AnyIO 已弃用的 `BlockingPortal` alias；这是既有第三方兼容提示，不影响断言结果。禁用 pytest cache provider 是为了不触碰现有不可写 `.pytest_cache`，没有隐藏测试失败或 warning。

## PostgreSQL 未验证项与资源状态

- 本轮没有运行、连接或收集真实 PostgreSQL 行为证据；S1 结论不包含 PostgreSQL 通过声明。
- 未验证项包括新列在 PostgreSQL 上的真实 upgrade/downgrade、并发 candidate confirm、supersede/invalidate 两连接竞争、receipt/event 原子性和 R1 fixture 重放；这些属于 S2。
- 任务卡禁止本轮启动或查询 Docker/PostgreSQL，因此没有启动容器，也没有执行 compose、volume、prune 或 Docker 全局设置操作；不存在本轮需要关闭的数据库资源。

## 普通 SHA-256 逐文件摘要

以下是相对起点发生变化的 10 个产品/测试文件，按路径排序，格式为 `path<TAB>sha256`：

```text
migrations/versions/p4_host_state.py	e6d71ad36d5a08a77ccc9026094b354213dba38b65b45257680d92198a9d2a96
src/wife_system/agent/application.py	4b955c172f2ca5ee6a31730e1d1ad3fee66bf34f4e205dbcb60ec4fac1159a43
src/wife_system/agent/models.py	b856ef2ab260b6d5fd2c2a265bbbb7b12a05c522e3d5f5b8b717f83e54bd6352
src/wife_system/host/factory.py	69dd107d5435de71a49526e3a0fedfcac513a5356d4945fbacbd9d6ebc58729a
src/wife_system/host/state.py	85a112fd688de3a1c59e234d4331b1f78b893796e063a047e201072fa623e45a
src/wife_system/host/state_models.py	fd954617dd8c57cd2f9b508eb9f069ea108a365853942f985be4ef44580f6d52
tests/agent_finance/test_r2_runtime.py	3c785082470e1f477a9d7b368bbce800dc33d44d226b56a390675aa46c8bea6a
tests/host/test_migrations.py	9e6d77a83887d8c80a7cdd27210d04500d1bd35ae6d8662d9bfbce9ecdaf62d5
tests/host/test_postgresql_r1.py	f4d16b080b4723229e046bd2b816092c1b67bcdd97286c7f7f536b82290e51bc
tests/host/test_state.py	244e199d48f7bbc7a961b9b6aa387ce085997897e664e42a1358fcac779cc16f
```

可复算总摘要：把以上 10 行按路径升序，以 UTF-8、LF 行尾和末尾一个 LF 编码，对整段计算普通 SHA-256，结果为：

```text
P4-B6-R2-S1-CHANGED-10-SHA256:5af6dc68cced09724c53b01c984167da77111ad5e9f546ca6d08646ee5ca8106
```

本运行说明不保存自身摘要，以免制造自引用。文件写定后的普通 SHA-256 记录在执行智能体角色日志；下一份稳定全文件清单由总控在停止修改后生成。

## 交接

S1 已停在 `review / finished`。总控可复核上述 10 文件和本说明；整体 R2 继续因 S2 未执行而保持 `blocked`。执行智能体不自行启动 S2、Docker/PostgreSQL 或 P4-C11。
