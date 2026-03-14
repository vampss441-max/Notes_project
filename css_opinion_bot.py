# =========================
# CSS Academy AI System (Enhanced Full Version)
# =========================

import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
from groq import Groq
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Image, ListFlowable, ListItem, Table, TableStyle
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
st.title("🗞 Dawn Opinion System")

api_key = st.secrets["GROQ_API_KEY"]

if not api_key:
    st.error("Groq API key missing.")
    st.stop()

client = Groq(api_key=api_key)

FAST_MODEL = "llama-3.1-8b-instant"

# =========================
# SCRAPER
# =========================

def scrape_opinions():

    url = "https://www.dawn.com/opinion"
    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")

    articles = []

    list_items = soup.find_all("h2", class_="story__title")

    for link_tag in list_items[:6]:

        title = link_tag.text.strip()
        article_url = link_tag.find("a")["href"]

        article_page = requests.get(article_url)
        article_soup = BeautifulSoup(article_page.text, "html.parser")

        paragraphs = article_soup.find_all("p")

        content = " ".join([p.text for p in paragraphs])

        author_tag = article_soup.select_one(".byline__name")

        if author_tag:
            author = author_tag.get_text(strip=True)
        else:
            alt_author = article_soup.select_one(".story__byline")
            author = alt_author.get_text(strip=True) if alt_author else "Unknown"

        articles.append({
            "title": title,
            "content": content,
            "author": author
        })

        time.sleep(0.1)

    return articles


# =========================
# RANDOM ANALYTICAL SENTENCES
# =========================

ANALYTICAL_SENTENCES = [
    "Understanding this debate requires examining the broader geopolitical context.",
    "This issue reflects deeper tensions in global power politics.",
    "The article raises important questions about the structure of the international system.",
    "Analyzing this perspective helps highlight the link between theory and policy.",
    "This argument demonstrates the recurring tension between power and ethics in international affairs."
]


# =========================
# CSS NOTES GENERATION
# =========================
def generate_css_notes(article, mode):

    structure = "Use short analytical paragraph followed by structured bullet points." \
        if mode=="Bullet Dominant Hybrid" \
        else "Use paragraph-dominant analysis with limited structured bullets."

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
- Provide 5-10 line summary of article
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

    cleaned_notes = "\n".join([
        line for line in notes_text.split("\n")
        if "Note: the phrasal verbs" not in line
    ])

    return cleaned_notes


# =========================
# LEARNING CAPSULE
# =========================

def learning_capsule():

    today = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""
Create a Daily Learning Capsule for CSS students.

Date: {today}

Sections:

Idiom of the Day
Meaning
Example sentence

Word of the Day
Meaning
Example sentence

Country Snapshot
Country
Capital
Currency

Did You Know
One surprising fact.

