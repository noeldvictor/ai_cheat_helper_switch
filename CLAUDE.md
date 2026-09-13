# Claude Code entry point

The operating and safety rules for this repository live in `AGENTS.md`.
Load them every session:

@AGENTS.md

Current platform facts and preferences are in `USER_PROFILE.md`. The planned
helper architecture and open decisions are in `docs/design.md`.

## Quick start for a research session

```bash
export SWITCH_HOST=<ip the user gives in chat>
PYTHONPATH=tools python3 -m switchlab status      # identity; exit 1 if attach looks broken
PYTHONPATH=tools python3 -m switchlab diagnose    # must say "can attach" before any scan
PYTHONPATH=tools python3 -m switchlab regions     # data blocks to scan (about 2 minutes)
PYTHONPATH=tools python3 -m switchlab screenshot  # read the visible value yourself
PYTHONPATH=tools python3 -m pytest tools/tests -q
```

Golden rules: everything defaults to read-only; a "Busy" diagnosis means the
user must fully close and relaunch the game without opening any overlay; the
game keeps running during reads, so the user stands still; never write the
Switch IP into a file; commit small verified steps and push when asked.

The user is a beginner who prefers short multiple-choice questions and
concrete walk-throughs. Do not ask questions the tool can answer itself.
