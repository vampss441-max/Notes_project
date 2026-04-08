# =========================
# CSS Academy AI System — FIXED & COMPLETE
# =========================

import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import random
import io
import os
from datetime import datetime

from groq import Groq

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    ListFlowable, ListItem, Table, TableStyle, HRFlowable
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# =========================
# DATE
# =========================
today = datetime.now().strftime("%d %B %Y")
file_date = datetime.now().strftime("%d-%m-%Y")

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Daily Opinions' Notes", layout="wide")
st.title("🗞️ CSS Daily Opinion Notes")
st.caption(f"📅 {today}")

api_key = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=api_key)
FAST_MODEL = "llama-3.1-8b-instant"

# =========================
# SCRAPER — Tribune (robust)
# =========================
def scrape_opinions():
    BASE = "https://tribune.com.pk"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        res = requests.get(f"{BASE}/opinion", headers=headers, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        articles = []
        seen_links = set()

        # Collect candidate links
        candidates = []
        for tag in soup.select("h2 a, h3 a, h4 a, .story-title a, .article-title a"):
            title = tag.get_text(strip=True)
            link = tag.get("href", "")
            if not title or not link or len(title) < 15:
                continue
            full_link = link if link.startswith("http") else BASE + link
            if full_link in seen_links:
                continue
            seen_links.add(full_link)
            candidates.append((title, full_link))

        for title, full_link in candidates:
            if len(articles) >= 6:
                break
            try:
                time.sleep(random.uniform(1.0, 2.5))  # polite delay
                page = requests.get(full_link, headers=headers, timeout=20)
                soup_page = BeautifulSoup(page.text, "html.parser")

                # Extract article body
                body_selectors = [
                    ".story-content", ".article-content",
                    ".entry-content", "#story-content", "article"
                ]
                body = None
                for sel in body_selectors:
                    body = soup_page.select_one(sel)
                    if body:
                        break

                if body:
                    paragraphs = body.find_all("p")
                else:
                    paragraphs = soup_page.find_all("p")

                content = " ".join(
                    p.get_text(strip=True) for p in paragraphs
                    if len(p.get_text(strip=True)) > 40
                )

                if len(content) < 400:
                    continue

                # Author
                author = "Unknown"
                for sel in [".author-name", ".author", ".byline", "[rel='author']"]:
                    tag = soup_page.select_one(sel)
                    if tag:
                        author = tag.get_text(strip=True)
                        break

                articles.append({
                    "title": title,
                    "content": content,
                    "author": author,
                    "url": full_link
                })

            except Exception as e:
                st.warning(f"Skipped one article: {e}")
                continue

        return articles

    except Exception as e:
        st.error(f"Tribune scrape failed: {e}")
        return []


# =========================
# ANALYTICAL SENTENCES
# =========================
ANALYTICAL_SENTENCES = [
    "Understanding this debate requires examining the broader geopolitical context.",
    "This issue reflects deeper tensions in global power politics.",
    "The article raises important questions about the structure of the international system.",
    "Analyzing this perspective helps highlight the link between theory and policy.",
    "This argument demonstrates the recurring tension between power and ethics in international affairs.",
    "The writer's argument can be evaluated through the lens of structural realism.",
    "This reflects a recurring pattern in South Asian geopolitical discourse.",
    "A critical reading reveals both the strengths and limitations of this viewpoint.",
]


# =========================
# GENERATE NOTES (AI)
# =========================
def generate_css_notes(article, mode):
    structure = (
        "Use short analytical paragraphs followed by structured bullet points."
        if mode == "Bullet Dominant Hybrid"
        else "Use paragraph-dominant analysis with limited structured bullets."
    )

    prompt = f"""
You are a senior FPSC CSS examiner and note-maker.

Create academy-style hybrid CSS notes from the article below.

STRICT RULES:
- No hashtags (#)
- No markdown symbols (**, __, etc.)
- Use clean numbered headings only
- Formal, academic tone
- {structure}
- MUST include a section: Phrasal Verbs with Explanation
- Extract 5 relevant phrasal verbs from the article and explain each briefly
- Include 5 key vocabulary words with meanings
- Provide a 5–10 line summary at the end
- Occasionally add short analytical linking sentences between sections
- Include one short "Examiner Insight" line where relevant
- Possible Questions must resemble real CSS exam questions
- Avoid AI-style filler and repetition
- Do not omit important facts, statistics, or names from the article

STRUCTURE:
1. Context and Background
2. Core Issue
3. Key Arguments
4. Counter-Arguments
5. Important Facts and Data
6. Analytical Evaluation
7. Way Forward
8. Possible CSS Exam Questions
9. Summary Box
10. Key Vocabulary
11. Phrasal Verbs with Explanation

Random analytical sentences to insert between 1–2 sections:
{random.sample(ANALYTICAL_SENTENCES, k=2)}

Article Title: {article['title']}
Author: {article['author']}

Article Content:
{article['content'][:6000]}
"""

    response = client.chat.completions.create(
        model=FAST_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.35,
    )
    return response.choices[0].message.content


# =========================
# DAILY LEARNING CAPSULE (AI)
# =========================
def get_daily_capsule():
    prompt = f"""
You are a CSS exam coach. Today is {today}.

Generate a structured Daily Learning Capsule for CSS aspirants. Include:

1. Word of the Day — one advanced English word with meaning, usage example, and origin
2. Idiom of the Day — one idiom with meaning and example sentence
3. Phrasal Verb of the Day — one phrasal verb with meaning and example
4. CSS Fact of the Day — one important current affairs or Pakistan Studies fact
5. Essay Tip of the Day — one practical writing tip for CSS essay paper
6. Motivational Quote — a short, powerful quote for CSS aspirants

Keep the tone formal yet encouraging. No markdown symbols or hashtags.
Use numbered headings only.
"""

    response = client.chat.completions.create(
        model=FAST_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )
    return response.choices[0].message.content


# =========================
# FORMAT CAPSULE TEXT
# =========================
def format_capsule_text(raw_text):
    """Convert plain numbered text into styled HTML for Streamlit."""
    lines = raw_text.strip().split("\n")
    html_parts = []
    for line in lines:
        line = line.strip()
        if not line:
            html_parts.append("<br>")
        elif line[0].isdigit() and len(line) > 2 and line[1] in ".):":
            # Heading line
            html_parts.append(
                f'<p style="font-size:1.05rem;font-weight:700;'
                f'color:#1a3c5e;margin-top:1rem;margin-bottom:0.2rem;">{line}</p>'
            )
        else:
            html_parts.append(
                f'<p style="margin:0.15rem 0;line-height:1.6;color:#2c2c2c;">{line}</p>'
            )
    return "\n".join(html_parts)


# =========================
# PDF GENERATOR
# =========================
def generate_pdf(notes_list, font_theme="Classic Serif"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.8 * inch,
        leftMargin=0.8 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.9 * inch,
    )

    # ---- Font selection ----
    if font_theme == "Modern Sans":
        body_font = "Helvetica"
        title_font = "Helvetica-Bold"
    else:  # Classic Serif
        body_font = "Times-Roman"
        title_font = "Times-Bold"

    # ---- Styles ----
    heading_style = ParagraphStyle(
        "heading",
        fontName=title_font,
        fontSize=13,
        textColor=colors.HexColor("#1a3c5e"),
        spaceAfter=6,
        spaceBefore=14,
        leading=16,
    )
    subheading_style = ParagraphStyle(
        "subheading",
        fontName=title_font,
        fontSize=11,
        textColor=colors.HexColor("#2e6da4"),
        spaceAfter=4,
        spaceBefore=10,
        leading=14,
    )
    body_style = ParagraphStyle(
        "body",
        fontName=body_font,
        fontSize=10,
        leading=15,
        spaceAfter=5,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor("#1e1e1e"),
    )
    meta_style = ParagraphStyle(
        "meta",
        fontName=body_font,
        fontSize=9,
        textColor=colors.HexColor("#666666"),
        spaceAfter=8,
    )
    cover_title_style = ParagraphStyle(
        "cover_title",
        fontName=title_font,
        fontSize=22,
        textColor=colors.HexColor("#0d2b45"),
        alignment=TA_CENTER,
        spaceAfter=10,
    )
    cover_sub_style = ParagraphStyle(
        "cover_sub",
        fontName=body_font,
        fontSize=12,
        textColor=colors.HexColor("#3a6ea5"),
        alignment=TA_CENTER,
        spaceAfter=6,
    )

    story = []

    # ---- Cover Page ----
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("CSS Academy", cover_title_style))
    story.append(Paragraph("Daily Opinions' Notes", cover_title_style))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(f"Date: {today}", cover_sub_style))
    story.append(Paragraph(f"Articles Covered: {len(notes_list)}", cover_sub_style))
    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(width="80%", thickness=1.5, color=colors.HexColor("#1a3c5e"), hAlign="CENTER"))
    story.append(Spacer(1, 0.2 * inch))
    story.append(
        Paragraph(
            "Prepared with AI-assisted analysis for CSS/PMS examination preparation.",
            meta_style,
        )
    )
    story.append(PageBreak())

    # ---- Articles ----
    for i, item in enumerate(notes_list, 1):
        # Article header
        story.append(Paragraph(f"Article {i}", subheading_style))
        story.append(Paragraph(item["title"], heading_style))
        story.append(Paragraph(f"Author: {item.get('author', 'Unknown')}", meta_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
        story.append(Spacer(1, 0.15 * inch))

        # Notes content — split by lines, detect headings
        lines = item["notes"].split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.08 * inch))
                continue

            # Detect numbered section headings like "1. Context and Background"
            is_heading = (
                len(line) < 80
                and line[0].isdigit()
                and len(line) > 2
                and line[1] in ".)"
            )
            if is_heading:
                story.append(Paragraph(line, subheading_style))
            elif line.startswith("-") or line.startswith("•"):
                story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;{line}", body_style))
            else:
                story.append(Paragraph(line, body_style))

        story.append(PageBreak())

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


