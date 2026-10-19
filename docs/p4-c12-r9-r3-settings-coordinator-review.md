# R9-R3：原生读取通过、设置恢复缺陷与最小返修裁定

2026-10-18核对，2026-10-19恢复协调并发布，Asia/Shanghai；头脑风暴总控。输入为[R9-R3独立报告](testing/phase-4-c12-r9-r3-storage-windows-report.md)、[H1首次原生结果](../tests/independent/desktop/evidence/r9-r3/helper-H1/native-result.json)、[W2首次结果](../tests/independent/desktop/evidence/r9-r3/windows-W2/result.json)。两次协调之间不追溯计为连续执行。本轮总控只读核对和协调，没有运行测试、产品、辅助、安装或打包。

## 1. 接受的证据及范围

- H1同源原生上下文已取得7/7独立比较通过，helper/controller均实际exit0；owner/outbox可读取、结构及虚拟continuity成立，产品副本保持，资源为0。此项阻断解除；不重新运行H1，不回填旧R9/R2未知异常的具体抛错位置，也不把H1替代尚未完成的H2跨产品续启验证。
- W2同一次真实续启首样：已保存theme=dark、privacyMode=true，文件字节未变且取样前settings写入0；Host及页面ready，但页面dataset和两个控件均为system/off。8条通过、4条失败来自同一首样，没有重启取巧。
- 接受 `P4-C12-R9-R3-SETTINGS-001` 为P1产品缺陷：已保存的主题及隐私选择没有恢复到页面。风险是隐私意图失效；没有真实个人数据泄露证据。CMP-06原矩阵风险P2不改，与本次综合缺陷P1分开记录。
- W2失败后普通关窗自然exit0，约367ms，资源为0；不扩大为Tray、注销或其他未运行条件通过。
- P4-B仍为1 passed、2 failed、19 blocked、2 not_run；UI-01接受保持，LAZY-001/UI-02及完整P4-B未关闭。测试方原blocked/finished保留。

## 2. 总控亲自核对与引用边界

170项交付、148项首次材料逐文件匹配；H1实际来源8份、W2来源5份逐文件匹配。1192项起点在总控编辑前只有tester、主报告、人工清单、矩阵四份授权变化，无缺失；staged=0。旧主报告/人工清单相对本地HEAD只追加。矩阵120个唯一ID、12列、原预期与A/C/D保持，唯一整行状态变化为CMP-06。

交付清单SHA-256：`130c4c1e601008998357a32785c71c8454b940d27dab2acbea80403bae669f03`；首次材料清单：`ee47682828cf4341c6cf78b7330446ec5329186998eea42d635ee4f7b1ea8e87`。

[终点审计](../tests/independent/desktop/evidence/r9-r3/end-audit.json)已经绑定固定构建932、产物140、资源67、dist73、完整依赖12677、执行方证据157，以及旧首次68/38/89和三个63项旧profile。本轮复核该审计所在交付的原字节及结论，没有冒称再次遍历整套外部依赖或再次解密。新profile的产品运行后变化与settings/continuity不变分别记录，不用文件摘要推断未运行的H2内容正确。

本地暂存后对全部180个新/改路径检查，发现四处首次材料的行尾空白：现行及两份冻结归档的r9-r3-storage.cjs第23行、windows-os.diff第48行。测试方先前普通diff未覆盖这些未跟踪新增文件，总控不沿用其“全部无空白”结论；为保持冻结原字节，不修改这四处。协调新增文档单独检查无空白错误。该提示不改变H1/W2的实际结果；Git另有既有用户ignore读取限制及LF/CRLF提示，未改全局配置。

## 3. 静态原因和既有设计依据

| 链路 | 当前源码事实 | 裁定 |
| --- | --- | --- |
| 文件→main | [device-settings.ts](../apps/desktop/electron/main/device-settings.ts)的load解析已存设置；[main/index.ts](../apps/desktop/electron/main/index.ts)在创建窗口前await load | 不是设置文件没有保存，也不是main完全不读文件 |
| main→preload | [ipc-contract.ts](../apps/desktop/electron/main/ipc-contract.ts)、[preload](../apps/desktop/electron/preload/index.ts)、[共享合同](../apps/desktop/src/shared/contracts.ts)只有settings.update，没有读取snapshot能力 | 已设计的读取链未实现 |
| renderer→Shell | [module-routes.tsx](../apps/desktop/src/renderer/module-routes.tsx)的DesktopApp从system/false初始化，只在用户操作时更新并保存；[Shell](../apps/desktop/src/shell/Shell.tsx)直接渲染这些值 | 与W2有效首样吻合，不靠增加等待时间解决 |

