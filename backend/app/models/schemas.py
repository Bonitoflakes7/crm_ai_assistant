from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class FormState(BaseModel):
    hcp_name: Optional[str] = None
    interaction_type: Optional[str] = "Meeting"
    date: Optional[str] = None
    time: Optional[str] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[List[str]] = []
    samples_distributed: Optional[List[str]] = []
    sentiment: Optional[str] = "neutral"
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    ai_suggested_followups: Optional[List[str]] = []


class ChatRequest(BaseModel):
    message: str
    form_state: FormState
    chat_history: List[ChatMessage] = []
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    assistant_message: str
    form_updates: dict
    suggestions: List[str] = []
    action_type: Optional[str] = "log"
    session_id: Optional[str] = None


class SaveInteractionRequest(BaseModel):
    form_state: FormState
    chat_history: List[ChatMessage] = []
    session_id: Optional[str] = None


class InteractionResponse(BaseModel):
    id: str
    hcp_name: Optional[str]
    interaction_type: Optional[str]
    date: Optional[str]
    time: Optional[str]
    attendees: Optional[str]
    topics_discussed: Optional[str]
    materials_shared: List[str]
    samples_distributed: List[str]
    sentiment: Optional[str]
    outcomes: Optional[str]
    follow_up_actions: Optional[str]
    ai_suggested_followups: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class HCPSchema(BaseModel):
    id: str
    name: str
    specialty: Optional[str]
    hospital: Optional[str]

    class Config:
        from_attributes = True
