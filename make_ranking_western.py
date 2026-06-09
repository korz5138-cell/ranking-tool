#!/usr/bin/env python3
"""差枚ランキング画像生成（英語取材・アメリカンヴィンテージ風デザイン）

データ読込・ファイル名解析は make_ranking_kamiko の機能を再利用し、
本ファイルは render_image のみ独自実装。
"""
import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# 神の子側のフォント解決・ローダーを再利用
from make_ranking_kamiko import (
    FONT_HEAVY, FONT_BOLD, FONT_MED, font,
    parse_filename, load_ranking,
)

# ===== カラーパレット（アメリカンヴィンテージ）=====
COL_PAPER       = (242, 226, 196)         # クリーム/紙
COL_PAPER_DEEP  = (220, 200, 160)
COL_STRIPE      = (236, 220, 188)         # 行の薄ストライプ
COL_NAVY        = (32, 46, 84)            # 紺
COL_NAVY_DEEP   = (20, 30, 60)
COL_RED         = (180, 50, 45)           # ヴィンテージレッド
COL_RED_DEEP    = (135, 30, 28)
COL_GOLD        = (212, 160, 46)          # 金
COL_GOLD_LIGHT  = (240, 200, 80)
COL_BROWN       = (107, 74, 48)
COL_BROWN_DARK  = (70, 45, 25)
COL_WHITE       = (252, 248, 240)
COL_FLAG_BLUE   = (31, 46, 96)


# ===== 描画ヘルパー =====
def draw_star(draw, cx, cy, r, fill, outline=None, outline_w=0, points=5):
    pts = []
    for i in range(points * 2):
        ang = math.radians(-90 + 180 * i / points)
        rad = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    if outline:
        draw.polygon(pts, fill=fill, outline=outline)
    else:
        draw.polygon(pts, fill=fill)


def draw_paper_bg(img, w, h):
    """紙風の背景（クリーム + うっすらノイズ風グラデ）。"""
    base = Image.new('RGB', (w, h), COL_PAPER)
    # 上下にうっすら陰
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(h):
        # 端ほど暗くする
        t = abs(y - h / 2) / (h / 2)
        a = int(20 * t)
        od.line([(0, y), (w, y)], fill=(120, 90, 50, a))
    base.paste(Image.alpha_composite(base.convert('RGBA'), overlay).convert('RGB'))
    img.paste(base, (0, 0))


