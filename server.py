"""Receiver pages on http://localhost:8765. Tokens, subscriptions and received messages go to data/."""

import argparse
import json
import os
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from testbed.common import ROOT, config_path, data_path, vapid_keys

PORT = 8765
SAVED = {
	"/fcm/token": "fcm-token.txt",
	"/webpush/subscription": "webpush-subscription.json",
	"/apns/token": "apns-token.txt",
	"/wns/channel": "wns-channel.txt",
}


class Handler(SimpleHTTPRequestHandler):
	def do_GET(self):
		if self.path == "/vapid-public-key":
			return self.reply(vapid_keys()["public_key"].encode(), "text/plain")
		if self.path == "/firebase-config.json":
			path = config_path("firebase")
			if not os.path.exists(path):
				return self.send_error(404, "Copy config/firebase.example.json to config/firebase.json")
			with open(path, "rb") as f:
				return self.reply(f.read(), "application/json")
		super().do_GET()

	def do_POST(self):
		body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
		if self.path in SAVED:
			with open(data_path(SAVED[self.path]), "w") as f:
				f.write(body)
		elif self.path == "/received":
			with open(data_path("received.jsonl"), "a") as f:
				f.write(json.dumps({"at": time.strftime("%H:%M:%S"), **json.loads(body)}) + "\n")
		else:
			return self.send_error(404)
		self.send_response(204)
		self.end_headers()

	def reply(self, body, content_type):
		self.send_response(200)
		self.send_header("Content-Type", content_type)
		self.end_headers()
		self.wfile.write(body)

	def log_message(self, format, *args):
		pass


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--host", default="127.0.0.1", help="use 0.0.0.0 to accept a Windows VM for WNS")
	host = parser.parse_args().host
	print(f"Receiver pages on http://localhost:{PORT}, listening on {host} (Ctrl+C to stop)", flush=True)
	ThreadingHTTPServer((host, PORT), partial(Handler, directory=os.path.join(ROOT, "receivers", "web"))).serve_forever()
