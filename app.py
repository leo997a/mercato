import requests
from bs4 import BeautifulSoup

def get_transfer_data(player_name_en, club_name_en):
    """
    يبحث عن اللاعب في موقع Transfermarkt، ويجلب معلوماته الأساسية
    بالإضافة إلى شائعات الانتقال مع النسبة الدقيقة لكل شائعة.
    """

    base_url = "https://www.transfermarkt.com"
    search_url = f"{base_url}/schnellsuche/ergebnis/schnellsuche?query={player_name_en.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}

    # البحث عن صفحة اللاعب عبر البحث السريع
    res = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(res.content, "html.parser")

    # الحصول على أول رابط صفحة للاعب
    link_tag = soup.select_one("a.spielprofil_tooltip")
    if not link_tag:
        # لم يتم العثور على اللاعب
        return None, None, [], "لم يتم العثور على اللاعب"

    player_url = base_url + link_tag["href"]

    # طلب صفحة اللاعب
    res = requests.get(player_url, headers=headers)
    soup = BeautifulSoup(res.content, "html.parser")

    # جلب معلومات اللاعب الأساسية
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
    rumors_div = soup.find("div", {"id": "transfers"})

    max_probability = 0  # أعلى نسبة انتقال للنادي المطلوب

    if rumors_div:
        # صفوف جدول شائعات الانتقال
        rows = rumors_div.select("table.transfergeruechte tbody tr")
        for row in rows:
            columns = row.find_all("td")
            if len(columns) >= 5:
                title = columns[0].text.strip()
                market_value = columns[1].text.strip()
                date = columns[2].text.strip()
                content = columns[4].text.strip()
                link = base_url + columns[0].find("a")["href"] if columns[0].find("a") else None

                # التقاط نسبة الانتقال (مثلاً 2%) من شريط النسبة داخل الصف
                percentage = 0
                percent_span = row.select_one("div.bar-graph span")
                if percent_span and "%" in percent_span.text:
                    try:
                        percentage = int(percent_span.text.replace("%", "").strip())
                    except:
                        pass

                # إذا كانت الشائعة تخص النادي المطلوب
                if club_name_en.lower() in title.lower():
                    rumors.append({
                        "title": title,
                        "market_value": market_value,
                        "date": date,
                        "content": content,
                        "link": link,
                        "percentage": percentage
                    })
                    if percentage > max_probability:
                        max_probability = percentage

    transfer_info = {
        "probability": max_probability,
        "source": "Transfermarkt"
    }

    return player_info, transfer_info, rumors, None
