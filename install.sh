#!/bin/bash

clear

if sudo -v >/dev/null 2>&1; then
    SUDOCMD="sudo"
else
    SUDOCMD=""
fi

LOG_FILE="install.log"
echo "[INFO] Starting installation" > "$LOG_FILE"
echo "[DEBUG] SUDOCMD: $SUDOCMD" >> "$LOG_FILE"

if [[ "$teagram" == "reset" ]]; then
    echo "[INFO] Resetting teagram..." >> "$LOG_FILE"
    eval "$SUDOCMD apt purge -y python3"
fi

PYTHON=""
for ver in python3.11 python3.10 python3.9 python 3.8 python3; do
    if command -v "$ver" &>/dev/null; then
        PYTHON="$ver"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "[INFO] Installing 4 packages..." >> "$LOG_FILE"
    echo "[INFO] Installing packages..."
    eval "$SUDOCMD $PKGINSTALL git openssl python3"
else
    ver=$(echo "$($PYTHON --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)" | tr -d '.')
    if [[ -z "$ver" || "$ver" -lt "308" ]]; then
        echo "[ERROR] Your python version must be higher than 3.8" >> "$LOG_FILE"
        echo "[ERROR] Your python version must be higher than 3.8"
        exit 1
    fi

fi

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

if ! command -v curl &>/dev/null; then
    echo "[ERROR] Curl not found." >> "$LOG_FILE"
    echo "[ERROR] Please install curl before installing teagram."
    exit 1
fi

if ! command -v $PYTHON -m pip &>/dev/null; then
    echo "[INFO] Installing get-pip.py" >> "$LOG_FILE"
    echo "[INFO] Installing python3-pip"

    $SUDOCMD curl https://bootstrap.pypa.io/get-pip.py -o __get_pip.py
    
    $PYTHON __get_pip.py
    $SUDOCMD __get_pip.py
fi

read -p "Do you want to update packages? (Y/n): " update_choice
if [[ "${update_choice,,}" == "y" ]]; then
    echo "[INFO] Updating and upgrading all packages..." >> "$LOG_FILE"
    echo "[INFO] Updating..."
    eval "$SUDOCMD $UPD"
else
    echo "[INFO] Skipping package update as per user choice."
fi

echo "[INFO] Installing requirements.txt..." >> "$LOG_FILE"
echo "[INFO] Installing libraries..."

echo "[INFO] Installing teagram..." >> "$LOG_FILE"
echo "[INFO] Installing teagram..."

git clone https://github.com/itzlayz/teagram-tl
cd teagram-tl

$PYTHON -m pip install -U -r requirements.txt

echo "[INFO] First start teagram..." >> "$LOG_FILE"
echo "[INFO] First start..."
clear

$PYTHON -m teagram
