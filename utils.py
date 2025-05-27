import requests
from bs4 import BeautifulSoup

def get_transfer_data(player_name_en, club_name_en):
    """
    يبحث عن اللاعب في موقع Transfermarkt، ويجلب معلوماته الأساسية والشائعات واحتمال الانتقال.
    """
    try:
        base_url = "https://www.transfermarkt.com"
        search_url = f"{base_url}/schnellsuche/ergebnis/schnellsuche?query={player_name_en.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0"}

        res = requests.get(search_url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, "html.parser")

        link_tag = soup.select_one("a.spielprofil_tooltip")
        if not link_tag:
            return None, None, [], "❌ لم يتم العثور على اللاعب في نتائج البحث."

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

        # استخراج الشائعات
        rumors = []
        rumors_table = soup.find("div", {"id": "transfers"})

        if rumors_table:
            rumor_rows = rumors_table.select("table.transfergeruechte > tbody > tr")
            for row in rumor_rows:
                columns = row.find_all("td")
                if len(columns) >= 5:
                    rumor_title = columns[0].text.strip()
                    rumor = {
                        "title": rumor_title,
                        "market_value": columns[1].text.strip(),
                        "date": columns[2].text.strip(),
                        "content": columns[4].text.strip(),
                        "link": base_url + columns[0].find("a")["href"] if columns[0].find("a") else None
                    }
                    if club_name_en.lower() in rumor_title.lower():
                        rumors.append(rumor)

        # تقدير نسبة الانتقال بناءً على عدد الشائعات
        transfer_info = {
            "probability": min(len(rumors) * 25, 100),
            "source": "Transfermarkt"
        }

        return player_info, transfer_info, rumors, None

    except requests.RequestException as e:
        return None, None, [], f"❌ خطأ في الاتصال: {str(e)}"
    except Exception as e:
        return None, None, [], f"❌ حدث خطأ غير متوقع: {str(e)}"
