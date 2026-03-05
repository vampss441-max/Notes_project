# =========================
# CSS Academy AI System (Clean PDF Version + Master Book)
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
from dotenv import load_dotenv

# =========================
# LOAD ENV
# =========================
load_dotenv()

# =========================
# DATE
# =========================
today = datetime.now().strftime("%d %B %Y")
file_date = datetime.now().strftime("%d-%m-%Y")
master_book_file = "CSS_Academy_Master_Book.pdf"

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Daily Opinions' Notes", layout="wide")
st.title("CSS AI Examiner + Dawn Opinion System")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("Groq API key is not set! Please set GROQ_API_KEY in your environment.")
    st.stop()
client = Groq(api_key=GROQ_API_KEY)
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
        author = author_tag.get_text(strip=True) if author_tag else \
                 article_soup.select_one(".story__byline").get_text(strip=True) if article_soup.select_one(".story__byline") else "Unknown"
        articles.append({"title": title, "content": content, "author": author})
        time.sleep(0.1)
    return articles

# =========================
# CSS NOTES GENERATION
# =========================
def generate_css_notes(article, mode):
    structure = "Use short analytical paragraph followed by structured bullet points." \
        if mode=="Bullet Dominant Hybrid" else "Use paragraph-dominant analysis with limited structured bullets."
    prompt = f"""
You are a senior FPSC CSS examiner.  

Create academy-style hybrid notes.  

STRICT RULES:
- No hashtags, no markdown
- Formal tone
- {structure}
- MUST include: Phrasal Verbs with Explanation, Key Vocabulary, Urdu Summary
- Extract 5 phrasal verbs if present (otherwise skip)
- Include 5 key vocabulary words
- Add CSS paper linkage tags
- 3–5 line summary

STRUCTURE:
1. Context and Background
2. Core Issue
3. Key Arguments
4. Counter-Arguments
5. Important Facts
6. CSS Linkages
7. Analytical Evaluation
8. Way Forward
9. Possible Questions
10. Summary Box
11. Key Vocabulary
12. Phrasal Verbs with Explanation
13. Urdu Summary

Article:
{article['content'][:5000]}
"""
    response = client.chat.completions.create(
        model=FAST_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    notes_text = response.choices[0].message.content
    cleaned_notes = "\n".join([line for line in notes_text.split("\n")
                               if "Note: The article does not explicitly mention" not in line])
    return cleaned_notes

# =========================
# FOOTER
# =========================
def add_footer(canvas_obj, doc):
    width, height = A4
    if os.path.exists("logo.png"):
        canvas_obj.saveState()
        canvas_obj.setFillAlpha(0.06)
        canvas_obj.drawImage("logo.png", width/2-180, height/2-180, width=360, height=360, mask='auto')
        canvas_obj.restoreState()
    canvas_obj.setStrokeColor(colors.black)
    canvas_obj.line(50, 35, width-50, 35)
    canvas_obj.setFont("Times-Roman", 9)
    canvas_obj.drawString(50, 20, f"Daily Opinions' Notes | {today}")
    canvas_obj.drawRightString(width-50, 20, f"Page {doc.page}")

# =========================
# PDF GENERATION
# =========================
def generate_pdf(notes_data, font_theme, book_mode=False):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=65, leftMargin=65, topMargin=80, bottomMargin=60)
    elements = []
    styles = getSampleStyleSheet()
    base_font, bold_font = ("Times-Roman", "Times-Bold") if font_theme=="Classic Serif" else ("Helvetica", "Helvetica-Bold")
    article_title = ParagraphStyle("ArticleTitle", parent=styles["Heading2"], fontName=bold_font, fontSize=17, spaceBefore=18, spaceAfter=8)
    section_heading = ParagraphStyle("SectionHeading", parent=styles["Normal"], fontName=bold_font, fontSize=12, leading=16, spaceBefore=12, spaceAfter=6, textColor=colors.black, backColor=colors.HexColor("#FFF176"))
    body_style = ParagraphStyle("BodyStyle", parent=styles["Normal"], fontName=base_font, fontSize=11.5, leading=17, spaceAfter=6)
    summary_box = ParagraphStyle("SummaryBox", parent=styles["Normal"], fontName=base_font, fontSize=11, leading=14, backColor=colors.HexColor("#E0F7FA"), leftIndent=6, rightIndent=6, spaceBefore=4, spaceAfter=8)
    phrasal_style = ParagraphStyle("PhrasalStyle", parent=styles["Normal"], fontName=bold_font, fontSize=11, leading=14, backColor=colors.HexColor("#FFF3E0"), leftIndent=0, rightIndent=0, spaceBefore=4, spaceAfter=4)

    # COVER PAGE
    elements.append(Spacer(1, 1.5*inch))
    if os.path.exists("logo.png"):
        img = Image("logo.png", width=3*inch, height=3*inch)
        img.hAlign = 'CENTER'
        elements.append(img)
        elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("CSS Academy Book | Dawn Editorial Notes", article_title))
    elements.append(Paragraph(f"Generated on {today}", body_style))
    elements.append(PageBreak())

    # TABLE OF CONTENTS
    if book_mode:
        toc_data = [["Title","Author","Page"]]
        for i, item in enumerate(notes_data): toc_data.append([item["title"],item["author"],str(i+3)])
        toc_table = Table(toc_data,colWidths=[3*inch,2*inch,0.8*inch])
        toc_table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#FFF176")),
                                       ("GRID",(0,0),(-1,-1),0.5,colors.black),
                                       ("FONTNAME",(0,0),(-1,-1),base_font),
                                       ("FONTNAME",(0,0),(-1,0),bold_font),
                                       ("ALIGN",(2,1),(2,-1),"CENTER")]))
        elements.append(Paragraph("Table of Contents", article_title))
        elements.append(Spacer(1,0.3*inch))
        elements.append(toc_table)
        elements.append(PageBreak())

    # ADD ARTICLES
    for item in notes_data:
        elements.append(Paragraph(item["title"], article_title))
        elements.append(Paragraph(f"Author: {item['author']}", body_style))
        elements.append(Spacer(1,0.2*inch))
        bullet_buffer = []
        for line in item["notes"].split("\n"):
            clean_line = line.strip().replace("**","")
            if not clean_line: elements.append(Spacer(1,0.1*inch)); continue
            line_no_num = ''.join([c for c in clean_line if not c.isdigit() and c != '.']).strip()
            if any(line_no_num.lower().startswith(sec.lower()) for sec in ["context and background","core issue","key arguments","counter-arguments","important facts","css linkages","analytical evaluation","way forward","possible questions","summary box","key vocabulary","phrasal verbs with explanation","urdu summary"]):
                if bullet_buffer: elements.append(ListFlowable(bullet_buffer, bulletType="bullet", leftIndent=20)); bullet_buffer=[]
                style_to_use = summary_box if "summary box" in line_no_num.lower() else section_heading
                elements.append(Paragraph(line_no_num, style_to_use))
                continue
            if ":" in clean_line:
                parts = clean_line.split(":",1); term=parts[0].strip(); explanation=parts[1].strip()
                elements.append(Paragraph(f"<b>{term}:</b> {explanation}", phrasal_style))
                continue
            if clean_line.startswith("*") or clean_line[0].isdigit():
                bullet_text = clean_line.lstrip("*0123456789. ").strip()
                bullet_buffer.append(ListItem(Paragraph(bullet_text, body_style)))
                continue
            if bullet_buffer: elements.append(ListFlowable(bullet_buffer, bulletType="bullet", leftIndent=20)); bullet_buffer=[]
            elements.append(Paragraph(clean_line, body_style))
        elements.append(PageBreak())

    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
    buffer.seek(0)
    return buffer

