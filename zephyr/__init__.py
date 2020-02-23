'''
Copyright 2020 Alex Puffer
Licensed under MIT License
'''

import logging
from .zephyr import Zephyr

__version__ = '0.0.1'

LOGGER = logging.getLogger('zephyr')
LOGGER.setLevel(logging.debug)

def get_version():
    return __version__
