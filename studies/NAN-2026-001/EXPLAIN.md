# EXPLAIN — NAN-2026-001: Pico's test bench

A plain-English walkthrough of the code. Line numbers refer to the files in `src/` and `tests/` at the Phase A commit.

**A few words used below**
- **Array**: a grid of numbers. `positions` is a 3-D grid: path number × time step × (x, y).
- **Seed**: a starting number for the random generator. Same seed → exactly the same "random" numbers.
- **Horizon (h)**: how many steps ahead a predictor is guessing.
- **Anchor (t)**: the moment the predictor stands at when it makes its guess.
- **Vectorised**: doing a sum for all paths at once with NumPy, instead of one path at a time in a loop.

---

## 1. The big picture

The test bench is a tiny simulated world: a point ball moving at constant speed in a 1 × 1 box, bouncing perfectly off the walls. Two very simple predictors guess where the ball will be 1, 5 and 10 steps ahead: "stay put" (SP) and "keep the same velocity" (CV). The code measures how far off each guess is, on average, using the same moments in time for every horizon. These two predictors are the baselines: the bar that Pico must clear later to show it has learned anything about space, time and speed. Building and testing the bench first means that when Pico arrives, any number it produces can be trusted to come from Pico, not from a bug in the measuring tools.

---

## 2. File by file

### `src/simulator.py` — makes ball paths

**Constants (lines 13–25).** Seven fixed settings: box size 1, 100 paths per seed, 50 positions per path, speed between 0.01 and 0.05 box widths per step, and start positions between 0.05 and 0.95. Each has a one-line comment with its source label (all ASSUMED).

**`step(position, velocity)` (lines 28–59)**
- *In:* the ball's current (x, y) and velocity (vx, vy). *Out:* the new position and new velocity one step later.
- Lines 34–36: copy the inputs so the original numbers are never changed by accident.
- Lines 40–42: for x, then for y separately, move in a straight line: `new = old + velocity`.
- Lines 44–48: if the ball went below 0 (left or bottom wall), mirror it back inside (`new = -new`) and reverse that direction.
- Lines 50–55: if the ball went above 1 (right or top wall), mirror it back inside (`new = 2 - new`) and reverse that direction.
- Line 59: hand back the new position and velocity.

**`make_paths(seed, n_paths, path_length)` (lines 62–104)**
- *In:* a seed, and optionally how many paths and how long. *Out:* `positions` and `velocities`, each shaped (100, 50, 2).
- Line 74: create one random generator from the seed. Everything random comes from this one generator, so the same seed always gives the same paths.
- Lines 76–78: make empty arrays to fill in.
- Lines 80–90: for each path, draw the random start x, start y, speed, then direction angle, in that fixed order, and turn speed + angle into a velocity using cos and sin.
- Lines 92–95: record the starting position and velocity.
- Lines 97–102: call `step` 49 times, recording each new position and the velocity the ball has after any bounce.
- Line 104: hand back both arrays.

### `src/predictors.py` — the two baselines

Both only see positions. They never see the true velocity or know where the walls are.

**`predict_stay_put(positions, t, h)` (lines 11–19)**
- *In:* all positions, the anchor time t, the horizon h. *Out:* one predicted (x, y) per path.
- Lines 17–19: the guess is simply "where the ball is at time t", for every path. h is not used: SP guesses the same place whatever the horizon.

**`predict_constant_velocity(positions, t, h)` (lines 22–46)**
- *In / out:* same as SP.
- Lines 32–36: refuse t = 0 with a clear error, because CV needs the position one step earlier and there is none.
- Lines 38–42: estimate the velocity as "position now minus position one step ago".
- Lines 44–46: guess `position now + h × estimated velocity`. No wall check: the guess can land outside the box, on purpose.

### `src/metrics.py` — the error measure

**`H_MAX` (line 20).** The largest horizon (10). It decides where the anchors stop.

**`mean_error(positions, predictor, h, h_max)` (lines 23–49)** — the fast version
- *In:* all positions, a predictor function, the horizon h, and h_max (normally 10). *Out:* one number, the mean error.
- Lines 32–36: list the anchors t = 1 … 39. They stop at 39 so that even h = 10 still has a true position to compare with (39 + 10 = 49, the last index). Every horizon uses these same anchors.
- Lines 38–45: for each anchor, get the predictor's guesses for all 100 paths at once and measure each guess's straight-line distance to the true position h steps later.
- Lines 47–49: average all 100 × 39 = 3,900 distances.

**`mean_error_loops(positions, predictor, h, h_max)` (lines 52–82)** — the independent check
- Same inputs and output. Written separately on purpose, with plain loops and `math.sqrt`, so a mistake in one version would show up as a disagreement with the other.
- Lines 58–64: read the sizes and start a running total and a counter at zero.
- Lines 66–71: work out the anchors again, independently, and ask the predictor for its guesses at each anchor.
- Lines 73–79: for each path, compute the distance by hand: `sqrt(dx² + dy²)`, and add it to the total.
- Lines 81–82: divide the total by the count.

### `src/run_experiment.py` — runs the measurement

