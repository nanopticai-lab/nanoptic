"""Runs the NAN-2026-001 measurement and writes the results and figure.
See WORKORDER.md, Part 3.4.

Example (smoke test, Phase A):
    python src/run_experiment.py --seeds 999 --tag smoke

Seeds 0, 1, 2 are LOCKED until the Research Card is frozen (needs --frozen-commit).
Seeds 100, 101, 102 are RESERVED for a future Pico study and always refused.
"""

import argparse
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

# Draw figures straight to files, without opening a window.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import simulator
from metrics import H_MAX, mean_error
from predictors import predict_constant_velocity, predict_stay_put


# --- Settings for this study ---

# Seeds kept for testing Pico in a future study: never used here.
RESERVED_SEEDS = {100, 101, 102}
# The study's real measurement seeds: locked until the card is frozen.
LOCKED_SEEDS = {0, 1, 2}
# Horizons (steps ahead) in the main analysis.
HORIZONS = [1, 5, 10]
# Exploratory extra: horizons 1 to 25, with anchors t = 1 ... 24.
EXPLORATORY_H_MAX = 25
EXPLORATORY_HORIZONS = list(range(1, EXPLORATORY_H_MAX + 1))
# The two predictors, by short name.
PREDICTORS = {
    "SP": predict_stay_put,
    "CV": predict_constant_velocity,
}
# Label attached to every measured number.
LABEL = "MEASURED"

# Output folders, found relative to this file (src/ sits inside the study folder).
STUDY_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = STUDY_DIR / "results"
FIGURES_DIR = STUDY_DIR / "figures"


def parse_args(argv):
    """Read the command-line options."""
    parser = argparse.ArgumentParser(description="NAN-2026-001: SP vs CV predictor errors.")
    parser.add_argument("--seeds", type=int, nargs="+", required=True,
                        help="One or more seeds (ints).")
    parser.add_argument("--tag", default="run",
                        help="Name used in the output file names (default: run).")
    parser.add_argument("--frozen-commit", default=None,
                        help="Commit hash of the frozen card.md; needed for seeds 0, 1, 2.")
    parser.add_argument("--exploratory", action="store_true",
                        help="Also compute the EXPLORATORY curve for h = 1 ... 25 (Phase B only).")
    return parser.parse_args(argv)


def check_seeds(seeds, frozen_commit):
    """Stop the program (non-zero exit) if any seed is not allowed.

    Runs before anything is computed, so a refused seed never produces numbers.
    """
    # Rule 1: reserved seeds are never allowed, with or without a frozen card.
    reserved_used = sorted(set(seeds) & RESERVED_SEEDS)
    if reserved_used:
        print(f"REFUSED: seed(s) {reserved_used} are reserved for testing Pico in a "
              f"future study and must never be used in NAN-2026-001.", file=sys.stderr)
        sys.exit(1)

    # Rule 2: the real measurement seeds need the frozen card's commit hash.
    locked_used = sorted(set(seeds) & LOCKED_SEEDS)
    if locked_used and frozen_commit is None:
        print(f"REFUSED: seed(s) {locked_used} are locked until the Research Card "
              f"(card.md) is frozen. Re-run with --frozen-commit <hash> once Seth "
              f"has given you the commit hash.", file=sys.stderr)
        sys.exit(1)


def measure(seeds, horizons, h_max):
    """Compute the mean error for every seed, horizon and predictor.

    Out: nested dict per_seed[seed][h][predictor_name] = mean error (float).
    """
    per_seed = {}
    for seed in seeds:
        # Make this seed's ball paths (same seed -> same paths).
        positions, _velocities = simulator.make_paths(seed)
        per_seed[seed] = {}
        for h in horizons:
            per_seed[seed][h] = {}
            for name, predictor in PREDICTORS.items():
                per_seed[seed][h][name] = mean_error(positions, predictor, h, h_max=h_max)
    return per_seed


def summarise(values):
    """Mean, sample standard deviation (ddof=1), min and max of a list of numbers.

    With only one value the standard deviation is undefined, so it is None
    (written as null in the JSON file).
    """
    array = np.array(values, dtype=np.float64)
    if len(array) > 1:
        std = float(np.std(array, ddof=1))
    else:
        std = None
    return {
        "mean": float(np.mean(array)),
        "std": std,
        "min": float(np.min(array)),
        "max": float(np.max(array)),
    }


def build_summary(per_seed, seeds, horizons):
    """Across-seed summary for each horizon: SP, CV and the gap SP - CV.

    The gap is computed per seed first (SP - CV for that seed), then
    summarised like the other numbers.
    """
    summary = {}
    for h in horizons:
        # Collect one number per seed for each predictor and for the gap.
        sp_values = [per_seed[seed][h]["SP"] for seed in seeds]
        cv_values = [per_seed[seed][h]["CV"] for seed in seeds]
        gap_values = [sp - cv for sp, cv in zip(sp_values, cv_values)]
        summary[h] = {
            "SP": summarise(sp_values),
            "CV": summarise(cv_values),
            "gap_SP_minus_CV": summarise(gap_values),
        }
    return summary


def label_numbers(obj):
    """Wrap every number in {"value": x, "label": "MEASURED"} (None stays None).

    Walks through nested dicts so the whole results block gets labelled.
    """
    if isinstance(obj, dict):
        return {str(key): label_numbers(value) for key, value in obj.items()}
    if obj is None:
        return None
    return {"value": obj, "label": LABEL}


