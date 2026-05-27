"""差枚ランキング画像生成 Web UI（Streamlit）

ローカル起動:
    streamlit run web_app.py

複数ファイル同時アップロード対応。
デザイン: 神の子 / win6game の切替式。
店舗名・日付は自動検出されるが、後から手動編集して再生成可能。
"""
from __future__ import annotations

import io
import os
import sys
import tempfile
import traceback
import zipfile
from datetime import datetime, date

import streamlit as st

# 既存スクリプトをそのまま import して再利用
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import make_ranking_kamiko as kamiko  # noqa: E402
import make_ranking as win6           # noqa: E402


# ===== 画像生成 =====
def parse_and_load(uploaded_file):
    """アップロードファイルから ranking, store, date_full, parse_ok を取得。
    ファイル名パースに失敗しても例外にせず、デフォルト値で返す。
    """
    tmpdir = tempfile.mkdtemp(prefix='ranking_src_')
    src_path = os.path.join(tmpdir, uploaded_file.name)
    with open(src_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())

    parse_ok = True
    try:
        date_full, store = kamiko.parse_filename(src_path)
        if store.endswith('店'):
            store = store[:-1]
    except Exception:
        date_full = datetime.now().strftime('%Y%m%d')
        store = ''
        parse_ok = False

    ranking = kamiko.load_ranking(src_path)
    return ranking, store, date_full, parse_ok


def render_to_png(ranking, date_full: str, store: str, design: str) -> bytes:
    """ranking + 店舗 + 日付 + デザイン から PNG バイト列を生成。"""
    tmpdir = tempfile.mkdtemp(prefix='ranking_out_')
    out_path = os.path.join(tmpdir, f'{date_full[4:]}_{store}.png')
    render_fn = win6.render_image if design == 'win6game' else kamiko.render_image
    render_fn(ranking, date_full, store, out_path)
    with open(out_path, 'rb') as f:
        return f.read()


def make_zip_bytes(items: list[tuple[str, bytes]]) -> bytes:
    """[(filename, png_bytes), ...] を1つの ZIP バイト列にまとめる。
    同名ファイルがあれば自動的に '_2', '_3' を付与して衝突回避。
    """
    seen = {}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname, data in items:
            name = fname
            if name in seen:
                seen[name] += 1
                base, ext = os.path.splitext(fname)
                name = f'{base}_{seen[fname]}{ext}'
            else:
                seen[name] = 1
            zf.writestr(name, data)
    return buf.getvalue()


def _date_full_to_date(date_full: str) -> date:
    try:
        return datetime.strptime(date_full, '%Y%m%d').date()
    except Exception:
        return datetime.now().date()


# ===== UI =====
st.set_page_config(
    page_title='差枚ランキング画像ジェネレーター',
    page_icon='🎰',
    layout='wide',
)

# セッションステート初期化
if 'history' not in st.session_state:
    st.session_state.history = []          # list of dict(label, filename, png, ts)
if 'parsed' not in st.session_state:
    st.session_state.parsed = {}           # file_id -> dict(ranking, auto_store, auto_date, parse_ok)
if 'overrides' not in st.session_state:
    st.session_state.overrides = {}        # file_id -> dict(store, date_full)  ※デザインを跨いで保持
if 'pngs' not in st.session_state:
    st.session_state.pngs = {}             # (file_id, design, store, date_full) -> png bytes

st.title('🎰 差枚ランキング画像ジェネレーター')
st.caption('Excel / CSV をアップロードするとランキング画像（PNG）を生成します。店舗名・日付は後から手動編集可能。')
st.markdown(
    '📖 [操作マニュアルを開く](https://github.com/korz5138-cell/ranking-tool/blob/main/MANUAL.md)'
)

