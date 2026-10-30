# Research Card — NAN-2026-001: Pico's test bench

**Status:** OPEN, not frozen. Two fields still need Seth (marked ⚠). The plan is frozen only when those are settled and this file is committed to GitHub.

| Field | Entry |
|---|---|
| Date opened | 2026-10-30 |
| Question | A point "ball" moves at constant speed inside a square box (side = 1 unit), with perfect bounces off the walls and no gravity. How much lower is the position error of the "keep same velocity" predictor than the "stay put" predictor, at 1, 5 and 10 steps ahead? |
| Question type | Comparison |
| Why it matters (Seth) | For Pico to be a credible world model it needs to perceive the basic dimensions of the world the way humans do: space, time and speed. Starting with spatial perception, awareness and prediction is crucial for Pico as a world model. |
| Already answered? | The physics of straight-line motion and wall bounces is well established. This study builds measuring tools; it is not a new finding. Survey: light (1 session). |
| Prediction ⚠ | Seth's draft: "25 steps; the winning predictor at 10 steps." Needs restating as: which predictor wins at h = 1, 5 and 10, and roughly how big each predictor's error is (a number with a range). |
| Proves me wrong if ⚠ | Not yet written. |
| Baselines | Stay put (SP); Constant velocity (CV). Both defined exactly in WORKORDER.md. |
| Data | Simulated. Per seed: 100 paths × 50 positions. Speeds 0.01–0.05 units/step (ASSUMED: slow enough for at most one bounce per wall per step). Seeds 100–102 reserved, unused, for future Pico testing. |
| Error measure | Straight-line (Euclidean) distance between predicted and true position, in box units. |
| Method | See WORKORDER.md, Parts 2–4. |
| Runs | 3 seeds (0, 1, 2). |
| Analysis plan | For each horizon h ∈ {1, 5, 10} and each predictor: mean error per seed, then mean and sample standard deviation across the 3 seeds. Gap = SP − CV. Anything beyond this (e.g. a curve up to h = 25) is labelled exploratory. |
| Stop / kill criteria | If any sanity test fails (ball leaves the box, speed changes, results not repeatable with the same seed), stop and fix before measuring. |
| Plan frozen | Pending: GitHub commit link + date. |

## AI-use note (for the eventual write-up)
Code by Claude Code from WORKORDER.md. Reviewed by Claude (Research Partner). Checked by: automated tests, a hand-calculated case, and a second independent implementation of the error measure.