def draw_flag_band(img, draw, x, y, w, h, side='left'):
    """側面の星条旗パターン。
    上半分: 青背景に白星 / 下半分: 赤白ストライプ。
    """
    # 青い canton
    canton_h = int(h * 0.4)
    draw.rectangle([x, y, x + w, y + canton_h], fill=COL_FLAG_BLUE)
    # ランダムっぽく星を配置
    star_r = max(6, w // 12)
    cols = max(2, w // (star_r * 3))
    rows = max(3, canton_h // (star_r * 3))
    sx = w / (cols + 1)
    sy = canton_h / (rows + 1)
    for r in range(rows):
        for c in range(cols):
            off = (sx / 2) if r % 2 else 0
            cx = x + sx * (c + 1) + off
            cy = y + sy * (r + 1)
            if cx < x + w - star_r:
                draw_star(draw, cx, cy, star_r, COL_WHITE)

    # 赤白ストライプ
    stripes = 7
    sh = (h - canton_h) / stripes
    for i in range(stripes):
        c = COL_RED if i % 2 == 0 else COL_WHITE
        sy_ = y + canton_h + i * sh
        draw.rectangle([x, sy_, x + w, sy_ + sh + 1], fill=c)


def draw_title_panel(img, draw, x, y, w, h, title='差枚ランキング'):
    """タイトルパネル：クリーム角丸 + 紺ボーダー + 中央にタイトル文字。"""
    # 影
    sh = Image.new('RGBA', (w + 30, h + 30), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle([10, 10, w + 10, h + 10], radius=22, fill=(0, 0, 0, 60))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    img.paste(sh, (x - 5, y - 5), sh)

    # 本体パネル
    draw.rounded_rectangle([x, y, x + w, y + h], radius=22,
                           fill=COL_PAPER, outline=COL_NAVY, width=4)
    # 二重ボーダー
    draw.rounded_rectangle([x + 8, y + 8, x + w - 8, y + h - 8], radius=16,
                           outline=COL_NAVY, width=2)

    # 縦方向に分割: 上 1/3 を "☆ Slot ☆"、下 2/3 を "差枚ランキング" のセンター
    sub_cy = y + h * 0.28
    title_cy = y + h * 0.62

    # "☆ Slot ☆"
    f_sub = font(FONT_BOLD, 24)
    draw.text((x + w / 2, sub_cy), '☆  Slot  ☆',
              font=f_sub, fill=COL_NAVY, anchor='mm')

    # メインタイトル「差枚/差玉ランキング」: ブラウンの太い縁取り + 金本体
    f_title = font(FONT_HEAVY, 68)
    draw.text((x + w / 2, title_cy), title,
              font=f_title, fill=COL_GOLD_LIGHT, anchor='mm',
              stroke_width=6, stroke_fill=COL_BROWN_DARK)
    # 軽く赤みを下にも乗せる演出（影として少し下にずらして描画）
    draw.text((x + w / 2 + 1, title_cy + 4), title,
              font=f_title, fill=COL_RED, anchor='mm',
              stroke_width=2, stroke_fill=COL_BROWN_DARK)
    # もう一度ゴールドで上書き（メインの色味）
    draw.text((x + w / 2, title_cy), title,
              font=f_title, fill=COL_GOLD_LIGHT, anchor='mm',
              stroke_width=3, stroke_fill=COL_BROWN_DARK)


def draw_date_badge(img, draw, cx, cy, r, date_str):
    """円形の集計日バッジ（星のリングが周囲を囲む）。"""
    # 外側薄影
    sh = Image.new('RGBA', (r * 2 + 30, r * 2 + 30), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.ellipse([15, 15, r * 2 + 15, r * 2 + 15], fill=(0, 0, 0, 70))
    sh = sh.filter(ImageFilter.GaussianBlur(6))
    img.paste(sh, (cx - r - 5, cy - r - 5), sh)

    # 円本体（ブラウン）
    draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                 fill=COL_BROWN, outline=COL_BROWN_DARK, width=3)
    # 内側に薄リング
    draw.ellipse([cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8],
                 outline=COL_GOLD, width=2)

    # 周囲に星を配置
    n_stars_top = 5
    n_stars_bot = 5
    for i in range(n_stars_top):
        ang = math.radians(-90 - 60 + 30 * i)
        sx = cx + (r - 16) * math.cos(ang)
        sy = cy + (r - 16) * math.sin(ang)
        draw_star(draw, sx, sy, 5, COL_GOLD_LIGHT)
    for i in range(n_stars_bot):
        ang = math.radians(90 - 60 + 30 * i)
        sx = cx + (r - 16) * math.cos(ang)
        sy = cy + (r - 16) * math.sin(ang)
        draw_star(draw, sx, sy, 5, COL_GOLD_LIGHT)

    # 「集計日」
    f_label = font(FONT_BOLD, 16)
    draw.text((cx, cy - 14), '集計日', font=f_label,
              fill=COL_GOLD_LIGHT, anchor='mm')
    # 日付（M/D）
    f_date = font(FONT_HEAVY, 28)
    draw.text((cx, cy + 16), date_str, font=f_date,
              fill=COL_WHITE, anchor='mm')


def draw_rank_badge(draw, x, y, w, h, rank):
    """順位バッジ。1-3位は二重線+星付き、4-10位はシンプル。"""
    cx = x + w / 2
    cy = y + h / 2

    if rank <= 3:
        # 二重ボーダー円
        draw.ellipse([x + 6, y + 4, x + w - 6, y + h - 4],
                     fill=COL_PAPER, outline=COL_NAVY, width=3)
        draw.ellipse([x + 10, y + 8, x + w - 10, y + h - 8],
                     outline=COL_NAVY, width=1)
        # 数字
        f = font(FONT_HEAVY, 36)
        draw.text((cx - 6, cy + 2), str(rank), font=f,
                  fill=COL_RED if rank == 1 else (COL_NAVY if rank == 2 else COL_BROWN),
                  anchor='mm', stroke_width=2, stroke_fill=COL_PAPER)
        # 「位」
        f_p = font(FONT_BOLD, 14)
        draw.text((cx + 14, cy + 8), '位', font=f_p, fill=COL_NAVY, anchor='lm')
    else:
        # シンプル円
        draw.ellipse([x + 8, y + 6, x + w - 8, y + h - 6],
                     fill=COL_PAPER, outline=COL_NAVY, width=2)
        f = font(FONT_HEAVY, 28)
        draw.text((cx - 4, cy + 2), str(rank), font=f,
                  fill=COL_NAVY, anchor='mm')
        f_p = font(FONT_BOLD, 12)
        draw.text((cx + 12, cy + 6), '位', font=f_p, fill=COL_NAVY, anchor='lm')


# ===== メイン描画 =====
def render_image(ranking, date_full, store, out_path):
    """date_full: 'YYYYMMDD' / store: 店舗名"""
    yyyy = date_full[:4]
    mm = int(date_full[4:6])
    dd = int(date_full[6:8])
    date_str = f'{mm}/{dd}'
    footer_date = f'{yyyy}年{mm}月{dd}日'

    # パチンコ/スロット判定
    is_pachi = bool(ranking) and ranking[0].get('kind') == 'pachinko'
    lbl_diff = '差玉' if is_pachi else '差枚'
    lbl_unit = '発' if is_pachi else '枚'
    title_main = f'{lbl_diff}ランキング'
    play_label = '4円パチンコ' if is_pachi else '20スロ'

    has_bb_rb = bool(ranking) and ('bb' in ranking[0]) and (ranking[0].get('bb') is not None)

    # ===== レイアウト =====
    PAD = 12
    SIDE_BAND = 60      # 両端の星条旗バンド幅
    INNER_X = SIDE_BAND + PAD
    COLS = [
        ('rank', '順位',   110),
        ('dai',  '台番号', 180),
        ('name', '機種名', 360 if has_bb_rb else 510),
        ('sa',   lbl_diff, 200),
    ]
    if has_bb_rb:
        COLS.append(('bb', 'BB', 110))
        COLS.append(('rb', 'RB', 110))

    INNER_W = sum(c[2] for c in COLS)
    W = INNER_W + SIDE_BAND * 2 + PAD * 2

    HEADER_H = 210
    ROW_H = 64
    N = len(ranking)
    FOOTER_H = 88
    H = HEADER_H + ROW_H * N + FOOTER_H + 12

    # ===== 背景 =====
    img = Image.new('RGB', (W, H), COL_PAPER)
    draw_paper_bg(img, W, H)
    draw = ImageDraw.Draw(img)

    # 両端の星条旗
    draw_flag_band(img, draw, 0, 0, SIDE_BAND, H, side='left')
    draw_flag_band(img, draw, W - SIDE_BAND, 0, SIDE_BAND, H, side='right')

    # ===== ヘッダー: タイトル + 日付バッジ =====
    title_w = INNER_W - 180
    title_h = 130
    draw_title_panel(img, draw, INNER_X + 30, 18, title_w, title_h, title=title_main)

    # 日付バッジ（右上）
    badge_r = 60
    badge_cx = W - SIDE_BAND - PAD - badge_r - 4
    badge_cy = 18 + badge_r + 4
    draw_date_badge(img, draw, badge_cx, badge_cy, badge_r, date_str)

    # ===== テーブルヘッダー =====
    hb_y = HEADER_H - 38
    draw.rectangle([INNER_X, hb_y, INNER_X + INNER_W, hb_y + 38],
                   fill=COL_NAVY_DEEP)
    f_head = font(FONT_HEAVY, 20)
    cx = INNER_X
    for j, (_, lbl, w) in enumerate(COLS):
        draw.text((cx + w / 2, hb_y + 19), lbl, font=f_head,
                  fill=COL_GOLD_LIGHT, anchor='mm')
        cx += w
        if j < len(COLS) - 1:
            draw_star(draw, cx, hb_y + 19, 5, COL_GOLD_LIGHT)

    # ===== 行 =====
    f_rk_lbl = font(FONT_BOLD, 14)
    f_dai    = font(FONT_HEAVY, 30)
    f_dai_lb = font(FONT_BOLD, 13)
    f_nm_l   = [font(FONT_HEAVY, s) for s in (28, 24, 20, 17)]
    f_val    = font(FONT_HEAVY, 30)
    f_unit   = font(FONT_BOLD, 13)
    f_count  = font(FONT_HEAVY, 26)
    f_count_u = font(FONT_BOLD, 12)

    def split_two(text, fnt, maxw):
        sep = [i for i, c in enumerate(text) if c in ' 　・-‐ｰー']
        best = None
        for i in sep:
            L = text[:i].rstrip()
            R = text[i + 1:].lstrip()
            if (draw.textlength(L, font=fnt) <= maxw and
                    draw.textlength(R, font=fnt) <= maxw):
                best = (L, R)
        if best:
            return best
        mid = len(text) // 2
        for off in range(0, len(text)):
            for k in (mid - off, mid + off):
                if 0 < k < len(text):
                    L, R = text[:k], text[k:]
                    if (draw.textlength(L, font=fnt) <= maxw and
                            draw.textlength(R, font=fnt) <= maxw):
                        return L, R
        R = text[mid:]
        while draw.textlength(R + '…', font=fnt) > maxw and len(R) > 1:
            R = R[:-1]
        return text[:mid], R + '…'

    y = HEADER_H
    for i, item in enumerate(ranking):
        rk = i + 1
        # 行背景（クリーム/薄ブラウンの交互）
        bg = COL_PAPER if i % 2 == 0 else COL_STRIPE
        draw.rectangle([INNER_X, y, INNER_X + INNER_W, y + ROW_H - 2], fill=bg)
        # 行の下に薄い罫線
        draw.line([(INNER_X + 8, y + ROW_H - 2), (INNER_X + INNER_W - 8, y + ROW_H - 2)],
                  fill=COL_BROWN, width=1)

        cx = INNER_X

        # 順位
        w = COLS[0][2]
        draw_rank_badge(draw, cx, y + 2, w, ROW_H - 4, rk)
        cx += w

        # 台番号
        w = COLS[1][2]
        s = str(item['dai'])
        sw = draw.textlength(s, font=f_dai)
        nx = cx + w / 2 - sw / 2 - 12
        draw.text((nx, y + ROW_H / 2), s, font=f_dai,
                  fill=COL_BROWN_DARK, anchor='lm')
        draw.text((nx + sw + 4, y + ROW_H / 2 + 7), '番台',
                  font=f_dai_lb, fill=COL_BROWN, anchor='lm')
        cx += w

        # 区切り星
        draw_star(draw, cx, y + ROW_H / 2, 5, COL_GOLD)

        # 機種名
        w = COLS[2][2]
        nm = item['name']
        avail = w - 36
        one_line = None
        for fnt in f_nm_l:
            if draw.textlength(nm, font=fnt) <= avail:
                one_line = fnt
                break
        if one_line is not None:
            draw.text((cx + 18, y + ROW_H / 2), nm, font=one_line,
                      fill=COL_NAVY_DEEP, anchor='lm')
        else:
            L, R = split_two(nm, f_nm_l[-1], avail)
            draw.text((cx + 18, y + ROW_H / 2 - 12), L, font=f_nm_l[-1],
                      fill=COL_NAVY_DEEP, anchor='lm')
            draw.text((cx + 18, y + ROW_H / 2 + 12), R, font=f_nm_l[-1],
                      fill=COL_NAVY_DEEP, anchor='lm')
        cx += w

        # 区切り星
        draw_star(draw, cx, y + ROW_H / 2, 5, COL_GOLD)

        # 差枚
        w = COLS[3][2]
        sa = item['samai']
        sa_text = f'{sa:+,}'
        sa_color = COL_RED_DEEP if sa >= 0 else COL_NAVY
        sw = draw.textlength(sa_text, font=f_val)
        mai_x = cx + w - 22
        draw.text((mai_x, y + ROW_H / 2 + 7), lbl_unit, font=f_unit,
                  fill=COL_BROWN, anchor='rm')
        draw.text((mai_x - 22, y + ROW_H / 2), sa_text, font=f_val,
                  fill=sa_color, anchor='rm')
        cx += w

        if has_bb_rb:
            # 区切り星
            draw_star(draw, cx, y + ROW_H / 2, 5, COL_GOLD)
            # BB
            w = COLS[4][2]
            bb_s = str(item['bb'])
            bbw = draw.textlength(bb_s, font=f_count)
            bb_cx = cx + w / 2 - 6
            draw.text((bb_cx, y + ROW_H / 2), bb_s, font=f_count,
                      fill=COL_NAVY, anchor='mm')
            draw.text((bb_cx + bbw / 2 + 4, y + ROW_H / 2 + 6), '回',
                      font=f_count_u, fill=COL_BROWN, anchor='lm')
            cx += w
            draw_star(draw, cx, y + ROW_H / 2, 5, COL_GOLD)
            # RB
            w = COLS[5][2]
            rb_s = str(item['rb'])
            rbw = draw.textlength(rb_s, font=f_count)
            rb_cx = cx + w / 2 - 6
            draw.text((rb_cx, y + ROW_H / 2), rb_s, font=f_count,
                      fill=COL_RED_DEEP, anchor='mm')
            draw.text((rb_cx + rbw / 2 + 4, y + ROW_H / 2 + 6), '回',
                      font=f_count_u, fill=COL_BROWN, anchor='lm')
            cx += w

        y += ROW_H

    # ===== フッター: 赤バナー =====
    fy = y + 8
    draw.rectangle([0, fy, W, fy + FOOTER_H], fill=COL_RED)
    draw.rectangle([0, fy, W, fy + 4], fill=COL_GOLD)
    draw.rectangle([0, fy + FOOTER_H - 4, W, fy + FOOTER_H], fill=COL_GOLD)
    # 飾り：両端と内側に星を散らす
    for sx in (40, 90, 140, 190, W - 40, W - 90, W - 140, W - 190):
        draw_star(draw, sx, fy + FOOTER_H / 2, 8, COL_GOLD_LIGHT)
    # 店舗名
    draw.text((W / 2, fy + 32), store, font=font(FONT_HEAVY, 30),
              fill=COL_WHITE, anchor='mm',
              stroke_width=2, stroke_fill=COL_RED_DEEP)
    # サブテキスト
    draw.text((W / 2, fy + 64),
              f'☆  {play_label}  /  {footer_date}  /  {lbl_diff}ランキング TOP{N}  ☆',
              font=font(FONT_BOLD, 14), fill=COL_PAPER, anchor='mm')

    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    img.save(out_path, 'PNG', optimize=True)


# ===== CLI =====
def process(path):
    date_full, store = parse_filename(path)
    if store.endswith('店'):
        store = store[:-1]
    out_dir = os.path.expanduser(f'~/Desktop/ランキング/英語取材/{store}')
    out = os.path.join(out_dir, f'{date_full[4:]}_{store}.png')
    ranking = load_ranking(path)
    render_image(ranking, date_full, store, out)
    print(f'OK -> {out}')


def main(argv):
    import sys, glob
    targets = []
    for a in argv[1:]:
        if any(c in a for c in '*?['):
            targets.extend(glob.glob(a))
        else:
            targets.append(a)
    for t in targets:
        try:
            process(t)
        except Exception as e:
            print(f'NG -> {t}: {e}', file=__import__('sys').stderr)


if __name__ == '__main__':
    import sys
    main(sys.argv)
