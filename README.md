# 确定性因果实验实验室

A deterministic causal laboratory for controlled social experiments.

这是一个可审计的研究原型，不是社会模拟平台，也不是已经完成的人工社会。它把少量显式因果边放在确定的 Tick 里运行，留下完整事件记录，用来检查一次干预是否改变信念、意图、显式行动或资源。

当前没有下一项功能计划。没有研究问题，就不开发。现有模型能够回答的问题，只记录结论。

## 现在实际运行的是什么

已冻结的开环基线是 PR-1～PR-12。132 项测试锁定这份 Python 实现。实验 1～4 已关闭。

自动链停在意图。行动必须显式提交。被接纳的 `support` 或 `oppose` 才给行动者的资源加 1。资源不回到生成、传播、信念或意图。

说明以这些文件为准：

- `docs/BASELINE_EXPERIMENT_SPEC.md`：参数、Tick 槽位、读写集合、复现步骤
- `docs/EXPERIMENT_BOUNDARY.md`：实验结论、因果边界、可辨识边界、准入纪律
- `docs/NEXT_MECHANISM_AUDIT.md`：尚未准入的候选边。列出不等于准备实现
- `docs/RESOURCE_SEMANTICS.md`：资源只是已接纳行动的账本

## 规格文档不是已实现功能

`POLITICAL_SIMULATION_MODEL_SPEC_V0.2.md` 是更大的设计文本。其中的联盟、制度、权力、界面和可替换理论，没有对应的执行体。空的 Tick 槽位保留在代码里，函数为空。组织、派系和制度对象可以出现在场景里，运行时的信息传递、采信、信念、意图和资源结算不读取它们。

## 运行测试

无第三方依赖。测试在 Python 3.14.3 上通过，`pyproject.toml` 要求 Python 3.11 或更高。

```text
python -m unittest discover -s tests -t .
```

## 两种复现

研究复现对齐同一干预、等价的因果轨迹和相同结论。事件字符串不必逐字相同。

工程回归是这 132 项测试。它们锁定当前 Python 实现的事件、字段和字符串契约。

## 已知注释漂移

这两处注释与执行不一致，不影响当前行为和实验结论，本次公开没有顺手改代码：

- `political_sim/core/actions/action_resolver.py` 的模块说明仍写后果尚未实现。被接纳的行动已经会写入 `action_consequence`，并把行动者资源加 1。
- `political_sim/core/models/individual.py` 里 `Capabilities` 的说明仍写影响力权重公式尚未实现。群体聚合已经使用 `0.5 + 0.5 * influence`。

## 许可证

MIT。见 `LICENSE`。
