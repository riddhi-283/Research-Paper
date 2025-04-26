import requests
import xml.etree.ElementTree as ET
import re
import fitz
import os
from utils.llm_helpers import get_author_names_from_text

def clean_text_with_regex(full_text):
    # Remove lines with IEEE footer patterns (copyright, DOI, ISBN, etc.)
    patterns = [
        r"\bISBN\b.*?\d{3}-\d-\d{4}-\d{4}-\d",  # ISBN
        r"©\d{4} IEEE",                         # ©2024 IEEE
        r"IEEE Xplore.*?ISBN.*?\d+",            # IEEE Xplore metadata
        r"Authorized licensed use.*?Restrictions apply\.",  # Licensing footer
        r"\d{3,4}",                             # Standalone page numbers like 658
        r"\bProceedings of the .*?Conference.*?\)",  # Conference headers
        r"DOI: *10\.\d{4,9}/[-._;()/:A-Z0-9]+",       # DOI
        r"http.*?ieee\.org.*",                  # IEEE download URL
    ]

    # Compile regex
    combined = re.compile("|".join(patterns), re.IGNORECASE)
    
    # Remove lines matching patterns
    lines = full_text.split('\n')
    filtered_lines = [line for line in lines if not combined.search(line)]
    
    # Return cleaned-up string
    return ' '.join(filtered_lines)


def extract_raw_text_between_sections(pdf_path, start_keywords, stop_keywords):
    doc = fitz.open(pdf_path)
    raw_text = ""
    for page in doc:
        raw_text += page.get_text()

    cleaned_text = clean_text_with_regex(raw_text)
    text = re.sub(r'\s+', ' ', cleaned_text)
    lower_text = text.lower()

    start_idx = stop_idx = None

    for kw in start_keywords:
        match = re.search(r'\b' + re.escape(kw.lower()) + r'\b', lower_text)
        if match:
            start_idx = match.start()
            break

    for kw in stop_keywords:
        match = re.search(r'\b' + re.escape(kw.lower()) + r'\b', lower_text)
        if match:
            stop_idx = match.start()
            break

    if start_idx is not None:
        return text[start_idx:stop_idx].strip() if stop_idx else text[start_idx:].strip()
    return None

def extract_sections_from_pdf(pdf_path, grobid_url="http://localhost:8070/api/processFulltextDocument"):
    
    # Resolve absolute path
    pdf_path = os.path.join(os.path.dirname(__file__), '..', pdf_path)
    pdf_path = os.path.abspath(pdf_path)

    # Step 1: Send PDF to Grobid
    with open(pdf_path, 'rb') as pdf_file:
        response = requests.post(
            grobid_url,
            files={'input': pdf_file},
            data={'consolidateHeader': '1', 'consolidateCitations': '0'}
        )
    if response.status_code != 200:
        raise Exception("Failed to process PDF with Grobid:", response.text)

    # Step 2: Parse the XML
    root = ET.fromstring(response.text)
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    result = {}

    # Extract title
    title_elem = root.find(".//tei:titleStmt/tei:title", ns)
    if title_elem is not None:
        result['title'] = title_elem.text.strip()
    
    # Extract authors
    title_for_matching = ' '.join(result['title'].split()[:7])
    between_text = extract_raw_text_between_sections(
        pdf_path,
        start_keywords=[title_for_matching],
        stop_keywords=["abstract"]
    )    
    if between_text:
        authors = get_author_names_from_text(between_text)
        result['authors'] = authors
        print(authors)
    else:
        print("Could not extract text between Title and Abstract")


    # Extract abstract
    abstract_elem = root.find(".//tei:abstract", ns)
    if abstract_elem is not None:
        result['abstract'] = " ".join(abstract_elem.itertext()).strip()

    # Extract year of publication
    date_elem = root.find(".//tei:publicationStmt/tei:date", ns)
    if date_elem is not None and date_elem.get("when"):
        result['year'] = date_elem.get("when")

    # Extract body content and specific sections
    for div in root.findall(".//tei:div", ns):
        head = div.find("tei:head", ns)
        if head is not None:
            section_title = head.text.strip().upper()

            # Match based on capitalized headings
            if "INTRODUCTION" in section_title:
                result['introduction'] = " ".join(div.itertext()).strip()
            elif "CONCLUSION" in section_title or "CONCLUSIONS" in section_title:
                result['conclusion'] = " ".join(div.itertext()).strip()

    # If introduction seems too short, try fallback extraction
    intro = result.get('introduction', '')
    if len(intro.split()) < 50:
        patched_intro = extract_raw_text_between_sections(
            pdf_path,
            start_keywords=["Introduction"],
            stop_keywords=["Literature Review", "Related Work", "Methodology"]
        )
        if patched_intro:
            result['introduction'] = patched_intro

    return result


# Example usage
pdf_file_path = "data/target_paper2.pdf"
sections = extract_sections_from_pdf(pdf_file_path)

for sec, content in sections.items():
    print(f"\n--- {sec.upper()} ---\n")
    print(content)  

# print(sections['authors'])
# print(sections['year'])