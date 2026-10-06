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
) -> bool:
    """Discordにメッセージを送信

    Args:
        content: メッセージテキスト
        image_path: 添付する画像ファイルのパス
        username: Webhook表示名

    Returns:
        送信成功時 True
    """
    webhook_url = get_webhook_url()

    data = {
        'username': username,
        'content': content,
    }

    try:
        if image_path and Path(image_path).exists():
            with open(image_path, 'rb') as f:
                image_data = f.read()
            response = requests.post(
                webhook_url,
                data=data,
                files={'file': (Path(image_path).name, image_data)},
            )
        else:
            response = requests.post(webhook_url, json=data)

        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f'Discord送信エラー: {e}')
        return False
