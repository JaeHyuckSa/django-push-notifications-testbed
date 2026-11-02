# the checkout passed with --repo provides tests.settings
from tests.settings import *  # noqa: F401,F403

from testbed.common import local_config, vapid_keys

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
ROOT_URLCONF = "testbed.urls"
PUSH_NOTIFICATIONS_SETTINGS = {
	"WP_PRIVATE_KEY": vapid_keys()["private_key"],
	"WP_CLAIMS": {"sub": "mailto:testbed@example.com"},
}

apns = local_config("apns")
if apns:
	PUSH_NOTIFICATIONS_SETTINGS.update({
		"APNS_AUTH_KEY_PATH": apns["key_path"],
		"APNS_AUTH_KEY_ID": apns["key_id"],
		"APNS_TEAM_ID": apns["team_id"],
		"APNS_TOPIC": apns["bundle_id"],
		"APNS_USE_SANDBOX": True,
	})

wns = local_config("wns")
if wns:
	PUSH_NOTIFICATIONS_SETTINGS.update({
		"WNS_PACKAGE_SECURITY_ID": wns["package_sid"],
		"WNS_SECRET_KEY": wns["secret"],
	})
