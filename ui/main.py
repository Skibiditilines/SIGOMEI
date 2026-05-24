"""
ui/main.py
===========
Interfaz gráfica principal de SIGOMEI — CustomTkinter.

Ventana con tres pestañas (Equipos / Técnicos / Órdenes) y una barra
de conexión al servidor TCP.  Cada pestaña está preparada para extenderse
con formularios CRUD completos conectados a SigomeiAPI.

Uso:
    cd ui/
    python main.py [--host 127.0.0.1] [--port 9000]
"""

import argparse
import sys
import os
import threading
import tkinter as tk
from tkinter import messagebox

# ---------------------------------------------------------------------------
# Resolución de imports: agrega ui/ al path
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import customtkinter as ctk
from client.api import SigomeiAPI, SigomeiAPIError
from client.socket_client import ConnectionError as SigomeiConnError

# ---------------------------------------------------------------------------
# Tema y apariencia
# ---------------------------------------------------------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FONT_TITLE  = ("Segoe UI", 22, "bold")
FONT_HEADER = ("Segoe UI", 13, "bold")
FONT_BODY   = ("Segoe UI", 12)
FONT_SMALL  = ("Segoe UI", 10)
FONT_MONO   = ("Consolas", 11)

COLOR_BG        = "#1a1a2e"
COLOR_SURFACE   = "#16213e"
COLOR_CARD      = "#0f3460"
COLOR_ACCENT    = "#e94560"
COLOR_SUCCESS   = "#2ecc71"
COLOR_WARNING   = "#f39c12"
COLOR_TEXT      = "#eaeaea"
COLOR_MUTED     = "#8892b0"
COLOR_CONNECTED = "#2ecc71"
COLOR_DISCONN   = "#e74c3c"

TIPOS_EQUIPO    = ["Mecanico", "Electrico", "Hidraulico", "Neumatico", "Electronico"]
ESTADOS_OP      = ["Disponible", "En Mantenimiento", "Fuera de Servicio"]
CRITICIDADES    = ["Normal", "Alta"]
NIVELES_CERT    = ["I", "II", "III"]
ESTATUSES_TEC   = ["Activo", "Inactivo"]
TIPOS_MANT      = ["Preventivo", "Correctivo", "Predictivo"]
ESTADOS_ORDEN   = ["Programada", "En ejecucion", "Finalizada", "Cancelada"]


# ===========================================================================
# Componentes reutilizables
# ===========================================================================

def make_label(parent, text, font=None, color=None, **kwargs):
    return ctk.CTkLabel(
        parent, text=text,
        font=font or FONT_BODY,
        text_color=color or COLOR_TEXT,
        **kwargs
    )


def make_entry(parent, placeholder="", width=220, **kwargs):
    return ctk.CTkEntry(
        parent,
        placeholder_text=placeholder,
        width=width,
        font=FONT_BODY,
        fg_color=COLOR_SURFACE,
        border_color=COLOR_CARD,
        **kwargs
    )


def make_button(parent, text, command, fg=None, width=120, **kwargs):
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        font=FONT_BODY,
        fg_color=fg or COLOR_ACCENT,
        hover_color="#c0392b" if (fg is None or fg == COLOR_ACCENT) else "#27ae60",
        width=width,
        corner_radius=8,
        **kwargs
    )


def make_optionmenu(parent, values, variable, width=220):
    return ctk.CTkOptionMenu(
        parent,
        values=values,
        variable=variable,
        font=FONT_BODY,
        fg_color=COLOR_SURFACE,
        button_color=COLOR_CARD,
        button_hover_color=COLOR_ACCENT,
        dropdown_fg_color=COLOR_SURFACE,
        width=width,
    )


def make_section_title(parent, text):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", padx=20, pady=(18, 4))
    ctk.CTkLabel(
        frame, text=text,
        font=FONT_HEADER,
        text_color=COLOR_ACCENT,
    ).pack(anchor="w")
    ctk.CTkFrame(frame, height=2, fg_color=COLOR_CARD).pack(fill="x", pady=(4, 0))
    return frame


# ===========================================================================
# Tab: Equipos
# ===========================================================================

