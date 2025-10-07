# view/costos_view.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkcalendar import DateEntry
import datetime


class CostsAnalysisis(tk.Frame):
    def __init__(self, root, controller, model):
        super().__init__(root)
        self.controller = controller
        self.model = model

        self.master.title("Costos")
        self.master.geometry("550x430")

        # --- Top ---
        top_frame = tk.Frame(self)
        top_frame.pack(pady=(10, 0), fill="x", padx=10)

        tk.Label(top_frame, text="Modelo:").pack(side=tk.LEFT, padx=(0, 2))
        self.combo_modelo_selector = ttk.Combobox(
            top_frame,
            values=self.model.get_existing_models(),
            width=20
        )
        self.combo_modelo_selector.set(self.model.modelo_actual_nombre)
        self.combo_modelo_selector.pack(side=tk.LEFT, padx=5)
        self.combo_modelo_selector.bind(
            "<<ComboboxSelected>>",
            lambda e: self.controller.cambiar_modelo_evento()
        )

        tk.Button(top_frame, text="Modelos", command=self.abrir_ventana_modelos)\
          .pack(side=tk.LEFT, padx=10)

        # --- Tronadura ---
        tronadura_frame = tk.Frame(self)
        tronadura_frame.pack(pady=(10, 0), fill="x", padx=10)

        tk.Label(tronadura_frame, text="Tronadura:").pack(side=tk.LEFT, padx=(0, 2))
        self.combo_tronadura = ttk.Combobox(tronadura_frame, width=25)
        self.combo_tronadura.pack(side=tk.LEFT, padx=5)
        self.combo_tronadura.bind(
            "<<ComboboxSelected>>",
            lambda e: self.controller.on_tronadura_selected()
        )

        # --- Tabla principal ---
        self.data_table = ttk.Treeview(
            self,
            columns=("Ítem", "Cantidad", "Unidad", "Total (Costo)"),
            show="headings"
        )
        for col in ("Ítem", "Cantidad", "Unidad", "Total (Costo)"):
            self.data_table.heading(col, text=col)
            anchor_val = tk.W if col == "Ítem" else tk.CENTER
            width_val = 180 if col == "Ítem" else 100
            self.data_table.column(col, width=width_val, anchor=anchor_val)
        self.data_table.pack(pady=10, fill="both", expand=True, padx=10)
        self.data_table.bind("<Double-1>", self.edit_cell_table)

        # --- Botones ---
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=(0, 10))
        tk.Button(btn_frame, text="Eliminar fila seleccionada",
                  command=self.eliminar_fila_tabla).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Añadir ítem manual",
                  command=self.añadir_item_manual).pack(side=tk.LEFT, padx=5)


    # ===== Puentes / Delegación al Controller (mismos nombres públicos) =====
    def cargar_tronaduras(self):
        return self.controller.cargar_tronaduras()

    def cargar_holes(self):
        return self.controller.cargar_holes()

    def on_tronadura_selected(self, event=None):
        return self.controller.on_tronadura_selected()

    def recalculate_table_costs(self, event=None):
        return self.controller.recalculate_table_costs(event)

    def cambiar_modelo_evento(self, event=None):
        return self.controller.cambiar_modelo_evento()

    def cambiar_modelo(self, nombre_modelo):
        # Simula selección en combo principal y dispara el flujo normal
        self.combo_modelo_selector.set(nombre_modelo)
        return self.controller.cambiar_modelo_evento()

    # ===== Métodos de soporte de UI =====
    def combo_modelo_selector_set_options(self, opciones):
        self.combo_modelo_selector["values"] = opciones

    def combo_modelo_selector_set(self, nombre):
        self.combo_modelo_selector.set(nombre)

    def get_combo_modelo_value(self):
        return self.combo_modelo_selector.get()

    def combo_tronadura_set_options(self, opciones):
        self.combo_tronadura["values"] = opciones

    def combo_tronadura_set(self, valor):
        self.combo_tronadura.set(valor)

    def get_combo_tronadura_value(self):
        return self.combo_tronadura.get()

    def table_clear(self):
        if hasattr(self, 'data_table') and self.data_table.winfo_exists():
            for iid in self.data_table.get_children():
                self.data_table.delete(iid)

    def table_add_items(self, filas):
        for row in filas:
            self.data_table.insert("", "end", values=row)

    # ===== Moneda / Títulos =====
    def _get_current_model_currency(self):
        # Si el editor está abierto y tiene moneda seleccionada, úsala (comportamiento original)
        if hasattr(self, 'modelo_ventana') and self.modelo_ventana and self.modelo_ventana.winfo_exists() and \
           hasattr(self.modelo_ventana, 'combo_moneda_modelo') and self.modelo_ventana.combo_moneda_modelo.winfo_exists():
            current_editor_currency = self.modelo_ventana.combo_moneda_modelo.get()
            if current_editor_currency:
                return current_editor_currency
        return self.model.modelos_data.get("moneda_modelo", self.model.moneda_modelo_actual)

    def _update_main_app_ui_for_currency(self):
        if hasattr(self, 'data_table') and self.data_table.winfo_exists():
            current_currency = self._get_current_model_currency()
            self.data_table.heading("Total (Costo)", text=f"Costo total ({current_currency})")
            self.update_totals()

    # ===== Pintado de filas "Otros" (solo UI) =====
    def _add_otros_items_to_main_table(self):
        if not hasattr(self, 'data_table') or not self.data_table.winfo_exists():
            return

        otros_items_en_modelo = self.model.modelos_data.get("Otros", {})
        if not isinstance(otros_items_en_modelo, dict) or not otros_items_en_modelo:
            return

        nombres_items_en_tabla = []
        for iid_tabla in self.data_table.get_children():
            if "total_row" not in self.data_table.item(iid_tabla)['tags']:
                valores_fila = self.data_table.item(iid_tabla)['values']
                if valores_fila and len(valores_fila) > 0:
                    nombres_items_en_tabla.append(valores_fila[0])

        for item_nombre_otro, item_data_otro in otros_items_en_modelo.items():
            if item_nombre_otro not in nombres_items_en_tabla:
                unidad = item_data_otro.get("unidad", "unidad")
                try:
                    costo_unitario = float(item_data_otro.get("precio", 0.0))
                except (ValueError, TypeError):
                    costo_unitario = 0.0

                cantidad = 0.0
                total_costo = round(cantidad * costo_unitario, 2)

                total_row_iid = None
                for iid_check in self.data_table.get_children():
                    if "total_row" in self.data_table.item(iid_check)['tags']:
                        total_row_iid = iid_check
                        break

                if total_row_iid:
                    self.data_table.insert(
                        self.data_table.parent(total_row_iid),
                        self.data_table.index(total_row_iid),
                        values=(item_nombre_otro, round(cantidad, 2), unidad, total_costo)
                    )
                else:
                    self.data_table.insert(
                        "", tk.END,
                        values=(item_nombre_otro, round(cantidad, 2), unidad, total_costo)
                    )

    # ===== Totales (solo UI) =====
    def update_totals(self):
        total_item_name = f" Costo total ({self._get_current_model_currency()})"
        total_row_iid = None
        if hasattr(self, 'data_table') and self.data_table.winfo_exists():
            for iid in self.data_table.get_children():
                if "total_row" in self.data_table.item(iid)['tags']:
                    total_row_iid = iid
                    break
            if total_row_iid:
                self.data_table.delete(total_row_iid)

            suma_total = 0.0
            for iid in self.data_table.get_children():
                if "total_row" in self.data_table.item(iid)['tags']:
                    continue
                try:
                    cost_value = self.data_table.item(iid)["values"][3]
                    suma_total += float(cost_value)
                except (ValueError, TypeError, IndexError):
                    pass
            total_iid = self.data_table.insert("", tk.END, values=(total_item_name, "", "", round(suma_total, 2)))
            self.data_table.tag_configure("total_row", background="#e0e0e0", font=('TkDefaultFont', 10, 'bold'))
            self.data_table.item(total_iid, tags=("total_row",))

    # ===== Handlers de tabla principal (UI + delegación al recálculo) =====
    def eliminar_fila_tabla(self, event=None):
        if not hasattr(self, 'data_table'):
            return
        sel = self.data_table.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una fila para eliminar.", parent=self.master)
            return
        iid = sel[0]
        if "total_row" in self.data_table.item(iid)['tags']:
            messagebox.showwarning("Atención", "No se puede eliminar la fila de Totales.", parent=self.master)
            return
        self.data_table.delete(iid)
        self.update_totals()

    def edit_cell_table(self, event):
        if not hasattr(self, 'data_table'):
            return
        region = self.data_table.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_iid = self.data_table.identify_row(event.y)
        col_id_str = self.data_table.identify_column(event.x)
        col_index_visual = int(col_id_str.replace('#', ''))
        if col_index_visual != 2:  # Solo 'Cantidad'
            messagebox.showwarning("Edición no permitida", "Solo se puede editar la columna 'Cantidad'.", parent=self.master)
            return
        if "total_row" in self.data_table.item(row_iid)['tags']:
            return

        x, y, w, h = self.data_table.bbox(row_iid, col_id_str)
        current_values = self.data_table.item(row_iid)["values"]
        original_value = current_values[1]

        entry_editor = tk.Entry(self.data_table)
        entry_editor.place(x=x, y=y, width=w, height=h)
        entry_editor.insert(0, str(original_value))
        entry_editor.select_range(0, tk.END)
        entry_editor.focus()

        def on_save_edit(_=None):
            new_quantity_str = entry_editor.get()
            entry_editor.destroy()
            try:
                new_quantity = float(new_quantity_str)
                if new_quantity < 0:
                    new_quantity = 0.0
            except ValueError:
                messagebox.showerror("Entrada inválida", "La cantidad debe ser un número.", parent=self.master)
                return

            # UI: solo actualiza cantidad; el Controller recalcula costos
            updated_values = list(current_values)
            updated_values[1] = round(new_quantity, 2)
            self.data_table.item(row_iid, values=tuple(updated_values))

            # Disparar recálculo coordinado
            self.recalculate_table_costs()

        entry_editor.bind("<Return>", on_save_edit)
        entry_editor.bind("<FocusOut>", on_save_edit)
        entry_editor.bind("<Escape>", lambda e: entry_editor.destroy())

    def añadir_item_manual(self):
        item_name = simpledialog.askstring("Añadir Ítem Manual", "Nombre del Ítem:", parent=self.master)
        if not item_name or not item_name.strip():
            return
        item_name = item_name.strip()

        cantidad_str = simpledialog.askstring("Añadir Ítem Manual", f"Cantidad para '{item_name}':", parent=self.master)
        if cantidad_str is None:
            return
        try:
            cantidad = float(cantidad_str)
            if cantidad < 0:
                cantidad = 0.0
        except ValueError:
            messagebox.showwarning("Entrada Inválida", "Por favor, ingrese un valor numérico para la cantidad.", parent=self.master)
            return

        # UI: merge/insert sin tocar precios; Controller recalcula luego
        merged = False
        for iid in self.data_table.get_children():
            if "total_row" in self.data_table.item(iid)['tags']:
                continue
            values = list(self.data_table.item(iid)["values"])
            if values and len(values) > 0 and values[0] == item_name:
                try:
                    existing_cantidad = float(values[1])
                except (ValueError, TypeError):
                    existing_cantidad = 0.0
                new_cantidad = round(existing_cantidad + cantidad, 2)
                values[1] = new_cantidad
                self.data_table.item(iid, values=tuple(values))
                merged = True
                break

        if not merged:
            # Insertar antes de Totales (si existe)
            total_row_iid = None
            for iid in self.data_table.get_children():
                if "total_row" in self.data_table.item(iid)['tags']:
                    total_row_iid = iid
                    break
            row_values = (item_name, round(cantidad, 2), "unidad", 0.0)
            if total_row_iid:
                self.data_table.insert(self.data_table.parent(total_row_iid), self.data_table.index(total_row_iid), values=row_values)
            else:
                self.data_table.insert("", tk.END, values=row_values)

        # Disparar recálculo coordinado
        self.recalculate_table_costs()

    # ===== Ventana de modelos (UI pura; delega handlers al Controller) =====
    def abrir_ventana_modelos(self):
        if hasattr(self, 'modelo_ventana') and self.modelo_ventana and self.modelo_ventana.winfo_exists():
            self.modelo_ventana.lift()
            return

        self.modelo_ventana = tk.Toplevel(self.master)
        self.modelo_ventana.title("Editor de Modelos de Costos")
        self.modelo_ventana.geometry("550x430")
        self.modelo_ventana.transient(self.master)
        self.modelo_ventana.grab_set()

        # Carga de DB en el Model (IO)
        self.model.load_explosive_db_data()
        self.model.load_detonator_db_data()
        self.model.load_booster_db_data()

        # --- Encabezado selección de modelo ---
        model_selection_frame = tk.Frame(self.modelo_ventana)
        model_selection_frame.pack(pady=(10, 5), padx=10, fill="x")

        tk.Label(model_selection_frame, text="Modelo a Editar/Crear:").pack(side=tk.LEFT, padx=(0, 5))
        self.modelo_ventana.combo_model_edit = ttk.Combobox(
            model_selection_frame,
            values=self.model.get_existing_models(),
            width=30
        )
        self.modelo_ventana.combo_model_edit.set(self.model.modelo_actual_nombre)
        self.modelo_ventana.combo_model_edit.pack(side=tk.LEFT, expand=True, fill="x")

        # Delegar a Controller (mismos nombres); fallback si aún no los pegas
        self.modelo_ventana.combo_model_edit.bind(
            "<<ComboboxSelected>>",
            getattr(self.controller, "on_model_edit_selected", lambda e: None)
        )
        self.modelo_ventana.combo_model_edit.bind(
            "<Return>",
            getattr(self.controller, "on_model_edit_enter", lambda e: None)
        )
        self.modelo_ventana.combo_model_edit.bind(
            "<FocusOut>",
            getattr(self.controller, "on_model_edit_focus_out", lambda e: None)
        )

        # --- Info general del modelo ---
        model_info_frame = tk.Frame(self.modelo_ventana)
        model_info_frame.pack(pady=5, padx=10, fill="x")

        tk.Label(model_info_frame, text="Fecha:").grid(row=0, column=0, padx=(0, 5), pady=2, sticky="w")
        self.modelo_ventana.date_entry_model = DateEntry(
            model_info_frame, width=12, background='darkblue',
            foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd',
            locale='es_ES'
        )
        self.modelo_ventana.date_entry_model.grid(row=0, column=1, padx=(0, 10), pady=2, sticky="w")

        tk.Label(model_info_frame, text="Moneda:").grid(row=0, column=2, padx=(0, 5), pady=2, sticky="w")
        monedas = ["CLP", "USD", "EUR", "JPY", "AUD", "CAD", "MXN", "BRL"]
        self.modelo_ventana.combo_moneda_modelo = ttk.Combobox(
            model_info_frame, values=monedas, width=6, state="readonly"
        )
        self.modelo_ventana.combo_moneda_modelo.grid(row=0, column=3, padx=(0, 10), pady=2, sticky="w")

        # Evento de moneda → Controller
        self.modelo_ventana.combo_moneda_modelo.bind(
            "<<ComboboxSelected>>",
            getattr(self.controller, "on_moneda_modelo_editor_selected", lambda e: None)
        )

        self.modelo_ventana.label_tipo_cambio = tk.Label(model_info_frame, text="Tipo de Cambio:")
        self.modelo_ventana.label_tipo_cambio.grid(row=0, column=4, padx=(0, 5), pady=2, sticky="w")
        self.modelo_ventana.entry_tipo_cambio_modelo_var = tk.StringVar()
        self.modelo_ventana.entry_tipo_cambio_modelo = tk.Entry(
            model_info_frame, width=8, textvariable=self.modelo_ventana.entry_tipo_cambio_modelo_var
        )
        self.modelo_ventana.entry_tipo_cambio_modelo.grid(row=0, column=5, pady=2, sticky="w")
        self.modelo_ventana.label_tipo_cambio_unidad = tk.Label(model_info_frame, text="CLP")
        self.modelo_ventana.label_tipo_cambio_unidad.grid(row=0, column=6, padx=(2, 0), pady=2, sticky="w")

        model_info_frame.grid_columnconfigure(1, weight=0)
        model_info_frame.grid_columnconfigure(3, weight=0)
        model_info_frame.grid_columnconfigure(5, weight=0)

        # --- Prompt / categoría / ítem ---
        self.modelo_ventana.item_prompt_container_frame = tk.Frame(self.modelo_ventana)
        self.modelo_ventana.label_item_prompt = tk.Label(
            self.modelo_ventana.item_prompt_container_frame,
            text="", fg="blue", font=('TkDefaultFont', 8)
        )
        self.modelo_ventana.label_item_prompt.pack(side=tk.LEFT, padx=0, pady=0)

        self.modelo_ventana.cat_item_frame = tk.Frame(self.modelo_ventana)
        self.modelo_ventana.cat_item_frame.pack(pady=(5, 5), padx=10, fill="x")

        tk.Label(self.modelo_ventana.cat_item_frame, text="Categoría:").pack(side=tk.LEFT, padx=(0, 5))
        self.modelo_ventana.combo_categoria_edit = ttk.Combobox(
            self.modelo_ventana.cat_item_frame,
            values=self.model.fixed_categories, width=20, state="readonly"
        )
        self.modelo_ventana.combo_categoria_edit.pack(side=tk.LEFT, padx=(0, 10))
        self.modelo_ventana.combo_categoria_edit.bind(
            "<<ComboboxSelected>>",
            getattr(self.controller, "on_categoria_edit_selected", lambda e: None)
        )

        tk.Label(self.modelo_ventana.cat_item_frame, text="Ítem:").pack(side=tk.LEFT, padx=(10, 5))
        self.modelo_ventana.combo_item_edit = ttk.Combobox(
            self.modelo_ventana.cat_item_frame, values=[], width=25
        )
        self.modelo_ventana.combo_item_edit.pack(side=tk.LEFT, expand=True, fill="x")
        self.modelo_ventana.combo_item_edit.bind(
            "<<ComboboxSelected>>",
            getattr(self.controller, "on_item_edit_selected_model_window", lambda e: None)
        )
        self.modelo_ventana.combo_item_edit.bind(
            "<Return>",
            getattr(self.controller, "on_item_edit_enter_model_window", lambda e: None)
        )

        # --- Tabla del editor de modelo ---
        self.modelo_ventana.tabla_modelo = ttk.Treeview(
            self.modelo_ventana,
            columns=("Ítem", "Unidad", "Costo unitario"),
            show="headings"
        )
        self.modelo_ventana.tabla_modelo.heading("Ítem", text="Ítem")
        self.modelo_ventana.tabla_modelo.heading("Unidad", text="Unidad")
        self.modelo_ventana.tabla_modelo.heading(
            "Costo unitario", text=f"Costo unitario ({self._get_current_model_currency()})"
        )
        self.modelo_ventana.tabla_modelo.column("Ítem", width=200, anchor=tk.W)
        self.modelo_ventana.tabla_modelo.column("Unidad", width=100, anchor=tk.CENTER)
        self.modelo_ventana.tabla_modelo.column("Costo unitario", width=120, anchor=tk.CENTER)
        self.modelo_ventana.tabla_modelo.pack(pady=10, padx=10, fill="both", expand=True)

        # Doble click sobre celdas (si tienes edit_cell en Controller, úsalo; si no, no-ops)
        self.modelo_ventana.tabla_modelo.bind(
            "<Double-1>",
            lambda e: getattr(self.controller, "edit_cell", lambda *a, **k: None)(
                e, self.modelo_ventana.tabla_modelo
            )
        )

        # --- Acciones del editor ---
        acciones_frame_modelos = tk.Frame(self.modelo_ventana)
        acciones_frame_modelos.pack(pady=5, padx=10, fill="x")
        tk.Button(
            acciones_frame_modelos, text="Eliminar Fila de Tabla",
            command=getattr(self.controller, "delete_row_model_table", lambda: None)
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            acciones_frame_modelos, text="Guardar Modelo Actual",
            command=getattr(self.controller, "save_modelo_from_table", lambda: None)
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            acciones_frame_modelos, text="Eliminar Modelo Completo",
            command=getattr(self.controller, "eliminar_modelo_completo", lambda: None)
        ).pack(side=tk.LEFT, padx=5)

        # --- Inicialización de estado del editor (delegada al Controller) ---
        getattr(self.controller, "update_model_window_category_items", lambda: None)()
        getattr(self.controller, "populate_model_table_with_model_data", lambda: None)()
        getattr(self.controller, "_update_model_info_widgets", lambda: None)()
        self._update_tipo_cambio_label_editor()
        getattr(self.controller, "_update_model_editor_ui_for_currency", lambda: None)()

    # ===== Pequeño helper de UI que el Controller puede llamar =====
    def _update_tipo_cambio_label_editor(self):
        if not (hasattr(self, 'modelo_ventana') and self.modelo_ventana and self.modelo_ventana.winfo_exists()):
            return
        if hasattr(self.modelo_ventana, 'label_tipo_cambio') and self.modelo_ventana.label_tipo_cambio.winfo_exists() and \
           hasattr(self.modelo_ventana, 'combo_moneda_modelo') and self.modelo_ventana.combo_moneda_modelo.winfo_exists():
            moneda_seleccionada = self.modelo_ventana.combo_moneda_modelo.get()
            if not moneda_seleccionada:
                moneda_seleccionada = self.model.modelos_data.get("moneda_modelo", self.model.moneda_modelo_actual)

            if hasattr(self.modelo_ventana, 'label_tipo_cambio_unidad'):
                self.modelo_ventana.label_tipo_cambio_unidad.config(text=f"({moneda_seleccionada} por CLP)")

            self.modelo_ventana.label_tipo_cambio.config(text="Tipo de Cambio:")
