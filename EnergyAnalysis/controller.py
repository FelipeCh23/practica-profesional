""" controller se encargará de:
- Coordinar la comunicación entre model y view
- Gestionar la carga de datos
- Ejecutar cálculos de energía
- Manejar acciones de UI y actualizar la vista"""

from model import EnergyModel
from view import EnergyView


class EnergyController:
    """
    Controlador principal del módulo de Energy Analysis.
    Coordina la interacción entre el modelo (EnergyModel) y la vista (EnergyView).
    """

    def __init__(self):
        # Inicializar modelo y vista
        self.model = EnergyModel()
        self.view = EnergyView()

        # Conectar botones y acciones de la vista con los métodos del controller
        self._connect_events()

    def _connect_events(self):
        """Vincula los eventos de la vista con las funciones del controlador."""
        self.view.load_button.config(command=self.load_data)
        self.view.calculate_button.config(command=self.calculate_energy)
        self.view.volume_button.config(command=self.calculate_stope_volume)

    def load_data(self):
        """Carga datos mediante el modelo y actualiza la vista."""
        try:
            self.view.load_data()  # la vista maneja el diálogo de selección de archivo
            data = self.model.get_results().get("data")
            if data is not None:
                self.view.show_results(f"Datos cargados correctamente: {len(data)} filas.")
        except Exception as e:
            self.view.show_results(f"Error al cargar datos: {e}")

    def calculate_energy(self):
        """Toma parámetros de la vista, calcula energía y actualiza resultados."""
        try:
            param1 = float(self.view.param1_entry.get())
            param2 = float(self.view.param2_entry.get())
            energy = self.model.calculate_energy(param1, param2)
            self.view.show_results(f"Energía calculada: {energy}")
        except Exception as e:
            self.view.show_results(f"Error en cálculo de energía: {e}")

    def calculate_stope_volume(self):
        """Calcula el volumen de la cámara de explotación usando el modelo auxiliar."""
        try:
            width = float(self.view.param1_entry.get())
            height = float(self.view.param2_entry.get())
            depth = 10  # valor ejemplo, podría hacerse dinámico
            volume = self.model.results.get("stope_volume")
            # Usar StopeDesigner directamente
            from model import StopeDesigner
            stope = StopeDesigner(width, height, depth)
            volume = stope.calculate_volume()
            self.view.show_results(f"Volumen de la cámara: {volume}")
            self.model.results["stope_volume"] = volume
        except Exception as e:
            self.view.show_results(f"Error al calcular volumen: {e}")

    def run(self):
        """Ejecuta la aplicación."""
        self.view.mainloop()


if __name__ == "__main__":
    controller = EnergyController()
    controller.run()
