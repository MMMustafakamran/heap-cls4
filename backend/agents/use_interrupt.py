# Doc: docs.copilotkit.ai/react-native/claude-sdk-python/human-in-the-loop/useInterrupt
# The page's backend is only SYSTEM_PROMPT (src/agents/interrupt_agent.py), verbatim below. It never imports
# dedent and never shows the agent or server that uses the prompt; those are filled in from quickstart main.py.
import os  # HARNESS: from quickstart main.py
from textwrap import dedent  # HARNESS: the excerpt calls dedent but never imports it

from ag_ui_claude_sdk import ClaudeAgentAdapter  # HARNESS: from quickstart main.py

# --- verbatim from the page (src/agents/interrupt_agent.py) ---
SYSTEM_PROMPT = dedent("""
    You are a scheduling assistant. Whenever the user asks you to book a call
    or schedule a meeting, you MUST call the `schedule_meeting` tool. Pass a
    short `topic` describing the purpose of the meeting and, if known, an
    `attendee` describing who the meeting is with.

    The `schedule_meeting` tool is implemented on the client: it surfaces a
    time-picker UI to the user and returns the user's selection. After the
    tool returns, briefly confirm whether the meeting was scheduled and at
    what time, or note that the user cancelled. Do NOT ask for approval
    yourself — always call the tool and let the picker handle the decision.

    Keep responses short and friendly. After you finish executing tools,
    always send a brief final assistant message summarizing what happened so
    the message persists.
""").strip()
# --- end verbatim ---

adapter = ClaudeAgentAdapter(  # HARNESS: quickstart main.py adapter, with the page's SYSTEM_PROMPT
    name="claude_agent",
    options={
        "model": os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8"),
        "system_prompt": SYSTEM_PROMPT,  # HARNESS: the page's prompt in place of the quickstart one
        "tools": [],
        "permission_mode": "dontAsk",
        "max_turns": 10,
    },
)
