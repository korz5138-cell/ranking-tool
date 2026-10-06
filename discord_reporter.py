"""Discord Webhook 送信機能"""
from __future__ import annotations

import os
from pathlib import Path

import requests


def get_webhook_url() -> str:
    """環境変数からDiscord Webhook URLを取得"""
    url = os.environ.get('DISCORD_WEBHOOK_URL')
    if not url:
        raise ValueError('DISCORD_WEBHOOK_URL 環境変数が設定されていません')
    return url


def send_message(
    content: str,
    image_path: str | None = None,
    username: str = "パチスロレポート",
) -> tuple[bool, str]:
    """Discordにメッセージを送信

    Args:
        content: メッセージテキスト
        image_path: 添付する画像ファイルのパス
        username: Webhook表示名

    Returns:
        (送信成功時 True, エラーメッセージ)
    """
    try:
        webhook_url = get_webhook_url()
    except ValueError as e:
        return False, str(e)

    data = {
        'username': username,
        'content': content,
    }

    try:
        print(f'[DEBUG] Webhook URL: {webhook_url[:50]}...')
        print(f'[DEBUG] Content length: {len(content)}')
        print(f'[DEBUG] Image path: {image_path}')

        if image_path and Path(image_path).exists():
            with open(image_path, 'rb') as f:
                image_data = f.read()
            print(f'[DEBUG] Image size: {len(image_data)} bytes')
            response = requests.post(
                webhook_url,
                data=data,
                files={'file': (Path(image_path).name, image_data)},
                timeout=30,
            )
        else:
            print(f'[DEBUG] Sending text only')
            response = requests.post(webhook_url, json=data, timeout=30)

        print(f'[DEBUG] Response status: {response.status_code}')
        print(f'[DEBUG] Response text: {response.text}')

        response.raise_for_status()
        return True, "送信成功"
    except Exception as e:
        error_msg = f'Discord送信エラー: {str(e)}'
        print(error_msg)
        return False, error_msg
