// HARNESS: the Sub-Agents page shows no runtime; quickstart runtime with the page's Claude agent
// (backend/rn_state_main.py, :8176/subagents) as "default" via HttpAgent.
import { CopilotRuntime } from "@copilotkit/runtime/v2";
import { HttpAgent } from "@ag-ui/client";

const runtime = new CopilotRuntime({
  agents: {
    default: new HttpAgent({ url: "http://localhost:8176/subagents" }),
  },
});

export default runtime;
