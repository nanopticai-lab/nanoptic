# Experiment Records — NAN-2026-001

## Run 1 — 2026-10-30

- **Study:** NAN-2026-001
- **Code:** commit b0c0fa4cb863219626233f61da9b76616c2f255d (frozen Research Card) | **Script/notebook:** `src/run_experiment.py --seeds 0 1 2 --tag main --frozen-commit b0c0fa4cb863219626233f61da9b76616c2f255d`
- **Seed(s):** 0, 1, 2 | **Hardware:** Intel(R) Celeron(R) N4020 CPU @ 1.10GHz, Windows-11-10.0.26200-SP0, Python 3.14.3, numpy 2.5.4, matplotlib 3.11.2 | **Run time:** 0.545 s computation (script wall clock, MEASURED); 12.0 s whole command incl. Python start-up (shell `time`, MEASURED)
- **Settings changed from plan:** none
- **Result:** from `results/main_table.md` (mean ± sample std across seeds, box widths; all MEASURED)

  | Horizon h | SP mean ± std | CV mean ± std | Gap (SP − CV) mean ± std |
  |---|---|---|---|
  | 1 | 0.03043 ± 0.00171 | 0.00217 ± 0.00020 | 0.02826 ± 0.00151 |
  | 5 | 0.14371 ± 0.00771 | 0.03280 ± 0.00321 | 0.11091 ± 0.00485 |
  | 10 | 0.26626 ± 0.01408 | 0.11886 ± 0.01067 | 0.14740 ± 0.00726 |

  Per-seed numbers: `results/main_results.json`. Figure: `figures/main_error_vs_horizon.png`.
- **Observations:** exit code 0; JSON, table and figure written.
- **Deviations:** none. Exploratory now? N

## Run 2 — 2026-10-30

- **Study:** NAN-2026-001
- **Code:** commit b0c0fa4cb863219626233f61da9b76616c2f255d (frozen Research Card) | **Script/notebook:** `src/run_experiment.py --seeds 0 1 2 --tag main --frozen-commit b0c0fa4cb863219626233f61da9b76616c2f255d --exploratory`
- **Seed(s):** 0, 1, 2 | **Hardware:** same as Run 1 | **Run time:** 0.297 s main analysis + 0.405 s exploratory analysis (script wall clock, MEASURED); 6.7 s whole command incl. Python start-up (shell `time`, MEASURED)
- **Settings changed from plan:** none
- **Result:** EXPLORATORY, h = 1 … 25, anchors t = 1 … 24, all MEASURED: see `results/main_exploratory_table.md` and `results/main_exploratory_results.json`. Figure: `figures/main_exploratory_error_vs_horizon.png`.
- **Observations:** exit code 0; exploratory JSON, table and figure written.
- **Deviations:** what changed: this command also re-runs the main analysis and overwrites `results/main_results.json`, `results/main_table.md` and `figures/main_error_vs_horizon.png` from Run 1. / why: the runner always does the main analysis first and adds the exploratory one when `--exploratory` is given (workorder 3.4 step 8). / effect: `main_table.md` is byte-identical to Run 1's; in `main_results.json` only `wall_clock_seconds` (0.5447 → 0.2974) and `timestamp` (2026-10-30T16:46:59 → 16:47:13 UTC) changed. The committed main files are therefore Run 2's copies. / exploratory now? Y (the h = 1 … 25 outputs are exploratory by design)
