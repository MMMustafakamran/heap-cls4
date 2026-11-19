# Doc: docs.copilotkit.ai/react-native/claude-sdk-python/agent-config (agent_config_agent.py, verbatim).
# The page shows read_properties(forwarded_props) and build_system_prompt, but not where the config comes
# from on React Native: the step says "reads configuration from shared state", the code reads forwarded
# props, the prose says "most agents read the config from the context ... useAgentContext" and points the
# Built-in Agent at the web <CopilotKit properties>. No imports, loop, server or RN frontend. HARNESS below.
import json  # HARNESS
from collections.abc import AsyncIterator  # HARNESS
from typing import Any, Literal  # HARNESS: used by the excerpt, never imported

from ag_ui.core import RunAgentInput  # HARNESS

from agents._messages_loop import run_loop  # HARNESS

# --- verbatim from the page ---
Tone = Literal["professional", "casual", "enthusiastic"]
Expertise = Literal["beginner", "intermediate", "expert"]
ResponseLength = Literal["concise", "detailed"]

DEFAULT_TONE: Tone = "professional"
DEFAULT_EXPERTISE: Expertise = "intermediate"
DEFAULT_RESPONSE_LENGTH: ResponseLength = "concise"

VALID_TONES: set[str] = {"professional", "casual", "enthusiastic"}
VALID_EXPERTISE: set[str] = {"beginner", "intermediate", "expert"}
VALID_RESPONSE_LENGTHS: set[str] = {"concise", "detailed"}


def read_properties(forwarded_props: Any) -> dict[str, str]:
    """Read the three config axes with defensive defaults.

    ``forwarded_props`` may arrive as either the raw top-level dict (when
    the Next.js route forwards provider ``properties`` straight through)
    or nested under ``config.configurable.properties`` (the LangGraph
    convention the shared runtime route adopts for compatibility). We
    accept both shapes — unknown values fall back to the defaults; the
    function never raises.
    """
    if not isinstance(forwarded_props, dict):
        forwarded_props = {}

    # Prefer the nested shape (mirrors the langgraph-python convention
    # the dedicated route repacks into) but fall back to top-level keys
    # so the demo still works if a caller forwards properties directly.
    nested = ((forwarded_props.get("config") or {}).get("configurable") or {}).get(
        "properties"
    ) or {}
    props = nested if isinstance(nested, dict) and nested else forwarded_props

    tone = props.get("tone", DEFAULT_TONE)
    expertise = props.get("expertise", DEFAULT_EXPERTISE)
    response_length = props.get("responseLength", DEFAULT_RESPONSE_LENGTH)

    if tone not in VALID_TONES:
        tone = DEFAULT_TONE
    if expertise not in VALID_EXPERTISE:
        expertise = DEFAULT_EXPERTISE
    if response_length not in VALID_RESPONSE_LENGTHS:
        response_length = DEFAULT_RESPONSE_LENGTH

    return {
        "tone": tone,
        "expertise": expertise,
        "response_length": response_length,
    }


def build_system_prompt(tone: str, expertise: str, response_length: str) -> str:
    """Compose the system prompt from the three axes."""
    tone_rules = {
        "professional": ("Use neutral, precise language. No emoji. Short sentences."),
        "casual": (
            "Use friendly, conversational language. Contractions OK. "
            "Light humor welcome."
        ),
        "enthusiastic": (
            "Use upbeat, energetic language. Exclamation points OK. Emoji OK."
        ),
    }
    expertise_rules = {
        "beginner": "Assume no prior knowledge. Define jargon. Use analogies.",
        "intermediate": (
            "Assume common terms are understood; explain specialized terms."
        ),
        "expert": ("Assume technical fluency. Use precise terminology. Skip basics."),
    }
    length_rules = {
        "concise": "Respond in 1-3 sentences.",
        "detailed": ("Respond in multiple paragraphs with examples where relevant."),
    }
    return (
        "You are a helpful assistant.\n\n"
        f"Tone: {tone_rules[tone]}\n"
        f"Expertise level: {expertise_rules[expertise]}\n"
        f"Response length: {length_rules[response_length]}"
    )
# --- end verbatim ---


def _latest_config(input_data: RunAgentInput) -> Any:  # HARNESS: "latestValidConfig(currentRun.context)" is pseudocode only
    for entry in reversed(input_data.context or []):  # HARNESS: the prose's useAgentContext route
        try:
            value = json.loads(entry.value)
        except (TypeError, ValueError):
            continue
        if isinstance(value, dict) and {"tone", "expertise", "responseLength"} & value.keys():
            return value
    return input_data.forwarded_props or {}  # HARNESS: what read_properties is written for


async def run_agent_config(input_data: RunAgentInput) -> AsyncIterator[str]:  # HARNESS
    cfg = read_properties(_latest_config(input_data))  # HARNESS
    system = build_system_prompt(cfg["tone"], cfg["expertise"], cfg["response_length"])  # HARNESS
    async for chunk in run_loop(input_data, system=system):  # HARNESS
        yield chunk
