#!/bin/bash

clear

if sudo -v >/dev/null 2>&1; then
    SUDOCMD="sudo"
else
    SUDOCMD=""
fi

echo -e "                                  
\033[0;36m_____\033[0m                           
\033[0;36m|_   _|___ ___ \033[0m___ ___ ___ _____ 
\033[0;36m  | | | -_| .'\033[0m| . |  _| .'|     |
\033[0;36m  |_| |___|__,\033[0m|_  |_| |__,|_|_|_|
\033[0;36m              \033[0m|___|              
"

LOG_FILE="install.log"
echo "[INFO] Starting installation" > "$LOG_FILE"
echo "[DEBUG] SUDOCMD: $SUDOCMD" >> "$LOG_FILE"

if [[ "$teagram" == "reset" ]]; then
    echo "[INFO] Resetting teagram..." >> "$LOG_FILE"
    eval "$SUDOCMD apt purge -y python3"
fi

if command -v python3.11 &>/dev/null; then
    PYTHON="python3.11"
elif command -v python3.10 &>/dev/null; then
    PYTHON="python3.10"
elif command -v python3.9 &>/dev/null; then
    PYTHON="python3.9"
else
    echo "[ERROR] Python 3.11, 3.10, or 3.9 not found. See logs for more information."
    exit 1
fi

echo "[INFO] Using Python: $PYTHON" >> "$LOG_FILE"

if [[ "$OSTYPE" == *linux-gnu* ]]; then
    echo "[INFO] Found OS type: GNU/Linux ($OSTYPE)" >> "$LOG_FILE"
    PKGINSTALL="apt install -y"
    UPD="apt update && apt upgrade -y"
elif [[ "$OSTYPE" == *linux-android* ]]; then
    echo "[INFO] Found OS type: Android ($OSTYPE)" >> "$LOG_FILE"
    PKGINSTALL="pkg install -y"
    UPD="pkg upgrade -y"
elif [[ -f /etc/fedora-release ]]; then
    echo "[INFO] Found OS type: Fedora" >> "$LOG_FILE"
    PKGINSTALL="dnf install -y"
    UPD="dnf upgrade -y"
elif [[ -f /etc/arch-release ]]; then
    echo "[INFO] Found OS type: Arch Linux" >> "$LOG_FILE"
    PKGINSTALL="pacman -S --noconfirm"
    UPD="pacman -Syu --noconfirm"
elif [[ -f /etc/gentoo-release ]]; then
    echo "[INFO] Found OS type: Gentoo" >> "$LOG_FILE"
    PKGINSTALL="emerge -u"
    UPD="emerge --sync && emerge -uDN @world"
elif [[ -f /etc/nixos/configuration.nix ]]; then
    echo "[INFO] Found OS type: NixOS" >> "$LOG_FILE"
    PKGINSTALL="nix-env -i"
    UPD="nix-channel --update && nix-env -u '*'"
else
    echo "[ERROR] OS type not found: $OSTYPE" >> "$LOG_FILE"
    echo "[ERROR] OS not found. See logs for more information."
    exit 1
fi

echo "[INFO] Updating and upgrading all packages..." >> "$LOG_FILE"
echo "[INFO] Updating..."
eval "$SUDOCMD $UPD"
echo "[INFO] Installing 4 packages..." >> "$LOG_FILE"
echo "[INFO] Installing packages..."
eval "$SUDOCMD $PKGINSTALL git openssl python python3-pip"
echo "[INFO] Installing requirements.txt..." >> "$LOG_FILE"
echo "[INFO] Installing libraries..."
pip3 install -r requirements.txt
echo "[INFO] First start teagram..." >> "$LOG_FILE"
echo "[INFO] First start..."
clear
$PYTHON -m teagram