# =========================
# TABS
# =========================
tab1, tab2, tab3 = st.tabs([
    "📰 Fetch Opinions",
    "🧠 Generate Notes",
    "📘 Daily Learning Capsule",
])

# =========================
# TAB 1 — FETCH + SELECT
# =========================
with tab1:
    st.subheader("Tribune Opinion Articles")

    if st.button("🔄 Fetch Top Opinions"):
        with st.spinner("Fetching articles from Tribune..."):
            articles = scrape_opinions()
            st.session_state["articles"] = articles
            for i in range(len(articles)):
                st.session_state[f"article_{i}"] = True

        if not articles:
            st.error("❌ No articles found. Tribune may have changed its layout. Try again later.")
        else:
            st.success(f"✅ Fetched {len(articles)} articles")

    if "articles" not in st.session_state:
        st.info("👆 Click 'Fetch Top Opinions' to load today's articles.")
    elif not st.session_state["articles"]:
        st.warning("No articles available.")
    else:
        st.markdown("### Select Articles for Notes Generation")
        selected_articles = []

        for i, art in enumerate(st.session_state["articles"]):
            key = f"article_{i}"
            with st.container():
                col1, col2 = st.columns([1, 10])
                with col1:
                    checked = st.checkbox("", key=key)
                with col2:
                    st.markdown(f"**{art['title']}**")
                    st.caption(f"✍️ {art['author']}  |  🔗 [Read original]({art.get('url', '#')})")
                    st.write(art["content"][:300] + "...")
                st.divider()
            if checked:
                selected_articles.append(art)

        st.session_state["selected_articles"] = selected_articles
        st.success(f"📚 {len(selected_articles)} article(s) selected")

