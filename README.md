# Tesseractocr Wrapper

## Description

CLAMS app wraps around [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) to perform OCR on images or video frames. 

## User instruction

General user instruction for CLAMS apps is available at [CLAMS Apps documentation](https://apps.clams.ai/clamsapp).

Below is a list of additional information specific to this app.

### System requirments

This tool relies on the tesseract ocr engine and the pytesseract python library.

- [tesseract](https://github.com/tesseract-ocr/tesseract)

(The container image is built with `tesseract-ocr` (version 4) on Debian Buster, see https://packages.debian.org/buster/tesseract-ocr)

- [pytesseract](https://github.com/madmaze/pytesseract)

### Configurable runtime parameter

For the full list of parameters, please refer to the app metadata from [CLAMS App Directory](https://apps.clams.ai/clamsapp/) or [`metadata.py`](metadata.py) file in this repository.
