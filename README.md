# 艾尔登法环地图导航程序（基于画面定位）

这是一个可扩展的 **《艾尔登法环》画面定位 + 地图坐标导航** 原型项目。

> 说明：由于《艾尔登法环》没有公开官方实时坐标接口，本项目通过**视觉匹配**来估计位置。精度取决于你建立的参考数据集质量（覆盖度、分辨率、时间段/天气一致性）。

## 核心能力

- 根据游戏截图（或录屏帧）估计当前位置。
- 输出地图坐标 `(x, y)`、置信度和候选匹配。
- 支持构建你自己的地点样本库（地标截图 + 已知坐标）。

## 项目结构

- `src/elden_nav/cli.py`：命令行入口。
- `src/elden_nav/indexer.py`：ORB 特征提取和匹配索引。
- `src/elden_nav/navigator.py`：坐标估计逻辑（加权 KNN）。
- `src/elden_nav/models.py`：数据模型。
- `tests/test_navigator.py`：定位估计单元测试。

## 安装

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 一、准备样本数据

创建一个 `samples/metadata.csv`，字段如下：

```csv
image_path,x,y,label
samples/limgrave_ruins_01.png,1200.0,820.0,宁姆格福-废墟
samples/limgrave_gatefront_01.png,1285.0,910.0,关卡前方
```

要求：
- `image_path` 是一张真实游戏画面截图。
- `x,y` 是你定义的地图坐标系中的坐标（可用你自己的地图基准）。
- 样本尽量覆盖多个区域、角度、时间条件。

## 二、构建特征索引

```bash
python -m elden_nav.cli build-index \
  --metadata samples/metadata.csv \
  --output data/index.pkl
```

## 三、进行定位

```bash
python -m elden_nav.cli locate \
  --index data/index.pkl \
  --image frames/current_frame.png \
  --top-k 5
```

示例输出：

```json
{
  "input_image": "frames/current_frame.png",
  "estimated": {
    "x": 1279.31,
    "y": 902.77,
    "confidence": 0.84
  },
  "matches": [
    {
      "sample_label": "关卡前方",
      "sample_coord": [1285.0, 910.0],
      "score": 0.89
    }
  ]
}
```

## 提升精度建议

1. 每个区域至少 20~50 张样本，包含不同朝向。
2. 统一截图分辨率（或使用相同缩放流程）。
3. 避免 UI 遮挡（弹窗、菜单等）。
4. 使用更细粒度区域建模（分区索引）。
5. 可进一步替换为深度特征（如 SuperPoint + LightGlue）。

## 法律/使用声明

本项目仅用于学习与研究视觉定位技术，不包含游戏逆向、内存读取或作弊功能。请遵守游戏及平台条款。
