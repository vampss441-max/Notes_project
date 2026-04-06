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
    from datetime import datetime

    RSS_URL = "https://www.dawn.com/feeds/opinion"

    try:
        res = requests.get(RSS_URL, timeout=15)
        soup = BeautifulSoup(res.content, "xml")

        items = soup.find_all("item")

        articles = []

        for item in items[:12]:  # take more to filter later
            title = item.title.text
            link = item.link.text

            try:
                page = requests.get(link, timeout=15)
                soup_page = BeautifulSoup(page.text, "html.parser")

                # Main content
                content_div = soup_page.find("div", class_="story__content")

                if content_div:
                    paragraphs = content_div.find_all("p")
                else:
                    paragraphs = soup_page.find_all("p")

                content = " ".join(
                    p.get_text(strip=True)
                    for p in paragraphs
                    if p.get_text(strip=True)
                )

                # Skip weak articles
                if len(content) < 300:
                    continue

                # Author
                author = "Unknown"
                for sel in [".byline__name", ".story__byline", ".author"]:
                    tag = soup_page.select_one(sel)
                    if tag:
                        author = tag.get_text(strip=True)
                        break

                articles.append({
                    "title": title,
                    "content": content,
                    "author": author
                })

                if len(articles) >= 6:
                    break

            except Exception as e:
                print("Skipping:", e)
                continue

        return articles

    except Exception as e:
        print("RSS error:", e)
        return []
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
