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
    articles = []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        # Step 1: Get opinion page
        res = requests.get("https://www.dawn.com/opinion", headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")

        candidates = []

        # Extract links
        for tag in soup.find_all("a", href=True):
            title = tag.get_text(strip=True)
            link = tag["href"]

            if "/opinion/" in link and len(title) > 20:
                full_url = link if link.startswith("http") else "https://www.dawn.com" + link
                candidates.append((title, full_url))

        # Remove duplicates
        seen = set()
        clean_articles = []
        for t, l in candidates:
            if l not in seen:
                seen.add(l)
                clean_articles.append((t, l))

        # Step 2: Fetch article content
        final_articles = []

        for title, url in clean_articles[:10]:
            try:
                page = requests.get(url, headers=headers, timeout=15)
                soup_page = BeautifulSoup(page.text, "html.parser")

                # Main content container
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

                if len(content) < 400:
                    continue

                # Author extraction
                author = "Unknown"
                for sel in [".byline__name", ".story__byline", ".author"]:
                    tag = soup_page.select_one(sel)
                    if tag:
                        author = tag.get_text(strip=True)
                        break

                final_articles.append({
                    "title": title,
                    "content": content,
                    "author": author
                })

                if len(final_articles) >= 6:
                    break

            except Exception as e:
                print("Skipping article:", e)
                continue

        return final_articles

    except Exception as e:
        print("Scraper failed:", e)
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
