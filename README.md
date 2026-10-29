# django-push-notifications testbed

Send real push notifications from a [django-push-notifications](https://github.com/jazzband/django-push-notifications) checkout to a real receiver.

| Backend  | Receiver          | Status                |
| -------- | ----------------- | --------------------- |
| Web Push | Chrome or Firefox | Ready, no account     |
| FCM      | Chrome or Firefox | Ready, needs Firebase |
| APNs     | iOS Simulator     | Planned               |
| WNS      | Windows app       | Planned               |

Unofficial, not part of django-push-notifications.

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
2. Add a web app (**Project settings → General → Add app → Web**) and copy its config into `firebase-config.json`, using `firebase-config.example.json` as the template. ([docs](https://firebase.google.com/docs/web/setup))
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

## What gets sent

| Case | `webpush.py send`                   | `fcm.py send`                   |
| ---- | ----------------------------------- | ------------------------------- |
| A    | Text                                | Topic on the message            |
| B    | JSON string                         | Topic as `send_message(to=...)` |
| C    | Dict                                | Condition                       |
| D    | `ttl=60`                            | Device token                    |
| E    | Queryset bulk send                  | `device.send_message(to=topic)` |
| F    | Unknown subscription is deactivated |                                 |

Results print in the terminal, and what arrives shows on the page and in `data/received.jsonl`.

## APNs and WNS (planned)

APNs:

1. [Apple Developer Program](https://developer.apple.com/programs/) membership, an App ID with push enabled and a `.p8` key. ([docs](https://developer.apple.com/documentation/usernotifications/establishing-a-token-based-connection-to-apns))
2. Xcode. The iOS Simulator receives sandbox pushes since Xcode 14 (Apple silicon or T2 Mac). ([release notes](https://developer.apple.com/go/?id=xcode-14-sdk-rn))
3. A small iOS app that posts its device token to the receiver. ([docs](https://developer.apple.com/documentation/usernotifications/registering-your-app-with-apns))

WNS:

1. A [Microsoft developer account](https://learn.microsoft.com/en-us/windows/apps/publish/partner-center/open-a-developer-account) and an app in [Partner Center](https://partner.microsoft.com/dashboard), for the Package SID and secret. ([docs](https://learn.microsoft.com/en-us/windows/apps/design/shell/tiles-and-notifications/windows-push-notification-services--wns--overview))
2. Windows 10 or 11 (a VM works).
3. A packaged Windows app that posts its channel URI to the receiver.

## Comparing versions

```sh
git -C ../django-push-notifications worktree add ../dpn-3.3.0 3.3.0
uv run webpush.py send --repo ../dpn-3.3.0
```

## Notes

- Keys, tokens and received messages are stored in `data/`, which git ignores along with `firebase-config.json`.
- Open the pages on `localhost`, browsers only allow push on secure origins.
- If notifications were blocked, allow them for `localhost:8765` in the site settings and reload.
- FCM condition messages can take about a minute to arrive, so wait before `fcm.py unsubscribe`.

## License

MIT
