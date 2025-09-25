#
# APLICACIÓN GUI PARA DISEÑO DE GALERÍAS (DRIFTS),
# FAMILIAS DE GEOMETRIAS Y CUELES

import math
import tkinter as tk
from tkinter import messagebox, ttk

# CARGA DE PATRONES DE CUELES (blast_cuts)
from blast_cuts import (apply_series_abanico, apply_series_bethune,
                        apply_series_coromant, apply_series_cuatro_secciones,
                        apply_series_cuna, apply_series_sarrois,
                        apply_series_sueco, cuele_abanico_geom,
                        cuele_bethune_geom, cuele_coromant_geom,
                        cuele_cuatro_secciones_geom, cuele_cuna_geom,
                        cuele_sarrois_geom, cuele_sueco_geom)
# GEOMETRÍA DE GALERÍAS (drift_geometry)
from drift_geometry import (bezier_tunnel, d_shaped, horseshoe, rectangular,
                            semicircular)
# COLOCACIÓN DE FAMILIAS SOBRE LA GALERÍA (drift_layout)
from drift_layout import (place_aux_grid, place_cajas, place_contracuele_hex,
                          place_contracuele_rect, place_corona,
                          place_zapateras)

# CONSTANTES MUNDO ↔ PANTALLA
PX_PER_M = 160.0
GRID_M = 0.10
CANVAS_W = 1000
CANVAS_H = 700
ORIGIN_X = CANVAS_W // 2
ORIGIN_Y = CANVAS_H // 2
SNAP_TOL_M = 0.20  # tolerancia para “snap” de contracuele en doble clic
SHIFT_MASK = 0x0001  # bit de Shift en Tk (sirve para detectar Shift presionado)


def w2c(xm: float, ym: float):
    """Convierte coordenadas mundo (m) a canvas (px)."""
    return ORIGIN_X + xm * PX_PER_M, ORIGIN_Y - ym * PX_PER_M


def c2w(xp: float, yp: float):
    """Convierte coordenadas canvas (px) a mundo (m)."""
    return (xp - ORIGIN_X) / PX_PER_M, (ORIGIN_Y - yp) / PX_PER_M


# ESCENA (MODELO DE DATOS)
class Scene:
    """Contenedor de perforaciones y geometrías de galería en memoria.

    Atributos:
        holes (list[dict]): perforaciones con campos x, y, is_void, note y tags de paso/kind.
        tunnels (list[list[tuple]]): polilíneas de galería [(x,y), ...].
        selected_idx (int|None): índice de perforación seleccionada, si hay.
    """

    def __init__(self):
        self.holes = []
        self.drifts = []
        self.selected_idx = None

    def add_holes(self, hs):
        """Agrega una lista de perforaciones (dicts)."""
        self.holes.extend(hs)

    def add_drift(self, poly):
        """Agrega una polilínea de galería.

        Retorna:
            int|None: índice de la galería insertada o None si no se agregó.
        """
        if poly and len(poly) >= 2:
            self.drifts.append(poly)
            return len(self.drifts) - 1
        return None

    def remove_holes_by_step(self, step):
        """Elimina todas las perforaciones etiquetadas con el paso dado."""
        self.holes = [h for h in self.holes if h.get("_step") != step]

    def nearest(self, xm, ym, tol_m=0.15):
        """Retorna el índice de la perforación más cercana al punto (xm,ym) si está dentro de tol_m."""
        best_i, best_d = None, 1e9
        for i, h in enumerate(self.holes):
            d = math.hypot(h["x"] - xm, h["y"] - ym)
            if d < best_d and d <= tol_m:
                best_d, best_i = d, i
        return best_i


# PASOS DEL ASISTENTE
# PASOS DEL ASISTENTE (en orden)
SP_EJE = 0
SP_GEOM = 1
SP_CUELES = 2
SP_CC = 3
SP_ZAP = 4
SP_CAJAS = 5
SP_CORONA = 6
SP_AUX = 7
STEPS_MAX = SP_AUX


