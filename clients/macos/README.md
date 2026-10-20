# PwnForge for macOS

PwnForge for macOS is a small native app that opens your PwnForge server in a persistent WebKit window and guides you through importing a VPN profile.

## Install

Open `dist/PwnForge-macOS.dmg`, drag **PwnForge** to **Applications**, then launch it. On first launch, enter the PwnForge address supplied by your server admin. It can be an HTTPS address, a LAN address, or a Tailscale address. Sign in normally; the app keeps the website's login session on this Mac.

The app is built for Apple Silicon and Intel Macs. The current downloadable build is ad-hoc signed and not notarized. If macOS blocks it, control-click PwnForge in Applications, choose **Open**, then confirm.

Use HTTPS whenever the server offers it. HTTP does not encrypt your sign-in or website traffic on the local network; reserve it for trusted LANs or a VPN tunnel.

## VPN access

In the app, choose **VPN access**, select the `.ovpn` profile supplied by your PwnForge admin, and choose **Import and open OpenVPN Connect**. PwnForge imports the profile into OpenVPN Connect, then opens that app so you can approve and connect. Return to PwnForge and choose **Check VPN connection**. Once reachable, choose **Use VPN address** to open the site through the tunnel.

The profile is passed directly to OpenVPN Connect and is not saved by PwnForge. OpenVPN Connect's published macOS CLI supports importing profiles, but does not document a command for starting a VPN session; its app therefore asks you to press **Connect**. Complete OpenVPN Connect's first-run consent once before importing profiles.

Set the VPN website address to the private address provided by your admin, for example `http://10.8.0.1:8080`. The website URL and the VPN server address are separate: an `.ovpn` profile does not necessarily contain the address of the PwnForge website.

## Build

Requirements: macOS with Swift 5.9+ command-line tools, `hdiutil`, and `lipo`.

```sh
./clients/macos/build.sh
```

This creates `clients/macos/dist/PwnForge.app`, `clients/macos/dist/PwnForge-macOS.app.zip`, and `clients/macos/dist/PwnForge-macOS.dmg`. The DMG contains an Applications shortcut. To sign and notarize a public release, set `APPLE_SIGN_IDENTITY` to a Developer ID Application identity and configure Apple notarization credentials; the local build intentionally uses ad-hoc signing.
