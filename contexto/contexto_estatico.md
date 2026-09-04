# Referencia técnica: el juego de la vida de Conway

Documento de referencia del proyecto. La interfaz lo envía como bloque inicial invariante en
las conversaciones del slot 2, marcado con `cache_control`, para que el proveedor lo reutilice
desde el cache en lugar de reprocesarlo en cada turno.

Este archivo no se modifica entre corridas. Cualquier cambio, incluso un espacio, altera el
prefijo y anula el acierto de cache.

---

## 1. Definición

El juego de la vida es un autómata celular de dos dimensiones formulado por John Horton Conway
en 1970. No es un juego en el sentido habitual: no hay jugadores ni decisiones. Se fija un
estado inicial y el sistema evoluciona de forma completamente determinista.

El universo es una grilla de celdas. Cada celda tiene exactamente dos estados posibles, viva o
muerta, y ocho celdas vecinas: las cuatro ortogonales y las cuatro diagonales. Esta relación de
vecindad se conoce como vecindad de Moore de radio 1.

El tiempo avanza en pasos discretos llamados generaciones. En cada paso, todas las celdas se
actualizan **simultáneamente** a partir del estado de la generación anterior. Esta
simultaneidad es la propiedad que más errores de implementación provoca y se trata en detalle
en la sección 6.

## 2. Las reglas

Sea `v` la cantidad de vecinas vivas de una celda en la generación actual. El estado en la
generación siguiente se determina así:

**Para una celda viva:**

- Con `v < 2` muere. Se interpreta como muerte por soledad.
- Con `v = 2` o `v = 3` sobrevive.
- Con `v > 3` muere. Se interpreta como muerte por superpoblación.

**Para una celda muerta:**

- Con `v = 3` nace, es decir, pasa a estar viva.
- En cualquier otro caso permanece muerta.

Las cuatro reglas se resumen en dos condiciones equivalentes y más compactas:

- Una celda viva sobrevive si y solo si `v` está en `{2, 3}`.
- Una celda muerta nace si y solo si `v = 3`.

Esta formulación se abrevia como B3/S23: nace (Birth) con 3 vecinas, sobrevive (Survival) con 2
o 3. La notación permite describir otras reglas de la misma familia, como B36/S23, conocida
como HighLife, o B1357/S1357, conocida como Replicator. Todo lo que sigue en este documento se
refiere exclusivamente a B3/S23.

## 3. Representación textual

La convención adoptada en este proyecto representa la grilla como texto plano:

- Una línea por fila de la grilla.
- El carácter `#` indica una celda viva.
- El carácter `.` indica una celda muerta.
- Todas las líneas tienen la misma longitud: la grilla es rectangular.

Ejemplo de una grilla de 5 por 5 con tres celdas vivas dispuestas en vertical:

```
.....
..#..
..#..
..#..
.....
```

La misma representación se usa para la entrada y para la salida, de modo que la salida de una
corrida puede alimentar directamente la siguiente.

## 4. Condiciones de borde

La definición original de Conway supone un plano infinito. Toda implementación real tiene que
elegir una de estas tres alternativas:

**Mundo finito con bordes muertos.** La grilla tiene el tamaño declarado en la entrada y todo
lo que queda fuera se considera permanentemente muerto. Las celdas del borde tienen menos
vecinas efectivas: una celda de esquina tiene tres vecinas dentro de la grilla, y una celda del
borde no esquina tiene cinco.

**Mundo toroidal, con wrap-around.** Los bordes se conectan entre sí: la columna de más a la
derecha es vecina de la de más a la izquierda, y la fila superior es vecina de la inferior. La
grilla se comporta como la superficie de un toro y toda celda tiene ocho vecinas.

**Mundo infinito.** La grilla crece según hace falta. Requiere una representación dispersa, por
ejemplo un conjunto de coordenadas de celdas vivas, en lugar de una matriz.

**Este proyecto usa la primera alternativa: mundo finito con bordes muertos, sin
wrap-around.** La distinción no es cosmética y produce resultados observablemente distintos.
Considérese esta grilla de 3 por 3:

