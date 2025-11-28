"""Module holding game-wide constants."""

from __future__ import annotations

from typing import Dict

BOARD_SIZE: int = 8
POINT_VALUES: list[int] = [-10, -5, -4, -3, -1, 1, 3, 4, 5, 10]
DIFFICULTY_DEPTH: Dict[str, int] = {
    "principiante": 2,
    "amateur": 4,
    "experto": 6,
}
MACHINE_PLAYER = "white"
HUMAN_PLAYER = "black"

KNIGHT_DELTAS: tuple[tuple[int, int], ...] = (
    (-2, -1),
    (-2, 1),
    (-1, -2),
    (-1, 2),
    (1, -2),
    (1, 2),
    (2, -1),
    (2, 1),
)
