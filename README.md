# Uninstall Trash for Ubuntu (GNOME)

This extension brings the **"Drag to Trash to Uninstall"** functionality (similar to macOS) to Ubuntu.

You can drag any application icon from your App Grid (Applications Menu) or Dash to the Trash icon in the top panel to uninstall it.

## Features
*   **Drag & Drop:** Drag app icons to the top panel trash icon.
*   **Clean Uninstall:** Uses `apt purge` + `apt autoremove` to completely clean up configuration files and unused dependencies.
*   **Standalone Helper:** Includes a standalone Python script that can also work as a drag-target window.

## Requirements
*   Ubuntu 24.04 (Noble Numbat) or newer (GNOME 46+).
*   Python 3.
*   `pkexec` (usually installed by default).

## Installation

### 1. Download
Clone this repository or download the folder.

### 2. Run Installer
Open your terminal in this folder and run:
```bash
chmod +x install.sh
./install.sh
```

### 3. Log Out & Log In
**Crucial Step:** GNOME Shell needs to reload to see the new extension. You must **Log Out** and **Log In** again (or restart your computer).

### 4. Enable (if needed)
If the trash icon does not appear automatically in the top-right panel after logging in, run:
```bash
gnome-extensions enable uninstall-trash@antigravity.dev
```

## How to Use
1.  Open your Applications Menu (click the 9 dots or Ubuntu logo).
2.  Click and drag any application icon.
3.  Drop it onto the **Trash Icon** in the top-right corner of the screen.
4.  Enter your password when prompted to confirm uninstallation.

---
*Created by Antigravity*
