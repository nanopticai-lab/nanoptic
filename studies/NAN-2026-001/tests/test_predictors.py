"""Tests for predictors.py (WORKORDER.md, Part 4, tests 7-9)."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

# Let the tests import the code in ../src.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from predictors import predict_constant_velocity, predict_stay_put  # noqa: E402


def test_7_no_bounce_limiting_case():
    """Test 7: on a straight path that never reaches a wall, CV is exact and
    SP is off by exactly h x speed."""
    # Build one path by hand: start (0.5, 0.5), velocity (0.01, 0.02), 15 positions.
    # The furthest point is (0.64, 0.78), so no wall is reached.
    n_positions = 15
    path = np.zeros((1, n_positions, 2))
    for k in range(n_positions):
        path[0, k] = [0.5 + k * 0.01, 0.5 + k * 0.02]

    expected_speed = 0.0223606797749979  # sqrt(0.01^2 + 0.02^2)

    # Check every anchor t >= 1 and h in {1, 5, 10} where t + h is in range.
    checked = 0
    for h in [1, 5, 10]:
        for t in range(1, n_positions - h):
            true = path[0, t + h]
            cv_error = np.linalg.norm(predict_constant_velocity(path, t, h)[0] - true)
            sp_error = np.linalg.norm(predict_stay_put(path, t, h)[0] - true)
            assert cv_error == pytest.approx(0.0, abs=1e-12)
            assert sp_error == pytest.approx(h * expected_speed, abs=1e-12)
            checked += 1
    # Guard against the loops silently checking nothing.
    assert checked > 0


def test_8_hand_calculated_bounce_case():
    """Test 8: start (0.90, 0.50), velocity (0.04, 0.0), 6 positions.
    At t = 2, h = 3: CV predicts x = 1.10 (outside the box, not clipped),
    error 0.20; SP error 0.08. CV is worse than SP here."""
    # True x-values worked out by hand (bounce between positions 2 and 3); y stays 0.5.
    true_x = [0.90, 0.94, 0.98, 0.98, 0.94, 0.90]
    path = np.zeros((1, len(true_x), 2))
    for k, x in enumerate(true_x):
        path[0, k] = [x, 0.50]

    t, h = 2, 3
    true = path[0, t + h]

    cv_prediction = predict_constant_velocity(path, t, h)[0]
    sp_prediction = predict_stay_put(path, t, h)[0]

    # CV lands outside the box and is not clipped.
    assert cv_prediction[0] == pytest.approx(1.10, abs=1e-9)
    assert cv_prediction[1] == pytest.approx(0.50, abs=1e-9)

    cv_error = math.dist(cv_prediction, true)
    sp_error = math.dist(sp_prediction, true)
    assert cv_error == pytest.approx(0.20, abs=1e-9)
    assert sp_error == pytest.approx(0.08, abs=1e-9)
    assert cv_error > sp_error


def test_9_cv_rejects_t_zero():
    """Test 9: CV raises ValueError for t = 0 (there is no position t - 1)."""
    path = np.zeros((1, 5, 2))
    with pytest.raises(ValueError):
        predict_constant_velocity(path, 0, 1)
