# the checkout passed with --repo provides tests.settings
from tests.settings import *  # noqa: F401,F403

from common import vapid_keys

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
ROOT_URLCONF = "testbed_urls"
PUSH_NOTIFICATIONS_SETTINGS = {
	"WP_PRIVATE_KEY": vapid_keys()["private_key"],
	"WP_CLAIMS": {"sub": "mailto:testbed@example.com"},
}
