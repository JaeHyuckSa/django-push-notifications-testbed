# django-push-notifications testbed

Send real push notifications from a [django-push-notifications](https://github.com/jazzband/django-push-notifications) checkout to a real receiver.

| Backend  | Receiver          | Status                                                            |
| -------- | ----------------- | ----------------------------------------------------------------- |
| Web Push | Chrome or Firefox | Ready, no account                                                 |
| FCM      | Chrome or Firefox | Ready, needs Firebase                                             |
| APNs     | iOS Simulator     | Needs an Apple developer account, not verified yet                |
| WNS      | Windows app       | Needs a Microsoft developer account and Windows, not verified yet |

Unofficial, not part of django-push-notifications.

```
server.py              receiver: serves the pages and stores tokens and received messages
fcm.py webpush.py      one send script per backend
apns.py wns.py
config/                *.example.json templates; your copies next to them are gitignored
receivers/             web/ (browser pages), ios/ (Simulator app), windows/ (UWP app)
testbed/               shared code and the Django settings
data/                  tokens, keys and received messages (gitignored)
```

## Setup

1. Install Python 3.10+ and [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Clone both repositories side by side:

   ```sh
   git clone https://github.com/jazzband/django-push-notifications
   git clone <this repository> django-push-notifications-testbed
   ```

3. Start the receiver and keep it running:

   ```sh
   cd django-push-notifications-testbed
   uv run server.py
   ```

To test another checkout, pass `--repo PATH` or set `DPN_REPO`.

## Web Push

1. Open http://localhost:8765/webpush/, click **Subscribe** and allow notifications.
2. Run `uv run webpush.py send`.

## FCM

Once:

1. Create a project in the [Firebase console](https://console.firebase.google.com/).
2. Add a web app (**Project settings → General → Add app → Web**) and copy its config into `config/firebase.json`, using `config/firebase.example.json` as the template. ([docs](https://firebase.google.com/docs/web/setup))
3. Generate a service account key (**Project settings → Service accounts → Generate new private key**) and keep it outside this folder. ([docs](https://firebase.google.com/docs/admin/setup))
4. For topics, give that service account the **Firebase Cloud Messaging API Admin** role in [IAM](https://console.cloud.google.com/iam-admin/iam). ([docs](https://cloud.google.com/iam/docs/granting-changing-revoking-access))

Each time:

```sh
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
uv run server.py              # then open http://localhost:8765/fcm/ and allow notifications
uv run fcm.py subscribe
uv run fcm.py send            # --dry-run to validate only
uv run fcm.py unsubscribe
```

## APNs

The iOS Simulator receives real pushes from the APNs sandbox since Xcode 14, on Apple silicon or T2 Macs. ([release notes](https://developer.apple.com/go/?id=xcode-14-sdk-rn))

Once:

1. Join the [Apple Developer Program](https://developer.apple.com/programs/) and install Xcode.
2. Create a key with **Apple Push Notifications service (APNs)** enabled (**Certificates, Identifiers & Profiles → Keys**), download the `.p8` file and note its Key ID and your Team ID. Keep the file outside this folder. ([docs](https://developer.apple.com/documentation/usernotifications/establishing-a-token-based-connection-to-apns))
3. In Xcode, create an iOS **App** project (SwiftUI) signed with your team, replace its Swift files with `receivers/ios/DPNTestbedApp.swift`, and add the **Push Notifications** and **Background Modes → Remote notifications** capabilities. ([docs](https://developer.apple.com/documentation/usernotifications/registering-your-app-with-apns))
4. In the target's **Info** tab, add **App Transport Security Settings → Allows Local Networking = YES**, so the app can reach `localhost:8765`.
5. Copy `config/apns.example.json` to `config/apns.json` and fill in the key path, Key ID, Team ID and the app's bundle ID.

Each time:

```sh
uv run server.py    # then run the app on an iOS 16+ Simulator, allow notifications and keep it open
uv run apns.py send
```

## WNS

django-push-notifications gets its WNS token with a Partner Center app's Package SID and secret, so the app has to come from Partner Center.

Once:

1. Set up Windows 10 or 11 (a VM works) with Visual Studio and its **Universal Windows Platform development** workload.
2. Open a [Microsoft developer account](https://learn.microsoft.com/en-us/windows/apps/publish/partner-center/open-a-developer-account) and reserve an app name in [Partner Center](https://partner.microsoft.com/dashboard).
3. In Visual Studio, create a **Blank App (Universal Windows)** project, replace `MainPage.xaml.cs` with `receivers/windows/MainPage.xaml.cs` and set your Mac's IP address in `Receiver`. In `Package.appxmanifest` → **Capabilities**, enable **Internet (Client)** and **Private Networks (Client & Server)**.
4. **Project → Publish → Associate App with the Store** and pick the reserved name.
5. Copy `config/wns.example.json` to `config/wns.json` and fill in the app's Package SID and client secret from Partner Center. ([docs](https://learn.microsoft.com/en-us/windows/apps/develop/notifications/push-notifications/wns-overview))

Each time:

```sh
uv run server.py --host 0.0.0.0   # reachable from Windows; then run the app until it says "ready"
uv run wns.py send
```

## What gets sent

| Case | `webpush.py send`                   | `fcm.py send`                   | `apns.py send`                  | `wns.py send`        |
| ---- | ----------------------------------- | ------------------------------- | ------------------------------- | -------------------- |
| A    | Text                                | Topic on the message            | Text alert                      | Text toast           |
| B    | JSON string                         | Topic as `send_message(to=...)` | Title and body                  | Toast with two lines |
| C    | Dict                                | Condition                       | Badge and sound                 | Badge (`xml_data`)   |
| D    | `ttl=60`                            | Device token                    | `thread_id` and `category`      | Raw                  |
| E    | Queryset bulk send                  | `device.send_message(to=topic)` | Extra data                      | Queryset bulk send   |
| F    | Unknown subscription is deactivated |                                 | Interruption level              | Unknown channel      |
| G    |                                     |                                 | Silent (`content_available`)    |                      |
| H    |                                     |                                 | Bulk send with a badge callback |                      |
| I    |                                     |                                 | Unknown token is deactivated    |                      |

Results print in the terminal, and what arrives shows on the page (or in the app) and in `data/received.jsonl`.

## Comparing versions

```sh
git -C ../django-push-notifications worktree add ../dpn-3.3.0 3.3.0
uv run webpush.py send --repo ../dpn-3.3.0
```

## Notes

- Keys, tokens and received messages are stored in `data/`; git ignores it and your `config/*.json` files.
- Open the pages on `localhost`, browsers only allow push on secure origins.
- If notifications were blocked, allow them for `localhost:8765` in the site settings and reload.
- FCM condition messages can take about a minute to arrive, so wait before `fcm.py unsubscribe`.

## License

MIT
