"""pision レポート用テンプレートレンダラー

テンプレートファイルにデータを埋め込んで画像を生成、テキストを作成。
"""
from __future__ import annotations

import importlib.util
import os
import platform
import re
import sys
import tempfile
from pathlib import Path

from pision_summary import HallSummary, ReportCondition


TEMPLATE_DIR = Path(__file__).parent


def _get_font_paths() -> dict[str, str]:
    """環境に応じたフォントパスを取得"""
    system = platform.system()
    project_dir = Path(__file__).parent

    if system == 'Darwin':  # macOS - プロジェクト内のフォントを優先
        fonts_dir = project_dir / 'fonts'
        if fonts_dir.exists():
            return {
                'bold': str(fonts_dir / 'NotoSansJP-Bold.ttf'),
                'regular': str(fonts_dir / 'NotoSansJP-Regular.ttf'),
                'medium': str(fonts_dir / 'NotoSansJP-Bold.ttf'),
                'serif_bold': str(fonts_dir / 'NotoSansJP-Bold.ttf'),
                'serif_regular': str(fonts_dir / 'NotoSansJP-Regular.ttf'),
            }
        # フォールバック
        return {
            'bold': str(Path.home() / 'Library/Fonts/NotoSansCJK.ttc'),
            'regular': str(Path.home() / 'Library/Fonts/NotoSansCJK.ttc'),
            'medium': str(Path.home() / 'Library/Fonts/NotoSansCJK.ttc'),
            'serif_bold': str(Path.home() / 'Library/Fonts/NotoSerifCJK.ttc'),
            'serif_regular': str(Path.home() / 'Library/Fonts/NotoSerifCJK.ttc'),
        }
    else:  # Linux（Streamlit Cloud など）
        return {
            'bold': '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
            'regular': '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            'medium': '/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc',
            'serif_bold': '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',
            'serif_regular': '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',
        }

# テンプレートマッピング
TEMPLATES = {
    'hokuriku': TEMPLATE_DIR / 'templates' / 'template_hokuriku.py',
    'kyoto': TEMPLATE_DIR / 'templates' / 'template_kyoto.py',
    'kishu_pickup': TEMPLATE_DIR / 'templates' / 'template_kishu_pickup.py',
}


