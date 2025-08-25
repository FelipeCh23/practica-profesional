
# view_vibration

# View fiel al código original: ctk.CTkToplevel con las MISMAS defs de la clase.
# Sin lógica de negocio; los command se conectan desde el Controller.

import customtkinter as ctk
from tkinter import messagebox

class VibrationView(ctk.CTkToplevel):
    """Crea una ventana para generar distribuciones de PPV (UI pura)."""

    def __init__(self, parent):
        super().__init__(parent)

        # Config ventana (igual a original)
        self.title('Vibraciones (Holmberg & Persson)')
        try:
            self.after(250, lambda: self.iconbitmap('images/blasting.ico'))
        except Exception:
            pass
        self.grab_set()

        # Estos dicts los inyecta el Controller desde DATA.json via Model
        self.charges = {}
        self.holes   = {}
        self.drifts  = {}
        self.stopes  = {}

        # Guarda params temporales (igual que original)
        self.params = {}

        # Crear variables/widgets (nombres iguales a los del original)
        self.create_variables()
        self.create_widgets()
        self.widgets_layout()

    # ----------------- (copiado del original) -----------------
    def create_variables(self):
        '''Crea la variables del menú de análisis'''

        # Definición de la distribución:
        self.name    = ctk.StringVar()
        self.pattern = ctk.StringVar()
        self.section = ctk.StringVar(value='Transversal')

        # Extensión del plano de evaluación:
        self.xmin = ctk.StringVar(value='0.0')
        self.xmax = ctk.StringVar(value='0.0')
        self.ymin = ctk.StringVar(value='0.0')
        self.ymax = ctk.StringVar(value='0.0')
        self.zmin = ctk.StringVar(value='0.0')
        self.zmax = ctk.StringVar(value='0.0')
        
        # Parámetros de visualización:
        self.cutoff = ctk.StringVar(value='2000')
        self.resol  = ctk.StringVar(value='200')
        self.levels = ctk.StringVar(value='20')

        # Parámetros de evaluación:
        self.diameter = ctk.StringVar(value='0.0')
        self.density  = ctk.StringVar(value='0.0')
        self.K_const  = ctk.StringVar(value='400')
        self.a_const  = ctk.StringVar(value='0.9')

    def create_widgets(self):
        '''Crea los widgets del menú de evaluación'''
        list_charges  = list(self.charges.keys())  # el Controller los carga
        list_sections = ['Transversal', 'Longitudinal', 'Planta']

        self.frame_def = ctk.CTkFrame(self, border_width=1, corner_radius=8)
        self.title_def = ctk.CTkLabel(self.frame_def, text='Plano de evaluación:', font=ctk.CTkFont(weight='bold'))
        
        self.label_pattern = ctk.CTkLabel(self.frame_def, text='Patrón de carga', width=90, anchor='w')
        self.label_section = ctk.CTkLabel(self.frame_def, text='Tipo de sección', width=90, anchor='w')

        self.combo_charges = ctk.CTkComboBox(self.frame_def, values=list_charges , variable=self.pattern, width=160, state='readonly')
        self.combo_section = ctk.CTkComboBox(self.frame_def, values=list_sections, variable=self.section, width=160, state='readonly')

        # Los command se asignan desde Controller (para mantener MVC)
        # self.combo_charges.configure(command=self.update_values)
        # self.combo_section.configure(command=self.update_values)

        self.param_tabs = ctk.CTkTabview(self, height=165, border_width=1, corner_radius=8)
        tab_exts = self.param_tabs.add('Extensión')
        tab_view = self.param_tabs.add('Visualización')
        tab_pars = self.param_tabs.add('Parámetros')

        self.label_min = ctk.CTkLabel(tab_exts, text='Mínimo')
        self.label_max = ctk.CTkLabel(tab_exts, text='Máximo')
        self.label_xcoord = ctk.CTkLabel(tab_exts, text='Coordenada x', width=90, anchor='w')
        self.label_ycoord = ctk.CTkLabel(tab_exts, text='Coordenada y', width=90, anchor='w')
        self.label_zcoord = ctk.CTkLabel(tab_exts, text='Coordenada z', width=90, anchor='w')

        _limit_opts = {'width': 90, 'justify': 'right'}
        self.entry_xmin = ctk.CTkEntry(tab_exts, textvariable=self.xmin, **_limit_opts)
        self.entry_xmax = ctk.CTkEntry(tab_exts, textvariable=self.xmax, **_limit_opts)
        self.entry_ymin = ctk.CTkEntry(tab_exts, textvariable=self.ymin, **_limit_opts)
        self.entry_ymax = ctk.CTkEntry(tab_exts, textvariable=self.ymax, **_limit_opts)
        self.entry_zmin = ctk.CTkEntry(tab_exts, textvariable=self.zmin, **_limit_opts)
        self.entry_zmax = ctk.CTkEntry(tab_exts, textvariable=self.zmax, **_limit_opts)
        
        # Los trace/commands los conecta el Controller:
        # self.xmin.trace_add('write', self.set_limits)
        # self.ymin.trace_add('write', self.set_limits)
        # self.zmin.trace_add('write', self.set_limits)

        self.label_cutoff = ctk.CTkLabel(tab_view, text='Energía máx.'  , width=90, anchor='w')
        self.label_resol  = ctk.CTkLabel(tab_view, text='Resolución'    , width=90, anchor='w')
        self.label_levels = ctk.CTkLabel(tab_view, text='No. de niveles', width=90, anchor='w')
        
        self.entry_cutoff = ctk.CTkEntry(tab_view, textvariable=self.cutoff, width=120, justify='right')
        self.entry_resol  = ctk.CTkEntry(tab_view, textvariable=self.resol , width=120, justify='right')
        self.entry_levels = ctk.CTkEntry(tab_view, textvariable=self.levels, width=120, justify='right')

        self.units_cutoff = ctk.CTkLabel(tab_view, text='mm/s' , anchor='w')
        self.units_resol  = ctk.CTkLabel(tab_view, text='pts/eje', anchor='w')

        self.label_diameter = ctk.CTkLabel(tab_pars, text='Diámetro carga' , width=90, anchor='w')
        self.label_density  = ctk.CTkLabel(tab_pars, text='Dens. explosivo', width=90, anchor='w')
        self.label_const_K  = ctk.CTkLabel(tab_pars, text='Constante (K)'  , width=90, anchor='w')
        self.label_const_a  = ctk.CTkLabel(tab_pars, text='Exponente (α)'  , width=90, anchor='w')

        self.entry_diameter = ctk.CTkEntry(tab_pars, textvariable=self.diameter, width=120, justify='right')
        self.entry_density  = ctk.CTkEntry(tab_pars, textvariable=self.density , width=120, justify='right')
        self.entry_const_K  = ctk.CTkEntry(tab_pars, textvariable=self.K_const , width=120, justify='right')
        self.entry_const_a  = ctk.CTkEntry(tab_pars, textvariable=self.a_const , width=120, justify='right')
        
        self.units_diameter = ctk.CTkLabel(tab_pars, text='mm'   , anchor='w')
        self.units_density  = ctk.CTkLabel(tab_pars, text='g/cm³', anchor='w')
        self.units_K        = ctk.CTkLabel(tab_pars, text='mm/s',  anchor='w')

        self.frame_buttons = ctk.CTkFrame(self, fg_color='transparent')
        self.button_plot   = ctk.CTkButton(self.frame_buttons, text='Graficar', width=60)
        self.button_save   = ctk.CTkButton(self.frame_buttons, text='Guardar' , width=60)

    def widgets_layout(self):
        '''Coloca los widgets en el menú de evaluación'''
        _frame_pack = {'fill': 'x', 'padx': 5, 'pady': 3, 'ipadx': 5, 'ipady': 5}
        _title_grid = {'row': 0, 'column': 0, 'columnspan': 2, 'padx': 10, 'pady': 3, 'sticky': 'w'}
        _label_grid = {'column': 0, 'sticky': 'w', 'padx': 10}
        _combo_grid = {'column': 1, 'sticky': 'w'}
        _entry_grid = {'column': 1, 'sticky': 'w'}
        _units_grid = {'column': 3, 'sticky': 'w', 'padx': (5,0)}
        _button_pack = {'side': 'left', 'padx': 5, 'pady': 10}

        self.frame_def.pack(**_frame_pack)
        self.title_def.grid(**_title_grid)

        self.label_pattern.grid(row=1, **_label_grid)
        self.label_section.grid(row=2, **_label_grid)
        
        self.combo_charges.grid(row=1, **_combo_grid)
        self.combo_section.grid(row=2, **_combo_grid)

        _frame_pack = {'fill': 'x', 'padx': 5, 'pady': 3}
        _label_grid = {'column': 0, 'sticky': 'w', 'padx': (2,10)}
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

        self.frame_buttons.pack()
        self.button_plot.pack(**_button_pack)
        self.button_save.pack(**_button_pack)