Quote of the Day
"""

    res = client.chat.completions.create(
        model=FAST_MODEL,
        messages=[{"role":"user","content":prompt}],
        temperature=1
    )

    return res.choices[0].message.content


# =========================
# CAPSULE CACHE
# =========================

def get_daily_capsule():

    today_key = datetime.now().strftime("%Y-%m-%d")

    if "capsule_date" not in st.session_state or st.session_state["capsule_date"] != today_key:

        st.session_state["capsule"] = learning_capsule()
        st.session_state["capsule_date"] = today_key

    return st.session_state["capsule"]


# =========================
# FORMAT CAPSULE TEXT
# =========================

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
            line = f"<b>{parts[0]}</b>: {parts[1]}"

        cleaned.append(line)

    return "<br/>".join(cleaned)


# =========================
# FOOTER
# =========================

def add_footer(canvas_obj, doc):

    width, height = A4

    canvas_obj.setStrokeColor(colors.black)
    canvas_obj.line(50, 35, width-50, 35)

    canvas_obj.setFont("Times-Roman",9)

    canvas_obj.drawString(50,20,f"Daily Opinions' Notes | {today}")

    canvas_obj.drawRightString(width-50,20,f"Page {doc.page}")


# =========================
# PDF GENERATION
# =========================

def generate_pdf(notes_data, font_theme):

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

    base_font = "Times-Roman"
    bold_font = "Times-Bold"

    if font_theme == "Modern Sans":
        base_font = "Helvetica"
        bold_font = "Helvetica-Bold"

    article_title = ParagraphStyle(
        "Title",
        parent=styles["Heading2"],
        fontName=bold_font,
        fontSize=17
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName=base_font,
        fontSize=11.5,
        leading=16
    )

    section_style = ParagraphStyle(
        "Section",
        parent=styles["Normal"],
        fontName=bold_font,
        fontSize=12,
        backColor=colors.HexColor("#FFF176")
    )

    # COVER
    elements.append(Spacer(1,1.5*inch))

    elements.append(Paragraph("Daily Opinions' Notes",article_title))
    elements.append(Paragraph(f"Dawn Newspaper | {today}",body_style))

    elements.append(PageBreak())

    # CONTENT

    SECTIONS = [
        "Context and Background",
        "Core Issue",
        "Key Arguments",
        "Counter-Arguments",
        "Important Facts",
        "Analytical Evaluation",
        "Way Forward",
        "Possible Questions",
        "Summary Box",
        "Key Vocabulary",
        "Phrasal Verbs with Explanation"
    ]

    for item in notes_data:

        elements.append(Paragraph(item["title"],article_title))
        elements.append(Paragraph(f"Author: {item['author']}",body_style))

        bullet_buffer = []

        for line in item["notes"].split("\n"):

            line=line.strip()

            if not line:
                continue

            if any(line.lower().startswith(s.lower()) for s in SECTIONS):

                if bullet_buffer:
                    elements.append(ListFlowable(bullet_buffer,bulletType="bullet"))
                    bullet_buffer=[]

                elements.append(Paragraph(line,section_style))
                continue

            if line.startswith("*") or line.startswith("-") or line.startswith("•") or line[:2].isdigit():

                text=line.lstrip("*-•0123456789. ")

                bullet_buffer.append(
                    ListItem(Paragraph(text,body_style))
                )

                continue

            if bullet_buffer:
                elements.append(ListFlowable(bullet_buffer,bulletType="bullet"))
                bullet_buffer=[]

            elements.append(Paragraph(line,body_style))

        elements.append(PageBreak())

    # CAPSULE

    capsule=get_daily_capsule()

    capsule_table = Table(
        [[Paragraph(format_capsule_text(capsule),body_style)]],
        colWidths=450
    )

    capsule_table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#E3F2FD")),
        ("BOX",(0,0),(-1,-1),1,colors.black),
        ("LEFTPADDING",(0,0),(-1,-1),14),
        ("RIGHTPADDING",(0,0),(-1,-1),14),
        ("TOPPADDING",(0,0),(-1,-1),12),
        ("BOTTOMPADDING",(0,0),(-1,-1),12)
    ]))

    elements.append(Paragraph("Daily Learning Capsule",article_title))
    elements.append(Spacer(1,10))
    elements.append(capsule_table)

    doc.build(elements,onFirstPage=add_footer,onLaterPages=add_footer)

    buffer.seek(0)

    return buffer


# =========================
# STREAMLIT UI
# =========================

tab1, tab2 = st.tabs(["Fetch Opinions","Generate Notes"])


with tab1:

    if st.button("Fetch Top Opinions"):

        with st.spinner("Fetching..."):

            st.session_state["articles"] = scrape_opinions()

        st.success("Fetched Successfully")

    if "articles" in st.session_state:

        st.subheader("Preview Articles")

        selected=[]

        for art in st.session_state["articles"]:

            if st.checkbox(f"{art['title']} - {art['author']}",value=True):

                st.write(art["content"][:400]+"...")

                selected.append(art)

        st.session_state["selected_articles"]=selected


with tab2:

    mode = st.selectbox(
        "Notes Mode",
        ["Bullet Dominant Hybrid","Paragraph Dominant Hybrid"]
    )

    font_theme = st.selectbox(
        "Font Theme",
        ["Classic Serif","Modern Sans"]
    )

    if "selected_articles" in st.session_state:

        if st.button("Generate CSS Notes"):

            results=[]

            for art in st.session_state["selected_articles"]:

                notes = generate_css_notes(art,mode)

                results.append({
                    "title":art["title"],
                    "notes":notes,
                    "author":art["author"]
                })

            st.session_state["notes"]=results

            st.success("Notes Generated")


if "notes" in st.session_state:

    st.subheader("Generated CSS Notes")

    for item in st.session_state["notes"]:

        with st.expander(item["title"],expanded=True):

            st.markdown(item["notes"])

    pdf_buffer = generate_pdf(
        st.session_state["notes"],
        font_theme
    )

    st.download_button(
        "Download PDF",
        pdf_buffer,
        file_name=f"Daily_Opinion_Notes_{file_date}.pdf",
        mime="application/pdf"
    )
