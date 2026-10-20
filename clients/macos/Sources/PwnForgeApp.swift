import AppKit
import SwiftUI
import UniformTypeIdentifiers
@preconcurrency import WebKit

private enum ForgeStyle {
    static let background = Color(red: 0.035, green: 0.055, blue: 0.09)
    static let surface = Color(red: 0.075, green: 0.10, blue: 0.15)
    static let surfaceRaised = Color(red: 0.095, green: 0.13, blue: 0.19)
    static let border = Color.white.opacity(0.09)
    static let muted = Color(red: 0.60, green: 0.66, blue: 0.76)
    static let lime = Color(red: 0.64, green: 0.95, blue: 0.04)
}

@MainActor
private final class PwnForgeModel: NSObject, ObservableObject, WKScriptMessageHandler, WKUIDelegate, WKNavigationDelegate {
    @Published var websiteAddress = UserDefaults.standard.string(forKey: "pwnforge.website") ?? ""
    @Published var vpnWebsiteAddress = UserDefaults.standard.string(forKey: "pwnforge.vpnWebsite") ?? ""
    @Published var isConfigured = false
    @Published var websiteMessage = "Enter your server address to get started."
    @Published var vpnMessage = "Import the VPN profile from your PwnForge administrator."
    @Published var importedProfileName = ""
    @Published var isCheckingWebsite = false
    @Published var isImportingProfile = false

    let webView: WKWebView

    override init() {
        let contentController = WKUserContentController()
        let clipboardFallback = WKUserScript(
            source: """
            if (location.protocol === 'http:' && !['localhost', '127.0.0.1'].includes(location.hostname)) {
              try {
                Object.defineProperty(navigator, 'clipboard', { configurable: true, value: {
                  writeText: function(value) {
                    return new Promise(function(resolve, reject) {
                      try { window.webkit.messageHandlers.pwnforgeClipboard.postMessage(String(value)); resolve(); }
                      catch (error) { reject(error); }
                    });
                  }
                }});
              } catch (_) {}
            }
            """,
            injectionTime: .atDocumentStart,
            forMainFrameOnly: false
        )
        contentController.addUserScript(clipboardFallback)

        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .default()
        configuration.userContentController = contentController
        webView = WKWebView(frame: .zero, configuration: configuration)
        super.init()
        contentController.add(self, name: "pwnforgeClipboard")
        webView.uiDelegate = self
        webView.navigationDelegate = self

        if let url = makeURL(websiteAddress) {
            isConfigured = true
            webView.load(URLRequest(url: url))
        }
        if vpnWebsiteAddress.isEmpty {
            vpnWebsiteAddress = "http://10.8.0.1:8080"
        }
    }

    func normalizedAddress(_ raw: String) -> String? {
        guard let url = makeURL(raw) else { return nil }
        return url.absoluteString.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
    }

