# HARNESS: not from the docs. The group-C pages (shared-state, agent-readonly, shared-state/streaming,
# agent-config, multi-agent/subagents) show Python excerpts of a showcase agent that drives the
# Anthropic Messages API directly ("This Python route intentionally uses its own Messages API loop"),
# but never the loop itself: no message conversion, no AG-UI event emission, no client, and
# `normalize_claude_model` / `DEFAULT_ANTHROPIC_MODEL` are never defined. This file is the smallest
# loop that lets those excerpts run. Every line here is HARNESS.
import json
import os
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

import anthropic
from ag_ui.core import (
    EventType,
    RunAgentInput,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    StateSnapshotEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallResultEvent,
    ToolCallStartEvent,
)
from ag_ui.encoder import EventEncoder

DEFAULT_ANTHROPIC_MODEL = "claude-opus-4-8"  # HARNESS: never defined on the pages; quickstart main.py default


def normalize_claude_model(model: str) -> str:  # HARNESS: never defined on the pages; identity
    return model


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def to_anthropic_messages(input_data: RunAgentInput) -> tuple[list[dict[str, Any]], list[str]]:
    """AG-UI messages -> Anthropic messages (+ extra system text from system/developer messages)."""
    out: list[dict[str, Any]] = []
    extra_system: list[str] = []

    def push(role: str, blocks: list[dict[str, Any]]) -> None:
        if not blocks:
            return
        if out and out[-1]["role"] == role:
            out[-1]["content"].extend(blocks)
        else:
            out.append({"role": role, "content": list(blocks)})

    for m in input_data.messages or []:
        role = _get(m, "role")
        content = _get(m, "content")
        if role in ("system", "developer"):
            if content:
                extra_system.append(str(content))
        elif role == "user":
            if isinstance(content, str):
                text = content
            else:
                text = " ".join(str(_get(p, "text", "")) for p in (content or []) if _get(p, "type") == "text")
            if text:
                push("user", [{"type": "text", "text": text}])
        elif role == "assistant":
            blocks: list[dict[str, Any]] = []
            if content:
                blocks.append({"type": "text", "text": str(content)})
            for tc in _get(m, "tool_calls") or []:
                fn = _get(tc, "function")
                try:
                    args = json.loads(_get(fn, "arguments") or "{}")
                except json.JSONDecodeError:
                    args = {}
                blocks.append({"type": "tool_use", "id": _get(tc, "id"), "name": _get(fn, "name"), "input": args})
            push("assistant", blocks)
        elif role == "tool":
            push("user", [{"type": "tool_result", "tool_use_id": _get(m, "tool_call_id"), "content": str(content or "")}])
    # Anthropic rejects a tool_use without a matching tool_result: drop dangling ones.
    answered = {b["tool_use_id"] for msg in out for b in msg["content"] if b["type"] == "tool_result"}
    for msg in out:
        if msg["role"] == "assistant":
            msg["content"] = [b for b in msg["content"] if b["type"] != "tool_use" or b["id"] in answered]
    out = [msg for msg in out if msg["content"]]
    return out, extra_system


def frontend_tools(input_data: RunAgentInput) -> list[dict[str, Any]]:
    return [
        {
            "name": _get(t, "name"),
            "description": _get(t, "description") or "",
            "input_schema": _get(t, "parameters") or {"type": "object", "properties": {}},
        }
        for t in input_data.tools or []
    ]


ServerTool = Callable[[dict[str, Any], dict[str, Any]], Awaitable[str]]
ArgsHook = Callable[[str, str, dict[str, Any]], AsyncIterator[str]]


