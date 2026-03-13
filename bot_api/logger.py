import logging
import sys

from gunicorn.glogging import Logger


def get_logger() -> logging.Logger:
    logging.captureWarnings(True)
    logger = logging.getLogger("hd-rag-bot")
    logger.setLevel(logging.INFO)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(
        logging.Formatter(fmt="[%(asctime)s;%(levelname)s;%(name)s] %(message)s")
    )

    logger.addHandler(stdout_handler)
    return logger


logger = get_logger()


class CustomLogger(Logger):
    def setup(self, cfg):
        super().setup(cfg)

        # Override Gunicorn's `error_log` configuration.
        self._set_handler(
            self.error_log,
            cfg.errorlog,
            logging.Formatter(fmt="[%(asctime)s;%(levelname)s;%(name)s] %(message)s"),
        )
