# Doc: docs.copilotkit.ai/react-native/claude-sdk-python/shared-state (shared_state_read_write_agent.py, three
# excerpts, verbatim). The page never shows run_shared_state_read_write_agent, the imports, the client, the
# message conversion, normalize_claude_model or DEFAULT_ANTHROPIC_MODEL: those lines are HARNESS.
import json  # HARNESS: used by the excerpt, never imported on the page
import os  # HARNESS
import uuid  # HARNESS
from collections.abc import AsyncIterator  # HARNESS
from textwrap import dedent  # HARNESS: used by the excerpt, never imported on the page
from typing import Any  # HARNESS

import anthropic  # HARNESS: no install step / import on the page
from ag_ui.core import (  # HARNESS: imports never shown
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
from ag_ui.encoder import EventEncoder  # HARNESS

from agents._messages_loop import DEFAULT_ANTHROPIC_MODEL, normalize_claude_model, to_anthropic_messages  # HARNESS: undefined on the page

# --- verbatim from the page (step 1) ---
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
# --- end step 1 ---


async def run_shared_state_read_write_agent(input_data: RunAgentInput) -> AsyncIterator[str]:  # HARNESS: called by agent_server.py, never shown
    encoder = EventEncoder()  # HARNESS
    client = anthropic.AsyncAnthropic()  # HARNESS
    state = _state_dict(dict(input_data.state or {}))  # HARNESS
    system = SYSTEM_PROMPT  # HARNESS
    prefs_block = build_preferences_block(state["preferences"])  # HARNESS
    if prefs_block:  # HARNESS
        system = f"{system}\n\n{prefs_block}"  # HARNESS
    if state["notes"]:  # HARNESS: let Claude see the existing notes so it can send the FULL list
        system = f"{system}\n\nCurrent notes: {json.dumps(state['notes'])}"  # HARNESS
    messages, _ = to_anthropic_messages(input_data)  # HARNESS
    yield encoder.encode(RunStartedEvent(type=EventType.RUN_STARTED, thread_id=input_data.thread_id, run_id=input_data.run_id))  # HARNESS
    for _turn in range(5):  # HARNESS
        msg_id = str(uuid.uuid4())  # HARNESS
        tool_calls: list[dict[str, Any]] = []  # HARNESS
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
        # --- end step 2 ---
        text_open = False  # HARNESS: event streaming below is not on the page
        current: dict[str, Any] | None = None  # HARNESS
        async with stream_request as stream:  # HARNESS
            async for event in stream:  # HARNESS
                if event.type == "content_block_start" and event.content_block.type == "tool_use":  # HARNESS
                    current = {"id": event.content_block.id, "name": event.content_block.name, "args": ""}  # HARNESS
                    yield encoder.encode(ToolCallStartEvent(type=EventType.TOOL_CALL_START, tool_call_id=current["id"], tool_call_name=current["name"], parent_message_id=msg_id))  # HARNESS
                elif event.type == "content_block_delta" and event.delta.type == "text_delta":  # HARNESS
                    if not text_open:  # HARNESS
                        text_open = True  # HARNESS
                        yield encoder.encode(TextMessageStartEvent(type=EventType.TEXT_MESSAGE_START, message_id=msg_id, role="assistant"))  # HARNESS
                    yield encoder.encode(TextMessageContentEvent(type=EventType.TEXT_MESSAGE_CONTENT, message_id=msg_id, delta=event.delta.text))  # HARNESS
                elif event.type == "content_block_delta" and event.delta.type == "input_json_delta" and current:  # HARNESS
                    current["args"] += event.delta.partial_json  # HARNESS
                    if event.delta.partial_json:  # HARNESS
                        yield encoder.encode(ToolCallArgsEvent(type=EventType.TOOL_CALL_ARGS, tool_call_id=current["id"], delta=event.delta.partial_json))  # HARNESS
                elif event.type == "content_block_stop" and current:  # HARNESS
                    yield encoder.encode(ToolCallEndEvent(type=EventType.TOOL_CALL_END, tool_call_id=current["id"]))  # HARNESS
                    current["input"] = json.loads(current["args"] or "{}")  # HARNESS
                    tool_calls.append(current)  # HARNESS
                    current = None  # HARNESS
            final = await stream.get_final_message()  # HARNESS
        if text_open:  # HARNESS
            yield encoder.encode(TextMessageEndEvent(type=EventType.TEXT_MESSAGE_END, message_id=msg_id))  # HARNESS
        messages.append({"role": "assistant", "content": [b.model_dump(exclude_none=True) for b in final.content]})  # HARNESS
        if not tool_calls:  # HARNESS
            break  # HARNESS
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
        # --- end step 3 ---
    yield encoder.encode(RunFinishedEvent(type=EventType.RUN_FINISHED, thread_id=input_data.thread_id, run_id=input_data.run_id))  # HARNESS
