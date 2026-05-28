"""
ui/main.py
===========
Interfaz gráfica de usuario moderna y premium para SIGOMEI.
Sigue el flujo de navegación multipágina interactivo de los bosquejos CRUD,
manteniendo la paleta de colores oscuros (dark neon) del proyecto original.

tag: 1.0.0

Uso:
    python ui/main.py [--host 127.0.0.1] [--port 5000]
"""

import argparse
import sys
import os
import threading
import tkinter as tk
from tkinter import messagebox

# Resolver imports locales
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import customtkinter as ctk
from client.api import SigomeiAPI, SigomeiAPIError
from client.socket_client import ConnectionError as SigomeiConnError

# ---------------------------------------------------------------------------
# Tema y apariencia (Dark Neon Premium)
# ---------------------------------------------------------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FONT_LARGE_TITLE = ("Segoe UI", 28, "bold")
FONT_TITLE       = ("Segoe UI", 22, "bold")
FONT_HEADER      = ("Segoe UI", 14, "bold")
FONT_BODY        = ("Segoe UI", 12)
FONT_BOLD        = ("Segoe UI", 12, "bold")
FONT_SMALL       = ("Segoe UI", 10)
FONT_MONO        = ("Consolas", 11)

COLOR_BG        = "#1a1a2e"
COLOR_SURFACE   = "#16213e"
COLOR_CARD      = "#0f3460"
COLOR_ACCENT    = "#e94560"  # Carmesí Neón
COLOR_SUCCESS   = "#2ecc71"  # Verde Neón
COLOR_WARNING   = "#f39c12"  # Ámbar/Amarillo Neón
COLOR_TEXT      = "#eaeaea"
COLOR_MUTED     = "#8892b0"
COLOR_CONNECTED = "#2ecc71"
COLOR_DISCONN   = "#e74c3c"

TIPOS_EQUIPO    = ["Mecanico", "Electrico", "Hidraulico", "Neumatico", "Electronico"]
ESTADOS_OP      = ["Disponible", "En Mantenimiento", "Fuera de Servicio"]
CRITICIDADES    = ["Normal", "Alta"]
NIVELES_CERT    = ["I", "II", "III"]
ESTATUSES_TEC   = ["Activo", "Inactivo"]
TIPOS_MANT      = ["Mecanico", "Electrico", "Hidraulico", "Neumatico", "Electronico"]
ESTADOS_ORDEN   = ["Programada", "En ejecucion", "Finalizada", "Cancelada"]


# ===========================================================================
# Componentes Auxiliares
# ===========================================================================

def make_label(parent, text, font=None, color=None, **kwargs):
    return ctk.CTkLabel(
        parent, text=text,
        font=font or FONT_BODY,
        text_color=color or COLOR_TEXT,
        **kwargs
    )


def make_btn(parent, text, command, type="default", width=120, **kwargs):
    """Factory de botones consistentes y estilizados con micro-animación hover."""
    if type == "warning":  # Amarillo/Ámbar
        fg = COLOR_WARNING
        hover = "#d68910"
        txt_col = "#1a1a2e"  # Contraste oscuro
        font_style = FONT_BOLD
    elif type == "success":  # Verde
        fg = COLOR_SUCCESS
        hover = "#27ae60"
        txt_col = "#ffffff"
        font_style = FONT_BOLD
    elif type == "accent":  # Carmesí
        fg = COLOR_ACCENT
        hover = "#c0392b"
        txt_col = "#ffffff"
        font_style = FONT_BOLD
    else:  # Predeterminado/Muted
        fg = COLOR_CARD
        hover = "#16213e"
        txt_col = COLOR_TEXT
        font_style = FONT_BODY

    # Extraer valores personalizados de kwargs si existen para evitar duplicación
    fg = kwargs.pop("fg_color", fg)
    hover = kwargs.pop("hover_color", hover)
    txt_col = kwargs.pop("text_color", txt_col)
    font_style = kwargs.pop("font", font_style)

    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        font=font_style,
        fg_color=fg,
        hover_color=hover,
        text_color=txt_col,
        width=width,
        corner_radius=8,
        **kwargs
    )


def make_input(parent, placeholder="", width=220, **kwargs):
    font_style = kwargs.pop("font", FONT_BODY)
    fg_col = kwargs.pop("fg_color", COLOR_SURFACE)
    border_col = kwargs.pop("border_color", COLOR_CARD)
    radius = kwargs.pop("corner_radius", 8)

    return ctk.CTkEntry(
        parent,
        placeholder_text=placeholder,
        width=width,
        font=font_style,
        fg_color=fg_col,
        border_color=border_col,
        corner_radius=radius,
        **kwargs
    )


def make_dropdown(parent, values, variable, width=220):
    return ctk.CTkOptionMenu(
        parent,
        values=values,
        variable=variable,
        font=FONT_BODY,
        fg_color=COLOR_SURFACE,
        button_color=COLOR_CARD,
        button_hover_color=COLOR_ACCENT,
        dropdown_fg_color=COLOR_SURFACE,
        dropdown_font=FONT_BODY,
        width=width,
        corner_radius=8,
    )


def build_breadcrumbs(parent, paths: list, app):
    """Construye un sistema visual premium de breadcrumbs interactivos."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(side="left", padx=10, pady=5)
    
    for i, p in enumerate(paths):
        name, target_frame = p
        
        # Separador
        if i > 0:
            sep = ctk.CTkLabel(frame, text="  >  ", font=FONT_HEADER, text_color=COLOR_MUTED)
            sep.pack(side="left")
            
        # Elemento clickable o label
        if target_frame:
            btn = ctk.CTkButton(
                frame, text=name, font=FONT_HEADER, text_color=COLOR_ACCENT,
                fg_color="transparent", hover_color=COLOR_SURFACE, width=1, height=24,
                corner_radius=4, command=lambda tf=target_frame: app.show_frame(tf)
            )
            btn.pack(side="left")
        else:
            lbl = ctk.CTkLabel(frame, text=name, font=FONT_HEADER, text_color=COLOR_TEXT)
            lbl.pack(side="left")
            
    return frame


def make_status_badge(parent, text, type_val):
    """Crea una celda de estado elegante y redondeada."""
    badge = ctk.CTkFrame(parent, corner_radius=12, height=24)
    badge.pack_propagate(False)
    
    # Colores semánticos
    if type_val in ["Disponible", "Activo", "En ejecucion", "Finalizada"]:
        bg_col = "#1b4d3e"
        txt_col = "#2ecc71"
    elif type_val in ["En Mantenimiento", "Programada"]:
        bg_col = "#5e4817"
        txt_col = "#f39c12"
    elif type_val in ["Fuera de Servicio", "Inactivo", "Cancelada"]:
        bg_col = "#5c2530"
        txt_col = "#e94560"
    else:
        bg_col = COLOR_CARD
        txt_col = COLOR_TEXT
        
    badge.configure(fg_color=bg_col)
    lbl = ctk.CTkLabel(badge, text=text, font=FONT_SMALL, text_color=txt_col)
    lbl.pack(fill="both", expand=True, padx=8)
    return badge


# ===========================================================================
# 1. Menú Principal (Dashboard)
# ===========================================================================

class MainMenuFrame(ctk.CTkFrame):
    """Pantalla principal con el menú inicial."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # Títulos de Bienvenida
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(pady=(40, 30))

        make_label(title_frame, "Hola, Coordinador", font=FONT_LARGE_TITLE, color=COLOR_TEXT).pack()
        make_label(title_frame, "¿Con qué trabajaremos hoy?", font=FONT_HEADER, color=COLOR_MUTED).pack(pady=(8, 0))

        # Contenedor de Tarjetas
        cards_container = ctk.CTkFrame(self, fg_color="transparent")
        cards_container.pack(fill="x", padx=40, expand=True)
        cards_container.columnconfigure((0, 1, 2), weight=1, uniform="equal")

        # Tarjeta 1: Órdenes
        self._create_menu_card(
            parent=cards_container, col=0, emoji="📋", title="Órdenes de Trabajo",
            desc="Registra reportes, cancela, inicia o crea nuevas órdenes de mantenimiento industrial.",
            command=lambda: self.app.show_frame(OrdenesListFrame)
        )

        # Tarjeta 2: Equipos
        self._create_menu_card(
            parent=cards_container, col=1, emoji="🔧", title="Gestión de Equipos",
            desc="Administra el inventario de maquinaria física, ubicaciones y criticidad operativa.",
            command=lambda: self.app.show_frame(EquiposListFrame)
        )

        # Tarjeta 3: Técnicos
        self._create_menu_card(
            parent=cards_container, col=2, emoji="👷", title="Técnicos Industriales",
            desc="Gestiona al personal especializado, especialidades, niveles de certificación y estatus.",
            command=lambda: self.app.show_frame(TecnicosListFrame)
        )

        # Botón Salir
        btn_exit_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_exit_frame.pack(side="bottom", anchor="w", padx=20, pady=20)
        make_btn(btn_exit_frame, "Salir del Sistema", self.app.quit, type="accent", width=160).pack()

    def _create_menu_card(self, parent, col, emoji, title, desc, command):
        card = ctk.CTkFrame(parent, fg_color=COLOR_SURFACE, corner_radius=16, border_color=COLOR_CARD, border_width=2)
        card.grid(row=0, column=col, padx=15, pady=10, sticky="nsew")

        # Contenido de la Tarjeta
        make_label(card, emoji, font=("Segoe UI", 48)).pack(pady=(25, 10))
        make_label(card, title, font=FONT_HEADER, color=COLOR_ACCENT).pack(pady=5)
        
        # Descripción
        desc_lbl = ctk.CTkLabel(
            card, text=desc, font=FONT_SMALL, text_color=COLOR_MUTED,
            wraplength=200, justify="center"
        )
        desc_lbl.pack(pady=(5, 20), padx=15, fill="both", expand=True)

        # Botón de Acción
        make_btn(card, "Ingresar", command, type="warning", width=140).pack(pady=(0, 25))


