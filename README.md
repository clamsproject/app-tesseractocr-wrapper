<<<<<<< Updated upstream
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
=======
# BURN AFTER READING

Delete this section of the document once the app development is done, before publishing the repository. 

---
This skeleton code is a scaffolding for Python-based CLAMS app development. Specifically, it contains 

1. `app.py` and `metadata.py` to write the app 
1. `requirements.txt` to specify python dependencies
1. `Containerfile` to containerize the app and specify system dependencies
1. `.gitignore` and `.dorckrignore` files listing commonly ignored files
1. an empty `LICENSE` file to replace with an actual license information of the app
1. `CLAMS-generic-readme.md` file with basic instructions of app installation and execution
1. This `README.md` file for additional information not specified in the generic readme file. 
1. A number of GitHub Actions workflows for issue/bug-report management 
1. A GHA workflow to publish app images upon any push of a git tag
   * **NOTE**: All GHA workflows included are designed to only work in repositories under `clamsproject` organization.

Before pushing your first commit, please make sure to delete this section of the document.

Then use the following section to document any additional information specific to this app. If your app works significantly different from what's described in the generic readme file, be as specific as possible. 

---

## User instruction

General user instruction for CLAMS apps is available at [CLAMS Apps documentation](https://apps.clams.ai/clamsapp/).

Below is a list of additional information specific to this app.

### System requirments

(Any system-level software required to run this app)

### Configurable runtime parameter

(Parameters should be already well-described in the app metadata. But you can use this space to show examples, for instance.)
>>>>>>> Stashed changes
