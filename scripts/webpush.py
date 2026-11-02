"""Send Web Push messages with a django-push-notifications checkout to the browser on the receiver page.

No account is needed: the VAPID keys are made in data/vapid.json on first use.

    uv run scripts/webpush.py send [--repo PATH] [--label NAME]
"""

import argparse
import json
import os
import sys
import warnings

from common import add_checkout_args, data_path, run_case, setup_django


def send(args):
	path = data_path("webpush-subscription.json")
	if not os.path.exists(path):
		sys.exit("No subscription yet: run scripts/server.py, open http://localhost:8765/webpush/ and click Subscribe.")
	setup_django(args)
	from push_notifications.models import WebPushDevice

	label = args.label
	with open(path) as f:
		sub = json.load(f)
	keys = {"p256dh": sub["keys"]["p256dh"], "auth": sub["keys"]["auth"], "browser": sub["browser"]}
	device = WebPushDevice.objects.create(registration_id=sub["endpoint"], **keys)

	def case(name, fn):
		run_case(label, name, fn, lambda r: json.dumps(r, default=str)[:90])

	case("A text", lambda: device.send_message(f"{label}:A"))
	case("B JSON string", lambda: device.send_message(json.dumps({"title": "dpn", "body": f"{label}:B"})))
	case("C dict", lambda: device.send_message({"title": "dpn", "body": f"{label}:C"}))
	case("D send_message(ttl=60)", lambda: device.send_message(f"{label}:D", ttl=60))
	case("E queryset bulk", lambda: WebPushDevice.objects.filter(pk=device.pk).send_message(f"{label}:E"))
	# same push service, a subscription it doesn't know: should come back 404/410 and deactivate the device
	gone = WebPushDevice.objects.create(registration_id=sub["endpoint"].rsplit("/", 1)[0] + "/testbed-unknown", **keys)
	case("F unknown subscription", lambda: gone.send_message(f"{label}:F"))
	gone.refresh_from_db()
	print(f"[{label}] {'F device active afterwards':32} {gone.active}")


def main():
	warnings.simplefilter("ignore")
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	sub = parser.add_subparsers(dest="command", required=True)
	add_checkout_args(sub.add_parser("send"))
	send(parser.parse_args())


if __name__ == "__main__":
	main()
