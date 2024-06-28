"""
The purpose of this file is to define the metadata of the app with minimal imports. 

DO NOT CHANGE the name of the file
"""

from mmif import DocumentTypes, AnnotationTypes

from clams.app import ClamsApp
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
    metadata.add_input(AnnotationTypes.BoundingBox, label='text')
    metadata.add_input(AnnotationTypes.TimeFrame, required=False)
    metadata.add_input(AnnotationTypes.TimePoint)

    metadata.add_output(DocumentTypes.TextDocument)
    metadata.add_output(AnnotationTypes.Alignment)

    metadata.add_parameter(name='frameType',
                           type='string',
                           description='Use this to specify TimeFrame to use for filtering "text"-typed BoundingBox '
                                       'annotations. Can be "slate", "chyron", "speech", etc.. If not set, the app '
                                       'won\'t use TimeFrames for filtering.',
                           default='',
                           multivalued=True)
    metadata.add_parameter(name='threshold',
                           type='number',
                           description='Use this value between 0 and 1 to filter out low-confidence text boxes.',
                           default=0.9)
    metadata.add_parameter(name='psm',
                           description='Tesseract Page Segmentation Modes. See '
                                       'https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html#page-segmentation-method',
                           type='integer',
                           choices=[x for x in range(14)],
                           default=0)
    return metadata


# DO NOT CHANGE the main block
if __name__ == '__main__':
    import sys
    metadata = appmetadata()
    for param in ClamsApp.universal_parameters:
        metadata.add_parameter(**param)
    sys.stdout.write(metadata.jsonify(pretty=True))