def _load_template_module(template_path: Path):
    """Pythonテンプレートファイルをモジュールとしてロード"""
    spec = importlib.util.spec_from_file_location('template', template_path)
    if not spec or not spec.loader:
        raise RuntimeError(f'テンプレートをロードできません: {template_path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _round_diff(val: float) -> int:
    """差枚を10枚単位で四捨五入"""
    import math
    return int(math.floor(val / 10 + 0.5)) * 10


def _shorten_model_name(name: str) -> str:
    """機種名を短縮（接頭辞削除）

    Args:
        name: 機種名

    Returns:
        短縮された機種名
    """
    # よくある接頭辞を削除
    if name.startswith('L'):
        name = name[1:]
    elif name.startswith('S'):
        name = name[1:]

    # それでも長ければ、最初の15文字
    if len(name) > 15:
        name = name[:15]

    return name


def render_hokuriku(summary: HallSummary, output_path: str, topic: str = "", lottery: int | None = None) -> None:
    """北陸テンプレートで画像を生成

    Args:
        summary: ホール集計データ
        output_path: 出力パス
        topic: トピック（省略時は空）
        lottery: 抽選人数（省略時は None）
    """
    # テンプレートコードを読み込む
    template_path = TEMPLATE_DIR / 'templates' / 'template_hokuriku.py'
    with open(template_path) as f:
        code = f.read()

    # フォントパスを置換（各行を個別に置換）
    fonts = _get_font_paths()
    code = code.replace('FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"', f'FB = "{fonts["bold"]}"')
    code = code.replace('FR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"', f'FR = "{fonts["regular"]}"')
    code = code.replace('FM = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"', f'FM = "{fonts["medium"]}"')

    # カラーを濃くする（文字色を強調）
    code = code.replace('TEXT = "#E8ECF5"', 'TEXT = "#FFFFFF"')  # 白に
    code = code.replace('SUB = "#8A94AB"', 'SUB = "#DDDDDD"')    # グレーをもっと濃く
    code = code.replace('PLUS = "#4FC3F7"', 'PLUS = "#4FC3F7"')  # 青は維持

    # 機種名短縮関数を追加
    shorten_func = '''
def _shorten_name(n):
    n = n.replace('L', '', 1) if n.startswith('L') else n
    n = n.replace('S', '', 1) if n.startswith('S') else n
    return n[:11] + '…' if len(n) > 11 else n
'''
    code = code.replace('import math', f'import math\n{shorten_func}')

    # 機種名を短縮するように修正
    code = code.replace('for i, (num, name, val) in enumerate(dai):',
                       'for i, (num, name, val) in enumerate(dai):\n    name = _shorten_name(name)')

    # データブロックを生成
    kishus = summary.kishu_summaries[:10]  # 上位10機種（既に2台以上フィルタ済み）
    kishu_data = '[\n'
    for k in kishus:
        kishu_data += f'    ("{k.short_name}", {int(k.avg_diff)}, {k.avg_games}, {k.win_count}, {k.total_units}),\n'
    kishu_data += ']'

    units = summary.unit_details[:20]  # 上位20台
    unit_data = '[\n'
    for u in units:
        unit_data += f'    ({u.unit_id}, "{u.short_name}", {u.diff}),\n'
    unit_data += ']'

    # 末尾別平均差枚を計算
    matsubi = [None] * 10
    for i in range(10):
        units_for_digit = [u for u in summary.unit_details if u.unit_id % 10 == i]
        if units_for_digit:
            avg = sum(u.diff for u in units_for_digit) / len(units_for_digit)
            matsubi[i] = _round_diff(avg)

    matsubi_str = '[' + ', '.join('None' if v is None else str(v) for v in matsubi) + ']'

    # ゾロ目の平均差枚
    zoro_units = [u for u in summary.unit_details if u.unit_id % 10 == u.unit_id // 10 % 10 and u.unit_id >= 10]
    zoro_avg = sum(u.diff for u in zoro_units) / len(zoro_units) if zoro_units else 0
    zoro_str = str(_round_diff(zoro_avg))

    # 日付をフォーマット
    from datetime import datetime
    date_obj = datetime.strptime(summary.target_date, '%Y-%m-%d')
    date_str = date_obj.strftime('%m月%d日(%a)')
    date_str = date_str.replace('Mon', '月').replace('Tue', '火').replace('Wed', '水').replace('Thu', '木').replace('Fri', '金').replace('Sat', '土').replace('Sun', '日')

    # データブロック内のプレースホルダーを先に置換
    code = code.replace('DATE = "9月19日(土)"', f'DATE = "{date_str}"')
    code = code.replace('TOPIC = "9の日＋北陸ダイナム合同賞品入荷"', f'TOPIC = "{topic if topic else "通常営業"}"')

    # 抽選人数を置換
    lottery_val = lottery if lottery else 'None'
    code = code.replace('LOTTERY = None', f'LOTTERY = {lottery_val}')

    # データブロックを生成・置換
    lottery_val = lottery if lottery else None
    data_block = f'''# ===================== データ =====================
STORE = "{summary.hall_name}"
DATE = "{date_str}"
TOPIC = "{topic if topic else "通常営業"}"
TOTAL_DIFF, AVG_DIFF, UNITS, WINS, LOTTERY = {summary.total_diff}, {int(summary.avg_diff)}, {summary.total_units}, {summary.win_units}, {lottery_val}

matsubi = {matsubi_str}
ZORO = {zoro_str}

# (機種名, 平均差枚, 平均G数, 勝ち台, 台数)
kishu = {kishu_data}

# (台番, 機種名, 差枚)
dai = {unit_data}
OUT = "{output_path}"
# ================================================='''

    # コードのデータブロックを置換
    code = re.sub(
        r'# ===================== データ =====================.*?# =================================================',
        data_block,
        code,
        flags=re.DOTALL,
    )

    # テンポラリファイルに書き込んで実行
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name

    try:
        # テンプレートモジュールを実行して画像を生成
        spec = importlib.util.spec_from_file_location('template_exec', temp_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                print(f'[DEBUG] 画像生成完了: {output_path}')
            except Exception as e:
                print(f'[ERROR] テンプレート実行エラー: {e}')
                import traceback
                traceback.print_exc()
                raise
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def render_kyoto(summary: HallSummary, output_path: str, topic: str = "", lottery: int | None = None) -> None:
    """京都テンプレートで画像を生成

    Args:
        summary: ホール集計データ
        output_path: 出力パス
        topic: トピック（省略時は空）
        lottery: 抽選人数（省略時は None）
    """
    # テンプレートコードを読み込む
    template_path = TEMPLATE_DIR / 'templates' / 'template_kyoto.py'
    with open(template_path) as f:
        code = f.read()

    # フォントパスを置換
    fonts = _get_font_paths()
    code = code.replace('FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"', f'FB = "{fonts["bold"]}"')
    code = code.replace('FR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"', f'FR = "{fonts["regular"]}"')
    code = code.replace('FM = "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"', f'FM = "{fonts["medium"]}"')
    code = code.replace('FMIN = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"', f'FMIN = "{fonts["serif_bold"]}"')
    code = code.replace('FMINR = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"', f'FMINR = "{fonts["serif_regular"]}"')

    # カラーを濃くする
    code = code.replace('TEXT = "#241C18"', 'TEXT = "#000000"')  # 黒に
    code = code.replace('SUB = "#9A8C7E"', 'SUB = "#333333"')    # グレーを濃く
    code = code.replace('GREY = "#6E6259"', 'GREY = "#222222"')  # グレーをもっと濃く

    # 日付をフォーマット
    from datetime import datetime
    date_obj = datetime.strptime(summary.target_date, '%Y-%m-%d')
    date_str = date_obj.strftime('%m.%d')
    date_str_big = date_obj.strftime('%m.%d')
    date_str_dow = date_obj.strftime('%a').replace('Mon', 'MON').replace('Tue', 'TUE').replace('Wed', 'WED').replace('Thu', 'THU').replace('Fri', 'FRI').replace('Sat', 'SAT').replace('Sun', 'SUN')
    date_str_dow_jp = date_obj.strftime('%A').replace('Monday', '月曜日').replace('Tuesday', '火曜日').replace('Wednesday', '水曜日').replace('Thursday', '木曜日').replace('Friday', '金曜日').replace('Saturday', '土曜日').replace('Sunday', '日曜日')

    # データを集計
    kishus = summary.kishu_summaries[:10]  # 既に2台以上フィルタ済み
    kishu_data = '[\n'
    for k in kishus:
        kishu_data += f'    ("{k.short_name}", {int(k.avg_diff)}, {k.avg_games}, {k.win_count}, {k.total_units}),\n'
    kishu_data += ']'

    # Aタイプ判定
    A_TYPE_KEYWORDS = ['ジャグラー', 'ハナビ', 'サンダー', 'ディスク', 'タコ', '不二子', 'クレア', 'ケロット', 'アレック', '南国育ち']

    def is_a_type(model_name: str) -> bool:
        return any(kw in model_name for kw in A_TYPE_KEYWORDS)

    # AT機とAタイプに分類
    units_at = [u for u in summary.unit_details if not is_a_type(u.model_name)][:10]
    units_a = [u for u in summary.unit_details if is_a_type(u.model_name)][:10]

    # テンプレート形式: (台番, 機種名, 差枚, BB, RB, ART/合算, G数)
    unit_data_at = '[\n'
    for u in units_at:
        unit_data_at += f'    ({u.unit_id}, "{u.short_name}", {u.diff}, {u.bb}, {u.rb}, {u.art}, {u.games}),\n'
    unit_data_at += ']'

    unit_data_a = '[\n'
    for u in units_a:
        # Aタイプの場合、ART の代わりに「合算」を表示（仕様書参照）
        gassaku = u.bb + u.rb  # 簡易的な合算
        unit_data_a += f'    ({u.unit_id}, "{u.short_name}", {u.diff}, {u.bb}, {u.rb}, {gassaku}, {u.games}),\n'
    unit_data_a += ']'

    # 末尾別平均差枚を計算
    matsubi = [None] * 10
    for i in range(10):
        units_for_digit = [u for u in summary.unit_details if u.unit_id % 10 == i]
        if units_for_digit:
            avg = sum(u.diff for u in units_for_digit) / len(units_for_digit)
            matsubi[i] = _round_diff(avg)

    matsubi_str = '[' + ', '.join('None' if v is None else str(v) for v in matsubi) + ']'

    # ゾロ目の平均差枚
    zoro_units = [u for u in summary.unit_details if u.unit_id % 10 == u.unit_id // 10 % 10 and u.unit_id >= 10]
    zoro_avg = sum(u.diff for u in zoro_units) / len(zoro_units) if zoro_units else 0
    zoro_str = str(_round_diff(zoro_avg))

    # データブロック生成
    lottery_val = lottery if lottery else None
    data_block = f'''# ===================== データ =====================
STORE = "{summary.hall_name}"
AREA = "AREA_PLACEHOLDER"
DATESTR = "{date_str}"
DATEBIG = "{date_str_big}"
DATEDOW = "{date_str_dow}  {date_str_dow_jp}"
TOPIC = "{topic if topic else "通常営業"}"
TOTAL_DIFF, AVG_DIFF, UNITS, WINS, LOTTERY = {summary.total_diff}, {int(summary.avg_diff)}, {summary.total_units}, {summary.win_units}, {lottery_val}

matsubi = {matsubi_str}
ZORO = {zoro_str}

# (機種名, 平均差枚, 平均G数, 勝ち台, 台数)
kishu = {kishu_data}

# (台番, 機種名, 差枚) - AT機TOP10
dai_at = {unit_data_at}

# (台番, 機種名, 差枚) - Aタイプ TOP10
dai_a = {unit_data_a}

OUT = "{output_path}"
# ================================================='''

    # コードのデータブロックを置換
    code = re.sub(
        r'# ===================== データ =====================.*?# =================================================',
        data_block,
        code,
        flags=re.DOTALL,
    )

    # テンポラリファイルに書き込んで実行
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name

    try:
        spec = importlib.util.spec_from_file_location('template_exec', temp_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                print(f'[DEBUG] 画像生成完了: {output_path}')
            except Exception as e:
                print(f'[ERROR] テンプレート実行エラー: {e}')
                import traceback
                traceback.print_exc()
                raise
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def generate_discord_text_hokuriku(summary: HallSummary, topic: str = "") -> str:
    """北陸版の投稿用テキストを生成"""
    from datetime import datetime
    from pision_summary import PREFECTURES

    # 日付をフォーマット
    date_obj = datetime.strptime(summary.target_date, '%Y-%m-%d')
    date_short = date_obj.strftime('%-m/%-d').lstrip('0').replace('/0', '/')  # 9/28 形式

    # 都道府県名と市町村を取得
    pref_name = PREFECTURES.get(summary.prefecture_id, "不明県")
    city = summary.city

    store_name = summary.hall_name
    total = summary.total_diff
    avg = int(summary.avg_diff)

    # マイナス差枚の場合は非表示
    total_text = f"+{total:,}枚" if total >= 0 else ""
    avg_text = f"平均+{avg:,}枚" if avg >= 0 else ""

    # トピック表示
    topic_line = f"➪{topic}" if topic else ""

    top3 = summary.kishu_summaries[:3]
    top3_text = "\n".join(f"・{k.short_name} +{int(k.avg_diff):,}枚" if k.avg_diff >= 0 else f"・{k.short_name}" for k in top3)

    # 市町村がある場合は「県 市」、ない場合は「県」のみ
    pref_city = f"{pref_name} {city}" if city else pref_name

    text = f"""{date_short}  万米データチェック🍚

【{pref_city}】
🌾{store_name}
{topic_line}

全体{total_text}  {avg_text}

■平均差枚上位
{top3_text}"""
    return text.strip()


def generate_discord_text_kyoto(summary: HallSummary, topic: str = "") -> str:
    """京都版の投稿用テキストを生成"""
    from datetime import datetime
    from pision_summary import PREFECTURES

    # 日付をフォーマット
    date_obj = datetime.strptime(summary.target_date, '%Y-%m-%d')
    date_short = date_obj.strftime('%-m/%-d').lstrip('0').replace('/0', '/')  # 9/28 形式

    # 都道府県名と市町村を取得
    pref_name = PREFECTURES.get(summary.prefecture_id, "不明県")
    city = summary.city

    store_name = summary.hall_name
    total = summary.total_diff
    avg = int(summary.avg_diff)

    # マイナス差枚の場合は非表示
    total_text = f"+{total:,}枚" if total >= 0 else ""
    avg_text = f"+{avg:,}枚" if avg >= 0 else ""

    # 市町村がある場合は「市 区」、ない場合は「県」のみ
    pref_city = f"{city}" if city else pref_name
    if not city:
        pref_city = pref_name

    # トピック表示
    topic_line = f"→{topic}" if topic else ""

    top3 = summary.kishu_summaries[:3]
    top3_text = "\n".join(f"・{k.short_name} +{int(k.avg_diff):,}枚" if k.avg_diff >= 0 else f"・{k.short_name}" for k in top3)

    text = f"""わやスロデータまとめ🦊

《{pref_city}》
{date_short} {store_name}
{topic_line}

全体{total_text}(平均{avg_text})

■平均差枚上位3機種
{top3_text}"""
    return text.strip()
