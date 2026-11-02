"""Pieces shared by server.py and the send scripts."""

import base64
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_REPO = os.environ.get("DPN_REPO", os.path.join(ROOT, "..", "django-push-notifications"))


def data_path(name):
	os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
	return os.path.join(ROOT, "data", name)


def config_path(name):
	return os.path.join(ROOT, "config", f"{name}.json")


def local_config(name):
	"""config/<name>.json (gitignored), or None if it doesn't exist yet."""
	path = config_path(name)
	if not os.path.exists(path):
		return None
	with open(path) as f:
		return json.load(f)


def vapid_keys():
	# raw base64url key pair, the format docs/WebPush.rst recommends
	path = data_path("vapid.json")
	if not os.path.exists(path):
		from cryptography.hazmat.primitives import serialization
		from cryptography.hazmat.primitives.asymmetric import ec

		key = ec.generate_private_key(ec.SECP256R1())
		public = key.public_key().public_bytes(
			serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
		)
		private = key.private_numbers().private_value.to_bytes(32, "big")
		with open(path, "w") as f:
			json.dump({"private_key": b64(private), "public_key": b64(public)}, f)
	with open(path) as f:
		return json.load(f)


def b64(raw):
	return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def add_checkout_args(parser):
	parser.add_argument(
		"--repo", default=DEFAULT_REPO,
		help="django-push-notifications checkout to test (default: $DPN_REPO or ../django-push-notifications)",
	)
	parser.add_argument("--label", help="prefix for the markers shown on the page (default: the checkout's branch)")


def setup_django(args):
	"""Make the checkout's push_notifications importable and set up an in-memory database."""
	repo = os.path.abspath(args.repo)
	if not os.path.isdir(os.path.join(repo, "push_notifications")):
		sys.exit(f"{repo} is not a django-push-notifications checkout, pass --repo")
	if not args.label:
		args.label = git_branch(repo)
	sys.path[:0] = [repo, HERE]
	os.environ["DJANGO_SETTINGS_MODULE"] = "testbed_settings"
	import django

	django.setup()
	from django.core.management import call_command

	call_command("migrate", verbosity=0)
	import push_notifications

	print(f"testing {os.path.dirname(push_notifications.__file__)}")


def git_branch(repo):
	try:
		out = subprocess.run(
			["git", "-C", repo, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True
		)
		return out.stdout.strip()
	except (OSError, subprocess.CalledProcessError):
		return "test"


def run_case(label, name, fn, describe):
	try:
		out = describe(fn())
	except Exception as e:
		out = f"raised {type(e).__name__}: {str(e)[:70]}"
	print(f"[{label}] {name:32} {out}", flush=True)
