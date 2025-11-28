import unittest

from smart_horse.constants import HUMAN_PLAYER, MACHINE_PLAYER
from smart_horse.state import GameState


class GameStateTestCase(unittest.TestCase):
    def test_random_start_generates_unique_positions(self):
        state = GameState.random_start(seed=42)
        self.assertEqual(len(state.points), 10)
        self.assertEqual(len(state.destroyed), 2)
        occupied = set(state.knight_positions.values())
        self.assertEqual(len(occupied), 2)
        self.assertTrue(all(cell not in occupied for cell in state.points))

    def test_legal_moves_respects_bounds(self):
        state = GameState(
            knight_positions={
                MACHINE_PLAYER: (4, 4),
                HUMAN_PLAYER: (0, 0),
            },
            destroyed={(4, 4), (0, 0)},
        )
        moves = state.legal_moves(MACHINE_PLAYER)
        expected = {
            (2, 3),
            (2, 5),
            (3, 2),
            (3, 6),
            (5, 2),
            (5, 6),
            (6, 3),
            (6, 5),
        }
        self.assertEqual(set(moves), expected)

    def test_move_collects_points_and_destroys_cell(self):
        state = GameState(
            points={(2, 3): 5},
            knight_positions={MACHINE_PLAYER: (4, 4), HUMAN_PLAYER: (0, 0)},
            destroyed={(4, 4), (0, 0)},
        )
        new_state = state.apply_move((2, 3))
        self.assertEqual(new_state.scores[MACHINE_PLAYER], 5)
        self.assertNotIn((2, 3), new_state.points)
        self.assertIn((2, 3), new_state.destroyed)
        self.assertEqual(new_state.current_player, HUMAN_PLAYER)

    def test_penalty_applied_correctly(self):
        state = GameState(
            knight_positions={MACHINE_PLAYER: (0, 0), HUMAN_PLAYER: (7, 7)},
            destroyed={(0, 0), (7, 7)},
        )
        penalized = state.apply_no_move_penalty()
        self.assertEqual(penalized.scores[MACHINE_PLAYER], -4)
        self.assertEqual(penalized.current_player, HUMAN_PLAYER)

    def test_tie_game_detected(self):
        # Construct a terminal state (no legal moves for both) with equal scores
        state = GameState(
            scores={MACHINE_PLAYER: 12, HUMAN_PLAYER: 12},
            knight_positions={MACHINE_PLAYER: (0, 0), HUMAN_PLAYER: (7, 7)},
            destroyed={(r, c) for r in range(8) for c in range(8)},
        )
        self.assertTrue(state.is_terminal())
        self.assertIsNone(state.winner())


if __name__ == "__main__":
    unittest.main()