    private func makeURL(_ raw: String) -> URL? {
        let trimmed = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return nil }
        let candidate = trimmed.contains("://") ? trimmed : "http://\(trimmed)"
        guard let url = URL(string: candidate),
              let scheme = url.scheme?.lowercased(), ["http", "https"].contains(scheme),
              let host = url.host, !host.isEmpty else { return nil }
        return url
    }

    @discardableResult
    func saveWebsiteAddress(_ raw: String) -> Bool {
        guard let normalized = normalizedAddress(raw), let url = URL(string: normalized) else {
            websiteMessage = "Enter a valid http:// or https:// server address."
            return false
        }
        websiteAddress = normalized
        UserDefaults.standard.set(normalized, forKey: "pwnforge.website")
        isConfigured = true
        websiteMessage = "Opening PwnForge…"
        webView.load(URLRequest(url: url))
        Task { await checkWebsite(at: normalized, label: "PwnForge server") }
        return true
    }

    func saveVPNWebsiteAddress(_ raw: String) -> Bool {
        guard let normalized = normalizedAddress(raw) else {
            vpnMessage = "Enter a valid private website address, such as http://10.8.0.1:8080."
            return false
        }
        vpnWebsiteAddress = normalized
        UserDefaults.standard.set(normalized, forKey: "pwnforge.vpnWebsite")
        vpnMessage = "VPN website address saved. Connect to the VPN, then check it below."
        return true
    }

    func useVPNWebsiteAddress() {
        guard saveWebsiteAddress(vpnWebsiteAddress) else { return }
        vpnMessage = "Opening the PwnForge address through your VPN…"
    }

    func checkCurrentVPNWebsite() async {
        guard let address = normalizedAddress(vpnWebsiteAddress) else {
            vpnMessage = "Add the private PwnForge website address first."
            return
        }
        vpnMessage = "Checking the website through the current network…"
        let result = await healthResult(for: address)
        switch result {
        case .success:
            vpnMessage = "Connected. The PwnForge website is reachable at this address."
        case .failure(let message):
            vpnMessage = "Not reachable yet. Connect in OpenVPN Connect, then check the address and try again. (\(message))"
        }
    }

    private func checkWebsite(at address: String, label: String) async {
        isCheckingWebsite = true
        defer { isCheckingWebsite = false }
        switch await healthResult(for: address) {
        case .success:
            websiteMessage = "Connected to \(label)."
        case .failure(let message):
            websiteMessage = "Address saved. The server isn't reachable yet: \(message)"
        }
    }

    private enum HealthResult {
        case success
        case failure(String)
    }

    private func healthResult(for address: String) async -> HealthResult {
        guard let base = makeURL(address) else { return .failure("check the address") }
        var components = URLComponents(url: base, resolvingAgainstBaseURL: false)
        let prefix = (components?.path ?? "").trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        components?.path = "/" + ([prefix, "api", "health"].filter { !$0.isEmpty }.joined(separator: "/"))
        components?.query = nil
        components?.fragment = nil
        guard let healthURL = components?.url else { return .failure("invalid address") }

        var request = URLRequest(url: healthURL)
        request.httpMethod = "GET"
        request.timeoutInterval = 7
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
                return .failure("server did not return a healthy response")
            }
            if let payload = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let status = payload["status"] as? String, status.lowercased() == "ok" {
                return .success
            }
            return .failure("unexpected health response")
        } catch let error as URLError where error.code == .timedOut {
            return .failure("timed out")
        } catch {
            return .failure(error.localizedDescription)
        }
    }

    func importVPNProfile(from url: URL) async {
        guard !isImportingProfile else { return }
        isImportingProfile = true
        defer { isImportingProfile = false }

        guard url.pathExtension.lowercased() == "ovpn" else {
            vpnMessage = "Choose an .ovpn profile file."
            return
        }
        guard let clientURL = openVPNConnectURL() else {
            vpnMessage = "OpenVPN Connect isn't installed. Install it from openvpn.net, finish its first-run setup, then import the profile here."
            return
        }
        let hasSecurityScope = url.startAccessingSecurityScopedResource()
        defer {
            if hasSecurityScope { url.stopAccessingSecurityScopedResource() }
        }

        do {
            let contents = try String(contentsOf: url, encoding: .utf8)
            let hasRemote = contents.range(of: #"(?im)^\s*remote\s+\S+"#, options: .regularExpression) != nil
            let hasClientMode = contents.range(of: #"(?im)^\s*(client|tls-client)\b"#, options: .regularExpression) != nil
            guard hasRemote && hasClientMode else {
                vpnMessage = "This doesn't look like a client VPN profile. Ask your PwnForge administrator for the .ovpn client profile."
                return
            }

            vpnMessage = "Importing the profile into OpenVPN Connect…"
            let safeName = url.deletingPathExtension().lastPathComponent
                .replacingOccurrences(of: "\n", with: " ")
                .trimmingCharacters(in: .whitespacesAndNewlines)
            let profileName = safeName.isEmpty ? "PwnForge VPN" : safeName
            let output = try await runOpenVPNImport(client: clientURL, source: url, profileName: profileName)
            guard output.status == 0 else {
                vpnMessage = "OpenVPN Connect couldn't import this profile. Open the VPN app once, accept its first-run prompt, and try again."
                return
            }
            importedProfileName = profileName
            vpnMessage = "Profile imported. OpenVPN Connect is ready—select ‘\(profileName)’ and press Connect. Return here to check the PwnForge website."
            let clientApp = clientURL.deletingLastPathComponent()
                .deletingLastPathComponent()
                .deletingLastPathComponent()
            NSWorkspace.shared.open(clientApp)
        } catch {
            vpnMessage = "Couldn't import the profile: \(error.localizedDescription)"
        }
    }

    private struct ImportOutput {
        let status: Int32
    }

    private func runOpenVPNImport(client: URL, source: URL, profileName: String) async throws -> ImportOutput {
        try await Task.detached(priority: .userInitiated) {
            let fileManager = FileManager.default
            let privateDirectory = fileManager.temporaryDirectory
                .appendingPathComponent("pwnforge-vpn-\(UUID().uuidString)", isDirectory: true)
            try fileManager.createDirectory(at: privateDirectory, withIntermediateDirectories: true,
                                            attributes: [.posixPermissions: 0o700])
            defer { try? fileManager.removeItem(at: privateDirectory) }
            let stagedProfile = privateDirectory.appendingPathComponent("profile.ovpn")
            try fileManager.copyItem(at: source, to: stagedProfile)
            try fileManager.setAttributes([.posixPermissions: 0o600], ofItemAtPath: stagedProfile.path)

            let process = Process()
            process.executableURL = client
            process.arguments = ["--import-profile=\(stagedProfile.path)", "--name=\(profileName)"]
            process.standardOutput = FileHandle.nullDevice
            process.standardError = FileHandle.nullDevice
            try process.run()
            process.waitUntilExit()
            return ImportOutput(status: process.terminationStatus)
        }.value
    }

    private func openVPNConnectURL() -> URL? {
        let candidates = [
            URL(fileURLWithPath: "/Applications/OpenVPN Connect/OpenVPN Connect.app/Contents/MacOS/OpenVPN Connect"),
            URL(fileURLWithPath: "/Applications/OpenVPN Connect.app/Contents/MacOS/OpenVPN Connect")
        ]
        return candidates.first { FileManager.default.isExecutableFile(atPath: $0.path) }
    }

    func openVPNDownloadPage() {
        if let url = URL(string: "https://openvpn.net/client/") { NSWorkspace.shared.open(url) }
    }

    func copyToPasteboard(_ value: String) {
        guard value.utf8.count <= 1_000_000 else { return }
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(value, forType: .string)
    }

    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard message.name == "pwnforgeClipboard", message.frameInfo.isMainFrame,
              let value = message.body as? String else { return }
        guard let configured = makeURL(websiteAddress),
              message.frameInfo.securityOrigin.host.caseInsensitiveCompare(configured.host ?? "") == .orderedSame,
              message.frameInfo.securityOrigin.port == (configured.port ?? (configured.scheme == "https" ? 443 : 80)) else { return }
        copyToPasteboard(value)
    }

    func webView(_ webView: WKWebView, runOpenPanelWith parameters: WKOpenPanelParameters,
                 initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping ([URL]?) -> Void) {
        let panel = NSOpenPanel()
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        panel.allowsMultipleSelection = parameters.allowsMultipleSelection
        panel.begin { response in
            completionHandler(response == .OK ? panel.urls : nil)
        }
    }

    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        // The user expects the whole PwnForge flow (including login) to stay in this app.
        // Leave navigation in WebKit so cookies and sign-in redirects share the same session.
        decisionHandler(.allow)
    }
}

