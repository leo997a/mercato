import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from deep_translator import GoogleTranslator
import plotly.express as px
import logging

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# تحميل قاعدة بيانات اللاعبين
try:
    players_df = pd.read_csv("players.csv", encoding="utf-8")
    logger.info("Loaded players.csv successfully")
    # تنظيف البيانات
    players_df = players_df.dropna().reset_index(drop=True)
    players_df = players_df[~players_df["name_en"].str.contains("#VALUE!")]
    players_df = players_df[players_df["name_en"].notnull() & players_df["name_ar"].notnull()]
    players = players_df.to_dict("records")
except FileNotFoundError as e:
    logger.error(f"FileNotFoundError: {str(e)}")
    players = []
    st.error("ملف players.csv غير موجود. يرجى التأكد من وجوده في المجلد.")
except Exception as e:
    logger.error(f"Error loading players.csv: {str(e)}")
    players = []
    st.error(f"خطأ في تحميل ملف players.csv: {str(e)}")

# التحقق من الإدخال العربي
def is_arabic(text):
    return any("\u0600" <= char <= "\u06FF" for char in text)

# دالة الاقتراح التلقائي
def suggest_players(input_text, is_arabic=False):
    suggestions = []
    input_text = input_text.lower().strip()
    
    for player in players:
        name_en = player["name_en"].lower()
        name_ar = player.get("name_ar", "").lower()
        if input_text in name_en or (is_arabic and input_text in name_ar):
            suggestions.append(player["name_en"])
    
    logger.info(f"Suggestions for '{input_text}': {suggestions}")
    return suggestions[:10]

# دالة جلب بيانات الشائعات من Transfermarkt
def get_transfer_data(player_name_en, club_name_en):
    try:
        base_url = "https://www.transfermarkt.com"
        search_url = f"{base_url}/schnellsuche/ergebnis/schnellsuche?query={player_name_en.replace(' ', '+')}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }

        logger.info(f"Fetching data for {player_name_en} from {search_url}")
        res = requests.get(search_url, headers=headers, timeout=10)
        res.raise_for_status()
        time.sleep(1)
        soup = BeautifulSoup(res.content, "html.parser")

        link_tag = soup.select_one("a.spielprofil_tooltip")
        if not link_tag:
            logger.warning(f"No player found for {player_name_en}")
            return None, None, [], "❌ لم يتم العثور على اللاعب."

        player_url = base_url + link_tag["href"]
        res = requests.get(player_url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, "html.parser")

        name_tag = soup.find("h1", {"itemprop": "name"})
        market_value_tag = soup.select_one(".right-td")
        image_tag = soup.select_one(".dataBild img")

        player_info = {
            "name": name_tag.text.strip() if name_tag else player_name_en,
            "market_value": market_value_tag.text.strip() if market_value_tag else "غير متوفر",
            "image": image_tag["src"] if image_tag else None,
            "url": player_url
        }

        rumors = []
        max_probability = 0
        rumors_div = soup.find("div", {"id": "transfers"})
        if rumors_div:
            rows = rumors_div.select("table.transfergeruechte tbody tr")
            for row in rows:
                columns = row.find_all("td")
                if len(columns) >= 5:
                    title = columns[0].text.strip()
                    if club_name_en.lower() in title.lower():
                        percentage = 0
                        percent_span = row.select_one("div.bar-graph span")
                        if percent_span and "%" in percent_span.text:
                            try:
                                percentage = int(percent_span.text.replace("%", "").strip())
                            except:
                                percentage = 0
                        rumors.append({
                            "title": title,
                            "market_value": columns[1].text.strip(),
                            "date": columns[2].text.strip(),
                            "content": columns[4].text.strip(),
                            "link": base_url + columns[0].find("a")["href"] if columns[0].find("a") else None,
                            "percentage": percentage
                        })
                        max_probability = max(max_probability, percentage)

        transfer_info = {
            "probability": max_probability if max_probability > 0 else min(len(rumors) * 25, 100),
            "source": "Transfermarkt"
        }

        logger.info(f"Found {len(rumors)} rumors for {player_name_en}")
        return player_info, transfer_info, rumors, None

    except requests.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return None, None, [], f"❌ خطأ في الاتصال: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return None, None, [], f"❌ حدث خطأ غير متوقع: {str(e)}"

# تنسيق الواجهة
st.set_page_config(page_title="Mercato App", layout="wide")
st.markdown("""
    <style>
    .main {background-color: #f5f5f5; font-family: 'Arial', sans-serif;}
    .title {color: #2c3e50; font-size: 2.5em; text-align: center; margin-bottom: 20px;}
    .subheader {color: #34495e; font-size: 1.5em;}
    .error {color: #e74c3c;}
    .warning {color: #f39c12;}
    .rumor-card {background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin-bottom: 10px;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="title">Mercato: تحليل شائعات انتقال اللاعبين</h1>', unsafe_allow_html=True)

# إدخال اسم اللاعب
player_input = st.text_input("اسم اللاعب (عربي أو إنجليزي)", key="player")
is_arabic_input = is_arabic(player_input)

if player_input and len(player_input) >= 2:
    suggestions = suggest_players(player_input, is_arabic_input)
    if suggestions:
        selected_player = st.selectbox("اختر اللاعب:", suggestions)
    else:
        st.markdown('<p class="warning">لا توجد اقتراحات متاحة.</p>', unsafe_allow_html=True)
        selected_player = player_input
else:
    selected_player = player_input

club_name = st.text_input("اسم النادي (بالإنجليزية)", key="club")

if st.button("بحث", key="search"):
    if selected_player and club_name:
        with st.spinner("جاري البحث..."):
            player_info, transfer_info, rumors, error = get_transfer_data(selected_player, club_name)
        if error:
            st.markdown(f'<p class="error">{error}</p>', unsafe_allow_html=True)
        else:
            # عرض معلومات اللاعب
            col1, col2 = st.columns([1, 2])
            with col1:
                if player_info["image"]:
                    st.image(player_info["image"], width=200)
            with col2:
                st.markdown(f'<h2 class="subheader">{player_info["name"]}</h2>', unsafe_allow_html=True)
                st.write(f"**القيمة السوقية**: {player_info['market_value']}")
                st.write(f"**احتمالية الانتقال**: {transfer_info['probability']}%")
                st.write(f"[رابط اللاعب]({player_info['url']})")

            # عرض الشائعات
            if rumors:
                st.markdown('<h2 class="subheader">الشائعات:</h2>', unsafe_allow_html=True)
                for rumor in rumors:
                    with st.container():
                        st.markdown(
                            f"""
                            <div class="rumor-card">
                                <strong>{rumor['title']}</strong><br>
                                القيمة السوقية: {rumor['market_value']}<br>
                                التاريخ: {rumor['date']}<br>
                                التفاصيل: {rumor['content']}<br>
                                نسبة الاحتمالية: {rumor['percentage']}%{'<br><a href="' + rumor['link'] + '">الرابط</a>' if rumor['link'] else ''}
                            </div>
                            """, unsafe_allow_html=True)

                # رسم بياني لنسب الشائعات
                if any(r["percentage"] > 0 for r in rumors):
                    fig = px.bar(
                        x=[r["title"] for r in rumors],
                        y=[r["percentage"] for r in rumors],
                        labels={"x": "الشائعة", "y": "النسبة المئوية (%)"},
                        title="نسب الشائعات"
                    )
                    st.plotly_chart(fig)
            else:
                st.markdown('<p class="warning">لا توجد شائعات متعلقة بالنادي.</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="warning">يرجى إدخال اسم اللاعب والنادي.</p>', unsafe_allow_html=True)
