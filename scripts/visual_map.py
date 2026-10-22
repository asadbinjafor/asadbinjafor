"""Turn the supplied portrait and licensed SVG icons into a native SVG pixel morph.

No replacement portrait is generated. The original photo remains untouched.
The contour below follows its background boundary, in original image coordinates.
"""
from functools import lru_cache
from collections import deque
from pathlib import Path
import random
import re
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 300, 369
SYMBOLS = {"react":"React", "nestjs":"NestJS", "postgresql":"PostgreSQL"}
CAPTIONS = {"react":"FRONTEND / REACT", "nestjs":"BACKEND / NESTJS",
            "postgresql":"DATABASE / POSTGRESQL"}
# Twelve seconds on the portrait across the loop boundary; three per stack logo.
TIMELINE = [(0,"portrait"),(10,"portrait"),(12,"react"),(15,"react"),
            (17,"nestjs"),(20,"nestjs"),(22,"postgresql"),(25,"postgresql"),
            (28,"portrait"),(30,"portrait")]
DURATION = 30
CONTOUR = [
    (332,350),(328,278),(334,211),(351,157),(383,115),(423,79),
    (481,60),(544,49),(600,51),(653,61),(704,84),(731,119),
    (746,166),(747,216),(737,280),(724,355),(738,355),(749,378),
    (751,416),(740,461),(718,495),(712,542),(694,584),
    (718,605),(745,636),(835,665),(925,702),(1002,738),
    (1033,766),(1050,839),(1085,1040),(0,1040),(40,837),
    (68,760),(107,735),(207,696),(304,660),(349,623),
    (383,589),(383,554),(367,508),(352,489),(342,454),
    (338,410),(345,375),(354,370),
]


@lru_cache(maxsize=1)
def portrait_sample():
    """Sample the original photograph once, preserving its facial geometry."""
    original = Image.open(ROOT / "assets/asad.png").convert("RGB")
    mask = Image.new("L", original.size)
    ImageDraw.Draw(mask).polygon(CONTOUR, fill=255)
    crop = (120, 0, 966, 1040)
    color = original.crop(crop).resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    sample = color.convert("L")
    mask = mask.crop(crop).resize((WIDTH, HEIGHT), Image.Resampling.NEAREST)
    # Remove only neutral wall pixels connected to the outside. Internal gray
    # shirt and suit details remain enclosed by the subject's silhouette.
    queue=deque([(x,0) for x in range(WIDTH)]+[(x,HEIGHT-1) for x in range(WIDTH)]
                +[(0,y) for y in range(HEIGHT)]+[(WIDTH-1,y) for y in range(HEIGHT)])
    visited=set()
    while queue:
        x,y=queue.popleft()
        if (x,y) in visited:continue
        visited.add((x,y))
        source_x=120+x*846/WIDTH
        source_y=y*1040/HEIGHT
        if (source_y>575 and 410<source_x<690) or (source_y>700 and 350<source_x<750):
            continue
        rgb=color.getpixel((x,y))
        if max(rgb)-min(rgb)>=22 or sum(rgb)/3<=105:continue
        mask.putpixel((x,y),0)
        queue.extend((xx,yy) for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))
                     if 0<=xx<WIDTH and 0<=yy<HEIGHT and (xx,yy) not in visited)
    return sample, mask


def portrait_pixels():
    """Dither the photograph only for the moving particle transitions."""
    sample, mask = portrait_sample()
    edges = sample.filter(ImageFilter.FIND_EDGES)
    values = [
        [min(1.0, max(0, (sample.getpixel((x,y))-34)/165)**1.1
             + edges.getpixel((x,y))/255*.7) if mask.getpixel((x,y)) else 0.0
         for x in range(WIDTH)] for y in range(HEIGHT)
    ]
    pixels = set()
    # Error diffusion preserves eyes, hair, facial hair and suit detail.
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if not mask.getpixel((x,y)):
                continue
            value = values[y][x]
            lit = 1 if value >= .5 else 0
            if lit:
                pixels.add((x,y))
            error = value-lit
            for dx,dy,weight in ((1,0,7/16),(-1,1,3/16),(0,1,5/16),(1,1,1/16)):
                xx,yy=x+dx,y+dy
                if 0<=xx<WIDTH and yy<HEIGHT and mask.getpixel((xx,yy)):
                    values[yy][xx]+=error*weight
    # Thin outline keeps the silhouette legible against the midnight background.
    outline = mask.filter(ImageFilter.FIND_EDGES)
    pixels.update((x,y) for y in range(1,HEIGHT-1) for x in range(1,WIDTH-1)
                  if outline.getpixel((x,y)) > 200)
    return pixels


