# IMSLP Zip extractor algorithm

This algorithm looks at a `MediaObject` whose `contributor` is `https://imslp.org`
and whose `source` points to a zip file.

It downloads the file pointed to by `source`, extracts the zip file, and finds
the path to a MusicXML file inside that archive. It updates the `MediaObject`
to set the `contentUrl` field to an ARCP hash which identifies the MusicXML
file inside the zip.

### Building

From this current directory:

        docker build -t tropmamusic/imslp-zip-extract:latest .

### Running

To run the extractor:

Ensure that the ce-