"""Send FCM messages with a django-push-notifications checkout to the browser on the receiver page."""

import argparse
import os
import sys
import urllib.parse
import warnings

from common import add_checkout_args, data_path, log, report, run_case, setup_django

TOPICS = ("news", "sports")


def read_token():
	path = data_path("fcm-token.txt")
	if not os.path.exists(path):
		sys.exit("No FCM token yet: run scripts/server.py, open http://localhost:8765/fcm/ and allow notifications.")
	return open(path).read().strip()


def topic_subscriptions(method):
	import google.auth.transport.requests
	from google.oauth2 import service_account

	creds = service_account.Credentials.from_service_account_file(
		os.environ["GOOGLE_APPLICATION_CREDENTIALS"],
		scopes=["https://www.googleapis.com/auth/firebase.messaging"],
	)
	session = google.auth.transport.requests.AuthorizedSession(creds)
	token = urllib.parse.quote(read_token(), safe="")
	base = f"https://fcm.googleapis.com/v1/projects/{creds.project_id}/registrations/{token}/topicSubscriptions"
	for topic in TOPICS:
		if method == "subscribe":
			r = session.post(f"{base}?topic_name={topic}", json={})
		else:
			r = session.delete(f"{base}/{topic}")
		log.info("%s %s: HTTP %s", method, topic, r.status_code)


def send(args):
	setup_django(args)
	import firebase_admin

	firebase_admin.initialize_app()
	from push_notifications.gcm import dict_to_fcm_message, send_message
	from push_notifications.models import GCMDevice

	label, dry_run = args.label, args.dry_run

	def msg(case, **kwargs):
		return dict_to_fcm_message({"message": "test", "marker": f"{label}:{case}"}, **kwargs)

	def describe(r):
		if r is None or not r.responses:
			return "nothing sent to Firebase"
		return f"success={r.success_count} failure={r.failure_count}"

	def case(name, fn):
		run_case(label, name, fn, describe)

	case("A topic on the message", lambda: send_message(None, msg("A", to="/topics/news"), dry_run=dry_run))
	case("B topic as send_message(to=...)", lambda: send_message(None, msg("B"), to="/topics/news", dry_run=dry_run))
	case("C condition", lambda: send_message(
		None, msg("C", condition="'news' in topics || 'sports' in topics"), dry_run=dry_run))
	token = read_token()
	case("D device token", lambda: send_message([token], msg("D"), dry_run=dry_run))
	if dry_run:
		# device.send_message() can't dry-run: dict_to_fcm_message() returns None
		report(label, "E device.send_message(to=topic)", "skipped with --dry-run")
		return
	device = GCMDevice.objects.create(registration_id=token, cloud_message_type="FCM")
	case("E device.send_message(to=topic)", lambda: device.send_message(
		"test", extra={"marker": f"{label}:E"}, to="/topics/news"))


def main():
	warnings.simplefilter("ignore")
	parser = argparse.ArgumentParser(description=__doc__)
	sub = parser.add_subparsers(dest="command", required=True)
	sub.add_parser("subscribe")
	sub.add_parser("unsubscribe")
	p = sub.add_parser("send")
	add_checkout_args(p)
	p.add_argument("--dry-run", action="store_true", help="let Firebase validate without delivering")
	args = parser.parse_args()
	if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
		sys.exit("Set GOOGLE_APPLICATION_CREDENTIALS to the path of your Firebase service account key.")
	if args.command == "send":
		send(args)
	else:
		topic_subscriptions(args.command)


if __name__ == "__main__":
	main()
