"""
The purpose of this file is to define the metadata of the app with minimal imports. 

DO NOT CHANGE the name of the file
"""

from mmif import DocumentTypes, AnnotationTypes

from clams.appmetadata import AppMetadata


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
    )
    metadata.add_input(DocumentTypes.VideoDocument)
    metadata.add_input(AnnotationTypes.BoundingBox, required=False, boxType='text')

    metadata.add_output(DocumentTypes.TextDocument)
    metadata.add_output(AnnotationTypes.BoundingBox)
    metadata.add_output(AnnotationTypes.Alignment)
    metadata.add_parameter(name='boxType', type='string',
                           description='When set, use exising "text"-typed ``BoundingBox`` annotations '
                                       'and run tesseract only on those regions, instead of entire frames.',
                           default=' ') # was this whitespace due to https://github.com/clamsproject/clams-python/issues/110 ?
    return metadata


# DO NOT CHANGE the main block
if __name__ == '__main__':
    import sys
    sys.stdout.write(appmetadata().jsonify(pretty=True))
