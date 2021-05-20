from clams.app import ClamsApp
from clams.restify import Restifier

from tesseract_utils import *

APP_VERSION = 0.1


class OCR(ClamsApp):
    def _appmetadata(self):
        metadata = {
            "name": "Tesseract OCR",
            "description": "This tool applies Tesseract OCR to an "
            "image and generates text boxes and OCR result.",
            "vendor": "Team CLAMS",
            "iri": f"http://mmif.clams.ai/apps/tesseract/{APP_VERSION}",
            "app": f"http://mmif.clams.ai/apps/tesseract/{APP_VERSION}",
            "requires": [DocumentTypes.ImageDocument.value, DocumentTypes.VideoDocument.value],
            "produces": [
                AnnotationTypes.BoundingBox.value,
                AnnotationTypes.Alignment.value,
                DocumentTypes.TextDocument.value,
            ],
        }
        return metadata

    def _annotate(self, mmif_obj: Mmif, **kwargs) -> Mmif:
        """
        :param mmif_obj: this mmif could contain images or video, with or without preannotated text boxes
        :param **kwargs:
        :return: annotated mmif as string
        """
        new_view = mmif_obj.new_view()
        new_view.metadata['app'] = self.metadata["iri"]
        new_view.metadata.set_additional_property("parameters", kwargs.copy())
        box_type = kwargs.pop('boxType') if 'boxType' in kwargs else None
        if box_type:
            mmif_obj = box_ocr(mmif_obj, new_view, box_type, **kwargs)
        else:
            mmif_obj = full_ocr(mmif_obj, new_view, **kwargs)
        return mmif_obj


if __name__ == "__main__":
    ocr_tool = OCR()
    ocr_service = Restifier(ocr_tool)
    ocr_service.run()
