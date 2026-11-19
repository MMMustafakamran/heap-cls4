# HARNESS: React Native group C (state / HITL / multi-agent). None of these pages shows a complete server;
# one FastAPI process on :8176, one path per page. ClaudeAgentAdapter routes use the quickstart main.py
# handler; Messages-API routes stream the page's own loop. /shared-state-read-write is the page's verbatim
# agent_server.py endpoint.
# Run: uv run uvicorn rn_state_main:app --port 8176
import logging
from collections.abc import AsyncIterator

from ag_ui.core import EventType, RunAgentInput, RunErrorEvent
from ag_ui.encoder import EventEncoder
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

load_dotenv()

from agents import governed_actions, hitl_headless, shared_state_rendering  # noqa: E402
from agents.agent_config import run_agent_config  # noqa: E402
from agents.agent_readonly import run_agent_readonly  # noqa: E402
from agents.shared_state import run_shared_state_read_write_agent  # noqa: E402
from agents.state_streaming import run_state_streaming  # noqa: E402
from agents.subagents import run_subagents_agent  # noqa: E402

app = FastAPI(title="Claude Agent SDK Agent (RN group C)")
logger = logging.getLogger("claude_agent")
SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# --- verbatim from docs.copilotkit.ai/react-native/claude-sdk-python/shared-state (agent_server.py) ---
@app.post("/shared-state-read-write")
async def shared_state_read_write_endpoint(request: Request) -> StreamingResponse:
    """Bidirectional shared state demo — UI writes preferences, agent writes notes.

    Uses its own streaming loop (not the shared sales-assistant
    ``run_agent``) because the state schema, tools, and prompt-injection
    middleware are all demo-specific.
    """
    body = await request.json()
    input_data = RunAgentInput(**body)

    async def event_stream() -> AsyncIterator[str]:
        async for chunk in run_shared_state_read_write_agent(input_data):
            yield chunk

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
# --- end verbatim ---


def _adapter_route(adapter):  # HARNESS: quickstart main.py run_agent handler
    async def run_agent(input_data: RunAgentInput) -> StreamingResponse:
        encoder = EventEncoder()

        async def event_stream() -> AsyncIterator[str]:
            try:
                async for event in adapter.run(input_data):
                    yield encoder.encode(event)
            except Exception as error:
                logger.exception("Claude agent run failed")
                yield encoder.encode(RunErrorEvent(type=EventType.RUN_ERROR, message=str(error)))

        return StreamingResponse(event_stream(), media_type="text/event-stream", headers=SSE_HEADERS)

    return run_agent


def _loop_route(runner):  # HARNESS: Messages-API loops already yield encoded SSE strings
    async def run_agent(input_data: RunAgentInput) -> StreamingResponse:
        return StreamingResponse(runner(input_data), media_type="text/event-stream", headers=SSE_HEADERS)

    return run_agent


for _path, _adapter in {
    "/shared-state-rendering": shared_state_rendering.adapter,
    "/hitl-headless": hitl_headless.adapter,
    "/governed-actions": governed_actions.adapter,
}.items():
    app.post(_path)(_adapter_route(_adapter))

for _path, _runner in {
    "/agent-readonly": run_agent_readonly,
    "/state-streaming": run_state_streaming,
    "/agent-config": run_agent_config,
    "/subagents": run_subagents_agent,
}.items():
    app.post(_path)(_loop_route(_runner))
