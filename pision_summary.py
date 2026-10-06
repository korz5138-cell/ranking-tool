"""pision APIからレポート用サマリーを生成

条件に合ったホールを抽出し、データ集計・テンプレート選択を行う。
"""
from __future__ import annotations

import csv
import os
from datetime import date
from pathlib import Path
from typing import NamedTuple

import pision_api as papi


# 都道府県コード → 名前
PREFECTURES = {
    1: '北海道', 2: '青森県', 3: '岩手県', 4: '宮城県', 5: '秋田県',
    6: '山形県', 7: '福島県', 8: '茨城県', 9: '栃木県', 10: '群馬県',
    11: '埼玉県', 12: '千葉県', 13: '東京都', 14: '神奈川県', 15: '新潟県',
    16: '富山県', 17: '石川県', 18: '福井県', 19: '山梨県', 20: '長野県',
    21: '岐阜県', 22: '静岡県', 23: '愛知県', 24: '三重県', 25: '滋賀県',
    26: '京都府', 27: '大阪府', 28: '兵庫県', 29: '奈良県', 30: '和歌山県',
    31: '鳥取県', 32: '島根県', 33: '岡山県', 34: '広島県', 35: '山口県',
    36: '徳島県', 37: '香川県', 38: '愛媛県', 39: '高知県', 40: '福岡県',
    41: '佐賀県', 42: '長崎県', 43: '熊本県', 44: '大分県', 45: '宮崎県',
    46: '鹿児島県', 47: '沖縄県',
}

# テンプレート分類
REGION_HOKURIKU = 'hokuriku'  # 富山、新潟、長野、山梨
REGION_KYOTO = 'kyoto'        # 京都
REGION_HOKURIKU_STRICT = 'hokuriku_strict'  # 福井、石川


def _load_model_mapping() -> dict[str, str]:
    """モデル変換ルールCSVからマッピングを読み込む

    Returns:
        フルネーム → 短縮名のマッピング辞書
    """
    mapping = {}
    # プロジェクト内の data フォルダから読み込む
    csv_path = Path(__file__).parent / 'data' / 'models (6).csv'
    if not csv_path.exists():
        # フォールバック: Downloads から読み込む
        csv_path = Path.home() / 'Downloads' / 'models (6).csv'

    if not csv_path.exists():
        return mapping

    try:
        with open(csv_path, encoding='shift_jis') as f:
            reader = csv.reader(f)
            next(reader)  # ヘッダーをスキップ
            for row in reader:
                if len(row) >= 6:
                    full_name = row[2].strip()  # 列2: 機種名（フル名）
                    short_name = row[5].strip()  # 列5: 短縮名
                    if full_name and short_name:
                        mapping[full_name] = short_name
    except Exception as e:
        print(f'[WARNING] モデルマッピングの読み込みに失敗: {e}')

    return mapping


_MODEL_MAPPING = _load_model_mapping()


