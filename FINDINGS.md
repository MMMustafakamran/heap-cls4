# FINDINGS: Claude Agent SDK (Python), React Native

Open doc defects on the React Native section of the Claude Agent SDK (Python) docs (Android emulator; iOS not testable on Windows). **Draft from the doc text only (2026-11-19): no page has been probed yet (no Anthropic credit).**

Stack: @copilotkit/react-native 1.89.0 (declared ^1.89.0), @copilotkit/runtime 1.89.0 (^1.89.0), react-native 0.88.1, zod ^3.25.76, react-native-get-random-values ^2.1.0, react-native-streamdown ^0.3.0, react-native-worklets ^0.13.1, react-native-reanimated ^4.7.2, expo-file-system ~58.0.14 · backend (uv.lock): ag-ui-claude-sdk 0.2.4, claude-agent-sdk 0.2.170, anthropic 2.10.0, ag-ui-protocol 1.0.0, fastapi 0.165.0, Python >=3.12 · Node 26.7.0, npm 11 · Windows 11 Pro, Android emulator API 36 x86_64 · docs https://docs.copilotkit.ai/react-native/claude-sdk-python, snapshot 2026-11-19

### [React Native (Quickstart)](https://docs.copilotkit.ai/react-native/claude-sdk-python)

**Dev blockers**

**#1 The Claude Agent SDK quickstart never connects a Claude agent.** The page sits under Claude Agent SDK (Python), but its only runtime registers a built-in OpenAI agent; there is no `pip install` for `ag-ui-claude-sdk` / `claude-agent-sdk`, no Python server and no runtime registration.
- **Doc:** `default: new BuiltInAgent({ model: "openai:gpt-6-luna", ... })` in `server.ts`; env step names `OPENAI_API_KEY`.
- **Result (expected, not probed):** a chat on OpenAI, not on Claude. To use Claude a reader has to guess the backend (`ClaudeAgentAdapter` on FastAPI) and the runtime wiring (`HttpAgent` from `@ag-ui/client`, a package no install step names).
- **Confirmed by harness:** every other page runs on `HttpAgent({ url: "http://localhost:817x/<page>" })` in a HARNESS runtime (`MyCopilotApp/pages/<id>/runtime.ts`) plus `backend/rn_*_main.py`.

**Minor notes**
- #2 `App.tsx` has no safe area: the first chat message renders under the Android status bar (same template as the Antigravity RN page).

### [Prebuilt Components](https://docs.copilotkit.ai/react-native/claude-sdk-python/prebuilt-components)

**Minor notes**
- #3 The `/components` chat needs `@gorhom/bottom-sheet`, `react-native-gesture-handler`, `react-native-reanimated`, `react-native-streamdown` (+ its peers `react-native-worklets`, `react-native-enriched-markdown`, `remend`); the page lists them in a table but gives no install command. Same gap on Markdown, Frontend Tools, Components as Tools, Tool Call Rendering, Render agent state.
- #4 `react-native-streamdown` needs its Worklets Bundle Mode setup (`babel.config.js` + `metro.config.js`); the page only says to follow the library's guide. Without it replies crash ("[Worklets] Tried to synchronously call a Remote Function", seen on the Antigravity RN harness).

### [Multimodal Attachments](https://docs.copilotkit.ai/react-native/claude-sdk-python/multimodal-attachments)

**Dev blockers**

**#5 The quick start has no place for the answer.**
- **Doc:** `<CopilotChat agentId="default" attachments={{ enabled: true }}>` with `{/* Your message list goes here. */}`.
- **Error (CI probe 2026-11-19, 3/3):** `E/ReactNativeJS: Text strings must be rendered within a <Text> component.`; after sending, nothing shows: there is no message list, so the agent's answer never appears on screen.
- Minor: the install step is `npx expo install expo-document-picker expo-file-system`, Expo-only, while the quickstart builds a bare React Native CLI app.

### [Frontend Tools](https://docs.copilotkit.ai/react-native/claude-sdk-python/frontend-tools)

