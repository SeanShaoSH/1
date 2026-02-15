# 高中有机合成路线设计程序

这是一个**高三水准**的有机合成路线自动设计小程序，面向高中常见反应类型：

- 取代反应（烷烃卤代、卤代烃水解等）
- 消去反应（卤代烃/醇制烯烃）
- 加成反应（烯烃水化）
- 氧化反应（醇→醛→酸）
- 酯化反应（羧酸 + 醇→酯）
- 芳香族经典反应（苯的卤代、硝化、硝基还原、氯苯水解）

程序会从预设起始原料中，自动寻找一条步骤较少的可行路线。

## 运行方式

```bash
python3 organic_route_designer.py 乙酸乙酯
```

## 常用参数

- 列出可识别化合物：

```bash
python3 organic_route_designer.py --list
```

- 生成批量示例（默认 120 条）：

```bash
python3 organic_route_designer.py --generate-demos examples_120.md --demo-count 120
```

## 已附带示例

仓库中已提供 `examples_120.md`，包含约 100+（实际 120）个自动规划范例。