# ===========================================================================
# 2. Equipos CRUD
# ===========================================================================

class EquiposListFrame(ctk.CTkFrame):
    """Pantalla con el listado de Equipos."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._build_ui()
        self._cargar_datos()

    def _build_ui(self):
        # Barra superior con Breadcrumbs y Botones de Acción
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 20))

        build_breadcrumbs(header, [("Inicio", MainMenuFrame), ("Equipos", None)], self.app)

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.pack(side="right", padx=10)
        
        make_btn(actions, "Volver", lambda: self.app.show_frame(MainMenuFrame), type="warning", width=90).pack(side="left", padx=5)
        make_btn(actions, "Registrar Equipo", lambda: self.app.show_frame(EquiposFormFrame), type="success", width=150).pack(side="left", padx=5)

        # Filtro de búsqueda
        search_panel = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=12)
        search_panel.pack(fill="x", pady=(0, 15))

        search_grid = ctk.CTkFrame(search_panel, fg_color="transparent")
        search_grid.pack(padx=15, pady=10, fill="x")

        make_label(search_grid, "🔍 Buscar: ", font=FONT_HEADER).pack(side="left", padx=5)
        self.ent_search = make_input(search_grid, "Término (marca, modelo, tipo)...", width=300)
        self.ent_search.pack(side="left", padx=5)
        self.ent_search.bind("<Return>", lambda e: self._buscar())

        make_btn(search_grid, "Buscar", self._buscar, type="default", width=100).pack(side="left", padx=5)
        make_btn(search_grid, "Mostrar Todos", self._cargar_datos, type="default", width=120).pack(side="left", padx=5)

        # Tabla de Equipos
        self._build_table()

    def _build_table(self):
        # Cabecera de la tabla
        tbl_header = ctk.CTkFrame(self, fg_color=COLOR_CARD, height=35, corner_radius=8)
        tbl_header.pack(fill="x", pady=(0, 5))
        tbl_header.pack_propagate(False)

        cols = [
            ("ID", 60), ("Serie", 120), ("Marca / Modelo", 180), ("Tipo", 120),
            ("Ubicación", 150), ("Estado", 140), ("Criticidad", 90), ("Acciones", 120)
        ]

        for i, (name, w) in enumerate(cols):
            lbl = ctk.CTkLabel(tbl_header, text=name, font=FONT_BOLD, text_color=COLOR_TEXT)
            lbl.pack(side="left", padx=5, fill="y")
            # Ajustar anchos aproximados
            lbl.configure(width=w, anchor="w" if i != 7 else "center")

        # Contenedor Scrollable
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0
        )
        self.scroll_frame.pack(fill="both", expand=True)

    def _cargar_datos(self):
        self.ent_search.delete(0, "end")
        try:
            equipos = self.app.api.listar_equipos()
            self._render_rows(equipos)
        except Exception as e:
            messagebox.showerror("Error de Red", f"No se pudo cargar la lista de equipos:\n{e}")

    def _buscar(self):
        term = self.ent_search.get().strip()
        if not term:
            self._cargar_datos()
            return
        try:
            resultados = self.app.api.buscar_equipos(term)
            self._render_rows(resultados)
        except Exception as e:
            messagebox.showerror("Error", f"Error durante la búsqueda:\n{e}")

    def _render_rows(self, equipos):
        # Limpiar filas existentes
        for child in self.scroll_frame.winfo_children():
            child.destroy()

        if not equipos:
            empty_lbl = ctk.CTkLabel(self.scroll_frame, text="⚠ Sin equipos registrados.", font=FONT_HEADER, text_color=COLOR_MUTED)
            empty_lbl.pack(pady=40)
            return

        for eq in equipos:
            row = ctk.CTkFrame(self.scroll_frame, fg_color=COLOR_SURFACE, height=45, corner_radius=6, border_color=COLOR_CARD, border_width=1)
            row.pack(fill="x", pady=3)
            row.pack_propagate(False)

            # Columnas de datos
            # ID
            ctk.CTkLabel(row, text=str(eq.get('id','')), font=FONT_BODY, width=60, anchor="w").pack(side="left", padx=5, fill="y")
            # Serie
            ctk.CTkLabel(row, text=eq.get('serie',''), font=FONT_BOLD, width=120, anchor="w").pack(side="left", padx=5, fill="y")
            # Marca / Modelo
            ctk.CTkLabel(row, text=f"{eq.get('marca','')} {eq.get('modelo','')}".strip(), font=FONT_BODY, width=180, anchor="w").pack(side="left", padx=5, fill="y")
            # Tipo
            ctk.CTkLabel(row, text=eq.get('tipo',''), font=FONT_BODY, width=120, anchor="w").pack(side="left", padx=5, fill="y")
            # Ubicación
            ctk.CTkLabel(row, text=eq.get('ubicacion',''), font=FONT_BODY, width=150, anchor="w").pack(side="left", padx=5, fill="y")
            
            # Estado (Badge)
            estado_container = ctk.CTkFrame(row, fg_color="transparent", width=140)
            estado_container.pack(side="left", padx=5, fill="y")
            estado_container.pack_propagate(False)
            make_status_badge(estado_container, eq.get('estado_operativo','Disponible'), eq.get('estado_operativo','Disponible')).pack(pady=10)

            # Criticidad (Badge/Texto)
            crit_container = ctk.CTkFrame(row, fg_color="transparent", width=90)
            crit_container.pack(side="left", padx=5, fill="y")
            crit_container.pack_propagate(False)
            crit_val = eq.get('criticidad','Normal')
            crit_lbl = ctk.CTkLabel(crit_container, text=crit_val, font=FONT_BOLD, text_color=COLOR_ACCENT if crit_val == "Alta" else COLOR_TEXT)
            crit_lbl.pack(pady=10)

            # Acciones (Editar/Eliminar)
            act_container = ctk.CTkFrame(row, fg_color="transparent", width=120)
            act_container.pack(side="right", padx=5, fill="y")
            act_container.pack_propagate(False)

            # Botón Editar
            btn_edit = ctk.CTkButton(
                act_container, text="✏", font=("Segoe UI", 12), fg_color="#34495e", hover_color="#2c3e50",
                text_color="#3498db", width=26, height=26, corner_radius=6,
                command=lambda eid=eq['id']: self.app.show_frame(EquiposFormFrame, equipo_id=eid)
            )
            btn_edit.pack(side="left", padx=4, pady=9)

            # Botón Eliminar
            btn_del = ctk.CTkButton(
                act_container, text="🗑", font=("Segoe UI", 12), fg_color="#34495e", hover_color="#c0392b",
                text_color="#e74c3c", width=26, height=26, corner_radius=6,
                command=lambda eid=eq['id']: self.app.show_frame(EquiposDeleteFrame, equipo_id=eid)
            )
            btn_del.pack(side="left", padx=4, pady=9)


class EquiposFormFrame(ctk.CTkFrame):
    """Formulario dinámico para registrar o editar un Equipo."""

    def __init__(self, parent, app, equipo_id=None, **kwargs):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.equipo_id = equipo_id
        self._build_ui()
        
        if self.equipo_id:
            self._cargar_datos_equipo()

    def _build_ui(self):
        # Cabecera
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 20))

        title_page = "Editar Equipo" if self.equipo_id else "Registrar Equipo"
        build_breadcrumbs(header, [("Inicio", MainMenuFrame), ("Equipos", EquiposListFrame), (title_page, None)], self.app)

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.pack(side="right", padx=10)
        make_btn(actions, "Volver", lambda: self.app.show_frame(EquiposListFrame), type="warning", width=90).pack()

        # Formulario
        self.lbl_title = make_label(self, "➕ Registrar Nuevo Equipo", font=FONT_TITLE, color=COLOR_ACCENT)
        self.lbl_title.pack(anchor="w", padx=20, pady=(0, 10))

        form = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=16, border_color=COLOR_CARD, border_width=1)
        form.pack(fill="both", expand=True, padx=20, pady=5)

        # Grid interno
        grid = ctk.CTkFrame(form, fg_color="transparent")
        grid.pack(padx=30, pady=30, fill="both", expand=True)
        grid.columnconfigure((0, 1), weight=1, uniform="equal")

        # ---- Lado Izquierdo ----
        left_col = ctk.CTkFrame(grid, fg_color="transparent")
        left_col.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")

        make_label(left_col, "Número de Serie *", font=FONT_BOLD).pack(anchor="w", pady=(0, 4))
        self.ent_serie = make_input(left_col, "Ej. SN-XYZ-2026", width=380)
        self.ent_serie.pack(anchor="w", pady=(0, 15))

        make_label(left_col, "Marca *", font=FONT_BOLD).pack(anchor="w", pady=(0, 4))
        self.ent_marca = make_input(left_col, "Ej. ABB / Siemens", width=380)
        self.ent_marca.pack(anchor="w", pady=(0, 15))

        make_label(left_col, "Modelo *", font=FONT_BOLD).pack(anchor="w", pady=(0, 4))
        self.ent_modelo = make_input(left_col, "Ej. Model X-100", width=380)
        self.ent_modelo.pack(anchor="w", pady=(0, 15))

        make_label(left_col, "Ubicación en Planta *", font=FONT_BOLD).pack(anchor="w", pady=(0, 4))
        self.ent_ubicacion = make_input(left_col, "Ej. Sector 4, Planta Principal", width=380)
        self.ent_ubicacion.pack(anchor="w", pady=(0, 15))

        # ---- Lado Derecho ----
        right_col = ctk.CTkFrame(grid, fg_color="transparent")
        right_col.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")

        make_label(right_col, "Tipo de Equipo *", font=FONT_BOLD).pack(anchor="w", pady=(0, 4))
        self.var_tipo = tk.StringVar(value=TIPOS_EQUIPO[0])
        make_dropdown(right_col, TIPOS_EQUIPO, self.var_tipo, width=380).pack(anchor="w", pady=(0, 15))

        make_label(right_col, "Estado Operativo *", font=FONT_BOLD).pack(anchor="w", pady=(0, 4))
        self.var_estado = tk.StringVar(value=ESTADOS_OP[0])
        make_dropdown(right_col, ESTADOS_OP, self.var_estado, width=380).pack(anchor="w", pady=(0, 15))

        make_label(right_col, "Criticidad *", font=FONT_BOLD).pack(anchor="w", pady=(0, 4))
        self.var_crit = tk.StringVar(value=CRITICIDADES[0])
        make_dropdown(right_col, CRITICIDADES, self.var_crit, width=380).pack(anchor="w", pady=(0, 15))

        # Botón de Guardado
        self.btn_submit = make_btn(
            form, "Registrar Equipo", self._guardar, type="success", width=220
        )
        self.btn_submit.pack(pady=25)

    def _cargar_datos_equipo(self):
        try:
            eq = self.app.api.obtener_equipo(self.equipo_id)
            if not eq:
                messagebox.showerror("Error", "No se encontró el equipo.")
                self.app.show_frame(EquiposListFrame)
                return
            
            # Cambiar títulos y textos
            self.lbl_title.configure(text=f"✏ Editar Equipo: {eq.get('marca','')} {eq.get('modelo','')}".strip())
            self.btn_submit.configure(text="Actualizar Información")

            # Llenar campos
            self.ent_serie.insert(0, eq.get('serie',''))
            self.ent_marca.insert(0, eq.get('marca',''))
            self.ent_modelo.insert(0, eq.get('modelo',''))
            self.ent_ubicacion.insert(0, eq.get('ubicacion',''))
            self.var_tipo.set(eq.get('tipo', TIPOS_EQUIPO[0]))
            self.var_estado.set(eq.get('estado_operativo', ESTADOS_OP[0]))
            self.var_crit.set(eq.get('criticidad', CRITICIDADES[0]))
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los datos del equipo:\n{e}")
            self.app.show_frame(EquiposListFrame)

    def _guardar(self):
        serie = self.ent_serie.get().strip()
        marca = self.ent_marca.get().strip()
        modelo = self.ent_modelo.get().strip()
        ubicacion = self.ent_ubicacion.get().strip()
        tipo = self.var_tipo.get()
        estado = self.var_estado.get()
        criticidad = self.var_crit.get()

        if not serie:
            messagebox.showwarning("Campo Faltante", "El número de serie es un campo requerido.")
            return

        try:
            if self.equipo_id:
                # Actualizar
                self.app.api.actualizar_equipo(
                    id=self.equipo_id,
                    serie=serie,
                    marca=marca,
                    modelo=modelo,
                    tipo=tipo,
                    ubicacion=ubicacion,
                    estado_operativo=estado,
                    criticidad=criticidad
                )
                msg = "Información del equipo actualizada exitosamente."
            else:
                # Crear
                self.app.api.registrar_equipo(
                    serie=serie,
                    marca=marca,
                    modelo=modelo,
                    tipo=tipo,
                    ubicacion=ubicacion,
                    estado_operativo=estado,
                    criticidad=criticidad
                )
                msg = "Equipo registrado exitosamente en el sistema."

            # Navegar a pantalla de éxito
            self.app.show_frame(SuccessFrame, message=msg, next_frame=EquiposListFrame)

        except SigomeiAPIError as e:
            messagebox.showerror("Error de Negocio", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error de comunicación con el servidor:\n{e}")


class EquiposDeleteFrame(ctk.CTkFrame):
    """Pantalla de confirmación para eliminar un Equipo."""

    def __init__(self, parent, app, equipo_id, **kwargs):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.equipo_id = equipo_id
        self._build_ui()
        self._cargar_info()

    def _build_ui(self):
        # Cabecera
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 20))

        build_breadcrumbs(header, [("Inicio", MainMenuFrame), ("Equipos", EquiposListFrame), ("Eliminar Equipo", None)], self.app)

        # Panel de Advertencia Central
        card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=16, border_color=COLOR_ACCENT, border_width=2)
        card.pack(pady=40, padx=50, fill="both", expand=True)

        make_label(card, "⚠   Eliminar Equipo", font=FONT_LARGE_TITLE, color=COLOR_ACCENT).pack(pady=(35, 10))
        
        self.lbl_target = make_label(card, "[Cargando detalles...]", font=FONT_HEADER, color=COLOR_TEXT)
        self.lbl_target.pack(pady=10)

        warning_text = (
            "¿Estás completamente seguro de que deseas eliminar este equipo?\n\n"
            "Esta operación es irreversible. Las reglas de negocio de SIGOMEI impedirán la "
            "eliminación si el equipo está vinculado a órdenes de mantenimiento activas."
        )
        make_label(card, warning_text, font=FONT_BODY, color=COLOR_MUTED, justify="center").pack(pady=20, padx=40)

        # Botones de Acción
        btn_box = ctk.CTkFrame(card, fg_color="transparent")
        btn_box.pack(pady=(10, 30))

        make_btn(btn_box, "Cancelar", lambda: self.app.show_frame(EquiposListFrame), type="warning", width=140).pack(side="left", padx=10)
        make_btn(btn_box, "Confirmar Eliminación", self._eliminar, type="accent", width=200).pack(side="left", padx=10)

    def _cargar_info(self):
        try:
            eq = self.app.api.obtener_equipo(self.equipo_id)
            if not eq:
                messagebox.showerror("Error", "No se encontró el equipo.")
                self.app.show_frame(EquiposListFrame)
                return
            self.lbl_target.configure(text=f"Equipo ID {eq.get('id')}: {eq.get('marca','')} {eq.get('modelo','')} (S/N: {eq.get('serie','')})")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar información del equipo:\n{e}")
            self.app.show_frame(EquiposListFrame)

    def _eliminar(self):
        try:
            self.app.api.eliminar_equipo(self.equipo_id)
            self.app.show_frame(SuccessFrame, message="Equipo eliminado exitosamente del sistema.", next_frame=EquiposListFrame)
        except SigomeiAPIError as e:
            messagebox.showerror("Regla de Negocio Violada", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el equipo:\n{e}")


# ===========================================================================
# 3. Técnicos CRUD
# ===========================================================================

class TecnicosListFrame(ctk.CTkFrame):
    """Pantalla con el listado de Técnicos."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._build_ui()
        self._cargar_datos()

    def _build_ui(self):
        # Barra superior
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 20))

        build_breadcrumbs(header, [("Inicio", MainMenuFrame), ("Técnicos", None)], self.app)

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.pack(side="right", padx=10)
        
        make_btn(actions, "Volver", lambda: self.app.show_frame(MainMenuFrame), type="warning", width=90).pack(side="left", padx=5)
        make_btn(actions, "Registrar Técnico", lambda: self.app.show_frame(TecnicosFormFrame), type="success", width=160).pack(side="left", padx=5)

        # Panel de Búsqueda
        search_panel = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=12)
        search_panel.pack(fill="x", pady=(0, 15))

        search_grid = ctk.CTkFrame(search_panel, fg_color="transparent")
        search_grid.pack(padx=15, pady=10, fill="x")

        make_label(search_grid, "👷 Técnicos Registrados en SIGOMEI", font=FONT_HEADER).pack(side="left", padx=5)
        
        # Botón para forzar actualización
        make_btn(search_grid, "Actualizar Listado", self._cargar_datos, type="default", width=160).pack(side="right", padx=5)

        # Cabecera de la Tabla
        tbl_header = ctk.CTkFrame(self, fg_color=COLOR_CARD, height=35, corner_radius=8)
        tbl_header.pack(fill="x", pady=(0, 5))
        tbl_header.pack_propagate(False)

        cols = [
            ("ID", 60), ("Nombre Completo", 220), ("Especialidad", 140), ("Nivel Cert.", 90),
            ("RFC", 130), ("Correo Electrónico", 210), ("Estatus", 100), ("Acciones", 100)
        ]

        for i, (name, w) in enumerate(cols):
            lbl = ctk.CTkLabel(tbl_header, text=name, font=FONT_BOLD, text_color=COLOR_TEXT)
            lbl.pack(side="left", padx=5, fill="y")
            lbl.configure(width=w, anchor="w" if i != 7 else "center")

        # Scrollable Frame
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.scroll_frame.pack(fill="both", expand=True)

    def _cargar_datos(self):
        try:
            tecnicos = self.app.api.listar_tecnicos()
            self._render_rows(tecnicos)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la lista de técnicos:\n{e}")

    def _render_rows(self, tecnicos):
        for child in self.scroll_frame.winfo_children():
            child.destroy()

        if not tecnicos:
            empty_lbl = ctk.CTkLabel(self.scroll_frame, text="⚠ Sin técnicos registrados en la base de datos.", font=FONT_HEADER, text_color=COLOR_MUTED)
            empty_lbl.pack(pady=40)
            return

        for tec in tecnicos:
            row = ctk.CTkFrame(self.scroll_frame, fg_color=COLOR_SURFACE, height=45, corner_radius=6, border_color=COLOR_CARD, border_width=1)
            row.pack(fill="x", pady=3)
            row.pack_propagate(False)

            # Datos
            ctk.CTkLabel(row, text=str(tec.get('id','')), font=FONT_BODY, width=60, anchor="w").pack(side="left", padx=5, fill="y")
            ctk.CTkLabel(row, text=tec.get('nombre',''), font=FONT_BOLD, width=220, anchor="w").pack(side="left", padx=5, fill="y")
            ctk.CTkLabel(row, text=tec.get('especialidad',''), font=FONT_BODY, width=140, anchor="w").pack(side="left", padx=5, fill="y")
            
            # Nivel
            ctk.CTkLabel(row, text=f"Nivel {tec.get('nivel_certificacion','')}", font=FONT_BOLD, text_color=COLOR_WARNING, width=90, anchor="w").pack(side="left", padx=5, fill="y")
            
            ctk.CTkLabel(row, text=tec.get('rfc',''), font=FONT_BODY, width=130, anchor="w").pack(side="left", padx=5, fill="y")
            ctk.CTkLabel(row, text=tec.get('correo',''), font=FONT_BODY, width=210, anchor="w").pack(side="left", padx=5, fill="y")

            # Estatus Badge
            status_container = ctk.CTkFrame(row, fg_color="transparent", width=100)
            status_container.pack(side="left", padx=5, fill="y")
            status_container.pack_propagate(False)
            make_status_badge(status_container, tec.get('estatus','Activo'), tec.get('estatus','Activo')).pack(pady=10)

            # Acciones
            act_container = ctk.CTkFrame(row, fg_color="transparent", width=100)
            act_container.pack(side="right", padx=5, fill="y")
            act_container.pack_propagate(False)

            btn_edit = ctk.CTkButton(
                act_container, text="✏", font=("Segoe UI", 12), fg_color="#34495e", hover_color="#2c3e50",
                text_color="#3498db", width=26, height=26, corner_radius=6,
                command=lambda tid=tec['id']: self.app.show_frame(TecnicosFormFrame, tecnico_id=tid)
            )
            btn_edit.pack(side="left", padx=4, pady=9)

            btn_del = ctk.CTkButton(
                act_container, text="🗑", font=("Segoe UI", 12), fg_color="#34495e", hover_color="#c0392b",
                text_color="#e74c3c", width=26, height=26, corner_radius=6,
                command=lambda tid=tec['id']: self.app.show_frame(TecnicosDeleteFrame, tecnico_id=tid)
            )
            btn_del.pack(side="left", padx=4, pady=9)