@lru_cache(maxsize=1)
def portrait_tones():
    """Keep continuous facial shading in 32 compact, photo-derived SVG layers."""
    sample, mask = portrait_sample()
    # Feather the cutout edge without softening eyes, hair or facial features.
    coverage = mask.filter(ImageFilter.GaussianBlur(.55))
    layers = [[] for _ in range(33)]
    for y in range(HEIGHT):
        tones = [round((sample.getpixel((x,y))/255)**.85
                       * coverage.getpixel((x,y))/255 * 32)
                 for x in range(WIDTH)]
        x = 0
        while x < WIDTH:
            tone = tones[x]
            end = x + 1
            while end < WIDTH and tones[end] == tone:
                end += 1
            if tone:
                layers[tone].append((x,y,end-x))
            x = end
    return ''.join(f'<path fill="url(#portrait-ink)" opacity="{tone/32:.5f}" '
                   f'd="{path_data(marks)}"/>'
                   for tone,marks in enumerate(layers) if marks)


def svg_contours(path):
    """Flatten the absolute M/L/H/V/C/Z commands used by the bundled icons."""
    tokens=re.findall(r"[A-Za-z]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?",path)
    contours=[]; points=[]; pos=(0.,0.); command=None; i=0
    while i<len(tokens):
        if tokens[i].isalpha():
            command=tokens[i]; i+=1
        if command=="Z":
            if points:
                pos=points[0]
                points.append(pos)
                contours.append(points)
            points=[]; command=None
            continue
        count={"M":2,"L":2,"H":1,"V":1,"C":6}.get(command)
        if count is None:
            raise ValueError(f"Unsupported icon path command: {command}")
        args=list(map(float,tokens[i:i+count])); i+=count
        if command=="M":
            if points:contours.append(points)
            pos=tuple(args); points=[pos]; command="L"
        elif command=="L":
            pos=tuple(args); points.append(pos)
        elif command=="H":
            pos=(args[0],pos[1]); points.append(pos)
        elif command=="V":
            pos=(pos[0],args[0]); points.append(pos)
        elif command=="C":
            start=pos; p1=args[:2]; p2=args[2:4]; end=args[4:]
            for step in range(1,25):
                t=step/24; u=1-t
                points.append(tuple(u**3*start[k]+3*u*u*t*p1[k]+3*u*t*t*p2[k]+t**3*end[k]
                                    for k in (0,1)))
            pos=tuple(end)
    if points:contours.append(points)
    return contours


def signed_area(points):
    return sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1]))/2


def inside(point,polygon):
    x,y=point
    crossings=0
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            crossings+=1
    return crossings%2==1


def symbol_pixels(name):
    """Sample the licensed icon's foreground paths, omitting its square backing."""
    image=Image.new("L",(WIDTH,HEIGHT))
    draw=ImageDraw.Draw(image)
    root=ET.parse(ROOT / "assets/icons" / f"{name}-Dark.svg").getroot()
    scale={"React":1.15,"NestJS":1.0,"PostgreSQL":1.35}[name]
    dx,dy=WIDTH/2-128*scale,173-128*scale
    for path in root.findall("{http://www.w3.org/2000/svg}path"):
        contours=svg_contours(path.attrib["d"])
        contours.sort(key=lambda p:abs(signed_area(p)),reverse=True)
        fill=path.get("fill",root.get("fill","black"))
        if fill!="none":
            drawn=[]
            # The elephant's linework needs contrast against its filled body.
            tone=70 if name=="PostgreSQL" and fill!="#fff" else 255
            for points in contours:
                containers=[p for p in drawn if inside(points[0],p)]
                winding=sum(1 if signed_area(p)>0 else -1 for p in containers+[points])
                points_on_map=[(dx+x*scale,dy+y*scale) for x,y in points]
                draw.polygon(points_on_map,fill=tone if winding else 0)
                drawn.append(points)
        if path.get("stroke","none")!="none":
            stroke_width=max(1,round(float(path.get("stroke-width","1"))*scale))
            for points in contours:
                mapped=[(dx+x*scale,dy+y*scale) for x,y in points]
                draw.line(mapped,fill=255,width=stroke_width,joint="curve")
                if path.get("stroke-linecap")=="round":
                    r=stroke_width/2
                    for cx,cy in (mapped[0],mapped[-1]):
                        draw.ellipse((cx-r,cy-r,cx+r,cy+r),fill=255)
    # The same monochrome texture as the portrait; deterministic, never flickers.
    rng=random.Random(21)
    return {(x,y) for y in range(HEIGHT) for x in range(WIDTH)
            if rng.random()<image.getpixel((x,y))/255*.92}


