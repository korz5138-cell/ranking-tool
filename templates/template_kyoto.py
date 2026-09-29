import math
from PIL import Image, ImageDraw, ImageFont

BAND = "#C93A1E"; ORANGE = "#EE8B2B"; DEEP = "#8E2A14"
BG = "#FFFFFF"; PAPER = "#FAF4EA"; TEXT = "#241C18"
SUB = "#9A8C7E"; GREY = "#6E6259"; LINE = "#E6DCCC"

FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FM = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"
FR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FMIN = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
FMINR = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"

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
STORE = "京都フォーカス"
AREA = "京都市南区"
DATESTR = "2026.09.18"
DATEBIG = "9.18"
DATEDOW = "FRI  金曜日"
TOPIC = "リニューアルオープン初日＋スロパチガール"
TOTAL_DIFF, AVG_DIFF, UNITS, WINS, LOTTERY = 140575, 696, 202, 106, None

matsubi = [None if v is None else r10(v) for v in
           [-324, 793, 1072, 1293, 479, 983, 752, 584, 637, 665]]
ZORO = r10(983)

# (機種名, 平均差枚, 平均G数, 勝ち台, 台数)
kishu = [
    ("ヴァルヴレイヴ2", 3925, 5502, 2, 3),
    ("L戦国乙女5", 3233, 2961, 2, 3),
    ("スマスロ北斗の拳", 2700, 4320, 6, 7),
    ("L少女☆歌劇レヴュー", 2632, 6199, 1, 2),
    ("L東京喰種", 2324, 4432, 7, 11),
    ("L炎炎ノ消防隊2", 2019, 5917, 2, 3),
    ("甲鉄城のカバネリ", 2002, 4183, 6, 8),
    ("バイオハザードRE:3", 1936, 3190, 2, 2),
    ("モンキーターンV", 1785, 3524, 4, 7),
    ("ビッグドリーム", 1774, 1240, 1, 2),
]

# (台番, 機種名, 差枚, BB, RB, ART/合算, G数)
dai_at = [
    (112, "彼女、お借りします", 9520, 92, 5, 0, 3846),
    (125, "L東京喰種", 9031, 59, 11, 0, 3310),
    (98, "リコリス・リコイル", 8734, 101, 0, 0, 6920),
    (321, "モンキーターンV", 8078, 66, 12, 0, 2490),
    (372, "甲鉄城のカバネリ", 7984, 70, 18, 0, 2938),
    (327, "ゴッドイーター", 7328, 77, 4, 0, 2991),
    (333, "L戦国乙女5", 7171, 66, 28, 0, 3023),
    (123, "L東京喰種", 7015, 59, 16, 0, 3648),
    (342, "ヴァルヴレイヴ2", 7015, 99, 5, 0, 5911),
    (366, "スマスロ北斗の拳", 6828, 93, 18, 0, 4505),
]
dai_a = [
    (425, "ゴーゴージャグラー3", 3006, 33, 33, 66, 7226),
    (317, "スマスロ ハナビ", 2847, 29, 23, 52, 6283),
    (428, "ゴーゴージャグラー3", 2557, 35, 36, 71, 7429),
    (417, "マイジャグラーV", 2505, 37, 23, 60, 7466),
    (431, "ネオアイムジャグラーEX", 2447, 36, 22, 58, 6864),
    (315, "スマスロ ハナビ", 2213, 28, 23, 51, 6669),
    (407, "ネオアイムジャグラーEX", 2187, 30, 26, 56, 6354),
    (421, "ジャグラーガールズSS", 2130, 35, 24, 59, 7482),
    (429, "ネオアイムジャグラーEX", 1796, 34, 28, 62, 7352),
    (423, "ミスタージャグラー", 1739, 32, 32, 64, 7358),
]
OUT = "/mnt/user-data/outputs/9_18_京都フォーカス_総合データ.png"
# =================================================

W = 1400
SIDE = 92          # 左サイドバー幅
L = SIDE + 40
R = W - 48

