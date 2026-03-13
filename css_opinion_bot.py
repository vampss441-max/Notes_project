
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
from dotenv import load_dotenv

# =========================
# LOAD .ENV
# =========================
load_dotenv()

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

# Load Groq API key safely
api_key = st.secrets["GROQ_API_KEY"]
if not api_key:
    st.error("Groq API key is not set! Please add GROK_API_KEY in Streamlit Secrets.")
    st.stop()
client = Groq(api_key=api_key)

FAST_MODEL = "llama-3.1-8b-instant"

# =========================
# SCRAPER (ONLY OPINIONS)
# =========================
def scrape_opinions():
    url = "https://www.dawn.com/opinion"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    articles = []
    list_items = soup.find_all("h2", class_="story__title")

    for link_tag in list_items[:6]:  # Adjust number if needed
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

        time.sleep(0.1)  # Reduced sleep for faster fetching

    return articles

# =========================
# RANDOM ANALYTICAL SENTENCES (Bonus)
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

    # Full enhanced prompt including examiner insights and human-style improvements
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

    # Remove unnecessary AI-style phrasal verb notes
    cleaned_notes = "\n".join([line for line in notes_text.split("\n")
                               if "Note: the phrasal verbs" not in line])
    return cleaned_notes

# =========================
def learning_capsule():

    prompt = """
Create a Daily Learning Capsule:

Idiom of the Day
Meaning
Example sentence

Country – Capital – Currency

Do You Know?
Provide one interesting global fact.
keep it concise and educational.
Do NOT use markdown symbols like ** or #. Use plain headings and bullet points.
"""

    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}],
        temperature=0.4
    )

    return res.choices[0].message.content
    
# =========================
def highlighted_heading(text):

    style = ParagraphStyle("h", fontSize=13)

    table = Table([[Paragraph(f"<b>{text}</b>", style)]], colWidths=450)

    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),colors.yellow),
        ("BOX",(0,0),(-1,-1),0.8,colors.black),
        ("LEFTPADDING",(0,0),(-1,-1),10),
        ("RIGHTPADDING",(0,0),(-1,-1),10),
        ("TOPPADDING",(0,0),(-1,-1),6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))

    return table








# FOOTER
# =========================
def add_footer(canvas_obj, doc):
    width, height = A4

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

    canvas_obj.setStrokeColor(colors.black)
    canvas_obj.line(50, 35, width - 50, 35)
    canvas_obj.setFont("Times-Roman", 9)
    canvas_obj.drawString(50, 20, f"Daily Opinions' Notes | {today}")
    canvas_obj.drawRightString(width - 50, 20, f"Page {doc.page}")

