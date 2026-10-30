"""Tests for simulator.py (WORKORDER.md, Part 4, tests 1-6)."""

import sys
from pathlib import Path

import numpy as np

# Let the tests import the code in ../src.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from simulator import N_PATHS, PATH_LENGTH, make_paths, step  # noqa: E402

TEST_SEED = 999


def test_1_shapes_and_dtype():
    """Test 1: outputs have shape (N_PATHS, PATH_LENGTH, 2) and dtype float64."""
    positions, velocities = make_paths(TEST_SEED)
    assert positions.shape == (N_PATHS, PATH_LENGTH, 2)
    assert velocities.shape == (N_PATHS, PATH_LENGTH, 2)
    assert positions.dtype == np.float64
    assert velocities.dtype == np.float64


def test_2_positions_stay_inside_box():
    """Test 2: every position stays inside [0, 1] (inclusive) for seed 999."""
    positions, _ = make_paths(TEST_SEED)
    assert np.all(positions >= 0.0)
    assert np.all(positions <= 1.0)


def test_3_speed_is_constant():
    """Test 3: |velocity| is the same at every step of a path (tolerance 1e-12)."""
    _, velocities = make_paths(TEST_SEED)
    speeds = np.linalg.norm(velocities, axis=2)  # shape (n_paths, path_length)
    first_speed = speeds[:, :1]                   # each path's starting speed
    assert np.all(np.abs(speeds - first_speed) <= 1e-12)


def test_4_determinism():
    """Test 4: seed 999 twice gives identical arrays; seed 998 gives different ones."""
    pos_a, vel_a = make_paths(TEST_SEED)
    pos_b, vel_b = make_paths(TEST_SEED)
    pos_c, vel_c = make_paths(998)
    assert np.array_equal(pos_a, pos_b)
    assert np.array_equal(vel_a, vel_b)
    assert not np.array_equal(pos_a, pos_c)
    assert not np.array_equal(vel_a, vel_c)


def test_5_step_bounce_right_wall():
    """Test 5: (0.98, 0.5) moving (0.04, 0.0) bounces to (0.98, 0.5), velocity (-0.04, 0.0)."""
    new_pos, new_vel = step(np.array([0.98, 0.5]), np.array([0.04, 0.0]))
    assert np.allclose(new_pos, [0.98, 0.5], rtol=0, atol=1e-12)
    assert np.allclose(new_vel, [-0.04, 0.0], rtol=0, atol=1e-12)


def test_6_step_bounce_corner():
    """Test 6: (0.99, 0.99) moving (0.03, 0.03) bounces to (0.98, 0.98), velocity (-0.03, -0.03)."""
    new_pos, new_vel = step(np.array([0.99, 0.99]), np.array([0.03, 0.03]))
    assert np.allclose(new_pos, [0.98, 0.98], rtol=0, atol=1e-12)
    assert np.allclose(new_vel, [-0.03, -0.03], rtol=0, atol=1e-12)
