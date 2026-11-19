#!/usr/bin/env bash
# HARNESS: starts every Claude Agent SDK (Python) React Native server on its harness port (never 3000/8000).
#   8170 Metro bundler            8171 Copilot Runtime (doc's server.ts, PORT=8171)
#   8172 Claude SDK quickstart agent (backend/main.py, verbatim from claude-sdk-python/quickstart)
#   8173 per-page Copilot Runtimes (harness-runtime.ts)   8174-8178 page agents (added per page)
# Emulator: AVD qa_pixel, headless. The app reaches the host at 10.0.2.2 (doc's own rule).
# Usage: bash start-all.sh            start servers + emulator + install/launch the app
#        NO_EMU=1 bash start-all.sh   servers only
cd "$(dirname "$0")"
mkdir -p logs
SDK="${ANDROID_HOME:-$LOCALAPPDATA/Android/Sdk}"
ADB="$SDK/platform-tools/adb"

if [ -z "$NO_EMU" ] && ! "$ADB" devices | grep -q "emulator-"; then
  "$SDK/emulator/emulator" -avd qa_pixel -no-window -no-audio -no-boot-anim -memory 3072 -cores 2 \
    -gpu host > logs/emulator.log 2>&1 &  # HARNESS: swiftshader froze System UI (ANR) on this laptop
fi

# backend/.env holds ANTHROPIC_API_KEY + ANTHROPIC_MODEL (doc's .env step; gitignored)
(cd backend && uv run --env-file .env uvicorn main:app --port 8172 > ../logs/backend-8172.log 2>&1) &
# HARNESS: page agents, one file per page group, one path per page (/<page-id>)
(cd backend && uv run --env-file .env uvicorn rn_chat_main:app --port 8174 > ../logs/backend-8174.log 2>&1) &
(cd backend && uv run --env-file .env uvicorn rn_genui_main:app --port 8175 > ../logs/backend-8175.log 2>&1) &
(cd backend && uv run --env-file .env uvicorn rn_state_main:app --port 8176 > ../logs/backend-8176.log 2>&1) &
[ -f backend/rn_misc_main.py ] && (cd backend && uv run --env-file .env uvicorn rn_misc_main:app --port 8178 > ../logs/backend-8178.log 2>&1) &
# Doc: `export OPENAI_API_KEY=sk-...` then `npx tsx server.ts`; the key comes from runtime.env (gitignored).
(cd MyCopilotApp && set -a && . ../runtime.env && set +a && PORT=8171 npx tsx server.ts > ../logs/runtime-8171.log 2>&1) &
# HARNESS: per-page runtimes (harness-runtime.ts) on :8173, at /api/<page-id>/copilotkit
(cd MyCopilotApp && set -a && . ../runtime.env && set +a && PORT=8173 npx tsx harness-runtime.ts > ../logs/runtimes-8173.log 2>&1) &
(cd MyCopilotApp && npx react-native start --port 8170 > ../logs/metro-8170.log 2>&1) &

if [ -z "$NO_EMU" ]; then
  "$ADB" wait-for-device
  until [ "$("$ADB" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ]; do sleep 3; done
  # HARNESS: the APK is built from a short-path copy (C:\rnc, see tools/build-apk.sh): the repo path is
  # past Windows' 260-char limit for the worklets CMake build. JS still comes from this repo via Metro.
  for s in window_animation_scale transition_animation_scale animator_duration_scale; do "$ADB" shell settings put global $s 0; done
  until "$ADB" install -r /c/rnc/android/app/build/outputs/apk/debug/app-debug.apk 2>&1 | grep -q Success; do sleep 10; done
  # HARNESS: the APK was built with the default Metro port; point its dev server at 10.0.2.2:8170
  "$ADB" shell "run-as com.claudesdkapp sh -c 'mkdir -p shared_prefs && echo \"<?xml version=\\\"1.0\\\" encoding=\\\"utf-8\\\" standalone=\\\"yes\\\" ?><map><string name=\\\"debug_http_host\\\">10.0.2.2:8170</string></map>\" > shared_prefs/com.claudesdkapp_preferences.xml'"
  echo "app installed; open a page: adb shell am start -a android.intent.action.VIEW -d copilotqacls://page/<id> com.claudesdkapp"
fi
wait
