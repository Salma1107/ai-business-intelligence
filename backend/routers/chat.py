from fastapi import APIRouter, Depends

from backend.core.deps import get_current_user_email
from backend.models.schemas import ChatRequest, ChatResponse
from Orchestrator import ask_orchestrator

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, user_email: str = Depends(get_current_user_email)):
    answer = ask_orchestrator(request.question)
    return ChatResponse(answer=answer)
