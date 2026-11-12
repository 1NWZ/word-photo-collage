#!/usr/bin/env python3
"""Pixel-preserving composition. Layout and semantic subject boxes are agent-authored."""
import argparse
import json
import random
from pathlib import Path

MODES = ('photo-full', 'photo-cluster', 'solid-type')


def render(spec, destination, root):
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    w, h = spec.get('size', [1080, 1440])
    if min(w, h) < 1:
        raise ValueError('Invalid canvas size')
    canvas = Image.new('RGB', (w, h), spec.get('background', {}).get('color', '#543c28'))
    draw = ImageDraw.Draw(canvas)

    def resolve(value):
        p = Path(value).expanduser()
        return p if p.is_absolute() else root / p

    def photo(item, size):
        with Image.open(resolve(item['path'])) as source:
            im = ImageOps.exif_transpose(source).convert('RGB')
        crop = item.get('crop', [0, 0, 1, 1])
        x0, y0, x1, y1 = crop
        if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
            raise ValueError('crop must be normalized [left, top, right, bottom]')
        crop_px = (round(x0*im.width), round(y0*im.height), round(x1*im.width), round(y1*im.height))
        if crop_px[2] <= crop_px[0] or crop_px[3] <= crop_px[1]:
            raise ValueError('crop too small')
        # Reject aspect mismatch instead of silently making a second subject crop.
        cropped = im.crop(crop_px)
        if abs((cropped.width/cropped.height)/(size[0]/size[1])-1) > .035:
            raise ValueError('crop aspect must match destination aspect within 3.5%; adjust crop or box')
        return cropped.resize(size, Image.Resampling.LANCZOS)

    bg = spec.get('background', {})
    if bg.get('path'):
        canvas.paste(photo(bg, (w, h)), (0, 0))
        shade = bg.get('shade', 0)
        if not 0 <= shade <= .3:
            raise ValueError('background shade must be 0..0.3')
        if shade:
            canvas = Image.blend(canvas, Image.new('RGB', (w, h), 'black'), shade)
            draw = ImageDraw.Draw(canvas)

    def inside(box):
        x0, y0, x1, y1 = box
        if not (0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h):
            raise ValueError('Element outside canvas or empty: %r' % (box,))

    for el in spec['elements']:
        kind = el['type']
        if kind == 'photo':
            x, y, ew, eh = el['box']
            inside((x, y, x+ew, y+eh))
            canvas.paste(photo(el, (ew, eh)), (x, y))
        elif kind == 'text':
            x, y = el['xy']
            font_path = el.get('font', spec.get('font'))
            if not font_path:
                raise ValueError('Provide an actual font file')
            font = ImageFont.truetype(str(resolve(font_path)), el['size'])
            anchor = el.get('anchor', 'lt')
            bounds = draw.textbbox((x, y), el['text'], font=font, anchor=anchor)
            inside(bounds)
            if el.get('max_width') and bounds[2]-bounds[0] > el['max_width']:
                raise ValueError('Text exceeds max_width: ' + el['text'])
            draw.text((x, y), el['text'], font=font, anchor=anchor, fill=el.get('color', spec.get('ink', '#ffffff')))
        elif kind == 'line':
            points = [tuple(p) for p in el['points']]
            if len(points) < 2:
                raise ValueError('Line needs at least two points')
            thickness = el.get('width', 3)
            if thickness <= 0:
                raise ValueError('Line width must be positive')
            for x, y in points:
                inside((x-thickness/2, y-thickness/2, x+thickness/2, y+thickness/2))
            draw.line(points, fill=el.get('color', spec.get('ink', '#ffffff')), width=thickness, joint='curve')
        else:
            raise ValueError('Unsupported element type: ' + kind)
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, 'PNG')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('spec', nargs='?', type=Path)
    parser.add_argument('output', nargs='?', type=Path)
    parser.add_argument('--choose-mode', action='store_true')
    parser.add_argument('--seed', type=int)
    args = parser.parse_args()
    if args.choose_mode:
        print(random.Random(args.seed).choice(MODES))
        return
    if not args.spec or not args.output:
        parser.error('Provide spec.json output.png, or --choose-mode')
    with args.spec.open(encoding='utf-8') as f:
        spec = json.load(f)
    if spec.get('mode') not in MODES:
        parser.error('spec.mode must be one of ' + ', '.join(MODES))
    render(spec, args.output, args.spec.resolve().parent)
    print(str(args.output.resolve()))


if __name__ == '__main__':
    main()