**Minor notes**
- #6 The agent step is only `_build_frontend_tools(input_data: RunAgentInput)` with no imports (`Any`, `RunAgentInput`), loop or server; the prose says the published `ClaudeAgentAdapter` needs no conversion but never shows it. Harness serves the quickstart-style adapter. Same on Components as Tools. Level to be decided on probe (level 1 if the adapter does not forward the tool).

### [Components as Tools](https://docs.copilotkit.ai/react-native/claude-sdk-python/generative-ui/tool-based)

**Minor notes**
- #7 Nothing on the page tells Claude to call `render_bar_chart` (no system prompt); the model may answer in prose. To check on probe.

### [Tool Call Rendering](https://docs.copilotkit.ai/react-native/claude-sdk-python/generative-ui/tool-rendering)

**Dev blockers**

**#8 The agent is two excerpts of an adapter whose helpers are never defined.**
- **Doc:** `run_with_claude_agent_sdk(...)` / `_make_sdk_tool(...)` excerpts of `claude_agent_sdk_adapter.py`, e.g. `"model": _normalize_claude_agent_sdk_model(model),`, plus `weather_tool.py`.
- **Error (expected):** run as published the module fails on import with `NameError`: `_normalize_claude_agent_sdk_model`, `_build_sdk_tools`, `_set_state`, `_with_initial_state`, `ExecuteTool`, `COPILOTKIT_MCP_SERVER_NAME`, `COPILOTKIT_TOOL_PREFIX` and the imports are undefined, and nothing ties `get_weather` into `execute_tool`.
- **Confirmed by harness:** `backend/agents/tool_rendering.py` fills every missing piece (HARNESS) so the weather card can be tried.
- Minor: the excerpt comments mention `:8000 /health` and `generate_a2ui` (showcase leftovers).

### [Shared State](https://docs.copilotkit.ai/react-native/claude-sdk-python/shared-state)

**Dev blockers**

**#9 The agent is three fragments of a Messages API loop the page never shows.**
- **Doc:** `async for chunk in run_shared_state_read_write_agent(input_data):` in `agent_server.py`; excerpts using `client.messages.stream(...)`, `normalize_claude_model`, `DEFAULT_ANTHROPIC_MODEL`; callout "intentionally uses its own Messages API loop. It does not use `ClaudeAgentAdapter`".
- **Error (expected):** `NameError` on `run_shared_state_read_write_agent`, `normalize_claude_model`, `DEFAULT_ANTHROPIC_MODEL`, `client`, `messages`, `system`, `tool_calls`, `msg_id`; no imports, no install step.
- **Confirmed by harness:** the whole loop is written in `backend/agents/shared_state.py` / `_messages_loop.py` (HARNESS).
- Minor: the `useCopilotKit` snippet is a bare fragment (`newLanguage` undefined, top-level await).

### [Agent Read-Only Context](https://docs.copilotkit.ai/react-native/claude-sdk-python/shared-state/agent-readonly)

**Minor notes**
- #10 The `agent.py` excerpt appends `input_data.context` to `system`, both from a function the page never shows.

### [HITL Overview](https://docs.copilotkit.ai/react-native/claude-sdk-python/human-in-the-loop)

**Minor notes**
- #11 No backend shown beyond the frontend tool (fine on the quickstart-style `ClaudeAgentAdapter`), and the first snippet is a web `page.tsx` excerpt (`agentId: "hitl-in-chat"`, `book_call`, undefined `TimePickerCard`) that doesn't match the React Native `schedule_meeting` code. Not probed yet.

### [Pausing the Agent for Input](https://docs.copilotkit.ai/react-native/claude-sdk-python/human-in-the-loop/useInterrupt)

**Minor notes**
- #12 The backend is only `SYSTEM_PROMPT = dedent(...)` with `dedent` not imported; the reader drops it into the quickstart-style `ClaudeAgentAdapter` (the picker is a frontend tool via `useHumanInTheLoop`). Not probed yet.

### [Headless Interrupts](https://docs.copilotkit.ai/react-native/claude-sdk-python/human-in-the-loop/headless)

**Minor notes**
- #13 `./src/ChatScreen` is imported but never shown.

