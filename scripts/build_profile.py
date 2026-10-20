"""Build self-contained, GitHub-compatible SVG panels from Asad's own profile data."""
from pathlib import Path
from html import escape
import base64
import json
import math
import re
from collections import Counter
from datetime import date
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
DATA = json.loads((ROOT / "data/github-snapshot.json").read_text(encoding="utf-8"))
CYAN = "#64f3f0"
PURPLE = "#ad8bfa"
WHITE = "#e8f0ff"
MUTED = "#94a8c9"
BG = "#071024"
FONT = "Consolas,Menlo,DejaVu Sans Mono,monospace"


def text(x, y, value, size=16, fill=WHITE, extra=""):
    return f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" {extra}>{escape(str(value))}</text>'


def rect(x, y, w, h, fill, stroke="none", radius=10, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" {extra}/>'


def svg(w, h, title, body, css=""):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">Custom terminal profile for Mohammad Asad Bin Jafor. Cyan and violet on midnight blue.</desc>
<defs>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{CYAN}"/><stop offset=".48" stop-color="#688eff"/><stop offset="1" stop-color="{PURPLE}"/></linearGradient>
<linearGradient id="surface" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#092044"/><stop offset=".55" stop-color="#09152d"/><stop offset="1" stop-color="#11132e"/></linearGradient>
<radialGradient id="blue"><stop stop-color="#10396d"/><stop offset="1" stop-color="#07152e"/></radialGradient>
<filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3"/></filter>
<pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#276080" stroke-opacity=".13"/></pattern>
</defs>
<style>text{{font-family:{FONT};font-variant-ligatures:none}}{css}</style>
{body}</svg>'''


def panel(w, h):
    return (rect(8, 8, w-16, h-16, "none", CYAN, 15, 'stroke-width="2" opacity=".28" filter="url(#glow)"')
            + rect(10, 10, w-20, h-20, "url(#surface)", "url(#edge)", 14, 'stroke-width="1.6"')
            + rect(11, 11, w-22, h-22, "url(#grid)", radius=13))


def save(name, data):
    (ASSETS / name).write_text(data, encoding="utf-8")


def heading():
    b = text(500, 28, "ASADBINJAFOR / DEVELOPER PROFILE", 13, CYAN, 'text-anchor="middle" letter-spacing="3"')
    b += text(500, 81, "MOHAMMAD ASAD BIN JAFOR", 38, WHITE, 'text-anchor="middle" font-weight="700" letter-spacing="1"')
    for i, label in enumerate(["Full Stack Web Developer", "CSE @ AIUB  /  Software Engineering", "Building purposeful, practical software"]):
        b += f'<g class="headline h{i}">' + text(500, 121, label, 20, CYAN, 'text-anchor="middle"') + "</g>"
    b += '<path d="M350 147H650" stroke="url(#edge)" stroke-width="2"/>'
    css = '''.headline{opacity:0}.h0{opacity:1;animation:head0 15s infinite}.h1{animation:head1 15s infinite}.h2{animation:head2 15s infinite}
@keyframes head0{0%,29%,100%{opacity:1}33%,96%{opacity:0}}
@keyframes head1{0%,31%,66%,100%{opacity:0}35%,62%{opacity:1}}
@keyframes head2{0%,64%,98%,100%{opacity:0}68%,94%{opacity:1}}
@media(prefers-reduced-motion:reduce){.headline{animation:none}.h0{opacity:1}.h1,.h2{opacity:0}}'''
    save("heading.svg", svg(1000, 160, "Mohammad Asad Bin Jafor — Full Stack Web Developer", b, css))
    mobile = text(250, 27, "ASADBINJAFOR / DEVELOPER", 12, CYAN, 'text-anchor="middle" letter-spacing="2"')
    mobile += text(250, 77, "MOHAMMAD ASAD", 32, WHITE, 'text-anchor="middle" font-weight="700"')
    mobile += text(250, 113, "BIN JAFOR", 32, WHITE, 'text-anchor="middle" font-weight="700"')
    mobile += text(250, 151, "Full Stack Web Developer", 17, CYAN, 'text-anchor="middle"')
    mobile += '<path d="M150 174H350" stroke="url(#edge)" stroke-width="2"/>'
    save("heading-mobile.svg", svg(500, 188, "Mohammad Asad Bin Jafor — Full Stack Web Developer", mobile))


def portrait_scene(x, y, s):
    photo = base64.b64encode((ASSETS / "asad.png").read_bytes()).decode()
    # Sampling the supplied portrait produces SVG text, not a generated replacement face.
    im = Image.open(ASSETS / "asad.png").convert("L").resize((64, 48))
    ramp = " .,:;irsXA253hMHGS#9B&@"
    ascii_lines = []
    for row in range(48):
        line = "".join(ramp[min(len(ramp)-1, int((255-im.getpixel((col,row))) / 256 * len(ramp)))] for col in range(64))
        ascii_lines.append(text(x+7, y+9+row*(s-16)/48, line, (s-14)/64/.6, CYAN,
                                'xml:space="preserve" textLength="%s" lengthAdjust="spacingAndGlyphs"' % (s-14)))
    b = f'<defs><clipPath id="portrait-clip">{rect(x,y,s,s,"white",radius=7)}</clipPath></defs>'
    b += rect(x, y, s, s, "url(#blue)", "#2b527a", 7)
    b += f'<g clip-path="url(#portrait-clip)">'
    b += f'<image class="photo" x="{x}" y="{y}" width="{s}" height="{s}" preserveAspectRatio="xMidYMid meet" xlink:href="data:image/png;base64,{photo}"/>'
    b += '<g class="ascii">' + "".join(ascii_lines) + "</g>"
    java = (ASSETS / "icons/Java-Dark.svg").read_text(encoding="utf-8")
    java = re.sub(r'<svg\b', f'<svg x="{x+s*.22}" y="{y+s*.15}"', java, count=1)
    java = re.sub(r'width="[^"]+"', f'width="{s*.56}"', java, count=1)
    java = re.sub(r'height="[^"]+"', f'height="{s*.56}"', java, count=1)
    b += '<g class="java">' + java + text(x+s/2, y+s*.86, "JAVA / OOP", 19, CYAN, 'text-anchor="middle"') + "</g>"
    b += '<g class="code">' + text(x+s/2, y+s*.53, "{ TS }", 60, CYAN, 'text-anchor="middle" font-weight="700"')
    b += text(x+s/2, y+s*.72, "NEXT.JS + NESTJS", 18, WHITE, 'text-anchor="middle"') + "</g>"
    b += f'<rect class="scan" x="{x}" y="{y}" width="{s}" height="2" fill="{CYAN}" opacity=".65"/>'
    b += "</g>"
    # The four corner brackets match the visual-map framing in the reference.
    for px,py,dx,dy in [(x-5,y-5,1,1),(x+s+5,y-5,-1,1),(x-5,y+s+5,1,-1),(x+s+5,y+s+5,-1,-1)]:
        b += f'<path d="M{px} {py+dy*20}V{py}H{px+dx*20}" fill="none" stroke="{CYAN}" stroke-width="2"/>'
    return b


ANIMATION = '''.ascii,.java,.code{opacity:0}.photo{opacity:1;animation:photo 20s infinite}
.ascii{animation:ascii 20s infinite}.java{animation:java 20s infinite}.code{animation:code 20s infinite}
.scan{animation:scan 8s linear infinite}
@keyframes photo{0%,44%,100%{opacity:1}49%,94%{opacity:0}}
@keyframes ascii{0%,44%,68%,100%{opacity:0}49%,63%{opacity:1}}
@keyframes java{0%,64%,83%,100%{opacity:0}69%,79%{opacity:1}}
@keyframes code{0%,79%,98%,100%{opacity:0}84%,94%{opacity:1}}
@keyframes scan{0%{transform:translateY(0);opacity:0}5%,90%{opacity:.45}100%{transform:translateY(330px);opacity:0}}
@media(prefers-reduced-motion:reduce){.photo{animation:none;opacity:1}.ascii,.java,.code,.scan{animation:none;opacity:0}}'''


def info(x, y, mobile=False):
    gap = 29 if mobile else 25
    offset = 128 if mobile else 145
    size = 17 if mobile else 15
    rows = [
        ("Subject", "Mohammad Asad Bin Jafor", WHITE),
        ("Role", "Full Stack Web Developer", WHITE),
        ("Origin", "Dhaka, Bangladesh", WHITE),
        ("Education", "BSc CSE / AIUB", WHITE),
        ("Status", "Final-semester student", CYAN),
        ("CGPA", "3.65 / 4.00", CYAN),
        ("", "", WHITE),
        ("Core.Lang", "PHP / TypeScript / Java / C#", WHITE),
        ("Core.Front", "React / Next.js / Tailwind", WHITE),
        ("Core.Back", "NestJS / PHP / REST APIs", WHITE),
        ("Core.Data", "PostgreSQL / MySQL / Oracle", WHITE),
        ("Core.Tools", "Git / Postman / Jira", WHITE),
        ("", "", WHITE),
        ("Grid.Mail", "asadbinjafor@gmail.com", CYAN),
        ("Grid.GitHub", "@asadbinjafor", PURPLE),
    ]
    b = text(x, y, "SYSTEM.INFO", 16, CYAN, 'font-weight="700" letter-spacing="2"')
    b += rect(x, y+13, 202, 23, "#6237c9", radius=3)
    b += text(x+10, y+29, "developer@asad:~$", 13, "#ffffff")
    for i,(label,value,color) in enumerate(rows):
        if label:
            yy = y+63+i*gap
            b += text(x, yy, label, size, MUTED)
            b += text(x+offset-18, yy, ":", size, "#56718e")
            b += text(x+offset, yy, value, size, color)
        else:
            yy = y+52+i*gap
            b += f'<path d="M{x} {yy}H{x+(402 if mobile else 520)}" stroke="#234065" stroke-dasharray="3 5"/>'
    return b


def hero(mobile=False):
    w,h=(500,1070) if mobile else (1000,610)
    b=panel(w,h)
    for x,c in [(30,"#ff6e87"),(47,"#ffd17a"),(64,"#6ce3b1")]:
        b+=f'<circle cx="{x}" cy="32" r="4" fill="{c}"/>'
    b+=text(92,37,"asad@github:~ / profile",13,MUTED)
    if not mobile:
        b+=text(969,37,"OPEN TO OPPORTUNITIES",12,CYAN,'text-anchor="end" letter-spacing="1"')
    b+=f'<path d="M11 52H{w-11}" stroke="#28415e"/>'
    px,py,ps=(82,108,336) if mobile else (38,113,338)
    b+=text(px,py-19,"VISUAL.MAP",13,CYAN,'letter-spacing="2"')
    b+=portrait_scene(px,py,ps)
    b+=text(px,py+ps+30,"01 / PORTRAIT · CODE · SYSTEMS",12,MUTED)
    if mobile:
        b+=info(32,517,True)
        b+=text(32,1032,"$ ready to build something useful_",14,CYAN)
    else:
        b+=info(417,91)
        b+=rect(38,506,338,55,"#0c2038","#254467",6)
        b+=f'<circle cx="56" cy="531" r="4" fill="#6ce3b1"/>'
        b+=text(70,529,"AVAILABLE FOR",11,MUTED,'letter-spacing="1.5"')
        b+=text(70,548,"Internships / Junior roles",14,CYAN)
        b+=text(417,555,"$ build / learn / improve_",14,PURPLE)
        b+=text(969,584,"READ THE WORK. MEET THE DEVELOPER.",11,MUTED,'text-anchor="end" letter-spacing="1"')
    save("hero-mobile.svg" if mobile else "hero.svg",svg(w,h,"Asad's terminal — portrait, skills, education and contact",b,ANIMATION))


def stats():
    days=DATA["contributions"]
    longest=run=0
    for d in days:
        run=run+1 if d["count"] else 0
        longest=max(longest,run)
    b=panel(1000,295)
    b+=text(35,45,"GITHUB.TELEMETRY",15,CYAN,'letter-spacing="2"')
    b+=text(965,45,DATA["updated"],12,MUTED,'text-anchor="end"')
    metrics=[(sum(d["count"] for d in days),"CONTRIBUTIONS / 12 MONTHS"),(DATA["public_repos"],"PUBLIC REPOSITORIES"),(f"{longest} days","LONGEST STREAK / 12 MONTHS")]
    for i,(v,label) in enumerate(metrics):
        x=175+i*325
        b+=text(x,105,v,38,WHITE,'text-anchor="middle" font-weight="700"')
        b+=text(x,133,label,11,CYAN,'text-anchor="middle" letter-spacing=".8"')
        if i<2:b+=f'<path d="M{x+162} 69V140" stroke="#315778"/>'
    b+=text(35,177,"REPOSITORIES BY PRIMARY LANGUAGE",12,MUTED,'letter-spacing="1"')
    langs=sorted(DATA["languages"].items(),key=lambda x:-x[1])
    colors=["#8e87dc","#338de6","#ef647d","#c8a5ff","#e2bb58","#5bcfbb","#c769a5","#fcb15c"]
    total=sum(n for _,n in langs)
    x=35
    for i,(lang,n) in enumerate(langs):
        width=n/total*930
        b+=rect(round(x,2),193,round(width,2),12,colors[i%len(colors)],radius=0)
        x+=width
    for i,(lang,n) in enumerate(langs):
        x=35+(i%4)*240; y=232+(i//4)*28
        b+=f'<circle cx="{x+4}" cy="{y-5}" r="4" fill="{colors[i%len(colors)]}"/>'
        b+=text(x+17,y,f"{lang} · {n}",13,WHITE)
    save("stats.svg",svg(1000,295,"GitHub activity snapshot and public repository languages",b))
    mobile=panel(500,525)
    mobile+=text(30,43,"GITHUB.TELEMETRY",15,CYAN,'letter-spacing="1"')
    mobile+=text(470,43,DATA["updated"],12,MUTED,'text-anchor="end"')
    for i,(value,label) in enumerate(metrics):
        yy=104+i*90
        mobile+=text(35,yy,value,31,WHITE,'font-weight="700"')
        mobile+=text(35,yy+23,label,12,CYAN)
        mobile+=f'<path d="M30 {yy+37}H470" stroke="#254361"/>'
    mobile+=text(30,347,"REPOSITORIES BY PRIMARY LANGUAGE",12,MUTED)
    for i,(lang,n) in enumerate(langs):
        xx=30+(i%2)*230; yy=380+(i//2)*34
        mobile+=f'<circle cx="{xx+4}" cy="{yy-5}" r="4" fill="{colors[i%len(colors)]}"/>'
        mobile+=text(xx+17,yy,f"{lang} · {n}",14,WHITE)
    save("stats-mobile.svg",svg(500,525,"GitHub activity snapshot and public repository languages",mobile))


def activity():
    days=DATA["contributions"]
    b=panel(1000,250)
    b+=text(35,44,"CONTRIBUTION.GRID",15,CYAN,'letter-spacing="2"')
    b+=text(965,44,"ACTIVITY SNAPSHOT / "+DATA["updated"],11,MUTED,'text-anchor="end"')
    start=date.fromisoformat(days[0]["date"])
    colors=["#122239","#15505f","#168786","#40bdb0","#83f9cd"]
    for d in days:
        day=date.fromisoformat(d["date"]); ix=(day-start).days
        x=35+(ix//7)*17.6; y=82+(ix%7)*17
        b+=f'<g><title>{d["date"]}: {d["count"]} contributions</title>'+rect(round(x,1),y,13,13,colors[d["level"]],radius=3)+"</g>"
    for col,label in [(0,"OCT"),(5,"NOV"),(9,"DEC"),(13,"JAN"),(18,"FEB"),(22,"MAR"),(26,"APR"),(31,"MAY"),(35,"JUN"),(39,"JUL"),(44,"AUG"),(48,"SEP")]:
        b+=text(35+col*17.6,71,label,9,MUTED)
    # A small decorative snake travels across the real, unmodified activity grid.
    coords=[]
    for col in range(53):
        rows=range(7) if col%2==0 else reversed(range(7))
        for row in rows:coords.append(f"{41.5+col*17.6:.1f},{88.5+row*17}")
    path="M"+" L".join(coords)
    for i in reversed(range(6)):
        b+=f'<rect class="snake" x="-6.5" y="-6.5" width="13" height="13" rx="3" fill="{CYAN}" opacity="{1-i*.12}"><animateMotion dur="48s" begin="-{i*.13}s" repeatCount="indefinite" path="{path}"/></rect>'
    b+=text(35,226,f"{days[0]['date']} — {days[-1]['date']}",11,MUTED)
    b+=text(965,226,"each square = one day",11,MUTED,'text-anchor="end"')
    save("activity.svg",svg(1000,250,"Asad's real contribution history with a decorative animated snake",b,
         "@media(prefers-reduced-motion:reduce){.snake{display:none}}"))


def research():
    b=panel(1000,170)
    b+=text(35,43,"RESEARCH.IN_PROGRESS",13,CYAN,'letter-spacing="2"')
    b+=text(35,81,"Explainable AI for safer roads.",27,WHITE,'font-weight="700"')
    b+=text(35,115,"Pothole detection + severity assessment for road maintenance",16,MUTED)
    b+=text(35,143,"FINAL-SEMESTER THESIS / EXPLAINABLE AI / COMPUTER VISION",11,PURPLE,'letter-spacing="1"')
    # Technical road diagram, intentionally decorative rather than a measured result.
    b+='<path d="M855 147L890 65M950 147L918 65M904 141L904 124M904 112L904 96M904 86L904 75" fill="none" stroke="#44718e" stroke-width="2"/>'
    b+='<ellipse cx="900" cy="117" rx="12" ry="5" fill="#ad8bfa" opacity=".8"/>'
    b+=rect(880,99,40,31,"none",CYAN,2,'stroke-dasharray="4 3"')
    save("research.svg",svg(1000,170,"Ongoing thesis: explainable AI-based pothole detection",b))
    mobile=panel(500,230)
    mobile+=text(28,44,"RESEARCH.IN_PROGRESS",14,CYAN,'letter-spacing="1"')
    mobile+=text(28,88,"Explainable AI",28,WHITE,'font-weight="700"')
    mobile+=text(28,121,"for safer roads.",28,WHITE,'font-weight="700"')
    mobile+=text(28,157,"Pothole detection + severity assessment",14,MUTED)
    mobile+=text(28,180,"for road maintenance",14,MUTED)
    mobile+=text(28,208,"ONGOING THESIS / AI / COMPUTER VISION",11,PURPLE)
    save("research-mobile.svg",svg(500,230,"Ongoing thesis: explainable AI-based pothole detection",mobile))


def buttons():
    for slug,label in [("portfolio","PORTFOLIO"),("linkedin","LINKEDIN"),("email","EMAIL"),("github","ALL PROJECTS"),("resume","RESUME"),("facebook","FACEBOOK"),("instagram","INSTAGRAM")]:
        w=max(115,len(label)*10+42)
        b=rect(1,1,w-2,39,BG,"url(#edge)",5)
        b+=text(w/2,26,label,14,CYAN,'text-anchor="middle" font-weight="700" letter-spacing="1"')
        save(f"link-{slug}.svg",svg(w,41,label,b))
    b=panel(1000,115)
    b+=text(500,50,"LET'S BUILD SOMETHING USEFUL.",24,WHITE,'text-anchor="middle" font-weight="700"')
    b+=text(500,82,"Open to internships, junior roles and project collaboration.",14,CYAN,'text-anchor="middle"')
    save("footer.svg",svg(1000,115,"Open to internships, junior roles and collaboration",b))
    mobile=panel(500,150)
    mobile+=text(250,51,"LET'S BUILD",25,WHITE,'text-anchor="middle" font-weight="700"')
    mobile+=text(250,82,"SOMETHING USEFUL.",25,WHITE,'text-anchor="middle" font-weight="700"')
    mobile+=text(250,117,"Internships / Junior roles / Collaboration",12,CYAN,'text-anchor="middle"')
    save("footer-mobile.svg",svg(500,150,"Open to internships, junior roles and collaboration",mobile))


if __name__=="__main__":
    heading()
    hero()
    hero(mobile=True)
    stats()
    activity()
    research()
    buttons()
    print("Built all profile SVG panels.")
