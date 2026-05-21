from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
import json

from app.db.database import get_db
from app.models.interaction import Interaction, HCP
from app.models.schemas import (
    ChatRequest, ChatResponse,
    SaveInteractionRequest, InteractionResponse,
)
from app.agent.graph import run_agent

router = APIRouter()


# ─── Chat endpoint ─────────────────────────────────────────────────────────────
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        result = run_agent(
            user_message=request.message,
            form_state=request.form_state.model_dump(),
            chat_history=[m.model_dump() for m in request.chat_history],
        )
        session_id = request.session_id or str(uuid.uuid4())
        return ChatResponse(
            assistant_message=result["assistant_message"],
            form_updates=result["form_updates"],
            suggestions=result["suggestions"],
            action_type=result.get("action_type", "log"),
            session_id=session_id,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


# ─── Save interaction ──────────────────────────────────────────────────────────
@router.post("/interactions", response_model=InteractionResponse)
async def save_interaction(request: SaveInteractionRequest, db: Session = Depends(get_db)):
    try:
        fs = request.form_state

        # Ensure lists are actual Python lists (not None)
        materials = fs.materials_shared if isinstance(fs.materials_shared, list) else []
        samples = fs.samples_distributed if isinstance(fs.samples_distributed, list) else []
        followups = fs.ai_suggested_followups if isinstance(fs.ai_suggested_followups, list) else []
        chat_log = [m.model_dump() for m in request.chat_history] if request.chat_history else []

        interaction = Interaction(
            hcp_name=fs.hcp_name or None,
            interaction_type=fs.interaction_type or "Meeting",
            date=fs.date or None,
            time=fs.time or None,
            attendees=fs.attendees or None,
            topics_discussed=fs.topics_discussed or None,
            materials_shared=materials,
            samples_distributed=samples,
            sentiment=fs.sentiment or "neutral",
            outcomes=fs.outcomes or None,
            follow_up_actions=fs.follow_up_actions or None,
            ai_suggested_followups=followups,
            raw_chat_log=chat_log,
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        return InteractionResponse(
            id=str(interaction.id),
            hcp_name=interaction.hcp_name,
            interaction_type=interaction.interaction_type,
            date=interaction.date,
            time=interaction.time,
            attendees=interaction.attendees,
            topics_discussed=interaction.topics_discussed,
            materials_shared=interaction.materials_shared or [],
            samples_distributed=interaction.samples_distributed or [],
            sentiment=interaction.sentiment,
            outcomes=interaction.outcomes,
            follow_up_actions=interaction.follow_up_actions,
            ai_suggested_followups=interaction.ai_suggested_followups or [],
            created_at=interaction.created_at,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Save error: {str(e)}")


# ─── Get all interactions ──────────────────────────────────────────────────────
@router.get("/interactions")
async def get_interactions(db: Session = Depends(get_db)):
    interactions = db.query(Interaction).order_by(Interaction.created_at.desc()).limit(20).all()
    return [
        {
            "id": str(i.id),
            "hcp_name": i.hcp_name,
            "date": i.date,
            "sentiment": i.sentiment,
            "interaction_type": i.interaction_type,
            "created_at": i.created_at.isoformat(),
        }
        for i in interactions
    ]


# ─── HCP search ────────────────────────────────────────────────────────────────
@router.get("/hcps/search")
async def search_hcps(q: str = "", db: Session = Depends(get_db)):
    if not q:
        hcps = db.query(HCP).limit(10).all()
    else:
        hcps = db.query(HCP).filter(HCP.name.ilike(f"%{q}%")).limit(10).all()
    return [{"id": str(h.id), "name": h.name, "specialty": h.specialty} for h in hcps]


# ─── Seed HCPs ─────────────────────────────────────────────────────────────────
@router.post("/hcps/seed")
async def seed_hcps(db: Session = Depends(get_db)):
    sample_hcps = [
        {"name": "Dr. Sarah Smith", "specialty": "Oncology", "hospital": "City Medical Center"},
        {"name": "Dr. John Chen", "specialty": "Cardiology", "hospital": "Heart Institute"},
        {"name": "Dr. Emily Johnson", "specialty": "Neurology", "hospital": "Neuro Clinic"},
        {"name": "Dr. Michael Sharma", "specialty": "Pulmonology", "hospital": "Lung Care Hospital"},
        {"name": "Dr. Priya Patel", "specialty": "Endocrinology", "hospital": "Diabetes Care Center"},
        {"name": "Dr. Robert Williams", "specialty": "Rheumatology", "hospital": "Joint Health Clinic"},
        {"name": "Dr. Anjali Mehta", "specialty": "Gastroenterology", "hospital": "Digestive Health"},
        {"name": "Dr. David Kumar", "specialty": "Hematology", "hospital": "Blood Disorders Institute"},
    ]
    added = 0
    for hcp_data in sample_hcps:
        existing = db.query(HCP).filter(HCP.name == hcp_data["name"]).first()
        if not existing:
            db.add(HCP(**hcp_data))
            added += 1
    db.commit()
    return {"message": f"Seeded {added} HCPs successfully"}


# ─── Health check ──────────────────────────────────────────────────────────────
@router.get("/health")
async def health():
    return {"status": "ok", "service": "HCP CRM AI Backend"}
