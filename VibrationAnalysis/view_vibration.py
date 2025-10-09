# view_vibration.py
<<<<<<< HEAD
from tkinter import messagebox

import customtkinter as ctk


class VibrationAnalysisView(ctk.CTkToplevel):
=======
import customtkinter as ctk
from tkinter import messagebox

class VibrationAnalysisView(ctk.CTkToplevel):
    
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)

    def __init__(self, parent):
        super().__init__(parent)

        # Configuración de la ventana:
<<<<<<< HEAD
        self.title("Vibraciones (Holmberg & Persson)")
        self.after(250, lambda: self.iconbitmap("images/blasting.ico"))
=======
        self.title('Vibraciones (Holmberg & Persson)')
        self.after(250, lambda: self.iconbitmap('images/blasting.ico'))
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)
        self.grab_set()

        # Param store (igual que el original):
        self.params = {}

        # Crear variables y widgets:
        self.create_variables()
        self.create_widgets()
        self.widgets_layout()

    def create_variables(self):
        """Crea la variables del menú de análisis (sin predefinidos)."""
        # Definición de la distribución:
<<<<<<< HEAD
        self.name = ctk.StringVar()
=======
        self.name    = ctk.StringVar()
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)
        self.pattern = ctk.StringVar()
        self.section = ctk.StringVar()  # sin valor por defecto

        # Extensión del plano de evaluación:
        self.xmin = ctk.StringVar()
        self.xmax = ctk.StringVar()
        self.ymin = ctk.StringVar()
        self.ymax = ctk.StringVar()
        self.zmin = ctk.StringVar()
        self.zmax = ctk.StringVar()

        # Parámetros de visualización:
        self.cutoff = ctk.StringVar()
<<<<<<< HEAD
        self.resol = ctk.StringVar()
=======
        self.resol  = ctk.StringVar()
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)
        self.levels = ctk.StringVar()

        # Parámetros de evaluación:
        self.diameter = ctk.StringVar()
<<<<<<< HEAD
        self.density = ctk.StringVar()
        self.K_const = ctk.StringVar()
        self.a_const = ctk.StringVar()

    def create_widgets(self):
        """Crea los widgets del menú de evaluación (sin command=)."""
        list_charges = []  # se llena desde el Controller
        list_sections = ["Transversal", "Longitudinal", "Planta"]

        self.frame_def = ctk.CTkFrame(self, border_width=1, corner_radius=8)
        self.title_def = ctk.CTkLabel(
            self.frame_def, text="Plano de evaluación:", font=ctk.CTkFont(weight="bold")
        )

        self.label_pattern = ctk.CTkLabel(
            self.frame_def, text="Patrón de carga", width=90, anchor="w"
        )
        self.label_section = ctk.CTkLabel(
            self.frame_def, text="Tipo de sección", width=90, anchor="w"
        )

        self.combo_charges = ctk.CTkComboBox(
            self.frame_def,
            values=list_charges,
            variable=self.pattern,
            width=160,
            state="readonly",
        )
        self.combo_section = ctk.CTkComboBox(
            self.frame_def,
            values=list_sections,
            variable=self.section,
            width=160,
            state="readonly",
        )

        # Pestañas
        self.param_tabs = ctk.CTkTabview(
            self, height=165, border_width=1, corner_radius=8
        )
        tab_exts = self.param_tabs.add("Extensión")
        tab_view = self.param_tabs.add("Visualización")
        tab_pars = self.param_tabs.add("Parámetros")

        # Extensión
        self.label_min = ctk.CTkLabel(tab_exts, text="Mínimo")
        self.label_max = ctk.CTkLabel(tab_exts, text="Máximo")
        self.label_xcoord = ctk.CTkLabel(
            tab_exts, text="Coordenada x", width=90, anchor="w"
        )
        self.label_ycoord = ctk.CTkLabel(
            tab_exts, text="Coordenada y", width=90, anchor="w"
        )
        self.label_zcoord = ctk.CTkLabel(
            tab_exts, text="Coordenada z", width=90, anchor="w"
        )

        _limit_opts = {"width": 90, "justify": "right"}