@main
private struct PwnForgeDesktopApp: App {
    var body: some Scene {
        WindowGroup {
            PwnForgeRootView()
                .frame(minWidth: 980, minHeight: 640)
                .preferredColorScheme(.dark)
        }
        .windowStyle(.titleBar)
    }
}

private struct PwnForgeRootView: View {
    @StateObject private var model = PwnForgeModel()
    @State private var showVPN = false
    @State private var showSettings = false

    var body: some View {
        Group {
            if model.isConfigured {
                VStack(spacing: 0) {
                    appToolbar
                    if !model.websiteMessage.isEmpty {
                        statusStrip
                    }
                    WebViewPane(webView: model.webView)
                        .background(Color.white)
                }
            } else {
                WelcomeView(model: model, showVPN: $showVPN)
            }
        }
        .background(ForgeStyle.background)
        .sheet(isPresented: $showVPN) { VPNAccessView(model: model) }
        .sheet(isPresented: $showSettings) { ServerSettingsView(model: model) }
        .onOpenURL { url in
            guard url.pathExtension.lowercased() == "ovpn" else { return }
            showVPN = true
            Task { await model.importVPNProfile(from: url) }
        }
    }

    private var appToolbar: some View {
        HStack(spacing: 14) {
            ZStack {
                RoundedRectangle(cornerRadius: 10).fill(ForgeStyle.lime.opacity(0.13))
                Image(systemName: "chevron.left.forwardslash.chevron.right")
                    .font(.system(size: 15, weight: .bold))
                    .foregroundStyle(ForgeStyle.lime)
            }
            .frame(width: 36, height: 36)
            VStack(alignment: .leading, spacing: 1) {
                Text("PwnForge").font(.system(size: 15, weight: .bold))
                Text(model.websiteAddress).font(.system(size: 11)).foregroundStyle(ForgeStyle.muted).lineLimit(1)
            }
            Spacer()
            Button { model.webView.reload() } label: {
                Label("Reload", systemImage: "arrow.clockwise")
            }
            .buttonStyle(ForgeSecondaryButton())
            Button { showVPN = true } label: {
                Label("VPN access", systemImage: "network.badge.shield.half.filled")
            }
            .buttonStyle(ForgeSecondaryButton())
            Button { showSettings = true } label: {
                Image(systemName: "gearshape")
                    .frame(width: 34)
                    .accessibilityLabel("Server settings")
            }
            .buttonStyle(ForgeSecondaryButton())
        }
        .padding(.horizontal, 18)
        .padding(.vertical, 11)
        .background(ForgeStyle.background)
        .overlay(alignment: .bottom) { Rectangle().fill(ForgeStyle.border).frame(height: 1) }
    }

