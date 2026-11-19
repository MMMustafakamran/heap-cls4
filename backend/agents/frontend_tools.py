# Doc: docs.copilotkit.ai/react-native/claude-sdk-python/frontend-tools ("Forward browser tools to Claude", agent.py).
# The same agent.py excerpt is on generative-ui/tool-based, so this file serves /frontend-tools and /tool-based.
# The page shows only the helper below: no imports, no agent loop, no server, no install step.
import os  # HARNESS: needed by the quickstart adapter below
from typing import Any  # HARNESS: the excerpt uses Any but never imports it

from ag_ui.core import RunAgentInput  # HARNESS: the excerpt uses RunAgentInput but never imports it
from ag_ui_claude_sdk import ClaudeAgentAdapter  # HARNESS: the prose names it ("needs no such conversion"), the page never shows it


# --- verbatim from the page (agent.py) ---
def _build_frontend_tools(input_data: RunAgentInput) -> list[dict[str, Any]]:
    """Extract frontend-defined tools from the AG-UI request.

    The CopilotKit runtime forwards frontend tool definitions (registered
    via ``useFrontendTool``, ``useHumanInTheLoop``, etc.) in
    ``input_data.tools``. We convert them to the Anthropic ``tools``
    schema so the LLM can call them. The runtime intercepts the resulting
    tool-call events and routes them to the frontend for resolution.
    """
    out: list[dict[str, Any]] = []
    for t in input_data.tools or []:
        name = getattr(t, "name", None) or (
            t.get("name") if isinstance(t, dict) else None
        )
        description = getattr(t, "description", None) or (
            t.get("description", "") if isinstance(t, dict) else ""
        )
        parameters = getattr(t, "parameters", None) or (
            t.get("parameters", {}) if isinstance(t, dict) else {}
        )
        if not name:
            continue
        out.append(
            {
                "name": name,
                "description": description or "",
                "input_schema": parameters or {"type": "object", "properties": {}},
            }
        )
    return out
# --- end verbatim ---


# HARNESS: the helper above feeds a Messages API loop the page never shows. The prose says the published
# ClaudeAgentAdapter needs no conversion ("Pass the run input to the adapter and frontend tools work with
# no extra wiring"), so the agent actually served is the quickstart main.py adapter, options verbatim.
adapter = ClaudeAgentAdapter(  # HARNESS
    name="claude_agent",
    options={
        "model": os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8"),
        "system_prompt": "You are a helpful assistant embedded in a CopilotKit app.",
        "tools": [],
        "permission_mode": "dontAsk",
        "max_turns": 10,
    },
)
