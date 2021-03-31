# app-tesseract-wrapper

This CLAMS app wraps the tesseract OCR tool. 

---
`docker build .`

`docker run -p 5000:[host port] -v [host data path]:/data [docker image name]`

Tested with command:

`curl -H 'Content-Type:application/json' -d "@[path to mmif json]" -X PUT http://localhost:5000/` 

Where the media location designated in the mmif json is in the volume mounted by the container.
___
# Parameters
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

---

This tool relies on the tesseract ocr engine and the pytesseract python library.

- [tesseract](https://github.com/tesseract-ocr/tesseract)

- [pytesseract](https://github.com/madmaze/pytesseract)