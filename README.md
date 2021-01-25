# Muziekweb data import for Trompa Contributor Environment

Muziekweb Rotterdam, the Netherlands

A python script that imports data from Muziekweb into the Trompa CE.

## Installation

For this application to run the Trompa CE Client is required. Download the
code from https://github.com/trompamusic/trompa-ce-client and install the
package as python library by running the following commend in the root of the
package:

    python setup.py install

To install the package dependencies run:

    pip install requirements.txt

## Running the application

To import data from Muziekweb into the Trompa CE start the import-mw.py script
with the nescessary parameters. For example to import an artist identified by
the Muziekweb identifier 'M00000238467':

    python import-mw.py -a M00000238467

To import album information use:

    python import-mw.py -r JK90000

To import a single track use:

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

```
Copyright 2020 Muziekweb

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
