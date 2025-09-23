
# Diseño de galerías (Drilling Design)

Aplicación GUI en Tkinter para diseñar galerías (drifts) y patrones de perforación (cueles, contracuele, zapateras, cajas, corona). Permite elegir familias de geometrías (rectangular, semicircular, D-shaped, horseshoe y bezier), colocar perforaciones y editar el arco. Incluye grilla configurable en metros alineada a los ejes.

## Características

* Geometrías: Rectangular, Semicircular, D-Shaped, Horseshoe, Bezier.
* Asistente por pasos: Geometría → Zapateras → Cajas → Corona → Cueles → Contracuele → Auxiliares.
* Grilla configurable: tamaño de celda (m), líneas mayores y ejes X/Y.
* Edición del arco:

  * Manillas C (centro) y R (radio/ancho) para D-Shaped y Horseshoe.
  * Puntos libres insertables sobre el arco para ajustar la curva localmente.
* Bloqueo de inserción para evitar apilar galerías.
* Exportación a JSON del diseño.

## Requisitos

* Python 3.10+ (probado en 3.13, Windows).
* Solo librerías estándar.

Archivos esperados en el mismo directorio:

* `drilling_design.py` (GUI)
* `drift_geometry.py` (contornos de galería)
* `drift_layout.py` (colocación: zapateras, cajas, corona, auxiliares, contracuele)
* `blast_cuts.py` (patrones de cueles y series)

## Instalación y ejecución

```powershell
git clone https://github.com/FelipeCh23/practica-profesional.git
cd practica-profesional

python -m venv .venv
.venv\Scripts\Activate.ps1

python algoritmo-de-galerias-2.0\drilling_design.py
```

Ajusta la ruta si tu carpeta difiere.

## Uso rápido

1. **Geometría**: elige tipo y parámetros en la barra lateral; haz click en el lienzo para insertarla.
2. **Zapateras / Cajas / Corona**: pulsa **Agregar** en cada panel.
3. **Cueles**: elige tipo y haz click para insertar; se aplican series automáticamente.
4. **Contracuele**: click para colocar; doble click para centrar en la perforación más cercana (snap).
5. **Auxiliares**: genera rejilla interna.
6. **Exportar**: botón **Export JSON**.

## Controles

* Click: inserta según el paso actual.
* Arrastrar: mueve perforaciones (si no estás editando geometría).
* Doble click (Contracuele): snap al centro de la perforación más cercana.
* **Delete/Backspace**: borra la perforación seleccionada.
* **Snap a grilla**: activable en “Opciones”.
* El foco se fija en el canvas al hacer click.

## Edición de geometría

### Manillas de arco (D-Shaped / Horseshoe)

* **C (centro)**: ajusta la altura de paredes (y el centro del arco).
* **R (radio)**: define el ancho (2R); se mueve verticalmente manteniendo X de C.
* Se crean automáticamente al insertar D-Shaped/Horseshoe.

### Puntos libres sobre el arco

* Con el **bloqueo de inserción** activo (para no crear otra galería):

  * Click cerca del arco: inserta un nuevo punto libre.
  * Arrastra el punto para modificar la curva localmente.
* Actualmente se edita como **polilínea** (suavizado pendiente).

## Flujo recomendado

1. Insertar y editar la geometría.
2. Cuele y contracuele.
3. Zapateras, cajas, corona.
4. Auxiliares.

## Estructura del proyecto

```
practica-profesional/
├─ algoritmo-de-galerias-2.0/
│  ├─ drilling_design.py
│  ├─ drift_geometry.py
│  ├─ drift_layout.py
│  └─ blast_cuts.py
└─ README.md
```

## Modelo de datos

* Las coordenadas internas están en **metros** (el lienzo convierte a píxeles con `PX_PER_M`).
* `Scene`:

  * `drifts: list[list[tuple(x, y)]]` — galerías como polilíneas cerradas.
  * `holes: list[dict]` — perforaciones con:

    * `x, y` (m)
    * `is_void: bool` (vacía vs cargada)
    * `serie: int` (opcional; colorea por serie)
    * `_step, _kind` (etiquetas internas)

## Exportación

Crea `layout_export.json`:

```json
{
  "holes": [ { "x": 0.0, "y": 0.0 } ],
  "drifts": [ [ [x, y], [x, y] ] ]
}
```

> Nota: si tu código aún exporta `tunnels`, migra a `drifts` en `export_json()`.

## Configuración

En `drilling_design.py`:

* `PX_PER_M`: escala (px/m).
* `GRID_M`: tamaño por defecto de la grilla (m).
* `CANVAS_W`, `CANVAS_H`: tamaño del lienzo.
* `ORIGIN_X`, `ORIGIN_Y`: origen del sistema de dibujo.

En la UI:

* Mostrar grilla y ejes X/Y.
* Tamaño de grilla (m) y línea mayor cada N.

## Detalles de implementación

* D-Shaped: si `altura ≤ (ancho/2)`, se fuerza pared mínima para evitar semicircular.
* Al insertar geometría se registran límites para “cajas”:

  * `wall_top_y`: altura donde terminan paredes y comienza el arco.
  * `wall_x_left/right`: extremos horizontales de paredes.

## Problemas conocidos

* El combobox de geometría puede resetearse a “Semicircular” tras insertar.
* **Cajas**: amontonamiento en el encuentro pared/techo; se trabaja en recorte usando `wall_top_y` y límites X.
* La edición con puntos libres es poligonal; falta suavizado tipo spline/Bezier.

## Contribución

1. Crea una rama (`feat/...`, `fix/...`).
2. Sigue PEP8 y usa nombres claros (`xm`, `ym` en metros).
3. Usa Conventional Commits (`feat:`, `fix:`, `refactor:`, `docs:`).
4. Abre un PR con descripción y, si aplica, capturas.

## Licencia

Por definir.
