#!/usr/bin/env python3
import gi
import subprocess

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

class SoplosThemeManager(Gtk.Window):
    def __init__(self):
        super().__init__(title="Soplos Theme Manager")
        self.set_default_size(200, 300)
        self.set_icon_from_file("/usr/share/branding-soplos/plymouth-logo.png")

        # Aplicar tema oscuro
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)

        # Contenedor principal
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_valign(Gtk.Align.CENTER)
        vbox.set_halign(Gtk.Align.CENTER)
        self.add(vbox)

        # Etiqueta
        label = Gtk.Label(label="¿Qué quieres hacer?")
        label.set_xalign(0.5)  # Centrar el texto
        vbox.pack_start(label, False, False, 5)

        # Lista de botones con iconos
        buttons = [
            ("Crear Nuevo Tema", "document-new", self.create_theme),
            ("Eliminar Tema", "edit-delete", self.remove_theme),
            ("Cambiar Tema", "preferences-desktop-theme", self.theme_selector),
            ("Salir", "application-exit", self.close_app)
        ]

        for text, icon_name, callback in buttons:
            button = Gtk.Button()
            button.set_size_request(200, 50)  # Ajustar el tamaño del botón

            # Caja para organizar el icono y el texto
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            hbox.set_halign(Gtk.Align.CENTER)  # Centrar contenido horizontalmente

            icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
            label = Gtk.Label(label=text)

            hbox.pack_start(icon, False, False, 0)
            hbox.pack_start(label, False, False, 0)

            button.add(hbox)
            button.connect("clicked", callback)
            vbox.pack_start(button, False, False, 0)

        self.connect("destroy", Gtk.main_quit)

    def create_theme(self, widget):
        subprocess.run(["/usr/local/bin/soplos-theme-manager/create_theme"])

    def remove_theme(self, widget):
        subprocess.run(["/usr/local/bin/soplos-theme-manager/remove_theme"])

    def theme_selector(self, widget):
        subprocess.run(["/usr/local/bin/soplos-theme-manager/themeselector"])

    def close_app(self, widget):
        self.close()

if __name__ == "__main__":
    app = SoplosThemeManager()
    app.show_all()
    Gtk.main()
