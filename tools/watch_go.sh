#!/bin/sh
# Runs /go in this worktree whenever .handoff/queue.md or .handoff/next.md changed and holds an open task (owner decision,
# 5 Nov 2026). Start it once per worktree in a plain terminal: sh tools/watch_go.sh. Stop it with Ctrl-C.
# Permission mode: GO_PERMISSION_MODE, else the owner's defaultMode in ~/.claude/settings.json, else acceptEdits.
cd "$(dirname "$0")/.." || exit 1
H=.handoff
LOG=$H/watch.log
mkdir -p "$H"
MODE=${GO_PERMISSION_MODE:-$(sed -n 's/.*"defaultMode"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$HOME/.claude/settings.json" 2>/dev/null | head -n 1)}
MODE=${MODE:-acceptEdits}

say() { echo "$(date '+%H:%M:%S') $(basename "$PWD"): $1" | tee -a "$LOG"; }
sum() { cat "$H/next.md" "$H/queue.md" 2>/dev/null | cksum; }

open_task() {
  # next.md with text that is not "(Empty ...", or a queue whose first block not done is todo (a blocked block stops the queue)
  if [ -f "$H/next.md" ] && grep -q '[^[:space:]]' "$H/next.md" && ! grep -m 1 '[^[:space:]]' "$H/next.md" | grep -q '^(Empty'; then
    return 0
  fi
  [ -f "$H/queue.md" ] && [ "$(awk '/^Status:/ { if ($2 != "done") { print $2; exit } }' "$H/queue.md")" = todo ]
}

say "watching, permission mode $MODE"
last=""
while :; do
  now=$(sum)
  if [ "$now" != "$last" ] && open_task; then
    say "start /go"
    out=$H/watch.last
    claude -p "/go" --permission-mode "$MODE" </dev/null >"$out" 2>&1
    code=$?
    cat "$out" >>"$LOG"
    after=$(sum)
    say "finish /go, exit $code"
    if [ "$code" -ne 0 ] && grep -qiE '/login|not logged in|log in|authenticat|invalid api key|oauth' "$out"; then
      say "LOGIN EXPIRED, run claude /login here"
      exit 1
    fi
    # A run that did its work looks again at once, so a task added meanwhile is not missed; a failed or idle run waits for a change.
    if [ "$code" -eq 0 ] && [ "$after" != "$now" ]; then last=""; else last=$after; fi
    continue
  fi
  last=$now
  sleep 30
done
