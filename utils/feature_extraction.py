import os
from utils.prompt_templates import load_prompt_template
from utils.llm_helpers import call_gpt

def extract_faceted_summary(title, abstract, introduction, conclusion):
    prompt = load_prompt_template('faceted_summary.txt')
    filled_prompt = prompt.format(
        title=title,
        abstract=abstract,
        introduction=introduction,
        conclusion=conclusion
    )
    return call_gpt(filled_prompt)

def extract_relationship_between_papers(faceted_summary_A, faceted_summary_B, citation_spans):
    prompt = load_prompt_template('relation_between_papers.txt')
    citation_context = "\n".join([f"{i+1}. {span}" for i, span in enumerate(citation_spans)])
    
    filled_prompt = prompt.format(
        title_A=faceted_summary_A['title'],
        author_A=faceted_summary_A['authors'],
        year_A=faceted_summary_A['year'],
        faceted_summary_A=faceted_summary_A['summary'],
        title_B=faceted_summary_B['title'],
        author_B=faceted_summary_B['authors'],
        year_B=faceted_summary_B['year'],
        faceted_summary_B=faceted_summary_B['summary'],
        citation_context=citation_context
    )
    return call_gpt(filled_prompt)

def extract_enriched_citation_usage(relations, citation_spans, paper_B_info):
    prompt = load_prompt_template('enriched_citation_usage.txt')
    
    filled_prompt = prompt.format(
        author_B=paper_B_info['authors'],
        year_B=paper_B_info['year'],
        relations_text="\n".join(relations),
        citation_spans_text="\n".join([f"{i+1}. {span}" for i, span in enumerate(citation_spans)])
    )
    return call_gpt(filled_prompt)

def extract_main_ideas(faceted_summary_target, related_work_text):
    prompt = load_prompt_template('main_ideas.txt')
    filled_prompt = prompt.format(
        title=faceted_summary_target['title'],
        faceted_summary=faceted_summary_target['summary'],
        related_work_section=related_work_text
    )
    return call_gpt(filled_prompt)
