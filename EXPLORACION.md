# Exploración de la plataforma

Notas de la etapa previa a escribir código: qué es un router, cómo está el mapa de modelos y
qué parámetros acepta cada proveedor.

Todas las cifras salen de dos fuentes consultadas el **2026-09-17**:

- `GET https://openrouter.ai/api/v1/models`, que ese día devolvió **446 modelos**. Es público y
  no pide credenciales. Se consulta con `herramientas/catalogo.py` (ver §5).
- El payload de `https://openrouter.ai/rankings`, que trae el leaderboard (score estilo Elo y
  win rate) y el uso diario por modelo. **Estos datos no están en la API de modelos**: el campo
  `supported_parameters` sí, el puesto en los benchmarks no.

## 1. Qué es un router de modelos

**Un router recibe el pedido y elige por vos a qué modelo mandarlo según la tarea que detecta;
resuelve el problema de tener que decidir y mantener a mano qué modelo conviene para cada
pedido, y de quedar atado a uno cuando cambia el catálogo, el precio o la disponibilidad.**

El Auto Router (`openrouter/auto`) clasifica cada request y lo rutea al modelo más usado del
mercado para ese tipo de tarea, medido por el gasto agregado de la comunidad en los últimos
días. La decisión no la toma un benchmark: la toma la facturación de los demás.

El catálogo tiene varios routers, todos bajo el autor `openrouter`:

| Router | Qué hace | Precio |
|---|---|---|
| `openrouter/auto` | Elige el mejor modelo para el prompt según el gasto agregado del mercado | `-1` |
| `openrouter/auto-beta` | Igual, con clasificación de tarea explícita y filtros propios | `-1` |
| `openrouter/pareto-code` | Lista corta de modelos de código por percentil de Artificial Analysis, con `min_coding_score` | `-1` |
| `openrouter/fusion` | Delibera en paralelo con un panel de modelos y sintetiza una respuesta | `-1` |
| `openrouter/free` | Elige al azar entre los modelos gratuitos disponibles | `0` |
| `openrouter/bodybuilder` | Traduce un pedido en lenguaje natural a un request armado de la API | `-1` |

El precio `-1` es la manera que tiene el catálogo de decir "el que cobre el modelo elegido": el
router no tiene tarifa propia, así que el costo de una llamada ruteada no se puede anticipar
desde la ficha. Para una misión con presupuesto eso es justamente lo que se quiere evitar, y es
la razón por la que los cuatro slots del ejercicio 1 fijan el modelo a mano.

`openrouter/auto` declara 2.000.000 de tokens de contexto y acepta el panel completo de
parámetros, porque el límite real lo pone el modelo que termine atendiendo.

## 2. El mapa de modelos

El modelo más avanzado de cada proveedor conocido, tomando el más reciente de su línea tope.
Los precios son por millón de tokens. El puesto es la posición en el leaderboard de
`openrouter.ai/rankings`, que ese día tenía **146 modelos evaluados**.

| Proveedor | Modelo | Entrada | Salida | Contexto | Publicado | Puesto (score) |
|---|---|---|---|---|---|---|
| OpenAI | `openai/gpt-6-astra-pro` | $10.00 | $50.00 | 1.050.000 | 2026-09-04 | sin entrada |
| Anthropic | `anthropic/claude-fable-5.1` | $10.00 | $50.00 | 1.000.000 | 2026-09-01 | 5 (1322) |
| xAI | `x-ai/grok-4.6` | $2.00 | $6.00 | 500.000 | 2026-08-12 | 15 (1304) |
| Google | `google/gemini-3.8-flash` | $0.75 | $3.75 | 1.048.576 | 2026-09-02 | 10 (1315) |
| DeepSeek | `deepseek/deepseek-v4.1-flash` | $0.30 | $1.20 | 1.048.576 | 2026-09-10 | sin entrada |
| Qwen | `qwen/qwen3.8-max-0902` | $2.00 | $6.00 | 1.000.000 | 2026-09-03 | 19 (1294, como `qwen3.8-max`) |
| Kimi | `moonshotai/kimi-k3` | $2.10 | $10.95 | 1.048.576 | 2026-07-16 | 3 (1353) |

