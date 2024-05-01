import logging
import sys
import os


def create_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    sysout_handler = logging.StreamHandler(sys.stdout)
    sysout_handler.setFormatter(
        logging.Formatter(r"%(name)-12s: %(levelname)-8s %(message)s")
    )
    file_handler = logging.FileHandler(f"{name}.log")
    file_handler.setFormatter(
        logging.Formatter(r"%(name)-12s: %(levelname)-8s %(message)s")
    )
    logger.addHandler(sysout_handler)
    logger.addHandler(file_handler)
    return logger


def is_debug():
    debug_var = os.environ.get("DEBUG")
    return debug_var == "true"
