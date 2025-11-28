"""Heuristic evaluation for the Smart Horses minimax agent."""

from __future__ import annotations

import math
from typing import Tuple

from . import state as game_state
from .constants import BOARD_SIZE, HUMAN_PLAYER, MACHINE_PLAYER

Position = game_state.Position
GameState = game_state.GameState


def _center_distance(position: Position) -> float:
    center = (BOARD_SIZE - 1) / 2
    return math.hypot(position[0] - center, position[1] - center)


def _potential(points: dict[Position, int], moves: list[Position]) -> int:
    return sum(points.get(move, 0) for move in moves)


def evaluate(state: GameState) -> float:
    """Returns a higher value when the machine (white) is favored."""

    score_diff = state.scores[MACHINE_PLAYER] - state.scores[HUMAN_PLAYER]

    machine_moves = state.legal_moves(MACHINE_PLAYER)
    human_moves = state.legal_moves(HUMAN_PLAYER)
    mobility_diff = len(machine_moves) - len(human_moves)

    potential_diff = _potential(state.points, machine_moves) - _potential(
        state.points, human_moves
    )

    center_diff = _center_distance(state.knight_positions[HUMAN_PLAYER]) - _center_distance(
        state.knight_positions[MACHINE_PLAYER]
    )

    remaining_points_bias = sum(v for v in state.points.values() if v > 0) - sum(
        -v for v in state.points.values() if v < 0
    )

    return (
        score_diff * 10.0
        + mobility_diff * 1.5
        + potential_diff * 2.0
        + center_diff
        + 0.05 * remaining_points_bias
    )