=======
        self.density  = ctk.StringVar()
        self.K_const  = ctk.StringVar()
        self.a_const  = ctk.StringVar()

    def create_widgets(self):
        """Crea los widgets del menú de evaluación (sin command=)."""
        list_charges  = []  # se llena desde el Controller
        list_sections = ['Transversal', 'Longitudinal', 'Planta']

        self.frame_def = ctk.CTkFrame(self, border_width=1, corner_radius=8)
        self.title_def = ctk.CTkLabel(self.frame_def, text='Plano de evaluación:', font=ctk.CTkFont(weight='bold'))

        self.label_pattern = ctk.CTkLabel(self.frame_def, text='Patrón de carga', width=90, anchor='w')
        self.label_section = ctk.CTkLabel(self.frame_def, text='Tipo de sección', width=90, anchor='w')

        self.combo_charges = ctk.CTkComboBox(self.frame_def, values=list_charges, variable=self.pattern,
                                             width=160, state='readonly')
        self.combo_section = ctk.CTkComboBox(self.frame_def, values=list_sections, variable=self.section,
                                             width=160, state='readonly')

        # Pestañas
        self.param_tabs = ctk.CTkTabview(self, height=165, border_width=1, corner_radius=8)
        tab_exts = self.param_tabs.add('Extensión')
        tab_view = self.param_tabs.add('Visualización')
        tab_pars = self.param_tabs.add('Parámetros')

        # Extensión
        self.label_min    = ctk.CTkLabel(tab_exts, text='Mínimo')
        self.label_max    = ctk.CTkLabel(tab_exts, text='Máximo')
        self.label_xcoord = ctk.CTkLabel(tab_exts, text='Coordenada x', width=90, anchor='w')
        self.label_ycoord = ctk.CTkLabel(tab_exts, text='Coordenada y', width=90, anchor='w')
        self.label_zcoord = ctk.CTkLabel(tab_exts, text='Coordenada z', width=90, anchor='w')

        _limit_opts = {'width': 90, 'justify': 'right'}
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)
        self.entry_xmin = ctk.CTkEntry(tab_exts, textvariable=self.xmin, **_limit_opts)
        self.entry_xmax = ctk.CTkEntry(tab_exts, textvariable=self.xmax, **_limit_opts)
        self.entry_ymin = ctk.CTkEntry(tab_exts, textvariable=self.ymin, **_limit_opts)
        self.entry_ymax = ctk.CTkEntry(tab_exts, textvariable=self.ymax, **_limit_opts)
        self.entry_zmin = ctk.CTkEntry(tab_exts, textvariable=self.zmin, **_limit_opts)
        self.entry_zmax = ctk.CTkEntry(tab_exts, textvariable=self.zmax, **_limit_opts)

        # trazas para fijar el plano
<<<<<<< HEAD
        self.xmin.trace_add("write", self.set_limits)
        self.ymin.trace_add("write", self.set_limits)
        self.zmin.trace_add("write", self.set_limits)

        # Visualización
        self.label_cutoff = ctk.CTkLabel(
            tab_view, text="Energía máx.", width=90, anchor="w"
        )
        self.label_resol = ctk.CTkLabel(
            tab_view, text="Resolución", width=90, anchor="w"
        )
        self.label_levels = ctk.CTkLabel(
            tab_view, text="No. de niveles", width=90, anchor="w"
        )

        _entry_opts = {"width": 120, "justify": "right"}
        self.entry_cutoff = ctk.CTkEntry(
            tab_view, textvariable=self.cutoff, **_entry_opts
        )
        self.entry_resol = ctk.CTkEntry(
            tab_view, textvariable=self.resol, **_entry_opts
        )
        self.entry_levels = ctk.CTkEntry(
            tab_view, textvariable=self.levels, **_entry_opts
        )

        self.units_cutoff = ctk.CTkLabel(tab_view, text="mm/s", anchor="w")
        self.units_resol = ctk.CTkLabel(tab_view, text="pts/eje", anchor="w")

        # Parámetros de evaluación
        self.label_diameter = ctk.CTkLabel(
            tab_pars, text="Diámetro carga", width=90, anchor="w"
        )
        self.label_density = ctk.CTkLabel(
            tab_pars, text="Dens. explosivo", width=90, anchor="w"
        )
        self.label_const_K = ctk.CTkLabel(
            tab_pars, text="Constante (K)", width=90, anchor="w"
        )
        self.label_const_a = ctk.CTkLabel(
            tab_pars, text="Exponente (α)", width=90, anchor="w"
        )

        self.entry_diameter = ctk.CTkEntry(
            tab_pars, textvariable=self.diameter, width=120, justify="right"
        )
        self.entry_density = ctk.CTkEntry(
            tab_pars, textvariable=self.density, width=120, justify="right"
        )
        self.entry_const_K = ctk.CTkEntry(
            tab_pars, textvariable=self.K_const, width=120, justify="right"
        )
        self.entry_const_a = ctk.CTkEntry(
            tab_pars, textvariable=self.a_const, width=120, justify="right"
        )

        self.units_diameter = ctk.CTkLabel(tab_pars, text="mm", anchor="w")
        self.units_density = ctk.CTkLabel(tab_pars, text="g/cm³", anchor="w")
        self.units_K = ctk.CTkLabel(tab_pars, text="mm/s", anchor="w")

        # Botones (sin command=; el Controller los conecta)
        self.frame_buttons = ctk.CTkFrame(self, fg_color="transparent")
        self.button_plot = ctk.CTkButton(self.frame_buttons, text="Graficar", width=60)
        self.button_save = ctk.CTkButton(self.frame_buttons, text="Guardar", width=60)

    def widgets_layout(self):
        """Coloca los widgets (copia fiel)."""
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
        _combo_grid = {"column": 1, "sticky": "w"}
        _entry_grid = {"column": 1, "sticky": "w"}
        _units_grid = {"column": 3, "sticky": "w", "padx": (5, 0)}
        _button_pack = {"side": "left", "padx": 5, "pady": 10}
