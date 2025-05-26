import requests
from bs4 import BeautifulSoup

def get_transfer_data(player_name_en, club_name_en):
    """
    يبحث عن اللاعب في موقع Transfermarkt، ويجلب معلوماته الأساسية واحتمال الانتقال.
    """
    base_url = "https://www.transfermarkt.com"
    search_url = f"{base_url}/schnellsuche/ergebnis/schnellsuche?query={player_name_en.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}

    res = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(res.content, "html.parser")

    # البحث عن أول رابط لصفحة اللاعب
    link_tag = soup.select_one("a.spielprofil_tooltip")
    if not link_tag:
        return None, None, [], None

    player_url = base_url + link_tag["href"]

    res = requests.get(player_url, headers=headers)
    soup = BeautifulSoup(res.content, "html.parser")

    # معلومات اللاعب
    name_tag = soup.find("h1", {"itemprop": "name"})
    market_value_tag = soup.select_one(".right-td")
    image_tag = soup.select_one(".dataBild img")

    player_info = {
        "name": name_tag.text.strip() if name_tag else player_name_en,
        "market_value": market_value_tag.text.strip() if market_value_tag else "غير متوفر",
        "image": image_tag["src"] if image_tag else None,
        "url": player_url
    }

    # استخراج الشائعات
    rumors = []
    rumors_table = soup.find("div", {"id": "transfers"})

    if rumors_table:
        rumor_rows = rumors_table.select("table.transfergeruechte > tbody > tr")
        for row in rumor_rows:
            columns = row.find_all("td")
            if len(columns) >= 5:
                rumor = {
                    "title": columns[0].text.strip(),
                    "market_value": columns[1].text.strip(),
                    "date": columns[2].text.strip(),
                    "content": columns[4].text.strip(),
                    "link": base_url + columns[0].find("a")["href"] if columns[0].find("a") else None
                }
                if club_name_en.lower() in rumor["title"].lower():
                    rumors.append(rumor)

    # حساب نسبة تقديرية من عدد الشائعات
    transfer_info = {
        "probability": min(len(rumors) * 25, 100),
        "source": "Transfermarkt"
    }

    return player_info, transfer_info, rumors, None
