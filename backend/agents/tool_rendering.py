# Doc: docs.copilotkit.ai/react-native/claude-sdk-python/generative-ui/tool-rendering
# The page shows two excerpts of claude_agent_sdk_adapter.py (run_with_claude_agent_sdk, _make_sdk_tool) and
# weather_tool.py (GET_WEATHER_TOOL, get_weather), verbatim below. Everything they call but never define
# (_build_sdk_tools, _set_state, _with_initial_state, _normalize_claude_agent_sdk_model, ExecuteTool,
# COPILOTKIT_MCP_SERVER_NAME / COPILOTKIT_TOOL_PREFIX, the execute_tool handler, every import, the server)
# is filled in below and marked HARNESS.
import asyncio  # HARNESS: missing import
import os  # HARNESS: model env, as in quickstart main.py
from collections.abc import AsyncIterator, Callable  # HARNESS: missing import
from typing import Any  # HARNESS: missing import

from ag_ui.core import EventType, RunAgentInput, StateSnapshotEvent  # HARNESS: missing import
from ag_ui.encoder import EventEncoder  # HARNESS: missing import
from ag_ui_claude_sdk import ClaudeAgentAdapter  # HARNESS: missing import
from claude_agent_sdk import create_sdk_mcp_server  # HARNESS: missing import
from claude_agent_sdk import tool as sdk_tool  # HARNESS: missing import (the excerpt calls it sdk_tool)

COPILOTKIT_MCP_SERVER_NAME = "copilotkit"  # HARNESS: never defined on the page
COPILOTKIT_TOOL_PREFIX = f"mcp__{COPILOTKIT_MCP_SERVER_NAME}__"  # HARNESS: never defined (SDK naming mcp__<server>__<tool>)
ExecuteTool = Callable[[str, dict[str, Any], Any, Any], tuple[str, Any]]  # HARNESS: never defined


# --- verbatim from the page (src/app/demos/tool-rendering/weather_tool.py) ---
# Anthropic tool schema — passed via the `tools` parameter on
# `client.messages.create(...)` / `.stream(...)`. Claude calls this
# tool by name; the runtime dispatches to the matching handler below.
GET_WEATHER_TOOL: dict[str, Any] = {
    "name": "get_weather",
    "description": (
        "Get the current weather for a given location. Useful on its "
        "own for weather questions, and a great companion to "
        "`search_flights` — always consider checking the weather at a "
        "destination the user is flying to."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city or region to get weather for.",
            },
        },
        "required": ["location"],
    },
}


def get_weather(location: str) -> dict[str, Any]:
    """Handler invoked when Claude calls the `get_weather` tool."""
    return {
        "city": location,
        "temperature": 68,
        "humidity": 55,
        "wind_speed": 10,
        "conditions": "Sunny",
    }
# --- end verbatim ---


def _normalize_claude_agent_sdk_model(model: str) -> str:  # HARNESS: never defined on the page
    return model


def _set_state(next_state: Any, state_box: dict[str, Any], pending: list[Any]) -> None:  # HARNESS: never defined
    state_box["state"] = next_state
    pending.append(next_state)


def _with_initial_state(input_data: RunAgentInput, state: Any) -> RunAgentInput:  # HARNESS: never defined
    return input_data.model_copy(update={"state": state})


def _build_sdk_tools(tools, *, execute_tool, get_state, set_state) -> list[Any]:  # HARNESS: never defined
    return [
        _make_sdk_tool(s, execute_tool=execute_tool, get_state=get_state, set_state=set_state)
        for s in tools
    ]


# --- verbatim from the page (claude_agent_sdk_adapter.py, "Register the backend tools") ---
async def run_with_claude_agent_sdk(
    input_data: RunAgentInput,
    *,
    system_prompt: str,
    tools: list[dict[str, Any]],
    state: Any,
    model: str,
    execute_tool: ExecuteTool,
    max_turns: int = 10,
) -> AsyncIterator[str]:
    """Run through the official AG-UI Claude adapter and emit SSE chunks."""

    encoder = EventEncoder()
    state_box = {"state": state}
    pending_state_snapshots: list[Any] = []
    sdk_tools = _build_sdk_tools(
        tools,
        execute_tool=execute_tool,
        get_state=lambda: state_box["state"],
        set_state=lambda next_state: _set_state(
            next_state,
            state_box,
            pending_state_snapshots,
        ),
    )

    options: dict[str, Any] = {
        "model": _normalize_claude_agent_sdk_model(model),
        "system_prompt": system_prompt,
        "tools": [],
        "permission_mode": "dontAsk",
        "max_turns": max_turns,
    }

    if sdk_tools:
        options["mcp_servers"] = {
            COPILOTKIT_MCP_SERVER_NAME: create_sdk_mcp_server(
                COPILOTKIT_MCP_SERVER_NAME,
                "1.0.0",
                tools=sdk_tools,
            )
        }
        options["allowed_tools"] = [
            f"{COPILOTKIT_TOOL_PREFIX}{schema['name']}" for schema in tools
        ]

    adapter = ClaudeAgentAdapter(
        name="claude-sdk-python",
        options=options,
    )
    run_input = _with_initial_state(input_data, state)

    async for event in adapter.run(run_input):
        if event.type == EventType.TOOL_CALL_RESULT and pending_state_snapshots:
            yield encoder.encode(
                StateSnapshotEvent(
                    type=EventType.STATE_SNAPSHOT,
                    snapshot=pending_state_snapshots.pop(0),
                )
            )
        yield encoder.encode(event)
# --- end verbatim ---


# --- verbatim from the page (claude_agent_sdk_adapter.py, "Call the CopilotKit tool handler") ---
def _make_sdk_tool(
    schema: dict[str, Any],
    *,
    execute_tool: ExecuteTool,
    get_state: Callable[[], Any],
    set_state: Callable[[Any], None],
) -> Any:
    name = schema["name"]
    description = schema.get("description", "")
    input_schema = schema.get("input_schema", {"type": "object", "properties": {}})

    @sdk_tool(name, description, input_schema)
    async def sdk_tool_handler(args: dict[str, Any]):
        try:
            # Offload to a worker thread: execute_tool may run a synchronous
            # anthropic.Anthropic() LLM round-trip (the generate_a2ui branch),
            # which would otherwise block the uvicorn event loop and wedge the
            # :8000 /health endpoint under load.
            result_text, next_state = await asyncio.to_thread(
                execute_tool,
                name,
                dict(args or {}),
                get_state(),
                None,
            )
            if next_state is not None:
                set_state(next_state)
            return {"content": [{"type": "text", "text": result_text}]}
        except Exception as exc:
            return {
                "content": [{"type": "text", "text": str(exc)}],
                "is_error": True,
            }

    return sdk_tool_handler
# --- end verbatim ---


def execute_tool(name: str, args: dict[str, Any], state: Any, _ctx: Any) -> tuple[str, Any]:  # HARNESS: never shown
    import json  # HARNESS

    if name == "get_weather":  # HARNESS: dispatch to the page's handler
        return json.dumps(get_weather(**args)), None
    raise ValueError(f"unknown tool {name}")  # HARNESS


def stream(input_data: RunAgentInput) -> AsyncIterator[str]:  # HARNESS: the page never shows the caller
    return run_with_claude_agent_sdk(
        input_data,
        system_prompt="You are a helpful assistant embedded in a CopilotKit app.",  # HARNESS: quickstart prompt
        tools=[GET_WEATHER_TOOL],
        state=input_data.state or {},
        model=os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8"),  # HARNESS: quickstart model default
        execute_tool=execute_tool,
    )
