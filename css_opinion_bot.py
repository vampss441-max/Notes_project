# =========================
# CSS Academy AI System (Full Version, Articles PDF Restored + Capsule Upgrade)
# =========================

import streamlit as st
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import time
from openai import OpenAI
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

api_key = st.secrets["OPENAI_API_KEY"]
if not api_key:
    st.error("OpenAI API key missing in secrets")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
FAST_MODEL = "openai/gpt-oss-120b"

# =========================
# SCRAPER — reads articles.json from GitHub (scraped daily by GitHub Actions)
# GitHub Actions runs scrape_dawn.py on GitHub servers at 6AM PKT
# Streamlit fetches the result via raw.githubusercontent.com (always accessible)
# =========================


GITHUB_USER = "Vampss441-max"
GITHUB_REPO = "notes_project"
GITHUB_BRANCH = "main"

@st.cache_data(ttl=3600)  # cache for 1 hour
def scrape_opinions():
    json_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/articles.json"
    try:
        r = requests.get(json_url, timeout=15)
        r.raise_for_status()
        data = r.json()
        articles = data.get("articles", [])
        date = data.get("date", "")
        if articles:
            st.info(f"📅 Articles from: {date}")
        return articles
    except Exception as e:
        st.error(f"Could not load articles from GitHub: {e}")
        st.markdown(
            "**Setup required:** Add `scrape_dawn.py` and `.github/workflows/scrape.yml` "
            "to your repo, then run the workflow once manually from GitHub → Actions tab."
        )
        return []


ANALYTICAL_SENTENCES = [
    "Understanding this debate requires examining the broader geopolitical context.",
    "This issue reflects deeper tensions in global power politics.",
    "The article raises important questions about the structure of the international system.",
    "Analyzing this perspective helps highlight the link between theory and policy.",
    "This argument demonstrates the recurring tension between power and ethics in international affairs."]
# =========================
# CSS NOTES GENERATION (UNCHANGED)
# =========================

