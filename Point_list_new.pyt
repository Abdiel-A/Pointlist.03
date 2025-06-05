import flet as ft
import calendar
import time
from datetime import date, datetime, time as dt_time

# ---------------------------
# CONFIGURACIÓN GLOBAL Y DATOS
# ---------------------------

# ————————————————
# Límite de uso (2 horas)
USAGE_LIMIT_SECONDS = 2 * 60 * 60
session_start_time = time.time()
def check_usage_limit():
    return (time.time() - session_start_time) > USAGE_LIMIT_SECONDS
# ————————————————

current_month_index = 2  # Empezamos en Marzo (índice 2)
current_year = 2025
month_names = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

current_filter = "Todos"

notes_data_all = [
    {"calificacion": "3.3", "asignatura": "Español",      "fecha": "2025-08-25", "timestamp": 1692921600},
    {"calificacion": "4.0", "asignatura": "Valores",      "fecha": "2025-08-26", "timestamp": 1693008000},
    {"calificacion": "4.5", "asignatura": "Matemáticas",  "fecha": "2025-08-27", "timestamp": 1693094400},
    {"calificacion": "5.0", "asignatura": "Inglés",       "fecha": "2025-08-28", "timestamp": 1693180800},
    {"calificacion": "3.0", "asignatura": "Informática",  "fecha": "2025-08-29", "timestamp": 1693267200},
    {"calificacion": "4.0", "asignatura": "Español",      "fecha": "2025-08-30", "timestamp": 1693353600}
]

# Técnicas de estudio
techniques = [
    {"id": 1, "titulo": "Técnica Pomodoro", "descripcion": "Estudia 25 min + 5 min descanso.", "categoria": "Recientes", "favorita": False},
    {"id": 2, "titulo": "SMART",            "descripcion": "Objetivos Specific–Measurable…",      "categoria": "Recientes", "favorita": False},
    {"id": 3, "titulo": "Mapas mentales",   "descripcion": "Diagramas que conectan conceptos.",     "categoria": "Todos",     "favorita": False},
    {"id": 4, "titulo": "SQ3R",             "descripcion": "Survey–Question–Read–Recite–Review.",  "categoria": "Todos",     "favorita": False},
]

# Cronogramas en memoria
cronogram_events = []  # cada entrada: {id, technique_id, title, start:datetime, end:datetime}

current_user = {
    "name": "Juan Perez",
    "photo_url": "https://cdn-icons-png.flaticon.com/512/219/219983.png"
}

# ——— Nuevas listas globales ———
urgent_events = [
    {"title": "Entrega Parcial Física", "date": date(2025, 4, 15), "type": "tarea"},
    {"title": "Día del Maestro",        "date": date(2025, 5, 5),  "type": "feriado"},
    # … añade los que necesites
]

reminders = []

# ---------------------------
# UTILIDADES
# ---------------------------
def change_month(delta: int):
    global current_month_index, current_year
    m = current_month_index + delta
    if m > 11:
        m = 0; current_year += 1
    elif m < 0:
        m = 11; current_year -= 1
    current_month_index = m
    NavigationController.update_view("Calendario")


def build_popup_menu():
    return ft.PopupMenuButton(
        icon=ft.icons.MENU, icon_color=ft.colors.BLACK,
        items=[
            ft.PopupMenuItem(text="Inicio",    on_click=lambda e: NavigationController.update_view("Inicio")),
            ft.PopupMenuItem(text="Notas",     on_click=lambda e: NavigationController.update_view("Notas")),
            ft.PopupMenuItem(text="Calendario",on_click=lambda e: NavigationController.update_view("Calendario")),
            ft.PopupMenuItem(text="Técnicas",  on_click=lambda e: NavigationController.update_view("Tecnicas")),
            ft.PopupMenuItem(text="Clases",    on_click=lambda e: NavigationController.update_view("Clases")),
            ft.PopupMenuItem(text="Recuperar", on_click=lambda e: NavigationController.update_view("Recuperar")),
        ]
    )

# ---------------------------
# COMPONENTES COMUNES
# ---------------------------
class Carousel(ft.Control):
    def __init__(self, images: list, width: int, height: int, **kwargs):
        super().__init__(**kwargs)
        self.images = images; self.width = width; self.height = height
        self.current_page = 0; self.tabs_control = None
    def _get_control_name(self): return "container"
    def build(self):
        self.tabs_control = ft.Tabs(
            selected_index=self.current_page, divider_height=0,
            tabs=[ft.Tab(content=ft.Image(src=url, fit=ft.ImageFit.COVER, width=self.width, height=self.height))
                  for url in self.images]
        )
        indicators = [
            ft.Container(width=10, height=10,
                         bgcolor=ft.colors.BLUE if i==self.current_page else ft.colors.GREY,
                         border_radius=5, margin=ft.margin.all(4))
            for i in range(len(self.images))
        ]
        return ft.Stack([
            self.tabs_control,
            ft.Container(content=ft.IconButton(icon=ft.icons.ARROW_BACK, icon_color=ft.colors.WHITE, on_click=self.prev_page),
                         alignment=ft.alignment.center_left, padding=ft.padding.all(10)),
            ft.Container(content=ft.IconButton(icon=ft.icons.ARROW_FORWARD, icon_color=ft.colors.WHITE, on_click=self.next_page),
                         alignment=ft.alignment.center_right, padding=ft.padding.all(10)),
            ft.Container(content=ft.Row(controls=indicators, alignment=ft.MainAxisAlignment.CENTER),
                         alignment=ft.alignment.bottom_center, padding=ft.padding.only(bottom=10)),
        ])
    def prev_page(self,e):
        p=self.current_page-1 if self.current_page>0 else len(self.images)-1
        self.current_page=p; self.tabs_control.selected_index=p; self.update()
    def next_page(self,e):
        p=self.current_page+1 if self.current_page<len(self.images)-1 else 0
        self.current_page=p; self.tabs_control.selected_index=p; self.update()

