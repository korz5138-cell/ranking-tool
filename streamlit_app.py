"""pision レポート生成・Discord送信 UI"""
import streamlit as st

st.set_page_config(
    page_title='pision レポート送信',
    page_icon='📊',
    layout='centered',
)

st.title('📊 pision レポート生成・Discord送信')
st.caption('指定したホールのデータをまとめて、Discord に送信します。')

# ページの説明
st.info('左サイドバーから「pision_report」を選択してください')