def get_cpu_name():
    """Best-effort CPU name; None if it cannot be found."""
    # Windows keeps the CPU's marketing name in the registry.
    if platform.system() == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            return name.strip()
        except OSError:
            pass
    # Linux (e.g. Google Colab) lists it in /proc/cpuinfo.
    if platform.system() == "Linux":
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("model name"):
                        return line.split(":", 1)[1].strip()
        except OSError:
            pass
    # Fallback: whatever Python reports (may be empty).
    return platform.processor() or None


def format_cell(stats):
    """Format one table cell as 'mean ± std' (or 'mean ± n/a' with one seed)."""
    if stats["std"] is None:
        return f"{stats['mean']:.5f} ± n/a"
    return f"{stats['mean']:.5f} ± {stats['std']:.5f}"


def write_table(path, summary, horizons, title):
    """Write a Markdown table: rows = horizons, columns = SP, CV, gap."""
    lines = [
        f"# {title}",
        "",
        "Mean error across seeds ± sample standard deviation (box widths). All numbers MEASURED.",
        "",
        "| Horizon h | SP mean ± std | CV mean ± std | Gap (SP − CV) mean ± std |",
        "|---|---|---|---|",
    ]
    for h in horizons:
        row = summary[h]
        lines.append(f"| {h} | {format_cell(row['SP'])} | {format_cell(row['CV'])} | "
                     f"{format_cell(row['gap_SP_minus_CV'])} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_figure(path, summary, horizons, title):
    """Plot error (y) vs horizon (x) for both predictors, error bars = std across seeds."""
    fig, ax = plt.subplots(figsize=(6, 4))
    for name, marker in [("SP", "o"), ("CV", "s")]:
        means = [summary[h][name]["mean"] for h in horizons]
        stds = [summary[h][name]["std"] for h in horizons]
        # With one seed there is no std, so no error bars are drawn.
        if any(s is None for s in stds):
            yerr = None
        else:
            yerr = stds
        ax.errorbar(horizons, means, yerr=yerr, marker=marker, capsize=4, label=name)
    ax.set_xlabel("Horizon h (steps ahead)")
    ax.set_ylabel("Mean position error (box widths)")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def run_analysis(seeds, horizons, h_max, name, title, frozen_commit, start_time):
    """Measure, summarise and write the JSON, table and figure for one analysis."""
    # The measurement itself.
    per_seed = measure(seeds, horizons, h_max)
    summary = build_summary(per_seed, seeds, horizons)
    run_time = time.perf_counter() - start_time

    # Everything needed to understand and reproduce the numbers.
    record = {
        "study": "NAN-2026-001",
        "analysis": name,
        "seeds": seeds,
        "frozen_commit": frozen_commit,
        "horizons": horizons,
        "anchors": {"first": 1, "last": simulator.PATH_LENGTH - 1 - h_max, "h_max": h_max},
        "constants": {
            "BOX_SIZE": simulator.BOX_SIZE,
            "N_PATHS": simulator.N_PATHS,
            "PATH_LENGTH": simulator.PATH_LENGTH,
            "SPEED_MIN": simulator.SPEED_MIN,
            "SPEED_MAX": simulator.SPEED_MAX,
            "START_MIN": simulator.START_MIN,
            "START_MAX": simulator.START_MAX,
            "source_label": "ASSUMED (WORKORDER.md, Part 3.1)",
        },
        "per_seed": label_numbers(per_seed),
        "summary": label_numbers(summary),
        "environment": {
            "python": sys.version,
            "numpy": np.__version__,
            "matplotlib": matplotlib.__version__,
            "os": platform.platform(),
            "cpu": get_cpu_name(),
        },
        "wall_clock_seconds": run_time,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Write the three output files.
    RESULTS_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)
    json_path = RESULTS_DIR / f"{name}_results.json"
    table_path = RESULTS_DIR / f"{name}_table.md"
    figure_path = FIGURES_DIR / f"{name}_error_vs_horizon.png"
    json_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    write_table(table_path, summary, horizons, title)
    write_figure(figure_path, summary, horizons, title)
    for path in (json_path, table_path, figure_path):
        print(f"wrote {path}")


def main(argv=None):
    args = parse_args(argv)

    # Refuse forbidden seeds before computing anything.
    check_seeds(args.seeds, args.frozen_commit)

    # Main analysis: h = 1, 5, 10 with anchors t = 1 ... 39.
    start_time = time.perf_counter()
    run_analysis(args.seeds, HORIZONS, H_MAX, args.tag,
                 f"NAN-2026-001 [{args.tag}] seeds {args.seeds}",
                 args.frozen_commit, start_time)

    # Exploratory extra (Phase B only): h = 1 ... 25 with anchors t = 1 ... 24,
    # saved to separate files with "exploratory" in the name.
    if args.exploratory:
        start_time = time.perf_counter()
        name = f"{args.tag}_exploratory"
        run_analysis(args.seeds, EXPLORATORY_HORIZONS, EXPLORATORY_H_MAX, name,
                     f"EXPLORATORY NAN-2026-001 [{args.tag}] seeds {args.seeds}",
                     args.frozen_commit, start_time)


if __name__ == "__main__":
    main()