def generate_css_notes(article, mode):
    structure = "Use short analytical paragraph followed by structured bullet points using the • symbol." if mode=="Bullet Dominant Hybrid" else "Use paragraph-dominant analysis with limited structured bullets using the • symbol."

    prompt = f"""
You are a senior FPSC CSS examiner.

Create academy-style hybrid notes.

STRICT RULES:
- No hashtags
- No markdown symbols like ** or __
- Clean numbered headings only
- Use the bullet point symbol • for all lists
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

    # Retry with exponential backoff to handle rate limits
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=FAST_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=4000
            )
            break  # success — exit retry loop
        except Exception as e:
            error_str = str(e).lower()
            if "rate_limit" in error_str or "429" in error_str or "ratelimit" in error_str:
                if attempt < max_retries - 1:
                    wait_time = 60 * (attempt + 1)  # 60s, 120s, 180s, 240s
                    st.warning(f"⏳ Rate limit hit. Waiting {wait_time}s before retrying... (attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    st.error("❌ Rate limit exceeded after all retries. Please wait a few minutes and try again.")
                    raise
            else:
                raise  # non-rate-limit error — raise immediately

    notes_text = response.choices[0].message.content
    # Strip ■ separator character used by openai/gpt-oss-20b model
    notes_text = notes_text.replace("■", "-")
    cleaned_notes = "\n".join([line for line in notes_text.split("\n") if "Note: the phrasal verbs" not in line])
    return cleaned_notes

# =========================
# ORIGINAL ARTICLES PDF GENERATION RESTORED
# =========================
# FOOTER
# =========================
def add_footer(canvas_obj, doc):
    width, height = A4

    # Watermark Logo
    if os.path.exists("logo.png"):
        canvas_obj.saveState()
        canvas_obj.setFillAlpha(0.06)

        canvas_obj.drawImage(
            "logo.png",
            width/2 - 180,
            height/2 - 180,
            width=360,
            height=360,
            mask='auto'
        )

        canvas_obj.restoreState()

    # Footer Line
    canvas_obj.setStrokeColor(colors.black)
    canvas_obj.line(50, 35, width - 50, 35)

    # Footer Text
    canvas_obj.setFont("Times-Roman", 9)

    canvas_obj.drawString(
        50,
        20,
        f"Daily Opinions' Notes | {today}"
    )

    canvas_obj.drawRightString(
        width - 50,
        20,
        f"Page {doc.page}"
    )


# =========================
# PDF GENERATION
# =========================
def generate_pdf(notes_data, font_theme="Classic Serif"):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=65,
        leftMargin=65,
        topMargin=80,
        bottomMargin=60
    )

    elements = []

    styles = getSampleStyleSheet()

    base_font = "Times-Roman" if font_theme == "Classic Serif" else "Helvetica"
    bold_font = "Times-Bold" if font_theme == "Classic Serif" else "Helvetica-Bold"

    # =========================
    # STYLES
    # =========================
    article_title = ParagraphStyle(
        name="ArticleTitle",
        parent=styles["Heading2"],
        fontName=bold_font,
        fontSize=17,
        spaceBefore=18,
        spaceAfter=8
    )

    section_heading = ParagraphStyle(
        name="SectionHeading",
        parent=styles["Normal"],
        fontName=bold_font,
        fontSize=12,
        leading=16,
        spaceBefore=12,
        spaceAfter=6,
        textColor=colors.black,
        backColor=colors.HexColor("#FFF176")
    )

    body_style = ParagraphStyle(
        name="BodyStyle",
        parent=styles["Normal"],
        fontName=base_font,
        fontSize=11.5,
        leading=17,
        spaceAfter=6
    )

    summary_box = ParagraphStyle(
        name="SummaryBox",
        parent=styles["Normal"],
        fontName=base_font,
        fontSize=11,
        leading=14,
        backColor=colors.HexColor("#E0F7FA"),
        leftIndent=6,
        rightIndent=6,
        spaceBefore=4,
        spaceAfter=8
    )

    phrasal_style = ParagraphStyle(
        name="PhrasalStyle",
        parent=styles["Normal"],
        fontName=bold_font,
        fontSize=11,
        leading=14,
        backColor=colors.HexColor("#FFF3E0"),
        spaceBefore=4,
        spaceAfter=4
    )

    # =========================
    # COVER PAGE
    # =========================
    elements.append(Spacer(1, 1.5 * inch))

    if os.path.exists("logo.png"):
        img = RLImage("logo.png", width=3 * inch, height=3 * inch)
        img.hAlign = "CENTER"
        elements.append(img)

    elements.append(Spacer(1, 0.5 * inch))

    elements.append(Paragraph("Daily Opinions' Notes", article_title))

    elements.append(
        Paragraph(f"Dawn Newspaper | {today}", body_style)
    )

    elements.append(PageBreak())

    # =========================
    # TABLE OF CONTENTS
    # =========================
    toc_data = [["Title", "Author", "Page"]]

    for i, item in enumerate(notes_data):
        toc_data.append([
            item["title"],
            item["author"],
            str(i + 3)
        ])

    toc_table = Table(
        toc_data,
        colWidths=[3 * inch, 2 * inch, 0.8 * inch]
    )

    toc_table.setStyle(TableStyle([

        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FFF176")),

        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),

        ("FONTNAME", (0, 0), (-1, -1), base_font),

        ("FONTNAME", (0, 0), (-1, 0), bold_font),

        ("ALIGN", (2, 1), (2, -1), "CENTER")
    ]))

    elements.append(Paragraph("Table of Contents", article_title))
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(toc_table)
    elements.append(PageBreak())

    # =========================
    # CONTENT
    # =========================
    for item in notes_data:

        elements.append(Paragraph(item["title"], article_title))
        elements.append(
            Paragraph(f"Author: {item['author']}", body_style)
        )

        elements.append(Spacer(1, 0.2 * inch))

        bullet_buffer = []

        for line in item["notes"].split("\n"):

            clean_line = line.strip().replace("**", "")

            if not clean_line:
                elements.append(Spacer(1, 0.1 * inch))
                continue

            line_no_num = ''.join([
                c for c in clean_line
                if not c.isdigit() and c != '.'
            ]).strip()

            sections = [
                "context and background",
                "core issue",
                "key arguments",
                "counter-arguments",
                "important facts",
                "analytical evaluation",
                "way forward",
                "possible questions",
                "summary box",
                "key vocabulary",
                "phrasal verbs with explanation"
            ]

            if any(line_no_num.lower().startswith(sec) for sec in sections):

                if bullet_buffer:
                    elements.append(
                        ListFlowable(
                            bullet_buffer,
                            bulletType="bullet",
                            leftIndent=20
                        )
                    )
                    bullet_buffer = []

                style_to_use = summary_box if "summary box" in line_no_num.lower() else section_heading

                elements.append(
                    Paragraph(line_no_num, style_to_use)
                )

                continue

            # Vocabulary / Phrasal
            if ":" in clean_line:

                parts = clean_line.split(":", 1)

                term = parts[0].strip()
                explanation = parts[1].strip()

                elements.append(
                    Paragraph(
                        f"<b>{term}:</b> {explanation}",
                        phrasal_style
                    )
                )

                continue

            # Bullet points
            if clean_line.startswith("*") or clean_line[0].isdigit():

                bullet_text = clean_line.lstrip("*0123456789. ").strip()

                bullet_buffer.append(
                    ListItem(
                        Paragraph(bullet_text, body_style)
                    )
                )

                continue

            # Flush bullets
            if bullet_buffer:

                elements.append(
                    ListFlowable(
                        bullet_buffer,
                        bulletType="bullet",
                        leftIndent=20
                    )
                )

                bullet_buffer = []

            elements.append(
                Paragraph(clean_line, body_style)
            )

        elements.append(PageBreak())

    # =========================
    # BUILD PDF
    # =========================
    doc.build(
        elements,
        onFirstPage=add_footer,
        onLaterPages=add_footer
    )

    buffer.seek(0)

    return buffer

# =========================
# DAILY TOP 10 WORLD NEWS (replaces Daily Learning Capsule)
# Headlines are pulled live from reputable outlets' RSS feeds, so the AI can only
# choose from real, current reports. Sources shown in the post are attached by
# code (not written by the AI), so they can't be invented.
# =========================

import json
import re
from datetime import timedelta, timezone
from email.utils import parsedate_to_datetime

NEWS_FEEDS = {
    "BBC News": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "The Guardian": "https://www.theguardian.com/world/rss",
    "DW": "https://rss.dw.com/xml/rss-en-all",
    "NYT": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "NPR": "https://feeds.npr.org/1004/rss.xml",
    "France 24": "https://www.france24.com/en/rss",
    "Dawn": "https://www.dawn.com/feeds/home",
}

PAGE_NAME = "DailyCapsule"
NEWS_MAX_AGE_HOURS = 36
NEWS_ITEMS_PER_SOURCE = 8


def _clean_text(html_text):
    if not html_text:
        return ""
    text = BeautifulSoup(html_text, "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text)


@st.cache_data(ttl=1800)  # cache for 30 minutes
def fetch_world_headlines():
    """Return (items, failed_sources). Each item: {id, source, title, summary, link}"""
    items = []
    failed = []
    cutoff = datetime.utcnow() - timedelta(hours=NEWS_MAX_AGE_HOURS)
    headers = {"User-Agent": "Mozilla/5.0 (compatible; DailyLearningCapsuleBot/1.0)"}

    for source, url in NEWS_FEEDS.items():
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            root = ET.fromstring(r.content)
            count = 0
            for node in root.iter("item"):
                title = _clean_text(node.findtext("title"))
                link = (node.findtext("link") or "").strip()
                summary = _clean_text(node.findtext("description"))[:160]
                pub = node.findtext("pubDate")

                if pub:
                    try:
                        pub_dt = parsedate_to_datetime(pub)
                        if pub_dt.tzinfo is not None:
                            pub_dt = pub_dt.astimezone(timezone.utc).replace(tzinfo=None)
                        if pub_dt < cutoff:
                            continue
                    except Exception:
                        pass  # keep item if date can't be parsed

                if not title or not link:
                    continue

                items.append({
                    "id": len(items) + 1,
                    "source": source,
                    "title": title,
                    "summary": summary,
                    "link": link,
                })
                count += 1
                if count >= NEWS_ITEMS_PER_SOURCE:
                    break
            if count == 0:
                failed.append(source)
        except Exception:
            failed.append(source)

    return items, failed


def build_news_prompt(items, date_str):
    lines = [
        f"[{it['id']}] {it['source']} | {it['title']} | {it['summary']}"
        for it in items
    ]
    headlines_block = "\n".join(lines)

    return f"""
