# HARNESS: human-in-the-loop/headless shows no Python agent; the schedule_meeting frontend tool needs one
# that forwards frontend tools. Quickstart adapter, unchanged (the frontend-tools page says it needs no conversion).
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
