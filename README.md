# TROMPA CE Data importer

This is a tool to import metadata to the Trompa Contributor Environment

It imports detailed data from the following sources:

  * CPDL
  * IMSLP
  * MusicBrainz
  * Wikidata
  * Muziekweb

It also imports basic identifiers for the following sources

  * VIAF
  * Worldcat
  * ISNI
  * Library of Congress

## Installation

    pip install requirements.txt

## Running the application

To configure the importer to point to a specific Contributor Environment, set
the `TROMPACE_CLIENT_CONFIG` environment variable to the path of a configuration
file for `trompace-client`:

    export TROMPACE_CLIENT_CONFIG=trompace.ini

The main entrypoint is `ceimport.cli`. Use

    python -m ceimport.cli

to get a list of imports that can be performed.

To get detailed documentation about a particular importer, user the help flag:

    $ python -m ceimport.cli cpdl-import-work --help

    Usage: python -m ceimport.cli cpdl-import-work [OPTIONS]

      Import the given work (--url x) or file of works (--file f). Works need to
      be wiki titles (no http://.... and no _ to split words.

    Options:
      --file TEXT
      --url TEXT
      --help       Show this message and exit.

### Muziekweb

To import data from Muziekweb into the Trompa CE start the import-mw.py script
with the nescessary parameters. For example To import a single track use:

    python import-mw.py -t JK136417-0003

The importer uses the Trompa CE client settings to connect and identify the
responsible account for the import. When using custom settings, you can place a
copy of the import.ini from the CE client in the root of this repository and
modify the settings in the file.

When importing audio fragments from an album release, the importer acquires
data from the Muziekweb API
(https://www.muziekweb.nl/Muziekweb/Webservice/WebserviceAPI.php). To make use
of this API an account is required. You can register a free account for the API
and fill the account details in a .env file. An example is given in the
.env.example file. You can also run the importer using the run parameters -mwu
and -mwp.

## License

Copyright 2020 Music Technology Group, Universitat Pompeu Fabra
Copyright 2020 Muziekweb

Licensed under the Apache License, Version 2.0. See LICENSE for more information
