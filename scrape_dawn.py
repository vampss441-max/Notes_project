"""
GitHub Actions scraper — runs on GitHub servers daily at 6 AM PKT
Scrapes Dawn newspaper/column + newspaper/editorial, saves to articles.json
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


def get_article_links(section_url, limit):
    """
    Get article links from Dawn newspaper listing page.
    Targets <h2><a href="/news/..."> which is how Dawn lists articles.
    """
    links = []
    seen = set()
    print(f"\nFetching: {section_url}")
    try:
        r = requests.get(section_url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        print(f"  Status: {r.status_code}, Length: {len(r.text)}")
        soup = BeautifulSoup(r.text, "html.parser")

        # Dawn listing pages use <h2><a href="/news/XXXXX">Title</a></h2>
        for h2 in soup.find_all("h2"):
            a = h2.find("a", href=True)
            if not a:
                continue
            href = a["href"]
            if "/news/" not in href:
                continue
            full_url = href if href.startswith("http") else BASE + href
            if full_url in seen:
                continue
            seen.add(full_url)

            title = a.get_text(strip=True)
            if not title or len(title) < 5:
                continue

            links.append((title, full_url))
            print(f"  Found: {title[:60]} → {full_url}")
            if len(links) >= limit:
                break

    except Exception as e:
        print(f"  ERROR: {e}")
        raise

    return links


def fetch_article(title, url, default_author="Unknown"):
    """Fetch full article content + author from Dawn article page."""
    try:
        time.sleep(random.uniform(1.5, 2.5))
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Get article body
        body = None
        for sel in [".story__content", ".template-story__body",
                    ".entry-body", "[itemprop='articleBody']", "article"]:
            body = soup.select_one(sel)
            if body:
                break

        # Remove soft hyphens and zero-width characters from HTML BEFORE get_text()
        # Dawn uses &shy; (soft hyphen) in compound words — it becomes \u00ad after parsing
        # and renders as ■ in PDFs. Must strip from raw HTML first.
        raw_html = str(body) if body else str(soup)
        raw_html = raw_html.replace("&shy;", "").replace("\u00ad", "")
        cleaned_soup = BeautifulSoup(raw_html, "html.parser")

        paras = cleaned_soup.find_all("p")
        content = " ".join(
            p.get_text(strip=True) for p in paras
            if len(p.get_text(strip=True)) > 40
        )

        # Final pass — strip any remaining invisible/control Unicode characters
        for bad_char in ["\u200b", "\u200c", "\u200d", "\ufeff", "\u2028", "\u2029"]:
            content = content.replace(bad_char, "")

        if len(content) < 300:
            print(f"  Skipped (too short: {len(content)} chars): {title[:50]}")
            return None

        # Get author from <meta name="author"> — always present on Dawn article pages
        author = default_author
        meta_author = soup.find("meta", attrs={"name": "author"})
        if meta_author and meta_author.get("content", "").strip():
            author = meta_author["content"].strip()
        else:
            # Fallback: author link in page body
            author_link = soup.find("a", href=lambda h: h and "/authors/" in str(h))
            if author_link:
                author = author_link.get_text(strip=True)

        print(f"  ✓ '{title[:55]}' by {author} ({len(content)} chars)")
        return {"title": title, "content": content, "author": author}

    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return None


# ── Main ─────────────────────────────────────────────────────
articles = []
seen_urls = set()

# 4 opinion columns
print("=" * 50)
print("SCRAPING OPINION COLUMNS")
print("=" * 50)
col_links = get_article_links(f"{BASE}/newspaper/column", limit=6)
for title, url in col_links:
    if len(articles) >= 4:
        break
    if url in seen_urls:
        continue
    seen_urls.add(url)
    a = fetch_article(title, url, default_author="Unknown")
    if a:
        articles.append(a)

# 2 editorials
print("=" * 50)
print("SCRAPING EDITORIALS")
print("=" * 50)
ed_links = get_article_links(f"{BASE}/newspaper/editorial", limit=4)
for title, url in ed_links:
    if len(articles) >= 6:
        break
    if url in seen_urls:
        continue
    seen_urls.add(url)
    a = fetch_article(title, url, default_author="Editorial")
    if a:
        if a["author"] == "Unknown":
            a["author"] = "Editorial"
        articles.append(a)

# ── Save ─────────────────────────────────────────────────────
print("=" * 50)
print(f"TOTAL: {len(articles)} articles")
for i, a in enumerate(articles, 1):
    print(f"  {i}. {a['title'][:60]} — {a['author']}")

output = {
    "date": datetime.now().strftime("%d %B %Y"),
    "fetched_at": datetime.utcnow().isoformat(),
    "articles": articles
}

with open("articles.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nSaved {len(articles)} articles to articles.json")

if len(articles) < 4:
    print(f"WARNING: Only {len(articles)} articles — expected 6")
    exit(1)
