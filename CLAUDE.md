# Claude Code entry point

The operating and safety rules for this repository live in `AGENTS.md`.
Load them every session:

@AGENTS.md

Current platform facts and preferences are in `USER_PROFILE.md`. The planned
helper architecture and open decisions are in `docs/design.md`.

## Writing style

Write cleanly and directly. Use plain language. State the idea instead of
decorating it.

- No metaphors, idioms, or poetic imagery where a direct statement works.
  Write "a parameter worth varying", not "a dial worth turning". Write "this
  point still matters", not "this point earns its keep".
- Mannered phrasing displays the writer instead of conveying the idea, and
  readers notice.
- Prefer short sentences with one idea each. Say what a thing is and what it
  does.
- Explain concepts simply. Do not reach for a clever framing when a plain
  description is shorter and clearer.
- This applies to everything: chat replies, commit messages, code comments,
  research logs, and every document in this repository.

## Quick start for a research session

```bash
export SWITCH_HOST=<ip the user gives in chat>
PYTHONPATH=tools python3 -m switchlab status      # identity; exit 1 if attach looks broken
PYTHONPATH=tools python3 -m switchlab diagnose    # must say "can attach" before any scan
PYTHONPATH=tools python3 -m switchlab regions     # mapped regions and the scan set
PYTHONPATH=tools python3 -m switchlab screenshot  # read the visible value yourself
PYTHONPATH=tools python3 -m switchlab scan new --label ap --width 4 --value 84
PYTHONPATH=tools python3 -m switchlab scan next --label ap --value 80
PYTHONPATH=tools python3 -m switchlab files ls /atmosphere/contents
PYTHONPATH=tools python3 -m pytest tools/tests -q
```

The `scan` and `files` commands need the `sys-botbase-lab` build on the
Switch, which reports a version ending in `-lab`. With the upstream build,
`regions` falls back to pointer harvesting and takes about two minutes.

Key rules: everything defaults to read-only; a "Busy" diagnosis means the
user must fully close and relaunch the game without opening any overlay; the
game keeps running during reads unless `pause` is used, so the user stands
still; never write the Switch IP into a file; commit small verified steps and
push when asked.

Do not probe the Homebrew Menu netloader port with a bare TCP connect. It
accepts one connection and expects the transfer to start immediately, so a
probe kills it.

The user is a beginner who prefers short multiple-choice questions and
concrete walk-throughs. Do not ask questions the tool can answer itself.
