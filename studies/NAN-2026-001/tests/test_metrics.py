"""Tests for metrics.py and the runner's seed guard (WORKORDER.md, Part 4, tests 10-12)."""

import subprocess
import sys
from pathlib import Path

import pytest

# Let the tests import the code in ../src.
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from metrics import mean_error, mean_error_loops  # noqa: E402
from predictors import predict_constant_velocity, predict_stay_put  # noqa: E402
from simulator import make_paths  # noqa: E402

TEST_SEED = 999
PREDICTORS = [predict_stay_put, predict_constant_velocity]
RUNNER = SRC_DIR / "run_experiment.py"


@pytest.mark.parametrize("predictor", PREDICTORS)
@pytest.mark.parametrize("h", [1, 5, 10])
def test_10_fast_and_loop_versions_agree(predictor, h):
    """Test 10: mean_error and mean_error_loops agree to 1e-12 on seed 999."""
    positions, _ = make_paths(TEST_SEED)
    fast = mean_error(positions, predictor, h)
    slow = mean_error_loops(positions, predictor, h)
    assert abs(fast - slow) <= 1e-12


@pytest.mark.parametrize("predictor", PREDICTORS)
def test_11_zero_horizon_gives_zero_error(predictor):
    """Test 11: with h = 0 both predictors give error exactly 0."""
    positions, _ = make_paths(TEST_SEED)
    assert mean_error(positions, predictor, 0) == 0.0
    assert mean_error_loops(positions, predictor, 0) == 0.0


@pytest.mark.parametrize("seed", ["100", "0"])
def test_12_runner_refuses_forbidden_seeds(seed):
    """Test 12: the runner exits non-zero for reserved seed 100, and for
    locked seed 0 without --frozen-commit."""
    result = subprocess.run(
        [sys.executable, str(RUNNER), "--seeds", seed, "--tag", "guardtest"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "REFUSED" in result.stderr
