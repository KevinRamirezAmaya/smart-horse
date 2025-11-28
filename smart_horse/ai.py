"""Minimax agent implementation."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from . import heuristics
from .constants import HUMAN_PLAYER, MACHINE_PLAYER
from .state import GameState, Position, other_player


@dataclass(eq=False)
class SearchNode:
    player: str
    move: Optional[Position]
    value: float
    children: List["SearchNode"] = field(default_factory=list)


class MinimaxAgent:
    def __init__(self, depth: int, *, noise: float = 0.3) -> None:
        self.depth = depth
        self.noise = noise
        self.last_tree: Optional[SearchNode] = None

    def choose_move(self, state: GameState) -> Tuple[Optional[Position], SearchNode]:
        value, move, tree = self._search(state, self.depth, -math.inf, math.inf, None)
        tree.value = value
        self.last_tree = tree
        return move, tree

    def _terminal_or_depth(self, state: GameState, depth: int) -> bool:
        return depth == 0 or state.is_terminal()

    def _search(
        self,
        state: GameState,
        depth: int,
        alpha: float,
        beta: float,
        applied_move: Optional[Position],
    ) -> Tuple[float, Optional[Position], SearchNode]:
        if self._terminal_or_depth(state, depth):
            value = heuristics.evaluate(state)
            if self.noise:
                value += random.uniform(-self.noise, self.noise)
            node = SearchNode(state.current_player, applied_move, value)
            return value, None, node

        current_player = state.current_player
        moves = state.legal_moves(current_player)

        if not moves:
            # penalty turn: no move possible
            penalty_state = state.apply_no_move_penalty()
            value, _, child_node = self._search(
                penalty_state, depth - 1, alpha, beta, None
            )
            node = SearchNode(current_player, applied_move, value, [child_node])
            return value, None, node

        best_value = -math.inf if current_player == MACHINE_PLAYER else math.inf
        best_move: Optional[Position] = None
        child_nodes: List[SearchNode] = []

        ordered_moves = list(moves)
        random.shuffle(ordered_moves)

        for move in ordered_moves:
            next_state = state.apply_move(move)
            value, _, child_node = self._search(
                next_state, depth - 1, alpha, beta, move
            )
            child_nodes.append(child_node)
            if current_player == MACHINE_PLAYER:
                if value > best_value:
                    best_value, best_move = value, move
                alpha = max(alpha, best_value)
                if beta <= alpha:
                    break
            else:
                if value < best_value:
                    best_value, best_move = value, move
                beta = min(beta, best_value)
                if beta <= alpha:
                    break

        node = SearchNode(current_player, applied_move, best_value, child_nodes)
        return best_value, best_move, node
