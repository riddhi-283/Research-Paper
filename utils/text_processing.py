import re
from rouge_score import rouge_scorer

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # Remove extra whitespace
    return text.strip()

def rouge_rank_sentences(query, sentences, top_k=5):
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2'], use_stemmer=True)
    scored = []
    for sent in sentences:
        scores = scorer.score(query, sent)
        avg_score = (scores['rouge1'].recall + scores['rouge2'].recall) / 2
        scored.append((avg_score, sent))
    
    # Sort by descending score
    scored = sorted(scored, reverse=True)
    return [s[1] for s in scored[:top_k]]
