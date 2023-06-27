import logging


def logging_config():
    log_format = '%(asctime)s %(name)s[%(module)s] %(levelname)s: %(message)s'
    logging.basicConfig(format=log_format, level=logging.INFO)
