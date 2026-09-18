#!/usr/bin/env python3
"""Consulta el catalogo de OpenRouter y lo imprime como tablas de markdown.

Existe para que las cifras de `EXPLORACION.md` sean reproducibles: cada fila sale de
`GET https://openrouter.ai/api/v1/models`, que es publico y no pide credenciales.

Uso:

    python herramientas/catalogo.py autores openai anthropic x-ai google deepseek qwen moonshotai
    python herramientas/catalogo.py fichas openai/gpt-5.6-luna anthropic/claude-haiku-4.5

`autores` lista los modelos de cada autor, del mas nuevo al mas viejo, para elegir cual es el
mas avanzado. `fichas` imprime la tabla de precios y contexto y la de parametros soportados.

Solo biblioteca estandar.
"""

import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

CATALOGO = "https://openrouter.ai/api/v1/models"
POR_MILLON = 1_000_000


def traer():
    try:
        with urllib.request.urlopen(CATALOGO, timeout=60) as r:
            return json.loads(r.read().decode("utf-8")).get("data") or []
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        sys.exit("No se pudo leer el catalogo: %s" % e)


def precio(modelo, clave):
    """Los precios vienen por token y como texto. Los paso a dolares por millon."""
    valor = (modelo.get("pricing") or {}).get(clave)
    try:
        return "$%.4f" % (float(valor) * POR_MILLON)
    except (TypeError, ValueError):
        return "n/d"


def fecha(modelo):
    marca = modelo.get("created")
    if not marca:
        return "n/d"
    return datetime.fromtimestamp(marca, timezone.utc).strftime("%Y-%m-%d")


def contexto(modelo):
    valor = modelo.get("context_length")
    return "{:,}".format(valor).replace(",", ".") if valor else "n/d"


def fila(modelo):
    return "| `%s` | %s | %s | %s | %s |" % (
        modelo.get("id", "n/d"), precio(modelo, "prompt"), precio(modelo, "completion"),
        contexto(modelo), fecha(modelo),
    )


def tabla_precios(modelos):
    print("| Modelo | Entrada | Salida | Contexto | Publicado |")
    print("|---|---|---|---|---|")
    for m in modelos:
        print(fila(m))


def tabla_parametros(modelos):
    print()
    print("| Modelo | Parametros soportados |")
    print("|---|---|")
    for m in modelos:
        params = sorted(m.get("supported_parameters") or [])
        listado = ", ".join("`%s`" % p for p in params) if params else "n/d"
        print("| `%s` | %s |" % (m.get("id", "n/d"), listado))


def por_autores(modelos, autores):
    for autor in autores:
        propios = [m for m in modelos if m.get("id", "").split("/")[0] == autor]
        propios.sort(key=lambda m: m.get("created") or 0, reverse=True)
        print()
        print("### %s (%d modelos)" % (autor, len(propios)))
        print()
        if not propios:
            print("Sin modelos con ese autor. Los autores son el tramo anterior a la barra")
            print("del id: `openai/...`, `x-ai/...`, `moonshotai/...`.")
            continue
        tabla_precios(propios)


def por_fichas(modelos, ids):
    indice = {m.get("id"): m for m in modelos}
    faltantes = [i for i in ids if i not in indice]
    elegidos = [indice[i] for i in ids if i in indice]
    tabla_precios(elegidos)
    tabla_parametros(elegidos)
    if faltantes:
        print()
        print("No estan en el catalogo: %s" % ", ".join(faltantes))


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("autores", "fichas"):
        sys.exit(__doc__)
    modelos = traer()
    print("<!-- %s consultado el %s: %d modelos -->"
          % (CATALOGO, datetime.now().strftime("%Y-%m-%d"), len(modelos)))
    if sys.argv[1] == "autores":
        por_autores(modelos, sys.argv[2:])
    else:
        por_fichas(modelos, sys.argv[2:])


if __name__ == "__main__":
    main()