=======
        self.xmin.trace_add('write', self.set_limits)
        self.ymin.trace_add('write', self.set_limits)
        self.zmin.trace_add('write', self.set_limits)

        # Visualización
        self.label_cutoff = ctk.CTkLabel(tab_view, text='Energía máx.',  width=90, anchor='w')
        self.label_resol  = ctk.CTkLabel(tab_view, text='Resolución',    width=90, anchor='w')
        self.label_levels = ctk.CTkLabel(tab_view, text='No. de niveles', width=90, anchor='w')

        _entry_opts = {'width': 120, 'justify': 'right'}
        self.entry_cutoff = ctk.CTkEntry(tab_view, textvariable=self.cutoff, **_entry_opts)
        self.entry_resol  = ctk.CTkEntry(tab_view, textvariable=self.resol,  **_entry_opts)
        self.entry_levels = ctk.CTkEntry(tab_view, textvariable=self.levels, **_entry_opts)

        self.units_cutoff = ctk.CTkLabel(tab_view, text='mm/s',  anchor='w')
        self.units_resol  = ctk.CTkLabel(tab_view, text='pts/eje', anchor='w')

        # Parámetros de evaluación
        self.label_diameter = ctk.CTkLabel(tab_pars, text='Diámetro carga',  width=90, anchor='w')
        self.label_density  = ctk.CTkLabel(tab_pars, text='Dens. explosivo', width=90, anchor='w')
        self.label_const_K  = ctk.CTkLabel(tab_pars, text='Constante (K)',   width=90, anchor='w')
        self.label_const_a  = ctk.CTkLabel(tab_pars, text='Exponente (α)',   width=90, anchor='w')

        self.entry_diameter = ctk.CTkEntry(tab_pars, textvariable=self.diameter, width=120, justify='right')
        self.entry_density  = ctk.CTkEntry(tab_pars, textvariable=self.density,  width=120, justify='right')
        self.entry_const_K  = ctk.CTkEntry(tab_pars, textvariable=self.K_const,  width=120, justify='right')
        self.entry_const_a  = ctk.CTkEntry(tab_pars, textvariable=self.a_const,  width=120, justify='right')

        self.units_diameter = ctk.CTkLabel(tab_pars, text='mm',    anchor='w')
        self.units_density  = ctk.CTkLabel(tab_pars, text='g/cm³', anchor='w')
        self.units_K        = ctk.CTkLabel(tab_pars, text='mm/s',  anchor='w')

        # Botones (sin command=; el Controller los conecta)
        self.frame_buttons = ctk.CTkFrame(self, fg_color='transparent')
        self.button_plot = ctk.CTkButton(self.frame_buttons, text='Graficar', width=60)
        self.button_save = ctk.CTkButton(self.frame_buttons, text='Guardar',  width=60)

    def widgets_layout(self):
        """Coloca los widgets (copia fiel)."""
        _frame_pack = {'fill': 'x', 'padx': 5, 'pady': 3, 'ipadx': 5, 'ipady': 5}
        _title_grid = {'row': 0, 'column': 0, 'columnspan': 2, 'padx': 10, 'pady': 3, 'sticky': 'w'}
        _label_grid = {'column': 0, 'sticky': 'w', 'padx': 10}
        _combo_grid = {'column': 1, 'sticky': 'w'}
        _entry_grid = {'column': 1, 'sticky': 'w'}
        _units_grid = {'column': 3, 'sticky': 'w', 'padx': (5,0)}
        _button_pack = {'side': 'left', 'padx': 5, 'pady': 10}
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)

        self.frame_def.pack(**_frame_pack)
        self.title_def.grid(**_title_grid)
        self.label_pattern.grid(row=1, **_label_grid)
        self.label_section.grid(row=2, **_label_grid)
        self.combo_charges.grid(row=1, **_combo_grid)
        self.combo_section.grid(row=2, **_combo_grid)