async def run_loop(
    input_data: RunAgentInput,
    *,
    system: str,
    tools: list[dict[str, Any]] | None = None,
    server_tools: dict[str, ServerTool] | None = None,
    state: dict[str, Any] | None = None,
    on_tool_args: ArgsHook | None = None,
    max_tokens: int = 2048,
    model_env: str = "ANTHROPIC_MODEL",
    max_turns: int = 8,
) -> AsyncIterator[str]:
    """Stream one AG-UI run. Server tools run here and loop; frontend tools end the run."""
    encoder = EventEncoder()
    client = anthropic.AsyncAnthropic()
    server_tools = server_tools or {}
    state = state if state is not None else dict(input_data.state or {})
    yield encoder.encode(RunStartedEvent(type=EventType.RUN_STARTED, thread_id=input_data.thread_id, run_id=input_data.run_id))
    try:
        messages, extra = to_anthropic_messages(input_data)
        if extra:
            system = system + "\n\n" + "\n".join(extra)
        all_tools = list(tools or []) + [t for t in frontend_tools(input_data) if t["name"] not in server_tools]
        for _ in range(max_turns):
            msg_id = str(uuid.uuid4())
            text_open = False
            tool_calls: list[dict[str, Any]] = []
            current: dict[str, Any] | None = None
            kwargs: dict[str, Any] = dict(
                model=normalize_claude_model(os.getenv(model_env, DEFAULT_ANTHROPIC_MODEL)),
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            )
            if all_tools:
                kwargs["tools"] = all_tools
            async with client.messages.stream(**kwargs) as stream:
                async for event in stream:
                    if event.type == "content_block_start" and event.content_block.type == "tool_use":
                        current = {"id": event.content_block.id, "name": event.content_block.name, "args": ""}
                        yield encoder.encode(ToolCallStartEvent(type=EventType.TOOL_CALL_START, tool_call_id=current["id"], tool_call_name=current["name"], parent_message_id=msg_id))
                    elif event.type == "content_block_delta" and event.delta.type == "text_delta":
                        if not text_open:
                            text_open = True
                            yield encoder.encode(TextMessageStartEvent(type=EventType.TEXT_MESSAGE_START, message_id=msg_id, role="assistant"))
                        yield encoder.encode(TextMessageContentEvent(type=EventType.TEXT_MESSAGE_CONTENT, message_id=msg_id, delta=event.delta.text))
                    elif event.type == "content_block_delta" and event.delta.type == "input_json_delta" and current:
                        current["args"] += event.delta.partial_json
                        if event.delta.partial_json:
                            yield encoder.encode(ToolCallArgsEvent(type=EventType.TOOL_CALL_ARGS, tool_call_id=current["id"], delta=event.delta.partial_json))
                        if on_tool_args:
                            async for chunk in on_tool_args(current["name"], current["args"], state):
                                yield chunk
                    elif event.type == "content_block_stop" and current:
                        yield encoder.encode(ToolCallEndEvent(type=EventType.TOOL_CALL_END, tool_call_id=current["id"]))
                        try:
                            current["input"] = json.loads(current["args"] or "{}")
                        except json.JSONDecodeError:
                            current["input"] = {}
                        tool_calls.append(current)
                        current = None
                final = await stream.get_final_message()
            if text_open:
                yield encoder.encode(TextMessageEndEvent(type=EventType.TEXT_MESSAGE_END, message_id=msg_id))
            messages.append({"role": "assistant", "content": [b.model_dump(exclude_none=True) for b in final.content]})
            if not tool_calls:
                break
            if any(tc["name"] not in server_tools for tc in tool_calls):
                break  # a frontend tool: the client runs it and starts a new run with the result
            results: list[dict[str, Any]] = []
            for tc in tool_calls:
                result_text = await server_tools[tc["name"]](tc["input"], state)
                yield encoder.encode(StateSnapshotEvent(type=EventType.STATE_SNAPSHOT, snapshot=state))
                yield encoder.encode(ToolCallResultEvent(type=EventType.TOOL_CALL_RESULT, tool_call_id=tc["id"], message_id=f"{msg_id}-tool-result-{tc['id']}", content=result_text))
                results.append({"type": "tool_result", "tool_use_id": tc["id"], "content": result_text})
            messages.append({"role": "user", "content": results})
        yield encoder.encode(RunFinishedEvent(type=EventType.RUN_FINISHED, thread_id=input_data.thread_id, run_id=input_data.run_id))
    except Exception as error:  # surface failures as RUN_ERROR, like quickstart main.py
        yield encoder.encode(RunErrorEvent(type=EventType.RUN_ERROR, message=str(error)))
