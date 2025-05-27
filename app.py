import requests
from bs4 import BeautifulSoup

def get_transfer_data(player_name_en, club_name_en):
    base_url = "https://www.transfermarkt.com"
    search_url = f"{base_url}/schnellsuche/ergebnis/schnellsuche?query={player_name_en.replace(' ', '+')}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/114.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    res = requests.get(search_url, headers=headers)
    if res.status_code != 200:
        return None, None, [], f"خطأ في تحميل صفحة البحث، كود الحالة: {res.status_code}"

    soup = BeautifulSoup(res.content, "html.parser")

    link_tag = soup.select_one("a.spielprofil_tooltip")
    if not link_tag:
        return None, None, [], "لم يتم العثور على اللاعب"

    player_url = base_url + link_tag["href"]

    res = requests.get(player_url, headers=headers)
    if res.status_code != 200:
        return None, None, [], f"خطأ في تحميل صفحة اللاعب، كود الحالة: {res.status_code}"

    soup = BeautifulSoup(res.content, "html.parser")

    # طباعة جزء من الصفحة لتشخيص المشكلة (يمكن تعطيلها لاحقاً)
    # print(soup.prettify()[:1000])

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

    max_probability = 0

    if rumors_div:
        rows = rumors_div.select("table.transfergeruechte tbody tr")
        for row in rows:
            columns = row.find_all("td")
            if len(columns) >= 5:
                title = columns[0].text.strip()
                market_value = columns[1].text.strip()
                date = columns[2].text.strip()
                content = columns[4].text.strip()
                link = base_url + columns[0].find("a")["href"] if columns[0].find("a") else None

                percentage = 0
                percent_span = row.select_one("div.bar-graph span")
                if percent_span and "%" in percent_span.text:
                    try:
                        percentage = int(percent_span.text.replace("%", "").strip())
                    except:
                        pass

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
