# app/services/letter_drafting.py

from langchain_ollama import OllamaLLM

llm = OllamaLLM(
    base_url="http://localhost:11434",
    model="llama3.2",
    format="json"  # Must be exactly 'json'
)

def draft_letter(user_comments: str) -> str:
    prompt = f"""
    Please respond with a JSON object containing a field "letter" which is a
    respectful, clear, and well-structured letter to a lawmaker regarding this issue:

    {user_comments}

    The letter should be concise, persuasive, and well-structured. Sign off at the end.
    """
    response = llm.invoke(prompt)
    return response
