import streamlit as st
from utils import get_transfer_data

st.set_page_config(page_title="تحليل انتقالات اللاعبين", layout="wide")
st.title("⚽ تحليل انتقالات اللاعبين من Transfermarkt")

# إدخال أسماء اللاعبين والنادي
club_name = st.text_input("🔍 اسم النادي (بالإنجليزية)", "Real Madrid")
players_input = st.text_area("🧑‍💼 أدخل أسماء اللاعبين (واحد في كل سطر):", 
"""
Kylian Mbappé
Mohamed Salah
Jude Bellingham
""")

# زر بدء التحليل
if st.button("ابدأ التحليل"):
    st.info("⏳ جارٍ ترجمة أسماء اللاعبين إلى العربية وجلب بياناتهم...")

    player_names = [name.strip() for name in players_input.strip().split("\n") if name.strip()]
    translated_players = []

    for player_name in player_names:
        with st.spinner(f"🔄 جارٍ جلب بيانات {player_name}..."):
            try:
                player_info, transfer_info, rumors, error = get_transfer_data(player_name, club_name)

                if error or not player_info:
                    st.warning(f"⚠️ لم يتم العثور على معلومات للاعب: {player_name}")
                    continue

                translated_players.append({
                    "name": player_info["name"],
                    "market_value": player_info["market_value"],
                    "probability": transfer_info["probability"],
                    "image": player_info["image"],
                    "rumors": rumors,
                    "link": player_info["url"]
                })
            except Exception as e:
                st.error(f"❌ حدث خطأ أثناء معالجة {player_name}: {str(e)}")
                continue

    # عرض النتائج
    if translated_players:
        st.success("✅ تم تحميل بيانات اللاعبين بنجاح.")

        for player in translated_players:
            st.markdown("---")
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if player["image"]:
                    st.image(player["image"], width=120)
                else:
                    st.text("لا توجد صورة متاحة.")
            
            with col2:
                st.subheader(player["name"])
                st.markdown(f"📈 القيمة السوقية: **{player['market_value']}**")
                st.markdown(f"🔁 احتمالية الانتقال إلى {club_name}: **{player['probability']}%**")
                st.markdown(f"🌐 [رابط Transfermarkt]({player['link']})")

                if player["rumors"]:
                    with st.expander("📢 عرض الشائعات المرتبطة"):
                        for rumor in player["rumors"]:
                            st.markdown(f"- **{rumor['title']}**")
                            st.markdown(f"  🗓️ {rumor['date']} | 💰 {rumor['market_value']}")
                            st.markdown(f"  🔗 [رابط الشائعة]({rumor['link']})")
                else:
                    st.info("لا توجد شائعات متاحة لهذا اللاعب.")
    else:
        st.error("❌ لم يتم العثور على بيانات لأي لاعب. يرجى التحقق من الأسماء أو المحاولة لاحقًا.")
