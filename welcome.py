import gi
import subprocess
import os
import threading
import time
import shlex
import re

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, GLib

class SoplosWelcomeApp(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Bienvenido a Soplos Linux")
        self.set_border_width(10)
        self.set_icon_from_file("/usr/share/branding-soplos/plymouth-logo.png")
        # Ajustamos el tamaño para la versión con pestañas
        self.set_default_size(500, 300)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Contenedor principal vertical
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_box)
        
        # Logo y bienvenida
        logo_path = "/usr/share/branding-soplos/transparent-logo.png"
        if os.path.exists(logo_path):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                filename=logo_path, width=100, height=100, preserve_aspect_ratio=True)
            logo_image = Gtk.Image.new_from_pixbuf(pixbuf)
            logo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            logo_box.pack_start(logo_image, True, True, 0)
            main_box.pack_start(logo_box, False, False, 10)
        
        welcome_label = Gtk.Label()
        welcome_label.set_markup(
            "<span size='x-large' weight='bold'>¡Bienvenido a Soplos Linux 1.0 (Tyron)!</span>\n\n"
            "<span size='large'>Gracias por escoger nuestra distribución. Esta herramienta te ayudará a configurar tu sistema.</span>"
        )
        welcome_label.set_justify(Gtk.Justification.CENTER)
        welcome_label.set_line_wrap(True)
        main_box.pack_start(welcome_label, False, False, 10)
        
        self.autostart_check = Gtk.CheckButton(label="Ejecutar al inicio")
        self.autostart_check.set_active(self.is_autostart_enabled())
        self.autostart_check.connect("toggled", self.toggle_autostart)
        main_box.pack_start(self.autostart_check, False, False, 5)
        
        # Crear notebook (pestañas)
        notebook = Gtk.Notebook()
        main_box.pack_start(notebook, True, True, 0)
        
        # --- PESTAÑA 1: CENTRO DE SOFTWARE ---
        software_frame = self.create_software_frame()
        software_label = Gtk.Label(label="Centro de Software")
        notebook.append_page(software_frame, software_label)
        
        # --- PESTAÑA 2: CENTRO DE CONTROLADORES ---
        drivers_frame = self.create_drivers_frame()
        drivers_label = Gtk.Label(label="Centro de Controladores")
        notebook.append_page(drivers_frame, drivers_label)
        
        # --- PESTAÑA 3: PERSONALIZACIÓN ---
        customization_frame = self.create_customization_frame()
        customization_label = Gtk.Label(label="Personalización")
        notebook.append_page(customization_frame, customization_label)
        
        # Barra de progreso y etiqueta para mostrar detalles
        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        main_box.pack_start(progress_box, False, False, 10)
        
        self.progress_bar = Gtk.ProgressBar()
        progress_box.pack_start(self.progress_bar, False, False, 0)
        
        self.status_label = Gtk.Label()
        self.status_label.set_text("")
        self.status_label.set_line_wrap(True)
        progress_box.pack_start(self.status_label, False, False, 0)
        
        exit_button = Gtk.Button(label="Salir")
        exit_button.connect("clicked", self.on_exit_clicked)
        main_box.pack_end(exit_button, False, False, 10)
        
        # Variable para almacenar el hilo de ejecución actual
        self.current_process = None
        self.command_running = False
    
    def create_customization_frame(self):
        """Crea el frame de personalización"""
        customization_frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        customization_frame.set_border_width(10)
        
        panel_button = Gtk.Button(label="Cambiar paneles")
        panel_button.connect("clicked", self.on_panel_clicked)
        customization_frame.pack_start(panel_button, False, False, 5)
        
        dock_button = Gtk.Button(label="Organizar Docklike")
        dock_button.connect("clicked", self.on_dock_clicked)
        customization_frame.pack_start(dock_button, False, False, 5)
        
        wallpaper_button = Gtk.Button(label="Cambiar Fondo")
        wallpaper_button.connect("clicked", self.on_wallpaper_clicked)
        customization_frame.pack_start(wallpaper_button, False, False, 5)
        
        # Nuevos botones añadidos
        grub_button = Gtk.Button(label="Personalizar GRUB")
        grub_button.connect("clicked", self.on_grub_clicked)
        customization_frame.pack_start(grub_button, False, False, 5)
        
        plymouth_button = Gtk.Button(label="Personalizar Plymouth")
        plymouth_button.connect("clicked", self.on_plymouth_clicked)
        customization_frame.pack_start(plymouth_button, False, False, 5)
        
        # Añadir separador
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        customization_frame.pack_start(separator, False, False, 5)
        
        # Sección para kernel Liquorix
        kernel_label = Gtk.Label()
        kernel_label.set_markup("<span weight='bold'>Kernel Liquorix</span>")
        kernel_label.set_halign(Gtk.Align.START)
        customization_frame.pack_start(kernel_label, False, False, 5)
        
        # Corregido: Usar keyword 'label' en lugar de argumento posicional
        kernel_desc_label = Gtk.Label(label="Instala el kernel de alto rendimiento Liquorix, optimizado para juegos y trabajo multimedia.")
        kernel_desc_label.set_line_wrap(True)
        kernel_desc_label.set_xalign(0)
        kernel_desc_label.set_max_width_chars(40)
        customization_frame.pack_start(kernel_desc_label, False, False, 5)
        
        # Crear caja para botones de kernel
        kernel_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        customization_frame.pack_start(kernel_buttons_box, False, False, 5)
        
        # Botones para el kernel Liquorix
        install_curl_button = Gtk.Button(label="Instalar curl")
        install_curl_button.connect("clicked", self.on_install_curl_clicked)
        kernel_buttons_box.pack_start(install_curl_button, True, True, 0)
        
        install_liquorix_button = Gtk.Button(label="Instalar Kernel Liquorix")
        install_liquorix_button.connect("clicked", self.on_install_liquorix_clicked)
        kernel_buttons_box.pack_start(install_liquorix_button, True, True, 0)
        
        return customization_frame
    
    # Añadir métodos para los nuevos botones
    def on_grub_clicked(self, widget):
        """Manejador para ejecutar grub-customizer"""
        subprocess.Popen(["grub-customizer"])
    
    def on_plymouth_clicked(self, widget):
        """Manejador para ejecutar el programa de Plymouth"""
        subprocess.Popen(["python3", "/usr/local/bin/plymouth/plymouth.py"])
    
    def create_software_frame(self):
        """Crea el frame del centro de software"""
        software_main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        software_main_box.set_border_width(10)
        
        # Botones para actualizar repositorios y sistema (horizontales)
        update_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        software_main_box.pack_start(update_buttons_box, False, False, 5)
        
        update_button = Gtk.Button(label="Actualizar repositorios")
        update_button.connect("clicked", self.on_update_repos_clicked)
        update_buttons_box.pack_start(update_button, True, True, 0)
        
        upgrade_button = Gtk.Button(label="Actualizar sistema")
        upgrade_button.connect("clicked", self.on_upgrade_system_clicked)
        update_buttons_box.pack_start(upgrade_button, True, True, 0)
        
        # Grid para las opciones de software
        software_box = Gtk.Grid()
        software_box.set_row_spacing(10)
        software_box.set_column_spacing(10)
        software_main_box.pack_start(software_box, False, False, 10)
        
        software_options = [
            ("Synaptic", "synaptic"),
            ("Gdebi", "gdebi gdebi-core"),
            ("Gnome Software", "gnome-software"),
            ("Flatpak", "flatpak gnome-software-plugin-flatpak"),
            ("Snap", "snapd gnome-software-plugin-snap")
        ]
        
        for i, (label, package) in enumerate(software_options):
            lbl = Gtk.Label(label=label, xalign=0)
            software_box.attach(lbl, 0, i, 1, 1)
            install_button = Gtk.Button(label="Instalar")
            install_button.connect("clicked", self.on_install_clicked, package)
            software_box.attach(install_button, 1, i, 1, 1)
            uninstall_button = Gtk.Button(label="Desinstalar")
            uninstall_button.connect("clicked", self.on_uninstall_clicked, package)
            software_box.attach(uninstall_button, 2, i, 1, 1)
        
        # Contenedor horizontal para los botones de Flathub y Snap
        repo_buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        software_main_box.pack_start(repo_buttons_box, False, False, 5)
        
        # Añadir los botones uno al lado del otro
        flathub_button = Gtk.Button(label="Agregar Flathub")
        flathub_button.connect("clicked", self.on_add_flathub_clicked)
        repo_buttons_box.pack_start(flathub_button, True, True, 0)
        
        snap_button = Gtk.Button(label="Habilitar Snap")
        snap_button.connect("clicked", self.on_enable_snap_clicked)
        repo_buttons_box.pack_start(snap_button, True, True, 0)
        
        # Botón para limpiar el sistema
        clean_button = Gtk.Button(label="Limpiar sistema")
        clean_button.connect("clicked", self.on_clean_system_clicked)
        software_main_box.pack_start(clean_button, False, False, 5)
        
        return software_main_box
    
    def create_drivers_frame(self):
        """Crea el frame del centro de controladores con scroll"""
        # Crear un ScrolledWindow para permitir el scroll
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_min_content_height(400)  # Altura mínima para asegurar que se ve correctamente
        
        # Contenedor principal para los controladores
        drivers_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        drivers_box.set_border_width(10)
        
        # Añadir el contenedor al ScrolledWindow
        scrolled_window.add(drivers_box)
        
        # Etiqueta informativa
        info_label = Gtk.Label()
        info_label.set_markup("<span weight='bold'>Controladores disponibles</span>")
        info_label.set_halign(Gtk.Align.START)
        drivers_box.pack_start(info_label, False, False, 5)
        
        # Descripción - Corregido: Usar keyword 'label' en lugar de argumento posicional
        desc_label = Gtk.Label(label="Instala controladores privativos para tu hardware para un mejor rendimiento.")
        desc_label.set_line_wrap(True)
        desc_label.set_xalign(0)
        desc_label.set_max_width_chars(40)
        drivers_box.pack_start(desc_label, False, False, 5)
        
        # --- NVIDIA ---
        nvidia_label = Gtk.Label()
        nvidia_label.set_markup("<span weight='bold'>Controladores NVIDIA</span>")
        nvidia_label.set_halign(Gtk.Align.START)
        drivers_box.pack_start(nvidia_label, False, False, 5)
        
        # Caja para botones NVIDIA
        nvidia_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        drivers_box.pack_start(nvidia_box, False, False, 5)
        
        # Botones para NVIDIA
        nvidia_latest = Gtk.Button(label="NVIDIA (último)")
        nvidia_latest.connect("clicked", self.on_driver_clicked, "nvidia-driver")
        nvidia_box.pack_start(nvidia_latest, True, True, 0)
        
        nvidia_legacy = Gtk.Button(label="NVIDIA (legacy)")
        nvidia_legacy.connect("clicked", self.on_driver_clicked, "nvidia-driver-470")
        nvidia_box.pack_start(nvidia_legacy, True, True, 0)
        
        # Separador
        drivers_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 5)
        
        # --- AMD ---
        amd_label = Gtk.Label()
        amd_label.set_markup("<span weight='bold'>Controladores AMD</span>")
        amd_label.set_halign(Gtk.Align.START)
        drivers_box.pack_start(amd_label, False, False, 5)
        
        amd_button = Gtk.Button(label="Instalar controladores AMD")
        amd_button.connect("clicked", self.on_driver_clicked, "firmware-amd-graphics libgl1-mesa-dri libglx-mesa0 mesa-vulkan-drivers xserver-xorg-video-all")
        drivers_box.pack_start(amd_button, False, False, 5)
        
        # Separador
        drivers_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 5)
        
        # --- Wi-Fi ---
        wifi_label = Gtk.Label()
        wifi_label.set_markup("<span weight='bold'>Controladores Wi-Fi</span>")
        wifi_label.set_halign(Gtk.Align.START)
        drivers_box.pack_start(wifi_label, False, False, 5)
        
        # Caja para botones Wi-Fi
        wifi_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        drivers_box.pack_start(wifi_box, False, False, 5)
        
        # Botones para controladores Wi-Fi
        intel_wifi = Gtk.Button(label="Intel")
        intel_wifi.connect("clicked", self.on_driver_clicked, "firmware-iwlwifi")
        wifi_box.pack_start(intel_wifi, True, True, 0)
        
        realtek_wifi = Gtk.Button(label="Realtek")
        realtek_wifi.connect("clicked", self.on_driver_clicked, "firmware-realtek")
        wifi_box.pack_start(realtek_wifi, True, True, 0)
        
        broadcom_wifi = Gtk.Button(label="Broadcom")
        broadcom_wifi.connect("clicked", self.on_driver_clicked, "firmware-b43-installer")
        wifi_box.pack_start(broadcom_wifi, True, True, 0)
        
        # Separador
        drivers_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 5)
        
        # --- Otros controladores ---
        other_label = Gtk.Label()
        other_label.set_markup("<span weight='bold'>Otros controladores</span>")
        other_label.set_halign(Gtk.Align.START)
        drivers_box.pack_start(other_label, False, False, 5)
        
        # Caja para otros controladores
        other_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        drivers_box.pack_start(other_box, False, False, 5)
        
        # Botones para otros controladores
        printer_button = Gtk.Button(label="Impresora")
        printer_button.connect("clicked", self.on_driver_clicked, "printer-driver-all")
        other_box.pack_start(printer_button, True, True, 0)
        
        bluetooth_button = Gtk.Button(label="Bluetooth")
        bluetooth_button.connect("clicked", self.on_driver_clicked, "bluetooth bluez bluez-tools")
        other_box.pack_start(bluetooth_button, True, True, 0)
        
        # Botón para escanear hardware (versión simple)
        scan_button = Gtk.Button(label="Escanear hardware")
        scan_button.connect("clicked", self.on_scan_hardware_simple)
        drivers_box.pack_start(scan_button, False, False, 10)
        
        # Devolver el ScrolledWindow que contiene todos los elementos
        return scrolled_window
    
    def on_driver_clicked(self, button, package):
        """Manejador para instalar un controlador"""
        self.run_command(f"pkexec apt install -y {package}")
    
    def on_scan_hardware_simple(self, button):
        """Versión simplificada del escaneo de hardware"""
        self.status_label.set_text("Escaneando hardware...")
        self.progress_bar.set_fraction(0.2)
        
        # Ejecutar el escaneo en un hilo separado
        def scan_thread():
            try:
                # Ejecutar comandos para detectar hardware
                gpu_cmd = "lspci | grep -i 'vga\\|3d\\|display'"
                wifi_cmd = "lspci | grep -i 'network\\|wireless'"
                
                gpu_output = subprocess.check_output(gpu_cmd, shell=True).decode('utf-8')
                wifi_output = subprocess.check_output(wifi_cmd, shell=True).decode('utf-8')
                
                # Detectar tipo de GPU
                gpu_type = "Genérica"
                if "nvidia" in gpu_output.lower():
                    gpu_type = "NVIDIA"
                elif "amd" in gpu_output.lower() or "radeon" in gpu_output.lower():
                    gpu_type = "AMD/ATI"
                elif "intel" in gpu_output.lower():
                    gpu_type = "Intel"
                
                # Detectar tipo de Wi-Fi
                wifi_type = []
                if "intel" in wifi_output.lower():
                    wifi_type.append("Intel")
                if "realtek" in wifi_output.lower():
                    wifi_type.append("Realtek")
                if "broadcom" in wifi_output.lower():
                    wifi_type.append("Broadcom")
                
                wifi_str = ", ".join(wifi_type) if wifi_type else "No detectado"
                
                # Actualizar la UI desde el hilo principal
                GLib.idle_add(self.update_hardware_info, gpu_type, wifi_str)
                
            except Exception as e:
                GLib.idle_add(self.status_label.set_text, f"Error en el escaneo: {str(e)}")
                GLib.idle_add(self.progress_bar.set_fraction, 0.0)
        
        # Iniciar el hilo
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def update_hardware_info(self, gpu_type, wifi_type):
        """Actualiza la información del hardware detectado"""
        message = f"Hardware detectado: GPU {gpu_type}, Wi-Fi {wifi_type}"
        self.status_label.set_text(message)
        self.progress_bar.set_fraction(0.0)
        
        # Mostrar un diálogo con la información
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Resultado del escaneo de hardware"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def is_autostart_enabled(self):
        return os.path.exists(os.path.expanduser("~/.config/autostart/soplos-welcome.desktop"))
    
    def toggle_autostart(self, widget):
        autostart_path = os.path.expanduser("~/.config/autostart/soplos-welcome.desktop")
        if widget.get_active():
            os.makedirs(os.path.dirname(autostart_path), exist_ok=True)
            with open(autostart_path, "w") as f:
                f.write("""[Desktop Entry]\nType=Application\nExec=python3 /usr/local/bin/welcome/welcome.py\nHidden=false\nNoDisplay=false\nX-GNOME-Autostart-enabled=true\nName=Soplos Welcome\nComment=Bienvenida de Soplos Linux""")
        else:
            if os.path.exists(autostart_path):
                os.remove(autostart_path)
    
    def on_panel_clicked(self, widget):
        # Usar la versión original que funciona
        subprocess.Popen(["python3", "/usr/local/bin/soplos-theme-manager/soplos-theme-manager.py"])
    
    def on_dock_clicked(self, widget):
        # Usar la versión original que funciona
        subprocess.Popen(["python3", "/usr/local/bin/docklike/docklike.py"])
    
    def on_wallpaper_clicked(self, widget):
        # Usar la versión original que funciona
        subprocess.Popen(["xfdesktop-settings"])
    
    def on_install_curl_clicked(self, widget):
        self.run_command("pkexec apt install -y curl")
    
    def on_install_liquorix_clicked(self, widget):
        # Crear un script temporal para ejecutar el comando
        script_content = """#!/bin/bash
curl -s 'https://liquorix.net/install-liquorix.sh' | bash
"""
        script_path = "/tmp/install-liquorix.sh"
        with open(script_path, "w") as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        
        # Ejecutar el script con permisos de administrador
        self.run_command(f"pkexec {script_path}")
    
    def on_install_clicked(self, widget, package):
        # Verificar si se está instalando GNOME Software
        if "gnome-software" in package and "gnome-software-plugin" not in package:
            self.run_command(f"pkexec apt install -y {package} && gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'")
        else:
            self.run_command(f"pkexec apt install -y {package}")
    
    def on_uninstall_clicked(self, widget, package):
        self.run_command(f"pkexec apt remove -y {package}")
    
    def on_add_flathub_clicked(self, widget):
        self.run_command("flatpak remote-add --if-not-exists --user flathub https://dl.flathub.org/repo/flathub.flatpakrepo")
    
    def on_enable_snap_clicked(self, widget):
        # Modificado para incluir los comandos adicionales después de instalar snap
        script_content = """#!/bin/bash
pkexec snap install snapd && \
mkdir -p ~/.local/share/applications && \
ln -sf /var/lib/snapd/desktop/applications/* ~/.local/share/applications/ && \
xfce4-panel -r
"""
        script_path = "/tmp/enable-snap.sh"
        with open(script_path, "w") as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        
        # Ejecutar el script
        self.run_command(script_path)
    
    def on_update_repos_clicked(self, widget):
        self.run_command("pkexec apt update")
    
    def on_upgrade_system_clicked(self, widget):
        self.run_command("pkexec apt dist-upgrade -y")
    
    def on_clean_system_clicked(self, widget):
        self.run_command("pkexec apt autoremove -y")
    
    def on_exit_clicked(self, widget):
        Gtk.main_quit()
    
    def run_command(self, command):
        # Si ya hay un comando ejecutándose, no hacer nada
        if self.command_running:
            return
            
        self.command_running = True
        
        def execute_command():
            try:
                # Preparar el comando para capturar la salida
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
                
                self.current_process = process
                
                # Patrones para detectar progreso
                progress_patterns = {
                    'apt': {
                        'total_packages': 0,
                        'current_package': 0,
                        'pattern': r'(\d+)%|Get:(\d+)',
                        'extracting_pattern': r'Extracting templates from packages: (\d+)%',
                        'unpacking_pattern': r'Unpacking .*? \((\d+)',
                        'setting_up_pattern': r'Setting up .*? \((\d+)'
                    }
                }
                
                # Detectar tipo de comando
                command_type = None
                if 'apt' in command:
                    command_type = 'apt'
                
                # Inicializar variables para seguimiento de progreso
                progress = 0.0
                last_line = ""
                
                # Leer la salida línea por línea
                for line in iter(process.stdout.readline, ''):
                    if not line.strip():
                        continue
                    
                    last_line = line.strip()
                    GLib.idle_add(self.status_label.set_text, last_line)
                    
                    # Actualizar progreso basado en patrones reconocidos
                    if command_type == 'apt':
                        # Buscar patrones de porcentaje en la salida
                        percent_match = re.search(r'(\d+)%', line)
                        if percent_match:
                            progress = float(percent_match.group(1)) / 100.0
                            GLib.idle_add(self.progress_bar.set_fraction, progress)
                            continue
                        
                        # Buscar patrones de desempaquetado/configuración
                        if "Unpacking" in line or "Setting up" in line:
                            progress = min(progress + 0.05, 0.95)  # Incrementar progreso, max 95%
                            GLib.idle_add(self.progress_bar.set_fraction, progress)
                    
                # Esperar a que el proceso termine
                process.wait()
                
                # Finalizar con el 100% de progreso
                GLib.idle_add(self.progress_bar.set_fraction, 1.0)
                GLib.idle_add(self.status_label.set_text, "¡Completado!")
                
                # Esperar un momento y luego limpiar
                time.sleep(1)
                GLib.idle_add(self.progress_bar.set_fraction, 0.0)
                GLib.idle_add(self.status_label.set_text, "")
                
                self.current_process = None
                self.command_running = False
                
            except Exception as e:
                GLib.idle_add(self.status_label.set_text, f"Error: {str(e)}")
                GLib.idle_add(self.progress_bar.set_fraction, 0.0)
                self.current_process = None
                self.command_running = False
        
        # Iniciar el hilo para ejecutar el comando
        threading.Thread(target=execute_command, daemon=True).start()

if __name__ == "__main__":
    app = SoplosWelcomeApp()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()
