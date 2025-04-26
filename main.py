import os
from utils.grobid_extraction import extract_sections_from_pdf
from utils.feature_extraction import (
    extract_faceted_summary,
    extract_relationship_between_papers,
    extract_enriched_citation_usage,
    extract_main_ideas
)
from utils.prompt_templates import load_prompt_template
from utils.llm_helpers import call_gpt, get_author_names_from_text
import json
from tqdm import tqdm

def main():
    # ----------------------
    # 1. Target Paper
    # ----------------------
    print("\n🔵 Extracting Target Paper Sections...")
    target_pdf_path = 'data/target_paper.pdf'
    
    # Extract TAIC sections
    target_sections = extract_sections_from_pdf(target_pdf_path)
    title = target_sections.get('title', '')
    abstract = target_sections.get('abstract', '')
    introduction = target_sections.get('introduction', '')
    conclusion = target_sections.get('conclusion', '')
    target_authors = target_sections.get('authors', 'Unknown')
    target_year = target_sections.get('year', 'Unknown')

    print("\n✅ Target Paper TAIC Extracted:")
    print(f"Title: {title}\n")
    print(f"Abstract: {abstract[:300]}...\n")  # print first 300 chars for brevity
    print(f"Introduction: {introduction[:300]}...\n")
    print(f"Conclusion: {conclusion[:300]}...\n")
    print(f"Authors: {target_authors}\n")
    print(f"Year: {target_year}\n")

    # Generate faceted summary for target paper
    print("\n🔵 Generating Faceted Summary for Target Paper...")
    target_faceted_summary = extract_faceted_summary(title, abstract, introduction, conclusion)
    print("\n✅ Target Faceted Summary:\n")
    print(target_faceted_summary, "\n")

    # ----------------------
    # 2. Cited Papers
    # ----------------------
    cited_papers_dir = 'data/cited_papers'
    cited_paper_files = [f for f in os.listdir(cited_papers_dir) if f.endswith('.pdf')]

    cited_papers_data = []
    for pdf_file in tqdm(cited_paper_files, desc="Processing Cited Papers"):
        cited_pdf_path = os.path.join(cited_papers_dir, pdf_file)
        cited_sections = extract_sections_from_pdf(cited_pdf_path)

        cited_title = cited_sections.get('title', '')
        cited_abstract = cited_sections.get('abstract', '')
        cited_introduction = cited_sections.get('introduction', '')
        cited_conclusion = cited_sections.get('conclusion', '')
        cited_authors = cited_sections.get('authors', 'Unknown')
        cited_year = cited_sections.get('year', 'Unknown')

        faceted_summary = extract_faceted_summary(
            cited_title,
            cited_abstract,
            cited_introduction,
            cited_conclusion
        )

        print(f"\n✅ Faceted Summary for {pdf_file}:\n")
        print(faceted_summary, "\n")

        # Simulate dummy citation spans (you can extract later properly)
        citation_spans = []

        cited_papers_data.append({
            'file_name': pdf_file,
            'title': cited_title,
            'abstract': cited_abstract,
            'introduction': cited_introduction,
            'conclusion': cited_conclusion,
            'authors': cited_authors,
            'year': cited_year,
            'faceted_summary': faceted_summary,
            'citation_spans': citation_spans
        })

    # ----------------------
    # 3. Relationships & Citation Usages
    # ----------------------
    relationships = []
    enriched_usages = []

    for cited_paper in tqdm(cited_papers_data, desc="Building Relationships"):
        relation = extract_relationship_between_papers(
            faceted_summary_A={
                'title': title,
                'authors': target_authors,  # You can improve by extracting later
                'year': target_year,
                'summary': target_faceted_summary
            },
            faceted_summary_B={
                'title': cited_paper['title'],
                'authors': cited_paper['authors'],
                'year': cited_paper['year'],
                'summary': cited_paper['faceted_summary']
            },
            citation_spans=cited_paper['citation_spans']
        )
        relationships.append(relation)

        print(f"\n✅ Relationship with {cited_paper['file_name']}:\n")
        print(relation, "\n")

        enriched_usage = extract_enriched_citation_usage(
            relations=[relation],
            citation_spans=cited_paper['citation_spans'],
            paper_B_info={
                'authors': cited_paper['authors'],
                'year': cited_paper['year']
            }
        )
        enriched_usages.append(enriched_usage)

        print(f"\n✅ Enriched Citation Usage for {cited_paper['file_name']}:\n")
        print(enriched_usage, "\n")

    # ----------------------
    # 4. Final Literature Review Prompt
    # ----------------------
    print("\n🔵 Preparing Final Literature Review Prompt...")

    prompt = load_prompt_template('literature_review_generation.txt')

    cited_papers_text = ""
    for cited, usage in zip(cited_papers_data, enriched_usages):
        cited_papers_text += f"""
Title: {cited['title']}
Authors: {cited['authors']}
Year: {cited['year']}
Summary: {cited['faceted_summary']}
Usage: {usage}
"""

    filled_prompt = prompt.format(
        title=title,
        abstract=abstract,
        introduction=introduction,
        conclusion=conclusion,
        main_ideas="(Optionally extract main ideas here, or leave blank for now)",
        cited_papers_details=cited_papers_text
    )

    print("\n✅ Final Literature Review Prompt Preview (First 1000 characters):\n")
    print(filled_prompt[:1000], "\n...\n")

    # ----------------------
    # 5. Generate Literature Review
    # ----------------------
    print("\n🔵 Generating Literature Review using LLM...")
    literature_review = call_gpt(filled_prompt, temperature=0.4)

    # Save output
    os.makedirs('outputs/generated_reviews', exist_ok=True)
    with open('outputs/generated_reviews/literature_review.txt', 'w', encoding='utf-8') as f:
        f.write(literature_review)

    print("\n✅ Literature review saved successfully at outputs/generated_reviews/literature_review.txt\n")

if __name__ == "__main__":
    main()