# =========================
# STREAMLIT UI
# =========================
tab1, tab2 = st.tabs(["Fetch Opinions","Generate Notes & Book"])

with tab1:
    if st.button("Fetch Top Opinions"):
        with st.spinner("Fetching..."):
            st.session_state["articles"] = scrape_opinions()
            st.success("Fetched Successfully")

    if "articles" in st.session_state:
        st.subheader("Preview & Select Articles")
        selected_articles=[]
        for i, art in enumerate(st.session_state["articles"]):
            if st.checkbox(f"{art['title']} - {art['author']}", value=True):
                st.write(art['content'][:400]+"...")
                selected_articles.append(art)
        st.session_state["selected_articles"]=selected_articles

with tab2:
    mode = st.selectbox("Select Notes Mode",["Bullet Dominant Hybrid","Paragraph Dominant Hybrid"])
    font_theme = st.selectbox("Select Font Theme",["Classic Serif","Modern Sans"])

    if "selected_articles" in st.session_state and st.session_state["selected_articles"]:
        if st.button("Generate CSS Notes"):
            results=[]
            with st.spinner("Generating Notes..."):
                for art in st.session_state["selected_articles"]:
                    notes = generate_css_notes(art, mode)
                    results.append({"title":art["title"],"notes":notes,"author":art["author"]})
                st.session_state["notes"]=results
            st.success("Notes Generated")

        if st.button("Generate CSS Academy Book"):
            if "notes" not in st.session_state:
                st.warning("Please generate notes first.")
            else:
                pdf_buffer = generate_pdf(st.session_state["notes"], font_theme, book_mode=True)
                # Save/update master book
                with open(master_book_file,"wb") as f: f.write(pdf_buffer.read())
                st.download_button("Download CSS Academy Book PDF", data=open(master_book_file,"rb"), file_name=f"CSS_Academy_Book_{file_date}.pdf", mime="application/pdf")