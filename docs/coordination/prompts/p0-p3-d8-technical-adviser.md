# P0-P3-D8：阶段 0～3 实现后教材与 PDF

## 角色与任务

- 角色：用户侧边栏中既有的“技术顾问”任务
- 任务编号：`P0-P3-D8`
- 固定代码输入：本地提交 `6e89762 Complete P3 activity Markdown import`
- 目标：把阶段 0、阶段 1、阶段 2、阶段 3 的实际实现分别整理为一份可学习的中文教材，并分别生成经过视觉检查的 PDF
- 交付状态：只能到 `review`；由头脑风暴总控核对后决定 `complete`

开始前必须按 `AGENTS.md` 读取：

1. `README.md`
2. `docs/project-coordination.md`
3. `docs/coordination/README.md`
4. `docs/coordination/control.md`
5. `docs/coordination/agents/technical-adviser.md`
6. 本任务卡
7. PDF skill：`C:\Users\xuhaolin\.codex\plugins\cache\openai-primary-runtime\pdf\26.915.20218\skills\pdf\SKILL.md`

不得把既有教学文档的存在写成“用户已经学过”。P0-D2、P2-D6、各阶段技术建议和运行说明只是教材输入，需要结合最终代码重新核对、重新组织。

## 教学对象与共同要求

用户会 Python、会基础 Git，前后端经验较少，正在通过本项目学习主流 AI Agent 应用工程。教材必须：

- 使用中文，从实际问题、数据流和代码开始讲，不堆砌术语；
- 首次出现 HTTP、JSON、DTO、ORM、migration、事务、幂等、Agent tool loop 等术语时解释；
- 每个技术点都说明：解决的问题、所在架构层、实际代码位置、输入输出、边界和暂不采用的替代方案；
- 使用经过脱敏的虚拟示例，不写 API key、个人财务数据、账号标识、微信标识或私密日志；
- 代码链接和行号必须来自提交 `6e89762`，不得凭记忆编造；
- 每册包含学习目标、前置知识、主数据流、关键代码、常见误区、测试证据、阶段练习和检查题；
- 区分“代码当前实现”“接口冻结要求”“测试证据”“未来规划”，不得把规划写成已经实现；
- 不把测试通过描述成绝对正确，不把 SQLite 证据外推成 PostgreSQL 证据。

## 四册教材范围

### 第一册：P0 最小 Agent、HTTP 与微信桥接

输出：

- `docs/teaching/p0-agent-http-wechat.md`
- `output/pdf/p0-agent-http-wechat-teaching.pdf`

至少讲清：

1. 最小 Agent 的模型调用、工具注册、参数校验、工具执行循环、停止条件和错误返回。
2. FastAPI 健康检查与随机探针，请求编号、时间戳、随机回执和进程内幂等。
3. Python HTTP 服务与 TypeScript OpenClaw 桥接之间的数据流。
4. 微信只承担手机消息入口，Windows 桌面端是另一个入口，两端如何共用后端。
5. DeepSeek 负责语言理解与回答，确定性工具负责计算和写入；没有 API key 时哪些功能仍可运行。
6. 阶段 0 自测、独立测试和真实微信验证分别证明了什么。

主要输入：

- `docs/phase-0-interface-freeze.md`
- `docs/phase-0-d2-bridge-teaching.md`
- `docs/b1-running.md`
- `docs/b2b-running.md`
- `docs/testing/phase-0-c2-b1-report.md`
- `docs/testing/phase-0-c2-b2b-report.md`
- `docs/testing/phase-0-w1-wechat-report.md`
- 当前 `src/wife_system/agent/**`、FastAPI 探针和 `integrations/openclaw/**` 实现

### 第二册：P1 财务数据底座

输出：

- `docs/teaching/p1-finance-data-foundation.md`
- `output/pdf/p1-finance-data-foundation-teaching.pdf`

至少讲清：

