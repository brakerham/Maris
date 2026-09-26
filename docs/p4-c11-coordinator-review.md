# P4-C11 独立验收总控核对

## 1. 当前结论

- 核对时间：`2026-09-27 00:12 Asia/Shanghai`
- C11 交付状态：保持 `review / finished`。
- P4-A 状态：暂不标记 `complete`；产品实现没有发现新的 P0/P1，但独立迁移证据存在一处必须补齐的覆盖缺口。
- 下一任务：`P4-C11-R1`，只由既有测试智能体修复独立测试证据和报告，不修改产品、migration、执行方测试或依赖，不重跑全部 64 项与全部历史回归。

## 2. 已通过的总控核对

总控直接复算得到：

```text
P4 产品固定快照
entries=105
matched=105
missing=0
mismatch=0
manifest_sha256=65ee400893171d6caf19f2bf5adf20a4432f1f3c8048d5c381b718fc10360126
```

交付摘要匹配：

```text
docs/testing/phase-4-c11-host-foundation-report.md
bd88bdf7437cd2120ee08e6d5ca8928e8445776321f86d2fb9d5e83ade25ee56

docs/testing/phase-4-modular-agent-host-test-matrix.md
3483ca3fbda8723b1cd627ed0d0aceb31c88c3f3c1dad776db2cea0417266c89
```

矩阵和报告结构匹配：

- P4-A：64 行，64 行 `passed`；
- P4-B/C/D：56 行，56 行 `not_run`；
- 120 个 ID 全部唯一；
- 报告包含 64 行逐项证据、8 行 P0 和 14 行 P1 审计映射；
- 测试方没有修改 105 文件产品快照，没有增加 `skip/xfail`；
- 项目 Compose 最终为空；
- 两个 P0 uvicorn 回环失败与 P2-C6 的既有 Windows 八秒健康等待记录一致，均未进入业务断言，不构成 P4-A 产品缺陷。

## 3. 必须补齐的独立证据

### 3.1 历史迁移证据被削弱

测试方修改了：

```text
tests/independent/finance/test_migration_sqlite_contract.py
```

其中原本从 `FIRST_REVISION = bfc163b9b8e9` 开始的测试被改为直接 `upgrade(..., HEAD_REVISION)`，随后才执行 P4→P3→P4。这样能够证明当前 head 往返，却不再证明首个 P1 revision 中已有事实经过 P2、P3、P4 migration 后仍保持。

新增 C11 SQLite 用例只覆盖空库和 head→P3→head；新增 C11 PostgreSQL 用例在 P4 head 写入事实后再降到 P3并升回 P4。两者都不能替代“带 P0～P3 历史的旧 schema 正向升级到 P4”这一冻结门禁。

因此 C11-R1 必须用 revision 对应的直接 SQL 或独立低层 fixture 创建旧 schema 数据，再升级到 P4；不得通过从最新 head 开始、删除断言、改测试名称或引用执行方通过数字规避。

### 3.2 取消错误码属于合同演进，不应伪装成 fixture 修改

测试方把旧 P2 独立断言从：

```text
confirmation_required
```

改为：

```text
pending_action_cancelled
```

这不是 fixture 调整，但它与 D10 已冻结的 P4 状态合同一致：cancelled pending 再 confirm 必须返回 409 `pending_action_cancelled` 且零写入。该变化不需要回退，也不是产品回归；C11 报告必须明确把它记录为 P4 合同演进，同时保留原业务不变量：取消终态、确认失败、财务事实为零。

## 4. C11-R1 验收口径

C11-R1 通过需要同时满足：

1. 105 文件产品快照继续 `105/105` 匹配；
2. 23 文件测试方起点快照开始前全部匹配；
3. SQLite 使用旧 revision 的虚拟 P1/P2/P3 事实正向升级到 P4，并验证事实、关系和 bootstrap owner 回填；
4. PostgreSQL 在随机 P3 schema 写入代表性 P1/P2/P3 历史事实，再升级到 P4 并验证保留、回填、约束和零孤儿；
5. 原 P1 migration 独立测试不再用“从最新 head 开始”冒充首版升级；
6. 报告准确区分 fixture 适配、P4 合同演进和新增证据；
7. 只定向运行受影响 migration、取消状态和 C11 独立测试；不得重复全部 64 项或全量 P0～P4 回归；
8. Docker 如被使用，只启动 `finance-postgres`，完成后普通 down 并确认 Compose 为空；
9. 测试智能体提交 `review / finished`，最终 `complete` 仍由总控决定。

## 5. Git 边界

C11 尚需 R1 补证，因此 P4-A 产品实现和 C11 测试交付暂不提交。总控只提交本核对、R1 Prompt、两份快照和协调状态；不推送远程、不创建 PR。C11-R1 通过后，总控再把完整 P4-A 实现、执行报告、独立测试和最终验收记录创建为一个本地提交。