class SubjectCard(ft.Control):
    def __init__(self, titulo, icon_url, descripcion, estado="Sin terminar", **kwargs):
        super().__init__(**kwargs)
        self.t, self.i, self.d, self.e = titulo, icon_url, descripcion, estado
        self.liked=False
    def _get_control_name(self): return "container"
    def toggle_like(self,e): self.liked=not self.liked; self.update()
    def build(self):
        ic = ft.icons.FAVORITE if self.liked else ft.icons.FAVORITE_BORDER
        size = 40 if self.liked else 30
        return ft.Container(
            width=250, bgcolor="white", border_radius=ft.border_radius.all(12), padding=ft.padding.all(20),
            on_click=lambda e: NavigationController.update_view("Clases"),
            content=ft.Column([
                ft.Row([
                    ft.Image(src=self.i, width=40, height=40),
                    ft.Container(expand=True),
                    ft.AnimatedSwitcher(
                        content=ft.Icon(ic, color="red", size=size),
                        duration=300
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=10, color="transparent"),
                ft.Text(self.t, size=20, weight=ft.FontWeight.BOLD, color="#2B2B2B"),
                ft.Text(self.d, size=14, color="#4B4B4B"),
                ft.Divider(height=10, color="transparent"),
                ft.Text(self.e, size=12, color="#9CA3AF", italic=True),
            ], spacing=5)
        )

class TechniqueCard(ft.Control):
    def __init__(self, tech, **kwargs):
        super().__init__(**kwargs)
        self.tech=tech
    def _get_control_name(self): return "container"
    def toggle_fav(self,e):
        self.tech["favorita"]=not self.tech["favorita"]; self.update()
    def add_to_schedule(self,e):
        dlg = ft.AlertDialog(
            title=ft.Text(f"Añadir cronograma: {self.tech['titulo']}"),
            content=ft.Column([
                ft.TextField(label="Título", value=self.tech["titulo"]),
                ft.Row([ft.Text("Inicio:"), ft.DatePicker(value=date.today()), ft.TimePicker(value=ft.Time(9,0))]),
                ft.Row([ft.Text("Fin:"),    ft.DatePicker(value=date.today()), ft.TimePicker(value=ft.Time(9,25))]),
            ], spacing=10),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.dialog.close()),
                ft.TextButton("Guardar",  on_click=lambda e,tc=self.tech: self._save_block(e,tc))
            ]
        )
        self.page.dialog=dlg; dlg.open=True; self.page.update()
    def _save_block(self,e,tech):
        c=self.page.dialog.content.controls
        title=c[0].value
        d1,t1=c[1].controls[1].value, c[1].controls[2].value
        d2,t2=c[2].controls[1].value, c[2].controls[2].value
        cronogram_events.append({
            "id": len(cronogram_events)+1,
            "technique_id": tech["id"],
            "title": title,
            "start": datetime.combine(d1,t1),
            "end":   datetime.combine(d2,t2)
        })
        self.page.dialog.open=False; self.page.update()
    def build(self):
        icon = ft.icons.FAVORITE if self.tech["favorita"] else ft.icons.FAVORITE_BORDER
        color= "red" if self.tech["favorita"] else "#CCC"
        return ft.Container(
            padding=ft.padding.all(12), bgcolor="#F0F8FF", border_radius=ft.border_radius.all(12),
            content=ft.Row([
                ft.Column([
                    ft.Text(self.tech["titulo"], size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(self.tech["descripcion"], size=14, color="#555")
                ], expand=True),
                ft.IconButton(icon=icon, icon_color=color, on_click=self.toggle_fav),
                ft.IconButton(icon=ft.icons.ADD, icon_color="#1E40AF", on_click=self.add_to_schedule)
            ], alignment=ft.MainAxisAlignment.START)
        )

def home_calendar_style_card(titulo, icon_url, descripcion, estado="Programado"):
    return ft.Container(
        width=250, bgcolor="white", border_radius=ft.border_radius.all(12), padding=ft.padding.all(20),
        content=ft.Column([
            ft.Row([ft.Image(src=icon_url,width=40,height=40), ft.Container(expand=True), ft.Icon(ft.icons.EVENT,color="red")],
                   alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=10, color="transparent"),
            ft.Text(titulo, size=20, weight=ft.FontWeight.BOLD, color="#2B2B2B"),
            ft.Text(descripcion, size=14, color="#4B4B4B"),
            ft.Divider(height=10, color="transparent"),
            ft.Text(estado, size=12, color="#9B88FF", italic=True)
        ], spacing=5)
    )

# ---------------------------
# BASE PAGE
# ---------------------------
class BasePage(ft.Control):
    def __init__(self, page: ft.Page = None, **kwargs):
        super().__init__(**kwargs)
        # Guardamos la referencia a la página para que los hijos la compartan
        self.page = page

    def _get_control_name(self):
        return "BasePage"


class LoginPage(BasePage):
    def __init__(self, page: ft.Page, **kwargs):
        super().__init__(**kwargs); self.page=page
    def build(self):
        name_field  = ft.TextField(label="Nombre de usuario")
        photo_field = ft.TextField(label="URL de tu foto")
        escala_field= ft.TextField(label="Escala (1–5)")
        def on_login(e):
            current_user["name"]=name_field.value
            current_user["photo_url"]=photo_field.value
            NavigationController.update_view("Inicio")
        return ft.Column([
            ft.Text("Iniciar Sesión", size=24, weight=ft.FontWeight.BOLD),
            name_field, photo_field, escala_field,
            ft.ElevatedButton("Entrar", on_click=on_login)
        ], expand=True, alignment=ft.MainAxisAlignment.CENTER,
           horizontal_alignment=ft.CrossAxisAlignment.CENTER)
# ---------------------------
# PÁGINAS DE LA APLICACIÓN
# ---------------------------

class HomePage(BasePage):
    def __init__(self, page: ft.Page, **kwargs):
        super().__init__(**kwargs)
        self.page = page

    def build(self):
        if check_usage_limit():
            return ft.Text("Has superado tu límite de uso. Vuelve mañana.", color="red", size=20)

        # ----------------------------
        # 1) Navbar (igual que antes)
        # ----------------------------
        navbar = ft.Container(
            bgcolor="white",
            padding=ft.padding.symmetric(horizontal=40, vertical=10),
            content=ft.Row(
                [
                    build_popup_menu(),
                    ft.Text("Point List", size=24, weight=ft.FontWeight.BOLD, color="#2B2B2B"),
                    ft.Container(expand=True),
                    ft.TextButton("Home", on_click=lambda e: NavigationController.update_view("Inicio")),
                    ft.TextButton("Calendario", on_click=lambda e: NavigationController.update_view("Calendario")),
                    ft.TextButton("Notas", on_click=lambda e: NavigationController.update_view("Notas")),
                    ft.TextButton("Clases", on_click=lambda e: NavigationController.update_view("Clases")),
                    ft.Container(expand=True),
                    ft.Row([
                        ft.Text(current_user["name"], color="#2B2B2B"),
                        ft.CircleAvatar(foreground_image_src=current_user["photo_url"], radius=15)
                    ], spacing=10)
                ],
                alignment=ft.MainAxisAlignment.CENTER
            )
        )

        # ----------------------------
        # 2) Hero (por ejemplo, una imagen fija o carrusel)
        # ----------------------------
        hero = ft.Container(
            width=self.page.width or 900,
            height=250,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            border_radius=ft.border_radius.only(top_left=20, top_right=20),
            content=ft.Stack([
                ft.Image(
                    src="/image.png",  # <-- asegúrate de que esté en assets_dir
                    fit=ft.ImageFit.COVER,
                    width=self.page.width or 900,
                    height=250,
                ),
                ft.Container(bgcolor=ft.colors.with_opacity(0.3, ft.colors.BLACK), expand=True),
                ft.Container(
                    alignment=ft.alignment.center,
                    content=ft.Text("¡Bienvenido a Point List!", size=32, weight=ft.FontWeight.BOLD, color="white")
                )
            ])
        )

        # ----------------------------
        # 3) Filtro / buscador (puedes dejarlo como antes)
        # ----------------------------
        filter_bar = ft.Container(
            bgcolor="white",
            padding=ft.padding.symmetric(horizontal=40, vertical=12),
            content=ft.Row(
                [
                    ft.Row([ft.Text("MASCOTA IA", weight=ft.FontWeight.BOLD), ft.Icon(ft.icons.ARROW_DROP_DOWN)]),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=16, vertical=8),
                        bgcolor="#A3C9A8",
                        border_radius=ft.border_radius.all(12),
                        content=ft.Text("Materias", color="white", weight=ft.FontWeight.BOLD)
                    ),
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=16, vertical=8),
                        bgcolor="#E0EFFF",
                        border_radius=ft.border_radius.all(12),
                        content=ft.Text("Técnicas de estudio", color="#3B5998"),
                        on_click=lambda e: NavigationController.update_view("Tecnicas")
                    ),
                    ft.Container(expand=True),
                    ft.TextField(
                        hint_text="Buscar asignación",
                        width=250,
                        prefix_icon=ft.icons.SEARCH,
                        border_radius=ft.border_radius.all(12),
                        bgcolor="#F0F4FF",
                        on_submit=lambda e: NavigationController.update_view("Notas", e.control.value)
                    )
                ],
                spacing=20,
                alignment=ft.MainAxisAlignment.CENTER
            )
        )

        # ------------------------------------------------------
        # 4) Ahora los 4 containers en 2 filas de 2 columnas,
        #    con un ancho mayor (por ejemplo 420 en lugar de 360)
        # ------------------------------------------------------
        def subj_card(t, ic, d):
            return ft.Card(
                elevation=2,
                content=ft.Container(
                    width=560,  # <- aquí agrandamos el ancho
                    padding=ft.padding.all(20),
                    bgcolor="white",
                    border_radius=ft.border_radius.all(16),
                    content=ft.Row(
                        [
                            ft.Image(src=ic, width=48, height=48),
                            ft.Container(width=16),  # margen horizontal entre icono y texto
                            ft.Column([
                                ft.Text(t, size=20, weight=ft.FontWeight.BOLD, color="#2B2B2B"),
                                ft.Text(d, size=16, color="#6B7280", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)
                            ], expand=True)
                        ],
                        spacing=10
                    )
                )
            )

        # Creamos dos filas, cada una con dos tarjetas:
        row1 = ft.Row(
            [
                subj_card("Informática",
                         "https://cdn-icons-png.flaticon.com/512/545/545680.png",
                         "Lorem ipsum dolor sit amet."),
                subj_card("Valores",
                         "https://cdn-icons-png.flaticon.com/512/1904/1904425.png",
                         "Lorem ipsum dolor sit amet.")
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.CENTER
        )

        row2 = ft.Row(
            [
                subj_card("Inglés",
                         "https://cdn-icons-png.flaticon.com/512/942/942748.png",
                         "Lorem ipsum dolor sit amet."),
                subj_card("Matemáticas",
                         "https://cdn-icons-png.flaticon.com/512/414/414975.png",
                         "Lorem ipsum dolor sit amet.")
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.CENTER
        )

        # ------------------------------------------------------
        # 5) Finalmente devolvemos todo en una sola columna
        # ------------------------------------------------------
        return ft.Column(
            [
                navbar,
                hero,
                filter_bar,
                ft.Divider(height=1, color="#E5E7EB"),
                ft.Container(height=20),  # espacio en blanco
                row1,
                ft.Container(height=20),  # separación vertical entre las filas
                row2
            ],
            spacing=0,
            expand=True
        )
    
    # ---------------------------
# Tarjeta para Técnica de Estudio
# ---------------------------
class MethodCard(ft.Control):
    def __init__(self, key: str, titulo: str, icon_url: str, descripcion: str, **kwargs):
        super().__init__(**kwargs)
        self.key = key
        self.titulo = titulo
        self.icon_url = icon_url
        self.descripcion = descripcion
        self.fav = False

    def _get_control_name(self):
        return "container"

    def toggle_fav(self, e):
        self.fav = not self.fav
        self.update()

    def build(self):
        heart_icon = ft.icons.FAVORITE if self.fav else ft.icons.FAVORITE_BORDER
        # Aumentamos ancho, altura, tamaño de texto e iconos
        return ft.Container(
            width=400,
            padding=ft.padding.symmetric(horizontal=32, vertical=24),
            bgcolor="#FFFFFF",
            border_radius=ft.border_radius.all(16),
            shadow=ft.BoxShadow(blur_radius=8, offset=ft.Offset(0,4), color="#00000015"),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=16,
                        controls=[
                            ft.Image(src=self.icon_url, width=56, height=56),
                            ft.Column(
                                spacing=8,
                                controls=[
                                    ft.Text(self.titulo, size=22, weight=ft.FontWeight.BOLD),
                                    ft.Text(
                                        self.descripcion,
                                        size=16,
                                        color="#4B5563",
                                        max_lines=4,
                                        overflow=ft.TextOverflow.ELLIPSIS
                                    )
                                ]
                            )
                        ]
                    ),
                    ft.IconButton(
                        icon=heart_icon,
                        icon_color="#EF4444",
                        icon_size= 30,
                        on_click=self.toggle_fav
                    )
                ]
            )
        )