# サイドバー: デザイン選択 + 履歴
with st.sidebar:
    st.subheader('設定')
    design = st.radio(
        'デザイン',
        options=['神の子', 'win6game'],
        index=0,
        help='神の子＝パステル系 TOP10 / win6game＝黒背景 TOP15',
    )

    st.divider()
    st.subheader('履歴（このセッション）')
    if not st.session_state.history:
        st.caption('まだ生成履歴はありません')
    else:
        zip_all = make_zip_bytes([(h['filename'], h['png']) for h in st.session_state.history])
        st.download_button(
            f'📦 履歴 {len(st.session_state.history)} 件を ZIP で一括DL',
            data=zip_all,
            file_name=f'ranking_history_{datetime.now().strftime("%Y%m%d_%H%M")}.zip',
            mime='application/zip',
            key='hist_zip_dl',
            use_container_width=True,
        )
        if st.button('履歴をクリア', use_container_width=True):
            st.session_state.history = []
            st.rerun()
        for h in reversed(st.session_state.history[-20:]):
            with st.expander(f"{h['label']}", expanded=False):
                st.image(h['png'])
                st.download_button(
                    'ダウンロード',
                    data=h['png'],
                    file_name=h['filename'],
                    mime='image/png',
                    key=f"hist_{h['ts']}_{h['filename']}",
                    use_container_width=True,
                )

# メインエリア
uploaded = st.file_uploader(
    'ファイルを選択（複数可・.xlsx / .csv）',
    type=['xlsx', 'csv'],
    accept_multiple_files=True,
)


def _add_history(label, fname, png):
    """同じファイル名の履歴は最新で上書き、なければ新規追加。"""
    st.session_state.history = [h for h in st.session_state.history if h['filename'] != fname]
    st.session_state.history.append({
        'label': label,
        'filename': fname,
        'png': png,
        'ts': datetime.now().isoformat(timespec='seconds'),
    })


