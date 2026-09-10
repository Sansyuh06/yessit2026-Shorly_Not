#!/bin/bash
# Make sure to run `chmod +x` on this file!

set -e

# Sanitize PATH for WSL/Linux environments to strip Windows paths with spaces
# (such as 'Program Files') which cause GNU find -execdir in ImageBuilder to fail.
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

IB_VER="22.03.7"
IB_TARGET="ramips/mt7621"
IB_TARBALL="openwrt-imagebuilder-${IB_VER}-${IB_TARGET/\//-}.Linux-x86_64.tar.xz"
IB_URL="https://downloads.openwrt.org/releases/${IB_VER}/targets/${IB_TARGET}/${IB_TARBALL}"
IB_DIR="${IB_TARBALL%.tar.xz}"

DRY_RUN=0

if [ "$1" = "--dry-run" ]; then
    DRY_RUN=1
    echo "Dry-run mode enabled."
fi

echo "Checking for ImageBuilder..."
if [ ! -d "$IB_DIR" ]; then
    if [ ! -f "$IB_TARBALL" ]; then
        echo "Downloading $IB_TARBALL..."
        wget -q "$IB_URL" || { echo "Error downloading ImageBuilder"; exit 1; }
        wget -q "${IB_URL%/*}/sha256sums" -O sha256sums || { echo "Error downloading sha256sums"; exit 1; }
    fi
    
    echo "Verifying SHA256..."
    grep "$IB_TARBALL" sha256sums | sha256sum -c - || { echo "SHA256 verification failed!"; exit 1; }
    
    echo "Extracting ImageBuilder..."
    tar -xf "$IB_TARBALL" || { echo "Extraction failed!"; exit 1; }
fi

if [ "$DRY_RUN" -eq 1 ]; then
    echo "Dry-run complete. Exiting."
    exit 0
fi

echo "Ensuring file permissions..."
chmod +x files/etc/init.d/* files/usr/bin/* files/etc/uci-defaults/* 2>/dev/null || true

echo "Copying files to ImageBuilder..."
mkdir -p "${IB_DIR}/files"
cp -r files/* "${IB_DIR}/files/" 2>/dev/null || true
chmod +x "${IB_DIR}"/files/etc/init.d/* "${IB_DIR}"/files/usr/bin/* "${IB_DIR}"/files/etc/uci-defaults/* 2>/dev/null || true

echo "Building image..."
cd "$IB_DIR"
mkdir -p staging_dir/host
touch staging_dir/host/.prereq-build
env -i PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" HOME="$HOME" USER="$USER" make image PROFILE="tplink_archer-c6-v3" PACKAGES="nftables" FILES="files" FORCE=1 || { echo "Build failed!"; exit 1; }

SYSUPGRADE_IMG=$(find bin/targets/ -type f -name "*tplink_archer-c6-v3*sysupgrade.bin" | head -n 1)
FACTORY_IMG=$(find bin/targets/ -type f -name "*tplink_archer-c6-v3*factory.bin" | head -n 1)

echo ""
echo "========================================="
echo "Build successful!"
echo "========================================="

if [ -n "$SYSUPGRADE_IMG" ] && [ -f "$SYSUPGRADE_IMG" ]; then
    mkdir -p "${SCRIPT_DIR}/../firmware"
    cp "$SYSUPGRADE_IMG" "${SCRIPT_DIR}/../firmware/"
    echo "[SYSUPGRADE IMAGE] (Use for existing OpenWrt / sysupgrade):"
    echo "  Path   : $SYSUPGRADE_IMG"
    echo "  Copied : firmware/$(basename "$SYSUPGRADE_IMG")"
    echo "  Size   : $(stat -c%s "$SYSUPGRADE_IMG") bytes"
    echo "  SHA256 : $(sha256sum "$SYSUPGRADE_IMG" | awk '{print $1}')"
fi

if [ -n "$FACTORY_IMG" ] && [ -f "$FACTORY_IMG" ]; then
    mkdir -p "${SCRIPT_DIR}/../firmware"
    cp "$FACTORY_IMG" "${SCRIPT_DIR}/../firmware/"
    echo ""
    echo "[FACTORY IMAGE] (Use ONLY when flashing from stock TP-Link web UI):"
    echo "  Path   : $FACTORY_IMG"
    echo "  Copied : firmware/$(basename "$FACTORY_IMG")"
    echo "  Size   : $(stat -c%s "$FACTORY_IMG") bytes"
    echo "  SHA256 : $(sha256sum "$FACTORY_IMG" | awk '{print $1}')"
fi
echo "========================================="
