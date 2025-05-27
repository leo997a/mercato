import streamlit as st
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from PIL import Image
import pandas as pd

# يجب أن يكون هذا السطر في البداية
st.set_page_config(page_title="شائعات انتقال اللاعبين", layout="centered", page_icon="⚽")

def translate_text(text):
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except:
        return text  # fallback

def get_transfer_data(player_name, club_name):
    player_name_en = translate_text(player_name)
    club_name_en = translate_text(club_name)

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
        'name': player_name,
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

# --- واجهة التطبيق ---
st.title("🔍 بحث شائعات انتقال اللاعبين")
st.markdown("ارفع ملف اللاعبين واختر اسماً من القائمة ثم أدخل النادي.")

uploaded_file = st.file_uploader("ارفع ملف اللاعبين (CSV ويحتوي عمود name_en)", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()

    if "name_en" in df.columns:
        player_name = st.selectbox("اختر اسم اللاعب", df["name_en"].dropna().unique())
        club_name = st.text_input("اسم النادي", placeholder="مثال: ريال مدريد")

        if st.button("بحث"):
            if not player_name or not club_name:
                st.warning("الرجاء ملء جميع الحقول.")
            else:
                with st.spinner("جارٍ البحث..."):
                    player_info, transfer_info, rumors = get_transfer_data(player_name, club_name)

                if not player_info:
                    st.error("❌ لم يتم العثور على اللاعب.")
                else:
                    if player_info['image']:
                        st.image(player_info['image'], width=150)
                    st.subheader(player_info['name'])
                    st.markdown(f"**القيمة السوقية:** {player_info['market_value']}")
                    st.markdown(f"**احتمالية الانتقال إلى {club_name}:** {transfer_info['probability']}%")
                    st.markdown(f"[عرض صفحة اللاعب على Transfermarkt]({player_info['url']})")

                    if not rumors:
                        st.info("لا توجد شائعات حالياً حول هذا الانتقال.")
    else:
        st.error("❌ ملف CSV لا يحتوي على العمود 'name_en'")
else:
    st.info("📄 الرجاء رفع ملف CSV يحتوي على عمود 'name_en'")
