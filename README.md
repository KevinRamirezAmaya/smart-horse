# Smart Horses

Juego por turnos sobre tablero $8\times 8$ con dos caballos (máquina y humano) que se mueven en “L”. Diez casillas tienen valores fijos en `{-10, -5, -4, -3, -1, +1, +3, +4, +5, +10}`. Toda casilla visitada se destruye. La máquina mueve primero. Si un jugador no tiene movimientos legales mientras el otro sí, recibe una penalización automática de `-4` puntos.

## Instalación y uso

- Requisitos: Python 3.12+ y Pygame.
- Instala dependencias:

```
pip install -r requirements.txt
```

- Ejecuta el juego:

```
python main.py
```

Flujo básico de uso:
- En el menú inicial, elige la dificultad: Principiante (profundidad 2), Amateur (4) o Experto (6).
- La máquina (caballo blanco) realiza el primer movimiento.
- Haz clic en cualquier casilla resaltada para mover tu caballo (solo movimientos en L válidos).
- Si un jugador queda sin movimientos, se aplicará la penalización o se finalizará la partida si ambos están bloqueados.
- Al terminar cada turno de la máquina, se imprime en la consola el árbol minimax construido (jugador, movimiento y valor de cada nodo) para su inspección.


Ver `docs/Smart-Horse-Heuristics.pdf` para el desarrollo y la discusión de la heurística implementada.
link Repositorio: https://github.com/KevinRamirezAmaya/smart-horse.git