if uploaded:
    st.write(f'**{len(uploaded)} 件**のファイルを処理します。')
    success_items: list[tuple[str, bytes]] = []
    fail = 0

    for i, uf in enumerate(uploaded, start=1):
        with st.container(border=True):
            st.markdown(f'### {uf.name}')

            fid = uf.file_id

            # 1) パース＋データ読込（ファイル毎に1回・デザイン非依存）
            if fid not in st.session_state.parsed:
                try:
                    ranking, auto_store, auto_date, parse_ok = parse_and_load(uf)
                    if not ranking:
                        raise ValueError('ランキング対象データが0件です（フォーマットを確認してください）')
                    st.session_state.parsed[fid] = {
                        'ranking': ranking,
                        'auto_store': auto_store,
                        'auto_date': auto_date,
                        'parse_ok': parse_ok,
                    }
                except Exception as e:
                    st.error(f'読み込み失敗: {e}')
                    with st.expander('詳細トレースバック'):
                        st.code(traceback.format_exc())
                    fail += 1
                    continue

            info = st.session_state.parsed[fid]

            # 2) 表示用の店舗名・日付（手動上書きが優先）
            override = st.session_state.overrides.get(fid, {})
            store = override.get('store', info['auto_store'])
            date_full = override.get('date_full', info['auto_date'])
            parse_ok = info['parse_ok'] or bool(override)

            # 3) 画像生成（同じ条件はキャッシュ再利用）
            png = None
            if store:
                png_key = (fid, design, store, date_full)
                if png_key in st.session_state.pngs:
                    png = st.session_state.pngs[png_key]
                else:
                    try:
                        png = render_to_png(info['ranking'], date_full, store, design)
                        st.session_state.pngs[png_key] = png
                    except Exception as e:
                        st.error(f'画像生成失敗: {e}')
                        with st.expander('詳細トレースバック'):
                            st.code(traceback.format_exc())
                        fail += 1
                        continue

            # 4) プレビュー＋ダウンロード
            if png is not None and store:
                fname = f'{date_full[4:]}_{store}.png'
                label = f'{store}　{date_full[:4]}-{date_full[4:6]}-{date_full[6:8]}　({design})'

                col1, col2 = st.columns([3, 2])
                with col1:
                    st.image(png, caption=label)
                with col2:
                    if not parse_ok:
                        st.info('ℹ️ ファイル名から自動検出できませんでした。下記で店舗名・日付を入力してください。')
                    else:
                        st.success('生成成功')
                    st.download_button(
                        '📥 PNGをダウンロード',
                        data=png,
                        file_name=fname,
                        mime='image/png',
                        key=f'dl_{fid}_{design}',
                        use_container_width=True,
                    )
                    st.code(fname, language=None)

                _add_history(label, fname, png)
                success_items.append((fname, png))
            elif not store:
                st.warning('⚠️ 店舗名が未入力です。下記フォームで入力してください。')

            # 5) 編集フォーム（店舗名・日付の上書き入力）
            with st.expander(
                '✏️ 店舗名・日付を変更',
                expanded=(not parse_ok or not store),
            ):
                ec1, ec2, ec3 = st.columns([3, 2, 1])
                with ec1:
                    new_store = st.text_input(
                        '店舗名',
                        value=store,
                        key=f'store_input_{fid}',
                        placeholder='例: ピーアーク北千住',
                    )
                with ec2:
                    new_date = st.date_input(
                        '日付',
                        value=_date_full_to_date(date_full),
                        key=f'date_input_{fid}',
                        format='YYYY/MM/DD',
                    )
                with ec3:
                    st.write('')
                    st.write('')
                    regen = st.button(
                        '🔄 反映',
                        key=f'regen_{fid}',
                        use_container_width=True,
                        type='primary',
                    )

                if regen:
                    new_store_clean = new_store.strip()
                    if not new_store_clean:
                        st.error('店舗名を入力してください')
                    else:
                        new_date_full = new_date.strftime('%Y%m%d')
                        st.session_state.overrides[fid] = {
                            'store': new_store_clean,
                            'date_full': new_date_full,
                        }
                        st.rerun()

    st.divider()
    success = len(success_items)
    if fail == 0 and success == len(uploaded):
        st.success(f'すべて完了しました（成功 {success} 件）')
    elif fail == 0:
        st.info(f'生成済み {success} 件 / 入力待ち {len(uploaded) - success} 件')
    else:
        st.warning(f'完了: 成功 {success} 件 / 失敗 {fail} 件')

    # 今回処理分のZIP一括DL
    if success >= 2:
        zip_data = make_zip_bytes(success_items)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        st.download_button(
            f'📦 今回生成した {success} 件を ZIP で一括ダウンロード',
            data=zip_data,
            file_name=f'ranking_{ts}.zip',
            mime='application/zip',
            key=f'zip_dl_{ts}',
            type='primary',
            use_container_width=True,
        )

else:
    # アップロード前: 結果キャッシュをクリア（手動入力もリセット）
    st.session_state.parsed = {}
    st.session_state.overrides = {}
    st.session_state.pngs = {}
    st.info('左上のボックスからファイルをドラッグ＆ドロップしてください。')

    with st.expander('対応ファイル名フォーマット', expanded=False):
        st.markdown('''
**xlsx**
- `YYYYMMDD_店舗名_20S.xlsx`（標準）
- `【店舗】【M.D】【神の子来店】S結果.xlsx`（神の子取材系）
- `【店舗】MMDD神の子...xlsx` / `【店舗】M.D...xlsx`
- `店舗名YYYY.M.D...xlsx` / `2026.5.10 神の子来店 店舗名.xlsx`

**CSV**
- `店舗名(20S)_YYYY-MM-DD_全台.csv`
- `店舗名YYYY-MM-DD_全台.csv`
- 先頭日付プレフィックス（例: `2025.5:9...`, `2025-11-8...`）も自動認識

**📝 ファイル名に店舗/日付がないテンプレート**

そのままアップロードして、画面下の「✏️ 店舗名・日付を変更」フォームで指定できます。
リネームせずにアップロードすると、店舗名は空欄、日付は本日が初期値で開きます。

**ピーアーク系列の自動補完**

地域名だけでも正式店舗名に変換されます（例: `北千住` → `ピーアーク北千住`）。
未登録の店舗があれば管理者にご連絡ください。
''')
