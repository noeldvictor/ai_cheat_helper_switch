# Claude Code entry point

The operating and safety rules for this repository live in `AGENTS.md`.
Load them every session:

@AGENTS.md

Current platform facts and preferences are in `USER_PROFILE.md`. The planned
helper architecture and open decisions are in `docs/design.md`. The list of
cheats the user wants, with the technique and difficulty for each, is in the
active game's card under `games/`. `AGENTS.md` section 6a explains which
technique fits which kind of effect.

Keep two files current for the active game. `cheat-notes.md` holds the state of
each cheat and is edited in place; update the section and the status table
together whenever a cheat changes stage. `research-log.md` is append-only.
Write to both while working, not at the end of a session.

Disassembly tooling on this machine: capstone 5.0.6 for targeted disassembly
inside the helper, and Ghidra 11.3.2 at `~/src/ghidra_11.3.2_PUBLIC` with a
bridge script at `~/ghidramcp` for analysis that needs cross-references. Code
to analyse is read from the running process, never from game files.

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

Use the project venv. Create it with `python3 -m venv .venv` and
`.venv/bin/pip install -r requirements.txt` if it is missing. Add any new
dependency to `requirements.txt`, never with a bare `pip install`.

```bash
export SWITCH_HOST=<ip the user gives in chat>
PYTHONPATH=tools .venv/bin/python -m switchlab status      # identity; exit 1 if attach looks broken
PYTHONPATH=tools .venv/bin/python -m switchlab diagnose    # must say "can attach" before any scan
PYTHONPATH=tools .venv/bin/python -m switchlab regions     # mapped regions and the scan set
PYTHONPATH=tools .venv/bin/python -m switchlab screenshot  # read the visible value yourself
PYTHONPATH=tools .venv/bin/python -m switchlab scan new --label hp --width 4 --value 100
PYTHONPATH=tools .venv/bin/python -m switchlab scan next --label hp --value 85
PYTHONPATH=tools .venv/bin/python -m switchlab files ls /atmosphere/contents
PYTHONPATH=tools .venv/bin/python -m pytest tools/tests -q
```

Before searching a value, check how common it is. Small numbers such as 1 or a
two-digit stat match hundreds of thousands of addresses and hit the candidate
cap, which truncates the set and can exclude the real address. Prefer a larger
or more distinctive value, or reach the field through a structure whose address
is already known.

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
