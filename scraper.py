import requests
from bs4 import BeautifulSoup
import json

BASE = "https://tribune.com.pk"

headers = {
    "User-Agent": "Mozilla/5.0"
}

def scrape():
    res = requests.get(BASE + "/opinion", headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    links = []

    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)
        href = a["href"]

        if href.startswith("/") and len(title) > 25:
            full = BASE + href
            links.append((title, full))

    seen = set()
    clean_links = []
    for t, l in links:
        if l not in seen:
            seen.add(l)
            clean_links.append((t, l))

    articles = []

    for title, link in clean_links[:12]:
        try:
            page = requests.get(link, headers=headers)
            soup_page = BeautifulSoup(page.text, "html.parser")

            paragraphs = soup_page.find_all("p")
            content = " ".join(p.get_text(strip=True) for p in paragraphs)

            if len(content) < 400:
                continue

            articles.append({
                "title": title,
                "content": content,
                "author": "Tribune"
            })

            if len(articles) >= 6:
                break

        except:
            continue

    return articles


if __name__ == "__main__":
    data = scrape()

    with open("articles.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
