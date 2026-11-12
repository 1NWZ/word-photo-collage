# 纯色文字拼贴模板

默认用本文件的输入直接生成最终图片，不再逐元素编写 render JSON。依赖已存在时直接运行，出现 `ModuleNotFoundError: PIL` 才安装 Pillow。

```sh
python3 scripts/layout.py work/input.json outputs/collage.png --layout-out work/layout.json
```

输入路径相对 JSON 文件；字体传可用的实际路径。一次看图后填写各原图 `protect` 和 `label`。`protect` 是 EXIF 校正后的归一化主体保护框 `[left,top,right,bottom]`，每张必填。边界应围住本张照片要表达的完整主体及关键姿态，不是只框眼睛或脸部。

```json
{
  "mode": "solid-type",
  "size": [1080,1440],
  "font": "/absolute/path/to/font.ttf",
  "background_color": "#543c28",
  "ink": "#f4d78f",
  "title": "(a pause)",
  "intro": "a collection of",
  "images": [
    {"path":"/absolute/path/to/a.jpg","protect":[0.25,0.2,0.8,0.9],"label":"quiet","ratio":0.75},
    {"path":"/absolute/path/to/b.jpg","protect":[0.15,0.3,0.85,0.85],"label":"light","ratio":1}
  ]
}
```

例子里的框只是格式示范，必须根据实际原图填写。主体框自带约 8% 扩展，代码尝试满足 `ratio`，无法同时保全主体时改用保护区域的实际比例，并在网格槽中居中。不会做二次中心 cover。

- `mode`：可省略，默认且仅支持 `solid-type`。不支持随机模式或照片底。
- `region`：归一化 `[x,y,width,height]`，默认 `[.09,.17,.82,.47]`。词图群在此区域内对齐。
- `columns`：1 或 2，默认 2；竖幅主体需要更大空间时减少列数或扩大区域。
- `row_gap` / `column_gap`：1080 宽基准，均默认 32；按 8px 节奏对齐。
- `label_size`：默认 44（单列48），过长文案自动缩小；优先缩短短词。
- `title` / `intro`：大号单行收尾词与顶部小引句。`title_size` 默认116、上限画布宽12%；`title_y` 默认 .77，拒绝挤压照片或底边。
- `subject_margin`：默认 .08；不要为强行满足照片框而设为负数或缩小 protect。
- `doodle`：纯色模式默认一颗小线条星，可关。需要其他手绘时在已生成布局里替换该元素，不重算整个版面。

`--layout-out` 可省略；需要局部精调时保留它，仅调整相关单元。高级修改格式见 render-spec.md。

保护框包含检查能防止裁剪越过已标注主体，但不能证明保护框标得正确，也不能自动判断人脸辨识度。因此保留一次最终成片目视检查，不增加逐图检查轮次。
