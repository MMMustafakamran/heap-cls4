# Route-building brief (Claude Agent SDK Python × React Native)

Repo: `c:\Users\QS\Desktop\Copilotkit\1-frameworks\claude-sdk-python\react-native`. Docs: `https://docs.copilotkit.ai/react-native/claude-sdk-python/<page>` (read the `.md` export with `curl -m 60`, and check the rendered page when in doubt).
Rules: `c:\Users\QS\Desktop\Copilotkit\2-shared\instructions\WORKFLOW.md` and `QA-RULES.md` (§1 verbatim code, §2 HARNESS edits, §3 ambiguity = defect, §8a levels). Page list and suspected findings: `PAGES-PLAN.md`.

The repo was copied from the Antigravity React Native harness (`1-frameworks/antigravity/react-native`, read-only for you). `MyCopilotApp/pages/<id>/` already holds Antigravity's verbatim frontend code; the RN frontend snippets are mostly identical across frameworks.

## Per page
1. Diff the live claude-sdk-python page against the live google-antigravity page (`sed` the slug out of both). Write down what differs.
2. Frontend (`MyCopilotApp/pages/<id>/`): make it match **this** page's code verbatim. Remove anything Antigravity-specific. New in-content pages: create the folder, copying the closest existing page named in PAGES-PLAN.md, then make it verbatim. Register new pages in `MyCopilotApp/pages/registry.ts`, and their runtime in `pages/runtimes.ts` / `harness-runtime.ts` (`/api/<id>/copilotkit` on :8173 → `HttpAgent` to your backend port + `/<id>`).
3. Backend: the page's Python Claude Agent SDK code, verbatim, in `backend/agents/<id>.py`. Mount it in your group's `backend/rn_<group>_main.py` at `/<id>`. Base the server on the doc quickstart's `backend/main.py` pattern (`ClaudeAgentAdapter`). When the page gives no usable Claude agent (fragment, undefined helpers, other-framework code), the smallest harness agent that lets the page run, every line marked `# HARNESS: <why>`; that gap is a finding.
4. Mark each harness line `HARNESS`. Never fix or hide a doc defect.

## Limits (the PC is shared)
- **No** `npm install`, gradle, emulator, adb, Metro or long-running servers. The owner session runs those.
- You may run `cd backend && uv run python -c "import agents.<id>"` once per file as a syntax/import check (uv may be slow on its cache lock; skip it if it hangs > 3 min and say so).
- Don't touch `assignment.json`, `FINDINGS.md`, `start-all.sh`, `.github/`, or other groups' pages or backend file.

## Output
Write `notes/group-<X>.md`: per page, the diff vs antigravity, files written, HARNESS lines, the expected finding (level 1/2/3/4 + one line), and a suggested probe prompt. Reply with a 10-line summary.
