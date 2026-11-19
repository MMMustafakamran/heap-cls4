# Doc: docs.copilotkit.ai/react-native/claude-sdk-python/shared-state/agent-readonly (agent.py excerpt, verbatim).
# The page shows only the block that appends input_data.context to `system`: no function around it, no
# `system` base prompt, no loop, no server. Those lines are HARNESS (agents/_messages_loop.py).
from collections.abc import AsyncIterator  # HARNESS

from ag_ui.core import RunAgentInput  # HARNESS

from agents._messages_loop import run_loop  # HARNESS: the page's Messages API loop is never shown


async def run_agent_readonly(input_data: RunAgentInput) -> AsyncIterator[str]:  # HARNESS
    system = "You are a helpful assistant embedded in a CopilotKit app."  # HARNESS: quickstart system prompt
    # --- verbatim from the page ---
    context_entries = getattr(input_data, "context", None) or []
    if context_entries:
        context_lines: list[str] = []
        for entry in context_entries:
            if isinstance(entry, dict):
                description = entry.get("description")
                value = entry.get("value")
            else:
                description = getattr(entry, "description", None)
                value = getattr(entry, "value", None)
            if description:
                context_lines.append(f"{description}: {value}")
        if context_lines:
            system = f"{system}\n\nContext:\n" + "\n".join(context_lines)
    # --- end verbatim ---
    async for chunk in run_loop(input_data, system=system):  # HARNESS
        yield chunk
