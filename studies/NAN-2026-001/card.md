# Research Card — NAN-2026-001: Pico's test bench

**Status:** OPEN, ready to freeze. Seth reviews the prediction, then commits this file to GitHub; that commit is the freeze.

| Field | Entry |
|---|---|
| Date opened | 2026-10-30 |
| Question | A point "ball" moves at constant speed inside a square box (side = 1 unit), with perfect bounces off the walls and no gravity. How much lower is the position error of the "keep same velocity" predictor than the "stay put" predictor, at 1, 5 and 10 steps ahead? |
| Question type | Comparison |
| Why it matters (Seth) | For Pico to be a credible world model it needs to perceive the basic dimensions of the world the way humans do: space, time and speed. Starting with spatial perception, awareness and prediction is crucial for Pico as a world model. |
| Already answered? | The physics of straight-line motion and wall bounces is well established. This study builds measuring tools; it is not a new finding. Survey: light (1 session). |
| Prediction | Made by Claude at Seth's request (2026-10-30), from a hand derivation without running the simulator. All numbers ESTIMATED, in box units, mean across 3 seeds. **CV has lower error than SP at h = 1, 5 and 10, and its advantage shrinks as h grows** (bounces pile up). SP: h=1 0.027–0.031 · h=5 0.13–0.155 · h=10 0.24–0.30. CV: h=1 0.001–0.005 · h=5 0.015–0.05 · h=10 0.06–0.16. Ratio CV÷SP: about 0.07 → 0.2 → 0.4. |
| Proves me wrong if | (1) Main claim: SP's mean error is equal to or lower than CV's at any of h = 1, 5, 10. (2) Trend: CV÷SP does not grow from h = 1 to h = 10. (3) Size: any measured mean falls outside its range above (this only shows the estimate was off, not that the main claim is wrong). |
| Baselines | Stay put (SP); Constant velocity (CV). Both defined exactly in WORKORDER.md. |
| Data | Simulated. Per seed: 100 paths × 50 positions. Speeds 0.01–0.05 units/step (ASSUMED: slow enough for at most one bounce per wall per step). Seeds 100–102 reserved, unused, for future Pico testing. |
| Error measure | Straight-line (Euclidean) distance between predicted and true position, in box units. |
| Method | See WORKORDER.md, Parts 2–4. |
| Runs | 3 seeds (0, 1, 2). |
| Analysis plan | For each horizon h ∈ {1, 5, 10} and each predictor: mean error per seed, then mean and sample standard deviation across the 3 seeds. Gap = SP − CV. Anything beyond this (e.g. a curve up to h = 25) is labelled exploratory. |
| Stop / kill criteria | If any sanity test fails (ball leaves the box, speed changes, results not repeatable with the same seed), stop and fix before measuring. |
| Plan frozen | Pending: GitHub commit link + date. |

## Timing note (for honesty)
The prediction above was written on 2026-10-30 at about 15:46 SAST, before Phase A existed. The Phase A smoke test (seed 999, not a measurement seed) was run and seen at about 17:15 SAST, before this card was frozen. The prediction was not changed after seeing it.

## AI-use note (for the eventual write-up)
Code by Claude Code from WORKORDER.md. Reviewed by Claude (Research Partner). Checked by: automated tests, a hand-calculated case, and a second independent implementation of the error measure.
