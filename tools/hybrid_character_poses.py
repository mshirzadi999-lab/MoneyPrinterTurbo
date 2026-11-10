"""Pose tests extending the canonical character (same shapes/colors/widths).
New poses only - the character design itself is unchanged."""
from PIL import Image, ImageDraw
import character as C

W, H, SS = C.W, C.H, C.SS
BLACK, WHITE, SHIRT, PANTS, SKIN = C.BLACK, C.WHITE, C.SHIRT, C.PANTS, C.SKIN

def base():
    layer = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    return layer, ImageDraw.Draw(layer)

def finish(layer):
    return layer.resize((W, H), Image.LANCZOS)

def draw_lying():
    """Lying flat on the ground, asleep. Head left, feet right."""
    s = SS
    layer, d = base()
    ground = 1150
    # wide soft shadow
    d.ellipse([(360-260)*s, (ground-6)*s, (360+260)*s, (ground+30)*s], fill=(0, 0, 0, 110))
    # legs (extended, slightly separated)
    d.line([430*s, 1102*s, 600*s, 1106*s], fill=PANTS, width=17*s, joint="curve")
    d.line([432*s, 1122*s, 602*s, 1126*s], fill=PANTS, width=17*s, joint="curve")
    for sx, sy in ((606, 1106), (608, 1126)):
        d.ellipse([(sx-24)*s, (sy-8)*s, (sx+30)*s, (sy+14)*s], fill=BLACK)
    # torso (thick red, horizontal)
    d.line([428*s, 1108*s, 252*s, 1108*s], fill=SHIRT, width=62*s, joint="curve")
    d.ellipse([(252-32)*s, (1108-30)*s, (252+32)*s, (1108+30)*s], fill=SHIRT)
    d.rectangle([(398)*s, (1108-30)*s, (452)*s, (1108+34)*s], fill=PANTS)
    # arm tucked under head
    d.line([258*s, 1112*s, 228*s, 1134*s], fill=SHIRT, width=26*s, joint="curve")
    d.line([228*s, 1134*s, 190*s, 1136*s], fill=SKIN, width=15*s, joint="curve")
    d.ellipse([(190-13)*s, (1136-13)*s, (190+13)*s, (1136+13)*s], fill=WHITE, outline=BLACK, width=3*s)
    # head resting on its side (bottom near ground)
    hr = 78
    hcx, hcy = 148, ground - hr + 14
    d.ellipse([(hcx-hr)*s, (hcy-hr)*s, (hcx+hr)*s, (hcy+hr)*s], fill=WHITE, outline=BLACK, width=6*s)
    # closed eyes (sleeping lines)
    for ex in (hcx-28, hcx+30):
        d.line([(ex-10)*s, (hcy-6)*s, (ex+10)*s, (hcy-6)*s], fill=BLACK, width=5*s)
    # relaxed brows
    for bx in (hcx-28, hcx+30):
        d.line([(bx-12)*s, (hcy-30)*s, (bx+12)*s, (hcy-30)*s], fill=BLACK, width=5*s)
    # small calm mouth
    d.arc([(hcx-14)*s, (hcy+18)*s, (hcx+14)*s, (hcy+40)*s], 15, 165, fill=BLACK, width=5*s)
    return finish(layer)

def draw_pushup():
    """Push-up plank, top position. Side view, same design language."""
    s = SS
    layer, d = base()
    ground = 1158
    # shadow
    d.ellipse([(360-250)*s, (ground+2)*s, (360+250)*s, (ground+32)*s], fill=(0, 0, 0, 110))
    S = (255, 1030)    # shoulder
    P = (480, 1075)    # hip
    # far arm (offset behind)
    d.line([(S[0]+22)*s, (S[1]+6)*s, (S[0]+22)*s, 1106*s], fill=SHIRT, width=24*s, joint="curve")
    d.line([(S[0]+22)*s, 1106*s, (S[0]+22)*s, 1148*s], fill=SKIN, width=14*s, joint="curve")
    d.ellipse([(S[0]+22-13)*s, (1150-13)*s, (S[0]+22+13)*s, (1150+13)*s], fill=WHITE, outline=BLACK, width=3*s)
    # legs to toes
    d.line([P[0]*s, P[1]*s, 626*s, 1144*s], fill=PANTS, width=17*s, joint="curve")
    d.line([P[0]*s, (P[1]+15)*s, 618*s, 1154*s], fill=PANTS, width=17*s, joint="curve")
    for tx, ty in ((634, 1142), (626, 1152)):
        d.ellipse([(tx-16)*s, (ty-10)*s, (tx+18)*s, (ty+10)*s], fill=BLACK)
    # torso (thick red plank)
    d.line([P[0]*s, P[1]*s, S[0]*s, S[1]*s], fill=SHIRT, width=62*s, joint="curve")
    d.ellipse([(S[0]-30)*s, (S[1]-30)*s, (S[0]+30)*s, (S[1]+30)*s], fill=SHIRT)
    d.rectangle([(P[0]-34)*s, (P[1]-28)*s, (P[0]+24)*s, (P[1]+34)*s], fill=PANTS)
    # near arm: sleeve then forearm, straight to ground
    d.line([S[0]*s, S[1]*s, S[0]*s, 1102*s], fill=SHIRT, width=26*s, joint="curve")
    d.line([S[0]*s, 1102*s, S[0]*s, 1146*s], fill=SKIN, width=15*s, joint="curve")
    d.ellipse([(S[0]-13)*s, (1148-13)*s, (S[0]+13)*s, (1148+13)*s], fill=WHITE, outline=BLACK, width=3*s)
    # head at front, determined
    hr = 74
    hcx, hcy = 168, 1000
    d.ellipse([(hcx-hr)*s, (hcy-hr)*s, (hcx+hr)*s, (hcy+hr)*s], fill=WHITE, outline=BLACK, width=6*s)
    # eye looking down-front
    d.ellipse([(hcx+8)*s, (hcy+2)*s, (hcx+28)*s, (hcy+22)*s], fill=BLACK)
    # determined angled brow
    d.line([(hcx+2)*s, (hcy-24)*s, (hcx+34)*s, (hcy-15)*s], fill=BLACK, width=6*s)
    # gritted mouth
    mx0, mx1, my = hcx+4, hcx+36, hcy+40
    d.line([mx0*s, my*s, mx1*s, my*s], fill=BLACK, width=5*s)
    for tx in (mx0+8, mx0+16, mx0+24):
        d.line([tx*s, (my-5)*s, tx*s, (my+5)*s], fill=BLACK, width=3*s)
    return finish(layer)

if __name__ == "__main__":
    bg = Image.open("media-generation-jungle-bg-0-b8d67ee9-4cf4-4d7f-984c-ce65c7440977.webp").convert("RGB")
    def scene(layer, name):
        bw, bh = int(W*1.02), int(H*1.02)
        b = bg.resize((bw, bh), Image.LANCZOS)
        x0 = (bw - W)//2; y0 = bh - H
        f = b.crop((x0, y0, x0+W, y0+H)).convert("RGBA")
        f.alpha_composite(layer)
        f.convert("RGB").save(name)
        print(name, "ok")
    scene(draw_lying(), "test-lying.png")
    scene(draw_pushup(), "test-pushup.png")