    private var statusStrip: some View {
        HStack(spacing: 8) {
            Circle().fill(model.websiteMessage.hasPrefix("Connected") ? ForgeStyle.lime : Color.orange).frame(width: 7, height: 7)
            Text(model.websiteMessage).font(.system(size: 12)).foregroundStyle(ForgeStyle.muted).lineLimit(1)
            Spacer()
        }
        .padding(.horizontal, 18)
        .padding(.vertical, 7)
        .background(ForgeStyle.surface)
    }
}

private struct WebViewPane: NSViewRepresentable {
    let webView: WKWebView
    func makeNSView(context: Context) -> WKWebView { webView }
    func updateNSView(_ nsView: WKWebView, context: Context) {}
}

private struct WelcomeView: View {
    @ObservedObject var model: PwnForgeModel
    @Binding var showVPN: Bool
    @State private var address: String
    @State private var isChecking = false

    init(model: PwnForgeModel, showVPN: Binding<Bool>) {
        self.model = model
        self._showVPN = showVPN
        self._address = State(initialValue: model.websiteAddress)
    }

    var body: some View {
        ZStack {
            ForgeStyle.background.ignoresSafeArea()
            Circle().fill(ForgeStyle.lime.opacity(0.06)).frame(width: 500).blur(radius: 70).offset(x: 380, y: -230)
            VStack(alignment: .leading, spacing: 22) {
                HStack(spacing: 13) {
                    Image(systemName: "chevron.left.forwardslash.chevron.right")
                        .font(.system(size: 22, weight: .bold)).foregroundStyle(ForgeStyle.lime)
                        .frame(width: 52, height: 52).background(ForgeStyle.lime.opacity(0.12), in: RoundedRectangle(cornerRadius: 15))
                    VStack(alignment: .leading, spacing: 2) {
                        Text("PwnForge").font(.system(size: 24, weight: .bold))
                        Text("Your private cyber range").font(.system(size: 13)).foregroundStyle(ForgeStyle.muted)
                    }
                }

                VStack(alignment: .leading, spacing: 8) {
                    Text("Connect to your server").font(.system(size: 28, weight: .bold))
                    Text("Enter the address your PwnForge administrator gave you. You can use a LAN, Tailscale, or public HTTPS address.")
                        .font(.system(size: 14)).foregroundStyle(ForgeStyle.muted).fixedSize(horizontal: false, vertical: true)
                }

                VStack(alignment: .leading, spacing: 9) {
                    Text("PWNFORGE ADDRESS").font(.system(size: 11, weight: .bold)).foregroundStyle(ForgeStyle.muted)
                    HStack(spacing: 10) {
                        Image(systemName: "link").foregroundStyle(ForgeStyle.muted)
                        TextField("http://100.82.189.124:8080", text: $address)
                            .textFieldStyle(.plain)
                            .onSubmit { connect() }
                    }
                    .padding(13)
                    .background(ForgeStyle.background.opacity(0.65), in: RoundedRectangle(cornerRadius: 11))
                    .overlay(RoundedRectangle(cornerRadius: 11).stroke(ForgeStyle.border, lineWidth: 1))
                    Text("If you use a VPN-only address, connect the VPN first or set it up below.")
                        .font(.system(size: 12)).foregroundStyle(ForgeStyle.muted)
                }

                HStack(spacing: 10) {
                    Button(action: connect) {
                        HStack(spacing: 8) {
                            if isChecking { ProgressView().controlSize(.small) }
                            Text("Open PwnForge")
                            Image(systemName: "arrow.right")
                        }
                        .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(ForgePrimaryButton())
                    Button { showVPN = true } label: {
                        Label("Set up VPN", systemImage: "shield.lefthalf.filled")
                    }
                    .buttonStyle(ForgeSecondaryButton())
                }
                if !model.websiteMessage.isEmpty {
                    Label(model.websiteMessage, systemImage: model.websiteMessage.hasPrefix("Connected") ? "checkmark.circle.fill" : "info.circle")
                        .font(.system(size: 12)).foregroundStyle(ForgeStyle.muted).fixedSize(horizontal: false, vertical: true)
                }

                HStack(spacing: 9) {
                    Image(systemName: "lock.shield").foregroundStyle(ForgeStyle.lime)
                    Text("Your sign-in stays on this Mac. PwnForge does not store your VPN profile.")
                        .font(.system(size: 12)).foregroundStyle(ForgeStyle.muted)
                }
                .padding(13).frame(maxWidth: .infinity, alignment: .leading)
                .background(ForgeStyle.surface, in: RoundedRectangle(cornerRadius: 11))
            }
            .padding(34)
            .frame(maxWidth: 570)
            .background(ForgeStyle.surface.opacity(0.96), in: RoundedRectangle(cornerRadius: 22))
            .overlay(RoundedRectangle(cornerRadius: 22).stroke(ForgeStyle.border, lineWidth: 1))
            .shadow(color: .black.opacity(0.25), radius: 35, y: 18)
        }
    }

    private func connect() {
        guard model.normalizedAddress(address) != nil else {
            model.websiteMessage = "Enter a valid server address, such as http://100.82.189.124:8080."
            return
        }
        isChecking = true
        _ = model.saveWebsiteAddress(address)
        Task { @MainActor in
            try? await Task.sleep(for: .milliseconds(650))
            isChecking = false
        }
    }
}

private struct VPNAccessView: View {
    @ObservedObject var model: PwnForgeModel
    @Environment(\.dismiss) private var dismiss
    @State private var vpnAddress: String
    @State private var showFilePicker = false
    @State private var selectedProfile: URL?