1. 为什么财务事实放关系数据库，Agent 不能靠聊天记忆代替账本。
2. SQLAlchemy ORM、Pydantic DTO、service、repository/session 和 Alembic migration 的职责。
3. 整数分、账户、交易、分录、活动模板与修订、活动发生、预算和收入怎样关联。
4. 单事务、回滚、幂等回执、乐观版本和数据库约束怎样保护财务正确性。
5. SQLite 开发与 PostgreSQL 目标库的差异，以及真实 PostgreSQL 门禁的必要性。
6. P1 的三个缺陷与 PostgreSQL claim 缺陷教会了什么。

主要输入：

- `docs/phase-1-interface-freeze.md`
- `docs/phase-1-d3-data-advice.md`
- `docs/b3-data-running.md`
- `docs/testing/phase-1-c4-data-report.md`
- `docs/testing/phase-2-c7-r2-postgresql-report.md`
- 当前 `src/wife_system/finance/**`、P1 migrations 和相应测试

### 第三册：P2 财务 Agent 工作流

输出：

- `docs/teaching/p2-finance-agent-workflow.md`
- `output/pdf/p2-finance-agent-workflow-teaching.pdf`

至少讲清：

1. 自然语言请求如何进入 `AgentRunner`、`ToolRegistry`、工具参数和 `FinanceService`。
2. 模型负责理解与选择工具，权限、金额、确认、幂等、事务和成功结论为什么由程序控制。
3. `pending_action` 为什么存在，候选确认、暂停恢复和 24 小时边界怎样工作。
4. 结构化输出、可信上下文、错误映射和隐私日志的边界。
5. 为什么当前保留显式工具循环，没有为了术语覆盖引入 LangGraph。
6. P2 本地测试、受控时钟和 PostgreSQL 测试分别覆盖什么。

主要输入：

- `docs/phase-2-interface-freeze.md`
- `docs/phase-2-d5-finance-agent-advice.md`
- `docs/phase-2-d6-agent-teaching.md`
- `docs/p2-a-running.md`
- `docs/p2-time-r1-running.md`
- `docs/testing/phase-2-c6-agent-report.md`
- `docs/testing/p2-time-c2-report.md`
- 当前 Agent、API、finance service 和对应测试

### 第四册：P3 Markdown 活动导入

输出：

- `docs/teaching/p3-activity-import.md`
- `output/pdf/p3-activity-import-teaching.pdf`

这是用户特别要求的 P3 实际技术完整讲解。至少讲清：

1. `Markdown → Pydantic → parser → service → repository/model → transaction → response` 的完整数据流。
2. 为什么采用离线确定性解析，不让模型直接产生数据库写入。
3. 受限 Markdown、Unicode、安全输入、整数金额和金额上下界。
4. 预览、候选动作、用户确认、原子提交和完整回滚。
5. HMAC 内容摘要、幂等键、请求指纹、回执、重放和重复载荷冲突。
6. PostgreSQL 行锁、乐观版本、唯一约束和名称竞争。
7. Alembic migration 与 82 字符外键名缺陷为什么需要真实 PostgreSQL 才能发现。
8. 89 项矩阵、执行方测试、独立测试、固定快照和总控验收的不同职责。
9. 这些 API 将怎样供 P4 桌面端调用；不得提前决定 P4 技术方案。

主要输入：

- `docs/phase-3-interface-freeze.md`
- `docs/phase-3-d7-activity-import-advice.md`
- `docs/b5-activity-import-running.md`
- `docs/testing/phase-3-c9-r2-activity-import-report.md`
- `src/wife_system/activity_import/**`
- `src/wife_system/api/activity_import_routes.py`
- P3 models、migration、执行方测试和独立测试

## PDF 制作与验收规则

严格遵循 PDF skill。第一次创建 PDF 前，必须且只能成功执行一次：

```powershell
node container_tools/mark_artifact_operation_started.mjs --operation-kind create --expected-output-count 4 --output-format pdf
```

然后：