```
###
...
...
```

Con bordes muertos, la celda central de la fila superior tiene dos vecinas vivas y sobrevive;
las dos celdas de las esquinas superiores tienen una sola vecina viva y mueren; la celda
central de la grilla tiene tres vecinas vivas y nace. El resultado es:

```
.#.
.#.
...
```

Con wrap-around, en cambio, las tres celdas de la fila superior tendrían cada una vecinas
adicionales provenientes de la fila inferior, y la evolución sería otra. Un mismo estado
inicial distingue las dos implementaciones en una sola generación.

## 5. Patrones clásicos

Los patrones se agrupan según su comportamiento en el tiempo.

### Naturalezas muertas

Configuraciones estables: se reproducen idénticas a sí mismas en cada generación. Tienen
período 1.

El **bloque**, la más simple, cuatro celdas en cuadrado. Cada una de las cuatro tiene
exactamente tres vecinas vivas, de modo que las cuatro sobreviven; ninguna celda vecina llega a
tres vecinas vivas, de modo que no nace nada:

```
....
.##.
.##.
....
```

Otras naturalezas muertas frecuentes son la colmena, seis celdas en hexágono; el pan, siete
celdas; y el bote, cinco celdas.

### Osciladores

Configuraciones que vuelven a su estado inicial después de un número fijo de generaciones,
llamado período.

El **blinker**, de período 2, es el oscilador más simple: tres celdas en línea que alternan
entre vertical y horizontal.

```
.....        .....
..#..        .....
..#..   ->   .###.
..#..        .....
.....        .....
```

En la posición vertical, la celda central tiene dos vecinas y sobrevive; las dos celdas de los
extremos tienen una sola vecina y mueren; las dos celdas laterales de la fila central tienen
tres vecinas cada una y nacen. Una generación más tarde, el mismo razonamiento devuelve la
posición vertical.

Otros osciladores conocidos: el **sapo** y el **faro**, ambos de período 2, y el **pulsar**, de
período 3 y 48 celdas vivas.

### Naves

Configuraciones que se reproducen idénticas a sí mismas pero desplazadas en la grilla. Se
trasladan de forma indefinida mientras no encuentren obstáculos.

El **glider** es la nave más pequeña, cinco celdas vivas. Recupera su forma original cada
cuatro generaciones, desplazado una celda en diagonal. Su velocidad es, por lo tanto, c/4 en
diagonal, donde c es la velocidad máxima de propagación de información en la grilla, una celda
por generación.

Estado inicial en una grilla de 10 por 10:

```
.#........
..#.......
###.......
..........
..........
..........
..........
..........
..........
..........
```

Después de cuatro generaciones, el mismo patrón desplazado una celda hacia abajo y una hacia
la derecha:

```
..........
..#.......
...#......
.###......
..........
..........
..........
..........
..........
..........
```

En un mundo finito, un glider que alcanza el borde se desarma y deja tras de sí, según el
ángulo de llegada, un bloque, un blinker o nada.

Existen naves mayores, como la **nave ligera** (LWSS), la **nave mediana** (MWSS) y la **nave
pesada** (HWSS), que se desplazan en horizontal a velocidad c/2.

### Metuselas

Patrones pequeños que evolucionan durante muchas generaciones antes de estabilizarse. El
**R-pentomino**, de cinco celdas, es el más conocido: en un plano infinito tarda 1103
generaciones en estabilizarse y emite seis gliders en el proceso.

## 6. Implementación

### El error de la actualización en el lugar

Las celdas se actualizan simultáneamente. Escribir el estado nuevo sobre la misma grilla que se
está leyendo hace que las celdas ya procesadas contaminen el cálculo de las que faltan, y el
resultado no corresponde a ninguna generación válida.

La solución estándar es mantener dos grillas: leer siempre de la anterior y escribir siempre en
una nueva, e intercambiarlas al terminar cada generación. Alcanza con construir la grilla nueva
desde cero en cada paso y descartar la anterior.

