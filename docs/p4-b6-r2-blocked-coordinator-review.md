# P4-B6-R2 受阻交付总控审查

- 审查时间：2026-09-26 16:26，Asia/Shanghai
- 审查角色：头脑风暴总控
- 被审查任务：`P4-B6-R2`
- 结论：执行智能体按任务卡正确停止；R2 保持 `blocked / finished`，尚不能进入 `review`，不得派发 P4-C11。

## 1. 已接受的本地交付事实

执行方报告的 100 文件边界可以逐项核对：`unchanged=76`、`changed=20`、`added=4`、`deleted=0`。清单中除运行说明自身外的 99 个普通 SHA-256 全部与当前文件匹配；运行说明的最终普通 SHA-256 也匹配 `864ba8b17bfb19426a5b32903071d4b824ca05a3cff6900972b49ebd31fd8103`。按报告声明的 `path<TAB>sha256<LF>` 算法复算清单总摘要，结果匹配：

```text
P4-B6-R2-END-SHA256:d8ff817da54875bcf2ca899a9b739e11438cd7f710f6e6ebeddbf6f8d2d588d5
```

本地执行方测试的通过结果可作为开发证据，但 22 个 PostgreSQL 跳过项不计为通过，也不构成独立验收。

## 2. 快照说明

运行说明声明的自引用 canonical SHA-256 为 `a5c4f63500712048bd35a691fe135fb73b20bee3c94f63be6f5781c7f18f53d9`。该值在文件中出现三次；对三个位置的全部八种置零组合逐一复算，都不能得到声明值。因此不把这个自引用值作为下一任务的信任根。

这不推翻其余 99 个普通文件摘要或可复算的清单总摘要。总控已从当前 100 个真实文件重新生成独立普通摘要清单：

- [P4-B6-R2-S1 起点清单](coordination/snapshots/p4-b6-r2-s1-start.sha256)
- 清单文件普通 SHA-256：`d6357a6e2612e5cc56217759780eaa3ab205930455e459eb4326f318965b194b`
- 清单格式：100 行 `path<TAB>ordinary_sha256<LF>`；清单本身不纳入清单，避免自引用。

后续交付不得再把自引用 canonical 摘要作为唯一复算依据。执行方交付普通文件摘要，最终稳定快照由总控在停止修改后生成。

## 3. 已确认的三个结构缺口

### 3.1 memory candidate 缺少提出时的 Profile 版本

`P4-IF-002` 冻结 candidate 的 target、Profile ID 和 Profile version 必须在 proposal 时固定。当前 `memory_candidate` 只有 `proposed_by_profile_id`，确认时只能解析当前 Profile，不能证明它仍是提出候选时的同一版本。

决定：在现有 `p4_host_state` migration 和 ORM 中增加非空 `proposed_by_profile_version VARCHAR(32)`；propose 保存实际版本，confirm 重新解析同 ID 并比较版本，再校验 module enablement 和 grant。版本不一致时以 409 `memory_candidate_conflict` 拒绝，零 memory item，事务内 receipt 回滚。

### 3.2 memory item 缺少 invalidated 状态

`P4-IF-002` 和 D10 均冻结 `active -> invalidated -> deleted tombstone`。当前数据库和 ORM check 只允许 `active/deleted/superseded`。

决定：约束加入 `invalidated`，实现 active/version CAS invalidation；胜者清空 `value_json` 和 `tags_json`，从检索立即排除，保留不含内容的审计字段。delete 允许从 active、superseded 或 invalidated 进入 deleted。supersede 与 invalidate 并发时只能有一个 CAS 胜者。

### 3.3 agent run 没有持久化 module version

`CompiledExecutionPlan` 声明绑定 module/version，但 `agent_run` 只有 `module_id` 和 `profile_version`。当前 compiler 将 `definition.manifest.version` 错误地与 `row.profile_version` 比较；模块版本和 Profile 版本恰好同为 `1.0.0`，使本地测试未暴露该错误。

决定：在现有 migration、ORM 和 start/resume/takeover 链加入非空 `module_version VARCHAR(32)`。P0～P3 旧 run 按现有 migration 已冻结的内置 `daily_finance` 版本回填 `1.0.0`；start 保存模块与 Profile 两个独立版本；compile 分别比较 `manifest.version == row.module_version` 和 `profile.version == row.profile_version`。本轮沿用稳定 409 `profile_changed` 表示已持久化执行计划版本发生变化，不扩展外部错误合同。

## 4. migration 裁定

P4 尚未验收或发布，`p4_host_state` 仍是待验收的 P4 migration。按 `P4-IF-002` 继续修正现有 P4 revision，保持三个 P4 migration 和单一 head，不新增第四个 revision。

- `memory_candidate` 与 `memory_item` 都由 `p4_host_state` 新建，P0～P3 不存在这些表，因此没有已验收历史数据需要伪造回填；随机测试 schema 从头升级即可得到正确结构。
- `agent_run` 来自 P2，`module_version` 必须遵循现有 `module_id/profile_id/profile_version` 的 nullable → 回填 → non-null 迁移顺序。
- downgrade 会整体删除 P4 的 memory 表，所以 `invalidated` 不需要映射为其他状态；`agent_run.module_version` 与同批 P4 列一起删除。
- 不对任何用户数据库执行破坏性重建。本轮只修改 migration 源码并在 SQLite 本地验证；真实 PostgreSQL 升降级留给下一门禁任务。

## 5. Docker 与后续顺序

审查时没有 `Docker Desktop` 或 `com.docker.backend` 进程，`dockerDesktopLinuxEngine` 命名管道不存在，Docker API 和 Compose 状态均不可访问。R2 的真实 PostgreSQL 门禁因此仍为 `unverified`。

下一步只派发 `P4-B6-R2-S1` 给既有执行智能体，完成三个结构缺口和本地回归，不启动 Docker。S1 停止后，总控核对新普通摘要；随后再恢复 Docker，并派发 PostgreSQL-only 的 S2 门禁。技术顾问和测试智能体继续停止，P4-C11 仍不得开始。
