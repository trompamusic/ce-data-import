#!/usr/bin/env python3
"""
Trompa data importer for Muziekweb catalog.


Copyright 2019, C. Karreman
Licensed under GPLv3.
"""
import os
import argparse
import asyncio
import trompace as ce

from muziekweb_api import set_api_account
from importers import import_artist, import_album
from dotenv import load_dotenv

# Environment settings (defaults)
load_dotenv()
trompa_ce_host = os.environ["CE_HOST"] if "CE_HOST" in os.environ else "http://localhost:4000"
mw_api_user = os.environ["MW_API_USER"] if "MW_API_USER" in os.environ else None
mw_api_pass = os.environ["MW_API_PASS"] if "MW_API_PASS" in os.environ else None

# Construct the argument parser and parse the arguments
main_parser = argparse.ArgumentParser(description="Input data options:")
main_parser.add_argument("-a", dest="artist", required=False, help="Muziekweb performer_id or input file with Muziekweb performer identifiers.")
main_parser.add_argument("-r", dest="release", required=False, help="Muziekweb album_id or input file with Muziekweb albums release identifiers.")

# Trompa CE
main_parser.add_argument("-ce", dest="ce_host", required=False, help="Trompa CE host.")
main_parser.add_argument("-ceu", dest="ce_user", required=False, help="Trompa CE username.")
main_parser.add_argument("-cep", dest="ce_pass", required=False, help="Trompa CE password.")

# Muziekweb API
main_parser.add_argument("-mwu", dest="mw_api_user", required=False, help="The username for the Muziekweb API.")
main_parser.add_argument("-mwp", dest="mw_api_pass", required=False, help="The password for the Muziekweb API.")


# Startup defaults or parameterized values
args = main_parser.parse_args()
# Import options
source_artist = None if args.artist is None else args.artist.strip(" \n\t\"")
source_release = None if args.release is None else args.release.strip(" \n\t\"")

# Trompa CE
trompa_ce_host = trompa_ce_host if args.ce_host is None else args.ce_host
trompa_ce_user = None if args.ce_host is None else args.ce_user
trompa_ce_pass = None if args.ce_host is None else args.ce_pass

# Muziekweb API
mw_api_user = mw_api_user if args.mw_api_user is None else args.mw_api_user
mw_api_pass = mw_api_pass if args.mw_api_pass is None else args.mw_api_pass


def readKeys(input: str) -> [str]:
    if os.path.isfile(input):
        with open(input, "r") as f:
            keys = f.read().splitlines()
        return keys
    else:
        return [input]


if __name__ == "__main__":
    # Set the hostname where data data is imported

    # NOTE: Currently requires the fix/remove-ce-host-setting-from-file branch
    # of the Trompa CE client


    # Trompa Example (not working yet)
    config_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'import.ini')
    if os.path.exists(config_file):
        ce.config.config.read_config(config_file)
    else:
        _proto, _server = trompa_ce_host.split("://")
        ce.config.config.set_server(_server, (_proto == "https"))


    # Set the Muziekweb API account
    if mw_api_user is not None and mw_api_pass is not None:
        set_api_account(mw_api_user, mw_api_pass)

    # Import Muziekweb artists into the Trompa CE
    #asyncio.run(import_artist(readKeys(source_artist)))
    asyncio.run(import_album(readKeys(source_release)))
