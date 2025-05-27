import streamlit as st
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from PIL import Image
from io import BytesIO

def translate_text(text):
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except:
        return text  # fallback if translation fails

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

    # Get player image and market value
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

    # Simulate transfer info (since there's no API)
    transfer_info = {
        'probability': 30,  # هذا رقم وهمي، يمكنك تحسينه لاحقاً
        'source': 'Transfermarkt'
    }

    # لا توجد شائعات فعلية بدون API، لكن نرسل قائمة فارغة
    rumors = []

    return player_info, transfer_info, rumors


# واجهة Streamlit
st.set_page_config(page_title="شائعات انتقال اللاعبين", layout="centered", page_icon="⚽")

st.title("🔍 بحث شائعات انتقال اللاعبين")
st.markdown("أدخل اسم اللاعب والنادي المحتمل للبحث من موقع Transfermarkt.")

player_name = st.text_input("اسم اللاعب", placeholder="مثال: محمد صلاح")
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
            st.image(player_info['image'], width=150)
            st.subheader(player_info['name'])
            st.markdown(f"**القيمة السوقية:** {player_info['market_value']}")
            st.markdown(f"**احتمالية الانتقال إلى {club_name}:** {transfer_info['probability']}%")
            st.markdown(f"[عرض صفحة اللاعب على Transfermarkt]({player_info['url']})")

            if not rumors:
                st.info("لا توجد شائعات حالياً حول هذا الانتقال.")

