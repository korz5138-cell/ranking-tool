"""操作マニュアルを1ページのPDFに書き出す。
出力: ~/Desktop/差枚ランキング_操作マニュアル.pdf
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# 組み込み日本語 CID フォント（OS非依存・絵文字は非対応のためテキストで表現）
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))   # ゴシック（見出し用）
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))      # 明朝（本文用）

JPB = 'HeiseiKakuGo-W5'   # 太め
JP = 'HeiseiMin-W3'       # 本文

# カラーパレット
COL_PINK = HexColor('#FF5C8D')
COL_NAVY = HexColor('#1E3258')
COL_GRAY = HexColor('#5A6478')
COL_LIGHT_PINK = HexColor('#FFE3EC')
COL_LIGHT_BLUE = HexColor('#EAF2FF')
COL_ACCENT = HexColor('#2A6FE0')
COL_BORDER = HexColor('#CDD3E0')
COL_WARN_BG = HexColor('#FFF4D8')
COL_WARN_FG = HexColor('#8A5400')

W, H = A4
M = 14 * mm  # 余白


def draw():
    out = os.path.expanduser('~/Desktop/差枚ランキング_操作マニュアル.pdf')
    c = canvas.Canvas(out, pagesize=A4)

    # ===== ヘッダー帯 =====
    c.setFillColor(COL_LIGHT_PINK)
    c.rect(0, H - 30 * mm, W, 30 * mm, stroke=0, fill=1)
    # 左：タイトル
    c.setFillColor(COL_PINK)
    c.setFont(JPB, 21)
    c.drawString(M, H - 14 * mm, '差枚ランキング画像ジェネレーター')
    c.setFillColor(COL_NAVY)
    c.setFont(JPB, 11)
    c.drawString(M, H - 21 * mm, '操作マニュアル　［1分でわかる使い方］')
    # 下段：URL 行
    c.setFillColor(COL_ACCENT)
    c.setFont(JPB, 10.5)
    c.drawString(M, H - 27.5 * mm, 'URL:  https://ranking-tool-slot.streamlit.app/')
    c.setFillColor(COL_GRAY)
    c.setFont(JP, 8.5)
    c.drawRightString(W - M, H - 27.5 * mm, 'ログイン不要 ／ スマホ・PC両対応')

    y = H - 38 * mm

    # ----- 共通描画ヘルパー -----
    def section(title, ypos):
        c.setFillColor(COL_LIGHT_BLUE)
        c.rect(M, ypos - 1.5 * mm, W - 2 * M, 6.5 * mm, stroke=0, fill=1)
        c.setFillColor(COL_NAVY)
        c.setFont(JPB, 11)
        c.drawString(M + 3 * mm, ypos + 1.5 * mm, title)
        return ypos - 5 * mm

    # ===== 基本の使い方（3ステップ） =====
    y = section('■ 基本の使い方（3ステップ）', y)
    y -= 2 * mm
    step_y = y
    step_w = (W - 2 * M - 6 * mm) / 3
    steps = [
        ('STEP 1', 'デザインを選ぶ',
         '左サイドバーから\n「神の子」or「win6game」'),
        ('STEP 2', 'ファイルをアップロード',
         'Excel/CSVを\nドラッグ&ドロップ\n（複数同時OK）'),
        ('STEP 3', 'ダウンロード',
         '自動生成された画像を\nダウンロードボタンで保存'),
    ]
    for i, (num, title, desc) in enumerate(steps):
        x = M + i * (step_w + 3 * mm)
        # カード背景
        c.setFillColor(HexColor('#FFFFFF'))
        c.setStrokeColor(COL_BORDER)
        c.roundRect(x, step_y - 24 * mm, step_w, 23 * mm, 3, stroke=1, fill=1)
        # ステップタグ（ピンク帯）
        c.setFillColor(COL_PINK)
        c.roundRect(x + 2 * mm, step_y - 6.5 * mm, 14 * mm, 5 * mm, 1.5, stroke=0, fill=1)
        c.setFillColor(HexColor('#FFFFFF'))
        c.setFont(JPB, 8)
        c.drawCentredString(x + 9 * mm, step_y - 5.3 * mm, num)
        # タイトル
        c.setFillColor(COL_NAVY)
        c.setFont(JPB, 10.5)
        c.drawString(x + 18 * mm, step_y - 5.5 * mm, title)
        # 説明
        c.setFillColor(COL_GRAY)
        c.setFont(JP, 8.5)
        dy = step_y - 12 * mm
        for line in desc.split('\n'):
            c.drawString(x + 3 * mm, dy, line)
            dy -= 3.6 * mm
    y = step_y - 28 * mm

    # ===== 便利機能 =====
    y = section('■ 便利機能', y)
    y -= 1 * mm
    feats = [
        ('・デザイン切替',          'サイドバーで切替→アップロード済みも即反映（再UP不要）'),
        ('・店舗名/日付を変更',     '画像下のフォームから入力 →「反映」ボタンで上書き'),
        ('・ZIP一括ダウンロード',    '複数ファイル処理後、画面下に一括DLボタンが表示'),
        ('・セッション履歴',        'サイドバーに当日生成画像の履歴。履歴の一括ZIP DLも可'),
    ]
    c.setFillColor(COL_NAVY)
    for label, desc in feats:
        c.setFont(JPB, 9.5)
        c.drawString(M + 4 * mm, y, label)
        c.setFont(JP, 9)
        c.setFillColor(COL_GRAY)
        c.drawString(M + 52 * mm, y, desc)
        c.setFillColor(COL_NAVY)
        y -= 4.6 * mm
    y -= 1 * mm

    # ===== 対応ファイル名形式 =====
    y = section('■ 対応ファイル名形式（自動判別）', y)
    y -= 1 * mm
    files = [
        ('標準xlsx',          '20250609_マルハン八千代東_20S.xlsx'),
        ('ピーアーク地域名',  '【北千住】0520神の子来店ホール調査S.xlsx'),
        ('神の子取材',        '【スタジオ】【4.24】【神の子来店】S結果.xlsx'),
        ('取材タグ付き',      '【サボテン推し】ウエスタン一之江2026.5.19結果.xlsx'),
        ('先頭日付型',        '2026.5.10 神の子来店 南行徳NEO.xlsx'),
        ('CSV',              'マルハン千葉北店(20S)_2025-05-09_全台.csv'),
    ]
    c.setFillColor(COL_NAVY)
    for tag, ex in files:
        c.setFont(JPB, 8.8)
        c.drawString(M + 4 * mm, y, tag)
        c.setFont(JP, 8.5)
        c.setFillColor(COL_GRAY)
        c.drawString(M + 42 * mm, y, ex)
        c.setFillColor(COL_NAVY)
        y -= 3.8 * mm

    y -= 1.5 * mm
    # 警告ボックス
    c.setFillColor(COL_WARN_BG)
    c.rect(M, y - 10 * mm, W - 2 * M, 10 * mm, stroke=0, fill=1)
    c.setFillColor(COL_WARN_FG)
    c.setFont(JPB, 9)
    c.drawString(M + 3 * mm, y - 3.8 * mm,
                 '［！］ 店舗名・日付がファイル名に無い場合')
    c.setFont(JP, 8.5)
    c.setFillColor(COL_NAVY)
    c.drawString(M + 3 * mm, y - 7.5 * mm,
                 '　そのままアップロード → 画像下「店舗名・日付を変更」フォームから入力できます。')
    y -= 13 * mm

    # ===== ピーアーク自動補完 =====
    y = section('■ ピーアーク系列の自動補完（地域名 → 正式名）', y)
    y -= 1 * mm
    c.setFont(JP, 8.5)
    c.setFillColor(COL_GRAY)
    c.drawString(M + 4 * mm, y,
                 '例: 北千住 → ピーアーク北千住 ／ おゆみ野 → ピーアーク おゆみ野')
    y -= 4 * mm
    c.drawString(M + 4 * mm, y,
                 '登録店舗: 北千住 / 北千住SSS / 三田 / 北綾瀬駅前 / 竹ノ塚スタジオ / 千葉駅前 / おゆみ野 /')
    y -= 3.6 * mm
    c.drawString(M + 4 * mm, y,
                 '          南行徳NEO / 朝霞 / 春日部 / 新田 / 松原 / 越谷 / 谷塚 / 草加 / 相模大野 / 相模原 / 新城')
    y -= 5 * mm

    # ===== 困ったとき =====
    y = section('■ 困ったときは（よくある質問）', y)
    y -= 1 * mm
    qs = [
        ('「読み込み失敗」エラー', 'ファイル名を「【店舗名】MMDD_元名.xlsx」にリネームして再試行'),
        ('機種名が筐体名のまま',   '対応表（約1,380機種）に未登録の可能性。管理者まで連絡'),
        ('デザイン切替が遅い',     '初回のみ数秒、2回目以降は瞬時に切替'),
        ('ファイルはどこに保存？',  'サーバー上の一時領域のみ・DLしない限り残らない'),
    ]
    c.setFillColor(COL_NAVY)
    for q, a in qs:
        c.setFont(JPB, 9)
        c.drawString(M + 4 * mm, y, 'Q. ' + q)
        c.setFont(JP, 8.5)
        c.setFillColor(COL_GRAY)
        c.drawString(M + 60 * mm, y, '→ ' + a)
        c.setFillColor(COL_NAVY)
        y -= 4 * mm

    # ===== フッター =====
    c.setStrokeColor(COL_BORDER)
    c.line(M, 15 * mm, W - M, 15 * mm)
    c.setFillColor(COL_GRAY)
    c.setFont(JP, 7.5)
    c.drawString(M, 10 * mm,
                 '詳細マニュアル: github.com/korz5138-cell/ranking-tool/blob/main/MANUAL.md')
    c.drawRightString(W - M, 10 * mm, '差枚ランキング画像ジェネレーター ／ 操作マニュアル')

    c.showPage()
    c.save()
    print(f'OK -> {out}')


if __name__ == '__main__':
    draw()
