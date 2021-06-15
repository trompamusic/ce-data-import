# MusicXML to MEI converter

This algorithm takes `MediaObjects` that represent a MusicXML file and converts
the MusicXML to MEI, creating a new `MediaObject` and linking them together.

Files get written to an S3 bucket called `meiconversion` on the configured S3 host.

The converter uses [verovio](https://www.verovio.org/index.xhtml) to convert to
MEI. Verovio sometimes has trouble converting files, so we also use musescore if
verovio crashes while converting.

The conversion process takes the following steps

1. Create a `SoftwareApplication` to represent the current version of veriovio and
   the current version of musescore.
   
2. Only process the `MediaObject` if its contributor is ISMLP or CPDL. Download the
   file referred to by `contentUrl`
   
3. Try and convert the MusicXML file using Verovio. If it crashes, use Musescore to
   pass through the MusicXML file to MusicXML again and try with Verovio again.
   If it continues to fail, mark the conversion as failed.

4. Join the newly created MEI file as `exampleOfWork` to the `MusicComposition`
   and `wasDerivedFrom` to the original MusicXML. Set `prov:used` between the MEI
   node and the Application(s) that were used to perform the conversion

### Building

Building is done in two steps. First build a Verovio image:

    cd verovio
    make build

Then you can build the converter, which copies verovio from the previous image.
This saves build time if you need to update the converter image.

   docker build -t tropmamusic/mxml-to-mei:latest .

### Running

To access the CE, set the environment variable `TROMPACE_CLIENT_CONFIG` to point to
a config file for the `trompace-client`, pointing to the CE that you want to read.

To write to S3, set the following environment variables: `S3_HOST`, `S3_ACCESS_KEY`,
`S3_SECRET_KEY`.

To run the converter:

    python mxml_to_mei.py convert-mxml-to-mei-node [mediaobject-id]
