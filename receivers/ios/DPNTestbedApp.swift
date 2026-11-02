import SwiftUI
import UIKit
import UserNotifications

// the Simulator shares the Mac's localhost
let receiverBase = "http://localhost:8765"

final class Receiver: NSObject, ObservableObject, UIApplicationDelegate, UNUserNotificationCenterDelegate {
    @Published var status = "starting"
    @Published var token = ""
    @Published var received: [String] = []

    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil
    ) -> Bool {
        UNUserNotificationCenter.current().delegate = self
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge, .sound]) { granted, _ in
            DispatchQueue.main.async {
                self.status = granted ? "registering" : "notifications not allowed"
                application.registerForRemoteNotifications()
            }
        }
        return true
    }

    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        token = deviceToken.map { String(format: "%02x", $0) }.joined()
        status = "ready"
        post("/apns/token", Data(token.utf8))
    }

    func application(_ application: UIApplication, didFailToRegisterForRemoteNotificationsWithError error: Error) {
        status = "error: \(error.localizedDescription)"
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        record("foreground", notification.request.content.userInfo)
        completionHandler([.banner, .list, .sound, .badge])
    }

    func application(
        _ application: UIApplication,
        didReceiveRemoteNotification userInfo: [AnyHashable: Any],
        fetchCompletionHandler completionHandler: @escaping (UIBackgroundFetchResult) -> Void
    ) {
        record("background", userInfo)
        completionHandler(.newData)
    }

    private func record(_ place: String, _ userInfo: [AnyHashable: Any]) {
        var payload: [String: Any] = [:]
        for (key, value) in userInfo {
            payload["\(key)"] = value
        }
        let body: [String: Any] = ["source": "apns", "where": place, "payload": payload]
        guard JSONSerialization.isValidJSONObject(body),
              let data = try? JSONSerialization.data(withJSONObject: body) else { return }
        DispatchQueue.main.async {
            self.received.append(String(decoding: data, as: UTF8.self))
        }
        post("/received", data)
    }

    private func post(_ path: String, _ body: Data) {
        guard let url = URL(string: receiverBase + path) else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.httpBody = body
        URLSession.shared.dataTask(with: request).resume()
    }
}

struct ReceiverView: View {
    @EnvironmentObject var receiver: Receiver

    var body: some View {
        List {
            Section("Status") {
                Text(receiver.status)
                Text(receiver.token).font(.caption.monospaced()).textSelection(.enabled)
            }
            Section("Received") {
                ForEach(Array(receiver.received.enumerated()), id: \.offset) { _, line in
                    Text(line).font(.caption)
                }
            }
        }
    }
}

@main
struct DPNTestbedApp: App {
    // also injected as an EnvironmentObject
    @UIApplicationDelegateAdaptor(Receiver.self) var receiver

    var body: some Scene {
        WindowGroup {
            ReceiverView()
        }
    }
}
