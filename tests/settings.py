SECRET_KEY = "test-django-secret-key"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "fastaar_django",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

ROOT_URLCONF = "fastaar_django.urls"

USE_TZ = True

# Fastaar mock settings
FASTAAR_API_KEY = "fk_test_12345"
FASTAAR_WEBHOOK_SECRET = "whsec_test_secret_key"
FASTAAR_TIMEOUT = 10
