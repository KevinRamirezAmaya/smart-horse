"""High-level game controller utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .constants import HUMAN_PLAYER, MACHINE_PLAYER
from .state import GameState, Position


@dataclass
class SmartHorseGame:
    state: GameState

    @classmethod
    def new(cls, seed: Optional[int] = None) -> "SmartHorseGame":
        return cls(GameState.random_start(seed=seed))

    def legal_moves(self, player: Optional[str] = None):
        return self.state.legal_moves(player)

    def move(self, destination: Position) -> None:
        self.state = self.state.apply_move(destination)

    def penalty(self) -> None:
        self.state = self.state.apply_no_move_penalty()

    def winner_text(self) -> str:
        winner = self.state.winner()
        if winner is None:
            return "Empate" if self.state.is_terminal() else "En juego"
        return "Máquina" if winner == MACHINE_PLAYER else "Humano"

    def current_scores(self) -> tuple[int, int]:
        return self.state.scores[MACHINE_PLAYER], self.state.scores[HUMAN_PLAYER]
