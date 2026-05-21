"""
LangGraph Tools for HCP CRM Agent
----------------------------------
Tool 1: log_interaction     - Extract & populate form from natural language
Tool 2: edit_interaction    - Update ONLY explicitly mentioned fields
Tool 3: suggest_followups   - Generate AI-powered follow-up suggestions
Tool 4: search_hcp          - Search HCP records from database
Tool 5: summarize_topics    - Summarize verbose discussion into concise points
"""

import json
from datetime import datetime
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from app.config import settings


llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model="llama-3.1-8b-instant",
    temperature=0,
)


# ─── Tool 1: Log Interaction ──────────────────────────────────────────────────
@tool
def log_interaction(user_message: str) -> dict:
    """
    Extract interaction details from a natural language message.
    Returns a structured dict with all form fields populated from the message.
    Use this when the user is describing a new HCP interaction they want to log.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M")

    prompt = f"""You are a CRM data extraction assistant for pharmaceutical field representatives.
Extract structured interaction data from the user's natural language message.

Today's date is: {today}
Current time is: {current_time}

User message: "{user_message}"

Extract and return ONLY a valid JSON object with these exact keys:
{{
  "hcp_name": "Full name with title (e.g., Dr. Smith) or null if not mentioned",
  "interaction_type": "MUST be one of exactly: Meeting, Call, Email, Conference, Other. Detect from context: 'called', 'phone call', 'rang' = Call. 'emailed', 'sent email' = Email. 'conference', 'event' = Conference. Default to Meeting.",
  "date": "YYYY-MM-DD format. Use {today} if they say 'today' or no date mentioned.",
  "time": "HH:MM in 24hr format. Use {current_time} if no time mentioned. NEVER return null for time.",
  "attendees": "Comma-separated names of attendees besides the HCP, or null",
  "topics_discussed": "Professional summary of key topics discussed (1-2 sentences, factual CRM language). null if nothing mentioned.",
  "materials_shared": ["list of materials/brochures/PDFs shared"] or [],
  "samples_distributed": ["list of drug samples distributed"] or [],
  "sentiment": "positive, neutral, or negative. Infer carefully: positive=interested/happy/receptive, negative=resistant/concerned/dismissive, neutral=standard/no strong signal. Default neutral.",
  "outcomes": "Professional CRM outcome summary: what was agreed, decided, or resulted from the meeting. Use language like 'HCP expressed interest in...', 'Agreement reached to...', 'HCP requested...'. null if nothing concrete.",
  "follow_up_actions": "Specific next steps or tasks mentioned. null if none."
}}

STRICT RULES:
- interaction_type: if they say 'called', 'by phone', 'over the phone' → MUST return 'Call'
- time: ALWAYS return a time. Use {current_time} as default, never null.
- outcomes: write professionally. Never copy raw user text. Extract the business outcome only.
- topics_discussed: professional CRM summary only, not raw transcript.
- Return ONLY the JSON object, no explanation, no markdown fences."""

    response = llm.invoke(prompt)
    raw = response.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        extracted = json.loads(raw)
    except json.JSONDecodeError:
        extracted = {
            "hcp_name": None,
            "interaction_type": "Meeting",
            "date": today,
            "time": current_time,
            "attendees": None,
            "topics_discussed": user_message,
            "materials_shared": [],
            "samples_distributed": [],
            "sentiment": "neutral",
            "outcomes": None,
            "follow_up_actions": None,
        }

    # Hard enforcements — never let these be null/empty
    extracted["date"] = extracted.get("date") or today
    extracted["time"] = extracted.get("time") or current_time
    extracted["interaction_type"] = extracted.get("interaction_type") or "Meeting"
    extracted["sentiment"] = extracted.get("sentiment") or "neutral"
    extracted.setdefault("materials_shared", [])
    extracted.setdefault("samples_distributed", [])

    # Validate interaction_type is one of the allowed values
    valid_types = ["Meeting", "Call", "Email", "Conference", "Other"]
    if extracted["interaction_type"] not in valid_types:
        extracted["interaction_type"] = "Meeting"

    return {
        "action": "log_interaction",
        "fields": extracted,
        "message": "Interaction logged successfully.",
    }


# ─── Tool 2: Edit Interaction ─────────────────────────────────────────────────
@tool
def edit_interaction(user_message: str, current_form_state: str) -> dict:
    """
    Detect which fields the user EXPLICITLY wants to correct and return ONLY those fields.
    NEVER infer or change fields not directly mentioned by the user.
    Use this when user says things like 'sorry', 'actually', 'change', 'update', 'wrong name', etc.
    """
    prompt = f"""You are a CRM form editor. The user wants to correct SPECIFIC fields only.

Current form state:
{current_form_state}

User correction message: "{user_message}"

