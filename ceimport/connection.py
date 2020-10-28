import os

import trompace.connection
from trompace.config import config

from ceimport import logger

config_file = os.getenv("TROMPA_CONFIG")
if not config_file:
    logger.info("TROMPA_CONFIG env var not set, using default trompace.ini")
    config_file = 'trompace.ini'

config.load('trompace.ini')


def submit_request(query):
    return trompace.connection.submit_query(query, auth_required=True)