<<<<<<< HEAD
        _frame_pack = {"fill": "x", "padx": 5, "pady": 3}
        _label_grid = {"column": 0, "sticky": "w", "padx": (2, 10)}
=======
        _frame_pack = {'fill': 'x', 'padx': 5, 'pady': 3}
        _label_grid = {'column': 0, 'sticky': 'w', 'padx': (2,10)}
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)
        self.param_tabs.pack(**_frame_pack)

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

        self.label_cutoff.grid(row=0, **_label_grid)
<<<<<<< HEAD
        self.label_resol.grid(row=1, **_label_grid)
        self.label_levels.grid(row=2, **_label_grid)
        self.entry_cutoff.grid(row=0, **_entry_grid)
        self.entry_resol.grid(row=1, **_entry_grid)
        self.entry_levels.grid(row=2, **_entry_grid)
        self.units_cutoff.grid(row=0, **_units_grid)
        self.units_resol.grid(row=1, **_units_grid)

        self.label_diameter.grid(row=0, **_label_grid)
        self.label_density.grid(row=1, **_label_grid)
        self.label_const_K.grid(row=2, **_label_grid)
        self.label_const_a.grid(row=3, **_label_grid)
        self.entry_diameter.grid(row=0, **_entry_grid)
        self.entry_density.grid(row=1, **_entry_grid)
        self.entry_const_K.grid(row=2, **_entry_grid)
        self.entry_const_a.grid(row=3, **_entry_grid)
        self.units_diameter.grid(row=0, **_units_grid)
        self.units_density.grid(row=1, **_units_grid)
        self.units_K.grid(row=2, **_units_grid)
=======
        self.label_resol .grid(row=1, **_label_grid)
        self.label_levels.grid(row=2, **_label_grid)
        self.entry_cutoff.grid(row=0, **_entry_grid)
        self.entry_resol .grid(row=1, **_entry_grid)
        self.entry_levels.grid(row=2, **_entry_grid)
        self.units_cutoff.grid(row=0, **_units_grid)
        self.units_resol .grid(row=1, **_units_grid)

        self.label_diameter.grid(row=0, **_label_grid)
        self.label_density .grid(row=1, **_label_grid)
        self.label_const_K .grid(row=2, **_label_grid)
        self.label_const_a .grid(row=3, **_label_grid)
        self.entry_diameter.grid(row=0, **_entry_grid)
        self.entry_density .grid(row=1, **_entry_grid)
        self.entry_const_K .grid(row=2, **_entry_grid)
        self.entry_const_a .grid(row=3, **_entry_grid)
        self.units_diameter.grid(row=0, **_units_grid)
        self.units_density .grid(row=1, **_units_grid)
        self.units_K       .grid(row=2, **_units_grid)
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)

        self.frame_buttons.pack()
        self.button_plot.pack(**_button_pack)
        self.button_save.pack(**_button_pack)

    # --- exactamente la utilidad de fijar plano ---
    def set_limits(self, *kwargs):
        """Establece un único valor para la coordenada del plano de evaluación"""
<<<<<<< HEAD
        if self.section.get() == "Longitudinal":
            xmin = self.xmin.get()
            self.xmax.set(xmin)
        elif self.section.get() == "Planta":
            ymin = self.ymin.get()
            self.ymax.set(ymin)
        elif self.section.get() == "Transversal":
=======
        if self.section.get() == 'Longitudinal':
            xmin = self.xmin.get()
            self.xmax.set(xmin)
        elif self.section.get() == 'Planta':
            ymin = self.ymin.get()
            self.ymax.set(ymin)
        elif self.section.get() == 'Transversal':
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)
            zmin = self.zmin.get()
            self.zmax.set(zmin)

    # --- validación, igual que el original pero sin 'self.variables' inexistente ---
    def valid_params(self):
        """Valida parámetros y los guarda en self.params."""
        pattern_name = self.pattern.get()
