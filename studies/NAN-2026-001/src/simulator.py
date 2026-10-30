"""Makes ball paths: a point ball moving at constant speed inside a unit box,
bouncing perfectly off the walls. Study NAN-2026-001 (see WORKORDER.md, Part 3.1).
"""

import math

import numpy as np


# --- Constants (values and source labels come from WORKORDER.md, Part 3.1) ---

# Side length of the square box; the box is [0, 1] x [0, 1] (ASSUMED).
BOX_SIZE = 1.0
# Number of ball paths made for each seed (ASSUMED, from card).
N_PATHS = 100
# Number of positions in each path, indices 0 to 49 (ASSUMED, from card).
PATH_LENGTH = 50
# Slowest allowed speed, in box units per step (ASSUMED).
SPEED_MIN = 0.01
# Fastest allowed speed; below 1, so at most one bounce per wall per step (ASSUMED).
SPEED_MAX = 0.05
# Lowest allowed start coordinate, keeping the ball away from the walls (ASSUMED).
START_MIN = 0.05
# Highest allowed start coordinate, keeping the ball away from the walls (ASSUMED).
START_MAX = 0.95


def step(position, velocity):
    """Move the ball forward by one step, bouncing off any wall it crosses.

    In:  position (x, y) and velocity (vx, vy), each a length-2 array.
    Out: (new_position, new_velocity), each a new length-2 float64 array.
    """
    # Copy the inputs so the caller's arrays are never changed by accident.
    new_position = np.array(position, dtype=np.float64)
    new_velocity = np.array(velocity, dtype=np.float64)

    # Handle x (axis 0) and y (axis 1) separately: a bounce off a side wall
    # only flips the x-velocity, and a bounce off the floor/ceiling only flips y.
    for axis in range(2):
        # Move in a straight line for one step.
        new = new_position[axis] + new_velocity[axis]

        # Went past the left/bottom wall (0): mirror the overshoot back inside
        # and reverse direction along this axis.
        if new < 0:
            new = -new
            new_velocity[axis] = -new_velocity[axis]

        # Went past the right/top wall (BOX_SIZE): mirror the overshoot back
        # inside and reverse direction along this axis. 2 * BOX_SIZE - new is
        # the workorder's "2 - new" for a box of side 1.
        if new > BOX_SIZE:
            new = 2 * BOX_SIZE - new
            new_velocity[axis] = -new_velocity[axis]

        new_position[axis] = new

    return new_position, new_velocity


def make_paths(seed, n_paths=N_PATHS, path_length=PATH_LENGTH):
    """Make n_paths ball paths, each path_length positions long.

    In:  seed (int) for the random number generator; optional path count and length.
    Out: (positions, velocities), each a float64 array of shape
         (n_paths, path_length, 2), last axis = (x, y).
         velocities[i, k] is the velocity the ball has at position k
         (after any bounce on the way there), i.e. the velocity that will
         carry it to position k + 1.
    """
    # One random generator, created once from the seed, so the same seed
    # always gives exactly the same paths. No global random state is used.
    rng = np.random.default_rng(seed)

    # Empty arrays to fill in, one row per path.
    positions = np.zeros((n_paths, path_length, 2), dtype=np.float64)
    velocities = np.zeros((n_paths, path_length, 2), dtype=np.float64)

    for i in range(n_paths):
        # 1. Random start position, drawn in the fixed order x then y.
        start_x = rng.uniform(START_MIN, START_MAX)
        start_y = rng.uniform(START_MIN, START_MAX)

        # 2. Random speed (how far the ball moves each step).
        speed = rng.uniform(SPEED_MIN, SPEED_MAX)

        # 3. Random direction angle; turn speed + angle into a velocity (vx, vy).
        angle = rng.uniform(0.0, 2.0 * math.pi)
        velocity = np.array([speed * math.cos(angle), speed * math.sin(angle)])

        # Record the starting position and velocity.
        position = np.array([start_x, start_y])
        positions[i, 0] = position
        velocities[i, 0] = velocity

        # Step the ball forward one frame at a time, recording each new
        # position and the velocity it has after any bounce.
        for k in range(1, path_length):
            position, velocity = step(position, velocity)
            positions[i, k] = position
            velocities[i, k] = velocity

    return positions, velocities
