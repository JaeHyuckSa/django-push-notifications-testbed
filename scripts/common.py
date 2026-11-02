import base64
import json
import logging
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_REPO = os.environ.get("DPN_REPO", os.path.join(ROOT, "..", "django-push-notifications"))

logging.basicConfig(format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("testbed")
log.setLevel(logging.INFO)

# ROOT_URLCONF; the checkout's own points to a missing module
urlpatterns = []


def data_path(name):
	os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
	return os.path.join(ROOT, "data", name)


def config_path(name):
	return os.path.join(ROOT, "config", f"{name}.json")


def local_config(name):
	path = config_path(name)
	if not os.path.exists(path):
		return None
	with open(path) as f:
		return json.load(f)


def vapid_keys():
	# base64url key pair, as docs/WebPush.rst recommends
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


def push_settings():
	conf = {
		"WP_PRIVATE_KEY": vapid_keys()["private_key"],
		"WP_CLAIMS": {"sub": "mailto:testbed@example.com"},
	}
	apns = local_config("apns")
	if apns:
		conf.update({
			"APNS_AUTH_KEY_PATH": apns["key_path"],
			"APNS_AUTH_KEY_ID": apns["key_id"],
			"APNS_TEAM_ID": apns["team_id"],
			"APNS_TOPIC": apns["bundle_id"],
			"APNS_USE_SANDBOX": True,
		})
	wns = local_config("wns")
	if wns:
		conf.update({
			"WNS_PACKAGE_SECURITY_ID": wns["package_sid"],
			"WNS_SECRET_KEY": wns["secret"],
		})
	return conf


def add_checkout_args(parser):
	parser.add_argument(
		"--repo", default=DEFAULT_REPO,
		help="django-push-notifications checkout to test (default: $DPN_REPO or ../django-push-notifications)",
	)
	parser.add_argument("--label", help="prefix for the markers shown on the page (default: the checkout's branch)")


def setup_django(args):
	repo = os.path.abspath(args.repo)
	if not os.path.isdir(os.path.join(repo, "push_notifications")):
		sys.exit(f"{repo} is not a django-push-notifications checkout, pass --repo")
	if not args.label:
		args.label = git_branch(repo)
	sys.path[:0] = [repo, HERE]
	import django
	from django.conf import settings
	from tests import settings as checkout_settings

	conf = {k: getattr(checkout_settings, k) for k in dir(checkout_settings) if k.isupper()}
	conf.update({
		"DATABASES": {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
		"ROOT_URLCONF": "common",
		"PUSH_NOTIFICATIONS_SETTINGS": push_settings(),
	})
	settings.configure(**conf)
	django.setup()
	from django.core.management import call_command

	call_command("migrate", verbosity=0)
	import push_notifications

	log.info("testing %s", os.path.dirname(push_notifications.__file__))


def git_branch(repo):
	try:
		out = subprocess.run(
			["git", "-C", repo, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True
		)
		return out.stdout.strip()
	except (OSError, subprocess.CalledProcessError):
		return "test"


def report(label, name, out):
	log.info("[%s] %-32s %s", label, name, out)


def run_case(label, name, fn, describe):
	try:
		out = describe(fn())
	except Exception as e:
		out = f"raised {type(e).__name__}: {str(e)[:70]}"
	report(label, name, out)
