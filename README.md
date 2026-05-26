# 差枚ランキング画像ジェネレーター

Excel/CSV をアップロードしてパチスロ差枚ランキング画像（PNG）を生成する Streamlit アプリ。

## 機能

- **2デザイン切替**: 神の子（パステル系 TOP10）/ win6game（黒背景）
- **複数ファイル一括処理** + **ZIPダウンロード**
- **多様なファイル名形式に対応**:
  - `YYYYMMDD_店舗名_20S.xlsx`（標準）
  - `【店舗】【M.D】【取材名】.xlsx`（神の子取材系）
  - `【店舗】M.D...xlsx` / `店舗名YYYY.M.D...xlsx`
  - `店舗名(20S)_YYYY-MM-DD_全台.csv` 等
- **ピーアーク系列店舗の自動補完**（地域名のみのファイル → 正式店舗名）
- **機種名の自動解決**（型式名 → `models.csv` から短縮名/正式名）
- セッション内履歴

## ローカル起動

```bash
pip install -r requirements.txt
streamlit run web_app.py
```

ブラウザで http://localhost:8501 にアクセス。

## ファイル構成

| ファイル | 役割 |
|---|---|
| `web_app.py` | Streamlit UI |
| `make_ranking_kamiko.py` | 神の子デザイン + 全フォーマット対応のローダー |
| `make_ranking.py` | win6gameデザイン |
| `models.csv` | 型式名→短縮名のマッピング |
| `requirements.txt` | Python依存 |
| `packages.txt` | Linux系パッケージ（Streamlit Cloud用：Noto Sans CJK） |
