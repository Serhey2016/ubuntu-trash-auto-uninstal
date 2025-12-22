#!/usr/bin/env python3
import gi
import sys
import os
import subprocess
import urllib.parse
import re

import threading
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio, GLib

class UninstallTrash(Gtk.Window):
    def __init__(self):
        super().__init__(title="Uninstall Trash")
        self.set_default_size(200, 200)
        self.set_keep_above(True)  # Keep window on top
        self.set_position(Gtk.WindowPosition.CENTER)

        # Main layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(20)
        vbox.set_margin_bottom(20)
        vbox.set_margin_start(20)
        vbox.set_margin_end(20)
        self.add(vbox)

        # Icon
        icon_theme = Gtk.IconTheme.get_default()
        try:
            icon = icon_theme.load_icon("user-trash", 64, 0)
            image = Gtk.Image.new_from_pixbuf(icon)
        except:
            image = Gtk.Image.new_from_icon_name("user-trash", Gtk.IconSize.DIALOG)
        
        vbox.pack_start(image, True, True, 0)

        # Label
        label = Gtk.Label(label="Drag App Here\nto Uninstall")
        label.set_justify(Gtk.Justification.CENTER)
        vbox.pack_start(label, False, False, 0)

        # Update styling
        self.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.95, 0.95, 0.95, 1))

        # Drag and Drop setup
        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.drag_dest_add_uri_targets()
        self.connect("drag-data-received", self.on_drag_data_received)

    def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        uris = data.get_uris()
        if not uris:
            Gtk.drag_finish(drag_context, False, False, time)
            return

        for uri in uris:
            file_path = urllib.parse.unquote(uri).replace('file://', '')
            if file_path.endswith('.desktop'):
                self.process_desktop_file(file_path)
        
        Gtk.drag_finish(drag_context, True, False, time)

    def process_desktop_file(self, file_path):
        try:
            # 1. Parse .desktop file to find Exec
            exec_cmd = None
            with open(file_path, 'r') as f:
                for line in f:
                    if line.startswith('Exec='):
                        # Extract the command (take first word)
                        cmd = line.split('=')[1].strip()
                        # Remove % codes and quotes
                        cmd = re.sub(r'%.*', '', cmd).strip()
                        cmd = cmd.replace('"', '').replace("'", "")
                        exec_cmd = cmd.split()[0] # Take first token
                        break
            
            if not exec_cmd:
                self.show_error(f"Could not find Exec command in {os.path.basename(file_path)}")
                return

            # 2. Find full path of executable
            full_path = self.get_full_path(exec_cmd)
            if not full_path:
                 # Try assuming it is in /usr/bin if just a name
                 if not os.path.dirname(exec_cmd):
                     full_path = os.path.join('/usr/bin', exec_cmd)
                 else:
                     self.show_error(f"Could not find executable: {exec_cmd}")
                     return

            # 3. Find package name
            package = self.get_package_owner(full_path)
            pkg_type = 'apt'
            
            if not package:
                # Try finding via snap
                if "snap" in full_path or "/snap/" in full_path:
                    pkg_type = 'snap'
                    # Extract snap name from path logic...
                    parts = full_path.split('/')
                    if 'bin' in parts and parts.index('bin') > 0 and parts[parts.index('bin')-1] == 'snap':
                         package = parts[parts.index('bin')+1]
                    elif 'snap' in parts:
                         try:
                             snap_index = parts.index('snap')
                             if len(parts) > snap_index + 1:
                                 package = parts[snap_index + 1]
                         except:
                             pass
                    if not package:
                         package = os.path.basename(full_path)

                # Try finding via flatpak
                elif "flatpak" in full_path or "flatpak" in file_path:
                    # Flatpak desktop files are usually named org.app.Name.desktop
                    # and the package ID is org.app.Name
                    pkg_type = 'flatpak'
                    package = os.path.basename(file_path).replace('.desktop', '')
                
                if not package:
                    self.show_error(f"Could not find package for: {full_path}")
                    return

            # 4. Confirm and Uninstall
            self.confirm_and_uninstall(package, os.path.basename(file_path), pkg_type)

        except Exception as e:
            self.show_error(str(e))

    def get_full_path(self, cmd):
        # Using `which` to find path
        try:
            return subprocess.check_output(['which', cmd]).decode().strip()
        except:
            return None

    def get_package_owner(self, path):
        # Using dpkg -S
        try:
            output = subprocess.check_output(['dpkg', '-S', path], stderr=subprocess.DEVNULL).decode().strip()
            # Output format: "package: /path/to/file"
            if ':' in output:
                return output.split(':')[0]
        except:
            return None
        return None

    def confirm_and_uninstall(self, package, app_name, pkg_type='apt'):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Uninstall {package}?",
        )
        msg = f"This will remove the application '{app_name}' (package: {package}).\n"
        if pkg_type == 'snap':
             msg += "Type: Snap Package"
        elif pkg_type == 'flatpak':
             msg += "Type: Flatpak Package"
        else:
             msg += "Type: System Package (APT)"
        
        dialog.format_secondary_text(msg)
        
        # Ensure dialog is on top and centered
        dialog.set_keep_above(True)
        dialog.set_modal(True)
        dialog.set_position(Gtk.WindowPosition.CENTER)
        dialog.present()
        
        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.YES:
            self.run_uninstall(package, pkg_type)

    def run_uninstall(self, package, pkg_type):
        # Create a progress window
        self.progress_win = Gtk.Window(title="Uninstalling...")
        self.progress_win.set_transient_for(self)
        self.progress_win.set_keep_above(True)
        self.progress_win.set_modal(True)
        self.progress_win.set_default_size(300, 100)
        self.progress_win.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        vbox.set_margin_top(20)
        vbox.set_margin_bottom(20)
        vbox.set_margin_start(20)
        vbox.set_margin_end(20)
        self.progress_win.add(vbox)
        
        label = Gtk.Label(label=f"Uninstalling {package}...\nThis may take a minute.")
        label.set_justify(Gtk.Justification.CENTER)
        vbox.pack_start(label, True, True, 0)
        
        spinner = Gtk.Spinner()
        spinner.start()
        vbox.pack_start(spinner, True, True, 0)
        
        self.progress_win.show_all()
        
        # Run uninstallation in a separate thread so UI doesn't freeze
        thread = threading.Thread(target=self._uninstall_thread, args=(package, pkg_type))
        thread.daemon = True
        thread.start()

    def _uninstall_thread(self, package, pkg_type):
        # Chain commands
        if pkg_type == 'snap':
            cmd = ['pkexec', 'snap', 'remove', package]
        elif pkg_type == 'flatpak':
            cmd = ['pkexec', 'flatpak', 'uninstall', package, '-y']
        else:
            cmd = ['pkexec', 'sh', '-c', f'apt purge {package} -y && apt autoremove -y']
        
        try:
            subprocess.check_call(cmd)
            GLib.idle_add(self._on_uninstall_success)
        except subprocess.CalledProcessError:
            GLib.idle_add(self._on_uninstall_error)

    def _on_uninstall_success(self):
        if hasattr(self, 'progress_win'):
            self.progress_win.destroy()
        
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Uninstallation Complete",
        )
        dialog.set_keep_above(True)
        dialog.present()
        dialog.run()
        dialog.destroy()
        # If we are in CLI mode (main window hidden), we might want to quit
        if not self.get_visible():
            Gtk.main_quit()

    def _on_uninstall_error(self):
        if hasattr(self, 'progress_win'):
            self.progress_win.destroy()
        self.show_error("Uninstallation failed or was cancelled.")
        if not self.get_visible():
            Gtk.main_quit()

    def show_error(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error",
        )
        dialog.format_secondary_text(message)
        dialog.set_keep_above(True)
        dialog.present()
        dialog.run()
        dialog.destroy()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line mode (called from extension)
        target = sys.argv[1]
        app = UninstallTrash()
        # We need to init Gtk but not show the window
        # app.show_all() is NOT called
        
        # If it looks like a full path (from file manager drag), keep as is
        # If it looks like an ID (from Shell), try to find it
        if not os.path.exists(target) and not target.startswith('/'):
             # Try to find standard desktop file locations
             candidates = [
                 os.path.join('/usr/share/applications', target),
                 os.path.join(os.path.expanduser('~/.local/share/applications'), target),
                 os.path.join('/var/lib/snapd/desktop/applications', target)
             ]
             for c in candidates:
                 if os.path.exists(c):
                     target = c
                     break
        
        if target.endswith('.desktop'):
            app.process_desktop_file(target)
        else:
            print("Invalid target")
        
        # Keep Gtk loop running until dialogs are closed
        # We can hack this by checking if any windows are left? 
        # Or simpler: The process_desktop_file calls dialogs.
        Gtk.main()
    else:
        # Window mode
        win = UninstallTrash()
        win.connect("destroy", Gtk.main_quit)
        win.show_all()
        Gtk.main()
