# =========================
# CSS Academy AI System (Full Version, Articles PDF Restored + Capsule Upgrade)
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
if not api_key:
    st.error("Groq API key missing in secrets")
    st.stop()

client = Groq(api_key=api_key)
FAST_MODEL = "llama-3.1-8b-instant"

# =========================
# SCRAPER (UNCHANGED)
# =========================

# =========================
# RANDOM ANALYTICAL SENTENCES
# =========================
def scrape_opinions():
    
    url = "https://www.dawn.com/opinion"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }

    session = requests.Session()
    response = session.get(url, headers=headers)

    if response.status_code != 200:
        print("Failed main request")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    articles = []

    # =========================
    # 🥇 METHOD 1: Article tags
    # =========================
    cards = soup.find_all("article")

    for card in cards:
        a_tag = card.find("a", href=True)
        if not a_tag:
            continue

        title = a_tag.get_text(strip=True)
        link = a_tag["href"]

        if not title or len(title) < 15:
            continue

        articles.append((title, link))

    # =========================
    # 🥈 METHOD 2: Headings
    # =========================
    if len(articles) < 3:
        print("Fallback 1 activated")

        for tag in soup.select("h2 a, h3 a"):
            title = tag.get_text(strip=True)
            link = tag.get("href")

            if title and link:
                articles.append((title, link))

    # =========================
    # 🥉 METHOD 3: ALL LINKS FILTER
    # =========================
    if len(articles) < 3:
        print("Fallback 2 activated")

        for tag in soup.find_all("a", href=True):
            href = tag["href"]
            title = tag.get_text(strip=True)

            if "/news/" in href and len(title) > 20:
                articles.append((title, href))

    # =========================
    # 🔄 CLEAN + FETCH CONTENT
    # =========================
    final_articles = []
    seen = set()

    for title, link in articles:

        if len(final_articles) >= 6:
            break

        full_url = link if link.startswith("http") else "https://www.dawn.com" + link

        if full_url in seen:
            continue

        seen.add(full_url)

        try:
            page = session.get(full_url, headers=headers)
            soup_page = BeautifulSoup(page.text, "html.parser")

            paragraphs = soup_page.find_all("p")
            content = " ".join(
                p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)
            )

            if len(content) < 300:
                continue

            author_tag = soup_page.select_one(".byline__name, .story__byline")
            author = author_tag.get_text(strip=True) if author_tag else "Unknown"

            final_articles.append({
                "title": title,
                "content": content,
                "author": author
            })

            time.sleep(0.2)

        except Exception as e:
            print("Skipping:", e)
            continue

    return final_articles
    "Understanding this debate requires examining the broader geopolitical context.",
    "This issue reflects deeper tensions in global power politics.",
    "The article raises important questions about the structure of the international system.",
    "Analyzing this perspective helps highlight the link between theory and policy.",
    "This argument demonstrates the recurring tension between power and ethics in international affairs."
]

# =========================
# CSS NOTES GENERATION (UNCHANGED)
# =========================

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

    notes_text = response.choices[0].message.content
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
# DAILY LEARNING CAPSULE FUNCTIONS
# =========================

from datetime import datetime
import random

def learning_capsule():

    today = datetime.utcnow().strftime("%Y-%m-%d")
    seed = random.randint(1000,9999)

    prompt = f"""
Create a Daily Learning Capsule for CSS competitive exam preparation.

Date: {today}
Seed: {seed}

STRICT RULES:
- Only provide the sections listed below
- No introduction
- No conclusion
- End after Quote of the Day
- Keep responses concise
- Ensure today's capsule is DIFFERENT from typical textbook examples
- Do not repeat the data again,try to generate new

Sections Format EXACTLY like this:

Idiom of the Day
Meaning:
Example:

Word of the Day
Meaning:
Example:

Country Snapshot
Country:
Capital:
Currency:

Did You Know
(one surprising global fact)

Quote of the Day
(one quote from a historical figure)

Ensure all facts are globally verified and accurate.
"""

    res = client.chat.completions.create(
        model=FAST_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    text = res.choices[0].message.content.strip()

    if "Idiom of the Day" in text:
        text = text[text.index("Idiom of the Day"):]

    return text
#Capsule Text
def format_capsule_text(text):

    lines = text.split("\n")
    cleaned = []

    for line in lines:

        line = line.replace("**","").strip()

        if not line:
            cleaned.append("<br/>")
            continue

        if ":" in line:
            parts = line.split(":",1)
            line = f"<b>{parts[0]}</b>: {parts[1].strip()}"

        cleaned.append(line)

    return "<br/>".join(cleaned)


# =========================
# CAPSULE CACHE
# =========================
def get_daily_capsule():

    today_key = datetime.utcnow().strftime("%Y-%m-%d")

    if "capsule_cache" not in st.session_state:
        st.session_state["capsule_cache"] = {}

    if today_key not in st.session_state["capsule_cache"]:
        st.session_state["capsule_cache"][today_key] = learning_capsule()

    return st.session_state["capsule_cache"][today_key]
# =========================
# CAPSULE PDF GENERATION
# =========================
def generate_capsule_pdf():

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=70,
        leftMargin=70,
        topMargin=80,
        bottomMargin=60
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        alignment=1,
        fontSize=22,
        spaceAfter=25
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=13,
        leading=20,
        spaceAfter=12
    )

    elements = []

    today = datetime.utcnow().strftime("%d %B %Y")

    elements.append(Paragraph("Daily Learning Capsule", title_style))
    elements.append(Paragraph(today, body_style))
    elements.append(Spacer(1,20))

    capsule = get_daily_capsule()
    capsule_lines = format_capsule_text(capsule).split("<br/>")

    for line in capsule_lines:
        elements.append(Paragraph(line, body_style))

    doc.build(elements)

    buffer.seek(0)
    return buffer

#=========================
  #STREAMLIT UI
#=========================

tab1, tab2, tab3 = st.tabs(["Fetch Opinions", "Generate Notes", "Daily Learning Capsule"])

# ===== TAB 1 =====
with tab1:
    st.write("Articles found:", len(st.session_state.get("articles", [])))
    if st.button("Fetch Top Opinions"):
    with st.spinner("Fetching..."):
        st.session_state["articles"] = scrape_opinions()

    if not st.session_state["articles"]:
        st.error("No articles found! Fallback failed.")
    else:
        st.success("Fetched Successfully")

    # Display previews only if articles exist
    if "articles" in st.session_state and st.session_state["articles"]:
        selected_articles = []

        for i, art in enumerate(st.session_state["articles"]):
            key = f"article_{i}"  # unique key to maintain checkbox state
            if st.checkbox(f"{art['title']} - {art['author']}", value=True, key=key):
                st.write(art['content'][:400] + "...")
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

            with st.spinner("Generating..."):
                for art in st.session_state["selected_articles"]:
                    notes = generate_css_notes(art, mode)

                    results.append({
                        "title": art["title"],
                        "notes": notes,
                        "author": art["author"]
                    })

            st.session_state["notes"] = results
            st.success("Notes Generated")

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
    st.subheader("📘 Daily Learning Capsule")

    if st.button("Generate Capsule"):
        capsule = get_daily_capsule()
        st.session_state["capsule_display"] = capsule

    if "capsule_display" in st.session_state:
        capsule_text = format_capsule_text(st.session_state["capsule_display"])
        st.markdown(capsule_text, unsafe_allow_html=True)

