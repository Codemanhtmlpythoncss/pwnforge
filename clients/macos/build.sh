#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CLIENT="$ROOT/clients/macos"
BUILD="$CLIENT/build"
DIST="$CLIENT/dist"
APP="$DIST/PwnForge.app"
SDK="$(xcrun --sdk macosx --show-sdk-path)"
SOURCE="$CLIENT/Sources/PwnForgeApp.swift"

rm -rf "$BUILD" "$APP" "$DIST/PwnForge-macOS.dmg" "$DIST/PwnForge-macOS.app.zip"
mkdir -p "$BUILD" "$DIST" "$APP/Contents/MacOS" "$APP/Contents/Resources"

for ARCH in arm64 x86_64; do
  swiftc \
    -sdk "$SDK" \
    -target "${ARCH}-apple-macosx13.0" \
    -swift-version 5 \
    -parse-as-library \
    -O \
    -framework SwiftUI \
    -framework WebKit \
    -framework AppKit \
    -framework UniformTypeIdentifiers \
    "$SOURCE" \
    -o "$BUILD/PwnForge-$ARCH"
done

lipo -create "$BUILD/PwnForge-arm64" "$BUILD/PwnForge-x86_64" \
  -output "$APP/Contents/MacOS/PwnForge"

cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key><string>en</string>
  <key>CFBundleExecutable</key><string>PwnForge</string>
  <key>CFBundleIdentifier</key><string>com.codemanhtmlpythoncss.pwnforge</string>
  <key>CFBundleInfoDictionaryVersion</key><string>6.0</string>
  <key>CFBundleName</key><string>PwnForge</string>
  <key>CFBundleDisplayName</key><string>PwnForge</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>1.0.0</string>
  <key>CFBundleVersion</key><string>1</string>
  <key>LSMinimumSystemVersion</key><string>13.0</string>
  <key>NSPrincipalClass</key><string>NSApplication</string>
  <key>NSHighResolutionCapable</key><true/>
  <key>NSAppTransportSecurity</key>
  <dict>
    <key>NSAllowsArbitraryLoads</key><true/>
    <key>NSAllowsArbitraryLoadsInWebContent</key><true/>
  </dict>
  <key>CFBundleDocumentTypes</key>
  <array>
    <dict>
      <key>CFBundleTypeName</key><string>OpenVPN profile</string>
      <key>CFBundleTypeRole</key><string>Viewer</string>
      <key>LSHandlerRank</key><string>Alternate</string>
      <key>LSItemContentTypes</key>
      <array><string>net.openvpn.profile</string></array>
      <key>CFBundleTypeExtensions</key>
      <array><string>ovpn</string></array>
    </dict>
  </array>
  <key>UTImportedTypeDeclarations</key>
  <array>
    <dict>
      <key>UTTypeIdentifier</key><string>net.openvpn.profile</string>
      <key>UTTypeDescription</key><string>OpenVPN profile</string>
      <key>UTTypeConformsTo</key><array><string>public.data</string></array>
      <key>UTTypeTagSpecification</key>
      <dict><key>public.filename-extension</key><array><string>ovpn</string></array></dict>
    </dict>
  </array>
</dict>
</plist>
PLIST

codesign --force --deep --sign "${APPLE_SIGN_IDENTITY:--}" --timestamp=none "$APP"
codesign --verify --deep --strict "$APP"
ditto -c -k --keepParent "$APP" "$DIST/PwnForge-macOS.app.zip"

STAGING="$BUILD/dmg-root"
mkdir -p "$STAGING"
cp -R "$APP" "$STAGING/PwnForge.app"
ln -s /Applications "$STAGING/Applications"
hdiutil create \
  -volname "PwnForge" \
  -srcfolder "$STAGING" \
  -ov \
  -format UDZO \
  "$DIST/PwnForge-macOS.dmg"

echo "Built universal app: $APP"
echo "Built app archive: $DIST/PwnForge-macOS.app.zip"
echo "Built DMG: $DIST/PwnForge-macOS.dmg"
