# 
# APLICACIÓN GUI PARA DISEÑO DE GALERÍAS (DRIFTS), 
# FAMILIAS DE GEOMETRIAS Y CUELES

import math
import tkinter as tk
from tkinter import ttk, messagebox

# CARGA DE PATRONES DE CUELES (blast_cuts)
from blast_cuts import (
    cuele_sarrois_geom, cuele_sueco_geom, cuele_coromant_geom,
    cuele_cuna_geom, cuele_abanico_geom, cuele_bethune_geom, cuele_cuatro_secciones_geom,
    apply_series_sarrois, apply_series_sueco, apply_series_coromant,
    apply_series_cuna, apply_series_abanico, apply_series_bethune,
    apply_series_cuatro_secciones,
)

# GEOMETRÍA DE GALERÍAS (drift_geometry)
from drift_geometry import semicircular, d_shaped, rectangular, horseshoe, bezier_tunnel

# COLOCACIÓN DE FAMILIAS SOBRE LA GALERÍA (drift_layout)
from drift_layout import (
    place_zapateras, place_cajas, place_corona,
    place_aux_grid, place_contracuele_hex, place_contracuele_rect
)

# CONSTANTES MUNDO ↔ PANTALLA
PX_PER_M   = 160.0
GRID_M     = 0.10
CANVAS_W   = 1000
CANVAS_H   = 700
ORIGIN_X   = CANVAS_W // 2
ORIGIN_Y   = CANVAS_H // 2
SNAP_TOL_M = 0.20  # tolerancia para “snap” de contracuele en doble clic

def w2c(xm: float, ym: float):
    """Convierte coordenadas mundo (m) a canvas (px)."""
    return ORIGIN_X + xm*PX_PER_M, ORIGIN_Y - ym*PX_PER_M

def c2w(xp: float, yp: float):
    """Convierte coordenadas canvas (px) a mundo (m)."""
    return (xp - ORIGIN_X)/PX_PER_M, (ORIGIN_Y - yp)/PX_PER_M


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
SP_GEOM   = 0   # geometría
SP_ZAP    = 1   # zapateras (base)
SP_CAJAS  = 2   # cajas (paredes)
SP_CORONA = 3   # corona (techo)
SP_CUELES = 4   # cueles (clic para ubicar)
SP_CC     = 5   # contracuele (clic libre o doble clic en perforación)
SP_AUX    = 6   # perforaciones auxiliares (rejilla interna)
STEPS_MAX = SP_AUX


# APLICACIÓN
class App(tk.Tk):
    """Interfaz de usuario para el diseño paso a paso de galería + familias + cueles/contracuele."""
    def __init__(self):
        super().__init__()
        self.title("Diseño de galerías (drifts) y cueles - asistente por pasos")
        self.geometry(f"{CANVAS_W+380}x{CANVAS_H+40}")

        # -----------------------
        # Estado principal
        # -----------------------
        self.scene = Scene()
        self.drift_poly = []          # polilínea de la galería ACTIVA en edición
        self.geom_index = None        # índice de la galería activa dentro de scene.drifts
        self.step = SP_GEOM           # paso actual del asistente
        self.dragging_idx = None      # índice de perforación arrastrándose (si aplica)

        # -----------------------
        # Flags de finalización por paso
        # -----------------------
        self.done_geom = False
        self.done_zap = False
        self.done_cajas = False
        self.done_corona = False
        self.done_cueles = False
        self.done_cc = False
        self.done_aux = False

        # -----------------------
        # Grilla y ejes (antes de draw())
        # -----------------------
        self.grid_m    = tk.DoubleVar(value=0.10)   # tamaño de celda en metros
        self.major_n   = tk.IntVar(value=5)         # línea mayor cada N menores
        self.show_grid = tk.BooleanVar(value=True)  # mostrar grilla
        self.show_axes = tk.BooleanVar(value=False) # mostrar ejes X/Y

        # -----------------------
        # Bloqueo de creación y edición libre del arco
        # -----------------------
        # Si True, evita que un click cree otra galería encima de la actual
        # (útil cuando estás editando con manillas o puntos libres)
        self.lock_geom_insert = tk.BooleanVar(value=True)

        # Edición libre del arco con puntos insertables/arrastrables
        self.edit_free = tk.BooleanVar(value=True)
        self.free_handles = []         # [{'i': idx_en_poly, 'x':..., 'y':...}, ...]
        self._drag_free_idx = None     # índice dentro de free_handles en arrastre
        self._arc_span = None          # (start_idx, end_idx) tramo del arco en drift_poly (incl.)
        self._arc_n = 0                # cantidad de puntos del arco (meta, opcional)

        # -----------------------
        # Estado de controles persistentes (Geometría)
        # (No se reinician al cambiar de paso)
        # -----------------------
        self.geom_type  = tk.StringVar(value="Semicircular")
        self.geom_w     = tk.DoubleVar(value=3.0)   # ancho total (o 2R)
        self.geom_h     = tk.DoubleVar(value=3.0)   # alto (o altura de pared)
        self.geom_r     = tk.DoubleVar(value=1.5)   # radio (semicircular / tope D)
        self.geom_curve = tk.DoubleVar(value=0.8)   # bombeo Bezier


        # Edición por manillas (D-shaped / Horseshoe)
 
        self.edit_arc = tk.BooleanVar(value=False)  # overlay de manillas C/R
        self.arc_handles = []                       # [{'role':'C'|'R','x':...,'y':...}, ...]
        self._drag_arc_idx = None                   # índice de manilla que se arrastra
        self._arc_base_y = None                     # y de base (piso) con que se creó el drift
        self._arc_kind = None                       # 'dshaped' | 'horseshoe' (informativo
        #Variables de estado paredes
        self.wall_top_y   = None
        self.wall_x_left  = None
        self.wall_x_right = None

        # Construcción de UI y primer render


        self._build_ui()
        self._render_step_panel()
        self._update_step_label()
        self.draw()




