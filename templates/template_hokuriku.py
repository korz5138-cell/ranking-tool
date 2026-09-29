import math
from PIL import Image, ImageDraw, ImageFont

BG = "#0D111C"; CARD = "#1A2030"; CARD2 = "#151B29"; GOLD = "#D4AF37"
TEXT = "#E8ECF5"; SUB = "#8A94AB"; PLUS = "#4FC3F7"; MINUS = "#FF7B8A"
LINE = "#2A3247"; BADGE = "#243049"
RANKC = {1: "#FFD84D", 2: "#C7D0E0", 3: "#E0975A"}

FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FM = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"

_c = {}
def f(p, s):
    k = (p, s)
    if k not in _c:
        _c[k] = ImageFont.truetype(p, s, index=0)
    return _c[k]

def r10(v):
    return int(math.floor(v / 10 + 0.5)) * 10

def sgn(v):
    return f"{v:+,}"

# ===================== データ =====================
STORE = "ダイナム丸岡"
DATE = "9月19日(土)"
TOPIC = "9の日＋北陸ダイナム合同賞品入荷"
TOTAL_DIFF, AVG_DIFF, UNITS, WINS, LOTTERY = 82305, 291, 283, 108, None

matsubi = [None if v is None else r10(v) for v in
           [-160, 1887, 98, -352, 120, 848, 369, -265, -42, 378]]
ZORO = r10(833)

# (機種名, 平均差枚, 平均G数, 勝ち台, 台数)
kishu = [
    ("かぐや様は告らせたい", 2602, 1885, 3, 5),
    ("マギアレコード", 2417, 3007, 4, 5),
    ("沖ドキ!DUO アンコール", 1870, 1226, 2, 4),
    ("真打 吉宗", 1725, 4969, 3, 5),
    ("L戦国乙女5", 1511, 5061, 1, 5),
    ("リコリス・リコイル", 1508, 8015, 6, 10),
    ("モンスターハンターライズ", 1319, 2689, 2, 5),
    ("L東京喰種", 1309, 3787, 12, 20),
    ("バイオハザードRE:3", 1207, 1448, 3, 5),
    ("化物語", 1083, 3620, 3, 5),
]

# (台番, 機種名, 差枚)
dai = [
    (721, "Lタクトオーパス", 16909),
    (806, "ソードアート・オンラインII", 16448),
    (619, "L戦国乙女5", 14206),
    (539, "ミリオンゴッド", 13324),
    (811, "真打 吉宗", 11827),
    (601, "リコリス・リコイル", 10866),
    (771, "沖ドキ!DUO アンコール", 8707),
    (442, "L東京喰種", 8136),
    (736, "ワールドダイスター", 7934),
    (552, "かぐや様は告らせたい", 7847),
    (715, "モグモグ風林火山", 7819),
    (459, "L東京喰種", 6857),
    (455, "L東京喰種", 6730),
    (805, "マギアレコード", 6257),
    (571, "スマスロ北斗の拳", 5973),
    (752, "L南国育ち SPECIAL", 5509),
    (550, "ヴァルヴレイヴ2", 5340),
    (803, "マギアレコード", 5320),
    (703, "モンキーターンV", 5201),
    (508, "北斗の拳 転生の章2", 4828),
]
OUT = "/mnt/user-data/outputs/9_19_ダイナム丸岡_総合データ.png"
# =================================================

W, PAD, GAP = 1400, 40, 24
img = Image.new("RGB", (W, 2600), BG)
d = ImageDraw.Draw(img)

def panel(x0, y0, x1, y1, title):
    d.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=CARD2, outline=LINE)
    d.rounded_rectangle([x0, y0, x1, y0 + 54], radius=16, fill=CARD)
    d.rectangle([x0, y0 + 38, x1, y0 + 54], fill=CARD)
    d.rectangle([x0 + 20, y0 + 15, x0 + 26, y0 + 39], fill=GOLD)
    d.text((x0 + 40, y0 + 27), title, font=f(FB, 31), fill=TEXT, anchor="lm")
    return y0 + 54

# ---------------- ヘッダー ----------------
d.rectangle([0, 0, W, 152], fill=CARD)
d.rectangle([0, 148, W, 152], fill=GOLD)
d.text((PAD, 24), STORE, font=f(FB, 52), fill=TEXT)
d.text((PAD, 88), "スロット全体データ", font=f(FB, 34), fill=GOLD)
_tw = d.textlength("スロット全体データ", font=f(FB, 34))
d.text((PAD + _tw + 26, 92), f"勝率 {WINS}/{UNITS}台 ({WINS/UNITS*100:.1f}%)",
       font=f(FM, 30), fill=SUB)
