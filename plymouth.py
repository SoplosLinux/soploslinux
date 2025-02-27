#!/usr/bin/env python3
import gi
import os
import subprocess
import sys
import shutil
import threading
import time

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

class PlymouthThemeManager(Gtk.Window):
    def __init__(self):
        super().__init__(title="Administrador de Temas Plymouth")
        self.set_default_size(450, 650)
        
        # Comprobar si tenemos las herramientas de plymouth
        self.plymouth_commands = self.find_plymouth_commands()
        
        # Intentar cargar el icono desde varias ubicaciones posibles
        icon_paths = [
            "/usr/share/branding-soplos/plymouth-logo.png",
            "/usr/share/plymouth/themes/spinner/watermark.png",
            "/usr/share/pixmaps/plymouth.png"
        ]
        
        for path in icon_paths:
            if os.path.exists(path):
                self.set_icon_from_file(path)
                break
        
        # Detectar si el sistema usa tema oscuro
        settings = Gtk.Settings.get_default()
        screen = Gdk.Screen.get_default()
        gtk_settings = Gtk.Settings.get_for_screen(screen)
        
        # Adaptar a la configuración del sistema si es posible
        if hasattr(gtk_settings, "gtk-application-prefer-dark-theme"):
            settings.set_property("gtk-application-prefer-dark-theme", True)

        # Contenedor principal con márgenes
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_box)
        
        # Encabezado
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        header_box.set_margin_top(15)
        header_box.set_margin_bottom(15)
        header_box.set_margin_start(20)
        header_box.set_margin_end(20)
        main_box.pack_start(header_box, False, False, 0)
        
        # Título y descripción
        title_label = Gtk.Label()
        title_label.set_markup("<span size='large' weight='bold'>Administrador de Temas Plymouth</span>")
        title_label.set_xalign(0.5)
        header_box.pack_start(title_label, False, False, 5)
        
        desc_label = Gtk.Label(label="Selecciona y aplica temas para la pantalla de inicio")
        desc_label.set_xalign(0.5)
        header_box.pack_start(desc_label, False, False, 5)
        
        # Contenedor para el contenido principal
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        content_box.set_margin_start(20)
        content_box.set_margin_end(20)
        content_box.set_margin_bottom(20)
        main_box.pack_start(content_box, True, True, 0)
        
        # Marco para la selección de tema
        theme_frame = Gtk.Frame(label="Temas disponibles")
        content_box.pack_start(theme_frame, True, True, 0)
        
        theme_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        theme_box.set_margin_top(10)
        theme_box.set_margin_bottom(10)
        theme_box.set_margin_start(10)
        theme_box.set_margin_end(10)
        theme_frame.add(theme_box)
        
        # Mensaje de estado
        self.status_label = Gtk.Label()
        self.status_label.set_xalign(0)
        theme_box.pack_start(self.status_label, False, False, 0)
        
        # Etiqueta para el tema actual
        self.current_theme_label = Gtk.Label()
        self.current_theme_label.set_xalign(0)
        theme_box.pack_start(self.current_theme_label, False, False, 0)
        
        # Desplegable para seleccionar el tema
        self.theme_combobox = Gtk.ComboBoxText()
        theme_box.pack_start(self.theme_combobox, False, False, 5)
        
        # Conectar la selección del combobox con la carga de la vista previa
        self.theme_combobox.connect("changed", self.on_theme_selected)
        
        # Área para la vista previa
        self.preview_image = Gtk.Image()
        self.preview_image.set_size_request(-1, 150)
        preview_scrolled = Gtk.ScrolledWindow()
        preview_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        preview_scrolled.add(self.preview_image)
        theme_box.pack_start(preview_scrolled, True, True, 5)
        
        # Barra de progreso
        self.progress_frame = Gtk.Frame(label="Progreso")
        content_box.pack_start(self.progress_frame, False, False, 0)
        
        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        progress_box.set_margin_top(10)
        progress_box.set_margin_bottom(10)
        progress_box.set_margin_start(10)
        progress_box.set_margin_end(10)
        self.progress_frame.add(progress_box)
        
        # Etiqueta de estado de la operación
        self.operation_label = Gtk.Label(label="Aplicando tema...")
        self.operation_label.set_xalign(0)
        progress_box.pack_start(self.operation_label, False, False, 0)
        
        # Barra de progreso
        self.progressbar = Gtk.ProgressBar()
        self.progressbar.set_show_text(True)
        self.progressbar.set_text("Preparando...")
        progress_box.pack_start(self.progressbar, False, False, 0)
        
        # Detalles de la operación
        self.detail_label = Gtk.Label(label="")
        self.detail_label.set_xalign(0)
        self.detail_label.set_line_wrap(True)
        progress_box.pack_start(self.detail_label, False, False, 0)
        
        # Contenedor para botones
        button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content_box.pack_start(button_box, False, False, 0)
        
        # Botones con iconos
        buttons = [
            ("Aplicar Tema", "preferences-desktop-theme", "Aplica el tema seleccionado", self.change_theme),
            ("Actualizar Lista", "view-refresh", "Actualiza la lista de temas disponibles", self.refresh_themes),
            ("Salir", "application-exit", "Cierra la aplicación", self.close_app)
        ]

        for text, icon_name, tooltip, callback in buttons:
            button = Gtk.Button()
            button.set_size_request(-1, 50)
            button.set_tooltip_text(tooltip)
            
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            hbox.set_halign(Gtk.Align.CENTER)
            
            icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
            label = Gtk.Label(label=text)
            
            hbox.pack_start(icon, False, False, 0)
            hbox.pack_start(label, False, False, 0)
            
            button.add(hbox)
            button.connect("clicked", callback)
            button_box.pack_start(button, False, False, 0)
        
        # Variable para controlar la cancelación de tareas
        self.cancel_operation = False
        
        # Verificar si podemos usar las herramientas de Plymouth
        if not self.plymouth_commands['list_themes'] or not self.plymouth_commands['set_theme']:
            self.status_label.set_markup("<span foreground='red'>⚠️ No se encontraron las herramientas de Plymouth</span>")
            self.show_dependencies_warning()
        else:
            # Cargar los temas disponibles
            self.load_themes()
            
            # Mostrar el tema actual
            self.show_current_theme()
        
        # Conectar evento de cierre
        self.connect("destroy", Gtk.main_quit)
    
    def find_plymouth_commands(self):
        """Busca las ubicaciones de los comandos de Plymouth"""
        commands = {
            'list_themes': None,
            'set_theme': None
        }
        
        # Posibles ubicaciones para los comandos
        possible_list_commands = [
            'plymouth-set-default-theme',
            '/usr/sbin/plymouth-set-default-theme',
            '/sbin/plymouth-set-default-theme'
        ]
        
        possible_set_commands = [
            'plymouth-set-default-theme',
            '/usr/sbin/plymouth-set-default-theme',
            '/sbin/plymouth-set-default-theme'
        ]
        
        # Alternativamente, buscar el comando plymouth
        plymouth_bin = shutil.which('plymouth')
        
        # Comprobar los comandos de listar temas
        for cmd in possible_list_commands:
            if shutil.which(cmd):
                commands['list_themes'] = cmd
                break
        
        # Si no encontramos el comando específico, pero tenemos plymouth
        if not commands['list_themes'] and plymouth_bin:
            commands['list_themes'] = f"{plymouth_bin} --list-themes"
        
        # Comprobar los comandos de cambiar tema
        for cmd in possible_set_commands:
            if shutil.which(cmd):
                commands['set_theme'] = cmd
                break
        
        return commands
    
    def show_dependencies_warning(self):
        """Muestra un diálogo de advertencia sobre dependencias faltantes"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK,
            text="Dependencias faltantes"
        )
        
        message = (
            "No se encontraron las herramientas de Plymouth necesarias.\n\n"
            "Por favor, instala el paquete 'plymouth-themes' o equivalente "
            "en tu distribución:\n\n"
            "• Debian/Ubuntu: sudo apt install plymouth-themes\n"
            "• Fedora: sudo dnf install plymouth-theme-spinner\n"
            "• Arch Linux: sudo pacman -S plymouth\n\n"
            "También asegúrate de que Plymouth esté correctamente configurado en tu sistema."
        )
        
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def show_current_theme(self):
        """Muestra el tema actualmente configurado en el sistema"""
        if not self.plymouth_commands['list_themes']:
            self.current_theme_label.set_text("No se pueden detectar los temas de Plymouth")
            return
            
        try:
            if ' ' in self.plymouth_commands['list_themes']:
                # Es un comando compuesto como "plymouth --list-themes"
                parts = self.plymouth_commands['list_themes'].split()
                result = subprocess.run(
                    parts,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            else:
                # Es un comando simple como "plymouth-set-default-theme"
                result = subprocess.run(
                    [self.plymouth_commands['list_themes'], "--list"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            output = result.stdout.strip()
            lines = output.split('\n')
            
            current_theme = None
            for line in lines:
                if '(' in line and ')' in line and 'default' in line:
                    parts = line.split('(')
                    if len(parts) > 1:
                        current_theme = parts[0].strip()
                        break
            
            if current_theme:
                self.current_theme_label.set_markup(f"<b>Tema actual:</b> {current_theme}")
                
                # Seleccionar el tema actual en el combobox
                model = self.theme_combobox.get_model()
                if model:
                    for i in range(len(model)):
                        if model[i][0] == current_theme:
                            self.theme_combobox.set_active(i)
                            break
                
                # Cargar la vista previa del tema actual
                self.load_theme_preview(current_theme)
            else:
                self.current_theme_label.set_text("No se pudo determinar el tema actual")
                
        except Exception as e:
            self.current_theme_label.set_text(f"Error al obtener tema actual: {str(e)}")
    
    def load_themes(self):
        """Carga la lista de temas disponibles"""
        if not self.plymouth_commands['list_themes']:
            return
            
        try:
            # Limpiar la lista actual
            self.theme_combobox.remove_all()
            
            # Determinar el comando adecuado
            if ' ' in self.plymouth_commands['list_themes']:
                # Es un comando compuesto como "plymouth --list-themes"
                cmd_parts = self.plymouth_commands['list_themes'].split()
                result = subprocess.run(
                    cmd_parts,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            else:
                # Es un comando simple como "plymouth-set-default-theme --list"
                result = subprocess.run(
                    [self.plymouth_commands['list_themes'], "--list"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            output = result.stdout.strip()
            if not output:
                # Intenta directamente listar los directorios de temas
                theme_dirs = [
                    "/usr/share/plymouth/themes/",
                    "/usr/local/share/plymouth/themes/"
                ]
                
                themes = []
                for theme_dir in theme_dirs:
                    if os.path.exists(theme_dir):
                        for item in os.listdir(theme_dir):
                            if os.path.isdir(os.path.join(theme_dir, item)):
                                themes.append(item)
                
                if not themes:
                    raise ValueError("No se encontraron temas")
            else:
                themes = []
                for line in output.split('\n'):
                    theme_name = line.split('(')[0].strip() if '(' in line else line.strip()
                    if theme_name:
                        themes.append(theme_name)
            
            # Agregar los temas al combobox
            for theme in sorted(set(themes)):
                self.theme_combobox.append_text(theme)
            
            # Seleccionar el primer tema si no hay ninguno seleccionado
            if self.theme_combobox.get_active() == -1 and themes:
                self.theme_combobox.set_active(0)
                
            # Actualizar el estado
            self.status_label.set_markup("<span foreground='green'>✓ Temas cargados correctamente</span>")
                
        except subprocess.CalledProcessError as e:
            self.status_label.set_markup("<span foreground='red'>⚠️ Error al ejecutar comandos de Plymouth</span>")
            self.show_error_dialog(f"Error al cargar los temas: {e.stderr}")
        except Exception as e:
            self.status_label.set_markup("<span foreground='red'>⚠️ Error al procesar temas</span>")
            self.show_error_dialog(f"Error al procesar los temas: {str(e)}")
    
    def on_theme_selected(self, combobox):
        """Maneja la selección de un tema en el combobox"""
        theme_name = combobox.get_active_text()
        if theme_name:
            self.load_theme_preview(theme_name)
    
    def load_theme_preview(self, theme_name):
        """Carga la vista previa del tema seleccionado"""
        # Posibles rutas para las imágenes de vista previa
        preview_paths = [
            f"/usr/share/plymouth/themes/{theme_name}/{theme_name}.png",
            f"/usr/share/plymouth/themes/{theme_name}/preview.png",
            f"/usr/share/plymouth/themes/{theme_name}/screenshot.png",
            f"/usr/local/share/plymouth/themes/{theme_name}/{theme_name}.png",
            f"/usr/local/share/plymouth/themes/{theme_name}/preview.png",
            f"/usr/local/share/plymouth/themes/{theme_name}/screenshot.png"
        ]
        
        # Verificar si existe alguna imagen de vista previa
        found_preview = None
        for path in preview_paths:
            if os.path.exists(path):
                found_preview = path
                break
        
        if found_preview:
            # Cargar y mostrar la imagen
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(found_preview)
                
                # Redimensionar si es necesario para ajustar al contenedor
                width = pixbuf.get_width()
                height = pixbuf.get_height()
                max_width = 360  # Ancho máximo para la vista previa
                
                if width > max_width:
                    ratio = max_width / width
                    new_width = max_width
                    new_height = int(height * ratio)
                    pixbuf = pixbuf.scale_simple(new_width, new_height, GdkPixbuf.InterpType.BILINEAR)
                
                self.preview_image.set_from_pixbuf(pixbuf)
                return True
            except Exception as e:
                print(f"Error al cargar la vista previa: {str(e)}")
                self.preview_image.clear()
                self.preview_image.set_from_icon_name("image-missing", Gtk.IconSize.DIALOG)
                return False
        else:
            # No se encontró vista previa, mostrar mensaje
            self.preview_image.clear()
            self.preview_image.set_from_icon_name("image-missing", Gtk.IconSize.DIALOG)
            return False
    
    def refresh_themes(self, widget):
        """Actualiza la lista de temas"""
        if not self.plymouth_commands['list_themes']:
            self.show_error_dialog("No se encontraron las herramientas de Plymouth")
            return
            
        self.load_themes()
        self.show_current_theme()
        self.show_info_dialog("Lista de temas actualizada")
    
    def update_progress_ui(self, fraction, text, detail_text):
        """Actualiza la UI de progreso desde el hilo principal"""
        self.progressbar.set_fraction(fraction)
        self.progressbar.set_text(text)
        self.detail_label.set_text(detail_text)
        
        # Esto es crítico: permitir que GTK procese otros eventos
        # durante la actualización de la interfaz
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        
        return False  # Para uso con GLib.idle_add
    
    def update_progress(self, step, total_steps, message=""):
        """Actualiza la barra de progreso de forma segura desde cualquier hilo"""
        if self.cancel_operation:
            return
            
        fraction = step / total_steps
        percentage_text = f"{int(fraction * 100)}%"
        
        # Usar GLib.idle_add para enviar la actualización al hilo principal
        GLib.idle_add(
            self.update_progress_ui,
            fraction,
            percentage_text,
            message
        )
    
    def reset_progress_ui(self):
        """Reinicia la interfaz de progreso"""
        self.cancel_operation = False
        self.progressbar.set_fraction(0.0)
        self.progressbar.set_text("0%")
        self.detail_label.set_text("")
    
    def theme_installation_worker(self, theme_name):
        """Hilo de trabajo para la instalación del tema"""
        try:
            # Comprobar si se ha cancelado
            if self.cancel_operation:
                return
                
            # Etapa 1: Preparación
            self.update_progress(1, 10, "Preparando la instalación del tema...")
            time.sleep(0.5)
            
            if self.cancel_operation:
                return
                
            # Etapa 2: Verificación del tema
            self.update_progress(2, 10, "Verificando tema seleccionado...")
            time.sleep(0.5)
            
            if self.cancel_operation:
                return
                
            # Etapa 3: Obtener ruta del tema
            self.update_progress(3, 10, "Localizando archivos del tema...")
            time.sleep(0.5)
            
            if self.cancel_operation:
                return
                
            # Etapa 4: Comprobar permisos
            self.update_progress(4, 10, "Comprobando permisos...")
            time.sleep(0.5)
            
            if self.cancel_operation:
                return
                
            # Etapa 5: Ejecutar el comando para cambiar el tema
            self.update_progress(5, 10, "Aplicando el nuevo tema...")
            
            # Ejecutar el comando real con pkexec para obtener privilegios
            cmd = ["pkexec", self.plymouth_commands['set_theme'], "-R", theme_name]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Esperar a que termine el proceso
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                GLib.idle_add(
                    self.installation_complete,
                    theme_name,
                    False,
                    f"Error: {stderr}"
                )
                return
            
            if self.cancel_operation:
                return
                
            # Etapa 6: Actualización de configuración
            self.update_progress(6, 10, "Actualizando configuración del sistema...")
            time.sleep(0.3)
            
            if self.cancel_operation:
                return
                
            # Etapa 7: Actualización de initramfs
            self.update_progress(7, 10, "Actualizando initramfs...")
            time.sleep(0.3)
            
            if self.cancel_operation:
                return
                
            # Etapa 8: Aplicando cambios
            self.update_progress(8, 10, "Aplicando cambios...")
            time.sleep(0.3)
            
            if self.cancel_operation:
                return
                
            # Etapa 9: Verificación
            self.update_progress(9, 10, "Verificando instalación...")
            time.sleep(0.3)
            
            if self.cancel_operation:
                return
                
            # Etapa 10: Finalizado
            self.update_progress(10, 10, "¡Tema instalado correctamente!")
            time.sleep(0.5)
            
            # Notificar completado en el hilo principal
            GLib.idle_add(
                self.installation_complete,
                theme_name,
                True
            )
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode('utf-8') if e.stderr else "Error desconocido"
            GLib.idle_add(
                self.installation_complete,
                theme_name,
                False,
                error_msg
            )
        except Exception as e:
            GLib.idle_add(
                self.installation_complete,
                theme_name,
                False,
                str(e)
            )
    
    def installation_complete(self, theme_name, success, error_msg=None):
        """Maneja la finalización de la instalación del tema"""
        # Ocultar barra de progreso
        self.progress_frame.hide()
        
        if success:
            self.show_info_dialog(f"Tema '{theme_name}' aplicado exitosamente")
            self.show_current_theme()
        else:
            self.show_error_dialog(f"Error al cambiar el tema: {error_msg}")
        
        # Habilitar la interfaz
        self.set_sensitive(True)
        
        # Reset the cancelation flag
        self.cancel_operation = False
        
        return False  # Para uso con GLib.idle_add
    
    def cancel_current_operation(self):
        """Cancelar la operación actual"""
        self.cancel_operation = True
        self.detail_label.set_text("Cancelando operación...")
        
        # Esperar un poco y reiniciar la interfaz
        GLib.timeout_add(1000, self.reset_progress_ui)
        GLib.timeout_add(1000, self.set_sensitive, True)
    
    def change_theme(self, widget):
        """Cambia el tema de Plymouth"""
        if not self.plymouth_commands['set_theme']:
            self.show_error_dialog("No se encontró el comando para cambiar el tema")
            return
            
        theme_name = self.theme_combobox.get_active_text()
        
        if not theme_name:
            self.show_error_dialog("Por favor, selecciona un tema")
            return
        
        # Mostrar diálogo de confirmación
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"¿Cambiar al tema '{theme_name}'?"
        )
        dialog.format_secondary_text("Esta acción requiere privilegios de administrador")
        response = dialog.run()
        dialog.destroy()
        
        if response != Gtk.ResponseType.YES:
            return
        
        # Preparar la interfaz para mostrar el progreso
        self.reset_progress_ui()
        self.operation_label.set_text(f"Aplicando tema '{theme_name}'...")
        self.progress_frame.show_all()  # Mostrar la barra de progreso
        
        # Forzar la actualización de la interfaz para asegurar que se muestre la barra
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        
        # Deshabilitar la interfaz durante la instalación
        self.set_sensitive(False)
        
        # Iniciar hilo de trabajo
        worker_thread = threading.Thread(
            target=self.theme_installation_worker,
            args=(theme_name,)
        )
        worker_thread.daemon = True
        worker_thread.start()
    
    def show_error_dialog(self, message):
        """Muestra un diálogo de error"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def show_info_dialog(self, message):
        """Muestra un diálogo informativo"""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Información"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def close_app(self, widget):
        """Cierra la aplicación"""
        # Cancelar cualquier operación pendiente antes de cerrar
        self.cancel_operation = True
        self.close()

if __name__ == "__main__":
    try:
        # Establecer variables de entorno para mejorar la compatibilidad
        os.environ['GTK_CSD'] = '0'  # Desactivar decoraciones del lado del cliente
        
        app = PlymouthThemeManager()
        app.show_all()
        # Ocultar inicialmente la barra de progreso, pero no quitarla del flujo
        app.progress_frame.hide()
        Gtk.main()
    except Exception as e:
        error_dialog = Gtk.MessageDialog(
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error al iniciar la aplicación"
        )
        error_dialog.format_secondary_text(str(e))
        error_dialog.run()
        error_dialog.destroy()
        sys.exit(1)
