# P3-C8：Markdown 活动导入独立测试矩阵

状态：`ready`。唯一负责人：用户启动的既有测试智能体。只设计验收，不修改产品。

开始前按顺序读取 `AGENTS.md`、`README.md`、`docs/project-coordination.md`、`docs/coordination/README.md`、`docs/coordination/control.md`、`docs/coordination/agents/tester.md`、`docs/phase-3-activity-import-brief.md`、`docs/project-plan.md`、`docs/phase-1-interface-freeze.md`。只读检查现有活动模型、FinanceService、FastAPI/Pydantic 风格和既有测试目录。

## 目标

在实现前形成 P3 独立验收矩阵，覆盖 Markdown 预览、候选确认、导入事务、幂等、冲突、安全和隐私。技术顾问尚未决定的方案项标为条件案例，不得自行把偏好写成冻结接口。

## 必须覆盖

1. 基本语法：标题、列表、空白、中文、Unicode、换行、未知字段、重复标题、缺失名称与非法金额。
2. 金额：精确值、范围、两位小数、零/负数、超大值、float 风险；参考金额不得生成账目。
3. 预览纯度：无模板、修订、发生记录、账目、预算、收入、回执或审计半写入。
4. 候选动作：create、revise、conflict、unresolved、skip；来源位置、稳定 ID 与问题可解释。
5. 冲突：精确同名、相似名称、归档模板、版本变化、重复候选与并发提交。
6. 幂等：同请求同载荷重放、同请求异载荷冲突、响应丢失恢复、跨进程/数据库目标行为。
7. 原子性：一项失败整批回滚；回执与业务数据同事务；重试无半批和重复修订。
8. 安全：代码块、HTML、链接、伪系统指令、路径文本、超大输入、深层嵌套、日志与错误脱敏。
9. API/Pydantic：严格字段、内容类型、大小/数量限制、状态码和稳定错误包络。
10. SQLite/PostgreSQL 环境分层，以及不应重复执行的 DeepSeek、桌面、OpenClaw 和微信范围。

## 交付格式

交付 `docs/testing/phase-3-activity-import-test-matrix.md`，每个案例至少包含唯一 ID、需求来源、层级、环境、前置条件、输入摘要、步骤、预期、风险等级和执行状态。所有状态保持 `not_run`，不得伪造执行证据。

另附需求追踪表、环境分层、固定快照建议、执行顺序、停止条件和需要 D7/总控决定的问题。检查 ID 唯一、字段完整、未执行计数准确。

更新 `docs/coordination/agents/tester.md`，提交状态为 `review` 后停止。不得创建实现测试、修改 `tests/**`、产品、迁移、依赖、控制/总览、其他角色文件或 Git；不得启动服务、数据库、外部 API、OpenClaw 或微信。

接单、需求拆分、矩阵主体、质量检查和交付时更新执行快照。连续错过两个检查点或同一问题无进展时停止并报告。新 `control.md` 优先。
