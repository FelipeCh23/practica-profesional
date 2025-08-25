#controller_vibration

# Conecta la View con el Model. Copia la lógica de:
# - set_limits
# - update_values
# - valid_params
# - plot_distribution
# pero llamando al Model para geometrías y cálculo HP.

from __future__ import annotations
import numpy as np
import shapely.geometry as shp
import matplotlib.pyplot as plt
from tkinter import messagebox

class VibrationController:
    def __init__(self, model, view):
        self.model = model
        self.view  = view

        # Inyectar DATA en la View (para listar combos fiel al original)
        # Nota: la UI original toma list(self.charges.keys()); aquí replicamos:
        self.view.charges = self.model.data.get("charges", {})
        self.view.holes   = self.model.data.get("holes", {})
        self.view.drifts  = self.model.data.get("drifts", {})
        self.view.stopes  = self.model.data.get("stopes", {})

        # Poblar el combo de patrones (incluye "" si está en DATA.json)
        self.view.combo_charges.configure(values=[""] + self.model.get_patterns())

        # Enlazar eventos/commands a métodos del Controller (MVC puro)
        self.view.combo_charges.configure(command=self.update_values)
        self.view.combo_section.configure(command=self.update_values)
        self.view.xmin.trace_add('write', self.set_limits)
        self.view.ymin.trace_add('write', self.set_limits)
        self.view.zmin.trace_add('write', self.set_limits)
        self.view.button_plot.configure(command=self.plot_distribution)

    # ----------------- (copiado y movido a Controller) -----------------
    def set_limits(self, *args):
        """Establece un único valor para la coordenada del plano (igual al original)."""
        if self.view.section.get() == 'Longitudinal':
            xmin = self.view.xmin.get()
            self.view.xmax.set(xmin)
        elif self.view.section.get() == 'Planta':
            ymin = self.view.ymin.get()
            self.view.ymax.set(ymin)
        else:
            zmin = self.view.zmin.get()
            self.view.zmax.set(zmin)

    def update_values(self, event=None):
        """Actualiza parámetros y geometrías (igual al original, pero leyendo desde Model.get_geometry)."""
        pattern_name = self.view.pattern.get()
        if pattern_name == '':
            return

        g = self.model.get_geometry(pattern_name)

        charges_collar = g["charges_collar"]
        charges_toe    = g["charges_toe"]
        charges_diam   = g.get("diameter")
        drift_geom     = g.get("drift_geom")
        stope_geom     = g.get("stope_geom")
        expl_dens      = g.get("density")
        burden         = g.get("burden")

        # Límites del plano desde stope_geom (igual al original)
        xmin, ymin, xmax, ymax = shp.Polygon(stope_geom).bounds
        xmid = round(0.5*(xmin + xmax), 1)
        ymid = round(0.5*(ymin + ymax), 1)
        zmid = 0.0

        self.view.xmin.set(round(1.1*xmin - 0.1*xmax, 1))
        self.view.xmax.set(round(1.1*xmax - 0.1*xmin, 1))
        self.view.ymin.set(round(1.1*ymin - 0.1*ymax, 1))
        self.view.ymax.set(round(1.1*ymax - 0.1*ymin, 1))

        # si DATA trae burden:
        if burden is not None:
            self.view.zmin.set(round(-10*burden, 1))
            self.view.zmax.set(round(+10*burden, 1))
        else:
            # dejar como estaban si no hay burden
            pass

        self.view.entry_xmax.configure(state='normal')
        self.view.entry_ymax.configure(state='normal')
        self.view.entry_zmax.configure(state='normal')

        if self.view.section.get() == 'Transversal':
            self.view.zmin.set(zmid)
            self.view.zmax.set(zmid)
            self.view.entry_zmax.configure(state='disabled')
        elif self.view.section.get() == 'Longitudinal':
            self.view.xmin.set(xmid)
            self.view.xmax.set(xmid)
            self.view.entry_xmax.configure(state='disabled')
        else:
            self.view.ymin.set(ymid)
            self.view.ymax.set(ymid)
            self.view.entry_ymax.configure(state='disabled')

        # Asignar parámetros (igual al original)
        self.view.diameter.set(str(charges_diam if charges_diam is not None else "0.0"))
        self.view.density .set(str(expl_dens   if expl_dens   is not None else "0.0"))

        # Guardar geometrías recuperadas:
        self.view.params.update({
            'charges_collar': charges_collar,
            'charges_toe'   : charges_toe,
            'drift_geom'    : drift_geom,
            'stope_geom'    : stope_geom
        })

    def valid_params(self) -> bool:
        """Valida los parámetros (copiado y adaptado, pero sin mover la UI ni sumar lógica nueva)."""
        pattern_name = self.view.pattern.get()
        if pattern_name == '':
            messagebox.showinfo('Análisis de Vibraciones',
                                'Seleccione un patrón de carga para calcular su distribución de vibraciones.')
            return False

        try:
            xmin = float(self.view.xmin.get()); xmax = float(self.view.xmax.get())
            ymin = float(self.view.ymin.get()); ymax = float(self.view.ymax.get())
            zmin = float(self.view.zmin.get()); zmax = float(self.view.zmax.get())

            cutoff = float(self.view.cutoff.get())
            resol  = int(self.view.resol .get())
            levels = int(self.view.levels.get())

            diameter = float(self.view.diameter.get())
            density  = float(self.view.density .get())
            const_K  = float(self.view.K_const .get())
            const_a  = float(self.view.a_const .get())
        except Exception:
            messagebox.showerror('Análisis de Vibraciones',
                                 'Complete todos los campos de entrada con valores numéricos.')
            return False

        if xmin > xmax:
            messagebox.showerror('Análisis de Vibraciones',
                                 'El límite inferior de la coordenada X no puede ser mayor que el límite superior.')
            return False
        if ymin > ymax:
            messagebox.showerror('Análisis de Vibraciones',
                                 'El límite inferior de la coordenada Y no puede ser mayor que el límite superior.')
            return False
        if zmin > zmax:
            messagebox.showerror('Análisis de Vibraciones',
                                 'El límite inferior de la coordenada Z no puede ser mayor que el límite superior.')
            return False
        if cutoff <= 0:
            messagebox.showerror('Análisis de Vibraciones',
                                 'El máximo valor que se graficará para la vibración no puede ser negativo.')
            return False
        if resol < 2:
            resol = 2
        if levels < 1:
            levels = 1
        if diameter <= 0:
            messagebox.showerror('Análisis de Vibraciones', 'El diámetro de carga debe ser mayor o igual a cero.')
            return False
        if density <= 0:
            messagebox.showerror('Análisis de Vibraciones', 'La densidad del explosivo debe ser mayor o igual a cero.')
            return False

        # Guardar (igual al original)
        self.view.params.update({
            'xmin': xmin, 'xmax': xmax, 'ymin': ymin, 'ymax': ymax, 'zmin': zmin, 'zmax': zmax,
            'cutoff': cutoff, 'resol': resol, 'levels': levels,
            'diameter': diameter, 'density': density, 'const_K': const_K, 'const_a': const_a
        })
        return True

    def plot_distribution(self):
        """Genera la distribución (igual al original), pero llama a model.holmberg_persson."""
        if not self.valid_params():
            return

        p = self.view.params
        xmin, xmax = p['xmin'], p['xmax']
        ymin, ymax = p['ymin'], p['ymax']
        zmin, zmax = p['zmin'], p['zmax']

        cutoff = p['cutoff']; resol = p['resol']; levels = p['levels']
        diameter = p['diameter']; density = p['density']
        const_K = p['const_K'];   const_a = p['const_a']

        collars = p['charges_collar']; toes = p['charges_toe']
        stope_geom = p['stope_geom'];  drift_geom = p['drift_geom']

        x = np.linspace(xmin, xmax, resol)
        y = np.linspace(ymin, ymax, resol)
        z = np.linspace(zmin, zmax, resol)

        if self.view.section.get() == 'Transversal':
            xx, yy = np.meshgrid(x, y)
            vals = self.model.holmberg_persson(xx.ravel(), yy.ravel(), zmin,
                                               charges_collar=collars, charges_toe=toes,
                                               diameter=diameter, density=density,
                                               K_const=const_K, a_const=const_a)
            total_vibration = vals.reshape(xx.shape)
            xlabel, ylabel = 'Coordenada x [m]', 'Coordenada y [m]'
            title = f'Distribución de Vibraciones\nPlano z = {zmin} m'
            grid_x, grid_y = x, y
        elif self.view.section.get() == 'Longitudinal':
            zz, yy = np.meshgrid(z, y)
            vals = self.model.holmberg_persson(xmin, yy.ravel(), zz.ravel(),
                                               charges_collar=collars, charges_toe=toes,
                                               diameter=diameter, density=density,
                                               K_const=const_K, a_const=const_a)
            total_vibration = vals.reshape(zz.shape)
            xlabel, ylabel = 'Coordenada z [m]', 'Coordenada y [m]'
            title = f'Distribución de Vibraciones\nPlano x = {xmin} m'
            grid_x, grid_y = z, y
        else:
            xx, zz = np.meshgrid(x, z)
            vals = self.model.holmberg_persson(xx.ravel(), ymin, zz.ravel(),
                                               charges_collar=collars, charges_toe=toes,
                                               diameter=diameter, density=density,
                                               K_const=const_K, a_const=const_a)
            total_vibration = vals.reshape(xx.shape)
            xlabel, ylabel = 'Coordenada x [m]', 'Coordenada z [m]'
            title = f'Distribución de Vibraciones\nPlano y = {ymin} m'
            grid_x, grid_y = x, z

        total_vibration = np.where(total_vibration > cutoff, cutoff, total_vibration)

        fig, ax = plt.subplots()
        ax.set_aspect('equal')
        cont = plt.contourf(grid_x, grid_y, total_vibration, levels, cmap='viridis')

        if self.view.section.get() == 'Transversal':
            plt.plot(*shp.Polygon(stope_geom).exterior.xy, c='lime', lw=1)
            for collar, toe in zip(collars, toes):
                line = shp.LineString([collar, toe])
                plt.plot(*line.xy, c='red')

        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        cbar = plt.colorbar(cont)
        cbar.ax.set_title('mm/s', loc='left')
        plt.show(block=False)
