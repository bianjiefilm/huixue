from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import math, random, textwrap, hashlib

OUT = Path('frontend/public/images/course-covers')
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1200, 675
FONT_BOLD = '/System/Library/Fonts/STHeiti Medium.ttc'
FONT_REG = '/System/Library/Fonts/STHeiti Medium.ttc'
FONT_MONO = '/System/Library/Fonts/Menlo.ttc'

def font(path, size):
    return ImageFont.truetype(path, size)

F_TITLE = font(FONT_BOLD, 58)
F_SUB = font(FONT_REG, 24)
F_TAG = font(FONT_BOLD, 21)
F_SMALL = font(FONT_REG, 18)
F_CODE = font(FONT_MONO, 22)

courses = [
    (101,'Python程序设计','实践课程','python','Python syntax / automation / data apps',('#1467ff','#20d2ff','#0b1026')),
    (102,'Spark编程基础','实践课程','spark','distributed compute / RDD / SQL',('#ff7a18','#ffd166','#160f0b')),
    (105,'大数据技术基础与应用实践','实践课程','bigdata','Hadoop / storage / compute / governance',('#2563eb','#22c55e','#061525')),
    (108,'数据挖掘分析','实践课程','mining','pattern discovery / clustering / rules',('#7c3aed','#38bdf8','#12091f')),
    (109,'数据清洗','实践课程','cleaning','quality / missing values / deduplication',('#0891b2','#34d399','#061a1d')),
    (110,'数据采集与预处理','实践课程','collection','crawler / ETL / preprocessing',('#0f766e','#facc15','#071717')),
    (112,'神经网络与深度学习','实践课程','neural','layers / tensors / optimization',('#4f46e5','#f472b6','#090b25')),
    (114,'计算机视觉','实践课程','vision','image recognition / detection / segmentation',('#0284c7','#a3e635','#061420')),
    (115,'电商销售BI分析','项目实训','ecommerce_bi','sales funnel / dashboard / conversion',('#ef4444','#f59e0b','#1b0a0a')),
    (116,'企业用能环保监测分析','项目实训','energy','energy monitor / emission / alert',('#16a34a','#22d3ee','#06170f')),
    (117,'公募基金精准营销案例','项目实训','fund','customer portrait / fund marketing',('#0ea5e9','#fbbf24','#07152a')),
    (118,'某零售企业经营分析','项目实训','retail','store operation / inventory / margin',('#db2777','#fb7185','#210714')),
    (119,'某高校校情管理分析案例','项目实训','university','campus analytics / student profile',('#2563eb','#c084fc','#081329')),
    (120,'某公司人力薪酬分析','项目实训','hr','salary structure / organization insight',('#7c2d12','#fdba74','#1b0d05')),
    (121,'某公司财务报表分析案例','项目实训','finance','balance sheet / cash flow / profit',('#047857','#67e8f9','#041714')),
    (122,'某电商货品销售分析案例','项目实训','goods','SKU / category / stock / sales',('#ea580c','#84cc16','#1a0d03')),
    (123,'风电齿轮箱预警分析','项目实训','wind','SCADA / gearbox / early warning',('#0f766e','#38bdf8','#061617')),
    (124,'分布式光伏出力预测','项目实训','solar','solar forecast / weather / output',('#ca8a04','#38bdf8','#1a1303')),
]

def hex_to_rgb(x):
    x=x.lstrip('#')
    return tuple(int(x[i:i+2],16) for i in (0,2,4))

def lerp(a,b,t): return int(a+(b-a)*t)

def gradient(c1,c2,c3):
    a,b,d = map(hex_to_rgb,(c1,c2,c3))
    img = Image.new('RGB',(W,H),d)
    px = img.load()
    for y in range(H):
        for x in range(W):
            t = (x/W*0.62 + y/H*0.38)
            if t < .56:
                u=t/.56
                col=tuple(lerp(d[i],a[i],u) for i in range(3))
            else:
                u=(t-.56)/.44
                col=tuple(lerp(a[i],b[i],u) for i in range(3))
            px[x,y]=col
    return img

