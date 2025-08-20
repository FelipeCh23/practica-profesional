# practica-profesional/vibraciones/controller.py

from model import VibrationModel
from view import VibrationView


class VibrationController:
    """
    Controlador principal para el análisis de vibraciones.
    Coordina la interacción entre el modelo (VibrationModel) y la vista (VibrationView).
    """

    def __init__(self):
        # Inicializar modelo y vista
        self.model = VibrationModel()
        self.view = VibrationView()

        # Conectar botones con acciones del controlador
        self._connect_events()

    def _connect_events(self):
        """Vincula los eventos de la vista con funciones del controlador."""
        self.view.load_button.configure(command=self.load_data)
        self.view.calculate_button.configure(command=self.calculate_vibrations)
        self.view.plot_button.configure(command=self.plot_signal)

    # ---------------- Métodos principales ---------------- #

    def load_data(self):
        """Carga datos de vibraciones desde un archivo CSV."""
        try:
            filepath = self.view.ask_file_path()
            if not filepath:
                return
            data = self.model.load_data(filepath)
            self.view.show_results(f"Datos cargados correctamente: {len(data)} filas.")
        except Exception as e:
            self.view.show_error(f"Error al cargar datos: {e}")

    def calculate_vibrations(self):
        """Ejecuta los cálculos de vibraciones usando parámetros de la vista."""
        try:
            param1 = float(self.view.param1_entry.get())  # frecuencia
            param2 = float(self.view.param2_entry.get())  # amplitud
            vibration = self.model.calculate_vibrations(param1, param2)
            self.view.show_results(f"Resultado del análisis de vibraciones: {vibration}")
        except Exception as e:
            self.view.show_error(f"Error en cálculo de vibraciones: {e}")

    def plot_signal(self):
        """Genera y muestra una gráfica de la señal de vibración."""
        try:
            fig = self.model.plot_vibration_signal()
            if fig:
                self.view.show_results("Gráfico generado correctamente (ver figura).")
                fig.show()
        except Exception as e:
            self.view.show_error(f"Error al graficar señal: {e}")

    # ---------------- Ejecución ---------------- #

    def run(self):
        """Ejecuta la aplicación."""
        self.view.mainloop()


if __name__ == "__main__":
    controller = VibrationController()
    controller.run()