1. 优先使用工作区已有的 ReportLab、pypdf、pdfplumber 和 Poppler；不得自行安装依赖。若关键依赖缺失，按 `blocked` 记录并向总控报告。
2. 中间文件放在 `tmp/pdfs/`，最终 PDF 放在 `output/pdf/`。
3. 选择并嵌入本机可用的中文字体；不得出现中文方框、缺字或字体替换导致的错位。
4. 四册使用统一封面、目录层级、页眉、页脚、页码、配色、代码块和提示框样式，同时每册可以独立阅读。
5. Mermaid 图不能作为未渲染源码直接塞进 PDF；使用可读的矢量/位图图形或排版清晰的文本流程图。
6. 每次有意义更新后重新渲染全部 PDF 页面为 PNG，逐页检查文字裁切、重叠、表格跨页、代码溢出、黑块、空白页和页码。
7. 使用 pypdf 或 pdfplumber 重新打开最终 PDF，核对文件可读、页数合理、标题存在、文本非空；视觉检查不能被纯文本提取替代。
8. 清理临时渲染文件，只保留需要的源 Markdown、最终 PDF 和必要的可复现生成脚本。生成脚本放在 `tools/teaching_pdf/`。
9. 最终回复按 PDF skill 要求，对四份最终 PDF 各使用一次 `:codex-file-citation{... purpose="output"}`，不得引用 PNG 或临时文件。

## 教学使用方式

四册教材先一次性制作完成，之后用户按 P0 → P1 → P2 → P3 顺序学习。技术顾问在最终回复中：

1. 说明推荐学习顺序和每册预计学习单元，不宣称用户已经学会。
2. 从 P0 第一单元开始给出一个很短的开场说明和第一个练习；完整内容以 PDF 为准。
3. 后续根据用户回答逐单元教学，不要求用户一次读完四册。

## 文件边界

允许新增或修改：

- `docs/teaching/README.md`
- `docs/teaching/p0-agent-http-wechat.md`
- `docs/teaching/p1-finance-data-foundation.md`
- `docs/teaching/p2-finance-agent-workflow.md`
- `docs/teaching/p3-activity-import.md`
- `output/pdf/p0-agent-http-wechat-teaching.pdf`
- `output/pdf/p1-finance-data-foundation-teaching.pdf`
- `output/pdf/p2-finance-agent-workflow-teaching.pdf`
- `output/pdf/p3-activity-import-teaching.pdf`
- `tools/teaching_pdf/**`
- `docs/coordination/agents/technical-adviser.md`

禁止修改：

- 产品代码、migration、执行方测试、独立测试和测试报告；
- 接口冻结、控制文件、总览、其他角色日志；
- 依赖声明、Docker、OpenClaw、微信或任何外部配置；
- 所有 Git 状态。

无需启动产品服务、Docker、DeepSeek、OpenClaw 或微信。只读检查当前代码和既有测试证据。如果代码与旧教学资料冲突，以提交 `6e89762` 的代码和最终验收报告为准，并在教材中解释差异。

## 进度与停止条件

- 接单、每完成一册源 Markdown、完成第一版四册 PDF、完成视觉 QA、交付时，更新技术顾问自身日志。
- `Current execution snapshot` 必须写明正在制作哪一册、最近完成页面/章节、下一个检查点和可观察命令会话。
- 单个生成或渲染操作预计超过五分钟时，先记录检查点；至少每十分钟或每个实质输出更新心跳。
- 连续两个检查点没有有效进展，安全停止当前生成过程，保留现场，报告具体卡点、错误、已尝试方案和需要总控共同决定的问题，不得无限重试。

## 完成条件

1. 四份 Markdown 教材和四份 PDF 均存在，内容分别对应 P0、P1、P2、P3。
2. 所有实际代码链接、技术结论和测试数字与提交 `6e89762` 及最终报告一致。
3. 四份 PDF 完成逐页 PNG 视觉检查及重新打开验证，无已知排版缺陷。
4. 没有修改禁止范围，没有 Git 写操作，没有泄露凭据或个人信息。
5. 技术顾问日志记录交付物、页数、验证方法、剩余限制和四份 PDF 摘要。
6. 最终停在 `review`，等待头脑风暴总控验收。
