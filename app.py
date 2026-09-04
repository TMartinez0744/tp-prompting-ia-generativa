#!/usr/bin/env python3
"""Servidor de la interfaz de chat: proxy a OpenRouter, contabilidad de usage y log en markdown.

Solo biblioteca estandar. Levanta en http://localhost:8000 y abre el navegador.
"""

import json
import os
import threading
import urllib.error
import urllib.request
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
WEB = RAIZ / "web"
LOGS = RAIZ / "logs"
CONTEXTO_ESTATICO = RAIZ / "contexto" / "contexto_estatico.md"
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
PUERTO = 8000

SLOTS = {
    "1": {
        "id": "openai/gpt-5.6-luna",
        "alias": "GPT-5.6 Luna",
        "proveedor": "OpenAI",
        "precio_in": 0.20,
        "precio_out": 1.20,
        "contexto": 1050000,
        "capacidad": "Effort configurable",
        "control": "effort",
        "razona": True,
    },
    "2": {
        "id": "anthropic/claude-haiku-4.5",
        "alias": "Claude Haiku 4.5",
        "proveedor": "Anthropic",
        "precio_in": 1.00,
        "precio_out": 5.00,
        "contexto": 200000,
        "capacidad": "Caching explicito",
        "control": "cache",
        "razona": False,
        # Sin fijar proveedor, OpenRouter puede enrutar a Amazon Bedrock, que descarta
        # cache_control y devuelve cache_write_tokens en cero.
        "proveedor_forzado": "Anthropic",
    },
    "3": {
        "id": "google/gemini-3.7-flash",
        "alias": "Gemini 3.7 Flash",
        "proveedor": "Google",
        "precio_in": 0.75,
        "precio_out": 3.75,
        "contexto": 1048576,
        "capacidad": "Salidas estructuradas",
        "control": "json",
        "razona": False,
    },
    "4": {
        "id": "deepseek/deepseek-v4-flash-0731",
        "alias": "DeepSeek V4 Flash",
        "proveedor": "DeepSeek",
        "precio_in": 0.065,
        "precio_out": 0.18,
        "contexto": 1310720,
        "capacidad": "El escalon barato",
        "control": "effort",
        "razona": True,
    },
}

ESQUEMA_JSON = {
    "name": "respuesta_estructurada",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "resumen": {"type": "string"},
            "pasos": {"type": "array", "items": {"type": "string"}},
            "supuestos": {"type": "array", "items": {"type": "string"}},
            "confianza": {"type": "number"},
        },
        "required": ["resumen", "pasos", "supuestos", "confianza"],
        "additionalProperties": False,
    },
}


class ErrorApi(Exception):
    pass


def cargar_env():
    ruta = RAIZ / ".env"
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


def ahora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def pedir(cuerpo, api_key):
    datos = json.dumps(cuerpo).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=datos,
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise ErrorApi("HTTP %s: %s" % (e.code, e.read().decode("utf-8", "replace")))
    except urllib.error.URLError as e:
        raise ErrorApi("No se pudo conectar con OpenRouter: %s" % e.reason)


def leer_usage(respuesta):
    """Extrae el consumo de la respuesta. Lo que la API no devuelve vale cero, no se oculta."""
    u = respuesta.get("usage") or {}
    entrada_det = u.get("prompt_tokens_details") or {}
    salida_det = u.get("completion_tokens_details") or {}
    return {
        "entrada": u.get("prompt_tokens") or 0,
        "salida": u.get("completion_tokens") or 0,
        "razonamiento": salida_det.get("reasoning_tokens") or 0,
        "cacheados": entrada_det.get("cached_tokens") or 0,
        "escritos_cache": entrada_det.get("cache_write_tokens") or 0,
        "costo": u.get("cost") or 0.0,
        "descuento_cache": u.get("cache_discount") or 0.0,
    }


def linea_usage(u):
    return (
        "entrada %d (cacheados %d, escritos %d) | salida %d | razonamiento %d | "
        "costo $%.6f | descuento cache $%.6f"
        % (u["entrada"], u["cacheados"], u["escritos_cache"], u["salida"], u["razonamiento"],
           u["costo"], u["descuento_cache"])
    )


