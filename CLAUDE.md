# CLAUDE.md

Instrucciones para los agentes de IA que trabajen en este repositorio.

## Contexto

Interfaz de chat multi-modelo sobre OpenRouter y, con ella, la resolución del juego de la vida
de Conway en la mínima cantidad de prompts. `SPEC.md` contiene la especificación completa y
debe leerse antes de modificar código.

## Regla principal

**`vida.py` se obtiene del chat con el modelo, no de este agente.** No debe escribirse,
completarse ni parchearse a mano: el archivo del repositorio tiene que coincidir exactamente
con el que aparece en el log de la conversación. Cuando un intento falla, lo que se reescribe
es el prompt, en una conversación nueva.

Los archivos de `logs/` son registro de auditoría. No se editan, no se reordenan y no se
eliminan los intentos fallidos.

## Restricciones

- La API key no se escribe en ningún archivo versionado. Va en `.env`, que está excluido.
- `tests/test_vida.py` no se modifica.
- `contexto/contexto_estatico.md` no se modifica entre corridas: cualquier cambio invalida el
  prefijo cacheado y elimina el cache hit.
- No se agregan dependencias. La interfaz usa solo biblioteca estándar.

## Convenciones

- Código, nombres y mensajes de commit en castellano. Identificadores sin acentos.
- Los mensajes de commit explican el cambio. Un commit por unidad de trabajo.
- Toda cifra del informe debe ser reconciliable contra un log.

## Verificación

```bash
python tests/test_vida.py vida.py
```
