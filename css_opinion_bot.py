# =========================
# CSS Academy AI System (Upgraded Scraper Version)
# =========================

import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
from groq import Groq
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Image as RLImage, ListFlowable, ListItem, Table, TableStyle
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
import io
import os
import random
from playwright.sync_api import sync_playwright

# =========================
# DATE
# =========================

today = datetime.now().strftime("%d %B %Y")
file_date = datetime.now().strftime("%d-%m-%Y")

# =========================
# CONFIG
# =========================

st.set_page_config(page_title="Daily Opinions' Notes", layout="wide")
st.title("🗞Dawn Opinion System")

api_key = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=api_key)
FAST_MODEL = "llama-3.1-8b-instant"

# =========================
# 🔥 UPGRADED SCRAPER (RESILIENT)
# =========================
def scrape_opinions():
    import requests
    from bs4 import BeautifulSoup

    BASE = "https://www.dawn.com"
    RSS_URL = "https://www.dawn.com/feeds/opinion"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    def extract_article(url):
        try:
            r = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")

            content_div = soup.find("div", class_="story__content")
            paragraphs = content_div.find_all("p") if content_div else soup.find_all("p")

            content = " ".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

            author = "Unknown"
            for sel in [".byline__name", ".story__byline", ".author"]:
                tag = soup.select_one(sel)
                if tag:
                    author = tag.get_text(strip=True)
                    break

            return content, author

        except Exception as e:
            print("Extract error:", e)
            return "", "Unknown"

    articles = []

    # =========================
    # 1. TRY RSS FIRST
    # =========================
    try:
        r = requests.get(RSS_URL, headers=headers, timeout=15)
        soup = BeautifulSoup(r.content, "xml")

        items = soup.find_all("item")

        for item in items[:10]:
            title = item.title.text
            link = item.link.text

            content, author = extract_article(link)

            if len(content) > 300:
                articles.append({
                    "title": title,
                    "content": content,
                    "author": author
                })

            if len(articles) >= 6:
                return articles

    except Exception as e:
        print("RSS failed:", e)

    # =========================
    # 2. FALLBACK → HTML SCRAPE
    # =========================
    try:
        r = requests.get(BASE + "/opinion", headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        links = []

        for a in soup.find_all("a", href=True):
            href = a["href"]
            title = a.get_text(strip=True)

            if href.startswith("/") and len(title) > 25:
                full = BASE + href
                links.append((title, full))

        # deduplicate
        seen = set()
        clean = []
        for t, l in links:
            if l not in seen:
                seen.add(l)
                clean.append((t, l))

        for title, link in clean[:12]:
            content, author = extract_article(link)

            if len(content) > 300:
                articles.append({
                    "title": title,
                    "content": content,
                    "author": author
                })

            if len(articles) >= 6:
                return articles

    except Exception as e:
        print("HTML fallback failed:", e)

    # =========================
    # 3. HARD FALLBACK (NEVER EMPTY)
    # =========================
    if not articles:
        return [{
            "title": "Fallback: Could not fetch live articles",
            "content": "Your network or Dawn blocking is preventing scraping. Check connection or try again later.",
            "author": "System"
        }]

    return articles
# =========================
# ⚠️ EVERYTHING BELOW UNCHANGED
# =========================

ANALYTICAL_SENTENCES = [
    "Understanding this debate requires examining the broader geopolitical context.",
    "This issue reflects deeper tensions in global power politics.",
    "The article raises important questions about the structure of the international system.",
    "Analyzing this perspective helps highlight the link between theory and policy.",
    "This argument demonstrates the recurring tension between power and ethics in international affairs."
]

def generate_css_notes(article, mode):
    structure = "Use short analytical paragraph followed by structured bullet points." if mode=="Bullet Dominant Hybrid" else "Use paragraph-dominant analysis with limited structured bullets."

    prompt = f"""
You are a senior FPSC CSS examiner.

Create academy-style hybrid notes.

STRICT RULES:
- No hashtags
- No markdown symbols
- Clean headings
- Formal tone
- {structure}
- MUST include a section titled: Phrasal Verbs with Explanation
- Extract 5 relevant phrasal verbs from article
- Provide very short explanation
- Include 5 key vocabulary words with meanings
- Provide 5-10 line summary of article and don't mention any note in the end
- Occasionally add short analytical linking sentences between sections.
- Include one short "Examiner Insight" line where relevant.
- Possible Questions must resemble real CSS exam questions.
- Avoid AI style repetition and don't miss important data mentioned in articles.

STRUCTURE:
1. Context and Background
2. Core Issue
3. Key Arguments
4. Counter-Arguments
5. Important Facts
6. Analytical Evaluation
7. Way Forward
8. Possible Questions
9. Summary Box
10. Key Vocabulary
11. Phrasal Verbs with Explanation

Random analytical sentence bank (choose 1-2 lines randomly to insert between sections):
{random.sample(ANALYTICAL_SENTENCES, k=2)}

Article:
{article['content'][:6000]}
"""

    response = client.chat.completions.create(
        model=FAST_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content

# =========================
# UI (UNCHANGED)
# =========================
tab1, tab2, tab3 = st.tabs(["Fetch Opinions", "Generate Notes", "Daily Learning Capsule"])

# =========================
# TAB 1 — FETCH + SELECT ARTICLES
# =========================
with tab1:

    st.subheader("📰 Fetch Dawn Opinion Articles")

    if st.button("Fetch Top Opinions"):
        with st.spinner("Fetching latest articles..."):
            st.session_state["articles"] = scrape_opinions()

        if not st.session_state["articles"]:
            st.error("❌ No articles found! Try again.")
        else:
            st.success(f"✅ Fetched {len(st.session_state['articles'])} articles")

    # ---------- SHOW ARTICLES ----------
    if "articles" not in st.session_state:
        st.info("Click 'Fetch Top Opinions' to load articles.")
    elif not st.session_state["articles"]:
        st.warning("No articles available.")
    else:
        st.markdown("### 📌 Select Articles for Notes Generation")

        selected_articles = []

        for i, art in enumerate(st.session_state["articles"]):
            key = f"article_{i}"

            with st.container():
                col1, col2 = st.columns([1, 10])

                with col1:
                    checked = st.checkbox("", value=True, key=key)

                with col2:
                    st.markdown(f"**{art['title']}**")
                    st.caption(f"✍️ {art['author']}")

                    # Preview content
                    preview = art["content"][:300] + "..."
                    st.write(preview)

                st.divider()

            if checked:
                selected_articles.append(art)

        st.session_state["selected_articles"] = selected_articles

        # ---------- SUMMARY ----------
        st.success(f"📚 Selected {len(selected_articles)} articles for note generation")
