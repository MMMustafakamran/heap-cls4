# HARNESS: docs.copilotkit.ai/react-native/claude-sdk-python/human-in-the-loop shows no Python agent at all
# (only a web page.tsx useHumanInTheLoop excerpt and src/MeetingApproval.tsx). The prose says the agent
# "calls an approval tool" and the run continues with the result, so this is the quickstart main.py adapter
# (options verbatim); the frontend tool from useHumanInTheLoop reaches it through the AG-UI run input.
import os  # HARNESS: from quickstart main.py

from ag_ui_claude_sdk import ClaudeAgentAdapter  # HARNESS: from quickstart main.py

adapter = ClaudeAgentAdapter(  # HARNESS: quickstart main.py adapter
    name="claude_agent",
    options={
        "model": os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8"),
        "system_prompt": "You are a helpful assistant embedded in a CopilotKit app.",
        "tools": [],
        "permission_mode": "dontAsk",
        "max_turns": 10,
    },
)
