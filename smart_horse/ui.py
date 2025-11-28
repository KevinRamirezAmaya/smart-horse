from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pygame

from .ai import MinimaxAgent, SearchNode
from .constants import BOARD_SIZE, DIFFICULTY_DEPTH, HUMAN_PLAYER, MACHINE_PLAYER
from .game import SmartHorseGame
from .state import Position, other_player

WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700
BOARD_MARGIN = 40
INFO_PANEL_HEIGHT = 150
CELL_SIZE = (WINDOW_HEIGHT - INFO_PANEL_HEIGHT - 2 * BOARD_MARGIN) // BOARD_SIZE
BOARD_PIXEL_SIZE = CELL_SIZE * BOARD_SIZE
BOARD_ORIGIN = ((WINDOW_WIDTH - BOARD_PIXEL_SIZE) // 2, BOARD_MARGIN)

BG_COLOR = (6, 64, 43)
INFO_PANEL_BG = (4, 50, 33)
SCORE_CARD_BG = (13, 92, 64)
LIGHT_SQUARE = (245, 245, 245)
DARK_SQUARE = (20, 20, 20)
DESTROYED_COLOR = (130, 30, 30)
POINT_COLOR = (0, 210, 140)
NEGATIVE_POINT_COLOR = (235, 80, 110)
OUTLINE_COLOR = (5, 110, 80)
TEXT_COLOR = (226, 255, 238)
BUTTON_BG = (0, 140, 96)
BUTTON_HOVER = (0, 190, 140)
HIGHLIGHT_COLOR = (0, 255, 180)
MACHINE_ACCENT = (0, 210, 150)
HUMAN_ACCENT = (0, 190, 255)


STROKE_WIDTH = 2


@dataclass
class Button:
    label: str
    rect: pygame.Rect
    difficulty_key: str


class SmartHorseApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Smart Horses")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Segoe UI", 20)
        self.bold_font = pygame.font.SysFont("Segoe UI", 20, bold=True)
        self.score_font = pygame.font.SysFont("Segoe UI", 32, bold=True)
        self.title_font = pygame.font.SysFont("Segoe UI", 38, bold=True)
        self.knight_images = self._load_knight_images()

        self.state = "menu"
        self.difficulty: Optional[str] = None
        self.game: Optional[SmartHorseGame] = None
        self.agent: Optional[MinimaxAgent] = None
        self.ai_thread: Optional[threading.Thread] = None
        self.ai_thinking = False
        self.ai_result: Optional[Tuple[Optional[Position], SearchNode]] = None
        self.thinking_since: float = 0.0
        self.status_message = "Selecciona una dificultad para comenzar"

        self.menu_buttons = self._build_menu_buttons()

    def _build_menu_buttons(self) -> List[Button]:
        labels = [
            ("Principiante", "principiante"),
            ("Amateur", "amateur"),
            ("Experto", "experto"),
        ]
        buttons: List[Button] = []
        start_y = WINDOW_HEIGHT // 2 - 80
        for index, (label, key) in enumerate(labels):
            rect = pygame.Rect(0, 0, 280, 60)
            rect.center = (WINDOW_WIDTH // 2, start_y + index * 90)
            buttons.append(Button(label, rect, key))
        return buttons

    def run(self) -> None:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_click(event.pos)
            self._update_ai()
            self._draw()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

    # Event handling -----------------------------------------------------

    def _handle_click(self, pos: Tuple[int, int]) -> None:
        if self.state == "menu":
            for button in self.menu_buttons:
                if button.rect.collidepoint(pos):
                    self.start_game(button.difficulty_key)
                    break
        elif self.state == "playing":
            self._handle_board_click(pos)
        elif self.state == "gameover":
            self.state = "menu"
            self.status_message = "Selecciona una dificultad para comenzar"

    def _handle_board_click(self, pos: Tuple[int, int]) -> None:
        if not self.game or self.ai_thinking:
            return
        if self.game.state.current_player != HUMAN_PLAYER:
            return

        cell = self._pixel_to_cell(pos)
        if cell is None:
            return
        legal = self.game.state.legal_moves(HUMAN_PLAYER)
        if not legal:
            return
        if cell not in legal:
            return
        self.game.move(cell)
        self.status_message = f"Humano mueve a {cell}"
        self._advance_flow()

    # Game management ----------------------------------------------------

    def start_game(self, difficulty: str) -> None:
        self.difficulty = difficulty
        self.agent = MinimaxAgent(DIFFICULTY_DEPTH[difficulty])
        self.game = SmartHorseGame.new()
        self.state = "playing"
        self.status_message = f"Modo {difficulty.capitalize()}"
        self.ai_thinking = False
        self.ai_result = None
        self.thinking_since = 0.0
        self._advance_flow()

    def _advance_flow(self) -> None:
        if not self.game:
            return
        if self.game.state.is_terminal():
            self.state = "gameover"
            winner = self.game.winner_text()
            if winner == "Empate":
                self.status_message = "Empate"
            else:
                self.status_message = f"Ganador: {winner}"
            return

        current = self.game.state.current_player
        moves = self.game.state.legal_moves(current)
        if moves:
            if current == MACHINE_PLAYER and not self.ai_thinking:
                self._start_ai_turn()
            return

        opponent_moves = self.game.state.legal_moves(other_player(current))
        if opponent_moves:
            self.game.penalty()
            player_label = "Máquina" if current == MACHINE_PLAYER else "Humano"
            self.status_message = f"{player_label} sin movimientos (-4 puntos)"
            self._advance_flow()
        else:
            self.state = "gameover"
            winner = self.game.winner_text()
            self.status_message = f"Ganador: {winner}"

    def _start_ai_turn(self) -> None:
        if not self.game or not self.agent:
            return
        if self.ai_thinking:
            return
        self.ai_thinking = True
        self.ai_result = None
        self.thinking_since = time.time()
        self.status_message = "Máquina pensando..."

        def worker(snapshot: SmartHorseGame) -> None:
            move, tree = self.agent.choose_move(snapshot.state)
            elapsed = time.time() - self.thinking_since
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
            self.ai_result = (move, tree)

        self.ai_thread = threading.Thread(target=worker, args=(self.game,), daemon=True)
        self.ai_thread.start()

    def _update_ai(self) -> None:
        if not self.ai_thinking:
            return
        if self.ai_result is None:
            return
        if not self.game:
            return
        move, tree = self.ai_result
        if move is None:
            self.game.penalty()
            self.status_message = "Máquina sin movimientos (-4 puntos)"
        else:
            self.game.move(move)
            self.status_message = f"Máquina mueve a {move}"
        self._log_tree_to_console(tree)
        self.ai_result = None
        self.ai_thinking = False
        self._advance_flow()

    # Rendering ----------------------------------------------------------

    def _draw(self) -> None:
        self.screen.fill(BG_COLOR)
        if self.state == "menu":
            self._draw_menu()
        else:
            self._draw_board()
            self._draw_info_panel()
            if self.state == "gameover":
                self._draw_gameover_overlay()

    def _draw_menu(self) -> None:
        title = self.title_font.render("Smart Horses", True, TEXT_COLOR)
        subtitle = self.font.render(
            "Selecciona la dificultad para empezar", True, TEXT_COLOR
        )
        rect = title.get_rect(center=(WINDOW_WIDTH // 2, 140))
        self.screen.blit(title, rect)
        sub_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, 190))
        self.screen.blit(subtitle, sub_rect)

        mouse_pos = pygame.mouse.get_pos()
        for button in self.menu_buttons:
            color = BUTTON_HOVER if button.rect.collidepoint(mouse_pos) else BUTTON_BG
            pygame.draw.rect(self.screen, color, button.rect, border_radius=8)
            text = self.font.render(button.label, True, TEXT_COLOR)
            text_rect = text.get_rect(center=button.rect.center)
            self.screen.blit(text, text_rect)

    def _draw_board(self) -> None:
        if not self.game:
            return
        board_rect = pygame.Rect(BOARD_ORIGIN, (BOARD_PIXEL_SIZE, BOARD_PIXEL_SIZE))
        pygame.draw.rect(self.screen, OUTLINE_COLOR, board_rect, width=2)

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                x = BOARD_ORIGIN[0] + col * CELL_SIZE
                y = BOARD_ORIGIN[1] + row * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                base_color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(self.screen, base_color, rect)

        destroyed = {
            cell
            for cell in self.game.state.destroyed
            if cell not in self.game.state.knight_positions.values()
        }
        for row, col in destroyed:
            x = BOARD_ORIGIN[0] + col * CELL_SIZE
            y = BOARD_ORIGIN[1] + row * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(self.screen, DESTROYED_COLOR, rect)

        # Puntos con borde
        for (row, col), value in self.game.state.points.items():
            cx = BOARD_ORIGIN[0] + col * CELL_SIZE + CELL_SIZE // 2
            cy = BOARD_ORIGIN[1] + row * CELL_SIZE + CELL_SIZE // 2
            radius = CELL_SIZE // 3
            color = POINT_COLOR if value > 0 else NEGATIVE_POINT_COLOR
            # Relleno
            pygame.draw.circle(self.screen, color, (cx, cy), radius)
            # Borde
            pygame.draw.circle(self.screen, OUTLINE_COLOR, (cx, cy), radius, width=STROKE_WIDTH)
            # Texto en negrilla
            text = self.bold_font.render(str(value), True, OUTLINE_COLOR)
            text_rect = text.get_rect(center=(cx, cy - 2))
            self.screen.blit(text, text_rect)

        # highlight human legal moves
        if self.game.state.current_player == HUMAN_PLAYER and not self.ai_thinking:
            for move in self.game.state.legal_moves(HUMAN_PLAYER):
                rect = self._cell_rect(move)
                pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, rect, width=3)

        # Caballos con borde (anillo)
        for player, (row, col) in self.game.state.knight_positions.items():
            rect = self._cell_rect((row, col))
            image = self.knight_images.get(player)
            if image is None:
                continue
            # Anillo de borde alrededor del sprite
            iw = image.get_width()
            ring_radius = iw // 2 + 2  # un poco más grande que el sprite
            pygame.draw.circle(self.screen, OUTLINE_COLOR, rect.center, ring_radius, width=STROKE_WIDTH)
            # Blit del sprite centrado
            image_rect = image.get_rect(center=rect.center)
            self.screen.blit(image, image_rect)

    def _draw_info_panel(self) -> None:
        panel_rect = pygame.Rect(
            0,
            WINDOW_HEIGHT - INFO_PANEL_HEIGHT,
            WINDOW_WIDTH,
            INFO_PANEL_HEIGHT,
        )
        pygame.draw.rect(self.screen, INFO_PANEL_BG, panel_rect)
        pygame.draw.rect(self.screen, OUTLINE_COLOR, panel_rect, width=2)

        if not self.game:
            return

        machine_score, human_score = self.game.current_scores()
        info_start_x = self._draw_score_cards(panel_rect, machine_score, human_score)

        turn_label = "Máquina" if self.game.state.current_player == MACHINE_PLAYER else "Humano"
        turn_text = self.bold_font.render(f"Turno: {turn_label}", True, TEXT_COLOR)
        self.screen.blit(turn_text, (info_start_x, panel_rect.top + 24))

        status = self.font.render(self.status_message, True, TEXT_COLOR)
        self.screen.blit(status, (info_start_x, panel_rect.top + 60))

        if self.ai_thinking:
            dots = int((pygame.time.get_ticks() / 300) % 4)
            loading_text = "Pensando" + "." * dots
            load_surface = self.bold_font.render(loading_text, True, HIGHLIGHT_COLOR)
            load_rect = load_surface.get_rect()
            load_rect.topright = (
                WINDOW_WIDTH - BOARD_MARGIN,
                panel_rect.top + 24,
            )
            self.screen.blit(load_surface, load_rect)

    def _draw_score_cards(
        self, panel_rect: pygame.Rect, machine_score: int, human_score: int
    ) -> int:
        card_width = 220
        card_height = 90
        spacing = 30
        top = panel_rect.top + 12
        left = BOARD_MARGIN
        cards = [
            ("Máquina", machine_score, MACHINE_ACCENT, MACHINE_PLAYER),
            ("Humano", human_score, HUMAN_ACCENT, HUMAN_PLAYER),
        ]
        for idx, (label, score, accent, player) in enumerate(cards):
            rect = pygame.Rect(left + idx * (card_width + spacing), top, card_width, card_height)
            pygame.draw.rect(self.screen, SCORE_CARD_BG, rect, border_radius=18)
            active = self.game and self.game.state.current_player == player
            border_color = accent if active else OUTLINE_COLOR
            pygame.draw.rect(self.screen, border_color, rect, width=2, border_radius=18)

            badge_center = (rect.left + 34, rect.top + 32)
            pygame.draw.circle(self.screen, accent, badge_center, 18)
            pygame.draw.circle(self.screen, (255, 255, 255), badge_center, 2)

            name_surface = self.bold_font.render(label, True, TEXT_COLOR)
            self.screen.blit(name_surface, (badge_center[0] + 22, rect.top + 18))

            score_surface = self.score_font.render(str(score), True, accent)
            score_rect = score_surface.get_rect()
            score_rect.left = rect.left + 30
            score_rect.top = rect.top + 48
            self.screen.blit(score_surface, score_rect)

        return left + len(cards) * (card_width + spacing)

    def _draw_gameover_overlay(self) -> None:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        title = self.title_font.render("Partida terminada", True, TEXT_COLOR)
        winner_text = self.font.render(self.status_message, True, TEXT_COLOR)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20))
        winner_rect = winner_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 30))
        self.screen.blit(title, title_rect)
        self.screen.blit(winner_text, winner_rect)
        hint = self.font.render("Haz clic para volver al menú", True, TEXT_COLOR)
        hint_rect = hint.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 80))
        self.screen.blit(hint, hint_rect)
    def _log_tree_to_console(self, root: Optional[SearchNode]) -> None:
        if not root:
            return

        def helper(node: SearchNode, depth: int, lines: List[str]) -> None:
            indent = "  " * depth
            move = "-" if node.move is None else str(node.move)
            player = "Máquina" if node.player == MACHINE_PLAYER else "Humano"
            lines.append(f"{indent}{player} -> {move} | valor={node.value:.2f}")
            for child in node.children:
                helper(child, depth + 1, lines)

        lines: List[str] = []
        helper(root, 0, lines)
        print("\n=== Árbol minimax del último turno ===")
        print("\n".join(lines))
        print("=== Fin del árbol ===\n")

    # Helpers ------------------------------------------------------------

    def _cell_rect(self, cell: Position) -> pygame.Rect:
        row, col = cell
        x = BOARD_ORIGIN[0] + col * CELL_SIZE
        y = BOARD_ORIGIN[1] + row * CELL_SIZE
        return pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

    def _pixel_to_cell(self, pos: Tuple[int, int]) -> Optional[Position]:
        x, y = pos
        board_x, board_y = BOARD_ORIGIN
        if not (board_x <= x < board_x + BOARD_PIXEL_SIZE and board_y <= y < board_y + BOARD_PIXEL_SIZE):
            return None
        col = (x - board_x) // CELL_SIZE
        row = (y - board_y) // CELL_SIZE
        return (row, col)

    def _load_knight_images(self) -> Dict[str, pygame.Surface]:
        assets_dir = Path(__file__).resolve().parent / "assets"
        target_size = CELL_SIZE - 8
        mapping = {
            MACHINE_PLAYER: "white-horse.png",
            HUMAN_PLAYER: "black-horse.png",
        }
        images: Dict[str, pygame.Surface] = {}
        for player, filename in mapping.items():
            path = assets_dir / filename
            if path.exists():
                image = pygame.image.load(str(path)).convert_alpha()
            else:
                image = pygame.Surface((target_size, target_size), pygame.SRCALPHA)
                color = (250, 250, 250, 255) if player == MACHINE_PLAYER else (30, 30, 30, 255)
                pygame.draw.circle(
                    image,
                    color,
                    (target_size // 2, target_size // 2),
                    target_size // 2,
                )
            image = pygame.transform.smoothscale(image, (target_size, target_size))
            images[player] = image
        return images


def run() -> None:
    app = SmartHorseApp()
    app.run()