Lo que se lee en esa tabla:

- **El leaderboard va más lento que el catálogo.** Los modelos publicados en septiembre todavía
  no están evaluados. De OpenAI, el primero que aparece en el ranking es `gpt-5.5`, puesto 33
  con score 1269: varias versiones atrás del tope de su propio catálogo. Elegir por benchmark
  implica elegir modelos viejos.
- **El podio está mezclado.** Los puestos 1 y 4 (`sourceful/riverflow-v2.5-pro`, score 1437, y
  `microsoft/mai-image-2.6`, 1335) son modelos de imagen. El score viene de una arena general,
  no de calidad de texto: no se puede leer como "el mejor programador".
- **Precio y puesto no están alineados.** Kimi K3 sale tercero cobrando $2.10 de entrada;
  `claude-fable-5.1` sale quinto cobrando $10.00, casi cinco veces más. Gemini 3.8 Flash entra
  décimo a $0.75.
- **Las ventanas de contexto convergieron en el millón.** La excepción hacia abajo es Grok 4.6
  con 500.000, y hacia arriba `deepseek-v4-flash-0731` con 1.310.720: el contexto más grande de
  todo el grupo y, a la vez, el modelo más barato.
- Casi todos los modelos tienen una variante `:batch` a mitad de precio, y algunos una `:free`.

## 3. Los cuatro slots del ejercicio 1

Los cuatro ids del enunciado (verificados por la cátedra al 2026-09-02) **siguen vigentes en el
catálogo al 2026-09-17**: ninguno hizo falta reemplazar.

| Slot | Modelo | Entrada | Salida | Contexto | Puesto (score) | Uso del día |
|---|---|---|---|---|---|---|
| 1 | `openai/gpt-5.6-luna` | $0.20 | $1.20 | 1.050.000 | sin entrada | **1.º**, 15,82 T de tokens |
| 2 | `anthropic/claude-haiku-4.5` | $1.00 | $5.00 | 200.000 | 99 (1135) | fuera del top 20 |
| 3 | `google/gemini-3.7-flash` | $0.75 | $3.75 | 1.048.576 | 9 (1315) | fuera del top 20 |
| 4 | `deepseek/deepseek-v4-flash-0731` | $0.06 | $0.12 | 1.310.720 | 42 (1251) | **5.º**, 10,62 T de tokens |

Dos observaciones que importan para el ejercicio 2:

- **El slot 4 está más barato de lo que documentábamos.** `SPEC.md` y `README.md` anotan $0.065
  de entrada y $0.18 de salida; el catálogo de hoy dice **$0.06 y $0.12**. Contra el slot 2 no
  es 15 veces más barato sino **16,7 veces en entrada y 41,7 en salida**. El enunciado usa la
  proporción de entrada, que es la que se mantiene cerca de 15.
- **Los dos modelos que el ejercicio hace usar son los dos más usados de la plataforma**: el
  slot 1 es el primero del día con 15,82 T de tokens y el slot 4 es el quinto con 10,62 T. El
  "escalón barato" no es un modelo marginal, es el que el mercado ya eligió.

El slot 2, en cambio, está en el puesto 99 de 146, el más bajo de los cuatro, y es el segundo
más caro. Su lugar en el ejercicio no se justifica por calidad ni por precio, sino por ser el
único de los cuatro con caching explícito.

Una curiosidad de la tabla de precios: la variante `deepseek/deepseek-v4-flash-0731:batch` sale
$0.11 / $0.33, es decir **más caro que el modelo base**, al revés que en el resto del catálogo,
donde `:batch` cuesta la mitad. Si se busca ahorro, el batch de este modelo no es el camino.

## 4. Parámetros: qué acepta cada proveedor

`supported_parameters` tal como lo devuelve la API para los cuatro slots. La lista es por
modelo, no por proveedor: dos modelos del mismo proveedor no aceptan lo mismo.

