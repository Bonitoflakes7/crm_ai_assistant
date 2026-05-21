from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import init_db
from app.routes.interactions import router
from app.config import settings

app = FastAPI(
    title="HCP CRM AI Backend",
    description="AI-first CRM for pharmaceutical field reps with LangGraph agent",
    version="1.0.0",
)

# CORS - allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:5173",
        "http://localhost:3000",
        "https://*.vercel.app",
        "*",  # for development; restrict in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router, prefix="/api")


@app.on_event("startup")
async def startup():
    """Initialize database tables on startup."""
    init_db()
    print("✅ Database tables initialized")
    print("✅ LangGraph agent ready")
    print(f"✅ Using Groq model: llama-3.3-70b-versatile")


@app.get("/")
async def root():
    return {
        "message": "HCP CRM AI Backend is running",
        "docs": "/docs",
        "health": "/api/health",
    }