class Conversacion:
    """Una conversacion con un modelo. Cambiar de modelo construye otra: no se mezclan."""

    def __init__(self, slot):
        self.slot = slot
        self.cfg = SLOTS[slot]
        self.mensajes = []
        self.turno = 0
        self.costo = 0.0
        self.inicio = ahora()
        marca = datetime.now().strftime("%Y%m%d-%H%M%S")
        alias = self.cfg["id"].split("/")[1]
        self.log = LOGS / ("%s-slot%s-%s.md" % (marca, slot, alias))

    def _escribir(self, texto):
        """Crea el log en el primer turno. Abrir la interfaz no deja archivos vacios."""
        if not self.log.exists():
            LOGS.mkdir(exist_ok=True)
            with self.log.open("w", encoding="utf-8") as f:
                f.write(
                    "# Conversacion slot %s: %s\n\n- Modelo: `%s`\n- Inicio: %s\n"
                    % (self.slot, self.cfg["alias"], self.cfg["id"], self.inicio)
                )
        with self.log.open("a", encoding="utf-8") as f:
            f.write(texto)

    def _cache_activo(self, op):
        """Cada capacidad pertenece a su slot: el cache es del 2 y el JSON Schema del 3."""
        return bool(op.get("cache")) and self.cfg["control"] == "cache"

    def _json_activo(self, op):
        return bool(op.get("json")) and self.cfg["control"] == "json"

    def _opciones(self, op):
        partes = []
        if self.cfg["razona"]:
            partes.append("reasoning.effort=%s" % op.get("effort", "medium"))
        if self._cache_activo(op):
            partes.append("cache_control=ephemeral")
        if self._json_activo(op):
            partes.append("response_format=json_schema")
        return ", ".join(partes) if partes else "ninguna"

    def _cuerpo(self, op):
        mensajes = [dict(m) for m in self.mensajes]
        if self._cache_activo(op) and mensajes:
            # El bloque estatico encabeza el primer mensaje de usuario y lleva el punto de
            # corte del cache. Queda como prefijo identico en todos los turnos.
            texto = CONTEXTO_ESTATICO.read_text(encoding="utf-8")
            mensajes[0]["content"] = [
                {"type": "text", "text": texto, "cache_control": {"type": "ephemeral"}},
                {"type": "text", "text": mensajes[0]["content"]},
            ]
        cuerpo = {"model": self.cfg["id"], "messages": mensajes, "usage": {"include": True}}
        if self.cfg.get("proveedor_forzado"):
            cuerpo["provider"] = {
                "order": [self.cfg["proveedor_forzado"]],
                "allow_fallbacks": False,
            }
        if self.cfg["razona"]:
            cuerpo["reasoning"] = {"effort": op.get("effort", "medium")}
        if self._json_activo(op):
            cuerpo["response_format"] = {"type": "json_schema", "json_schema": ESQUEMA_JSON}
        return cuerpo

    def enviar(self, texto, op, api_key):
        self.turno += 1
        marca_usuario = ahora()
        self.mensajes.append({"role": "user", "content": texto})
        respuesta = pedir(self._cuerpo(op), api_key)
        eleccion = (respuesta.get("choices") or [{}])[0]
        salida = (eleccion.get("message") or {}).get("content") or ""
        self.mensajes.append({"role": "assistant", "content": salida})
        u = leer_usage(respuesta)
        self.costo += u["costo"]
        self._escribir(
            "\n## Turno %d\n\n### user (%s)\n\n%s\n\n### assistant (%s)\n\n%s\n\n"
            "**Usage** %s\n\n**Opciones** %s\n\n**Proveedor** %s\n\n"
            "**Acumulado de la conversacion** $%.6f\n"
            % (self.turno, marca_usuario, texto, ahora(), salida,
               linea_usage(u), self._opciones(op),
               respuesta.get("provider") or "desconocido", self.costo)
        )
        return salida, u


ESTADO = {"conversacion": None}
CANDADO = threading.Lock()

TIPOS = {".html": "text/html", ".css": "text/css", ".js": "application/javascript"}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _json(self, codigo, cuerpo):
        datos = json.dumps(cuerpo).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        ruta = self.path.split("?")[0]
        if ruta == "/api/modelos":
            return self._json(200, {"slots": SLOTS})
        archivo = WEB / "index.html" if ruta == "/" else WEB / ruta.lstrip("/")
        if not archivo.is_file() or WEB not in archivo.resolve().parents:
            self.send_error(404)
            return
        datos = archivo.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", TIPOS.get(archivo.suffix, "text/plain") + "; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def do_POST(self):
        largo = int(self.headers.get("Content-Length") or 0)
        try:
            pedido = json.loads(self.rfile.read(largo).decode("utf-8") or "{}")
        except ValueError:
            return self._json(400, {"error": "JSON invalido"})

        if self.path == "/api/conversacion":
            slot = str(pedido.get("slot", "1"))
            if slot not in SLOTS:
                return self._json(400, {"error": "Slot invalido"})
            with CANDADO:
                ESTADO["conversacion"] = Conversacion(slot)
                conv = ESTADO["conversacion"]
            return self._json(200, {"slot": slot, "log": conv.log.name})

        if self.path == "/api/mensaje":
            api_key = os.environ.get("OPENROUTER_API_KEY")
            if not api_key:
                return self._json(500, {"error": "Falta OPENROUTER_API_KEY en el .env"})
            texto = (pedido.get("texto") or "").strip()
            if not texto:
                return self._json(400, {"error": "Mensaje vacio"})
            op = {
                "effort": pedido.get("effort", "medium"),
                "cache": bool(pedido.get("cache")),
                "json": bool(pedido.get("json")),
            }
            # El candado abarca todo el turno. Sin esto, dos clientes simultaneos comparten la
            # conversacion global, se pisan la numeracion de turnos y mezclan sus mensajes en
            # el mismo log.
            with CANDADO:
                conv = ESTADO["conversacion"]
                if conv is None:
                    return self._json(400, {"error": "No hay conversacion abierta"})
                try:
                    salida, u = conv.enviar(texto, op, api_key)
                except ErrorApi as e:
                    return self._json(502, {"error": str(e)})
            return self._json(200, {
                "respuesta": salida,
                "usage": u,
                "acumulado": conv.costo,
                "turno": conv.turno,
                "log": conv.log.name,
            })

        self.send_error(404)


def main():
    cargar_env()
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("Aviso: falta OPENROUTER_API_KEY. Copia .env.example a .env y pone la key ahi.")
    servidor = ThreadingHTTPServer(("127.0.0.1", PUERTO), Handler)
    url = "http://localhost:%d" % PUERTO
    print("Interfaz en %s  (Ctrl+C para cortar)" % url)
    threading.Timer(0.7, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nCortado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
