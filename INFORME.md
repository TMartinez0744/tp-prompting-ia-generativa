# Informe del ejercicio 3: la cuenta final

## Método

El trabajo previo —qué es un router, el mapa de los siete proveedores y la comparación de
parámetros— está en [`EXPLORACION.md`](EXPLORACION.md). De ahí salen los precios con los que se
reconcilia cada costo de este informe (catálogo consultado el 2026-09-17).

Ninguna cifra de este informe se escribió a mano. Todas salen de la línea `**Usage**` de los
logs de `logs/`, que es el `usage` que devolvió la API, y se suman con:

```bash
python herramientas/cuenta.py
```

Las cuatro conversaciones del ejercicio 2 se suman pasando sus logs de forma explícita. El filtro
`--slot 4` no sirve para esto: incluye también la prueba del slot 4 del ejercicio 1 y la
comparación de §2, y da $0.006566 en lugar de $0.006252.

```bash
python herramientas/cuenta.py logs/20260918-003247-slot4-deepseek-v4-flash-0731.md logs/20260918-003740-slot4-deepseek-v4-flash-0731.md logs/20260918-004105-slot4-deepseek-v4-flash-0731.md logs/20260918-004158-slot4-deepseek-v4-flash-0731.md
```

Cada costo informado se verifica contra la tarifa en las secciones que siguen.

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

Se fijó el proveedor en `app.py` (`provider.order = ["Relace"]`, la misma solución que ya tenía
el slot 2 con Anthropic). Aun así, el reenvío 3 volvió con `cached_tokens` en 0, pese a caer en
el mismo proveedor que el intento ganador. Hay dos causas compatibles con los datos, y los datos
no alcanzan para distinguirlas:

- **El effort cambia lo que recibe el proveedor.** El mismo texto, en el mismo proveedor, midió
  1.406 tokens de entrada con `high` (intento 1) y 1.327 con `medium` (reenvío 3). Si esa
  diferencia está al principio del pedido, el prefijo cacheado por el intento 1 no le servía a
  ningún pedido en `medium`.
- **El cache pudo haber vencido.** Entre el intento 1 y el reenvío 3 pasaron nueve minutos.

En cualquiera de los dos casos, el reenvío 3 escribió el prefijo y el 4, un minuto después, lo
leyó: **1.280 de 1.327 tokens de entrada servidos desde cache, el 96,5%**. La cuenta cierra con
la tarifa de lectura de Relace, $0.012 por millón:

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

No se tuvo acceso al dashboard de actividad de la cuenta, así que el contraste se hace contra el
consumo que informa `GET /api/v1/key`, que es el total acumulado de la key.

La key informa **$0.123294** consumidos, contra **$0.056525** sumados de los logs del
repositorio. La diferencia, **$0.066769**, corresponde a llamadas del 2026-09-04 hechas durante
la depuración de la interfaz, cuyos logs se descartaron del repositorio por no formar parte de
la entrega. Las cifras se tomaron de esos logs antes de descartarlos:

| Hora (UTC−3) | Modelo | Qué era | Costo |
|---|---|---|---|
| 17:54 | `deepseek/deepseek-v4-flash-0731` | Primera llamada con la key | $0.000149 |
| 17:54 | `openai/gpt-5.6-luna` | Effort `low`, primera tanda del ejercicio 1 | $0.001834 |
| 17:55 | `openai/gpt-5.6-luna` | Effort `high`, primera tanda del ejercicio 1 | $0.017395 |
| 17:56 | `openai/gpt-5.6-luna` | Mensaje manual que se mezcló en la conversación anterior | $0.001357 |
| 17:57 | `anthropic/claude-haiku-4.5` ×2 | Cache sin proveedor fijo: no escribió cache | $0.010333 |
| 17:57 | `google/gemini-3.7-flash` | JSON Schema, primera tanda del ejercicio 1 | $0.003542 |
| 17:59 | `anthropic/claude-haiku-4.5` ×2 | Repetición de la anterior | $0.010380 |
| 18:00 – 18:03 | `anthropic/claude-haiku-4.5` ×4 | Sondas para ubicar el umbral cacheable (§2) | $0.019005 |
| 18:15 – 18:19 | `openai/gpt-5.6-luna` ×4 | Pruebas de la interfaz tras corregir un defecto | $0.002774 |
| | | **Total** | **$0.066769** |

Ninguna corresponde al ejercicio 2:

- Todas son del 4 de septiembre. El ejercicio 2 se corrió el 18.
- Antes de las corridas del 18, la key marcaba $0.115230 contra $0.048461 en logs: la misma
  diferencia de $0.066769, al sexto decimal. Todo lo gastado después está en `logs/`.

Las pruebas de la interfaz incluyen $0.000018 obtenidos por diferencia: el log de una de ellas se
descartó sin registrar su costo. Todo lo demás sale de los logs.

Crédito restante: $0.876706 de $1.

## 4. Conclusión

**Bajar el effort de `high` a `medium` en el slot 4.** Los cuatro envíos del mismo prompt
pasaron los nueve tests, y el de `medium` con proveedor fijo costó $0.000876 contra los
$0.003646 del ganador en `high`: **4,2 veces menos por el mismo resultado**. El acierto vino de
la especificación, no del presupuesto de pensamiento. El effort se mantiene en `medium` también
en un eventual segundo intento: cambiarlo puede alterar el prefijo y perder el cache que ese
intento tiene que mostrar (§1).

**Fijar el proveedor del slot 4, no dejarlo al reparto de OpenRouter.** Sin `provider.order` el
prefijo cae en un proveedor distinto cada vez, el cache nunca acierta y la tarifa varía hasta 7x
entre los 28 que sirven el modelo.

**No tocar el prompt.** En el intento ganador la entrada fue el 2,3% del costo ($0.0000844 de
$0.003646): el resto es salida, y de esa salida el 97% fue pensamiento. Acortar la
especificación ahorraría centésimas de centavo y pondría en riesgo el "1 prompt", que es lo
único caro de recuperar.
