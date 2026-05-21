"""
LangGraph Agent Graph — single-tool-call per request, no loop timeout.
"""

import json
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from app.config import settings
from app.agent.tools import (
    log_interaction,
    edit_interaction,
    suggest_followups,
    search_hcp,
    summarize_topics,
)
import operator


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    form_state: dict
    tool_result: dict
    intent: str


tools = [log_interaction, edit_interaction, suggest_followups, search_hcp, summarize_topics]

llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model="llama-3.1-8b-instant",
    temperature=0,
    max_tokens=1024,
)
llm_with_tools = llm.bind_tools(tools)


# ─── Detect if this is a conversational message (no tool needed) ───────────────
CONVERSATIONAL_TRIGGERS = [
    "hi", "hello", "hey", "thanks", "thank you", "thank", "ok", "okay",
    "great", "awesome", "perfect", "got it", "sounds good", "cool", "nice",
    "bye", "goodbye", "see you", "good morning", "good evening", "good afternoon",
    "help", "what can you do", "how do you work", "what do you do",
]

def is_conversational(message: str) -> bool:
    msg = message.strip().lower()
    # Short messages that match conversational triggers
    if msg in CONVERSATIONAL_TRIGGERS:
        return True
    if len(msg.split()) <= 4 and any(msg.startswith(t) for t in CONVERSATIONAL_TRIGGERS):
        return True
    return False


CONVERSATIONAL_REPLIES = {
    "hi": "Hi there! 👋 Tell me about your HCP interaction and I'll fill the form automatically. For example: *\"Today I met Dr. Smith and discussed product X efficacy. Sentiment was positive and I shared brochures.\"*",
    "hello": "Hello! 👋 Ready to log your interaction. Just describe what happened in plain English and I'll handle the rest!",
    "hey": "Hey! 👋 Describe your HCP interaction and I'll fill in the form for you automatically.",
    "thanks": "You're welcome! 😊 Let me know if you need to make any corrections or log another interaction.",
    "thank you": "Happy to help! 😊 Let me know if you need any changes to the form.",
    "thank": "You're welcome! Let me know if you need anything else.",
    "ok": "Got it! Feel free to describe another interaction or ask me to correct anything.",
    "okay": "Sure! Let me know how I can help.",
    "great": "Glad it's working! Let me know if you need any corrections.",
    "awesome": "Thanks! 😊 Let me know if you need to change anything in the form.",
    "perfect": "Great! Let me know if you need any adjustments.",
    "got it": "Perfect! Let me know if you need anything else.",
    "cool": "😊 Let me know if you need any corrections to the form.",
    "nice": "Thanks! Feel free to continue or correct anything.",
    "help": "I can help you log HCP interactions! Here's how:\n\n• **Log**: *\"Met Dr. Smith today, discussed Drug X, positive sentiment, shared brochure\"*\n• **Edit**: *\"Sorry, the name was actually Dr. John\"*\n• **Summarize**: *\"Summarize the topics discussed\"*\n\nJust describe your interaction naturally and I'll fill the form automatically.",
    "what can you do": "I can:\n\n• 📝 **Log interactions** — just describe them in plain English\n• ✏️ **Edit fields** — say *\"sorry, change the name to Dr. X\"*\n• 💡 **Suggest follow-ups** — automatically after each log\n• 🔍 **Search HCPs** — say *\"search for Dr. Patel\"*\n• 📋 **Summarize topics** — condense long discussion notes",
    "bye": "Goodbye! Your interaction data is saved. 👋",
}

def get_conversational_reply(message: str) -> str:
    msg = message.strip().lower()
    for key in CONVERSATIONAL_REPLIES:
        if msg == key or msg.startswith(key):
            return CONVERSATIONAL_REPLIES[key]
    return "Got it! Feel free to describe an HCP interaction or ask me to make corrections to the form."


def detect_intent(user_message: str) -> str:
    msg = user_message.lower()
    edit_keywords = ["sorry", "actually", "wrong", "mistake", "change", "update",
                     "correct", "fix", "instead", "was actually", "meant", "not right"]
    if any(kw in msg for kw in edit_keywords):
        return "edit"
    summarize_keywords = ["summarize", "summary", "condense", "shorten", "brief"]
    if any(kw in msg for kw in summarize_keywords):
        return "summarize"
    search_keywords = ["search for", "find hcp", "look up", "who is dr"]
    if any(kw in msg for kw in search_keywords):
        return "search"
    return "log"


