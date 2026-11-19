# HARNESS: React Native group B (genUI / tools / HITL) backend on :8175
#   cd backend && uv run uvicorn rn_genui_main:app --port 8175
# None of these pages shows a server. Built on the quickstart main.py pattern (FastAPI + ClaudeAgentAdapter,
# RunAgentInput -> EventEncoder SSE), one path per page:
#   /frontend-tools, /tool-based  agents/frontend_tools.py (same agent.py excerpt on both pages)
#   /tool-rendering               agents/tool_rendering.py (page's run_with_claude_agent_sdk + get_weather)
#   /hitl                         agents/hitl.py (page shows no agent)
#   /use-interrupt                agents/use_interrupt.py (page's SYSTEM_PROMPT)
#   /state-rendering/shared-state-read-write  agents/state_rendering.py (page's agent_server.py endpoint)
import logging
from collections.abc import AsyncIterator, Callable

from ag_ui.core import EventType, RunAgentInput, RunErrorEvent
from ag_ui.encoder import EventEncoder
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

load_dotenv()

from agents import frontend_tools, hitl, state_rendering, tool_rendering, use_interrupt  # noqa: E402

app = FastAPI(title="Claude Agent SDK RN group B")
logger = logging.getLogger("claude_agent")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def _adapter_stream(adapter) -> Callable[[RunAgentInput], AsyncIterator[str]]:
    # Same body as quickstart main.py run_agent.
    async def run(input_data: RunAgentInput) -> AsyncIterator[str]:
        encoder = EventEncoder()
        async for event in adapter.run(input_data):
            yield encoder.encode(event)

    return run


def _mount(path: str, stream: Callable[[RunAgentInput], AsyncIterator[str]]) -> None:
    @app.post(path)
    async def run_agent(input_data: RunAgentInput) -> StreamingResponse:
        encoder = EventEncoder()

        async def event_stream() -> AsyncIterator[str]:
            try:
                async for chunk in stream(input_data):
                    yield chunk
            except Exception as error:
                logger.exception("Claude agent run failed (%s)", path)
                yield encoder.encode(RunErrorEvent(type=EventType.RUN_ERROR, message=str(error)))

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )


_mount("/frontend-tools", _adapter_stream(frontend_tools.adapter))
_mount("/tool-based", _adapter_stream(frontend_tools.adapter))
_mount("/tool-rendering", tool_rendering.stream)
_mount("/hitl", _adapter_stream(hitl.adapter))
_mount("/use-interrupt", _adapter_stream(use_interrupt.adapter))
app.include_router(state_rendering.app, prefix="/state-rendering")