def _load_city_mapping() -> dict[str, str]:
    """ホール名から市町村を取得するマッピングを読み込む

    Returns:
        ホール名 → 市町村のマッピング辞書
    """
    mapping = {}

    try:
        import openpyxl
    except ImportError:
        print('[WARNING] openpyxl がインストールされていません')
        return mapping

    # ファイル1: 新潟山梨長野京都
    data_dir = Path(__file__).parent / 'data'
    file1 = data_dir / '店舗マスター_下書き_新潟山梨長野京都.xlsx'
    if not file1.exists():
        # フォールバック: Downloads から読み込む
        file1 = Path.home() / 'Downloads' / '店舗マスター_下書き_新潟山梨長野京都.xlsx'

    if file1.exists():
        try:
            wb = openpyxl.load_workbook(file1, data_only=True)
            ws = wb['店舗マスター']
            for row in ws.iter_rows(min_row=5, values_only=True):
                if len(row) >= 7 and row[3] and row[2]:  # 店名と市区町村
                    store_name = str(row[3]).strip()
                    city = str(row[2]).strip()
                    mapping[store_name] = city
                    # 別名がある場合も追加
                    if row[6]:
                        aliases = str(row[6]).split('／')
                        for alias in aliases:
                            alias = alias.strip()
                            if alias:
                                mapping[alias] = city
        except Exception as e:
            print(f'[WARNING] ファイル1の読み込みに失敗: {e}')

    # ファイル2: 北陸3県
    file2 = data_dir / '北陸3県_パチンコ店リスト_みんパチ.xlsx'
    if not file2.exists():
        # フォールバック: Downloads から読み込む
        file2 = Path.home() / 'Downloads' / '北陸3県_パチンコ店リスト_みんパチ.xlsx'

    if file2.exists():
        try:
            wb = openpyxl.load_workbook(file2, data_only=True)
            ws = wb['一覧']
            for row in ws.iter_rows(min_row=5, values_only=True):
                if len(row) >= 4 and row[3] and row[2]:  # 店舗名と市町村
                    store_name = str(row[3]).strip()
                    city = str(row[2]).strip()
                    mapping[store_name] = city
        except Exception as e:
            print(f'[WARNING] ファイル2の読み込みに失敗: {e}')

    return mapping


_CITY_MAPPING = _load_city_mapping()


class ReportCondition(NamedTuple):
    """レポート送信条件"""
    prefectures: list[int]
    min_games: int
    min_diff: int
    region: str


# 送信条件定義
CONDITIONS = [
    ReportCondition(
        prefectures=[16, 15, 20, 19, 26],  # 富山、新潟、長野、山梨、京都
        min_games=3000,
        min_diff=150,
        region=REGION_HOKURIKU,
    ),
    ReportCondition(
        prefectures=[18, 17],  # 福井、石川
        min_games=2500,
        min_diff=75,
        region=REGION_HOKURIKU_STRICT,
    ),
]


class UnitData(NamedTuple):
    """台別データ"""
    unit_id: int
    model_name: str
    short_name: str
    diff: int
    games: int
    bb: int
    rb: int
    art: int


class KishuSummary(NamedTuple):
    """機種別サマリー"""
    name: str
    short_name: str
    avg_diff: float
    avg_games: int
    win_count: int
    total_units: int


class HallSummary(NamedTuple):
    """ホール別サマリー"""
    hall_id: int
    hall_name: str
    prefecture_id: int
    city: str
    target_date: str
    total_diff: int
    avg_diff: float
    total_units: int
    win_units: int

    # 詳細データ
    kishu_summaries: list[KishuSummary]
    unit_details: list[UnitData]


def _round_diff(val: float) -> int:
    """差枚を10枚単位で四捨五入"""
    import math
    return int(math.floor(val / 10 + 0.5)) * 10


def _get_model_name(model: papi.ModelInfo | None) -> str:
    """モデル情報から機種名を取得"""
    if not model:
        return "不明"
    return model.get('name', '不明')


