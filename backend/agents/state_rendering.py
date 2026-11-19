# Doc: docs.copilotkit.ai/react-native/claude-sdk-python/generative-ui/state-rendering
# The page shows three excerpts of shared_state_read_write_agent.py and the agent_server.py endpoint, verbatim
# below. It never shows run_shared_state_read_write_agent (the loop the excerpts sit in), normalize_claude_model,
# DEFAULT_ANTHROPIC_MODEL, client / system / messages / tool_calls / msg_id, or any import. Those are HARNESS.
# Note: this backend writes `preferences` / `notes`; the page's frontend (ResearchProgress.tsx) reads
# `status` / `draft` / `completed` / `total` from an agent named "researcher". Kept as published.
import json  # HARNESS: missing import
import os  # HARNESS: missing import
import uuid  # HARNESS: message ids for the harness loop
from collections.abc import AsyncIterator  # HARNESS: missing import
from textwrap import dedent  # HARNESS: missing import
from typing import Any  # HARNESS: missing import

import anthropic  # HARNESS: missing import (the prose says the demo calls the Messages API directly)
from ag_ui.core import (  # HARNESS: missing import
    EventType,
    RunAgentInput,
    RunFinishedEvent,
    RunStartedEvent,
    StateSnapshotEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallResultEvent,
    ToolCallStartEvent,
)
from ag_ui.encoder import EventEncoder  # HARNESS: missing import
from fastapi import APIRouter, Request  # HARNESS: missing import (agent_server.py's app is never shown)
from fastapi.responses import StreamingResponse  # HARNESS: missing import

DEFAULT_ANTHROPIC_MODEL = "claude-opus-4-8"  # HARNESS: never defined; quickstart main.py default


def normalize_claude_model(model: str) -> str:  # HARNESS: never defined on the page
    return model


# --- verbatim from the page (shared_state_read_write_agent.py, step 1) ---
SYSTEM_PROMPT = dedent("""
    You are a helpful, concise assistant.

    The user's preferences are supplied via shared state and added at the
    start of every turn — always respect them. Address the user by name
    when known, match the requested tone, and respond in the requested
    language.

    When the user asks you to "remember" something, or you observe
    something worth surfacing in the UI's notes panel, call the
    ``set_notes`` tool with the FULL updated list of short notes
    (existing notes + new ones, not a diff). Keep each note short
    (< 120 characters). After updating notes, briefly acknowledge what
    you remembered.
""").strip()


SET_NOTES_TOOL: dict[str, Any] = {
    "name": "set_notes",
    "description": (
        "Replace the notes array in shared state with the FULL updated "
        "list. Always include every existing note plus any new ones, "
        "not a diff. Keep each note short (< 120 chars)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "notes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Full list of short note strings to persist.",
            },
        },
        "required": ["notes"],
    },
}


def build_preferences_block(prefs: dict[str, Any] | None) -> str | None:
    """Render the user-supplied preferences as an injectable prompt block.

    Returns ``None`` when no recognised keys are present so the system
    prompt is left untouched.
    """
    if not isinstance(prefs, dict) or not prefs:
        return None
    lines = ["The user has shared these preferences with you:"]
    if prefs.get("name"):
        lines.append(f"- Name: {prefs['name']}")
    if prefs.get("tone"):
        lines.append(f"- Preferred tone: {prefs['tone']}")
    if prefs.get("language"):
        lines.append(f"- Preferred language: {prefs['language']}")
    interests = prefs.get("interests") or []
    if isinstance(interests, list) and interests:
        lines.append(f"- Interests: {', '.join(str(i) for i in interests)}")
    if len(lines) == 1:
        # No recognised fields — don't emit a header with no content.
        return None
    lines.append(
        "Tailor every response to these preferences. Address the user "
        "by name when appropriate."
    )
    return "\n".join(lines)


def _state_dict(state: dict[str, Any]) -> dict[str, Any]:
    """Coerce the AG-UI raw state envelope into the slots we care about."""
    return {
        "preferences": state.get("preferences") or {},
        "notes": list(state.get("notes") or []),
    }
# --- end verbatim ---


def _to_anthropic_messages(input_data: RunAgentInput) -> list[dict[str, Any]]:  # HARNESS: never shown
    out: list[dict[str, Any]] = []
    for m in input_data.messages:
        if m.role in ("user", "assistant") and isinstance(getattr(m, "content", None), str) and m.content:
            out.append({"role": m.role, "content": m.content})
    return out


