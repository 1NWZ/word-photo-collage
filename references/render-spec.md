# 渲染规格

默认使用 [三种模板](templates.md)；本文件只用于精调模板输出或用户明确要求自定义排版。

先查看原图、确定模式及坐标，再写 JSON。此脚本是执行器，不自动理解照片，也不会自行安排词图关系。可用 Python + Pillow，缺依赖时在工作目录的虚拟环境中安装 Pillow。

```sh
python3 scripts/render.py --choose-mode
python3 scripts/render.py work/layout.json outputs/collage.png
```

路径相对 JSON 文件目录解析，或使用绝对路径。字体必须是存在的字体文件；英文可用系统 Arial/DejaVu Sans，中文须使用已检查支持中文字形的字体，不随包复制系统字体。

```json
{
  "mode": "photo-cluster",
  "size": [1080, 1440],
  "font": "/absolute/path/to/font.ttf",
  "ink": "#ffffff",
  "background": {"path": "/absolute/path/to/base.jpg", "crop": [0, 0, 1, 1], "shade": 0.04},
  "elements": [
    {"type": "text", "text": "mood", "xy": [300, 720], "size": 48, "max_width": 170},
    {"type": "text", "text": "(", "xy": [480, 720], "size": 56},
    {"type": "photo", "path": "/absolute/path/to/detail.jpg", "crop": [0, 0.25, 1, 0.75], "box": [520, 695, 240, 120]},
    {"type": "text", "text": ")", "xy": [780, 720], "size": 56}
  ]
}
```

示例背景假定 3:4 原图；前景假定正方形原图。实际文件尺寸不同必须重算 crop，不可照抄示例框。纯色模式的 background 改为 `{"color":"#543c28"}`。

- `box` 是输出像素 `[x,y,width,height]`，整数。
- `crop` 是 EXIF 方向纠正后的原图归一化 `[left,top,right,bottom]`。裁切宽高比必须与目标框匹配，容差 3.5%；脚本拒绝再次居中裁切，防止悄悄截断主体。默认完整原图。
- 以主体框为基础向外扩展到目标比例，再平移到图内。若完整主体无法容纳，修改输出照片框比例；不要缩小主体框来绕过检查。
- `text.xy` 默认定位可见文字左上角（`anchor: lt`），可设置 Pillow 支持的 anchor；用 `textbbox` 测量整行，再安排括号和图片。`max_width` 检测行溢出，脚本不自动缩字。
- `font` 和 `color` 可在单个文字元素覆盖，用于字体粗细和三级字号。字符串以单行短词为主，换行应拆成不同元素。
- `line` 元素：`{"type":"line","points":[[850,230],[862,245],[848,260]],"width":3}`。手绘花可用多条略不规则的细线，星用折线；只在纯色模式少量使用。脚本不会自动添加花朵。
- 元素按数组顺序绘制。需自己检查碰撞和语义配对，脚本仅检查画布边界、裁剪比例和可选文字宽度。

所有源照片都需在 background 或 photo 中出现，脚本不持有输入清单，因此交付前由执行者对照清单检查。不要将已排版的参考图当作原片输入测试后声称完成了用户新图拼贴。

照片元素和照片背景可携带 `protect: [left,top,right,bottom]`。它是归一化主体保护框；渲染器会拒绝不完整包含该框的 crop。模板默认自动传入，手写布局也应填写。
