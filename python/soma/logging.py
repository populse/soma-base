import logging


def create_logger(name):
    """ """
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)s:%(funcName)s(%(lineno)s): %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
