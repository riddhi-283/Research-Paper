import json
import os
import openai
import requests
import faiss
import numpy as np
from tqdm import tqdm
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

from numpy.linalg import norm

def cosine_similarity(a, b):
    return np.dot(a, b) / (norm(a) * norm(b))

client = OpenAI()
# ---------- Step 1: Embed text using OpenAI ----------
def get_embedding(text, model="text-embedding-3-small"):
    text = text.replace("\n", " ")
    
    response = client.embeddings.create(
        input=text,
        model=model
    )

    return response.data[0].embedding

# ---------- Step 2: Search Semantic Scholar ----------
def search_semantic_scholar(query, num_results=50):
    url = f"https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": num_results,
        "fields": "title,abstract,url"
    }

    # Directly define the API key (Reminder: Securely handle API keys in production environments)
    api_key = os.getenv('SEMANTIC_SCHOLAR_API_KEY')

    # Define headers with API key
    headers = {"x-api-key": api_key}

    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 429:
        raise Exception("Rate limit exceeded. Use an API key or wait before retrying.")

    response.raise_for_status()

    response_json = response.json()

    print(f"Will retrieve an estimated {len(response_json.get('data', []))} documents")

    papers = response_json.get("data", [])

    # Save papers to a JSON file
    with open("papers.json", "w") as file:
        json.dump(papers, file, indent=2)

    return papers

# ---------- Step 3: Embed all papers + store in FAISS ----------
def build_faiss_index(papers):
    embeddings = []
    valid_papers = []

    print("Embedding papers...")
    for paper in tqdm(papers):
        abstract = paper.get("abstract", "")
        if abstract:
            emb = get_embedding(abstract)
            embeddings.append(emb)
            valid_papers.append(paper)

    index = faiss.IndexFlatL2(len(embeddings[0]))
    index.add(np.array(embeddings).astype("float32"))
    return index, valid_papers, embeddings

# ---------- Step 4: Query top k = 5 similar ----------
def search_similar_papers(query, index, valid_papers, embeddings, k=5):
    query_emb = get_embedding(query)
    D, I = index.search(np.array([query_emb]).astype("float32"), k)
    results = []

    for idx in I[0]:
        paper = valid_papers[idx]
        sim_score = cosine_similarity(query_emb, embeddings[idx])
        results.append((paper, sim_score))

    return results

# ---------- Step 5: Run everything ----------
def main():
    user_query = input("Enter your research idea: ")

    print("\nSearching Semantic Scholar...")
    papers = search_semantic_scholar(user_query, num_results=10)

    if not papers:
        print("No papers found.")
        return

    index, valid_papers, embeddings = build_faiss_index(papers)

    print("\nFinding top 5 most similar papers...")
    top5 = search_similar_papers(user_query, index, valid_papers, embeddings)

    with open("top_5_similar_papers.txt", "w", encoding="utf-8") as f:
        print("\n--- Top 5 Most Similar Papers ---\n")
        f.write("--- Top 5 Most Similar Papers ---\n\n")

        for i, (paper, score) in enumerate(top5, 1):
            title = paper.get("title", "N/A")
            abstract = paper.get("abstract", "N/A")
            url = paper.get("url", "N/A")

            entry = (
                f"🔹 Paper {i}\n"
                f"Title: {title}\n"
                f"Similarity Score: {score:.4f}\n"
                f"Abstract: {abstract}\n"
                f"Link: {url}\n"
                + "-" * 50 + "\n"
            )

            print(entry)
            f.write(entry)

if __name__ == "__main__":
    main()
