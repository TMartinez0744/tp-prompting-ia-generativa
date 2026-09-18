#!/usr/bin/env python3
"""Suma el consumo de los logs de conversacion y lo imprime como tablas de markdown.

Existe para que ninguna cifra del informe se escriba a mano: cada numero sale de la linea
`**Usage**` de un log, que es lo que devolvio la API.

Uso:

    python herramientas/cuenta.py                       # todos los logs
    python herramientas/cuenta.py --slot 4              # solo los del slot 4
    python herramientas/cuenta.py logs/un-log.md ...    # los que se nombren

Solo biblioteca estandar.
"""

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LOGS = RAIZ / "logs"

# El formato de la linea de usage cambio entre corridas: los primeros logs no informan los
# tokens escritos en cache. El grupo es opcional para que los viejos sigan siendo legibles.
USAGE = re.compile(
    r"\*\*Usage\*\* entrada (\d+) \(cacheados (\d+)(?:, escritos (\d+))?\) \| "
    r"salida (\d+) \| razonamiento (\d+) \| costo \$([\d.]+) \| descuento cache \$([\d.]+)"
)
MODELO = re.compile(r"^- Modelo: `(.+)`$", re.M)
OPCIONES = re.compile(r"^\*\*Opciones\*\* (.+)$", re.M)
CAMPOS = ("entrada", "cacheados", "escritos", "salida", "razonamiento", "costo", "descuento")


def turnos(texto):
    for m in USAGE.finditer(texto):
        e, c, w, s, r, costo, desc = m.groups()
        yield {
            "entrada": int(e), "cacheados": int(c), "escritos": int(w or 0),
            "salida": int(s), "razonamiento": int(r),
            "costo": float(costo), "descuento": float(desc),
        }


def leer(ruta):
    texto = ruta.read_text(encoding="utf-8")
    modelo = MODELO.search(texto)
    return {
        "archivo": ruta.name,
        "modelo": modelo.group(1) if modelo else "desconocido",
        "opciones": sorted(set(OPCIONES.findall(texto))),
        "turnos": list(turnos(texto)),
    }


def sumar(turnos_):
    total = {k: 0 for k in CAMPOS}
    for t in turnos_:
        for k in CAMPOS:
            total[k] += t[k]
    return total


def fila(etiqueta, t):
    return "| %s | %d | %d | %d | %d | %d | $%.6f |" % (
        etiqueta, t["entrada"], t["cacheados"], t["escritos"], t["salida"],
        t["razonamiento"], t["costo"],
    )


def tabla(conv):
    print()
    print("### %s" % conv["archivo"])
    print()
    print("- Modelo: `%s`" % conv["modelo"])
    if conv["opciones"]:
        print("- Opciones: %s" % "; ".join(conv["opciones"]))
    if not conv["turnos"]:
        print("- Sin turnos con usage.")
        return {k: 0 for k in CAMPOS}
    print()
    print("| Turno | Entrada | Cacheados | Escritos | Salida | Razonamiento | Costo |")
    print("|---|---|---|---|---|---|---|")
    for n, t in enumerate(conv["turnos"], 1):
        print(fila(str(n), t))
    total = sumar(conv["turnos"])
    print(fila("**Total**", total))
    return total


def elegir(argv):
    if "--slot" in argv:
        slot = argv[argv.index("--slot") + 1]
        return sorted(LOGS.glob("*-slot%s-*.md" % slot))
    rutas = [Path(a) for a in argv if not a.startswith("--")]
    return rutas or sorted(LOGS.glob("*.md"))


def main():
    rutas = elegir(sys.argv[1:])
    faltantes = [r for r in rutas if not r.is_file()]
    if faltantes:
        sys.exit("No encuentro: %s" % ", ".join(str(r) for r in faltantes))
    if not rutas:
        sys.exit("No hay logs para contar.")

    conversaciones = [leer(r) for r in rutas]
    totales = [tabla(c) for c in conversaciones]
    gran = sumar([t for t in totales])
    turnos_totales = sum(len(c["turnos"]) for c in conversaciones)

    print()
    print("### Total de %d conversaciones, %d turnos" % (len(conversaciones), turnos_totales))
    print()
    print("| | Entrada | Cacheados | Escritos | Salida | Razonamiento | Costo |")
    print("|---|---|---|---|---|---|---|")
    print(fila("**Total**", gran))
    print()
    if gran["entrada"]:
        print("- Tokens de entrada servidos desde cache: %d de %d (%.1f%%)"
              % (gran["cacheados"], gran["entrada"], 100.0 * gran["cacheados"] / gran["entrada"]))
    print("- Descuento por cache informado por la API: $%.6f" % gran["descuento"])
    print("- Costo total: $%.6f" % gran["costo"])


if __name__ == "__main__":
    main()