img = Image.new("RGB", (W, 3400), BG)
d = ImageDraw.Draw(img)

# ---------------- ヘッダー ----------------
y = 40
DW, DH = 262, 112
dx0, dy0 = R - DW, y - 2
d.rectangle([dx0, dy0, R, dy0 + DH], fill=BAND)
d.rectangle([dx0, dy0 + DH, R, dy0 + DH + 7], fill=ORANGE)
d.text((dx0 + DW / 2, dy0 + 22), "2026", font=f(FR, 19), fill="#F7C9B6", anchor="mm")
d.text((dx0 + DW / 2, dy0 + 58), DATEBIG, font=f(FB, 52), fill="#FFF6EA", anchor="mm")
d.text((dx0 + DW / 2, dy0 + 94), DATEDOW, font=f(FM, 19), fill="#F7C9B6", anchor="mm")

d.text((L, y + 6), AREA, font=f(FM, 24), fill=BAND, anchor="lm")
_fs = 54
while d.textlength(STORE, font=f(FMIN, _fs)) > dx0 - L - 40 and _fs > 34:
    _fs -= 2
d.text((L, y + 24), STORE, font=f(FMIN, _fs), fill=TEXT)
y += 116

d.rectangle([L, y, R, y + 4], fill=TEXT)
y += 18

# ---------------- トピック ----------------
d.rectangle([L, y + 4, L + 94, y + 40], fill=BAND)
d.text((L + 47, y + 22), "TOPIC", font=f(FB, 21), fill="#FFF6EA", anchor="mm")
d.text((L + 112, y + 22), TOPIC, font=f(FB, 25), fill=TEXT, anchor="lm")
y += 62

# ---------------- 全体データ ----------------
items = [("総差枚", f"{sgn(r10(TOTAL_DIFF))}", "枚", 66),
         ("平均差枚", f"{sgn(AVG_DIFF)}", "枚", 50),
         ("抽選人数", "－" if LOTTERY is None else str(LOTTERY),
          None if LOTTERY is None else "人", 44)]
y += 10
for lbl, val, unit, size in items:
    rowh = 78 if size >= 60 else 56
    cy = y + rowh / 2 - (6 if size >= 60 else 0)
    d.text((L, cy), lbl, font=f(FM, 26), fill=GREY, anchor="lm")
    if unit:
        d.text((R, cy + (16 if size >= 60 else 12)), unit, font=f(FR, 22), fill=SUB, anchor="rm")
        d.text((R - 34, cy), val, font=f(FB, size), fill=BAND, anchor="rm")
    else:
        d.text((R, cy), val, font=f(FB, size), fill=SUB, anchor="rm")
    x = L + d.textlength(lbl, font=f(FM, 26)) + 20
    while x < R - 300:
        d.rectangle([x, cy, x + 3, cy + 2], fill=LINE)
        x += 12
    y += rowh
    d.rectangle([L, y, R, y + 1], fill=LINE)
    y += 6

d.text((L, y + 24), "末尾別 平均差枚", font=f(FMIN, 32), fill=BAND, anchor="lm")
d.text((R, y + 24), f"全{UNITS}台中 プラス {WINS}台 ／ {WINS/UNITS*100:.1f}%",
       font=f(FR, 22), fill=SUB, anchor="rm")
y += 54

