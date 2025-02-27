#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gio
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Ruta del archivo de configuración de Docklike
CONFIG_FILE = os.path.expanduser("~/.config/xfce4/panel/docklike-1.rc")
APPLICATIONS_DIR = "/usr/share/applications"

# Verificar si el archivo existe
if not os.path.exists(CONFIG_FILE):
    logger.error("El archivo de configuración no se encuentra.")
    exit(1)

def find_icon_in_system(icon_name):
    """Busca el icono en el sistema usando Gio/GLib."""
    logger.debug(f"Buscando icono: {icon_name}")
    
    # Si es una ruta absoluta
    if icon_name.startswith('/'):
        if os.path.exists(icon_name):
            logger.debug(f"Icono encontrado en ruta absoluta: {icon_name}")
            return icon_name

    # Usar el tema de iconos actual
    icon_theme = Gtk.IconTheme.get_default()
    
    try:
        # Intentar encontrar el icono en el tema actual
        icon_info = icon_theme.lookup_icon(icon_name, 48, 0)
        if icon_info:
            icon_path = icon_info.get_filename()
            logger.debug(f"Icono encontrado en tema: {icon_path}")
            return icon_path
    except Exception as e:
        logger.debug(f"Error buscando icono {icon_name} en tema: {e}")

    # Búsqueda manual en ubicaciones comunes
    search_paths = [
        '/usr/share/icons/hicolor/48x48/apps',
        '/usr/share/icons/hicolor/scalable/apps',
        '/usr/share/pixmaps',
        '/usr/share/icons/gnome/48x48/apps',
        '/usr/share/icons/Adwaita/48x48/apps',
        '/usr/share/app-install/icons',
        os.path.expanduser('~/.local/share/icons'),
        '/usr/local/share/icons'
    ]

    # Extensiones comunes de iconos
    extensions = ['', '.png', '.svg', '.xpm']

    for path in search_paths:
        for ext in extensions:
            full_path = os.path.join(path, f"{icon_name}{ext}")
            if os.path.exists(full_path):
                logger.debug(f"Icono encontrado en búsqueda manual: {full_path}")
                return full_path

    # Si todo falla, intentar buscar como aplicación
    try:
        app_info = Gio.DesktopAppInfo.new(f"{icon_name}.desktop")
        if app_info:
            icon = app_info.get_icon()
            if icon:
                icon_info = icon_theme.lookup_icon(icon.to_string(), 48, 0)
                if icon_info:
                    icon_path = icon_info.get_filename()
                    logger.debug(f"Icono encontrado como aplicación: {icon_path}")
                    return icon_path
    except Exception as e:
        logger.debug(f"Error buscando icono como aplicación: {e}")

    logger.warning(f"No se encontró el icono: {icon_name}")
    return None

