# P3-D7：Markdown 活动导入技术方案

状态：`ready`。唯一负责人：用户启动的既有技术顾问。只做方案，不实现产品。

开始前按顺序读取 `AGENTS.md`、`README.md`、`docs/project-coordination.md`、`docs/coordination/README.md`、`docs/coordination/control.md`、`docs/coordination/agents/technical-adviser.md`、`docs/phase-3-activity-import-brief.md`、`docs/project-plan.md`、`docs/phase-1-interface-freeze.md`。随后只读检查现有活动模型、DTO、`FinanceService`、FastAPI 组装和迁移链。

## 目标

为“Markdown → 候选预览 → 用户确认 → 活动模板原子导入”选择首版技术方案，给出足以让总控冻结 `P3-IF-001` 的数据、API、幂等、事务和安全边界。

## 必须比较并决定

1. Markdown 解析：严格自定义语法、现有 Markdown AST 库、模型结构化提取或分阶段混合方案。说明首版是否需要新依赖和联网。
2. 预览状态：持久化 import batch/candidate，或无状态摘要与重新解析。比较恢复、并发、隐私和实现复杂度。
3. 数据模型：是否新增导入批次表；活动组合是否本阶段建模；金额范围如何与现有单一 `reference_minor` 协调。
4. API：建议准确端点、Pydantic 请求/响应、候选动作、确认字段、状态码、稳定错误码、大小和数量限制。
5. 提交：整批事务、现有 `FinanceService` 的复用方式、请求幂等、版本冲突、失败回滚和响应丢失恢复。
6. 安全与隐私：prompt injection、代码块/HTML/链接、超大输入、Unicode、日志脱敏、原文保存策略和来源追溯。
7. 工程边界：建议代码目录、迁移影响、SQLite/PostgreSQL 分工、执行方测试范围与独立验收重点。

每个关键选择至少给一个有意义的替代方案、取舍和最终推荐。不要为了覆盖术语引入 LangChain、LangGraph、RAG 或模型调用；只有实际需求支持时才建议。

## 交付物

- `docs/phase-3-d7-activity-import-advice.md`
- 更新 `docs/coordination/agents/technical-adviser.md`

建议文档必须包含：现状差距、用户流程、推荐架构图、候选数据结构、API 示例、状态/事务图、错误表、文件所有权、依赖建议、实施顺序、风险、未决定项，以及给总控的冻结清单。面向用户的正式教学由头脑风暴总控结合后续实际代码完成；本任务提供准确的代码位置和学习要点即可。

## 边界与停止

全部产品、测试、迁移、依赖、其他角色文件和 Git 只读。不得写实现、启动服务、安装依赖、联网调用模型、操作 OpenClaw/微信或真实数据。状态只能提交 `review`；不得自行冻结接口或派发执行任务。

接单、完成现状核对、方案比较、推荐形成和交付时更新自己的执行快照。连续错过两个检查点或同一问题无进展时停止并报告。新 `control.md` 优先。
