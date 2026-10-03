# E2：静态依赖形式的独立反证

E1新增证据：CLI6982ms/exit0；jsdom顶层动态import5903.349ms，React16.004ms，body正常进入；未触达产品或Router。它证明固定安装依赖可完成求值，但动态逐段导入不等于旧A静态形式。

本次唯一问题：换回旧A同样的三个静态运行时依赖vitest/jsdom/React、仍为全新极小模块与worker，是否停在收集/依赖求值，还是能进入正文？不复制旧A的main/DOM/Router/fixture/四断言代码。首个module_evaluation_complete只在静态依赖全部完成后记，不把它伪称依赖开始前。

共用config/plugin/setup/controller保持E1摘要；只新增本目录config和17行以内的极小测试模块及这份问题说明，专属cache和空node_modules保证config临时产物留在新目录。静态来源与E1相同，不配置Router门面，因为该门面不属于本问题的三项依赖。旧A动态main文本/其他正文不存在是明确差异，不能以本次成功倒写旧A根因。

这是CLI2/3，test10秒、总体120秒（118秒收口）、累计动态≤360秒；失败不修改本次源码重跑。若也正常完成，固定依赖不可加载或普遍静态导入死锁无支持，不消耗第3次预算盲试；根因unknown但交付解耦A/B和阶段化初始化的可执行路线。