    init(model: PwnForgeModel) {
        self.model = model
        self._vpnAddress = State(initialValue: model.vpnWebsiteAddress)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 5) {
                    Text("VPN access").font(.system(size: 23, weight: .bold))
                    Text("Import your administrator-provided profile and open PwnForge through the tunnel.")
                        .font(.system(size: 13)).foregroundStyle(ForgeStyle.muted).fixedSize(horizontal: false, vertical: true)
                }
                Spacer()
                Button { dismiss() } label: { Image(systemName: "xmark").foregroundStyle(ForgeStyle.muted) }
                    .buttonStyle(.plain).accessibilityLabel("Close")
            }

            stepCard(number: "1", title: "Choose your VPN profile", detail: "Select the .ovpn file your PwnForge administrator gave you.") {
                HStack(spacing: 10) {
                    Button { showFilePicker = true } label: {
                        Label(selectedProfile?.lastPathComponent ?? "Choose .ovpn file", systemImage: "doc.badge.plus")
                    }.buttonStyle(ForgeSecondaryButton())
                    if selectedProfile != nil {
                        Button {
                            guard let selectedProfile else { return }
                            Task { await model.importVPNProfile(from: selectedProfile) }
                        } label: {
                            if model.isImportingProfile { ProgressView().controlSize(.small) }
                            Label("Import and open OpenVPN Connect", systemImage: "arrow.up.right.square")
                        }
                        .buttonStyle(ForgePrimaryButton())
                        .disabled(model.isImportingProfile)
                    }
                }
                .fileImporter(isPresented: $showFilePicker,
                              allowedContentTypes: [UTType(filenameExtension: "ovpn") ?? .data],
                              allowsMultipleSelection: false) { result in
                    switch result {
                    case .success(let urls): selectedProfile = urls.first
                    case .failure(let error): model.vpnMessage = "Couldn't open that profile: \(error.localizedDescription)"
                    }
                }
            }

            stepCard(number: "2", title: "Connect in OpenVPN Connect", detail: "Select the imported profile and press Connect. PwnForge opens the client for you.") {
                Button { model.openVPNDownloadPage() } label: {
                    Label("Get OpenVPN Connect", systemImage: "arrow.up.right")
                }
                .buttonStyle(ForgeSecondaryButton())
            }

