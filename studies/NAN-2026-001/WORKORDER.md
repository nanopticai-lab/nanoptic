# WORKORDER — NAN-2026-001: Pico's test bench

**Issued by:** Seth (director, Nanoptic Research), drafted with Claude (Research Partner)
**Date:** 2026-10-30
**For:** Claude Code
**Read first:** `../../CLAUDE.md` (lab rules) and `card.md` (the Research Card for this study).

---

## 0. Read this before writing any code

1. **This workorder has two phases. Do Phase A only.** Phase B (the real measurement) is locked until Seth gives you the commit hash of a frozen `card.md`. The lab pre-registers its predictions: the real numbers must not exist before the prediction is written down. If you run seeds 0, 1 or 2, the study is spoiled.
2. **Seeds 100, 101 and 102 are reserved for testing Pico in a future study. Never use them in this study, not even for smoke tests.**
3. **Seth is the director, not a programmer.** Every block of code needs a short plain-English comment saying *what the block does and why*. Avoid clever one-liners where a clear loop or a named intermediate variable is easier to explain. Clarity beats speed here: the arrays are tiny.
4. **Keep scope tight.** Build only what is listed. If something seems missing or wrong, stop and ask Seth rather than adding it.
5. **Do not create a GitHub remote or push anything without Seth's explicit yes.** Local commits are fine.
6. **Report with evidence** (test output, commands run), not just "done".

---

## 1. Environment

