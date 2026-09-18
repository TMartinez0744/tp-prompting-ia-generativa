# Informe del ejercicio 3: la cuenta final

## Método

Ninguna cifra de este informe se escribió a mano. Todas salen de la línea `**Usage**` de los
logs de `logs/`, que es el `usage` que devolvió la API, y se suman con:

```bash
python herramientas/cuenta.py            # todas las conversaciones
python herramientas/cuenta.py --slot 4   # las del ejercicio 2
```

Los precios usados para reconciliar son los del catálogo (`EXPLORACION.md`, consultado el
2026-09-17). Cada costo informado se verifica contra la tarifa en las secciones que siguen.

## 1. El ejercicio 2, intento por intento

**Resultado: correcto en 1 prompt, al primer intento, sin intentos quemados.** Los nueve tests
pasan contra el `vida.py` que salió del chat, sin tocar una línea.

Las cuatro conversaciones del slot 4 son con el mismo prompt (`prompts/prompt_vida.md`, 4.671
caracteres). Solo la primera es un intento; las otras tres son reenvíos del mismo texto para
producir la evidencia de cache que el ejercicio exige y que un acierto al primer intento no
genera por sí solo. Su salida se descartó.

| # | Log (`logs/…-slot4-deepseek-v4-flash-0731.md`) | Qué es | Proveedor | Effort | Entrada | Cacheados | Salida | Razonamiento | Costo | Tests |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `20260918-003247` | **Intento ganador** | Relace | `high` | 1.406 | 0 | 29.681 | 28.801 | $0.003646 | 9/9 |
| 2 | `20260918-003740` | Reenvío | StreamLake | `medium` | 1.327 | 0 | 5.438 | 4.885 | $0.001051 | 9/9 |
| 3 | `20260918-004105` | Reenvío, proveedor fijo | Relace | `medium` | 1.327 | 0 | 6.633 | 5.016 | $0.000876 | 9/9 |
| 4 | `20260918-004158` | Reenvío, proveedor fijo | Relace | `medium` | 1.327 | **1.280** | 5.508 | 4.436 | $0.000679 | 9/9 |
| | | **Total** | | | **5.387** | **1.280** | **47.260** | **43.138** | **$0.006252** | |

`vida.py` es el bloque de código del turno 1 del log 1, extraído tal cual. La salida de los
tests:

```
$ python tests/test_vida.py vida.py
test_blinker_oscila_de_vertical_a_horizontal ... ok
test_blinker_vuelve_al_original_en_dos_generaciones ... ok
test_bloque_es_naturaleza_muerta ... ok
test_borde_sin_wrap ... ok
test_celula_sola_muere_por_soledad ... ok
test_generacion_cero_devuelve_el_estado_inicial ... ok
test_glider_se_desplaza_una_diagonal_en_cuatro_generaciones ... ok
test_grilla_vacia_sigue_vacia ... ok
test_nacimiento_por_tres_vecinas ... ok

Ran 9 tests in 0.319s

OK
```

### Los tokens de pensamiento

**El 91,3% de los tokens de salida del ejercicio 2 fue pensamiento** (43.138 de 47.260), y se
facturaron a tarifa de salida como cualquier otro token. La cuenta del intento ganador cierra al
sexto decimal:

```
1.406 x $0.06/M + 29.681 x $0.12/M = $0.003646   (informado: $0.003646)
```

Si el razonamiento se facturara aparte, o no se facturara, no daría. El modelo devolvió
`reasoning_tokens` en los cuatro turnos: el caso de los razonadores opacos que el enunciado
anticipa no se dio con este modelo.

### El cache

El cache de DeepSeek es automático por prefijo, pero **no acierta si el pedido lo atiende otro
proveedor**. OpenRouter reparte este modelo entre 28 proveedores con tokenizaciones y tarifas
distintas: el reenvío 2 cayó en StreamLake y el prefijo no coincidió con el de Relace, así que
volvió con `cached_tokens` en 0.

Fijando el proveedor en `app.py` (`provider.order = ["Relace"]`, la misma solución que ya tenía
el slot 2 con Anthropic), el reenvío 4 acertó: **1.280 de 1.327 tokens de entrada servidos desde
cache, el 96,5%**. La cuenta cierra con la tarifa de lectura de Relace, $0.012 por millón:

```
47 x $0.06/M + 1.280 x $0.012/M + 5.508 x $0.12/M = $0.000679   (informado: $0.000679)
```

**Cuánto ahorró:** la entrada de ese turno pasó de $0.0000796 a $0.0000182, un 77% menos. En
plata, **$0.000061**. Con un prompt de 1.327 tokens el cache es irrelevante para la factura: el
turno cuesta $0.000679 y el 97% de eso es salida. El ahorro del cache aparece cuando el prefijo
es grande, como en el slot 2, donde un bloque de 6.014 tokens bajó el turno un 68,4% (§2).

**Hallazgo: el hit no se ve en `cache_discount`.** El enunciado dice que se observa ahí; la API
devolvió `$0.000000` en los catorce turnos del repositorio, incluidos los que leyeron cache. La
evidencia real son `cached_tokens` y la caída del `cost`.

## 2. Lo medido en el ejercicio 1

