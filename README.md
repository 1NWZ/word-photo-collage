# 纯色词图拼贴 · Word Photo Collage

将多张用户照片制作成一张1080×1440纯色底图文拼贴，仅保留参考图4的编辑式风格：大小文字穿插矩形照片，小编号和少量同色手绘。默认深棕底、奶油黄字，可按照片调整纯色配色。已移除照片铺底与随机模式。

## 使用

将目录放入 `~/.codex/skills/word-photo-collage/`，上传至少两张照片，输入：

> 用 $word-photo-collage 做一张纯色底图文拼贴。

默认直接交付一张PNG。流程为一次看图、一次模板渲染、一次成片检查；参考分析按需阅读，缺依赖才安装。

## 模板

模型根据原图提供主体保护框、短词及配色；Python模板负责共享网格、保全主体的裁剪和字号布局。不会自动识别主体或重绘人物。

```sh
python3 scripts/layout.py input.json collage.png --layout-out layout.json
```

需要Python 3.9+与Pillow，遇到缺依赖时执行 `python3 -m pip install -r requirements.txt`。输入见[模板说明](references/templates.md)，高级精调见[渲染规格](references/render-spec.md)，执行规则见[SKILL.md](SKILL.md)。`mode`可省略或设为`solid-type`，其他模式会报错。

主体保护框必须覆盖照片想表达的完整人物或物件；无法适配图框时改变图块比例，避免中心裁切截脸。共享网格与受限的底部标题用于控制对齐和重心；两图仍采用同一纯色风格。

## 素材与许可证

本仓库不包含私人测试照片、测试成片或第三方参考图片。字体使用环境内可用文件，不随包分发系统字体。[MIT](LICENSE)涵盖代码与文档，不涵盖用户提供的照片或字体。
