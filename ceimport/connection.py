import trompace.connection
from trompace.config import config

config.load()


def submit_request(query):
    return trompace.connection.submit_query(query, auth_required=True)
