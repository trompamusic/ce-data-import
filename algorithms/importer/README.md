# CE Data importer algorithm

To build, run from the root directory of the ce-data-import project:

    docker build -f algorithms/importer/Dockerfile -t tropmamusic/ce-data-importer:latest .

Each importer should have its own EntryPoint, connected to the same SoftwareApplication.

Additional import methods can be discovered by running the help of the main `ceimport.cli`
module, as described in the main README file.