#!/usr/bin/env python3
"""Adjustable solid-background editorial grid layout; semantic subject boxes are supplied by the caller."""
import argparse
import json
import math
from pathlib import Path
from PIL import Image, ImageOps, ImageFont
from render import render, MODES


def protected_crop(size, protect, ratio, margin=.08):
    w, h = size
    x0, y0, x1, y1 = protect
    if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
        raise ValueError('protect must be normalized [left, top, right, bottom]')
    px, py = (x1-x0)*margin, (y1-y0)*margin
    a,b,c,d = max(0,x0-px)*w, max(0,y0-py)*h, min(1,x1+px)*w, min(1,y1+py)*h
    cw,ch = c-a,d-b
    if cw/ch < ratio: cw = ch*ratio
    else: ch = cw/ratio
    if cw <= w and ch <= h:
        a = min(max(0,(a+c-cw)/2), w-cw)
        b = min(max(0,(b+d-ch)/2), h-ch)
        c,d = a+cw,b+ch
    # If the preferred ratio cannot contain the protected region, keep the
    # expanded region and let the slot adapt; never crop the subject to fill.
    return [a/w,b/h,c/w,d/h], (c-a)/(d-b)


def build(config, root):
    w,h = config.get('size',[1080,1440])
    if min(w,h)<360: raise ValueError('Use a canvas at least 360px on each side')
    if not 0<=config.get('subject_margin',.08)<=.3: raise ValueError('subject_margin must be 0..0.3')
    scale=w/1080
    def snap(v): return round(v/(8*scale))*round(8*scale) if scale>=.5 else round(v)
    mode=config.get('mode','solid-type')
    if mode not in MODES: raise ValueError('Unknown mode')
    def path(s):
        p=Path(s).expanduser();return str(p if p.is_absolute() else (root/p).resolve())
    font=path(config['font'])
    images=config['images']
    if len(images)<2: raise ValueError('At least two source images required')
    sources=[]
    for item in images:
        item=dict(item);item['path']=path(item['path'])
        with Image.open(item['path']) as im: item['source_size']=ImageOps.exif_transpose(im).size
        if 'protect' not in item: raise ValueError('Each image requires a visually chosen protect box')
        sources.append(item)
    out={'mode':mode,'size':[w,h],'font':font,'ink':config.get('ink','#f4d78f'),'elements':[]}
    elements=out['elements']
    def text(value,x,y,size,maxwidth,anchor='mm'):
        size=max(1,round(size))
        while size>max(12,round(20*scale)):
            f=ImageFont.truetype(font,size)
            if f.getlength(value)<=maxwidth: break
            size-=1
        if ImageFont.truetype(font,size).getlength(value)>maxwidth: raise ValueError('Shorten label: '+value)
        elements.append({'type':'text','text':value,'xy':[round(x),round(y)],'size':size,'anchor':anchor,'max_width':round(maxwidth)+2})
    if 'background_index' in config or 'shade' in config:
        raise ValueError('Photo backgrounds are no longer supported; use background_color')
    out['background']={'color':config.get('background_color','#543c28')}
    default=[.09,.17,.82,.47]
    region=config.get('region',default)
    rx,ry,rw,rh=region
    if not(0<=rx<rx+rw<=1 and 0<=ry<ry+rh<=1): raise ValueError('region must fit canvas')
    x,y,ww,hh=rx*w,ry*h,rw*w,rh*h
    cols=config.get('columns',2)
    if cols not in (1,2): raise ValueError('columns must be 1 or 2')
    rows=math.ceil(len(sources)/cols)
    gap=snap(config.get('column_gap',32)*scale)
    rowgap=snap(config.get('row_gap',32)*scale)
    cw=(ww-gap*(cols-1))/cols;ch=(hh-rowgap*(rows-1))/rows
    if ch<90*scale: raise ValueError('Too many rows: enlarge region or canvas')
    boxes=[]
    for i,item in enumerate(sources):
        row,col=divmod(i,cols)
        count=min(cols,len(sources)-row*cols)
        # A short final row uses whole grid columns, centered as a unit.
        left=snap(x+(ww-(count*cw+(count-1)*gap))/2+col*(cw+gap))
        cy=snap(y+row*(ch+rowgap)+ch/2)
        innergap=20*scale;maxpw=min(cw*.47,260*scale);maxph=ch-32*scale
        crop,aspect=protected_crop(item['source_size'],item['protect'],item.get('ratio',1),config.get('subject_margin',.08))
        pw=min(maxpw,maxph*aspect);ph=pw/aspect
        if min(pw,ph)<64*scale: raise ValueError('Subject tile too small: enlarge region or use fewer columns')
        imagefirst=(row+col)%2==0
        imagecx=left+maxpw/2 if imagefirst else left+cw-maxpw/2
        tx=left+maxpw+innergap if imagefirst else left
        tw=cw-maxpw-innergap
        box=[round(imagecx-pw/2),round(cy-ph/2),round(pw),round(ph)]
        elements.append({'type':'photo','path':item['path'],'crop':crop,'protect':item['protect'],'box':box})
        text(item.get('label','moment'),tx+tw/2,cy,config.get('label_size',44 if cols==2 else 48)*scale,tw)
        text('(%d)'%(i+1),imagecx,box[1]+box[3]+17*scale,19*scale,pw)
        boxes.append(box)
    title_y=config.get('title_y',.77)*h
    maxbottom=max(b[1]+b[3]+32*scale for b in boxes)
    title_size=min(config.get('title_size',116)*scale,.12*w)
    if title_y-title_size/2<maxbottom+32*scale or title_y+title_size/2>.89*h:
        raise ValueError('Title crowds photos or bottom margin: move region/title or reduce title size')
    text(config.get('intro','a collection of'),w/2,.105*h,24*scale,.75*w)
    text(config.get('title','(little moments)'),w/2,title_y,title_size,.82*w)
    # One quiet hand-drawn star in reserved space, independent of photo cells.
    if config.get('doodle',True):
        cx,cy=.85*w,.105*h;r=15*scale
        pts=[]
        for j in range(11):
            a=-math.pi/2+j*math.pi/5;rr=r if j%2==0 else r*.4
            pts.append([round(cx+math.cos(a)*rr),round(cy+math.sin(a)*rr)])
        elements.append({'type':'line','points':pts,'width':max(1,round(2*scale))})
    return out


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input',type=Path);ap.add_argument('output',type=Path)
    ap.add_argument('--layout-out',type=Path)
    args=ap.parse_args()
    config=json.loads(args.input.read_text(encoding='utf-8'))
    spec=build(config,args.input.resolve().parent)
    render(spec,args.output,args.input.resolve().parent)
    if args.layout_out:
        args.layout_out.parent.mkdir(parents=True,exist_ok=True)
        args.layout_out.write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'mode':spec['mode'],'output':str(args.output.resolve())}))

if __name__=='__main__': main()
