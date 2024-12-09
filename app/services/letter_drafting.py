# app/services/letter_drafting.py

import json
from bs4 import BeautifulSoup
from langchain_ollama import OllamaLLM
from app.core.config import settings  # Import settings to access OLLAMA_BASE_URL

llm = OllamaLLM(
    base_url=settings.OLLAMA_BASE_URL,  # Use OLLAMA_BASE_URL from .env
    model="llama3.2",
    format="json"  # Tells OllamaLLM to interpret response as JSON if possible
)

def draft_letter(user_comments: str) -> str:
    # Refine the prompt for stricter instructions
    prompt = f"""
    You are to respond ONLY with a well-formed JSON object that includes a single field "letter".
    "letter" should be a string containing the full text of the letter. 
    Do not include any additional commentary, metadata, or text outside the JSON object.

    The letter should be respectful, clear, and well-structured, addressed to a lawmaker regarding this issue:

    {user_comments}

    The letter should be concise, persuasive, and sign off at the end (e.g., "Sincerely, [Your Name]").

    Example of the desired format:
    {{
      "letter": "Dear Senator Doe,\\n\\nI am writing to express my support...\\n\\nSincerely,\\n[Your Name]"
    }}

    Respond with only a JSON object, nothing else.
    """

    response = llm.invoke(prompt)

    # If the response contains HTML or other formatting, strip it out with BeautifulSoup
    soup = BeautifulSoup(response, "html.parser")
    cleaned_response = soup.get_text()

    # Attempt to parse the cleaned response as JSON
    try:
        data = json.loads(cleaned_response)
    except json.JSONDecodeError:
        # If parsing fails, the model may not have followed instructions.
        raise ValueError("The LLM did not return valid JSON.")

    # Verify that "letter" is present and is a string
    letter_text = data.get("letter")
    if not letter_text or not isinstance(letter_text, str):
        raise ValueError("No valid 'letter' field found in the LLM response.")

    # Return the cleaned JSON as a string, which can be stored in final_letter_text
    return json.dumps(data)
