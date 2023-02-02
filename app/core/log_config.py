import logging
import logging.config

# testing
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "standard",
        },
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": "match_gathering.log",
            "when": "D",
            "interval": 1,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "": {"handlers": ["stdout", "file"], "level": "INFO"},
    },
}


def log_config():
    logging.config.dictConfig(LOGGING_CONFIG)
