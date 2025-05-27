import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

# Set page configuration at the very top
st.set_page_config(page_title="شائعات انتقال اللاعبين", layout="centered", page_icon="⚽")

# تحميل ملف اللاعبين
@st.cache_data
def load_players():
    df = pd.read_csv('https://raw.githubusercontent.com/leo997a/mercato/refs/heads/main/players.csv')
    return df

# دالة ترجمة النص
def translate_text(text, source='auto', target='en'):
    try:
        return GoogleTranslator(source=source, target=target).translate(text)
    except:
        return text

# دالة البحث عن بيانات اللاعب
def get_transfer_data(player_name_en, club_name_en):
    search_url = f"https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query={player_name_en.replace(' ', '+')}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    player_link = soup.find('a', class_='spielprofil_tooltip')
    if not player_link:
        return None, None, []

    player_url = 'https://www.transfermarkt.com' + player_link['href']
    player_page = requests.get(player_url, headers=headers)
    soup_player = BeautifulSoup(player_page.text, 'html.parser')

    try:
        image_url = soup_player.find('img', class_='data-header__profile-image')['src']
    except:
        image_url = None

    try:
        market_value = soup_player.find('div', class_='right-td').text.strip()
    except:
        market_value = "غير متوفرة"

    player_info = {
        'name': player_name_en,
        'image': image_url,
        'market_value': market_value,
        'url': player_url
    }

    transfer_info = {
        'probability': 30,
        'source': 'Transfermarkt'
    }

    rumors = []

    return player_info, transfer_info, rumors

# تحميل بيانات اللاعبين
players_df = load_players()

# التحقق من وجود العمود 'name_en'
if 'name_en' not in players_df.columns:
    st.error("❌ ملف players.csv لا يحتوي على العمود 'name_en'")
    st.stop()

st.title("🔍 بحث شائعات انتقال اللاعبين")

# إنشاء قائمة للأسماء الإنجليزية
player_options = players_df['name_en'].tolist()
player_selected = st.selectbox("اختر اسم اللاعب (يمكن البحث بالكتابة)", player_options)

club_name = st.text_input("اسم النادي", placeholder="مثال: ريال مدريد")

if st.button("بحث"):
    if not player_selected or not club_name:
        st.warning("الرجاء ملء جميع الحقول.")
    else:
        player_name_en = player_selected  # الاسم المختار هو بالفعل بالإنجليزية
        club_name_en = translate_text(club_name, source='ar', target='en')

        with st.spinner("جارٍ البحث..."):
            player_info, transfer_info, rumors = get_transfer_data(player_name_en, club_name_en)

        if not player_info:
            st.error("❌ لم يتم العثور على اللاعب في موقع Transfermarkt.")
        else:
            if player_info['image']:
                st.image(player_info['image'], width=150)
            st.subheader(player_selected)
            st.markdown(f"**القيمة السوقية:** {player_info['market_value']}")
            st.markdown(f"**احتمالية الانتقال إلى {club_name}:** {transfer_info['probability']}%")
            st.markdown(f"[عرض صفحة اللاعب على Transfermarkt]({player_info['url']})")

            if not rumors:
                st.info("لا توجد شائعات حالياً حول هذا الانتقال.")
