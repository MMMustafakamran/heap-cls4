// HARNESS: the Shared State page shows no runtime / server snippet. Quickstart server.ts runtime, with
// the "default" agent pointed at the page's Claude agent (backend/rn_state_main.py, :8176/shared-state-read-write, the path agent_server.py mounts)
// instead of the quickstart's BuiltInAgent, since the page's state comes from that Python agent.
import { HttpAgent } from "@ag-ui/client";
import { CopilotRuntime } from "@copilotkit/runtime/v2";

const runtime = new CopilotRuntime({
  agents: {
    default: new HttpAgent({ url: "http://localhost:8176/shared-state-read-write" }),
  },
});

export default runtime;