d.rounded_rectangle([W - PAD - 220, 30, W - PAD, 112], radius=14, fill=BADGE, outline=GOLD)
d.text((W - PAD - 110, 54), "2026年", font=f(FR, 21), fill=SUB, anchor="mm")
d.text((W - PAD - 110, 88), DATE, font=f(FB, 32), fill=TEXT, anchor="mm")

y = 182

# ---------------- トピック ----------------
h = 74
d.rounded_rectangle([PAD, y, W - PAD, y + h], radius=14, fill=CARD2, outline=GOLD)
d.rounded_rectangle([PAD, y, PAD + 160, y + h], radius=14, fill=GOLD)
d.rectangle([PAD + 140, y, PAD + 160, y + h], fill=GOLD)
d.text((PAD + 80, y + h / 2), "トピック", font=f(FB, 27), fill="#1A1405", anchor="mm")
_ts = 30
while d.textlength(TOPIC, font=f(FB, _ts)) > W - PAD * 2 - 220 and _ts > 20:
    _ts -= 1
d.text((PAD + 190, y + h / 2), TOPIC, font=f(FB, _ts), fill=GOLD, anchor="lm")
y += h + GAP

# ---------------- 全体最終データ ----------------
h = 180
top = panel(PAD, y, W - PAD, y + h, "全体最終データ")
colw = (W - PAD * 2) / 3
vals = [("総差枚", f"{sgn(r10(TOTAL_DIFF))}枚" if TOTAL_DIFF > 0 else "－"),
        ("平均差枚", f"{sgn(AVG_DIFF)}枚" if TOTAL_DIFF > 0 else "－"),
        ("抽選人数", "－" if LOTTERY is None else f"{LOTTERY}人")]
for i, (lbl, val) in enumerate(vals):
    cx = PAD + colw * i + colw / 2
    if i:
        d.rectangle([PAD + colw * i, top + 16, PAD + colw * i + 2, y + h - 16], fill=LINE)
    d.text((cx, top + 32), lbl, font=f(FM, 25), fill=SUB, anchor="mm")
    fs = 56 if i == 0 else 48
    while d.textlength(val, font=f(FB, fs)) > colw - 40:
        fs -= 2
    d.text((cx, top + 86), val, font=f(FB, fs),
           fill=PLUS if i < 2 and TOTAL_DIFF > 0 else TEXT, anchor="mm")
y += h + GAP

# ---------------- 中段 ----------------
MID_H = 480
LW = 560
# --- 左: 末尾別 ---
top = panel(PAD, y, PAD + LW, y + MID_H, "末尾別 平均差枚")
rows = [(f"末尾 {i}", v, False) for i, v in enumerate(matsubi)] + [("ゾロ目", ZORO, True)]
rh = (MID_H - 54 - 22) / len(rows)
mx = PAD + LW / 2 + 10
half = 118
SCALE = max([abs(v) for _, v, _ in rows if v is not None]) or 1
for i, (lbl, v, zoro) in enumerate(rows):
    ry = top + 12 + rh * i
    if zoro:
        d.rounded_rectangle([PAD + 12, ry + 1, PAD + LW - 12, ry + rh - 3],
                            radius=8, fill=BADGE, outline=GOLD)
    my = ry + rh / 2
    d.text((PAD + 28, my), lbl, font=f(FM, 25), fill=GOLD if zoro else TEXT, anchor="lm")
    if v is None:
        d.text((PAD + LW - 28, my), "－", font=f(FB, 27), fill=SUB, anchor="rm")
        d.rectangle([mx, ry + 8, mx + 1, ry + rh - 10], fill=LINE)
        continue
    bl = abs(v) / SCALE * half
    col = GOLD if zoro and v >= 0 else (PLUS if v >= 0 else MINUS)
    if v >= 0:
        d.rounded_rectangle([mx, my - 9, mx + bl, my + 9], radius=5, fill=col)
    else:
        d.rounded_rectangle([mx - bl, my - 9, mx, my + 9], radius=5, fill=col)
    d.rectangle([mx, ry + 8, mx + 1, ry + rh - 10], fill=LINE)
    d.text((PAD + LW - 28, my), sgn(v), font=f(FB, 27),
           fill=GOLD if zoro else (PLUS if v >= 0 else MINUS), anchor="rm")

