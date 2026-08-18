"""
GitHub Actions scraper — runs on GitHub servers (not Streamlit Cloud)
Scrapes Dawn opinion + editorial articles, saves to articles.json in repo.
Schedule: daily at 6 AM PKT (1 AM UTC)
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime

BASE = "https://www.dawn.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}

def get_article_links(url, limit):
    links = []
    seen = set()
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/news/" not in href:
                continue
            full = href if href.startswith("http") else BASE + href
            if full in seen:
                continue
            seen.add(full)
            title = a.get_text(strip=True)
            if not title or len(title) < 8:
                p = a.find_parent(["h2","h3","h4","div","article"])
                if p:
                    title = p.get_text(strip=True)[:120]
            if not title or len(title) < 8:
                continue
            author = "Unknown"
            pb = a.find_parent(["article","div","li"])
            if pb:
                for t in pb.stripped_strings:
                    t = t.strip()
                    if t and t != title and len(t) < 50 and t[0].isupper():
                        author = t
                        break
            links.append((title, full, author))
            if len(links) >= limit:
                break
    except Exception as e:
        print(f"Listing error {url}: {e}")
    return links

def fetch_article(title, url, default_author="Unknown"):
    try:
        time.sleep(random.uniform(1, 2))
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        body = None
        for sel in [".story__content", ".template-story__body", ".entry-body", "article"]:
            body = soup.select_one(sel)
            if body:
                break
        paras = body.find_all("p") if body else soup.find_all("p")
        content = " ".join(p.get_text(strip=True) for p in paras if len(p.get_text(strip=True)) > 40)
        if len(content) < 300:
            return None
        author = default_author
        for sel in [".byline__name", ".story__byline", ".author", "[rel='author']"]:
            t = soup.select_one(sel)
            if t:
                txt = t.get_text(strip=True)
                if txt:
                    author = txt
                    break
        return {"title": title, "content": content, "author": author}
    except Exception as e:
        print(f"Article error {url}: {e}")
        return None

articles = []
seen_urls = set()

print("Scraping opinion columns...")
for title, url, author in get_article_links(f"{BASE}/newspaper/column", 8):
    if len(articles) >= 4:
        break
    if url in seen_urls:
        continue
    seen_urls.add(url)
    a = fetch_article(title, url, author)
    if a:
        articles.append(a)
        print(f"  ✓ {a['title'][:60]}")

print("Scraping editorials...")
for title, url, author in get_article_links(f"{BASE}/newspaper/editorial", 5):
    if len(articles) >= 6:
        break
    if url in seen_urls:
        continue
    seen_urls.add(url)
    a = fetch_article(title, url, "Editorial")
    if a:
        if a["author"] == "Unknown":
            a["author"] = "Editorial"
        articles.append(a)
        print(f"  ✓ {a['title'][:60]}")

output = {
    "date": datetime.now().strftime("%d %B %Y"),
    "fetched_at": datetime.utcnow().isoformat(),
    "articles": articles
}

with open("articles.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nSaved {len(articles)} articles to articles.json")