            stepCard(number: "3", title: "Open your PwnForge website", detail: "Your VPN profile does not tell us which private address serves the website. Enter the address your administrator provided.") {
                HStack(spacing: 9) {
                    TextField("http://10.8.0.1:8080", text: $vpnAddress).textFieldStyle(.roundedBorder)
                    Button("Save") { _ = model.saveVPNWebsiteAddress(vpnAddress) }.buttonStyle(ForgeSecondaryButton())
                }
                HStack(spacing: 9) {
                    Button { Task { await model.checkCurrentVPNWebsite() } } label: {
                        Label("Check VPN connection", systemImage: "network")
                    }.buttonStyle(ForgeSecondaryButton())
                    Button { model.useVPNWebsiteAddress(); dismiss() } label: {
                        Label("Use VPN address", systemImage: "arrow.right")
                    }.buttonStyle(ForgePrimaryButton())
                }
            }

            Label(model.vpnMessage, systemImage: model.vpnMessage.hasPrefix("Connected") ? "checkmark.circle.fill" : "info.circle")
                .font(.system(size: 12)).foregroundStyle(ForgeStyle.muted).fixedSize(horizontal: false, vertical: true)
                .padding(.top, 1)

            HStack(alignment: .top, spacing: 8) {
                Image(systemName: "lock.fill").foregroundStyle(ForgeStyle.lime)
                Text("The profile is imported into OpenVPN Connect and the temporary import copy is removed. PwnForge does not keep the profile or its private keys.")
                    .font(.system(size: 11)).foregroundStyle(ForgeStyle.muted).fixedSize(horizontal: false, vertical: true)
            }
        }
        .padding(24)
        .frame(width: 640)
        .background(ForgeStyle.background)
        .preferredColorScheme(.dark)
    }

    private func stepCard<Content: View>(number: String, title: String, detail: String,
                                         @ViewBuilder content: () -> Content) -> some View {
        HStack(alignment: .top, spacing: 13) {
            Text(number).font(.system(size: 12, weight: .bold)).foregroundStyle(ForgeStyle.lime)
                .frame(width: 25, height: 25).background(ForgeStyle.lime.opacity(0.13), in: Circle())
            VStack(alignment: .leading, spacing: 10) {
                Text(title).font(.system(size: 14, weight: .semibold))
                Text(detail).font(.system(size: 12)).foregroundStyle(ForgeStyle.muted).fixedSize(horizontal: false, vertical: true)
                content()
            }
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(ForgeStyle.surface, in: RoundedRectangle(cornerRadius: 13))
        .overlay(RoundedRectangle(cornerRadius: 13).stroke(ForgeStyle.border, lineWidth: 1))
    }
}

private struct ServerSettingsView: View {
    @ObservedObject var model: PwnForgeModel
    @Environment(\.dismiss) private var dismiss
    @State private var address: String

    init(model: PwnForgeModel) {
        self.model = model
        self._address = State(initialValue: model.websiteAddress)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 17) {
            Text("Server settings").font(.system(size: 22, weight: .bold))
            Text("Change which PwnForge server this app opens. Your website login remains in the app.")
                .font(.system(size: 13)).foregroundStyle(ForgeStyle.muted)
            TextField("https://pwnforge.example.com", text: $address).textFieldStyle(.roundedBorder)
            Text(model.websiteMessage).font(.system(size: 12)).foregroundStyle(ForgeStyle.muted).fixedSize(horizontal: false, vertical: true)
            HStack {
                Button("Cancel") { dismiss() }.buttonStyle(ForgeSecondaryButton())
                Spacer()
                Button("Save and open") {
                    if model.saveWebsiteAddress(address) { dismiss() }
                }.buttonStyle(ForgePrimaryButton())
            }
        }
        .padding(24)
        .frame(width: 500)
        .background(ForgeStyle.background)
        .preferredColorScheme(.dark)
    }
}

private struct ForgePrimaryButton: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 13, weight: .semibold))
            .foregroundStyle(Color.black.opacity(0.9))
            .padding(.horizontal, 14).padding(.vertical, 9)
            .background(ForgeStyle.lime.opacity(configuration.isPressed ? 0.78 : 1), in: RoundedRectangle(cornerRadius: 9))
            .scaleEffect(configuration.isPressed ? 0.985 : 1)
    }
}

private struct ForgeSecondaryButton: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 12, weight: .medium))
            .foregroundStyle(.white.opacity(0.92))
            .padding(.horizontal, 11).padding(.vertical, 8)
            .background(ForgeStyle.surfaceRaised.opacity(configuration.isPressed ? 0.7 : 1), in: RoundedRectangle(cornerRadius: 9))
            .overlay(RoundedRectangle(cornerRadius: 9).stroke(ForgeStyle.border, lineWidth: 1))
    }
}
