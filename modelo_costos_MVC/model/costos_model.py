# model/costos_model.py
import os
import json
import datetime
import math


class CostosModel:
    def __init__(self, base_path):
        # Estado principal
        self.base_path = base_path
        self.modelo_actual_nombre = "Modelo 1"
        self.modelo_ventana = None
        self.tronadura_data = {}
        self.modelos_data = {}

        # Bases de datos de ítems (opcionalmente cargadas en el editor)
        self.explosive_db_data = {}
        self.detonator_db_data = {}
        self.booster_db_data = {}

        # Categorías fijas
        self.fixed_categories = ["Explosivo", "Perforación", "Detonadores", "Iniciadores", "Otros"]

        # Campos del modelo
        self.fecha_modelo_actual = datetime.date.today().strftime('%Y-%m-%d')
        self.moneda_modelo_actual = "CLP"
        self.tipo_cambio_modelo_actual = 1.0

    # --------------------------
    # Persistencia de modelos
    # --------------------------

    def get_model_file(self, name):
        folder = os.path.join(self.base_path, "Modelo")
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, f"{name}.json")

    def save_modelos_data(self):
        """Guarda self.modelos_data en el archivo del modelo actual."""
        path = self.get_model_file(self.modelo_actual_nombre)
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.modelos_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            # En Model no mostramos UI; dejamos trazas.
            print(f"Error al guardar modelo '{self.modelo_actual_nombre}' en '{path}': {e}")

    def load_modelos_data(self, nombre_modelo):
        """
        Carga el JSON del modelo, MERGEA con estructura por defecto (como en V_2),
        asegura que existan todas las categorías y actualiza campos actuales.
        Devuelve True siempre que deja listo un estado coherente (aun con fallback).
        """
        path = self.get_model_file(nombre_modelo)

        default_data_structure = {
            "fecha_modelo": datetime.date.today().strftime('%Y-%m-%d'),
            "moneda_modelo": "CLP",
            "tipo_cambio_modelo": 1.0,
            **{cat: {} for cat in self.fixed_categories}
        }

        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    loaded_data_from_file = json.load(f)

                # Merge conservando claves por defecto
                temp_model_data = default_data_structure.copy()
                temp_model_data.update(loaded_data_from_file)

                # Asegurar categorías como dict
                for cat in self.fixed_categories:
                    if cat not in temp_model_data or not isinstance(temp_model_data[cat], dict):
                        temp_model_data[cat] = {}

                self.modelos_data = temp_model_data
            else:
                # Si no existe, construir estructura por defecto.
                self.modelos_data = default_data_structure.copy()
                # Si es "Modelo 1" y no existe, lo creamos como en V_2
                if nombre_modelo == "Modelo 1":
                    self.save_modelos_data()

            # Actualizar punteros del "modelo actual"
            self.modelo_actual_nombre = nombre_modelo
            self.fecha_modelo_actual = self.modelos_data.get("fecha_modelo", self.fecha_modelo_actual)
            self.moneda_modelo_actual = self.modelos_data.get("moneda_modelo", self.moneda_modelo_actual)
            self.tipo_cambio_modelo_actual = self.modelos_data.get("tipo_cambio_modelo", self.tipo_cambio_modelo_actual)

            return True

        except Exception as e:
            # Fallback duro: dejar estructura por defecto y reportar por trazas
            print(f"Error al cargar modelo '{nombre_modelo}' desde '{path}': {e}. Usando valores por defecto.")
            self.modelos_data = default_data_structure.copy()
            self.modelo_actual_nombre = nombre_modelo
            self.fecha_modelo_actual = self.modelos_data["fecha_modelo"]
            self.moneda_modelo_actual = self.modelos_data["moneda_modelo"]
            self.tipo_cambio_modelo_actual = self.modelos_data["tipo_cambio_modelo"]
            return True

    def get_existing_models(self):
        """Lista de nombres de modelos existentes en /Modelo. Crea 'Modelo 1' si no hay nada."""
        folder = os.path.join(self.base_path, "Modelo")
        os.makedirs(folder, exist_ok=True)
        try:
            files = os.listdir(folder)
            json_files = [f for f in files if f.endswith(".json")]
            models = sorted([f.replace(".json", "") for f in json_files])
            if not models:
                if not os.path.exists(self.get_model_file("Modelo 1")):
                    temp_current_model_name = self.modelo_actual_nombre
                    self.modelo_actual_nombre = "Modelo 1"
                    self.modelos_data = {
                        "fecha_modelo": self.fecha_modelo_actual,
                        "moneda_modelo": self.moneda_modelo_actual,
                        "tipo_cambio_modelo": self.tipo_cambio_modelo_actual,
                        **{cat: {} for cat in self.fixed_categories}
                    }
                    self.save_modelos_data()
                    self.modelo_actual_nombre = temp_current_model_name
                return ["Modelo 1"]
            return models
        except Exception as e:
            print(f"Error al leer la carpeta de modelos '{folder}': {e}")
            return ["Modelo 1"]

    def get_model_currency(self):
        return self.modelos_data.get("moneda_modelo", self.moneda_modelo_actual)

    # --------------------------
    # Tronaduras / Holes
    # --------------------------

    def cargar_tronaduras(self):
        """Lee el archivo de tronaduras (JSON en .txt) y devuelve (ok, lista_tronaduras | status_str)."""
        file_name = os.path.join(self.base_path, "Caseron 3 (Convencional).txt")
        try:
            if not os.path.exists(file_name):
                return False, "Archivo .txt no encontrado"
            with open(file_name, "r", encoding="utf-8") as f:
                self.tronadura_data = json.load(f)

            charges = self.tronadura_data.get("charges", {})
            tronaduras = list(charges.keys())
            if tronaduras:
                return True, tronaduras
            else:
                return False, "No hay tronaduras"

        except json.JSONDecodeError:
            return False, "Error en JSON del .txt"
        except Exception:
            return False, "Error al cargar"

    def cargar_holes(self):
        """Si faltan 'holes' en tronadura_data, los sincroniza desde el archivo."""
        file_name = os.path.join(self.base_path, "Caseron 3 (Convencional).txt")
        try:
            if not self.tronadura_data or "holes" not in self.tronadura_data:
                if not os.path.exists(file_name):
                    return
                with open(file_name, "r", encoding="utf-8") as f:
                    if not self.tronadura_data:
                        self.tronadura_data = json.load(f)
                    else:
                        temp_data = json.load(f)
                        if "holes" in temp_data:
                            self.tronadura_data["holes"] = temp_data["holes"]
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            print(f"Error: No se pudo decodificar el contenido JSON del archivo '{file_name}' al intentar cargar 'holes'.")
        except Exception as e:
            print(f"Error al leer archivo '{file_name}' para 'holes': {e}")

    # --------------------------
    # Cálculos geométricos
    # --------------------------

    def calculate_distance(self, p1, p2):
        if not p1 or not p2:
            return 0.0
        len_p1, len_p2 = len(p1), len(p2)
        if len_p1 < 2 or len_p2 < 2:
            return 0.0
        if len_p1 == 2 and len_p2 == 2:
            return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        elif len_p1 >= 3 and len_p2 >= 3:
            return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2 + (p2[2] - p1[2])**2)
        else:
            return 0.0

    def calculate_largo_total_explosivo(self, geometry):
        if (not geometry or len(geometry) != 2 or
            not geometry[0] or not geometry[1] or
            len(geometry[0]) != len(geometry[1])):
            return 0.0
        list_a, list_b = geometry[0], geometry[1]
        total_length = 0.0
        min_len = min(len(list_a), len(list_b))
        for i in range(min_len):
            if isinstance(list_a[i], (list, tuple)) and isinstance(list_b[i], (list, tuple)):
                total_length += self.calculate_distance(list_a[i], list_b[i])
            else:
                print(f"Warning: Formato de punto inválido en geometría de explosivo en índice {i}: {list_a[i]}, {list_b[i]}")
        return total_length

    def calculate_largo_total_hole(self, geometry):
        if (not geometry or len(geometry) != 2 or
            not geometry[0] or not geometry[1] or
            len(geometry[0]) != len(geometry[1])):
            return 0.0
        list_a, list_b = geometry[0], geometry[1]
        total_length = 0.0
        min_len = min(len(list_a), len(list_b))
        for i in range(min_len):
            if isinstance(list_a[i], (list, tuple)) and isinstance(list_b[i], (list, tuple)):
                total_length += self.calculate_distance(list_a[i], list_b[i])
            else:
                print(f"Warning: Formato de punto inválido en geometría de hole en índice {i}: {list_a[i]}, {list_b[i]}")
        return total_length

    # --------------------------
    # Bases de datos locales
    # --------------------------

    def _load_db_file(self, db_name):
        db_dir = os.path.join(self.base_path, 'databases')
        file_path = os.path.join(db_dir, db_name)
        data = {}
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                print(f"Advertencia: Archivo '{file_path}' no encontrado.")
        except Exception as e:
            print(f"Error al cargar '{file_path}': {e}")
        return data

    def load_explosive_db_data(self):
        self.explosive_db_data = self._load_db_file('explosive.db')

    def load_detonator_db_data(self):
        self.detonator_db_data = self._load_db_file('detonator.db')

    def load_booster_db_data(self):
        self.booster_db_data = self._load_db_file('booster.db')
