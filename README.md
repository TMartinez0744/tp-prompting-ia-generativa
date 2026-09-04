# TP de prompting — el prompt mínimo

Interfaz de chat multi-modelo sobre [OpenRouter](https://openrouter.ai) que registra el
consumo de tokens y el costo de cada respuesta, y su aplicación a un objetivo concreto: el
juego de la vida de Conway resuelto en la mínima cantidad de prompts posible.

## Requisitos

- Python 3.9 o superior. No hay dependencias externas: la interfaz usa solo biblioteca estándar.
- Una cuenta de OpenRouter con crédito y su API key.

## Uso

La clave se define en el archivo `.env` de la raíz, que está excluido del control de versiones:

```
OPENROUTER_API_KEY=sk-or-v1-...
```

La interfaz se inicia con:

```bash
python app.py
```

y queda disponible en `http://localhost:8000`.

## Modelos

Un slot por proveedor, cada uno destinado a ejercitar una capacidad distinta. Los precios son
por millón de tokens, verificados contra `GET https://openrouter.ai/api/v1/models`.

| Slot | Modelo | Entrada | Salida | Contexto | Capacidad |
|---|---|---|---|---|---|
| 1 | `openai/gpt-5.6-luna` | $0.20 | $1.20 | 1.050.000 | `reasoning.effort` configurable |
| 2 | `anthropic/claude-haiku-4.5` | $1.00 | $5.00 | 200.000 | caching explícito con `cache_control` |
| 3 | `google/gemini-3.7-flash` | $0.75 | $3.75 | 1.048.576 | salidas estructuradas con JSON Schema |
| 4 | `deepseek/deepseek-v4-flash-0731` | $0.065 | $0.18 | 1.310.720 | referencia de bajo costo |

## Funcionamiento

Cada respuesta se acompaña del consumo que devuelve la API: tokens de entrada, de salida, de
razonamiento y cacheados, junto con el costo en dólares y el descuento por cache. Los valores
que la API no informa se muestran en cero.

El cambio de modelo abre una conversación nueva, de modo que ninguna conversación mezcla dos
modelos. Los parámetros disponibles dependen del slot activo: el nivel de `reasoning.effort`
en los slots 1 y 4, el bloque cacheable en el 2 y el JSON Schema en el 3.

Las conversaciones se guardan en `logs/`, un archivo `.md` por conversación, con el rol, la
marca de tiempo, el mensaje completo y el consumo de cada turno. El archivo se escribe al
cierre de cada turno.

## El objetivo

`vida.py` implementa el juego de la vida de Conway según el contrato que verifican los tests:

```bash
python vida.py <archivo_estado_inicial> <generaciones>
```

El archivo de estado es una grilla rectangular, una línea por fila, `#` para célula viva y `.`
para célula muerta. El mundo es finito: fuera de los bordes todo está muerto, sin
wrap-around. La salida por stdout es la grilla resultante tras N generaciones, en el mismo
formato; con `0` generaciones se imprime el estado inicial sin cambios.

El script se obtiene del chat. Entre intentos se reescribe el prompt, no el código.

### Tests

```bash
python tests/test_vida.py vida.py
```

Nueve casos: osciladores, naturalezas muertas, el glider, nacimiento, muerte por soledad,
bordes y generación cero.

## Documentación

- [`SPEC.md`](SPEC.md) — especificación de la interfaz y del contrato de `vida.py`.
- [`CLAUDE.md`](CLAUDE.md) — instrucciones para los agentes de IA que trabajen en el repositorio.
