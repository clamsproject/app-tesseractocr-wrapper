import argparse
from clams import ClamsApp, Restifier, AppMetadata
from mmif import Mmif
from tesseract_utils import *

class OCR(ClamsApp):
    def _appmetadata(self) -> AppMetadata:
        """See metadata.py"""
        pass

    def _annotate(self, mmif_obj: Mmif, **kwargs) -> Mmif:
        """
        :param mmif_obj: this mmif could contain images or video, with or without preannotated text boxes
        :param **kwargs:
        :return: annotated mmif as string
        """
        new_view = mmif_obj.new_view()
        self.sign_view(new_view, self.get_configuration(**kwargs))
        new_view.new_contain(DocumentTypes.TextDocument)
        if 'use_existing_text_boxes' in kwargs and kwargs['use_existing_text_boxes']:
            mmif_obj = box_ocr(mmif_obj, new_view, **kwargs)
        else:
            mmif_obj = full_ocr(mmif_obj, new_view, **kwargs)
        return mmif_obj

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port", action="store", default="5000", help="set port to listen"
    )
    parser.add_argument("--production", action="store_true", help="run gunicorn server")
    # more arguments as needed
    # parser.add_argument(more_arg...)

    parsed_args = parser.parse_args()

    # create the app instance
    ocr_tool = OCR()

    ocr_service = Restifier(ocr_tool, port=int(parsed_args.port)
                         )
    if parsed_args.production:
        ocr_service.serve_production()
    else:
        ocr_service.run()