You are the news editor for the Facebook page "{PAGE_NAME}".
Today's date is {date_str}.

Below are real headlines published in the last 24-36 hours by reputable outlets.
Each line is: [id] Outlet | Headline | Short summary

TASK:
Pick the 10 most important WORLD news stories from this list only.

STRICT RULES:
- Use ONLY the information in the lines below. Never add facts, numbers, names or quotes that are not in them.
- Prefer stories reported by 2 or more different outlets. When several lines cover the same story, group their ids together.
- Rank by global impact, not clickbait.
- Give a balanced mix: politics, economy, science/technology, health, climate, conflicts/humanitarian. Include 1-2 stories from Pakistan or South Asia if available.
- No celebrity gossip, rumours, or graphic details.
- Neutral tone. Facts only, no opinions.
- Simple English. Each "what_happened" is 1-2 short sentences. "why_it_matters" is 1 short sentence.

Return ONLY valid JSON, no markdown fences, no extra text, in exactly this shape:
{{
  "stories": [
    {{
      "emoji": "one relevant emoji",
      "headline": "max 12 words",
      "what_happened": "1-2 simple sentences",
      "why_it_matters": "1 sentence",
      "ids": [list of line ids supporting this story]
    }}
  ],
  "takeaway": "2 short lines summarising the day"
}}

