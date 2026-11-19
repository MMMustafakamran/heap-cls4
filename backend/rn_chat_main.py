# HARNESS: group A (chat/UI) pages. None of these pages shows a backend; each route serves the
# quickstart main.py ClaudeAgentAdapter (agents/<id>.py). Run: uv run uvicorn rn_chat_main:app --port 8174
import logging
from collections.abc import AsyncIterator

from ag_ui.core import EventType, RunAgentInput, RunErrorEvent
from ag_ui.encoder import EventEncoder
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

load_dotenv()

from agents import headless_ui, markdown, multimodal_attachments, prebuilt_components, programmatic_control  # noqa: E402

app = FastAPI(title="Claude Agent SDK Agent (RN group A)")
logger = logging.getLogger("claude_agent")

ADAPTERS = {
    "prebuilt-components": prebuilt_components.adapter,
    "markdown": markdown.adapter,
    "headless-ui": headless_ui.adapter,
    "multimodal-attachments": multimodal_attachments.adapter,
    "programmatic-control": programmatic_control.adapter,
}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def _route(adapter):
    # Same handler as quickstart main.py run_agent.
    async def run_agent(input_data: RunAgentInput) -> StreamingResponse:
        encoder = EventEncoder()

        async def event_stream() -> AsyncIterator[str]:
            try:
                async for event in adapter.run(input_data):
                    yield encoder.encode(event)
            except Exception as error:
                logger.exception("Claude agent run failed")
                yield encoder.encode(RunErrorEvent(type=EventType.RUN_ERROR, message=str(error)))

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return run_agent


for _id, _adapter in ADAPTERS.items():
    app.post(f"/{_id}")(_route(_adapter))
