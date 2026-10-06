"""特定ホールのデータをDiscordに送信"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timedelta

import pision_api as papi
import pision_summary as ps
import pision_renderer as pr
import discord_reporter as dr


def send_hall_report(hall_id: int, target_date: str | None = None):
    """指定ホールのレポートを送信

    Args:
        hall_id: ホールID
        target_date: 対象日（YYYY-MM-DD形式。省略時は昨日）
    """
    # APIキー確認
    if not os.environ.get('PISION_API_KEY'):
        print('エラー: PISION_API_KEY 環境変数が設定されていません')
        return False

    # 対象日の決定
    if target_date is None:
        target_date = (datetime.now() - timedelta(days=1)).date().isoformat()

    print(f'ホールID: {hall_id}, 対象日: {target_date}')

    # ホール情報取得
    halls = papi.get_halls()
    hall_info = next((h for h in halls if h['id'] == hall_id), None)
    if not hall_info:
        print('エラー: ホールが見つかりません')
        return False

    print(f'ホール名: {hall_info["name"]}')

    # データ取得・集計
    summary = ps.fetch_and_summarize_hall(hall_id, target_date)
    if not summary:
        print('エラー: データを取得できませんでした')
        return False

    print(f'総差枚: {summary.total_diff}, 平均差枚: {summary.avg_diff:.0f}')

    # テンプレート選択
    pref_id = hall_info['prefectureId']
    if pref_id in [16, 15, 20, 19]:  # 富山、新潟、長野、山梨
        template_name = 'hokuriku'
        text_fn = pr.generate_discord_text_hokuriku
    elif pref_id == 26:  # 京都
        template_name = 'kyoto'
        text_fn = pr.generate_discord_text_kyoto
    elif pref_id in [18, 17]:  # 福井、石川
        template_name = 'hokuriku'
        text_fn = pr.generate_discord_text_hokuriku
    else:
        print('警告: 未対応の都道府県です')
        return False

    # 画像生成
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        output_path = f.name

    try:
        print(f'画像生成中...')
        if template_name == 'hokuriku':
            pr.render_hokuriku(summary, output_path)

        # テキスト生成
        text = text_fn(summary)
        print(f'テキスト: {len(text)} 文字')

        # Discord送信
        print(f'Discord送信中...')
        success, message = dr.send_message(text, output_path)
        if success:
            print(f'✓ 送信完了')
            return True
        else:
            print(f'✗ 送信失敗: {message}')
            return False

    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


if __name__ == '__main__':
    # イーゾーン富山 (ID: 3625) を昨日のデータで送信
    send_hall_report(3625)