### El effort se paga íntegro en la salida

La misma pregunta al slot 1, dos conversaciones, cambiando solo `reasoning.effort`:

| Effort | Entrada | Salida | Razonamiento | Costo |
|---|---|---|---|---|
| `low` | 67 | 3.200 | 2.450 | $0.003853 |
| `high` | 67 | 14.991 | 14.502 | $0.018003 |

Costo por 4,7 sin cambiar una coma del prompt. En `high`, el 96,7% de la salida facturada fue
pensamiento que nadie lee. Las dos cuentas cierran exactas contra la tarifa $0.20/$1.20.

### La economía del caching explícito

Dos turnos de la misma conversación del slot 2, con un bloque de 6.014 tokens marcado con
`cache_control` (`20260904-180549`):

| Turno | Entrada | Cacheados | Escritos | Salida | Costo |
|---|---|---|---|---|---|
| 1 | 6.065 | 0 | 6.014 | 294 | $0.009038 |
| 2 | 6.377 | 6.014 | 0 | 379 | $0.002859 |

**68,4% más barato el segundo turno**, con un contexto más grande. La cuenta cierra tomando la
escritura a 1,25x la tarifa de entrada y la lectura a 0,10x:

```
turno 1:  51 x $1.00/M + 6.014 x $1.25/M + 294 x $5.00/M = $0.009038
turno 2: 363 x $1.00/M + 6.014 x $0.10/M + 379 x $5.00/M = $0.002859
```

Por debajo del mínimo cacheable no hay cache ni aviso: la conversación `20260904-180100` mandó
un bloque menor y pagó tarifa plena (`3.484 x $1.00/M + 348 x $5.00/M = $0.005224`, exacto), con
`cached_tokens` en 0 y sin error.

### El escalón barato, misma pregunta

Un mismo texto de 155 caracteres mandado a los dos slots (`20260918-004310` y `20260918-004316`):

| Slot | Modelo | Entrada | Salida | Razonamiento | Costo |
|---|---|---|---|---|---|
| 2 | `anthropic/claude-haiku-4.5` | 53 | 325 | 0 | $0.001678 |
| 4 | `deepseek/deepseek-v4-flash-0731` | 43 | 1.099 | 887 | $0.000134 |

**12,5 veces más barato el slot 4**, y eso que produjo 3,4 veces más tokens de salida porque
razonó. A igual cantidad de tokens la diferencia sería de 42x en salida.

## 3. Gasto total

Las doce conversaciones del repositorio, según `herramientas/cuenta.py`:

| | Entrada | Cacheados | Escritos | Salida | Razonamiento | Costo |
|---|---|---|---|---|---|---|
| 12 conversaciones, 14 turnos | 25.590 | 7.294 | 6.014 | 70.997 | 62.579 | **$0.056525** |

Reparto:

| Bloque | Costo | Participación |
|---|---|---|
| Ejercicio 1, pruebas de los 4 modelos | $0.048461 | 85,7% |
| Ejercicio 2, las 4 conversaciones del slot 4 | $0.006252 | 11,1% |
| Comparación de la misma pregunta (slots 2 y 4) | $0.001812 | 3,2% |

El 88,1% de los tokens de salida de todo el repositorio fueron pensamiento (62.579 de 70.997).

### Contraste contra la cuenta de OpenRouter

`GET /api/v1/key` informa **$0.121482** consumidos por la key, contra **$0.056525** sumados de
los logs. La diferencia es de **$0.064957**, y no es un error de contabilidad de los logs:

- Antes de las corridas de hoy la key marcaba $0.115230 con $0.048461 en logs: la misma brecha
  de ~$0.0668 ya existía.
- Corresponde a las mediciones del umbral de cache del slot 2 que documenta `SPEC.md` §1, hechas
  contra la API durante el desarrollo de la interfaz, antes de que existiera el registro en
  `logs/`. Por definición no tienen log.
- La lectura de la key va unos segundos atrás: los $0.001812 de la comparación de §2 ya están en
  los logs y todavía no en el total de la key.

**Queda por confirmar contra el dashboard** (openrouter.ai/activity), que muestra el detalle por
request y permite identificar una por una las llamadas sin log. Crédito restante: $0.878518 de
$1.

## 4. Conclusión

**Bajar el effort de `high` a `medium` en el slot 4.** Los cuatro envíos del mismo prompt
pasaron los nueve tests, y el de `medium` con proveedor fijo costó $0.000876 contra los
$0.003646 del ganador en `high`: **4,2 veces menos por el mismo resultado**. El acierto vino de
la especificación, no del presupuesto de pensamiento; `high` queda reservado para un eventual
segundo intento.

**Fijar el proveedor del slot 4, no dejarlo al reparto de OpenRouter.** Sin `provider.order` el
prefijo cae en un proveedor distinto cada vez, el cache nunca acierta y la tarifa varía hasta 7x
entre los 28 que sirven el modelo.

**No tocar el prompt.** En el intento ganador la entrada fue el 2,3% del costo ($0.0000844 de
$0.003646): el resto es salida, y de esa salida el 97% fue pensamiento. Acortar la
especificación ahorraría centésimas de centavo y pondría en riesgo el "1 prompt", que es lo
único caro de recuperar.