def add_grid(draw, accent):
    ar,ag,ab=hex_to_rgb(accent)
    for x in range(0,W,48):
        draw.line([(x,0),(x,H)], fill=(ar,ag,ab,25), width=1)
    for y in range(0,H,48):
        draw.line([(0,y),(W,y)], fill=(ar,ag,ab,20), width=1)
    for i in range(20):
        x=70+i*54
        draw.line([(x,H-160),(x+80,H-210)], fill=(255,255,255,18), width=1)

def glow_layer():
    layer=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(layer)
    d.ellipse((690,70,1280,650), fill=(255,255,255,12))
    d.ellipse((760,130,1160,530), fill=(255,255,255,22))
    return layer.filter(ImageFilter.GaussianBlur(35))

def rounded(draw, box, r, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)

def draw_chart(draw, x, y, accent, secondary, seed):
    random.seed(seed)
    for i in range(7):
        h=random.randint(55,190); bx=x+i*46
        rounded(draw,(bx,y+210-h,bx+25,y+210),7,hex_to_rgb(accent)+(220,))
    pts=[]
    for i in range(9): pts.append((x+i*38,y+random.randint(35,150)))
    draw.line(pts, fill=hex_to_rgb(secondary)+(235,), width=5, joint='curve')
    for p in pts: draw.ellipse((p[0]-5,p[1]-5,p[0]+5,p[1]+5), fill=(255,255,255,230))
    rounded(draw,(x-24,y-32,x+360,y+246),22,(255,255,255,22),(255,255,255,58),1)