### Conteo de vecinas

Para una celda en la posición `(f, c)`, las ocho vecinas son las posiciones `(f + df, c + dc)`
con `df` y `dc` en `{-1, 0, 1}`, excluyendo el caso `df = 0` y `dc = 0`.

Con bordes muertos, toda posición fuera del rango de la grilla cuenta como muerta. Conviene
verificar los límites explícitamente antes de acceder al arreglo.

En lenguajes con índices negativos válidos, como Python, un índice `-1` no produce error sino
que accede al último elemento del arreglo. Esto introduce, sin ningún mensaje de error, un
wrap-around parcial en el borde superior y en el izquierdo. Es la causa más frecuente de que
una implementación pase las pruebas del interior de la grilla y falle exclusivamente en los
bordes.

### Complejidad

El recorrido directo evalúa todas las celdas en cada generación: `O(f · c)` por generación en
tiempo, y `O(f · c)` en memoria para las dos grillas. Para `g` generaciones, el costo total es
`O(g · f · c)`.

Para grillas grandes y mayormente vacías, una representación dispersa —el conjunto de
coordenadas de las celdas vivas, y el conteo de vecinas solo en las celdas vivas y sus
adyacentes— reduce el costo a un orden proporcional a la cantidad de celdas vivas y no al
tamaño de la grilla. Para grillas chicas, la sobrecarga de la estructura dispersa supera el
ahorro.

Algoritmos como HashLife explotan la repetición de subpatrones mediante memorización sobre un
quadtree, y alcanzan un rendimiento muy superior en patrones regulares y en horizontes de
muchas generaciones. La complejidad de la implementación solo se justifica en esa escala.

### Casos límite

Una implementación correcta tiene que resolver estos casos sin tratamiento especial:

- **Cero generaciones.** La salida es el estado inicial sin ninguna modificación.
- **Grilla vacía.** Sin celdas vivas no puede haber nacimientos, y toda generación posterior es
  igualmente vacía.
- **Celda aislada.** Una única celda viva tiene cero vecinas y muere en la generación
  siguiente.
- **Grilla de una sola fila o de una sola columna.** Ninguna celda puede llegar a tres vecinas,
  de modo que no hay nacimientos y toda celda viva con menos de dos vecinas muere.
- **Patrón que alcanza el borde.** Con bordes muertos no hay desbordamiento: las celdas fuera
  de la grilla simplemente no existen y no se cuentan.

## 7. Propiedades formales

El juego de la vida es **Turing completo**. Se han construido dentro de la grilla compuertas
lógicas a partir de colisiones de gliders, y con ellas circuitos arbitrarios; existen
implementaciones de una máquina de Turing universal y de un intérprete del propio juego de la
vida dentro del juego de la vida.

Como consecuencia, determinar si un patrón dado alcanza alguna vez una configuración
particular es **indecidible** en el caso general: equivale al problema de la detención. No
existe un procedimiento general que prediga el comportamiento a largo plazo de un patrón
arbitrario sin simularlo paso a paso.

Un **jardín del Edén** es una configuración que no tiene predecesor: ninguna configuración
evoluciona hacia ella, de modo que solo puede aparecer como estado inicial. Se demostró su
existencia en 1971 mediante un argumento de conteo, antes de que se conociera ningún ejemplo
explícito.

La evolución no es reversible: dos configuraciones distintas pueden producir la misma
configuración siguiente, y por lo tanto el estado anterior no siempre se puede reconstruir a
partir del actual.

## 8. Origen y difusión

Conway buscaba un conjunto de reglas que cumpliera tres condiciones a la vez: que ninguna
configuración inicial pequeña creciera sin límite de manera evidente, que existieran
configuraciones iniciales que aparentaran crecer indefinidamente, y que hubiera
configuraciones simples que crecieran y cambiaran durante un período largo antes de terminar
de tres maneras posibles: desapareciendo por completo, estabilizándose en una configuración
fija, o entrando en un ciclo que se repitiera indefinidamente.

