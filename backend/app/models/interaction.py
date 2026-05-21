from sqlalchemy import Column, String, Text, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base
from datetime import datetime
import uuid
import enum


class SentimentEnum(str, enum.Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hcp_name = Column(String(255), nullable=True)
    interaction_type = Column(String(100), default="Meeting")
    date = Column(String(20), nullable=True)
    time = Column(String(20), nullable=True)
    attendees = Column(Text, nullable=True)
    topics_discussed = Column(Text, nullable=True)
    materials_shared = Column(JSON, default=list)
    samples_distributed = Column(JSON, default=list)
    sentiment = Column(String(50), default="neutral")
    outcomes = Column(Text, nullable=True)
    follow_up_actions = Column(Text, nullable=True)
    ai_suggested_followups = Column(JSON, default=list)
    raw_chat_log = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HCP(Base):
    __tablename__ = "hcps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    specialty = Column(String(255), nullable=True)
    hospital = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