- Detect the OS first (Seth's laptop: Intel Celeron N4020, 8 GB RAM, no GPU, limited disk space). Use commands that work on that OS.
- Python ≥ 3.10. Check with `python --version` (or `python3`/`py` on Windows). If it is missing or older, stop and tell Seth.
- Create a virtual environment at the repo root: `.venv/` (add it to `.gitignore`).
- Install only: `numpy`, `matplotlib`, `pytest`. Nothing else.
- Write `studies/NAN-2026-001/requirements.txt` with the **exact installed versions** (`pip freeze` filtered to those three plus their dependencies).
- If disk space is too low to install, stop and tell Seth (fallback: Google Colab, which he can run from the browser).

---

## 2. Files to create (Phase A)

All paths are relative to `studies/NAN-2026-001/`.

```
src/
  simulator.py      # makes ball paths
  predictors.py     # the two baselines
  metrics.py        # the error measure (vectorised) + an independent loop version
  run_experiment.py # runs the measurement; writes results + figure
tests/
  test_simulator.py
  test_predictors.py
  test_metrics.py
results/            # empty for now (.gitkeep)
figures/            # empty for now (.gitkeep)
EXPLAIN.md          # plain-English walkthrough for Seth (see Part 6)
README.md           # how to re-run everything, in 5 steps or fewer
requirements.txt
```

Use NumPy for everything numeric. Use `numpy.random.default_rng(seed)` for all randomness, created **once per call** from the seed passed in. No global random state.

---

## 3. Specification

### 3.1 The world (`simulator.py`)

The box is the square `[0, 1] × [0, 1]`. The ball is a **point** (no radius). Time moves in whole steps; one step = one frame.

**Constants (module-level, ALL_CAPS, each with a one-line comment):**

| Name | Value | Why (source label) |
|---|---|---|
| `BOX_SIZE` | `1.0` | Unit box (ASSUMED) |
| `N_PATHS` | `100` | Paths per seed (ASSUMED, from card) |
| `PATH_LENGTH` | `50` | Positions per path, indices 0–49 (ASSUMED, from card) |
| `SPEED_MIN`, `SPEED_MAX` | `0.01`, `0.05` | Units per step. Max < 1, so at most one bounce per wall per step (ASSUMED) |
| `START_MIN`, `START_MAX` | `0.05`, `0.95` | Start away from walls (ASSUMED) |

**Function `make_paths(seed, n_paths=N_PATHS, path_length=PATH_LENGTH) -> (positions, velocities)`**

- `positions`: float64 array, shape `(n_paths, path_length, 2)`; last axis is `(x, y)`.
- `velocities`: same shape; the true velocity **after** each position's update (the velocity the ball is moving with at that step).
- For each path, draw in this order from one `rng`:
  1. start position: `x, y ~ Uniform(START_MIN, START_MAX)` each;
  2. speed `s ~ Uniform(SPEED_MIN, SPEED_MAX)`;
  3. direction angle `θ ~ Uniform(0, 2π)`; velocity `v = (s·cos θ, s·sin θ)`.
- Update rule from position `p[k]` to `p[k+1]`, applied to x and y **separately**:
  ```
  new = old + v
  if new < 0:    new = -new;       v = -v      (bounce off left/bottom wall)
  if new > 1:    new = 2 - new;    v = -v      (bounce off right/top wall)
  ```
  This is an exact mirror reflection: the distance travelled "into" the wall is reflected back.
- Write the single-step update as its own small function `step(position, velocity) -> (new_position, new_velocity)` so it can be tested alone.

### 3.2 The two predictors (`predictors.py`)

Both predictors only see **observed positions** (never the true velocity, never the walls). They predict where the ball will be `h` steps after an "anchor" time `t`.

| Predictor | Function | Rule |
|---|---|---|
| Stay put (SP) | `predict_stay_put(positions, t, h)` | `p̂(t+h) = p(t)` |
| Constant velocity (CV) | `predict_constant_velocity(positions, t, h)` | `v̂ = p(t) − p(t−1)`, then `p̂(t+h) = p(t) + h·v̂` |

- CV is deliberately naive: it does **not** know about walls, so its prediction may land outside the box. **Do not clip or correct it.** That failure is the point of the study.
- CV needs `t ≥ 1`; raise a `ValueError` with a clear message if `t < 1`.
- `positions` input shape `(n_paths, path_length, 2)`; output shape `(n_paths, 2)`. Vectorise across paths.

### 3.3 The error measure (`metrics.py`)

- Error for one prediction = Euclidean distance `‖p̂ − p_true‖` (units: box widths).
- **Anchors:** `t = 1, 2, …, path_length − 1 − H_MAX`, with `H_MAX = 10`. That is `t = 1 … 39` for 50 positions. **Use the same anchors for every horizon** so all horizons are compared on the same moments.
- `mean_error(positions, predictor, h)` → one float: the mean error over all paths × all anchors.
- `mean_error_loops(...)`: an **independent second implementation** of the same quantity using plain Python `for` loops and `math.sqrt`, with no NumPy vectorisation. It exists only so the tests can check the fast version a second way. Do not share helper code between the two versions.

### 3.4 The runner (`run_experiment.py`)

Command-line script with a required `--seeds` argument (list of ints) and an optional `--tag` (default `"run"`).

1. **Refuse to run** if any seed is in `{100, 101, 102}` (print why and exit non-zero).
2. **Refuse to run** seeds `0`, `1` or `2` unless the flag `--frozen-commit <hash>` is given. Print a message explaining that these seeds are locked until the Research Card is frozen.
3. For each seed and each `h ∈ {1, 5, 10}` and each predictor: compute `mean_error`.
4. Across seeds: mean, sample standard deviation (`ddof=1`; if only one seed, report `null` for std), min and max. Also the gap `SP − CV` per horizon.
5. Write `results/<tag>_results.json` containing: all per-seed numbers, the summary, the constants used, the seeds, the frozen commit hash (or null), Python and library versions, OS, CPU name if available, wall-clock run time, and an ISO timestamp. Every number is labelled `"MEASURED"`.
6. Write `results/<tag>_table.md`: a Markdown table, rows = horizons, columns = SP mean ± std, CV mean ± std, gap.
7. Write `figures/<tag>_error_vs_horizon.png`: error (y) vs horizon (x) for both predictors, error bars = std across seeds (or none if one seed), labelled axes with units, a title that includes the tag and seeds. Generated **only** by this script.
8. **Exploratory extra (Phase B only, clearly labelled):** with flag `--exploratory`, also compute both predictors for `h = 1 … 25` using anchors `t = 1 … 24`, saved to separate files with `exploratory` in the name and the word "EXPLORATORY" in the figure title.

---

## 4. Tests (pytest) — all must pass before Phase A is done

**`test_simulator.py`**
1. Shapes and dtype of `make_paths` outputs are as specified.
2. Every position stays inside `[0, 1]` (inclusive) for seed 999.
3. Speed is constant: `‖velocity‖` is the same at every step of a path (tolerance `1e-12`).
4. Determinism: two calls with seed 999 give identical arrays; seed 998 gives different arrays.
5. `step` hand case: position `(0.98, 0.5)`, velocity `(0.04, 0.0)` → new position `(0.98, 0.5)` (tolerance `1e-12`), new velocity `(−0.04, 0.0)`.
6. Corner case: position `(0.99, 0.99)`, velocity `(0.03, 0.03)` → `(0.98, 0.98)`, velocity `(−0.03, −0.03)`.

**`test_predictors.py`**
7. **No-bounce limiting case:** build one path by hand starting at `(0.5, 0.5)` with velocity `(0.01, 0.02)` for 15 positions (no wall is reached). For every anchor `t ≥ 1` and `h ∈ {1, 5, 10}` with `t + h` in range: CV error is `0` (tolerance `1e-12`) and SP error equals `h × 0.0223606797749979` (that is `h·√(0.01² + 0.02²)`, tolerance `1e-12`).
8. **Hand-calculated bounce case:** one path, start `(0.90, 0.50)`, velocity `(0.04, 0.0)`, 6 positions. The true x-values are `0.90, 0.94, 0.98, 0.98, 0.94, 0.90`. At anchor `t = 2`, `h = 3`: CV predicts x = `1.10` (outside the box, unclipped), error `0.20`; SP error `0.08` (tolerance `1e-9`). So here CV is *worse* than SP.
9. CV raises `ValueError` for `t = 0`.

**`test_metrics.py`**
10. `mean_error` and `mean_error_loops` agree to `1e-12` on seed 999 for both predictors and all three horizons.
11. Zero-horizon limiting case: with `h = 0`, both predictors give error exactly `0`.
12. Runner guard: calling the runner with seed `100` exits non-zero; with seed `0` and no `--frozen-commit` exits non-zero.

---

## 5. Phase A — do now

1. Create the venv, install, write `requirements.txt`.
2. Write `src/` and `tests/` as specified. Run `pytest -v` until all tests pass. **Fix the code, never weaken a test.** If you believe a test itself is wrong, stop and explain why to Seth instead of changing it.
3. **Smoke run only:** `python src/run_experiment.py --seeds 999 --tag smoke`. Check the JSON, table and figure are produced and look sensible. Smoke numbers are not results; they are only a check that the pipeline works.
4. Write `README.md` and `EXPLAIN.md`.
5. `git init` at the `nanoptic/` root if not already a repo, then commit with message `NAN-2026-001: Phase A test bench (simulator, baselines, metrics, tests)`.
6. **Stop and report** (Part 7).

## Phase B — LOCKED (only when Seth sends a frozen commit hash)

1. `python src/run_experiment.py --seeds 0 1 2 --tag main --frozen-commit <hash>`
2. Then, separately: `... --seeds 0 1 2 --tag main --frozen-commit <hash> --exploratory`
3. Append one Experiment Record per command to `records.md` using the template in `../../templates/experiment_record.md`.
4. Commit. Report the numbers **with their source label (MEASURED) and without interpreting them**. Interpretation is Seth's job.

---

## 6. `EXPLAIN.md` (for Seth)

Plain English, no jargon without a one-line definition. Sections:
1. **The big picture** (5 sentences): what the test bench is and why it comes before Pico.
2. **One section per file**: for each function, what goes in, what comes out, and what each block does, in 1–3 sentences per block. Quote the line numbers the block covers.
3. **The bounce rule** explained with a tiny worked example using real numbers.
4. **What each test protects against**, one line per test.
5. **Five questions Seth should be able to answer** after reading (e.g. "Why can CV's prediction land outside the box?"). Questions only, no answers.

---

## 7. Report back to Seth (end of Phase A)

- Files created (list).
- `pytest -v` output (full).
- The smoke-run table (labelled as a smoke test, seed 999, not a result).
- Exact library versions and OS.
- Every decision you made that this workorder did not specify, and why.
- Anything in this workorder you think is wrong or unclear.
