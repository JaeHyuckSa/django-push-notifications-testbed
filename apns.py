"""Send APNs notifications with a django-push-notifications checkout to the iOS app in the Simulator.

Settings come from config/apns.json. Sends go to the APNs sandbox through the apns-async backend.

    python apns.py send [--repo PATH] [--label NAME]
"""

import argparse
import json
import os
import sys
import warnings

from testbed.common import add_checkout_args, data_path, local_config, run_case, setup_django


def send(args):
	if not local_config("apns"):
		sys.exit("Copy config/apns.example.json to config/apns.json and fill it in.")
	token_path = data_path("apns-token.txt")
	if not os.path.exists(token_path):
		sys.exit("No device token yet: run server.py and start the iOS app in the Simulator.")
	setup_django(args)
	# fails right away if aioapns isn't installed, instead of falling back to apns2
	import push_notifications.apns_async  # noqa: F401
	from push_notifications.models import APNSDevice

	label = args.label
	with open(token_path) as f:
		device = APNSDevice.objects.create(registration_id=f.read().strip())

	def case(name, fn):
		run_case(label, name, fn, lambda r: json.dumps(r, default=str)[:90])

	case("A text alert", lambda: device.send_message(f"{label}:A"))
	case("B title and body", lambda: device.send_message({"title": "dpn", "body": f"{label}:B"}))
	case("C badge and sound", lambda: device.send_message(f"{label}:C", badge=3, sound="default"))
	case("D thread_id and category", lambda: device.send_message(f"{label}:D", thread_id="dpn", category="DPN"))
	case("E extra data", lambda: device.send_message(f"{label}:E", extra={"marker": f"{label}:E"}))
	try:
		from push_notifications.enums import InterruptionLevelType
	except ImportError:
		print(f"[{label}] {'F interruption level':32} skipped, not in this checkout")
	else:
		case("F interruption level", lambda: device.send_message(
			f"{label}:F", interruption_level=InterruptionLevelType.TIME_SENSITIVE))
	case("G silent (content_available)", lambda: device.send_message(
		None, content_available=True, extra={"marker": f"{label}:G"}))
	case("H bulk with a badge callback", lambda: APNSDevice.objects.filter(pk=device.pk).send_message(
		f"{label}:H", badge=lambda token: 7))
	# a well-formed token APNs doesn't know: should be rejected and deactivate the device
	gone = APNSDevice.objects.create(registration_id="0" * 64)
	case("I unknown token", lambda: gone.send_message(f"{label}:I"))
	gone.refresh_from_db()
	print(f"[{label}] {'I device active afterwards':32} {gone.active}")


def main():
	warnings.simplefilter("ignore")
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	sub = parser.add_subparsers(dest="command", required=True)
	add_checkout_args(sub.add_parser("send"))
	send(parser.parse_args())


if __name__ == "__main__":
	main()
