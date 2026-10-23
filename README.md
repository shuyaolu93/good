# Python 星空 / 螺旋星系粒子动画

用 Python + moderngl (OpenGL) 写的螺旋星系粒子动画，复刻自抖音「可乐鸡翅^O^」的 Python 星空教程效果。

## 效果

- 三旋臂螺旋星系粒子云，中心白亮、外围偏蓝
- 整体缓慢旋转 + 波浪起伏 + 轻微呼吸
- 点缀少量带十字光芒的亮星
- 加色混合发光质感

## 安装依赖

```bash
pip install moderngl glfw numpy pillow
```

## 运行

```bash
python3 starfield.py
```

窗口大小 900×900，自动开始动画。关闭窗口退出。

## 可调参数

代码顶部有一组参数可以自己调：

| 参数 | 含义 |
| --- | --- |
| `SHIFT` | 偏移量 |
| `PRES` | 密度相关 |
| `PA/PB/PC` | 三通道权重 |
| `CYCLE` | 循环周期 |
| `WAMP` | 波浪振幅 |
| `WFREQ` | 波浪频率 |
| `SWR` | 散射/扭曲强度 |
| `SPIN` | 旋转速度 |

## 文件说明

- `starfield.py` — 主程序，直接运行
- `test_offscreen.py` — 离屏渲染一帧保存成 png 的测试脚本
