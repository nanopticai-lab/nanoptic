# NAN-2026-001 — Pico's test bench

Stay-put vs constant-velocity predictors in a bouncing-ball world. Plan: [`card.md`](card.md). Spec: [`WORKORDER.md`](WORKORDER.md). Code walkthrough: [`EXPLAIN.md`](EXPLAIN.md).

## How to re-run everything

Commands are for Windows (Git Bash or PowerShell) from the `nanoptic/` folder. On macOS/Linux/Colab use `python3` and `.venv/bin/python` instead.

1. **Make a virtual environment** (once): `python -m venv .venv`
2. **Install the exact library versions** (once): `.venv/Scripts/python -m pip install -r studies/NAN-2026-001/requirements.txt`
3. **Go to the study folder:** `cd studies/NAN-2026-001`
4. **Run the tests** (all must pass): `../../.venv/Scripts/python -m pytest -v`
5. **Run the measurement:**
   - Smoke test (pipeline check, not a result): `../../.venv/Scripts/python src/run_experiment.py --seeds 999 --tag smoke`
   - Real run (only after `card.md` is frozen): `../../.venv/Scripts/python src/run_experiment.py --seeds 0 1 2 --tag main --frozen-commit <hash>`

Outputs: `results/<tag>_results.json`, `results/<tag>_table.md`, `figures/<tag>_error_vs_horizon.png`.

Seeds 100, 101, 102 are reserved for a future Pico study; the runner always refuses them.