def _aggregate_hall_data(result: papi.HallResult) -> HallSummary:
    """ホール別結果データを集計"""
    hall = result['hall']
    details = result['details']
    target_date = result['targetDate']

    # 台別データの集計
    units = []
    for d in details:
        model_name = _get_model_name(d.get('model'))
        short_name = _MODEL_MAPPING.get(model_name, model_name)
        units.append(UnitData(
            unit_id=d['unitId'],
            model_name=model_name,
            short_name=short_name,
            diff=d['diff'],
            games=d['games'],
            bb=d['bb'],
            rb=d['rb'],
            art=d['art'],
        ))

    # 機種別集計
    kishu_map: dict[str, list[UnitData]] = {}
    for unit in units:
        if unit.model_name not in kishu_map:
            kishu_map[unit.model_name] = []
        kishu_map[unit.model_name].append(unit)

    kishu_list: list[KishuSummary] = []
    for name, unit_list in kishu_map.items():
        total_diff = sum(u.diff for u in unit_list)
        total_games = sum(u.games for u in unit_list)
        avg_diff = total_diff / len(unit_list)
        avg_games = total_games // len(unit_list) if len(unit_list) > 0 else 0
        win_count = sum(1 for u in unit_list if u.diff > 0)

        # 短縮名を取得（CSVマッピングから優先、なければモデル情報から、それでもなければ機種名をそのまま使用）
        short_name = _MODEL_MAPPING.get(name)
        if not short_name:
            model = unit_list[0].get('model') if hasattr(unit_list[0], 'get') else None
            if model and model.get('shortName'):
                short_name = model['shortName']
            else:
                short_name = name

        kishu_list.append(KishuSummary(
            name=name,
            short_name=short_name,
            avg_diff=avg_diff,
            avg_games=avg_games,
            win_count=win_count,
            total_units=len(unit_list),
        ))

    # ソート（平均差枚で降順）＆フィルタ（2台以上設置）
    kishu_list.sort(key=lambda k: k.avg_diff, reverse=True)
    kishu_list = [k for k in kishu_list if k.total_units >= 2]

    # 全体集計
    total_diff = sum(u.diff for u in units)
    avg_diff = total_diff / len(units) if units else 0
    win_units = sum(1 for u in units if u.diff > 0)

    # 台別をソート（差枚で降順）
    units_sorted = sorted(units, key=lambda u: u.diff, reverse=True)

    # 市町村を取得
    city = _CITY_MAPPING.get(hall['name'], '')

    return HallSummary(
        hall_id=hall['id'],
        hall_name=hall['name'],
        prefecture_id=hall['prefectureId'],
        city=city,
        target_date=target_date,
        total_diff=total_diff,
        avg_diff=avg_diff,
        total_units=len(units),
        win_units=win_units,
        kishu_summaries=kishu_list,
        unit_details=units_sorted,
    )


def check_condition(summary: HallSummary) -> tuple[bool, ReportCondition | None]:
    """ホールが報告条件に該当するかチェック

    Returns:
        (条件に該当するか, 該当する条件) のタプル
    """
    avg_games = sum(u.games for u in summary.unit_details) // len(summary.unit_details) if summary.unit_details else 0
    avg_diff = summary.avg_diff
    pref_id = summary.prefecture_id

    for cond in CONDITIONS:
        if pref_id not in cond.prefectures:
            continue
        if avg_games >= cond.min_games and avg_diff >= cond.min_diff:
            return True, cond

    return False, None


def fetch_and_summarize_hall(hall_id: int, target_date: date | str) -> HallSummary | None:
    """ホールのデータを取得して集計

    Args:
        hall_id: ホールID
        target_date: 対象日

    Returns:
        HallSummary、またはデータが存在しない場合は None
    """
    try:
        result = papi.get_hall_results(hall_id, target_date)
        return _aggregate_hall_data(result)
    except Exception:
        return None


def find_reportable_halls(target_date: date | str) -> list[tuple[HallSummary, ReportCondition]]:
    """条件を満たすホールを検索

    Args:
        target_date: 対象日

    Returns:
        (HallSummary, 該当条件) のリスト
    """
    print(f'[DEBUG] ホール一覧を取得中...')
    halls = papi.get_halls()
    print(f'[DEBUG] {len(halls)} 件のホールを取得しました')
    reportable = []

    for i, hall in enumerate(halls):
        print(f'[DEBUG] [{i+1}/{len(halls)}] {hall["name"]} (ID: {hall["id"]}) をチェック中...')
        summary = fetch_and_summarize_hall(hall['id'], target_date)
        if not summary:
            print(f'[DEBUG]   → データなし')
            continue

        matches, cond = check_condition(summary)
        print(f'[DEBUG]   → 平均G数: {sum(u.games for u in summary.unit_details) // len(summary.unit_details) if summary.unit_details else 0}, 平均差枚: {summary.avg_diff:.0f}, 条件該当: {matches}')
        if matches and cond:
            reportable.append((summary, cond))

    return reportable
