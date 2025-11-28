# Pruebas unitarias

Este directorio contiene pruebas unitarias para el núcleo lógico del juego (sin UI). Las pruebas usan `unittest` y validan:

- Generación del estado inicial aleatorio y posiciones únicas.
- Cálculo de movimientos legales del caballo respetando límites y reglas.
- Aplicación de movimientos: recolección de puntos, destrucción de casilla y cambio de turno.
- Penalización por no tener movimientos.
- Detección de empate cuando ambos jugadores no tienen movimientos y las puntuaciones son iguales.

## Cómo ejecutar las pruebas

Desde la raíz del proyecto:

```
python -m unittest discover -s tests
```

También puedes ejecutar el archivo de pruebas directamente:

```
python tests/test_game_state.py
```


## Justificación

Se implementaron estas pruebas principalmente para probar lo que pasaba con el empate.