# tools

Python helpers for the research loop described in `docs/design.md`.

Run from the repository root with the Switch's LAN IP (never commit it):

```bash
export SWITCH_HOST=<switch-ip>
PYTHONPATH=tools python3 -m switchlab status
PYTHONPATH=tools python3 -m switchlab screenshot --label "gold visible"
PYTHONPATH=tools python3 -m switchlab peek main 0x0 64
PYTHONPATH=tools python3 -m pytest tools/tests -q
```

Everything in `switchlab` today is read-only. Screenshots go to `local/screens/`,
which Git ignores; copy a chosen one into `games/<slug>/evidence/` by hand.