# =========================
# PDF GENERATION
# =========================
def generate_pdf(notes_data, font_theme):

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=65, leftMargin=65, topMargin=80, bottomMargin=60)
    elements = []
    styles = getSampleStyleSheet()

    if font_theme == "Classic Serif":
        base_font = "Times-Roman"
        bold_font = "Times-Bold"
    else:
        base_font = "Helvetica"
        bold_font = "Helvetica-Bold"

    article_title = ParagraphStyle(
        name="ArticleTitle", parent=styles["Heading2"], fontName=bold_font,
        fontSize=17, spaceBefore=18, spaceAfter=8
    )

    section_heading = ParagraphStyle(
        name="SectionHeading", parent=styles["Normal"], fontName=bold_font,
        fontSize=12, leading=16, spaceBefore=12, spaceAfter=6,
        textColor=colors.black, backColor=colors.HexColor("#FFF176")
    )

    body_style = ParagraphStyle(
        name="BodyStyle", parent=styles["Normal"], fontName=base_font,
        fontSize=11.5, leading=17, spaceAfter=6
    )

    summary_box = ParagraphStyle(
        name="SummaryBox", parent=styles["Normal"], fontName=base_font,
        fontSize=11, leading=14, backColor=colors.HexColor("#E0F7FA"),
        leftIndent=6, rightIndent=6, spaceBefore=4, spaceAfter=8
    )

    phrasal_style = ParagraphStyle(
        name="PhrasalStyle", parent=styles["Normal"], fontName=bold_font,
        fontSize=11, leading=14, backColor=colors.HexColor("#FFF3E0"),
        leftIndent=0, rightIndent=0, spaceBefore=4, spaceAfter=4
    )

    # =========================
    # COVER
    # =========================
    elements.append(Spacer(1, 1.5 * inch))
    if os.path.exists("logo.png"):
        img = Image("logo.png", width=3*inch, height=3*inch)
        img.hAlign = 'CENTER'
        elements.append(img)
        elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph("Daily Opinions' Notes", article_title))
    elements.append(Paragraph(f"Dawn Newspaper | {today}", body_style))
    elements.append(PageBreak())

    # =========================
    # TABLE OF CONTENTS
    # =========================
    toc_data = [["Title", "Author", "Page"]]
    for i, item in enumerate(notes_data):
        toc_data.append([item["title"], item["author"], str(i + 3)])
    toc_table = Table(toc_data, colWidths=[3*inch, 2*inch, 0.8*inch])
    toc_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#FFF176")),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("FONTNAME", (0,0), (-1,-1), base_font),
        ("FONTNAME", (0,0), (-1,0), bold_font),
        ("ALIGN", (2,1), (2,-1), "CENTER")
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
        elements.append(Paragraph(f"Author: {item['author']}", body_style))
        elements.append(Spacer(1, 0.2 * inch))
        bullet_buffer = []

        for line in item["notes"].split("\n"):
            clean_line = line.strip().replace("**", "")
            if not clean_line:
                elements.append(Spacer(1, 0.1 * inch))
                continue

            # Remove leading numbers/dots for headings
            line_no_num = ''.join([c for c in clean_line if not c.isdigit() and c != '.']).strip()

            # Highlight section headings
            if any(line_no_num.lower().startswith(sec.lower()) for sec in [
                "context and background", "core issue", "key arguments", "counter-arguments",
                "important facts", "analytical evaluation", "way forward",
                "possible questions", "summary box", "key vocabulary", "phrasal verbs with explanation"
            ]):
                if bullet_buffer:
                    elements.append(ListFlowable(bullet_buffer, bulletType="bullet", leftIndent=20))
                    bullet_buffer = []
                style_to_use = summary_box if "summary box" in line_no_num.lower() else section_heading
                elements.append(Paragraph(line_no_num, style_to_use))
                continue

            # Highlight phrasal verbs or vocabulary
            if ":" in clean_line:
                parts = clean_line.split(":", 1)
                term = parts[0].strip()
                explanation = parts[1].strip()
                elements.append(Paragraph(f"<b>{term}:</b> {explanation}", phrasal_style))
                continue

            # Bulleted list items
            if clean_line.startswith("*") or clean_line[0].isdigit():
                bullet_text = clean_line.lstrip("*0123456789. ").strip()
                bullet_buffer.append(ListItem(Paragraph(bullet_text, body_style)))
                continue

            if bullet_buffer:
                elements.append(ListFlowable(bullet_buffer, bulletType="bullet", leftIndent=20))
                bullet_buffer = []

            elements.append(Paragraph(clean_line, body_style))

        elements.append(PageBreak())
    
    capsule = learning_capsule()

    elements.append(highlighted_heading("Daily Learning Capsule"))

    capsule_table = Table(
        [[Paragraph(format_capsule_text(capsule), body_style)]],
        colWidths=450)

    capsule_table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#E0F7FA")),
        ("BOX",(0,0),(-1,-1),1,colors.black),
        ("LEFTPADDING",(0,0),(-1,-1),12),
        ("RIGHTPADDING",(0,0),(-1,-1),12),
        ("TOPPADDING",(0,0),(-1,-1),10),
        ("BOTTOMPADDING",(0,0),(-1,-1),10),]))

    elements.append(Spacer(1,10))
    elements.append(capsule_table)
    elements.append(PageBreak())
        

    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
    buffer.seek(0)
    return buffer

# ========================
# =========================
# STREAMLIT UI
# =========================
tab1, tab2 = st.tabs(["Fetch Opinions", "Generate Notes"])

with tab1:
    if st.button("Fetch Top Opinions"):
        with st.spinner("Fetching..."):
            st.session_state["articles"] = scrape_opinions()
            st.success("Fetched Successfully")

    if "articles" in st.session_state:
        st.subheader("Preview & Select Articles")
        selected_articles = []
        for i, art in enumerate(st.session_state["articles"]):
            if st.checkbox(f"{art['title']} - {art['author']}", value=True):
                st.write(art['content'][:400] + "...")
                selected_articles.append(art)
        st.session_state["selected_articles"] = selected_articles

with tab2:
    mode = st.selectbox("Select Notes Mode", ["Bullet Dominant Hybrid", "Paragraph Dominant Hybrid"])
    font_theme = st.selectbox("Select Font Theme", ["Classic Serif", "Modern Sans"])

    if "selected_articles" in st.session_state and st.session_state["selected_articles"]:
        if st.button("Generate CSS Notes"):
            results = []
            with st.spinner("Generating..."):
                for art in st.session_state["selected_articles"]:
                    notes = generate_css_notes(art, mode)
                    results.append({"title": art["title"], "notes": notes, "author": art["author"]})
                st.session_state["notes"] = results
            st.success("Notes Generated")

    # =========================
# PROFESSIONAL NOTES DISPLAY
# =========================
if "notes" in st.session_state:

    st.subheader("📘 Generated CSS Academy Notes")

    for i, item in enumerate(st.session_state["notes"]):

        with st.expander(f"📰 {item['title']}  |  ✍️ {item['author']}", expanded=True):

            formatted_notes = item["notes"]

            # Convert bullet symbols for markdown
            formatted_notes = formatted_notes.replace("* ", "- ")
            formatted_notes = formatted_notes.replace("• ", "- ")

            # Render nicely formatted markdown
            st.markdown(formatted_notes)

            # Copy button
            st.code(item["notes"], language="markdown")

            st.divider()

    # PDF download still available
    pdf_buffer = generate_pdf(st.session_state["notes"], font_theme)

    st.download_button(
        label="📥 Download Professional PDF",
        data=pdf_buffer,
        file_name=f"Daily_Opinion_Notes_{file_date}.pdf",
        mime="application/pdf"
    )
