# =========================
# TAB 2 — GENERATE NOTES
# =========================
with tab2:
    st.subheader("Generate CSS Notes")

    mode = st.selectbox(
        "Notes Mode",
        ["Bullet Dominant Hybrid", "Paragraph Dominant Hybrid"],
        help="Bullet Dominant = more structured lists. Paragraph Dominant = more prose."
    )
    font_theme = st.selectbox("PDF Font Theme", ["Classic Serif", "Modern Sans"])
    st.session_state["font_theme"] = font_theme

    if "selected_articles" not in st.session_state or not st.session_state["selected_articles"]:
        st.warning("⚠️ Please select at least one article from Tab 1 first.")
    else:
        if st.button("⚡ Generate CSS Notes"):
            results = []
            progress = st.progress(0)
            total = len(st.session_state["selected_articles"])

            for idx, art in enumerate(st.session_state["selected_articles"]):
                with st.spinner(f"Generating notes for: {art['title'][:60]}..."):
                    notes = generate_css_notes(art, mode)
                    results.append({
                        "title": art["title"],
                        "author": art["author"],
                        "notes": notes,
                    })
                progress.progress((idx + 1) / total)

            st.session_state["notes"] = results
            st.success("✅ Notes generated successfully!")

    # ---- Display + Download ----
    if "notes" in st.session_state and st.session_state["notes"]:
        st.subheader("📘 Generated Notes")

        for item in st.session_state["notes"]:
            with st.expander(f"📄 {item['title']}", expanded=True):
                st.markdown(f"**Author:** {item['author']}")
                st.text(item["notes"])

        # PDF download
        with st.spinner("Building PDF..."):
            pdf_bytes = generate_pdf(
                st.session_state["notes"],
                st.session_state.get("font_theme", "Classic Serif"),
            )

        st.download_button(
            label="⬇️ Download PDF",
            data=pdf_bytes,
            file_name=f"Daily_Opinion_Notes_{file_date}.pdf",
            mime="application/pdf",
        )

# =========================
# TAB 3 — CAPSULE
# =========================
with tab3:
    st.subheader("Daily Learning Capsule")
    st.caption("A quick daily dose of vocabulary, facts, and exam tips.")

    if st.button("✨ Generate Today's Capsule"):
        with st.spinner("Generating capsule..."):
            capsule = get_daily_capsule()
            st.session_state["capsule_display"] = capsule

    if "capsule_display" in st.session_state:
        capsule_html = format_capsule_text(st.session_state["capsule_display"])
        st.markdown(capsule_html, unsafe_allow_html=True)

        # Also offer plain text download
        st.download_button(
            label="⬇️ Download Capsule as Text",
            data=st.session_state["capsule_display"],
            file_name=f"Daily_Capsule_{file_date}.txt",
            mime="text/plain",
        )