<<<<<<< HEAD
        if pattern_name == "":
            messagebox.showinfo(
                "Análisis de Vibraciones",
                "Seleccione un patrón de carga para calcular su distribución de vibraciones.",
            )
            return False
        try:
            xmin = float(self.xmin.get())
            xmax = float(self.xmax.get())
            ymin = float(self.ymin.get())
            ymax = float(self.ymax.get())
            zmin = float(self.zmin.get())
            zmax = float(self.zmax.get())

            cutoff = float(self.cutoff.get())
            resol = int(self.resol.get())
            levels = int(self.levels.get())

            diameter = float(self.diameter.get())
            density = float(self.density.get())
            const_K = float(self.K_const.get())
            const_a = float(self.a_const.get())
        except Exception:
            messagebox.showerror(
                "Análisis de Vibraciones",
                "Complete todos los campos de entrada con valores numéricos.",
            )
            return False

        if xmin > xmax:
            messagebox.showerror(
                "Análisis de Vibraciones",
                "El límite inferior de X no puede ser mayor que el superior.",
            )
            return False
        if ymin > ymax:
            messagebox.showerror(
                "Análisis de Vibraciones",
                "El límite inferior de Y no puede ser mayor que el superior.",
            )
            return False
        if zmin > zmax:
            messagebox.showerror(
                "Análisis de Vibraciones",
                "El límite inferior de Z no puede ser mayor que el superior.",
            )
            return False

        if cutoff <= 0:
            messagebox.showerror(
                "Análisis de Vibraciones",
                "El máximo de la vibración no puede ser negativo.",
            )
=======
        if pattern_name == '':
            messagebox.showinfo('Análisis de Vibraciones',
                                'Seleccione un patrón de carga para calcular su distribución de vibraciones.')
            return False
        try:
            xmin = float(self.xmin.get());  xmax = float(self.xmax.get())
            ymin = float(self.ymin.get());  ymax = float(self.ymax.get())
            zmin = float(self.zmin.get());  zmax = float(self.zmax.get())

            cutoff = float(self.cutoff.get())
            resol  = int(self.resol.get())
            levels = int(self.levels.get())

            diameter = float(self.diameter.get())
            density  = float(self.density.get())
            const_K  = float(self.K_const.get())
            const_a  = float(self.a_const.get())
        except Exception:
            messagebox.showerror('Análisis de Vibraciones', 'Complete todos los campos de entrada con valores numéricos.')
            return False

        if xmin > xmax:
            messagebox.showerror('Análisis de Vibraciones', 'El límite inferior de X no puede ser mayor que el superior.')
            return False
        if ymin > ymax:
            messagebox.showerror('Análisis de Vibraciones', 'El límite inferior de Y no puede ser mayor que el superior.')
            return False
        if zmin > zmax:
            messagebox.showerror('Análisis de Vibraciones', 'El límite inferior de Z no puede ser mayor que el superior.')
            return False

        if cutoff <= 0:
            messagebox.showerror('Análisis de Vibraciones', 'El máximo de la vibración no puede ser negativo.')
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)
            return False

        if resol < 2:
            resol = 2
<<<<<<< HEAD
            self.resol.set("2")
        if levels < 1:
            levels = 1
            self.levels.set("1")

        if diameter <= 0:
            messagebox.showerror(
                "Análisis de Vibraciones", "El diámetro de carga debe ser > 0."
            )
            return False
        if density <= 0:
            messagebox.showerror(
                "Análisis de Vibraciones", "La densidad del explosivo debe ser > 0."
            )
            return False

        self.params.update(
            {
                "xmin": xmin,
                "xmax": xmax,
                "ymin": ymin,
                "ymax": ymax,
                "zmin": zmin,
                "zmax": zmax,
                "cutoff": cutoff,
                "resol": resol,
                "levels": levels,
                "diameter": diameter,
                "density": density,
                "const_K": const_K,
                "const_a": const_a,
            }
        )
=======
            self.resol.set('2')
        if levels < 1:
            levels = 1
            self.levels.set('1')

        if diameter <= 0:
            messagebox.showerror('Análisis de Vibraciones', 'El diámetro de carga debe ser > 0.')
            return False
        if density <= 0:
            messagebox.showerror('Análisis de Vibraciones', 'La densidad del explosivo debe ser > 0.')
            return False

        self.params.update({
            'xmin': xmin, 'xmax': xmax, 'ymin': ymin, 'ymax': ymax, 'zmin': zmin, 'zmax': zmax,
            'cutoff': cutoff, 'resol': resol, 'levels': levels,
            'diameter': diameter, 'density': density, 'const_K': const_K, 'const_a': const_a
        })
>>>>>>> d67434d (refactor(estructura): reorganiza carpetas y normaliza nombres)
        return True