# ---------------------------
# Página de Métodos de Estudio
# ---------------------------
class StudyMethodsPage(BasePage):
    def __init__(self, page: ft.Page, **kwargs):
        super().__init__(**kwargs)
        self.page = page
        self.current_filter = "Recientes"
        self.search_query = ""

    def _get_control_name(self):
        return "StudyMethodsPage"

    def set_filter(self, f: str):
        self.current_filter = f
        self.page.update()

    def on_search(self, e):
        self.search_query = e.control.value.strip().lower()
        self.page.update()

    def build(self):
        # ——— Banner estático arriba ———
        banner = ft.Container(
            height=200,
            expand=True,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Stack([
                ft.Image(
                    src="https://images.pexels.com/photos/4145247/pexels-photo-4145247.jpeg",
                    fit=ft.ImageFit.COVER,
                    width=self.page.width or 800,
                    height=200
                ),
                ft.Container(
                    expand=True,
                    bgcolor=ft.colors.with_opacity(0.3, ft.colors.BLACK)
                ),
                ft.Container(
                    alignment=ft.alignment.center,
                    content=ft.Text(
                        "Aprende mejor,\nestudia más fácil",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        color="white",
                        text_align=ft.TextAlign.CENTER
                    )
                )
            ])
        )

        # ——— Navbar pequeño ———
        navbar = ft.Container(
            bgcolor="white",
            padding=ft.padding.symmetric(horizontal=40, vertical=8),
            content=ft.Row([
                build_popup_menu(),
                ft.Container(expand=True),
                ft.Text(current_user["name"], color="#2B2B2B"),
                ft.CircleAvatar(foreground_image_src=current_user["photo_url"], radius=15),
            ], alignment=ft.MainAxisAlignment.CENTER)
        )

        # ——— Título + buscador ———
        title = ft.Text("Técnicas de estudio", size=24, weight=ft.FontWeight.BOLD)
        search = ft.TextField(
            hint_text="Buscar técnica",
            prefix_icon=ft.icons.SEARCH,
            width=250,
            on_change=self.on_search
        )
        title_row = ft.Row([title, ft.Container(expand=True), search],
                           alignment=ft.MainAxisAlignment.CENTER)

        # ——— Preparo las tarjetas filtradas ———
        def make_cards(categoria):
            data = [
                t for t in techniques
                if (categoria == "Todos" or t["categoria"] == categoria)
                   and (not self.search_query or self.search_query in t["titulo"].lower())
            ]
            return [
                MethodCard(
                    key=str(t["id"]),
                    titulo=t["titulo"],
                    icon_url=t.get("icon_url", ""),
                    descripcion=t["descripcion"]
                )
                for t in data
            ]

        recientes_cards = make_cards("Recientes")
        todos_cards     = make_cards("Todos")

        # ——— Secciones con scroll horizontal ———
        recientes_section = ft.Column([
            ft.Text("Recientes", weight=ft.FontWeight.BOLD),
            ft.Container(
                height=140,
                scroll=ft.ScrollMode.HORIZONTAL,
                content=ft.Row(recientes_cards, spacing=10)
            )
        ], spacing=8)

        todos_section = ft.Column([
            ft.Text("Todos", weight=ft.FontWeight.BOLD),
            ft.Container(
                height=140,
                scroll=ft.ScrollMode.HORIZONTAL,
                content=ft.Row(todos_cards, spacing=10)
            )
        ], spacing=8)

        # ——— Panel derecho: Mis favoritos ———
                # ——— Panel derecho: Mis favoritos ———
        favs = [c for c in recientes_cards + todos_cards if getattr(c, "fav", False)]
        # 1) Preparamos la lista de controles según haya o no favoritos
        fav_controls = [
            ft.Row([
                ft.Icon(ft.icons.FAVORITE, color="#EF4444"),
                ft.Text("Mis favoritos", weight=ft.FontWeight.BOLD)
            ])
        ]
        if favs:
            # añadimos cada tarjeta favorita
            fav_controls += [c.build() for c in favs]
        else:
            # o un mensaje de “sin favoritos”
            fav_controls.append(ft.Text("— Sin favoritos —", color="#6B7280"))

        # 2) Luego la usamos con splat sin or en medio
        right = ft.Column(
            controls=fav_controls,
            spacing=12,
            width=200
        )


        # ——— Armo la fila principal ———
        content = ft.Row(
            controls=[
                ft.Column([recientes_section, todos_section], expand=True, spacing=20),
                right
            ],
            expand=True,
            spacing=20
        )

        # ——— Retorno final ———
        return ft.Column([
            navbar,
            banner,
            title_row,
            ft.Divider(height=1, color="#E5E7EB"),
            content
        ], spacing=20, expand=True)