def draw_database(draw,x,y,accent,secondary):
    for i in range(4):
        yy=y+i*56
        draw.ellipse((x,yy,x+230,yy+48), outline=hex_to_rgb(secondary)+(210,), width=4)
        draw.rectangle((x,yy+24,x+230,yy+58), outline=hex_to_rgb(secondary)+(210,), width=4)
        draw.ellipse((x,yy+34,x+230,yy+82), outline=hex_to_rgb(accent)+(180,), width=3)
    for i in range(18):
        draw.ellipse((x+270+(i%6)*32,y+20+(i//6)*50,x+280+(i%6)*32,y+30+(i//6)*50), fill=(255,255,255,160))

def draw_network(draw,x,y,accent,secondary,neural=False):
    pts=[]
    cols=[0,1,2,3] if neural else [0,1,2]
    for c in cols:
        n=5 if neural else 4
        for r in range(n):
            pts.append((x+c*105,y+r*56+(c%2)*26))
    for i,p in enumerate(pts):
        for j,q in enumerate(pts):
            if q[0]>p[0] and q[0]-p[0]<120 and abs(q[1]-p[1])<95:
                draw.line([p,q], fill=hex_to_rgb(accent)+(70,), width=2)
    for i,p in enumerate(pts):
        col=secondary if i%3==0 else accent
        draw.ellipse((p[0]-13,p[1]-13,p[0]+13,p[1]+13), fill=hex_to_rgb(col)+(230,), outline=(255,255,255,180), width=2)

def draw_code(draw,x,y,accent,secondary):
    rounded(draw,(x,y,x+390,y+245),22,(8,14,32,190),(255,255,255,60),1)
    lines=['def transform(data):','  cleaned = pipeline(data)','  model.fit(features)','  return result']
    for i,line in enumerate(lines):
        draw.text((x+28,y+34+i*46), line, font=F_CODE, fill=(230,245,255,220))
    draw.text((x+245,y+150), '{ }', font=font(FONT_MONO,56), fill=hex_to_rgb(accent)+(220,))

def draw_domain(draw, kind, accent, secondary, seed):
    x,y=735,170
    if kind in ['ecommerce_bi','retail','goods']:
        draw_chart(draw,x-40,y-10,accent,secondary,seed)
        for i in range(3): rounded(draw,(x+260+i*42,y+190-i*28,x+292+i*42,y+220),8,hex_to_rgb(secondary)+(220,))
    elif kind in ['energy','wind','solar']:
        draw_chart(draw,x-50,y+15,accent,secondary,seed)
        cx,cy=x+235,y+72
        if kind=='wind':
            draw.line((cx,cy,cx,cy+185),fill=(255,255,255,190),width=7)
            for a in [0,120,240]:
                ex=cx+math.cos(math.radians(a))*95; ey=cy+math.sin(math.radians(a))*95
                draw.line((cx,cy,ex,ey),fill=hex_to_rgb(secondary)+(230,),width=9)
            draw.ellipse((cx-15,cy-15,cx+15,cy+15),fill=(255,255,255,230))
        elif kind=='solar':
            for r in range(3):
                for c in range(4): rounded(draw,(x+210+c*42,y+40+r*34,x+245+c*42,y+68+r*34),4,hex_to_rgb(accent)+(180,),(255,255,255,90),1)
            draw.ellipse((x+70,y+30,x+135,y+95),fill=hex_to_rgb(secondary)+(230,))
        else:
            draw.arc((x+210,y+34,x+360,y+184),200,520,fill=hex_to_rgb(secondary)+(235,),width=12)
    elif kind in ['python','spark','bigdata','collection','cleaning']:
        draw_code(draw,x-40,y,accent,secondary)
        if kind in ['bigdata','collection','cleaning']: draw_database(draw,x+210,y+4,accent,secondary)
    elif kind in ['mining','neural','vision']:
        draw_network(draw,x-5,y+4,accent,secondary, neural=(kind=='neural'))
        if kind=='vision':
            rounded(draw,(x+190,y+30,x+380,y+210),24,(255,255,255,20),(255,255,255,90),2)
            draw.ellipse((x+245,y+82,x+325,y+162),outline=hex_to_rgb(secondary)+(240,),width=10)
            draw.ellipse((x+270,y+107,x+300,y+137),fill=hex_to_rgb(accent)+(220,))
    elif kind in ['fund','finance','hr','university']:
        draw_chart(draw,x-40,y-5,accent,secondary,seed)
        if kind=='fund':
            for i in range(4): draw.arc((x+225+i*22,y+30+i*15,x+325+i*22,y+130+i*15),40,310,fill=hex_to_rgb(secondary)+(170,),width=4)
        elif kind=='finance':
            for i in range(4): rounded(draw,(x+240,y+40+i*43,x+385,y+70+i*43),8,(255,255,255,26),(255,255,255,75),1)
        elif kind=='hr':
            for i in range(5): draw.ellipse((x+245+i*36,y+62+(i%2)*42,x+275+i*36,y+92+(i%2)*42), fill=hex_to_rgb(secondary)+(210,))
        else:
            rounded(draw,(x+245,y+45,x+380,y+190),16,(255,255,255,22),(255,255,255,90),2)
            for i in range(4): draw.rectangle((x+265+i*25,y+90,x+280+i*25,y+190),fill=hex_to_rgb(accent)+(160,))

def wrap_title(title):
    if len(title)<=10: return [title]
    if len(title)<=15: return [title[:8], title[8:]]
    return [title[:9], title[9:18], title[18:]]

def make(course):
    cid,title,tag,kind,subtitle,colors=course
    accent, secondary, bg=colors
    img=gradient(bg,accent,secondary).convert('RGBA')
    img.alpha_composite(glow_layer())
    d=ImageDraw.Draw(img,'RGBA')
    add_grid(d, secondary)
    # diagonal glass band
    poly=[(820,0),(1200,0),(1200,675),(1000,675)]
    d.polygon(poly, fill=(255,255,255,12))
    # domain art
    seed=int(hashlib.sha1(title.encode()).hexdigest()[:8],16)
    draw_domain(d,kind,accent,secondary,seed)
    # brand lockup
    d.text((72,54),'慧学',font=F_TAG,fill=(255,255,255,215))
    rounded(d,(72,96,250,132),18,hex_to_rgb(secondary)+(42,),hex_to_rgb(secondary)+(150,),1)
    d.text((94,102),tag,font=F_TAG,fill=(255,255,255,230))
    # title block
    y0=380
    for i,line in enumerate(wrap_title(title)):
        d.text((72,y0+i*66),line,font=F_TITLE,fill=(255,255,255,245))
    d.text((76,600),subtitle,font=F_SUB,fill=(230,245,255,205))
    # small course id capsule
    rounded(d,(72,326,168,360),17,(255,255,255,28),(255,255,255,90),1)
    d.text((94,331),f'#{cid}',font=F_SMALL,fill=(255,255,255,210))
    out=OUT/f'course-{cid}.png'
    img.convert('RGB').save(out, optimize=True, quality=95)
    return out

for c in courses:
    p=make(c)
    print(p)
