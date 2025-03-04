# Tesseractocr Wrapper

## Description

CLAMS app wraps around [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) to perform OCR on images or video frames. 

## Input

The wrapper takes a [`VideoDocument`]('https://mmif.clams.ai/vocabulary/VideoDocument/v1/') with SWT 
[`TimeFrame`]('https://mmif.clams.ai/vocabulary/TimeFrame/v3/') annotations. The app specifically 
uses the representative `TimePoint` annotations from SWT v4 `TimeFrame` annotations to extract specific frames for OCR

## tesseract Structured Output

[From the tesseract documentation]('https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html')

The tesseract model returns a `dict` with pytesseract's `image_to_data` [function](https://pypi.org/project/pytesseract/)

Here is the typical layout:
```
{'level': [], 'page_num': [], 'block_num': [],’par_num': [], 'line_num': [], 'word_num': [], 'left': [], 'top': [], 'width': [], 'height': [], 'conf': [], 'text': []}
```

The tesseract wrapper preserves this structured information in the output MMIF by creating 
lapps `Paragraph` `Sentence` and `Token` annotations corresponding to the `Block`, `Line`, and `Word` from the tesseract output.

## User instruction

General user instruction for CLAMS apps is available at [CLAMS Apps documentation](https://apps.clams.ai/clamsapp).

Below is a list of additional information specific to this app.

### System requirments

This tool relies on the tesseract ocr engine and the pytesseract python library.

- [tesseract](https://github.com/tesseract-ocr/tesseract)

(The container image is built with `tesseract-ocr` (version 5.3) on Debian Bookworm, see https://packages.debian.org/source/bookworm/tesseract)

- [pytesseract](https://github.com/madmaze/pytesseract)
- Requires mmif-python[cv] for the `VideoDocument` helper functions

### Configurable runtime parameter

For the full list of parameters, please refer to the app metadata from [CLAMS App Directory](https://apps.clams.ai/clamsapp/) or [`metadata.py`](metadata.py) file in this repository.