def runs(pixels):
    """Compact adjacent pixels into short horizontal marks."""
    result=[]
    for y in range(HEIGHT):
        x=0
        while x<WIDTH:
            if (x,y) not in pixels:
                x+=1; continue
            length=1
            while length<4 and (x+length,y) in pixels:
                length+=1
            result.append((x,y,length))
            x+=length
    return result


def equalize(marks,count):
    """Match SVG command topology for continuous interpolation between shapes."""
    return [marks[min(len(marks)-1,int(i*len(marks)/count))] for i in range(count)]


def path_data(marks):
    return "".join(f"M{x},{y}h{w}v1h-{w}Z" for x,y,w in marks)


@lru_cache(maxsize=1)
def scenes():
    marks={"portrait":runs(portrait_pixels())}
    marks.update({key:runs(symbol_pixels(icon)) for key,icon in SYMBOLS.items()})
    count=max(map(len,marks.values()))
    return {key:path_data(equalize(value,count)) for key,value in marks.items()}


MOTION_CSS = """
.map-still{display:none}
@media(prefers-reduced-motion:reduce){
  .map-motion,.map-portrait,.map-caption{display:none}.map-still{display:inline}
}
"""


def render(x,y,width,height,static_scene=None):
    shapes=scenes()
    scale=width/WIDTH
    art_y=y+(height-HEIGHT*scale)/2
    fill="url(#portrait-ink)"
    b=f'''<defs>
<linearGradient id="portrait-ink" x1="0" y1="0" x2="0" y2="{HEIGHT}" gradientUnits="userSpaceOnUse">
<stop stop-color="#89a5ff"/><stop offset=".36" stop-color="#b19aff"/><stop offset=".8" stop-color="#a78bfa"/><stop offset="1" stop-color="#6edee8"/>
</linearGradient>
<g id="portrait-tones">{portrait_tones()}</g>
<clipPath id="portrait-clip"><rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8"/></clipPath>
</defs>
<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" fill="#090e1d" stroke="#27b9ce" stroke-opacity=".5"/>
<g clip-path="url(#portrait-clip)"><g transform="translate({x} {art_y}) scale({scale})">'''
    if static_scene:
        b+=('<use href="#portrait-tones"/>' if static_scene=="portrait"
            else f'<path fill="{fill}" d="{shapes[static_scene]}"/>')
    else:
        b+='<use class="map-still" href="#portrait-tones"/>'
        b+=f'<path class="map-motion" opacity="0" fill="{fill}" d="{shapes["portrait"]}">'
        times=";".join(f"{t/DURATION:.6g}" for t,_ in TIMELINE)
        values=";".join(shapes[key] for _,key in TIMELINE)
        b+=f'<animate attributeName="d" dur="{DURATION}s" repeatCount="indefinite" calcMode="linear" keyTimes="{times}" values="{values}"/>'
        # Crossfade only while both representations are in the portrait shape.
        # The morph itself keeps its existing matching particle topology.
        fade_times=";".join(f"{t/DURATION:.6g}" for t in (0,9.4,10,28,28.6,30))
        b+=f'<animate attributeName="opacity" dur="{DURATION}s" repeatCount="indefinite" keyTimes="{fade_times}" values="0;0;1;1;0;0"/></path>'
        b+=f'<use class="map-portrait" href="#portrait-tones"><animate attributeName="opacity" dur="{DURATION}s" repeatCount="indefinite" keyTimes="{fade_times}" values="1;1;0;0;1;1"/></use>'
    for key,label in CAPTIONS.items():
        if static_scene and static_scene!=key:continue
        opacity="1" if static_scene else "0"
        b+=f'<text class="map-caption" x="150" y="345" text-anchor="middle" fill="#7edeea" font-family="Consolas,monospace" font-size="10" letter-spacing="1" opacity="{opacity}">{label}'
        if not static_scene:
            start,end=[t for t,scene in TIMELINE if scene==key]
            b+=f'<animate attributeName="opacity" dur="{DURATION}s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;{start/DURATION:.6g};{end/DURATION:.6g};1" values="0;1;0;0"/>'
        b+="</text>"
    b+="</g></g>"
    for px,py,dx,dy in [(x,y,1,1),(x+width,y,-1,1),(x,y+height,1,-1),(x+width,y+height,-1,-1)]:
        b+=f'<path d="M{px} {py+dy*16}V{py}H{px+dx*16}" fill="none" stroke="#54e4ee" stroke-width="1.5"/>'
    return b
