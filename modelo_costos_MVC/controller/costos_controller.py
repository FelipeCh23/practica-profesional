# controller/costos_controller.py
"""
Controlador (Controller) de la app de costos.

- La View (interfaz) SOLO pinta y recoge eventos.
- El Model (datos) SOLO lee/escribe y calcula.
- El Controller orquesta: escucha eventos de la View, pide datos al Model,
  y decide qué y cuándo pintar en la View.
"""

import os
import math
import datetime
import tkinter as tk
from tkinter import messagebox


class CostosController:
    """
    Orquesta la comunicación entre View y Model:
    - Decide qué datos pedir/cargar del Model.
    - Prepara/transforma los datos para la View.
    - Reacciona a eventos (cambios de modelo, selección de tronadura, etc.).
    """

    def __init__(self, model, view):
        """
        Guarda referencias a Model (datos) y View (interfaz).
        No hace trabajo pesado aquí; solo inicializa punteros.
        """
        self.model = model
        self.view = view

    # --------------------------------------------------------------------- #
    #                             INICIO / ARRANQUE
    # --------------------------------------------------------------------- #
    def start(self):
        """
        Arranque de la app:
        1) Carga el modelo actual (JSON).
        2) Pobla el combo de modelos.
        3) Carga tronaduras/holes.
        4) Deja la tabla en un estado consistente si no hay tronadura válida.
        5) Ajusta encabezados según moneda.
        """
        # 1) Cargar modelo actual por defecto (desde disco o estructura por defecto)
        self.model.load_modelos_data(self.model.modelo_actual_nombre)

        # 2) Poblar combo de modelos en la vista
        modelos = self.model.get_existing_models()
        self.view.combo_modelo_selector_set_options(modelos)
        self.view.combo_modelo_selector_set(self.model.modelo_actual_nombre)

        # 3) Cargar tronaduras (charges) y asegurar holes
        self.cargar_tronaduras()
        self.cargar_holes()

        # 4) Si no hay tronadura válida, limpiar y mostrar "Otros" + totales
        current_tronadura_status = self.view.get_combo_tronadura_value()
        if (
            not current_tronadura_status
            or current_tronadura_status
            in [
                "No hay tronaduras",
                "Archivo .txt no encontrado",
                "Error JSON",
                "Error en JSON del .txt",
                "Error al cargar",
            ]
        ):
            self.view.table_clear()
            if hasattr(self.view, "_add_otros_items_to_main_table"):
                self.view._add_otros_items_to_main_table()
            self.view.update_totals()

        # 5) Ajustar encabezado con la moneda actual (si la View expone helper)
        if hasattr(self.view, "_update_main_app_ui_for_currency"):
            self.view._update_main_app_ui_for_currency()

    # --------------------------------------------------------------------- #
    #                          TRONADURAS / HOLES
    # --------------------------------------------------------------------- #
    def cargar_tronaduras(self):
        """
        Pide al Model cargar tronaduras desde el archivo.
        Según el resultado, actualiza el combo y tabla en la View.
        """
        ok, payload = self.model.cargar_tronaduras()
        if ok:
            tronaduras = payload
            self.view.combo_tronadura_set_options(tronaduras)
            if tronaduras:
                # Auto-seleccionar la primera y pintar
                self.view.combo_tronadura_set(tronaduras[0])
                self.on_tronadura_selected()
            else:
                # Sin tronaduras
                self.view.combo_tronadura_set_options([])
                self.view.combo_tronadura_set("No hay tronaduras")
                self.view.table_clear()
        else:
            # payload es un string de estado/errores
            status = payload
            self.view.combo_tronadura_set_options([])
            self.view.combo_tronadura_set(status)
            self.view.table_clear()

    def cargar_holes(self):
        """
        Asegura que el diccionario de 'holes' esté presente en self.model.tronadura_data.
        No pinta nada; solo sincroniza datos.
        """
        self.model.cargar_holes()

    # --------------------------------------------------------------------- #
    #                       CAMBIO DE MODELO (COMBO SUPERIOR)
    # --------------------------------------------------------------------- #
    def cambiar_modelo_evento(self):
        """
        Se dispara al cambiar de modelo desde el combo de la ventana principal.
        Re-carga datos, re-puebla combos y refresca UI según la moneda.
        """
        nuevo = self.view.get_combo_modelo_value()
        if not nuevo:
            return
        if not self.model.load_modelos_data(nuevo):
            return

        # Refrescar lista y selección visible
        modelos = self.model.get_existing_models()
        self.view.combo_modelo_selector_set_options(modelos)
        self.view.combo_modelo_selector_set(self.model.modelo_actual_nombre)

        # Recalcular tronaduras/holes porque el modelo (precios/unidades) cambió
        self.cargar_tronaduras()
        self.cargar_holes()

        # Actualizar encabezado por moneda
        if hasattr(self.view, "_update_main_app_ui_for_currency"):
            self.view._update_main_app_ui_for_currency()

    # =====================  REUBICADAS DESDE V_2  ======================== #
    #         (Son las mismas funciones; solo viven en el Controller)       #
    # --------------------------------------------------------------------- #
    #              Helpers de UI/editor y persistencia de modelos           #
    # --------------------------------------------------------------------- #
    def update_main_window_model_selector(self):
        """
        Actualiza el combo de modelos de la ventana principal para que muestre
        TODOS los modelos disponibles y deje seleccionado el actual.
        """
        existing_models = self.model.get_existing_models()
        self.view.combo_modelo_selector_set_options(existing_models)

        # Si el actual desapareció, elegir un fallback razonable
        if self.model.modelo_actual_nombre not in existing_models:
            new_default_model = (
                "Modelo 1"
                if "Modelo 1" in existing_models
                else (existing_models[0] if existing_models else "Modelo 1")
            )
            self.model.modelo_actual_nombre = new_default_model

        self.view.combo_modelo_selector_set(self.model.modelo_actual_nombre)

    def cambiar_modelo(self, modelo_nombre):
        """
        Cambia el modelo activo (desde el editor), recarga datos y refresca UI.
        """
        self.model.modelo_actual_nombre = modelo_nombre
        self.model.load_modelos_data(modelo_nombre)

        # Si la ventana del editor está visible, reflejar nuevo nombre y repintar
        if (
            hasattr(self.view, "modelo_ventana")
            and self.view.modelo_ventana
            and self.view.modelo_ventana.winfo_exists()
        ):
            if hasattr(self.view.modelo_ventana, "combo_model_edit"):
                self.view.modelo_ventana.combo_model_edit.set(modelo_nombre)

            # Mantiene tus mismos flujos/nombres:
            self.populate_model_table_with_model_data()
            self.update_model_window_category_items()
            self._update_model_info_widgets()
            self._update_model_editor_ui_for_currency()

        # Encabezado con moneda actualizada
        if hasattr(self.view, "_update_main_app_ui_for_currency"):
            self.view._update_main_app_ui_for_currency()

    def save_modelo_from_table(self):
        """
        Toma los datos de la tabla del editor (ítem, unidad, precio),
        los valida y los guarda en el JSON del modelo actual.
        Después refresca la UI y recalcula la tabla principal.
        """
        win = getattr(self.view, "modelo_ventana", None)
        if not (
            win
            and win.winfo_exists()
            and hasattr(win, "tabla_modelo")
            and hasattr(win, "date_entry_model")
            and hasattr(win, "combo_moneda_modelo")
            and hasattr(win, "entry_tipo_cambio_modelo_var")
        ):
            messagebox.showerror(
                "Error",
                "La ventana de modelos o sus componentes no están "
                "completamente inicializados.",
                parent=win if win and win.winfo_exists() else self.view.master,
            )
            return

        current_model_to_save_name = win.combo_model_edit.get()
        if not current_model_to_save_name:
            messagebox.showwarning(
                "Sin Modelo",
                "No hay un modelo seleccionado para guardar.",
                parent=win,
            )
            return

        # Alinea el combo con el modelo activo si no coincide
        if current_model_to_save_name != self.model.modelo_actual_nombre:
            win.combo_model_edit.set(self.model.modelo_actual_nombre)
            messagebox.showinfo(
                "Información",
                f"Guardando cambios en el modelo "
                f"'{self.model.modelo_actual_nombre}'.\n"
                f"El nombre en el combo fue ajustado.",
                parent=win,
            )

        # Tomar fecha desde el widget (o fallback hoy)
        try:
            fecha_seleccionada = win.date_entry_model.get_date().strftime(
                "%Y-%m-%d"
            )
        except Exception:
            fecha_seleccionada = datetime.date.today().strftime("%Y-%m-%d")
            print(
                "Advertencia: No se pudo obtener la fecha del widget, "
                "usando fecha actual."
            )

        # Moneda desde combo y tipo de cambio desde entry
        moneda_seleccionada = win.combo_moneda_modelo.get()

        tipo_cambio_str = win.entry_tipo_cambio_modelo_var.get()
        try:
            tipo_cambio_seleccionado = float(tipo_cambio_str)
            if tipo_cambio_seleccionado < 0:
                tipo_cambio_seleccionado = 0.0
        except ValueError:
            messagebox.showwarning(
                "Tipo de Cambio Inválido",
                f"El tipo de cambio '{tipo_cambio_str}' no es un número "
                f"válido. Se guardará como 1.0.",
                parent=win,
            )
            tipo_cambio_seleccionado = 1.0
            win.entry_tipo_cambio_modelo_var.set("1.0")

        # Armar la estructura base para guardar (categorías vacías)
        new_model_data_structure = {
            "fecha_modelo": fecha_seleccionada,
            "moneda_modelo": moneda_seleccionada,
            "tipo_cambio_modelo": tipo_cambio_seleccionado,
            **{cat: {} for cat in self.model.fixed_categories},
        }

        # Recorrer filas del editor y volcar a estructura
        invalid_items_count = 0
        for row_iid in win.tabla_modelo.get_children():
            try:
                (
                    item_display_name_from_table,
                    unidad_from_table,
                    precio_str_from_table,
                ) = win.tabla_modelo.item(row_iid)["values"]

                item_display_name_from_table = str(
                    item_display_name_from_table
                ).strip()
                unidad_from_table = str(unidad_from_table).strip()
                precio_str_from_table = str(precio_str_from_table).strip()

                if not item_display_name_from_table:
                    invalid_items_count += 1
                    continue

                # Precio válido o 0.0
                try:
                    precio_to_save = (
                        float(precio_str_from_table)
                        if precio_str_from_table
                        else 0.0
                    )
                except ValueError:
                    messagebox.showwarning(
                        "Precio Inválido",
                        f"Precio '{precio_str_from_table}' para "
                        f"'{item_display_name_from_table}' no es un número. "
                        f"Se guardará como 0.0.",
                        parent=win,
                    )
                    precio_to_save = 0.0

                # Determinar clave/categoría (Perforación usa diámetro como clave)
                item_key_for_json = item_display_name_from_table
                category_for_item = None

                if (
                    item_display_name_from_table.startswith("Perforación D")
                    and item_display_name_from_table.endswith("mm")
                ):
                    potential_diameter = item_display_name_from_table[
                        len("Perforación D") : -len("mm")
                    ]
                    if potential_diameter.isdigit():
                        item_key_for_json = potential_diameter
                        category_for_item = "Perforación"

                # Intentar inferir categoría desde los catálogos cargados
                if (
                    category_for_item is None
                    and self.model.explosive_db_data
                    and item_display_name_from_table
                    in self.model.explosive_db_data
                ):
                    category_for_item = "Explosivo"
                if (
                    category_for_item is None
                    and self.model.detonator_db_data
                    and item_display_name_from_table
                    in self.model.detonator_db_data
                ):
                    category_for_item = "Detonadores"
                if (
                    category_for_item is None
                    and self.model.booster_db_data
                    and item_display_name_from_table
                    in self.model.booster_db_data
                ):
                    category_for_item = "Iniciadores"
                if category_for_item is None:
                    category_for_item = "Otros"

                if category_for_item not in new_model_data_structure:
                    new_model_data_structure[category_for_item] = {}

                new_model_data_structure[category_for_item][
                    item_key_for_json
                ] = {"unidad": unidad_from_table, "precio": round(precio_to_save, 2)}

            except Exception as e:
                # No abortamos todo por una fila mala; contabilizamos y seguimos
                print(
                    "Error procesando fila de tabla de modelo para guardar: "
                    f"{e}"
                )
                invalid_items_count += 1
                continue

        # Persistir cambios en el Model y guardar a disco
        self.model.modelos_data = new_model_data_structure
        self.model.moneda_modelo_actual = moneda_seleccionada
        self.model.fecha_modelo_actual = fecha_seleccionada
        self.model.tipo_cambio_modelo_actual = tipo_cambio_seleccionado
        self.model.save_modelos_data()

        # Feedback al usuario
        if invalid_items_count == 0:
            messagebox.showinfo(
                "Modelo Guardado",
                f"Modelo '{self.model.modelo_actual_nombre}' guardado "
                f"exitosamente.",
                parent=win,
            )
        else:
            messagebox.showwarning(
                "Guardado Parcial",
                f"Modelo '{self.model.modelo_actual_nombre}' guardado, "
                f"pero {invalid_items_count} ítems inválidos de la tabla no "
                f"se procesaron.",
                parent=win,
            )

        # Refrescar cabeceras/moneda en editor y app
        self.view._update_tipo_cambio_label_editor()
        self._update_model_editor_ui_for_currency()
        self.view._update_main_app_ui_for_currency()

        # Recalcular tabla principal (según tronadura vigente)
        current_tronadura = self.view.get_combo_tronadura_value()
        if current_tronadura and current_tronadura not in [
            "No hay tronaduras",
            "Archivo .txt no encontrado",
            "Error JSON",
            "Error al cargar",
            "Error en JSON del .txt",
        ]:
            self.on_tronadura_selected()
        else:
            self.view.table_clear()
            if hasattr(self.view, "_add_otros_items_to_main_table"):
                self.view._add_otros_items_to_main_table()
            self.view.update_totals()

    def delete_row_model_table(self):
        """
        Elimina la fila seleccionada en la tabla del editor de modelos.
        No guarda todavía; solo modifica la tabla. El guardado lo hace
        `save_modelo_from_table`.
        """
        win = getattr(self.view, "modelo_ventana", None)
        if not (win and win.winfo_exists() and hasattr(win, "tabla_modelo")):
            return
        sel = win.tabla_modelo.selection()
        if not sel:
            messagebox.showwarning(
                "Sin Selección",
                "Seleccione una fila de la tabla para eliminar.",
                parent=win,
            )
            return
        iid_to_delete = sel[0]
        item_name_in_row = win.tabla_modelo.item(iid_to_delete)["values"][0]
        confirm = messagebox.askyesno(
            "Confirmar Eliminación",
            "¿Está seguro de eliminar el ítem "
            f"'{item_name_in_row}' de la tabla?\n"
            "El cambio se reflejará en el archivo al guardar el modelo.",
            parent=win,
        )
        if confirm:
            win.tabla_modelo.delete(iid_to_delete)

    def edit_cell(self, event, table_widget):
        """
        Editor inline para la tabla del editor de modelos:
        - Bloquea editar nombres provenientes de catálogos (DB/Perforación).
        - Permite editar 'Unidad' (texto) y 'Costo unitario' (numérico).
        """
        win = getattr(self.view, "modelo_ventana", None)
        if not (win and win.winfo_exists()):
            return

        region = table_widget.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_iid = table_widget.identify_row(event.y)
        col_id_str = table_widget.identify_column(event.x)
        col_index_visual = int(col_id_str.replace("#", ""))
        col_index_data = col_index_visual - 1

        current_values = table_widget.item(row_iid)["values"]
        item_name_in_row = (
            str(current_values[0]).strip()
            if current_values and len(current_values) > 0
            else ""
        )

        # No permitir editar NOMBRE si viene de DB/perforación
        if col_index_data == 0:
            is_db_item = False
            if (
                item_name_in_row.startswith("Perforación D")
                and item_name_in_row.endswith("mm")
            ):
                is_db_item = True
            elif (
                self.model.explosive_db_data
                and item_name_in_row in self.model.explosive_db_data
            ):
                is_db_item = True
            elif (
                self.model.detonator_db_data
                and item_name_in_row in self.model.detonator_db_data
            ):
                is_db_item = True
            elif (
                self.model.booster_db_data
                and item_name_in_row in self.model.booster_db_data
            ):
                is_db_item = True

            if is_db_item:
                messagebox.showwarning(
                    "Edición no Permitida",
                    "El nombre de este tipo de ítem (Perforación, "
                    "Explosivo, etc. de DB) no se puede editar directamente. "
                    "Elimine y añada de nuevo si es necesario.",
                    parent=win,
                )
                return

            messagebox.showwarning(
                "Edición no Permitida",
                "El nombre del ítem se gestiona con los combos superiores "
                "o añadiéndolo de nuevo. Para cambiar un 'Otros', elimine y "
                "añada de nuevo.",
                parent=win,
            )
            return

        # Solo 'Unidad' (col 1) y 'Costo unitario' (col 2)
        if col_index_data not in [1, 2]:
            messagebox.showwarning(
                "Edición no Permitida",
                "Solo se pueden editar las columnas 'Unidad' y "
                "'Costo unitario'.",
                parent=win,
            )
            return

        # Crear un Entry encima de la celda para editar inline
        x, y, w, h = table_widget.bbox(row_iid, col_id_str)
        original_value = current_values[col_index_data]
        entry_editor = tk.Entry(table_widget)
        entry_editor.place(x=x, y=y, width=w, height=h)
        entry_editor.insert(0, str(original_value))
        entry_editor.select_range(0, tk.END)
        entry_editor.focus()

        def on_save_model_cell_edit(_=None):
            """Guarda el valor del Entry en la celda y valida tipo/campo."""
            new_value_str = entry_editor.get()
            entry_editor.destroy()
            updated_values = list(current_values)

            if col_index_data == 2:  # costo unitario
                try:
                    new_cost = float(new_value_str)
                    if new_cost < 0:
                        new_cost = 0.0
                    updated_values[col_index_data] = round(new_cost, 2)
                except ValueError:
                    messagebox.showerror(
                        "Valor Inválido",
                        "El costo debe ser un número.",
                        parent=win,
                    )
                    return
            else:  # unidad (texto libre)
                updated_values[col_index_data] = new_value_str.strip()

            table_widget.item(row_iid, values=tuple(updated_values))

        entry_editor.bind("<Return>", on_save_model_cell_edit)
        entry_editor.bind("<FocusOut>", on_save_model_cell_edit)
        entry_editor.bind("<Escape>", lambda e: entry_editor.destroy())

    def eliminar_modelo_completo(self):
        """
        Elimina del disco el archivo JSON del modelo seleccionado
        en el editor. Si es el activo, elige un modelo de reemplazo
        (Modelo 1 u otro) y refresca toda la UI relacionada.
        """
        win = getattr(self.view, "modelo_ventana", None)
        if not (win and win.winfo_exists() and hasattr(win, "combo_model_edit")):
            return

        model_to_delete_name = win.combo_model_edit.get().strip()
        if not model_to_delete_name:
            messagebox.showwarning(
                "Sin Selección",
                "No hay un modelo seleccionado para eliminar.",
                parent=win,
            )
            return
        if model_to_delete_name == "Modelo 1":
            messagebox.showwarning(
                "Acción no Permitida",
                "No se puede eliminar el modelo predeterminado 'Modelo 1'.",
                parent=win,
            )
            return

        existing_models = self.model.get_existing_models()
        if model_to_delete_name not in existing_models:
            # El archivo no existe o hubo una inconsistencia
            messagebox.showerror(
                "Error",
                f"El modelo '{model_to_delete_name}' no parece existir.",
                parent=win,
            )
            self.update_main_window_model_selector()
            if hasattr(win, "combo_model_edit") and win.combo_model_edit.winfo_exists():
                win.combo_model_edit["values"] = self.model.get_existing_models()
                win.combo_model_edit.set(self.model.modelo_actual_nombre)
            return

        confirm = messagebox.askyesno(
            "Confirmar Eliminación de Modelo",
            "¿Está seguro de eliminar el modelo completo "
            f"'{model_to_delete_name}'?\n"
            "Esta acción eliminará el archivo y no se puede deshacer.",
            parent=win,
            icon="warning",
        )
        if not confirm:
            return

        file_path_to_delete = self.model.get_model_file(model_to_delete_name)
        try:
            os.remove(file_path_to_delete)
            messagebox.showinfo(
                "Modelo Eliminado",
                f"El modelo '{model_to_delete_name}' ha sido "
                f"eliminado exitosamente.",
                parent=win,
            )

            # Si borramos el activo, escoger uno nuevo
            if self.model.modelo_actual_nombre == model_to_delete_name:
                available_models_after_delete = self.model.get_existing_models()
                new_active_model = "Modelo 1"
                if not available_models_after_delete:
                    # Si no queda nada, recrear/usar Modelo 1
                    self.model.modelo_actual_nombre = "Modelo 1"
                    self.model.load_modelos_data(self.model.modelo_actual_nombre)
                elif "Modelo 1" in available_models_after_delete:
                    new_active_model = "Modelo 1"
                elif available_models_after_delete:
                    new_active_model = available_models_after_delete[0]

                self.model.modelo_actual_nombre = new_active_model
                self.model.load_modelos_data(self.model.modelo_actual_nombre)

            # Refrescar combos de la ventana principal y del editor
            self.update_main_window_model_selector()
            if hasattr(win, "combo_model_edit") and win.combo_model_edit.winfo_exists():
                win.combo_model_edit["values"] = self.model.get_existing_models()
                win.combo_model_edit.set(self.model.modelo_actual_nombre)

            # Repintar tabla del editor y widgets auxiliares
            self.populate_model_table_with_model_data()
            self.update_model_window_category_items()
            self._update_model_info_widgets()
            self._update_model_editor_ui_for_currency()

            # Disparar flujo de cambio de modelo en la ventana principal
            self.cambiar_modelo_evento()

        except FileNotFoundError:
            messagebox.showerror(
                "Error",
                f"No se encontró el archivo del modelo '{model_to_delete_name}' "
                f"para eliminar.",
                parent=win,
            )
        except PermissionError:
            messagebox.showerror(
                "Error de Permisos",
                "No se tienen permisos para eliminar el archivo del modelo "
                f"'{model_to_delete_name}'.",
                parent=win,
            )
        except Exception as e:
            messagebox.showerror(
                "Error Inesperado",
                "Ocurrió un error al eliminar el modelo "
                f"'{model_to_delete_name}': {e}",
                parent=win,
            )

        # Sincronizar por si hubo cambios de última hora
        self.update_main_window_model_selector()
        if hasattr(win, "combo_model_edit") and win.combo_model_edit.winfo_exists():
            avail = self.model.get_existing_models()
            win.combo_model_edit["values"] = avail
            if self.model.modelo_actual_nombre in avail:
                win.combo_model_edit.set(self.model.modelo_actual_nombre)
            elif avail:
                win.combo_model_edit.set(avail[0])
            else:
                win.combo_model_edit.set("")

    # --------------------------------------------------------------------- #
    #                     SELECCIÓN DE TRONADURA (PINTADO)
    # --------------------------------------------------------------------- #
    def on_tronadura_selected(self):
        """
        Cuando el usuario elige una tronadura:
        - Limpia la tabla principal.
        - Calcula cantidades (explosivo, perforación, detonadores, iniciadores)
          usando datos/geom. del Model.
        - Busca precios/unidades en el modelo de costos y coloca filas.
        - Añade ítems "Otros" que no dependan de tronadura.
        - Recalcula totales.
        """
        selected_tronadura_name = self.view.get_combo_tronadura_value()
        self.view.table_clear()

        # Validaciones básicas de estado
        if (
            not self.model.tronadura_data
            or not selected_tronadura_name
            or selected_tronadura_name
            in [
                "No hay tronaduras",
                "Archivo .txt no encontrado",
                "Error JSON",
                "Error en JSON del .txt",
                "Error al cargar",
            ]
        ):
            if hasattr(self.view, "_add_otros_items_to_main_table"):
                self.view._add_otros_items_to_main_table()
            self.view.update_totals()
            return

        charges = self.model.tronadura_data.get("charges", {})
        selected_charge_data = charges.get(selected_tronadura_name)
        if not selected_charge_data or not isinstance(selected_charge_data, dict):
            if hasattr(self.view, "_add_otros_items_to_main_table"):
                self.view._add_otros_items_to_main_table()
            self.view.update_totals()
            return

        # ------------------------ Explosivo ------------------------ #
        explosive_info = selected_charge_data.get("explosive")
        if isinstance(explosive_info, dict):
            explosive_name = explosive_info.get("name")
            if explosive_name:
                largo_total_explosivo = self.model.calculate_largo_total_explosivo(
                    selected_charge_data.get("geometry", [])
                )
                is_cartridge = explosive_info.get("cartridge", False)
                cartridge_length = explosive_info.get("length", 0.0)

                cantidad_explosivo = 0.0
                unidad_explosivo = "kg"

                # Cartucho: convertir largo total en N° de unidades aprox.
                if is_cartridge and largo_total_explosivo > 0 and cartridge_length > 0:
                    cantidad_explosivo = math.ceil(
                        (largo_total_explosivo / cartridge_length) * 1000
                    )
                    unidad_explosivo = "unidad"
                else:
                    # Granel: volumen cilíndrico * densidad → kg
                    explosive_diameter_mm = selected_charge_data.get(
                        "diameter", 0.0
                    )
                    explosive_density_gcm3 = explosive_info.get("density", 0.0)
                    diameter_m = (
                        float(explosive_diameter_mm) / 1000.0
                        if explosive_diameter_mm
                        else 0.0
                    )
                    density_kgm3 = (
                        float(explosive_density_gcm3) * 1000.0
                        if explosive_density_gcm3
                        else 0.0
                    )
                    if (
                        largo_total_explosivo > 0
                        and diameter_m > 0
                        and density_kgm3 > 0
                    ):
                        volumen_m3 = (math.pi * (diameter_m**2) / 4) * largo_total_explosivo
                        cantidad_explosivo = volumen_m3 * density_kgm3
                    unidad_explosivo = "kg"

                # Precio/unidad según modelo de costos (si existe)
                explosivo_model_price = 0.0
                explosivo_unidad_final = unidad_explosivo
                for category_in_model, items_in_category_model in self.model.modelos_data.items():
                    if not isinstance(items_in_category_model, dict):
                        continue
                    key_to_check = explosive_name
                    if key_to_check in items_in_category_model:
                        item_data_model = items_in_category_model[key_to_check]
                        try:
                            explosivo_model_price = float(item_data_model.get("precio", 0.0))
                        except (ValueError, TypeError):
                            explosivo_model_price = 0.0
                        explosivo_unidad_final = item_data_model.get(
                            "unidad", unidad_explosivo
                        )
                        break

                explosivo_total_cost = cantidad_explosivo * explosivo_model_price
                self.view.table_add_items(
                    [
                        (
                            explosive_name,
                            round(cantidad_explosivo, 2),
                            explosivo_unidad_final,
                            round(explosivo_total_cost, 2),
                        )
                    ]
                )

        # ---------------------- Perforación (holes) ---------------------- #
        associated_hole_name = selected_charge_data.get("holes")
        holes_data = self.model.tronadura_data.get("holes", {})
        associated_hole_data = holes_data.get(associated_hole_name)

        if isinstance(associated_hole_data, dict):
            largo_total_hole = self.model.calculate_largo_total_hole(
                associated_hole_data.get("geometry", [])
            )
            hole_diameter_mm_val = associated_hole_data.get("diameter")

            perforacion_item_name = None
            hole_diameter_key = None

            # Determinar nombre del ítem de perforación (Dxxmm)
            if hole_diameter_mm_val is not None:
                try:
                    hole_diameter_int = int(float(str(hole_diameter_mm_val).strip()))
                    hole_diameter_key = str(hole_diameter_int)
                    perforacion_item_name = f"Perforación D{hole_diameter_key}mm"
                except (ValueError, TypeError):
                    perforacion_item_name = None
                    hole_diameter_key = None

            if perforacion_item_name and hole_diameter_key and largo_total_hole > 0:
                perforacion_model_price = 0.0
                perforacion_unidad_final = "m"
                for category_in_model, items_in_category_model in self.model.modelos_data.items():
                    if not isinstance(items_in_category_model, dict):
                        continue
                    key_to_check = perforacion_item_name
                    if (
                        category_in_model == "Perforación"
                        and perforacion_item_name.startswith("Perforación D")
                        and perforacion_item_name.endswith("mm")
                    ):
                        # La clave real en JSON es el número (e.g., "89")
                        key_to_check = perforacion_item_name[len("Perforación D") : -len("mm")]
                    if key_to_check in items_in_category_model:
                        item_data_model = items_in_category_model[key_to_check]
                        try:
                            perforacion_model_price = float(item_data_model.get("precio", 0.0))
                        except (ValueError, TypeError):
                            perforacion_model_price = 0.0
                        perforacion_unidad_final = item_data_model.get("unidad", "m")
                        break

                perforacion_total_cost = largo_total_hole * perforacion_model_price
                self.view.table_add_items(
                    [
                        (
                            perforacion_item_name,
                            round(largo_total_hole, 2),
                            perforacion_unidad_final,
                            round(perforacion_total_cost, 2),
                        )
                    ]
                )

        # ----------------- Detonadores / Iniciadores (blasts) ------------- #
        selected_blast_data = None
        for _, blast_data_item in self.model.tronadura_data.get("blasts", {}).items():
            if (
                isinstance(blast_data_item, dict)
                and blast_data_item.get("charges") == selected_tronadura_name
            ):
                selected_blast_data = blast_data_item
                break

        if selected_blast_data:
            # Detonadores
            detonator_name = selected_blast_data.get("detonator")
            detonator_geometry = selected_blast_data.get("geometry", [])
            cantidad_detonador = len(detonator_geometry)

            if detonator_name and cantidad_detonador > 0:
                detonador_model_price = 0.0
                detonador_unidad_final = "unidad"
                for category_in_model, items_in_category_model in self.model.modelos_data.items():
                    if not isinstance(items_in_category_model, dict):
                        continue
                    key_to_check = detonator_name
                    if key_to_check in items_in_category_model:
                        item_data_model = items_in_category_model[key_to_check]
                        try:
                            detonador_model_price = float(item_data_model.get("precio", 0.0))
                        except (ValueError, TypeError):
                            detonador_model_price = 0.0
                        detonador_unidad_final = item_data_model.get("unidad", "unidad")
                        break

                detonador_total_cost = cantidad_detonador * detonador_model_price
                self.view.table_add_items(
                    [
                        (
                            detonator_name,
                            round(float(cantidad_detonador), 2),
                            detonador_unidad_final,
                            round(detonador_total_cost, 2),
                        )
                    ]
                )

            # Iniciadores (booster)
            booster_name = selected_blast_data.get("booster")
            booster_geometry = selected_blast_data.get("geometry", [])
            cantidad_base_booster = len(booster_geometry)
            is_double = selected_blast_data.get("double", False)
            cantidad_booster = (
                cantidad_base_booster * 2 if is_double else cantidad_base_booster
            )

            if booster_name and cantidad_booster > 0:
                booster_model_price = 0.0
                booster_unidad_final = "unidad"
                for category_in_model, items_in_category_model in self.model.modelos_data.items():
                    if not isinstance(items_in_category_model, dict):
                        continue
                    key_to_check = booster_name
                    if key_to_check in items_in_category_model:
                        item_data_model = items_in_category_model[key_to_check]
                        try:
                            booster_model_price = float(item_data_model.get("precio", 0.0))
                        except (ValueError, TypeError):
                            booster_model_price = 0.0
                        booster_unidad_final = item_data_model.get("unidad", "unidad")
                        break

                booster_total_cost = cantidad_booster * booster_model_price
                self.view.table_add_items(
                    [
                        (
                            booster_name,
                            round(float(cantidad_booster), 2),
                            booster_unidad_final,
                            round(booster_total_cost, 2),
                        )
                    ]
                )

        # Añade "Otros" que estén definidos en el modelo de costos
        if hasattr(self.view, "_add_otros_items_to_main_table"):
            self.view._add_otros_items_to_main_table()

        # Recalcular fila de totales
        self.view.update_totals()

    # --------------------------------------------------------------------- #
    #                     RECÁLCULO COMPLETO DE LA TABLA
    # --------------------------------------------------------------------- #
    def recalculate_table_costs(self, event=None):
        """
        Relee todas las filas actuales (excepto la de total), busca su precio y
        unidad actualizados en `modelos_data` y vuelve a pintarlas con el costo
        recalculado. Finalmente actualiza los totales.
        """
        if not (hasattr(self.view, "data_table") and self.view.data_table.winfo_exists()):
            return

        # Copiar filas existentes (excepto totales) y limpiar tabla
        current_table_items = []
        for iid in self.view.data_table.get_children():
            if "total_row" not in self.view.data_table.item(iid)["tags"]:
                current_table_items.append(self.view.data_table.item(iid)["values"])
        self.view.table_clear()

        # Reinsertar filas recalculando con los valores del modelo de costos
        for values in current_table_items:
            if not values:
                continue
            item_name = values[0]
            try:
                cantidad = float(values[1])
            except (ValueError, TypeError):
                cantidad = 0.0

            current_unit = values[2] if len(values) > 2 else "unidad"
            costo_unitario = 0.0
            unidad_from_model = current_unit
            found_in_model = False

            # Buscar el item en cualquiera de las categorías del modelo
            for category_in_model, items_in_category_model in self.model.modelos_data.items():
                if not isinstance(items_in_category_model, dict):
                    continue

                key_to_check = item_name

                # Perforación: la clave real en JSON es el diámetro (e.g., "89")
                if (
                    category_in_model == "Perforación"
                    and item_name.startswith("Perforación D")
                    and item_name.endswith("mm")
                ):
                    key_to_check = item_name[len("Perforación D") : -len("mm")]

                if key_to_check in items_in_category_model:
                    item_data = items_in_category_model[key_to_check]
                    try:
                        costo_unitario = float(item_data.get("precio", 0.0))
                    except (ValueError, TypeError):
                        costo_unitario = 0.0
                    unidad_from_model = item_data.get("unidad", current_unit)
                    found_in_model = True
                    break

            if found_in_model:
                new_total_cost = round(cantidad * costo_unitario, 2)
                self.view.table_add_items(
                    [(item_name, round(cantidad, 2), unidad_from_model, new_total_cost)]
                )

        # Recalcular fila total
        self.view.update_totals()

    # --------------------------------------------------------------------- #
    #                 HANDLERS DEL EDITOR (UI secundaria)
    # --------------------------------------------------------------------- #
    def on_moneda_modelo_editor_selected(self, event=None):
        """
        Cuando cambias la moneda en el editor:
        - Actualiza etiqueta de tipo de cambio.
        - Cambia encabezado de columna de costos con la moneda actual.
        """
        self.view._update_tipo_cambio_label_editor()
        self._update_model_editor_ui_for_currency()

    def _update_model_info_widgets(self):
        """
        Pone en los widgets del editor (fecha, moneda, tipo de cambio)
        los valores que existen en el modelo de costos cargado.
        """
        win = getattr(self.view, "modelo_ventana", None)
        if not (win and win.winfo_exists()):
            return

        fecha_str = self.model.modelos_data.get(
            "fecha_modelo", self.model.fecha_modelo_actual
        )
        moneda = self.model.modelos_data.get(
            "moneda_modelo", self.model.moneda_modelo_actual
        )
        tipo_cambio = self.model.modelos_data.get(
            "tipo_cambio_modelo", self.model.tipo_cambio_modelo_actual
        )

        # Fecha segura en el DateEntry
        try:
            fecha_obj = datetime.datetime.strptime(fecha_str, "%Y-%m-%d").date()
            if hasattr(win, "date_entry_model"):
                win.date_entry_model.set_date(fecha_obj)
        except ValueError:
            if hasattr(win, "date_entry_model"):
                win.date_entry_model.set_date(datetime.date.today())
            print(
                f"Advertencia: Fecha '{fecha_str}' en modelo no válida. "
                "Usando fecha actual."
            )

        # Moneda en el combo (o CLP si no está en la lista)
        if hasattr(win, "combo_moneda_modelo"):
            if moneda in win.combo_moneda_modelo["values"]:
                win.combo_moneda_modelo.set(moneda)
            else:
                win.combo_moneda_modelo.set("CLP")
                print(
                    f"Advertencia: Moneda '{moneda}' en modelo no válida. "
                    "Usando CLP."
                )

        # Tipo de cambio en el Entry
        if hasattr(win, "entry_tipo_cambio_modelo_var"):
            win.entry_tipo_cambio_modelo_var.set(str(tipo_cambio))

        # Ajustar etiqueta (CLP por moneda seleccionada)
        self.view._update_tipo_cambio_label_editor()

    def _update_model_editor_ui_for_currency(self):
        """
        Cambia el texto del encabezado de la columna 'Costo unitario' del editor
        para que muestre la moneda que corresponda.
        """
        win = getattr(self.view, "modelo_ventana", None)
        if not (win and win.winfo_exists()):
            return
        if hasattr(win, "tabla_modelo") and win.tabla_modelo.winfo_exists():
            current_currency = self.view._get_current_model_currency()
            win.tabla_modelo.heading(
                "Costo unitario", text=f"Costo unitario ({current_currency})"
            )

    def update_model_window_category_items(self):
        """
        Pone en el combo de 'Categoría' del editor la lista fija y asegura una
        selección válida. Luego actualiza el combo de 'Ítem' según categoría.
        """
        win = getattr(self.view, "modelo_ventana", None)
        if not (win and win.winfo_exists()):
            return
        if hasattr(win, "combo_categoria_edit") and win.combo_categoria_edit:
            win.combo_categoria_edit["values"] = self.model.fixed_categories
            current_selection = win.combo_categoria_edit.get()
            if self.model.fixed_categories:
                if current_selection not in self.model.fixed_categories:
                    win.combo_categoria_edit.set(self.model.fixed_categories[0])
            else:
                win.combo_categoria_edit.set("")
            self.update_model_window_item_list()

    def update_model_window_item_list(self):
        """
        Rellena el combo 'Ítem' del editor según la categoría elegida:
        - Perforación → ingresa diámetro manual (muestra prompt).
        - Explosivo/Detonadores/Iniciadores → carga desde catálogos.
        - Otros → lista vacía (texto libre).
        """
        win = getattr(self.view, "modelo_ventana", None)
        if not (
            win
            and win.winfo_exists()
            and hasattr(win, "combo_categoria_edit")
            and hasattr(win, "combo_item_edit")
        ):
            return

        selected_category = win.combo_categoria_edit.get()
        item_list = []
        prompt_visible = False
        prompt_text = ""

        if selected_category == "Perforación":
            item_list = []
            prompt_text = "Introduce el Diametro de Perforación en Ítem"
            prompt_visible = True
        elif selected_category == "Explosivo":
            if self.model.explosive_db_data and isinstance(
                self.model.explosive_db_data, dict
            ):
                item_list = sorted(list(self.model.explosive_db_data.keys()))
        elif selected_category == "Detonadores":
            if self.model.detonator_db_data and isinstance(
                self.model.detonator_db_data, dict
            ):
                item_list = sorted(list(self.model.detonator_db_data.keys()))
        elif selected_category == "Iniciadores":
            if self.model.booster_db_data and isinstance(
                self.model.booster_db_data, dict
            ):
                item_list = sorted(list(self.model.booster_db_data.keys()))
        elif selected_category == "Otros":
            item_list = []

        # Mostrar/ocultar prompt de ayuda sobre el campo Ítem
        if hasattr(win, "label_item_prompt") and win.label_item_prompt.winfo_exists():
            win.label_item_prompt.config(text=prompt_text)

        if (
            hasattr(win, "item_prompt_container_frame")
            and win.item_prompt_container_frame.winfo_exists()
            and hasattr(win, "cat_item_frame")
            and win.cat_item_frame.winfo_exists()
        ):
            is_prompt_mapped = win.item_prompt_container_frame.winfo_ismapped()
            if prompt_visible and not is_prompt_mapped:
                win.item_prompt_container_frame.pack(
                    fill="x", padx=10, pady=(2, 0), before=win.cat_item_frame
                )
            elif not prompt_visible and is_prompt_mapped:
                win.item_prompt_container_frame.pack_forget()

        # Cargar opciones y estado del combo Ítem
        win.combo_item_edit["values"] = item_list
        win.combo_item_edit.set("")
        win.combo_item_edit.config(state="readonly" if item_list else tk.NORMAL)

    def populate_model_table_with_model_data(self):
        """
        Vuelca TODOS los ítems del modelo de costos a la tabla del editor,
        convirtiendo Perforación 'xx' → 'Perforación Dxxmm' para mostrar.
        """
        win = getattr(self.view, "modelo_ventana", None)
        if not (win and win.winfo_exists()) or not hasattr(win, "tabla_modelo"):
            return

        # Limpiar tabla del editor
        win.tabla_modelo.delete(*win.tabla_modelo.get_children())

        # Construir una lista ordenada por nombre visible
        all_model_items_for_table = []
        for category, items_in_category in self.model.modelos_data.items():
            if category in ["fecha_modelo", "moneda_modelo", "tipo_cambio_modelo"]:
                continue
            if isinstance(items_in_category, dict):
                for item_key, item_data_dict in items_in_category.items():
                    if isinstance(item_data_dict, dict):
                        unidad = item_data_dict.get("unidad", "")
                        precio = item_data_dict.get("precio", 0.0)
                        item_display_name = item_key
                        if category == "Perforación":
                            item_display_name = f"Perforación D{item_key}mm"
                        all_model_items_for_table.append(
                            (item_display_name, unidad, precio)
                        )

        # Insertar ordenado por nombre
        all_model_items_for_table.sort(key=lambda x: x[0])
        for name, unit, cost in all_model_items_for_table:
            win.tabla_modelo.insert("", tk.END, values=(name, unit, cost))

    def on_model_edit_focus_out(self, event=None):
        """
        Cuando el combo del nombre de modelo pierde foco, no forzamos cambios;
        mantenemos el flujo original (no hace nada si el nombre difiere).
        """
        win = getattr(self.view, "modelo_ventana", None)
        if not (win and win.winfo_exists()) or not hasattr(win, "combo_model_edit"):
            return
        current_text = win.combo_model_edit.get().strip()
        if current_text and current_text != self.model.modelo_actual_nombre:
            # Sin acción: se respeta el flujo original.
            pass

    def on_model_edit_selected(self, event=None):
        """
        Al seleccionar un modelo existente en el editor:
        - Carga ese modelo si es distinto al activo.
        - Re-pinta tabla y widgets auxiliares (fecha/moneda/tipo cambio).
        """
        win = getattr(self.view, "modelo_ventana", None)
        if not (win and win.winfo_exists()) or not hasattr(win, "combo_model_edit"):
            return
        selected_model = win.combo_model_edit.get()
        if not selected_model or selected_model not in self.model.get_existing_models():
            win.combo_model_edit.set(self.model.modelo_actual_nombre)
            return
        if selected_model != self.model.modelo_actual_nombre:
            self.cambiar_modelo(selected_model)
        else:
            self.model.load_modelos_data(self.model.modelo_actual_nombre)

        self.populate_model_table_with_model_data()
        self.update_model_window_category_items()
        self._update_model_info_widgets()
        self._update_model_editor_ui_for_currency()

    def on_model_edit_enter(self, event=None):
        """
        Si el usuario escribe un nombre de modelo nuevo y presiona Enter:
        - Pregunta si desea crearlo.
        - Si acepta, crea estructura por defecto, guarda, y refresca UI.
        """
        win = getattr(self.view, "modelo_ventana", None)
        if not (win and win.winfo_exists()) or not hasattr(win, "combo_model_edit"):
            return
        new_model_name = win.combo_model_edit.get().strip()
        if not new_model_name:
            return

        existing_models = self.model.get_existing_models()
        if new_model_name not in existing_models:
            confirm_new = messagebox.askyesno(
                "Crear Nuevo Modelo",
                f"El modelo '{new_model_name}' no existe. ¿Desea crearlo?",
                parent=win,
            )
            if not confirm_new:
                win.combo_model_edit.set(self.model.modelo_actual_nombre)
                return

            # Crear nuevo con estructura por defecto y persistir
            self.model.modelo_actual_nombre = new_model_name
            self.model.modelos_data = {
                "fecha_modelo": datetime.date.today().strftime("%Y-%m-%d"),
                "moneda_modelo": "CLP",
                "tipo_cambio_modelo": 1.0,
                **{cat: {} for cat in self.model.fixed_categories},
            }
            self.model.save_modelos_data()

            # Refrescar combos/tablas/labels del editor
            self.update_main_window_model_selector()
            win.combo_model_edit["values"] = self.model.get_existing_models()
            win.combo_model_edit.set(new_model_name)

            self.populate_model_table_with_model_data()
            self.update_model_window_category_items()
            self._update_model_info_widgets()
            self._update_model_editor_ui_for_currency()

            # Que la ventana principal reaccione al cambio de modelo
            self.cambiar_modelo_evento()

        elif new_model_name != self.model.modelo_actual_nombre:
            # Si es un modelo existente distinto al activo
            self.cambiar_modelo(new_model_name)

    def on_categoria_edit_selected(self, event=None):
        """Cuando cambia la categoría en el editor, refresca el combo Ítem."""
        self.update_model_window_item_list()

    def on_categoria_edit_enter(self, event=None):
        """
        Enter sobre el combo Categoría: recordatorio de que son fijas,
        y reponer una selección válida si el valor no es aceptado.
        """
        win = getattr(self.view, "modelo_ventana", None)
        if not (win and win.winfo_exists()):
            return
        messagebox.showinfo(
            "Información",
            "Las categorías son predefinidas y no se pueden añadir nuevas.",
            parent=win,
        )
        current_selection = win.combo_categoria_edit.get()
        if (
            current_selection not in self.model.fixed_categories
            and self.model.fixed_categories
        ):
            win.combo_categoria_edit.set(self.model.fixed_categories[0])
        elif not self.model.fixed_categories:
            win.combo_categoria_edit.set("")

    def on_item_edit_selected_model_window(self, event=None):
        """
        Al escoger un ítem en el combo del editor:
        - Determina unidad por defecto según la categoría (y catálogos).
        - Evita duplicados en la tabla.
        - Si el ítem ya existía en el modelo, usa sus valores guardados.
        - Inserta la fila en la tabla del editor.
        """
        win = getattr(self.view, "modelo_ventana", None)
        if not (
            win
            and win.winfo_exists()
            and hasattr(win, "combo_item_edit")
            and hasattr(win, "combo_categoria_edit")
        ):
            return

        selected_item_key = win.combo_item_edit.get()
        selected_category = win.combo_categoria_edit.get()
        if not selected_item_key or not selected_category:
            return

        item_display_name = selected_item_key
        default_unidad = "unidad"
        default_precio = 0.0

        # Unidad por defecto según categoría/DB
        if selected_category == "Explosivo":
            if (
                self.model.explosive_db_data
                and selected_item_key in self.model.explosive_db_data
            ):
                explosive_item_data = self.model.explosive_db_data[selected_item_key]
                default_unidad = (
                    "unidad" if explosive_item_data.get("cartridge", False) else "kg"
                )
            else:
                default_unidad = "kg"
        elif selected_category == "Perforación":
            default_unidad = "m"
            if selected_item_key.isdigit():
                item_display_name = f"Perforación D{selected_item_key}mm"
            else:
                # Si no es un número, no es válido como diámetro
                win.combo_item_edit.set("")
                return
        elif selected_category in ("Detonadores", "Iniciadores"):
            default_unidad = "unidad"
        elif selected_category == "Otros":
            default_unidad = "unidad"

        # Evitar duplicados en la tabla del editor
        for iid_row in win.tabla_modelo.get_children():
            if win.tabla_modelo.item(iid_row)["values"][0] == item_display_name:
                messagebox.showwarning(
                    "Ítem Duplicado",
                    f"El ítem '{item_display_name}' ya está en la tabla del modelo.",
                    parent=win,
                )
                win.tabla_modelo.selection_set(iid_row)
                win.tabla_modelo.see(iid_row)
                win.combo_item_edit.set("")
                return

        # Si el ítem ya existía guardado en el JSON, respetar sus valores
        unidad_to_add = default_unidad
        price_to_add = default_precio
        key_for_model_lookup = selected_item_key

        if (
            selected_category in self.model.modelos_data
            and isinstance(self.model.modelos_data.get(selected_category), dict)
            and key_for_model_lookup in self.model.modelos_data[selected_category]
        ):
            item_data_in_model = self.model.modelos_data[selected_category][
                key_for_model_lookup
            ]
            unidad_to_add = item_data_in_model.get("unidad", default_unidad)
            price_to_add = float(item_data_in_model.get("precio", default_precio))

        # Insertar en la tabla del editor y enfocar
        new_iid = win.tabla_modelo.insert(
            "", tk.END, values=(item_display_name, unidad_to_add, round(price_to_add, 2))
        )
        win.tabla_modelo.selection_set(new_iid)
        win.tabla_modelo.see(new_iid)
        win.combo_item_edit.set("")
