"""Send WNS notifications with a django-push-notifications checkout to the Windows app."""

import argparse
import json
import os
import sys
import warnings

from common import add_checkout_args, data_path, local_config, report, run_case, setup_django


def send(args):
	if not local_config("wns"):
		sys.exit("Copy config/wns.example.json to config/wns.json and fill it in.")
	channel_path = data_path("wns-channel.txt")
	if not os.path.exists(channel_path):
		sys.exit("No channel yet: run scripts/server.py --host 0.0.0.0 and start the Windows app.")
	setup_django(args)
	from push_notifications.models import WNSDevice

	label = args.label
	with open(channel_path) as f:
		channel = f.read().strip()
	device = WNSDevice.objects.create(registration_id=channel)

	def case(name, fn):
		run_case(label, name, fn, lambda r: json.dumps(r, default=str)[:90])

	case("A text toast", lambda: device.send_message(f"{label}:A"))
	case("B toast with two lines", lambda: device.send_message(
		{"text": ["dpn", f"{label}:B"]}, template="ToastText02"))
	case("C badge (xml_data)", lambda: device.send_message(
		None, xml_data={"badge": {"attrs": {"value": "7"}}}))
	case("D raw", lambda: device.send_message(None, raw_data=f"{label}:D"))
	case("E queryset bulk", lambda: WNSDevice.objects.filter(pk=device.pk).send_message(f"{label}:E"))
	# same host, unknown channel
	gone = WNSDevice.objects.create(registration_id=channel.split("?")[0].rsplit("/", 1)[0] + "/testbed-unknown")
	case("F unknown channel", lambda: gone.send_message(f"{label}:F"))
	gone.refresh_from_db()
	report(label, "F device active afterwards", gone.active)


def main():
	warnings.simplefilter("ignore")
	parser = argparse.ArgumentParser(description=__doc__)
	sub = parser.add_subparsers(dest="command", required=True)
	add_checkout_args(sub.add_parser("send"))
	send(parser.parse_args())


if __name__ == "__main__":
	main()
