# main.py
from model import Model
from view import View
from controller import Controller

if __name__ == "__main__":
    """
    Punto de entrada principal de la aplicación.

    Este script instancia los componentes del patrón Modelo-Vista-Controlador (MVC),
    los conecta y lanza el bucle principal de la interfaz gráfica.
    """
    # 1. Crear las instancias de cada componente
    model = Model()
    view = View()
    
    # 2. Conectarlos a través del controlador
    controller = Controller(model, view)
    
    # 3. Iniciar la aplicación
    view.mainloop()