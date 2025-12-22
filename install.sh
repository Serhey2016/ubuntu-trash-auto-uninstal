#!/bin/bash

# Configuration
UUID="uninstall-trash@antigravity.dev"
EXTENSION_DIR="$HOME/.local/share/gnome-shell/extensions/$UUID"
LOG_DIR="./gnome_extension/$UUID"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Installing Uninstall Trash Extension...${NC}"

# 1. Install Dependencies
echo "Installing python3-gi dependencies..."
if command -v apt &> /dev/null; then
    sudo apt update
    sudo apt install -y python3-gi gir1.2-gtk-3.0 pkexec
else
    echo -e "${RED}Warning: 'apt' not found. Please ensure 'python3-gi', 'gir1.2-gtk-3.0' and 'pkexec' are installed manually.${NC}"
fi

# 2. Create Directory
echo "Creating extension directory..."
rm -rf "$EXTENSION_DIR"
mkdir -p "$EXTENSION_DIR"

# 3. Copy Files
echo "Copying files..."
if [ -d "$LOG_DIR" ]; then
    cp -r "$LOG_DIR"/* "$EXTENSION_DIR/"
    chmod +x "$EXTENSION_DIR/uninstall_trash.py"
else
    echo -e "${RED}Error: Source directory $LOG_DIR not found! Are you running this script from the correct folder?${NC}"
    exit 1
fi

# 4. Enable Extension
echo "Enabling extension..."
gnome-extensions enable "$UUID"

echo -e "${GREEN}Installation Complete!${NC}"
echo "--------------------------------------------------------"
echo "IMPORTANT: You MUST log out and log back in for the extension to appear."
echo "If it doesn't appear automatically, run this command after logging back in:"
echo "   gnome-extensions enable $UUID"
echo "--------------------------------------------------------"