Llegó a B3/S23 después de descartar por prueba y error muchas otras combinaciones. Reglas
apenas distintas producen o bien extinción rápida de casi todo patrón, o bien crecimiento
descontrolado que llena la grilla de ruido. El equilibrio de B3/S23 entre esos dos extremos es
lo que hace interesante al sistema.

Las reglas se difundieron en octubre de 1970, en la columna de juegos matemáticos que Martin
Gardner escribía para Scientific American. Conway había ofrecido un premio de cincuenta
dólares a quien demostrara que algún patrón crecía sin límite, convencido de que no existía.
El grupo de inteligencia artificial del MIT reclamó el premio ese mismo año con el cañón de
planeadores, descrito en la sección siguiente.

## 9. Patrones de mayor escala

### Crecimiento ilimitado

El **cañón de planeadores de Gosper** ocupa 36 celdas vivas y emite un glider cada 30
generaciones, de forma indefinida. Su existencia prueba que hay configuraciones finitas cuya
población crece sin cota superior, algo que la intuición inicial sobre las reglas no sugiere.

El cañón es además la pieza que abre la construcción de circuitos: un flujo regular de gliders
funciona como señal, y las colisiones entre flujos implementan operaciones lógicas.

### Comedores

Un **comedor** es un patrón estable que absorbe gliders u otros objetos sin sufrir daño
permanente: se deforma con el impacto y recupera su forma original en unas pocas generaciones.
El más común consta de siete celdas. Los comedores cumplen en los circuitos el papel de
terminadores de señal, evitando que los gliders sobrantes contaminen otras regiones.

### Reflectores y duplicadores

Un **reflector** cambia la dirección de un glider que lo atraviesa; un **duplicador** produce
dos gliders a partir de uno. Combinados con cañones y comedores, permiten enrutar señales por
la grilla como en un circuito impreso y son la base de las construcciones de máquinas
universales.

### El problema de la densidad

Un patrón de crecimiento cuadrático, como el **breeder**, produce cañones que a su vez
producen gliders. Su población crece proporcionalmente al cuadrado del número de generaciones,
que es el orden de crecimiento máximo posible: nada puede crecer más rápido, porque la
información no se propaga a más de una celda por generación y la región alcanzable en `g`
generaciones tiene área proporcional a `g²`.

## 10. Configuraciones aleatorias

Una **sopa** es una región inicializada al azar con una densidad dada de celdas vivas. Su
evolución sigue un patrón estadístico bien caracterizado.

Con densidades bajas, cercanas al 5 por ciento, casi todo muere en pocas generaciones por
soledad. Con densidades altas, por encima del 60 por ciento, casi todo muere por
superpoblación en las primeras generaciones y quedan pocos núcleos aislados. El
comportamiento más rico aparece entre el 25 y el 40 por ciento.

Una sopa típica atraviesa tres fases. Durante las primeras decenas de generaciones la
población cae abruptamente y aparecen estructuras locales. Luego viene una fase de actividad
prolongada, con frentes que se propagan y colisiones frecuentes. Finalmente el sistema se
estabiliza en un conjunto disperso de naturalezas muertas y osciladores, con algún glider
escapando hacia los bordes.

En la fase estable, la distribución de patrones es notablemente regular: los bloques y los
blinkers dominan por amplio margen, seguidos por colmenas y panes. Esta distribución es tan
estable entre corridas que sirve como prueba de sanidad de una implementación: una
distribución final muy distinta a la esperada suele indicar un error en el conteo de vecinas o
en el manejo de bordes.

## 11. La familia de reglas B/S

La notación B/S generaliza el sistema. Se listan las cantidades de vecinas que producen
nacimiento después de la `B`, y las que permiten supervivencia después de la `S`. Las reglas
así descriptas se conocen como *life-like* y son 262.144 en total.

Algunas con nombre propio:

- **B3/S23**, el juego de la vida original.
- **B36/S23**, HighLife. Agrega el nacimiento con seis vecinas y contiene un replicador de
  doce celdas que produce copias de sí mismo.
