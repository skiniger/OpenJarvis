#!/bin/zsh
# Build OpenJarvis.app — AppleScript Launcher
# Usage: zsh scripts/build_mac_app.sh

set -e

SCRIPT_DIR="${0:A:h}"
SOURCE="${SCRIPT_DIR}/mac_launcher.scpt"
APP_DIR="${HOME}/Applications"
APP_NAME="OpenJarvis.app"
APP_PATH="${APP_DIR}/${APP_NAME}"

echo "→ Kompiliere AppleScript zu .app ..."
mkdir -p "${APP_DIR}"
osacompile -x -o "${APP_PATH}" "${SOURCE}"

echo "→ App erstellt: ${APP_PATH}"
echo ""
echo "Optionales Icon setzen:"
echo "  1. Erstelle ein 512×512 PNG (z.B. jarvis-icon.png)"
echo "  2. Konvertiere zu ICNS:"
echo "     mkdir iconset.iconset"
echo "     sips -z 16 16   jarvis-icon.png --out iconset.iconset/icon_16x16.png"
echo "     sips -z 32 32   jarvis-icon.png --out iconset.iconset/icon_16x16@2x.png"
echo "     sips -z 32 32   jarvis-icon.png --out iconset.iconset/icon_32x32.png"
echo "     sips -z 64 64   jarvis-icon.png --out iconset.iconset/icon_32x32@2x.png"
echo "     sips -z 128 128 jarvis-icon.png --out iconset.iconset/icon_128x128.png"
echo "     sips -z 256 256 jarvis-icon.png --out iconset.iconset/icon_128x128@2x.png"
echo "     sips -z 256 256 jarvis-icon.png --out iconset.iconset/icon_256x256.png"
echo "     sips -z 512 512 jarvis-icon.png --out iconset.iconset/icon_256x256@2x.png"
echo "     sips -z 512 512 jarvis-icon.png --out iconset.iconset/icon_512x512.png"
echo "     iconutil -c icns iconset.iconset -o jarvis.icns"
echo "     cp jarvis.icns ${APP_PATH}/Contents/Resources/applet.icns"
echo "     touch ${APP_PATH}"
echo ""
echo "Fertig. App liegt in ~/Applications/OpenJarvis.app"
echo "Starten via Doppelklick, Spotlight (Cmd+Space) oder Dock."