def get_icon_name_from_desktop(desktop_file):
    """Obtiene el nombre del icono desde un archivo .desktop"""
    logger.debug(f"Leyendo archivo .desktop: {desktop_file}")
    
    # Intentar usar Gio primero
    try:
        app_info = Gio.DesktopAppInfo.new_from_filename(desktop_file)
        if app_info:
            icon = app_info.get_icon()
            if icon:
                icon_name = icon.to_string()
                logger.debug(f"Icono encontrado en .desktop (Gio): {icon_name}")
                return icon_name
    except Exception as e:
        logger.debug(f"Error leyendo .desktop con Gio: {e}")

    # Fallback: leer el archivo manualmente
    try:
        with open(desktop_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.lower().startswith("icon="):
                    icon_name = line.split('=')[1].strip()
                    logger.debug(f"Icono encontrado en .desktop (manual): {icon_name}")
                    return icon_name
    except Exception as e:
        logger.debug(f"Error leyendo .desktop manualmente: {e}")

    # Si no se encuentra, usar el nombre del archivo
    base_name = os.path.basename(desktop_file).replace('.desktop', '')
    logger.debug(f"Usando nombre base como icono: {base_name}")
    return base_name

def get_app_name_from_desktop(desktop_file):
    """Obtiene el nombre de la aplicación desde un archivo .desktop"""
    try:
        app_info = Gio.DesktopAppInfo.new_from_filename(desktop_file)
        if app_info:
            return app_info.get_name()
    except Exception as e:
        logger.debug(f"Error obteniendo nombre de aplicación: {e}")
    
    # Fallback: extraer del archivo
    try:
        with open(desktop_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.lower().startswith("name="):
                    return line.split('=')[1].strip()
    except Exception:
        pass
    
    # Usar el nombre del archivo si todo falla
    return os.path.basename(desktop_file).replace('.desktop', '')

def get_icon_name_and_path(desktop_file):
    """Obtiene el nombre del icono y su ruta desde un archivo .desktop"""
    if not desktop_file or not desktop_file.strip():
        return None, None

    icon_name = get_icon_name_from_desktop(desktop_file)
    icon_path = find_icon_in_system(icon_name) if icon_name else None
    
    logger.debug(f"Resultado final - Nombre: {icon_name}, Ruta: {icon_path}")
    return icon_name, icon_path

class IconListWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Ordenar iconos de Docklike")
        self.set_default_size(500, 550)

        # Cambiar el icono de la ventana
        if os.path.exists("/usr/share/branding-soplos/plymouth-logo.png"):
            self.set_icon_from_file("/usr/share/branding-soplos/plymouth-logo.png")
        
        # Crear un contenedor principal
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(self.box)

        # Crear encabezado
        header = Gtk.Label()
        header.set_markup("<b>Organizar iconos anclados</b>")
        header.set_margin_top(10)
        header.set_margin_bottom(10)
        self.box.pack_start(header, False, False, 0)

        # Crear ScrolledWindow para la lista
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(300)  # Establecer altura mínima
        self.box.pack_start(scrolled, True, True, 0)

        # Crear lista con iconos
        self.liststore = Gtk.ListStore(str, str, GdkPixbuf.Pixbuf, str)  # (nombre, ruta_icono, pixbuf, desktop_file)
        
        # Leer los iconos del archivo de configuración
        self.pinned_icons = []
        with open(CONFIG_FILE, 'r') as f:
            for line in f:
                if line.startswith("pinned="):
                    self.pinned_icons = line.split('=')[1].strip().split(';')
                    for desktop_file in self.pinned_icons:
                        if desktop_file:  # Ignorar entradas vacías
                            icon_name, icon_path = get_icon_name_and_path(desktop_file)
                            app_name = get_app_name_from_desktop(desktop_file)
                            pixbuf = self.load_icon(icon_path)
                            if pixbuf:  # Solo agregar si se pudo cargar el icono
                                self.liststore.append([app_name or icon_name, icon_path, pixbuf, desktop_file])
                            else:
                                logger.warning(f"No se pudo cargar el icono para: {desktop_file}")

        # Crear la vista de lista
        self.treeview = Gtk.TreeView(model=self.liststore)
        self.treeview.set_headers_visible(True)
        
        # Crear un renderer de imagen para los iconos
        renderer_pixbuf = Gtk.CellRendererPixbuf()
        column_icon = Gtk.TreeViewColumn("Icono", renderer_pixbuf, pixbuf=2)
        
        # Crear un renderer de texto para los nombres
        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn("Aplicación", renderer_text, text=0)
        column_text.set_expand(True)  # Permitir que la columna de texto se expanda
        
        # Agregar las columnas al TreeView
        self.treeview.append_column(column_icon)
        self.treeview.append_column(column_text)
        
        # Agregar la vista al ScrolledWindow
        scrolled.add(self.treeview)

        # Botones de acción
        self.button_box = Gtk.Box(spacing=6)
        self.button_box.set_margin_top(10)
        self.button_box.set_margin_bottom(10)
        self.button_box.set_margin_start(10)
        self.button_box.set_margin_end(10)
        self.box.pack_start(self.button_box, False, False, 0)

        self.up_button = Gtk.Button(label="Subir")
        self.down_button = Gtk.Button(label="Bajar")
        self.remove_button = Gtk.Button(label="Eliminar")
        self.button_box.pack_start(self.up_button, True, True, 0)
        self.button_box.pack_start(self.down_button, True, True, 0)
        self.button_box.pack_start(self.remove_button, True, True, 0)

        # Botón para añadir aplicaciones
        self.add_button = Gtk.Button(label="Añadir Aplicación")
        self.add_button.set_margin_start(10)
        self.add_button.set_margin_end(10)
        self.box.pack_start(self.add_button, False, False, 0)

        # Botones de guardar/cancelar
        self.action_box = Gtk.Box(spacing=6)
        self.action_box.set_margin_top(10)
        self.action_box.set_margin_bottom(10)
        self.action_box.set_margin_start(10)
        self.action_box.set_margin_end(10)
        self.box.pack_start(self.action_box, False, False, 0)

        self.save_button = Gtk.Button(label="Guardar")
        self.cancel_button = Gtk.Button(label="Salir")
        self.action_box.pack_start(self.save_button, True, True, 0)
        self.action_box.pack_start(self.cancel_button, True, True, 0)

        # Conectar botones
        self.up_button.connect("clicked", self.move_up)
        self.down_button.connect("clicked", self.move_down)
        self.remove_button.connect("clicked", self.remove_selected)
        self.add_button.connect("clicked", self.open_app_selector)
        self.save_button.connect("clicked", self.save_and_close)
        self.cancel_button.connect("clicked", self.close_window)

    def load_icon(self, icon_path):
        """Carga el icono desde el path especificado y lo convierte en un Pixbuf"""
        try:
            if icon_path and os.path.exists(icon_path):
                logger.debug(f"Cargando icono desde: {icon_path}")
                return GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, 48, 48)
            
            # Cargar un icono por defecto si no se encuentra el icono
            default_icon = "/usr/share/icons/hicolor/48x48/apps/application-default-icon.png"
            if os.path.exists(default_icon):
                logger.debug("Cargando icono por defecto")
                return GdkPixbuf.Pixbuf.new_from_file_at_size(default_icon, 48, 48)
            
        except Exception as e:
            logger.error(f"Error al cargar icono: {e}")
        return None

    def move_up(self, widget):
        selection = self.treeview.get_selection()
        model, iter = selection.get_selected()
        if iter:
            row = model.get_path(iter)[0]
            if row > 0:
                prev_iter = model.get_iter(row - 1)
                model.swap(iter, prev_iter)
                self.treeview.set_cursor(model.get_path(iter))

    def move_down(self, widget):
        selection = self.treeview.get_selection()
        model, iter = selection.get_selected()
        if iter:
            row = model.get_path(iter)[0]
            if row < len(model) - 1:
                next_iter = model.get_iter(row + 1)
                model.swap(iter, next_iter)
                self.treeview.set_cursor(model.get_path(iter))

    def remove_selected(self, widget):
        selection = self.treeview.get_selection()
        model, iter = selection.get_selected()
        if iter:
            app_name = model.get_value(iter, 0)
            
            # Confirmar la eliminación
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text=f"¿Estás seguro de que quieres eliminar '{app_name}' de la lista?"
            )
            response = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.YES:
                model.remove(iter)

    def open_app_selector(self, widget):
        app_selector = AppSelectorDialog(self)
        response = app_selector.run()
        
        if response == Gtk.ResponseType.OK:
            selected_apps = app_selector.get_selected_apps()
            for app_path in selected_apps:
                # Verificar si la app ya está en la lista
                already_added = False
                for row in self.liststore:
                    if row[3] == app_path:
                        already_added = True
                        break
                
                if not already_added:
                    icon_name, icon_path = get_icon_name_and_path(app_path)
                    app_name = get_app_name_from_desktop(app_path)
                    pixbuf = self.load_icon(icon_path)
                    if pixbuf:
                        self.liststore.append([app_name or icon_name, icon_path, pixbuf, app_path])
                    else:
                        logger.warning(f"No se pudo cargar el icono para: {app_path}")
        
        app_selector.destroy()

    def save_and_close(self, widget):
        new_icons = []
        for row in self.liststore:
            desktop_file = row[3]
            if desktop_file:
                new_icons.append(desktop_file)
        
        with open(CONFIG_FILE, 'r') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines):
            if line.startswith("pinned="):
                lines[i] = f"pinned={';'.join(new_icons)}\n"
                break
        
        try:
            with open(CONFIG_FILE, 'w') as f:
                f.writelines(lines)
            
            os.system("xfce4-panel -r")
            
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Cambios guardados correctamente"
            )
            dialog.run()
            dialog.destroy()
            
        except Exception as e:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=f"Error al guardar los cambios: {str(e)}"
            )
            dialog.run()
            dialog.destroy()
            return
        
        self.destroy()

    def close_window(self, widget):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="¿Estás seguro de que quieres cerrar sin guardar?"
        )
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            self.destroy()

class AppSelectorDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(
            self, title="Seleccionar Aplicaciones", transient_for=parent, flags=0,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK
            )
        )

        # Establecer un tamaño más grande para el diálogo
        self.set_default_size(600, 500)
        self.set_modal(True)
        
        box = self.get_content_area()
        box.set_spacing(6)
        
        # Etiqueta de instrucción
        label = Gtk.Label(label="Selecciona las aplicaciones que quieres añadir:")
        label.set_margin_top(10)
        label.set_margin_bottom(5)
        box.add(label)
        
        # Añadir barra de búsqueda
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        search_box.set_margin_start(10)
        search_box.set_margin_end(10)
        search_box.set_margin_bottom(10)
        
        search_label = Gtk.Label(label="Buscar:")
        search_box.pack_start(search_label, False, False, 0)
        
        self.search_entry = Gtk.Entry()
        self.search_entry.connect("changed", self.on_search_changed)
        search_box.pack_start(self.search_entry, True, True, 0)
        
        box.add(search_box)
        
        # Crear ScrolledWindow para la lista
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_margin_top(5)
        scrolled.set_margin_bottom(10)
        scrolled.set_margin_start(10)
        scrolled.set_margin_end(10)
        scrolled.set_min_content_height(350)  # Altura mínima para ver varias aplicaciones
        box.add(scrolled)
        
        # Modelo de lista con casillas de verificación
        self.liststore = Gtk.ListStore(bool, str, GdkPixbuf.Pixbuf, str)  # (seleccionado, nombre, pixbuf, ruta)
        
        # Crear la vista de la lista
        self.treeview = Gtk.TreeView(model=self.liststore)
        self.treeview.set_headers_visible(True)  # Mostrar encabezados para mejor visualización
        
        # Agregar una columna de casilla de verificación
        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.connect("toggled", self.on_cell_toggled)
        column_toggle = Gtk.TreeViewColumn("", renderer_toggle, active=0)
        self.treeview.append_column(column_toggle)
        
        # Agregar una columna para el icono
        renderer_pixbuf = Gtk.CellRendererPixbuf()
        column_icon = Gtk.TreeViewColumn("Icono", renderer_pixbuf, pixbuf=2)
        self.treeview.append_column(column_icon)
        
        # Agregar una columna para el nombre
        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn("Aplicación", renderer_text, text=1)
        column_text.set_expand(True)  # Permitir que la columna se expanda
        column_text.set_min_width(300)  # Establecer un ancho mínimo para la columna de nombre
        self.treeview.append_column(column_text)
        
        # Ordenar por nombre
        self.liststore.set_sort_column_id(1, Gtk.SortType.ASCENDING)
        
        scrolled.add(self.treeview)
        
        # Agregar indicador de estado
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        status_box.set_margin_start(10)
        status_box.set_margin_end(10)
        status_box.set_margin_bottom(10)
        
        self.status_label = Gtk.Label(label="Cargando aplicaciones...")
        status_box.pack_start(self.status_label, False, False, 0)
        
        # Botón para seleccionar/deseleccionar todas
        self.select_all_button = Gtk.Button(label="Seleccionar Todo")
        self.select_all_button.connect("clicked", self.toggle_select_all)
        status_box.pack_end(self.select_all_button, False, False, 0)
        
        box.add(status_box)
        
        # Mostrar todo
        self.show_all()
        
        # Cargar aplicaciones DESPUÉS de crear todos los elementos de la interfaz
        self.load_applications()
        
        # Focus en el campo de búsqueda
        self.search_entry.grab_focus()

    def load_applications(self):
        """Carga todas las aplicaciones disponibles en el directorio de aplicaciones"""
        desktop_files = []
        
        # Buscar en el directorio principal de aplicaciones
        for filename in os.listdir(APPLICATIONS_DIR):
            if filename.endswith(".desktop"):
                desktop_files.append(os.path.join(APPLICATIONS_DIR, filename))
        
        # También buscar en ~/.local/share/applications
        local_app_dir = os.path.expanduser("~/.local/share/applications")
        if os.path.exists(local_app_dir):
            for filename in os.listdir(local_app_dir):
                if filename.endswith(".desktop"):
                    desktop_files.append(os.path.join(local_app_dir, filename))
        
        # Contador de aplicaciones cargadas
        loaded_count = 0
        
        # Añadir cada aplicación a la lista
        for desktop_file in desktop_files:
            try:
                app_info = Gio.DesktopAppInfo.new_from_filename(desktop_file)
                
                # Solo mostrar aplicaciones visibles que no son específicas del sistema
                if app_info and not app_info.get_nodisplay() and not app_info.get_is_hidden():
                    app_name = app_info.get_name()
                    icon_name, icon_path = get_icon_name_and_path(desktop_file)
                    pixbuf = self.load_icon(icon_path)
                    
                    if pixbuf and app_name:
                        self.liststore.append([False, app_name, pixbuf, desktop_file])
                        loaded_count += 1
            except Exception as e:
                logger.warning(f"Error cargando {desktop_file}: {e}")
        
        # Actualizar el estado
        self.status_label.set_text(f"Mostrando {loaded_count} aplicaciones")

    def load_icon(self, icon_path):
        """Carga el icono desde el path especificado y lo convierte en un Pixbuf"""
        try:
            if icon_path and os.path.exists(icon_path):
                return GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path, 32, 32)
            
            # Icono por defecto
            default_icon = "/usr/share/icons/hicolor/48x48/apps/application-default-icon.png"
            if os.path.exists(default_icon):
                return GdkPixbuf.Pixbuf.new_from_file_at_size(default_icon, 32, 32)
            
        except Exception as e:
            logger.error(f"Error al cargar icono: {e}")
        return None

    def on_cell_toggled(self, widget, path):
        """Cambia el estado de selección cuando se hace clic en la casilla"""
        model = self.treeview.get_model()
        
        if isinstance(model, Gtk.TreeModelFilter):
            # Convertir path del modelo filtrado al modelo original
            child_path = model.convert_path_to_child_path(Gtk.TreePath(path))
            self.liststore[child_path][0] = not self.liststore[child_path][0]
        else:
            # Modelo normal
            self.liststore[path][0] = not self.liststore[path][0]
        
        # Actualizar el contador de seleccionados
        self.update_selection_count()

    def update_selection_count(self):
        """Actualiza el contador de aplicaciones seleccionadas"""
        selected_count = sum(1 for row in self.liststore if row[0])
        model = self.treeview.get_model()
        
        if isinstance(model, Gtk.TreeModelFilter):
            visible_count = len([row for row in model])
            self.status_label.set_text(f"Seleccionadas: {selected_count} de {visible_count} aplicaciones visibles")
        else:
            self.status_label.set_text(f"Seleccionadas: {selected_count} de {len(self.liststore)} aplicaciones")

    def toggle_select_all(self, widget):
        """Selecciona o deselecciona todas las aplicaciones visibles"""
        model = self.treeview.get_model()
        select_all = "Seleccionar" in self.select_all_button.get_label()
        
        if isinstance(model, Gtk.TreeModelFilter):
            # Recorrer el modelo filtrado y cambiar las selecciones
            for row in model:
                child_iter = model.convert_iter_to_child_iter(row.iter)
                self.liststore[child_iter][0] = select_all
        else:
            # Modelo normal
            for row in self.liststore:
                row[0] = select_all
        
        # Actualizar el botón y el contador
        if select_all:
            self.select_all_button.set_label("Deseleccionar Todo")
        else:
            self.select_all_button.set_label("Seleccionar Todo")
        
        self.update_selection_count()

    def on_search_changed(self, widget):
        """Filtra la lista según el texto de búsqueda"""
        search_text = widget.get_text().lower()
        
        # Si el modelo tiene un filtro, quitarlo primero
        model = self.treeview.get_model()
        if isinstance(model, Gtk.TreeModelFilter):
            original_model = model.get_model()
            self.treeview.set_model(original_model)
        
        # Si hay texto de búsqueda, aplicar filtro
        if search_text:
            filter_model = self.liststore.filter_new()
            filter_model.set_visible_func(
                lambda model, iter, data: search_text in model[iter][1].lower()
            )
            self.treeview.set_model(filter_model)
            
            # Contar los resultados filtrados
            visible_count = len([row for row in filter_model])
            self.status_label.set_text(f"Mostrando {visible_count} resultados de búsqueda")
        else:
            # Si no hay texto, mostrar todo
            self.treeview.set_model(self.liststore)
            
            # Restablecer el contador
            self.update_selection_count()
        
        # Restablecer el botón de seleccionar todo
        self.select_all_button.set_label("Seleccionar Todo")

    def get_selected_apps(self):
        """Devuelve una lista de rutas de las aplicaciones seleccionadas"""
        selected_apps = []
        
        # Recorrer todas las filas en el liststore original
        for row in self.liststore:
            if row[0]:  # Si está seleccionado
                selected_apps.append(row[3])
        
        return selected_apps

def main():
    win = IconListWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
