import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost").split(",")

INSTALLED_APPS = [
    "jazzmin",
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
    "apps.accounts",
    "apps.rooms",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "lexisync.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ASGI_APPLICATION = "lexisync.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "lexisync",
        "USER": "lexisync",
        "PASSWORD": "lexisync_pass",
        "HOST": os.environ.get("DB_HOST", "db"),
        "PORT": "5432",
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get("REDIS_URL", "redis://redis:6379/0")],
        },
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_REDIRECT_URL = "rooms:lobby"
LOGOUT_REDIRECT_URL = "accounts:login"
LOGIN_URL = "accounts:login"

DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# ─────────────────────────────────────────────
#  JAZZMIN — Admin theme
# ─────────────────────────────────────────────
JAZZMIN_SETTINGS = {
    # Browser tab title
    "site_title": "LexiSync Admin",
    "site_header": "LexiSync",
    "site_brand": "LexiSync",
    "site_logo": None,
    "login_logo": None,
    "welcome_sign": "Welcome to the LexiSync Admin Panel",
    "copyright": "LexiSync",

    # Top nav search
    "search_model": ["auth.user", "rooms.room"],

    # User avatar in top bar
    "user_avatar": None,

    # Top nav links
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Open App", "url": "/", "new_window": True},
        {"model": "auth.user"},
        {"model": "rooms.room"},
    ],

    # Side menu
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],

    "order_with_respect_to": [
        "auth",
        "rooms",
    ],

    "icons": {
        "auth":                     "fas fa-users-cog",
        "auth.user":                "fas fa-user",
        "auth.Group":               "fas fa-users",
        "rooms.room":               "fas fa-video",
        "rooms.transcript":         "fas fa-comments",
    },

    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",

    # Related modal instead of new page
    "related_modal_active": True,

    # UI customizations
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": False,
    "show_ui_builder": False,

    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
    },
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,

    # Dark navbar + sidebar to match our app
    "brand_colour": "navbar-dark",
    "accent": "accent-purple",
    "navbar": "navbar-dark",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-purple",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "darkly",           # dark base theme
    "dark_mode_theme": "darkly",
    "button_classes": {
        "primary":   "btn-primary",
        "secondary": "btn-secondary",
        "info":      "btn-info",
        "warning":   "btn-warning",
        "danger":    "btn-danger",
        "success":   "btn-success",
    },
    "actions_sticky_top": True,
}
