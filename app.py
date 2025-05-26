import streamlit as st
from googletrans import Translator
from utils import get_transfer_data
from PIL import Image
import requests
from io import BytesIO

st.set_page_config(layout="wide", page_title="شائعات انتقال اللاعبين", page_icon="⚽")

st.title("🔍 بحث شائعات انتقال اللاعبين")
st.write("أدخل اسم اللاعب والنادي للبحث عن شائعات انتقال من موقع Transfermarkt")

with st.form("search_form"):
    player_name = st.text_input("اسم اللاعب", placeholder="مثال: ليونيل ميسي")
    club_name = st.text_input("اسم النادي", placeholder="مثال: برشلونة")
    submitted = st.form_submit_button("🔍 بحث")

if submitted:
    if player_name and club_name:
        with st.spinner("جارٍ جلب البيانات..."):
            translator = Translator()
            player_name_en = translator.translate(player_name, src='ar', dest='en').text
            club_name_en = translator.translate(club_name, src='ar', dest='en').text

            player_info, transfer_info, rumors, transfer_image = get_transfer_data(player_name_en, club_name_en)

        if player_info:
            st.subheader(f"معلومات عن {player_info['name']}")

            col1, col2 = st.columns([1, 2])
            if player_info.get("image"):
                image = Image.open(BytesIO(requests.get(player_info["image"]).content))
                col1.image(image, caption=player_info['name'], width=150)

            col2.markdown(f"**القيمة السوقية:** {player_info['market_value']}")
            col2.markdown(f"**رابط اللاعب:** [عرض الصفحة]({player_info['url']})")

            if transfer_info:
                st.markdown(f"### نسبة احتمال الانتقال إلى {club_name}")
                st.progress(transfer_info["probability"] / 100)
                st.markdown(f"**المصدر:** {transfer_info['source']}")

            if rumors:
                st.subheader("📢 الشائعات المرتبطة")
                for rumor in rumors:
                    st.markdown(f"**{rumor['title']}**")
                    st.markdown(f"- القيمة السوقية: {rumor['market_value']}")
                    st.markdown(f"- التاريخ: {rumor['date']}")
                    st.markdown(f"- المحتوى: {rumor['content'][:200]}...")
                    if rumor.get("link"):
                        st.markdown(f"[عرض المنشور الكامل]({rumor['link']})")
                    st.markdown("---")
            else:
                st.warning("لم يتم العثور على شائعات حول هذا الانتقال.")
        else:
            st.error("لم يتم العثور على معلومات عن اللاعب.")
    else:
        st.error("يرجى ملء جميع الحقول.")