- **B3678/S34678**, Day & Night. Es simétrica bajo el intercambio de celdas vivas y muertas:
  un patrón y su negativo evolucionan de manera equivalente.
- **B2/S**, Seeds. Ninguna celda sobrevive a la generación siguiente; todo el comportamiento
  proviene de los nacimientos, y casi cualquier configuración explota.
- **B1357/S1357**, Replicator. Toda configuración se replica a sí misma.

Cambiar de regla en una implementación bien estructurada se reduce a cambiar dos conjuntos de
enteros. Conviene no incrustar los números 2 y 3 en el código como literales dispersos.

## 12. Formatos de intercambio

Existen tres formatos habituales para patrones, más allá de la representación de este
proyecto.

**Plaintext**, de extensión `.cells`: una línea por fila, `O` para viva y `.` para muerta, con
líneas de comentario que empiezan con `!`. Es legible pero ineficiente para patrones grandes.

**RLE**, *run-length encoded*: codifica secuencias repetidas como un número seguido de `b`
para muerta u `o` para viva, con `$` como fin de fila y `!` como fin del patrón. Una cabecera
declara el ancho, el alto y la regla. El glider se escribe `bob$2bo$3o!`. Es el formato
estándar de intercambio.

**Life 1.06**: una lista de pares de coordenadas de celdas vivas, una por línea. Es el más
adecuado para patrones muy dispersos, donde la mayoría de la grilla está vacía.

## 13. Diseño de casos de prueba

Una batería de pruebas útil cubre cada regla y cada decisión de diseño por separado, con casos
mínimos y verificables a mano.

**Por regla.** Una celda viva con una sola vecina, para la muerte por soledad. Una celda viva
con cuatro vecinas, para la muerte por superpoblación. Una celda muerta con exactamente tres
vecinas, para el nacimiento. Un bloque, para la supervivencia con dos y tres vecinas.

**Por comportamiento temporal.** Un blinker tras una generación, para verificar que el
oscilador cambia. El mismo blinker tras dos generaciones, para verificar que vuelve al estado
inicial: una implementación que confunda las reglas puede acertar la primera y fallar la
segunda.

**Por manejo de bordes.** Un patrón adyacente al borde cuyo resultado difiera entre el mundo
finito y el toroidal. Es la única forma de detectar un wrap-around accidental, que en el
interior de la grilla no produce ninguna diferencia observable.

**Por casos límite.** Cero generaciones, grilla vacía, celda aislada, grilla de una sola fila.

**Por desplazamiento.** Un glider tras cuatro generaciones, que verifica simultáneamente el
conteo de vecinas, la simultaneidad de la actualización y la traslación correcta del patrón.
Es el caso que más errores detecta por sí solo, y por eso conviene que no sea el único: cuando
falla, no indica cuál de las tres cosas está mal.

## 14. Glosario

**Autómata celular.** Sistema discreto formado por una grilla de celdas con un número finito
de estados, que evolucionan en pasos sincrónicos según una regla local uniforme.

**Vecindad de Moore.** Las ocho celdas que rodean a una dada, incluyendo las diagonales. Se
distingue de la vecindad de Von Neumann, que considera solo las cuatro ortogonales.

**Generación.** Un paso de tiempo. Todas las celdas se actualizan a la vez.

**Población.** Cantidad de celdas vivas en una generación dada.

**Período.** Cantidad de generaciones tras las cuales un patrón vuelve a su estado inicial.

**Naturaleza muerta.** Patrón de período 1: no cambia.

**Oscilador.** Patrón de período mayor que 1 que no se desplaza.

**Nave.** Patrón que vuelve a su forma inicial desplazado en la grilla.

**Metusela.** Patrón pequeño que tarda muchas generaciones en estabilizarse.

**Jardín del Edén.** Configuración sin predecesor posible.

**Sopa.** Región inicializada al azar.

**Velocidad c.** Una celda por generación, el límite de propagación en la grilla. Las
velocidades de las naves se expresan como fracciones de c.
