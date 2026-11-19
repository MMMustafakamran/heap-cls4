# Doc: docs.copilotkit.ai/react-native/claude-sdk-python/shared-state/streaming. Verbatim: the
# state_streaming_backend.py block and the agent.py branch ("runs inside the streamed tool-argument handler").
# Never shown: that handler, the loop, the client, the prompt, how WRITE_DOCUMENT_TOOL_SCHEMA is passed to
# Claude, the server. Those lines are HARNESS (agents/_messages_loop.py). The prose says "save the final
# value when the tool finishes" but shows no code for it.
from ag_ui.core import RunAgentInput  # HARNESS

from agents._messages_loop import run_loop  # HARNESS

# --- verbatim from the page (src/app/demos/shared-state-streaming/state_streaming_backend.py) ---
import json
from collections.abc import AsyncIterator
from typing import Any

from ag_ui.core import EventType, StateSnapshotEvent
from ag_ui.encoder import EventEncoder
from pydantic import BaseModel


class AgentState(BaseModel):
    document: str = ""


WRITE_DOCUMENT_TOOL_SCHEMA: dict[str, Any] = {
    "name": "write_document",
    "description": "Write a document into shared agent state.",
    "input_schema": {
        "type": "object",
        "properties": {
            "document": {
                "type": "string",
                "description": "The full document text to render in shared state.",
            },
        },
        "required": ["document"],
    },
}


def _partial_json_string_property(source: str, key: str) -> str | None:
    """Return the current value of a streamed JSON string property."""
    marker = json.dumps(key)
    key_pos = source.find(marker)
    if key_pos < 0:
        return None
    colon_pos = source.find(":", key_pos)
    if colon_pos < 0:
        # The colon hasn't streamed yet (e.g. source is `{"document`); bail out
        # rather than letting find(":") return -1 and matching the key's own
        # opening quote, which would report the key name as the value.
        return None
    value_start = source.find('"', colon_pos + 1)
    if value_start < 0:
        return None

    raw_chars: list[str] = []
    escaped = False
    for char in source[value_start + 1 :]:
        if escaped:
            raw_chars.append("\\" + char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == '"':
            break
        else:
            raw_chars.append(char)

    try:
        return json.loads(f'"{"".join(raw_chars)}"')
    except json.JSONDecodeError:
        return None


async def stream_document_state(
    anthropic_stream: AsyncIterator[Any],
    state: AgentState,
) -> AsyncIterator[str]:
    encoder = EventEncoder()
    current_tool_name: str | None = None
    current_tool_args = ""
    last_streamed_document = state.document

    async for event in anthropic_stream:
        if (
            event.type == "content_block_start"
            and event.content_block.type == "tool_use"
        ):
            current_tool_name = event.content_block.name
            current_tool_args = ""
            continue

        if (
            event.type != "content_block_delta"
            or event.delta.type != "input_json_delta"
        ):
            continue

        current_tool_args += event.delta.partial_json
        if current_tool_name != "write_document":
            continue

        streamed_document = _partial_json_string_property(
            current_tool_args,
            "document",
        )
        if streamed_document is None or streamed_document == last_streamed_document:
            continue

        state.document = streamed_document
        last_streamed_document = streamed_document
        yield encoder.encode(
            StateSnapshotEvent(
                type=EventType.STATE_SNAPSHOT,
                snapshot=state.model_dump(),
            )
        )

# --- end state_streaming_backend.py ---


async def run_state_streaming(input_data: RunAgentInput) -> AsyncIterator[str]:  # HARNESS
    state = AgentState(document=str((input_data.state or {}).get("document") or ""))  # HARNESS
    encoder = EventEncoder()  # HARNESS
    last = {"doc": state.document}  # HARNESS

    async def on_tool_args(current_tool_name: str, current_tool_args: str, _s: dict) -> AsyncIterator[str]:  # HARNESS: the "streamed tool-argument handler"
        last_streamed_document = last["doc"]  # HARNESS
        # --- verbatim from the page (agent.py) ---
        if current_tool_name == "write_document":
            streamed_document = _partial_json_string_property(
                current_tool_args,
                "document",
            )
            if (
                streamed_document is not None
                and streamed_document != last_streamed_document
            ):
                state.document = streamed_document
                last_streamed_document = streamed_document
                yield encoder.encode(
                    StateSnapshotEvent(
                        type=EventType.STATE_SNAPSHOT,
                        snapshot=state.model_dump(),
                    )
                )
        # --- end agent.py ---
        last["doc"] = last_streamed_document  # HARNESS

    async def write_document(args: dict, s: dict) -> str:  # HARNESS: final value + tool result, not on the page
        state.document = str(args.get("document") or state.document)  # HARNESS
        s.update(state.model_dump())  # HARNESS
        return "Document written."  # HARNESS

    async for chunk in run_loop(  # HARNESS
        input_data,
        system="You are a writing assistant. When asked to write something, call write_document with the full text, then reply with one short sentence.",  # HARNESS: no prompt on the page
        tools=[WRITE_DOCUMENT_TOOL_SCHEMA],  # HARNESS
        server_tools={"write_document": write_document},  # HARNESS
        state=state.model_dump(),  # HARNESS
        on_tool_args=on_tool_args,  # HARNESS
    ):
        yield chunk
