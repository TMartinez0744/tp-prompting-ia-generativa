# SPEC

Especificación de lo que se construye. Se escribe antes que el código y se actualiza cuando el
entendimiento cambia.

## 1. Interfaz de chat

Interfaz web sobre la API de OpenRouter. Sin dependencias externas: `app.py` levanta el
servidor HTTP de la biblioteca estándar en `localhost:8000` y sirve el frontend de `web/`.

- `app.py`: proxy a OpenRouter, estado de la conversación, lectura del consumo y escritura del log.
- `web/index.html`, `web/estilos.css`, `web/app.js`: el frontend.

Se inicia con `python app.py`, que abre el navegador automáticamente.

### Modelos

Cuatro slots, un proveedor cada uno. Los precios son por millón de tokens, verificados contra
`GET https://openrouter.ai/api/v1/models`.

| Slot | Modelo | Entrada | Salida | Contexto | Capacidad que ejercita |
|---|---|---|---|---|---|
| 1 | `openai/gpt-5.6-luna` | $0.20 | $1.20 | 1.050.000 | `reasoning.effort` configurable |
| 2 | `anthropic/claude-haiku-4.5` | $1.00 | $5.00 | 200.000 | caching explícito con `cache_control` |
| 3 | `google/gemini-3.7-flash` | $0.75 | $3.75 | 1.048.576 | salidas estructuradas por JSON Schema |
| 4 | `deepseek/deepseek-v4-flash-0731` | $0.065 | $0.18 | 1.310.720 | referencia de bajo costo: 15x menos que el slot 2 |

### Comportamiento

- Cada respuesta muestra el consumo que devuelve la API: tokens de entrada, de salida, de
  razonamiento, cacheados y costo en USD. Los cinco siempre; los que la API no devuelve se
  muestran en `0` en lugar de ocultarse.
- Cambiar de modelo **inicia una conversación nueva**: se descarta el historial y se abre un
  log nuevo. Ninguna conversación mezcla dos modelos.
- Cada conversación se guarda en `logs/<timestamp>-<slot>-<modelo>.md` con, por turno: rol,
  marca de tiempo, mensaje completo y consumo de la respuesta. El log se escribe al cierre de
  cada turno, no al cerrar la aplicación, para que una caída no elimine el registro.
- El costo se acumula por conversación y se muestra junto a cada respuesta.

### Controles de la interfaz

| Control | Ubicación | Efecto |
|---|---|---|
| Tarjetas de modelo | Panel izquierdo | Selección de slot. Cada selección abre conversación y log nuevos |
| `reasoning.effort` | Panel, slots 1 y 4 | `low`, `medium` o `high` |
| `cache_control ephemeral` | Panel, slot 2 | Antepone el bloque estático marcado para cachear |
| `response_format JSON Schema` | Panel, slot 3 | Valida la respuesta contra `ESQUEMA_JSON` de `app.py` |
| Cargar archivo | Compositor | Carga el contenido de un archivo en el cuadro de texto |
| Copiar | Bloques de código | Copia el bloque al portapapeles |

"Cargar archivo" existe porque el prompt del ejercicio 2 es una especificación extensa que
vive en un archivo versionado: retipearla altera el texto y rompe el prefijo cacheado.

### API interna

| Ruta | Método | Efecto |
|---|---|---|
| `/api/modelos` | GET | Devuelve los cuatro slots con precio, contexto y capacidad |
| `/api/conversacion` | POST | Abre una conversación nueva para un slot y crea su log |
| `/api/mensaje` | POST | Envía un turno, devuelve respuesta y consumo, y escribe el log |

### Caching

- Slot 2 (Anthropic): explícito. El bloque de `contexto/contexto_estatico.md` encabeza el
  primer mensaje de usuario, marcado con `"cache_control": {"type": "ephemeral"}`, de modo que
  queda como prefijo idéntico en todos los turnos. La escritura se observa en
  `cache_write_tokens` y el acierto en `cached_tokens`.

  Dos condiciones son necesarias y se determinaron por medición:

  1. **El proveedor tiene que ser Anthropic.** Sin fijarlo, OpenRouter puede enrutar el pedido
     a Amazon Bedrock, que descarta `cache_control` en silencio y devuelve
     `cache_write_tokens` en cero. Se fija con
     `"provider": {"order": ["Anthropic"], "allow_fallbacks": false}`.
  2. **El bloque tiene que superar el mínimo cacheable del modelo.** Con 3.444 tokens no se
     escribió cache; con 6.874 sí. El umbral de `claude-haiku-4.5` está entre ambos valores,
     consistente con 4.096. El documento actual mide unos 6.000 tokens.

  Por debajo del mínimo no hay error ni advertencia: la respuesta llega normal y el cache
  simplemente no ocurre. La única señal es `cache_write_tokens` en cero y el costo a tarifa
  plena.
- Slot 4 (DeepSeek): automático por prefijo repetido. No hay parámetro que lo active: depende
  del diseño del prompt, con la parte invariante al principio y la parte variable al final.

### Credenciales

`OPENROUTER_API_KEY` se lee de `.env` en la raíz. `.env` está en `.gitignore` y no se versiona;
`.env.example` documenta el formato.

## 2. El objetivo: `vida.py`

Contrato que verifica `tests/test_vida.py`. Es la interfaz que los tests invocan y no admite
variantes.

- Uso: `python3 vida.py <archivo_estado_inicial> <generaciones>`.
- El archivo de estado es una grilla rectangular, una línea por fila, `#` viva, `.` muerta.
- Mundo finito del tamaño de la grilla: fuera de los bordes todo está muerto. Sin wrap-around.
- Imprime por stdout la grilla tras N generaciones, en el mismo formato.
- Con `generaciones = 0` imprime el estado inicial sin cambios.
- Solo biblioteca estándar, en un único script.

`vida.py` se obtiene del chat; no se escribe ni se parchea a mano. Entre intentos se corrige el
prompt.

## 3. Verificación

```bash
python tests/test_vida.py vida.py
```

Los nueve tests en verde son el criterio de correctitud.