class NotesPage(BasePage):
    def __init__(self, page: ft.Page, **kwargs):
        super().__init__(**kwargs); self.page=page
        self.current_filter=current_filter; self.search_query=""
    def _get_control_name(self): return "NotesPage"

    def set_filter(self, opt):
        global current_filter; current_filter=opt; self.current_filter=opt
        NavigationController.update_view("Notas")

    def on_search_change(self,e):
        self.search_query=e.control.value.strip()
        NavigationController.update_view("Notas")

    def load_filtered_notes(self):
        if self.current_filter=="Recientes":
            notes=sorted(notes_data_all,key=lambda n:n["timestamp"],reverse=True)
        elif self.current_filter=="Viejas":
            notes=sorted(notes_data_all,key=lambda n:n["timestamp"])
        else:
            notes=notes_data_all.copy()
        if self.search_query:
            notes=[n for n in notes if self.search_query.lower() in n["asignatura"].lower()]
        return notes

    def color_for(self,avg):
        if avg>=4.7: return "#2F855A"
        if avg>=4.3: return "#68D391"
        if avg>=4.0: return "#C6F6D5"
        if avg>=3.7: return "#FAF089"
        if avg>=3.4: return "#F6E05E"
        if avg>=3.0: return "#D69E2E"
        if avg>=2.7: return "#FEB2B2"
        if avg>=2.4: return "#FC8181"
        return "#C53030"

    def get_average_by_subject(self):
        subj_data={}
        for n in notes_data_all:
            s=n["asignatura"]; g=float(n["calificacion"])
            subj_data.setdefault(s,[]).append(g)
        return {s:sum(gs)/len(gs) for s,gs in subj_data.items()}

    def build_graph(self):
        averages=self.get_average_by_subject()
        bars=[]
        for subj,avg in averages.items():
            bars.append(ft.Row([
                ft.Text(subj,width=80,size=12),
                ft.Container(width=avg*30,height=16,bgcolor=self.color_for(avg),border_radius=ft.border_radius.all(4)),
                ft.Text(f"{avg:.2f}",size=12)
            ],spacing=6))
        return ft.Column([ft.Text("Desempeño por Asignatura",weight=ft.FontWeight.BOLD)]+bars,spacing=8)

    def build(self):
        if check_usage_limit():
            return ft.Text("Has superado tu límite de uso. Vuelve mañana.",color="red",size=20)

        # Navbar
        navbar = ft.Container(
                bgcolor="white",
                padding=ft.padding.only(left=20, right=20, top=10, bottom=10),
                content=ft.Row(
                    controls=[
                        build_popup_menu(),  # ← Ícono de menú
                        ft.Text("Point List", size=22, weight=ft.FontWeight.BOLD, color="#2B2B2B"),
                        ft.Container(expand=True),
                        ft.TextButton("Home", on_click=lambda e: NavigationController.update_view("Inicio")),
                        ft.TextButton("Calendario", on_click=lambda e: NavigationController.update_view("Calendario")),
                        ft.TextButton("Notas", on_click=lambda e: NavigationController.update_view("Notas")),
                        ft.Container(expand=True),
                        ft.Row([
                            ft.Text(current_user["name"], color="#2B2B2B"),
                            ft.CircleAvatar(foreground_image_src=current_user["photo_url"], radius=15)
                        ], spacing=5),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                )
        )


        # — Notificaciones por calif < 3.0 —
        alertas=[n for n in notes_data_all if float(n["calificacion"])<3.0]
        notifs=[ft.Text(f"⚠️ {n['asignatura']}: {n['calificacion']} ({n['fecha']})",color="red",size=14)
                for n in alertas]

        # Filtros
        chips=ft.Row([
            ft.Container(padding=ft.padding.symmetric(horizontal=12,vertical=6),border_radius=ft.border_radius.all(16),
                         bgcolor="#B4C8D4" if self.current_filter=="Todos" else "white",
                         content=ft.Text("Todos"), on_click=lambda e:self.set_filter("Todos")),
            ft.Container(padding=ft.padding.symmetric(horizontal=12,vertical=6),border_radius=ft.border_radius.all(16),
                         bgcolor="#BEE3F8" if self.current_filter=="Recientes" else "white",
                         content=ft.Text("Recientes"), on_click=lambda e:self.set_filter("Recientes")),
            ft.Container(padding=ft.padding.symmetric(horizontal=12,vertical=6),border_radius=ft.border_radius.all(16),
                         bgcolor="#BEE3F8" if self.current_filter=="Viejas" else "white",
                         content=ft.Text("Viejas"), on_click=lambda e:self.set_filter("Viejas")),
        ],spacing=10)

        # Buscador
        search_field=ft.TextField(hint_text="Buscar asignatura",prefix_icon=ft.icons.SEARCH,
                                  width=250,value=self.search_query,on_change=self.on_search_change)

        # Listado de notas
        filtered_notes=self.load_filtered_notes()
        def nota_card(n):
            return ft.Container(
                bgcolor="white",border_radius=ft.border_radius.all(8),padding=ft.padding.all(12),
                on_click=lambda e,subj=n["asignatura"]:NavigationController.update_view("DetalleAsignatura",subj),
                content=ft.Row([ft.Text(n["calificacion"],size=24,weight=ft.FontWeight.BOLD,width=50),
                                ft.Column([ft.Text(n["asignatura"],size=16,weight=ft.FontWeight.BOLD),
                                           ft.Text(n["fecha"],size=12,color="#6B7280")])],spacing=20)
            )
        notes_list=ft.ListView(expand=True,spacing=8,controls=[nota_card(n) for n in filtered_notes])

        # Mini calendario
                # — Mini calendario —
        today = date.today()
        cal = calendar.Calendar(firstweekday=6)
        month_days = cal.monthdayscalendar(current_year, current_month_index + 1)
        mini_rows = []
        for week in month_days:
            cells = []
            for day in week:
                day_str = str(day) if day else ""
                border_color = (
                    ft.colors.RED
                    if day == today.day and (current_month_index+1)==today.month and current_year==today.year
                    else ft.colors.GREY
                )
                cells.append(
                    ft.Container(
                        width=30, height=30,
                        border=ft.border.all(1, border_color),
                        border_radius=ft.border_radius.all(4),
                        content=ft.Text(day_str, size=12, text_align="center") if day else None,
                        margin=ft.margin.all(2),
                        on_click=lambda e, d=day: self.set_filter_date(d)
                    )
                )
            mini_rows.append(
                ft.Row(controls=cells, spacing=2, alignment=ft.MainAxisAlignment.CENTER)
            )
        mini_header = ft.Row([
                ft.IconButton(icon=ft.icons.ARROW_BACK, icon_size=16, on_click=lambda e: change_month(-1)),
                ft.Text(f"{month_names[current_month_index]} {current_year}", size=12, weight=ft.FontWeight.BOLD, expand=True, text_align="center"),
                ft.IconButton(icon=ft.icons.ARROW_FORWARD, icon_size=16, on_click=lambda e: change_month(1)),
            ], alignment=ft.MainAxisAlignment.CENTER)
        mini_calendar = ft.Column([mini_header] + mini_rows, spacing=2, alignment=ft.MainAxisAlignment.CENTER)

        # — Estadísticas breves —
        perf = {}
        for n in filtered_notes:
            try:
                g = float(n["calificacion"])
            except:
                continue
            perf.setdefault(n["asignatura"], []).append(g)
        bars = []
        for subj, grades in perf.items():
            avg = sum(grades) / len(grades)
            bars.append(
                ft.Row([
                    ft.Text(subj, width=80, size=12),
                    ft.Container(width=avg*20, height=10, bgcolor=self.color_for(avg), border_radius=ft.border_radius.all(4)),
                    ft.Text(f"{avg:.1f}", size=12)
                ], spacing=6)
            )
        stats_panel = ft.Column(
            controls=[ft.Text("Desempeño", size=14, weight=ft.FontWeight.BOLD)] + bars,
            spacing=8
        )

        # ————— Right Panel con ancho fijo y margen —————
                # ————— Right Panel con ancho fijo y margen —————
        right_panel = ft.Container(
            width=240,
            margin=ft.margin.only(right=20),
            content=ft.Column(
                controls=[
                    ft.Container(height=200, content=mini_calendar),  # antes usaba min_height
                    ft.Divider(height=10),
                    stats_panel
                ],
                spacing=12
            )
        )


        # ————— Contenido principal: notas + panel derecho —————
        main_content = ft.Row(
            controls=[
                ft.Column(
                    controls=[chips, search_field, notes_list],
                    expand=True,
                    spacing=10
                ),
                right_panel
            ],
            spacing=20,
            expand=True
        )

        # Encabezado y envoltorio
        heading = ft.Container(
            content=ft.Text("Sección de Notas", size=28, weight=ft.FontWeight.BOLD),
            margin=ft.margin.only(left=30, right=30, top=20, bottom=10)
        )
        notes_wrapper = ft.Container(
            bgcolor="#F9FAFB",
            padding=ft.padding.all(20),
            border_radius=ft.border_radius.all(10),
            margin=ft.margin.symmetric(horizontal=30, vertical=10),
            content=main_content
        )

        return ft.Column(
            controls=[
                navbar,
                *notifs,
                ft.Divider(height=1, color="#E5E7EB"),
                heading,
                notes_wrapper,
                ft.Divider(height=10),
                self.build_graph()
            ],
            spacing=0,
            expand=True
        )


    def set_filter_date(self,day:int):
        date_str=f"{current_year}-{current_month_index+1:02d}-{day:02d}"
        filtered=[n for n in notes_data_all if n["fecha"]==date_str]
        if filtered:
            dlg=ft.AlertDialog(
                title=ft.Text(f"Notas del día {date_str}"),
                content=ft.Column([ft.Text(f"{n['asignatura']}: {n['calificacion']}") for n in filtered]),
                actions=[ft.TextButton("Cerrar",on_click=lambda e:self.page.dialog.close())]
            )
            self.page.dialog=dlg; dlg.open=True; self.page.update()

class SubjectDetailPage(BasePage):
    def __init__(self, page: ft.Page, subject: str, **kwargs):
        super().__init__(**kwargs); self.page=page; self.subject=subject
    def _get_control_name(self): return "SubjectDetailPage"
    def build(self):
        navbar=ft.Container(bgcolor="white",padding=ft.padding.symmetric(horizontal=30,vertical=10),
            content=ft.Row([ft.IconButton(icon=ft.icons.ARROW_BACK,on_click=lambda e:NavigationController.update_view("Notas")),
                            ft.Text(f"Detalle: {self.subject}",size=22,weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),ft.CircleAvatar(foreground_image_src=current_user["photo_url"],radius=15)],
                           alignment=ft.MainAxisAlignment.CENTER))
        entries=[n for n in notes_data_all if n["asignatura"]==self.subject]
        cards=[ft.Container(bgcolor="white",border_radius=ft.border_radius.all(8),padding=ft.padding.all(12),
                            content=ft.Column([ft.Text(f"Calificación: {e['calificacion']}",size=16,weight=ft.FontWeight.BOLD),
                                              ft.Text(f"Fecha: {e['fecha']}",size=14,color="#6B7280")],spacing=6))
               for e in entries]
        return ft.Column([navbar,ft.Divider(height=1)] + cards,spacing=10,expand=True)

# -------------------------
# LISTA GLOBAL DE TÉCNICAS
# -------------------------
techniques = [
    {
        "id": 1,
        "titulo": "Técnica Pomodoro",
        "descripcion": "Estudia en bloques de 25 minutos seguidos de 5 minutos de descanso.",
        "categoria": "Recientes",
        "favorita": False,
        "icon_url": "https://cdn-icons-png.flaticon.com/512/4213/4213492.png"
    },
    {
        "id": 2,
        "titulo": "SMART",
        "descripcion": "La técnica SMART es una metodología para establecer objetivos claros y alcanzables.",
        "categoria": "Recientes",
        "favorita": False,
        "icon_url": "https://cdn-icons-png.flaticon.com/512/2524/2524506.png"
    },
    {
        "id": 3,
        "titulo": "Mapas mentales",
        "descripcion": "Esta técnica visual implica crear diagramas que representan conceptos y sus conexiones.",
        "categoria": "Todos",
        "favorita": False,
        "icon_url": "https://cdn-icons-png.flaticon.com/512/2099/2099072.png"
    },
    {
        "id": 4,
        "titulo": "Método SQ3R",
        "descripcion": "Survey–Question–Read–Recite–Review: un método de lectura para mejorar retención.",
        "categoria": "Todos",
        "favorita": False,
        "icon_url": "https://cdn-icons-png.flaticon.com/512/3565/3565517.png"
    },
]


class StudyMethodsPage(BasePage):
    def __init__(self, page: ft.Page, techniques_list: list[dict], **kwargs):
        super().__init__(**kwargs)
        self.page = page
        self.techniques = techniques_list
        self.search_query = ""

    def toggle_fav(self, tech_id: int):
        """
        Invierte el estado 'favorita' de la técnica con id = tech_id
        y reconstruye la vista de Métodos de Estudio.
        """
        for t in self.techniques:
            if t["id"] == tech_id:
                t["favorita"] = not t["favorita"]
                break
        NavigationController.update_view("Metodos")

    def on_search(self, e):
        self.search_query = e.control.value.strip().lower()
        NavigationController.update_view("Metodos")

    def build(self):
        # ————— 1) BANNER CON IMAGEN DE FONDO Y OVERLAY —————
        banner = ft.Container(
            width=self.page.width or 800,
            height=180,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            border_radius=ft.border_radius.all(12),
            content=ft.Stack(
                controls=[
                    # Imagen de fondo
                    ft.Image(
                        src="banner_metodos.jpg",  # Debe estar en assets/
                        fit=ft.ImageFit.COVER,
                        width=self.page.width or 800,
                        height=180,
                    ),
                    # Overlay semitransparente
                    ft.Container(
                        expand=True,
                        bgcolor=ft.colors.with_opacity(0.3, ft.colors.BLACK),
                    ),
                    # Texto centrado
                    ft.Container(
                        alignment=ft.alignment.center,
                        content=ft.Text(
                            "Aprende mejor,\nestudia más fácil",
                            size=32,
                            weight=ft.FontWeight.BOLD,
                            color="white",
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ),
                ]
            ),
        )

        # ————— 2) ENCABEZADO CON MENÚ, TÍTULO “Técnicas de estudio” + BUSCADOR —————
        menu_button = build_popup_menu()  # Aquí insertamos el menú hamburguesa

        title = ft.Text("Técnicas de estudio", size=24, weight=ft.FontWeight.BOLD, color="#2B2B2B")
        search = ft.TextField(
            hint_text="Buscar técnica",
            prefix_icon=ft.icons.SEARCH,
            width=300,
            on_change=self.on_search,
            border_radius=ft.border_radius.all(20),
            border_color="#D1D5DB",
            bgcolor="#F9FAFB",
            on_focus=lambda e: setattr(e.control, "border_color", "#4A90E2"),
            on_blur=lambda e: setattr(e.control, "border_color", "#D1D5DB"),
        )
        header_bar = ft.Container(
            bgcolor="white",
            padding=ft.padding.symmetric(horizontal=24, vertical=12),
            border_radius=ft.border_radius.all(8),
            shadow=ft.BoxShadow(blur_radius=2, offset=ft.Offset(0, 1), color="#0000000F"),
            margin=ft.margin.only(top=-36, left=30, right=30),  # Sobresale sobre el banner
            content=ft.Row(
                controls=[
                    # 1) Botón de menú a la izquierda
                    menu_button,
                    ft.Container(width=12),
                    # 2) Título
                    title,
                    ft.Container(expand=True),
                    # 3) Campo de búsqueda
                    search
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=16,
            ),
        )

        # ————— 3) TARJETAS DE TÉCNICA CON “hover” Y ANIMATED SWITCHER EN EL CORAZÓN —————
        def make_card(t: dict):
            desc = t["descripcion"]
            if len(desc) > 60:
                desc = desc[:57].rstrip() + "..."

            heart_icon = ft.icons.FAVORITE if t.get("favorita", False) else ft.icons.FAVORITE_BORDER
            heart_color = "#EF4444" if t.get("favorita", False) else "#9CA3AF"

            icon_control = (
                ft.Image(src=t["icon_url"], width=36, height=36)
                if t.get("icon_url")
                else ft.Icon(ft.icons.LIGHTBULB_OUTLINE, size=36, color="#BBBBBB")
            )

            card = ft.Container(
                width=360,
                bgcolor="#FAFAFA",  # Gris muy claro
                border_radius=ft.border_radius.all(12),
                padding=ft.padding.all(18),
                shadow=ft.BoxShadow(blur_radius=6, offset=ft.Offset(0, 3), color="#0000001A"),
                margin=ft.margin.all(10),
                content=ft.Column(
                    controls=[
                        # Icono y título
                        ft.Row(
                            controls=[
                                icon_control,
                                ft.Container(width=14),
                                ft.Text(
                                    t["titulo"],
                                    size=19,
                                    weight=ft.FontWeight.BOLD,
                                    color="#2B2B2B",
                                    expand=True,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        ft.Divider(height=10, color="transparent"),
                        # Descripción en cursiva y gris medio
                        ft.Text(
                            desc,
                            size=14,
                            color="#6B7280",
                            italic=True,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Divider(height=14, color="transparent"),
                        # Corazón para marcar favorito
                        ft.Row(
                            controls=[
                                ft.Container(expand=True),
                                ft.AnimatedSwitcher(
                                    transition=ft.AnimatedSwitcherTransition.FADE,
                                    duration=200,
                                    content=ft.IconButton(
                                        icon=heart_icon,
                                        icon_color=heart_color,
                                        icon_size=26,
                                        padding=ft.padding.all(0),
                                        on_click=lambda e, tid=t["id"]: self.toggle_fav(tid),
                                    ),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ],
                    spacing=6,
                ),
            )

            # Efecto hover en la sombra
            card.mouse_enter = lambda e: setattr(card, "shadow", ft.BoxShadow(blur_radius=12, offset=ft.Offset(0, 5), color="#00000022"))
            card.mouse_leave = lambda e: setattr(card, "shadow", ft.BoxShadow(blur_radius=6, offset=ft.Offset(0, 3), color="#0000001A"))
            return card

        # ————— 4) FILTRAR LAS TÉCNICAS POR CATEGORÍA Y BÚSQUEDA —————
        recientes = [
            t for t in self.techniques
            if t["categoria"] == "Recientes"
            and (not self.search_query or self.search_query in t["titulo"].lower())
        ]
        todos = [
            t for t in self.techniques
            if t["categoria"] == "Todos"
            and (not self.search_query or self.search_query in t["titulo"].lower())
        ]

        recientes_cards = [make_card(t) for t in recientes]
        todos_cards     = [make_card(t) for t in todos]

        recientes_section = ft.Column(
            controls=[
                ft.Text("Recientes", size=20, weight=ft.FontWeight.BOLD, color="#2B2B2B"),
                ft.Row(recientes_cards, spacing=40, alignment=ft.MainAxisAlignment.CENTER),
            ],
            spacing=16,
        )

        todos_section = ft.Column(
            controls=[
                ft.Text("Todos", size=20, weight=ft.FontWeight.BOLD, color="#2B2B2B"),
                ft.Row(todos_cards, spacing=40, alignment=ft.MainAxisAlignment.CENTER),
            ],
            spacing=16,
        )

        # ————— 5) PANEL DERECHO: “Mis favoritos” DETALLADO Y SCROLLABLE —————
        fav_title = ft.Row(
            controls=[
                ft.Icon(ft.icons.FAVORITE, color="#EF4444", size=24),
                ft.Container(width=8),
                ft.Text(
                    f"Mis favoritos ({len([t for t in self.techniques if t['favorita']])})",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color="#2B2B2B",
                    expand=True,
                ),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.START,
        )
        fav_divider = ft.Container(
            height=2,
            bgcolor="#EF4444",
            margin=ft.margin.symmetric(horizontal=4, vertical=4),
        )

        favoritos = [t for t in self.techniques if t.get("favorita", False)]
        fav_list_controls = []
        if favoritos:
            for t in favoritos:
                fav_list_controls.append(
                    ft.Card(
                        elevation=1,
                        content=ft.Container(
                            bgcolor="#E6F4EA",
                            border_radius=ft.border_radius.all(8),
                            padding=ft.padding.symmetric(horizontal=12, vertical=6),
                            content=ft.Row(
                                controls=[
                                    ft.Image(src=t["icon_url"], width=20, height=20),
                                    ft.Container(width=6),
                                    ft.Text(t["titulo"], size=15, color="#0F5132"),
                                    ft.Container(expand=True),
                                    ft.IconButton(
                                        icon=ft.icons.CLOSE,
                                        icon_color="#9B2A2A",
                                        icon_size=18,
                                        padding=ft.padding.all(0),
                                        on_click=lambda e, tid=t["id"]: self.toggle_fav(tid),
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=6,
                            ),
                        ),
                    )
                )
        else:
            fav_list_controls.append(
                ft.Container(
                    margin=ft.margin.only(top=12),
                    content=ft.Text("— Sin favoritos —", size=16, color="#6B7280", italic=True),
                )
            )

        fav_list = ft.ListView(
            expand=True,
            spacing=8,
            controls=fav_list_controls
        )

        right_panel = ft.Column(
            controls=[fav_title, fav_divider, fav_list],
            spacing=8,
            width=260,  # un poco más ancho para los iconos y texto
        )

        # ————— 6) DISEÑO RESPONSIVO: PANEL DERECHO DEBAJO SI ANCHO < 1024 —————
        if self.page.width and self.page.width < 1024:
            # Apilar en columna para pantallas estrechas
            main_content = ft.Column(
                controls=[
                    recientes_section,
                    ft.Container(height=24),
                    todos_section,
                    ft.Container(height=24),
                    right_panel
                ],
                spacing=24,
                expand=True,
            )
        else:
            # Disposición en fila normal
            left_column = ft.Column(
                controls=[recientes_section, todos_section],
                spacing=24,
                expand=True,
            )
            main_content = ft.Row(
                controls=[left_column, right_panel],
                spacing=48,
                expand=True,
            )

        # ————— 7) COMPONER Y DEVOLVER TODO —————
        return ft.Column(
            controls=[
                banner,
                header_bar,
                ft.Container(height=24),
                main_content,
            ],
            spacing=0,
            expand=True,
        )



        # ————— Generar todas las tarjetas —————
        cards = []
        for idx, m in enumerate(self.methods):
            # buscamos 'key', si no existe usamos 'title' o un fallback con el índice
            key = m.get("key") or m.get("title") or f"method_{idx}"
            # buscamos título bajo 'titulo' o 'title'
            title = m.get("titulo") or m.get("title", "Sin título")
            cards.append(MethodCard(
                key=key,
                titulo=title,
                icon_url=m.get("icon", ""),
                descripcion=m.get("desc", "")
            ))


        # ————— PANEL IZQUIERDO: 2x2 tarjetas —————
        # Solo tomamos hasta 4 técnicas
        left_rows = []
        for i in range(0, min(4, len(cards)), 2):
            row_cards = cards[i:i+2]
            left_rows.append(
                ft.Row(
                    controls=[c.build() for c in row_cards],
                    spacing=20
                )
            )
        left_panel = ft.Column(
            controls=left_rows,
            spacing=20,
            expand=True
        )

        # ————— PANEL DERECHO: lista vertical de favoritos —————
        favs = [c for c in cards if c.fav]
        fav_controls = [
            ft.Text("❤️ Mis favoritos", size=16, weight=ft.FontWeight.BOLD)
        ]
        if favs:
            # mostramos cada favorito en vertical
            fav_controls += [c.build() for c in favs]
        else:
            fav_controls.append(
                ft.Text("— Sin favoritos —", color="#6B7280")
            )
        right_panel = ft.Column(
            controls=fav_controls,
            spacing=12,
            width=200
        )

        # ————— ENSAMBLAR fila principal —————
        content_row = ft.Row(
            controls=[
                left_panel,
                right_panel
            ],
            spacing=40,
            expand=True
        )

        # ————— RETORNO FINAL —————
        return ft.Column(
            expand=True,
            spacing=20,
            controls=[
                hero,           # tu banner superior
                filter_row,     # la fila de filtros + buscador
                content_row     # aquí el nuevo layout
            ]
        )

        return ft.Column([navbar, content], expand=True)

    def _set_tab(self, tab):
        self.current_tab = tab
        NavigationController.update_view("Metodos")

    def _on_search(self, e):
        self.search_query = e.control.value
        NavigationController.update_view("Metodos")

    def _toggle_fav(self, title):
        if title in self.favorites:
            self.favorites.remove(title)
        else:
            self.favorites.add(title)
        self.page.update()

    def _open_cronogram_dialog(self, method):
        dlg = ft.AlertDialog(
            title=ft.Text(f"Cronograma: {method['title']}"),
            content=ft.Text("Aquí podrás definir tu plan…"),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: setattr(dlg, "open", False))]
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    cronogram_events = [
                {
                    "id": 1,
                    "technique_id": None,
                    "title": "Relajo",
                    "start": datetime(2025, 8, 8, 10, 0),
                    "end": datetime(2025, 8, 8, 11, 0),
                    "completed": False
                },]


class CalendarPage(BasePage):
    def __init__(self, page: ft.Page, **kwargs):
        super().__init__(**kwargs)
        self.page = page

        # ------ Campos para el formulario de "Añadir Evento" ------
        self.new_event_title       = ft.TextField(label="Título del evento", width=200)
        self.new_event_date        = ft.DatePicker(value=date.today())
        self.new_event_start_time  = ft.TimePicker(value=dt_time(hour=9, minute=0))
        self.new_event_end_time    = ft.TimePicker(value=dt_time(hour=10, minute=0))
        self.new_event_type        = ft.Dropdown(
            label="Tipo de evento",
            width=200,
            value="General",
            options=[
                ft.dropdown.Option("Examen"),
                ft.dropdown.Option("Entrega"),
                ft.dropdown.Option("General")
            ]
        )
        self.new_event_description = ft.TextField(
            label="Descripción",
            width=200,
            multiline=True,
            max_lines=3,
            hint_text="Descripción opcional..."
        )

        # Para el diálogo de “Eventos del día”
        self.selected_day = None

    # ——— Método que faltaba: posiciona la vista en el mes/año de hoy ———
    def _go_to_today(self):
        global current_month_index, current_year
        hoy = date.today()
        current_month_index = hoy.month - 1
        current_year = hoy.year
        NavigationController.update_view("Calendario")

    # ——— Marcar/desmarcar un evento como completado ———
    def _toggle_completed(self, ev, new_value):
        ev["completed"] = new_value
        self.page.update()

    # ——— Eliminar un evento del listado ———
    def _delete_event(self, ev_to_delete):
        global cronogram_events
        cronogram_events = [
            ev for ev in cronogram_events
            if ev["id"] != ev_to_delete["id"]
        ]
        self.page.update()

    # ——— Abrir diálogo que muestra todos los eventos de un día dado ———
    def _open_day_dialog(self, day: int):
        self.selected_day = day
        eventos_dia = [
            ev for ev in cronogram_events
            if ev["start"].date() == date(current_year, current_month_index + 1, day)
        ]

        controles = []
        if eventos_dia:
            for ev in eventos_dia:
                hora_str = ev["start"].strftime("%H:%M")
                cb = ft.Checkbox(
                    label=f"{hora_str} – {ev['title']}",
                    value=ev.get("completed", False),
                    on_change=lambda e, ev=ev: self._toggle_completed(ev, e.control.value),
                )
                controles.append(cb)
        else:
            controles.append(ft.Text("No hay eventos para este día.", italic=True, color="#6B7280"))

        btn_nuevo = ft.ElevatedButton(
            text="Añadir nuevo evento",
            on_click=lambda e: self._open_add_in_day_dialog()
        )

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                f"Eventos para {current_year}-{current_month_index+1:02d}-{day:02d}",
                weight=ft.FontWeight.BOLD
            ),
            content=ft.Column(
                controls=controles + [ft.Divider(height=10), btn_nuevo],
                spacing=8
            ),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: self._close_dialog())]
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    # ——— Abre un segundo diálogo para añadir un evento en el día seleccionado ———
    def _open_add_in_day_dialog(self):
        dia = self.selected_day
        fecha_preset = date(current_year, current_month_index + 1, dia)

        tf_title = ft.TextField(label="Título", width=200, value=self.new_event_title.value)
        dp_date = ft.DatePicker(value=fecha_preset)
        tp_start = ft.TimePicker(value=self.new_event_start_time.value)
        tp_end   = ft.TimePicker(value=self.new_event_end_time.value)
        dd_tipo  = ft.Dropdown(
            label="Tipo de evento",
            width=200,
            value=self.new_event_type.value,
            options=[
                ft.dropdown.Option("Examen"),
                ft.dropdown.Option("Entrega"),
                ft.dropdown.Option("General")
            ]
        )
        tf_desc = ft.TextField(
            label="Descripción",
            width=200,
            multiline=True,
            max_lines=3,
            value=self.new_event_description.value,
            hint_text="Descripción opcional..."
        )

        def save_and_close(e):
            titulo = tf_title.value.strip()
            fecha = dp_date.value
            hora_inicio = tp_start.value
            hora_fin = tp_end.value
            tipo = dd_tipo.value or "General"
            desc = tf_desc.value.strip()

            if titulo and fecha and hora_inicio and hora_fin:
                dt_inicio = datetime.combine(fecha, hora_inicio)
                dt_fin = datetime.combine(fecha, hora_fin)
                cronogram_events.append({
                    "id": len(cronogram_events) + 1,
                    "technique_id": None,
                    "title": titulo,
                    "start": dt_inicio,
                    "end": dt_fin,
                    "completed": False,
                    "type": tipo,
                    "description": desc
                })
            # Cerrar ambos diálogos
            self.page.dialog.open = False
            self.second_dialog.open = False
            self.page.update()

        contenido_2 = ft.Column(
            controls=[
                tf_title,
                ft.Row([ft.Text("Fecha:"), dp_date], alignment=ft.MainAxisAlignment.START),
                ft.Row([ft.Text("Inicio:"), tp_start], alignment=ft.MainAxisAlignment.START),
                ft.Row([ft.Text("Fin:"), tp_end], alignment=ft.MainAxisAlignment.START),
                dd_tipo,
                tf_desc
            ],
            spacing=8
        )

        self.second_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Añadir evento", weight=ft.FontWeight.BOLD),
            content=contenido_2,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(self.second_dialog, "open", False)),
                ft.TextButton("Guardar", on_click=save_and_close)
            ]
        )
        self.page.dialog = self.second_dialog
        self.second_dialog.open = True
        self.page.update()

    # ——— Cierra cualquier diálogo abierto ———
    def _close_dialog(self):
        self.page.dialog.open = False
        self.page.update()

    def build(self):
        # 1) Límite de uso
        if check_usage_limit():
            return ft.Text("Has superado tu límite de uso. Vuelve mañana.",
                           color="red", size=20)

        hoy = date.today()

        # ------------------------------------------------
        # 2) Navbar superior
        # ------------------------------------------------
        navbar = ft.Container(
            bgcolor="white",
            padding=ft.padding.symmetric(horizontal=20, vertical=8),
            shadow=ft.BoxShadow(blur_radius=2, offset=ft.Offset(0, 1), color="#0000000F"),
            content=ft.Row(
                [
                    build_popup_menu(),
                    ft.Container(expand=True),
                    ft.Text(current_user["name"], color="#2B2B2B"),
                    ft.CircleAvatar(foreground_image_src=current_user["photo_url"], radius=15),
                ],
                alignment=ft.MainAxisAlignment.CENTER
            )
        )

        # ------------------------------------------------------------------
        # 3) Encabezado: {Año actual}  [<-]  [Hoy]  {Mes}  [->]  {Año siguiente}
        # ------------------------------------------------------------------
        header_year_left  = ft.Text(str(current_year), size=18, weight=ft.FontWeight.BOLD, color="#2B2B2B")
        header_year_right = ft.Text(str(current_year + 1), size=18, weight=ft.FontWeight.BOLD, color="#2B2B2B")
        month_name = month_names[current_month_index]

        btn_today = ft.IconButton(
            icon=ft.icons.CALENDAR_TODAY,
            icon_color="#2B2B2B",
            tooltip="Ir a Hoy",
            on_click=lambda e: self._go_to_today()
        )

        header_row = ft.Row(
            controls=[
                header_year_left,
                ft.IconButton(icon=ft.icons.ARROW_BACK_IOS, icon_color="#2B2B2B",
                              on_click=lambda e: change_month(-1)),
                btn_today,
                ft.Text(f"{month_name}", size=20, weight=ft.FontWeight.BOLD, color="#2B2B2B"),
                ft.IconButton(icon=ft.icons.ARROW_FORWARD_IOS, icon_color="#2B2B2B",
                              on_click=lambda e: change_month(1)),
                header_year_right,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8
        )

        # -----------------------------------------------------
        # 4) Separador amarillo debajo del encabezado principal
        # -----------------------------------------------------
        separator = ft.Container(
            height=2,
            bgcolor="#FACC15",
            margin=ft.margin.only(top=6, bottom=6, left=30, right=30)
        )

        # -----------------------------------------------------
        # 5) Fila de días (“SUN”, “MON”, …) con estilo cápsula
        # -----------------------------------------------------
        day_labels = ft.Container(
            margin=ft.margin.only(bottom=8),
            content=ft.Row(
                controls=[
                    ft.Container(
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        bgcolor="#000000",
                        border_radius=ft.border_radius.all(12),
                        content=ft.Text(dia, color="white", size=12, weight=ft.FontWeight.BOLD)
                    )
                    for dia in ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6
            )
        )

        # -----------------------------------------------------
        # 6) Construcción de la cuadrícula del mes actual
        # -----------------------------------------------------
        cal = calendar.Calendar(firstweekday=6)
        month_days = cal.monthdayscalendar(current_year, current_month_index + 1)

        def make_cell(day: int):
            # Celda vacía (day == 0), color más oscuro para destacar
            if day == 0:
                return ft.Container(
                    width=120,
                    height=100,
                    bgcolor="#E0E0E0",  # gris más oscuro
                    border_radius=ft.border_radius.all(6),
                    margin=ft.margin.all(4)
                )

            # Determinar si es el día actual
            is_today = (
                day == hoy.day
                and (current_month_index + 1) == hoy.month
                and current_year == hoy.year
            )

            # Construir lista de controles internos:
            cell_controls = []

            # 6.1) Número de día
            numero = ft.Container(
                content=ft.Text(str(day), size=14, weight=ft.FontWeight.BOLD, color="#2B2B2B"),
                margin=ft.margin.only(bottom=4)
            )
            cell_controls.append(numero)

            # 6.2) Eventos de ese día
            eventos_dia = [
                ev for ev in cronogram_events
                if ev["start"].date() == date(current_year, current_month_index + 1, day)
            ]

            if eventos_dia:
                # Solo mostramos el primer evento en la celda
                ev = eventos_dia[0]
                dot = ft.Container(
                    width=6,
                    height=6,
                    bgcolor=ft.colors.GREEN if not ev.get("completed", False) else "#6B7280",
                    border_radius=ft.border_radius.all(3),
                    margin=ft.margin.only(right=4)
                )
                texto = ft.Text(ev["title"], size=12, color="#2B2B2B",
                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
                cell_controls.append(
                    ft.Row(
                        controls=[dot, texto],
                        alignment=ft.MainAxisAlignment.START,
                        spacing=4
                    )
                )
                if len(eventos_dia) > 1:
                    resto = ft.Text(f"+ {len(eventos_dia)-1} más", size=10, color="#6B7280", italic=True)
                    cell_controls.append(resto)

                # Badge pequeño
                badge = ft.Container(
                    width=8,
                    height=8,
                    bgcolor="#EF4444",
                    border_radius=ft.border_radius.all(4),
                    alignment=ft.alignment.top_right,
                    margin=ft.margin.only(top=2, right=2),
                    tooltip=f"{len(eventos_dia)} evento(s)"
                )
            else:
                badge = None

            # 6.3) Celda final con borde y hover
            cell = ft.Container(
                width=120,
                height=100,
                bgcolor="white",
                border=ft.border.all(1, "#E5E7EB"),
                border_radius=ft.border_radius.all(6),
                padding=ft.padding.only(left=6, top=6, right=6, bottom=0),
                content=ft.Stack(
                    controls=[
                        ft.Column(
                            controls=cell_controls,
                            spacing=4,
                            alignment=ft.MainAxisAlignment.START
                        ),
                        badge or ft.Container()
                    ]
                ),
                margin=ft.margin.all(4)
            )

            # Resaltar día actual con borde amarillo
            if is_today:
                cell.border = ft.border.all(2, "#FACC15")

            # Hover: sombra más marcada
            cell.mouse_enter = lambda e: setattr(cell, "shadow", ft.BoxShadow(
                blur_radius=10, offset=ft.Offset(0, 4), color="#00000015"))
            cell.mouse_leave = lambda e: setattr(cell, "shadow", None)

            # Clic en la celda → abrir diálogo de ese día
            cell.on_click = lambda e, d=day: self._open_day_dialog(d)

            return cell

        calendar_rows = []
        for semana in month_days:
            fila = ft.Row(
                controls=[make_cell(d) for d in semana],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=0
            )
            calendar_rows.append(fila)

        calendar_grid = ft.Column(controls=calendar_rows, spacing=0)

        # -----------------------------------------------------
        # 6.5) GRÁFICA DE DISTRIBUCIÓN DE TIPOS DE EVENTO
        # -----------------------------------------------------
        distribucion = {}
        for ev in cronogram_events:
            ev_fecha = ev["start"].date()
            if ev_fecha.year == current_year and ev_fecha.month == (current_month_index + 1):
                tipo = ev.get("type", "General")
                distribucion[tipo] = distribucion.get(tipo, 0) + 1
        if not distribucion:
            distribucion["General"] = 0

        color_para_tipo = {
            "Examen": "#EF4444",
            "Entrega": "#1E40AF",
            "General": "#10B981"
        }
        barras_controles = []
        for tipo, cantidad in distribucion.items():
            color = color_para_tipo.get(tipo, "#6B7280")
            ancho_barra = min(cantidad * 10, 200)
            barras_controles.append(
                ft.Row(
                    controls=[
                        ft.Text(f"{tipo}:", size=12, weight=ft.FontWeight.BOLD, color="#2B2B2B", width=60),
                        ft.Container(width=ancho_barra, height=12, bgcolor=color, border_radius=ft.border_radius.all(6)),
                        ft.Text(f"{cantidad}", size=12, color="#2B2B2B")
                    ],
                    spacing=4
                )
            )
        grafico_distribucion = ft.Container(
            padding=ft.padding.symmetric(horizontal=30, vertical=12),
            content=ft.Column(
                controls=[ft.Text("Distribución de eventos", size=14, weight=ft.FontWeight.BOLD)] + barras_controles,
                spacing=6
            )
        )

        # -----------------------------------------------------
        # 6.6) INDICADOR DE PROGRESO MENSUAL (USANDO ProgressBar)
        # -----------------------------------------------------
        eventos_mes_actual = [
            ev for ev in cronogram_events
            if ev["start"].year == current_year and ev["start"].month == (current_month_index + 1)
        ]
        total_eventos = len(eventos_mes_actual)
        completados = sum(1 for ev in eventos_mes_actual if ev.get("completed", False))
        porcentaje = (completados / total_eventos) if total_eventos > 0 else 0.0

        etiqueta_progreso = ft.Text(
            f"{completados} / {total_eventos} eventos completados",
            size=12, color="#2B2B2B"
        )
        barra_progreso = ft.ProgressBar(
            value=porcentaje,
            width=300
        )
        progreso_mensual = ft.Container(
            padding=ft.padding.symmetric(horizontal=30, vertical=8),
            content=ft.Row(
                controls=[etiqueta_progreso, ft.Container(width=16), barra_progreso],
                spacing=8,
                alignment=ft.MainAxisAlignment.START
            )
        )

        # -----------------------------------------------------
        # 7) PANEL “Próximos eventos” (ahora sobre el formulario)
        # -----------------------------------------------------
        ahora = datetime.now()
        futuros = sorted(
            [ev for ev in cronogram_events if ev["start"] >= ahora],
            key=lambda ev: ev["start"]
        )[:3]
        proximos_controles = []
        if futuros:
            for ev in futuros:
                fecha_str = ev["start"].strftime("%d/%m %H:%M")
                proximos_controles.append(
                    ft.Row(
                        controls=[
                            ft.Container(
                                width=6,
                                height=6,
                                bgcolor="#10B981" if not ev.get("completed", False) else "#6B7280",
                                border_radius=ft.border_radius.all(3),
                                margin=ft.margin.only(right=6)
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(ev["title"], size=12, weight=ft.FontWeight.BOLD, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Text(fecha_str, size=10, color="#6B7280")
                                ],
                                spacing=2
                            )
                        ],
                        spacing=4
                    )
                )
        else:
            proximos_controles.append(
                ft.Text("— Sin eventos futuros —", size=12, color="#6B7280")
            )

        proximos_panel = ft.Container(
            padding=ft.padding.all(8),
            bgcolor="#F9FAFB",
            border_radius=ft.border_radius.all(6),
            content=ft.Column(
                controls=[ft.Text("Próximos eventos", size=14, weight=ft.FontWeight.BOLD)] + proximos_controles,
                spacing=6
            )
        )

        # -----------------------------------------------------
        # 8) FORMULARIO DE “Añadir nuevo evento”
        # -----------------------------------------------------
        def save_new_event(e):
            titulo = self.new_event_title.value.strip()
            fecha = self.new_event_date.value
            hora_inicio = self.new_event_start_time.value
            hora_fin    = self.new_event_end_time.value
            tipo = self.new_event_type.value or "General"
            desc = self.new_event_description.value.strip()

            if titulo and fecha and hora_inicio and hora_fin:
                dt_inicio = datetime.combine(fecha, hora_inicio)
                dt_fin    = datetime.combine(fecha, hora_fin)
                cronogram_events.append({
                    "id": len(cronogram_events) + 1,
                    "technique_id": None,
                    "title": titulo,
                    "start": dt_inicio,
                    "end":   dt_fin,
                    "completed": False,
                    "type": tipo,
                    "description": desc
                })
                # Limpiar campos tras guardar
                self.new_event_title.value = ""
                self.new_event_date.value = date.today()
                self.new_event_start_time.value = dt_time(hour=9, minute=0)
                self.new_event_end_time.value = dt_time(hour=10, minute=0)
                self.new_event_type.value = "General"
                self.new_event_description.value = ""
                self.page.update()

        add_event_panel = ft.Container(
            bgcolor="#EFF6FF",
            border_radius=ft.border_radius.all(8),
            padding=ft.padding.all(12),
            width=260,
            shadow=ft.BoxShadow(blur_radius=4, offset=ft.Offset(0, 2), color="#00000010"),
            content=ft.Column(
                controls=[
                    self.new_event_title,
                    ft.Row([ft.Text("Fecha:", size=12), self.new_event_date], alignment=ft.MainAxisAlignment.START),
                    ft.Row([ft.Text("Inicio:", size=12), self.new_event_start_time], alignment=ft.MainAxisAlignment.START),
                    ft.Row([ft.Text("Fin:",    size=12), self.new_event_end_time], alignment=ft.MainAxisAlignment.START),
                    self.new_event_type,
                    self.new_event_description,
                    ft.Divider(height=8, color="#FFFFFF00"),
                    ft.ElevatedButton("Guardar", on_click=save_new_event, bgcolor="#1E40AF", color="white")
                ],
                spacing=8
            )
        )

        # -----------------------------------------------------
        # 9) PANEL “Resumen mensual” (ahora debajo del formulario)
        # -----------------------------------------------------
        eventos_mes = [
            ev for ev in cronogram_events
            if ev["start"].year == current_year and ev["start"].month == (current_month_index + 1)
        ]
        total_mes = len(eventos_mes)
        completados_mes = sum(1 for ev in eventos_mes if ev.get("completed", False))
        # Para “días sin eventos” se podría mejorar, pero va un cálculo aproximado:
        dias_mes_calendario = sum(len(week) for week in month_days)
        dias_sin_eventos = dias_mes_calendario - total_mes

        resumen_controles = [
            ft.Row([ft.Text("Total eventos:", size=12), ft.Text(str(total_mes), size=12, weight=ft.FontWeight.BOLD)]),
            ft.Row([ft.Text("Completados:", size=12), ft.Text(str(completados_mes), size=12, weight=ft.FontWeight.BOLD)]),
            ft.Row([ft.Text("Días sin eventos:", size=12), ft.Text(str(dias_sin_eventos), size=12, weight=ft.FontWeight.BOLD)])
        ]

        resumen_panel = ft.Container(
            padding=ft.padding.all(8),
            bgcolor="#F9FAFB",
            border_radius=ft.border_radius.all(6),
            content=ft.Column(
                controls=[ft.Text("Resumen mensual", size=14, weight=ft.FontWeight.BOLD)] + resumen_controles,
                spacing=6
            )
        )

        # -----------------------------------------------------
        # 10) Composición de la sección de calendario + lateral
        # -----------------------------------------------------
        calendar_section = ft.Row(
            controls=[
                # Columna principal: calendario + gráficas + progreso
                ft.Column(
                    controls=[
                        header_row,
                        separator,
                        day_labels,
                        calendar_grid,
                        grafico_distribucion,
                        progreso_mensual
                    ],
                    spacing=6,
                    expand=True
                ),
                ft.Container(width=16),
                # Columna derecha: Próximos eventos → Formulario → Resumen mensual
                ft.Column(
                    controls=[
                        proximos_panel,
                        ft.Container(height=12, bgcolor="transparent"),
                        add_event_panel,
                        ft.Container(height=12, bgcolor="transparent"),
                        resumen_panel
                    ],
                    spacing=12,
                    width=260  # algo más ancho para que el formulario tenga suficiente espacio
                )
            ],
            spacing=20,
            expand=True
        )

        # -------------------------------------------------------------
        # 11) Panel “Eventos de este mes” en grid 2×2 (dos por fila)
        # -------------------------------------------------------------
        eventos_mes_controles = []
        for ev in cronogram_events:
            ev_fecha = ev["start"].date()
            if ev_fecha.year == current_year and ev_fecha.month == (current_month_index + 1):
                card = ft.Container(
                    width=220,
                    height=100,
                    bgcolor="white",
                    border_radius=ft.border_radius.all(8),
                    shadow=ft.BoxShadow(blur_radius=4, offset=ft.Offset(0, 2), color="#00000010"),
                    margin=ft.margin.all(8),
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    # Izquierda: título + hora + descripción
                                    ft.Column(
                                        controls=[
                                            ft.Row([
                                                ft.Container(
                                                    width=8,
                                                    height=8,
                                                    bgcolor=(
                                                        "#10B981"
                                                        if not ev.get("completed", False)
                                                        else "#6B7280"
                                                    ),
                                                    border_radius=ft.border_radius.all(4),
                                                    margin=ft.margin.only(right=6)
                                                ),
                                                ft.Text(ev["title"], 
                                                        size=14, weight=ft.FontWeight.BOLD, 
                                                        color="#2B2B2B", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
                                            ]),
                                            ft.Text(ev["start"].strftime("%d/%m %H:%M"),
                                                    size=12, color="#6B7280"),
                                            ft.Text(ev.get("description", ""), 
                                                    size=10, color="#4A4A4A", max_lines=2, 
                                                    overflow=ft.TextOverflow.ELLIPSIS)
                                        ],
                                        spacing=2,
                                        expand=True
                                    ),
                                    # Derecha: iconos (check / eliminar)
                                    ft.Row(
                                        controls=[
                                            ft.IconButton(
                                                icon=(
                                                    ft.icons.CHECK_CIRCLE
                                                    if ev.get("completed", False)
                                                    else ft.icons.CHECK_CIRCLE_OUTLINE
                                                ),
                                                icon_color=(
                                                    "#10B981"
                                                    if ev.get("completed", False)
                                                    else "#9CA3AF"
                                                ),
                                                tooltip="Marcar completado",
                                                on_click=lambda e, ev=ev:
                                                    self._toggle_completed(ev, not ev.get("completed", False))
                                            ),
                                            ft.IconButton(
                                                icon=ft.icons.DELETE_OUTLINE,
                                                icon_color="#EF4444",
                                                tooltip="Eliminar evento",
                                                on_click=lambda e, ev=ev: self._delete_event(ev)
                                            )
                                        ],
                                        spacing=4
                                    )
                                ]
                            )
                        ]
                    )
                )
                eventos_mes_controles.append(card)

        if not eventos_mes_controles:
            eventos_mes_controles.append(
                ft.Text("No hay eventos programados este mes.", italic=True, color="#6B7280")
            )

        filas_grid = []
        for i in range(0, len(eventos_mes_controles), 2):
            fila_dos = eventos_mes_controles[i:i+2]
            filas_grid.append(
                ft.Row(
                    controls=fila_dos,
                    spacing=16,
                    alignment=ft.MainAxisAlignment.START
                )
            )

        eventos_mes_grid = ft.Column(
            controls=[ft.Text("Eventos de este mes", size=16, weight=ft.FontWeight.BOLD, color="#2B2B2B")] + filas_grid,
            spacing=8
        )

        bottom_calendar_panel = ft.Container(
            padding=ft.padding.symmetric(horizontal=30, vertical=12),
            content=eventos_mes_grid
        )

        # -----------------------------------------------------
        # 12) Devolvemos la página completa
        # -----------------------------------------------------
        return ft.Column(
            controls=[
                navbar,
                ft.Container(height=12, bgcolor="transparent"),
                calendar_section,
                bottom_calendar_panel
            ],
            spacing=0,
            expand=True
        )

        



class ClassesPage(BasePage):
    def __init__(self, page: ft.Page, **kwargs):
        super().__init__(**kwargs); self.page=page
    def build(self):
        navbar=ft.Container(bgcolor="white",padding=ft.padding.only(left=40,right=30,top=10,bottom=10),
            content=ft.Row([build_popup_menu(),ft.Text("Point List",size=22,weight=ft.FontWeight.BOLD,color="#2B2B2B"),
                            ft.Container(expand=True),ft.Row([ft.Text(current_user["name"],color="#2B2B2B"),
                                                              ft.CircleAvatar(foreground_image_src=current_user["photo_url"],radius=15)],spacing=5)],
                           alignment=ft.MainAxisAlignment.CENTER))
        content=ft.Column([ft.Text("Página de Clases",size=36,weight=ft.FontWeight.BOLD,color="#2B2B2B"),
                           ft.Text("Aquí se mostrarán las clases de la asignatura seleccionada.",size=16,color="#4B4B4B")],
                          alignment=ft.MainAxisAlignment.CENTER,spacing=20)
        return ft.Column([navbar,ft.Divider(height=20,color="transparent"),content],spacing=0,expand=True)

class RecuperarContrasenaPage(BasePage):
    def __init__(self, page: ft.Page, **kwargs):
        super().__init__(**kwargs); self.page=page
    def build(self):
        navbar=ft.Container(bgcolor="white",padding=ft.padding.symmetric(horizontal=40,vertical=10),
            content=ft.Row([build_popup_menu(),ft.Text("Point List",size=24,weight=ft.FontWeight.BOLD,color="#2B2B2B"),ft.Container(expand=True)],
                           alignment=ft.MainAxisAlignment.CENTER))
        bg=ft.Image(src="/image.png",fit=ft.ImageFit.COVER,expand=True)
        overlay=ft.Container(expand=True,bgcolor=ft.colors.BLACK,opacity=0.5)
        left=ft.Container(expand=True,padding=ft.padding.all(30),
                          content=ft.Column([ft.Text("Recupera tu cuenta",size=32,weight=ft.FontWeight.BOLD,color="white"),
                                             ft.Container(height=20),
                                             ft.Text("Si has olvidado tu contraseña, ingresa tu correo…",size=14,color="white")],
                                            spacing=10))
        right=ft.Container(expand=True,padding=ft.padding.all(30),border_radius=ft.border_radius.all(12),
                           bgcolor="rgba(255,255,255,0.9)",
                           content=ft.Column([ft.Text("Recuperar cuenta",size=24,weight=ft.FontWeight.BOLD,color="#212121"),
                                              ft.TextField(label="Correo",hint_text="ejemplo@mail.com",border_color="#9E9E9E",text_size=14),
                                              ft.ElevatedButton(text="Enviar enlace",color="white",bgcolor="#1E40AF",on_click=lambda e:print("Enlace enviado"))],
                                             spacing=10))
        row=ft.Row([left,right],expand=True,alignment=ft.MainAxisAlignment.SPACE_BETWEEN,vertical_alignment=ft.CrossAxisAlignment.CENTER)
        layout=ft.Stack([bg,overlay,ft.Container(expand=True,content=row)])
        return layout

# ---------------------------
# CONTROLADOR DE NAVEGACIÓN
# ---------------------------
class NavigationController:
    page = None,
    content_container = None

    @classmethod
    def initialize(cls, page: ft.Page, container: ft.Container):
        cls.page = page
        cls.content_container = container

    @classmethod
    def update_view(cls, view_name: str, data: str = ""):
        if view_name == "Inicio":
            cls.content_container.content = HomePage(cls.page).build()

        elif view_name == "Login":
            cls.content_container.content = LoginPage(cls.page).build()

        elif view_name == "Notas":
            cls.content_container.content = NotesPage(cls.page).build()

        elif view_name == "DetalleAsignatura":
            cls.content_container.content = SubjectDetailPage(cls.page, data).build()

        elif view_name == "Calendario":
            # Aquí ya no le pasamos 'data', solo el page:
            cls.content_container.content = CalendarPage(cls.page).build()

        elif view_name == "Tecnicas":
            cls.content_container.content = StudyMethodsPage(cls.page, techniques).build()

        elif view_name == "Clases":
            cls.content_container.content = ClassesPage(cls.page).build()

        elif view_name == "Recuperar":
            cls.content_container.content = RecuperarContrasenaPage(cls.page).build()

        elif view_name == "Metodos":
            cls.content_container.content = StudyMethodsPage(cls.page, techniques).build()

        cls.page.update()

# ---------------------------
# FUNCIÓN PRINCIPAL
# ---------------------------
def main(page:ft.Page):
    page.title="Point List App"; page.bgcolor="#F3F3F3"; page.theme_mode=ft.ThemeMode.LIGHT; page.scroll=ft.ScrollMode.AUTO
    content_container=ft.Container(expand=True)
    content_container.content=LoginPage(page).build()
    NavigationController.initialize(page,content_container)
    page.add(content_container)

ft.app(target=main, assets_dir="assets")