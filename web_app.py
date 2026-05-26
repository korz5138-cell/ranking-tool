"""差枚ランキング画像生成 Web UI（Streamlit）

ローカル起動:
    streamlit run web_app.py

複数ファイル同時アップロード対応。
デザイン: 神の子 / win6game の切替式。
"""
from __future__ import annotations

import io
import os
import sys
import tempfile
import traceback
import zipfile
from datetime import datetime

import streamlit as st

# 既存スクリプトをそのまま import して再利用
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import make_ranking_kamiko as kamiko  # noqa: E402
import make_ranking as win6           # noqa: E402


# ===== 画像生成 =====
def generate_png(uploaded_file, design: str) -> tuple[bytes, str, str]:
    """アップロードファイルから PNG バイト列を生成し返す。

    ファイル名パース・データ読込はすべて kamiko（多様な形式に対応）を使用し、
    描画のみ選択されたデザインで実行する。
    Returns: (png_bytes, suggested_filename, info_label)
    """
    # アップロードを一時ファイルに書き出し（元ファイル名を保持してパース可能に）
    tmpdir = tempfile.mkdtemp(prefix='ranking_')
    src_path = os.path.join(tmpdir, uploaded_file.name)
    with open(src_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())

    date_full, store = kamiko.parse_filename(src_path)
    if store.endswith('店'):
        store = store[:-1]
    ranking = kamiko.load_ranking(src_path)
    if not ranking:
        raise ValueError('ランキング対象データが0件です（フォーマットを確認してください）')

    date_md = date_full[4:]
    out_path = os.path.join(tmpdir, f'{date_md}_{store}.png')

    render_fn = win6.render_image if design == 'win6game' else kamiko.render_image
    render_fn(ranking, date_full, store, out_path)

    with open(out_path, 'rb') as f:
        png = f.read()
    label = f'{store}　{date_full[:4]}-{date_full[4:6]}-{date_full[6:8]}　({design})'
    return png, f'{date_md}_{store}.png', label


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


# ===== UI =====
st.set_page_config(
    page_title='差枚ランキング画像ジェネレーター',
    page_icon='🎰',
    layout='wide',
)

# 履歴用セッションステート
if 'history' not in st.session_state:
    st.session_state.history = []  # list of dict(label, filename, png, ts)

st.title('🎰 差枚ランキング画像ジェネレーター')
st.caption('Excel / CSV をアップロードするとランキング画像（PNG）を生成します。')

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
        # 全履歴をZIPでまとめてダウンロード
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

if uploaded:
    st.write(f'**{len(uploaded)} 件**のファイルを処理します。')
    progress = st.progress(0.0)
    success_items: list[tuple[str, bytes]] = []   # ZIP用
    fail = 0
    for i, uf in enumerate(uploaded, start=1):
        with st.container(border=True):
            st.markdown(f'### {uf.name}')
            try:
                png, fname, label = generate_png(uf, design)
                col1, col2 = st.columns([3, 2])
                with col1:
                    st.image(png, caption=label)
                with col2:
                    st.success('生成成功')
                    st.download_button(
                        '📥 PNGをダウンロード',
                        data=png,
                        file_name=fname,
                        mime='image/png',
                        key=f'dl_{i}_{fname}',
                        use_container_width=True,
                    )
                    st.code(fname, language=None)
                # 履歴 + ZIP集約へ追加
                st.session_state.history.append({
                    'label': label,
                    'filename': fname,
                    'png': png,
                    'ts': datetime.now().isoformat(timespec='seconds'),
                })
                success_items.append((fname, png))
            except Exception as e:
                st.error(f'生成失敗: {e}')
                with st.expander('詳細トレースバック'):
                    st.code(traceback.format_exc())
                fail += 1
        progress.progress(i / len(uploaded))

    st.divider()
    success = len(success_items)
    if fail == 0:
        st.success(f'すべて完了しました（成功 {success} 件）')
    else:
        st.warning(f'完了: 成功 {success} 件 / 失敗 {fail} 件')

    # 今回処理分のZIP一括DL（2件以上で表示）
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
    st.info('左上のボックスからファイルをドラッグ＆ドロップしてください。')

    with st.expander('対応ファイル名フォーマット', expanded=False):
        st.markdown('''
**xlsx**
- `YYYYMMDD_店舗名_20S.xlsx`（標準）
- `【店舗】【M.D】【神の子来店】S結果.xlsx`（神の子スタジオ形式・BB/RB省略）

**CSV**
- `店舗名(20S)_YYYY-MM-DD_全台.csv`
- `店舗名YYYY-MM-DD_全台.csv`
- 先頭日付プレフィックス（例: `2025.5:9...`, `2025-11-8...`）も自動認識
''')
