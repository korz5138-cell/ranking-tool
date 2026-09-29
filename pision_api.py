"""pision.io API クライアント

APIキーは環境変数 PISION_API_KEY から取得します。
"""
from __future__ import annotations

import os
from datetime import date
from typing import TypedDict

import requests


class ModelInfo(TypedDict):
    """機種情報"""
    id: int
    name: str
    shortName: str | None
    licenceName: str | None
    licenceNo: str | None
    updatedAt: str


class HallInfo(TypedDict):
    """ホール情報"""
    id: int
    name: str
    prefectureId: int
    secret: bool
    remarks: str | None
    updatedAt: str


class UnitResult(TypedDict):
    """台別結果"""
    unitId: int
    displayName: str
    model: ModelInfo | None
    diff: int
    games: int
    bb: int
    rb: int
    art: int
    points: list[dict[str, int]]


class HallResult(TypedDict):
    """ホール別結果"""
    targetDate: str
    createdAt: str
    hall: HallInfo
    details: list[UnitResult]


API_BASE_URL = 'https://www.pision.io'


def _get_api_key() -> str:
    """環境変数からAPIキーを取得"""
    key = os.environ.get('PISION_API_KEY')
    if not key:
        raise ValueError('PISION_API_KEY 環境変数が設定されていません')
    return key


def _request(endpoint: str, **kwargs) -> dict:
    """APIにリクエストを送信"""
    headers = kwargs.pop('headers', {})
    headers['X-Api-Key'] = _get_api_key()

    url = f'{API_BASE_URL}{endpoint}'
    resp = requests.get(url, headers=headers, **kwargs)
    resp.raise_for_status()
    return resp.json()


def get_models() -> list[ModelInfo]:
    """機種一覧を取得"""
    result = _request('/api/v2/models')
    return result.get('models', [])


def get_halls() -> list[HallInfo]:
    """ホール一覧を取得"""
    result = _request('/api/v2/halls')
    return result.get('halls', [])


def get_hall_results(hall_id: int, target_date: date | str) -> HallResult:
    """ホール別結果データを取得

    Args:
        hall_id: ホールID
        target_date: 対象日 (yyyy-MM-dd 形式またはdateオブジェクト)

    Returns:
        ホール別結果データ

    Raises:
        requests.HTTPError: 404 の場合、データが存在しません
    """
    if isinstance(target_date, date):
        target_date = target_date.isoformat()

    endpoint = f'/api/v2/halls/{hall_id}/results/{target_date}'
    return _request(endpoint)


def get_result_by_id(result_id: int) -> HallResult:
    """結果ID指定でデータを取得

    Args:
        result_id: 結果ID

    Returns:
        ホール別結果データ

    Raises:
        requests.HTTPError: 404 の場合、データが存在しません
    """
    return _request(f'/api/v2/results/{result_id}')