class EquiposTab(ctk.CTkFrame):
    """Pestaña de gestión de Equipos."""

    def __init__(self, parent, api: SigomeiAPI):
        super().__init__(parent, fg_color="transparent")
        self.api = api
        self._build_ui()

    def _build_ui(self):
        # ---- Formulario de registro ----
        make_section_title(self, "➕  Registrar Equipo")
        form = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=12)
        form.pack(fill="x", padx=20, pady=6)

        grid = ctk.CTkFrame(form, fg_color="transparent")
        grid.pack(padx=16, pady=16)

        # Fila 0
        make_label(grid, "Serie *").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self.ent_serie = make_entry(grid, "Número de serie")
        self.ent_serie.grid(row=0, column=1, padx=8, pady=4)

        make_label(grid, "Marca").grid(row=0, column=2, sticky="w", padx=8, pady=4)
        self.ent_marca = make_entry(grid, "Marca del equipo")
        self.ent_marca.grid(row=0, column=3, padx=8, pady=4)

        # Fila 1
        make_label(grid, "Modelo").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self.ent_modelo = make_entry(grid, "Modelo")
        self.ent_modelo.grid(row=1, column=1, padx=8, pady=4)

        make_label(grid, "Tipo").grid(row=1, column=2, sticky="w", padx=8, pady=4)
        self.var_tipo = tk.StringVar(value=TIPOS_EQUIPO[0])
        make_optionmenu(grid, TIPOS_EQUIPO, self.var_tipo).grid(row=1, column=3, padx=8, pady=4)

        # Fila 2
        make_label(grid, "Ubicación").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        self.ent_ubicacion = make_entry(grid, "Ubicación física")
        self.ent_ubicacion.grid(row=2, column=1, padx=8, pady=4)

        make_label(grid, "Estado").grid(row=2, column=2, sticky="w", padx=8, pady=4)
        self.var_estado = tk.StringVar(value=ESTADOS_OP[0])
        make_optionmenu(grid, ESTADOS_OP, self.var_estado).grid(row=2, column=3, padx=8, pady=4)

        # Fila 3
        make_label(grid, "Criticidad").grid(row=3, column=0, sticky="w", padx=8, pady=4)
        self.var_criticidad = tk.StringVar(value=CRITICIDADES[0])
        make_optionmenu(grid, CRITICIDADES, self.var_criticidad, width=120).grid(
            row=3, column=1, sticky="w", padx=8, pady=4
        )

        btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_frame.pack(pady=(0, 12))
        make_button(btn_frame, "Registrar", self._registrar, width=160).pack(side="left", padx=8)
        make_button(btn_frame, "Limpiar", self._limpiar_form, fg=COLOR_CARD, width=100).pack(side="left", padx=4)

        # ---- Búsqueda y listado ----
        make_section_title(self, "🔍  Buscar / Listar Equipos")
        search_frame = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=12)
        search_frame.pack(fill="x", padx=20, pady=6)

        search_row = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_row.pack(padx=16, pady=12)
        self.ent_buscar = make_entry(search_row, "Término de búsqueda...", width=320)
        self.ent_buscar.pack(side="left", padx=8)
        make_button(search_row, "Buscar", self._buscar, width=100).pack(side="left", padx=4)
        make_button(search_row, "Listar todos", self._listar, fg="#1a6b4a", width=120).pack(side="left", padx=4)

        # Tabla de resultados
        self.tabla = ctk.CTkTextbox(
            self, height=200, font=FONT_MONO,
            fg_color=COLOR_SURFACE, text_color=COLOR_TEXT, corner_radius=8
        )
        self.tabla.pack(fill="both", expand=True, padx=20, pady=(6, 12))
        self.tabla.configure(state="disabled")

        # ---- Eliminar ----
        make_section_title(self, "🗑️  Eliminar Equipo")
        del_frame = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=12)
        del_frame.pack(fill="x", padx=20, pady=(0, 16))
        del_row = ctk.CTkFrame(del_frame, fg_color="transparent")
        del_row.pack(padx=16, pady=12)
        make_label(del_row, "ID del equipo:").pack(side="left", padx=8)
        self.ent_del_id = make_entry(del_row, "ID", width=100)
        self.ent_del_id.pack(side="left", padx=8)
        make_button(del_row, "Eliminar", self._eliminar, fg=COLOR_ACCENT, width=100).pack(side="left", padx=8)

    def _registrar(self):
        try:
            eq = self.api.registrar_equipo(
                serie=self.ent_serie.get().strip(),
                marca=self.ent_marca.get().strip(),
                modelo=self.ent_modelo.get().strip(),
                tipo=self.var_tipo.get(),
                ubicacion=self.ent_ubicacion.get().strip(),
                estado_operativo=self.var_estado.get(),
                criticidad=self.var_criticidad.get(),
            )
            messagebox.showinfo("Éxito", f"✅ Equipo registrado\nID: {eq['id']}  Serie: {eq['serie']}")
            self._limpiar_form()
            self._listar()
        except SigomeiAPIError as e:
            messagebox.showerror("Error de negocio", str(e))
        except Exception as e:
            messagebox.showerror("Error de conexión", str(e))

    def _buscar(self):
        termino = self.ent_buscar.get().strip()
        try:
            resultados = self.api.buscar_equipos(termino)
            self._mostrar_equipos(resultados)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _listar(self):
        try:
            equipos = self.api.listar_equipos()
            self._mostrar_equipos(equipos)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _eliminar(self):
        try:
            eid = int(self.ent_del_id.get().strip())
        except ValueError:
            messagebox.showwarning("Aviso", "Ingresa un ID numérico válido.")
            return
        if not messagebox.askyesno("Confirmar", f"¿Eliminar equipo con ID {eid}?"):
            return
        try:
            self.api.eliminar_equipo(eid)
            messagebox.showinfo("Éxito", f"✅ Equipo {eid} eliminado.")
            self._listar()
        except SigomeiAPIError as e:
            messagebox.showerror("Error de negocio", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _mostrar_equipos(self, equipos: list):
        self.tabla.configure(state="normal")
        self.tabla.delete("1.0", "end")
        if not equipos:
            self.tabla.insert("end", "  (Sin resultados)\n")
        else:
            header = f"{'ID':<5} {'Serie':<15} {'Marca':<12} {'Modelo':<15} {'Tipo':<12} {'Estado':<20} {'Criticidad'}\n"
            sep = "-" * 90 + "\n"
            self.tabla.insert("end", header)
            self.tabla.insert("end", sep)
            for e in equipos:
                line = (
                    f"{e.get('id',''):<5} "
                    f"{e.get('serie',''):<15} "
                    f"{e.get('marca',''):<12} "
                    f"{e.get('modelo',''):<15} "
                    f"{e.get('tipo',''):<12} "
                    f"{e.get('estado_operativo',''):<20} "
                    f"{e.get('criticidad','')}\n"
                )
                self.tabla.insert("end", line)
        self.tabla.configure(state="disabled")

    def _limpiar_form(self):
        for w in [self.ent_serie, self.ent_marca, self.ent_modelo, self.ent_ubicacion]:
            w.delete(0, "end")


# ===========================================================================
# Tab: Técnicos
# ===========================================================================

class TecnicosTab(ctk.CTkFrame):
    """Pestaña de gestión de Técnicos."""

    def __init__(self, parent, api: SigomeiAPI):
        super().__init__(parent, fg_color="transparent")
        self.api = api
        self._build_ui()

    def _build_ui(self):
        make_section_title(self, "➕  Registrar Técnico")
        form = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=12)
        form.pack(fill="x", padx=20, pady=6)

        grid = ctk.CTkFrame(form, fg_color="transparent")
        grid.pack(padx=16, pady=16)

        # Fila 0
        make_label(grid, "Nombre *").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self.ent_nombre = make_entry(grid, "Nombre completo")
        self.ent_nombre.grid(row=0, column=1, padx=8, pady=4)

        make_label(grid, "Especialidad").grid(row=0, column=2, sticky="w", padx=8, pady=4)
        self.var_esp = tk.StringVar(value=TIPOS_EQUIPO[0])
        make_optionmenu(grid, TIPOS_EQUIPO, self.var_esp).grid(row=0, column=3, padx=8, pady=4)

        # Fila 1
        make_label(grid, "RFC").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self.ent_rfc = make_entry(grid, "RFC")
        self.ent_rfc.grid(row=1, column=1, padx=8, pady=4)

        make_label(grid, "Correo *").grid(row=1, column=2, sticky="w", padx=8, pady=4)
        self.ent_correo = make_entry(grid, "correo@ejemplo.com")
        self.ent_correo.grid(row=1, column=3, padx=8, pady=4)

        # Fila 2
        make_label(grid, "Nivel Cert.").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        self.var_nivel = tk.StringVar(value=NIVELES_CERT[0])
        make_optionmenu(grid, NIVELES_CERT, self.var_nivel, width=120).grid(
            row=2, column=1, sticky="w", padx=8, pady=4
        )

        make_label(grid, "Estatus").grid(row=2, column=2, sticky="w", padx=8, pady=4)
        self.var_estatus = tk.StringVar(value=ESTATUSES_TEC[0])
        make_optionmenu(grid, ESTATUSES_TEC, self.var_estatus, width=120).grid(
            row=2, column=3, sticky="w", padx=8, pady=4
        )

        btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_frame.pack(pady=(0, 12))
        make_button(btn_frame, "Registrar", self._registrar, width=160).pack(side="left", padx=8)
        make_button(btn_frame, "Limpiar", self._limpiar, fg=COLOR_CARD, width=100).pack(side="left", padx=4)

        # Listado
        make_section_title(self, "📋  Técnicos Registrados")
        list_frame = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=12)
        list_frame.pack(fill="x", padx=20, pady=6)
        btn_row = ctk.CTkFrame(list_frame, fg_color="transparent")
        btn_row.pack(padx=16, pady=10)
        make_button(btn_row, "Actualizar listado", self._listar, fg="#1a6b4a", width=180).pack()

        self.tabla = ctk.CTkTextbox(
            self, height=200, font=FONT_MONO,
            fg_color=COLOR_SURFACE, text_color=COLOR_TEXT, corner_radius=8
        )
        self.tabla.pack(fill="both", expand=True, padx=20, pady=(6, 12))
        self.tabla.configure(state="disabled")

        # Eliminar
        make_section_title(self, "🗑️  Eliminar Técnico")
        del_frame = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=12)
        del_frame.pack(fill="x", padx=20, pady=(0, 16))
        del_row = ctk.CTkFrame(del_frame, fg_color="transparent")
        del_row.pack(padx=16, pady=12)
        make_label(del_row, "ID del técnico:").pack(side="left", padx=8)
        self.ent_del_id = make_entry(del_row, "ID", width=100)
        self.ent_del_id.pack(side="left", padx=8)
        make_button(del_row, "Eliminar", self._eliminar, fg=COLOR_ACCENT, width=100).pack(side="left", padx=8)

    def _registrar(self):
        try:
            tec = self.api.registrar_tecnico(
                nombre=self.ent_nombre.get().strip(),
                especialidad=self.var_esp.get(),
                rfc=self.ent_rfc.get().strip(),
                nivel_certificacion=self.var_nivel.get(),
                correo=self.ent_correo.get().strip(),
                estatus=self.var_estatus.get(),
            )
            messagebox.showinfo("Éxito", f"✅ Técnico registrado\nID: {tec['id']}  Nombre: {tec['nombre']}")
            self._limpiar()
            self._listar()
        except SigomeiAPIError as e:
            messagebox.showerror("Error de negocio", str(e))
        except Exception as e:
            messagebox.showerror("Error de conexión", str(e))

    def _listar(self):
        try:
            tecnicos = self.api.listar_tecnicos()
            self._mostrar(tecnicos)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _eliminar(self):
        try:
            tid = int(self.ent_del_id.get().strip())
        except ValueError:
            messagebox.showwarning("Aviso", "Ingresa un ID numérico válido.")
            return
        if not messagebox.askyesno("Confirmar", f"¿Eliminar técnico con ID {tid}?"):
            return
        try:
            self.api.eliminar_tecnico(tid)
            messagebox.showinfo("Éxito", f"✅ Técnico {tid} eliminado.")
            self._listar()
        except SigomeiAPIError as e:
            messagebox.showerror("Error de negocio", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _mostrar(self, tecnicos: list):
        self.tabla.configure(state="normal")
        self.tabla.delete("1.0", "end")
        if not tecnicos:
            self.tabla.insert("end", "  (Sin técnicos registrados)\n")
        else:
            header = f"{'ID':<5} {'Nombre':<22} {'Especialidad':<14} {'Nivel':<7} {'Correo':<28} {'Estatus'}\n"
            self.tabla.insert("end", header)
            self.tabla.insert("end", "-" * 90 + "\n")
            for t in tecnicos:
                line = (
                    f"{t.get('id',''):<5} "
                    f"{t.get('nombre',''):<22} "
                    f"{t.get('especialidad',''):<14} "
                    f"{t.get('nivel_certificacion',''):<7} "
                    f"{t.get('correo',''):<28} "
                    f"{t.get('estatus','')}\n"
                )
                self.tabla.insert("end", line)
        self.tabla.configure(state="disabled")

    def _limpiar(self):
        for w in [self.ent_nombre, self.ent_rfc, self.ent_correo]:
            w.delete(0, "end")


# ===========================================================================
# Tab: Órdenes
# ===========================================================================

class OrdenesTab(ctk.CTkFrame):
    """Pestaña de gestión de Órdenes de mantenimiento."""

    def __init__(self, parent, api: SigomeiAPI):
        super().__init__(parent, fg_color="transparent")
        self.api = api
        self._build_ui()

    def _build_ui(self):
        make_section_title(self, "➕  Crear Orden de Mantenimiento")
        form = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=12)
        form.pack(fill="x", padx=20, pady=6)

        grid = ctk.CTkFrame(form, fg_color="transparent")
        grid.pack(padx=16, pady=16)

        # Fila 0
        make_label(grid, "ID Equipo *").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self.ent_eq_id = make_entry(grid, "ID del equipo", width=120)
        self.ent_eq_id.grid(row=0, column=1, sticky="w", padx=8, pady=4)

        make_label(grid, "ID Técnico *").grid(row=0, column=2, sticky="w", padx=8, pady=4)
        self.ent_tec_id = make_entry(grid, "ID del técnico", width=120)
        self.ent_tec_id.grid(row=0, column=3, sticky="w", padx=8, pady=4)

        # Fila 1
        make_label(grid, "Tipo Mant.").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self.var_tipo_mant = tk.StringVar(value=TIPOS_MANT[0])
        make_optionmenu(grid, TIPOS_MANT, self.var_tipo_mant).grid(row=1, column=1, padx=8, pady=4)

        make_label(grid, "Fecha prog. *").grid(row=1, column=2, sticky="w", padx=8, pady=4)
        self.ent_fecha = make_entry(grid, "YYYY-MM-DD", width=150)
        self.ent_fecha.grid(row=1, column=3, padx=8, pady=4)

        # Fila 2
        make_label(grid, "Costo estimado").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        self.ent_costo = make_entry(grid, "0.00", width=150)
        self.ent_costo.grid(row=2, column=1, sticky="w", padx=8, pady=4)

        make_label(grid, "Observaciones").grid(row=2, column=2, sticky="w", padx=8, pady=4)
        self.ent_obs_crear = make_entry(grid, "Notas adicionales", width=220)
        self.ent_obs_crear.grid(row=2, column=3, padx=8, pady=4)

        btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_frame.pack(pady=(0, 12))
        make_button(btn_frame, "Crear Orden", self._crear, width=160).pack(side="left", padx=8)

        make_label(
            form,
            "ⓘ  Los IDs de Equipo y Técnico deben existir previamente en el servidor.",
            font=FONT_SMALL, color=COLOR_MUTED,
        ).pack(pady=(0, 8))

        # Acciones sobre órdenes
        make_section_title(self, "⚙️  Operaciones sobre Orden")
        ops_frame = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=12)
        ops_frame.pack(fill="x", padx=20, pady=6)

        ops_grid = ctk.CTkFrame(ops_frame, fg_color="transparent")
        ops_grid.pack(padx=16, pady=14)

        make_label(ops_grid, "ID Orden:").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.ent_ord_id = make_entry(ops_grid, "ID", width=100)
        self.ent_ord_id.grid(row=0, column=1, sticky="w", padx=8, pady=6)

        make_button(ops_grid, "Cancelar", self._cancelar, fg=COLOR_ACCENT, width=120).grid(
            row=0, column=2, padx=8, pady=6
        )
        make_button(ops_grid, "Obtener info", self._obtener, fg=COLOR_CARD, width=130).grid(
            row=0, column=3, padx=8, pady=6
        )

        make_label(ops_grid, "Nuevo estado:").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        self.var_nuevo_estado = tk.StringVar(value=ESTADOS_ORDEN[1])
        make_optionmenu(ops_grid, ESTADOS_ORDEN[1:], self.var_nuevo_estado, width=180).grid(
            row=1, column=1, padx=8, pady=6
        )
        make_button(ops_grid, "Actualizar estado", self._actualizar_estado, fg="#1a6b4a", width=160).grid(
            row=1, column=2, columnspan=2, padx=8, pady=6
        )

        make_label(ops_grid, "Costo cierre:").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        self.ent_costo_cierre = make_entry(ops_grid, "0.00", width=120)
        self.ent_costo_cierre.grid(row=2, column=1, sticky="w", padx=8, pady=6)

        make_label(ops_grid, "Observaciones cierre:").grid(row=2, column=2, sticky="w", padx=8, pady=6)
        self.ent_obs_cierre = make_entry(ops_grid, "Observaciones", width=220)
        self.ent_obs_cierre.grid(row=2, column=3, padx=8, pady=6)

        make_button(ops_grid, "Registrar reporte", self._reporte, fg=COLOR_WARNING, width=160).grid(
            row=3, column=0, columnspan=4, pady=10
        )

        # Resultado
        self.resultado = ctk.CTkTextbox(
            self, height=180, font=FONT_MONO,
            fg_color=COLOR_SURFACE, text_color=COLOR_TEXT, corner_radius=8
        )
        self.resultado.pack(fill="both", expand=True, padx=20, pady=(6, 16))
        self.resultado.configure(state="disabled")

    def _get_ord_id(self):
        try:
            return int(self.ent_ord_id.get().strip())
        except ValueError:
            messagebox.showwarning("Aviso", "Ingresa un ID de orden numérico válido.")
            return None

    def _crear(self):
        try:
            eq_id  = int(self.ent_eq_id.get().strip())
            tec_id = int(self.ent_tec_id.get().strip())
        except ValueError:
            messagebox.showwarning("Aviso", "Los IDs de equipo y técnico deben ser números.")
            return

        try:
            equipo  = self.api.obtener_equipo(eq_id)
            tecnico = self.api.obtener_tecnico(tec_id)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener equipo/técnico:\n{e}")
            return

        if equipo is None:
            messagebox.showerror("Error", f"Equipo con ID {eq_id} no existe.")
            return
        if tecnico is None:
            messagebox.showerror("Error", f"Técnico con ID {tec_id} no existe.")
            return

        try:
            costo = float(self.ent_costo.get().strip() or "0")
        except ValueError:
            costo = 0.0

        try:
            orden = self.api.crear_orden(
                equipo=equipo,
                tecnico=tecnico,
                tipo_mantenimiento=self.var_tipo_mant.get(),
                fecha_programada=self.ent_fecha.get().strip(),
                costo_estimado=costo,
                observaciones=self.ent_obs_crear.get().strip(),
            )
            self._mostrar_orden(orden)
            messagebox.showinfo("Éxito", f"✅ Orden creada con ID: {orden['id']}")
        except SigomeiAPIError as e:
            messagebox.showerror("Error de negocio", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _cancelar(self):
        oid = self._get_ord_id()
        if oid is None:
            return
        if not messagebox.askyesno("Confirmar", f"¿Cancelar la orden {oid}?"):
            return
        try:
            self.api.cancelar_orden(oid)
            messagebox.showinfo("Éxito", f"✅ Orden {oid} cancelada.")
            self._obtener_by_id(oid)
        except SigomeiAPIError as e:
            messagebox.showerror("Error de negocio", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _obtener(self):
        oid = self._get_ord_id()
        if oid is not None:
            self._obtener_by_id(oid)

    def _obtener_by_id(self, oid: int):
        try:
            orden = self.api.obtener_orden(oid)
            self._mostrar_orden(orden)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _actualizar_estado(self):
        oid = self._get_ord_id()
        if oid is None:
            return
        try:
            self.api.actualizar_estado_orden(oid, self.var_nuevo_estado.get())
            messagebox.showinfo("Éxito", f"✅ Estado actualizado a '{self.var_nuevo_estado.get()}'.")
            self._obtener_by_id(oid)
        except SigomeiAPIError as e:
            messagebox.showerror("Error de negocio", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _reporte(self):
        oid = self._get_ord_id()
        if oid is None:
            return
        try:
            costo = float(self.ent_costo_cierre.get().strip() or "0")
        except ValueError:
            costo = 0.0
        try:
            self.api.realizar_reporte(oid, costo, self.ent_obs_cierre.get().strip())
            messagebox.showinfo("Éxito", "✅ Reporte de cierre registrado.")
            self._obtener_by_id(oid)
        except SigomeiAPIError as e:
            messagebox.showerror("Error de negocio", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _mostrar_orden(self, orden):
        self.resultado.configure(state="normal")
        self.resultado.delete("1.0", "end")
        if orden is None:
            self.resultado.insert("end", "  (Orden no encontrada)\n")
        else:
            eq  = orden.get("equipo") or {}
            tec = orden.get("tecnico") or {}
            lines = [
                f"  ID Orden        : {orden.get('id')}",
                f"  Estado          : {orden.get('estado')}",
                f"  Tipo Mant.      : {orden.get('tipo_mantenimiento')}",
                f"  Fecha prog.     : {orden.get('fecha_programada')}",
                f"  Costo estimado  : ${orden.get('costo_estimado', 0):.2f}",
                f"  Costo real      : ${orden.get('costo_real', 0):.2f}",
                f"  Observaciones   : {orden.get('observaciones')}",
                f"  Equipo          : [{eq.get('id')}] {eq.get('serie')} — {eq.get('marca')} {eq.get('modelo')}",
                f"  Técnico         : [{tec.get('id')}] {tec.get('nombre')} ({tec.get('especialidad')})",
            ]
            self.resultado.insert("end", "\n".join(lines) + "\n")
        self.resultado.configure(state="disabled")


# ===========================================================================
# Ventana Principal
# ===========================================================================

class SigomeiApp(ctk.CTk):
    """Ventana principal de la aplicación SIGOMEI."""

    def __init__(self, host: str, port: int):
        super().__init__()
        self.title("SIGOMEI — Sistema de Gestión de Órdenes de Mantenimiento Industrial")
        self.geometry("1100x780")
        self.minsize(900, 640)
        self.configure(fg_color=COLOR_BG)

        self._host = host
        self._port = port
        self.api = SigomeiAPI(host=host, port=port)
        self._connected = False

        self._build_header()
        self._build_connection_bar()
        self._build_tabs()
        self._build_statusbar()

        # Verificar conexión inicial en hilo separado
        threading.Thread(target=self._check_connection, daemon=True).start()

    # ------------------------------------------------------------------
    # Construcción de UI
    # ------------------------------------------------------------------

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, height=70, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(side="left", padx=24, pady=12)

        ctk.CTkLabel(
            inner, text="⚙  SIGOMEI",
            font=FONT_TITLE, text_color=COLOR_ACCENT
        ).pack(side="left")

        ctk.CTkLabel(
            inner,
            text="  Sistema de Gestión de Órdenes de Mantenimiento Industrial",
            font=("Segoe UI", 12), text_color=COLOR_MUTED,
        ).pack(side="left", padx=12)

    def _build_connection_bar(self):
        bar = ctk.CTkFrame(self, fg_color=COLOR_CARD, height=50, corner_radius=0)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(side="left", padx=20, pady=8)

        make_label(inner, "Servidor:", color=COLOR_MUTED, font=FONT_SMALL).pack(side="left", padx=(0, 6))

        self.ent_host = ctk.CTkEntry(
            inner, width=160, placeholder_text="host",
            font=FONT_SMALL, fg_color=COLOR_SURFACE, border_color=COLOR_MUTED
        )
        self.ent_host.insert(0, self._host)
        self.ent_host.pack(side="left", padx=4)

        make_label(inner, ":", color=COLOR_MUTED, font=FONT_SMALL).pack(side="left")

        self.ent_port = ctk.CTkEntry(
            inner, width=70, placeholder_text="puerto",
            font=FONT_SMALL, fg_color=COLOR_SURFACE, border_color=COLOR_MUTED
        )
        self.ent_port.insert(0, str(self._port))
        self.ent_port.pack(side="left", padx=4)

        make_button(inner, "Conectar", self._reconnect, fg=COLOR_CARD, width=90).pack(side="left", padx=10)

        # Indicador de estado
        self.lbl_status = ctk.CTkLabel(
            bar, text="● Desconectado",
            font=FONT_SMALL, text_color=COLOR_DISCONN
        )
        self.lbl_status.pack(side="right", padx=24)

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=COLOR_BG,
            segmented_button_fg_color=COLOR_SURFACE,
            segmented_button_selected_color=COLOR_ACCENT,
            segmented_button_selected_hover_color="#c0392b",
            segmented_button_unselected_color=COLOR_SURFACE,
            segmented_button_unselected_hover_color=COLOR_CARD,
            text_color=COLOR_TEXT,
        )
        self.tabview.pack(fill="both", expand=True, padx=12, pady=8)

        self.tabview.add("🔧  Equipos")
        self.tabview.add("👷  Técnicos")
        self.tabview.add("📋  Órdenes")

        self._tab_equipos  = EquiposTab(self.tabview.tab("🔧  Equipos"),  self.api)
        self._tab_tecnicos = TecnicosTab(self.tabview.tab("👷  Técnicos"), self.api)
        self._tab_ordenes  = OrdenesTab(self.tabview.tab("📋  Órdenes"),  self.api)

        for tab in [self._tab_equipos, self._tab_tecnicos, self._tab_ordenes]:
            tab.pack(fill="both", expand=True)

    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, height=28, corner_radius=0)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        ctk.CTkLabel(
            bar,
            text="SIGOMEI v1.0  |  Protocolo: JSON/TCP  |  Puerto por defecto: 5000",
            font=FONT_SMALL, text_color=COLOR_MUTED,
        ).pack(side="left", padx=16)

    # ------------------------------------------------------------------
    # Conexión
    # ------------------------------------------------------------------

    def _reconnect(self):
        host = self.ent_host.get().strip()
        try:
            port = int(self.ent_port.get().strip())
        except ValueError:
            messagebox.showwarning("Aviso", "El puerto debe ser un número.")
            return
        self.api.set_server(host, port)
        threading.Thread(target=self._check_connection, daemon=True).start()

    def _check_connection(self):
        connected = self.api.esta_conectado()
        self.after(0, self._update_status, connected)

    def _update_status(self, connected: bool):
        self._connected = connected
        if connected:
            host = self.api._client.host
            port = self.api._client.port
            self.lbl_status.configure(
                text=f"● Conectado  {host}:{port}",
                text_color=COLOR_CONNECTED,
            )
        else:
            self.lbl_status.configure(
                text="● Desconectado",
                text_color=COLOR_DISCONN,
            )


# ===========================================================================
# Punto de entrada
# ===========================================================================

def parse_args():
    parser = argparse.ArgumentParser(description="SIGOMEI — Interfaz gráfica (CustomTkinter)")
    parser.add_argument("--host", default="127.0.0.1", help="Host del servidor TCP")
    parser.add_argument("--port", type=int, default=5000, help="Puerto del servidor TCP")
    return parser.parse_args()


def main():
    args = parse_args()
    app = SigomeiApp(host=args.host, port=args.port)
    app.mainloop()


if __name__ == "__main__":
    main()