# Métodos para editar arco
# (D-shaped / Horseshoe)

    def _arc_points(self, Cx, Cy, r, n=32):
        """
        Genera puntos de un semicírculo (techo) centrado en (Cx, Cy) con radio r.
        Recorre desde la izquierda (ángulo π) hacia la derecha (ángulo 0),
        devolviendo una lista de vértices [(x,y), ...] para dibujar el arco.

        Args:
            Cx, Cy (float): centro del arco (el "tope" de las paredes).
            r (float): radio del arco (ancho/2).
            n (int): cantidad de segmentos (más = más suave).

        Returns:
            list[tuple[float,float]]: puntos (x,y) del semicírculo.
        """
        pts = []
        for i in range(n + 1):
            # th va de π → 0 (izquierda a derecha)
            th = math.pi - (math.pi * i / n)
            x = Cx + r * math.cos(th)
            y = Cy + r * math.sin(th)
            pts.append((x, y))
        return pts


    def _init_arc_handles(self, xm, ym, width, wall_h, kind):
        """
        Inicializa las manillas de edición del arco para D-shaped/Horseshoe.

        Creamos dos manillas:
          - 'C': Centro del arco (Cx, Cy). Moverla ↑/↓ cambia la altura de paredes.
          - 'R': Punto sobre el arco por encima de C (mismo x, y+radio).
            Moverla ↑/↓ cambia el radio (y con ello el ancho = 2r).

        Además guardamos:
          - _arc_base_y: y de la base (piso) con la que se creó la galería.
          - _arc_kind:   tipo de galería ('dshaped' | 'horseshoe'), por si lo necesitas.

        Args:
            xm, ym (float): click del usuario (centro horizontal y base vertical).
            width (float): ancho inicial (sugiere r = width/2).
            wall_h (float): altura de paredes rectas (hasta el inicio del arco).
            kind (str): 'dshaped' o 'horseshoe'.
        """
        Cx, Cy = xm, ym + wall_h                    # centro del arco
        r = max(0.05, width * 0.5)                  # radio mínimo de seguridad
        # C = centro; R = punto sobre el arco (arriba del centro)
        self.arc_handles = [
            {"role": "C", "x": Cx, "y": Cy},
            {"role": "R", "x": Cx, "y": Cy + r},
        ]
        self._arc_base_y = ym
        self._arc_kind = kind


    def _rebuild_drift_from_arc(self):
        """
        Reconstruye la polilínea de la galería (paredes + techo) a partir
        de las manillas de arco actuales ('C' y 'R').

        Lógica:
        - r = distancia(C, R)
        - left_top  = (Cx - r, Cy)
        - right_top = (Cx + r, Cy)
        - paredes: desde base_y hasta Cy en x fijo (izquierda/derecha)
        - techo: semicírculo entre left_top y right_top centrado en (Cx, Cy)

        Side effects:
        - Actualiza self.drift_poly con los nuevos vértices.
        - Si existe al menos un drift en escena, actualiza el último.
        """
        if len(self.arc_handles) < 2 or self._arc_base_y is None:
            return

        # Obtiene posiciones de manillas
        roles = {h["role"]: (h["x"], h["y"]) for h in self.arc_handles}
        (Cx, Cy) = roles["C"]
        (Rx, Ry) = roles["R"]

        # Radio = distancia entre centro y punto sobre arco
        r = max(0.05, math.hypot(Rx - Cx, Ry - Cy))

        # Geometría resultante
        yb = self._arc_base_y  # y de la base (piso)
        left_top  = (Cx - r, Cy)
        right_top = (Cx + r, Cy)
        left_base  = (left_top[0], yb)
        right_base = (right_top[0], yb)

        # Arco superior (semicírculo)
        arc = self._arc_points(Cx, Cy, r, n=48)

        # Polilínea cerrada: base izq -> top izq -> arco -> top der -> base der -> base izq
        verts = [left_base, left_top] + arc + [right_top, right_base, left_base]
        self.drift_poly = verts

        # Mantén sincronizado el último drift en escena (si lo estás usando así)
        if hasattr(self.scene, "drifts") and self.scene.drifts:
            self.scene.drifts[-1] = verts

        # (Opcional) Si quieres reflejar el cambio en la UI:
        # self.geom_w.set(2 * r)
        # self.geom_h.set(Cy - yb)  # para horseshoe (altura de pared)
        # Nota: en D-shaped tu altura total suele ser pared + r;
        #       ajusta según cómo quieras reflejarlo en la UI.


    def _hit_arc_handle(self, xm, ym, tol=0.15):
        """
        Devuelve el índice de la manilla de arco más cercana a (xm, ym)
        si está dentro de la tolerancia 'tol' (en metros). Si ninguna,
        retorna None.

        Se usa para "tomar" una manilla al hacer click cerca de ella.

        Args:
            xm, ym (float): coordenadas en el mundo (no en píxeles).
            tol (float): radio de captura (m).

        Returns:
            int | None: índice de la manilla en self.arc_handles o None.
        """
        best, bestd = None, 1e9
        for i, h in enumerate(self.arc_handles):
            d = math.hypot(h["x"] - xm, h["y"] - ym)
            if d < bestd and d <= tol:
                best, bestd = i, d
        return best



    def _tag(self, holes, step, kind):
        """Agrega etiquetas internas de control a un conjunto de perforaciones."""
        for h in holes:
            h["_step"] = step
            h["_kind"] = kind
        return holes

    def _build_ui(self):
        """Construye los widgets estáticos de la interfaz."""
        # canvas
        self.canvas = tk.Canvas(self, width=CANVAS_W, height=CANVAS_H, bg="white")
        self.canvas.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0,   weight=1)

        # lateral
        self.side = ttk.Frame(self)
        self.side.grid(row=0, column=1, sticky="ns", padx=6, pady=6)

        # cabecera
        hdr = ttk.Frame(self.side); hdr.pack(fill="x")
        self.step_label = ttk.Label(hdr, text="")
        self.step_label.pack(anchor="w")

        # panel de paso
        self.step_frame = ttk.Frame(self.side)
        self.step_frame.pack(fill="x", pady=(6,4))

        # opciones generales
        opts = ttk.LabelFrame(self.side, text="Opciones")
        opts.pack(fill="x", pady=6)
        self.show_labels = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts, text="Mostrar series", variable=self.show_labels,
                        command=self.draw).pack(anchor="w")
        self.snap_grid = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="Ajustar a grilla", variable=self.snap_grid).pack(anchor="w")

        #  controles de grilla/ejes <<<
        ttk.Checkbutton(opts, text="Mostrar grilla", variable=self.show_grid,
                        command=self.draw).pack(anchor="w")
        ttk.Checkbutton(opts, text="Mostrar ejes X/Y", variable=self.show_axes,
                        command=self.draw).pack(anchor="w")
        ttk.Checkbutton(opts, text="Bloquear creación (clic edita)",
                variable=self.lock_geom_insert).pack(anchor="w")

        ttk.Checkbutton(opts, text="Edición libre del arco (puntos)",
                        variable=self.edit_free, command=self.draw).pack(anchor="w")


        row_opts = ttk.Frame(opts); row_opts.pack(fill="x", pady=(4,0))
        ttk.Label(row_opts, text="Grilla (m):").pack(side="left")
        e_grid = ttk.Entry(row_opts, textvariable=self.grid_m, width=6)
        e_grid.pack(side="left", padx=(4,8))
        ttk.Label(row_opts, text="Mayor cada:").pack(side="left")
        sp_major = ttk.Spinbox(row_opts, from_=2, to=20, textvariable=self.major_n,
                               width=4, command=self.draw)
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

        ttk.Label(self.side, text="Arrastra puntos para ajustarlos manualmente.")\
            .pack(anchor="w", pady=(2,8))

        # navegación
        foot = ttk.Frame(self.side); foot.pack(fill="x", pady=(6,0))
        self.btn_prev = ttk.Button(foot, text="Anterior", command=self.prev_step)
        self.btn_prev.pack(side="left")
        self.btn_next = ttk.Button(foot, text="Siguiente", command=self.next_step)
        self.btn_next.pack(side="right")

        # utilidades
        util = ttk.Frame(self.side); util.pack(fill="x", pady=6)
        ttk.Button(util, text="Borrar todo", command=self.clear_all).pack(side="left")
        ttk.Button(util, text="Export JSON", command=self.export_json).pack(side="right")

        # eventos
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.bind("<Delete>", self._delete_selected)
        self.bind("<BackSpace>", self._delete_selected)



    def _render_step_panel(self):
        """Reconstruye el panel lateral del paso actual con sus controles."""
        for w in self.step_frame.winfo_children():
            w.destroy()

        self.btn_prev.configure(state="normal" if self.step > SP_GEOM else "disabled")
        self.btn_next.configure(state="disabled")

        if self.step == SP_GEOM:
            frm = ttk.LabelFrame(self.step_frame, text="Geometría de galería")
            frm.pack(fill="x")

            ttk.Label(frm, text="Tipo").grid(row=0, column=0, sticky="w")
            ttk.Combobox(
                frm, textvariable=self.geom_type,
                values=["Semicircular", "D-shaped", "Rectangular", "Horseshoe", "Bezier"],
                state="readonly", width=18
            ).grid(row=0, column=1, sticky="e")

            row = 1
            for label, var in [
                ("Ancho / 2R", self.geom_w),
                ("Alto",        self.geom_h),
                ("Radio",       self.geom_r),
                ("Curva (Bezier)", self.geom_curve),
            ]:
                ttk.Label(frm, text=label).grid(row=row, column=0, sticky="w")
                ttk.Entry(frm, textvariable=var, width=10).grid(row=row, column=1, sticky="e")
                row += 1

            ttk.Label(self.step_frame, text="Haz CLICK en el canvas para ubicar el centro de la galería.").pack(anchor="w", pady=(6,6))
            ttk.Button(self.step_frame, text="Borrar este paso", command=lambda: self._clear_step(SP_GEOM)).pack(anchor="w")

            if self.drift_poly:
                self.done_geom = True
            self.btn_next.configure(state="normal" if self.done_geom else "disabled")

        elif self.step == SP_ZAP:
            frm = ttk.LabelFrame(self.step_frame, text="Zapateras (base)")
            frm.pack(fill="x")
            self.n_zap = tk.IntVar(value=6)
            ttk.Label(frm, text="Nº de perforaciones").grid(row=0, column=0, sticky="w")
            ttk.Entry(frm, textvariable=self.n_zap, width=10).grid(row=0, column=1, sticky="e")

            bar = ttk.Frame(self.step_frame); bar.pack(fill="x", pady=(6,0))
            ttk.Button(bar, text="Agregar", command=self._do_zap).pack(side="left")
            ttk.Button(bar, text="Borrar este paso", command=lambda: self._clear_step(SP_ZAP)).pack(side="left", padx=6)

            ttk.Label(self.step_frame, text="Se distribuirán equidistantes sobre la base.").pack(anchor="w", pady=(6,0))
            self.btn_next.configure(state="normal" if self.done_zap else "disabled")

        elif self.step == SP_CAJAS:
            frm = ttk.LabelFrame(self.step_frame, text="Cajas (paredes)")
            frm.pack(fill="x")
            self.n_caja = tk.IntVar(value=5)
            ttk.Label(frm, text="Cajas por lado").grid(row=0, column=0, sticky="w")
            ttk.Entry(frm, textvariable=self.n_caja, width=10).grid(row=0, column=1, sticky="e")

            bar = ttk.Frame(self.step_frame); bar.pack(fill="x", pady=(6,0))
            ttk.Button(bar, text="Agregar", command=self._do_cajas).pack(side="left")
            ttk.Button(bar, text="Borrar este paso", command=lambda: self._clear_step(SP_CAJAS)).pack(side="left", padx=6)

            ttk.Label(self.step_frame, text="Se colocan en ambos lados (mismo número por lado).").pack(anchor="w", pady=(6,0))
            self.btn_next.configure(state="normal" if self.done_cajas else "disabled")

        elif self.step == SP_CORONA:
            frm = ttk.LabelFrame(self.step_frame, text="Corona (techo)")
            frm.pack(fill="x")
            self.n_corona = tk.IntVar(value=8)
            ttk.Label(frm, text="Nº de perforaciones").grid(row=0, column=0, sticky="w")
            ttk.Entry(frm, textvariable=self.n_corona, width=10).grid(row=0, column=1, sticky="e")

            bar = ttk.Frame(self.step_frame); bar.pack(fill="x", pady=(6,0))
            ttk.Button(bar, text="Agregar", command=self._do_corona).pack(side="left")
            ttk.Button(bar, text="Borrar este paso", command=lambda: self._clear_step(SP_CORONA)).pack(side="left", padx=6)

            ttk.Label(self.step_frame, text="Se distribuirán equidistantes en el techo.").pack(anchor="w", pady=(6,0))
            self.btn_next.configure(state="normal" if self.done_corona else "disabled")

        elif self.step == SP_CUELES:
            frm = ttk.LabelFrame(self.step_frame, text="Cueles")
            frm.pack(fill="x")

            ttk.Label(frm, text="Tipo").grid(row=0, column=0, sticky="w")
            self.cuele_type = tk.StringVar(value="Sarrois")
            ttk.Combobox(
                frm, textvariable=self.cuele_type,
                values=["Sarrois","Sueco","Coromant","Cuña 2x3","Cuña zigzag","Abanico","Bethune","Cuatro secciones"],
                state="readonly", width=18
            ).grid(row=0, column=1, sticky="e")

            self.d_var = tk.DoubleVar(value=0.15)
            self.rot   = tk.DoubleVar(value=0.0)
            self.sx    = tk.DoubleVar(value=1.0)
            self.sy    = tk.DoubleVar(value=1.0)
            self.vy    = tk.DoubleVar(value=3.5)

            row = 1
            for label, var in [("d (m)", self.d_var), ("rot (°)", self.rot),
                               ("scale X", self.sx), ("scale Y", self.sy), ("Bethune vy", self.vy)]:
                ttk.Label(frm, text=label).grid(row=row, column=0, sticky="w")
                ttk.Entry(frm, textvariable=var, width=10).grid(row=row, column=1, sticky="e")
                row += 1

            ttk.Label(self.step_frame, text="Haz CLICK en el canvas para insertar un cuele.").pack(anchor="w", pady=(6,6))
            ttk.Button(self.step_frame, text="Borrar este paso", command=lambda: self._clear_step(SP_CUELES)).pack(anchor="w")
            self.btn_next.configure(state="normal" if self.done_cueles else "disabled")

        elif self.step == SP_CC:
            frm = ttk.LabelFrame(self.step_frame, text="Contracuele")
            frm.pack(fill="x")

            ttk.Label(frm, text="Figura").grid(row=0, column=0, sticky="w")
            self.cc_type = tk.StringVar(value="Hexágono")
            ttk.Combobox(frm, textvariable=self.cc_type,
                         values=["Hexágono","Rectángulo"], state="readonly", width=18).grid(row=0, column=1, sticky="e")

            self.cc_hex_r  = tk.DoubleVar(value=0.8)
            self.cc_rect_w = tk.DoubleVar(value=1.6)
            self.cc_rect_h = tk.DoubleVar(value=1.1)
            self.cc_rect_n = tk.IntVar(value=2)

            row = 1
            ttk.Label(frm, text="Hex r").grid(row=row, column=0, sticky="w")
            ttk.Entry(frm, textvariable=self.cc_hex_r, width=10).grid(row=row, column=1, sticky="e"); row += 1
            ttk.Label(frm, text="Rect w").grid(row=row, column=0, sticky="w")
            ttk.Entry(frm, textvariable=self.cc_rect_w, width=10).grid(row=row, column=1, sticky="e"); row += 1
            ttk.Label(frm, text="Rect h").grid(row=row, column=0, sticky="w")
            ttk.Entry(frm, textvariable=self.cc_rect_h, width=10).grid(row=row, column=1, sticky="e"); row += 1
            ttk.Label(frm, text="Rect n/lado").grid(row=row, column=0, sticky="w")
            ttk.Entry(frm, textvariable=self.cc_rect_n, width=10).grid(row=row, column=1, sticky="e"); row += 1

            ttk.Label(self.step_frame, text="CLICK: coloca libre.  DOBLE CLICK: usa centro de perforación más cercana.").pack(anchor="w", pady=(6,6))
            ttk.Button(self.step_frame, text="Borrar este paso", command=lambda: self._clear_step(SP_CC)).pack(anchor="w")
            self.btn_next.configure(state="normal" if self.done_cc else "disabled")

        elif self.step == SP_AUX:
            frm = ttk.LabelFrame(self.step_frame, text="Perforaciones auxiliares (grilla interna)")
            frm.pack(fill="x")
            self.aux_nx = tk.IntVar(value=5)
            self.aux_ny = tk.IntVar(value=3)
            ttk.Label(frm, text="nx").grid(row=0, column=0, sticky="w")
            ttk.Entry(frm, textvariable=self.aux_nx, width=10).grid(row=0, column=1, sticky="e")
            ttk.Label(frm, text="ny").grid(row=1, column=0, sticky="w")
            ttk.Entry(frm, textvariable=self.aux_ny, width=10).grid(row=1, column=1, sticky="e")

            bar = ttk.Frame(self.step_frame); bar.pack(fill="x", pady=(6,0))
            ttk.Button(bar, text="Agregar", command=self._do_aux).pack(side="left")
            ttk.Button(bar, text="Borrar este paso", command=lambda: self._clear_step(SP_AUX)).pack(side="left", padx=6)

            ttk.Label(self.step_frame, text="Se distribuyen equidistantes dentro de la galería.").pack(anchor="w", pady=(6,0))
            self.btn_next.configure(state="normal" if self.done_aux else "disabled")

    def _update_step_label(self):
        """Actualiza el rótulo del paso actual."""
        names = {
            SP_GEOM:   "Paso 1/7: Geometría",
            SP_ZAP:    "Paso 2/7: Zapateras",
            SP_CAJAS:  "Paso 3/7: Cajas",
            SP_CORONA: "Paso 4/7: Corona",
            SP_CUELES: "Paso 5/7: Cueles",
            SP_CC:     "Paso 6/7: Contracuele",
            SP_AUX:    "Paso 7/7: Auxiliares",
        }
        self.step_label.config(text=names[self.step])

    def prev_step(self):
        """Retrocede un paso en el asistente si es posible."""
        if self.step > SP_GEOM:
            self.step -= 1
            self._render_step_panel()
            self._update_step_label()

    def next_step(self):
        """Avanza al siguiente paso si el actual está completo."""
        if self.step == SP_GEOM and not self.done_geom:
            messagebox.showwarning("Geometría", "Coloca la geometría con un click en el canvas.")
            return
        if self.step == SP_ZAP and not self.done_zap:
            messagebox.showwarning("Zapateras", "Pulsa 'Agregar' para colocar las zapateras.")
            return
        if self.step == SP_CAJAS and not self.done_cajas:
            messagebox.showwarning("Cajas", "Pulsa 'Agregar' para colocar las cajas.")
            return
        if self.step == SP_CORONA and not self.done_corona:
            messagebox.showwarning("Corona", "Pulsa 'Agregar' para colocar la corona.")
            return
        if self.step == SP_CUELES and not self.done_cueles:
            messagebox.showwarning("Cueles", "Inserta al menos un cuele haciendo click en el canvas.")
            return
        if self.step == SP_CC and not self.done_cc:
            messagebox.showwarning("Contracuele", "Inserta el contracuele con click o doble click.")
            return

        if self.step < STEPS_MAX:
            self.step += 1
            self._render_step_panel()
            self._update_step_label()

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
        if (getattr(self, "wall_top_y", None) is not None and
            getattr(self, "wall_x_left", None) is not None and
            getattr(self, "wall_x_right", None) is not None):
            x1, y1 = w2c(self.wall_x_left,  self.wall_top_y)
            x2, y2 = w2c(self.wall_x_right, self.wall_top_y)
            self.canvas.create_line(x1, y1, x2, y2, dash=(4, 3), fill="#999")

        # --- Overlay: edición de arco (D-shaped / Horseshoe) ---
        # Manillas 'C' (centro del arco) y 'R' (radio), más la línea guía entre ellas.
        if (self.step == SP_GEOM and
            getattr(self, "edit_arc", tk.BooleanVar(value=False)).get() and
            getattr(self, "arc_handles", [])):

            # Dibuja línea guía C-R y las manillas
            try:
                roles = {h["role"]: (h["x"], h["y"]) for h in self.arc_handles}
                if "C" in roles and "R" in roles:
                    (Cx, Cy) = roles["C"]
                    (Rx, Ry) = roles["R"]
                    x1, y1 = w2c(Cx, Cy)
                    x2, y2 = w2c(Rx, Ry)
                    # guía
                    self.canvas.create_line(x1, y1, x2, y2, dash=(3, 3), fill="#999")
            except Exception:
                pass

            # manillas
            for h in self.arc_handles:
                xp, yp = w2c(h["x"], h["y"])
                r = 6
                fill = "#2ca02c" if h.get("role") == "C" else "#ff7f0e"
                self.canvas.create_oval(xp - r, yp - r, xp + r, yp + r, fill=fill, outline="")
                self.canvas.create_text(xp, yp - 10, text=h.get("role", "?"),
                                        fill="#444", font=("Arial", 9))

        #  Overlay: edición libre de puntos del arco (tipo spline simple) ---
        # Muestra marcadores en los vértices seleccionados como "free handles".
        if (self.step == SP_GEOM and
            getattr(self, "edit_free", tk.BooleanVar(value=False)).get() and
            getattr(self, "free_handles", []) and
            getattr(self, "drift_poly", [])):

            for fh in self.free_handles:
                i = fh.get("i")
                if i is None:
                    continue
                if 0 <= i < len(self.drift_poly):
                    x, y = self.drift_poly[i]
                    xp, yp = w2c(x, y)
                    r = 5
                    # marcador del handle libre (azul)
                    self.canvas.create_rectangle(xp - r, yp - r, xp + r, yp + r,
                                                outline="#1f77b4", fill="")
                    # índice pequeño arriba
                    self.canvas.create_text(xp, yp - 10, text=str(i),
                                            fill="#1f77b4", font=("Arial", 8))


    def _draw_grid(self):
        """Dibuja una grilla con líneas menores/mayores y ejes opcionales."""
        # Nada que dibujar
        if not self.show_grid.get() and not self.show_axes.get():
            return

        # Parámetros
        try:
            gm = max(0.01, float(self.grid_m.get())) #metros por celda 
        except Exception:
            gm = GRID_M

        try:
            major_every = max(2, int(self.major_n.get()))
        except Exception:
            major_every = 5

        step = gm * PX_PER_M           # píxeles por celda
        W, H = CANVAS_W, CANVAS_H

        def crisp(v):                  # líneas nítidas
            return int(v) + 0.5


        if self.show_grid.get():
            # Verticales: origen y hacia la derecha
            k, x = 0, ORIGIN_X
            while x <= W:
                is_major = (k % major_every == 0)
                self.canvas.create_line(crisp(x), 0, crisp(x), H,
                                        fill="#b0b0b0" if is_major else "#cfcfcf",
                                        width=1.5 if is_major else 1)
                k += 1; x = ORIGIN_X + k*step
            # Verticales: hacia la izquierda
            k, x = 1, ORIGIN_X - step
            while x >= 0:
                is_major = (k % major_every == 0)
                self.canvas.create_line(crisp(x), 0, crisp(x), H,
                                        fill="#b0b0b0" if is_major else "#cfcfcf",
                                        width=1.5 if is_major else 1)
                k += 1; x = ORIGIN_X - k*step

            # Horizontales: origen y hacia abajo
            k, y = 0, ORIGIN_Y
            while y <= H:
                is_major = (k % major_every == 0)
                self.canvas.create_line(0, crisp(y), W, crisp(y),
                                        fill="#b0b0b0" if is_major else "#cfcfcf",
                                        width=1.5 if is_major else 1)
                k += 1; y = ORIGIN_Y + k*step
            # Horizontales: hacia arriba
            k, y = 1, ORIGIN_Y - step
            while y >= 0:
                is_major = (k % major_every == 0)
                self.canvas.create_line(0, crisp(y), W, crisp(y),
                                        fill="#b0b0b0" if is_major else "#cfcfcf",
                                        width=1.5 if is_major else 1)
                k += 1; y = ORIGIN_Y - k*step

        # Ejes X/Y opcionales
        if self.show_axes.get():
            self.canvas.create_line(0, crisp(ORIGIN_Y), W, crisp(ORIGIN_Y), fill="#666", width=2)
            self.canvas.create_line(crisp(ORIGIN_X), 0, crisp(ORIGIN_X), H, fill="#666", width=2)

    def _draw_drifts(self):
        """Dibuja todas las polilíneas de drift (galería)."""
        polys = list(self.scene.drifts)
        if self.drift_poly:
            polys.append(self.drift_poly)
        for poly in polys:
            if not poly or len(poly) < 2:
                continue
            pts = []
            for (x, y) in poly:
                xp, yp = w2c(x, y)
                pts.extend([xp, yp])
            self.canvas.create_line(*pts, fill="#888", width=2)
    def _draw_holes(self):
        """Dibuja perforaciones; si hay 'serie' usa paleta por serie."""
        r_px = 5
        palette = ["#2ca02c","#ff7f0e","#d62728","#9467bd","#8c564b","#e377c2"]
        for i, h in enumerate(self.scene.holes):
            xp, yp = w2c(h["x"], h["y"])
            if "serie" in h:
                color = "black" if h.get("is_void", False) else palette[h["serie"] % len(palette)]
            else:
                color = "black" if h.get("is_void", False) else "#1f77b4"
            self.canvas.create_oval(xp-r_px, yp-r_px, xp+r_px, yp+r_px, fill=color, outline="")
            if self.show_labels.get() and "serie" in h:
                self.canvas.create_text(xp, yp-10, text=str(h["serie"]), fill="#444", font=("Arial", 9))
            if i == self.scene.selected_idx:
                self.canvas.create_oval(xp-9, yp-9, xp+9, yp+9, outline="#444")
    
    def _hit_free_handle(self, xm, ym, tol=0.15):
        """Índice en self.free_handles si haces click cerca de un handle libre."""
        best, bestd = None, 1e9
        for j, fh in enumerate(self.free_handles):
            i = fh.get("i")
            if i is None or not (0 <= i < len(self.drift_poly)):
                continue
            x, y = self.drift_poly[i]
            d = math.hypot(x - xm, y - ym)
            if d < bestd and d <= tol:
                best, bestd = j, d
        return best

   
    def _dist_point_to_segment(px, py, x1, y1, x2, y2):
        """Distancia de punto a segmento y el parámetro t de proyección (0..1)."""
        vx, vy = x2 - x1, y2 - y1
        wx, wy = px - x1, py - y1
        vv = vx*vx + vy*vy
        if vv <= 1e-12:
            # segmento degenerado
            return math.hypot(px - x1, py - y1), 0.0
        t = (wx*vx + wy*vy) / vv
        t = max(0.0, min(1.0, t))
        qx = x1 + t*vx
        qy = y1 + t*vy
        return math.hypot(px - qx, py - qy), t

    def _insert_vertex_on_arc(self, xm, ym, tol=0.30):
        """
        Inserta un vértice en el arco cerca del click (xm,ym) si hay segmento a <= tol.
        Actualiza drift_poly, scene.drifts, free_handles y _arc_span.
        Retorna el índice del nuevo vértice o None si no insertó.
        """
        if not self.drift_poly or not self._arc_span:
            return None
        s, e = self._arc_span  # inclusive
        best = (None, None, 1e9, 0.0)  # (idx_seg, insert_at, dist, t)
        for i in range(s, min(e, len(self.drift_poly) - 2) + 1):
            x1, y1 = self.drift_poly[i]
            x2, y2 = self.drift_poly[i + 1]
            d, t = self._dist_point_to_segment(xm, ym, x1, y1, x2, y2)
            if d < best[2]:
                best = (i, i + 1, d, t)

        idx_seg, insert_at, dist, t = best
        if idx_seg is None or dist > tol:
            return None

        x1, y1 = self.drift_poly[idx_seg]
        x2, y2 = self.drift_poly[idx_seg + 1]
        nx = x1 + t*(x2 - x1)
        ny = y1 + t*(y2 - y1)

        # Inserta vértice
        self.drift_poly.insert(insert_at, (nx, ny))

        # Empuja índices de handles >= insert_at
        for fh in self.free_handles:
            if fh["i"] >= insert_at:
                fh["i"] += 1
        # Agrega este nuevo como handle
        self.free_handles.append({"i": insert_at})

        # Corre el span del arco (se alarga en 1)
        if self._arc_span:
            s, e = self._arc_span
            if insert_at >= s and insert_at <= e + 1:
                self._arc_span = (s, e + 1)

        # Sincroniza escena
        if getattr(self.scene, "drifts", []):
            self.scene.drifts[-1] = list(self.drift_poly)

        return insert_at

    def _delete_free_handle_near(self, xm, ym, tol=0.15):
        """Elimina el handle más cercano si está dentro de tol. Retorna True si borró."""
        j = self._hit_free_handle(xm, ym, tol=tol)
        if j is None:
            return False
        i = self.free_handles[j]["i"]
        # Protege extremos del arco: evita borrar si i es extremo del span
        if self._arc_span:
            s, e = self._arc_span
            if i == s or i == e:
                return False

        # Borra vértice i
        if 0 <= i < len(self.drift_poly):
            del self.drift_poly[i]

            # Ajusta _arc_span
            if self._arc_span:
                s, e = self._arc_span
                if i <= e:
                    e -= 1
                if i < s:
                    s -= 1
                self._arc_span = (max(0, s), max(0, e))

            # Ajusta índices de handles
            for k, fh in enumerate(self.free_handles):
                if k == j:
                    continue
                if fh["i"] > i:
                    fh["i"] -= 1
            del self.free_handles[j]

            # Sincroniza escena
            if getattr(self.scene, "drifts", []):
                self.scene.drifts[-1] = list(self.drift_poly)
            return True
        return False

    def on_click(self, ev):
        """
        Click izquierdo:
        1) Si estás editando geometría (manillas de arco o edición libre), toma manilla
            o inserta un punto libre sobre el arco.
        2) Si no estás editando geometría, permite seleccionar una perforación para arrastrarla.
        3) Si estás en Paso GEOM y el candado permite insertar, crea la geometría.
        4) En otros pasos: inserta cueles / contracuele según corresponda.
        """
        # Evita que la barra espaciadora accione botones con foco
        self.canvas.focus_set()

        # 0) Coords a "metros" (+ snap si corresponde)
        xm, ym = c2w(ev.x, ev.y)
        if self.snap_grid.get():
            gm = max(0.01, float(self.grid_m.get()))
            xm = round(xm / gm) * gm
            ym = round(ym / gm) * gm

        # 1) Edición de manillas del ARCO (C/R) para D-shaped / Horseshoe
        if self.step == SP_GEOM and self.edit_arc.get() and self.arc_handles:
            hi = self._hit_arc_handle(xm, ym, tol=0.20)
            if hi is not None:
                self._drag_arc_idx = hi
                return  # no continuar (estamos arrastrando manilla de arco)

        # 1b) Edición LIBRE del arco con puntos (si hay galería y candado activo)
        if (self.step == SP_GEOM and self.done_geom and
            self.lock_geom_insert.get() and self.edit_free.get()):
            # ¿Click sobre un handle libre existente? -> empezar arrastre
            hi = self._hit_free_handle(xm, ym, tol=0.15)
            if hi is not None:
                self._drag_free_idx = hi
                return
            # Si no tocaste un handle, intenta insertar un punto nuevo sobre el arco
            if self._insert_vertex_on_arc(xm, ym, tol=0.25):
                self.draw()
                return
            # Si no estaba cerca del arco, ignoramos (no insertamos otra galería)

        # 2) Selección/arrastre de perforación (solo si NO editas geometría)
        editing_geom = (
            self.step == SP_GEOM and (
                (self.edit_arc.get() and self.arc_handles) or
                (self.edit_free.get() and self.done_geom and self.lock_geom_insert.get())
            )
        )
        if not editing_geom:
            idx = self.scene.nearest(xm, ym)
            # Evita capturar perforaciones en pasos que requieren click de inserción
            if idx is not None and self.step not in (SP_CUELES, SP_CC):
                self.scene.selected_idx = idx
                self.dragging_idx = idx
                self.draw()
                return

        # 2b) Bloqueo: si ya hay una galería y el candado está activo, no insertes otra
        if (self.step == SP_GEOM and self.lock_geom_insert.get() and
            (self.drift_poly or (hasattr(self.scene, "drifts") and self.scene.drifts))):
            return

        # 3) Inserción según paso
        # 3.1) GEOMETRÍA
        if self.step == SP_GEOM:
            gtype = self.geom_type.get()

            if gtype == "Semicircular":
                R = float(self.geom_r.get())
                self.drift_poly = semicircular(xm, ym, radius=R, n_points=48)
                # No hay paredes verticales puras en semicircular
                self.wall_top_y = None
                self.wall_x_left = None
                self.wall_x_right = None

            elif gtype == "Rectangular":
                w = float(self.geom_w.get()); h = float(self.geom_h.get())
                self.drift_poly = rectangular(xm, ym, width=w, height=h)
                # Paredes rectas completas
                self.wall_top_y   = ym + h
                self.wall_x_left  = xm - w * 0.5
                self.wall_x_right = xm + w * 0.5

            elif gtype == "D-shaped":
                # r = w/2. Si h <= r, sería semicircular — forzamos pared mínima
                w = float(self.geom_w.get()); h = float(self.geom_h.get())
                r = max(0.05, w * 0.5)
                if h <= r:
                    h = r + 0.1
                self.drift_poly = d_shaped(xm, ym, width=w, height=h, n_points=48)
                # En D: paredes hasta (h - r)
                self.wall_top_y   = ym + (h - r)
                self.wall_x_left  = xm - r
                self.wall_x_right = xm + r
                # Manillas para editar el arco
                self._init_arc_handles(xm, ym, width=w, wall_h=(h - r), kind="dshaped")
                self.edit_arc.set(True)

            elif gtype == "Horseshoe":
                # 'height' es la altura de pared recta; el semicírculo va encima
                w = float(self.geom_w.get()); wall = max(0.05, float(self.geom_h.get()))
                self.drift_poly = horseshoe(xm, ym, width=w, height=wall, n_curve=24)
                self.wall_top_y   = ym + wall
                self.wall_x_left  = xm - w * 0.5
                self.wall_x_right = xm + w * 0.5
                # Manillas para editar el arco
                self._init_arc_handles(xm, ym, width=w, wall_h=wall, kind="horseshoe")
                self.edit_arc.set(True)

            elif gtype == "Bezier":
                w = float(self.geom_w.get()); wall = float(self.geom_h.get()); ch = float(self.geom_curve.get())
                self.drift_poly = bezier_tunnel(xm, ym, width=w, wall_height=wall, curve_height=ch, n_points=48)
                self.wall_top_y   = ym + wall
                self.wall_x_left  = xm - w * 0.5
                self.wall_x_right = xm + w * 0.5
                # (Si implementas edición Bezier con manillas p0..p3, inicialízalas aquí.)

            else:
                self.drift_poly = []

            self.geom_index = self.scene.add_drift(self.drift_poly)
            self.done_geom = bool(self.drift_poly)
            self.draw()
            self._render_step_panel()
            return

        # 3.2) CUELES
        if self.step == SP_CUELES:
            holes = self._insert_cuele_at(xm, ym)
            if holes:
                self.scene.add_holes(self._tag(holes, SP_CUELES, "cuele"))
                self.done_cueles = True
                self.draw()
                self._render_step_panel()
            return

        # 3.3) CONTRACUELE (click simple; doble click tiene su propio handler)
        if self.step == SP_CC:
            cct = self.cc_type.get()
            if cct == "Hexágono":
                r = float(self.cc_hex_r.get())
                holes = place_contracuele_hex((xm, ym), r=r)
            else:
                w = float(self.cc_rect_w.get()); h = float(self.cc_rect_h.get()); m = int(self.cc_rect_n.get())
                holes = place_contracuele_rect((xm, ym), w=w, h=h, n_per_side=m)
            self.scene.add_holes(self._tag(holes, SP_CC, "contracuele"))
            self.done_cc = True
            self.draw()
            self._render_step_panel()
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
            w = float(self.cc_rect_w.get()); h = float(self.cc_rect_h.get()); m = int(self.cc_rect_n.get())
            holes = place_contracuele_rect((xm, ym), w=w, h=h, n_per_side=m)

        self.scene.add_holes(self._tag(holes, SP_CC, "contracuele"))
        self.done_cc = True
        self.draw()
        self._render_step_panel()

    def on_drag(self, ev):
        """Arrastra manillas de arco (C/R), luego puntos libres del arco, o perforaciones."""
        # 1) Manilla de ARCO (C/R)
        if self._drag_arc_idx is not None and self.edit_arc.get() and self.arc_handles:
            xm, ym = c2w(ev.x, ev.y)
            if self.snap_grid.get():
                gm = max(0.01, float(self.grid_m.get()))
                xm = round(xm / gm) * gm
                ym = round(ym / gm) * gm

            role = self.arc_handles[self._drag_arc_idx]["role"]
            roles = {h["role"]: (h["x"], h["y"]) for h in self.arc_handles}
            Cx = roles.get("C", (xm, ym))[0]

            if role == "R":
                # Mantener arco centrado: forzar X de R al X del centro C
                self.arc_handles[self._drag_arc_idx]["x"] = Cx
                self.arc_handles[self._drag_arc_idx]["y"] = ym
            else:  # 'C'
                self.arc_handles[self._drag_arc_idx]["x"] = xm
                self.arc_handles[self._drag_arc_idx]["y"] = ym

            self._rebuild_drift_from_arc()
            self.draw()
            return

        # 2) Punto libre sobre el arco
        if self._drag_free_idx is not None and self.edit_free.get() and self.drift_poly:
            xm, ym = c2w(ev.x, ev.y)
            if self.snap_grid.get():
                gm = max(0.01, float(self.grid_m.get()))
                xm = round(xm / gm) * gm
                ym = round(ym / gm) * gm

            i = self.free_handles[self._drag_free_idx]["i"]
            # Restringe el movimiento al rango del arco (opcional pero recomendado)
            if self._arc_span and (self._arc_span[0] <= i <= self._arc_span[1]):
                self.drift_poly[i] = (xm, ym)
                if self.scene.drifts:
                    self.scene.drifts[-1] = list(self.drift_poly)
                self.draw()
            return

        # 3) Arrastre de perforación seleccionada
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

        # Arrastre de handle libre (free handle)
        if self._drag_free_idx is not None and self.drift_poly and self.free_handles:
            gm = max(0.01, float(self.grid_m.get())) if self.snap_grid.get() else 0.0
            xm, ym = c2w(ev.x, ev.y)
            if self.snap_grid.get():
                xm = round(xm / gm) * gm
                ym = round(ym / gm) * gm

            j = self._drag_free_idx
            i = self.free_handles[j]["i"]
            if 0 <= i < len(self.drift_poly):
                self.drift_poly[i] = (xm, ym)
                if getattr(self.scene, "drifts", []):
                    self.scene.drifts[-1] = list(self.drift_poly)
                self.draw()
            return


    def on_release(self, ev):
        """Termina cualquier arrastre activo (perforación, manilla de arco o punto libre)."""
        self.dragging_idx = None     # ya no arrastro perforación
        self._drag_arc_idx = None    # ya no arrastro manilla C/R
        self._drag_free_idx = None   # ya no arrastro punto libre del arco

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
        d  = float(self.d_var.get())
        sx = float(self.sx.get())
        sy = float(self.sy.get())
        rot= float(self.rot.get())
        vy = float(self.vy.get())

        if name == "Sarrois":
            holes = cuele_sarrois_geom(center=(xm,ym), d=d, scale_x=sx, scale_y=sy, rot_deg=rot)
            apply_series_sarrois(holes, d=d)
        elif name == "Sueco":
            holes = cuele_sueco_geom(center=(xm,ym), d=d, scale_x=sx, scale_y=sy, rot_deg=rot)
            apply_series_sueco(holes, d=d)
        elif name == "Coromant":
            v  = 0.5*d; ax = 1.2*d; ay = 1.2*d
            holes = cuele_coromant_geom(center=(xm,ym), v=v, ax=ax, ay=ay, skew=0.4*d, spread=1.4,
                                        scale_x=sx, scale_y=sy, rot_deg=rot)
            apply_series_coromant(holes, v=v, ax=ax, ay=ay, skew=0.4*d)
        elif name == "Cuña 2x3":
            holes = cuele_cuna_geom(center=(xm,ym), d=d, variante="2x3", sep_cols_factor=2.0,
                                    scale_x=sx, scale_y=sy, rot_deg=rot)
            apply_series_cuna(holes, variante="2x3", d=d)
        elif name == "Cuña zigzag":
            holes = cuele_cuna_geom(center=(xm,ym), d=d, variante="zigzag",
                                    scale_x=sx, scale_y=sy, rot_deg=rot)
            apply_series_cuna(holes, variante="zigzag", d=d)
        elif name == "Abanico":
            holes = cuele_abanico_geom(center=(xm,ym), d=d, dx_factor=0.5,
                                       scale_x=sx, scale_y=sy, rot_deg=rot)
            apply_series_abanico(holes, d=d)
        elif name == "Bethune":
            holes = cuele_bethune_geom(center=(xm,ym), d=d, dx_factor=1.2,
                                       y_levels=(1.6,1.4,1.2,1.0,0.9),
                                       invert_y=True, vy_factor=vy,
                                       scale_x=sx, scale_y=sy, rot_deg=rot)
            apply_series_bethune(holes, d=d, y_levels=(1.6,1.4,1.2,1.0,0.9),
                                 invert_y=True, vy_factor=vy)
        elif name == "Cuatro secciones":
            holes = cuele_cuatro_secciones_geom(center=(xm,ym), D=d, D2=d,
                                                k2=1.5, k3=1.5, k4=1.5,
                                                add_mids_S4=True,
                                                scale_x=sx, scale_y=sy, rot_deg=rot)
            B1=1.5*d; B2=1.5*B1; B3=1.5*B2; B4=1.5*B3
            A1=B1; A2=B1+B2; A3=B1+B2+B3; A4=B1+B2+B3+B4
            apply_series_cuatro_secciones(holes, A1,A2,A3,A4, add_mids_S4=True)
        else:
            holes = []

        return holes

    def _do_zap(self):
        """Calcula y agrega perforaciones de zapateras sobre la base."""
        if not self.drift_poly:
            messagebox.showwarning("Geometría", "Primero inserta la geometría (Paso 1).")
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
            messagebox.showwarning("Geometría", "Primero inserta la geometría (Paso 1).")
            return

        n = int(self.n_caja.get())
        holes = place_cajas(
            self.drift_poly, n,
            wall_top_y=self.wall_top_y,
            wall_x_left=self.wall_x_left,
            wall_x_right=self.wall_x_right,
            top_clear_m=0.05, bottom_clear_m=0.05
        )
        if not holes:
            messagebox.showinfo("Cajas", "Esta geometría no tiene paredes verticales (p. ej., Semicircular).")
            return

        self.scene.add_holes(self._tag(holes, SP_CAJAS, "caja"))
        self.done_cajas = True
        self.draw()
        self.btn_next.configure(state="normal")


    def _do_corona(self):
        """Calcula y agrega perforaciones de corona en el arco superior."""
        if not self.drift_poly:
            messagebox.showwarning("Geometría", "Primero inserta la geometría (Paso 1).")
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
            messagebox.showwarning("Geometría", "Primero inserta la geometría (Paso 1).")
            return
        nx = int(self.aux_nx.get()); ny = int(self.aux_ny.get())
        holes = place_aux_grid(self.drift_poly, nx, ny)
        self.scene.add_holes(self._tag(holes, SP_AUX, "aux"))
        self.done_aux = True
        self.draw()
        self.btn_next.configure(state="normal")
   

    def _clear_step(self, step_to_clear):
        """Borra el contenido de un paso. Si es geometría, resetea todo el flujo."""
        if step_to_clear == SP_GEOM:
            self.scene = Scene()
            self.drift_poly = []
            self.geom_index = None
            self.step = SP_GEOM
            self.done_geom = self.done_zap = self.done_cajas = False
            self.done_corona = self.done_cueles = self.done_cc = self.done_aux = False
            self._render_step_panel()
            self._update_step_label()
            self.draw()
            return

        self.scene.remove_holes_by_step(step_to_clear)

        if step_to_clear == SP_ZAP:    self.done_zap = False
        elif step_to_clear == SP_CAJAS: self.done_cajas = False
        elif step_to_clear == SP_CORONA: self.done_corona = False
        elif step_to_clear == SP_CUELES: self.done_cueles = False
        elif step_to_clear == SP_CC:     self.done_cc = False
        elif step_to_clear == SP_AUX:    self.done_aux = False

        self.draw()
        self._render_step_panel()

    def clear_all(self):
        """Borra todo el diseño y vuelve al paso 1."""
        self.scene = Scene()
        self.drift_poly = []
        self.geom_index = None
        self.step = SP_GEOM
        self.done_geom = self.done_zap = self.done_cajas = False
        self.done_corona = self.done_cueles = self.done_cc = self.done_aux = False

        # limpiar edición de arco y puntos libres
        self.arc_handles = []
        self.free_handles = []
        self._drag_arc_idx = None
        self._drag_free_idx = None
        self._arc_base_y = None
        self._arc_span = None

        self._render_step_panel()
        self._update_step_label()
        self.draw()

    def export_json(self):
        """Exporta a JSON los hoyos y galerías en layout_export.json."""
        try:
            import json
            data = {"holes": self.scene.holes, "drifts": self.scene.drifts}
            with open("layout_export.json","w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Export", "Guardado layout_export.json")
        except Exception as e:
            messagebox.showerror("Export", str(e))


if __name__ == "__main__":
    App().mainloop()