### [Governed Action Approval UI](https://docs.copilotkit.ai/react-native/claude-sdk-python/human-in-the-loop/governed-actions)

**Minor notes**
- #14 The `useInterrupt` agent example is LangGraph only (`from langgraph.types import interrupt`, `deliver_email` undefined); the page's `useHumanInTheLoop` tool-call pattern works with the plain Claude adapter. Not probed yet.

### [WebMCP](https://docs.copilotkit.ai/react-native/claude-sdk-python/webmcp)

**Build-only**
- #15 The snippet calls `searchOrders(status)`, never defined (TS2304). The page itself says WebMCP is a no-op on React Native.

### [Sub-agents](https://docs.copilotkit.ai/react-native/claude-sdk-python/multi-agent/subagents)

**Dev blockers**

**#16 No frontend for the delegation log, and no supervisor loop.**
- **Doc:** "On the frontend, the delegation log is a reactive render of the `delegations` slot." (no snippet follows); `_delegation_tool_schema`, `SUPERVISOR_TOOLS`, `_invoke_sub_agent` excerpts.
- **Error (expected):** the loop that calls the supervisor and writes `delegations` is never shown; `normalize_claude_model`, `DEFAULT_ANTHROPIC_MODEL` and env `ANTHROPIC_SUBAGENT_MODEL` are undefined.
- **Confirmed by harness:** `run_subagents_agent` in `backend/agents/subagents.py` and the `DelegationLog` in `MyCopilotApp/pages/subagents/App.tsx` (HARNESS).
- Minor: text refers to "The LangGraph excerpt above" and the Built-in Agent's STATE_DELTA, neither on the page.

### [State Rendering](https://docs.copilotkit.ai/react-native/claude-sdk-python/generative-ui/state-rendering)

Linked from Generative UI (overview).

**Dev blockers**

**#17 The agent and the frontend use different state, and the frontend's agent is never registered.**
- **Doc:** `ResearchProgress` reads `status` / `draft` / `completed` / `total` via `useAgent({ agentId: "researcher", ... })`; the agent (`shared_state_read_write_agent.py`) writes `preferences` / `notes`, and the runner `run_shared_state_read_write_agent` is never shown.
- **Result (expected):** nothing the agent does can update the panel; it stays at its idle state. No `researcher` agent in any runtime.
- **Confirmed by harness:** `backend/agents/state_rendering.py` (loop, helpers, imports) and the runtime registering `researcher` (HARNESS).

### [State Streaming](https://docs.copilotkit.ai/react-native/claude-sdk-python/shared-state/streaming)

Linked from Shared State, Render agent state, Agent Read-Only Context, Sub-agents.

**Dev blockers**

**#18 Only a branch of a handler the page never shows.**
- **Doc:** "This branch runs inside the streamed tool-argument handler." then `if current_tool_name == "write_document":`; a separate `stream_document_state` helper; "save the final value" in prose only.
- **Result (expected):** no handler, loop, prompt or tool registration for `write_document`; two overlapping versions of the logic with no word on which to call.
- **Confirmed by harness:** `run_state_streaming` in `backend/agents/state_streaming.py` (HARNESS).

### [Programmatic Control](https://docs.copilotkit.ai/react-native/claude-sdk-python/programmatic-control)

Linked from Headless UI, Shared State.

**Minor notes**
- #19 "Wrap Claude Agent SDK once to expose that endpoint" shows no code; the subscribe excerpt uses an undefined `setStatus`, and nothing renders `request`.

### [Agent Config](https://docs.copilotkit.ai/react-native/claude-sdk-python/agent-config)

Linked from Inspector.

**Dev blockers**

**#20 No React Native frontend, and three different config channels.**
- **Doc:** "The Claude Agent SDK demo reads configuration from shared state"; the code reads `forwarded_props`; the prose names `useAgentContext` and the web `<CopilotKit properties>`; `latestValidConfig` is pseudocode.
- **Result:** a reader has to guess both ends.
- **Confirmed by harness:** `MyCopilotApp/pages/agent-config/` (config panel via `useAgentContext`) and `backend/agents/agent_config.py` (HARNESS).