# APLICACIÓN
class App(tk.Tk):
    """Interfaz de usuario para el diseño paso a paso de galería + familias + cueles/contracuele."""

    def __init__(self):
        super().__init__()
        self.title("Diseño de galerías - asistente por pasos")
        self.geometry(f"{CANVAS_W+380}x{CANVAS_H+40}")

        # Estado principal

        self.scene = Scene()
        self.drift_poly = []  # polilínea de la galería ACTIVA en edición
        self.geom_index = None  # índice de la galería activa dentro de scene.drifts
        self.step = SP_EJE  # paso actual del asistente
        self.done_eje = False
        self.dragging_idx = None  # índice de perforación arrastrándose (si aplica)

        # Flags de finalización por paso

        self.done_geom = False
        self.done_zap = False
        self.done_cajas = False
        self.done_corona = False
        self.done_cueles = False
        self.done_cc = False
        self.done_aux = False

        # Grilla y ejes (antes de draw())

        self.grid_m = tk.DoubleVar(value=0.10)  # tamaño de celda en metros
        self.major_n = tk.IntVar(value=5)  # línea mayor cada N menores
        self.show_grid = tk.BooleanVar(value=True)  # mostrar grilla
        self.show_axes = tk.BooleanVar(value=False)  # mostrar ejes X/Y

        # Bloqueo de creación y edición libre del arco
        # True, evita que un click cree otra galería encima de la actual
        self.lock_geom_insert = tk.BooleanVar(value=True)

        # Edición libre del arco con puntos insertables/arrastrables
        self.edit_free = tk.BooleanVar(value=True)
        self.free_handles = []  # [{'i': idx_en_poly, 'x':..., 'y':...}, ...]
        self._drag_free_idx = None  # índice dentro de free_handles en arrastre
        self._arc_span = (
            None  # (start_idx, end_idx) tramo del arco en drift_poly (incl.)
        )
        self._arc_n = 0  # cantidad de puntos del arco (meta, opcional)

        # Estado de controles persistentes (Geometría)
        # (No se reinician al cambiar de paso)

        self.geom_type = tk.StringVar(value="Semicircular")
        self.geom_w = tk.DoubleVar(value=3.0)  # ancho total (o 2R)
        self.geom_h = tk.DoubleVar(value=3.0)  # alto (o altura de pared)
        self.geom_r = tk.DoubleVar(value=1.5)  # radio (semicircular / tope D)
        self.geom_curve = tk.DoubleVar(value=0.8)  # bombeo Bezier

        # Variables de estado paredes
        self.wall_top_y = None
        self.wall_x_left = None
        self.wall_x_right = None
        # Estado de paneo grilla
        self._panning = False  # No hay paneo hasta el click
        self._pan_start_px = 0  # coordenada de click inicial (px:pixel x)
        self._pan_start_py = 0  # coordenada de click inicial (py)
        self._pan_origin_x0 = 0  # copia del ORIGIN_x momento empieza el drag
        self._pan_origin_y0 = 0  # copia del ORIGIN_y momento empieza el drag

        # Construcción de UI y primer render
        self._build_ui()
        self._render_step_panel()
        self._update_step_label()
        self.draw()

    def _vbind(self, widget, virtual_name, handler, *sequences):
        """
        Une varias secuencias físicas a un único evento virtual y lo bindea a 'handler'.
        Ej: self._vbind(self.canvas, '<<AppAny>>', self._router, '<Button-1>', '<B1-Motion>', ...)
        """
        widget.event_add(virtual_name, *sequences)
        widget.bind(virtual_name, handler)

    def _tag(self, holes, step, kind):
        """Agrega etiquetas internas de control a un conjunto de perforaciones."""
        for h in holes:
            h["_step"] = step
            h["_kind"] = kind
        return holes

    def _build_ui(self):
        "Construye widgets estaticos de la interfaz"
        # --- HEADER con pestañas (fila 0) ---
        self.header = ttk.Frame(self)  # contenedor superior
        self.header.grid(
            row=0,
            column=0,
            columnspan=2,  # ocupa el ancho completo
            sticky="ew",
            padx=6,
            pady=(6, 0),
        )

        self.tabs = ttk.Notebook(self.header)  # contenedor de pestañas
        self.tabs.pack(fill="x")

        # Pestañas en el mismo orden que las constantes (índice == número de paso)
        tab_eje = ttk.Frame(self.tabs)
        self.tabs.add(tab_eje, text="Eje")
        tab_geom = ttk.Frame(self.tabs)
        self.tabs.add(tab_geom, text="Galería")
        tab_cuele = ttk.Frame(self.tabs)
        self.tabs.add(tab_cuele, text="Cuele")
        tab_cc = ttk.Frame(self.tabs)
        self.tabs.add(tab_cc, text="Contracuele")
        tab_zap = ttk.Frame(self.tabs)
        self.tabs.add(tab_zap, text="Zapateras")
        tab_cajas = ttk.Frame(self.tabs)
        self.tabs.add(tab_cajas, text="Cajas")
        tab_corona = ttk.Frame(self.tabs)
        self.tabs.add(tab_corona, text="Corona")
        tab_aux = ttk.Frame(self.tabs)
        self.tabs.add(tab_aux, text="Auxiliares")

        # Cuando el usuario cambia de pestaña, decidimos si puede avanzar (gating)
        self.tabs.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # canvas
        self.canvas = tk.Canvas(self, width=CANVAS_W, height=CANVAS_H, bg="white")
        self.canvas.grid(row=1, column=0, padx=6, pady=6, sticky="nsew")

        # ⬇️ Configuración de la grilla del contenedor raíz (self):
        # Columna 0 (canvas) crece, columna 1 (lateral) fija.
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)  # opcional; por defecto es 0

        # Binds compactos: un solo virtual para todo el canvas, manejado por _router#
        # --- Interacción normal con botón izquierdo ---
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)

        # --- Paneo (botón central o Shift+izquierdo) con 3 virtuales compactos ---
        self.canvas.event_add("<<PanStart>>", "<Button-2>", "<Shift-Button-1>")
        self.canvas.event_add("<<PanMove>>", "<B2-Motion>", "<Shift-B1-Motion>")
        self.canvas.event_add(
            "<<PanEnd>>", "<ButtonRelease-2>", "<Shift-ButtonRelease-1>"
        )

        # Cada virtual llama a _pan con su etapa (sin depender de event.type)
        self.canvas.bind("<<PanStart>>", lambda e: self._pan(e, "start"))
        self.canvas.bind("<<PanMove>>", lambda e: self._pan(e, "move"))
        self.canvas.bind("<<PanEnd>>", lambda e: self._pan(e, "end"))

        # --- Delete/BackSpace en una sola línea virtual (ya lo tenías así) ---
        self._vbind(
            self, "<<DelKey>>", self._delete_selected, "<Delete>", "<BackSpace>"
        )

        # lateral
        self.side = ttk.Frame(self)
        self.side.grid(row=1, column=1, sticky="ns", padx=6, pady=6)

        # Fila 0 (header) fija; fila 1 (canvas + lateral) crece.
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        # cabecera
        hdr = ttk.Frame(self.side)
        hdr.pack(fill="x")
        self.step_label = ttk.Label(hdr, text="")
        self.step_label.pack(anchor="w")

        # panel de paso
        self.step_frame = ttk.Frame(self.side)
        self.step_frame.pack(fill="x", pady=(6, 4))

        # opciones generales
        opts = ttk.LabelFrame(self.side, text="Opciones")
        opts.pack(fill="x", pady=6)
        self.show_labels = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            opts, text="Mostrar series", variable=self.show_labels, command=self.draw
        ).pack(anchor="w")
        self.snap_grid = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="Ajustar a grilla", variable=self.snap_grid).pack(
            anchor="w"
        )

        #  controles de grilla/ejes
        ttk.Checkbutton(
            opts, text="Mostrar grilla", variable=self.show_grid, command=self.draw
        ).pack(anchor="w")
        ttk.Checkbutton(
            opts, text="Mostrar ejes X/Y", variable=self.show_axes, command=self.draw
        ).pack(anchor="w")
        ttk.Checkbutton(
            opts,
            text="Bloquear creación (evitar nueva galería por click)",
            variable=self.lock_geom_insert,
        ).pack(anchor="w")

        row_opts = ttk.Frame(opts)
        row_opts.pack(fill="x", pady=(4, 0))
        ttk.Label(row_opts, text="Grilla (m):").pack(side="left")
        e_grid = ttk.Entry(row_opts, textvariable=self.grid_m, width=6)
        e_grid.pack(side="left", padx=(4, 8))
        ttk.Label(row_opts, text="Mayor cada:").pack(side="left")
        sp_major = ttk.Spinbox(
            row_opts,
            from_=2,
            to=20,
            textvariable=self.major_n,
            width=4,
            command=self.draw,
        )
        sp_major.pack(side="left")

        # trazas para redibujar al cambiar parámetros de grilla
        def _on_grid_change(*_):
            try:
                float(self.grid_m.get())
            except Exception:
                return
            self.draw()

        self.grid_m.trace_add("write", _on_grid_change)
        self.major_n.trace_add("write", lambda *_: self.draw())

        ttk.Label(
            self.side, text="Arrastra perforaciones para ajustarlas manualmente."
        ).pack(anchor="w", pady=(2, 8))

        # navegación
        foot = ttk.Frame(self.side)
        foot.pack(fill="x", pady=(6, 0))
        self.btn_prev = ttk.Button(foot, text="Anterior", command=self.prev_step)
        self.btn_prev.pack(side="left")
        self.btn_next = ttk.Button(foot, text="Siguiente", command=self.next_step)
        self.btn_next.pack(side="right")

        # utilidades
        util = ttk.Frame(self.side)
        util.pack(fill="x", pady=6)
        ttk.Button(util, text="Borrar todo", command=self.clear_all).pack(side="left")
        ttk.Button(util, text="Export JSON", command=self.export_json).pack(
            side="right"
        )

    def _can_go_to(self, step_target: int) -> bool:
        """
        Regla de gating: no se puede saltar al siguiente paso si el anterior no está ✓.
        Permite volver hacia atrás siempre.
        """
        if step_target <= self.step:
            return True
        req = {
            SP_GEOM: self.done_eje,  # Para ir a Geometría, primero completa Eje
            SP_CUELES: self.done_geom,  # Para ir a Cueles, primero completa Geometría
            SP_CC: self.done_cueles,  # Para ir a Contracuele, primero Cueles
            SP_ZAP: self.done_cc,  # Para ir a Zapateras, primero Contracuele
            SP_CAJAS: self.done_zap,  # Para ir a Cajas, primero Zapateras
            SP_CORONA: self.done_cajas,  # Para ir a Corona, primero Cajas
            SP_AUX: self.done_corona,  # Para ir a Auxiliares, primero Corona
        }
        return req.get(step_target, True)

    def _sync_tabs(self):
        """
        Selecciona la pestaña que corresponde al paso actual (self.step).
        Como añadimos las tabs en orden, el índice coincide con self.step.
        """
        try:
            self.tabs.select(self.step)
        except Exception:
            pass

    def _on_tab_changed(self, ev):
        """
        Handler cuando el usuario hace click en otra pestaña.
        Valida con _can_go_to(); si no puede, vuelve a la pestaña actual y avisa.
        """
        idx = self.tabs.index(self.tabs.select())
        if not self._can_go_to(idx):
            self._sync_tabs()
            messagebox.showinfo(
                "Paso bloqueado", "Completa el paso anterior antes de continuar."
            )
            return
        self.step = idx
        self._render_step_panel()
        self._update_step_label()
        self.draw()

    def _center_origin(self):
        """Centra el origen en el canvas y marca el paso Eje como completo."""
        globals()["ORIGIN_X"] = CANVAS_W // 2
        globals()["ORIGIN_Y"] = CANVAS_H // 2
        self.done_eje = True
        self.draw()
        self._sync_tabs()

    def _render_step_panel(self):
        """Reconstruye el panel lateral del paso actual con sus controles."""
        for w in self.step_frame.winfo_children():
            w.destroy()

        self.btn_prev.configure(state="normal" if self.step > SP_EJE else "disabled")
        self.btn_next.configure(state="disabled")

        if self.step == SP_EJE:
            frm = ttk.LabelFrame(self.step_frame, text="Eje y vista")
            frm.pack(fill="x")
            ttk.Label(
                frm,
                text="• Click en el canvas fija el origen (0,0).\n• Paneo: botón medio o Shift+arrastre.\n• También puedes centrar el origen.",
            ).pack(anchor="w", pady=(2, 6))
            ttk.Button(
                frm, text="Centrar en el canvas", command=self._center_origin
            ).pack(anchor="w")
            ttk.Button(
                self.step_frame,
                text="Borrar este paso",
                command=lambda: self._clear_step(SP_EJE),
            ).pack(anchor="w", pady=(6, 0))
            # Habilita “Siguiente” cuando el eje esté fijado o centrado
            self.btn_next.configure(state="normal" if self.done_eje else "disabled")

        elif self.step == SP_GEOM:
            frm = ttk.LabelFrame(self.step_frame, text="Geometría de galería")
            frm.pack(fill="x")

            ttk.Label(frm, text="Tipo").grid(row=0, column=0, sticky="w")
            ttk.Combobox(
                frm,
                textvariable=self.geom_type,
                values=[
                    "Semicircular",
                    "D-shaped",
                    "Rectangular",
                    "Horseshoe",
                    "Bezier",
                ],
                state="readonly",
                width=18,
            ).grid(row=0, column=1, sticky="e")

            row = 1
            for label, var in [
                ("Ancho / 2R", self.geom_w),
                ("Alto", self.geom_h),
                ("Radio", self.geom_r),
                ("Curva (Bezier)", self.geom_curve),
            ]:
                ttk.Label(frm, text=label).grid(row=row, column=0, sticky="w")
                ttk.Entry(frm, textvariable=var, width=10).grid(
                    row=row, column=1, sticky="e"
                )
                row += 1

            ttk.Label(
                self.step_frame,
                text="Haz CLICK en el canvas para ubicar el centro de la galería.",
            ).pack(anchor="w", pady=(6, 6))
            ttk.Button(
                self.step_frame,
                text="Borrar este paso",
                command=lambda: self._clear_step(SP_GEOM),
            ).pack(anchor="w")

            if self.drift_poly:
                self.done_geom = True
            self.btn_next.configure(state="normal" if self.done_geom else "disabled")

        elif self.step == SP_ZAP:
            frm = ttk.LabelFrame(self.step_frame, text="Zapateras (base)")
            frm.pack(fill="x")
            self.n_zap = tk.IntVar(value=6)
            ttk.Label(frm, text="Nº de perforaciones").grid(row=0, column=0, sticky="w")
            ttk.Entry(frm, textvariable=self.n_zap, width=10).grid(
                row=0, column=1, sticky="e"
            )

            bar = ttk.Frame(self.step_frame)
            bar.pack(fill="x", pady=(6, 0))
            ttk.Button(bar, text="Agregar", command=self._do_zap).pack(side="left")
            ttk.Button(
                bar, text="Borrar este paso", command=lambda: self._clear_step(SP_ZAP)
            ).pack(side="left", padx=6)

            ttk.Label(
                self.step_frame, text="Se distribuirán equidistantes sobre la base."
            ).pack(anchor="w", pady=(6, 0))
            self.btn_next.configure(state="normal" if self.done_zap else "disabled")

        elif self.step == SP_CAJAS:
            frm = ttk.LabelFrame(self.step_frame, text="Cajas (paredes)")
            frm.pack(fill="x")
            self.n_caja = tk.IntVar(value=5)
            ttk.Label(frm, text="Cajas por lado").grid(row=0, column=0, sticky="w")
            ttk.Entry(frm, textvariable=self.n_caja, width=10).grid(
                row=0, column=1, sticky="e"
            )

            bar = ttk.Frame(self.step_frame)
            bar.pack(fill="x", pady=(6, 0))
            ttk.Button(bar, text="Agregar", command=self._do_cajas).pack(side="left")
            ttk.Button(
                bar, text="Borrar este paso", command=lambda: self._clear_step(SP_CAJAS)
            ).pack(side="left", padx=6)

            ttk.Label(
                self.step_frame,
                text="Se colocan en ambos lados (mismo número por lado).",
            ).pack(anchor="w", pady=(6, 0))
            self.btn_next.configure(state="normal" if self.done_cajas else "disabled")

        elif self.step == SP_CORONA:
            frm = ttk.LabelFrame(self.step_frame, text="Corona (techo)")
            frm.pack(fill="x")
            self.n_corona = tk.IntVar(value=8)
            ttk.Label(frm, text="Nº de perforaciones").grid(row=0, column=0, sticky="w")
            ttk.Entry(frm, textvariable=self.n_corona, width=10).grid(
                row=0, column=1, sticky="e"
            )

            bar = ttk.Frame(self.step_frame)
            bar.pack(fill="x", pady=(6, 0))
            ttk.Button(bar, text="Agregar", command=self._do_corona).pack(side="left")
            ttk.Button(
                bar,
                text="Borrar este paso",
                command=lambda: self._clear_step(SP_CORONA),
            ).pack(side="left", padx=6)

            ttk.Label(
                self.step_frame, text="Se distribuirán equidistantes en el techo."
            ).pack(anchor="w", pady=(6, 0))
            self.btn_next.configure(state="normal" if self.done_corona else "disabled")

        elif self.step == SP_CUELES:
            frm = ttk.LabelFrame(self.step_frame, text="Cueles")
            frm.pack(fill="x")

            ttk.Label(frm, text="Tipo").grid(row=0, column=0, sticky="w")
            self.cuele_type = tk.StringVar(value="Sarrois")
            ttk.Combobox(
                frm,
                textvariable=self.cuele_type,
                values=[
                    "Sarrois",
                    "Sueco",
                    "Coromant",
                    "Cuña 2x3",
                    "Cuña zigzag",
                    "Abanico",
                    "Bethune",
                    "Cuatro secciones",
                ],
                state="readonly",
                width=18,
            ).grid(row=0, column=1, sticky="e")

            self.d_var = tk.DoubleVar(value=0.15)
            self.rot = tk.DoubleVar(value=0.0)
            self.sx = tk.DoubleVar(value=1.0)
            self.sy = tk.DoubleVar(value=1.0)
            self.vy = tk.DoubleVar(value=3.5)

            row = 1
            for label, var in [
                ("d (m)", self.d_var),
                ("rot (°)", self.rot),
                ("scale X", self.sx),
                ("scale Y", self.sy),
                ("Bethune vy", self.vy),
            ]:
                ttk.Label(frm, text=label).grid(row=row, column=0, sticky="w")
                ttk.Entry(frm, textvariable=var, width=10).grid(
                    row=row, column=1, sticky="e"
                )
                row += 1

            ttk.Label(
                self.step_frame, text="Haz CLICK en el canvas para insertar un cuele."
            ).pack(anchor="w", pady=(6, 6))
            ttk.Button(
                self.step_frame,
                text="Borrar este paso",
                command=lambda: self._clear_step(SP_CUELES),
            ).pack(anchor="w")
            self.btn_next.configure(state="normal" if self.done_cueles else "disabled")

        elif self.step == SP_CC:
            frm = ttk.LabelFrame(self.step_frame, text="Contracuele")
            frm.pack(fill="x")

            ttk.Label(frm, text="Figura").grid(row=0, column=0, sticky="w")
            self.cc_type = tk.StringVar(value="Hexágono")
            ttk.Combobox(
                frm,
                textvariable=self.cc_type,
                values=["Hexágono", "Rectángulo"],
                state="readonly",
                width=18,
            ).grid(row=0, column=1, sticky="e")

            self.cc_hex_r = tk.DoubleVar(value=0.8)
            self.cc_rect_w = tk.DoubleVar(value=1.6)
            self.cc_rect_h = tk.DoubleVar(value=1.1)
            self.cc_rect_n = tk.IntVar(value=2)

            row = 1
            ttk.Label(frm, text="Hex r").grid(row=row, column=0, sticky="w")
            ttk.Entry(frm, textvariable=self.cc_hex_r, width=10).grid(
                row=row, column=1, sticky="e"
            )
            row += 1
            ttk.Label(frm, text="Rect w").grid(row=row, column=0, sticky="w")
            ttk.Entry(frm, textvariable=self.cc_rect_w, width=10).grid(
                row=row, column=1, sticky="e"
            )
            row += 1
            ttk.Label(frm, text="Rect h").grid(row=row, column=0, sticky="w")
            ttk.Entry(frm, textvariable=self.cc_rect_h, width=10).grid(
                row=row, column=1, sticky="e"
            )
            row += 1
            ttk.Label(frm, text="Rect n/lado").grid(row=row, column=0, sticky="w")
            ttk.Entry(frm, textvariable=self.cc_rect_n, width=10).grid(
                row=row, column=1, sticky="e"
            )
            row += 1

            ttk.Label(
                self.step_frame,
                text="CLICK: coloca libre.  DOBLE CLICK: usa centro de perforación más cercana.",
            ).pack(anchor="w", pady=(6, 6))
            ttk.Button(
                self.step_frame,
                text="Borrar este paso",
                command=lambda: self._clear_step(SP_CC),
            ).pack(anchor="w")
            self.btn_next.configure(state="normal" if self.done_cc else "disabled")

        elif self.step == SP_AUX:
            frm = ttk.LabelFrame(
                self.step_frame, text="Perforaciones auxiliares (grilla interna)"
            )
            frm.pack(fill="x")
            self.aux_nx = tk.IntVar(value=5)
            self.aux_ny = tk.IntVar(value=3)
            ttk.Label(frm, text="nx").grid(row=0, column=0, sticky="w")
            ttk.Entry(frm, textvariable=self.aux_nx, width=10).grid(
                row=0, column=1, sticky="e"
            )
            ttk.Label(frm, text="ny").grid(row=1, column=0, sticky="w")
            ttk.Entry(frm, textvariable=self.aux_ny, width=10).grid(
                row=1, column=1, sticky="e"
            )

            bar = ttk.Frame(self.step_frame)
            bar.pack(fill="x", pady=(6, 0))
            ttk.Button(bar, text="Agregar", command=self._do_aux).pack(side="left")
            ttk.Button(
                bar, text="Borrar este paso", command=lambda: self._clear_step(SP_AUX)
            ).pack(side="left", padx=6)

            ttk.Label(
                self.step_frame,
                text="Se distribuyen equidistantes dentro de la galería.",
            ).pack(anchor="w", pady=(6, 0))
            self.btn_next.configure(state="normal" if self.done_aux else "disabled")

    def _update_step_label(self):
        """Actualiza el rótulo del paso actual."""
        names = {
            SP_EJE: "Paso 1/8: Eje",
            SP_GEOM: "Paso 2/8: Geometría",
            SP_CUELES: "Paso 3/8: Cueles",
            SP_CC: "Paso 4/8: Contracuele",
            SP_ZAP: "Paso 5/8: Zapateras",
            SP_CAJAS: "Paso 6/8: Cajas",
            SP_CORONA: "Paso 7/8: Corona",
            SP_AUX: "Paso 8/8: Auxiliares",
        }
        self.step_label.config(text=names[self.step])

    def prev_step(self):
        """Retrocede un paso y sincroniza las pestañas."""
        if self.step > SP_EJE:
            self.step -= 1
            self._render_step_panel()
            self._update_step_label()
            self._sync_tabs()

    def next_step(self):
        """Avanza al siguiente paso, respetando el gating (no saltarse pasos)."""
        if self.step == SP_EJE and not self.done_eje:
            return messagebox.showwarning(
                "Eje", "Fija el origen con un click o pulsa 'Centrar'."
            )
        elif self.step == SP_GEOM and not self.done_geom:
            return messagebox.showwarning(
                "Geometría", "Coloca la geometría con un click en el canvas."
            )
        elif self.step == SP_CUELES and not self.done_cueles:
            return messagebox.showwarning("Cueles", "Inserta al menos un cuele.")
        elif self.step == SP_CC and not self.done_cc:
            return messagebox.showwarning(
                "Contracuele", "Inserta el contracuele (click o doble click)."
            )
        elif self.step == SP_ZAP and not self.done_zap:
            return messagebox.showwarning(
                "Zapateras", "Pulsa 'Agregar' para colocar las zapateras."
            )
        elif self.step == SP_CAJAS and not self.done_cajas:
            return messagebox.showwarning(
                "Cajas", "Pulsa 'Agregar' para colocar las cajas."
            )
        elif self.step == SP_CORONA and not self.done_corona:
            return messagebox.showwarning(
                "Corona", "Pulsa 'Agregar' para colocar la corona."
            )

        if self.step < STEPS_MAX:
            self.step += 1
            self._render_step_panel()
            self._update_step_label()
            self._sync_tabs()

    def draw(self):
        """Redibuja todo: grilla, drifts, perforaciones, límite de pared y overlays de edición."""
        self.canvas.delete("all")

        # Fondo: grilla y ejes
        self._draw_grid()

        # Contorno de galerías
        self._draw_drifts()

        # Perforaciones
        self._draw_holes()

        # --- Límite de pared (si existe) ---
        # Línea punteada horizontal desde x_left a x_right a la altura wall_top_y
        if (
            getattr(self, "wall_top_y", None) is not None
            and getattr(self, "wall_x_left", None) is not None
            and getattr(self, "wall_x_right", None) is not None
        ):
            x1, y1 = w2c(self.wall_x_left, self.wall_top_y)
            x2, y2 = w2c(self.wall_x_right, self.wall_top_y)
            self.canvas.create_line(x1, y1, x2, y2, dash=(4, 3), fill="#999")

    def _draw_grid(self):
        """Dibuja una grilla con líneas menores/mayores y ejes opcionales."""
        # Nada que dibujar
        if not self.show_grid.get() and not self.show_axes.get():
            return

        # Parámetros
        try:
            gm = max(0.01, float(self.grid_m.get()))  # metros por celda
        except Exception:
            gm = GRID_M

        try:
            major_every = max(2, int(self.major_n.get()))
        except Exception:
            major_every = 5

        step = gm * PX_PER_M  # píxeles por celda
        W, H = CANVAS_W, CANVAS_H

        def crisp(v):  # líneas nítidas
            return int(v) + 0.5

        if self.show_grid.get():
            # Verticales: origen y hacia la derecha
            k, x = 0, ORIGIN_X
            while x <= W:
                is_major = k % major_every == 0
                self.canvas.create_line(
                    crisp(x),
                    0,
                    crisp(x),
                    H,
                    fill="#b0b0b0" if is_major else "#cfcfcf",
                    width=1.5 if is_major else 1,
                )
                k += 1
                x = ORIGIN_X + k * step
            # Verticales: hacia la izquierda
            k, x = 1, ORIGIN_X - step
            while x >= 0:
                is_major = k % major_every == 0
                self.canvas.create_line(
                    crisp(x),
                    0,
                    crisp(x),
                    H,
                    fill="#b0b0b0" if is_major else "#cfcfcf",
                    width=1.5 if is_major else 1,
                )
                k += 1
                x = ORIGIN_X - k * step

            # Horizontales: origen y hacia abajo
            k, y = 0, ORIGIN_Y
            while y <= H:
                is_major = k % major_every == 0
                self.canvas.create_line(
                    0,
                    crisp(y),
                    W,
                    crisp(y),
                    fill="#b0b0b0" if is_major else "#cfcfcf",
                    width=1.5 if is_major else 1,
                )
                k += 1
                y = ORIGIN_Y + k * step
            # Horizontales: hacia arriba
            k, y = 1, ORIGIN_Y - step
            while y >= 0:
                is_major = k % major_every == 0
                self.canvas.create_line(
                    0,
                    crisp(y),
                    W,
                    crisp(y),
                    fill="#b0b0b0" if is_major else "#cfcfcf",
                    width=1.5 if is_major else 1,
                )
                k += 1
                y = ORIGIN_Y - k * step

        # Ejes X/Y opcionales
        if self.show_axes.get():
            self.canvas.create_line(
                0, crisp(ORIGIN_Y), W, crisp(ORIGIN_Y), fill="#666", width=2
            )
            self.canvas.create_line(
                crisp(ORIGIN_X), 0, crisp(ORIGIN_X), H, fill="#666", width=2
            )

    def _draw_drifts(self):
        """Dibuja todas las polilíneas de drift (galería)."""
        polys = list(self.scene.drifts)
        if self.drift_poly:
            polys.append(self.drift_poly)
        for poly in polys:
            if not poly or len(poly) < 2:
                continue
            pts = []
            for x, y in poly:
                xp, yp = w2c(x, y)
                pts.extend([xp, yp])
            self.canvas.create_line(*pts, fill="#888", width=2)

    def _draw_holes(self):
        """Dibuja perforaciones; si hay 'serie' usa paleta por serie."""
        r_px = 5
        palette = ["#2ca02c", "#ff7f0e", "#d62728", "#9467bd", "#8c564b", "#e377c2"]
        for i, h in enumerate(self.scene.holes):
            xp, yp = w2c(h["x"], h["y"])
            if "serie" in h:
                color = (
                    "black"
                    if h.get("is_void", False)
                    else palette[h["serie"] % len(palette)]
                )
            else:
                color = "black" if h.get("is_void", False) else "#1f77b4"
            self.canvas.create_oval(
                xp - r_px, yp - r_px, xp + r_px, yp + r_px, fill=color, outline=""
            )
            if self.show_labels.get() and "serie" in h:
                self.canvas.create_text(
                    xp, yp - 10, text=str(h["serie"]), fill="#444", font=("Arial", 9)
                )
            if i == self.scene.selected_idx:
                self.canvas.create_oval(xp - 9, yp - 9, xp + 9, yp + 9, outline="#444")

    def on_click(self, ev):
        """
        Click izquierdo:
        1) Si NO estás en modo de inserción (cueles/cc), permite seleccionar/arrastrar perforaciones.
        2) Si estás en Paso GEOM y no está bloqueado, crea la geometría.
        3) En otros pasos: inserta cueles / contracuele según corresponda.
        """

        if ev.state & SHIFT_MASK:
            return  # esto es paneo, no insertar/seleccionar

        self.canvas.focus_set()

        # Coords a metros (+ snap)
        xm, ym = c2w(ev.x, ev.y)
        if self.snap_grid.get():
            gm = max(0.01, float(self.grid_m.get()))
            xm = round(xm / gm) * gm
            ym = round(ym / gm) * gm

        # Selección/arrastre de perforación (si no estamos en pasos que usan click para insertar)
        idx = self.scene.nearest(xm, ym)
        if idx is not None and self.step not in (SP_EJE, SP_CUELES, SP_CC):
            self.scene.selected_idx = idx
            self.dragging_idx = idx
            self.draw()
            return

        # Bloqueo: si ya hay una galería y el candado está activo, no insertes otra
        if (
            self.step == SP_GEOM
            and self.lock_geom_insert.get()
            and (self.drift_poly or self.scene.drifts)
        ):
            return

        # Inserción según paso
        if self.step == SP_GEOM:
            gtype = self.geom_type.get()

            if gtype == "Semicircular":
                R = float(self.geom_r.get())
                self.drift_poly = semicircular(xm, ym, radius=R, n_points=48)
                self.wall_top_y = self.wall_x_left = self.wall_x_right = None

            elif gtype == "Rectangular":
                w = float(self.geom_w.get())
                h = float(self.geom_h.get())
                self.drift_poly = rectangular(xm, ym, width=w, height=h)
                self.wall_top_y = ym + h
                self.wall_x_left = xm - w * 0.5
                self.wall_x_right = xm + w * 0.5

            elif gtype == "D-shaped":
                w = float(self.geom_w.get())
                h = float(self.geom_h.get())
                r = max(0.05, w * 0.5)
                if h <= r:  # evita semicircular disfrazado
                    h = r + 0.1
                self.drift_poly = d_shaped(xm, ym, width=w, height=h, n_points=48)
                self.wall_top_y = ym + (h - r)  # altura de pared recta
                self.wall_x_left = xm - r
                self.wall_x_right = xm + r

            elif gtype == "Horseshoe":
                w = float(self.geom_w.get())
                wall = max(0.05, float(self.geom_h.get()))
                self.drift_poly = horseshoe(xm, ym, width=w, height=wall, n_curve=24)
                self.wall_top_y = ym + wall
                self.wall_x_left = xm - w * 0.5
                self.wall_x_right = xm + w * 0.5

            elif gtype == "Bezier":
                w = float(self.geom_w.get())
                wall = float(self.geom_h.get())
                ch = float(self.geom_curve.get())
                self.drift_poly = bezier_tunnel(
                    xm, ym, width=w, wall_height=wall, curve_height=ch, n_points=48
                )
                self.wall_top_y = ym + wall
                self.wall_x_left = xm - w * 0.5
                self.wall_x_right = xm + w * 0.5

            else:
                self.drift_poly = []
                self.wall_top_y = self.wall_x_left = self.wall_x_right = None

            self.geom_index = self.scene.add_drift(self.drift_poly)
            self.done_geom = bool(self.drift_poly)
            self.draw()
            self._render_step_panel()
            return

        if self.step == SP_CUELES:
            holes = self._insert_cuele_at(xm, ym)
            if holes:
                self.scene.add_holes(self._tag(holes, SP_CUELES, "cuele"))
                self.done_cueles = True
                self.draw()
                self._render_step_panel()
            return

        if self.step == SP_CC:
            cct = self.cc_type.get()
            if cct == "Hexágono":
                r = float(self.cc_hex_r.get())
                holes = place_contracuele_hex((xm, ym), r=r)
            else:
                w = float(self.cc_rect_w.get())
                h = float(self.cc_rect_h.get())
                m = int(self.cc_rect_n.get())
                holes = place_contracuele_rect((xm, ym), w=w, h=h, n_per_side=m)
            self.scene.add_holes(self._tag(holes, SP_CC, "contracuele"))
            self.done_cc = True
            self.draw()
            self._render_step_panel()
            return

        # Paso EJE: click fija el origen
        if self.step == SP_EJE:
            globals()["ORIGIN_X"] = ev.x
            globals()["ORIGIN_Y"] = ev.y
            self.done_eje = True
            self.draw()
            self._render_step_panel()
            self._sync_tabs()
            return

    def on_double_click(self, ev):
        """Doble clic en Contracuele: snapea al centro de la perforación más cercana."""
        if self.step != SP_CC:
            return
        xm, ym = c2w(ev.x, ev.y)
        idx = self.scene.nearest(xm, ym, tol_m=SNAP_TOL_M)
        if idx is None:
            return
        xm = self.scene.holes[idx]["x"]
        ym = self.scene.holes[idx]["y"]

        cct = self.cc_type.get()
        if cct == "Hexágono":
            r = float(self.cc_hex_r.get())
            holes = place_contracuele_hex((xm, ym), r=r)
        else:
            w = float(self.cc_rect_w.get())
            h = float(self.cc_rect_h.get())
            m = int(self.cc_rect_n.get())
            holes = place_contracuele_rect((xm, ym), w=w, h=h, n_per_side=m)

        self.scene.add_holes(self._tag(holes, SP_CC, "contracuele"))
        self.done_cc = True
        self.draw()
        self._render_step_panel()

    def _pan(self, ev, stage: str):
        if stage == "start":
            self._panning = True
            self._pan_start_px, self._pan_start_py = ev.x, ev.y
            self._pan_origin_x0, self._pan_origin_y0 = ORIGIN_X, ORIGIN_Y
            return

        if stage == "move" and self._panning:
            dx = ev.x - self._pan_start_px
            dy = ev.y - self._pan_start_py
            # Actualizamos el origen global para que w2c/c2w reflejen el desplazamiento
            globals()["ORIGIN_X"] = self._pan_origin_x0 + dx
            globals()["ORIGIN_Y"] = self._pan_origin_y0 + dy
            self.draw()
            return

        if stage == "end":
            self._panning = False
            return

    def on_drag(self, ev):
        """Arrastra la perforación seleccionada si corresponde."""
        if self.dragging_idx is None:
            return
        xm, ym = c2w(ev.x, ev.y)
        if self.snap_grid.get():
            gm = max(0.01, float(self.grid_m.get()))
            xm = round(xm / gm) * gm
            ym = round(ym / gm) * gm
        self.scene.holes[self.dragging_idx]["x"] = xm
        self.scene.holes[self.dragging_idx]["y"] = ym
        self.draw()

    def on_release(self, ev):
        """Termina cualquier arrastre activo (perforación, manilla de arco o punto libre)."""
        self.dragging_idx = None  # ya no arrastra perforación

    def _delete_selected(self, ev=None):
        """Elimina la perforación seleccionada."""
        i = self.scene.selected_idx
        if i is not None and 0 <= i < len(self.scene.holes):
            del self.scene.holes[i]
            self.scene.selected_idx = None
            self.draw()

    def _insert_cuele_at(self, xm, ym):
        """Genera y retorna la lista de perforaciones de un cuele en torno al punto (xm,ym)."""
        name = self.cuele_type.get()
        d = float(self.d_var.get())
        sx = float(self.sx.get())
        sy = float(self.sy.get())
        rot = float(self.rot.get())
        vy = float(self.vy.get())

        if name == "Sarrois":
            holes = cuele_sarrois_geom(
                center=(xm, ym), d=d, scale_x=sx, scale_y=sy, rot_deg=rot
            )
            apply_series_sarrois(holes, d=d)
        elif name == "Sueco":
            holes = cuele_sueco_geom(
                center=(xm, ym), d=d, scale_x=sx, scale_y=sy, rot_deg=rot
            )
            apply_series_sueco(holes, d=d)
        elif name == "Coromant":
            v = 0.5 * d
            ax = 1.2 * d
            ay = 1.2 * d
            holes = cuele_coromant_geom(
                center=(xm, ym),
                v=v,
                ax=ax,
                ay=ay,
                skew=0.4 * d,
                spread=1.4,
                scale_x=sx,
                scale_y=sy,
                rot_deg=rot,
            )
            apply_series_coromant(holes, v=v, ax=ax, ay=ay, skew=0.4 * d)
        elif name == "Cuña 2x3":
            holes = cuele_cuna_geom(
                center=(xm, ym),
                d=d,
                variante="2x3",
                sep_cols_factor=2.0,
                scale_x=sx,
                scale_y=sy,
                rot_deg=rot,
            )
            apply_series_cuna(holes, variante="2x3", d=d)
        elif name == "Cuña zigzag":
            holes = cuele_cuna_geom(
                center=(xm, ym),
                d=d,
                variante="zigzag",
                scale_x=sx,
                scale_y=sy,
                rot_deg=rot,
            )
            apply_series_cuna(holes, variante="zigzag", d=d)
        elif name == "Abanico":
            holes = cuele_abanico_geom(
                center=(xm, ym), d=d, dx_factor=0.5, scale_x=sx, scale_y=sy, rot_deg=rot
            )
            apply_series_abanico(holes, d=d)
        elif name == "Bethune":
            holes = cuele_bethune_geom(
                center=(xm, ym),
                d=d,
                dx_factor=1.2,
                y_levels=(1.6, 1.4, 1.2, 1.0, 0.9),
                invert_y=True,
                vy_factor=vy,
                scale_x=sx,
                scale_y=sy,
                rot_deg=rot,
            )
            apply_series_bethune(
                holes,
                d=d,
                y_levels=(1.6, 1.4, 1.2, 1.0, 0.9),
                invert_y=True,
                vy_factor=vy,
            )
        elif name == "Cuatro secciones":
            holes = cuele_cuatro_secciones_geom(
                center=(xm, ym),
                D=d,
                D2=d,
                k2=1.5,
                k3=1.5,
                k4=1.5,
                add_mids_S4=True,
                scale_x=sx,
                scale_y=sy,
                rot_deg=rot,
            )
            B1 = 1.5 * d
            B2 = 1.5 * B1
            B3 = 1.5 * B2
            B4 = 1.5 * B3
            A1 = B1
            A2 = B1 + B2
            A3 = B1 + B2 + B3
            A4 = B1 + B2 + B3 + B4
            apply_series_cuatro_secciones(holes, A1, A2, A3, A4, add_mids_S4=True)
        else:
            holes = []

        return holes

    def _do_zap(self):
        """Calcula y agrega perforaciones de zapateras sobre la base."""
        if not self.drift_poly:
            messagebox.showwarning(
                "Geometría", "Primero inserta la geometría (Paso 1)."
            )
            return
        n = int(self.n_zap.get())
        holes = place_zapateras(self.drift_poly, n)
        self.scene.add_holes(self._tag(holes, SP_ZAP, "zapatera"))
        self.done_zap = True
        self.draw()
        self.btn_next.configure(state="normal")

    def _do_cajas(self):
        """Coloca 'cajas' SOLO sobre paredes (sin techo), usando el límite de pared."""
        if not self.drift_poly:
            messagebox.showwarning(
                "Geometría", "Primero inserta la geometría (Paso 1)."
            )
            return

        n = int(self.n_caja.get())
        holes = place_cajas(
            self.drift_poly,
            n,
            wall_top_y=self.wall_top_y,
            wall_x_left=self.wall_x_left,
            wall_x_right=self.wall_x_right,
            top_clear_m=0.1,
            bottom_clear_m=0.05,
        )
        if not holes:
            messagebox.showinfo(
                "Cajas",
                "Esta geometría no tiene paredes verticales (p. ej., Semicircular).",
            )
            return

        self.scene.add_holes(self._tag(holes, SP_CAJAS, "caja"))
        self.done_cajas = True
        self.draw()
        self.btn_next.configure(state="normal")

    def _do_corona(self):
        """Calcula y agrega perforaciones de corona en el arco superior."""
        if not self.drift_poly:
            messagebox.showwarning(
                "Geometría", "Primero inserta la geometría (Paso 1)."
            )
            return
        n = int(self.n_corona.get())
        holes = place_corona(self.drift_poly, n)
        self.scene.add_holes(self._tag(holes, SP_CORONA, "corona"))
        self.done_corona = True
        self.draw()
        self.btn_next.configure(state="normal")

    def _do_aux(self):
        """Calcula y agrega perforaciones auxiliares como rejilla interna."""
        if not self.drift_poly:
            messagebox.showwarning(
                "Geometría", "Primero inserta la geometría (Paso 1)."
            )
            return
        nx = int(self.aux_nx.get())
        ny = int(self.aux_ny.get())
        holes = place_aux_grid(self.drift_poly, nx, ny)
        self.scene.add_holes(self._tag(holes, SP_AUX, "aux"))
        self.done_aux = True
        self.draw()
        self.btn_next.configure(state="normal")

    def _clear_step(self, step_to_clear):
        """Borra el contenido de un paso y actualiza banderas y UI."""
        # 0) EJE: sólo marcar incompleto y volver a la pestaña Eje
        if step_to_clear == SP_EJE:
            # Volver a centrar el origen y apagar paneo
            globals()["ORIGIN_X"] = CANVAS_W // 2
            globals()["ORIGIN_Y"] = CANVAS_H // 2
            self._panning = False

            # Marcar el paso como no completado y volver a la pestaña
            self.done_eje = False
            self.step = SP_EJE
            self.draw()
            self._render_step_panel()
            self._update_step_label()
            self._sync_tabs()
            return

        # 1) GEOMETRÍA: resetea todo lo dependiente y vuelve a Geometría
        if step_to_clear == SP_GEOM:
            self.scene = Scene()
            self.drift_poly = []
            self.geom_index = None
            self.wall_top_y = None
            self.wall_x_left = None
            self.wall_x_right = None
            self.scene.selected_idx = None
            self.dragging_idx = None
            self.done_geom = False
            self.done_zap = False
            self.done_cajas = False
            self.done_corona = False
            self.done_cueles = False
            self.done_cc = False
            self.done_aux = False
            self.step = SP_GEOM
            self.draw()
            self._render_step_panel()
            self._update_step_label()
            self._sync_tabs()
            return

        # 2) Resto de pasos: elimina sus perforaciones y baja bandera
        self.scene.remove_holes_by_step(step_to_clear)
        self.scene.selected_idx = None
        self.dragging_idx = None

        flag_by_step = {
            SP_ZAP: "done_zap",
            SP_CAJAS: "done_cajas",
            SP_CORONA: "done_corona",
            SP_CUELES: "done_cueles",
            SP_CC: "done_cc",
            SP_AUX: "done_aux",
        }
        if step_to_clear in flag_by_step:
            setattr(self, flag_by_step[step_to_clear], False)

        self.draw()
        self._render_step_panel()
        self._update_step_label()
        self._sync_tabs()

    def clear_all(self):
        """Borra todo el diseño y vuelve al paso Eje."""
        # Reset del origen (eje) y del paneo
        globals()["ORIGIN_X"] = CANVAS_W // 2
        globals()["ORIGIN_Y"] = CANVAS_H // 2
        self._panning = False

        # Modelo de datos
        self.scene = Scene()
        self.drift_poly = []
        self.geom_index = None

        # Límites de pared (para Cajas)
        self.wall_top_y = None
        self.wall_x_left = None
        self.wall_x_right = None

        # Banderas de pasos
        self.step = SP_EJE
        self.done_eje = False
        self.done_geom = False
        self.done_zap = False
        self.done_cajas = False
        self.done_corona = False
        self.done_cueles = False
        self.done_cc = False
        self.done_aux = False

        # Refresco de UI
        self._render_step_panel()
        self._update_step_label()
        self._sync_tabs()
        self.draw()

    def export_json(self):
        """Exporta a JSON los hoyos y galerías en layout_export.json."""
        try:
            import json

            data = {"holes": self.scene.holes, "drifts": self.scene.drifts}
            with open("layout_export.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Export", "Guardado layout_export.json")
        except Exception as e:
            messagebox.showerror("Export", str(e))


if __name__ == "__main__":
    App().mainloop()
