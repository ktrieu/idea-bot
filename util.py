import logging
import sys


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