| Modelo | Parámetros soportados |
|---|---|
| `openai/gpt-5.6-luna` | `include_reasoning`, `max_completion_tokens`, `max_tokens`, `reasoning`, `reasoning_effort`, `response_format`, `seed`, `structured_outputs`, `tool_choice`, `tools` |
| `anthropic/claude-haiku-4.5` | `include_reasoning`, `max_completion_tokens`, `max_tokens`, `reasoning`, `response_format`, `stop`, `structured_outputs`, `temperature`, `tool_choice`, `tools`, `top_k`, `top_p` |
| `google/gemini-3.7-flash` | `include_reasoning`, `max_tokens`, `reasoning`, `reasoning_effort`, `response_format`, `seed`, `stop`, `structured_outputs`, `temperature`, `tool_choice`, `tools`, `top_p` |
| `deepseek/deepseek-v4-flash-0731` | `frequency_penalty`, `include_reasoning`, `logit_bias`, `logprobs`, `max_tokens`, `min_p`, `parallel_tool_calls`, `presence_penalty`, `reasoning`, `reasoning_effort`, `repetition_penalty`, `response_format`, `seed`, `stop`, `structured_outputs`, `temperature`, `tool_choice`, `tools`, `top_a`, `top_k`, `top_logprobs`, `top_p` |

Las diferencias concretas:

- **OpenAI no expone ninguna perilla de sampling.** Ni `temperature`, ni `top_p`, ni `top_k`, ni
  penalidades: la ficha de `gpt-5.6-luna` (y también la de `gpt-6-astra-pro`) solo acepta
  razonamiento, formato de respuesta, `seed` y herramientas. Lo que en otros proveedores se
  regula con temperatura, acá se regula con `reasoning.effort`. Es coherente con el slot que le
  tocó en el ejercicio.
- **`claude-haiku-4.5` acepta `reasoning` pero no `reasoning_effort`.** El presupuesto de
  pensamiento se pasa como `{"max_tokens": N}`, no como nivel; por eso la interfaz ofrece el
  selector de effort en los slots 1 y 4 y no en el 2. No es una limitación de Anthropic sino de
  este modelo: `claude-fable-5.1` sí acepta `reasoning_effort`, y además un `verbosity` que no
  aparece en ninguna otra ficha del grupo.
- **DeepSeek, Qwen y Kimi exponen el panel completo** (`min_p`, `top_a`, `logit_bias`,
  `repetition_penalty`, `top_logprobs`): son los modelos de pesos abiertos, servidos por
  proveedores que dejan tocar el sampler entero.
- **`structured_outputs` lo aceptan los cuatro slots.** El JSON Schema no es una exclusividad de
  Gemini: el reparto de capacidades por slot es didáctico, no técnico.
- **`cache_control` no aparece en ninguna lista.** El caching no es un parámetro de sampling:
  es una anotación dentro del mensaje (Anthropic, Qwen) o un comportamiento automático del
  proveedor (OpenAI, Gemini, DeepSeek). Por eso la ficha no avisa si un pedido va a cachear, y
  por eso el umbral del slot 2 que documenta `SPEC.md` §1 hubo que medirlo contra la API en vez
  de leerlo del catálogo.

## 5. Cómo reproducir estas cifras

```bash
# los modelos de cada proveedor, del mas nuevo al mas viejo
python herramientas/catalogo.py autores openai anthropic x-ai google deepseek qwen moonshotai

# precios, contexto y parametros soportados de fichas puntuales
python herramientas/catalogo.py fichas openai/gpt-5.6-luna anthropic/claude-haiku-4.5 \
    google/gemini-3.7-flash deepseek/deepseek-v4-flash-0731
```

Los puestos del leaderboard y el uso diario no salen de la API de modelos: están en el payload
de `https://openrouter.ai/rankings`. La misma comparación en pantalla, para los cuatro slots,
está en
[la vista comparativa](https://openrouter.ai/compare/openai/gpt-5.6-luna/anthropic/claude-haiku-4.5/google/gemini-3.7-flash/deepseek/deepseek-v4-flash-0731).
