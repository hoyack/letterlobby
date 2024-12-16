# app/schemas/letter_draft_request.py

from pydantic import BaseModel

class LetterDraftRequest(BaseModel):
    personal_feedback: str
