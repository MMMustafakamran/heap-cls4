# Doc: docs.copilotkit.ai/react-native/claude-sdk-python/human-in-the-loop/governed-actions. The only Python on
# the page is a LangGraph tool (langchain_core.tools.tool + langgraph.types.interrupt): wrong framework, it
# can't run on a Claude Agent SDK backend and there is no Claude equivalent of interrupt() shown. It is kept
# below as a string (verbatim) so the harness still imports.
GOVERNED_ACTIONS_DOC_AGENT = r'''
import hashlib
import json

from langchain_core.tools import tool
from langgraph.types import interrupt


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email. The user must approve it first."""
    arguments = {"to": to, "subject": subject, "body": body}
    action = {
        # Derive the id from the arguments: LangGraph runs the tool again on resume.
        "id": hashlib.sha256(json.dumps(arguments, sort_keys=True).encode()).hexdigest()[:16],
        "summary": f"Send an email to {to}",
        "tool": "send_email",
        "reference": "policy:outbound-email",
        "verdict": "require_approval",
        "arguments": arguments,
    }

    response = interrupt({"action": action})

    if (
        isinstance(response, dict)
        and response.get("approved")
        and response.get("actionId") == action["id"]
        and response.get("reference") == action["reference"]
    ):
        deliver_email(to, subject, body)  # your own email client
        return f"Email sent to {to}."

    return "The user did not approve this action. The email was not sent."
'''  # HARNESS: doc code kept as text (LangGraph, not importable here)

# HARNESS: so the useHumanInTheLoop half (approve_governed_action) can be tried at all, the agent is the
# HARNESS: quickstart main.py adapter (docs.copilotkit.ai/claude-sdk-python/quickstart, "Use an existing agent"), verbatim options
import os  # HARNESS

from ag_ui_claude_sdk import ClaudeAgentAdapter  # HARNESS

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
