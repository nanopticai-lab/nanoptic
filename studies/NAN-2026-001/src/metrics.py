"""The error measure. Study NAN-2026-001 (see WORKORDER.md, Part 3.3).

Error for one prediction = straight-line (Euclidean) distance between the
predicted and the true position, in box widths.

There are two separate versions of the same quantity:
  - mean_error:       the fast version (NumPy, all paths at once);
  - mean_error_loops: a slow, independent version (plain Python loops and
                      math.sqrt) that exists only so the tests can check the
                      fast version a second way. The two share no helper code.
"""

import math

import numpy as np


# Largest horizon in the main analysis. Anchors stop early enough that
# t + H_MAX is still inside every path, so every horizon uses the same anchors.
H_MAX = 10


def mean_error(positions, predictor, h, h_max=H_MAX):
    """Mean prediction error over all paths and all anchors (fast NumPy version).

    In:  positions, shape (n_paths, path_length, 2);
         predictor, a function (positions, t, h) -> predictions of shape (n_paths, 2);
         h, how many steps ahead to predict;
         h_max, the largest horizon in this analysis (sets the anchors; default H_MAX).
    Out: one float, the mean distance between prediction and truth.
    """
    # Anchors t = 1, 2, ..., path_length - 1 - h_max (t = 1 ... 39 for 50
    # positions and h_max = 10). Same anchors for every h, so all horizons
    # are compared on the same moments.
    path_length = positions.shape[1]
    anchors = np.arange(1, path_length - h_max)

    # For each anchor: predict all paths at once, then measure the distance
    # from each prediction to the true position h steps later.
    errors_per_anchor = []
    for t in anchors:
        predicted = predictor(positions, t, h)
        true = positions[:, t + h, :]
        distances = np.linalg.norm(predicted - true, axis=1)
        errors_per_anchor.append(distances)

    # Average over every (path, anchor) pair.
    all_errors = np.concatenate(errors_per_anchor)
    return float(np.mean(all_errors))


def mean_error_loops(positions, predictor, h, h_max=H_MAX):
    """The same mean error, computed a second, independent way with plain loops.

    Same inputs and output as mean_error. Uses only Python for-loops,
    float arithmetic and math.sqrt (no NumPy maths), and no shared helpers.
    """
    # Sizes of the data, read as plain Python ints.
    n_paths = len(positions)
    path_length = len(positions[0])

    # Running total of all distances and how many were added.
    total = 0.0
    count = 0

    # Same anchors as the fast version, written out independently:
    # t = 1 up to and including path_length - 1 - h_max.
    last_anchor = path_length - 1 - h_max
    for t in range(1, last_anchor + 1):
        # Ask the predictor for its guesses at this anchor.
        predicted = predictor(positions, t, h)

        # For each path, measure the distance by hand: sqrt(dx^2 + dy^2).
        for i in range(n_paths):
            dx = float(predicted[i][0]) - float(positions[i][t + h][0])
            dy = float(predicted[i][1]) - float(positions[i][t + h][1])
            distance = math.sqrt(dx * dx + dy * dy)
            total = total + distance
            count = count + 1

    # Mean = total distance divided by number of predictions.
    return total / count
