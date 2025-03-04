"""
The purpose of this file is to define the metadata of the app with minimal imports.
"""

from mmif import DocumentTypes, AnnotationTypes

from clams.app import ClamsApp
from clams.appmetadata import AppMetadata

from lapps.discriminators import Uri


# DO NOT CHANGE the function name
def appmetadata() -> AppMetadata:
    """
    Function to set app-metadata values and return it as an ``AppMetadata`` obj.
    Read these documentations for more on the code below
    - https://sdk.clams.ai/appmetadata.html metadata specification.
    - https://sdk.clams.ai/autodoc/clams.appmetadata.html python API
    
    :return: AppMetadata object holding all necessary information.
    """
    
    # basic information
    metadata = AppMetadata(
        name="Tesseractocr Wrapper",
        description="This tool applies Tesseract OCR to a video or image and generates text boxes and OCR results.",
        app_license="Apache 2.0",  # short name for a software license
        identifier="tesseract",
        url="https://github.com/clamsproject/app-tesseractocr-wrapper",
        # (see ``.github/README.md`` file in this directory)
        analyzer_version='tesseract5.3',
        analyzer_license="Apache 2.0",  # short name for a software license
    )

    # I/O specifications: an app must have at least one input and one output
    metadata.add_input(DocumentTypes.VideoDocument)
    in_tf = metadata.add_input(AnnotationTypes.TimeFrame, representatives='?')
    in_tf.add_description('The Time frame annotation that represents the video segment to be processed. When '
                          '`representatives` property is present, the app will process videos still frames at the '
                          'underlying time point annotations that are referred to by the `representatives` property. '
                          'Otherwise, the app will process the middle frame of the video segment.')
    out_td = metadata.add_output(DocumentTypes.TextDocument, **{'@lang': 'en'})
    out_td.add_description('Fully serialized text content of the recognized text in the input images. Serialization is'
                           'done by concatenating `text` values of `Paragraph` annotations with two newline characters.')
    out_tkn = metadata.add_output(at_type=Uri.TOKEN, text='*', word='*')
    out_tkn.add_description('Translation of the recognized tesseract "words" in the input images. `token` '
                            'properties store the string values of the recognized text. The duplication is for keeping'
                            'backward compatibility and consistency with `Paragraph` and `Sentence` annotations.')
    out_sent = metadata.add_output(at_type=Uri.SENTENCE, text='*')
    out_sent.add_description('Translation of the recognized tesseract "lines" in the input images. `sentence` property from '
                             'LAPPS vocab stores the string value of space-joined words.')
    out_para = metadata.add_output(at_type=Uri.PARAGRAPH, text='*')
    out_para.add_description('Translation of the recognized tesseract "blocks" in the input images. `paragraph` property from '
                             'LAPPS vocab stores the string value of newline-joined sentences.')
    out_ali = metadata.add_output(AnnotationTypes.Alignment)
    out_ali.add_description('Alignments between 1) `TimePoint` <-> `TextDocument`, 2) `TimePoint` <-> '
                            '`Token`/`Sentence`/`Paragraph`, 3) `BoundingBox` <-> `Token`/`Sentence`/`Paragraph`')
    out_bbox = metadata.add_output(AnnotationTypes.BoundingBox, label='text')
    out_bbox.add_description('Bounding boxes of the detected text regions in the input images. No corresponding box '
                             'for the entire image (`TextDocument`) region')
    
    # add runtime parameter specifications
    metadata.add_parameter(name='tfLabel', default=[], type='string', multivalued=True,
                           description='The label of the TimeFrame annotation to be processed. By default (`[]`), all '
                                       'TimeFrame annotations will be processed, regardless of their `label` property '
                                       'values.')
    
    return metadata


# DO NOT CHANGE the main block
if __name__ == '__main__':
    import sys
    metadata = appmetadata()
    for param in ClamsApp.universal_parameters:
        metadata.add_parameter(**param)
    sys.stdout.write(metadata.jsonify(pretty=True))
