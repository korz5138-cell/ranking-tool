import math
from PIL import Image, ImageDraw, ImageFont

BG = "#0D111C"; CARD = "#1A2030"; CARD2 = "#151B29"; GOLD = "#D4AF37"
TEXT = "#E8ECF5"; SUB = "#8A94AB"; PLUS = "#4FC3F7"; MINUS = "#FF7B8A"
LINE = "#2A3247"; BADGE = "#243049"

FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FM = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"

_c = {}
def f(p, s):
    k = (p, s)
    if k not in _c:
        _c[k] = ImageFont.truetype(p, s, index=0)
    return _c[k]

def sgn(v):
    return f"{v:+,}"

STORE = "マルハン富山店"
DATE = "9月27日(日)"

# ブロック: (見出し, 角台の台番, [(台番, 差枚, G数, BB, RB)])
blocks = [
    ("スマスロ北斗の拳", [
        (643, 1400, 7441, 88, 31),
        (644, 3500, 6428, 94, 20),
        (645, 1100, 6486, 77, 20),
        (646, 2800, 6833, 89, 26),
        (647, 2900, 6277, 85, 20),
        (690, 1000, 6638, 71, 21),
        (691, 1600, 5815, 72, 20),
        (692, 3500, 6738, 101, 22),
        (693, 3500, 6457, 94, 23),
        (694, 5800, 6857, 114, 20),
        (695, -300, 7228, 70, 17),
    ]),
]
KADO = set()

W, PAD = 1400, 40
img = Image.new("RGB", (W, 2600), BG)
d = ImageDraw.Draw(img)

def panel(x0, y0, x1, y1, title, note=""):
    d.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=CARD2, outline=LINE)
    d.rounded_rectangle([x0, y0, x1, y0 + 54], radius=16, fill=CARD)
    d.rectangle([x0, y0 + 38, x1, y0 + 54], fill=CARD)
    d.rectangle([x0 + 20, y0 + 15, x0 + 26, y0 + 39], fill=GOLD)
    d.text((x0 + 40, y0 + 27), title, font=f(FB, 31), fill=TEXT, anchor="lm")
    if note:
        d.text((x1 - 22, y0 + 28), note, font=f(FR, 22), fill=SUB, anchor="rm")
    return y0 + 54

# ヘッダー
d.rectangle([0, 0, W, 152], fill=CARD)
d.rectangle([0, 148, W, 152], fill=GOLD)
d.text((PAD, 24), STORE, font=f(FB, 52), fill=TEXT)
d.text((PAD, 88), "北斗の拳 全台データ", font=f(FB, 34), fill=GOLD)
d.rounded_rectangle([W - PAD - 220, 30, W - PAD, 112], radius=14, fill=BADGE, outline=GOLD)
d.text((W - PAD - 110, 54), "2026年", font=f(FR, 21), fill=SUB, anchor="mm")
d.text((W - PAD - 110, 88), DATE, font=f(FB, 32), fill=TEXT, anchor="mm")

y = 182
rowh = 56

for title, units in blocks:
    tot = sum(u[1] for u in units)
    wins = sum(1 for u in units if u[1] > 0)
    h = 54 + 16 + 40 + rowh * len(units) + 16
    top = panel(PAD, y, W - PAD, y + h, title,
                f"{len(units)}台 ／ 平均 {sgn(round(tot/len(units)/10)*10):>6} 枚 ／ 勝率 {wins}/{len(units)}台")
    # 見出し行
    hy = top + 26
    d.text((PAD + 74, hy), "台番", font=f(FR, 21), fill=SUB, anchor="mm")
    d.text((PAD + 148, hy), "機種", font=f(FR, 21), fill=SUB, anchor="lm")
    d.text((PAD + 500, hy), "差枚", font=f(FR, 21), fill=SUB, anchor="mm")
    d.text((PAD + 620, hy), "G数", font=f(FR, 21), fill=SUB, anchor="mm")
    d.text((PAD + 810, hy), "BB", font=f(FR, 21), fill=SUB, anchor="mm")
    d.text((PAD + 980, hy), "RB", font=f(FR, 21), fill=SUB, anchor="mm")
    d.text((PAD + 1180, hy), "合算", font=f(FR, 21), fill=SUB, anchor="mm")
    for i, (num, val, g, bb, rb) in enumerate(units):
        ry = top + 44 + rowh * i
        my = ry + rowh / 2 - 2
        kado = num in KADO
        if kado:
            d.rounded_rectangle([PAD + 14, ry + 1, W - PAD - 14, ry + rowh - 5],
                                radius=9, fill=BADGE, outline=GOLD)
        elif i % 2 == 0:
            d.rounded_rectangle([PAD + 14, ry + 1, W - PAD - 14, ry + rowh - 5],
                                radius=9, fill=CARD)
        bx, BWD = PAD + 24, 100
        d.rounded_rectangle([bx, my - 17, bx + BWD, my + 17], radius=8,
                            fill=GOLD if kado else BADGE, outline=LINE)
        d.text((bx + BWD / 2, my), str(num), font=f(FB, 25),
               fill="#1A1405" if kado else TEXT, anchor="mm")
        d.text((PAD + 148, my), title, font=f(FM, 23), fill=TEXT, anchor="lm")
        d.text((PAD + 550, my), "枚", font=f(FR, 19), fill=SUB, anchor="rm")
        d.text((PAD + 528, my), sgn(val), font=f(FB, 30),
               fill=PLUS if val > 0 else (MINUS if val < 0 else SUB), anchor="rm")
        d.text((PAD + 690, my), f"{g:,}", font=f(FM, 26), fill=TEXT, anchor="rm")
        d.text((PAD + 710, my), "G", font=f(FR, 19), fill=SUB, anchor="lm")
        bf = f(FB, 34 if kado else 28)
        d.text((PAD + 850, my), str(bb), font=bf, fill=GOLD if kado else TEXT, anchor="rm")
        d.text((PAD + 1020, my), str(rb), font=bf, fill=GOLD if kado else TEXT, anchor="rm")
        tt = bb + rb
        d.text((PAD + 1220, my), f"1/{round(g/tt)}" if tt else "－",
               font=f(FM, 26), fill=TEXT, anchor="rm")
    y += h + 24

img = img.crop((0, 0, W, y + 10))
img.save("/mnt/user-data/outputs/9_27_マルハン富山店_北斗の拳.png")
print("saved", img.size)
