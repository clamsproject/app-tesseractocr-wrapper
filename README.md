## User instruction

General user instruction for CLAMS apps is available at [CLAMS Apps documentation](https://apps.clams.ai/clamsapp/).

Below is a list of additional information specific to this app.

### System requirments

This tool relies on the tesseract ocr engine and the pytesseract python library.

- [tesseract](https://github.com/tesseract-ocr/tesseract)

(The container image is built with `tesseract-ocr` (version 4) on Debian Buster, see https://packages.debian.org/buster/tesseract-ocr)

- [pytesseract](https://github.com/madmaze/pytesseract)

### Configurable runtime parameter

This CLAMS app accepts the following query parameters

- pretty
- boxType: string, default: None, If this parameter is set, the sample ratio parameter is ignored. When this parameter is set, instead of applying Tesseract to the entire frame, Tesseract is applied to regions of the frame specified by BoundingBox annotations with the specified box type.
- frameType: string, default: None, If this parameter is set, the sample ratio parameter is ignored. The middle frame is selected from all TimeFrame annotations that match the specified frameType
- sampleRatio: integer, default: 30
- boxThreshold: integer, default: 90
- Tesseract Specific Parameters
   - psm: string, page segmentation mode
   - oem: string,
   - char_whitelist: string *NOTE: only supported with oem=0.*