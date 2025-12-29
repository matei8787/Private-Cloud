from .base import *



LOG_FOLDER = Path(os.environ["LOG_FOLDER"])
LOG_FOLDER.mkdir(parents=True, exist_ok=True)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = ['https://ovpn.dorbjojomatei.mooo.com', 'https://dorbjojomatei.mooo.com',]
USE_X_FORWARDED_HOST = True

DATABASES = {
    'default': {
        'ENGINE': os.environ.get("SQL_ENGINE"),
        'NAME': os.environ.get("SQL_NAME"),
        'USER': os.environ.get("SQL_USER"),
        'PASSWORD': os.environ.get("SQL_PASS"),
        'HOST': os.environ.get("SQL_HOST"),
        'PORT': os.environ.get("SQL_PORT"),
    }
}

MIDDLEWARE.insert(0, 'core.middleware.ips.IPSMiddleware')
MIDDLEWARE.insert(0, 'core.middleware.ids.IDSMiddleware')
MIDDLEWARE.append('core.middleware.req_logger.ReqLoggerMiddleware')

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[{levelname}] {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "app_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_FOLDER / "ovpn.log"),
            "maxBytes": 10_000_000,
            "backupCount": 10,
            "formatter": "default",
        },
        "security_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_FOLDER / "security.log"),
            "maxBytes": 10_000_000,
            "backupCount": 10,
            "formatter": "default",
        },
        "req_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_FOLDER / "requests.log"),
            "maxBytes": 20_000_000,
            "backupCount": 10,
            "formatter": "default",
        },
        "test_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_FOLDER / "test.log"),
            "maxBytes": 1_000_000,
            "backupCount": 10,
            "formatter": "default",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    
    "loggers": {
        "django": {
            "handlers": ["console", "app_file"],
            "level": "INFO",
        },
        "ovpn.security": {
            "handlers": ["console", "security_file"],
            "level": "WARNING",
        },
        "ovpn.requests": {
            "handlers": ["console", "req_file"],
            "level": "INFO",
            "propagate": False,
        },
        "test": {
            "handlers": ["console", "test_file"],
            "level": "INFO",
        },
    }
}