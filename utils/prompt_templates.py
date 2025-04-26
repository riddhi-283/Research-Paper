import os

def load_prompt_template(template_name):
    prompt_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    template_path = os.path.join(prompt_dir, template_name)
    
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()
