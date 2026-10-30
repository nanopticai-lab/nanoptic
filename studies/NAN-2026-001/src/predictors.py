"""The two baseline predictors. Study NAN-2026-001 (see WORKORDER.md, Part 3.2).

Both only look at observed positions: never the true velocity, never the walls.
Each predicts where the ball will be h steps after an "anchor" time t,
for every path at once.
"""

import numpy as np


def predict_stay_put(positions, t, h):
    """Stay put (SP): guess that the ball will still be where it is now.

    In:  positions, shape (n_paths, path_length, 2); anchor time t; horizon h.
    Out: predicted positions at time t + h, shape (n_paths, 2).
    """
    # The prediction is simply the position at time t, for every path.
    # A copy is returned so changing the prediction cannot change the data.
    return positions[:, t, :].copy()


def predict_constant_velocity(positions, t, h):
    """Constant velocity (CV): guess that the ball keeps its last step's motion.

    In:  positions, shape (n_paths, path_length, 2); anchor time t (must be >= 1); horizon h.
    Out: predicted positions at time t + h, shape (n_paths, 2).

    Deliberately naive: it knows nothing about walls, so the prediction may
    land outside the box. It is NOT clipped or corrected; that failure is
    what the study measures.
    """
    # CV needs the position one step earlier (t - 1), which does not exist at t = 0.
    if t < 1:
        raise ValueError(
            f"Constant-velocity predictor needs t >= 1 (it uses position t-1); got t = {t}."
        )

    # Estimate the velocity from the last observed step: where it is now
    # minus where it was one step ago.
    current = positions[:, t, :]
    previous = positions[:, t - 1, :]
    estimated_velocity = current - previous

    # Assume the ball keeps that velocity for h more steps, in a straight line.
    prediction = current + h * estimated_velocity
    return prediction