**Settings (lines 34–53).** Reserved seeds {100, 101, 102}, locked seeds {0, 1, 2}, horizons {1, 5, 10}, the exploratory range (h = 1 … 25), the two predictors by name, the "MEASURED" label, and where to save results and figures.

**`parse_args` (lines 56–67).** Reads the command-line options: `--seeds` (required), `--tag` (default "run"), `--frozen-commit`, `--exploratory`.

**`check_seeds` (lines 70–88).** The safety guard. Runs before anything is computed.
- Lines 75–80: any reserved seed (100–102) → print why and stop with an error code.
- Lines 82–88: any locked seed (0–2) without `--frozen-commit` → print why and stop with an error code.

**`measure` (lines 91–105).** For each seed: make the paths, then for each horizon and each predictor compute `mean_error`. Stores the numbers in a nested table: seed → horizon → predictor.

**`summarise` (lines 108–124).** For a list of per-seed numbers: mean, sample standard deviation (the spread between seeds, with the usual n − 1 correction), min and max. With only one seed the spread is undefined, so it is stored as "null".

**`build_summary` (lines 127–144).** For each horizon: summarise SP, summarise CV, and summarise the gap SP − CV (worked out per seed first).

**`label_numbers` (lines 147–156).** Wraps every number as `{"value": …, "label": "MEASURED"}` so no number in the results file is unlabelled.

**`get_cpu_name` (lines 159–181).** Finds the processor's name: from the Windows registry, or from `/proc/cpuinfo` on Linux (e.g. Colab), or whatever Python reports.

**`format_cell` and `write_table` (lines 184–205).** Turn the summary into a Markdown table: one row per horizon, columns SP, CV and gap, each "mean ± std" to 5 decimals ("± n/a" with one seed).

**`write_figure` (lines 208–227).** Draws error vs horizon for SP and CV, with error bars showing the spread between seeds (no bars with one seed), labelled axes with units, and the tag and seeds in the title.

**`run_analysis` (lines 230–278).**
- Lines 232–235: do the measurement and summary, and note how long it took.
- Lines 237–266: build the results record: the numbers, the seeds, the frozen commit hash, the constants, the Python/NumPy/Matplotlib versions, OS, CPU, run time and a timestamp.
- Lines 268–278: save the JSON file, the table and the figure, and print where they went.

**`main` (lines 281–300).**
- Lines 284–285: run the safety guard first.
- Lines 287–291: the main analysis (h = 1, 5, 10; anchors 1 … 39).
- Lines 293–300: only with `--exploratory`: the extra h = 1 … 25 curve (anchors 1 … 24), saved to separate files with "exploratory" in the name and "EXPLORATORY" in the figure title.

### `tests/` — the automated checks

Each test file starts by telling Python where `src/` is (so it can import the code), then runs the checks listed in section 4 below. `test_metrics.py` also starts the runner as a separate program to check the safety guard.

---

## 3. The bounce rule, worked through

The ball is at x = 0.98, moving right at 0.04 per step. The right wall is at x = 1.

1. Straight-line move: 0.98 + 0.04 = **1.02**. That is 0.02 past the wall.
2. 1.02 > 1, so the bounce rule applies: new x = 2 − 1.02 = **0.98**. The 0.02 it "went into" the wall is mirrored back, so it ends 0.02 *inside* the wall.
3. The x-velocity flips: +0.04 → **−0.04**. Next step it moves left: 0.98 − 0.04 = 0.94.

The y-coordinate is handled on its own with the same rule, so a ball heading into a corner bounces off both walls in the same step (test 6).

---

## 4. What each test protects against

| # | Test | Protects against |
|---|---|---|
| 1 | Shapes and dtype | Arrays the wrong size or type, which would break everything downstream. |
| 2 | Inside the box | A bounce bug letting the ball escape the box. |
| 3 | Constant speed | A bounce that changes speed instead of only direction. |
| 4 | Determinism | Results that can't be repeated, or a seed that is ignored. |
| 5 | Wall bounce by hand | The mirror rule being coded wrong (e.g. stopping at the wall instead of reflecting). |
| 6 | Corner bounce by hand | x and y not being bounced independently. |
| 7 | No-bounce case | CV or SP being wrong even in the easy case, where the right answer is known exactly. |
| 8 | Bounce case by hand | CV being secretly clipped or "wall-aware", hiding the failure the study is about. |
| 9 | CV refuses t = 0 | CV silently using a nonsense "position at t = −1". |
| 10 | Fast vs loop versions agree | A bug in the error measure that a single implementation would hide. |
| 11 | Zero horizon gives zero error | The measure comparing the wrong time steps (off-by-one). |
| 12 | Runner refuses seeds 100 and 0 | Accidentally using reserved Pico seeds, or running the real seeds before the card is frozen. |

---

## 5. Five questions you should be able to answer

1. Why can CV's prediction land outside the box, and why must the code not fix that?
2. Why do all three horizons use the same anchors (t = 1 … 39), and why does the list stop at 39?
3. Why does CV need t ≥ 1, while SP works at t = 0?
4. If you run the simulator twice with seed 999, why do you get exactly the same paths, and what would break if you didn't?
5. Why is there a second, slower version of the error measure, and what would it mean if the two versions disagreed?
