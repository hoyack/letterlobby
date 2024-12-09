# app/schemas/letter_draft_request.py

from pydantic import BaseModel, Field
from typing import Optional

class LetterDraftRequest(BaseModel):
    bill_name: str
    lawmaker_name: str
    stance: str = Field(..., description="The stance towards the bill, e.g., 'support' or 'oppose'")
    support_level: int = Field(..., ge=1, le=10, description="Support level from 1 to 10")
    personal_feedback: Optional[str] = None