async def run_shared_state_read_write_agent(input_data: RunAgentInput) -> AsyncIterator[str]:  # HARNESS: never shown
    encoder = EventEncoder()  # HARNESS
    client = anthropic.AsyncAnthropic()  # HARNESS
    state = _state_dict(input_data.state if isinstance(input_data.state, dict) else {})  # HARNESS
    prefs_block = build_preferences_block(state["preferences"])  # HARNESS
    system = SYSTEM_PROMPT + ("\n\n" + prefs_block if prefs_block else "")  # HARNESS
    messages = _to_anthropic_messages(input_data)  # HARNESS
    yield encoder.encode(RunStartedEvent(type=EventType.RUN_STARTED, thread_id=input_data.thread_id, run_id=input_data.run_id))  # HARNESS
    for _turn in range(10):  # HARNESS: the loop the excerpts sit in
        msg_id = str(uuid.uuid4())  # HARNESS
        # --- verbatim from the page (step 2) ---
        stream_request = client.messages.stream(
            model=normalize_claude_model(
                os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
            ),
            max_tokens=2048,
            system=system,
            messages=messages,
            tools=[SET_NOTES_TOOL],
        )
        # --- end verbatim ---
        async with stream_request as s:  # HARNESS: consume the stream, emit AG-UI text events
            started = False  # HARNESS
            async for text in s.text_stream:  # HARNESS
                if not started:  # HARNESS
                    yield encoder.encode(TextMessageStartEvent(type=EventType.TEXT_MESSAGE_START, message_id=msg_id, role="assistant"))  # HARNESS
                    started = True  # HARNESS
                yield encoder.encode(TextMessageContentEvent(type=EventType.TEXT_MESSAGE_CONTENT, message_id=msg_id, delta=text))  # HARNESS
            if started:  # HARNESS
                yield encoder.encode(TextMessageEndEvent(type=EventType.TEXT_MESSAGE_END, message_id=msg_id))  # HARNESS
            final = await s.get_final_message()  # HARNESS
        messages.append({"role": "assistant", "content": [b.model_dump(exclude_none=True) for b in final.content]})  # HARNESS
        tool_calls = [{"id": b.id, "name": b.name, "input": b.input} for b in final.content if b.type == "tool_use"]  # HARNESS
        if not tool_calls:  # HARNESS
            break  # HARNESS
        for tc in tool_calls:  # HARNESS: announce the tool call so the UI sees it
            yield encoder.encode(ToolCallStartEvent(type=EventType.TOOL_CALL_START, tool_call_id=tc["id"], tool_call_name=tc["name"], parent_message_id=msg_id))  # HARNESS
            yield encoder.encode(ToolCallArgsEvent(type=EventType.TOOL_CALL_ARGS, tool_call_id=tc["id"], delta=json.dumps(tc["input"])))  # HARNESS
            yield encoder.encode(ToolCallEndEvent(type=EventType.TOOL_CALL_END, tool_call_id=tc["id"]))  # HARNESS
        # --- verbatim from the page (step 3) ---
        # Execute set_notes by mutating shared state and emitting a
        # StateSnapshotEvent so the UI re-renders the agent-authored
        # notes. This is the agent-side half of the WRITE direction.
        tool_results: list[dict[str, Any]] = []
        for tc in tool_calls:
            if tc["name"] == "set_notes":
                notes = tc["input"].get("notes") or []
                if isinstance(notes, list):
                    state["notes"] = [str(n) for n in notes]
                result_text = json.dumps({"status": "ok", "count": len(state["notes"])})
                yield encoder.encode(
                    StateSnapshotEvent(type=EventType.STATE_SNAPSHOT, snapshot=state)
                )
            else:
                result_text = json.dumps({"error": f"unknown tool {tc['name']}"})

            yield encoder.encode(
                ToolCallResultEvent(
                    type=EventType.TOOL_CALL_RESULT,
                    tool_call_id=tc["id"],
                    message_id=f"{msg_id}-tool-result-{tc['id']}",
                    content=result_text,
                )
            )
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tc["id"],
                    "content": result_text,
                }
            )
        messages.append({"role": "user", "content": tool_results})
        # --- end verbatim ---
    yield encoder.encode(RunFinishedEvent(type=EventType.RUN_FINISHED, thread_id=input_data.thread_id, run_id=input_data.run_id))  # HARNESS


app = APIRouter()  # HARNESS: agent_server.py's `app` is never shown; a router mounted by rn_genui_main.py


# --- verbatim from the page (agent_server.py) ---
@app.post("/shared-state-read-write")
async def shared_state_read_write_endpoint(request: Request) -> StreamingResponse:
    """Bidirectional shared state demo — UI writes preferences, agent writes notes.

    Uses its own streaming loop (not the shared sales-assistant
    ``run_agent``) because the state schema, tools, and prompt-injection
    middleware are all demo-specific.
    """
    body = await request.json()
    input_data = RunAgentInput(**body)

    async def event_stream() -> AsyncIterator[str]:
        async for chunk in run_shared_state_read_write_agent(input_data):
            yield chunk

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
# --- end verbatim ---
