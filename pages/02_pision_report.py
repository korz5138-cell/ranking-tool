"""pision レポート生成・Discord送信 UI"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timedelta

import streamlit as st

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import pision_api as papi
import pision_summary as ps
import pision_renderer as pr
import discord_reporter as dr


st.set_page_config(
    page_title='pision レポート送信',
    page_icon='📊',
)

st.title('📊 pision レポート生成・Discord送信')
st.caption('指定したホールのデータをまとめて、Discord に送信します。')

# APIキー確認
if not os.environ.get('PISION_API_KEY'):
    st.error('❌ PISION_API_KEY 環境変数が設定されていません')
    st.stop()

if not os.environ.get('DISCORD_WEBHOOK_URL'):
    st.error('❌ DISCORD_WEBHOOK_URL 環境変数が設定されていません')
    st.stop()

# ホール検索
st.subheader('1. ホールを選択')

with st.spinner('ホール一覧を取得中...'):
    try:
        halls = papi.get_halls()
    except Exception as e:
        st.error(f'エラー: ホール一覧の取得に失敗しました\n{e}')
        st.stop()

# ホール名で検索
search_text = st.text_input('ホール名で検索', placeholder='例: イーゾーン富山')
filtered_halls = [h for h in halls if search_text.lower() in h['name'].lower()] if search_text else halls

if len(filtered_halls) > 50:
    st.info(f'検索結果が多すぎます。ホール名をより詳しく入力してください。')
    st.stop()

hall_options = {h['name']: h['id'] for h in filtered_halls}
selected_hall_name = st.selectbox('ホール', options=list(hall_options.keys()))
selected_hall_id = hall_options[selected_hall_name]

# 日付選択
st.subheader('2. 日付を選択')
target_date = st.date_input(
    '対象日',
    value=datetime.now().date() - timedelta(days=1),
    format='YYYY/MM/DD',
)

# トピック・抽選人数入力
st.subheader('3. トピック・抽選人数（オプション）')
col1, col2 = st.columns(2)
with col1:
    topic = st.text_input(
        'トピック',
        placeholder='例: 通常営業',
        help='例: 〇〇記念日 / リニューアル / キャンペーン開催中 など',
    )
with col2:
    lottery_str = st.text_input(
        '抽選人数',
        placeholder='例: 150',
        help='数値のみ入力。なければ空欄',
    )
    lottery = None
    if lottery_str.strip():
        try:
            lottery = int(lottery_str.strip())
        except ValueError:
            st.warning('抽選人数は数値で入力してください')

# プレビュー・送信
st.subheader('4. 確認・送信')

if st.button('🔍 プレビュー生成', use_container_width=True, type='primary'):
    with st.spinner('データを取得中...'):
        try:
            # API キーの確認
            api_key = os.environ.get('PISION_API_KEY')
            if not api_key:
                st.error('❌ PISION_API_KEY が設定されていません')
                st.stop()

            st.write(f'ホールID: {selected_hall_id}, 日付: {target_date.isoformat()}')

            summary = ps.fetch_and_summarize_hall(selected_hall_id, target_date.isoformat())
            if not summary:
                st.error('❌ 指定されたホール・日付のデータが見つかりません')
                st.info('ℹ️ サイトで同じホール・日付のデータがあるか確認してください')
                st.stop()
        except Exception as e:
            st.error(f'❌ エラー: データ取得に失敗しました')
            st.write(f'詳細: {str(e)}')
            import traceback
            st.code(traceback.format_exc())
            st.stop()

    # ホール情報取得
    hall_info = next((h for h in halls if h['id'] == selected_hall_id), None)
    pref_id = hall_info['prefectureId']

    # テンプレート選択（都道府県による）
    if pref_id == 26:  # 京都
        template_name = 'kyoto'
        text_fn = pr.generate_discord_text_kyoto
    else:  # 富山、新潟、長野、山梨、福井、石川など
        template_name = 'hokuriku'
        text_fn = pr.generate_discord_text_hokuriku

    # 統計情報表示
    col1, col2, col3 = st.columns(3)
    with col1:
        total_str = f"+{summary.total_diff:,}" if summary.total_diff >= 0 else str(summary.total_diff)
        st.metric('総差枚', f"{total_str}枚")
    with col2:
        avg_val = int(summary.avg_diff)
        avg_str = f"+{avg_val:,}" if avg_val >= 0 else str(avg_val)
        st.metric('平均差枚', f"{avg_str}枚")
    with col3:
        avg_games = sum(u.games for u in summary.unit_details) // len(summary.unit_details) if summary.unit_details else 0
        st.metric('平均G数', f"{avg_games:,}G")

    # 機種TOP3
    st.markdown('**機種別 TOP3**')
    for i, k in enumerate(summary.kishu_summaries[:3], 1):
        st.write(f'{i}. {k.name}: +{int(k.avg_diff):,}枚 ({k.avg_games:,}G)')

    # 台別TOP5
    st.markdown('**台別 TOP5**')
    for i, u in enumerate(summary.unit_details[:5], 1):
        st.write(f'{i}. {u.unit_id}番台 ({u.model_name}): +{u.diff:,}枚')

    # 画像生成
    with st.spinner('画像を生成中...'):
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            output_path = f.name

        try:
            if template_name == 'hokuriku':
                pr.render_hokuriku(summary, output_path, topic, lottery)
            elif template_name == 'kyoto':
                pr.render_kyoto(summary, output_path, topic, lottery)
            else:
                st.warning('未対応の都道府県です')
                st.stop()

            # 画像表示
            with open(output_path, 'rb') as f:
                img_bytes = f.read()
            st.image(img_bytes, caption=f'{summary.hall_name} - {target_date}')

            # テキスト生成
            if template_name == 'hokuriku':
                text = pr.generate_discord_text_hokuriku(summary, topic=topic if topic else "通常営業")
            elif template_name == 'kyoto':
                text = pr.generate_discord_text_kyoto(summary, topic=topic if topic else "通常営業")

            st.markdown('**投稿テキスト**')
            st.code(text, language=None)

            # Discord送信ボタン
            if st.button('📤 Discord に送信', use_container_width=True, type='primary', key='send_discord'):
                with st.spinner('送信中...'):
                    success, message = dr.send_message(text, output_path)
                    if success:
                        st.success('✅ Discord に送信完了！')
                    else:
                        st.error(f'❌ Discord送信に失敗しました')
                        st.write(f'詳細: {message}')

        finally:
            import os as _os
            if _os.path.exists(output_path):
                _os.unlink(output_path)
