# HARNESS: shared-state/rendering-in-app shows no Python agent at all (frontend only). The reader must
# guess one that reads/writes the board state; this is the quickstart adapter, unchanged.
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