# --- 右: 機種平均 ---
RX = PAD + LW + GAP
top = panel(RX, y, W - PAD, y + MID_H, "機種平均差枚ランキング")
d.text((RX + 420, top + 22), "平均差枚", font=f(FR, 21), fill=SUB, anchor="mm")
d.text((RX + 560, top + 22), "平均G数", font=f(FR, 21), fill=SUB, anchor="mm")
d.text((RX + 676, top + 22), "勝率", font=f(FR, 21), fill=SUB, anchor="mm")
rh = (MID_H - 54 - 44) / len(kishu)
for i, (name, val, gm, w, nn) in enumerate(kishu):
    ry = top + 40 + rh * i
    my = ry + rh / 2
    if i % 2 == 0:
        d.rounded_rectangle([RX + 12, ry + 2, W - PAD - 12, ry + rh - 2], radius=8, fill=CARD)
    d.text((RX + 34, my), str(i + 1), font=f(FB, 26),
           fill=RANKC.get(i + 1, SUB), anchor="lm")
    nm = name
    fn = f(FM, 27)
    while d.textlength(nm, font=fn) > 250:
        fn = f(FM, fn.size - 1)
        if fn.size <= 19:
            break
    d.text((RX + 76, my), nm, font=fn, fill=TEXT, anchor="lm")
    d.text((RX + 470, my), "枚", font=f(FR, 19), fill=SUB, anchor="rm")
    d.text((RX + 448, my), sgn(r10(val)), font=f(FB, 30),
           fill=PLUS if val >= 0 else MINUS, anchor="rm")
    d.text((RX + 600, my), "G", font=f(FR, 19), fill=SUB, anchor="rm")
    d.text((RX + 580, my), f"{gm:,}", font=f(FM, 26), fill=TEXT, anchor="rm")
    d.text((RX + 700, my - 10), f"{w}/{nn}", font=f(FM, 24), fill=TEXT, anchor="rm")
    d.text((RX + 704, my - 10), "台", font=f(FR, 18), fill=SUB, anchor="lm")
    BX, BW = RX + 640, 74
    d.rectangle([BX, my + 12, BX + BW, my + 17], fill=LINE)
    d.rectangle([BX, my + 12, BX + BW * (w / nn), my + 17], fill=PLUS)
y += MID_H + GAP

# ---------------- 台別 TOP20 ----------------
rowh = 46
h = 54 + 18 + rowh * 10 + 18
top = panel(PAD, y, W - PAD, y + h, "台別差枚 TOP20")
colw = (W - PAD * 2) / 2
for i, (num, name, val) in enumerate(dai):
    c, rr = divmod(i, 10)
    x0 = PAD + colw * c
    ry = top + 14 + rr * rowh
    if rr % 2 == 0:
        d.rounded_rectangle([x0 + 14, ry, x0 + colw - 14, ry + rowh - 4], radius=8, fill=CARD)
    my = ry + rowh / 2 - 2
    rk = i + 1
    rc = RANKC.get(rk, "#52D6A8" if rk <= 5 else ("#6FD1FF" if rk <= 10 else "#5C6680"))
    d.text((x0 + 46, my), str(rk), font=f(FB, 34 if rk <= 3 else 26), fill=rc, anchor="mm")
    bx, BWD = x0 + 76, 92
    d.rounded_rectangle([bx, my - 16, bx + BWD, my + 16], radius=8, fill=BADGE, outline=LINE)
    d.text((bx + BWD / 2, my), str(num), font=f(FB, 23), fill=TEXT, anchor="mm")
    xv = x0 + colw - 26
    d.text((xv, my), "枚", font=f(FR, 19), fill=SUB, anchor="rm")
    d.text((xv - 22, my), sgn(r10(val)), font=f(FB, 29),
           fill=PLUS if val >= 0 else MINUS, anchor="rm")
    xn = bx + BWD + 16
    nmax = xv - 44 - d.textlength(sgn(r10(val)), font=f(FB, 29)) - 16 - xn
    fn = f(FM, 25)
    nm = name
    while d.textlength(nm, font=fn) > nmax and fn.size > 18:
        fn = f(FM, fn.size - 1)
    while d.textlength(nm, font=fn) > nmax and len(nm) > 4:
        nm = nm[:-1]
    if nm != name and len(nm) < len(name):
        nm += "…"
    d.text((xn, my), nm, font=fn, fill=TEXT, anchor="lm")
y += h + 34

img = img.crop((0, 0, W, y))
img.save(OUT)
print("saved", img.size)