def agent_node(state: AgentState) -> AgentState:
    messages = state["messages"]
    form_state_str = json.dumps(state.get("form_state", {}))
    system = SystemMessage(content=f"""You are an AI assistant for a pharmaceutical CRM.
Help field reps log HCP interactions. Current form: {form_state_str}

Call ONE tool based on intent:
- log_interaction: for new interaction descriptions
- edit_interaction: when user says sorry/wrong/actually/change/fix
- summarize_topics: when user asks to summarize
- search_hcp: when user asks to search/find an HCP
- suggest_followups: when explicitly asked

Call only ONE tool. Be decisive.""")
    response = llm_with_tools.invoke([system] + list(messages))
    return {"messages": [response]}


tool_node = ToolNode(tools)


def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", END)
    return graph.compile()


compiled_graph = build_graph()


def run_agent(user_message: str, form_state: dict, chat_history: list) -> dict:
    # Handle conversational messages without hitting the LLM/tools
    if is_conversational(user_message):
        return {
            "assistant_message": get_conversational_reply(user_message),
            "form_updates": {},
            "suggestions": [],
            "action_type": "none",
            "tool_results": [],
        }

    messages = []
    for msg in chat_history[-4:]:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=user_message))

    result = compiled_graph.invoke({
        "messages": messages,
        "form_state": form_state,
        "tool_result": {},
        "intent": detect_intent(user_message),
    })

    form_updates = {}
    suggestions = []
    primary_action = None

    for msg in result["messages"]:
        if isinstance(msg, ToolMessage):
            try:
                data = json.loads(msg.content)
                action = data.get("action", "")
                primary_action = action
                if action == "log_interaction":
                    form_updates.update(data.get("fields", {}))
                elif action == "edit_interaction":
                    form_updates.update(data.get("fields", {}))
                elif action == "suggest_followups":
                    suggestions = data.get("suggestions", [])
                elif action == "summarize_topics":
                    if data.get("summary"):
                        form_updates["topics_discussed"] = data["summary"]
                elif action == "search_hcp":
                    if data.get("best_match"):
                        form_updates["hcp_name"] = data["best_match"]
            except (json.JSONDecodeError, TypeError):
                pass

    # Inline suggest after log (no second graph loop)
    if primary_action == "log_interaction" and form_updates:
        try:
            context = f"HCP: {form_updates.get('hcp_name','')}, Topics: {form_updates.get('topics_discussed','')}, Sentiment: {form_updates.get('sentiment','')}"
            sugg_result = suggest_followups.invoke({"interaction_context": context})
            if isinstance(sugg_result, dict):
                suggestions = sugg_result.get("suggestions", [])
        except Exception:
            pass

    # Build response message
    if primary_action == "log_interaction" and form_updates:
        hcp = form_updates.get("hcp_name", "HCP")
        sentiment = form_updates.get("sentiment", "neutral")
        materials = form_updates.get("materials_shared", [])
        mat_str = f"\n📎 Materials: {', '.join(materials)}" if materials else ""
        ai_response = (
            f"✅ Interaction logged!\n\n"
            f"👤 {hcp}  |  📅 {form_updates.get('date','today')}  |  💬 Sentiment: {sentiment}{mat_str}\n\n"
            f"The form has been filled. Need any corrections?"
        )
    elif primary_action == "edit_interaction" and form_updates:
        changed = ", ".join(k.replace("_", " ").title() for k in form_updates.keys())
        ai_response = f"✅ Updated: {changed}. All other fields remain unchanged."
    elif primary_action == "summarize_topics":
        ai_response = "✅ Topics summarized and updated in the form."
    elif primary_action == "search_hcp":
        best = form_updates.get("hcp_name")
        ai_response = f"🔍 Found: **{best}** — set in HCP Name field." if best else "🔍 No matching HCP found."
    elif primary_action == "suggest_followups":
        ai_response = "💡 Suggested follow-ups added below the form."
    else:
        ai_response = "I processed your request. Please check the form fields."

    return {
        "assistant_message": ai_response,
        "form_updates": form_updates,
        "suggestions": suggestions,
        "action_type": primary_action or "log",
        "tool_results": [],
    }
