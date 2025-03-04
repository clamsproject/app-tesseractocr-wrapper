"""
wrapper for tesseract version 5.5 OCR
"""

import argparse
import logging

from clams.app import ClamsApp
from clams.restify import Restifier
from mmif import Mmif, View, Document, AnnotationTypes, DocumentTypes

# For an NLP tool we need to import the LAPPS vocabulary items
from lapps.discriminators import Uri

import tesseract_utils
import json


class TesseractocrWrapper(ClamsApp):

    def __init__(self):
        super().__init__()

    def _appmetadata(self):
        pass

    def _annotate(self, mmif: Mmif, **parameters) -> Mmif:
        video_doc: Document = mmif.get_documents_by_type(DocumentTypes.VideoDocument)[0]
        input_view: View = mmif.get_views_for_document(video_doc.properties.id)[-1]

        new_view: View = mmif.new_view()
        self.sign_view(new_view, parameters)
        new_view.new_contain(DocumentTypes.TextDocument)
        new_view.new_contain(AnnotationTypes.BoundingBox)
        new_view.new_contain(AnnotationTypes.Alignment)
        new_view.new_contain(Uri.PARAGRAPH)
        new_view.new_contain(Uri.SENTENCE)
        new_view.new_contain(Uri.TOKEN)

        futures = []
        for timeframe in input_view.get_annotations(AnnotationTypes.TimeFrame):
            if 'label' in timeframe:
                self.logger.debug(f'Found a time frame "{timeframe.id}" of label: "{timeframe.get("label")}"')
            else:
                self.logger.debug(f'Found a time frame "{timeframe.id}" without label')
            if parameters.get("tfLabel") and \
                    'label' in timeframe and timeframe.get("label") not in parameters.get("tfLabel"):
                continue
            else:
                self.logger.debug(f'Processing time frame "{timeframe.id}"')
            for rep_id in timeframe.get("representatives"):
                if Mmif.id_delimiter not in rep_id:
                    rep_id = f'{input_view.id}{Mmif.id_delimiter}{rep_id}'
                representative = mmif[rep_id]
                futures.append(tesseract_utils.process_time_annotation(mmif, representative, new_view, video_doc))
            if len(futures) == 0:
                # meaning "representatives" was not present, so alternatively, just process the middle frame
                futures.append(tesseract_utils.process_time_annotation(mmif, timeframe, new_view, video_doc))
                pass

        for future in futures:
            timestamp, text_content = future
            self.logger.debug(f'Processed timepoint: {timestamp} ms, recognized text: "{json.dumps(text_content)}"')

        return mmif

def get_app():
    """
    This function effectively creates an instance of the app class, without any arguments passed in, meaning, any
    external information such as initial app configuration should be set without using function arguments. The easiest
    way to do this is to set global variables before calling this.
    """
    return TesseractocrWrapper()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", action="store", default="5000", help="set port to listen")
    parser.add_argument("--production", action="store_true", help="run gunicorn server")
    # add more arguments as needed

    parsed_args = parser.parse_args()

    # create the app instance
    app = get_app()

    http_app = Restifier(app, port=int(parsed_args.port))
    # for running the application in production mode
    if parsed_args.production:
        http_app.serve_production()
    # development mode
    else:
        app.logger.setLevel(logging.DEBUG)
        http_app.run()
