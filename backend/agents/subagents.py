# Doc: docs.copilotkit.ai/react-native/claude-sdk-python/multi-agent/subagents (src/agents/subagents_agent.py,
# verbatim; the page repeats _delegation_tool_schema / SUPERVISOR_TOOLS three times, kept once). Never shown:
# imports, run_subagents_agent ("see the subagents-delegation-flow region": that region is not on the page),
# how a delegation is written into `delegations`, normalize_claude_model, DEFAULT_ANTHROPIC_MODEL,
# ANTHROPIC_SUBAGENT_MODEL, the server, and any frontend. Lines marked HARNESS.
import os  # HARNESS
import uuid  # HARNESS
from collections.abc import AsyncIterator  # HARNESS
from typing import Any  # HARNESS

import anthropic  # HARNESS
from ag_ui.core import RunAgentInput  # HARNESS

from agents._messages_loop import DEFAULT_ANTHROPIC_MODEL, normalize_claude_model, run_loop  # HARNESS: undefined on the page

# --- verbatim from the page ---
# Each sub-agent is defined by its own system prompt; `_invoke_sub_agent`
# (below) issues a single-shot Anthropic call as that sub-agent. They
# don't share memory or tools with the supervisor — the supervisor only
# ever sees what the sub-agent returns as a tool result.
SUB_AGENT_PROMPTS: dict[str, str] = {
    "research_agent": (
        "You are a research sub-agent. Given a topic, produce a concise "
        "bulleted list of 3-5 key facts. No preamble, no closing."
    ),
    "writing_agent": (
        "You are a writing sub-agent. Given a brief and optional source "
        "facts, produce a polished 1-paragraph draft. Be clear and "
        "concrete. No preamble."
    ),
    "critique_agent": (
        "You are an editorial critique sub-agent. Given a draft, give "
        "2-3 crisp, actionable critiques. No preamble."
    ),
}


SUPERVISOR_SYSTEM_PROMPT = (
    "You are a supervisor agent that coordinates three specialized "
    "sub-agents to produce high-quality deliverables.\n\n"
    "Available sub-agents (call them as tools):\n"
    "  - research_agent: gathers facts on a topic.\n"
    "  - writing_agent: turns facts + a brief into a polished draft.\n"
    "  - critique_agent: reviews a draft and suggests improvements.\n\n"
    "For most non-trivial user requests, delegate in sequence: "
    "research -> write -> critique. Pass the relevant facts/draft "
    "through the `task` argument of each tool. Keep your own messages "
    "short — explain the plan once, delegate, then return a concise "
    "summary once done. The UI shows the user a live log of every "
    "sub-agent delegation, including the in-flight 'running' state."
)


# The supervisor delegates by calling tools. Each entry in
# `SUPERVISOR_TOOLS` is an Anthropic tool schema that the supervisor LLM
# "calls" to delegate work; the run loop in `run_subagents_agent` (see
# the subagents-delegation-flow region) runs the matching sub-agent
# synchronously, records the delegation into shared agent state, and
# returns the sub-agent's output as a tool_result the supervisor can
# read on its next step.
def _delegation_tool_schema(name: str, description: str) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": (
                        "The full task description to hand to the "
                        "sub-agent. Pass relevant prior facts/drafts "
                        "verbatim — the sub-agent has no shared memory "
                        "with the supervisor."
                    ),
                }
            },
            "required": ["task"],
        },
    }


SUPERVISOR_TOOLS: list[dict[str, Any]] = [
    _delegation_tool_schema(
        "research_agent",
        "Delegate a research task. Returns a bulleted list of key facts.",
    ),
    _delegation_tool_schema(
        "writing_agent",
        (
            "Delegate a drafting task. Pass relevant facts in `task`. "
            "Returns a polished paragraph."
        ),
    ),
    _delegation_tool_schema(
        "critique_agent",
        "Delegate a critique task. Returns 2-3 actionable critiques.",
    ),
]


async def _invoke_sub_agent(
    client: anthropic.AsyncAnthropic,
    sub_agent: str,
    task: str,
) -> str:
    """Issue a single-shot Anthropic call as the named sub-agent.

    Returns the concatenated text content of the response. Raises any
    SDK exception so the caller can mark the delegation as ``failed``.
    """
    response = await client.messages.create(
        model=normalize_claude_model(
            os.getenv("ANTHROPIC_SUBAGENT_MODEL", DEFAULT_ANTHROPIC_MODEL)
        ),
        max_tokens=1024,
        system=SUB_AGENT_PROMPTS[sub_agent],
        messages=[{"role": "user", "content": task}],
    )
    parts: list[str] = []
    for block in response.content:
        if getattr(block, "type", None) == "text":
            parts.append(getattr(block, "text", ""))
    text = "".join(parts).strip()
    if not text:
        raise RuntimeError("sub-agent returned empty response")
    return text
# --- end verbatim ---


async def run_subagents_agent(input_data: RunAgentInput) -> AsyncIterator[str]:  # HARNESS: never shown
    client = anthropic.AsyncAnthropic()  # HARNESS
    state: dict[str, Any] = dict(input_data.state or {})  # HARNESS
    state["delegations"] = list(state.get("delegations") or [])  # HARNESS: merged by id, per the page's callout

    def make_tool(name: str):  # HARNESS
        async def run(args: dict, s: dict) -> str:  # HARNESS
            entry = {"id": str(uuid.uuid4()), "sub_agent": name, "task": args.get("task", ""), "status": "running"}  # HARNESS
            try:  # HARNESS
                entry["result"] = await _invoke_sub_agent(client, name, str(args.get("task", "")))  # HARNESS
                entry["status"] = "completed"  # HARNESS
            except Exception as error:  # HARNESS
                entry["result"], entry["status"] = str(error), "failed"  # HARNESS
            s["delegations"] = [d for d in s.get("delegations", []) if d.get("id") != entry["id"]] + [entry]  # HARNESS
            return str(entry["result"])  # HARNESS
        return run  # HARNESS

    async for chunk in run_loop(  # HARNESS
        input_data,
        system=SUPERVISOR_SYSTEM_PROMPT,
        tools=SUPERVISOR_TOOLS,
        server_tools={t["name"]: make_tool(t["name"]) for t in SUPERVISOR_TOOLS},
        state=state,
        max_turns=8,
    ):
        yield chunk
