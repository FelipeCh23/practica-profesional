from tkinter import messagebox

import customtkinter as ctk


class EnergyAnalysisView(ctk.CTkToplevel):
    """
    VIEW pura (CTkToplevel). Solo UI.
    - Copia literal de create_variables / create_widgets / widgets_layout / set_limits / activate_max
      de tu EnergyAnalysis original, pero:
        * SIN valores por defecto (vacío/"")
        * SIN command=... pegado (el Controller los conecta)
    - El Controller accede a los StringVar/BooleanVar y a los widgets.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Análisis de Energía (Kleine)")
        self.grab_set()
        # self.after(250, lambda: self.iconbitmap('images/blasting.ico'))  # opcional

        # Expuestos (el controller les pondrá values):
        self.charges = (
            {}
        )  # (solo para poblar combo values; el Controller mantiene los datos)
        self.params = {}  # espejo igual que en la clase original (lo usa Controller)

        self.create_variables()
        self.create_widgets()
        self.widgets_layout()

    def create_variables(self):
        """Crea las variables del menú de análisis (sin valores por defecto)."""
        # Definición del plano de evaluación:
        self.pattern = ctk.StringVar(
            value=""
        )  # patrón seleccionado ("" = PatronDemo vacío)
        self.section = ctk.StringVar(value="")  # 'Transversal'|'Longitudinal'|'Planta'
        self.type = ctk.StringVar(value="")  # 'Volumen'|'Tonelaje'

        # Extensión del plano de evaluación:
        self.xmin = ctk.StringVar(value="")
        self.xmax = ctk.StringVar(value="")
        self.ymin = ctk.StringVar(value="")
        self.ymax = ctk.StringVar(value="")
        self.zmin = ctk.StringVar(value="")
        self.zmax = ctk.StringVar(value="")

        # Parámetros de visualización:
        self.cutoff = ctk.StringVar(value="")
        self.resol = ctk.StringVar(value="")
        self.levels = ctk.StringVar(value="")

        # Parámetros de evaluación:
        self.rock_dens = ctk.StringVar(value="")
        self.expl_dens = ctk.StringVar(value="")
        self.diameter = ctk.StringVar(value="")

        # Parámetros de visualización:
        self.tridimensional = ctk.BooleanVar(value=False)

    def create_widgets(self):
        """Crear los widgets del menú de evaluación (sin commands; los pone el Controller)."""
        _frame_opts = {"border_width": 1, "corner_radius": 8}
        _title_font = ctk.CTkFont(weight="bold")
        _label_opts = {"width": 90, "anchor": "w"}
        _entry_opts = {"width": 120, "justify": "right"}
        _combo_opts = {"width": 160, "state": "readonly"}
        _units_opts = {"anchor": "w"}
        _button_opts = {"width": 50}

        # NOTA: las listas (values) las setea el Controller
        self.frame_def = ctk.CTkFrame(self, **_frame_opts)
        self.title_def = ctk.CTkLabel(
            self.frame_def, text="Plano de evaluación:", font=_title_font
        )

        self.label_charges = ctk.CTkLabel(
            self.frame_def, text="Patrón de carga", **_label_opts
        )
        self.label_section = ctk.CTkLabel(
            self.frame_def, text="Tipo de sección", **_label_opts
        )
        self.label_type = ctk.CTkLabel(
            self.frame_def, text="Uds. del factor", **_label_opts
        )

        self.combo_charges = ctk.CTkComboBox(
            self.frame_def, values=[], variable=self.pattern, **_combo_opts
        )
        self.combo_section = ctk.CTkComboBox(
            self.frame_def,
            values=["Transversal", "Longitudinal", "Planta"],
            variable=self.section,
            **_combo_opts
        )
        self.combo_type = ctk.CTkComboBox(
            self.frame_def,
            values=["Volumen", "Tonelaje"],
            variable=self.type,
            **_combo_opts
        )

        self.check_3d = ctk.CTkCheckBox(
            self.frame_def, text="Vista tridimensional", variable=self.tridimensional
        )

        # Pestañas:
        self.param_tabs = ctk.CTkTabview(self, height=165, **_frame_opts)
        tab_exts = self.param_tabs.add("Extensión")
        tab_view = self.param_tabs.add("Visualización")
        tab_pars = self.param_tabs.add("Parámetros")

        # Extensión:
        self.label_min = ctk.CTkLabel(tab_exts, text="Mínimo")
        self.label_max = ctk.CTkLabel(tab_exts, text="Máximo")
        self.label_xcoord = ctk.CTkLabel(tab_exts, text="Coordenada x", **_label_opts)
        self.label_ycoord = ctk.CTkLabel(tab_exts, text="Coordenada y", **_label_opts)
        self.label_zcoord = ctk.CTkLabel(tab_exts, text="Coordenada z", **_label_opts)

        _limits_opts = {"width": 90, "justify": "right"}
        self.entry_xmin = ctk.CTkEntry(tab_exts, textvariable=self.xmin, **_limits_opts)
        self.entry_xmax = ctk.CTkEntry(tab_exts, textvariable=self.xmax, **_limits_opts)
        self.entry_ymin = ctk.CTkEntry(tab_exts, textvariable=self.ymin, **_limits_opts)
        self.entry_ymax = ctk.CTkEntry(tab_exts, textvariable=self.ymax, **_limits_opts)
        self.entry_zmin = ctk.CTkEntry(tab_exts, textvariable=self.zmin, **_limits_opts)
        self.entry_zmax = ctk.CTkEntry(tab_exts, textvariable=self.zmax, **_limits_opts)

        # Visualización:
        self.label_cutoff = ctk.CTkLabel(tab_view, text="Energía máx.", **_label_opts)
        self.label_resol = ctk.CTkLabel(tab_view, text="Resolución", **_label_opts)
        self.label_levels = ctk.CTkLabel(tab_view, text="No. de niveles", **_label_opts)

        self.entry_cutoff = ctk.CTkEntry(
            tab_view, textvariable=self.cutoff, **_entry_opts
        )
        self.entry_resol = ctk.CTkEntry(
            tab_view, textvariable=self.resol, **_entry_opts
        )
        self.entry_levels = ctk.CTkEntry(
            tab_view, textvariable=self.levels, **_entry_opts
        )

        self.units_cutoff = ctk.CTkLabel(tab_view, text="kg/m³", **_units_opts)
        self.units_resol = ctk.CTkLabel(tab_view, text="pts/eje", **_units_opts)

        # Parámetros:
        self.label_rock_dens = ctk.CTkLabel(tab_pars, text="Dens. roca", **_label_opts)
        self.label_expl_dens = ctk.CTkLabel(
            tab_pars, text="Dens. explosivo", **_label_opts
        )
        self.label_chrg_diam = ctk.CTkLabel(
            tab_pars, text="Diámetro carga", **_label_opts
        )

        self.entry_rock_dens = ctk.CTkEntry(
            tab_pars, textvariable=self.rock_dens, **_entry_opts
        )
        self.entry_expl_dens = ctk.CTkEntry(
            tab_pars, textvariable=self.expl_dens, **_entry_opts
        )
        self.entry_chrg_diam = ctk.CTkEntry(
            tab_pars, textvariable=self.diameter, **_entry_opts
        )

        self.units_rock_dens = ctk.CTkLabel(tab_pars, text="g/cm³", **_units_opts)
        self.units_expl_dens = ctk.CTkLabel(tab_pars, text="g/cm³", **_units_opts)
        self.units_chrg_diam = ctk.CTkLabel(tab_pars, text="mm", **_units_opts)

        # Botones:
        self.frame_buttons = ctk.CTkFrame(self, fg_color="transparent")
        self.button_plot = ctk.CTkButton(self.frame_buttons, text="Graficar")
        self.button_save = ctk.CTkButton(self.frame_buttons, text="Guardar")

        # traces que usa tu set_limits:
        self.xmin.trace_add("write", self.set_limits)
        self.ymin.trace_add("write", self.set_limits)
        self.zmin.trace_add("write", self.set_limits)

    def widgets_layout(self):
        """Colocar los widgets en el menú de evaluación"""
        _frame_pack = {"fill": "x", "padx": 5, "pady": 3, "ipadx": 5, "ipady": 5}
        _title_grid = {
            "row": 0,
            "column": 0,
            "columnspan": 2,
            "padx": 10,
            "pady": 3,
            "sticky": "w",
        }
        _label_grid = {"column": 0, "sticky": "w", "padx": 10}
        _entry_grid = {"column": 1, "sticky": "w"}
        _units_grid = {"column": 3, "sticky": "w", "padx": (5, 0)}
        _button_pack = {"side": "left", "padx": 5, "pady": 10}

        self.frame_def.pack(**_frame_pack)
        self.title_def.grid(**_title_grid)

        self.label_charges.grid(row=1, **_label_grid)
        self.label_section.grid(row=2, **_label_grid)
        self.label_type.grid(row=3, **_label_grid)

        self.combo_charges.grid(row=1, **_entry_grid)
        self.combo_section.grid(row=2, **_entry_grid)
        self.combo_type.grid(row=3, **_entry_grid)

        self.check_3d.grid(row=4, column=0, columnspan=3, sticky="w", padx=10)

        # Tabs
        _frame_pack = {"fill": "x", "padx": 5, "pady": 0}
        _label_grid = {"column": 0, "sticky": "w", "padx": (2, 10)}
        self.param_tabs.pack(**_frame_pack)

        # Extensión
        self.label_min.grid(row=0, column=1)
        self.label_max.grid(row=0, column=2)
        self.label_xcoord.grid(row=1, **_label_grid)
        self.label_ycoord.grid(row=2, **_label_grid)
        self.label_zcoord.grid(row=3, **_label_grid)

        self.entry_xmin.grid(row=1, column=1)
        self.entry_xmax.grid(row=1, column=2)
        self.entry_ymin.grid(row=2, column=1)
        self.entry_ymax.grid(row=2, column=2)
        self.entry_zmin.grid(row=3, column=1)
        self.entry_zmax.grid(row=3, column=2)

        # Visualización
        self.label_cutoff.grid(row=0, **_label_grid)
        self.label_resol.grid(row=1, **_label_grid)
        self.label_levels.grid(row=2, **_label_grid)

        self.entry_cutoff.grid(row=0, **_entry_grid)
        self.entry_resol.grid(row=1, **_entry_grid)
        self.entry_levels.grid(row=2, **_entry_grid)

        self.units_cutoff.grid(row=0, **_units_grid)
        self.units_resol.grid(row=1, **_units_grid)

        # Parámetros
        self.label_rock_dens.grid(row=1, **_label_grid)
        self.label_expl_dens.grid(row=3, **_label_grid)
        self.label_chrg_diam.grid(row=4, **_label_grid)

        self.entry_rock_dens.grid(row=1, **_entry_grid)
        self.entry_expl_dens.grid(row=3, **_entry_grid)
        self.entry_chrg_diam.grid(row=4, **_entry_grid)

        self.units_rock_dens.grid(row=1, **_units_grid)
        self.units_expl_dens.grid(row=3, **_units_grid)
        self.units_chrg_diam.grid(row=4, **_units_grid)

        # Botones
        self.frame_buttons.pack()
        self.button_plot.pack(**_button_pack)
        self.button_save.pack(**_button_pack)

    # -------- métodos “de view” copiados --------
    def set_limits(self, *args):
        """Actualiza la entrada para la coordenada fija (igual que tu View original)."""
        if self.tridimensional.get():
            return

        if self.section.get() == "Transversal":
            zmin = self.zmin.get()
            self.zmax.set(zmin)
        elif self.section.get() == "Longitudinal":
            xmin = self.xmin.get()
            self.xmax.set(xmin)
        else:
            ymin = self.ymin.get()
            self.ymax.set(ymin)

    def activate_max(self):
        """Activa las entradas tridimensionales (igual que tu View original)."""
        self.entry_xmax.configure(state="normal")
        self.entry_ymax.configure(state="normal")
        self.entry_zmax.configure(state="normal")

    # Helpers para mensajes (para que el Controller no importe messagebox)
    def info(self, title, msg):
        messagebox.showinfo(title, msg)

    def error(self, title, msg):
        messagebox.showerror(title, msg)
