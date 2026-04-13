import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _default_sqlite_path() -> Path:
    # Inside the container, /data is mounted as a volume.
    if Path("/data").exists():
        return Path("/data/db.sqlite3")
    return BASE_DIR / "data" / "db.sqlite3"


def _default_static_root() -> Path:
    # Keep /static for containerized deploy, use local folder otherwise.
    if Path("/static").exists():
        return Path("/static")
    return BASE_DIR / "staticfiles"

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key-insegura-apenas-local")

DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = ["*"]

# Origens confiáveis para CSRF (necessário para proxies/tunnels como Cloudflare)
_extra_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [
    "https://*.trycloudflare.com",
] + [o.strip() for o in _extra_origins.split(",") if o.strip()]

INSTALLED_APPS = [
    # Unfold deve vir antes do django.contrib.admin
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.import_export",
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceiros
    "import_export",
    "admincharts",
    # App principal
    "inventory",
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

ROOT_URLCONF = "netinventory.urls"

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

WSGI_APPLICATION = "netinventory.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("SQLITE_PATH", str(_default_sqlite_path())),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Recife"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = os.environ.get("STATIC_ROOT", str(_default_static_root()))
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/admin/login/"

# ─── Tema Unfold ─────────────────────────────────────────────────────────────
UNFOLD = {
    "SITE_TITLE": "NetInventory",
    "SITE_HEADER": "Inventário de Rede — UFPB",
    "SITE_SYMBOL": "router",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "COLORS": {
        "primary": {
            "50": "240 249 255",
            "100": "224 242 254",
            "200": "186 230 253",
            "300": "125 211 252",
            "400": "56 189 248",
            "500": "14 165 233",
            "600": "2 132 199",
            "700": "3 105 161",
            "800": "7 89 133",
            "900": "12 74 110",
            "950": "8 47 73",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Dispositivos de Rede",
                "separator": True,
                "items": [
                    {
                        "title": "Switches",
                        "icon": "device_hub",
                        "link": "/admin/inventory/switch/",
                    },
                    {
                        "title": "Roteadores",
                        "icon": "router",
                        "link": "/admin/inventory/roteador/",
                    },
                    {
                        "title": "Access Points",
                        "icon": "wifi",
                        "link": "/admin/inventory/accesspoint/",
                    },
                ],
            },
            {
                "title": "Computação",
                "separator": True,
                "items": [
                    {
                        "title": "Computadores",
                        "icon": "computer",
                        "link": "/admin/inventory/computador/",
                    },
                    {
                        "title": "E-mails Institucionais",
                        "icon": "email",
                        "link": "/admin/inventory/emailinstitucional/",
                    },
                    {
                        "title": "Sites",
                        "icon": "language",
                        "link": "/admin/inventory/site/",
                    },
                ],
            },
            {
                "title": "Infraestrutura",
                "separator": True,
                "items": [
                    {
                        "title": "Subredes",
                        "icon": "lan",
                        "link": "/admin/inventory/subrede/",
                    },
                    {
                        "title": "Localizações",
                        "icon": "location_on",
                        "link": "/admin/inventory/localizacao/",
                    },
                    {
                        "title": "Fabricantes",
                        "icon": "factory",
                        "link": "/admin/inventory/fabricante/",
                    },
                ],
            },
            {
                "title": "Monitoramento",
                "separator": True,
                "items": [
                    {
                        "title": "Varredura de Rede",
                        "icon": "radar",
                        "link": "/inventory/varredura/",
                    },
                    {
                        "title": "Histórico de Pings",
                        "icon": "timeline",
                        "link": "/admin/inventory/historicoping/",
                    },
                    {
                        "title": "Dashboard",
                        "icon": "dashboard",
                        "link": "/inventory/dashboard/",
                    },
                ],
            },
        ],
    },
}
