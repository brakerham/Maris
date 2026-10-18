# R9-R2 总控核对：原生辅助读取上下文与分段记录

2026-10-18。R9-R2保持`blocked / finished`。接受共享路径身份、现场前置及真实H1身份/ready/release已通过的有限结论；H1原生业务未通过，产品原因仍未验证。发布 [P4-C12-R9-R3](coordination/prompts/p4-c12-r9-r3-storage-windows-tester.md)，仅修正辅助读取上下文和分段取证，再沿有限额度续验。不是产品返修。

## 本轮亲自核对

- [114项交付](../tests/independent/desktop/evidence/r9-r2/delivery.sha256)全部匹配，清单摘要`31722e61175b5dec530fb596178352e77a31523cd7c20c9d8074808426173be3`；89份首次材料全部匹配，清单摘要`4644653d9e9aeb7f8ef27cdcd5e02aaf19067e930304594331d00549d38eccf7`。
- 编辑协调前1077起点只有tester、主报告、人工清单、矩阵四份授权变化，无缺失，staged=0。旧主报告/人工清单应保持追加；矩阵B保持1 passed、1 failed、19 blocked、3 not_run，不因工具通过新增业务通过。
- [native首次结果](../tests/independent/desktop/evidence/r9-r2/helper-H1/native-result.json)仅1条availability比较为true，随后operation_error；[controller实际结果](../tests/independent/desktop/evidence/r9-r2/helper-H1/process.json)记录helper exit1、约8207ms、release已发、无强制清理及owned/listener/window为0。owner/outbox其余6比较未执行。当前不重复动态核验资源。
- 原R9、R9-R1、R9-R2三份profile/continuity各63个文件的字节数、摘要及路径库存亲自复算一致。owner/outbox各235/317 bytes、文件存在、具有safeStorage识别的版本前缀；未解密、不输出密文或正文。固定构建932、包140、资源67、dist73、依赖12677及执行方157证据采用已由114清单绑定的[end-audit](../tests/independent/desktop/evidence/r9-r2/end-audit.json)，不冒称本轮再次全量扫描。

## 已确认的工具缺口与归因限制

1. [H1 controller](../tests/independent/desktop/r9-r2-h1-run.mjs)新建空`helper-profile-H1`；[native](../tests/independent/desktop/r9-r2-h1-native.cjs)把userData设为该目录，却从另一目录`profile-main`读取owner/outbox密文。controller没有将产品的Local State预置到辅助环境。
2. 总控只读比较R9-R2现场两份Local State的安全元数据：文件均存在，`os_crypt.encrypted_key`均非空，字段字符串不相等。只记录布尔，不输出密钥字段、明文或密文。包裹密文不同不等于数学上证明原始密钥不同；准确结论是**本次没有保持相同加密上下文**，与跨上下文解密失败假设一致。
3. native把readFile、decryptString、JSON.parse串联后由统一catch记录为operation_error，首次证据无法确定异常在哪一步。当前文件存在及前缀有效也不能倒填当时读取/解密已成功。availability不证明这份既有密文能够在当前上下文解开。
4. 上一张总控卡明确要求helper目录隔离，但没有要求隔离目录预置同源加密上下文；这是总控合同遗漏，不能只归责测试方。当前仍不认定产品损坏、设备不支持或已证实的旧H1根因。

精确版本官方依据：Electron [v44.4.5同步safeStorage](https://github.com/electron/electron/blob/v44.4.5/shell/browser/api/electron_api_safe_storage.cc)调用OSCrypt；[browser_process_impl.cc](https://github.com/electron/electron/blob/v44.4.5/shell/browser/browser_process_impl.cc)从sessionData的Local State加载配置；[electron_browser_main_parts.cc](https://github.com/electron/electron/blob/v44.4.5/shell/browser/electron_browser_main_parts.cc)在用户入口后准备配置并在Windows初始化OSCrypt；[electron_paths.cc](https://github.com/electron/electron/blob/v44.4.5/shell/common/electron_paths.cc)默认sessionData回落userData。以上支持预置同源配置的工具修正路线，不代替真实H1解密结果。Chromium精确tag源码本轮访问未成功，不用main分支行为填补。

## 决定

- 保留所有旧源码、失败、目录和profile。新helper仍隔离，spawn前仅向全新helper目录复制当前已验证虚拟产品profile的完整Local State原字节；顶层同步绑定userData和sessionData。H1只读产品文件，H2/H3/H4都复用这一上下文规则，防止H2用另一套上下文生成产品不能读取的虚拟密文。
- 读取、解密、解析、schema、continuity和结果写入分别即时记录enter/terminal与安全分类。允许在无Electron、无产品、无真实密文的局部工具开发中验证记录器失败分支；不重跑38项已通过路径集合或现场Node门禁，只核对未变来源及本次新参数接线。
- 显式新增**一次**H1恢复额度，辅助系列上限由5改6，已用2，剩4为新H1/H2/H3/H4各一次。产品仍已用1/上限8/剩7。新H1通过后在同任务继续尚未执行的Windows；失败后带准确阶段停止，不再泛化为只有operation_error的交接。
- 这是对已明确上下文遗漏的受限修正，不保证本次恢复成功。旧W1、8退出节点、48兼容、模块/冷入口/恢复等通过不重跑。QUIT-001普通关闭有限结论保持；LAZY-001/UI-02及P4-B尚未关闭。

总控只进行了只读代码/证据核对、安全元数据比较和协调写入；没有启动Electron、H1、EXE、后端、测试、安装或打包。内部`h1_native_review`只读子审查确认上述上下文缺口并强调先复制、后启动和准确归因，不写产品或测试文件。新任务与[新起点](coordination/snapshots/p4-c12-r9-r3-start.sha256)交既有测试方，实际接单另核实；仅建立未完成状态的本地检查点，不推送。

发布前已再次核对9项target与两份各11项冻结归档源码，全部匹配；矩阵120条原行不变，主报告/人工清单仅追加。新卡经内部只读复核无阻断，已明确ready后只核对实际路径和加密字段，不因Local State无关字段更新误判失败。新起点1192项，本地检查点精确124路径；快照不包含自身，提交结果以最终Git核验为准。
