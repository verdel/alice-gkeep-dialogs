# -*- coding: utf-8 -*-
import logging
import yaml


def init_log(debug=None):
    if debug:
        consolelog_level = logging.DEBUG
    else:
        consolelog_level = logging.INFO

    logger = logging.getLogger('alice-gkeep-dialogs')
    logger.setLevel(logging.DEBUG)

    # create console handler with a higher log level
    consolelog = logging.StreamHandler()
    consolelog.setLevel(consolelog_level)

    # create formatter and add it to the handlers
    formatter = logging.Formatter(u'%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s')
    consolelog.setFormatter(formatter)

    # add the handlers to logger
    logger.addHandler(consolelog)

    return logger


def get_config(path):
    with open(path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    return cfg
