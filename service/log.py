"""
Module to init logging.
"""

import os
import logging


LOG_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING').upper()


def init_logging():
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s %(module)20s:%(lineno)-8s %(levelname)-8s %(funcName)20s - %(message)s',
    )
