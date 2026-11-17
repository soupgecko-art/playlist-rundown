from PIL import Image, ImageDraw, ImageFont
import math, sys
S=3000
img=Image.new("RGB",(S,S),(18,22,38))
d=ImageDraw.Draw(img)
# warm gradient band
for y in range(S):
    t=y/S
    r=int(18+ (232-18)*max(0,t-0.55)/0.45*0.9); g=int(22+(110-22)*max(0,t-0.55)/0.45*0.9); b=int(38+(64-38)*max(0,t-0.55)/0.45*0.9)
    d.line([(0,y),(S,y)],fill=(r,g,b))
# sound-wave bars
import random; random.seed(7)
cx=S//2; base=1250
for i in range(-22,23):
    h=int(520*abs(math.sin(i*0.37))*math.exp(-(i/16)**2)+60+random.randint(0,90))
    x=cx+i*58
    d.rounded_rectangle([x-20,base-h//2,x+20,base+h//2],radius=20,fill=(245,196,92))
F="/usr/share/fonts/opentype/inter/"
big=ImageFont.truetype(F+"InterDisplay-Bold.otf",330)
sm=ImageFont.truetype(F+"InterDisplay-Medium.otf",120)
def ctext(y,s,f,fill):
    w=d.textlength(s,font=f); d.text(((S-w)/2,y),s,font=f,fill=fill)
ctext(250,"THE PLAYLIST",big,(255,255,255))
ctext(1950,"RUNDOWN",big,(255,255,255))
ctext(2400,"your podcast queue, in one conversation",sm,(255,235,210))
img.save("site/cover.jpg",quality=88)