[D11既有建议](phase-4-d11-windows-shell-technical-advice.md)第119行已要求renderer读取脱敏snapshot，第366行设计了无参deviceSettings.get；[IF-003 §11—13](phase-4-interface-freeze-003.md#11-设备设置)已冻结main持有设备设置、主题与隐私要求。因此本次补上既有设计漏接，不引入新的设置架构或文件格式。D11中的示例命名与实际settings.update命名不同，以下明确适配当前产品名称；不重命名旧写接口，不修改旧冻结文本。

## 4. 本次补充合同（SETTINGS-R8）

1. 新增唯一只读 `window.maris.settings.getSnapshot()`，固定channel `settings:get-snapshot@1`，零参数。沿用现有registerMainHandler及sender、mainFrame、origin、空tuple校验。不能开放任意channel、文件路径、Node、整个DeviceSettings或毛毛跨窗口访问。
2. 响应严格仅包含 `theme: system|light|dark|high_contrast`、`reducedMotion: boolean`、`privacyMode: boolean`。main从已经load的当前有效设置构造新投影对象；renderer做实际运行时严格校验，不以TypeScript强转代替。禁止返回backendMode、关闭策略、bounds、启动项、owner、token、nonce、路径或任何其他字段。原update输入/accepted回执保持。
3. DesktopApp启动读取设置。未取得合法snapshot前不把默认privacy=false的模块内容当作ready展示；允许安全加载态。拒绝/非法响应进入不含内部错误的有限错误态，不能默默显示隐私关闭、写回默认值或自动循环重试。显式重试若实现，只能由用户操作触发；不借此扩展设置页面。
4. 读取完成后，Shell属性、主题控件和隐私控件一致。读取无写入副作用。StrictMode/卸载/失效请求晚到不得写回状态；读取等待时不让未同步控件产生旧值覆盖。runtime、modules、recover通知不重新水合覆盖用户选择，不因此重建相同路由、重载页面或自动重试故障模块。
5. 三字段snapshot只补数据通路；不扩展reducedMotion/主题视觉、毛毛多屏、设置文件schema/迁移或损坏回退策略，不做P4-C设计。正常关闭、现有update保存、outbox和Host语义保持。

内部只读审阅子任务确认该链路和窄范围；没有实施产品修改或替代独立验收。若实现需要改变上述架构、权限、存储或范围，应停止并交总控/技术顾问，而不是在执行任务中自行扩展。

## 5. 下一任务及预算

发布[P4-B7-R8-SETTINGS执行任务](coordination/prompts/p4-b7-r8-settings-executor.md)，新[起点清单](coordination/snapshots/p4-b7-r8-settings-start.sha256)。开发可正常编辑调试、保留红灯；最后一次完整桌面回归后，最多一次新package和两次顺序的新EXE：第一次真实UI保存并普通关闭，第二次在同一新虚拟profile首次取样验证恢复、再正常关闭。两次是不同场景，不是失败重试；任一有效失败停止后续场景。

本轮执行预算独立于Tester R9系列。Tester累计产品2/8、辅助3/6冻结，不能自行使用剩余额度；旧H1、W1、路径工具及所有已过独立集合不重跑。执行方不能关闭SETTINGS-001或修改独立断言。新源码/包交review后，总控再冻结独立W2定向复验及后续场景。

提前记录两项后续工具适配，不让下一次验收再因已知合同差异中断：旧W1 driver把settings键集固定为仅update，新runner必须按本次窄getter明确更新期望；旧R9-R3 W2未执行的后续分支含 `settings.update({closePolicy:...})`，但当前写IPC只接受theme/reducedMotion/privacyMode。后者属于静态可证实的工具/公开接口不一致，未形成新的产品失败；下一Tester卡须在正式目标启动前裁定场景合法配置方式，不能为测试顺手开放closePolicy写权限。原driver和首次证据保持，不在本次Executor中修独立工具。

协调更新和本轮已核对交付保存为明确标注未完成的本地Git检查点，不推送、不宣称P4-B完成。真正P4-C前端前的参考图及模型分工提醒继续保留。