CRITICAL RULES:
1. ONLY return fields the user EXPLICITLY mentions changing. 
2. NEVER infer sentiment, topics, or any other field from context if not directly stated.
3. If user says "the time was 3pm" → only update time. Nothing else.
4. If user says "change the name to Dr. John" → only update hcp_name. Nothing else.
5. If user says "it was a call not a meeting" → only update interaction_type to "Call".
6. NEVER include sentiment unless user explicitly says the sentiment was X.
7. NEVER include materials_shared or samples_distributed unless user explicitly mentions them.

Return ONLY this JSON:
{{
  "fields_to_update": {{
    "field_name": "new_value"
  }},
  "explanation": "What was changed and why"
}}

Valid field names: hcp_name, interaction_type, date, time, attendees, topics_discussed,
materials_shared, samples_distributed, sentiment, outcomes, follow_up_actions

For interaction_type, valid values are: Meeting, Call, Email, Conference, Other
For time, use HH:MM 24hr format.
For date, use YYYY-MM-DD format.

Return ONLY the JSON, no markdown fences."""

    response = llm.invoke(prompt)
    raw = response.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "fields_to_update": {},
            "explanation": "Could not parse the correction. Please be more specific.",
        }

    return {
        "action": "edit_interaction",
        "fields": result.get("fields_to_update", {}),
        "message": result.get("explanation", "Fields updated."),
    }


# ─── Tool 3: Suggest Follow-ups ───────────────────────────────────────────────
@tool
def suggest_followups(interaction_context: str) -> dict:
    """
    Generate 3-4 actionable AI-suggested follow-up actions based on the interaction context.
    Use this after an interaction is logged to proactively help the rep plan next steps.
    """
    prompt = f"""You are an expert pharmaceutical sales coach. Based on this HCP interaction,
suggest 3-4 specific, actionable follow-up items a field rep should do.

Interaction context: "{interaction_context}"

Return ONLY a JSON array of concise follow-up strings (each under 10 words):
["follow-up 1", "follow-up 2", "follow-up 3", "follow-up 4"]

Good examples:
- "Schedule follow-up meeting in 2 weeks"
- "Send product efficacy PDF to HCP"
- "Share clinical trial data via email"
- "Follow up on sample distribution feedback"
- "Add HCP to advisory board invite list"

Return ONLY the JSON array, no explanation, no markdown."""

    response = llm.invoke(prompt)
    raw = response.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        suggestions = json.loads(raw)
        if not isinstance(suggestions, list):
            suggestions = []
    except json.JSONDecodeError:
        suggestions = [
            "Schedule a follow-up meeting",
            "Send product information materials",
            "Follow up on discussed outcomes",
        ]

    return {
        "action": "suggest_followups",
        "suggestions": suggestions,
        "message": "Here are suggested follow-up actions based on your interaction.",
    }


# ─── Tool 4: Search HCP ───────────────────────────────────────────────────────
@tool
def search_hcp(query: str, db_hcps: str) -> dict:
    """
    Search for HCP records matching the query name.
    Use this when the user mentions an HCP name to auto-complete or verify.
    db_hcps is a JSON string of available HCP records.
    """
    prompt = f"""You are searching an HCP database for a field rep CRM.

Search query: "{query}"
Available HCPs (JSON): {db_hcps}

Find HCPs whose name closely matches the query (fuzzy match, case-insensitive).
Return ONLY a JSON object:
{{
  "matches": [
    {{"id": "uuid", "name": "Dr. Full Name", "specialty": "specialty", "hospital": "hospital"}}
  ],
  "best_match": "The single best matching full name or null"
}}

If no matches found, return {{"matches": [], "best_match": null}}
Return ONLY the JSON, no markdown."""

    response = llm.invoke(prompt)
    raw = response.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {"matches": [], "best_match": None}

    return {
        "action": "search_hcp",
        "matches": result.get("matches", []),
        "best_match": result.get("best_match"),
        "message": f"Found {len(result.get('matches', []))} matching HCPs.",
    }


# ─── Tool 5: Summarize Topics ─────────────────────────────────────────────────
@tool
def summarize_topics(verbose_text: str) -> dict:
    """
    Summarize verbose discussion text into concise, professional CRM key points.
    Use this when the user provides long discussion notes or says 'summarize'.
    """
    prompt = f"""You are a pharmaceutical CRM assistant. Summarize the following discussion notes
into concise, professional CRM language.

Discussion notes: "{verbose_text}"

Return ONLY a JSON object:
{{
  "summary": "2-3 sentence professional CRM summary. Use language like 'Discussed...', 'HCP indicated...', 'Key topics covered...'",
  "key_points": ["Professional bullet point 1", "Professional bullet point 2", "Professional bullet point 3"]
}}

Keep it factual and professional. No personal health info, no raw quotes. Return ONLY the JSON."""

    response = llm.invoke(prompt)
    raw = response.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "summary": verbose_text[:200],
            "key_points": [verbose_text[:100]],
        }

    return {
        "action": "summarize_topics",
        "summary": result.get("summary", ""),
        "key_points": result.get("key_points", []),
        "message": "Topics summarized successfully.",
    }
