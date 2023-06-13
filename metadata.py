"""
The purpose of this file is to define the metadata of the app with minimal imports. 

DO NOT CHANGE the name of the file
"""

from mmif import DocumentTypes, AnnotationTypes

from clams.appmetadata import AppMetadata


<<<<<<< Updated upstream
# DO NOT CHANGE the function name 
def appmetadata() -> AppMetadata:
    
    metadata = AppMetadata(
        name="Tesseract OCR Wrapper",
        description="This tool applies Tesseract OCR to a video or image and generates text boxes and OCR results.",
        app_license='MIT',
        identifier="tesseract", 
        url="https://github.com/clamsproject/app-tesseractocr-wrapper",
        analyzer_version='tesseract4',
        analyzer_license='apache',
=======
def appmetadata() -> AppMetadata:
    """
    Function to set app-metadata values and return it as an ``AppMetadata`` obj.
    Read these documentations before changing the code below
    - https://sdk.clams.ai/appmetadata.html metadata specification. 
    - https://sdk.clams.ai/autodoc/clams.appmetadata.html python API
    
    :return: AppMetadata object holding all necessary information.
    """
    
    metadata = AppMetadata(
        name="Tesseract OCR Wrapper",
        description="This tool applies Tesseract OCR to a video or"
            "image and generates text boxes and OCR results.",
        app_license="MIT",
        identifier="tesseract",  # from 'tesseract' in the old id full url: http://apps.clams.ai/tesseract/...
        url="https://github.com/clamsproject/app-tesseractocr-wrapper",
        analyzer_version='version_4.0.0-2',   # https://packages.debian.org/buster/tesseract-ocr
        # if pytesseract
        # analyzer_version=[line.strip().rsplit('==')[-1]
        #                  for line in open('requirements.txt').readlines() if re.match(r'^pytesseract==', line)][0],
        analyzer_license="apache",
>>>>>>> Stashed changes
    )
    metadata.add_input(DocumentTypes.VideoDocument)
    metadata.add_input(AnnotationTypes.BoundingBox, required=False, boxType='text')

    metadata.add_output(DocumentTypes.TextDocument)
    metadata.add_output(AnnotationTypes.BoundingBox)
    metadata.add_output(AnnotationTypes.Alignment)
<<<<<<< Updated upstream
    metadata.add_parameter(name='boxType', type='string',
                           description='When set, use exising "text"-typed ``BoundingBox`` annotations '
                                       'and run tesseract only on those regions, instead of entire frames.',
                           default=' ') # was this whitespace due to https://github.com/clamsproject/clams-python/issues/110 ?
=======
    
    # (optional) and finally add runtime parameter specifications
    metadata.add_parameter(name='boxType', type='string',
                           description='When set, use exising "text"-typed ``BoundingBox`` annotations '
                                       'and run tesseract only on those regions, instead of entire frames.',
                           default=' ')

>>>>>>> Stashed changes
    return metadata


# DO NOT CHANGE the main block
if __name__ == '__main__':
    import sys
    sys.stdout.write(appmetadata().jsonify(pretty=True))
