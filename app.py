import argparse
<<<<<<< Updated upstream

from clams import ClamsApp, Restifier, AppMetadata
=======
from typing import Union
>>>>>>> Stashed changes

# mostly likely you'll need these modules/classes
from clams import ClamsApp, Restifier
from mmif import Mmif, View, Annotation, Document, AnnotationTypes, DocumentTypes
from tesseract_utils import *

<<<<<<< Updated upstream

class OCR(ClamsApp):
    def _appmetadata(self) -> AppMetadata:
        pass

    def _annotate(self, mmif_obj: Mmif, **kwargs) -> Mmif:
=======

class OCRWrapper(ClamsApp):

    def __init__(self):
        super().__init__()

    def _appmetadata(self):
        # see https://sdk.clams.ai/autodoc/clams.app.html#clams.app.ClamsApp._load_appmetadata
        # Also check out ``metadata.py`` in this directory. 
        # When using the ``metadata.py`` leave this do-nothing "pass" method here. 
        pass

    def _annotate(self, mmif: Union[str, dict, Mmif], **runtime_params) -> Mmif:
        # see https://sdk.clams.ai/autodoc/clams.app.html#clams.app.ClamsApp._annotate
>>>>>>> Stashed changes
        """
        :param mmif_obj: this mmif could contain images or video, with or without preannotated text boxes
        :param **kwargs:
        :return: annotated mmif as string
        """
        new_view = mmif.new_view()
        self.sign_view(new_view, self.get_configuration(**runtime_params))
        new_view.new_contain(DocumentTypes.TextDocument)
        box_type = runtime_params.pop("boxType").strip() if "boxType" in runtime_params else None
        if box_type:
            mmif = box_ocr(mmif, new_view, box_type, **runtime_params)
        else:
            mmif = full_ocr(mmif, new_view, **runtime_params)
        return mmif

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
<<<<<<< Updated upstream
    ocr_tool = OCR()

    ocr_service = Restifier(ocr_tool, port=int(parsed_args.port)
                         )
    if parsed_args.production:
        ocr_service.serve_production()
    else:
        ocr_service.run()
=======
    app = OCRWrapper()

    http_app = Restifier(app, port=int(parsed_args.port))
    if parsed_args.production:
        http_app.serve_production()
    else:
        http_app.run()
>>>>>>> Stashed changes