HEADLINES:
{headlines_block}
"""


def parse_news_json(raw):
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON found in model output")
    return json.loads(raw[start:end + 1])


def generate_world_news_post():
    """Returns (post_text, verification_rows, warnings)"""
    date_str = (datetime.utcnow() + timedelta(hours=5)).strftime("%d %B %Y")  # PKT
    warnings = []

    items, failed = fetch_world_headlines()
    if failed:
        warnings.append("Could not load: " + ", ".join(failed))
    if len(items) < 10:
        raise RuntimeError("Not enough live headlines could be loaded. Try again in a few minutes.")

    by_id = {it["id"]: it for it in items}
    prompt = build_news_prompt(items, date_str)

    max_retries = 3
    response = None
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=FAST_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=3000
            )
            break
        except Exception as e:
            error_str = str(e).lower()
            if ("rate_limit" in error_str or "429" in error_str or "ratelimit" in error_str) and attempt < max_retries - 1:
                wait_time = 60 * (attempt + 1)
                st.warning(f"⏳ Rate limit hit. Waiting {wait_time}s before retrying... (attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
            else:
                raise

    data = parse_news_json(response.choices[0].message.content)
    stories = data.get("stories", [])[:10]
    if not stories:
        raise RuntimeError("The model returned no stories. Please try again.")

    post_lines = [f"🌍 Top 10 World News | {date_str}", ""]
    verification = []

    for n, s in enumerate(stories, start=1):
        ids = [i for i in s.get("ids", []) if isinstance(i, int) and i in by_id]
        outlets = []
        for i in ids:
            if by_id[i]["source"] not in outlets:
                outlets.append(by_id[i]["source"])

        if not outlets:
            source_line = "Source: Not verified"
        elif len(outlets) == 1:
            source_line = f"Source: {outlets[0]} (single source)"
        else:
            source_line = "Source: " + ", ".join(outlets)

        post_lines.append(f"{n}. {s.get('emoji', '📰')} {s.get('headline', '').strip()}")
        post_lines.append(f"• What happened: {s.get('what_happened', '').strip()}")
        post_lines.append(f"• Why it matters: {s.get('why_it_matters', '').strip()}")
        post_lines.append(f"• {source_line}")
        post_lines.append("")

        for i in ids:
            verification.append({
                "story": n,
                "source": by_id[i]["source"],
                "title": by_id[i]["title"],
                "link": by_id[i]["link"],
            })

    takeaway = data.get("takeaway", "").strip()
    if takeaway:
        post_lines.append(f"💡 Quick Takeaway: {takeaway}")
        post_lines.append("")

    post_lines.append(f"Follow {PAGE_NAME} for daily learning and updates 📚")
    post_lines.append("")
    post_lines.append("#WorldNews #DailyNews #TopNews #Headlines #CurrentAffairs #DailyLearningCapsule")

    return "\n".join(post_lines), verification, warnings


#Streamlit ===== TAB 1 =====
tab1, tab2, tab3 = st.tabs(["Fetch Opinions", "Generate Notes", "Daily Top 10 News"])

with tab1:
    st.subheader("📰 Today's Dawn Opinion Articles")

    if st.button("🔄 Fetch Today's Opinions"):
        st.cache_data.clear()
        with st.spinner("Loading articles from GitHub..."):
            articles = scrape_opinions()
            st.session_state["articles"] = articles
            for i in range(len(articles)):
                st.session_state[f"article_{i}"] = True

        if not st.session_state.get("articles"):
            st.error("No articles found. Check GitHub Actions ran successfully.")
        else:
            st.success(f"✅ Fetched {len(st.session_state['articles'])} articles")

    if "articles" in st.session_state and st.session_state["articles"]:
        selected_articles = []
        st.markdown(f"**Select articles to include:**")
        for i, art in enumerate(st.session_state["articles"]):
            key = f"article_{i}"
            if st.checkbox(f"{art['title']} — {art['author']}", value=True, key=key):
                st.caption(art["content"][:250] + "...")
                selected_articles.append(art)
        st.session_state["selected_articles"] = selected_articles


# ===== TAB 2 =====
with tab2:
    mode = st.selectbox(
        "Select Notes Mode",
        ["Bullet Dominant Hybrid", "Paragraph Dominant Hybrid"]
    )

    font_theme = st.selectbox(
        "Select Font Theme",
        ["Classic Serif", "Modern Sans"]
    )

    # Save theme to session state
    st.session_state["font_theme"] = font_theme

    if "selected_articles" in st.session_state and st.session_state["selected_articles"]:
        if st.button("Generate CSS Notes"):
            results = []
            total = len(st.session_state["selected_articles"])
            progress = st.progress(0)

            for idx, art in enumerate(st.session_state["selected_articles"]):
                with st.spinner(f"Generating notes {idx+1}/{total}: {art['title'][:60]}..."):
                    # Clean encoding artifacts before sending to AI
                    clean_content = art["content"]
                    for bad_char in ["\u00ad", "\u200b", "\u200c", "\u200d", "\ufeff"]:
                        clean_content = clean_content.replace(bad_char, "")
                    clean_art = {**art, "content": clean_content}
                    notes = generate_css_notes(clean_art, mode)
                    if not notes or len(notes.strip()) < 100:
                        st.warning(f"Notes too short for '{art['title'][:50]}' — skipped")
                    else:
                        results.append({
                            "title": art["title"],
                            "notes": notes,
                            "author": art["author"]
                        })
                progress.progress((idx + 1) / total)
                if idx < total - 1:
                    # Longer pause before last article to avoid rate limit cutoff
                    wait = 30 if idx == total - 2 else 20
                    time.sleep(wait)

            st.session_state["notes"] = results
            st.success("✅ Notes Generated")

# =========================
# SHOW NOTES + DOWNLOAD PDF
# =========================

if "notes" in st.session_state:

    st.subheader("Generated CSS Notes")

    for item in st.session_state["notes"]:
        with st.expander(item["title"], expanded=True):
            st.markdown(item["notes"])

    font_theme = st.session_state.get("font_theme", "Classic Serif")

    pdf_bytes = generate_pdf(
        st.session_state["notes"],
        font_theme
    )

    st.download_button(
        "Download PDF",
        pdf_bytes,
        file_name=f"Daily_Opinion_Notes_{file_date}.pdf",
        mime="application/pdf"
    )

# ===== TAB 3 =====
with tab3:
    st.subheader("🌍 Daily Top 10 World News")
    st.caption("Built from live headlines of BBC, Al Jazeera, Guardian, DW, NYT, NPR, France 24 and Dawn.")

    if st.button("Generate Top 10 News"):
        with st.spinner("Collecting live headlines and writing your post..."):
            try:
                post, verification, warnings = generate_world_news_post()
                st.session_state["news_post"] = post
                st.session_state["news_verification"] = verification
                st.session_state["news_warnings"] = warnings
            except Exception as e:
                st.session_state.pop("news_post", None)
                st.error(f"Could not generate news: {e}")

    if "news_post" in st.session_state:
        for w in st.session_state.get("news_warnings", []):
            st.warning(w)

        st.text_area(
            "Facebook post (copy and paste)",
            st.session_state["news_post"],
            height=600
        )

        st.download_button(
            "Download as .txt",
            st.session_state["news_post"],
            file_name=f"Top10_World_News_{file_date}.txt",
            mime="text/plain"
        )

        with st.expander("🔎 Verification links (check before posting)"):
            for row in st.session_state.get("news_verification", []):
                st.markdown(f"**Story {row['story']}** — {row['source']}: [{row['title']}]({row['link']})")
