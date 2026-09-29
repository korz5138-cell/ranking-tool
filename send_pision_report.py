"""pision レポートを条件に基づいて生成・Discord送信

使用例:
    python send_pision_report.py --date 2026-09-29 --dry-run
"""
from __future__ import annotations

import argparse
import os
import tempfile
from datetime import date, datetime, timedelta

import pision_summary as ps
import discord_reporter as dr
import pision_renderer as pr


def main():
    parser = argparse.ArgumentParser(description='pision レポート生成・送信')
    parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='対象日 (YYYY-MM-DD形式。省略時は昨日)',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='実際には送信せず、結果を表示のみ',
    )
    args = parser.parse_args()

    # 対象日の決定
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            print(f'エラー: 日付の形式が不正です: {args.date}')
            return 1
    else:
        target_date = datetime.now().date() - timedelta(days=1)

    print(f'対象日: {target_date}')

    # APIキー確認
    if not os.environ.get('PISION_API_KEY'):
        print('エラー: PISION_API_KEY 環境変数が設定されていません')
        return 1

    # 条件を満たすホールを検索
    print('ホールを検索中...')
    try:
        reportable = ps.find_reportable_halls(target_date)
    except Exception as e:
        print(f'エラー: ホール検索に失敗しました: {e}')
        import traceback
        traceback.print_exc()
        return 1

    if not reportable:
        print('条件を満たすホールが見つかりませんでした')
        return 0

    print(f'条件を満たすホール: {len(reportable)}件')

    # 各ホールについてレポートを生成・送信
    for summary, condition in reportable:
        print(f'\n{summary.hall_name} (都道府県ID: {summary.prefecture_id})')
        print(f'  総差枚: {summary.total_diff}, 平均差枚: {summary.avg_diff:.0f}')

        # テンプレート選択
        if condition.region == ps.REGION_HOKURIKU or condition.region == ps.REGION_HOKURIKU_STRICT:
            template_name = 'hokuriku'
            text_fn = pr.generate_discord_text_hokuriku
        elif condition.region == ps.REGION_KYOTO:
            template_name = 'kyoto'
            text_fn = pr.generate_discord_text_kyoto
        else:
            print(f'  警告: 未知の地域タイプ: {condition.region}')
            continue

        # 画像パス（テンポラリ）
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            output_path = f.name

        try:
            # 画像生成
            print(f'  画像生成中 ({template_name})...')
            if template_name == 'hokuriku':
                pr.render_hokuriku(summary, output_path)
            # elif template_name == 'kyoto':
            #     pr.render_kyoto(summary, output_path)

            # テキスト生成
            if template_name in ['hokuriku', 'kyoto']:
                text = text_fn(summary, topic="通常営業")
            else:
                text = text_fn(summary)

            print(f'  テキスト: {len(text)} 文字')

            if args.dry_run:
                print(f'  [DRY-RUN] Discord送信をスキップします')
                print(f'  テキスト内容:\n{text}')
            else:
                # Discord送信
                print(f'  Discord送信中...')
                if dr.send_message(text, output_path):
                    print(f'  ✓ 送信完了')
                else:
                    print(f'  ✗ 送信失敗')

        finally:
            # クリーンアップ
            if os.path.exists(output_path):
                os.unlink(output_path)

    return 0


if __name__ == '__main__':
    exit(main())