# ---------------- 末尾：縦棒グラフ ----------------
CH_TOP = y
CH_H = 320
labels = [str(i) for i in range(10)] + ["ゾロ"]
vals = matsubi + [ZORO]
n = len(vals)
slot = (R - L) / n
SCALE = max(abs(v) for v in vals if v is not None)
zero_y = CH_TOP + CH_H * 0.62
d.rectangle([L, zero_y, R, zero_y + 2], fill=TEXT)
for i, (lb, v) in enumerate(zip(labels, vals)):
    cx = L + slot * i + slot / 2
    bw = slot * 0.42
    if v is None:
        d.text((cx, zero_y - 14), "－", font=f(FB, 24), fill=SUB, anchor="ms")
        d.text((cx, CH_TOP + CH_H + 6), lb, font=f(FM, 24), fill=SUB, anchor="ms")
        continue
    hgt = abs(v) / SCALE * (CH_H * 0.52 if v >= 0 else CH_H * 0.3)
    col = ORANGE if lb == "ゾロ" else (BAND if v >= 0 else GREY)
    if v >= 0:
        d.rectangle([cx - bw / 2, zero_y - hgt, cx + bw / 2, zero_y], fill=col)
        d.text((cx, zero_y - hgt - 14), sgn(v), font=f(FB, 22), fill=col, anchor="ms")
    else:
        d.rectangle([cx - bw / 2, zero_y + 2, cx + bw / 2, zero_y + 2 + hgt], fill=col)
        d.text((cx, zero_y + 2 + hgt + 26), sgn(v), font=f(FB, 22), fill=col, anchor="ms")
    d.text((cx, CH_TOP + CH_H + 6), lb, font=f(FM, 24),
           fill=BAND if lb == "ゾロ" else GREY, anchor="ms")
y = CH_TOP + CH_H + 24
d.rectangle([L, y, R, y + 1], fill=LINE)
y += 24

# ---------------- 機種平均：2列カード ----------------
d.text((L, y), "機種平均差枚", font=f(FMIN, 32), fill=BAND)
d.text((R, y + 26), "2台以上設置／上位10機種", font=f(FR, 21), fill=SUB, anchor="rs")
y += 44
cw = (R - L - 24) / 2
ch = 100
for i, (name, val, gm, w, nn) in enumerate(kishu):
    c, rr = divmod(i, 5)
    x0 = L + c * (cw + 24)
    y0 = y + rr * (ch + 14)
    d.rectangle([x0, y0, x0 + cw, y0 + ch], fill=PAPER)
    d.rectangle([x0, y0, x0 + 8, y0 + ch], fill=BAND if i < 3 else ORANGE)
    d.text((x0 + 28, y0 + 30), f"{i+1}", font=f(FMIN, 40),
           fill=BAND if i < 3 else SUB, anchor="lm")
    nm = name
    fn = f(FM, 27)
    while d.textlength(nm, font=fn) > cw - 250 and len(nm) > 4:
        nm = nm[:-1]
    if nm != name:
        nm += "…"
    d.text((x0 + 76, y0 + 30), nm, font=fn, fill=TEXT, anchor="lm")
    d.text((x0 + cw - 18, y0 + 32), "枚", font=f(FR, 19), fill=SUB, anchor="rm")
    d.text((x0 + cw - 40, y0 + 30), sgn(r10(val)), font=f(FB, 32),
           fill=BAND if val >= 0 else GREY, anchor="rm")
    d.text((x0 + 28, y0 + 72), f"平均 {gm:,}G", font=f(FR, 21), fill=SUB, anchor="lm")
    BX, BW = x0 + 160, 118
    d.rectangle([BX, y0 + 68, BX + BW, y0 + 76], fill=LINE)
    d.rectangle([BX, y0 + 68, BX + BW * (w / nn), y0 + 76], fill=ORANGE)
    d.text((x0 + cw - 18, y0 + 72), f"勝率 {w}/{nn}台", font=f(FR, 21), fill=SUB, anchor="rm")
y += ch * 5 + 14 * 4 + 40

