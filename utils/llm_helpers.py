import openai
from dotenv import load_dotenv
import os

load_dotenv()

client = openai.OpenAI()
def call_gpt(prompt, model="gpt-3.5-turbo", temperature=0.3):
    response = client.responses.create(
        model=model,
        input=[{"role": "user", "content": prompt}],
        temperature=temperature
    )
    return response.output_text


def get_author_names_from_text(raw_text):
    prompt = f"""
    Extract only the names of the authors from the following text. 
    Ignore any department, college, university, or email addresses.
    Return a Python list of names.

    Text:
    {raw_text}
    """

    response = client.responses.create(
        model="gpt-3.5-turbo",
        input=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.output_text