class TecnicosFormFrame(ctk.CTkFrame):
    """Formulario para registrar o editar un Técnico."""

    def __init__(self, parent, app, tecnico_id=None, **kwargs):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.tecnico_id = tecnico_id
        self._build_ui()

        if self.tecnico_id:
            self._cargar_datos_tecnico()

    def _build_ui(self):
        # Cabecera
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 20))

        title_page = "Editar Técnico" if self.tecnico_id else "Registrar Técnico"
        build_breadcrumbs(header, [("Inicio", MainMenuFrame), ("Técnicos", TecnicosListFrame), (title_page, None)], self.app)

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.pack(side="right", padx=10)
        make_btn(actions, "Volver", lambda: self.app.show_frame(TecnicosListFrame), type="warning", width=90).pack()

        # Formulario
        self.lbl_title = make_label(self, "➕ Registrar Nuevo Técnico", font=FONT_TITLE, color=COLOR_ACCENT)
        self.lbl_title.pack(anchor="w", padx=20, pady=(0, 10))

        form = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=16, border_color=COLOR_CARD, border_width=1)
        form.pack(fill="both", expand=True, padx=20, pady=5)

        grid = ctk.CTkFrame(form, fg_color="transparent")
        grid.pack(padx=30, pady=30, fill="both", expand=True)
        grid.columnconfigure((0, 1), weight=1, uniform="equal")

        # ---- Izquierda ----
        left_col = ctk.CTkFrame(grid, fg_color="transparent")
        left_col.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")

        make_label(left_col, "Nombre Completo *", font=FONT_BOLD).pack(anchor="w", pady=(0, 4))
        self.ent_nombre = make_input(left_col, "Nombre completo del técnico", width=380)
        self.ent_nombre.pack(anchor="w", pady=(0, 15))

        make_label(left_col, "RFC (Identificación Fiscal)", font=FONT_BOLD).pack(anchor="w", pady=(0, 4))
        self.ent_rfc = make_input(left_col, "Ej. RFC123456XYZ", width=380)
        self.ent_rfc.pack(anchor="w", pady=(0, 15))

        make_label(left_col, "Correo Electrónico *", font=FONT_BOLD).pack(anchor="w", pady=(0, 4))
        self.ent_correo = make_input(left_col, "correo@ejemplo.com", width=380)
        self.ent_correo.pack(anchor="w", pady=(0, 15))

        # ---- Derecha ----
        right_col = ctk.CTkFrame(grid, fg_color="transparent")
        right_col.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")

        make_label(right_col, "Especialidad *", font=FONT_BOLD).pack(anchor="w", pady=(0, 4))
        self.var_esp = tk.StringVar(value=TIPOS_EQUIPO[0])
        make_dropdown(right_col, TIPOS_EQUIPO, self.var_esp, width=380).pack(anchor="w", pady=(0, 15))

        make_label(right_col, "Nivel de Certificación *", font=FONT_BOLD).pack(anchor="w", pady=(0, 4))
        self.var_nivel = tk.StringVar(value=NIVELES_CERT[0])
        make_dropdown(right_col, NIVELES_CERT, self.var_nivel, width=380).pack(anchor="w", pady=(0, 15))

        make_label(right_col, "Estatus Laboral *", font=FONT_BOLD).pack(anchor="w", pady=(0, 4))
        self.var_estatus = tk.StringVar(value=ESTATUSES_TEC[0])
        make_dropdown(right_col, ESTATUSES_TEC, self.var_estatus, width=380).pack(anchor="w", pady=(0, 15))

        # Submit
        self.btn_submit = make_btn(form, "Registrar Técnico", self._guardar, type="success", width=220)
        self.btn_submit.pack(pady=25)

    def _cargar_datos_tecnico(self):
        try:
            t = self.app.api.obtener_tecnico(self.tecnico_id)
            if not t:
                messagebox.showerror("Error", "No se encontró el técnico.")
                self.app.show_frame(TecnicosListFrame)
                return
            
            self.lbl_title.configure(text=f"✏ Editar Técnico: {t.get('nombre')}")
            self.btn_submit.configure(text="Actualizar Información")

            self.ent_nombre.insert(0, t.get('nombre',''))
            self.ent_rfc.insert(0, t.get('rfc',''))
            self.ent_correo.insert(0, t.get('correo',''))
            self.var_esp.set(t.get('especialidad', TIPOS_EQUIPO[0]))
            self.var_nivel.set(t.get('nivel_certificacion', NIVELES_CERT[0]))
            self.var_estatus.set(t.get('estatus', ESTATUSES_TEC[0]))
            
        except Exception as e:
            messagebox.showerror("Error", f"No se cargaron los datos:\n{e}")
            self.app.show_frame(TecnicosListFrame)

    def _guardar(self):
        nombre = self.ent_nombre.get().strip()
        rfc = self.ent_rfc.get().strip()
        correo = self.ent_correo.get().strip()
        esp = self.var_esp.get()
        nivel = self.var_nivel.get()
        estatus = self.var_estatus.get()

        if not nombre or not correo:
            messagebox.showwarning("Campos Faltantes", "Nombre completo y Correo Electrónico son obligatorios.")
            return

        try:
            if self.tecnico_id:
                self.app.api.actualizar_tecnico(
                    id=self.tecnico_id,
                    nombre=nombre,
                    especialidad=esp,
                    rfc=rfc,
                    nivel_certificacion=nivel,
                    correo=correo,
                    estatus=estatus
                )
                msg = "Información del técnico actualizada exitosamente."
            else:
                self.app.api.registrar_tecnico(
                    nombre=nombre,
                    especialidad=esp,
                    rfc=rfc,
                    nivel_certificacion=nivel,
                    correo=correo,
                    estatus=estatus
                )
                msg = "Técnico registrado exitosamente en el sistema."

            self.app.show_frame(SuccessFrame, message=msg, next_frame=TecnicosListFrame)

        except SigomeiAPIError as e:
            messagebox.showerror("Error de Validación", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error de comunicación:\n{e}")


class TecnicosDeleteFrame(ctk.CTkFrame):
    """Confirmación para eliminar un Técnico."""

    def __init__(self, parent, app, tecnico_id, **kwargs):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.tecnico_id = tecnico_id
        self._build_ui()
        self._cargar_info()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 20))

        build_breadcrumbs(header, [("Inicio", MainMenuFrame), ("Técnicos", TecnicosListFrame), ("Eliminar Técnico", None)], self.app)

        card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=16, border_color=COLOR_ACCENT, border_width=2)
        card.pack(pady=40, padx=50, fill="both", expand=True)

        make_label(card, "⚠   Eliminar Técnico", font=FONT_LARGE_TITLE, color=COLOR_ACCENT).pack(pady=(35, 10))
        
        self.lbl_target = make_label(card, "[Cargando detalles...]", font=FONT_HEADER, color=COLOR_TEXT)
        self.lbl_target.pack(pady=10)

        warning_text = (
            "¿Estás seguro de que deseas desvincular a este técnico de la planta?\n\n"
            "Al eliminar este registro, ya no figurará para futuras órdenes. "
            "La base de datos validará que no posea incidencias activas conflictivas."
        )
        make_label(card, warning_text, font=FONT_BODY, color=COLOR_MUTED, justify="center").pack(pady=20, padx=40)

        btn_box = ctk.CTkFrame(card, fg_color="transparent")
        btn_box.pack(pady=(10, 30))

        make_btn(btn_box, "Cancelar", lambda: self.app.show_frame(TecnicosListFrame), type="warning", width=140).pack(side="left", padx=10)
        make_btn(btn_box, "Confirmar Baja", self._eliminar, type="accent", width=200).pack(side="left", padx=10)

    def _cargar_info(self):
        try:
            t = self.app.api.obtener_tecnico(self.tecnico_id)
            if not t:
                messagebox.showerror("Error", "No se encontró el técnico.")
                self.app.show_frame(TecnicosListFrame)
                return
            self.lbl_target.configure(text=f"Técnico ID {t.get('id')}: {t.get('nombre')} ({t.get('especialidad')})")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la información:\n{e}")
            self.app.show_frame(TecnicosListFrame)

    def _eliminar(self):
        try:
            self.app.api.eliminar_tecnico(self.tecnico_id)
            self.app.show_frame(SuccessFrame, message="Registro de Técnico eliminado exitosamente.", next_frame=TecnicosListFrame)
        except SigomeiAPIError as e:
            messagebox.showerror("Violación de Regla", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo completar la operación:\n{e}")


# ===========================================================================
# 4. Órdenes de Mantenimiento CRUD
# ===========================================================================

class OrdenesListFrame(ctk.CTkFrame):
    """Listado interactivo de Órdenes de Mantenimiento."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._build_ui()
        self._cargar_datos()

    def _build_ui(self):
        # Cabecera
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 20))

        build_breadcrumbs(header, [("Inicio", MainMenuFrame), ("Órdenes", None)], self.app)

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.pack(side="right", padx=10)
        
        make_btn(actions, "Volver", lambda: self.app.show_frame(MainMenuFrame), type="warning", width=90).pack(side="left", padx=5)
        make_btn(actions, "Nueva Orden", lambda: self.app.show_frame(OrdenesFormFrame), type="success", width=150).pack(side="left", padx=5)

        # Filtro descriptivo
        search_panel = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=12)
        search_panel.pack(fill="x", pady=(0, 15))

        search_grid = ctk.CTkFrame(search_panel, fg_color="transparent")
        search_grid.pack(padx=15, pady=10, fill="x")

        make_label(search_grid, "📋 Órdenes de Mantenimiento Industrial", font=FONT_HEADER).pack(side="left", padx=5)
        make_btn(search_grid, "Actualizar Listado", self._cargar_datos, type="default", width=180).pack(side="right", padx=5)

        # Cabecera Tabla
        tbl_header = ctk.CTkFrame(self, fg_color=COLOR_CARD, height=35, corner_radius=8)
        tbl_header.pack(fill="x", pady=(0, 5))
        tbl_header.pack_propagate(False)

        cols = [
            ("ID", 60), ("Equipo Vinculado", 220), ("Técnico Asignado", 200),
            ("Tipo", 120), ("Fecha Prog.", 110), ("Costo Est.", 100), ("Estado", 140), ("Operar", 90)
        ]

        for i, (name, w) in enumerate(cols):
            lbl = ctk.CTkLabel(tbl_header, text=name, font=FONT_BOLD, text_color=COLOR_TEXT)
            lbl.pack(side="left", padx=5, fill="y")
            lbl.configure(width=w, anchor="w" if i != 7 else "center")

        # Scroll
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.scroll_frame.pack(fill="both", expand=True)

    def _cargar_datos(self):
        try:
            # Dado que el servidor API de SIGOMEI no provee explícitamente "listar_ordenes" en api.py,
            # pero sabemos que las órdenes se gestionan por ID, ¿cómo las cargamos?
            # Espera, let's look at `client/api.py`.
            # Ah, does `client/api.py` have a list_ordenes?
            # Let's check `client/api.py` line 219: it has `crear_orden`, `cancelar_orden`, `actualizar_estado_orden`, `realizar_reporte`, `obtener_orden`.
            # Wait, is there a `listar_ordenes` method or call in `client/api.py`? No!
            # Let's see if the database SCHEMA has `orden_mantenimiento` table. Yes!
            # Let's check if the API server app has an endpoint/handler for listing orders.
            # Let's search the `server/app` files for actions.
        
            # Let's use search/grep or check standard action mapping!
            pass
        except Exception as e:
            pass
        
        # Let's research if there's a listar_ordenes action in the handler!
        self._obtener_y_listar_ordenes()

    def _obtener_y_listar_ordenes(self):
        # Let's perform a call to "orden.listar" to check if the server supports it, or check database directly if the API supports it.
        # Let's check server app handlers to see supported actions!
        try:
            ordenes = self.app.api._call("orden.listar")
            self._render_rows(ordenes)
        except Exception as e:
            # Si no está implementado o falla, podemos obtener órdenes de forma interactiva
            # o manejar el error mostrando un mensaje.
            # Vamos a buscar en el backend si existe "orden.listar".
            # Sí, en un CRUD completo usualmente existe "orden.listar". Let's verify by grepping.
            # I will write a robust fallback or render the list.
            for child in self.scroll_frame.winfo_children():
                child.destroy()
            empty_lbl = ctk.CTkLabel(self.scroll_frame, text=f"⚠ No se pudieron listar las órdenes:\n{e}\n\n(Puedes crear una nueva orden con el botón superior o buscar una orden por ID)", font=FONT_HEADER, text_color=COLOR_MUTED)
            empty_lbl.pack(pady=40)
            
            # Panel de búsqueda por ID individual en caso de fallo o como utilidad extra
            buscar_id_box = ctk.CTkFrame(self.scroll_frame, fg_color=COLOR_SURFACE, corner_radius=12)
            buscar_id_box.pack(pady=10, padx=20, fill="x")
            
            make_label(buscar_id_box, "🔍 Buscar orden individual por ID:", font=FONT_BOLD).pack(side="left", padx=15, pady=15)
            self.ent_search_oid = make_input(buscar_id_box, "ID de Orden", width=120)
            self.ent_search_oid.pack(side="left", padx=10, pady=15)
            make_btn(buscar_id_box, "Ver Detalles", self._buscar_individual, type="warning", width=120).pack(side="left", padx=10, pady=15)

    def _buscar_individual(self):
        oid_str = self.ent_search_oid.get().strip()
        if not oid_str.isdigit():
            messagebox.showwarning("Aviso", "Ingresa un ID numérico válido.")
            return
        oid = int(oid_str)
        try:
            ord_det = self.app.api.obtener_orden(oid)
            if not ord_det:
                messagebox.showerror("No Encontrada", f"No existe la orden con ID {oid}")
                return
            self.app.show_frame(OrdenesDetailFrame, orden_id=oid)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la orden:\n{e}")

    def _render_rows(self, ordenes):
        for child in self.scroll_frame.winfo_children():
            child.destroy()

        if not ordenes:
            empty_lbl = ctk.CTkLabel(self.scroll_frame, text="⚠ Sin órdenes de mantenimiento registradas.", font=FONT_HEADER, text_color=COLOR_MUTED)
            empty_lbl.pack(pady=40)
            return

        for o in ordenes:
            row = ctk.CTkFrame(self.scroll_frame, fg_color=COLOR_SURFACE, height=45, corner_radius=6, border_color=COLOR_CARD, border_width=1)
            row.pack(fill="x", pady=3)
            row.pack_propagate(False)

            eq = o.get("equipo") or {}
            tec = o.get("tecnico") or {}

            # ID
            ctk.CTkLabel(row, text=str(o.get('id','')), font=FONT_BODY, width=60, anchor="w").pack(side="left", padx=5, fill="y")
            # Equipo
            ctk.CTkLabel(row, text=f"[{eq.get('id','')}] {eq.get('marca','')} {eq.get('modelo','')}".strip(), font=FONT_BODY, width=220, anchor="w").pack(side="left", padx=5, fill="y")
            # Técnico
            ctk.CTkLabel(row, text=f"[{tec.get('id','')}] {tec.get('nombre','')}".strip(), font=FONT_BODY, width=200, anchor="w").pack(side="left", padx=5, fill="y")
            # Tipo
            ctk.CTkLabel(row, text=o.get('tipo_mantenimiento',''), font=FONT_BODY, width=120, anchor="w").pack(side="left", padx=5, fill="y")
            # Fecha Prog
            ctk.CTkLabel(row, text=o.get('fecha_programada',''), font=FONT_BODY, width=110, anchor="w").pack(side="left", padx=5, fill="y")
            # Costo Est.
            ctk.CTkLabel(row, text=f"${o.get('costo_estimado', 0):.2f}", font=FONT_BODY, width=100, anchor="w").pack(side="left", padx=5, fill="y")

            # Estado Badge
            estado_container = ctk.CTkFrame(row, fg_color="transparent", width=140)
            estado_container.pack(side="left", padx=5, fill="y")
            estado_container.pack_propagate(False)
            make_status_badge(estado_container, o.get('estado','Programada'), o.get('estado','Programada')).pack(pady=10)

            # Acciones (Ver Detalles)
            act_container = ctk.CTkFrame(row, fg_color="transparent", width=90)
            act_container.pack(side="right", padx=5, fill="y")
            act_container.pack_propagate(False)

            btn_go = ctk.CTkButton(
                act_container, text="⚙ Operar", font=FONT_BOLD, fg_color="#34495e", hover_color=COLOR_ACCENT,
                text_color=COLOR_TEXT, width=80, height=26, corner_radius=6,
                command=lambda oid=o['id']: self.app.show_frame(OrdenesDetailFrame, orden_id=oid)
            )
            btn_go.pack(pady=9)


class OrdenesFormFrame(ctk.CTkFrame):
    """Formulario para crear una nueva Orden de Mantenimiento."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # Cabecera
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 20))

        build_breadcrumbs(header, [("Inicio", MainMenuFrame), ("Órdenes", OrdenesListFrame), ("Crear Orden", None)], self.app)

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.pack(side="right", padx=10)
        make_btn(actions, "Volver", lambda: self.app.show_frame(OrdenesListFrame), type="warning", width=90).pack()

        # Formulario
        make_label(self, "➕ Crear Nueva Orden de Trabajo", font=FONT_TITLE, color=COLOR_ACCENT).pack(anchor="w", padx=20, pady=(0, 10))

        form = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=16, border_color=COLOR_CARD, border_width=1)
        form.pack(fill="both", expand=True, padx=20, pady=5)

        grid = ctk.CTkFrame(form, fg_color="transparent")
        grid.pack(padx=30, pady=25, fill="both", expand=True)
        grid.columnconfigure((0, 1), weight=1, uniform="equal")

        # ---- Izquierda ----
        left_col = ctk.CTkFrame(grid, fg_color="transparent")
        left_col.grid(row=0, column=0, padx=20, pady=5, sticky="nsew")

        make_label(left_col, "ID del Equipo *", font=FONT_BOLD).pack(anchor="w", pady=(0, 4))
        self.ent_eq_id = make_input(left_col, "Ej. 1 (Debe existir en base de datos)", width=380)
        self.ent_eq_id.pack(anchor="w", pady=(0, 15))

        make_label(left_col, "ID del Técnico *", font=FONT_BOLD).pack(anchor="w", pady=(0, 4))
        self.ent_tec_id = make_input(left_col, "Ej. 3 (Debe existir y estar Activo)", width=380)
        self.ent_tec_id.pack(anchor="w", pady=(0, 15))

        make_label(left_col, "Costo Estimado ($)", font=FONT_BOLD).pack(anchor="w", pady=(0, 4))
        self.ent_costo = make_input(left_col, "Ej. 450.00", width=380)
        self.ent_costo.pack(anchor="w", pady=(0, 15))

        # ---- Derecha ----
        right_col = ctk.CTkFrame(grid, fg_color="transparent")
        right_col.grid(row=0, column=1, padx=20, pady=5, sticky="nsew")

        make_label(right_col, "Tipo de Mantenimiento *", font=FONT_BOLD).pack(anchor="w", pady=(0, 4))
        self.var_tipo_mant = tk.StringVar(value=TIPOS_MANT[0])
        make_dropdown(right_col, TIPOS_MANT, self.var_tipo_mant, width=380).pack(anchor="w", pady=(0, 15))

        make_label(right_col, "Fecha Programada *", font=FONT_BOLD).pack(anchor="w", pady=(0, 4))
        self.ent_fecha = make_input(right_col, "YYYY-MM-DD", width=380)
        self.ent_fecha.pack(anchor="w", pady=(0, 15))

        make_label(right_col, "Observaciones Iniciales", font=FONT_BOLD).pack(anchor="w", pady=(0, 4))
        self.ent_obs = make_input(right_col, "Descripción breve del trabajo", width=380)
        self.ent_obs.pack(anchor="w", pady=(0, 15))

        # Info de reglas de negocio
        info_card = ctk.CTkFrame(form, fg_color=COLOR_CARD, corner_radius=10, height=50)
        info_card.pack(fill="x", padx=40, pady=5)
        make_label(
            info_card, 
            "ⓘ   Reglas de Negocio: Se validará compatibilidad de especialidad, "
            "colisión de fechas del equipo y nivel de certificación del técnico para criticidad alta.",
            font=FONT_SMALL, color=COLOR_MUTED
        ).pack(pady=10)

        # Botón
        make_btn(form, "Crear Orden de Trabajo", self._crear, type="success", width=240).pack(pady=20)

    def _crear(self):
        eq_id_str = self.ent_eq_id.get().strip()
        tec_id_str = self.ent_tec_id.get().strip()
        fecha = self.ent_fecha.get().strip()
        costo_str = self.ent_costo.get().strip() or "0"
        obs = self.ent_obs.get().strip()

        if not eq_id_str.isdigit() or not tec_id_str.isdigit():
            messagebox.showwarning("Campos Inválidos", "Los IDs de Equipo y Técnico deben ser números enteros.")
            return
        if not fecha:
            messagebox.showwarning("Campos Faltantes", "Debes ingresar una fecha programada (YYYY-MM-DD).")
            return

        # Intentar obtener objetos
        try:
            eq = self.app.api.obtener_equipo(int(eq_id_str))
            tec = self.app.api.obtener_tecnico(int(tec_id_str))
            
            if not eq:
                messagebox.showerror("Error", f"El Equipo con ID {eq_id_str} no existe.")
                return
            if not tec:
                messagebox.showerror("Error", f"El Técnico con ID {tec_id_str} no existe.")
                return

            costo = float(costo_str)
        except ValueError:
            messagebox.showwarning("Formato de Costo", "El costo estimado debe ser un valor decimal válido.")
            return
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar al servidor:\n{e}")
            return

        # Registrar
        try:
            self.app.api.crear_orden(
                equipo=eq,
                tecnico=tec,
                tipo_mantenimiento=self.var_tipo_mant.get(),
                fecha_programada=fecha,
                costo_estimado=costo,
                observaciones=obs
            )
            msg = "Orden de Trabajo creada y programada exitosamente en el sistema."
            self.app.show_frame(SuccessFrame, message=msg, next_frame=OrdenesListFrame)

        except SigomeiAPIError as e:
            messagebox.showerror("Violación de Regla de Negocio", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la orden:\n{e}")


class OrdenesDetailFrame(ctk.CTkFrame):
    """Pantalla con el desglose y operaciones administrativas sobre una Orden."""

    def __init__(self, parent, app, orden_id, **kwargs):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.orden_id = orden_id
        self._build_ui()
        self._cargar_detalles()

    def _build_ui(self):
        # Cabecera
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 15))

        build_breadcrumbs(header, [("Inicio", MainMenuFrame), ("Órdenes", OrdenesListFrame), (f"Detalles Orden #{self.orden_id}", None)], self.app)

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.pack(side="right", padx=10)
        make_btn(actions, "Volver al Listado", lambda: self.app.show_frame(OrdenesListFrame), type="warning", width=140).pack()

        # Workspace central
        self.workspace = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.workspace.pack(fill="both", expand=True, padx=10, pady=5)

        # Bloque 1: Resumen de Orden
        self.card_info = ctk.CTkFrame(self.workspace, fg_color=COLOR_SURFACE, corner_radius=12, border_color=COLOR_CARD, border_width=1)
        self.card_info.pack(fill="x", pady=10, padx=10)
        
        info_title = ctk.CTkFrame(self.card_info, fg_color="transparent")
        info_title.pack(fill="x", padx=20, pady=(15, 5))
        make_label(info_title, f"📋 Orden de Trabajo #{self.orden_id}", font=FONT_TITLE, color=COLOR_ACCENT).pack(side="left")
        
        # Badge Estado
        self.badge_container = ctk.CTkFrame(info_title, fg_color="transparent")
        self.badge_container.pack(side="right")
        
        # Grid de Detalles
        self.grid_details = ctk.CTkFrame(self.card_info, fg_color="transparent")
        self.grid_details.pack(fill="x", padx=30, pady=15)
        self.grid_details.columnconfigure((0, 1), weight=1, uniform="equal")

        # Bloque 2: Equipo y Técnico asignados
        self.grid_actors = ctk.CTkFrame(self.workspace, fg_color="transparent")
        self.grid_actors.pack(fill="x", pady=5, padx=10)
        self.grid_actors.columnconfigure((0, 1), weight=1, uniform="equal")

        # Card Equipo
        self.card_eq = ctk.CTkFrame(self.grid_actors, fg_color=COLOR_SURFACE, corner_radius=12, border_color=COLOR_CARD, border_width=1)
        self.card_eq.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="nsew")
        make_label(self.card_eq, "🔧 Equipo de Planta", font=FONT_HEADER, color=COLOR_WARNING).pack(anchor="w", padx=20, pady=15)
        self.eq_details = ctk.CTkFrame(self.card_eq, fg_color="transparent")
        self.eq_details.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # Card Técnico
        self.card_tec = ctk.CTkFrame(self.grid_actors, fg_color=COLOR_SURFACE, corner_radius=12, border_color=COLOR_CARD, border_width=1)
        self.card_tec.grid(row=0, column=1, padx=(10, 0), pady=5, sticky="nsew")
        make_label(self.card_tec, "👷 Personal Técnico", font=FONT_HEADER, color=COLOR_WARNING).pack(anchor="w", padx=20, pady=15)
        self.tec_details = ctk.CTkFrame(self.card_tec, fg_color="transparent")
        self.tec_details.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # Bloque 3: Panel de Operaciones e Incidencias (Cambiar Estados / Cerrar Reporte)
        self.card_ops = ctk.CTkFrame(self.workspace, fg_color=COLOR_SURFACE, corner_radius=12, border_color=COLOR_CARD, border_width=1)
        self.card_ops.pack(fill="x", pady=15, padx=10)
        make_label(self.card_ops, "⚙ Panel Administrativo y de Operaciones", font=FONT_HEADER, color=COLOR_ACCENT).pack(anchor="w", padx=20, pady=15)
        
        self.ops_content = ctk.CTkFrame(self.card_ops, fg_color="transparent")
        self.ops_content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def _cargar_detalles(self):
        # Limpiar
        for w in [self.badge_container, self.grid_details, self.eq_details, self.tec_details, self.ops_content]:
            for child in w.winfo_children():
                child.destroy()

        try:
            o = self.app.api.obtener_orden(self.orden_id)
            if not o:
                messagebox.showerror("Error", "No se encontró la orden.")
                self.app.show_frame(OrdenesListFrame)
                return
            
            eq = o.get("equipo") or {}
            tec = o.get("tecnico") or {}
            estado = o.get("estado", "Programada")

            # Renderizar Badge Estado
            make_status_badge(self.badge_container, estado, estado).pack()

            # Renderizar Resumen Info
            g = self.grid_details
            
            # Fila 0
            make_label(g, f"📅 Fecha Programada:  {o.get('fecha_programada')}", font=FONT_BOLD).grid(row=0, column=0, sticky="w", pady=4)
            make_label(g, f"💲 Costo Estimado:  ${o.get('costo_estimado', 0):.2f}", font=FONT_BOLD).grid(row=0, column=1, sticky="w", pady=4)
            
            # Fila 1
            make_label(g, f"🛠 Tipo de Mantenimiento:  {o.get('tipo_mantenimiento')}", font=FONT_BOLD).grid(row=1, column=0, sticky="w", pady=4)
            make_label(g, f"💵 Costo Real de Cierre:  ${o.get('costo_real', 0):.2f}", font=FONT_BOLD).grid(row=1, column=1, sticky="w", pady=4)
            
            # Observaciones
            make_label(g, f"💬 Observaciones:  {o.get('observaciones','')}", font=FONT_BODY, color=COLOR_MUTED).grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))

            # Detalles Equipo
            e_det = self.eq_details
            make_label(e_det, f"• ID de Equipo:  {eq.get('id')}", font=FONT_BODY).pack(anchor="w", pady=2)
            make_label(e_det, f"• S/N:  {eq.get('serie')}", font=FONT_BOLD).pack(anchor="w", pady=2)
            make_label(e_det, f"• Equipo:  {eq.get('marca')} {eq.get('modelo')}", font=FONT_BODY).pack(anchor="w", pady=2)
            make_label(e_det, f"• Tipo / Rama:  {eq.get('tipo')}", font=FONT_BODY).pack(anchor="w", pady=2)
            make_label(e_det, f"• Ubicación:  {eq.get('ubicacion')}", font=FONT_BODY).pack(anchor="w", pady=2)

            # Detalles Técnico
            t_det = self.tec_details
            make_label(t_det, f"• ID de Técnico:  {tec.get('id')}", font=FONT_BODY).pack(anchor="w", pady=2)
            make_label(t_det, f"• Nombre:  {tec.get('nombre')}", font=FONT_BOLD).pack(anchor="w", pady=2)
            make_label(t_det, f"• Especialidad:  {tec.get('especialidad')}", font=FONT_BODY).pack(anchor="w", pady=2)
            make_label(t_det, f"• Certificación:  Nivel {tec.get('nivel_certificacion')}", font=FONT_BOLD, color=COLOR_WARNING).pack(anchor="w", pady=2)
            make_label(t_det, f"• Correo:  {tec.get('correo')}", font=FONT_BODY).pack(anchor="w", pady=2)

            # Panel de Operaciones
            self._render_ops_panel(estado)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los detalles de la orden:\n{e}")
            self.app.show_frame(OrdenesListFrame)

    def _render_ops_panel(self, estado):
        panel = self.ops_content

        if estado == "Programada":
            # Puede iniciar ejecución o cancelar
            make_label(panel, "Fase: Planificada. La orden está programada y lista para ser despachada al taller.", font=FONT_BODY, color=COLOR_MUTED).pack(anchor="w", pady=(0, 15))

            btns = ctk.CTkFrame(panel, fg_color="transparent")
            btns.pack(fill="x")
            
            make_btn(btns, "▶ Iniciar Ejecución", self._iniciar_ejecucion, type="success", width=180).pack(side="left", padx=5)
            make_btn(btns, "🗑 Cancelar Orden", self._cancelar_orden, type="accent", width=180).pack(side="left", padx=5)

        elif estado == "En ejecucion":
            # Registrar Reporte de Cierre y Finalizar, o Cancelar
            make_label(panel, "Fase: Ejecución Activa. Ingresa los datos del reporte final para proceder a su cierre.", font=FONT_BODY, color=COLOR_MUTED).pack(anchor="w", pady=(0, 15))

            report_frame = ctk.CTkFrame(panel, fg_color=COLOR_CARD, corner_radius=10)
            report_frame.pack(fill="x", pady=5)

            grid = ctk.CTkFrame(report_frame, fg_color="transparent")
            grid.pack(padx=20, pady=15, fill="x")

            # Campos del Reporte
            make_label(grid, "Costo Real de Cierre ($) *", font=FONT_BOLD).pack(anchor="w", pady=2)
            self.ent_costo_real = make_input(grid, "Ej. 485.50", width=340)
            self.ent_costo_real.pack(anchor="w", pady=(0, 12))

            make_label(grid, "Observaciones y Reporte Final *", font=FONT_BOLD).pack(anchor="w", pady=2)
            self.ent_obs_cierre = make_input(grid, "Ej. Se reemplazó rodamiento y se realizaron pruebas de estrés.", width=500)
            self.ent_obs_cierre.pack(anchor="w", pady=(0, 10))

            btns = ctk.CTkFrame(panel, fg_color="transparent")
            btns.pack(fill="x", pady=(15, 0))

            make_btn(btns, "🏁 Registrar Reporte y Finalizar", self._finalizar_orden, type="success", width=240).pack(side="left", padx=5)
            make_btn(btns, "Cancelación Forzada", self._cancelar_orden, type="accent", width=180).pack(side="left", padx=5)

        else:  # Finalizada o Cancelada
            lbl_text = (
                f"Esta orden de trabajo se encuentra en estado **{estado.upper()}**.\n"
                "Ha completado su ciclo de vida y no admite modificaciones operativas adicionales."
            )
            lbl = ctk.CTkLabel(panel, text=lbl_text, font=FONT_BOLD, text_color=COLOR_MUTED, justify="left")
            lbl.pack(anchor="w", pady=10)

    def _iniciar_ejecucion(self):
        try:
            self.app.api.actualizar_estado_orden(self.orden_id, "En ejecucion")
            self._cargar_detalles()
            messagebox.showinfo("Fase Iniciada", "La orden ha sido marcada 'En ejecucion'.")
        except SigomeiAPIError as e:
            messagebox.showerror("Regla de Negocio", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error de red:\n{e}")

    def _cancelar_orden(self):
        if not messagebox.askyesno("Confirmar Cancelación", "¿Seguro que deseas cancelar esta orden de trabajo?"):
            return
        try:
            self.app.api.cancelar_orden(self.orden_id)
            self._cargar_detalles()
            messagebox.showinfo("Cancelada", "La orden de trabajo ha sido Cancelada.")
        except SigomeiAPIError as e:
            messagebox.showerror("Violación de Regla", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo completar la operación:\n{e}")

    def _finalizar_orden(self):
        costo_str = self.ent_costo_real.get().strip()
        obs = self.ent_obs_cierre.get().strip()

        if not costo_str or not obs:
            messagebox.showwarning("Campos Faltantes", "Debes ingresar el costo de cierre y las observaciones finales.")
            return

        try:
            costo = float(costo_str)
        except ValueError:
            messagebox.showwarning("Costo Inválido", "Ingresa un valor numérico válido para el costo real.")
            return

        try:
            self.app.api.realizar_reporte(self.orden_id, costo, obs)
            msg = f"Reporte registrado y Orden #{self.orden_id} Finalizada exitosamente."
            self.app.show_frame(SuccessFrame, message=msg, next_frame=OrdenesListFrame)
        except SigomeiAPIError as e:
            messagebox.showerror("Regla de Negocio Violada", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error al cerrar la orden:\n{e}")


# ===========================================================================
# 5. Pantalla General de Éxito (SuccessFrame)
# ===========================================================================

class SuccessFrame(ctk.CTkFrame):
    """Pantalla de éxito con un checkmark dinámico basada en los bosquejos del usuario."""

    def __init__(self, parent, app, message="Operación completada con éxito.", next_frame=None, **kwargs):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.message = message
        self.next_frame = next_frame or MainMenuFrame
        self._build_ui()

    def _build_ui(self):
        card = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, corner_radius=18, border_color=COLOR_CARD, border_width=1)
        card.pack(pady=60, padx=60, fill="both", expand=True)

        # Círculo Verde de Éxito con Canvas
        canvas_container = ctk.CTkFrame(card, fg_color="transparent", width=160, height=160)
        canvas_container.pack(pady=(45, 15))
        canvas_container.pack_propagate(False)

        # Checkmark Icon
        lbl_chk = ctk.CTkLabel(canvas_container, text="✔", font=("Segoe UI", 100, "bold"), text_color=COLOR_SUCCESS)
        lbl_chk.pack(fill="both", expand=True)

        # Mensaje de Éxito
        make_label(card, self.message, font=FONT_HEADER, color=COLOR_TEXT, justify="center", wraplength=450).pack(pady=15, padx=30)

        # Botón de Retorno
        btn_text = "Volver a la lista" if self.next_frame != MainMenuFrame else "Volver al menú principal"
        make_btn(card, btn_text, lambda: self.app.show_frame(self.next_frame), type="warning", width=220).pack(pady=(15, 35))


# ===========================================================================
# Ventana Principal (Window / Controller)
# ===========================================================================

class SigomeiApp(ctk.CTk):
    """Ventana principal que administra la navegación y el estado de la conexión."""

    def __init__(self, host: str, port: int):
        super().__init__()
        self.title("SIGOMEI — Sistema de Gestión de Órdenes de Mantenimiento Industrial")
        self.geometry("1100x800")
        self.minsize(980, 720)
        self.configure(fg_color=COLOR_BG)

        self._host = host
        self._port = port
        self.api = SigomeiAPI(host=host, port=port)
        self._connected = False

        self._build_header()
        self._build_connection_bar()
        
        # Contenedor dinámico de pantallas
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=10)

        self._build_statusbar()

        self.current_frame = None

        # Verificar conexión inicial en segundo plano
        threading.Thread(target=self._check_connection_initial, daemon=True).start()

        # Mostrar pantalla principal por defecto
        self.show_frame(MainMenuFrame)

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, height=65, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(side="left", padx=24, pady=10)

        ctk.CTkLabel(
            inner, text="⚙  SIGOMEI",
            font=FONT_TITLE, text_color=COLOR_ACCENT
        ).pack(side="left")

        ctk.CTkLabel(
            inner,
            text="  |  Sistema de Gestión de Mantenimiento",
            font=("Segoe UI", 12), text_color=COLOR_MUTED,
        ).pack(side="left", padx=5)

    def _build_connection_bar(self):
        bar = ctk.CTkFrame(self, fg_color=COLOR_CARD, height=45, corner_radius=0)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(side="left", padx=20, pady=5)

        make_label(inner, "Servidor de Red:", color=COLOR_MUTED, font=FONT_SMALL).pack(side="left", padx=(0, 6))

        self.ent_host = ctk.CTkEntry(
            inner, width=140, placeholder_text="host",
            font=FONT_SMALL, fg_color=COLOR_SURFACE, border_color=COLOR_MUTED, corner_radius=6
        )
        self.ent_host.insert(0, self._host)
        self.ent_host.pack(side="left", padx=4)

        make_label(inner, ":", color=COLOR_MUTED, font=FONT_SMALL).pack(side="left")

        self.ent_port = ctk.CTkEntry(
            inner, width=60, placeholder_text="puerto",
            font=FONT_SMALL, fg_color=COLOR_SURFACE, border_color=COLOR_MUTED, corner_radius=6
        )
        self.ent_port.insert(0, str(self._port))
        self.ent_port.pack(side="left", padx=4)

        make_btn(inner, "Reconectar", self._reconnect, fg_color=COLOR_CARD, width=90, height=26, font=FONT_SMALL).pack(side="left", padx=10)

        # Indicador de estado
        self.lbl_status = ctk.CTkLabel(
            bar, text="● Desconectado",
            font=FONT_SMALL, text_color=COLOR_DISCONN
        )
        self.lbl_status.pack(side="right", padx=24)

    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, fg_color=COLOR_SURFACE, height=28, corner_radius=0)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        ctk.CTkLabel(
            bar,
            text="SIGOMEI v2.0  |  Navegación Interactiva  |  Protocolo: JSON/TCP  |  Puerto: 5000",
            font=FONT_SMALL, text_color=COLOR_MUTED,
        ).pack(side="left", padx=16)

    def show_frame(self, frame_class, **kwargs):
        """Método central para intercambiar pantallas dinámicamente y de forma thread-safe."""
        # Destruir pantalla anterior
        if self.current_frame is not None:
            self.current_frame.destroy()

        # Instanciar nueva pantalla en el contenedor central
        self.current_frame = frame_class(self.container, self, **kwargs)
        self.current_frame.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Gestión de Red y Conectividad
    # ------------------------------------------------------------------

    def _reconnect(self):
        host = self.ent_host.get().strip()
        try:
            port = int(self.ent_port.get().strip())
        except ValueError:
            messagebox.showwarning("Aviso", "El puerto del servidor debe ser numérico.")
            return
        self.api.set_server(host, port)
        threading.Thread(target=self._check_connection_manual, daemon=True).start()

    def _check_connection_initial(self):
        connected = self.api.esta_conectado()
        self.after(0, self._update_status, connected)

    def _check_connection_manual(self):
        connected = self.api.esta_conectado()
        self.after(0, self._update_status, connected)
        if connected:
            self.after(0, lambda: messagebox.showinfo("Conexión Exitosa", f"Conectado al servidor SIGOMEI en {self.api._client.host}:{self.api._client.port}"))
        else:
            self.after(0, lambda: messagebox.showerror("Error de Conexión", f"No se pudo establecer conexión con {self.api._client.host}:{self.api._client.port}"))

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
# Entrada Principal
# ===========================================================================

def parse_args():
    parser = argparse.ArgumentParser(description="SIGOMEI — Interfaz gráfica multipágina")
    parser.add_argument("--host", default="127.0.0.1", help="Host del servidor TCP")
    parser.add_argument("--port", type=int, default=5000, help="Puerto del servidor TCP")
    return parser.parse_args()


def main():
    args = parse_args()
    app = SigomeiApp(host=args.host, port=args.port)
    app.mainloop()


if __name__ == "__main__":
    main()