# ---------------- 台別ランキング ----------------
def draw_rank_block(y, title, note, items, is_at):
    d.text((L, y), title, font=f(FMIN, 32), fill=BAND)
    d.text((R, y + 26), note, font=f(FR, 21), fill=SUB, anchor="rs")
    y += 44
    cw = (R - L - 20) / 2
    ch = 92
    for i, it in enumerate(items):
        num, name, val, bb, rb, third, g = it
        c, rr = divmod(i, 5)
        x0 = L + c * (cw + 20)
        y0 = y + rr * (ch + 8)
        ch_i = ch + 6 if rr == 4 else ch
        d.rectangle([x0, y0, x0 + cw, y0 + ch_i], fill=PAPER if i % 2 == 0 else "#FFFFFF",
                    outline=LINE)
        _bar = BAND if i < 3 else ORANGE
        d.rectangle([x0, y0, x0 + cw, y0 + 5], fill=_bar)
        if rr == 4:
            d.rectangle([x0, y0 + ch_i - 5, x0 + cw, y0 + ch_i], fill=_bar)
        d.text((x0 + 18, y0 + 32), f"{i+1}", font=f(FMIN, 31),
               fill=BAND if i < 3 else SUB, anchor="lm")
        d.text((x0 + 68, y0 + 22), f"{num}番台", font=f(FM, 20), fill=SUB, anchor="lm")
        fn = f(FM, 26)
        nm = name
        while d.textlength(nm, font=fn) > cw - 300 and len(nm) > 4:
            nm = nm[:-1]
        if nm != name:
            nm += "…"
        d.text((x0 + 68, y0 + 48), nm, font=fn, fill=TEXT, anchor="lm")
        d.text((x0 + cw - 20, y0 + 36), "枚", font=f(FR, 19), fill=SUB, anchor="rm")
        d.text((x0 + cw - 42, y0 + 36), sgn(r10(val)), font=f(FB, 32),
               fill=BAND if val >= 0 else GREY, anchor="rm")
        d.rectangle([x0 + 16, y0 + 64, x0 + cw - 16, y0 + 65], fill=LINE)
        fl, fv = f(FR, 18), f(FM, 22)
        if is_at:
            stats = [("BB", f"{bb:,}"), ("RB", f"{rb:,}"),
                     ("ART", "－" if third == 0 else f"{third:,}"), ("G数", f"{g:,}")]
        else:
            tot = bb + rb
            stats = [("BB", f"{bb:,}"), ("RB", f"{rb:,}"),
                     ("合算", "－" if tot == 0 else f"1/{round(g/tot)}"), ("G数", f"{g:,}")]
        sx = x0 + 16
        for sl, sv in stats:
            d.text((sx, y0 + 79), sl, font=fl, fill=SUB, anchor="lm")
            d.text((sx + d.textlength(sl, font=fl) + 6, y0 + 79), sv, font=fv, fill=TEXT, anchor="lm")
            sx += d.textlength(sl, font=fl) + d.textlength(sv, font=fv) + 26
    return y + ch * 5 + 6 + 8 * 4 + 32

y = draw_rank_block(y, "台別差枚 AT機 TOP10", "AT機", dai_at, True)
y += 12
y = draw_rank_block(y, "台別差枚 Aタイプ TOP10", "ノーマルタイプ", dai_a, False)
y += 10

H = y
img = img.crop((0, 0, W, H))
d = ImageDraw.Draw(img)

# ---------------- 左サイドバー ----------------
d.rectangle([0, 0, SIDE - 10, H], fill=BAND)
d.rectangle([SIDE - 10, 0, SIDE - 4, H], fill=ORANGE)

def vtext(cx, top, s, font, fill):
    yy = top
    for chx in s:
        d.text((cx, yy), chx, font=font, fill=fill, anchor="mt")
        yy += font.size + 6
    return yy

vtext((SIDE - 10) / 2, 34, STORE, f(FMIN, 26), "#FFF6EA")
bot = f(FM, 22)
s2 = f"SLOT TOTAL DATA   {DATESTR}"
tmp = Image.new("RGB", (int(bot.getlength(s2)) + 20, 40), BAND)
td = ImageDraw.Draw(tmp)
td.text((10, 20), s2, font=bot, fill="#F7C9B6", anchor="lm")
tmp = tmp.rotate(90, expand=True)
img.paste(tmp, (int((SIDE - 10) / 2 - tmp.width / 2), H - tmp.height - 40))

img.save(OUT)
print("saved", img.size)
