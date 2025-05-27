import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

# ضبط إعدادات الصفحة
st.set_page_config(page_title="شائعات انتقال اللاعبين", layout="centered", page_icon="⚽")

# تحميل ملف اللاعبين
@st.cache_data
def load_players():
    url = 'https://raw.githubusercontent.com/leo997a/mercato/main/players.csv'
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"❌ خطأ أثناء تحميل ملف players.csv: {str(e)}")
        st.stop()

# دالة ترجمة النص
def translate_text(text, source='auto', target='en'):
    try:
        return GoogleTranslator(source=source, target=target).translate(text)
    except:
        return text

# دالة البحث عن بيانات اللاعب في Transfermarkt
def get_transfer_data(player_name_en, club_name_en):
    try:
        search_url = f"https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query={player_name_en.replace(' ', '+')}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        res = requests.get(search_url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')

        # البحث عن رابط اللاعب
        player_link = soup.find('a', class_='spielprofil_tooltip')
        if not player_link:
            return None, None, []

        player_url = 'https://www.transfermarkt.com' + player_link['href']
        player_page = requests.get(player_url, headers=headers, timeout=10)
        player_page.raise_for_status()
        soup_player = BeautifulSoup(player_page.text, 'html.parser')

        # استخراج صورة اللاعب
        try:
            image_url = soup_player.find('img', class_='data-header__profile-image')['src']
        except:
            image_url = None

        # استخراج القيمة السوقية
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
            'probability': 30,  # قيمة وهمية، يمكن تحسينها لاحقًا
            'source': 'Transfermarkt'
        }

        rumors = []

        return player_info, transfer_info, rumors

    except requests.RequestException as e:
        st.error(f"❌ خطأ أثناء الاتصال بـ Transfermarkt: {str(e)}")
        return None, None, []

# تحميل بيانات اللاعبين
players_df = load_players()

# التحقق من وجود العمود 'name_en'
if 'name_en' not in players_df.columns:
    st.error("❌ ملف players.csv لا يحتوي على العمود 'name_en'")
    st.write("أسماء الأعمدة المتوفرة:", players_df.columns.tolist())
    st.stop()

# إنشاء عمود 'name_ar' باستخدام الترجمة التلقائية إذا لم يكن موجودًا
if 'name_ar' not in players_df.columns:
    with st.spinner("جارٍ ترجمة أسماء اللاعبين إلى العربية..."):
        players_df['name_ar'] = players_df['name_en'].apply(
            lambda x: translate_text(x, source='en', target='ar')
        )

st.title("🔍 بحث شائعات انتقال اللاعبين")

# البحث عن اللاعب باستخدام text_input
search_term = st.text_input("ابحث عن اللاعب (اكتب الحرف الأول من الاسم بالعربية أو الإنجليزية)", placeholder="مثال: م أو M")

# تصفية اللاعبين بناءً على بداية الاسم فقط
if search_term:
    search_term = search_term.strip()
    filtered_players = players_df[
        players_df['name_ar'].str.startswith(search_term, na=False) |
        players_df['name_en'].str.lower().str.startswith(search_term.lower(), na=False)
    ]
    player_options = filtered_players['name_ar'].tolist()
else:
    player_options = []

# اختيار اللاعب من النتائج المصفاة
player_selected = st.selectbox(
    "اختر اللاعب",
    player_options,
    help="اكتب الحرف الأول من اسم اللاعب أعلاه لتصفية القائمة"
)

club_name = st.text_input("اسم النادي", placeholder="مثال: ريال مدريد")

if st.button("بحث"):
    if not player_selected or not club_name:
        st.warning("الرجاء ملء جميع الحقول.")
    else:
        # جلب الاسم الإنجليزي المطابق للاسم العربي المختار
        player_name_en = players_df.loc[players_df['name_ar'] == player_selected, 'name_en'].values
        if len(player_name_en) == 0:
            st.error("❌ لم يتم العثور على اسم اللاعب باللغة الإنجليزية في قاعدة البيانات.")
        else:
            player_name_en = player_name_en[0]
            club_name_en = translate_text(club_name, source='ar', target='en')

            with st.spinner("جارٍ البحث في Transfermarkt..."):
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
