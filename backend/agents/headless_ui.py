# HARNESS: the headless-ui page shows no Claude Agent SDK agent; this is the quickstart main.py adapter
# (docs.copilotkit.ai/claude-sdk-python/quickstart, "Use an existing agent"), served at /headless-ui.
import os  # HARNESS: from quickstart main.py

from ag_ui_claude_sdk import ClaudeAgentAdapter  # HARNESS: from quickstart main.py

adapter = ClaudeAgentAdapter(  # HARNESS: quickstart main.py adapter, verbatim options
    name="claude_agent",
    options={
        "model": os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8"),
        "system_prompt": "You are a helpful assistant embedded in a CopilotKit app.",
        "tools": [],
        "permission_mode": "dontAsk",
        "max_turns": 10,
    },
)
