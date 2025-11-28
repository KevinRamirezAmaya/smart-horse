"""Game state representation for Smart Horses."""

from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Dict, Iterable, List, Optional, Tuple

from .constants import (
    BOARD_SIZE,
    HUMAN_PLAYER,
    KNIGHT_DELTAS,
    MACHINE_PLAYER,
    POINT_VALUES,
)

Position = Tuple[int, int]
Player = str


def other_player(player: Player) -> Player:
    return MACHINE_PLAYER if player == HUMAN_PLAYER else HUMAN_PLAYER


@dataclass
class GameState:
    """Immutable-ish snapshot of the board."""

    size: int = BOARD_SIZE
    points: Dict[Position, int] = field(default_factory=dict)
    destroyed: set[Position] = field(default_factory=set)
    knight_positions: Dict[Player, Position] = field(
        default_factory=lambda: {MACHINE_PLAYER: (0, 0), HUMAN_PLAYER: (7, 7)}
    )
    scores: Dict[Player, int] = field(
        default_factory=lambda: {MACHINE_PLAYER: 0, HUMAN_PLAYER: 0}
    )
    current_player: Player = MACHINE_PLAYER
    last_move: Optional[Tuple[Player, Optional[Position]]] = None

    @classmethod
    def random_start(cls, seed: Optional[int] = None) -> "GameState":
        rng = random.Random(seed)
        all_cells = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)]
        chosen = rng.sample(all_cells, k=12)  # 2 knights + 10 point cells
        knight_cells = chosen[:2]
        point_cells = chosen[2:]

        white_pos, black_pos = knight_cells
        destroyed = {white_pos, black_pos}

        shuffled_values = POINT_VALUES.copy()
        rng.shuffle(shuffled_values)
        points = {pos: value for pos, value in zip(point_cells, shuffled_values)}

        state = cls(
            points=points,
            destroyed=destroyed,
            knight_positions={
                MACHINE_PLAYER: white_pos,
                HUMAN_PLAYER: black_pos,
            },
            scores={MACHINE_PLAYER: 0, HUMAN_PLAYER: 0},
            current_player=MACHINE_PLAYER,
            last_move=None,
        )
        return state

    def clone(
        self,
        *,
        points: Optional[Dict[Position, int]] = None,
        destroyed: Optional[Iterable[Position]] = None,
        knight_positions: Optional[Dict[Player, Position]] = None,
        scores: Optional[Dict[Player, int]] = None,
        current_player: Optional[Player] = None,
        last_move: Optional[Tuple[Player, Optional[Position]]] = None,
    ) -> "GameState":
        return GameState(
            size=self.size,
            points=points if points is not None else dict(self.points),
            destroyed=set(destroyed) if destroyed is not None else set(self.destroyed),
            knight_positions=
                knight_positions if knight_positions is not None else dict(self.knight_positions),
            scores=scores if scores is not None else dict(self.scores),
            current_player=
                current_player if current_player is not None else self.current_player,
            last_move=last_move if last_move is not None else self.last_move,
        )

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.size and 0 <= col < self.size

    def legal_moves(self, player: Optional[Player] = None) -> List[Position]:
        player = player or self.current_player
        origin = self.knight_positions[player]
        moves: List[Position] = []
        for dr, dc in KNIGHT_DELTAS:
            nr, nc = origin[0] + dr, origin[1] + dc
            if not self.in_bounds(nr, nc):
                continue
            dest = (nr, nc)
            if dest in self.destroyed:
                continue
            if dest in self.knight_positions.values():
                continue
            moves.append(dest)
        return moves

    def apply_move(self, destination: Position) -> "GameState":
        player = self.current_player
        opponent = other_player(player)
        new_points = dict(self.points)
        new_destroyed = set(self.destroyed)
        new_knights = dict(self.knight_positions)
        new_scores = dict(self.scores)

        new_knights[player] = destination
        new_destroyed.add(destination)

        gained = new_points.pop(destination, 0)
        new_scores[player] += gained

        return GameState(
            size=self.size,
            points=new_points,
            destroyed=new_destroyed,
            knight_positions=new_knights,
            scores=new_scores,
            current_player=opponent,
            last_move=(player, destination),
        )

    def apply_no_move_penalty(self) -> "GameState":
        player = self.current_player
        opponent = other_player(player)
        new_scores = dict(self.scores)
        new_scores[player] -= 4
        return GameState(
            size=self.size,
            points=dict(self.points),
            destroyed=set(self.destroyed),
            knight_positions=dict(self.knight_positions),
            scores=new_scores,
            current_player=opponent,
            last_move=(player, None),
        )

    def is_terminal(self) -> bool:
        return not self.legal_moves(MACHINE_PLAYER) and not self.legal_moves(HUMAN_PLAYER)

    def winner(self) -> Optional[Player]:
        if not self.is_terminal():
            return None
        white, black = self.scores[MACHINE_PLAYER], self.scores[HUMAN_PLAYER]
        if white == black:
            return None
        return MACHINE_PLAYER if white > black else HUMAN_PLAYER

    def matrix_view(self) -> List[List[str]]:
        """Convenience view for debugging/CLI."""
        grid: List[List[str]] = [["" for _ in range(self.size)] for _ in range(self.size)]
        for (r, c), value in self.points.items():
            grid[r][c] = str(value)
        for (r, c) in self.destroyed:
            if grid[r][c] == "":
                grid[r][c] = "X"
        for player, (r, c) in self.knight_positions.items():
            grid[r][c] = "W" if player == MACHINE_PLAYER else "B"
        return grid
