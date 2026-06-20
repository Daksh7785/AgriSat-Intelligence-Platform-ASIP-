from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.copilot_service import CopilotService
from app.api.auth import get_current_user
from app.db import models

router = APIRouter(prefix="/copilot", tags=["AI Copilot Assistant"])

class ChatRequest(BaseModel):
    message: str

@router.post("/query")
def chat_copilot(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Query message cannot be empty.")
        
    try:
        response = CopilotService.answer_query(db, req.message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
